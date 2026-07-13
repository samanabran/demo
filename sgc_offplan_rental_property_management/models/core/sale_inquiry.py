# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleInquiry(models.Model):
    _name = 'sale.inquiry'
    _description = 'Sale Inquiry'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True)
    property_id = fields.Many2one('property.details', string='Property')
    buyer_id = fields.Many2one('res.partner', string='Buyer')
    inquiry_date = fields.Date(string='Inquiry Date')
    state = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('closed', 'Closed'),
    ], string='Status', default='new')
