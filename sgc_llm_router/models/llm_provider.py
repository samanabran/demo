import logging

import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SgcLlmProvider(models.Model):
    _name = 'sgc.llm.provider'
    _description = 'LLM Provider (chat-completion routing entry)'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10, help='Lower numbers are tried first.')
    active = fields.Boolean(default=True)

    provider_type = fields.Selection(
        [
            ('opencode', 'OpenCode'),
            ('mistral', 'Mistral'),
            ('groq', 'Groq'),
        ],
        required=True,
    )

    # No hardcoded default for base_url: Mistral and Groq's OpenAI-compatible
    # endpoints are stable and well-documented, but OpenCode's gateway
    # endpoint moves fast enough that a baked-in guess here would be more
    # likely to silently break than to help. Verify each URL against the
    # provider's current docs before saving a real key against it.
    base_url = fields.Char(
        required=True,
        help='Full chat-completions endpoint URL for this provider.',
    )
    model_id = fields.Char(
        required=True,
        help='Exact model slug/ID as the provider expects it in the request payload.',
    )
    api_key = fields.Char(
        string='API Key',
        help='Bearer token sent as `Authorization: Bearer <api_key>`. Enter this value yourself in the UI -- never pre-filled by automation.',
    )
    timeout = fields.Integer(default=30, help='Request timeout, in seconds.')

    last_used = fields.Datetime(readonly=True, copy=False)
    last_error = fields.Text(readonly=True, copy=False)

    def _chat_completion_single(self, messages, **kwargs):
        """Call this provider's chat-completions endpoint once. Raises on
        any failure (network, timeout, non-2xx, malformed response) --
        callers are expected to catch and move to the next provider."""
        self.ensure_one()
        payload = {'model': self.model_id, 'messages': messages}
        payload.update(kwargs)
        headers = {
            'Authorization': 'Bearer %s' % (self.api_key or ''),
            'Content-Type': 'application/json',
        }
        response = requests.post(
            self.base_url,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']

    @api.model
    def chat_completion(self, messages, **kwargs):
        """Try each active provider in sequence order; return the first
        success. Raises UserError listing every failure if all providers
        are exhausted (or none are configured)."""
        providers = self.search([('active', '=', True)], order='sequence, id')
        if not providers:
            raise UserError('No active sgc.llm.provider records configured.')

        errors = []
        for provider in providers:
            try:
                result = provider._chat_completion_single(messages, **kwargs)
                provider.write({'last_used': fields.Datetime.now(), 'last_error': False})
                return result
            except Exception as exc:  # noqa: BLE001 -- deliberately broad: any
                # failure mode (network, auth, timeout, malformed response)
                # should fall through to the next provider, not abort the chain.
                _logger.warning(
                    'sgc.llm.provider %s (%s) failed, trying next fallback: %s',
                    provider.name, provider.provider_type, exc,
                )
                provider.write({'last_error': str(exc)})
                errors.append('%s: %s' % (provider.name, exc))

        raise UserError(
            'All configured LLM providers failed:\n' + '\n'.join(errors)
        )
