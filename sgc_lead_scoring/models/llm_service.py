# -*- coding: utf-8 -*-

import requests
import json
import time
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class LlmService(models.Model):
    _name = 'llm.service'
    _description = 'LLM Service'

    name = fields.Char(string='Name')
    provider_id = fields.Many2one('llm.provider', string='Provider', required=True)
    active = fields.Boolean(string='Active', default=True)

    _scoring_weights_cache = None

    @api.model
    def _get_api_url(self, provider):
        if provider.provider_type == 'custom' and provider.api_endpoint:
            return provider.api_endpoint.rstrip('/') + '/chat/completions'
        urls = {
            'openai': 'https://api.openai.com/v1/chat/completions',
            'groq': 'https://api.groq.com/openai/v1/chat/completions',
            'anthropic': 'https://api.anthropic.com/v1/messages',
            'mistral': 'https://api.mistral.ai/v1/chat/completions',
            'huggingface': f'https://api-inference.huggingface.co/models/{provider.model_name}',
            'google': f'https://generativelanguage.googleapis.com/v1/models/{provider.model_name}:generateContent',
        }
        return urls.get(provider.provider_type, '')

    @api.model
    def _get_headers(self, provider):
        if provider.provider_type == 'anthropic':
            return {
                'x-api-key': provider.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json',
            }
        if provider.provider_type == 'google':
            params = {'key': provider.api_key}
            return {'Content-Type': 'application/json'}
        return {
            'Authorization': f'Bearer {provider.api_key}',
            'Content-Type': 'application/json',
        }

    @api.model
    def _get_payload(self, provider, messages):
        if provider.provider_type == 'anthropic':
            return {
                'model': provider.model_name,
                'messages': messages,
                'max_tokens': provider.max_tokens or 2000,
                'temperature': provider.temperature or 0.7,
            }
        if provider.provider_type == 'google':
            return {
                'contents': [{'parts': [{'text': m['content']}]} for m in messages],
                'generationConfig': {
                    'maxOutputTokens': provider.max_tokens or 2000,
                    'temperature': provider.temperature or 0.7,
                },
            }
        if provider.provider_type == 'huggingface':
            return {
                'inputs': messages[-1]['content'] if messages else '',
                'parameters': {
                    'max_new_tokens': provider.max_tokens or 2000,
                    'temperature': provider.temperature or 0.7,
                },
            }
        return {
            'model': provider.model_name,
            'messages': messages,
            'max_tokens': provider.max_tokens or 2000,
            'temperature': provider.temperature or 0.7,
        }

    @api.model
    def _parse_response(self, provider, response_data):
        if provider.provider_type == 'anthropic':
            content = ''
            for block in response_data.get('content', []):
                if block.get('type') == 'text':
                    content += block.get('text', '')
            return content
        if provider.provider_type == 'google':
            candidates = response_data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                return ' '.join(p.get('text', '') for p in parts)
            return ''
        if provider.provider_type == 'huggingface':
            if isinstance(response_data, list):
                return response_data[0].get('generated_text', '') if response_data else ''
            return response_data.get('generated_text', '')
        choices = response_data.get('choices', [])
        if choices:
            return choices[0].get('message', {}).get('content', '')
        return ''

    @api.model
    def call_llm(self, messages, provider=None, max_retries=3):
        if not provider:
            provider = self.env['llm.provider'].get_default_provider()
        if not provider:
            return {
                'success': False,
                'content': '',
                'error': 'No LLM provider configured',
                'retries': 0,
            }

        url = self._get_api_url(provider)
        headers = self._get_headers(provider)
        payload = self._get_payload(provider, messages)

        timeout = provider.timeout or 30

        for attempt in range(max_retries + 1):
            try:
                if provider.provider_type == 'google':
                    params = {'key': provider.api_key}
                    response = requests.post(
                        url, headers=headers, json=payload,
                        params=params, timeout=timeout
                    )
                else:
                    response = requests.post(
                        url, headers=headers, json=payload, timeout=timeout
                    )

                if response.status_code == 200:
                    data = response.json()
                    content = self._parse_response(provider, data)
                    provider.write({
                        'total_requests': provider.total_requests + 1,
                        'last_used': fields.Datetime.now(),
                    })
                    return {
                        'success': True,
                        'content': content,
                        'error': '',
                        'retries': attempt,
                    }

                if response.status_code == 429 and attempt < max_retries:
                    _logger.warning(
                        'Rate limited (429) on attempt %d/%d for provider %s. Retrying...',
                        attempt + 1, max_retries, provider.name
                    )
                    time.sleep(2 ** attempt)
                    continue

                if response.status_code == 429:
                    provider.write({
                        'failed_requests': provider.failed_requests + 1,
                    })
                    return {
                        'success': False,
                        'content': '',
                        'error': f'Rate limit exceeded after {max_retries} retries',
                        'retries': attempt,
                    }

                provider.write({
                    'failed_requests': provider.failed_requests + 1,
                })
                return {
                    'success': False,
                    'content': '',
                    'error': f'API Error {response.status_code}: {response.text}',
                    'retries': attempt,
                }

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    _logger.warning(
                        'Timeout on attempt %d/%d for provider %s. Retrying...',
                        attempt + 1, max_retries, provider.name
                    )
                    continue
                provider.write({
                    'failed_requests': provider.failed_requests + 1,
                })
                return {
                    'success': False,
                    'content': '',
                    'error': f'Request timed out after {timeout}s and {max_retries} retries',
                    'retries': attempt,
                }

            except requests.exceptions.RequestException as e:
                provider.write({
                    'failed_requests': provider.failed_requests + 1,
                })
                return {
                    'success': False,
                    'content': '',
                    'error': str(e),
                    'retries': attempt,
                }

        provider.write({
            'failed_requests': provider.failed_requests + 1,
        })
        return {
            'success': False,
            'content': '',
            'error': f'Failed after {max_retries} retries',
            'retries': max_retries,
        }

    @api.model
    def _get_scoring_weights(self):
        if LlmService._scoring_weights_cache is not None:
            return LlmService._scoring_weights_cache
        params = self.env['ir.config_parameter'].sudo()
        weights = {
            'completeness': float(params.get_param('llm_lead_scoring.weight_completeness', '30.0')),
            'clarity': float(params.get_param('llm_lead_scoring.weight_clarity', '40.0')),
            'engagement': float(params.get_param('llm_lead_scoring.weight_engagement', '30.0')),
        }
        LlmService._scoring_weights_cache = weights
        return weights

    @api.model
    def _get_config_bool(self, key, default='False'):
        val = self.env['ir.config_parameter'].sudo().get_param(key, default)
        return val.strip().lower() == 'true'

    @api.model
    def clear_caches(self):
        LlmService._scoring_weights_cache = None
