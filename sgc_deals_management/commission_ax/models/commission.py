# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CommissionMain(models.Model):
    _name = 'commission.main'
    _description = 'Commission Main'
    _order = 'date desc'

    name = fields.Char(string='Commission Reference', required=True, copy=False,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Agent/Partner', required=True)
    commission_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ], string='Commission Type', default='percentage', required=True)
    commission_base = fields.Selection([
        ('sale_value', 'Sale Value (Untaxed)'),
        ('total_amount', 'Total Sale Amount'),
    ], string='Commission Base', default='total_amount', required=True,
        help='Which amount the commission percentage is applied to: '
             'the untaxed sale value, or the total order amount (incl. tax).')
    base_amount = fields.Float(
        string='Base Amount', compute='_compute_amount', store=True,
        help='Amount picked up from the linked order according to Commission Base.')
    amount = fields.Float(
        string='Commission Amount', compute='_compute_amount', store=True,
        readonly=False, required=True,
        help='Auto-calculated from Base Amount x Percentage when Commission Type is '
             'Percentage. Editable directly when Commission Type is Fixed Amount.')
    percentage = fields.Float(string='Percentage (%)', default=5.0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    @api.depends('commission_type', 'commission_base', 'percentage',
                 'sale_order_id.amount_untaxed', 'sale_order_id.amount_total',
                 'purchase_order_id.amount_untaxed', 'purchase_order_id.amount_total')
    def _compute_amount(self):
        for rec in self:
            order = rec.sale_order_id or rec.purchase_order_id
            if order and rec.commission_base == 'sale_value':
                rec.base_amount = order.amount_untaxed
            elif order:
                rec.base_amount = order.amount_total
            else:
                rec.base_amount = 0.0

            if rec.commission_type == 'percentage':
                rec.amount = rec.base_amount * (rec.percentage / 100.0)
            elif not rec.amount:
                rec.amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('commission.main') or _('New')
        return super().create(vals_list)
