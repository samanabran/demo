# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HrAppraisal(models.Model):
    _name = 'hr.appraisal'
    _description = 'Employee Appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Appraisal Name', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', required=True, tracking=True)
    date_from = fields.Date(string='Period From', required=True)
    date_to = fields.Date(string='Period To', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Appraisal components
    goal_ids = fields.One2many('hr.appraisal.goal', 'appraisal_id', string='Goals')
    comment_ids = fields.One2many('hr.appraisal.comment', 'appraisal_id', string='Comments')

    # Multi-company support
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    # Record rule field
    creater_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user
    )
