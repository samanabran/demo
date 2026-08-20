# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        """When a customer invoice is posted, generate the linked sale
        order's commission lines (draft -> calculated) and record the source
        invoice on them, which later gates commission bill posting."""
        res = super()._post(soft=soft)
        self.filtered(lambda m: m.move_type == 'out_invoice')._generate_commissions()
        return res

    def _generate_commissions(self):
        for move in self:
            for order in move._get_commission_sale_orders():
                order._generate_commissions_from_invoice(move)

    def _get_commission_sale_orders(self):
        self.ensure_one()
        orders = self.line_ids.sale_line_ids.order_id
        if 'sale_order_deal_id' in self._fields and self.sale_order_deal_id:
            orders |= self.sale_order_deal_id
        if self.invoice_origin:
            orders |= self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        return orders

    def action_post(self):
        """A commission bill may only be posted once the related customer
        invoice (same sale order) is fully paid."""
        for move in self:
            commission_lines = move.line_ids.commission_line_id.filtered(
                lambda l: l._name == 'commission.line')
            if commission_lines:
                commission_lines._check_commission_eligible()
        return super().action_post()