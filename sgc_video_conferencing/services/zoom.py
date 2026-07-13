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
class ZoomProvider(BaseVideoProvider):

    provider_code = 'zoom'
    provider_name = 'Zoom'

    @property
    def supports_oauth(self):
        return True

    @property
    def supports_recordings(self):
        return True

    @property
    def supports_recurring_meetings(self):
        return True

    def _get_headers(self, account):
        token = account._get_oauth_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def _get_base_url(self):
        return 'https://api.zoom.us/v2'

    def get_oauth_url(self, account):
        client_id = account.oauth_client_id
        redirect_uri = account.oauth_redirect_uri or 'http://localhost:8069/video_conference/oauth/callback'
        return (
            f'https://zoom.us/oauth/authorize'
            f'?client_id={client_id}'
            f'&redirect_uri={redirect_uri}'
            f'&response_type=code'
            f'&scope=meeting:write meeting:read recording:read'
        )

    def exchange_oauth_code(self, account, code):
        client_id = account.oauth_client_id
        client_secret = account._get_oauth_client_secret()
        redirect_uri = account.oauth_redirect_uri

        resp = requests.post('https://zoom.us/oauth/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }, auth=(client_id, client_secret), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        expires_at = datetime.now() + timedelta(seconds=data.get('expires_in', 3600))
        account._set_oauth_access_token(data['access_token'])
        if data.get('refresh_token'):
            account._set_oauth_refresh_token(data['refresh_token'])
        account.oauth_expires_at = expires_at
        account.state = 'verified'
        return data

    def _generate_jwt(self, account):
        """Generate JWT for Server-to-Server OAuth if configured"""
        client_id = account.oauth_client_id
        client_secret = account._get_oauth_client_secret()
        zoom_account_id = account.zoom_account_id
        if not zoom_account_id:
            return None
        payload = {
            'iss': client_id,
            'sub': zoom_account_id,
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
        }
        # In production, use a proper JWT library
        header = base64.urlsafe_b64encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()).rstrip(b'=').decode()
        body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
        signature = hmac.new(
            client_secret.encode(),
            f'{header}.{body}'.encode(),
            hashlib.sha256
        ).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        return f'{header}.{body}.{sig_b64}'

    def refresh_token(self, account):
        client_id = account.oauth_client_id
        client_secret = account._get_oauth_client_secret()
        refresh_token = account._get_oauth_refresh_token()

        if not refresh_token:
            return False

        try:
            resp = requests.post('https://zoom.us/oauth/token', data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            }, auth=(client_id, client_secret), timeout=30)
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
            _logger.error("Zoom token refresh failed: %s", e)
            account.state = 'expired'
            return False

    def create_meeting(self, meeting):
        account = meeting.provider_account_id
        if not account:
            return self._generate_basic_link(meeting)

        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        meeting_type = 2  # Scheduled
        if meeting.meeting_type == 'instant':
            meeting_type = 1
        elif meeting.is_recurring:
            meeting_type = 8

        body = {
            'topic': meeting.name,
            'type': meeting_type,
            'start_time': start,
            'duration': meeting.duration_minutes or 60,
            'timezone': self.env.user.tz or 'UTC',
            'settings': {
                'host_video': True,
                'participant_video': True,
                'join_before_host': True,
                'mute_upon_entry': False,
                'watermark': False,
                'approval_type': 0,
                'audio': 'both',
                'auto_recording': 'none',
            },
        }

        if meeting.description:
            body['agenda'] = meeting.description[:2000]

        if meeting.is_recurring:
            body['recurrence'] = {
                'type': {'daily': 1, 'weekly': 2, 'monthly': 3}.get(
                    meeting.recurrence_frequency, 1),
                'repeat_interval': meeting.recurrence_interval or 1,
            }

        resp = requests.post(
            f'{self._get_base_url()}/users/me/meetings',
            headers=headers, json=body, timeout=30,
        )

        if resp.status_code == 401:
            if self.refresh_token(account):
                headers = self._get_headers(account)
                resp = requests.post(
                    f'{self._get_base_url()}/users/me/meetings',
                    headers=headers, json=body, timeout=30,
                )

        resp.raise_for_status()
        data = resp.json()

        return {
            'join_url': data.get('join_url', ''),
            'start_url': data.get('start_url', ''),
            'provider_meeting_id': str(data.get('id', '')),
            'password': data.get('password', ''),
        }

    def _generate_basic_link(self, meeting):
        """Generate a Zoom link without API (basic format)"""
        return {
            'join_url': 'https://zoom.us/j/' + str(uuid.uuid4().int)[:11],
            'start_url': 'https://zoom.us/j/' + str(uuid.uuid4().int)[:11],
            'provider_meeting_id': str(uuid.uuid4().int)[:11],
        }

    def update_meeting(self, meeting):
        if not meeting.provider_meeting_id or not meeting.provider_account_id:
            return True
        account = meeting.provider_account_id
        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        body = {
            'topic': meeting.name,
            'start_time': start,
            'duration': meeting.duration_minutes or 60,
            'timezone': self.env.user.tz or 'UTC',
        }
        url = f"{self._get_base_url()}/meetings/{meeting.provider_meeting_id}"
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
        url = f"{self._get_base_url()}/meetings/{meeting.provider_meeting_id}"
        try:
            resp = requests.delete(url, headers=headers, timeout=30)
            if resp.status_code == 401 and self.refresh_token(account):
                headers = self._get_headers(account)
                resp = requests.delete(url, headers=headers, timeout=30)
        except Exception as e:
            _logger.warning("Zoom delete meeting failed: %s", e)
        return True

    def get_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return None
        account = meeting.provider_account_id
        if not account:
            return None
        headers = self._get_headers(account)
        url = f"{self._get_base_url()}/meetings/{meeting.provider_meeting_id}"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_join_url(self, meeting):
        return meeting.join_url

    def get_recordings(self, meeting):
        if not meeting.provider_meeting_id:
            return []
        account = meeting.provider_account_id
        if not account:
            return []
        headers = self._get_headers(account)
        url = f"{self._get_base_url()}/meetings/{meeting.provider_meeting_id}/recordings"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            recordings = []
            for rec in data.get('recording_files', []):
                recordings.append({
                    'recording_url': rec.get('play_url', ''),
                    'download_url': rec.get('download_url', ''),
                    'recording_type': rec.get('recording_type', 'video'),
                    'duration_seconds': rec.get('duration', 0),
                    'file_size_bytes': rec.get('file_size', 0),
                    'file_format': rec.get('file_extension', ''),
                })
            return recordings
        except Exception as e:
            _logger.error("Failed to get Zoom recordings: %s", e)
            return []

    def verify_connection(self, account):
        headers = self._get_headers(account)
        try:
            resp = requests.get(
                f'{self._get_base_url()}/users/me',
                headers=headers, timeout=15,
            )
            return resp.status_code == 200
        except Exception:
            return False
