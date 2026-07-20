# -*- coding: utf-8 -*-
# Copyright 2026 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RentCommissionLine(models.Model):
    _name = 'rent.commission.line'
    _inherit = ['property.commission.line.mixin']
    _description = 'Rent Commission Distribution Line'

    contract_id = fields.Many2one(
        'rent.contract',
        string='Rent Contract',
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
        selection_add=[('contract_value', 'Annual Rent')],
        ondelete={'contract_value': 'set default'},
    )
    base_line_id = fields.Many2one(
        'rent.commission.line',
        string='Base Commission Line',
        domain="[('contract_id', '=', contract_id), ('id', '!=', id)]",
        help='The other beneficiary line this percentage is calculated against, '
             'when Commission Base is "Another Commission Line".',
    )
    payer_type = fields.Selection([
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
        ('company', 'Company (internal)'),
    ], string='Payer', required=True, default='landlord',
        help='Who is actually charged for this commission line. In Dubai, brokerage '
             'commission on rentals is commonly charged to the tenant rather than the '
             'landlord — set this per line to match the deal.')

    @api.depends('contract_id.annual_rent_amount', 'commission_type', 'commission_base',
                 'commission_percentage', 'commission_fixed_amount', 'base_line_id')
    def _compute_commission_amount(self):
        self._set_commission_amounts()

    def _get_contract_value_base(self):
        self.ensure_one()
        return self.contract_id.annual_rent_amount or 0.0

    def _get_base_line(self):
        self.ensure_one()
        return self.base_line_id

    @api.constrains('commission_base', 'base_line_id')
    def _check_base_line(self):
        super()._check_base_line()

    def _get_parent_contract(self):
        self.ensure_one()
        return self.contract_id

    def _get_bill_move_type(self):
        self.ensure_one()
        return 'out_invoice' if self.payer_type == 'tenant' else 'in_invoice'

    def _get_bill_partner(self):
        self.ensure_one()
        if self.payer_type == 'tenant':
            return self.contract_id.tenant_id
        if self.payer_type == 'landlord':
            return self.contract_id.landlord_id
        return self.partner_id

    def _check_commission_eligible(self):
        for line in self:
            contract = line.contract_id
            if not contract.is_commission_eligible:
                raise UserError(_(
                    'Cannot generate a commission bill for %s: %s'
                ) % (contract.display_name, contract.commission_ineligible_reason or _('not yet eligible.')))
