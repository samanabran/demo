# -*- coding: utf-8 -*-
# Copyright 2026 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class PropertyVendorCommissionLine(models.Model):
    _name = 'property.vendor.commission.line'
    _inherit = ['property.commission.line.mixin']
    _description = 'Booking Commission Distribution Line'

    vendor_id = fields.Many2one(
        'property.vendor',
        string='Booking',
        required=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='vendor_id.currency_id',
        store=True,
    )

    @api.depends('vendor_id.sale_price', 'commission_type',
                 'commission_percentage', 'commission_fixed_amount')
    def _compute_commission_amount(self):
        for line in self:
            line.commission_amount = line._calc_amount(line.vendor_id.sale_price or 0.0)

    def _get_parent_contract(self):
        self.ensure_one()
        return self.vendor_id
