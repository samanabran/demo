# -*- coding: utf-8 -*-
{
    'name': 'SGC - Deals Management',
    "version": "19.0.3.0",
    'category': 'Sales',
    'summary': 'Real estate deals + commission + project/unit management',
    'description': """
SGC - Deals Management - Unified Deals & Commission Suite
==========================================================

This module merges deals tracking and commission management into a
single, production-ready Odoo 19 add-on with custom project and unit models.

Key Features:
- Real estate deal tracking (offplan, resale, rental)
- Custom project and unit inventory management
- Buyer, project, and unit management
- Document attachments (KYC, booking forms, passports)
- Financial summaries with VAT and totals
- Commission workflows with analytics and reports
- Vendor bill integration and commission purchase orders
    """,
    'author': 'SGC TECH AI',
    'icon': 'static/description/icon.png',
    'website': 'https://sgctech.ai',
    'support': 'bran@sgctech.ai',
    'images': ['static/description/banner.png'],
    'depends': [
        'base',
        'sale',
        'purchase',
        'account',
        'mail',
        'hr',
        'utm',
        # Canonical commission engine — Deals no longer vendors its own copy.
        # See CHANGELOG: this module's commission logic used to duplicate
        # sgc_commission (a separate commission.main model + a second
        # "Commissions" tab on sale.order, out of sync with this one), which
        # is now retired in favor of depending on it directly.
        'sgc_commission',
    ],
    'data': [
        'security/ir.model.access.csv',

        # ============================================
        # Deals management views
        # ============================================
        'views/account_move_views.xml',
        'views/realestate_project_views.xml',
        'views/realestate_unit_views.xml',
        'views/sale_order_deals_views.xml',
        'views/deals_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 58,
    'currency': 'USD',
    'external_dependencies': {
        'python': [],
    },
}
