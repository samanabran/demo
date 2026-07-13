# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CommissionLine(models.Model):
    """Individual commission line for a sale order."""
    _name = 'commission.line'
    _description = 'Commission Line'
    _order = 'id desc'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Commission Agent',
        required=True
    )
    commission_type_id = fields.Many2one(
        'commission.type',
        string='Commission Type'
    )
    commission_amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id'
    )
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(16, 4)
    )
    base_amount = fields.Monetary(
        string='Base Amount',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='sale_order_id.currency_id',
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

