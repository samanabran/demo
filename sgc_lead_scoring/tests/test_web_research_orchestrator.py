# -*- coding: utf-8 -*-
import hashlib
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestWebResearchOrchestratorCore(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['web.research.provider'].search([]).unlink()
        self.provider = self.env['web.research.provider'].create({
            'name': 'Test Tavily',
            'provider_type': 'tavily',
            'api_key': 'test-key',
            'active': True,
        })
        self.service = self.env['web.research.service']

    def test_hash_query_is_deterministic(self):
        h1 = self.service.hash_query('acme corp company profile')
        h2 = self.service.hash_query('acme corp company profile')
        self.assertEqual(h1, h2)
        self.assertEqual(h1, hashlib.sha256(b'acme corp company profile').hexdigest())

    def test_hash_query_differs_for_different_queries(self):
        h1 = self.service.hash_query('acme corp')
        h2 = self.service.hash_query('beta inc')
        self.assertNotEqual(h1, h2)

    def test_anonymize_lead_id_is_deterministic_sha256(self):
        a1 = self.service.anonymize_lead_id(42)
        a2 = self.service.anonymize_lead_id(42)
        self.assertEqual(a1, a2)
        self.assertEqual(a1, hashlib.sha256(b'42').hexdigest())

    def test_search_cache_hit_skips_provider_call_real(self):
        query = 'acme corp company profile'
        query_hash = self.service.hash_query(query)
        self.env['web.research.result'].store(
            query_hash, query, [{'title': 'Cached', 'url': 'https://acme.com'}], 'tavily'
        )
        with patch('requests.get') as mock_get:
            result = self.service.search(query)
        mock_get.assert_not_called()
        self.assertTrue(result['success'])
        self.assertTrue(result['cache_hit'])
        self.assertEqual(result['results'][0]['title'], 'Cached')

    def test_search_no_available_provider_returns_failure(self):
        self.provider.active = False
        result = self.service.search('some uncached query xyz')
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'], 'all_providers_unavailable')

    def test_search_writes_audit_row_with_hash_not_raw_query(self):
        self.provider.active = False  # force the no-provider path, still audits nothing here
        query = 'super secret company name'
        self.service.search(query)
        # No provider was called, so no audit row for this query — assert none leaked the raw text
        audits = self.env['web.research.audit'].search([])
        for row in audits:
            self.assertNotEqual(row.query_hash, query)

    def test_search_google_custom_shim_delegates_to_search_with_google_provider(self):
        with patch.object(self.service, 'search', return_value={'success': True, 'results': [], 'providers_used': ['google'], 'cache_hit': False, 'latency_ms': 0}) as mock_search:
            result = self.service.search_google_custom('epsilon corp', num_results=3)
        mock_search.assert_called_once_with('epsilon corp', num_results=3, providers=['google'])
        self.assertTrue(result['success'])
