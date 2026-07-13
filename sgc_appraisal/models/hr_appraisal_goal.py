# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrAppraisalGoal(models.Model):
    _name = 'hr.appraisal.goal'
    _description = 'Appraisal Goal'
    _order = 'sequence, id'

    appraisal_id = fields.Many2one(
        'hr.appraisal',
        string='Appraisal',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Goal', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('achieved', 'Achieved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    progress = fields.Float(string='Progress (%)', default=0.0)
