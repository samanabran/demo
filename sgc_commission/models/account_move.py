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

    # -------------------------------------------------------------------------
    # Bill <-> commission line state sync.
    # commission.line's workflow buttons are driven purely by its state
    # ("Generate Bill" for calculated/confirmed, "View Bill" for
    # processed/paid), so whenever the bill itself changes lifecycle the
    # billed lines must follow, otherwise a cancelled/reset/deleted bill
    # would strand its lines in 'processed' forever with no way to re-bill.
    # -------------------------------------------------------------------------

    def _get_billed_commission_lines(self):
        """Commission lines currently billed by these moves.

        Filters on the line's *current* bill_id: journal items keep
        commission_line_id pointing at a line even after that line was
        re-billed by a newer move, and acting on the stale reference would
        wrongly release a live link (e.g. deleting an old cancelled bill
        must not touch a line already billed by a new one).
        """
        return self.mapped('line_ids.commission_line_id').filtered(
            lambda l: l.bill_id.id in self.ids)

    def action_post(self):
        """A commission bill may only be posted once the related customer
        invoice (same sale order) is fully paid. After posting, billed
        commission lines are marked processed."""
        for move in self:
            commission_lines = move.line_ids.commission_line_id.filtered(
                lambda l: l._name == 'commission.line')
            if commission_lines:
                commission_lines._check_commission_eligible()
        res = super().action_post()
        self._get_billed_commission_lines().write({'state': 'processed'})
        return res

    def button_draft(self):
        res = super().button_draft()
        # Back to draft: release the lines to 'confirmed' but KEEP bill_id so
        # they cannot be double-billed while a draft bill still exists —
        # posting that same bill flips them back to processed.
        self._get_billed_commission_lines().write({'state': 'confirmed'})
        return res

    def button_cancel(self):
        res = super().button_cancel()
        # Cancelled: fully release the lines for re-billing.
        self._get_billed_commission_lines().write(
            {'state': 'confirmed', 'bill_id': False})
        return res

    def unlink(self):
        commission_lines = self._get_billed_commission_lines()
        res = super().unlink()
        # Bill removed entirely: release its lines for re-billing (bill_id is
        # also cleared DB-side by ondelete='set null'; the explicit write
        # restores the state so "Generate Bill" becomes available again).
        commission_lines.write({'state': 'confirmed', 'bill_id': False})
        return res
