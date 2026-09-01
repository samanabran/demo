# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Generic key/value store for TENANT_CONFIG and TENANT_DECISION values.

Per Wave 3 remediation round 2, defect 5: the fresh-tenant blocking
matrix's "unblocks when complete" half was untestable because
`tenant.readiness.state.state` was a plain Selection field a human sets
by hand via `action_mark_ready()` — there was no code path that actually
checked whether the tenant's required fields were populated. A readiness
gate that a human flips manually is a checkbox, not a gate; it does not
enforce anything, which is exactly the failure mode G28 exists to close.

This model is the tenant-side value store: one row per
(tenant, key). The key names match the comma-separated lists in
`tenant.readiness.capability.required_tenant_config` /
`.required_tenant_decision` (e.g. `goaml_organisation_id`,
`trakheesi_credentials`, `eocn_registration_reference`).

Class: VENDOR (the store and the completeness algorithm are ours).
The values themselves are TENANT_CONFIG or TENANT_DECISION per the
`field_class` on each row, matching the classification the capability
catalogue already declares for that key.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TenantReadinessConfigValue(models.Model):
    _name = "tenant.readiness.config.value"
    _description = "Tenant Readiness Config Value"
    _order = "tenant_company_id, key"
    _rec_name = "key"

    tenant_company_id = fields.Many2one(
        "res.company", required=True, index=True, ondelete="cascade",
    )
    key = fields.Char(
        required=True, index=True,
        help="Matches a name in a capability's required_tenant_config "
             "or required_tenant_decision CSV list.",
    )
    value = fields.Char(
        help="The tenant-supplied value. Blank counts as not-set for "
             "readiness purposes — an empty string and no row at all "
             "are treated identically by the completeness check.",
    )
    field_class = fields.Selection(
        selection=[
            ("tenant_config", "TENANT_CONFIG"),
            ("tenant_decision", "TENANT_DECISION"),
        ],
        required=True, default="tenant_config",
    )
    acknowledgement_id = fields.Many2one(
        "tenant.decision.acknowledgement",
        help="Required (non-null) before a tenant_decision value counts "
             "as satisfied. A TENANT_DECISION value with no cited source "
             "and no acknowledgement is not a decision — it is a guess "
             "the tenant has not actually signed off on.",
    )

    _sql_constraints = [
        ("tenant_key_uniq",
         "UNIQUE(tenant_company_id, key)",
         "One value per key per tenant."),
    ]

    @api.constrains("field_class", "value", "acknowledgement_id")
    def _check_decision_requires_acknowledgement(self):
        for rec in self:
            if rec.field_class == "tenant_decision" and rec.value:
                if not rec.acknowledgement_id:
                    raise ValidationError(_(
                        "'%s' is a TENANT_DECISION value with a value "
                        "set but no acknowledgement. Per R9, a decision "
                        "value is not satisfied until the tenant's "
                        "acknowledgement (source + sign-off) is recorded."
                    ) % rec.key)

    def _is_satisfied(self):
        """A row is satisfied when it has a non-blank value, and — for
        tenant_decision rows — a linked acknowledgement.
        """
        self.ensure_one()
        if not self.value:
            return False
        if self.field_class == "tenant_decision" and not self.acknowledgement_id:
            return False
        return True

    @api.model
    def set_value(self, tenant_company_id, key, value, field_class="tenant_config",
                acknowledgement_id=None):
        """Convenience upsert. Triggers readiness recomputation on the
        tenant's capability states after write.
        """
        rec = self.search([
            ("tenant_company_id", "=", tenant_company_id),
            ("key", "=", key),
        ], limit=1)
        vals = {
            "tenant_company_id": tenant_company_id,
            "key": key,
            "value": value,
            "field_class": field_class,
        }
        if acknowledgement_id:
            vals["acknowledgement_id"] = acknowledgement_id
        if rec:
            rec.write(vals)
        else:
            rec = self.create(vals)
        self.env["tenant.readiness.state"]._recompute_for_tenant(tenant_company_id)
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            self.env["tenant.readiness.state"]._recompute_for_tenant(
                rec.tenant_company_id.id
            )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        tenants = recs.mapped("tenant_company_id").ids
        for tenant_id in tenants:
            self.env["tenant.readiness.state"]._recompute_for_tenant(tenant_id)
        return recs
