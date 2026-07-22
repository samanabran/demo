# -*- coding: utf-8 -*-
import threading
from unittest.mock import patch

from odoo import api
from odoo.modules.registry import Registry
from odoo.tests.common import TransactionCase


class TestCronConcurrency(TransactionCase):
    """Odoo's TransactionCase forbids cr.commit()/cr.rollback() on self.env.cr
    (it would break the class-shared savepoint every sibling test relies on),
    so leads are created and committed through a genuinely separate cursor —
    the same "open another cursor" escape hatch the framework's own
    AssertionError message points to. Real, committed rows are required here
    because _cron_enrich_leads() gives each ThreadPoolExecutor worker its own
    cursor, and a worker's separate connection can never see another
    connection's uncommitted writes."""

    def setUp(self):
        super().setUp()
        with Registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, self.env.uid, self.env.context)
            leads = env['crm.lead'].create([
                {'name': 'Lead A', 'partner_name': 'Acme A', 'auto_enrich': True},
                {'name': 'Lead B', 'partner_name': 'Acme B', 'auto_enrich': True},
                {'name': 'Lead C', 'partner_name': 'Acme C', 'auto_enrich': True},
            ])
            self.lead_ids = leads.ids
            cr.commit()
        self.leads = self.env['crm.lead'].browse(self.lead_ids)
        self.addCleanup(self._cleanup_committed_leads)

    def _cleanup_committed_leads(self):
        """The leads above were committed on a separate connection, so they
        survive this test's own rollback -- delete them the same way so no
        fake leads accumulate in the shared database across test runs."""
        with Registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, self.env.uid, self.env.context)
            env['crm.lead'].browse(self.lead_ids).unlink()
            cr.commit()

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
        # _enrich_one() runs each lead on its own ThreadPoolExecutor worker, so
        # a plain shared int would race under real concurrency; a lock makes
        # "exactly one call fails" deterministic regardless of thread interleaving.
        lock = threading.Lock()
        call_count = {'n': 0}

        def flaky_call_llm(*a, **kw):
            with lock:
                call_count['n'] += 1
                n = call_count['n']
            if n == 2:
                raise Exception('simulated provider outage')
            return {'success': True, 'content': 'summary', 'error': None, 'retries': 0}

        with patch(
            'odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
            return_value={'success': True, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0},
        ), patch(
            'odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
            side_effect=flaky_call_llm,
        ):
            self.env['crm.lead']._cron_enrich_leads()

        statuses = [lead.ai_enrichment_status for lead in self.leads.browse(self.lead_ids)]
        self.assertIn('failed', statuses)
        self.assertIn('completed', statuses)
