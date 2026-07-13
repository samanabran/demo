# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_line_ids = fields.One2many(
        'commission.line',
        'sale_order_id',
        string='Commission Lines'
    )
    commission_lines_count = fields.Integer(
        string='Commission Lines Count',
        compute='_compute_commission_counts',
        store=True
    )
    purchase_order_count = fields.Integer(
        string='Purchase Orders',
        compute='_compute_commission_counts',
        store=True
    )
    total_commission_amount = fields.Monetary(
        string='Total Commission',
        compute='_compute_commission_amounts',
        store=True,
        currency_field='currency_id'
    )
    total_internal_commission_amount = fields.Monetary(
        string='Internal Commission',
        compute='_compute_commission_amounts',
        store=True,
        currency_field='currency_id'
    )
    total_external_commission_amount = fields.Monetary(
        string='External Commission',
        compute='_compute_commission_amounts',
        store=True,
        currency_field='currency_id'
    )
    commission_status = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Commission Status', default='draft', compute='_compute_commission_status', store=True)

    @api.depends('commission_line_ids')
    def _compute_commission_counts(self):
        for order in self:
            order.commission_lines_count = len(order.commission_line_ids)
            order.purchase_order_count = len(self.env['purchase.order'].search([
                ('commission_sale_order_id', '=', order.id)
            ]))

    @api.depends('commission_line_ids', 'commission_line_ids.commission_amount')
    def _compute_commission_amounts(self):
        for order in self:
            lines = order.commission_line_ids
            order.total_commission_amount = sum(lines.mapped('commission_amount')) if lines else 0.0
            order.total_internal_commission_amount = sum(
                lines.filtered(lambda l: l.partner_id.is_company).mapped('commission_amount')
            ) if lines else 0.0
            order.total_external_commission_amount = sum(
                lines.filtered(lambda l: not l.partner_id.is_company).mapped('commission_amount')
            ) if lines else 0.0

    @api.depends('commission_line_ids.state')
    def _compute_commission_status(self):
        for order in self:
            states = order.commission_line_ids.mapped('state') if order.commission_line_ids else []
            if not states:
                order.commission_status = 'draft'
            elif all(s == 'paid' for s in states):
                order.commission_status = 'paid'
            elif all(s in ('paid', 'processed') for s in states):
                order.commission_status = 'processed'
            elif all(s in ('paid', 'processed', 'confirmed') for s in states):
                order.commission_status = 'confirmed'
            elif any(s in ('calculated', 'confirmed', 'processed', 'paid') for s in states):
                order.commission_status = 'calculated'
            else:
                order.commission_status = 'draft'

    def action_process_commissions(self):
        """Process commissions for this sale order."""
        self.ensure_one()
        for line in self.commission_line_ids:
            if line.state == 'draft':
                line.state = 'calculated'
        return True
