# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    commission_rate = fields.Float(string='Commission Rate (%)', default=0.0)
    is_commission_agent = fields.Boolean(string='Is Commission Agent', default=False)
