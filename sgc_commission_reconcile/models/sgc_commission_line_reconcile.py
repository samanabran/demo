# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# EXTENDS the existing `commission.line` model from `sgc_commission` via
# `_inherit`. Per Section 0 CHECK 0.1, the confirmed model name in this
# codebase is `commission.line` (defined in
# `sgc_commission/models/commission_line.py`), NOT `sgc.commission.line`
# as originally assumed in the generation brief. Using the CONFIRMED
# name below — do not revert to the assumed name.
#
# This file does NOT redefine or duplicate the commission calculation
# engine. It only adds analytics/reconciliation fields and the
# Phase-9-boundary stub method.
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CommissionLineReconcile(models.Model):
    _inherit = "commission.line"

    tenant_id = fields.Many2one(
        "sgc.brokerage.tenant",
        ondelete="restrict",
        index=True,
        help="Owning tenant for multi-tenant reconciliation. Optional "
             "at the ORM level (a single-tenant sgc_commission "
             "installation may leave this blank) but required by the "
             "tenant-isolation ir.rule once a tenant is assigned.",
    )
    lead_create_date = fields.Datetime(
        help="Snapshot of crm.lead.create_date, stored (not computed) "
             "so it survives lead deletion. Populated by the calling "
             "flow that creates this commission line from a lead/deal, "
             "not automatically derived here.",
    )
    commission_received_date = fields.Date(
        help="Date the commission was actually confirmed received. "
             "Set manually, or via "
             "`sgc.commission.invoice_bridge.action_confirm_received()`.",
    )
    cycle_days = fields.Integer(
        compute="_compute_cycle_days",
        store=True,
        readonly=True,
        help="Days from lead creation to commission received. 0 until "
             "`commission_received_date` is set. Brief §1.3 metric.",
    )
    policy_id = fields.Many2one(
        "sgc.commission.policy",
        ondelete="set null",
        index=True,
        help="The tenant-configured policy this line was calculated "
             "against, if any. Set via the "
             "sgc.commission.policy.apply.wizard.",
    )
    invoice_bridge_ids = fields.One2many(
        "sgc.commission.invoice_bridge",
        "commission_line_id",
        string="Linked invoices",
    )

    @api.depends("lead_create_date", "commission_received_date")
    def _compute_cycle_days(self):
        for line in self:
            if line.lead_create_date and line.commission_received_date:
                delta_days = (
                    line.commission_received_date
                    - line.lead_create_date.date()
                ).days
                line.cycle_days = max(0, delta_days)
            else:
                line.cycle_days = 0

    def trigger_payout_calculation(self):
        """Phase-9 boundary marker.

        Payout disbursement logic is explicitly OUT OF SCOPE for this
        module — it is deferred to a future `sgc_commission_payout`
        addon. This stub must not be overridden ad hoc; see README.md
        "Phase 9 boundary note".
        """
        raise UserError(_(
            "Payout calculation is not yet active. Activate the "
            "sgc_commission_payout addon to enable this feature."
        ))
