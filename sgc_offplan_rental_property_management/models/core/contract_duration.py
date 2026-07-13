# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ContractDuration(models.Model):
    _name = 'contract.duration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Contract Duration'
    _order = 'name'

    name = fields.Char(string='Duration', required=True)
    duration = fields.Char(string='Duration Label')
    month = fields.Integer(string='Month')
    rent_unit = fields.Selection([
        ('month', 'Month'),
        ('year', 'Year'),
        ('day', 'Day'),
    ], string='Rent Unit', required=True, default='month')
    duration_days = fields.Integer(string='Duration (Days)')
    duration_months = fields.Integer(string='Duration (Months)')
