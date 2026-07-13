# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PropertyTag(models.Model):
    _name = 'property.tag'
    _description = 'Property Tags'
    _order = 'title'

    title = fields.Char(string='Title', required=True)
