# -*- coding: utf-8 -*-
import json
from datetime import date

from odoo import models, fields, api, _


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

    @api.depends('ai_probability_score')
    def _compute_ai_score_color(self):
        for lead in self:
            if lead.ai_probability_score >= 70:
                lead.ai_score_color = 10  # green/success
            elif lead.ai_probability_score >= 40:
                lead.ai_score_color = 5   # orange/warning
            else:
                lead.ai_score_color = 1   # red/danger

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

    def _enrich_lead(self):
        """Run web research + LLM summarization for a single lead."""
        self.ensure_one()
        if self.ai_enrichment_status == 'processing':
            return
        self.ai_enrichment_status = 'processing'

        company_name = self.partner_name or self.name
        queries = [
            '%s company profile about' % company_name,
            '%s news %s' % (company_name, date.today().year),
        ]
        if self.website:
            queries.append('site:%s products services' % self.website)

        anonymize = self.env['ir.config_parameter'].sudo().get_param(
            'llm_lead_scoring.anonymize_company_names', 'False'
        ) == 'True'
        search_kwargs = {'parallel': True}
        if anonymize:
            search_kwargs['providers'] = ['searxng']
        research = self.env['web.research.service'].multi_search(queries, **search_kwargs)

        anon_id = self.env['web.research.service'].anonymize_lead_id(self.id)
        prompt_template = self.env['ir.config_parameter'].sudo().get_param(
            'llm_lead_scoring.enrichment_prompt_template',
            default=(
                'You are analyzing a sales lead (ref: {anon_id}). Company: {company_name}. '
                'Web research findings:\n{research_summary}\n\n'
                'Write a concise 3-5 sentence summary of this company for a sales rep, '
                'noting any relevant recent news.'
            ),
        )
        research_summary = '\n'.join(
            '- %s: %s' % (r.get('title', ''), r.get('snippet', '')) for r in research.get('results', [])
        ) or 'No web research results available.'
        prompt = prompt_template.format(
            anon_id=anon_id, company_name=company_name, research_summary=research_summary,
        )

        llm_resp = self.env['llm.service'].call_llm(messages=[{'role': 'user', 'content': prompt}])

        self.ai_enrichment_data = json.dumps({
            'results': research.get('results', []),
            'providers_used': research.get('providers_used', []),
            'cache_hits': research.get('cache_hits', 0),
        })

        if llm_resp.get('success'):
            self.ai_enrichment_report = llm_resp.get('content')
            self.ai_enrichment_status = 'completed' if research.get('success') else 'partial'
        else:
            self.ai_enrichment_report = False
            self.ai_enrichment_status = 'partial' if research.get('results') else 'failed'

        self.ai_last_enrichment_date = fields.Datetime.now()

        if self.ai_enrichment_status != 'failed':
            note_lines = ['<b>AI Research Summary</b>']
            if self.ai_enrichment_report:
                note_lines.append('<p>%s</p>' % self.ai_enrichment_report)
            if research.get('providers_used'):
                note_lines.append('<p><i>Sources: %s</i></p>' % ', '.join(research['providers_used']))
            self.message_post(body=''.join(note_lines), subtype_xmlid='mail.mt_note')

    @api.model
    def _cron_enrich_leads(self):
        """Scheduled cron method to auto-enrich leads.
        Override with actual LLM integration logic.
        """
        leads = self.search([
            ('auto_enrich', '=', True),
            ('ai_enrichment_status', '!=', 'processing'),
        ], limit=50)
        for lead in leads:
            try:
                lead._enrich_lead()
            except Exception:
                lead.ai_enrichment_status = 'failed'
        return True
