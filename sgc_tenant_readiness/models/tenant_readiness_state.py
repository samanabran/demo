# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Readiness state per capability per tenant.

The gate is per capability, never system-wide (per amendment §6).
A tenant missing Trakheesi credentials must be unable to publish listings
while remaining fully able to run property management. The state is
recorded here, and the relevant consumer module reads it to decide
whether the capability is available.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TenantReadinessState(models.Model):
    _name = "tenant.readiness.state"
    _description = "Tenant Readiness State"
    _order = "tenant_company_id, capability_id"
    _rec_name = "capability_id"

    tenant_company_id = fields.Many2one(
        "res.company", required=True, index=True, ondelete="cascade",
    )
    capability_id = fields.Many2one(
        "tenant.readiness.capability", required=True, index=True,
        ondelete="restrict",
    )
    state = fields.Selection(
        selection=[
            ("not_configured", "Not configured"),
            ("in_progress", "In progress"),
            ("ready", "Ready"),
            ("blocked", "Blocked"),
        ],
        required=True, default="not_configured", index=True,
    )

    # --- Audit -----------------------------------------------------------

    state_set_by_id = fields.Many2one("res.users", tracking=True)
    state_set_at = fields.Datetime(default=fields.Datetime.now)
    state_reason = fields.Text(
        help="Why the state is what it is. Required when the state is "
             "blocked or when transitioning from ready to anything else.",
    )

    # --- Computed gate ---------------------------------------------------

    gate_open = fields.Boolean(
        compute="_compute_gate_open", store=True,
        help="True when the capability is 'ready'. Read by consumer modules "
             "to decide whether the capability is available.",
    )

    @api.depends("state", "capability_id")
    def _compute_gate_open(self):
        for rec in self:
            rec.gate_open = rec.state == "ready"

    _sql_constraints = [
        ("capability_per_company_uniq",
         "UNIQUE(tenant_company_id, capability_id)",
         "Each tenant company may have only one state per capability."),
    ]

    def action_mark_ready(self):
        for rec in self:
            if rec.state == "blocked":
                raise ValidationError(_(
                    "Cannot mark a blocked capability as ready. Resolve the "
                    "block first."
                ))
            rec.state = "ready"
        return True

    def action_mark_blocked(self, reason):
        for rec in self:
            if not reason:
                raise ValidationError(_(
                    "Blocking a capability requires a reason. The block "
                    "must be visible and attributable."
                ))
            rec.state = "blocked"
            rec.state_reason = reason
        return True
