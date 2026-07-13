# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AppraisalSurveyQuestion(models.Model):
    _name = 'appraisal.survey.question'
    _description = 'Appraisal Survey Question'
    _order = 'sequence, id'

    survey_id = fields.Many2one(
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
    question_text = fields.Text(
        string='Question Text',
        required=True
    )
    question_type = fields.Selection([
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
        ('rating', 'Rating'),
        ('date', 'Date'),
        ('numeric', 'Numeric'),
    ], string='Question Type', default='text', required=True)
    required = fields.Boolean(string='Required', default=False)
    sequence = fields.Integer(string='Sequence', default=10)
