# -*- coding: utf-8 -*-
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class SaleOrderType(models.Model):
    """Lightweight sales order type model — replaces OCA sale_order_type dep."""
    _name = 'sale.order.type'
    _description = 'Sales Order Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_order_type_id = fields.Many2one(
        'sale.order.type', string='Order Type',
        help="Categorise orders for dashboard filtering and grouping.",
    )
