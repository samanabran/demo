# -*- coding: utf-8 -*-
##############################################################################
#    SGC - Unified Video Conferencing
#    Copyright (C) 2026 SGC TECH AI (https://sgctech.ai)
#    Licensed under the Odoo Proprietary License v1.0 (OPL-1)
##############################################################################
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class VideoConferenceController(http.Controller):
    @http.route('/video_conference/oauth/callback', type='http', auth='user', methods=['GET'], csrf=False)
    def oauth_callback(self, **kwargs):
        """Handle OAuth 2.0 callback from providers"""
        code = kwargs.get('code')
        state = kwargs.get('state', '')
        error = kwargs.get('error', '')
        if error:
            return self._oauth_error_response(error)
        if not code:
            return self._oauth_error_response('No authorization code received')
        # Find the account waiting for OAuth (stored in context/session)
        account_id = request.session.get('oauth_account_id')
        if not account_id:
            return self._oauth_error_response('No pending OAuth account found')
        account = request.env['video.provider.account'].sudo().browse(account_id)
        if not account.exists():
            return self._oauth_error_response('Account not found')
        try:
            # Exchange the code for tokens using the provider service
            from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry
            service = ProviderRegistry.get_service(account.provider_id.code, request.env)
            if service and hasattr(service, 'exchange_oauth_code'):
                service.exchange_oauth_code(account, code)
            else:
                return self._oauth_error_response(f'OAuth not supported for {account.provider_id.name}')
            request.session.pop('oauth_account_id', None)
            # Log audit
            request.env['video.audit.log'].sudo().log_action(
                'oauth_callback',
                model='video.provider.account',
                res_id=account.id,
                provider_id=account.provider_id.id,
                description=f'OAuth authorization completed for {account.provider_id.name}',
                result='success',
            )
            return """
            <html>
            <head><title>OAuth Success</title></head>
            <body>
                <h2>Authorization Successful</h2>
                <p>Your provider account has been configured successfully.</p>
                <p>You can close this window and return to Odoo.</p>
                <script>window.close();</script>
            </body>
            </html>
            """
        except Exception as e:
            _logger.error("OAuth callback error: %s", e)
            request.env['video.audit.log'].sudo().log_action(
                'oauth_callback',
                model='video.provider.account',
                res_id=account.id,
                provider_id=account.provider_id.id,
                description=f'OAuth authorization failed: {str(e)}',
                result='failure',
                error_message=str(e),
            )
            return self._oauth_error_response(str(e))

    def _oauth_error_response(self, message):
        return request.render('sgc_video_conferencing.oauth_error_page', {
            'error_message': message,
        })

    @http.route('/video_conference/oauth/authorize', type='http', auth='user', methods=['GET'], csrf=False)
    def oauth_authorize(self, **kwargs):
        """Initiate OAuth flow for a provider account"""
        account_id = kwargs.get('account_id')
        if not account_id:
            return self._oauth_error_response('No account ID provided')
        account = request.env['video.provider.account'].sudo().browse(int(account_id))
        if not account.exists():
            return self._oauth_error_response('Account not found')
        from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry
        service = ProviderRegistry.get_service(account.provider_id.code, request.env)
        if not service or not hasattr(service, 'get_oauth_url'):
            return self._oauth_error_response(f'OAuth not supported for {account.provider_id.name}')
        oauth_url = service.get_oauth_url(account)
        if not oauth_url:
            return self._oauth_error_response('Failed to generate OAuth URL')
        request.session['oauth_account_id'] = account.id
        return request.redirect(oauth_url)

    @http.route('/video_conference/webhook/<string:provider_code>', type='jsonrpc', auth='none', methods=['POST'], csrf=False)
    def webhook_handler(self, provider_code, **kwargs):
        """Handle webhooks from providers (meeting ended, recording ready, etc.)"""
        data = request.jsonrequest
        _logger.info("Webhook received from %s: %s", provider_code, json.dumps(data)[:500])
        # Process based on provider
        if provider_code == 'zoom':
            self._process_zoom_webhook(data)
        elif provider_code == 'webex':
            self._process_webex_webhook(data)
        elif provider_code == 'microsoft_teams':
            self._process_teams_webhook(data)
        return {'status': 'ok'}

    def _process_zoom_webhook(self, data):
        event = data.get('event', '')
        payload = data.get('payload', {})
        meeting_id = str(payload.get('object', {}).get('id', ''))
        meeting = request.env['video.meeting'].sudo().search([
            ('provider_meeting_id', '=', meeting_id),
        ], limit=1)
        if not meeting:
            return
        if 'meeting.ended' in event:
            meeting.status = 'completed'
            # Import recordings
            meeting._get_provider_service().get_recordings(meeting)

    def _process_webex_webhook(self, data):
        meeting_id = data.get('data', {}).get('meetingId', '')
        meeting = request.env['video.meeting'].sudo().search([
            ('provider_meeting_id', '=', meeting_id),
        ], limit=1)
        if meeting:
            meeting.status = 'completed'

    def _process_teams_webhook(self, data):
        meeting_id = data.get('meetingId', '')
        meeting = request.env['video.meeting'].sudo().search([
            ('provider_meeting_id', '=', meeting_id),
        ], limit=1)
        if meeting:
            meeting.status = 'completed'
