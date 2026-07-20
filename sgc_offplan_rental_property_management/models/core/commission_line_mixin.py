# -*- coding: utf-8 -*-
# Copyright 2026 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PropertyCommissionLineMixin(models.AbstractModel):
    """Shared field set + billing logic for per-beneficiary commission lines.

    Concrete models (property.commission.line for sale.contract,
    rent.commission.line for rent.contract, property.vendor.commission.line
    for property.vendor bookings) add their own parent Many2one and override
    the hooks below to plug in their parent's price base, eligibility rule,
    and which partner/move type a generated bill should target.
    """
    _name = 'property.commission.line.mixin'
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
    commission_base = fields.Selection([
        ('contract_value', 'Total Contract Value'),
        ('commission_line', 'Another Commission Line'),
    ], string='Commission Base', default='contract_value', required=True,
        help='What the percentage is calculated against — the total property/contract '
             'value, or another beneficiary\'s commission amount (e.g. an agent split '
             'quoted as a percentage of the broker\'s commission, not of the sale price).')
    commission_percentage = fields.Float(
        string='Commission %',
        default=0.0,
        help='Percentage of the Commission Base selected above.',
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
        annual rent, etc.) used when commission_base == 'contract_value'."""
        self.ensure_one()
        return 0.0

    def _get_base_line(self):
        """Override: return the self-referencing base_line_id field value
        used when commission_base == 'commission_line'. Empty recordset by
        default for concrete models that don't declare that field."""
        self.ensure_one()
        return self.browse()

    def _get_base_amount(self):
        self.ensure_one()
        if self.commission_base == 'commission_line':
            return self._get_base_line().commission_amount
        return self._get_contract_value_base()

    def _calc_amount(self):
        self.ensure_one()
        if self.commission_type == 'percentage':
            return (self._get_base_amount() or 0.0) * (self.commission_percentage / 100.0)
        return self.commission_fixed_amount or 0.0

    def _compute_commission_amount(self):
        # Concrete models override this with their own @api.depends (the base
        # amount lives on a different parent field per model) and call
        # line._calc_amount(). Base implementation here is a safe no-op
        # fallback so the abstract model itself stays instantiable-free.
        for line in self:
            line.commission_amount = line._calc_amount()

    @api.constrains('commission_base')
    def _check_base_line(self):
        for line in self:
            if line.commission_base != 'commission_line':
                continue
            base_line = line._get_base_line()
            if not base_line:
                raise ValidationError(_(
                    'Select a Commission Line to use as the base when Commission Base '
                    'is "Another Commission Line".'))
            if base_line.id == line.id:
                raise ValidationError(_(
                    'A commission line cannot use itself as its own commission base.'))
            if base_line.commission_base == 'commission_line':
                raise ValidationError(_(
                    'The base commission line ("%s") is itself based on another '
                    'commission line. Chaining more than one level deep is not '
                    'supported — pick a line whose base is the contract value.'
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
    # billed to different parties (e.g. tenant vs landlord) don't merge.
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
                'name': _('%s - %s (%s)') % (
                    contract.display_name, line.get_role_label(), line.display_name),
                'quantity': 1,
                'price_unit': line.commission_amount,
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
