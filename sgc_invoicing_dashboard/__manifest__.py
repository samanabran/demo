# -*- coding: utf-8 -*-
{
    "name": "SGC - Invoicing Dashboard",
    "version": "19.0.2.1",
    "category": "Sales",
    "summary": "Modern analytics dashboard for invoicing KPIs and sales orders",
    "description": (
        "Provides a modern, responsive dashboard with real-time analytics, "
        "chart visualizations, and automated KPI tracking for posted invoices, "
        "pending orders, and unpaid invoices. Features modern responsive design "
        "with auto-updating charts that react to filter changes."
    ),
    "author": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "license": "OPL-1",
    "price": 23,
    "currency": "USD",
    "images": ["static/description/banner.png"],
    "depends": ["sale", "account"],
    "assets": {
        "web.assets_backend": [
            # Modern responsive styling
            "sgc_invoicing_dashboard/static/src/scss/dashboard_modern.scss",
            # Chart.js library (use Odoo core Chart.js to avoid vendored parse errors)
            "web/static/lib/Chart/Chart.js",
            # Chart.js shim to ensure module availability
            "sgc_invoicing_dashboard/static/src/js/chart_shim.js",
            # OWL template for chart widget
            "sgc_invoicing_dashboard/static/src/xml/dashboard_charts.xml",
            # JavaScript components (enhanced)
            "sgc_invoicing_dashboard/static/src/js/dashboard_charts.js",
            "sgc_invoicing_dashboard/static/src/js/dashboard_form_controller_enhanced.js",
        ],
    },
    "data": [
        "data/sale_order_type_data.xml",
        "security/ir.model.access.csv",
        "security/dashboard_security.xml",
        "views/account_move_views.xml",
        "views/sale_order_views.xml",
        "views/dashboard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
