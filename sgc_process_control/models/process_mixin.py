# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Fail-closed mixin for any consumer that depends on an external integration.

The brief §4 Directive Two requires that compliance modules must not depend
on transaction modules. The correct pattern is the other way: every
money-touching model inherits this mixin and calls ``_assert_compliance_cleared()``
in its own transition method.

The mixin returns one of three outcomes — CLEARED, BLOCKED, INDETERMINATE.
INDETERMINATE behaves as BLOCKED. Missing records behave as BLOCKED. This
is the Wave 1 exit gate pattern.

Consumers must not treat a missing record as "no adverse finding." That
is the most dangerous defect in the chain.
"""

import enum

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ComplianceOutcome(enum.Enum):
    CLEARED = "cleared"
    BLOCKED = "blocked"
    INDETERMINATE = "indeterminate"


class ProcessFailClosedMixin(models.AbstractModel):
    """Mixin: fail-closed guard for any money-touching transition.

    Consumers implement ``_compliance_check_record_id()`` returning the
    record id of the screening / compliance case that must be CLEARED
    before the consumer's action proceeds. The mixin then performs the
    fail-closed check.

    Override hooks:
        * ``_compliance_check_record_id()`` — return the case record id.
        * ``_compliance_check_consumer_name()`` — return a string used in
          error messages (default: ``self._name``).
    """

    _name = "process.fail_closed.mixin"
    _description = "Process Fail-Closed Mixin"

    compliance_case_model = fields.Char(
        default="kyc.application",
        help="Model name of the compliance case to check (default: kyc.application).",
    )

    def _compliance_check_consumer_name(self):
        return self._name

    @api.model
    def _compliance_check_record_id(self):
        """Override in the consumer to return the relevant case id."""
        raise NotImplementedError(
            "Consumers of process.fail_closed.mixin must implement "
            "_compliance_check_record_id()"
        )

    def _assert_compliance_cleared(self):
        """Fail-closed guard. Raises UserError on BLOCKED or INDETERMINATE.

        Returns the CLEARED case record on success. Consumers must call
        this in their state-transition method (write/button handlers).

        Three outcomes, not two:
            * CLEARED — the screening / compliance case is approved and
              still in force.
            * BLOCKED — the case is rejected, sealed, or expired.
            * INDETERMINATE — the case is missing, in pending review, or
              timed out. Behaves as BLOCKED. Always raises an exception.

        A missing record is INDETERMINATE. A pending review is INDETERMINATE.
        A sealed case is BLOCKED. Only ``state='approved'`` is CLEARED.
        """
        case_id = self._compliance_check_record_id()
        consumer = self._compliance_check_consumer_name()
        if not case_id:
            self._raise_indeterminate(consumer, reason="no compliance case linked")
        case = self.env[self.compliance_case_model].browse(case_id).exists()
        if not case:
            self._raise_indeterminate(consumer, reason="compliance case record missing")
        state = getattr(case, "state", None)
        if state == "approved":
            return case
        if state in ("rejected", "sealed", "expired", "blocked"):
            raise UserError(_(
                "%(consumer)s blocked: compliance case %(case)s is in "
                "state '%(state)s'. Money cannot move."
            ) % {
                "consumer": consumer, "case": case.display_name,
                "state": state,
            })
        # pending, in_review, draft, anything else → INDETERMINATE
        self._raise_indeterminate(consumer, reason=(
            "compliance case %s is in state '%s'" % (case.display_name, state)
        ))

    def _raise_indeterminate(self, consumer, reason):
        """INDETERMINATE == BLOCKED, always raises an exception.

        The exception queue entry is what surfaces this state visibly.
        """
        Exception = self.env["process.exception"]
        Exception.raise_exception(
            summary=_("%s blocked: %s") % (consumer, reason),
            classification="integration",
            severity="critical",
            source_model=self._name,
            source_id=self.id if self and self.id else None,
            alert=True,
        )
        raise UserError(_(
            "%(consumer)s blocked: %(reason)s. This is INDETERMINATE, "
            "not CLEARED. Resolve the compliance case before retrying."
        ) % {"consumer": consumer, "reason": reason})
