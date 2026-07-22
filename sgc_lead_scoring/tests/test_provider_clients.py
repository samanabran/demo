# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase


class TestProviderClients(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['web.research.provider'].search([]).unlink()
        # These tests exercise Tavily/Exa/Google directly; opt in past the
        # master kill switch (Task 1) so get_available_chain() doesn't
        # silently restrict the chain to searxng-only.
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.allow_third_party_search', 'True')
        self.service = self.env['web.research.service']

    def _mock_response(self, status_code, json_data, headers=None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = headers or {}
        return resp

    @patch('requests.post')
    def test_tavily_200_returns_results(self, mock_post):
        provider = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(200, {
            'results': [{'title': 'Acme', 'url': 'https://acme.com', 'content': 'snippet'}]
        })
        result = self.service.search('acme corp', providers=['tavily'])
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Acme')
        self.assertEqual(provider.total_requests, 1)
        self.assertEqual(provider.failed_requests, 0)

    @patch('requests.post')
    def test_tavily_429_marks_failure_no_crash(self, mock_post):
        provider = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(429, {}, headers={'Retry-After': '30'})
        result = self.service.search('acme corp', providers=['tavily'])
        self.assertFalse(result['success'])
        self.assertEqual(provider.failed_requests, 1)

    @patch('requests.post')
    def test_tavily_500_marks_failure(self, mock_post):
        provider = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(500, {})
        result = self.service.search('acme corp', providers=['tavily'])
        self.assertFalse(result['success'])
        self.assertEqual(provider.failed_requests, 1)

    @patch('requests.post')
    def test_exa_200_returns_results(self, mock_post):
        self.env['web.research.provider'].create({
            'name': 'Exa', 'provider_type': 'exa', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(200, {
            'results': [{'title': 'Beta Inc', 'url': 'https://beta.com', 'text': 'snippet'}]
        })
        result = self.service.search('beta inc', providers=['exa'])
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Beta Inc')

    @patch('requests.get')
    def test_searxng_200_returns_results(self, mock_get):
        self.env['web.research.provider'].create({
            'name': 'SearXNG', 'provider_type': 'searxng',
            'base_url': 'https://searxng.example.com/search', 'active': True,
        })
        mock_get.return_value = self._mock_response(200, {
            'results': [{'title': 'Gamma LLC', 'url': 'https://gamma.com', 'content': 'snippet'}]
        })
        result = self.service.search('gamma llc', providers=['searxng'])
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Gamma LLC')

    @patch('requests.get')
    def test_google_401_marks_failure(self, mock_get):
        self.env['web.research.provider'].create({
            'name': 'Google', 'provider_type': 'google', 'api_key': 'bad-key',
            'search_engine_id': 'eid', 'active': True,
        })
        mock_get.return_value = self._mock_response(401, {})
        result = self.service.search('delta corp', providers=['google'])
        self.assertFalse(result['success'])

    @patch('requests.get')
    def test_search_google_custom_compat_shim(self, mock_get):
        self.env['web.research.provider'].create({
            'name': 'Google', 'provider_type': 'google', 'api_key': 'k',
            'search_engine_id': 'eid', 'active': True,
        })
        mock_get.return_value = self._mock_response(200, {
            'items': [{'title': 'Epsilon', 'link': 'https://epsilon.com', 'snippet': 'snippet'}]
        })
        result = self.service.search_google_custom('epsilon corp', num_results=3)
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Epsilon')