# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AppraisalSurveyQuestionOption(models.Model):
    _name = 'appraisal.survey.question.option'
    _description = 'Appraisal Survey Question Option'
    _order = 'sequence, id'

    question_id = fields.Many2one(
        'appraisal.survey.question',
        string='Question',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Option Text', required=True)
    value = fields.Char(string='Value')
    sequence = fields.Integer(string='Sequence', default=10)
