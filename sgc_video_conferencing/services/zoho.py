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

import logging
import uuid
from datetime import datetime, timedelta

import requests

from odoo import _
from odoo.addons.sgc_video_conferencing.services.provider_interface import BaseVideoProvider
from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry

_logger = logging.getLogger(__name__)


@ProviderRegistry.register
class ZohoMeetingProvider(BaseVideoProvider):

    provider_code = 'zoho'
    provider_name = 'Zoho Meeting'

    @property
    def supports_oauth(self):
        return True

    def _get_accounts_url(self, account):
        return account.zoho_accounts_url or 'https://accounts.zoho.com'

    def _get_api_url(self, account):
        region = self._get_region(account)
        return f'https://meetingapi.zoho.{region}/api/v1'

    def _get_region(self, account):
        url = self._get_accounts_url(account)
        mapping = {
            'accounts.zoho.com': 'com',
            'accounts.zoho.eu': 'eu',
            'accounts.zoho.in': 'in',
            'accounts.zoho.com.cn': 'cn',
            'accounts.zoho.jp': 'jp',
            'accounts.zoho.com.au': 'com.au',
        }
        for key, region in mapping.items():
            if key in url:
                return region
        return 'com'

    def _get_headers(self, account):
        token = account._get_oauth_access_token()
        return {'Authorization': f'Zoho-oauthtoken {token}'}

    def get_oauth_url(self, account):
        client_id = account.oauth_client_id
        redirect_uri = account.oauth_redirect_uri or 'http://localhost:8069/video_conference/oauth/callback'
        accounts_url = self._get_accounts_url(account)
        scope = 'ZohoMeeting.meeting.all,ZohoMeeting.recording.all'
        return (
            f'{accounts_url}/oauth/v2/auth'
            f'?scope={scope}'
            f'&client_id={client_id}'
            f'&response_type=code'
            f'&redirect_uri={redirect_uri}'
            f'&access_type=offline'
        )

    def exchange_oauth_code(self, account, code):
        client_id = account.oauth_client_id
        client_secret = account._get_oauth_client_secret()
        redirect_uri = account.oauth_redirect_uri
        accounts_url = self._get_accounts_url(account)

        resp = requests.post(f'{accounts_url}/oauth/v2/token', data={
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
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
        client_secret = account._get_oauth_client_secret()
        refresh_token = account._get_oauth_refresh_token()
        accounts_url = self._get_accounts_url(account)
        if not refresh_token:
            return False
        try:
            resp = requests.post(f'{accounts_url}/oauth/v2/token', data={
                'grant_type': 'refresh_token',
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
            }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
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
            _logger.error("Zoho token refresh failed: %s", e)
            account.state = 'expired'
            return False

    def create_meeting(self, meeting):
        account = meeting.provider_account_id
        if not account:
            return self._generate_basic_link(meeting)
        headers = self._get_headers(account)
        api_url = self._get_api_url(account)
        body = {
            'session_name': meeting.name,
            'duration': meeting.duration_minutes or 60,
        }
        resp = requests.post(
            f'{api_url}/sessions',
            headers=headers, json=body, timeout=30,
        )
        if resp.status_code == 401 and self.refresh_token(account):
            headers = self._get_headers(account)
            resp = requests.post(
                f'{api_url}/sessions',
                headers=headers, json=body, timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        return {
            'join_url': data.get('join_link', '') or data.get('join_url', ''),
            'start_url': data.get('start_link', '') or data.get('host_url', ''),
            'provider_meeting_id': str(data.get('session_id', '')),
            'password': data.get('password', ''),
        }

    def _generate_basic_link(self, meeting):
        meeting_id = str(uuid.uuid4())
        return {
            'join_url': f'https://meeting.zoho.com/join/{meeting_id}',
            'start_url': f'https://meeting.zoho.com/host/{meeting_id}',
            'provider_meeting_id': meeting_id,
        }

    def update_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return True
        account = meeting.provider_account_id
        if not account:
            return True
        headers = self._get_headers(account)
        api_url = self._get_api_url(account)
        body = {'session_name': meeting.name, 'duration': meeting.duration_minutes or 60}
        url = f"{api_url}/sessions/{meeting.provider_meeting_id}"
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
        api_url = self._get_api_url(account)
        url = f"{api_url}/sessions/{meeting.provider_meeting_id}"
        try:
            resp = requests.delete(url, headers=headers, timeout=30)
            if resp.status_code == 401 and self.refresh_token(account):
                headers = self._get_headers(account)
                resp = requests.delete(url, headers=headers, timeout=30)
        except Exception as e:
            _logger.warning("Zoho delete failed: %s", e)
        return True

    def get_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return None
        account = meeting.provider_account_id
        if not account:
            return None
        headers = self._get_headers(account)
        api_url = self._get_api_url(account)
        try:
            resp = requests.get(
                f"{api_url}/sessions/{meeting.provider_meeting_id}",
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
        api_url = self._get_api_url(account)
        try:
            resp = requests.get(
                f'{api_url}/sessions',
                headers=headers, timeout=15,
            )
            return resp.status_code == 200
        except Exception:
            return False
