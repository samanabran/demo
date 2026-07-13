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
    # EXTERNAL COMMISSION (Broker / Agency)
    # -------------------------------------------------------------------------
    commission_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ], string='Commission Type', default='percentage')
    commission_percentage = fields.Float(
        string='Commission %',
        default=2.0,
        help='Broker commission percentage. Default 2% per DLD standard.')
    commission_fixed_amount = fields.Monetary(
        string='Fixed Commission Amount',
        currency_field='currency_id',
        help='Fixed commission amount when type is Fixed.')
    broker_agency_id = fields.Many2one(
        'res.partner', string='Brokerage Company',
        domain=[('is_company', '=', True)],
        help='The brokerage/agency company the broker belongs to.')
    broker_bill_id = fields.Many2one('account.move', string='Broker Bill', readonly=True)
    broker_bill_payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
    ], string='Broker Bill Payment Status', default='not_paid')
    commission_split_type = fields.Selection([
        ('no_split', 'No Split — Full to Broker'),
        ('percentage', 'Split by Percentage'),
        ('fixed', 'Split by Fixed Amount'),
    ], string='Commission Split Type', default='no_split')
    commission_split_percentage = fields.Float(
        string='Broker Split %',
        default=100.0,
        help='Percentage of commission going to the broker. Remainder goes to the agency/company.')
    commission_split_fixed_amount = fields.Monetary(
        string='Broker Split Fixed Amount',
        currency_field='currency_id',
        help='Fixed amount of commission going to the broker. Remainder goes to the agency/company.')
    total_external_commission = fields.Monetary(
        string='External Commission',
        currency_field='currency_id',
        compute='_compute_commission', store=True,
        help='Total external commission payable to broker/agency.')

    # -------------------------------------------------------------------------
    # INTERNAL COMMISSION (Company / Agent / Referral / Office split)
    # -------------------------------------------------------------------------
    company_commission_pct = fields.Float(
        string='Company Commission %', default=0.0,
        help='Commission percentage retained by the company.')
    agent_commission_pct = fields.Float(
        string='Agent Commission %', default=0.0,
        help='Commission percentage allocated to the sales agent.')
    referral_commission_pct = fields.Float(
        string='Referral Commission %', default=0.0,
        help='Commission percentage allocated for referral fees.')
    office_commission_pct = fields.Float(
        string='Office Commission %', default=0.0,
        help='Commission percentage allocated to the office/branch.')
    commission_override_pct = fields.Float(
        string='Override %', default=0.0,
        help='Override commission percentage for senior management/broker.')
    total_internal_commission = fields.Monetary(
        string='Internal Commission',
        currency_field='currency_id',
        compute='_compute_commission', store=True,
        help='Total internal commission from company/agent/referral/office splits.')
    total_commission = fields.Monetary(
        string='Total Commission',
        currency_field='currency_id',
        compute='_compute_commission', store=True)

    # -------------------------------------------------------------------------
    # NAMED COMMISSION DISTRIBUTION (multi-party, supersedes the fixed
    # percentage fields above when lines are present)
    # -------------------------------------------------------------------------
    commission_line_ids = fields.One2many(
        'property.vendor.commission.line', 'vendor_id',
        string='Commission Lines',
        help='Named external and internal commission beneficiaries with individual rates',
    )

    # -------------------------------------------------------------------------
    # Computes
    # -------------------------------------------------------------------------
    @api.depends('sale_price', 'commission_type', 'commission_percentage',
                 'commission_fixed_amount', 'company_commission_pct',
                 'agent_commission_pct', 'referral_commission_pct',
                 'office_commission_pct', 'commission_override_pct',
                 'commission_line_ids.commission_amount', 'commission_line_ids.category')
    def _compute_commission(self):
        for rec in self:
            if rec.commission_line_ids:
                lines = rec.commission_line_ids
                rec.total_external_commission = sum(
                    l.commission_amount for l in lines if l.category == 'external')
                rec.total_internal_commission = sum(
                    l.commission_amount for l in lines if l.category == 'internal')
                rec.total_commission = rec.total_external_commission + rec.total_internal_commission
                continue

            base = rec.sale_price or 0.0
            # External
            if rec.commission_type == 'percentage':
                ext = base * (rec.commission_percentage / 100.0)
            else:
                ext = rec.commission_fixed_amount or 0.0
            rec.total_external_commission = ext

            # Internal
            internal_pct = (
                rec.company_commission_pct +
                rec.agent_commission_pct +
                rec.referral_commission_pct +
                rec.office_commission_pct +
                rec.commission_override_pct
            )
            rec.total_internal_commission = base * (internal_pct / 100.0)

            # Combined total (external + internal)
            rec.total_commission = ext + rec.total_internal_commission

    # -------------------------------------------------------------------------
    # State transitions
    # -------------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
