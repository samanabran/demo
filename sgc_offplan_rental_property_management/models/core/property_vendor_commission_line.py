# -*- coding: utf-8 -*-
# Copyright 2026 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class PropertyVendorCommissionLine(models.Model):
    _name = 'property.vendor.commission.line'
    _description = 'Booking Commission Distribution Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    vendor_id = fields.Many2one(
        'property.vendor',
        string='Booking',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Beneficiary',
        required=True,
        help='Person or company receiving this commission',
    )
    category = fields.Selection([
        ('external', 'External'),
        ('internal', 'Internal'),
    ], string='Category', required=True, default='internal')
    role = fields.Selection([
        ('broker', 'Broker'),
        ('brokerage', 'Brokerage Company'),
        ('agent', 'Sales Agent'),
        ('manager', 'Manager'),
        ('referral', 'Referral'),
        ('office', 'Office/Company'),
        ('override', 'Override'),
        ('custom', 'Custom'),
    ], string='Role', required=True, default='agent')
    custom_role_name = fields.Char(
        string='Custom Role Name',
        help='Specify role name when role is "Custom"',
    )
    commission_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Commission Type', required=True, default='percentage')
    commission_percentage = fields.Float(
        string='Commission %',
        default=0.0,
        help='Percentage of sale price or total commission',
    )
    commission_fixed_amount = fields.Monetary(
        string='Fixed Amount',
        currency_field='currency_id',
        help='Fixed commission amount',
    )
    commission_amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id',
        compute='_compute_commission_amount',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='vendor_id.currency_id',
        store=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
    ], string='Payment Status', default='not_paid')
    notes = fields.Text(string='Notes')

    @api.depends('vendor_id.sale_price', 'commission_type',
                 'commission_percentage', 'commission_fixed_amount')
    def _compute_commission_amount(self):
        for line in self:
            base = line.vendor_id.sale_price or 0.0
            if line.commission_type == 'percentage':
                line.commission_amount = base * (line.commission_percentage / 100.0)
            else:
                line.commission_amount = line.commission_fixed_amount or 0.0

    def get_role_label(self):
        """Return human-readable role label."""
        self.ensure_one()
        if self.role == 'custom':
            return self.custom_role_name or 'Custom'
        return dict(self._fields['role'].selection).get(self.role, self.role)
