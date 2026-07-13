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

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import config as odoo_config
import logging

_logger = logging.getLogger(__name__)


class VideoProvider(models.Model):
    _name = 'video.provider'
    _description = 'Video Conferencing Provider'
    _order = 'sequence, name'

    name = fields.Char(
        string='Provider Name',
        required=True,
        translate=True,
        help="Name of the video conferencing provider (e.g., Google Meet, Microsoft Teams, Zoom)"
    )
    code = fields.Char(
        string='Provider Code',
        required=True,
        help="Unique code for the provider (e.g., google_meet, microsoft_teams, zoom)"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order in which the provider is displayed"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the provider is active and can be used"
    )
    description = fields.Html(
        string='Description',
        help="Description of the provider and its features"
    )
    icon = fields.Binary(
        string='Icon',
        attachment=True,
        help="Provider icon (optional)"
    )
    provider_type = fields.Selection([
        ('google_meet', 'Google Meet'),
        ('microsoft_teams', 'Microsoft Teams'),
        ('zoom', 'Zoom'),
        ('webex', 'Cisco Webex'),
        ('jitsi', 'Jitsi Meet'),
        ('zoho', 'Zoho Meeting'),
        ('gotomeeting', 'GoTo Meeting'),
        ('other', 'Other')
    ], string='Provider Type', required=True, help="Type of provider for specific implementations")
    config_template = fields.Text(
        string='Configuration Template',
        help="JSON template for provider-specific configuration fields"
    )
    documentation_url = fields.Char(
        string='Documentation URL',
        help="Link to provider's API documentation"
    )
    website_url = fields.Char(
        string='Website URL',
        help="Provider's official website"
    )
    account_ids = fields.One2many(
        'video.provider.account',
        'provider_id',
        string='Accounts',
        help='Authenticated accounts for this provider'
    )

    _check_code_unique = models.Constraint(
        'unique(code)',
        'Provider code must be unique!',
    )
    _check_name_unique = models.Constraint(
        'unique(name)',
        'Provider name must be unique!',
    )

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if not record.code.replace('_', '').isalnum():
                raise ValidationError(_("Provider code must contain only alphanumeric characters and underscores."))

    @api.model
    def get_provider_by_code(self, code):
        """Get provider record by code"""
        return self.search([('code', '=', code), ('active', '=', True)], limit=1)

    def name_get(self):
        result = []
        for record in self:
            name = '[%s] %s' % (record.code, record.name)
            result.append((record.id, name))
        return result
