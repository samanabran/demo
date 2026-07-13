# -*- coding: utf-8 -*-
{
    "name": "SGC - Real Estate Website",
    "version": "19.0.1.1.0",
    "category": "Website/Real Estate",
    "sequence": 10,
    "summary": "Modern responsive real estate website with advanced search and SEO optimization",
    "description": """
 SGC Real Estate Website
 ==============================
 
 A world-class real estate website module built with Odoo 19 best practices.

 Key Features:
 -------------
 * Property Listings with Advanced Search
 * Destination Country Management
 * Consultation Request Forms
 * SEO Optimized Pages
 * Fully Responsive Design
 * Performance Optimized
 * Modern OWL Components
 * Security Hardened

     """,
    "author": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "license": "OPL-1",
    "depends": [
        "base",
        "web",
        "website",
        "website_mail",
        "portal",
        "mail",
    ],
    "data": [
        # Security (load first)
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/website_menu.xml",
        "data/property_data.xml",
        # Views - Backend
        "views/property_views.xml",
        "views/destination_country_views.xml",
        "views/consultation_request_views.xml",
        "views/menu.xml",
        # Views - Frontend (Website)
        "views/website_templates.xml",
        "views/website_property_listing.xml",
        "views/website_property_detail.xml",
        "views/website_consultation_form.xml",
        "views/website_snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            # SCSS (compiled to CSS)
            "sgc_realestate_website/static/src/css/main.css",
            "sgc_realestate_website/static/src/css/responsive.css",
            "sgc_realestate_website/static/src/css/variables.scss",
            "sgc_realestate_website/static/src/css/mixins.scss",
            "sgc_realestate_website/static/src/css/base.scss",
            "sgc_realestate_website/static/src/css/components.scss",
            "sgc_realestate_website/static/src/css/property_listing.scss",
            "sgc_realestate_website/static/src/css/property_detail.scss",
            # Modern JavaScript (ES6+)
            "sgc_realestate_website/static/src/js/navbar.js",
            "sgc_realestate_website/static/src/js/property_search.js",
            "sgc_realestate_website/static/src/js/property_filters.js",
            "sgc_realestate_website/static/src/js/consultation_form.js",
            "sgc_realestate_website/static/src/js/image_gallery.js",
            # OWL Components
            "sgc_realestate_website/static/src/components/**/*",
        ],
    },
    "images": ["static/description/icon.png", "static/description/banner.png", "static/description/screenshots/01_tile.jpeg", "static/description/screenshots/02_inapp.jpeg", "static/description/screenshots/03_menu.jpeg", "static/description/screenshots/04_banner.png", "static/description/screenshots/screenshot.png"],
"installable": True,
    "application": True,
    "auto_install": False,
    "price": 35,
    "currency": "USD",
}
