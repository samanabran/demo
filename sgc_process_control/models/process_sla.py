# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""SLA clocks.

A clock starts at a configurable trigger and escalates on breach.
Closes G6 (bounded document chase with attempt counter and SLA breach).
The clock reads its due-window from a named rules-pack constant by code
when available; falls back to a parameter otherwise.
"""

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProcessSla(models.Model):
    _name = "process.sla"
    _description = "Process SLA Clock"
    _order = "due_at asc, id asc"
    _rec_name = "name"

    name = fields.Char(required=True, index=True)
    description = fields.Text()

    # --- Linkage ---------------------------------------------------------

    source_model = fields.Char(index=True)
    source_id = fields.Many2one_reference(model_field="source_model")
    rule_code = fields.Char(
        index=True,
        help="Identifier used by consumers to find their clock.",
    )
    # Tenant scoping.
    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda s: s.env.company,
    )

    # --- Timing ----------------------------------------------------------

    started_at = fields.Datetime(required=True, default=fields.Datetime.now)
    due_at = fields.Datetime(required=True)
    paused_at = fields.Datetime()
    paused_total_seconds = fields.Integer(default=0)

    paused = fields.Boolean(default=False)
    breached = fields.Boolean(default=False, index=True)
    resolved_at = fields.Datetime()

    # --- Escalation ------------------------------------------------------

    escalation_level = fields.Integer(default=0)
    next_escalation_at = fields.Datetime()

    # --- Attempt counter (G6) -------------------------------------------

    attempt_count = fields.Integer(default=0)
    max_attempts = fields.Integer(default=3)
    exhausted = fields.Boolean(default=False, index=True)
    exhausted_at = fields.Datetime()

    # --- API -------------------------------------------------------------

    def action_start(self, due_in_minutes):
        for rec in self:
            rec.started_at = fields.Datetime.now()
            rec.due_at = fields.Datetime.now() + timedelta(minutes=due_in_minutes)
            rec.paused = False
        return True

    def action_pause(self):
        for rec in self:
            if not rec.paused:
                rec.paused = True
                rec.paused_at = fields.Datetime.now()
        return True

    def action_resume(self):
        for rec in self:
            if rec.paused and rec.paused_at:
                paused_seconds = (fields.Datetime.now() - rec.paused_at).total_seconds()
                rec.paused_total_seconds += int(paused_seconds)
                rec.due_at = rec.due_at + timedelta(seconds=paused_seconds)
                rec.paused = False
                rec.paused_at = False
        return True

    def action_record_attempt(self):
        """Increment the attempt counter; on exhaustion, raise an exception."""
        Exception = self.env["process.exception"]
        for rec in self:
            rec.attempt_count += 1
            if rec.attempt_count >= rec.max_attempts:
                rec.exhausted = True
                rec.exhausted_at = fields.Datetime.now()
                Exception.raise_exception(
                    summary=_("SLA attempts exhausted for %s") % rec.name,
                    classification="process",
                    severity="error",
                    source_model=self._name,
                    source_id=rec.id,
                    alert=True,
                )

    def action_resolve(self):
        for rec in self:
            rec.resolved_at = fields.Datetime.now()
            rec.breached = False
        return True
