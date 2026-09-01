# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Readiness state per capability per tenant.

The gate is per capability, never system-wide (per amendment §6).
A tenant missing Trakheesi credentials must be unable to publish listings
while remaining fully able to run property management. The state is
recorded here, and the relevant consumer module reads it to decide
whether the capability is available.

Per Wave 3 remediation round 2, defect 5: `state` was previously a plain
Selection field a human set by hand via `action_mark_ready()` — no code
path checked whether the tenant had actually populated the required
fields. That is a checkbox, not a gate. `state` is now driven by
`_recompute_for_tenant()`, which reads the capability's
`required_tenant_config` / `required_tenant_decision` lists and checks
each key against `tenant.readiness.config.value`. A human can no longer
mark a capability ready by clicking a button; the capability becomes
ready only when its required data is genuinely present. The only
manual override left is `action_mark_blocked` — an administrator can
force a capability CLOSED for cause, never force it OPEN.
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
    missing_keys = fields.Char(
        help="Comma-separated list of required keys not yet satisfied. "
             "Computed alongside state so the readiness dashboard can "
             "name what is missing, not just report closed.",
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

    # --- Completeness computation -----------------------------------------

    @staticmethod
    def _parse_csv(text):
        if not text:
            return []
        return [k.strip() for k in text.split(",") if k.strip()]

    def _compute_completeness(self):
        """Return (state, missing_keys) for this record based on the
        capability's required fields vs. the tenant's config-value store.

        A missing or blank row is unsatisfied. A tenant_decision row
        additionally requires a linked acknowledgement — see
        tenant.readiness.config.value._is_satisfied().
        """
        self.ensure_one()
        cap = self.capability_id
        required = self._parse_csv(cap.required_tenant_config) + \
            self._parse_csv(cap.required_tenant_decision)
        if not required:
            # A capability with no declared requirements has nothing to
            # gate on — this should not happen for any seeded capability,
            # but fail closed rather than silently open.
            return "not_configured", "(capability has no required fields declared)"

        ConfigValue = self.env["tenant.readiness.config.value"]
        rows = ConfigValue.search([
            ("tenant_company_id", "=", self.tenant_company_id.id),
            ("key", "in", required),
        ])
        rows_by_key = {r.key: r for r in rows}

        satisfied = []
        missing = []
        for key in required:
            row = rows_by_key.get(key)
            if row and row._is_satisfied():
                satisfied.append(key)
            else:
                missing.append(key)

        if not missing:
            return "ready", ""
        if satisfied:
            return "in_progress", ", ".join(missing)
        return "not_configured", ", ".join(missing)

    @api.model
    def _recompute_for_tenant(self, tenant_company_id):
        """Recompute every capability's state for one tenant.

        Called by tenant.readiness.config.value on create/write. Creates
        the state row if it does not yet exist (one per capability per
        tenant, per the unique constraint). A row already `blocked` is
        left blocked — blocking is a stronger, explicit override that
        only an admin's action_unblock can lift.
        """
        Capability = self.env["tenant.readiness.capability"]
        capabilities = Capability.search([("enabled", "=", True)])
        for cap in capabilities:
            state_rec = self.search([
                ("tenant_company_id", "=", tenant_company_id),
                ("capability_id", "=", cap.id),
            ], limit=1)
            if not state_rec:
                state_rec = self.create({
                    "tenant_company_id": tenant_company_id,
                    "capability_id": cap.id,
                })
            if state_rec.state == "blocked":
                continue
            new_state, missing = state_rec._compute_completeness()
            if new_state != state_rec.state or missing != (state_rec.missing_keys or ""):
                state_rec.write({
                    "state": new_state,
                    "missing_keys": missing,
                    "state_set_at": fields.Datetime.now(),
                })
        return True

    def action_recompute(self):
        """Manual trigger — recompute this record's completeness now."""
        for rec in self:
            if rec.state == "blocked":
                continue
            new_state, missing = rec._compute_completeness()
            rec.write({
                "state": new_state,
                "missing_keys": missing,
                "state_set_at": fields.Datetime.now(),
            })
        return True

    def action_mark_blocked(self, reason):
        """Force this capability closed regardless of completeness.

        The only manual override in this model. There is no symmetric
        action_mark_ready — readiness is earned by populating the
        required data, never granted by a click.
        """
        for rec in self:
            if not reason:
                raise ValidationError(_(
                    "Blocking a capability requires a reason. The block "
                    "must be visible and attributable."
                ))
            rec.state = "blocked"
            rec.state_reason = reason
        return True

    def action_unblock(self):
        """Lift a manual block. Reverts to the computed state, not to
        'ready' — the underlying data still has to be complete.
        """
        for rec in self:
            new_state, missing = rec._compute_completeness()
            rec.write({
                "state": new_state,
                "missing_keys": missing,
                "state_reason": False,
                "state_set_at": fields.Datetime.now(),
            })
        return True
