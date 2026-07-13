# -*- coding: utf-8 -*-

import requests
import json

from odoo import models, fields, api, _


class WebResearchService(models.Model):
    _name = 'web.research.service'
    _description = 'Web Research Service'

    name = fields.Char(string='Name')

    def search_google_custom(self, query, num_results=5):
        """Search using Google Custom Search API.
        
        This is a minimal stub for module installation purposes.
        Full implementation requires google-api-python-client.
        """
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('llm_lead_scoring.google_search_api_key', '')
        search_engine_id = config.get_param('llm_lead_scoring.google_search_engine_id', '')

        if not api_key or not search_engine_id:
            return {
                'success': False,
                'error': 'Google Custom Search not configured. Set API Key and Search Engine ID in settings.',
                'results': [],
            }

        try:
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': min(num_results, 10),
            }
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                })

            return {
                'success': True,
                'results': results,
                'error': None,
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'results': [],
            }
