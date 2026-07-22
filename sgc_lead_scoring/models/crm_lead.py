# -*- coding: utf-8 -*-
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from odoo import models, fields, api, _

from . import lead_intelligence as li

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    ai_probability_score = fields.Float(
        string='AI Probability Score',
        aggregator='avg',
        help='AI-calculated probability score based on lead quality analysis',
    )
    ai_enrichment_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('partial', 'Partial'),
        ('parse_failure', 'Parse Failure'),
        ('failed', 'Failed'),
    ], string='AI Enrichment Status', default='pending')
    ai_last_enrichment_date = fields.Datetime(
        string='Last AI Enrichment',
        readonly=True,
    )
    auto_enrich = fields.Boolean(
        string='Auto-Enrich',
        default=True,
        help='Automatically enrich this lead with AI analysis',
    )
    ai_completeness_score = fields.Float(
        string='Completeness Score',
        aggregator='avg',
        help='Score based on form completeness (0-100)',
    )
    ai_clarity_score = fields.Float(
        string='Clarity Score',
        aggregator='avg',
        help='Score based on requirement clarity (0-100)',
    )
    ai_engagement_score = fields.Float(
        string='Engagement Score',
        aggregator='avg',
        help='Score based on engagement level (0-100)',
    )
    ai_enrichment_report = fields.Text(
        string='AI Enrichment Report',
        readonly=True,
    )
    ai_analysis_summary = fields.Text(
        string='AI Analysis Summary',
        readonly=True,
    )
    ai_enrichment_data = fields.Text(
        string='AI Enrichment Data (JSON)',
        readonly=True,
    )
    ai_score_color = fields.Integer(
        string='AI Score Color Indicator',
        compute='_compute_ai_score_color',
        store=True,
    )

    # ------------------------------------------------------------------
    # Lead Intelligence Engine fields (Universal JSON Contract)
    # ------------------------------------------------------------------
    entity_hint = fields.Selection(
        li.ENTITY_HINT_SELECTION, string='Entity Hint (heuristic)', readonly=True)
    ai_entity_type = fields.Selection(
        li.ENTITY_TYPE_SELECTION, string='AI Entity Type', readonly=True)
    ai_entity_type_confidence = fields.Selection(
        li.CONFIDENCE_SELECTION, string='AI Entity Confidence', readonly=True)
    ai_need_score = fields.Float(string='Need Score', readonly=True, aggregator='avg')
    ai_budget_score = fields.Float(string='Budget Score', readonly=True, aggregator='avg')
    ai_authority_score = fields.Float(string='Authority Score', readonly=True, aggregator='avg')
    ai_timeline_score = fields.Float(string='Timeline Score', readonly=True, aggregator='avg')
    ai_urgency_score = fields.Float(string='Urgency Score', readonly=True, aggregator='avg')
    ai_relationship_score = fields.Float(string='Relationship Score', readonly=True, aggregator='avg')
    ai_digital_maturity_score = fields.Float(
        string='Digital Maturity Score', readonly=True, aggregator='avg')
    ai_implementation_complexity_score = fields.Float(
        string='Implementation Complexity Score', readonly=True, aggregator='avg')
    ai_proposal_confidence_score = fields.Float(
        string='Proposal Confidence Score', readonly=True, aggregator='avg')
    ai_win_probability_score = fields.Float(
        string='Win Probability Score', readonly=True, aggregator='avg')
    ai_opportunity_score = fields.Float(string='Opportunity Score', readonly=True, aggregator='avg')
    ai_scoring_rationale = fields.Text(string='Scoring Rationale (11 lines)', readonly=True)
    ai_budget_tier = fields.Char(string='Budget Tier', readonly=True)
    ai_industry = fields.Char(string='Industry', readonly=True)
    ai_readiness = fields.Selection([
        ('hot', 'Hot'), ('warm', 'Warm'), ('nurture', 'Nurture'), ('cold', 'Cold'),
    ], string='Readiness', compute='_compute_readiness', store=True, readonly=True)
    ai_enrichment_evidence = fields.Text(string='Normalized Evidence (JSON)', readonly=True)
    ai_classification_mismatch = fields.Boolean(
        string='Classification Mismatch', compute='_compute_mismatch', store=True, readonly=True,
    )

    @api.depends('ai_probability_score')
    def _compute_ai_score_color(self):
        for lead in self:
            if lead.ai_probability_score >= 70:
                lead.ai_score_color = 10  # green/success
            elif lead.ai_probability_score >= 40:
                lead.ai_score_color = 5   # orange/warning
            else:
                lead.ai_score_color = 1   # red/danger

    @api.depends('ai_win_probability_score', 'ai_need_score', 'ai_budget_score')
    def _compute_readiness(self):
        """Stored readiness label derived from the win/need/budget scores
        (Decision G.1). The pure logic lives in the helper module so it is
        unit-testable without an Odoo environment."""
        for lead in self:
            label = li.compute_readiness_label({
                'ai_win_probability_score': lead.ai_win_probability_score,
                'ai_need_score': lead.ai_need_score,
                'ai_budget_score': lead.ai_budget_score,
            })
            lead.ai_readiness = label.lower()

    @api.depends('entity_hint', 'ai_entity_type', 'ai_entity_type_confidence')
    def _compute_mismatch(self):
        """True iff the heuristic family disagrees with the LLM family AND the
        LLM classified with high confidence (Decision I). ``unknown`` has no
        family and therefore never produces a mismatch on its own."""
        for lead in self:
            hint_family = li.entity_family(lead.entity_hint)
            llm_family = li.entity_family(lead.ai_entity_type)
            lead.ai_classification_mismatch = bool(
                hint_family and llm_family
                and hint_family != llm_family
                and lead.ai_entity_type_confidence == 'high'
            )

    def action_enrich_with_ai(self):
        """Enrich this lead with AI-powered analysis."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Enrich Lead with AI'),
            'res_model': 'lead.enrichment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lead_ids': self.ids},
        }

    def action_regenerate_report(self):
        """Regenerate AI report from existing enrichment data (no API call)."""
        self.ensure_one()
        return True

    def _build_research_queries(self, company_name, display_name):
        """Search queries for multi_search(). Uses ``display_name`` (already
        anonymized upstream when the toggle is on) as the subject for
        individual leads, and never leaks the real contact name."""
        subject = company_name or display_name or self.name or ''
        queries = []
        if subject:
            queries.append('%s profile about' % subject)
            queries.append('%s news %s' % (subject, date.today().year))
        if self.website:
            queries.append('site:%s products services' % self.website)
        return queries

    def _lead_intelligence_note(self, parsed, research, evidence):
        """Build the structured HTML chatter note from ``summary.*`` (step 17)."""
        summary = parsed.get('summary') or {}
        note = ['<b>AI Research Summary</b>']
        exec_summary = summary.get('executive_summary')
        if exec_summary:
            note.append('<p>%s</p>' % exec_summary)

        def _section(title, items):
            if not items:
                return
            if isinstance(items, str):
                items = [items]
            lis = ''.join('<li>%s</li>' % item for item in items if item)
            if lis:
                note.append('<p><b>%s</b></p><ul>%s</ul>' % (title, lis))

        _section(_('Key Findings'), summary.get('key_findings'))
        conversation_strategy = summary.get('conversation_strategy')
        if conversation_strategy:
            note.append('<p><b>%s</b>: %s</p>' % (_('Conversation Strategy'), conversation_strategy))
        _section(_('Risks'), summary.get('risks'))
        _section(_('Opportunities'), summary.get('opportunities'))
        _section(_('Recommended Next Actions'), summary.get('recommended_next_actions'))

        providers = research.get('providers_used') or [
            e['provider'] for e in evidence if e.get('provider')
        ]
        if providers:
            note.append('<p><i>%s: %s</i></p>' % (
                _('Sources'), ', '.join(dict.fromkeys(providers))))
        return ''.join(note)

    def _enrich_lead(self):
        """Universal Lead Intelligence enrichment: pre-classify, search,
        one (or at most two) LLM call(s), parse the Universal JSON Contract,
        promote to native fields, persist 3 artifacts and post a structured
        chatter note. See the design spec's Resolved Decisions A-I."""
        self.ensure_one()
        # 1 — do not double-run an in-flight enrichment.
        if self.ai_enrichment_status == 'processing':
            return
        # 2 — mark in-flight.
        self.ai_enrichment_status = 'processing'

        # 3 — deterministic pre-classifier hint.
        entity_hint = li.classify_entity_hint(self, self.env)
        self.entity_hint = entity_hint

        # 4 — anonymized (or plain) contact display name.
        display_name = li.anonymize_contact_name(self, self.env)

        # 5 + 6 — search (existing infrastructure, unchanged).
        company_name = self.partner_name or ''
        queries = self._build_research_queries(company_name, display_name)
        research = self.env['web.research.service'].multi_search(queries, parallel=True)

        # 7 + 8 — normalize evidence and persist artifact 3 immediately.
        evidence = li.normalize_evidence(research)
        self.ai_enrichment_evidence = json.dumps(evidence)

        # 9 — build the prompt (injection-defended evidence block).
        messages = li.build_prompt(self, entity_hint, evidence, self.env)

        # 10 + 11 — at most two LLM calls: initial + one deterministic retry.
        parsed = None
        raw_content = ''
        parse_error = ''
        for _attempt in range(2):
            resp = self.env['llm.service'].call_llm(
                messages=messages, response_schema=li.LEAD_INTELLIGENCE_SCHEMA)
            raw_content = resp.get('content') or ''
            try:
                parsed = li.parse_llm_response(raw_content)
                break
            except li.ParseFailure as exc:
                parse_error = str(exc)
                continue

        if parsed is None:
            # Terminal parse failure: persist the raw content for diagnosis.
            self.ai_enrichment_data = raw_content
            self.ai_enrichment_status = 'parse_failure'
            self.ai_last_enrichment_date = fields.Datetime.now()
            self.message_post(
                body='<b>%s</b><p>%s</p>' % (
                    _('AI Research Summary'),
                    _('Enrichment could not parse the AI response after 2 attempts: %s') % parse_error,
                ),
                subtype_xmlid='mail.mt_note',
            )
            return

        # 12 — persist artifact 2 (full validated JSON).
        self.ai_enrichment_data = json.dumps(parsed)

        # 13 + 14 — promote to native fields. The stored-compute fields
        # (ai_readiness, ai_classification_mismatch) are derived by their own
        # methods on write, so they are intentionally not written here.
        native = li.promote_to_native_fields(parsed)
        write_vals = {field: native[field] for _key, field in li.SCORE_KEYS}
        write_vals.update({
            'ai_entity_type': native['ai_entity_type'],
            'ai_entity_type_confidence': native['ai_entity_type_confidence'],
            'ai_scoring_rationale': native['ai_scoring_rationale'],
            'ai_budget_tier': native['ai_budget_tier'],
            'ai_industry': native['ai_industry'],
        })
        self.write(write_vals)

        # 15 + 16 — terminal status + timestamp.
        self.ai_enrichment_status = 'completed'
        self.ai_last_enrichment_date = fields.Datetime.now()

        # 17 + 18 — structured chatter note.
        note_body = self._lead_intelligence_note(parsed, research, evidence)
        self.message_post(body=note_body, subtype_xmlid='mail.mt_note')

    @api.model
    def _cron_enrich_leads(self):
        """Scheduled cron: auto-enrich up to 50 leads, 5 at a time, each
        worker on its own cursor so one lead's failure/rollback can't
        affect another's commit."""
        leads = self.search([
            ('auto_enrich', '=', True),
            ('ai_enrichment_status', '!=', 'processing'),
        ], limit=50)

        def _enrich_one(lead_id):
            with self.env.registry.cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)
                lead = env['crm.lead'].browse(lead_id)
                try:
                    lead._enrich_lead()
                except Exception:
                    _logger.exception('crm.lead._cron_enrich_leads: lead %s failed', lead_id)
                    lead.ai_enrichment_status = 'failed'
                cr.commit()

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(_enrich_one, leads.ids))
        return True
