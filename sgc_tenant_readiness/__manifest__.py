# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
# See LICENSE file for full copyright and licensing details.
{
    "name": "SGC Tenant Readiness",
    "summary": (
        "Per-tenant onboarding model. Holds the CO/MLRO and Alternate "
        "(with fit-and-proper assessments), the LNOO reference field, the "
        "per-capability readiness state, and the high-risk-customer override "
        "record. Closes G28 and provides the primary-source basis for G18."
    ),
    "version": "19.0.1.0.0",
    "category": "Tools / Onboarding",
    "author": "Scholarix Global Consultants -FZCO",
    "website": "https://www.sgctech.ai",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "sgc_regulatory_rules_pack",
        "sgc_process_control",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data — capability catalogue (per amendment §6)
        "data/tenant_readiness_capability_data.xml",
        # Views
        "views/tenant_compliance_officer_views.xml",
        "views/tenant_readiness_state_views.xml",
        "views/tenant_high_risk_override_views.xml",
        "views/tenant_readiness_dashboard_views.xml",
        "views/tenant_menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "sequence": 52,
    "description": """
SGC Tenant Readiness
====================

Per-tenant onboarding model. Holds the CO/MLRO and Alternate with their
fit-and-proper assessments, the LNOO reference field, the per-capability
readiness state, and the high-risk-customer override record. Closes G28
and provides the primary-source basis for G18 (agent-licence segregation).

The module supports the tenant's onboarding programme. It does not
constitute one. The CO/MLRO is appointed by the tenant. The fit-and-proper
assessment is performed by the tenant. The high-risk override is decided
by the tenant's senior management. The module provides the engine; the
tenants own the values.

Class assignment (per amendment §4):

* The engine, the capability catalogue, the segregation mixin, the
  override record's structure and state machine — VENDOR.
* CO/MLRO identity, Alternate identity, fit-and-proper records, LNOO
  reference, broker / agent licence credentials, screening provider
  identity — TENANT_CONFIG. Blank by default. No defaults. Mandatory
  source citation.
* Risk-appetite thresholds, EDD trigger levels, override rationale,
  mitigation text — TENANT_DECISION. Blank by default. Source +
  acknowledgement required.

Primary sources (per amendment §10 outstanding item 4):

* UAE MoJ Notice No. 247 of 2026 — joint guidance on the AML/CFT/CPF
  Compliance Officer, referencing Article 22 of Cabinet Resolution 134/2025.
* UAE MoET DNFBP Guidelines, March 2026 — qualification assessments,
  background verification, appointment notification.
* Cabinet Resolution 134/2025 — Article 22 (CO/MLRO report cycle).
* Cabinet Decision 74/2020 — Article 21 (Sanctions Compliance Program).

The CO/MLRO cannot be outsourced at all (Section 4.2 of MoJ Notice 247/2026).
Specific tasks may be, after a Letter of No Objection (LNOO) from the
supervisory authority. The LNOO reference is recorded here as a
TENANT_CONFIG field, blank. Tenants who determine they need one fill it in;
tenants who determine they do not leave it blank.
    """,
}
