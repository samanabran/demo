# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    """Extend account.move to track related deals"""
    _inherit = 'account.move'

    # Relational field to link invoice back to the sale order (deal)
    sale_order_deal_id = fields.Many2one(
        'sale.order',
        string='Deal (Sale Order)',
        readonly=True,
        compute='_compute_sale_order_deal',
        store=True,
        help='Related sale order deal'
    )
    
    # Deal Details - automatically populated from linked sale order
    booking_date = fields.Date(
        string='Booking Date',
        related='sale_order_deal_id.booking_date',
        readonly=True,
        store=True
    )
    
    primary_buyer_id = fields.Many2one(
        'res.partner',
        string='Primary Buyer',
        related='sale_order_deal_id.primary_buyer_id',
        readonly=True,
        store=True
    )
    
    secondary_buyer_id = fields.Many2one(
        'res.partner',
        string='Secondary Buyer',
        related='sale_order_deal_id.secondary_buyer_id',
        readonly=True,
        store=True
    )
    
    project_id = fields.Many2one(
        'realestate.project',
        string='Project',
        related='sale_order_deal_id.deal_project_id',
        readonly=True,
        store=True
    )
    
    unit_id = fields.Many2one(
        'realestate.unit',
        string='Unit',
        related='sale_order_deal_id.unit_id',
        readonly=True,
        store=True
    )
    
    deal_sales_value = fields.Monetary(
        string='Unit Sale Value',
        related='sale_order_deal_id.deal_sales_value',
        readonly=True,
        store=True,
        currency_field='currency_id'
    )
    
    deal_commission_rate = fields.Float(
        string='Commission Rate (%)',
        related='sale_order_deal_id.deal_commission_rate',
        readonly=True,
        store=True
    )
    
    sales_type = fields.Selection(
        [
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('exclusive', 'Exclusive'),
            ('rental', 'Rental'),
        ],
        string='Sales Type',
        compute='_compute_sales_type',
        readonly=True,
        store=True
    )

    @api.depends('sale_order_deal_id')
    def _compute_sales_type(self):
        """Get sales type from linked sale order"""
        for move in self:
            move.sales_type = move.sale_order_deal_id.sales_type if move.sale_order_deal_id else False

    @api.depends('invoice_origin', 'line_ids.sale_line_ids.order_id')
    def _compute_sale_order_deal(self):
        """Auto-link invoice to sale order deal"""
        for move in self:
            deal = False
            
            # Only process customer invoices/refunds
            if move.move_type not in ('out_invoice', 'out_refund'):
                move.sale_order_deal_id = False
                continue
            
            # Method 1: Link via invoice_origin (SO reference number)
            if move.invoice_origin:
                # Try exact match first
                deal = self.env['sale.order'].search([
                    ('name', '=', move.invoice_origin)
                ], limit=1)
                
                # If not found, try searching for SO containing the origin
                if not deal and len(move.invoice_origin) > 2:
                    deal = self.env['sale.order'].search([
                        ('name', 'like', move.invoice_origin)
                    ], limit=1)
            
            # Method 2: Link via invoice lines that came from a sale order
            if not deal and move.line_ids:
                # Look at all sale lines in the invoice lines
                so_from_lines = move.line_ids.mapped('sale_line_ids.order_id')
                if so_from_lines:
                    deal = so_from_lines[0]
            
            # Method 3: Try via sale_id if the move has one (some moves might have it)
            if not deal and hasattr(move, 'sale_id') and move.sale_id:
                deal = move.sale_id
            
            move.sale_order_deal_id = deal

