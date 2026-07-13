# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CommissionMain(models.Model):
    _name = 'commission.main'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Commission Main'
    _order = 'date desc'

    name = fields.Char(string='Commission Reference', required=True, copy=False,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Agent/Partner', required=True)
    commission_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ], string='Commission Type', default='percentage', required=True)
    amount = fields.Float(string='Commission Amount', required=True)
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('commission.main') or _('New')
        return super().create(vals_list)

    @api.model
    def process_commission_payments(self):
        """Cron: process confirmed commissions for payment.

        Finds all confirmed commissions and marks them as paid.
        Override in a more specific module for actual payment gateway integration.
        """
        confirmed = self.search([('state', '=', 'confirmed')])
        confirmed.write({'state': 'paid'})
        return len(confirmed)
