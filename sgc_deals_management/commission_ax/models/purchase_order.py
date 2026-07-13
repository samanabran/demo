# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    commission_id = fields.Many2one('commission.main', string='Commission')
    is_commission_payment = fields.Boolean(string='Is Commission Payment', default=False)
