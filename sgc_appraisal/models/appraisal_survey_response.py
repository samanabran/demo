# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AppraisalSurveyResponse(models.Model):
    _name = 'appraisal.survey.response'
    _description = 'Appraisal Survey Response'
    _rec_name = 'respondent_name'
    _order = 'id desc'

    survey_form_id = fields.Many2one(
        'appraisal.survey.form',
        string='Survey Form',
        required=True,
        ondelete='cascade'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    respondent_name = fields.Char(string='Respondent Name')
    respondent_email = fields.Char(string='Respondent Email')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
    ], string='State', default='pending', required=True)
    created_date = fields.Datetime(
        string='Created Date',
        default=fields.Datetime.now
    )
    submitted_date = fields.Datetime(string='Submitted Date')
    completion_percentage = fields.Float(
        string='Completion (%)',
        default=0.0
    )
    response_data = fields.Text(
        string='Response Data',
        help='JSON-encoded response data'
    )
    comments = fields.Text(string='Comments')

    def response_data_get(self):
        """Get response_data as dict."""
        self.ensure_one()
        if self.response_data:
            try:
                import json
                return json.loads(self.response_data)
            except (ValueError, TypeError):
                pass
        return {}
