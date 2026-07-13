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
import json
import logging

_logger = logging.getLogger(__name__)


class ProviderSetupWizard(models.TransientModel):
    _name = 'provider.setup.wizard'
    _description = 'Provider Setup Wizard'

    provider_type = fields.Selection([
        ('google_meet', 'Google Meet'),
        ('microsoft_teams', 'Microsoft Teams'),
        ('zoom', 'Zoom'),
        ('webex', 'Cisco Webex'),
        ('jitsi', 'Jitsi Meet'),
        ('zoho', 'Zoho Meeting'),
        ('gotomeeting', 'GoTo Meeting'),
    ], string='Provider', required=True)

    account_name = fields.Char(string='Account Name', required=True, default='Main Account')
    auth_method = fields.Selection([
        ('oauth2', 'OAuth 2.0'),
        ('apikey', 'API Key / JWT'),
    ], string='Authentication Method', default='oauth2', required=True)

    # OAuth fields
    oauth_client_id = fields.Char(string='Client ID')
    oauth_client_secret = fields.Char(string='Client Secret')
    oauth_redirect_uri = fields.Char(string='Redirect URI', default='http://localhost:8069/video_conference/oauth/callback')

    # Provider-specific fields
    tenant_id = fields.Char(string='Tenant ID', help='Microsoft Azure AD Tenant ID')
    zoom_account_id = fields.Char(string='Zoom Account ID', help='Zoom Account ID for Server-to-Server OAuth')
    jitsi_domain = fields.Char(string='Jitsi Domain', default='meet.jit.si')
    webex_site_url = fields.Char(string='Webex Site URL')
    zoho_accounts_url = fields.Char(string='Zoho Accounts URL', default='https://accounts.zoho.com')
    goto_consumer_key = fields.Char(string='GoTo Consumer Key')

    # API key fields
    api_key = fields.Char(string='API Key')
    api_secret = fields.Char(string='API Secret')

    provider_id = fields.Many2one('video.provider', string='Provider (resolved)')

    @api.onchange('provider_type')
    def _onchange_provider_type(self):
        labels = {
            'google_meet': ('Main Google Account', True, False, False),
            'microsoft_teams': ('Main Teams Account', True, False, True),
            'zoom': ('Main Zoom Account', True, True, False),
            'webex': ('Main Webex Account', True, False, False),
            'jitsi': ('Jitsi Server', False, False, False),
            'zoho': ('Main Zoho Account', True, False, False),
            'gotomeeting': ('Main GoTo Account', True, False, False),
        }
        if self.provider_type in labels:
            name, oauth, zoom_acct, tenant = labels[self.provider_type]
            self.account_name = name
            self.auth_method = 'oauth2' if oauth else 'apikey'

    def action_setup(self):
        """Create the provider account with configured credentials"""
        self.ensure_one()

        # Find or create the provider record
        provider = self.env['video.provider'].search([
            ('provider_type', '=', self.provider_type)
        ], limit=1)
        if not provider:
            provider = self.env['video.provider'].create({
                'name': dict(self._fields['provider_type'].selection).get(self.provider_type, self.provider_type),
                'code': self.provider_type,
                'provider_type': self.provider_type,
                'active': True,
            })

        # Create the account
        vals = {
            'name': self.account_name,
            'provider_id': provider.id,
            'auth_method': self.auth_method,
            'oauth_client_id': self.oauth_client_id or '',
            'oauth_redirect_uri': self.oauth_redirect_uri or '',
        }

        if self.auth_method == 'oauth2':
            vals['oauth_client_secret_encrypted'] = self.env['video.provider.account']._encrypt_value(self.oauth_client_secret or '')
        else:
            vals['api_key_encrypted'] = self.env['video.provider.account']._encrypt_value(self.api_key or '')
            vals['api_secret_encrypted'] = self.env['video.provider.account']._encrypt_value(self.api_secret or '')

        # Provider-specific fields
        if self.tenant_id:
            vals['tenant_id'] = self.tenant_id
        if self.zoom_account_id:
            vals['zoom_account_id'] = self.zoom_account_id
        if self.jitsi_domain:
            vals['jitsi_domain'] = self.jitsi_domain
        if self.webex_site_url:
            vals['webex_site_url'] = self.webex_site_url
        if self.zoho_accounts_url:
            vals['zoho_accounts_url'] = self.zoho_accounts_url
        if self.goto_consumer_key:
            vals['goto_consumer_key'] = self.goto_consumer_key

        account = self.env['video.provider.account'].create(vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'video.provider.account',
            'view_mode': 'form',
            'res_id': account.id,
            'target': 'current',
        }

    def action_test_connection(self):
        """Test the connection before saving"""
        account = self._create_account_preview()
        try:
            account.action_verify_connection()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'message': _('Successfully connected to the provider!'),
                    'type': 'success',
                    'sticky': False,
                },
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': False,
                },
            }

    def _create_account_preview(self):
        """Create a temporary account for testing"""
        self.ensure_one()
        provider = self.env['video.provider'].search([
            ('provider_type', '=', self.provider_type)
        ], limit=1)
        if not provider:
            provider = self.env['video.provider'].create({
                'name': 'Temporary Provider',
                'code': f'temp_{self.provider_type}',
                'provider_type': self.provider_type,
                'active': True,
            })
        return self.env['video.provider.account'].create({
            'name': '_test_connection',
            'provider_id': provider.id,
            'auth_method': self.auth_method,
            'oauth_client_id': self.oauth_client_id or '',
            'oauth_client_secret_encrypted': self.env['video.provider.account']._encrypt_value(self.oauth_client_secret or ''),
            'tenant_id': self.tenant_id or '',
            'zoom_account_id': self.zoom_account_id or '',
        })
