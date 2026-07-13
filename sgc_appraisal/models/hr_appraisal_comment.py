# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrAppraisalComment(models.Model):
    _name = 'hr.appraisal.comment'
    _description = 'Appraisal Comment'
    _order = 'id desc'

    appraisal_id = fields.Many2one(
        'hr.appraisal',
        string='Appraisal',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Subject', required=True)
    body = fields.Text(string='Comment')
    comment_type = fields.Selection([
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('peer', 'Peer'),
        ('other', 'Other'),
    ], string='Comment Type', default='manager')
    author_id = fields.Many2one(
        'res.users',
        string='Author',
        default=lambda self: self.env.user
    )
