# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AppraisalSurveyForm(models.Model):
    _name = 'appraisal.survey.form'
    _description = 'Appraisal Survey Form'
    
    name = fields.Char(string='Survey Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    question_ids = fields.One2many('survey.question', 'survey_id', string='Questions')
    
    def action_start_survey(self):
        # Action to start the survey
        return {
            'type': 'ir.actions.act_window',
            'name': _('Start Survey'),
            'res_model': 'survey.user_input',
            'view_mode': 'form',
            'view_id': self.env.ref('survey.survey_user_input_form').id,
            'target': 'new',
            'context': {
                'default_survey_id': self.id,
                'default_insert_mode': 'register',
                'default_scoring_type': 'none',
                'default_user_input_line_ids': [(0, 0, {'question_id': q.id}) for q in self.question_ids]
            }
        }
