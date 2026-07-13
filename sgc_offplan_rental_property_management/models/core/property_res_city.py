# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyResCity(models.Model):
    _name = 'property.res.city'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property City'
    _order = 'name'

    name = fields.Char(string='City Name', required=True)
    region_id = fields.Many2one('property.region', string='Region')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
