# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import requests
import logging

_logger = logging.getLogger(__name__)

_DEFAULT_API_ENDPOINT = "http://freellmapi-prod:3001/v1/chat/completions"
_DEFAULT_MODEL = "nemotron-3-super-120b"


class SgcAIController(http.Controller):

    @http.route(
        '/sgc_ai_powerbox/get_response',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def get_response(self, **kwargs):
        """Receive prompt from Powerbox, forward to SGC AI backend, return response.

        Context-aware: when invoked from an html_field (the powerbox flow), the
        JS sends a `context` dict with res_model, res_id, record_name, and the
        current field_text. We prepend a system message summarising that
        context so the model can answer with awareness of the open record.
        """
        prompt = (kwargs.get('prompt') or '').strip()
        context = kwargs.get('context') or {}
        if not prompt:
            return {'error': 'No prompt provided.'}

        ICPSudo = request.env['ir.config_parameter'].sudo()
        api_endpoint = ICPSudo.get_param(
            'sgc_ai.api_endpoint', _DEFAULT_API_ENDPOINT
        )
        api_key = ICPSudo.get_param('sgc_ai.api_key', '')
        model = ICPSudo.get_param('sgc_ai.model', _DEFAULT_MODEL)

        if not api_endpoint or not api_key:
            return {
                'error': (
                    'SGC AI not configured. Go to Settings → Technical → '
                    'System Parameters and set sgc_ai.api_endpoint and '
                    'sgc_ai.api_key.'
                )
            }

        messages = self._build_messages(prompt, context)

        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 500,
        }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        try:
            _logger.info(
                'SGC AI → sending to %s (model=%s, ctx=%s)',
                api_endpoint, model,
                {k: v for k, v in context.items() if k != 'field_text'},
            )
            resp = requests.post(
                api_endpoint, json=payload, headers=headers, timeout=60
            )
            resp.raise_for_status()
            data = resp.json()

            ai_text = ''
            choices = data.get('choices', [])
            if choices:
                msg = choices[0].get('message', {})
                ai_text = msg.get('content', '')

            if not ai_text:
                ai_text = data.get('content', '') or data.get('response', '') or str(data)

            if not ai_text.strip():
                return {'error': 'AI returned empty response.'}

            return {'response': ai_text.strip()}

        except requests.exceptions.Timeout:
            _logger.error('SGC AI request timed out after 60s')
            return {'error': 'AI service timed out. Try again later.'}
        except requests.exceptions.HTTPError as e:
            _logger.error('SGC AI HTTP error: %s', str(e))
            return {'error': f'AI service returned HTTP {e.response.status_code}.'}
        except requests.exceptions.ConnectionError:
            _logger.error('SGC AI connection failed to %s', api_endpoint)
            return {'error': 'Cannot reach AI service. Check sgc_ai.api_endpoint.'}
        except Exception as e:
            _logger.error('SGC AI unexpected error: %s', str(e))
            return {'error': f'Unexpected error: {str(e)}'}

    def _build_messages(self, prompt, context):
        """Compose the OpenAI-style messages array, optionally prepending a
        context system message describing the open record.
        """
        messages = [{'role': 'user', 'content': prompt}]
        res_model = context.get('res_model')
        res_id = context.get('res_id')
        record_name = context.get('record_name') or ''
        field_text = context.get('field_text') or ''

        if res_model:
            sys_lines = [
                'You are an AI assistant embedded in the Odoo ERP at SGC TECH.',
                f'The user is currently editing record: {res_model}'
                + (f' "{record_name}"' if record_name else '')
                + (f' (id={res_id})' if res_id else ''),
            ]
            if field_text:
                truncated = field_text[:1500]
                sys_lines.append(
                    f'Current field content (first 1500 chars):\n{truncated}'
                )
            sys_lines.append(
                'Use this context to make answers specific to the open record. '
                'Keep responses concise and ready to paste into a form field.'
            )
            messages = [
                {'role': 'system', 'content': '\n\n'.join(sys_lines)},
                *messages,
            ]
        return messages