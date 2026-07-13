# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleContractInstallment(models.Model):
    _name = 'sale.contract.installment'
    _description = 'Sale Contract Installment'
    _order = 'contract_id, sequence, due_date'

    contract_id = fields.Many2one(
        'sale.contract',
        string='Sale Contract',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    due_date = fields.Date(string='Due Date')
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='contract_id.currency_id',
        store=True,
        readonly=True,
    )
    percentage = fields.Float(string='Percentage (%)', digits=(5, 2))
    state = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ], string='Status', default='pending', required=True)
    payment_date = fields.Date(string='Payment Date')
    notes = fields.Text(string='Notes')

    # -------------------------------------------------------------------------
    # State transitions
    # -------------------------------------------------------------------------

    def action_mark_paid(self):
        for installment in self:
            if installment.state == 'paid':
                raise UserError(_('This installment is already marked as paid.'))
            installment.write({
                'state': 'paid',
                'payment_date': fields.Date.context_today(self),
            })

    def action_mark_overdue(self):
        for installment in self:
            if installment.state == 'paid':
                raise UserError(_('A paid installment cannot be marked as overdue.'))
            installment.state = 'overdue'
