# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Readiness capability catalogue.

The catalogue of capabilities a tenant activates through the readiness gate.
Each capability is gated on a specific set of TENANT_CONFIG / TENANT_DECISION
fields. Gate scope is per capability, never system-wide (per amendment §6).
"""

from odoo import _, api, fields, models


CAPABILITY_STATES = [
    ("not_configured", "Not configured — required fields blank"),
    ("in_progress", "In progress — partial fields populated"),
    ("ready", "Ready — all required fields populated"),
    ("blocked", "Blocked — explicit tenant hold"),
]


CAPABILITY_SEVERITY = [
    ("critical", "Critical — gate required for go-live"),
    ("high", "High — gate required for the capability to operate"),
    ("medium", "Medium — gate recommended"),
]


class TenantReadinessCapability(models.Model):
    _name = "tenant.readiness.capability"
    _description = "Tenant Readiness Capability"
    _order = "sequence, code"
    _rec_name = "name"

    code = fields.Char(required=True, index=True, unique=True)
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)
    severity = fields.Selection(CAPABILITY_SEVERITY, default="high", required=True)

    # --- Required fields -------------------------------------------------

    required_tenant_config = fields.Text(
        translate=True,
        help="Comma-separated list of TENANT_CONFIG fields that must be populated "
             "for this capability to be 'ready'.",
    )
    required_tenant_decision = fields.Text(
        translate=True,
        help="Comma-separated list of TENANT_DECISION fields that must be "
             "populated AND acknowledged for this capability to be 'ready'.",
    )

    # --- Operational mapping --------------------------------------------

    enabled = fields.Boolean(default=True)
    module_dependency = fields.Char(
        help="Module that owns this capability. The capability is 'ready' when "
             "the module is installed and the required fields are populated.",
    )
