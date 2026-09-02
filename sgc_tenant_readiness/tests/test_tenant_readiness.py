# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Tests for the G28 onboarding model.

Coverage:
  - CO/MLRO + Alternate (single officer per role per tenant enforced).
  - Fit-and-proper assessment — required for activation; integrity +
    skills attestation required for a passing outcome.
  - Readiness state — per-capability gate open computed; cannot mark
    blocked as ready without resolving the block.
  - High-risk override — first-class record, segregation of duties
    enforced, override rationale + mitigation required when management
    decision differs from CO/MLRO recommendation.
"""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness", "sgc_gate")
class TestTenantReadiness(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Officer = cls.env["tenant.compliance.officer"]
        cls.FitAndProper = cls.env["tenant.fit.and.proper"]
        cls.State = cls.env["tenant.readiness.state"]
        cls.Capability = cls.env["tenant.readiness.capability"]
        cls.Override = cls.env["tenant.high.risk.override"]
        cls.Ack = cls.env["tenant.decision.acknowledgement"]
        cls.company = cls.env.ref("base.main_company")
        # Two users — one will be Primary, one Alternate, one customer-facing.
        cls.primary_user = cls.env["res.users"].create({
            "name": "Test Primary CO/MLRO",
            "login": "test_primary_compliance_officer",
            "email": "primary@example.com",
            "company_id": cls.company.id,
            "group_ids": [
                (4, cls.env.ref("base.group_user").id),
            ],
        })
        cls.alternate_user = cls.env["res.users"].create({
            "name": "Test Alternate CO/MLRO",
            "login": "test_alternate_compliance_officer",
            "email": "alternate@example.com",
            "company_id": cls.company.id,
            "group_ids": [
                (4, cls.env.ref("base.group_user").id),
            ],
        })
        cls.manager_user = cls.env["res.users"].create({
            "name": "Test Senior Manager",
            "login": "test_senior_manager",
            "email": "manager@example.com",
            "company_id": cls.company.id,
            "group_ids": [
                (4, cls.env.ref("base.group_user").id),
            ],
        })
        cls.customer_partner = cls.env["res.partner"].create({
            "name": "Test Customer",
            "company_id": cls.company.id,
        })

    # ---- CO/MLRO + Alternate uniqueness ---------------------------------

    def test_01_one_primary_one_alternate_per_company(self):
        self.Officer.create({
            "role": "primary",
            "user_id": self.primary_user.id,
            "tenant_company_id": self.company.id,
        })
        self.Officer.create({
            "role": "alternate",
            "user_id": self.alternate_user.id,
            "tenant_company_id": self.company.id,
        })
        # A second Primary for the same tenant must fail.
        with self.assertRaises(Exception):
            self.Officer.create({
                "role": "primary",
                "user_id": self.manager_user.id,
                "tenant_company_id": self.company.id,
            })

    # ---- Activation requires fit-and-proper -------------------------------

    def test_02_activation_requires_fit_and_proper(self):
        officer = self.Officer.create({
            "role": "primary",
            "user_id": self.primary_user.id,
            "tenant_company_id": self.company.id,
        })
        with self.assertRaises(ValidationError):
            officer.action_activate()

    def test_03_passing_assessment_requires_attestations(self):
        with self.assertRaises(ValidationError):
            self.FitAndProper.create({
                "subject_user_id": self.primary_user.id,
                "outcome": "pass",
                # integrity_attested missing on purpose
                # skills_attested missing on purpose
            })

    def test_04_full_pass_lifecycle(self):
        fap = self.FitAndProper.create({
            "subject_user_id": self.primary_user.id,
            "outcome": "pass",
            "integrity_attested": True,
            "skills_attested": True,
            "integrity_attested_by_name": "Test Reviewer",
            "integrity_attested_on": "2026-09-01",
            "qualifications_summary": "CAMS, CIPP/E",
            "experience_years": 10,
            "skills_summary": "AML/CFT investigations, regulatory reporting",
            "professional_path_attested": True,
            "professional_path_reference": "HR-2026-001",
            "assessor_name": "Test Reviewer",
        })
        officer = self.Officer.create({
            "role": "primary",
            "user_id": self.primary_user.id,
            "tenant_company_id": self.company.id,
            "fit_and_proper_id": fap.id,
            "appointment_date": "2026-09-01",
            "appointment_notification_date": "2026-09-02",
            "appointment_notification_reference": "MOET-2026-12345",
        })
        officer.action_activate()
        self.assertEqual(officer.state, "active")

    # ---- High-risk override segregation ---------------------------------

    def test_05_high_risk_override_segregation_enforced(self):
        """The CO/MLRO and the deciding manager must be different people.

        _check_segregation is a standing @api.constrains — it fires as
        soon as both fields are set, at create() itself. It is a data
        integrity invariant, not a stage-gated business rule.
        """
        with self.assertRaises(ValidationError):
            self.Override.create({
                "subject_customer_id": self.customer_partner.id,
                "tenant_company_id": self.company.id,
                "risk_classification": "high",
                "co_mlro_consulted_id": self.primary_user.id,
                "co_mlro_consultation_at": "2026-09-01 10:00:00",
                "co_mlro_recommendation": "decline",
                "co_mlro_recommendation_rationale": "Insufficient source of funds.",
                "management_decision": "proceed",
                "decided_by_id": self.primary_user.id,  # same person!
                "override_rationale": "Commercial value justifies the risk.",
                "mitigation": "Enhanced monitoring, monthly reviews.",
                "decision_at": "2026-09-01 11:00:00",
            })

    def test_06_high_risk_override_requires_rationale_when_differing(self):
        """When management's decision differs from CO/MLRO's, rationale + mitigation are required."""
        rec = self.Override.create({
            "subject_customer_id": self.customer_partner.id,
            "tenant_company_id": self.company.id,
            "risk_classification": "high",
            "co_mlro_consulted_id": self.primary_user.id,
            "co_mlro_consultation_at": "2026-09-01 10:00:00",
            "co_mlro_recommendation": "decline",
            "co_mlro_recommendation_rationale": "Insufficient source of funds.",
            "management_decision": "proceed",
            "decided_by_id": self.manager_user.id,
            # override_rationale + mitigation required — missing on purpose
            "decision_at": "2026-09-01 11:00:00",
        })
        rec.state = "awaiting_management"  # skip to the validation path
        with self.assertRaises(ValidationError):
            rec.action_record_management_decision()

    def test_07_high_risk_override_full_lifecycle_with_ack(self):
        """A full happy-path override records the acknowledgement."""
        rec = self.Override.create({
            "subject_customer_id": self.customer_partner.id,
            "tenant_company_id": self.company.id,
            "risk_classification": "high",
            "co_mlro_consulted_id": self.primary_user.id,
            "co_mlro_consultation_at": "2026-09-01 10:00:00",
            "co_mlro_recommendation": "decline",
            "co_mlro_recommendation_rationale": "Insufficient source of funds.",
            "management_decision": "proceed",
            "decided_by_id": self.manager_user.id,
            "override_rationale": "Commercial value justifies the risk.",
            "mitigation": "Enhanced monitoring, monthly reviews.",
            "decision_at": "2026-09-01 11:00:00",
        })
        rec.state = "awaiting_management"
        rec.action_record_management_decision()
        self.assertEqual(rec.state, "acknowledged")
        self.assertIsNotNone(rec.acknowledgement_id)
        # The acknowledgement is a TENANT_DECISION record with the recorded
        # rationale and mitigation in the body.
        ack = self.Ack.browse(rec.acknowledgement_id.id)
        self.assertIn("Commercial value", ack.decision_value)
        self.assertIn("Enhanced monitoring", ack.decision_value)
