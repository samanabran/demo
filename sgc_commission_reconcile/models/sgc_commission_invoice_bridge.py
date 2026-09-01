# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# NEW MODEL — a lightweight bridge to actual invoice/payment
# confirmation. Per the CRITICAL CONSTRAINTS: this model only READS
# `account.move.id` and `account.move.state`; it never creates or
# posts journal entries, and never duplicates accounting logic.
from odoo import _, api, fields, models


class SgcCommissionInvoiceBridge(models.Model):
    _name = "sgc.commission.invoice_bridge"
    _description = "Commission Invoice Bridge"
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(
        compute="_compute_name", store=True, readonly=True,
    )
    tenant_id = fields.Many2one(
        "sgc.brokerage.tenant",
        required=True,
        ondelete="restrict",
        index=True,
        check_company=True,
    )
    commission_line_id = fields.Many2one(
        "commission.line",
        required=True,
        ondelete="cascade",
        index=True,
    )
    invoice_id = fields.Many2one(
        "account.move",
        required=True,
        domain="[('move_type', 'in', ['out_invoice', 'out_refund'])]",
        ondelete="restrict",
        help="Read-only linkage to the invoice. This module reads "
             "`invoice_id.state`/`invoice_id.id` only — it never "
             "creates or posts account.move records.",
    )
    invoice_state = fields.Char(
        compute="_compute_invoice_state",
        store=True,
        readonly=True,
        help="Mirror of account.move.state for dashboard filtering "
             "only — no journal-entry logic is duplicated here.",
    )
    invoice_date = fields.Date(
        related="invoice_id.invoice_date", store=True, readonly=True,
    )
    amount_aed = fields.Monetary(
        currency_field="currency_id",
        help="Populated manually by the confirming user, not "
             "auto-derived from invoice lines — the agent must "
             "confirm the amount explicitly before receipt is "
             "recorded.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.ref("base.AED"),
    )
    confirmed_received = fields.Boolean(default=False, tracking=True)
    confirmed_received_date = fields.Date(tracking=True)
    notes = fields.Text()

    _sql_constraints = [
        ("sgc_commission_invoice_bridge_unique",
         "unique(commission_line_id, invoice_id)",
         "This invoice is already linked to this commission line."),
    ]

    @api.depends("commission_line_id", "invoice_id")
    def _compute_name(self):
        for bridge in self:
            bridge.name = _("%(line)s ↔ %(invoice)s") % {
                "line": bridge.commission_line_id.display_name or "?",
                "invoice": bridge.invoice_id.name or "?",
            }

    @api.depends("invoice_id.state")
    def _compute_invoice_state(self):
        for bridge in self:
            bridge.invoice_state = bridge.invoice_id.state or ""

    def action_confirm_received(self):
        """Explicit button trigger — NOT a silent onchange — to avoid
        accidental date overwrites. Writes the confirmation back onto
        the linked commission line so `cycle_days` can be computed.
        """
        today = fields.Date.context_today(self)
        for bridge in self:
            confirm_date = bridge.confirmed_received_date or today
            bridge.write({
                "confirmed_received": True,
                "confirmed_received_date": confirm_date,
            })
            if bridge.commission_line_id:
                bridge.commission_line_id.write({
                    "commission_received_date": confirm_date,
                })
                bridge.commission_line_id.message_post(
                    body=_(
                        "Commission receipt confirmed via invoice "
                        "%(invoice)s on %(date)s.",
                        invoice=bridge.invoice_id.name or "?",
                        date=confirm_date,
                    )
                )
