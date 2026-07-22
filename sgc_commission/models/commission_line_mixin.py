# -*- coding: utf-8 -*-
# Copyright 2026 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
#
# Relocated from sgc_offplan_rental_property_management/models/core/
# commission_line_mixin.py (was _name='property.commission.line.mixin').
# The model was renamed to a neutral commission.line.mixin so it can be the
# shared base for every per-beneficiary commission line in the suite —
# property mgmt's sale/rent/vendor lines AND sgc_commission's own
# commission.line. Pure code move, zero runtime behavior change.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CommissionLineMixin(models.AbstractModel):
    """Shared field set + billing logic for per-beneficiary commission lines.

    Concrete models (commission.line for sale.order,
    property.commission.line for sale.contract,
    rent.commission.line for rent.contract,
    property.vendor.commission.line for property.vendor bookings) add their
    own parent Many2one and override the hooks below to plug in their parent's
    price base, eligibility rule, and which partner/move type a generated
    bill should target.
    """
    _name = 'commission.line.mixin'
    _description = 'Commission Distribution Line (shared)'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    partner_id = fields.Many2one(
        'res.partner',
        string='Beneficiary',
        required=True,
        help='Person or company receiving this commission (broker, brokerage company, agent, or internal employee).',
    )
    category = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('others', 'Others'),
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
    computation_type = fields.Selection([
        ('property_price', 'Property Price'),
        ('fixed_amount', 'Fixed Amount'),
        ('commission_received', 'Commission Received'),
    ], string='Computation Type', required=True, default='property_price',
        help='Property Price: a percentage of the total property/contract value. '
             'Fixed Amount: a flat amount, no percentage involved. '
             'Commission Received: a percentage of another beneficiary\'s commission '
             '(e.g. an agent split quoted against the broker\'s payout, not the price).')
    commission_percentage = fields.Float(
        string='Rate %',
        default=0.0,
        help='Percentage applied under Property Price or Commission Received.',
    )
    commission_fixed_amount = fields.Monetary(
        string='Fixed Amount',
        currency_field='currency_id',
        help='Flat commission amount, used when Computation Type is Fixed Amount.',
    )
    commission_amount = fields.Monetary(
        string='Total w/o Tax',
        currency_field='currency_id',
        compute='_compute_commission_amount',
        store=True,
        help='Commission amount before tax.',
    )
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        help='Optional. Typically only set for External party commission '
             '(e.g. VAT on a brokerage invoice) — leave empty for internal splits.',
    )
    amount_tax = fields.Monetary(
        string='Tax Amount',
        currency_field='currency_id',
        compute='_compute_amount_total',
        store=True,
    )
    amount_total = fields.Monetary(
        string='Total w/ Tax',
        currency_field='currency_id',
        compute='_compute_amount_total',
        store=True,
        help='Commission amount including tax. This is the amount actually billed.',
    )
    currency_id = fields.Many2one('res.currency', string='Currency')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    bill_id = fields.Many2one(
        'account.move',
        string='Bill',
        ondelete='set null',
        index=True,
        help='Bill raised to charge/pay this commission line.',
    )
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
    ], string='Payment Status', compute='_compute_payment_state', store=True, default='not_paid')
    notes = fields.Text(string='Notes')

    def _get_contract_value_base(self):
        """Override: return the total property/contract value (sale price,
        annual rent, etc.) used when computation_type == 'property_price'."""
        self.ensure_one()
        return 0.0

    def _get_base_line(self):
        """Override: return the self-referencing base_line_id field value
        used when computation_type == 'commission_received'. Empty
        recordset by default for concrete models that don't declare that
        field."""
        self.ensure_one()
        return self.browse()

    def _get_base_amount(self):
        self.ensure_one()
        if self.computation_type == 'commission_received':
            return self._get_base_line().commission_amount
        return self._get_contract_value_base()

    def _calc_amount(self):
        self.ensure_one()
        if self.computation_type == 'fixed_amount':
            return self.commission_fixed_amount or 0.0
        return (self._get_base_amount() or 0.0) * (self.commission_percentage / 100.0)

    def _compute_commission_amount(self):
        # Concrete models override this with their own @api.depends (the base
        # amount lives on a different parent field per model) and call
        # line._set_commission_amounts(). Base implementation here is a safe
        # no-op fallback so the abstract model itself stays instantiable-free.
        self._set_commission_amounts()

    def _set_commission_amounts(self):
        # Shared body for every concrete model's _compute_commission_amount.
        # After computing each line's own amount, explicitly cascades to any
        # OTHER line whose computation_type is "Commission Received" pointing
        # at one of these — a bounded, one-level-deep cascade (matching the
        # max-depth-1 chaining rule enforced in _check_base_line) done via
        # plain method calls rather than a recursive stored @api.depends,
        # which triggers an Odoo ORM edge case involving not-yet-saved
        # records in an editable list.
        for line in self:
            line.commission_amount = line._calc_amount()
        dependents = self.search([('base_line_id', 'in', self.ids)]) - self
        if dependents:
            dependents._set_commission_amounts()

    @api.depends('commission_amount', 'tax_ids')
    def _compute_amount_total(self):
        for line in self:
            if line.tax_ids:
                taxes = line.tax_ids.compute_all(
                    line.commission_amount,
                    currency=line.currency_id,
                    quantity=1.0,
                    product=False,
                    partner=line.partner_id,
                )
                line.amount_total = taxes['total_included']
                line.amount_tax = taxes['total_included'] - taxes['total_excluded']
            else:
                line.amount_total = line.commission_amount
                line.amount_tax = 0.0

    @api.constrains('computation_type')
    def _check_base_line(self):
        for line in self:
            if line.computation_type != 'commission_received':
                continue
            base_line = line._get_base_line()
            if not base_line:
                raise ValidationError(_(
                    'Select a Commission Line to use as the base when Computation '
                    'Type is "Commission Received".'))
            if base_line.id == line.id:
                raise ValidationError(_(
                    'A commission line cannot use itself as its own commission base.'))
            if base_line.computation_type == 'commission_received':
                raise ValidationError(_(
                    'The base commission line ("%s") is itself based on another '
                    'commission line. Chaining more than one level deep is not '
                    'supported — pick a line whose Computation Type is Property Price.'
                ) % base_line.display_name)

    @api.depends('bill_id.payment_state', 'bill_id.state')
    def _compute_payment_state(self):
        for line in self:
            bill = line.bill_id
            if bill and bill.state == 'posted':
                line.payment_state = bill.payment_state if bill.payment_state in (
                    'not_paid', 'in_payment', 'paid', 'partial') else 'not_paid'
            else:
                line.payment_state = 'not_paid'

    def get_role_label(self):
        """Return human-readable role label."""
        self.ensure_one()
        if self.role == 'custom':
            return self.custom_role_name or 'Custom'
        return dict(self._fields['role'].selection).get(self.role, self.role)

    @api.depends('partner_id.name', 'role', 'custom_role_name', 'commission_amount',
                 'currency_id.symbol')
    def _compute_display_name(self):
        # Default Odoo display_name for a model with no name/_rec_name field
        # falls back to "model.name,id" (e.g. "commission.line.mixin,4"),
        # which is meaningless in the Base Commission Line picker or on a
        # generated bill line. Show who gets paid, in what role, and how
        # much instead.
        for line in self:
            beneficiary = line.partner_id.name or _('New Commission Line')
            role = line.get_role_label()
            amount = '{:,.2f}'.format(line.commission_amount or 0.0)
            currency = line.currency_id.symbol or ''
            line.display_name = ('%s — %s (%s %s)' % (beneficiary, role, amount, currency)).strip()

    # -------------------------------------------------------------------------
    # Hooks — override in concrete models
    # -------------------------------------------------------------------------

    def _get_parent_contract(self):
        """Return the sale.contract / rent.contract / property.vendor record
        this line belongs to (used for bill line labels and invoice_origin)."""
        self.ensure_one()
        raise NotImplementedError

    def _get_bill_move_type(self):
        """'in_invoice' (vendor bill) or 'out_invoice' (customer invoice)."""
        return 'in_invoice'

    def _get_bill_partner(self):
        self.ensure_one()
        return self.partner_id

    def _check_commission_eligible(self):
        """Override in concrete models: raise UserError if the parent
        contract hasn't met its eligibility rule yet. No-op by default."""
        return

    # -------------------------------------------------------------------------
    # Commission billing — one click generates a bill for every approved,
    # unbilled commission line, one document per (payer, move type) so lines
    # billed to different parties (e.g. tenant vs landlord) don't merge. The
    # line's own tax_ids travel onto the invoice line so Odoo computes
    # untaxed/tax/total natively instead of pre-baking a tax-inclusive price.
    # -------------------------------------------------------------------------

    def action_generate_bill(self):
        return self._generate_bills(post=True)

    def _generate_bills(self, post=False):
        billable = self.filtered(lambda l: l.state == 'approved' and not l.bill_id)
        if not billable:
            raise UserError(_('No approved, unbilled commission lines to process.'))
        billable._check_commission_eligible()

        AccountMove = self.env['account.move']
        created = self.env['account.move']
        groups = {}
        for line in billable:
            key = (line._get_bill_partner().id, line._get_bill_move_type())
            groups[key] = groups.get(key, line.browse()) | line

        for (partner_id, move_type), lines in groups.items():
            contract = lines[0]._get_parent_contract()
            move_lines = [(0, 0, {
                'name': _('%s - %s') % (contract.display_name, line.display_name),
                'quantity': 1,
                'price_unit': line.commission_amount,
                'tax_ids': [(6, 0, line.tax_ids.ids)],
            }) for line in lines]
            move = AccountMove.create({
                'move_type': move_type,
                'partner_id': partner_id,
                'invoice_date': fields.Date.context_today(self),
                'invoice_origin': contract.name,
                'currency_id': lines[0].currency_id.id,
                'invoice_line_ids': move_lines,
            })
            if post:
                move.action_post()
            lines.write({'bill_id': move.id})
            created |= move
        return created

    def action_view_bill(self):
        self.ensure_one()
        if not self.bill_id:
            raise UserError(_('No bill has been generated for this commission line yet.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
        }
