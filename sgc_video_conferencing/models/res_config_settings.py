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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # General settings
    video_conference_enabled = fields.Boolean(
        string='Enable Video Conferencing',
        default=True,
        help='Global switch to enable/disable video conferencing features'
    )
    auto_create_meeting_links = fields.Boolean(
        string='Auto-create Meeting Links',
        default=True,
        help='Automatically generate meeting links when scheduling events'
    )
    send_invitation_automatically = fields.Boolean(
        string='Send Invitations Automatically',
        default=False,
        help='Automatically send meeting invitations when meetings are created'
    )
    meeting_default_duration = fields.Integer(
        string='Default Meeting Duration (min)',
        default=60,
        help='Default duration for new meetings in minutes'
    )
    max_meeting_duration = fields.Integer(
        string='Max Meeting Duration (min)',
        default=480,
        help='Maximum allowed meeting duration in minutes'
    )
    enable_recording_auto_import = fields.Boolean(
        string='Auto-import Recordings',
        default=False,
        help='Automatically import recordings from provider after meeting ends'
    )

    # Security settings
    enforce_encrypted_credentials = fields.Boolean(
        string='Enforce Encrypted Credentials',
        default=True,
        help='Require encryption for all stored credentials'
    )
    audit_log_enabled = fields.Boolean(
        string='Enable Audit Logging',
        default=True,
        help='Log all video conferencing actions for security auditing'
    )
    audit_log_retention_days = fields.Integer(
        string='Audit Log Retention (days)',
        default=365,
        help='Number of days to keep audit logs'
    )

    # OAuth settings
    oauth_token_refresh_enabled = fields.Boolean(
        string='Auto-refresh Tokens',
        default=True,
        help='Automatically refresh OAuth tokens before expiry'
    )
    oauth_token_refresh_threshold = fields.Integer(
        string='Token Refresh Threshold (min)',
        default=30,
        help='Refresh token when less than this many minutes remain before expiry'
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            video_conference_enabled=params.get_param('sgc_video_conferencing.enabled', 'True') == 'True',
            auto_create_meeting_links=params.get_param('sgc_video_conferencing.auto_create_links', 'True') == 'True',
            send_invitation_automatically=params.get_param('sgc_video_conferencing.auto_send_invite', 'False') == 'True',
            meeting_default_duration=int(params.get_param('sgc_video_conferencing.default_duration', '60')),
            max_meeting_duration=int(params.get_param('sgc_video_conferencing.max_duration', '480')),
            enable_recording_auto_import=params.get_param('sgc_video_conferencing.auto_import_recordings', 'False') == 'True',
            enforce_encrypted_credentials=params.get_param('sgc_video_conferencing.enforce_encryption', 'True') == 'True',
            audit_log_enabled=params.get_param('sgc_video_conferencing.audit_log_enabled', 'True') == 'True',
            audit_log_retention_days=int(params.get_param('sgc_video_conferencing.audit_log_retention_days', '365')),
            oauth_token_refresh_enabled=params.get_param('sgc_video_conferencing.token_refresh_enabled', 'True') == 'True',
            oauth_token_refresh_threshold=int(params.get_param('sgc_video_conferencing.token_refresh_threshold', '30')),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('sgc_video_conferencing.enabled', str(self.video_conference_enabled))
        params.set_param('sgc_video_conferencing.auto_create_links', str(self.auto_create_meeting_links))
        params.set_param('sgc_video_conferencing.auto_send_invite', str(self.send_invitation_automatically))
        params.set_param('sgc_video_conferencing.default_duration', str(self.meeting_default_duration))
        params.set_param('sgc_video_conferencing.max_duration', str(self.max_meeting_duration))
        params.set_param('sgc_video_conferencing.auto_import_recordings', str(self.enable_recording_auto_import))
        params.set_param('sgc_video_conferencing.enforce_encryption', str(self.enforce_encrypted_credentials))
        params.set_param('sgc_video_conferencing.audit_log_enabled', str(self.audit_log_enabled))
        params.set_param('sgc_video_conferencing.audit_log_retention_days', str(self.audit_log_retention_days))
        params.set_param('sgc_video_conferencing.token_refresh_enabled', str(self.oauth_token_refresh_enabled))
        params.set_param('sgc_video_conferencing.token_refresh_threshold', str(self.oauth_token_refresh_threshold))
