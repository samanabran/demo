# -*- coding: utf-8 -*-
{
    "name": "SGC Commission Reconcile",
    "summary": (
        "Configurable tiered commission policies, co-brokerage splits, "
        "cycle-time analytics, and an invoice-confirmation bridge — the "
        "reconciliation layer over sgc_commission."
    ),
    "version": "19.0.1.0.0",
    "category": "Real Estate / Finance",
    "license": "LGPL-3",
    "author": "Scholarix Global Consultants -FZCO",
    "website": "https://www.sgctech.ai",
    "depends": [
        "sgc_commission",
        "sgc_realestate_brokerage_template",
        "account",
        "crm",
        "mail",
    ],
    "data": [
        "security/sgc_commission_reconcile_groups.xml",
        "security/ir.model.access.csv",
        "security/ir_rule_tenant_isolation.xml",
        "views/sgc_commission_invoice_bridge_views.xml",
        "views/sgc_commission_policy_views.xml",
        "views/sgc_commission_partner_split_views.xml",
        "views/sgc_commission_line_reconcile_views.xml",
        "views/sgc_commission_reconcile_menus.xml",
        "data/sgc_commission_policy_default_data.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "description": """
SGC Commission Reconcile
=========================

Resolves the Phase 9 UNRESOLVED status of `sgc_commission` by adding a
tenant-scoped, fully-configurable reconciliation layer on top of it —
without redefining the calculation engine itself.

See README.md for the full configuration checklist, the Phase 9
boundary note, and the regulatory verification checklist that must be
completed by human counsel before go-live.
    """,
}
