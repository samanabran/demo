# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionLine(models.Model):
    _name = 'commission.line'
    _inherit = 'commission.line'
    _description = 'Commission Distribution Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    contract_id = fields.Many2one(
        'sale.contract',
        string='Sale Contract',
        required=True,
        ondelete='cascade',
    )
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
        related='contract_id.currency_id',
        store=True,
    )
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
        help='Vendor bill raised to pay this commission to its beneficiary.',
    )
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
    ], string='Payment Status', compute='_compute_payment_state', store=True, default='not_paid')
    notes = fields.Text(string='Notes')

    @api.depends('contract_id.sale_price', 'commission_type',
                 'commission_percentage', 'commission_fixed_amount')
    def _compute_commission_amount(self):
        for line in self:
            base = line.contract_id.sale_price or 0.0
            if line.commission_type == 'percentage':
                line.commission_amount = base * (line.commission_percentage / 100.0)
            else:
                line.commission_amount = line.commission_fixed_amount or 0.0

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
    # Commission billing — one click generates a vendor bill for every
    # approved, unbilled commission line, one bill per beneficiary partner.
    # -------------------------------------------------------------------------

    def action_generate_bill(self):
        return self._generate_bills(post=True)

    def _generate_bills(self, post=False):
        billable = self.filtered(lambda l: l.state == 'approved' and not l.bill_id)
        if not billable:
            raise UserError(_('No approved, unbilled commission lines to process.'))
        AccountMove = self.env['account.move']
        created = self.env['account.move']
        for partner in billable.mapped('partner_id'):
            lines = billable.filtered(lambda l: l.partner_id == partner)
            contract = lines[0].contract_id
            move_lines = []
            for line in lines:
                move_lines.append((0, 0, {
                    'name': _('%s - %s (%s)') % (
                        contract.display_name, line.get_role_label(), line.name if hasattr(line, 'name') else line.display_name),
                    'quantity': 1,
                    'price_unit': line.commission_amount,
                }))
            move = AccountMove.create({
                'move_type': 'in_invoice',
                'partner_id': partner.id,
                'invoice_date': fields.Date.context_today(self),
                'invoice_origin': contract.name,
                'currency_id': contract.currency_id.id,
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
