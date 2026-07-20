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
    commission_base = fields.Selection(
        selection_add=[('contract_value', 'Sale Price')],
        ondelete={'contract_value': 'set default'},
    )
    base_line_id = fields.Many2one(
        'property.commission.line',
        string='Base Commission Line',
        domain="[('contract_id', '=', contract_id), ('id', '!=', id)]",
        help='The other beneficiary line this percentage is calculated against, '
             'when Commission Base is "Another Commission Line".',
    )

    @api.depends('contract_id.sale_price', 'commission_type', 'commission_base',
                 'commission_percentage', 'commission_fixed_amount',
                 'base_line_id.commission_amount')
    def _compute_commission_amount(self):
        for line in self:
            line.commission_amount = line._calc_amount()

    def _get_contract_value_base(self):
        self.ensure_one()
        return self.contract_id.sale_price or 0.0

    def _get_base_line(self):
        self.ensure_one()
        return self.base_line_id

    @api.constrains('commission_base', 'base_line_id')
    def _check_base_line(self):
        super()._check_base_line()

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
