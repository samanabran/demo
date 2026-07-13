# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TenancyInquiry(models.Model):
    _name = 'tenancy.inquiry'
    _description = 'Tenancy Inquiry'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True)
    property_id = fields.Many2one('property.details', string='Property')
    tenant_id = fields.Many2one('res.partner', string='Tenant')
    inquiry_date = fields.Date(string='Inquiry Date')
    state = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('closed', 'Closed'),
    ], string='Status', default='new')
