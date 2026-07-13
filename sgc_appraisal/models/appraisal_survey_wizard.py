# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AppraisalSurveyWizard(models.TransientModel):
    _name = 'appraisal.survey.wizard'
    _description = 'Appraisal Survey Wizard'
    
    appraisal_id = fields.Many2one('hr.appraisal', string='Appraisal', required=True)
    survey_id = fields.Many2one('survey.survey', string='Survey', required=True)
    
    def action_start_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Start Survey'),
            'res_model': 'survey.user_input',
            'view_mode': 'form',
            'view_id': self.env.ref('survey.survey_user_input_form').id,
            'target': 'new',
            'context': {
                'default_survey_id': self.survey_id.id,
                'default_insert_mode': 'register',
                'default_scoring_type': 'none',
                'default_user_input_line_ids': [(0, 0, {'question_id': q.id}) for q in self.survey_id.question_ids],
                'default_appraisal_id': self.appraisal_id.id
            }
        }
