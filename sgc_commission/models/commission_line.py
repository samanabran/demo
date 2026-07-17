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
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        readonly=False,
    )
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(16, 4)
    )
    base_amount = fields.Monetary(
        string='Base Amount',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        readonly=False,
        help='Auto-filled from the Sale Order according to the selected '
             'Commission Type\'s Calculation Base (Sale Value / Order Total '
             'excl. tax / Order Total incl. tax). Overridable.',
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

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.partner_id.is_commission_agent:
            if not self.commission_type_id and self.partner_id.commission_type_id:
                self.commission_type_id = self.partner_id.commission_type_id
            if not self.commission_rate and self.partner_id.commission_rate:
                self.commission_rate = self.partner_id.commission_rate

    @api.onchange('commission_type_id')
    def _onchange_commission_type_id(self):
        if self.commission_type_id and not self.commission_rate:
            self.commission_rate = self.commission_type_id.default_rate

    @api.depends('sale_order_id.amount_untaxed', 'sale_order_id.amount_total',
                 'sale_order_id.order_line.price_subtotal',
                 'commission_type_id.calculation_base',
                 'commission_type_id.calculation_method',
                 'commission_type_id.default_rate',
                 'commission_rate')
    def _compute_amounts(self):
        for line in self:
            order = line.sale_order_id
            ctype = line.commission_type_id
            base = order.amount_untaxed if order else 0.0
            if order and ctype:
                if ctype.calculation_base == 'unit_price':
                    base = sum(order.order_line.mapped('price_subtotal'))
                elif ctype.calculation_base == 'order_total':
                    base = order.amount_total
                else:
                    base = order.amount_untaxed
            line.base_amount = base

            rate = line.commission_rate or (ctype.default_rate if ctype else 0.0)
            if ctype and ctype.calculation_method == 'fixed':
                line.commission_amount = rate
            else:
                line.commission_amount = base * (rate / 100.0)
