# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta


class SaleContract(models.Model):
    _name = 'sale.contract'
    _description = 'Sale Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Contract Reference',
        required=True,
        tracking=True,
    )
    property_id = fields.Many2one(
        'property.details',
        string='Property',
        required=True,
        tracking=True,
    )
    buyer_id = fields.Many2one(
        'res.partner',
        string='Buyer',
        required=True,
        tracking=True,
    )
    seller_id = fields.Many2one(
        'res.partner',
        string='Seller',
        tracking=True,
    )
    sale_price = fields.Monetary(
        string='Sale Price',
        currency_field='currency_id',
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    contract_date = fields.Date(
        string='Contract Date',
        default=fields.Date.context_today,
        tracking=True,
    )
    handover_date = fields.Date(string='Handover Date')
    payment_schedule_id = fields.Many2one(
        'payment.schedule',
        string='Payment Schedule',
        domain=[('schedule_type', '=', 'sale')],
    )
    booking_amount = fields.Monetary(
        string='Booking Amount',
        currency_field='currency_id',
        help='Deposit paid upfront at time of booking.',
    )
    notes = fields.Text(string='Notes')
    signed_via_portal = fields.Boolean(
        string='Signed via Portal',
        default=False,
        help='Marked when the customer clicked "I agree & sign" from the portal.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    # -------------------------------------------------------------------------
    # Commission Distribution (dynamic lines)
    # -------------------------------------------------------------------------
    commission_line_ids = fields.One2many(
        'property.commission.line', 'contract_id',
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
        compute='_compute_commission_line_count',
    )

    @api.depends('commission_line_ids.commission_amount')
    def _compute_commission_totals(self):
        for rec in self:
            lines = rec.commission_line_ids
            rec.commission_external_total = sum(
                l.commission_amount for l in lines if l.category == 'external'
            )
            rec.commission_internal_total = sum(
                l.commission_amount for l in lines if l.category == 'internal'
            )
            rec.commission_total_amount = (
                rec.commission_external_total + rec.commission_internal_total
            )

    @api.depends('commission_line_ids')
    def _compute_commission_line_count(self):
        for rec in self:
            rec.commission_line_count = len(rec.commission_line_ids)

    # Legacy fields (kept for backward compatibility during migration)
    commission_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ], string='Commission Type (Legacy)', default='percentage',
        help='Deprecated: use commission lines instead.')
    commission_percentage = fields.Float(
        string='Commission % (Legacy)', default=2.0,
        help='Deprecated: use commission lines instead.')
    commission_fixed_amount = fields.Monetary(
        string='Fixed Commission Amount (Legacy)', currency_field='currency_id',
        help='Deprecated: use commission lines instead.')
    broker_id = fields.Many2one('res.partner', string='Broker (Legacy)',
                                domain=[('user_type', '=', 'broker')],
                                help='Deprecated: use commission lines instead.')
    broker_agency_id = fields.Many2one(
        'res.partner', string='Brokerage Company (Legacy)',
        domain=[('is_company', '=', True)],
        help='Deprecated: use commission lines instead.')
    broker_bill_id = fields.Many2one('account.move', string='Broker Bill', readonly=True)
    broker_bill_payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
    ], string='Broker Bill Payment Status', default='not_paid')
    total_external_commission = fields.Monetary(
        string='External Commission (Legacy)', currency_field='currency_id',
        compute='_compute_commission_legacy', store=True)

    # Legacy internal commission fields
    company_commission_pct = fields.Float(string='Company Commission % (Legacy)', default=0.0)
    agent_commission_pct = fields.Float(string='Agent Commission % (Legacy)', default=0.0)
    referral_commission_pct = fields.Float(string='Referral Commission % (Legacy)', default=0.0)
    office_commission_pct = fields.Float(string='Office Commission % (Legacy)', default=0.0)
    commission_override_pct = fields.Float(string='Override % (Legacy)', default=0.0)
    total_internal_commission = fields.Monetary(
        string='Internal Commission (Legacy)', currency_field='currency_id',
        compute='_compute_commission_legacy', store=True)

    total_commission = fields.Monetary(
        string='Total Commission (Legacy)', currency_field='currency_id',
        compute='_compute_commission_legacy', store=True)

    @api.depends('sale_price', 'commission_type', 'commission_percentage',
                 'commission_fixed_amount')
    def _compute_commission_legacy(self):
        for rec in self:
            base = rec.sale_price or 0.0
            if rec.commission_type == 'percentage':
                ext = base * (rec.commission_percentage / 100.0)
            else:
                ext = rec.commission_fixed_amount or 0.0
            rec.total_external_commission = ext
            internal_pct = (
                rec.company_commission_pct +
                rec.agent_commission_pct +
                rec.referral_commission_pct +
                rec.office_commission_pct +
                rec.commission_override_pct
            )
            rec.total_internal_commission = base * (internal_pct / 100.0)
            rec.total_commission = ext + rec.total_internal_commission

    def action_create_commission_line(self):
        self.ensure_one()
        return {
            'name': _('Add Commission Line'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.commission.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_currency_id': self.currency_id.id,
            },
        }

    # Installment relation
    installment_ids = fields.One2many(
        'sale.contract.installment',
        'contract_id',
        string='Installments',
    )
    installment_count = fields.Integer(
        string='Installment Count',
        compute='_compute_installment_count',
    )
    total_paid = fields.Monetary(
        string='Total Paid',
        currency_field='currency_id',
        compute='_compute_total_paid',
        store=True,
    )

    # -------------------------------------------------------------------------
    # Computes
    # -------------------------------------------------------------------------

    @api.depends('installment_ids')
    def _compute_installment_count(self):
        for contract in self:
            contract.installment_count = len(contract.installment_ids)

    @api.depends('installment_ids.amount', 'installment_ids.state')
    def _compute_total_paid(self):
        for contract in self:
            contract.total_paid = sum(
                line.amount for line in contract.installment_ids
                if line.state == 'paid'
            )

    # -------------------------------------------------------------------------
    # State transitions
    # -------------------------------------------------------------------------

    def _assign_reference(self):
        for contract in self:
            if not contract.name or contract.name == _('New'):
                contract.name = self.env['ir.sequence'].next_by_code('sale.contract') or _('New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.contract') or _('New')
        return super(SaleContract, self).create(vals_list)

    def action_sign(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(_('Only draft contracts can be signed.'))
            contract._assign_reference()
            contract.state = 'signed'
            # Signing reserves the property; it isn't actually sold until the
            # contract is completed (handover/final payment) via action_complete.
            if contract.property_id:
                contract.property_id.state = 'booked'

    def action_complete(self):
        for contract in self:
            if contract.state != 'signed':
                raise UserError(_('Only signed contracts can be marked as completed.'))
            contract._assign_reference()
            contract.state = 'completed'
            if contract.property_id:
                contract.property_id.state = 'sold'

    def action_cancel(self):
        for contract in self:
            if contract.state in ('completed', 'cancelled'):
                raise UserError(_('Completed or already cancelled contracts cannot be cancelled.'))
            contract.state = 'cancelled'
            if contract.property_id:
                contract.property_id.state = 'available'

    # -------------------------------------------------------------------------
    # Installment generation
    # -------------------------------------------------------------------------

    def action_generate_installments(self):
        """Generate installment lines from the linked payment schedule template."""
        self.ensure_one()
        if not self.payment_schedule_id:
            raise UserError(_('Please select a Payment Schedule before generating installments.'))
        if not self.contract_date:
            raise UserError(_('Please set a Contract Date before generating installments.'))

        # Remove existing draft installments only
        draft_lines = self.installment_ids.filtered(lambda l: l.state == 'pending')
        draft_lines.unlink()

        sequence = 1
        installment_vals = []
        for line in self.payment_schedule_id.schedule_line_ids.sorted('sequence'):
            # Determine the interval in days per frequency
            freq_days = {
                'one_time': 0,
                'monthly': 30,
                'quarterly': 90,
                'bi_annual': 180,
                'annual': 365,
            }.get(line.installment_frequency, 0)

            n = max(line.number_of_installments, 1)
            # Amount per installment split
            if n > 1 and freq_days > 0:
                amount_each = (self.sale_price * line.percentage / 100.0) / n
                for i in range(n):
                    due = self.contract_date + timedelta(days=line.days_after + freq_days * i)
                    installment_vals.append({
                        'contract_id': self.id,
                        'name': '%s — %d/%d' % (line.name, i + 1, n),
                        'sequence': sequence,
                        'due_date': due,
                        'percentage': line.percentage / n,
                        'amount': amount_each,
                        'state': 'pending',
                        'currency_id': self.currency_id.id,
                    })
                    sequence += 1
            else:
                due = self.contract_date + timedelta(days=line.days_after)
                installment_vals.append({
                    'contract_id': self.id,
                    'name': line.name,
                    'sequence': sequence,
                    'due_date': due,
                    'percentage': line.percentage,
                    'amount': self.sale_price * line.percentage / 100.0,
                    'state': 'pending',
                    'currency_id': self.currency_id.id,
                })
                sequence += 1

        self.env['sale.contract.installment'].create(installment_vals)

    # -------------------------------------------------------------------------
    # Smart button action
    # -------------------------------------------------------------------------

    def action_view_installments(self):
        self.ensure_one()
        return {
            'name': _('Installments'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.contract.installment',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }

    # -------------------------------------------------------------------------
    # Invoices smart button (invoices generated from installments)
    # -------------------------------------------------------------------------

    invoice_ids = fields.Many2many(
        'account.move',
        compute='_compute_invoice_ids',
        string='Invoices',
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_ids',
    )

    @api.depends('installment_ids.invoice_id')
    def _compute_invoice_ids(self):
        for contract in self:
            invoices = contract.installment_ids.invoice_id
            contract.invoice_ids = invoices
            contract.invoice_count = len(invoices)

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'create': False},
        }

    # -------------------------------------------------------------------------
    # Commission bills smart button (vendor bills generated from commission
    # lines)
    # -------------------------------------------------------------------------

    commission_bill_ids = fields.Many2many(
        'account.move',
        relation='sale_contract_commission_bill_rel',
        compute='_compute_commission_bill_ids',
        string='Commission Bills',
    )
    commission_bill_count = fields.Integer(
        string='Commission Bill Count',
        compute='_compute_commission_bill_ids',
    )

    @api.depends('commission_line_ids.bill_id')
    def _compute_commission_bill_ids(self):
        for contract in self:
            bills = contract.commission_line_ids.bill_id
            contract.commission_bill_ids = bills
            contract.commission_bill_count = len(bills)

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

    # -------------------------------------------------------------------------
    # Overall payment status — summarizes the payment_state of every invoice
    # generated for this contract's installments, so the form/list can show
    # at a glance whether the buyer is fully paid, partially paid, or not
    # paid, without opening each invoice individually.
    # -------------------------------------------------------------------------

    overall_payment_state = fields.Selection([
        ('no_invoices', 'No Invoices'),
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ], string='Payment Status', compute='_compute_overall_payment_state', store=True)

    @api.depends('installment_ids.invoice_id.payment_state', 'installment_ids.invoice_id.state')
    def _compute_overall_payment_state(self):
        for contract in self:
            invoices = contract.installment_ids.invoice_id.filtered(lambda m: m.state == 'posted')
            if not invoices:
                contract.overall_payment_state = 'no_invoices'
            elif all(inv.payment_state == 'paid' for inv in invoices):
                contract.overall_payment_state = 'paid'
            elif any(inv.payment_state in ('paid', 'partial', 'in_payment') for inv in invoices):
                contract.overall_payment_state = 'partial'
            else:
                contract.overall_payment_state = 'not_paid'

    # -------------------------------------------------------------------------
    # Bulk installment invoicing — one click generates the customer invoice
    # for every pending installment on the contract.
    # -------------------------------------------------------------------------

    def action_generate_installment_invoices(self):
        for contract in self:
            pending_lines = contract.installment_ids.filtered(
                lambda l: not l.invoice_id and l.state != 'cancelled')
            pending_lines._generate_invoices(post=True)
            if pending_lines:
                contract.message_post(
                    body=_('%d installment invoice(s) generated.') % len(pending_lines))
        return True

    # -------------------------------------------------------------------------
    # Cron hook — keeps overdue flag honest without user intervention.
    # Triggered daily. Idempotent: nothing destructive, just refreshes state.
    # -------------------------------------------------------------------------

    @api.model
    def cron_refresh_installment_overdue(self):
        cutoff = fields.Date.subtract(fields.Date.context_today(self), days=0)
        stale = self.env['sale.contract.installment'].search([
            ('state', 'in', ['pending', 'invoiced']),
            ('due_date', '<', cutoff),
        ])
        if stale:
            # Trigger recompute by re-writing an unchanged value
            stale.write({'sequence': lambda l: l.sequence})  # no-op but forces store recompute
        return True

    # -------------------------------------------------------------------------
    # One-click: generate customer invoices for every pending installment
    # on this contract. The installment line state is then auto-derived from
    # the invoice's payment_state (paid / partial / overdue) and the due date.
    # -------------------------------------------------------------------------

    def action_generate_installment_invoices(self):
        for contract in self:
            pending_lines = contract.installment_ids.filtered(
                lambda l: not l.invoice_id and l.state != 'cancelled')
            if not pending_lines:
                continue
            pending_lines._generate_invoices(post=True)
            contract.message_post(
                body=_('%d installment invoice(s) generated.') % len(pending_lines))
        return True

    # -------------------------------------------------------------------------
    # Daily cron — keeps the overdue flag honest for pending/invoiced lines
    # whose due date has passed without an invoice being posted/paid.
    # -------------------------------------------------------------------------

    @api.model
    def cron_refresh_installment_overdue(self):
        today = fields.Date.context_today(self)
        stale = self.env['sale.contract.installment'].search([
            ('state', 'in', ['pending', 'invoiced']),
            ('due_date', '!=', False),
            ('due_date', '<', today),
        ])
        for line in stale:
            line._compute_state()
        return True

    # -------------------------------------------------------------------------
    # One-click: generate vendor bills for every approved commission line on
    # this contract that hasn't been billed yet (one bill per beneficiary).
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
