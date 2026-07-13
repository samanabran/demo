# -*- coding: utf-8 -*-
from odoo import api, models


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def _get_reconciled_moves(self):
        return (self.debit_move_id.move_id | self.credit_move_id.move_id)

    @api.model_create_multi
    def create(self, vals_list):
        partials = super().create(vals_list)
        partials._get_reconciled_moves()._trigger_project_financials_recompute()
        return partials

    def unlink(self):
        moves = self._get_reconciled_moves()
        res = super().unlink()
        moves._trigger_project_financials_recompute()
        return res
