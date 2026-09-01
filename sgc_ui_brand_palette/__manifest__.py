# -*- coding: utf-8 -*-
# SGC TECH AI - UI Brand Palette
# Copyright (c) 2026 SGC TECH AI (https://sgctech.ai)
# License OPL-1
{
    "name": "SGC TECH AI - UI Brand Palette",
    "version": "19.0.2.0.0",
    "category": "Theme/Brand",
    "summary": (
        "Standalone, tenant-configurable UI colour palette + uniform "
        "SGC brand icons for native and SGC main-menu apps"
    ),
    "description": """
SGC TECH AI - UI Brand Palette
================================

Two independent features, both standalone (no vertical-app dependency):

1. **Tenant-configurable colour palette** (new in 2.0.0) — a "Brand &
   Theme" panel under Settings lets any company/tenant set its own
   Primary, Secondary, Link, Navbar background, and Navbar text colours.
   Colours are applied live to the backend web client via a per-request
   CSS override (Bootstrap 5 custom properties + the top navbar), with
   zero SCSS recompilation — safe on a single Odoo instance serving
   multiple companies with different brand colours.

2. **Best-effort menu icon rebranding** (carried over from 1.x) — a
   self-healing `_register_hook` re-applies a uniform SGC icon set to
   any of ~20 known app root menus, IF that app happens to be
   installed. No hard dependency on any of them: an uninstalled app's
   entry is silently skipped.

Breaking change from 1.x: this module no longer depends on ~20 vertical
apps (hr_payroll_community, eh_uae_payroll_wps, sgc_hr_memos, project,
purchase, survey, ...). See CHANGES.md for the full upgrade note.
    """,
    "author": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "license": "OPL-1",
    "depends": [
        "base",
        "web",
        "base_setup",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "templates/web_layout.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
