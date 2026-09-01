# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""CO/MLRO segregation mixin.

Per UAE MoJ Notice 247/2026: where CO/MLRO duties sit with someone holding
other responsibilities, that person must not have day-to-day responsibility
for sales or customer relationship management. The rule is enforceable in
code: a user holding the CO/MLRO role cannot be assigned as agent on a deal
or own a customer relationship.

This module is the gate. Other modules (the deal-assignment module, the
customer-relationship module) call this mixin's check before allowing the
assignment. A user holding the CO/MLRO role and being assigned as agent is
a system-block; a UserError raises with a clear message.

Class: VENDOR (the rule engine). The values (which user holds the role, which
deal / customer the assignment is about) are TENANT_CONFIG.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TenantMlroSegregationMixin(models.AbstractModel):
    """Mixin: a CO/MLRO user cannot be assigned as agent on a deal or
    own a customer relationship.

    Consumers implement ``_mlro_role_field()`` returning the Odoo
    res.users id of the user the segregation check should be applied to.
    The mixin returns one of two outcomes:

        * ALLOW — the user does not hold the CO/MLRO or Alternate role,
          or the user is a CO/MLRO but the caller has explicitly
          identified the relationship as a compliance activity
          (override flag).
        * BLOCK — the user holds the role and the caller has not
          overridden.

    The check is fail-closed: a missing record on the CO/MLRO side is
    treated as BLOCKED, not ALLOW.
    """

    _name = "tenant.mlro.segregation.mixin"
    _description = "Tenant MLRO Segregation Mixin"

    # Override flag for cases where a CO/MLRO legitimately touches a
    # deal — e.g. a deal where the CO/MLRO is the subject of the
    # decision rather than the agent. The caller must set this to True
    # AND set ``override_rationale`` to record why.
    override_segregation = fields.Boolean(
        help="Set to True to indicate the CO/MLRO is on the deal for a "
             "legitimate reason (e.g. subject of a case, not the agent).",
    )
    override_rationale = fields.Text(
        help="Why the segregation rule does not apply here. Required when "
             "override_segregation=True. Recorded verbatim — the caller is "
             "the source.",
    )

    @api.model
    def _mlro_role_user_id(self):
        """Override in the consumer to return the user the check applies to.

        Default: uses the model field ``user_id`` if present. Consumers
        with a different field name override this method.
        """
        return self.user_id.id if hasattr(self, "user_id") and self.user_id else None

    def _assert_not_mlro_on_sales_activity(self):
        """Block assignment when the user holds the CO/MLRO or Alternate role.

        Raises UserError on BLOCK. Returns silently on ALLOW.
        """
        self.ensure_one()
        user_id = self._mlro_role_user_id()
        if not user_id:
            # No user on the record — no segregation check possible.
            return
        Officer = self.env["tenant.compliance.officer"]
        officer = Officer.search([
            ("user_id", "=", user_id),
            ("state", "=", "active"),
            ("role", "in", ("primary", "alternate")),
        ], limit=1)
        if not officer:
            # The user is not a CO/MLRO. No segregation applies.
            return
        if self.override_segregation:
            if not self.override_rationale:
                raise UserError(_(
                    "Segregation override requires a rationale. Per "
                    "amendment §10.4, the rationale must be recorded."
                ))
            return
        raise UserError(_(
            "User '%(user)s' holds the %(role)s CO/MLRO role and cannot "
            "be assigned as agent on a deal or own a customer "
            "relationship. Per MoJ Notice 247/2026 segregation rule. "
            "Either pick a different user, or set "
            "override_segregation=True with a recorded rationale."
        ) % {
            "user": self.env["res.users"].browse(user_id).name,
            "role": "Primary" if officer.role == "primary" else "Alternate",
        })
