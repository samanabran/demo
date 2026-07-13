# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_state_display = fields.Selection(
        selection=lambda self: self._fields['payment_state'].selection,
        string='Payment Status (Display)',
        compute='_compute_payment_state_display',
        store=False,
    )

    @api.depends(
        'payment_state',
        'amount_residual_signed',
        'company_id',
        'move_type',
        'state',
    )
    def _compute_payment_state_display(self):
        threshold = self._get_small_balance_threshold()
        for move in self:
            state = move.payment_state
            if (
                move.state == 'posted'
                and move.move_type in (
                    'out_invoice',
                    'out_refund',
                    'in_invoice',
                    'in_refund',
                )
                and state in ('not_paid', 'partial', 'in_payment')
            ):
                residual = abs(move.amount_residual_signed or 0.0)
                rounding = move.company_id.currency_id.rounding
                if float_compare(
                    residual,
                    threshold,
                    precision_rounding=rounding,
                ) < 0:
                    state = 'paid'
            move.payment_state_display = state

    def _get_small_balance_threshold(self):
        return 10.0

    def _balance_to_debit_credit(self, balance):
        debit = balance if balance > 0 else 0.0
        credit = -balance if balance < 0 else 0.0
        return debit, credit

    def _get_small_balance_writeoff_journal(self, company):
        Journal = self.env['account.journal']
        journal = Journal.search(
            [
                ('company_id', '=', company.id),
                ('type', '=', 'general'),
                ('name', 'ilike', 'write-off'),
            ],
            limit=1,
        )
        if journal:
            return journal
        code = 'WOFF'
        existing_code = Journal.search_count([
            ('company_id', '=', company.id),
            ('code', '=', code),
        ])
        if existing_code:
            code = 'WOF1'
        return Journal.create({
            'name': 'Write-Off',
            'code': code,
            'type': 'general',
            'company_id': company.id,
        })

    def _get_small_balance_writeoff_account(self, company, account_type):
        Account = self.env['account.account']
        if account_type == 'expense':
            code = 'WOFFEXP'
            name = 'Small Balance Write-Off (Expense)'
        else:
            code = 'WOFFINC'
            name = 'Small Balance Write-Off (Income)'
        account = Account.search(
            [
                ('company_id', '=', company.id),
                ('code', '=', code),
            ],
            limit=1,
        )
        if account:
            return account
        return Account.create({
            'name': name,
            'code': code,
            'account_type': account_type,
            'company_id': company.id,
        })

    def _get_small_balance_writeoff_account_for_move(self, move):
        account_type = 'expense' if move.amount_residual_signed > 0 else 'income'
        return self._get_small_balance_writeoff_account(
            move.company_id,
            account_type,
        )

    def _prepare_small_balance_writeoff_lines(
        self,
        move,
        residual_signed,
        account_id,
        writeoff_account_id,
    ):
        partner = move.partner_id
        balance_receivable = -residual_signed
        debit, credit = self._balance_to_debit_credit(balance_receivable)
        line_vals = {
            'name': 'Small balance write-off',
            'account_id': account_id.id,
            'partner_id': partner.id,
            'debit': debit,
            'credit': credit,
        }
        if move.currency_id != move.company_id.currency_id:
            residual_currency = move.amount_residual
            if residual_signed < 0:
                residual_currency = -residual_currency
            line_vals.update({
                'currency_id': move.currency_id.id,
                'amount_currency': -residual_currency,
            })
        balance_writeoff = residual_signed
        debit, credit = self._balance_to_debit_credit(balance_writeoff)
        writeoff_vals = {
            'name': 'Small balance write-off',
            'account_id': writeoff_account_id.id,
            'partner_id': partner.id,
            'debit': debit,
            'credit': credit,
        }
        return [
            (0, 0, line_vals),
            (0, 0, writeoff_vals),
        ]

    def action_writeoff_small_balance(self):
        threshold = self._get_small_balance_threshold()
        moves = self.filtered(
            lambda m: m.state == 'posted'
            and m.move_type in (
                'out_invoice',
                'out_refund',
                'in_invoice',
                'in_refund',
            )
            and m.payment_state in ('not_paid', 'partial', 'in_payment')
        )
        for move in moves:
            residual_signed = move.amount_residual_signed or 0.0
            rounding = move.company_id.currency_id.rounding
            if float_compare(
                abs(residual_signed),
                threshold,
                precision_rounding=rounding,
            ) >= 0:
                continue
            receivable_lines = move.line_ids.filtered(
                lambda l: l.account_id.account_type in (
                    'asset_receivable',
                    'liability_payable',
                ) and not l.reconciled
            )
            if not receivable_lines:
                continue
            account_id = receivable_lines[0].account_id
            writeoff_account = self._get_small_balance_writeoff_account_for_move(
                move,
            )
            journal = self._get_small_balance_writeoff_journal(move.company_id)
            line_ids = self._prepare_small_balance_writeoff_lines(
                move,
                residual_signed,
                account_id,
                writeoff_account,
            )
            ref = 'Small balance write-off: %s' % move.name
            writeoff_move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'ref': ref,
                'line_ids': line_ids,
            })
            writeoff_move.action_post()
            reconcile_lines = receivable_lines.filtered(
                lambda l: not l.reconciled
            ) | writeoff_move.line_ids.filtered(
                lambda l: l.account_id == account_id and not l.reconciled
            )
            if reconcile_lines:
                reconcile_lines.reconcile()
