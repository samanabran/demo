# -*- coding: utf-8 -*-
# Copyright 2026 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
{
    "name": "SGC - Scroll Hero Homepage",
    "summary": "Cinematic scroll-triggered hero section + property search, as a native Website Builder snippet",
    "description": """
        Scroll Hero Homepage
        ====================
        Adds a cinematic, scroll-triggered image-sequence hero section (GSAP +
        ScrollTrigger) to the Website Builder's "Storytelling" snippet
        category, and republishes the site homepage to use it, ending in a
        search bar wired to the existing SGC Property Management module.

        This module is purely additive: it does not modify any file inside
        sgc_offplan_rental_property_management or sgc_realestate_website. It
        only reads from property.details (via request.env, sudo, filtered on
        is_published_website) and redirects the website's homepage_url to a
        new page it owns — the original generic homepage view is left
        completely intact and can be restored by uninstalling this module.
    """,
    "version": "19.0.1.0.0",
    "category": "Website/Real Estate",
    "author": "SGC TECH AI",
    "company": "SGC TECH AI",
    "maintainer": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "license": "OPL-1",
    "depends": [
        "website",
        "sgc_offplan_rental_property_management",
    ],
    "data": [
        "views/snippets/snippets.xml",
        "views/snippets/s_re_scroll_hero.xml",
        "views/homepage.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "sgc_scroll_hero_homepage/static/src/css/scroll_hero.css",
            "sgc_scroll_hero_homepage/static/src/js/scroll_hero.js",
        ],
    },
    "images": [
        "static/description/icon.png",
    ],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
