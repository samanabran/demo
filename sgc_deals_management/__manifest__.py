# -*- coding: utf-8 -*-
{
    'name': 'SGC - Deals Management',
    "version": "19.0.2.4",
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
    ],
    'data': [
        # ============================================
        # Commission cleanup and security
        # ============================================
        'commission_ax/data/cleanup_views.xml',
        'commission_ax/security/security.xml',
        'security/ir.model.access.csv',
        'commission_ax/security/ir.model.access.csv',

        # ============================================
        # Commission data and configuration
        # ============================================
        'commission_ax/data/commission_types_data.xml',
        'commission_ax/data/commission_payment_cron.xml',
        'commission_ax/data/commission_purchase_orders_action.xml',
        'commission_ax/data/commission_report_template.xml',
        'commission_ax/data/commission_report_wizard_action.xml',
        'commission_ax/data/cron_data.xml',

        # ============================================
        # Deals management views
        # ============================================
        'views/account_move_views.xml',
        'views/realestate_project_views.xml',
        'views/realestate_unit_views.xml',
        'views/sale_order_deals_views.xml',

        # ============================================
        # Commission views and wizards
        # ============================================
        'commission_ax/views/commission_actions.xml',
        'views/deals_menu.xml',
        'commission_ax/views/commission_menu.xml',
        'commission_ax/views/commission_type_views.xml',
        'commission_ax/views/sale_order.xml',
        'commission_ax/views/purchase_order.xml',
        'commission_ax/views/res_partner_views.xml',
        'commission_ax/views/commission_cancel_wizard_views.xml',
        'commission_ax/views/commission_payment_wizard_views.xml',
        'commission_ax/views/commission_partner_statement_wizard_views.xml',
        'commission_ax/views/commission_profit_analysis_wizard_views.xml',

        # ============================================
        # Reports
        # ============================================
        'commission_ax/reports/commission_report_template_enhanced.xml',
        'commission_ax/reports/commission_report.xml',
        'commission_ax/reports/commission_partner_statement_reports.xml',
        'commission_ax/reports/commission_payout_report_professional.xml',
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
