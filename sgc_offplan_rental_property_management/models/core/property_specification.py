# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PropertySpecification(models.Model):
    _name = 'property.specification'
    _description = 'Property Specifications'
    _order = 'title'

    image = fields.Binary(string='Image')
    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
