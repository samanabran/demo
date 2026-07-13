# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AppraisalSurveyBulkWizard(models.TransientModel):
    _name = 'appraisal.survey.bulk.wizard'
    _description = 'Appraisal Survey Bulk Actions Wizard'

    survey_form_id = fields.Many2one(
        'appraisal.survey.form',
        string='Survey Form'
    )
    action_type = fields.Selection([
        ('send', 'Send Invitations'),
        ('close', 'Close Survey'),
        ('export', 'Export Responses'),
    ], string='Action', default='send', required=True)
    recipient_ids = fields.Many2many(
        'res.partner',
        string='Recipients'
    )

    def action_execute(self):
        self.ensure_one()
        if self.action_type == 'send':
            return {'type': 'ir.actions.act_window_close'}
        elif self.action_type == 'close':
            if self.survey_form_id:
                self.survey_form_id.write({'active': False})
            return {'type': 'ir.actions.act_window_close'}
        return {'type': 'ir.actions.act_window_close'}
