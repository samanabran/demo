# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestCronConcurrency(TransactionCase):

    def setUp(self):
        super().setUp()
        self.leads = self.env['crm.lead'].create([
            {'name': 'Lead A', 'partner_name': 'Acme A', 'auto_enrich': True},
            {'name': 'Lead B', 'partner_name': 'Acme B', 'auto_enrich': True},
            {'name': 'Lead C', 'partner_name': 'Acme C', 'auto_enrich': True},
        ])
        self.env.cr.commit()  # leads must be committed so worker cursors can see them

    def test_cron_enrich_leads_all_reach_terminal_status(self):
        with patch(
            'odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
            return_value={'success': True, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0},
        ), patch(
            'odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
            return_value={'success': True, 'content': 'summary', 'error': None, 'retries': 0},
        ):
            self.env['crm.lead']._cron_enrich_leads()

        for lead in self.leads:
            lead.invalidate_recordset()
            self.assertIn(lead.ai_enrichment_status, ('completed', 'partial', 'failed'))
            self.assertNotEqual(lead.ai_enrichment_status, 'pending')
            self.assertNotEqual(lead.ai_enrichment_status, 'processing')

    def test_cron_enrich_leads_one_failure_does_not_block_others(self):
        call_count = {'n': 0}

        def flaky_enrich(self_lead, *a, **kw):
            call_count['n'] += 1
            if call_count['n'] == 2:
                raise Exception('simulated provider outage')
            self_lead.ai_enrichment_status = 'completed'

        with patch.object(type(self.leads), '_enrich_lead', flaky_enrich, create=False):
            self.env['crm.lead']._cron_enrich_leads()

        statuses = [lead.ai_enrichment_status for lead in self.leads.browse(self.leads.ids)]
        self.assertIn('failed', statuses)
        self.assertIn('completed', statuses)
