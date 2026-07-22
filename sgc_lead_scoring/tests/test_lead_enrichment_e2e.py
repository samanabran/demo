# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import HttpCase, tagged


@tagged('-at_install', 'post_install')
class TestLeadEnrichmentE2E(HttpCase):

    def test_ai_enrich_button_produces_research_note(self):
        lead = self.env['crm.lead'].create({
            'name': 'E2E Test Lead', 'partner_name': 'E2E Acme', 'website': 'https://e2eacme.com',
        })
        # action_enrich_leads() raises UserError without a configured
        # provider (no llm.provider is seeded active+default) -- same gap
        # found in Task 14; create a minimal one for this E2E path too.
        provider = self.env['llm.provider'].create({
            'name': 'E2E Test Provider', 'provider_type': 'openai',
            'model_name': 'gpt-4', 'api_key': 'test-key',
        })
        with patch(
            'odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
            return_value={
                'success': True,
                'results': [{'title': 'E2E Acme', 'url': 'https://e2eacme.com', 'snippet': 'a company', 'sources': ['tavily']}],
                'providers_used': ['tavily'],
                'cache_hits': 0,
                'latency_ms': 90,
            },
        ), patch(
            'odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
            return_value={'success': True, 'content': 'E2E Acme is a test company.', 'error': None, 'retries': 0},
        ):
            wizard = self.env['lead.enrichment.wizard'].create({
                'lead_ids': [(6, 0, lead.ids)], 'provider_id': provider.id, 'parallel': False,
            })
            wizard.action_enrich_leads()

        lead.invalidate_recordset()
        self.assertEqual(lead.ai_enrichment_status, 'completed')
        messages = lead.message_ids.filtered(lambda m: 'AI Research Summary' in (m.body or ''))
        self.assertTrue(messages)
        self.assertIn('tavily', messages[0].body)
