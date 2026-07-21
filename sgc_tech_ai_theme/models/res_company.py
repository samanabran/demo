# -*- coding: utf-8 -*-
# Part of SGC TECH AI. See LICENSE file for full copyright and licensing details.
# Copyright (c) 2026 SGC TECH AI (https://sgctech.ai)

from odoo import fields, models


class ResCompany(models.Model):
    """Add SGC branding fields to company."""

    _inherit = 'res.company'

    favicon = fields.Binary(
        string='Company Favicon',
        attachment=True,
    )
    background_image = fields.Binary(
        string='Home Menu Background Image',
        attachment=True,
    )
    appbar_image = fields.Binary(
        string='Sidebar Logo',
        attachment=True,
        help='Logo displayed at the top of the left sidebar.',
    )

    sgc_theme_mode = fields.Selection(
        selection=[
            ('light', 'Light'),
            ('dark', 'Dark'),
        ],
        string='Theme Mode',
        default='light',
        required=True,
        help='Default theme for users in this company. Users can override per session.',
    )