# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    commission_sale_order_id = fields.Many2one(
        'sale.order',
        string='Commission Source Sale Order',
        ondelete='set null'
    )
    commission_posted = fields.Boolean(
        string='Commission Posted',
        default=False,
        help='Indicates if the commission for this purchase order has been posted.'
    )
    origin_so_id = fields.Many2one(
        'sale.order',
        string='Origin Sale Order',
        ondelete='set null'
    )
