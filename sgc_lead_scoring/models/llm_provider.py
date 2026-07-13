# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LlmProvider(models.Model):
    _name = 'llm.provider'
    _description = 'LLM Provider'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    provider_type = fields.Selection([
        ('openai', 'OpenAI'),
        ('groq', 'Groq'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google Gemini'),
        ('huggingface', 'HuggingFace'),
        ('mistral', 'Mistral AI'),
        ('custom', 'Custom Endpoint'),
    ], string='Provider Type', required=True, default='openai')
    model_name = fields.Char(string='Model Name', required=True,
                             help='The model identifier (e.g. gpt-4, llama-3.3-70b)')
    api_key = fields.Char(string='API Key', required=True,
                          help='API authentication key')
    api_endpoint = fields.Char(string='Custom API Endpoint',
                               help='Base URL for custom API endpoint')
    temperature = fields.Float(string='Temperature', default=0.7,
                               help='Model temperature (0.0 - 1.0)')
    max_tokens = fields.Integer(string='Max Tokens', default=2000)
    timeout = fields.Integer(string='Timeout (seconds)', default=30)
    is_default = fields.Boolean(string='Default Provider',
                                help='Use as default provider for lead scoring')
    active = fields.Boolean(string='Active', default=True)
    total_requests = fields.Integer(string='Total Requests', default=0, readonly=True)
    failed_requests = fields.Integer(string='Failed Requests', default=0, readonly=True)
    last_used = fields.Datetime(string='Last Used', readonly=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    @api.model
    def get_default_provider(self):
        """Get the default active provider"""
        return self.search([('is_default', '=', True), ('active', '=', True)], limit=1)
