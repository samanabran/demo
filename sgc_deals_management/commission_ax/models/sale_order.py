# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_ids = fields.One2many('commission.main', 'sale_order_id', string='Commissions')
    commission_total = fields.Monetary(string='Commission Total', compute='_compute_commission_total', store=True)

    @api.depends('commission_ids', 'commission_ids.amount', 'commission_ids.state')
    def _compute_commission_total(self):
        for order in self:
            total = sum(order.commission_ids.filtered(lambda c: c.state in ('draft', 'confirmed', 'paid')).mapped('amount'))
            order.commission_total = total
