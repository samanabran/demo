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

from odoo import _
from odoo.addons.sgc_video_conferencing.services.provider_interface import BaseVideoProvider
from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry

_logger = logging.getLogger(__name__)


@ProviderRegistry.register
class JitsiMeetProvider(BaseVideoProvider):

    provider_code = 'jitsi'
    provider_name = 'Jitsi Meet'

    @property
    def supports_oauth(self):
        return False

    @property
    def supports_recordings(self):
        return False

    def _get_domain(self, account=None):
        if account and account.jitsi_domain:
            return account.jitsi_domain
        return 'meet.jit.si'

    def create_meeting(self, meeting):
        account = meeting.provider_account_id
        domain = self._get_domain(account)
        meeting_id = meeting.provider_meeting_id or str(uuid.uuid4()).split('-')[0]
        join_url = f'https://{domain}/{meeting_id}'
        return {
            'join_url': join_url,
            'start_url': join_url,
            'provider_meeting_id': meeting_id,
        }

    def update_meeting(self, meeting):
        return True

    def delete_meeting(self, meeting):
        return True

    def get_meeting(self, meeting):
        return {
            'id': meeting.provider_meeting_id,
            'join_url': meeting.join_url,
        }

    def get_join_url(self, meeting):
        return meeting.join_url

    def verify_connection(self, account):
        return True  # Jitsi is serverless, always available

    def get_oauth_url(self, account):
        return None
