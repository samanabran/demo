# -*- coding: utf-8 -*-
import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestCrmLeadEnrichment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.lead = self.env['crm.lead'].create({
            'name': 'Acme Corp Deal',
            'partner_name': 'Acme Corp',
            'website': 'https://acme.com',
        })

    def _multi_search_success(self, *_a, **_k):
        return {
            'success': True,
            'results': [{'title': 'Acme', 'url': 'https://acme.com', 'snippet': 'x', 'sources': ['tavily']}],
            'providers_used': ['tavily'],
            'cache_hits': 0,
            'latency_ms': 120,
        }

    def _llm_success(self, *_a, **_k):
        return {'success': True, 'content': 'Acme Corp is a mid-size manufacturer.', 'error': None, 'retries': 0}

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_completed_status(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertEqual(self.lead.ai_enrichment_status, 'completed')
        self.assertTrue(self.lead.ai_enrichment_report)
        data = json.loads(self.lead.ai_enrichment_data)
        self.assertIn('providers_used', data)
        self.assertTrue(self.lead.ai_last_enrichment_date)

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_partial_when_llm_fails(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.return_value = {'success': False, 'content': None, 'error': 'timeout', 'retries': 3}
        self.lead._enrich_lead()
        self.assertEqual(self.lead.ai_enrichment_status, 'partial')
        data = json.loads(self.lead.ai_enrichment_data)
        self.assertTrue(data['results'])

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_falls_back_to_llm_only_when_all_providers_unavailable(self, mock_multi_search, mock_call_llm):
        mock_multi_search.return_value = {
            'success': False, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0,
        }
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertIn(self.lead.ai_enrichment_status, ('completed', 'partial'))
        mock_call_llm.assert_called_once()

    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_skips_website_query_when_no_website(self, mock_multi_search):
        self.lead.website = False
        mock_multi_search.side_effect = self._multi_search_success
        with patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm', side_effect=self._llm_success):
            self.lead._enrich_lead()
        called_queries = mock_multi_search.call_args[0][0]
        self.assertEqual(len(called_queries), 2)

    def test_enrich_lead_anonymizes_before_building_prompt(self):
        self.lead.phone = '+1-555-0100'
        self.lead.email_from = 'buyer@acme.com'
        with patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
                   side_effect=self._multi_search_success), \
             patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm') as mock_llm:
            mock_llm.side_effect = self._llm_success
            self.lead._enrich_lead()
            prompt_messages = mock_llm.call_args.kwargs.get('messages') or mock_llm.call_args[0][0]
            prompt_text = json.dumps(prompt_messages)
            self.assertNotIn('+1-555-0100', prompt_text)
            self.assertNotIn('buyer@acme.com', prompt_text)

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_anonymize_company_names_restricts_to_searxng(self, mock_multi_search, mock_call_llm):
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.anonymize_company_names', 'True')
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertEqual(mock_multi_search.call_args.kwargs.get('providers'), ['searxng'])

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_anonymize_off_does_not_restrict_providers(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertNotIn('providers', mock_multi_search.call_args.kwargs)
