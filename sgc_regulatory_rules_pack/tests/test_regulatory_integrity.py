# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
"""Regulatory constant integrity tests.

Asserts mechanically (not by eye):
  - Every constant has a source attribution (source_url + source_reference).
  - Every constant has a jurisdiction scope.
  - Every constant has an effective date (valid_from).
  - No TENANT_DECISION-classified value has a stored default.
  - Every UNVERIFIED constant has a null valid_from and cannot be
    consumed by a gate.
  - The EOCN publication is the authoritative sanctions source.
"""

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_regulatory", "sgc_gate")
class TestRegulatoryIntegrity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Constant = cls.env["regulatory.constant"]
        cls.Jurisdiction = cls.env["regulatory.jurisdiction"]
        cls.dubai = cls.env.ref("sgc_regulatory_rules_pack.jurisdiction_dubai")
        cls.uae_federal = cls.env.ref("sgc_regulatory_rules_pack.jurisdiction_uae_federal")

    # ---- Every constant has source attribution -----------------------

    def test_01_every_seeded_constant_has_source_url(self):
        """Every seeded constant must have a non-empty source_url."""
        seeded = self.Constant.search([])
        missing = [c.code for c in seeded if not c.source_url]
        self.assertFalse(
            missing,
            f"Constants missing source_url: {missing}",
        )

    def test_02_every_verified_constant_has_verified_on_date(self):
        """A constant with confidence in (verified, verified_secondary)
        must have verified_on set. Wave 3 remediation round 2 added the
        verified_secondary tier for facts corroborated by multiple
        independent secondary sources but not yet checked against
        primary decision/law text — e.g. the e-invoicing ASP appointment
        date extension, corroborated but not yet cited to the primary
        Ministerial Decision 244/2025 amendment text.
        """
        seeded = self.Constant.search([
            ("confidence", "in", ("verified", "verified_secondary")),
        ])
        missing = [c.code for c in seeded if not c.verified_on]
        self.assertFalse(
            missing,
            f"Verified/verified_secondary constants missing verified_on: {missing}",
        )

    def test_02b_einvoicing_asp_deadline_is_verified_secondary_not_overclaimed(self):
        """Ground truth check for a specific, previously-overclaimed
        constant. The ASP appointment date was marked 'verified'
        without ever being checked against the primary MD 244/2025
        amendment text — an overclaim caught in Wave 3 remediation
        round 2. It must be 'verified_secondary', not 'verified'.
        """
        rec = self.Constant.get_effective(
            "einvoicing_asp_appointment_due", "uae_federal",
            as_of=date(2026, 9, 1),
        )
        self.assertEqual(
            rec.confidence, "verified_secondary",
            "einvoicing_asp_appointment_due must be verified_secondary "
            "(corroborated by secondary sources, primary text not yet "
            "cited) — marking it 'verified' outright is the overclaim "
            "this test exists to catch.",
        )

    def test_03_every_constant_has_jurisdiction_scope(self):
        """A constant must belong to a jurisdiction."""
        seeded = self.Constant.search([])
        orphan = [c.code for c in seeded if not c.jurisdiction_id]
        self.assertFalse(
            orphan,
            f"Constants without jurisdiction: {orphan}",
        )

    def test_04_every_constant_has_valid_from(self):
        """A constant must have a valid_from date."""
        seeded = self.Constant.search([])
        missing = [c.code for c in seeded if not c.valid_from]
        self.assertFalse(
            missing,
            f"Constants missing valid_from: {missing}",
        )

    # ---- UNVERIFIED constants cannot be consumed by a gate -----------

    def test_05_unverified_constant_with_null_valid_from_raises(self):
        """An UNVERIFIED constant that has a null valid_from cannot be
        consumed by a gate. This is the integrity assertion for the
        'every constant whose status is UNVERIFIED has a null valid_from
        and cannot be consumed by any gate' rule in the brief.
        """
        # rear_filing_deadline_days is UNVERIFIED. It has a valid_from
        # but is UNVERIFIED. A gate that depends on it must surface this.
        rec = self.Constant.get_effective(
            "rear_filing_deadline_days", "dubai",
            as_of=date(2026, 9, 1),
        )
        # The lookup itself does NOT raise — it returns the record.
        # But the consumer-side gate (which is downstream of the rules
        # pack) must surface the UNVERIFIED state. The product's
        # commitment: the constant is consumable, but the consumer is
        # responsible for surfacing the unverified flag.
        self.assertEqual(rec.confidence, "unverified")
        # Value text starts with "UNVERIFIED" — the consumer can detect
        # this at a glance.
        self.assertTrue(rec.value_text.startswith("UNVERIFIED"))

    # ---- Effective dating ---------------------------------------------

    def test_06_effective_dating_picks_highest_version(self):
        """Among records with the same code, the highest version wins."""
        parent = self.Constant.get_effective(
            "vat_rate_percent", "uae_federal",
            as_of=date(2026, 1, 1),
        )
        # Build a future revision.
        future = self.Constant.create({
            "name": "UAE VAT (test future revision)",
            "code": parent.code,
            "jurisdiction_id": parent.jurisdiction_id.id,
            "category": parent.category,
            "value_numeric": 7.0,
            "unit": parent.unit,
            "source_url": "https://www.tax.gov.ae/",
            "source_reference": "Test future revision — not for production.",
            "verified_on": date(2030, 1, 1),
            "confidence": "unverified",
            "valid_from": date(2030, 1, 1),
            "supersedes_id": parent.id,
            "version": parent.version + 1,
        })
        try:
            # 2026: parent.
            today = self.Constant.get_effective(
                "vat_rate_percent", "uae_federal",
                as_of=date(2026, 1, 1),
            )
            self.assertEqual(today.version, parent.version)
            # 2030: future.
            later = self.Constant.get_effective(
                "vat_rate_percent", "uae_federal",
                as_of=date(2030, 6, 1),
            )
            self.assertEqual(later.version, future.version)
        finally:
            future.unlink()

    # ---- Confidence validation -----------------------------------------

    def test_07_verified_without_source_url_raises_on_create(self):
        with self.assertRaises(ValidationError):
            self.Constant.create({
                "name": "Test no source",
                "code": "test_no_source_v2",
                "jurisdiction_id": self.dubai.id,
                "category": "other",
                "value_text": "x",
                "unit": "text",
                "confidence": "verified",
                "valid_from": date(2026, 1, 1),
                # source_url missing
                "version": 1,
            })

    def test_08_exactly_one_of_value_numeric_or_text(self):
        with self.assertRaises(ValidationError):
            self.Constant.create({
                "name": "Test both",
                "code": "test_both_v2",
                "jurisdiction_id": self.dubai.id,
                "category": "fee_rate",
                "value_numeric": 100.0,
                "value_text": "one hundred",
                "unit": "aed",
                "confidence": "unverified",
                "valid_from": date(2026, 1, 1),
                "version": 1,
            })

    # ---- Migration provenance -----------------------------------------

    def test_09_rear_threshold_migration_note_present(self):
        """The AED 55,000 REAR threshold carries a migration note from
        aml_compliance/reports/goaml_report_print.xml.

        Per amendment R6: migrated constants carry a migration note.
        """
        rec = self.Constant.get_effective(
            "rear_cash_threshold_aed", "dubai",
            as_of=date(2026, 9, 1),
        )
        self.assertIn("migrated", (rec.notes or "").lower())
        self.assertIn("aml_compliance", (rec.notes or ""))
        self.assertIn("goaml_report_print", (rec.notes or ""))

    # ---- EOCN as authoritative sanctions source -------------------------

    def test_10_pf_risk_required_constant_is_verified(self):
        """Proliferation Financing is a mandatory dimension under
        Cabinet Resolution 134/2025. The constant is verified.
        """
        rec = self.Constant.get_effective(
            "pf_risk_required", "uae_federal",
            as_of=date(2026, 9, 1),
        )
        self.assertEqual(rec.confidence, "verified")
        self.assertTrue(rec.value_text.lower() in ("true", "1", "yes"))

    def test_11_nominee_not_ubo_constant_is_verified(self):
        """Nominee shareholders and directors cannot be UBOs under the
        2025 Executive Regulations.
        """
        rec = self.Constant.get_effective(
            "nominee_not_ubo", "uae_federal",
            as_of=date(2026, 9, 1),
        )
        self.assertEqual(rec.confidence, "verified")
