# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Tests for the exception queue, DLQ, idempotency, and SLA models."""

from datetime import datetime, timedelta

from odoo.exceptions import ValidationError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_process_control", "sgc_gate")
class TestProcessControl(TransactionCase):
    # The exit-gate class lives in test_exit_gate.py and is named
    # TestExitGate — this name is referenced by the Wave 3 install
    # protocol command 6.4. Renaming this class to a different name
    # would cause 6.4 to silently match nothing and the run to exit
    # zero with zero exit-gate coverage. The check lives in the
    # meta-test (test_count_meta.py) — see TestCountMeta.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Exception = cls.env["process.exception"]
        cls.Dlq = cls.env["process.dlq"]
        cls.Idem = cls.env["process.idempotency"]
        cls.Sla = cls.env["process.sla"]

    # ---- Exception queue -------------------------------------------------

    def test_01_exception_create_minimal(self):
        exc = self.Exception.raise_exception(
            summary="Integration X timed out",
            classification="integration",
            severity="error",
            target_system="DowJones",
            integration_key="dj-2026-001",
        )
        self.assertEqual(exc.status, "open")
        self.assertEqual(exc.alert, True)
        self.assertEqual(exc.classification, "integration")

    def test_02_exception_lifecycle(self):
        exc = self.Exception.raise_exception(
            summary="Portal push failed",
            classification="integration",
            target_system="Bayut",
        )
        exc.action_mark_in_progress()
        self.assertEqual(exc.status, "in_progress")
        exc.action_escalate()
        self.assertEqual(exc.status, "escalated")
        self.assertEqual(exc.escalation_level, 1)
        exc.action_resolve()
        self.assertEqual(exc.status, "resolved")
        self.assertIsNotNone(exc.resolved_at)

    def test_03_retry_count_within_max_required_for_open(self):
        """retry_count > max_retries on an open exception is a state corruption."""
        exc = self.Exception.raise_exception(
            summary="Test",
            classification="integration",
            max_retries=2,
        )
        with self.assertRaises(ValidationError):
            exc.write({"retry_count": 5})

    def test_04_retry_count_can_exceed_max_on_dead_letter(self):
        exc = self.Exception.raise_exception(
            summary="Test",
            classification="integration",
            max_retries=2,
        )
        exc.write({"retry_count": 5, "status": "dead_letter"})
        # Should not raise — dead_letter is the documented terminal exception.
        exc._check_retry_count_within_max()

    # ---- DLQ -------------------------------------------------------------

    def test_05_dlq_park_creates_linked_exception(self):
        exc = self.Exception.raise_exception(
            summary="Screening call failed",
            classification="integration",
            severity="critical",
            target_system="DowJones",
        )
        exc.write({"status": "dead_letter"})
        dlq = self.Dlq.park(
            summary="Screening call exhausted retries",
            target_system="DowJones",
            operation="screening.match",
            exception_id=exc,
            idempotency_key="dj-2026-001",
            attempt_count=3,
        )
        self.assertEqual(dlq.status, "parked")
        self.assertEqual(dlq.exception_id, exc)
        self.assertEqual(dlq.target_system, "DowJones")

    # ---- Idempotency -----------------------------------------------------

    def test_06_idempotency_get_or_create(self):
        rec1, is_new1 = self.Idem.get_or_create(
            key="abc", target_system="DowJones", operation="screening.match",
        )
        self.assertTrue(is_new1)
        rec2, is_new2 = self.Idem.get_or_create(
            key="abc", target_system="DowJones", operation="screening.match",
        )
        self.assertFalse(is_new2)
        self.assertEqual(rec1.id, rec2.id)

    def test_07_idempotency_different_op_same_key(self):
        """Same key under different operation is a different idempotency record."""
        rec1, _ = self.Idem.get_or_create(key="x", target_system="S1", operation="op1")
        rec2, _ = self.Idem.get_or_create(key="x", target_system="S1", operation="op2")
        self.assertNotEqual(rec1.id, rec2.id)

    # ---- SLA clock -------------------------------------------------------

    def test_08_sla_attempt_exhaustion_raises_exception(self):
        sla = self.Sla.create({
            "name": "Document chase SLA",
            "rule_code": "kyc_document_chase",
            "due_at": datetime.now() + timedelta(days=1),
            "max_attempts": 2,
        })
        sla.action_record_attempt()
        sla.action_record_attempt()
        self.assertTrue(sla.exhausted)
        # An exception was raised by the SLA on the second attempt.
        exc = self.Exception.search([
            ("source_model", "=", "process.sla"),
            ("source_id", "=", sla.id),
        ])
        self.assertTrue(exc, "Exhaustion must raise an exception")

    def test_09_sla_pause_resume(self):
        sla = self.Sla.create({
            "name": "Test pause",
            "due_at": datetime.now() + timedelta(hours=2),
        })
        sla.action_pause()
        self.assertTrue(sla.paused)
        sla.action_resume()
        self.assertFalse(sla.paused)
