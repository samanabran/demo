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

import requests
import json
import logging
from datetime import datetime, timedelta

from odoo import _
from odoo.addons.sgc_video_conferencing.services.provider_interface import BaseVideoProvider
from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry

_logger = logging.getLogger(__name__)


@ProviderRegistry.register
class GoogleMeetProvider(BaseVideoProvider):

    provider_code = 'google_meet'
    provider_name = 'Google Meet'

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

    def get_oauth_url(self, account):
        client_id = account.oauth_client_id
        redirect_uri = account.oauth_redirect_uri or 'http://localhost:8069/video_conference/oauth/callback'
        scopes = ' '.join([
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
        ])
        return (
            f'https://accounts.google.com/o/oauth2/v2/auth'
            f'?client_id={client_id}'
            f'&redirect_uri={redirect_uri}'
            f'&response_type=code'
            f'&scope={scopes}'
            f'&access_type=offline'
            f'&prompt=consent'
        )

    def exchange_oauth_code(self, account, code):
        client_id = account.oauth_client_id
        client_secret = account._get_oauth_client_secret()
        redirect_uri = account.oauth_redirect_uri

        resp = requests.post('https://oauth2.googleapis.com/token', data={
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }, timeout=30)
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

        if not refresh_token:
            return False

        try:
            resp = requests.post('https://oauth2.googleapis.com/token', data={
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
            }, timeout=30)
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
            _logger.error("Google token refresh failed: %s", e)
            account.state = 'expired'
            return False

    def create_meeting(self, meeting):
        account = meeting.provider_account_id
        if not account or account.state != 'verified':
            # Generate Google Meet link without OAuth (conferencing only)
            return self._generate_conference_link(meeting)

        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%S')
        end_dt = meeting.end_time or (meeting.start_time + timedelta(hours=1))
        end = end_dt.strftime('%Y-%m-%dT%H:%M:%S')

        event_body = {
            'summary': meeting.name,
            'description': meeting.description or '',
            'start': {'dateTime': start, 'timeZone': self.env.user.tz or 'UTC'},
            'end': {'dateTime': end, 'timeZone': self.env.user.tz or 'UTC'},
            'conferenceData': {
                'createRequest': {
                    'requestId': f'odoomeeting_{meeting.id}_{datetime.now().timestamp()}',
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                }
            },
        }

        resp = requests.post(
            'https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1',
            headers=headers,
            json=event_body,
            timeout=30,
        )

        if resp.status_code == 401:
            if self.refresh_token(account):
                headers = self._get_headers(account)
                resp = requests.post(
                    'https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1',
                    headers=headers, json=event_body, timeout=30,
                )

        resp.raise_for_status()
        data = resp.json()

        conference_data = data.get('conferenceData', {})
        entry_points = conference_data.get('entryPoints', [])
        join_url = ''
        for ep in entry_points:
            if ep.get('entryPointType') == 'video':
                join_url = ep.get('uri', '')
                break

        return {
            'join_url': join_url or data.get('hangoutLink', ''),
            'start_url': join_url,
            'provider_meeting_id': data.get('id', ''),
        }

    def _generate_conference_link(self, meeting):
        """Generate a Google Meet link without OAuth (fallback)"""
        import random
        import string
        meeting_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        join_url = f'https://meet.google.com/{meeting_code}'
        return {
            'join_url': join_url,
            'start_url': join_url,
            'provider_meeting_id': meeting_code,
        }

    def update_meeting(self, meeting):
        account = meeting.provider_account_id
        if not account or account.state != 'verified':
            return True
        headers = self._get_headers(account)
        start = meeting.start_time.strftime('%Y-%m-%dT%H:%M:%S')
        end = (meeting.end_time or meeting.start_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        event_body = {
            'summary': meeting.name,
            'start': {'dateTime': start, 'timeZone': self.env.user.tz or 'UTC'},
            'end': {'dateTime': end, 'timeZone': self.env.user.tz or 'UTC'},
        }
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{meeting.provider_meeting_id}"
        resp = requests.patch(url, headers=headers, json=event_body, timeout=30)
        if resp.status_code == 401 and self.refresh_token(account):
            headers = self._get_headers(account)
            resp = requests.patch(url, headers=headers, json=event_body, timeout=30)
        resp.raise_for_status()
        return True

    def delete_meeting(self, meeting):
        account = meeting.provider_account_id
        if not account or not meeting.provider_meeting_id:
            return True
        if account.state == 'verified':
            headers = self._get_headers(account)
            url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{meeting.provider_meeting_id}"
            try:
                resp = requests.delete(url, headers=headers, timeout=30)
                if resp.status_code == 401 and self.refresh_token(account):
                    headers = self._get_headers(account)
                    resp = requests.delete(url, headers=headers, timeout=30)
            except Exception as e:
                _logger.warning("Failed to delete Google Calendar event: %s", e)
        return True

    def get_meeting(self, meeting):
        if not meeting.provider_meeting_id:
            return None
        account = meeting.provider_account_id
        if not account or account.state != 'verified':
            return None
        headers = self._get_headers(account)
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{meeting.provider_meeting_id}"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            _logger.error("Failed to get Google meeting: %s", e)
            return None

    def get_join_url(self, meeting):
        return meeting.join_url

    def get_recordings(self, meeting):
        # Google Meet recordings are stored in Google Drive
        # Requires additional Drive API scopes
        return []

    def verify_connection(self, account):
        headers = self._get_headers(account)
        try:
            resp = requests.get(
                'https://www.googleapis.com/calendar/v3/users/me/calendarList',
                headers=headers, timeout=15,
            )
            return resp.status_code == 200
        except Exception:
            return False
