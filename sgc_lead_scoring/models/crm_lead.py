# -*- coding: utf-8 -*-

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
        """Enrich a single lead with AI analysis (stub - no API call)."""
        self.ensure_one()
        self.ai_enrichment_status = 'completed'
        self.ai_last_enrichment_date = fields.Datetime.now()

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
