# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

from .property_amenities import ICON_STATIC_BASE, _match_icon_filename


class PropertyConnectivity(models.Model):
    _name = 'property.connectivity'
    _description = 'Property Nearby Connectivities'
    _order = 'name'

    image = fields.Binary(string='Image')
    name = fields.Char(string='Name', required=True)
    icon_url = fields.Char(string='Icon URL', compute='_compute_icon_url')

    @api.depends('image', 'name')
    def _compute_icon_url(self):
        for record in self:
            record.icon_url = record.get_icon_url()

    def get_icon_url(self):
        self.ensure_one()
        if self.image:
            return '/web/image/property.connectivity/%s/image' % self.id
        return ICON_STATIC_BASE + _match_icon_filename(self.name)
