# -*- coding: utf-8 -*-
# SGC TECH AI Enterprise Theme for Odoo v19

from . import models


def _setup_module(env):
    """Post-install: ensure module is marked installed."""
    env['ir.module.module'].search([
        ('name', '=', 'sgc_tech_ai_theme'),
    ]).write({'state': 'installed'})


def _uninstall_cleanup(env):
    """Cleanup on uninstall — no-op, assets are auto-removed by Odoo."""
    pass