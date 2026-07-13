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

import json
import logging
from datetime import datetime, timedelta

import requests

from odoo import _
from odoo.addons.sgc_video_conferencing.services.provider_interface import BaseVideoProvider
from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry

_logger = logging.getLogger(__name__)


@ProviderRegistry.register
class TeamsProvider(BaseVideoProvider):

    provider_code = 'microsoft_teams'
    provider_name = 'Microsoft Teams'

    @property
    def supports_oauth(self):
        return True

    @property
    def supports_recordings(self):
        return True

    def _get_headers(self, account):
        token = account._get_oauth_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def _get_graph_url(self):
        return 'https://graph.microsoft.com/v1.0'

    def get_oauth_url(self, account):
        client_id = account.oauth_client_id
        redirect_uri = account.oauth_redirect_uri or 'http://localhost:8069/video_conference/oauth/callback'
        tenant_id = account.tenant_id or 'common'
        scopes = ' '.join([
            'OnlineMeetings.ReadWrite',
            'OnlineMeetingArtifact.Read.All',
            'User.Read',
        ])
        return (
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize'
            f'?client_id={client_id}'
            f'&redirect_uri={redirect_uri}'
            f'&response_type=code'
            f'&scope={scopes}'
        )

    def exchange_oauth_code(self, account, code):
        client_id = account.oauth_client_id
        client_secret = account._get_oauth_client_secret()
        redirect_uri = account.oauth_redirect_uri
        tenant_id = account.tenant_id or 'common'

        resp = requests.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
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
        client_secret = account._get_oauth_client_secret()
        refresh_token = account._get_oauth_refresh_token()
        tenant_id = account.tenant_id or 'common'

        if not refresh_token:
            return False

        try:
            resp = requests.post(
                f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token',
                },
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
            _logger.error("Teams token refresh failed: %s", e)
            account.state = 'expired'
            return False

    def create_meeting(self, meeting):
        account = meeting.provider_account_id
        if not account:
            return self._generate_basic_link(meeting)

        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end = (meeting.end_time or meeting.start_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

        body = {
            'startDateTime': start,
            'endDateTime': end,
            'subject': meeting.name,
            'participants': {
                'organizer': {
                    'identity': {},
                    'upn': self.env.user.email or '',
                },
            },
        }

        if meeting.description:
            body['description'] = meeting.description

        resp = requests.post(
            f'{self._get_graph_url()}/me/onlineMeetings',
            headers=headers, json=body, timeout=30,
        )

        if resp.status_code == 401:
            if self.refresh_token(account):
                headers = self._get_headers(account)
                resp = requests.post(
                    f'{self._get_graph_url()}/me/onlineMeetings',
                    headers=headers, json=body, timeout=30,
                )

        resp.raise_for_status()
        data = resp.json()

        return {
            'join_url': data.get('joinUrl', '') or data.get('joinWebUrl', ''),
            'start_url': data.get('joinUrl', ''),
            'provider_meeting_id': data.get('id', ''),
        }

    def _generate_basic_link(self, meeting):
        """Generate a Teams meeting link without Graph API"""
        import uuid
        meeting_id = str(uuid.uuid4())
        return {
            'join_url': f'https://teams.microsoft.com/l/meetup-join/{meeting_id}',
            'start_url': f'https://teams.microsoft.com/l/meetup-join/{meeting_id}',
            'provider_meeting_id': meeting_id,
        }

    def update_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return True
        account = meeting.provider_account_id
        if not account:
            return True
        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end = (meeting.end_time or meeting.start_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        body = {
            'startDateTime': start,
            'endDateTime': end,
            'subject': meeting.name,
        }
        url = f"{self._get_graph_url()}/me/onlineMeetings/{meeting.provider_meeting_id}"
        resp = requests.patch(url, headers=headers, json=body, timeout=30)
        if resp.status_code == 401 and self.refresh_token(account):
            headers = self._get_headers(account)
            resp = requests.patch(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        return True

    def delete_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return True
        account = meeting.provider_account_id
        if not account:
            return True
        headers = self._get_headers(account)
        url = f"{self._get_graph_url()}/me/onlineMeetings/{meeting.provider_meeting_id}"
        try:
            resp = requests.delete(url, headers=headers, timeout=30)
            if resp.status_code == 401 and self.refresh_token(account):
                headers = self._get_headers(account)
                resp = requests.delete(url, headers=headers, timeout=30)
        except Exception as e:
            _logger.warning("Teams delete meeting failed: %s", e)
        return True

    def get_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return None
        account = meeting.provider_account_id
        if not account:
            return None
        headers = self._get_headers(account)
        url = f"{self._get_graph_url()}/me/onlineMeetings/{meeting.provider_meeting_id}"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
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
                f'{self._get_graph_url()}/me',
                headers=headers, timeout=15,
            )
            return resp.status_code == 200
        except Exception:
            return False
