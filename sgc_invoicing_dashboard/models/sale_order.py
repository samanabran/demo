# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_progress = fields.Selection(
        selection=[
            ('none', 'Not Invoiced'),
            ('partial', 'Pending to Invoice'),
            ('full', 'Fully Invoiced'),
        ],
        string='Invoicing Progress',
        compute='_compute_invoice_progress',
        store=True,
    )
    
    # Hidden fields for pivot analysis
    invoiced_amount = fields.Monetary(
        string='Invoiced Amount',
        compute='_compute_invoice_amounts',
        store=True,
        currency_field='currency_id',
        help='Total amount invoiced (visible in pivot/graph views)'
    )
    outstanding_amount = fields.Monetary(
        string='Outstanding Amount',
        compute='_compute_invoice_amounts',
        store=True,
        currency_field='currency_id',
        help='Remaining unpaid amount (visible in pivot/graph views)'
    )
    collected_amount = fields.Monetary(
        string='Collected Amount',
        compute='_compute_invoice_amounts',
        store=True,
        currency_field='currency_id',
        help='Amount already collected (visible in pivot/graph views)'
    )

    collection_rate = fields.Float(
        string='Collection Rate %',
        compute='_compute_collection_rate',
        store=True,
        aggregator='avg'
    )

    days_to_invoice = fields.Integer(
        string='Days to Invoice',
        compute='_compute_days_to_invoice',
        store=True
    )

    payment_delay_days = fields.Integer(
        string='Payment Delay (Days)',
        compute='_compute_payment_delay',
        store=True
    )

    @api.depends('invoice_status')
    def _compute_invoice_progress(self):
        """Simple classification badge - no amounts shown"""
        for order in self:
            status = order.invoice_status
            if status == 'invoiced':
                order.invoice_progress = 'full'
            elif status == 'to invoice':
                order.invoice_progress = 'partial'
            else:
                order.invoice_progress = 'none'

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.amount_total', 
                 'invoice_ids.amount_residual', 'invoice_ids.payment_state')
    def _compute_invoice_amounts(self):
        """Store amounts for pivot/graph analysis - hidden from form/tree"""
        for order in self:
            # Get only posted customer invoices
            invoices = order.invoice_ids.filtered(
                lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted'
            )
            invoiced = sum(invoices.mapped('amount_total'))
            outstanding = sum(invoices.mapped('amount_residual'))
            collected = max(invoiced - outstanding, 0.0)
            
            order.invoiced_amount = invoiced
            order.outstanding_amount = outstanding
            order.collected_amount = collected

    @api.depends('amount_total', 'invoiced_amount', 'collected_amount')
    def _compute_collection_rate(self):
        for order in self:
            invoiced = float(order.invoiced_amount or 0.0)
            collected = float(order.collected_amount or 0.0)
            order.collection_rate = (collected / invoiced * 100.0) if invoiced else 0.0

    @api.depends('date_order', 'invoice_ids.invoice_date', 'invoice_ids.state')
    def _compute_days_to_invoice(self):
        for order in self:
            if order.date_order and order.invoice_ids:
                posted = order.invoice_ids.filtered(lambda m: m.state == 'posted' and m.move_type == 'out_invoice')
                if posted:
                    first_date = min([m.invoice_date for m in posted if m.invoice_date])
                    if first_date and order.date_order:
                        order_date = fields.Date.to_date(order.date_order)
                        order.days_to_invoice = (first_date - order_date).days
                        continue
            order.days_to_invoice = 0

    @api.depends('invoice_ids.invoice_date_due', 'invoice_ids.amount_residual', 'invoice_ids.state')
    def _compute_payment_delay(self):
        today = fields.Date.context_today(self)
        for order in self:
            delay = 0
            posted = order.invoice_ids.filtered(lambda m: m.state == 'posted' and m.move_type == 'out_invoice')
            for m in posted:
                if m.amount_residual and m.invoice_date_due and m.invoice_date_due < today:
                    delay = max(delay, (today - m.invoice_date_due).days)
            order.payment_delay_days = delay

    def action_create_invoice_wizard(self):
        """Open the advance payment invoice wizard for selected orders."""
        self.ensure_one()
        return self.env.ref('sale.action_view_sale_advance_payment_inv').read()[0]

    def action_send_payment_reminder(self):
        """Post a payment reminder message on the customer and return unpaid invoices."""
        self.ensure_one()
        if self.partner_id:
            self.partner_id.message_post(body='Automated reminder: Please settle outstanding invoices.')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        domain = [
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('line_ids.sale_line_ids.order_id', 'in', self.ids),
            ('payment_state', 'in', ['not_paid', 'partial', 'in_payment']),
        ]
        action['domain'] = domain
        return action
