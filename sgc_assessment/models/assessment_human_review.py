# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AssessmentHumanReview(models.Model):
    """Human review of a candidate's assessment results.
    Allows reviewers to provide additional evaluation, override AI scores,
    and make hiring recommendations."""
    _name = 'assessment.human.review'
    _description = 'Assessment Human Review'
    _order = 'id desc'
    _rec_name = 'display_name'

    candidate_id = fields.Many2one('assessment.candidate', string='Candidate',
                                   required=True, ondelete='cascade')
    reviewer_id = fields.Many2one('res.users', string='Reviewer',
                                  required=True,
                                  default=lambda self: self.env.user)
    review_date = fields.Datetime(string='Review Date', default=fields.Datetime.now)
    recommendation = fields.Selection([
        ('strong_hire', 'Strong Hire'),
        ('hire', 'Hire'),
        ('consider', 'Consider'),
        ('no_hire', 'No Hire'),
    ], string='Recommendation', required=True)
    reviewer_notes = fields.Text(string='Reviewer Notes')
    rating_technical = fields.Selection([(str(i), str(i)) for i in range(1, 6)],
                                        string='Technical Rating')
    rating_communication = fields.Selection([(str(i), str(i)) for i in range(1, 6)],
                                            string='Communication Rating')
    rating_cultural_fit = fields.Selection([(str(i), str(i)) for i in range(1, 6)],
                                           string='Cultural Fit Rating')
    override_ai_score = fields.Boolean(string='Override AI Score', default=False)
    override_reason = fields.Text(string='Override Reason')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    display_name = fields.Char(string='Display Name',
                               compute='_compute_display_name', store=True)

    @api.depends('candidate_id', 'reviewer_id', 'review_date')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"Review - {rec.candidate_id.name}"
                f" by {rec.reviewer_id.display_name}"
                f" ({rec.review_date})"
            )

    def action_complete(self):
        self.state = 'completed'
