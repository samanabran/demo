# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RentContract(models.Model):
    _name = "rent.contract"
    _description = "Rent Contract"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Identity
    name = fields.Char(
        string="Contract Reference", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", string="Company",
        default=lambda self: self.env.company)

    # Parties
    property_id = fields.Many2one(
        "property.details", string="Property", required=True, tracking=True)
    tenant_id = fields.Many2one(
        "res.partner", string="Tenant", required=True, tracking=True)
    landlord_id = fields.Many2one(
        "res.partner", string="Landlord", tracking=True)

    # Dates
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    # Financial
    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        default=lambda self: self.env.company.currency_id)
    rent_amount = fields.Monetary(
        string="Rent Amount", currency_field="currency_id")
    security_deposit = fields.Monetary(
        string="Security Deposit", currency_field="currency_id")
    security_deposit_paid = fields.Boolean(
        string="Security Deposit Paid", default=False)
    deposit_paid_amount = fields.Monetary(
        string="Deposit Paid", currency_field="currency_id")
    deposit_returned_amount = fields.Monetary(
        string="Deposit Returned", currency_field="currency_id")
    deposit_deducted_amount = fields.Monetary(
        string="Deposit Deducted", currency_field="currency_id")
    renewal_requested = fields.Boolean(
        string="Renewal Requested", default=False)
    payment_frequency = fields.Selection([
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ], string="Payment Frequency", default="monthly")
    payment_cheque_count = fields.Integer(string="Number of Cheques")

    # UAE Ejari-style contract fields
    ejari_registration_number = fields.Char(string="Ejari Registration Number")
    furnished_status = fields.Selection([
        ("furnished", "Furnished"),
        ("unfurnished", "Unfurnished"),
    ], string="Furnishing Status", default="unfurnished")
    maintenance_responsibility = fields.Selection([
        ("landlord", "Landlord"),
        ("tenant", "Tenant"),
        ("shared", "Shared"),
    ], string="Maintenance Responsibility", default="shared")

    # Payment Schedule
    payment_schedule_id = fields.Many2one(
        "payment.schedule", string="Payment Schedule",
        domain=[("schedule_type", "=", "rental")])

    # Notes
    notes = fields.Text(string="Notes")

    # State
    state = fields.Selection([
        ("draft", "Draft"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", tracking=True)

    # E-signature fields
    signed_via_portal = fields.Boolean(
        string="Signed via Portal",
        readonly=True,
        help="Indicates if the tenant signed electronically via the portal."
    )

    # Computed
    duration_months = fields.Integer(
        string="Duration (Months)",
        compute="_compute_duration_months", store=True)
    total_rent = fields.Monetary(
        string="Total Rent", currency_field="currency_id",
        compute="_compute_total_rent", store=True)

    # Rent Bills
    rent_bill_count = fields.Integer(
        string="Rent Bills", compute="_compute_rent_bill_count")

    # -------------------------------------------------------------------------
    # Commission Distribution (dynamic lines)
    # -------------------------------------------------------------------------
    annual_rent_amount = fields.Monetary(
        string="Annual Rent", currency_field="currency_id",
        compute="_compute_annual_rent_amount", store=True,
        help="Rent amount normalized to a 12-month basis. Used as the commission "
             "calculation base, since rental commission is conventionally quoted "
             "against annual rent regardless of the lease term or payment frequency.")
    commission_line_ids = fields.One2many(
        'rent.commission.line', 'contract_id',
        string='Commission Lines',
        help='Dynamic commission distribution to external and internal parties',
    )
    commission_total_amount = fields.Monetary(
        string='Total Commission', currency_field='currency_id',
        compute='_compute_commission_totals', store=True,
    )
    commission_external_total = fields.Monetary(
        string='External Commission Total', currency_field='currency_id',
        compute='_compute_commission_totals', store=True,
    )
    commission_internal_total = fields.Monetary(
        string='Internal Commission Total', currency_field='currency_id',
        compute='_compute_commission_totals', store=True,
    )
    commission_line_count = fields.Integer(
        string='Commission Line Count',
        compute='_compute_commission_totals', store=True,
    )
    commission_bill_ids = fields.Many2many(
        'account.move',
        relation='rent_contract_commission_bill_rel',
        compute='_compute_commission_bill_ids',
        string='Commission Bills',
    )
    commission_bill_count = fields.Integer(
        string='Commission Bill Count',
        compute='_compute_commission_bill_ids',
    )
    is_commission_eligible = fields.Boolean(
        string='Commission Eligible', compute='_compute_commission_eligibility')
    commission_ineligible_reason = fields.Char(
        string='Commission Ineligibility Reason', compute='_compute_commission_eligibility')

    @api.depends("start_date", "end_date")
    def _compute_duration_months(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                delta = relativedelta(rec.end_date, rec.start_date)
                rec.duration_months = delta.years * 12 + delta.months
            else:
                rec.duration_months = 0

    @api.depends("rent_amount", "duration_months")
    def _compute_total_rent(self):
        for rec in self:
            rec.total_rent = rec.rent_amount * rec.duration_months

    @api.depends("rent_amount", "payment_frequency")
    def _compute_annual_rent_amount(self):
        periods = {"monthly": 12, "quarterly": 4, "yearly": 1}
        for rec in self:
            rec.annual_rent_amount = rec.rent_amount * periods.get(rec.payment_frequency, 12)

    def _compute_rent_bill_count(self):
        for rec in self:
            rec.rent_bill_count = self.env["rent.bill"].search_count(
                [("contract_id", "=", rec.id)])

    @api.depends('commission_line_ids.commission_amount', 'commission_line_ids.category')
    def _compute_commission_totals(self):
        for rec in self:
            lines = rec.commission_line_ids
            rec.commission_external_total = sum(
                l.commission_amount for l in lines if l.category == 'external')
            rec.commission_internal_total = sum(
                l.commission_amount for l in lines if l.category == 'internal')
            rec.commission_total_amount = rec.commission_external_total + rec.commission_internal_total
            rec.commission_line_count = len(lines)

    @api.depends('commission_line_ids.bill_id')
    def _compute_commission_bill_ids(self):
        for rec in self:
            bills = rec.commission_line_ids.bill_id
            rec.commission_bill_ids = bills
            rec.commission_bill_count = len(bills)

    @api.depends('state')
    def _compute_commission_eligibility(self):
        for rec in self:
            if rec.state == 'active':
                rec.is_commission_eligible = True
                rec.commission_ineligible_reason = False
            else:
                rec.is_commission_eligible = False
                rec.commission_ineligible_reason = _(
                    'Commission is eligible once the rent contract is confirmed (Active).')

    def _assign_reference(self):
        for contract in self:
            if not contract.name or contract.name == _('New'):
                contract.name = self.env['ir.sequence'].next_by_code('rent.contract') or _('New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rent.contract') or _('New')
        return super(RentContract, self).create(vals_list)

    # State transitions
    def action_activate(self):
        self.ensure_one()
        self._assign_reference()
        self.write({"state": "active"})
        if self.property_id:
            self.property_id.write({"state": "rented"})
        self.message_post(body=_("Contract activated. Property has been marked as rented."))

    def action_expire(self):
        self.ensure_one()
        self.write({"state": "expired"})
        if self.property_id:
            self.property_id.write({"state": "available"})
        self.message_post(body=_("Contract expired. Property is now available."))

    def action_cancel(self):
        self.ensure_one()
        self.write({"state": "cancelled"})
        if self.property_id:
            self.property_id.write({"state": "available"})
        self.message_post(body=_("Contract cancelled. Property is now available."))

    def action_request_renewal(self):
        self.ensure_one()
        self.renewal_requested = True
        self.message_post(body=_("Tenant requested lease renewal."))

    @api.model
    def cron_expire_contracts(self):
        today = fields.Date.context_today(self)
        expired = self.search([
            ("state", "=", "active"),
            ("end_date", "<", today),
        ])
        for contract in expired:
            contract.action_expire()
        return True

    def action_generate_rent_bills(self):
        self.ensure_one()
        if not self.start_date or not self.end_date:
            raise UserError(
                _("Please set both a start date and an end date before generating rent bills."))
        if not self.rent_amount:
            raise UserError(
                _("Please set a rent amount before generating rent bills."))

        self.env["rent.bill"].search([("contract_id", "=", self.id)]).unlink()

        months_step = {"monthly": 1, "quarterly": 3, "yearly": 12}.get(
            self.payment_frequency, 1)
        period_amount = self.rent_amount * months_step

        invoice_post_type = self.env['ir.config_parameter'].sudo().get_param(
            'sgc_offplan_rental_property_management.invoice_post_type')

        # Rent-billing product (Rent Installment). Mirrors how the other
        # invoice-creating paths resolve their configured product so the generated
        # move line carries a product, its income account and taxes instead of a
        # bare name/quantity/price_unit line.
        rent_product_id = self.env['ir.config_parameter'].sudo().get_param(
            'sgc_offplan_rental_property_management.account_installment_item_id')
        rent_product = (
            self.env['product.product'].browse(int(rent_product_id))
            if rent_product_id else
            self.env.ref(
                'sgc_offplan_rental_property_management.property_product_1',
                raise_if_not_found=False)
        )
        if rent_product and not rent_product.exists():
            rent_product = self.env['product.product']
        income_account = (
            rent_product.product_tmpl_id._get_product_accounts().get('income')
            if rent_product else False
        )

        property_label = self.property_id.display_name or _("Property")
        tenancy = self.env["tenancy.details"].search(
            [("tenancy_id", "=", self.id)], limit=1)
        count = 0
        current_date = self.start_date
        while current_date <= self.end_date:
            description = _("Rent - %s") % current_date.strftime("%B %Y")
            line_vals = {
                "name": "%s - %s" % (property_label, description),
                "quantity": 1,
                "price_unit": period_amount,
            }
            if rent_product:
                line_vals["product_id"] = rent_product.id
                line_vals["tax_ids"] = [(6, 0, rent_product.taxes_id.ids)]
                if income_account:
                    line_vals["account_id"] = income_account.id
            move = self.env["account.move"].create({
                "move_type": "out_invoice",
                "partner_id": self.tenant_id.id,
                "invoice_date": current_date,
                "invoice_origin": self.name,
                "currency_id": self.currency_id.id,
                "invoice_line_ids": [(0, 0, line_vals)],
            })
            if invoice_post_type == 'automatically':
                move.action_post()
            self.env["rent.bill"].create({
                "contract_id": self.id,
                "tenancy_id": tenancy.id,
                "rent_no": self.env['ir.sequence'].next_by_code('rent.bill') or _('New'),
                "vendor_id": self.landlord_id.id,
                "bill_type": _("Rent"),
                "description": description,
                "invoice_date": current_date,
                "amount": period_amount,
                "rent_amount": period_amount,
                "currency_id": self.currency_id.id,
                "company_id": self.company_id.id,
                "rent_bill_id": move.id,
            })
            count += 1
            current_date = current_date + relativedelta(months=months_step)

        if count:
            self.message_post(
                body=_("%d rent bill(s) generated.") % count)

    def action_view_rent_bills(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Rent Bills"),
            "res_model": "rent.bill",
            "view_mode": "list,form",
            "domain": [("contract_id", "=", self.id)],
            "context": {"default_contract_id": self.id},
        }

    # -------------------------------------------------------------------------
    # One-click: generate bills for every approved commission line on this
    # contract that hasn't been billed yet (vendor bill to landlord/company,
    # or customer invoice to the tenant depending on each line's payer_type).
    # -------------------------------------------------------------------------
    def action_generate_commission_bills(self):
        for contract in self:
            billable = contract.commission_line_ids.filtered(
                lambda l: l.state == 'approved' and not l.bill_id)
            if not billable:
                continue
            bills = billable._generate_bills(post=True)
            contract.message_post(
                body=_('%d commission bill(s) generated for %d line(s).') % (
                    len(bills), len(billable)))
        return True

    def action_view_commission_bills(self):
        self.ensure_one()
        return {
            'name': _('Commission Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.commission_bill_ids.ids)],
            'context': {'create': False},
        }

    # E-signature method
    def action_send_for_signature(self):
        self.ensure_one()
        self.signed_via_portal = True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": "Signature request sent (MVP demo)",
                "type": "success",
            }
        }
