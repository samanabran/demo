# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CommissionDashboard(models.TransientModel):
    _name = 'commission.dashboard'
    _description = 'Commission Dashboard'

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        readonly=True
    )
    
    # Summary fields
    total_commission_amount = fields.Monetary(
        string="Total Commission",
        currency_field='currency_id',
        readonly=True
    )
    
    internal_commission_amount = fields.Monetary(
        string="Internal Commission",
        currency_field='currency_id',
        readonly=True
    )
    
    external_commission_amount = fields.Monetary(
        string="External Commission",
        currency_field='currency_id',
        readonly=True
    )
    
    commission_lines_count = fields.Integer(
        string="Commission Lines",
        readonly=True
    )
    
    purchase_orders_count = fields.Integer(
        string="Purchase Orders",
        readonly=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        readonly=True
    )
    
    commission_status = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string="Status", readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Load commission data from active sale order"""
        defaults = super().default_get(fields_list)
        
        sale_order_id = self.env.context.get('default_sale_order_id') or self.env.context.get('active_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(sale_order_id)
            if sale_order.exists():
                defaults.update({
                    'sale_order_id': sale_order.id,
                    'total_commission_amount': sale_order.total_commission_amount,
                    'internal_commission_amount': sale_order.total_internal_commission_amount,
                    'external_commission_amount': sale_order.total_external_commission_amount,
                    'commission_lines_count': sale_order.commission_lines_count,
                    'purchase_orders_count': sale_order.purchase_order_count,
                    'currency_id': sale_order.currency_id.id,
                    'commission_status': sale_order.commission_status,
                })
        
        return defaults

    def action_view_commission_lines(self):
        """View commission lines for this sale order"""
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_("No sale order selected"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission Lines'),
            'res_model': 'commission.line',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.sale_order_id.id)],
            'context': {
                'default_sale_order_id': self.sale_order_id.id,
            }
        }

    def action_view_purchase_orders(self):
        """View purchase orders for this sale order"""
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_("No sale order selected"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission Purchase Orders'),
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('commission_sale_order_id', '=', self.sale_order_id.id)],
            'context': {}
        }

    def action_process_commissions(self):
        """Process commissions for the sale order"""
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_("No sale order selected"))
        
        result = self.sale_order_id.action_process_commissions()
        
        # Refresh the dashboard data
        self.write(self.default_get([]))
        
        return result

    def action_close(self):
        """Close the dashboard"""
        return {'type': 'ir.actions.act_window_close'}