# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Dead-letter queue.

A DLQ entry holds a failed integration call that has exhausted its retries.
Every DLQ entry is also a ``process.exception`` with classification
'integration' and status 'dead_letter' — the two are paired for visibility.

The Wave 1 exit gate proves that a deliberately failed screening call lands
here, not as a clear result.
"""

from odoo import _, api, fields, models


class ProcessDlq(models.Model):
    _name = "process.dlq"
    _description = "Process Dead-Letter Queue"
    _order = "occurred_at desc, id desc"
    _inherit = ["mail.thread"]
    _rec_name = "summary"

    # --- Identification --------------------------------------------------

    summary = fields.Char(required=True, index=True)
    target_system = fields.Char(
        required=True, index=True,
        help="External system that failed (Dow Jones, Trakheesi, bank feed, …).",
    )
    operation = fields.Char(
        required=True, index=True,
        help="Operation name (e.g. 'screening.match', 'portal.push').",
    )
    idempotency_key = fields.Char(index=True)
    request_payload = fields.Text(
        help="Serialised request that failed.",
    )
    response_payload = fields.Text(
        help="Serialised response (or error message) from the last attempt.",
    )

    # --- Linked exception ------------------------------------------------

    exception_id = fields.Many2one(
        "process.exception", required=True, ondelete="restrict",
        domain=[("classification", "=", "integration"),
                ("status", "=", "dead_letter")],
    )
    # Tenant scoping. Derived from the linked exception so the
    # per-tenant ir.rule can isolate. Stored explicitly so a
    # search by company does not require a join.
    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda s: s.env.company,
    )

    # --- Timing / attempts ----------------------------------------------

    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now)
    first_attempt_at = fields.Datetime()
    last_attempt_at = fields.Datetime()
    attempt_count = fields.Integer(default=0)

    # --- Status -----------------------------------------------------------

    status = fields.Selection(
        selection=[
            ("parked", "Parked — awaiting manual replay"),
            ("replayed", "Replayed — replay in progress"),
            ("resolved", "Resolved — call succeeded after replay"),
            ("abandoned", "Abandoned — terminal"),
        ],
        required=True, default="parked", index=True,
    )

    # --- Reprocessing ----------------------------------------------------

    replay_at = fields.Datetime()
    replay_by_id = fields.Many2one("res.users")
    resolution_note = fields.Text()

    # --- API -------------------------------------------------------------

    @api.model
    def park(self, summary, target_system, operation,
            exception_id, idempotency_key=None,
            request_payload=None, response_payload=None,
            attempt_count=0, first_attempt_at=None, last_attempt_at=None):
        """Park a failed integration call after retry exhaustion.

        Caller must have already created a ``process.exception`` with
        classification='integration' and status='dead_letter'. This
        method creates the DLQ record, links it, and anchors the
        retention clock on the exception at the dead_letter
        transition (per G27 §5 — the clock starts at the
        terminal-state transition, not at creation).
        """
        # Anchor the retention clock at the dead_letter transition.
        if exception_id and not exception_id.retention_anchor_at:
            exception_id.write({
                "retention_anchor_event": "terminal_state_entry",
                "retention_anchor_at": fields.Datetime.now(),
            })
        return self.create({
            "summary": summary,
            "target_system": target_system,
            "operation": operation,
            "exception_id": exception_id.id,
            "idempotency_key": idempotency_key,
            "request_payload": request_payload,
            "response_payload": response_payload,
            "attempt_count": attempt_count,
            "first_attempt_at": first_attempt_at or fields.Datetime.now(),
            "last_attempt_at": last_attempt_at or fields.Datetime.now(),
        })

    def action_mark_replayed(self):
        for rec in self:
            if rec.status == "parked":
                rec.status = "replayed"
        return True

    def action_resolve(self):
        for rec in self:
            if rec.status in ("replayed", "parked"):
                rec.status = "resolved"
        return True

    def action_abandon(self):
        for rec in self:
            rec.status = "abandoned"
        return True
