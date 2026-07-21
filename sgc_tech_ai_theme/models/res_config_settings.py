# -*- coding: utf-8 -*-
# Part of SGC TECH AI. See LICENSE file for full copyright and licensing details.
# Copyright (c) 2026 SGC TECH AI (https://sgctech.ai)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extend settings with SGC theme branding fields."""

    _inherit = 'res.config.settings'

    theme_favicon = fields.Binary(
        related='company_id.favicon',
        readonly=False,
    )

    theme_background_image = fields.Binary(
        related='company_id.background_image',
        readonly=False,
    )

    appbar_image = fields.Binary(
        related='company_id.appbar_image',
        readonly=False,
    )

    theme_mode = fields.Selection(
        related='company_id.sgc_theme_mode',
        readonly=False,
    )