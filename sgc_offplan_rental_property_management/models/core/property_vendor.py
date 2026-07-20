# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyVendor(models.Model):
    _name = 'property.vendor'
    _description = 'Property Vendor / Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Vendor Reference', required=True)
    property_id = fields.Many2one('property.details', string='Property')
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    broker_id = fields.Many2one('res.partner', string='Broker',
                                domain=[('user_type', '=', 'broker')])
    sale_price = fields.Monetary(string='Sale Price', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    # Bridge to canonical sale.contract model
    sale_contract_id = fields.Many2one(
        'sale.contract', string='Sale Contract',
        help='Linked sale.contract record. When set, this booking/vendor record is bridged to the canonical sales model.')

    contract_date = fields.Date(string='Contract Date')
    signed_via_portal = fields.Boolean(
        string='Signed via Portal',
        default=False,
        help='Marked when the customer clicked "I agree & sign" from the portal.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    sold_seq = fields.Char(string='Sold Seq')
    date = fields.Date(string='Date')
    notes = fields.Text(string='Notes')

    # -------------------------------------------------------------------------
    # COMMISSION DISTRIBUTION (multi-party, per-beneficiary lines)
    # -------------------------------------------------------------------------
    commission_line_ids = fields.One2many(
        'property.vendor.commission.line', 'vendor_id',
        string='Commission Lines',
        help='Named external and internal commission beneficiaries with individual rates',
    )
    total_external_commission = fields.Monetary(
        string='External Commission',
        currency_field='currency_id',
        compute='_compute_commission', store=True,
        help='Total external commission payable to broker/agency (sum of Commission Lines).')
    total_internal_commission = fields.Monetary(
        string='Internal Commission',
        currency_field='currency_id',
        compute='_compute_commission', store=True,
        help='Total internal commission (sum of Commission Lines).')
    total_commission = fields.Monetary(
        string='Total Commission',
        currency_field='currency_id',
        compute='_compute_commission', store=True)

    @api.depends('commission_line_ids.commission_amount', 'commission_line_ids.category')
    def _compute_commission(self):
        for rec in self:
            lines = rec.commission_line_ids
            rec.total_external_commission = sum(
                l.commission_amount for l in lines if l.category == 'external')
            rec.total_internal_commission = sum(
                l.commission_amount for l in lines if l.category == 'internal')
            rec.total_commission = rec.total_external_commission + rec.total_internal_commission

    # -------------------------------------------------------------------------
    # State transitions
    # -------------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
