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
from cryptography.fernet import Fernet
from odoo.tools import config
import base64
import hashlib
import json
import logging

_logger = logging.getLogger(__name__)


class VideoProviderAccount(models.Model):
    _name = 'video.provider.account'
    _description = 'Video Provider Account'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Account Name',
        required=True,
        tracking=True,
        help="Human-readable name for this account (e.g., 'Company Google Workspace')"
    )
    provider_id = fields.Many2one(
        'video.provider',
        string='Provider',
        required=True,
        tracking=True,
        help="Video conferencing provider"
    )
    provider_type = fields.Selection(
        related='provider_id.provider_type',
        string='Provider Type',
        store=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether this account is active"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verified', 'Verified'),
        ('error', 'Connection Error'),
        ('expired', 'Token Expired'),
    ], string='State', default='draft', tracking=True)
    # Authentication method
    auth_method = fields.Selection([
        ('oauth2', 'OAuth 2.0'),
        ('apikey', 'API Key'),
        ('jwt', 'JWT Token'),
        ('basic', 'Basic Auth'),
    ], string='Authentication Method', default='oauth2', required=True)

    # OAuth 2.0 credentials (encrypted)
    oauth_client_id = fields.Char(
        string='Client ID',
        help='OAuth 2.0 Client ID'
    )
    oauth_client_secret_encrypted = fields.Text(
        string='Client Secret (Encrypted)',
        help='OAuth 2.0 Client Secret (encrypted at rest)'
    )
    oauth_access_token_encrypted = fields.Text(
        string='Access Token (Encrypted)',
        help='OAuth 2.0 Access Token (encrypted at rest)'
    )
    oauth_refresh_token_encrypted = fields.Text(
        string='Refresh Token (Encrypted)',
        help='OAuth 2.0 Refresh Token (encrypted at rest)'
    )
    oauth_token_type = fields.Char(
        string='Token Type',
        default='Bearer'
    )
    oauth_expires_at = fields.Datetime(
        string='Token Expires At',
        help='When the current access token expires'
    )
    oauth_redirect_uri = fields.Char(
        string='Redirect URI',
        help='OAuth 2.0 Redirect URI'
    )

    # API Key credentials (encrypted)
    api_key_encrypted = fields.Text(
        string='API Key (Encrypted)',
        help='API Key (encrypted at rest)'
    )
    api_secret_encrypted = fields.Text(
        string='API Secret (Encrypted)',
        help='API Secret (encrypted at rest)'
    )

    # Provider-specific fields
    tenant_id = fields.Char(
        string='Tenant ID',
        help='Microsoft Teams Tenant ID'
    )
    zoom_account_id = fields.Char(
        string='Zoom Account ID',
        help='Zoom Account ID for Server-to-Server OAuth'
    )
    jitsi_domain = fields.Char(
        string='Jitsi Domain',
        default='meet.jit.si',
        help='Jitsi Meet server domain'
    )
    webex_site_url = fields.Char(
        string='Webex Site URL',
        help='Cisco Webex site URL'
    )
    zoho_accounts_url = fields.Char(
        string='Zoho Accounts URL',
        default='https://accounts.zoho.com',
        help='Zoho Accounts URL (varies by region)'
    )
    goto_consumer_key = fields.Char(
        string='GoTo Consumer Key',
        help='GoTo Meeting consumer key'
    )

    # Additional config as JSON
    additional_config = fields.Text(
        string='Additional Configuration',
        help='Provider-specific additional configuration (JSON format)'
    )

    # Related meetings
    meeting_ids = fields.One2many(
        'video.meeting',
        'provider_account_id',
        string='Meetings',
        help='Meetings created using this account'
    )
    meeting_count = fields.Integer(
        string='Meeting Count',
        compute='_compute_meeting_count',
        store=True
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # User
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )

    # Dates
    last_verified_date = fields.Datetime(
        string='Last Verified',
        help='Last time the connection was verified'
    )
    last_error_message = fields.Text(
        string='Last Error Message',
        help='Last error message from connection verification'
    )

    _check_account_provider_unique = models.Constraint(
        'unique(name, provider_id)',
        'Account name must be unique per provider!',
    )

    # -----------------------------------------------------------------
    # Encryption helpers
    # -----------------------------------------------------------------
    @api.model
    def _get_encryption_key(self):
        """Derive a Fernet key from the database UUID or config secret"""
        # Use database UUID as seed for the encryption key
        db_uuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid', 'default_key')
        # Hash to get exactly 32 url-safe base64 bytes
        key = base64.urlsafe_b64encode(hashlib.sha256(db_uuid.encode()).digest())
        return key

    @api.model
    def _encrypt_value(self, value):
        """Encrypt a string value"""
        if not value:
            return False
        try:
            f = Fernet(self._get_encryption_key())
            return f.encrypt(value.encode()).decode()
        except Exception as e:
            _logger.error("Encryption failed: %s", e)
            return False

    @api.model
    def _decrypt_value(self, encrypted_value):
        """Decrypt an encrypted string value"""
        if not encrypted_value:
            return ''
        try:
            f = Fernet(self._get_encryption_key())
            return f.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            _logger.error("Decryption failed: %s", e)
            return ''

    # -----------------------------------------------------------------
    # Computed fields
    # -----------------------------------------------------------------
    @api.depends('meeting_ids')
    def _compute_meeting_count(self):
        for record in self:
            record.meeting_count = len(record.meeting_ids)

    def name_get(self):
        result = []
        for record in self:
            name = '%s - %s' % (record.provider_id.name, record.name)
            result.append((record.id, name))
        return result

    # -----------------------------------------------------------------
    # OAuth helpers
    # -----------------------------------------------------------------
    def _get_oauth_client_secret(self):
        self.ensure_one()
        return self._decrypt_value(self.oauth_client_secret_encrypted)

    def _get_oauth_access_token(self):
        self.ensure_one()
        return self._decrypt_value(self.oauth_access_token_encrypted)

    def _get_oauth_refresh_token(self):
        self.ensure_one()
        return self._decrypt_value(self.oauth_refresh_token_encrypted)

    def _get_api_key(self):
        self.ensure_one()
        return self._decrypt_value(self.api_key_encrypted)

    def _get_api_secret(self):
        self.ensure_one()
        return self._decrypt_value(self.api_secret_encrypted)

    def _set_oauth_access_token(self, token):
        self.ensure_one()
        self.oauth_access_token_encrypted = self._encrypt_value(token)

    def _set_oauth_refresh_token(self, token):
        self.ensure_one()
        self.oauth_refresh_token_encrypted = self._encrypt_value(token)

    def _set_api_key(self, key):
        self.ensure_one()
        self.api_key_encrypted = self._encrypt_value(key)

    def _set_api_secret(self, secret):
        self.ensure_one()
        self.api_secret_encrypted = self._encrypt_value(secret)

    def is_token_valid(self):
        """Check if the current token is still valid"""
        self.ensure_one()
        if not self.oauth_expires_at:
            return False
        return fields.Datetime.now() < self.oauth_expires_at

    def action_verify_connection(self):
        """Test the connection to the provider"""
        self.ensure_one()
        try:
            from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry
            service = ProviderRegistry.get_service(self.provider_id.code, env=self.env)
            if service and service.verify_connection(self):
                self.write({
                    'state': 'verified',
                    'last_verified_date': fields.Datetime.now(),
                    'last_error_message': False,
                })
            else:
                self.write({
                    'state': 'error',
                    'last_error_message': 'Connection verification failed',
                })
        except Exception as e:
            self.write({
                'state': 'error',
                'last_error_message': str(e),
            })

    def action_revoke_token(self):
        """Revoke the OAuth token"""
        self.ensure_one()
        self.write({
            'oauth_access_token_encrypted': False,
            'oauth_refresh_token_encrypted': False,
            'oauth_expires_at': False,
            'state': 'draft',
        })
