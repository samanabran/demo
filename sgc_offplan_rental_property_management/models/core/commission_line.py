# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionLine(models.Model):
    _name = 'property.commission.line'
    _inherit = ['property.commission.line.mixin']
    _description = 'Sale Commission Distribution Line'

    contract_id = fields.Many2one(
        'sale.contract',
        string='Sale Contract',
        required=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='contract_id.currency_id',
        store=True,
    )

    @api.depends('contract_id.sale_price', 'commission_type',
                 'commission_percentage', 'commission_fixed_amount')
    def _compute_commission_amount(self):
        for line in self:
            line.commission_amount = line._calc_amount(line.contract_id.sale_price or 0.0)

    def _get_parent_contract(self):
        self.ensure_one()
        return self.contract_id

    def _check_commission_eligible(self):
        for line in self:
            contract = line.contract_id
            if not contract.is_commission_eligible:
                raise UserError(_(
                    'Cannot generate a commission bill for %s: %s'
                ) % (contract.display_name, contract.commission_ineligible_reason or _('not yet eligible.')))
