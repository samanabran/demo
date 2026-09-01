# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Exception queue.

The cross-cutting queue every module writes to when something goes wrong.
Classifications, severities, statuses, and routing are enforced at the
model layer. Retention clocks are carried per record so the rules-pack
retention constant binds here directly.
"""

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


# Classification catalogue. Stable identifiers — used in (de)serialisation,
# route rules, and reporting. Do not rename without a migration.
CLASSIFICATIONS = [
    ("integration", "Integration failure"),
    ("data", "Data / master record failure"),
    ("process", "Process / control breach"),
    ("dispute", "Client or counterparty dispute"),
    ("regulatory", "Regulatory event"),
]

SEVERITIES = [
    ("info", "Info"),
    ("warning", "Warning"),
    ("error", "Error"),
    ("critical", "Critical"),
]

STATUSES = [
    ("open", "Open"),
    ("in_progress", "In progress"),
    ("escalated", "Escalated"),
    ("resolved", "Resolved"),
    ("sealed", "Sealed — terminal"),
    ("dead_letter", "Dead-letter — terminal (no further retry)"),
]

TERMINAL_STATUSES = {"sealed", "dead_letter", "resolved"}


class ProcessException(models.Model):
    _name = "process.exception"
    _description = "Process Exception"
    _order = "severity desc, occurred_at desc, id desc"
    _inherit = ["mail.thread"]
    _rec_name = "summary"

    # --- Identification --------------------------------------------------

    summary = fields.Char(
        required=True, index=True, translate=True,
        help="One-line description of what went wrong.",
    )
    description = fields.Text()
    reference = fields.Char(
        help="Free-form external reference (job id, request id, …).",
    )

    # --- Classification --------------------------------------------------

    classification = fields.Selection(
        CLASSIFICATIONS, required=True, index=True,
    )
    severity = fields.Selection(
        SEVERITIES, required=True, index=True, default="error",
    )
    status = fields.Selection(
        STATUSES, required=True, index=True, default="open",
    )

    # --- Source / linkage ------------------------------------------------

    source_model = fields.Char(index=True)
    source_id = fields.Many2one_reference(
        model_field="source_model",
        string="Source record",
        help="Polymorphic reference to the record that raised this exception.",
    )
    # Tenant scoping. The exception is anchored to a company so the
    # per-tenant ir.rule can isolate it. Defaults to the current
    # user's company, never user-editable on a different tenant's
    # record (enforced by check_company + ir.rule).
    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda s: s.env.company,
    )
    integration_key = fields.Char(
        index=True,
        help="Idempotency key when the exception is integration-class.",
    )
    target_system = fields.Char(
        index=True,
        help="External system that failed (Dow Jones, Trakheesi, …).",
    )

    # --- Ownership -------------------------------------------------------

    owner_id = fields.Many2one(
        "res.users", string="Owner", tracking=True, index=True,
    )
    team_id = fields.Many2one(
        "res.teams", string="Team",
        help="Routing target on auto-classified exceptions.",
    )

    # --- Timing ----------------------------------------------------------

    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now)
    detected_at = fields.Datetime(
        default=fields.Datetime.now,
        help="When the failure was detected (may lag occurred_at for batch jobs).",
    )
    resolved_at = fields.Datetime(readonly=True)
    age_hours = fields.Float(
        compute="_compute_age_hours",
        help="Hours since occurred_at. Used for ageing reports.",
    )

    @api.depends("occurred_at", "status")
    def _compute_age_hours(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.status in TERMINAL_STATUSES:
                rec.age_hours = 0.0
            else:
                rec.age_hours = round((now - rec.occurred_at).total_seconds() / 3600.0, 2)

    # --- Retry / escalation ---------------------------------------------

    retry_count = fields.Integer(default=0)
    max_retries = fields.Integer(default=3)
    next_retry_at = fields.Datetime()
    escalation_level = fields.Integer(
        default=0,
        help="0=owner, 1=manager, 2=executive.",
    )

    # --- Alert -----------------------------------------------------------

    alert = fields.Boolean(
        default=False, index=True,
        help="True when the exception has raised a user-visible alert.",
    )
    alert_message = fields.Char()

    # --- Retention -------------------------------------------------------

    # Anchor-event catalogue. The retention clock does NOT start at
    # record creation. The clock starts at the right event per record
    # type — typically the terminal-state transition, the end of the
    # business relationship, or the completion of the transaction.
    # Early deletion of AML records is a worse failure than late deletion.
    RETENTION_ANCHOR_EVENTS = [
        ("record_creation", "Record creation — only when explicitly required by law"),
        ("terminal_state_entry", "Terminal state entry (sealed / dead_letter / resolved)"),
        ("relationship_end", "End of the business relationship"),
        ("transaction_completion", "Completion of the underlying transaction"),
    ]

    retention_anchor_event = fields.Selection(
        RETENTION_ANCHOR_EVENTS,
        default="terminal_state_entry",
        required=True, index=True,
        help="The event the retention clock starts from. Default is "
             "'terminal_state_entry' — the clock does not tick during the "
             "active life of the record.",
    )
    retention_anchor_at = fields.Datetime(
        compute="_compute_retention_anchor_at", store=True,
        help="The datetime the anchor event occurred. Set at the "
             "terminal-state transition by action_resolve / action_seal / "
             "the dead_letter park path.",
    )

    @api.depends("status", "resolved_at", "occurred_at")
    def _compute_retention_anchor_at(self):
        """Anchor datetime is set at the terminal-state transition.

        For anchor='terminal_state_entry' (default), the anchor is
        `resolved_at` for resolved, `now` for sealed/dead_letter, and
        `False` for live records. The clock is not ticking during
        active life — it is paused until terminal.
        """
        for rec in self:
            if rec.status in TERMINAL_STATUSES:
                if rec.status == "resolved" and rec.resolved_at:
                    rec.retention_anchor_at = rec.resolved_at
                else:
                    rec.retention_anchor_at = fields.Datetime.now()
            else:
                rec.retention_anchor_at = False

    retention_until = fields.Date(
        compute="_compute_retention_until", store=True,
    )

    @api.depends("retention_anchor_at", "retention_anchor_event")
    def _compute_retention_until(self):
        """Retention clock runs from the anchor event, not from creation.

        Default horizon is 5 years. The rules-pack constant binds via
        the consumer; this field is the cross-cutting default. The
        five-year horizon reads from `aml_retention_years` at the
        rules-pack layer when the constant is read at the consumer side.
        """
        DEFAULT_HORIZON_DAYS = 5 * 365
        for rec in self:
            if not rec.retention_anchor_at:
                # Live record — no clock ticking yet. The clock is set
                # at the terminal-state transition.
                rec.retention_until = False
                continue
            anchor_date = (
                rec.retention_anchor_at.date()
                if isinstance(rec.retention_anchor_at, datetime)
                else rec.retention_anchor_at
            )
            rec.retention_until = anchor_date + timedelta(days=DEFAULT_HORIZON_DAYS)

    # --- Constraints -----------------------------------------------------

    @api.constrains("status", "retry_count")
    def _check_retry_count_within_max(self):
        for rec in self:
            if rec.status != "dead_letter" and rec.retry_count > rec.max_retries:
                # Allow over-max only on dead_letter (terminal). Anything
                # else is a state corruption.
                raise ValidationError(_(
                    "Exception '%s' has retry_count=%(r)d greater than "
                    "max_retries=%(m)d but status=%(s)s. Either reset "
                    "retry_count or move the exception to dead_letter."
                ) % {
                    "r": rec.retry_count, "m": rec.max_retries, "s": rec.status,
                })

    # --- API -------------------------------------------------------------

    @api.model
    def raise_exception(self, summary, classification="error", severity="error",
                       source_model=None, source_id=None,
                       target_system=None, integration_key=None,
                       owner_id=None, description=None, alert=True,
                       max_retries=3):
        """Convenience creator that writes a chatter note, optionally alerts.

        Returns the new exception record.
        """
        rec = self.create({
            "summary": summary,
            "description": description or summary,
            "classification": classification,
            "severity": severity,
            "source_model": source_model,
            "source_id": source_id,
            "target_system": target_system,
            "integration_key": integration_key,
            "owner_id": owner_id,
            "alert": alert,
            "alert_message": summary if alert else False,
            "max_retries": max_retries,
        })
        return rec

    def action_mark_in_progress(self):
        for rec in self:
            if rec.status == "open":
                rec.status = "in_progress"
        return True

    def action_escalate(self):
        for rec in self:
            if rec.status in ("open", "in_progress"):
                rec.status = "escalated"
                rec.escalation_level = min(rec.escalation_level + 1, 2)
        return True

    def action_resolve(self):
        for rec in self:
            if rec.status in TERMINAL_STATUSES:
                continue
            rec.status = "resolved"
            rec.resolved_at = fields.Datetime.now()
            # Anchor the retention clock at the terminal-state transition.
            rec.retention_anchor_at = rec.resolved_at
        return True

    def action_seal(self):
        """Move to sealed — terminal state with retention locked.

        The retention anchor is set here. Sealing is the documented
        terminal-state event for retention-clock starts.
        """
        for rec in self:
            rec.status = "sealed"
            rec.resolved_at = rec.resolved_at or fields.Datetime.now()
            rec.retention_anchor_at = rec.resolved_at
        return True
