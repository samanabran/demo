# -*- coding: utf-8 -*-
###############################################################################
#    Part of the SGC Odoo Suite <https://sgctech.ai>
#
#    SGC TECH AI
#    Copyright (C) 2026 SGC TECH AI (<https://sgctech.ai>)
#
#    This module and its source code are licensed under the Odoo Proprietary
#    License v1.0 (OPL-1). You may not redistribute or resell it. See
#    https://www.odoo.com/documentation/19.0/legal/licenses.html for terms.
###############################################################################

import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timedelta

import requests

from odoo import _
from odoo.addons.sgc_video_conferencing.services.provider_interface import BaseVideoProvider
from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry

_logger = logging.getLogger(__name__)


@ProviderRegistry.register
class GoToMeetingProvider(BaseVideoProvider):

    provider_code = 'gotomeeting'
    provider_name = 'GoTo Meeting'

    @property
    def supports_oauth(self):
        return True

    def _get_headers(self, account):
        token = account._get_oauth_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def get_oauth_url(self, account):
        client_id = account.oauth_client_id
        redirect_uri = account.oauth_redirect_uri or 'http://localhost:8069/video_conference/oauth/callback'
        return (
            f'https://authentication.logmeininc.com/oauth/authorize'
            f'?client_id={client_id}'
            f'&redirect_uri={redirect_uri}'
            f'&response_type=code'
        )

    def exchange_oauth_code(self, account, code):
        client_id = account.oauth_client_id
        client_secret = account._get_oauth_client_secret()
        redirect_uri = account.oauth_redirect_uri

        resp = requests.post(
            'https://authentication.logmeininc.com/oauth/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
            },
            auth=(client_id, client_secret),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        expires_at = datetime.now() + timedelta(seconds=data.get('expires_in', 3600))
        account._set_oauth_access_token(data['access_token'])
        if data.get('refresh_token'):
            account._set_oauth_refresh_token(data['refresh_token'])
        account.oauth_expires_at = expires_at
        account.state = 'verified'
        return data

    def refresh_token(self, account):
        client_id = account.oauth_client_id
        refresh_token = account._get_oauth_refresh_token()
        if not refresh_token:
            return False
        try:
            resp = requests.post(
                'https://authentication.logmeininc.com/oauth/token',
                data={'grant_type': 'refresh_token', 'refresh_token': refresh_token},
                auth=(client_id, ''),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            expires_at = datetime.now() + timedelta(seconds=data.get('expires_in', 3600))
            account._set_oauth_access_token(data['access_token'])
            if data.get('refresh_token'):
                account._set_oauth_refresh_token(data['refresh_token'])
            account.oauth_expires_at = expires_at
            account.state = 'verified'
            return True
        except Exception as e:
            _logger.error("GoTo token refresh failed: %s", e)
            account.state = 'expired'
            return False

    def create_meeting(self, meeting):
        account = meeting.provider_account_id
        if not account:
            return self._generate_basic_link(meeting)
        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        body = {
            'subject': meeting.name,
            'starttime': start,
            'endtime': (meeting.end_time or meeting.start_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'timezone': self.env.user.tz or 'UTC',
        }
        resp = requests.post(
            'https://api.getgo.com/G2M/rest/meetings',
            headers=headers, json=body, timeout=30,
        )
        if resp.status_code == 401 and self.refresh_token(account):
            headers = self._get_headers(account)
            resp = requests.post(
                'https://api.getgo.com/G2M/rest/meetings',
                headers=headers, json=body, timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        return {
            'join_url': data.get('joinUrl', ''),
            'start_url': data.get('hostUrl', ''),
            'provider_meeting_id': str(data.get('meetingId', '')),
            'password': str(data.get('meetingPassword', '')),
        }

    def _generate_basic_link(self, meeting):
        return {
            'join_url': 'https://meetings.goto.com/join',
            'start_url': 'https://meetings.goto.com/join',
            'provider_meeting_id': str(uuid.uuid4().int)[:11],
        }

    def update_meeting(self, meeting):
        if not meeting.provider_meeting_id or not meeting.provider_account_id:
            return True
        account = meeting.provider_account_id
        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        body = {'subject': meeting.name, 'starttime': start}
        url = f"https://api.getgo.com/G2M/rest/meetings/{meeting.provider_meeting_id}"
        resp = requests.put(url, headers=headers, json=body, timeout=30)
        if resp.status_code == 401 and self.refresh_token(account):
            headers = self._get_headers(account)
            resp = requests.put(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        return True

    def delete_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return True
        account = meeting.provider_account_id
        if not account:
            return True
        headers = self._get_headers(account)
        url = f"https://api.getgo.com/G2M/rest/meetings/{meeting.provider_meeting_id}"
        try:
            resp = requests.delete(url, headers=headers, timeout=30)
            if resp.status_code == 401 and self.refresh_token(account):
                headers = self._get_headers(account)
                resp = requests.delete(url, headers=headers, timeout=30)
        except Exception:
            pass
        return True

    def get_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return None
        account = meeting.provider_account_id
        if not account:
            return None
        headers = self._get_headers(account)
        try:
            resp = requests.get(
                f"https://api.getgo.com/G2M/rest/meetings/{meeting.provider_meeting_id}",
                headers=headers, timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_join_url(self, meeting):
        return meeting.join_url

    def verify_connection(self, account):
        headers = self._get_headers(account)
        try:
            resp = requests.get(
                'https://api.getgo.com/G2M/rest/meetings',
                headers=headers, timeout=15,
            )
            return resp.status_code == 200
        except Exception:
            return False
