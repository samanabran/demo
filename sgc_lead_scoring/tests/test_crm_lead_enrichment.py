# -*- coding: utf-8 -*-
"""Tests for `crm.lead._enrich_lead()` against the Universal JSON Contract
pipeline (Task 8 rewrite).

These tests exercise the orchestrator end-to-end via mocked `multi_search`/
`call_llm`. Pure-function coverage (parser tolerance, pre-classifier matrix,
promotion, anonymization toggle matrix) already lives in
`tests/test_lead_intelligence.py` (`TestLeadIntelligenceHelpers` /
`TestLeadIntelligencePipeline`, from Tasks 3+4/5) and is NOT duplicated here.
"""
import json
from unittest.mock import patch

from markupsafe import Markup

from odoo.tests.common import TransactionCase

from odoo.addons.sgc_lead_scoring.models import lead_intelligence as li


def _scores_block(score=80, confidence='high', reason='strong'):
    """Full 11-key `scores` block for the Universal JSON Contract."""
    scores = {}
    for key, _field in li.SCORE_KEYS:
        scores['%s_score' % key] = {'score': score, 'confidence': confidence, 'reason': reason}
    return scores


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

    def _llm_free_text(self, *_a, **_k):
        """Legacy-shaped free-text LLM reply — not valid JSON, so the new
        pipeline correctly fails to parse it (used to test the parse-failure
        path, not the happy path)."""
        return {'success': True, 'content': 'Acme Corp is a mid-size manufacturer.', 'error': None, 'retries': 0}

    def _good_contract_json(self, entity_type='b2b_company'):
        return json.dumps({
            'metadata': {'schema_version': '1.0', 'providers_used': ['tavily']},
            'classification': {'entity_type': entity_type, 'confidence': 'high'},
            'scores': _scores_block(),
            'customer_intelligence': {'industry': {'value': 'Manufacturing'}},
            'buying_intelligence': {'budget_readiness': {'value': 'AED 5M+'}},
            'summary': {
                'executive_summary': 'Acme is a promising manufacturer.',
                'key_findings': ['Growing fast', 'New facility'],
                'conversation_strategy': 'Lead with ROI.',
                'risks': ['Long procurement cycle'],
                'opportunities': ['Digital transformation budget'],
                'recommended_next_actions': ['Book discovery call'],
            },
        })

    def _llm_good_contract(self, *_a, **_k):
        return {'success': True, 'content': self._good_contract_json(), 'error': None, 'retries': 0}

    # ------------------------------------------------------------------
    # 1. Happy path against the new contract (was: asserted the old
    #    ai_enrichment_report/ai_enrichment_data shape and a free-text 'completed').
    # ------------------------------------------------------------------
    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_completed_status(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_good_contract
        self.lead._enrich_lead()

        self.assertEqual(self.lead.ai_enrichment_status, 'completed')
        self.assertTrue(self.lead.ai_last_enrichment_date)

        # 11 score fields populated from the contract's `scores` block.
        for _key, field in li.SCORE_KEYS:
            self.assertEqual(getattr(self.lead, field), 80.0, field)

        # ai_enrichment_data now stores the FULL validated JSON contract,
        # not the old {results, providers_used, cache_hits} shape.
        data = json.loads(self.lead.ai_enrichment_data)
        self.assertEqual(data['classification']['entity_type'], 'b2b_company')
        self.assertIn('customer_intelligence', data)
        self.assertIn('summary', data)

    # ------------------------------------------------------------------
    # 2. 'partial' is a dead Selection value from this method's perspective:
    #    _enrich_lead() only ever sets processing/parse_failure/completed;
    #    'failed' is set by the cron's own exception handler, not here.
    #    A response with no parseable content -> parse_failure after 2 tries.
    # ------------------------------------------------------------------
    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_parse_failure_when_llm_content_empty(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.return_value = {'success': False, 'content': None, 'error': 'timeout', 'retries': 3}
        self.lead._enrich_lead()

        self.assertEqual(self.lead.ai_enrichment_status, 'parse_failure')
        # deterministic retry: called exactly twice, not once.
        self.assertEqual(mock_call_llm.call_count, 2)

    # ------------------------------------------------------------------
    # 3. Search returning nothing usable must not block the LLM call. Fixed
    #    to mock a VALID JSON reply so the intended assertion ("LLM still
    #    called even when search fails") is tested against a state that
    #    actually reaches 'completed' rather than a free-text reply that
    #    would (correctly) retry twice under the new pipeline.
    # ------------------------------------------------------------------
    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_calls_llm_when_all_search_providers_unavailable(self, mock_multi_search, mock_call_llm):
        mock_multi_search.return_value = {
            'success': False, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0,
        }
        mock_call_llm.side_effect = self._llm_good_contract
        self.lead._enrich_lead()

        mock_call_llm.assert_called_once()
        self.assertEqual(self.lead.ai_enrichment_status, 'completed')

    # ------------------------------------------------------------------
    # 4. Query-building shape re-verified against the current
    #    _build_research_queries(): unchanged (2 queries when no website).
    # ------------------------------------------------------------------
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_skips_website_query_when_no_website(self, mock_multi_search):
        self.lead.website = False
        mock_multi_search.side_effect = self._multi_search_success
        with patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
                   side_effect=self._llm_good_contract):
            self.lead._enrich_lead()
        called_queries = mock_multi_search.call_args[0][0]
        self.assertEqual(len(called_queries), 2)

    # ------------------------------------------------------------------
    # 5. phone/email_from were never in scope for any anonymization
    #    decision (F/F.1/F.2 only cover contact_name, lead.name,
    #    partner_name). Verified against build_prompt(): its `facts` dict
    #    only ever includes lead_name, company_name, contact_display_name,
    #    website, entity_hint, schema_version, prompt_version — phone/email
    #    are never assembled into the prompt payload at all, regardless of
    #    the anonymize_customer_names toggle. Replaced the old (incorrect)
    #    "these get anonymized" assertion with the correct one.
    # ------------------------------------------------------------------
    def test_enrich_lead_phone_and_email_never_reach_prompt(self):
        self.lead.phone = '+1-555-0100'
        self.lead.email_from = 'buyer@acme.com'
        with patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
                   side_effect=self._multi_search_success), \
             patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm') as mock_llm:
            mock_llm.side_effect = self._llm_good_contract
            self.lead._enrich_lead()
            prompt_messages = mock_llm.call_args.kwargs.get('messages') or mock_llm.call_args[0][0]
            prompt_text = json.dumps(prompt_messages)
            self.assertNotIn('+1-555-0100', prompt_text)
            self.assertNotIn('buyer@acme.com', prompt_text)

    # ------------------------------------------------------------------
    # 6. Regression test for the chatter-rendering bug: `_lead_intelligence_note`
    #    must return a `markupsafe.Markup` instance so `message_post()`'s
    #    `escape(body)` (mail_thread.py: "escape if text, keep if markup")
    #    leaves it untouched, and the structural tags this method builds
    #    itself (`<b>`, `<ul>`, `<li>`) must survive un-escaped in the
    #    stored message body -- i.e. the note actually renders as HTML
    #    instead of showing literal `&lt;b&gt;` text in the chatter.
    # ------------------------------------------------------------------
    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_lead_intelligence_note_renders_as_real_html(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_good_contract
        self.lead._enrich_lead()

        messages = self.lead.message_ids.filtered(
            lambda m: 'AI Research Summary' in (m.body or ''))
        self.assertTrue(messages)
        body = messages[0].body
        self.assertIsInstance(body, Markup)
        # structural tags built by _lead_intelligence_note itself must be
        # live markup, not escaped text.
        self.assertIn('<b>AI Research Summary</b>', body)
        self.assertIn('<ul>', body)
        self.assertIn('<li>Growing fast</li>', body)
        self.assertNotIn('&lt;b&gt;', body)
        self.assertNotIn('&lt;ul&gt;', body)

    # ------------------------------------------------------------------
    # 7. Regression test for the latent injection gap: HTML-special
    #    characters inside LLM-controlled `summary.*` fields must be
    #    escaped in the final chatter body, not interpreted as live markup
    #    -- this is what stops an attacker-controlled web page from
    #    smuggling a `<script>` (or any other tag/attribute) into the CRM
    #    chatter via the LLM's JSON response.
    # ------------------------------------------------------------------
    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_lead_intelligence_note_escapes_llm_controlled_html(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        malicious_contract = json.loads(self._good_contract_json())
        malicious_contract['summary']['executive_summary'] = (
            'A <script>alert(1)</script> company')
        malicious_contract['summary']['key_findings'] = [
            '<img src=x onerror=alert(2)>', 'Growing fast']
        malicious_contract['summary']['conversation_strategy'] = (
            '"><svg onload=alert(3)>')
        malicious_contract['summary']['risks'] = ['Tom & Jerry <b>risk</b>']
        mock_call_llm.return_value = {
            'success': True, 'content': json.dumps(malicious_contract), 'error': None, 'retries': 0,
        }
        self.lead._enrich_lead()

        messages = self.lead.message_ids.filtered(
            lambda m: 'AI Research Summary' in (m.body or ''))
        self.assertTrue(messages)
        body = messages[0].body
        self.assertIsInstance(body, Markup)
        # the whole body is still valid Markup (rendering fix holds)...
        self.assertIn('<b>AI Research Summary</b>', body)
        # ...but every LLM-controlled value is escaped, not live markup.
        self.assertNotIn('<script>', body)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', body)
        self.assertNotIn('<img src=x onerror=alert(2)>', body)
        self.assertIn('&lt;img src=x onerror=alert(2)&gt;', body)
        self.assertNotIn('<svg onload=alert(3)>', body)
        self.assertIn('&lt;svg onload=alert(3)&gt;', body)
        self.assertIn('Tom &amp; Jerry &lt;b&gt;risk&lt;/b&gt;', body)

    # ------------------------------------------------------------------
    # 8. Same rendering + escaping treatment on the OTHER message_post()
    #    call site: the terminal parse-failure path. `parse_error` is
    #    `str(exc)` from the module's own `ParseFailure`, not LLM-controlled,
    #    but the fix is applied uniformly for consistency, and this path's
    #    plain-str body had the exact same rendering bug.
    # ------------------------------------------------------------------
    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_parse_failure_note_renders_as_real_html_and_escapes_error(
            self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.return_value = {
            'success': False, 'content': None, 'error': 'timeout', 'retries': 3,
        }
        self.lead._enrich_lead()

        self.assertEqual(self.lead.ai_enrichment_status, 'parse_failure')
        messages = self.lead.message_ids.filtered(
            lambda m: 'AI Research Summary' in (m.body or ''))
        self.assertTrue(messages)
        body = messages[0].body
        self.assertIsInstance(body, Markup)
        self.assertIn('<b>AI Research Summary</b>', body)
        self.assertIn('could not parse the AI response after 2 attempts', body)

    # NOTE: the two old tests
    #   - test_enrich_lead_anonymize_company_names_restricts_to_searxng
    #   - test_enrich_lead_anonymize_off_does_not_restrict_providers
    # tested the OLD `anonymize_company_names`-restricts-search-to-searxng
    # behavior. Confirmed via grep that crm_lead.py no longer references
    # `anonymize_company_names` at all -- Task 3+4's rewrite of
    # _enrich_lead() dropped that provider-restriction behavior entirely
    # (the NEW `anonymize_customer_names` toggle governs name-hashing only,
    # not provider selection). Removed rather than fixed: the anonymization
    # behavior that matters now is already thoroughly covered by
    # tests/test_lead_intelligence.py's TestLeadIntelligencePipeline class
    # (test_contact_name_anonymized_in_prompt,
    # test_lead_name_and_company_name_anonymized_toggle_on,
    # test_names_cleartext_when_toggle_off,
    # test_lead_name_fallback_subject_anonymized_in_query).


class TestLeadEnrichmentB2CB2BEndToEnd(TransactionCase):
    """Explicit B2C and B2B end-to-end coverage through the real
    `_enrich_lead()` orchestrator (Task 8 point 4) -- distinct from
    `test_lead_intelligence.py::test_completed_single_call`, which is
    B2B-shaped but exercises the orchestrator's internals directly rather
    than standing in as a named "this is the B2C/B2B scenario" test.
    """

    def _multi_search_success(self, *_a, **_k):
        return {
            'success': True,
            'results': [{'title': 'Hit', 'url': 'https://example.com', 'snippet': 'x', 'sources': ['tavily']}],
            'providers_used': ['tavily'],
            'cache_hits': 0,
            'latency_ms': 100,
        }

    # ---- B2C -------------------------------------------------------
    def test_b2c_individual_end_to_end(self):
        """Public-email, no company, no website lead -> heuristic
        b2c_individual (Rule 3), mocked LLM classifies it as
        b2c_individual too, with customer_intelligence/needs_assessment/
        relationship_intelligence populated and company_intelligence
        marked not_applicable."""
        lead = self.env['crm.lead'].create({
            'name': 'Jane Buyer',
            'contact_name': 'Jane Buyer',
            'email_from': 'jane.buyer@gmail.com',
        })
        contract = json.dumps({
            'metadata': {'schema_version': '1.0', 'providers_used': ['tavily']},
            'classification': {'entity_type': 'b2c_individual', 'confidence': 'high'},
            'scores': _scores_block(),
            'company_intelligence': {'not_applicable': True},
            'customer_intelligence': {'industry': {'value': 'Retail'}},
            'needs_assessment': {'primary_need': {'value': 'Home renovation financing'}},
            'relationship_intelligence': {'engagement_level': {'value': 'Warm'}},
            'buying_intelligence': {'budget_readiness': {'value': 'AED 100k-250k'}},
            'summary': {'executive_summary': 'Individual buyer researching renovation financing.'},
        })
        with patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
                   side_effect=self._multi_search_success), \
             patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
                   return_value={'success': True, 'content': contract, 'error': None, 'retries': 0}):
            lead._enrich_lead()

        self.assertEqual(lead.ai_enrichment_status, 'completed')
        self.assertEqual(lead.entity_hint, 'b2c_individual')
        self.assertEqual(lead.ai_entity_type, 'b2c_individual')
        self.assertEqual(lead.ai_entity_type_confidence, 'high')
        self.assertFalse(lead.ai_classification_mismatch)
        for _key, field in li.SCORE_KEYS:
            self.assertEqual(getattr(lead, field), 80.0, field)
        # native-field promotion: industry sourced from customer_intelligence
        # (the B2C section), not company_intelligence.
        self.assertEqual(lead.ai_industry, 'Retail')
        self.assertEqual(lead.ai_budget_tier, 'AED 100k-250k')
        parsed = json.loads(lead.ai_enrichment_data)
        self.assertTrue(parsed['company_intelligence'].get('not_applicable'))
        self.assertIn('needs_assessment', parsed)
        self.assertIn('relationship_intelligence', parsed)

    # ---- B2B -------------------------------------------------------
    def test_b2b_company_end_to_end(self):
        """Corporate-domain, company name + website lead -> heuristic
        b2b_company (Rule 4), mocked LLM classifies it as the more specific
        'enterprise' (same b2b family, so no mismatch), with
        company_intelligence/decision_makers/business_requirements
        populated and industry sourced via the company_intelligence
        fallback (no customer_intelligence section present)."""
        lead = self.env['crm.lead'].create({
            'name': 'Acme Manufacturing Deal',
            'partner_name': 'Acme Manufacturing LLC',
            'website': 'https://acmemfg.com',
        })
        contract = json.dumps({
            'metadata': {'schema_version': '1.0', 'providers_used': ['tavily']},
            'classification': {'entity_type': 'enterprise', 'confidence': 'high'},
            'scores': _scores_block(),
            'company_intelligence': {'industry': {'value': 'Manufacturing'}},
            'decision_makers': {'primary_contact': {'value': 'VP of Operations'}},
            'business_requirements': {'key_requirement': {'value': 'ERP integration'}},
            'buying_intelligence': {'budget_readiness': {'value': 'AED 5M+'}},
            'summary': {'executive_summary': 'Enterprise manufacturer evaluating ERP integration.'},
        })
        with patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
                   side_effect=self._multi_search_success), \
             patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
                   return_value={'success': True, 'content': contract, 'error': None, 'retries': 0}):
            lead._enrich_lead()

        self.assertEqual(lead.ai_enrichment_status, 'completed')
        self.assertEqual(lead.entity_hint, 'b2b_company')
        self.assertEqual(lead.ai_entity_type, 'enterprise')
        self.assertEqual(lead.ai_entity_type_confidence, 'high')
        # hint 'b2b_company' and llm 'enterprise' are both b2b family -> no mismatch.
        self.assertFalse(lead.ai_classification_mismatch)
        for _key, field in li.SCORE_KEYS:
            self.assertEqual(getattr(lead, field), 80.0, field)
        # native-field promotion: no customer_intelligence section present,
        # so industry falls back to company_intelligence.
        self.assertEqual(lead.ai_industry, 'Manufacturing')
        self.assertEqual(lead.ai_budget_tier, 'AED 5M+')
        parsed = json.loads(lead.ai_enrichment_data)
        self.assertIn('decision_makers', parsed)
        self.assertIn('business_requirements', parsed)
