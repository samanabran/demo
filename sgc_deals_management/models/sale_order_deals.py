# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderDeal(models.Model):
    """Extends sale.order with real estate deal management fields."""
    _inherit = 'sale.order'

    deal_type = fields.Selection([
        ('offplan', 'Off-Plan'),
        ('resale', 'Resale'),
        ('rental', 'Rental'),
    ], string='Deal Type', help='Type of real estate deal')
    deal_project_id = fields.Many2one('realestate.project', string='Deal Project',
                                       help="Real estate project (separate from Odoo project_manager projects).")
    unit_id = fields.Many2one('realestate.unit', string='Unit')
    commission_amount = fields.Monetary(string='Commission Amount', currency_field='currency_id')
    commission_paid = fields.Boolean(string='Commission Paid', default=False)
    broker_id = fields.Many2one('res.partner', string='Broker')
    deal_date = fields.Date(string='Deal Date', default=fields.Date.today)
    booking_date = fields.Date(string='Booking Date', help='Date when the unit was booked/reserved')
    payment_terms_summary = fields.Text(string='Payment Terms Summary')
    document_ids = fields.One2many('ir.attachment', 'res_id',
                                   domain=[('res_model', '=', 'sale.order')],
                                   string='Deal Documents')
    is_deal = fields.Boolean(string='Is Real Estate Deal', default=True,
                             help="Technical field to distinguish deals from regular orders")
    primary_buyer_id = fields.Many2one('res.partner', string='Primary Buyer',
                                       domain="[('is_company', '=', False)]")
    secondary_buyer_id = fields.Many2one('res.partner', string='Secondary Buyer',
                                         domain="[('is_company', '=', False)]")
    deal_sales_value = fields.Monetary(string='Unit Sale Value', currency_field='currency_id')
    deal_commission_rate = fields.Float(string='Commission Rate (%)')
    sales_type = fields.Selection([
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('exclusive', 'Exclusive'),
        ('rental', 'Rental'),
    ], string='Sales Type')

    def action_confirm(self):
        """Override to set deal-specific fields on confirmation."""
        result = super(SaleOrderDeal, self).action_confirm()
        for order in self:
            if order.is_deal:
                order.deal_date = fields.Date.today()
        return result
