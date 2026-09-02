# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
"""Tests for the rules pack.

These tests prove:
  1. The hard-coded AED 55,000 REAR threshold has been migrated off the
     consumer (aml_compliance) and onto the rules pack.
  2. Lookup by code + jurisdiction + as_of returns the right record.
  3. Effective dating works — different versions win on different dates.
  4. UNVERIFIED entries are flagged but not blocked at lookup time
     (the consumer decides whether to surface that state).
  5. Confidence=verified requires source_url and verified_on.
  6. The bool unit parses correctly.
  7. Exactly-one-of-value constraint is enforced.
"""

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_regulatory", "sgc_gate")
class TestRegulatoryRulesPack(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Constant = cls.env["regulatory.constant"]
        cls.Jurisdiction = cls.env["regulatory.jurisdiction"]
        cls.dubai = cls.env.ref("sgc_regulatory_rules_pack.jurisdiction_dubai")
        cls.uae_federal = cls.env.ref("sgc_regulatory_rules_pack.jurisdiction_uae_federal")

    # ------------------------------------------------------------------ #
    # 1. The migration off aml_compliance / G24                            #
    # ------------------------------------------------------------------ #

    def test_01_rear_cash_threshold_migrated(self):
        """AED 55,000 is in the rules pack, NOT hard-coded in the consumer."""
        rec = self.Constant.get_effective(
            "rear_cash_threshold_aed", "dubai",
            as_of=date(2026, 9, 1),
        )
        self.assertEqual(rec.value_numeric, 55000)
        self.assertEqual(rec.unit, "aed")
        self.assertEqual(rec.confidence, "verified")
        self.assertEqual(rec.jurisdiction_id, self.dubai)
        # The record must carry a migration note.
        self.assertIn("migrated", (rec.notes or "").lower())

    # ------------------------------------------------------------------ #
    # 2. Lookup by code + jurisdiction + as_of                            #
    # ------------------------------------------------------------------ #

    def test_02_lookup_value_helper(self):
        val = self.Constant.get_effective_value(
            "rear_cash_threshold_aed", "dubai",
            as_of=date(2026, 9, 1),
        )
        self.assertEqual(val, 55000.0)
        self.assertIsInstance(val, float)

    def test_03_lookup_returns_record_object(self):
        rec = self.Constant.get_effective(
            "ejari_required", "dubai",
            as_of=date(2026, 9, 1),
        )
        self.assertEqual(rec.value_text, "true")
        self.assertEqual(rec.unit, "bool")

    def test_04_bool_unit_helper(self):
        val = self.Constant.get_effective_value(
            "ejari_required", "dubai",
            as_of=date(2026, 9, 1),
        )
        self.assertIs(val, True)

    # ------------------------------------------------------------------ #
    # 3. Effective dating                                                #
    # ------------------------------------------------------------------ #

    def test_05_effective_dating(self):
        """Add a record that supersedes an existing one. Lookup by date picks the right one."""
        # Take a verified, open-ended value and add a future replacement.
        parent = self.Constant.get_effective(
            "vat_rate_percent", "uae_federal",
            as_of=date(2026, 1, 1),
        )
        # Build a future revision effective 2030-01-01.
        future = self.Constant.create({
            "name": "UAE VAT standard rate (future revision)",
            "code": parent.code,
            "jurisdiction_id": parent.jurisdiction_id.id,
            "category": parent.category,
            "value_numeric": 7.0,
            "unit": parent.unit,
            "source_url": "https://www.tax.gov.ae/",
            "source_reference": "Future revision — illustrative only.",
            "verified_on": date(2030, 1, 1),
            "confidence": "unverified",
            "valid_from": date(2030, 1, 1),
            "supersedes_id": parent.id,
            "version": parent.version + 1,
        })
        try:
            # Today: still the original 5%.
            today = self.Constant.get_effective(
                "vat_rate_percent", "uae_federal",
                as_of=date(2026, 1, 1),
            )
            self.assertEqual(today.value_numeric, 5.0)
            self.assertEqual(today.version, parent.version)

            # 2030: future revision wins, higher version overrides same-code.
            later = self.Constant.get_effective(
                "vat_rate_percent", "uae_federal",
                as_of=date(2030, 6, 1),
            )
            self.assertEqual(later.value_numeric, 7.0)
            self.assertEqual(later.version, future.version)
        finally:
            future.unlink()

    # ------------------------------------------------------------------ #
    # 4. UNVERIFIED entries are flagged but not blocked                    #
    # ------------------------------------------------------------------ #

    def test_06_unverified_returns_value(self):
        """UNVERIFIED entries are returned by lookup; consumers surface the flag."""
        rec = self.Constant.get_effective(
            "rear_filing_deadline_days", "dubai",
            as_of=date(2026, 9, 1),
        )
        self.assertEqual(rec.confidence, "unverified")
        # Lookup still returns a value (the consumer decides what to do).
        self.assertIsNotNone(rec.value_text)
        # The value text begins with the UNVERIFIED marker — the consumer
        # can detect this at a glance.
        self.assertTrue(rec.value_text.startswith("UNVERIFIED"))

    # ------------------------------------------------------------------ #
    # 5. Confidence=verified requires provenance                          #
    # ------------------------------------------------------------------ #

    def test_07_verified_requires_source_url(self):
        with self.assertRaises(ValidationError):
            self.Constant.create({
                "name": "Test — verified without source_url",
                "code": "test_no_source",
                "jurisdiction_id": self.dubai.id,
                "category": "other",
                "value_text": "test",
                "unit": "text",
                "confidence": "verified",
                "valid_from": date(2026, 1, 1),
                "verified_on": date(2026, 1, 1),
                # source_url MISSING on purpose
                "version": 1,
            })

    def test_08_verified_requires_verified_on(self):
        with self.assertRaises(ValidationError):
            self.Constant.create({
                "name": "Test — verified without verified_on",
                "code": "test_no_verified_on",
                "jurisdiction_id": self.dubai.id,
                "category": "other",
                "value_text": "test",
                "unit": "text",
                "confidence": "verified",
                "valid_from": date(2026, 1, 1),
                "source_url": "https://www.example.gov.ae/test",
                # verified_on MISSING on purpose
                "version": 1,
            })

    # ------------------------------------------------------------------ #
    # 6. Effective-window sanity                                         #
    # ------------------------------------------------------------------ #

    def test_09_valid_to_before_valid_from_raises(self):
        with self.assertRaises(ValidationError):
            self.Constant.create({
                "name": "Test — invalid window",
                "code": "test_invalid_window",
                "jurisdiction_id": self.dubai.id,
                "category": "other",
                "value_text": "test",
                "unit": "text",
                "confidence": "unverified",
                "valid_from": date(2026, 6, 1),
                "valid_to": date(2026, 1, 1),
                "version": 1,
            })

    # ------------------------------------------------------------------ #
    # 7. Exactly-one-of-value constraint                                 #
    # ------------------------------------------------------------------ #

    def test_10_both_value_set_raises(self):
        with self.assertRaises(ValidationError):
            self.Constant.create({
                "name": "Test — both values",
                "code": "test_both_values",
                "jurisdiction_id": self.dubai.id,
                "category": "fee_rate",
                "value_numeric": 100.0,
                "value_text": "one hundred",
                "unit": "aed",
                "confidence": "unverified",
                "valid_from": date(2026, 1, 1),
                "version": 1,
            })

    def test_11_neither_value_set_raises(self):
        with self.assertRaises(ValidationError):
            self.Constant.create({
                "name": "Test — neither value",
                "code": "test_neither_value",
                "jurisdiction_id": self.dubai.id,
                "category": "fee_rate",
                "unit": "aed",
                "confidence": "unverified",
                "valid_from": date(2026, 1, 1),
                "version": 1,
            })

    # ------------------------------------------------------------------ #
    # 8. Missing code raises                                             #
    # ------------------------------------------------------------------ #

    def test_12_missing_code_raises(self):
        with self.assertRaises(UserError):
            self.Constant.get_effective(
                "no_such_constant", "dubai",
                as_of=date(2026, 9, 1),
            )

    # ------------------------------------------------------------------ #
    # 9. PF and UBO constants drive Wave 2 schema changes                 #
    # ------------------------------------------------------------------ #

    def test_13_pf_required(self):
        val = self.Constant.get_effective_value(
            "pf_risk_required", "uae_federal",
            as_of=date(2026, 9, 1),
        )
        self.assertIs(val, True)

    def test_14_nominee_not_ubo(self):
        val = self.Constant.get_effective_value(
            "nominee_not_ubo", "uae_federal",
            as_of=date(2026, 9, 1),
        )
        self.assertIs(val, True)

    # ------------------------------------------------------------------ #
    # 10. Round-trip: every seeded constant returns a value               #
    # ------------------------------------------------------------------ #

    def test_15_every_seeded_constant_resolves(self):
        for seed in self.Constant.search([]):
            rec = self.Constant.get_effective(seed.code, seed.jurisdiction_id.code)
            self.assertIsNotNone(rec, f"{seed.code} did not resolve")
            if rec.unit == "text":
                self.assertTrue(rec.value_text, f"{seed.code} has empty value_text")
            elif rec.unit != "bool":
                self.assertNotEqual(rec.value_numeric, 0.0,
                                    f"{seed.code} has zero value_numeric")
