# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
from odoo import _, fields, models


class SgcCommissionPolicyApplyWizard(models.TransientModel):
    _name = "sgc.commission.policy.apply.wizard"
    _description = "Apply Commission Policy to Lines"

    policy_id = fields.Many2one(
        "sgc.commission.policy", required=True,
    )
    line_ids = fields.Many2many(
        "commission.line",
        help="Lines to apply the policy to. Model name confirmed via "
             "Section 0 CHECK 0.1 as `commission.line`.",
    )
    overwrite_existing = fields.Boolean(
        default=False,
        help="If unchecked, only lines with an empty policy_id are "
             "updated. If checked, all selected lines are overwritten.",
    )

    def action_apply(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.policy_id and not self.overwrite_existing:
                continue
            line.write({"policy_id": self.policy_id.id})
            line.message_post(
                body=_(
                    "Commission policy set to %(policy)s via bulk-apply "
                    "wizard.",
                    policy=self.policy_id.display_name,
                )
            )
        return {"type": "ir.actions.act_window_close"}
