# -*- coding: utf-8 -*-
# Part of SGC. See LICENSE file for full copyright and licensing details.

{
    "name": "SGC Scroll Hero Builder",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "Website Builder options panel for SGC cinematic scroll hero snippets",
    "description": """
Adds Website Builder option panels to customize the SGC scroll
hero snippets (V1 homepage + V2) directly in the Odoo page editor.
    """,
    "author": "SGC",
    "website": "",
    "depends": [
        "website",
        "sgc_scroll_hero_homepage",
        "sgc_scroll_hero_v2",
    ],
    "data": [],
    "assets": {
        "website.website_builder_assets": [
            "sgc_scroll_hero_builder/static/src/js/scroll_hero_option.js",
            "sgc_scroll_hero_builder/static/src/xml/scroll_hero_option.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
