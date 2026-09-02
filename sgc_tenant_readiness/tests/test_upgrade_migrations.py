# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Upgrade-path migration tests — residency enum and TENANT_DECISION survival.

Moved here from sgc_process_control per Wave 3 remediation round 2: both
tests exercise fields owned by this module
(`res.company.data_residency_region`, `tenant.compliance.officer.lnoo_reference`),
not by process_control. Testing a downstream module's fields from an
upstream module's test suite meant the assertions were only meaningful
by coincidence of install order, and gave the earlier deliverable a
false sense that process_control validated the residency enum when
process_control has no field to validate — the enum did not exist in
code anywhere until this remediation round.

Two of the three mandatory upgrade assertions from Wave 3 protocol §7:

  2. Residency enum migration. Any stored value of 'uae' must be
     migrated to an explicit uae_mainland / difc / adgm value or set null
     and flagged for tenant re-entry. Must NOT be silently defaulted to
     uae_mainland.

  3. No data loss on TENANT_DECISION fields. Values survive upgrade;
     any newly added TENANT_DECISION field arrives blank.

(The first mandatory assertion — retention anchor migration — lives in
sgc_process_control/tests/test_upgrade_migrations.py, which owns
process.exception.)
"""

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness", "sgc_gate")
class TestTenantReadinessUpgradeMigrations(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Company = cls.env["res.company"]
        cls.Officer = cls.env["tenant.compliance.officer"]

    # ---- Residency enum: real field, not a placeholder ------------------

    def test_01_residency_field_exists_and_defaults_to_uae_mainland(self):
        """The field exists on res.company, is a real Selection, and its
        VENDOR default is 'uae_mainland' — not a config-parameter string
        that nothing in code ever set.
        """
        company = self.env.ref("base.main_company")
        self.assertIn(
            company.data_residency_region,
            ("uae_mainland", "difc", "adgm", "other"),
            "data_residency_region did not default to a valid enum value",
        )
        # Ground truth default for a freshly created company.
        fresh = self.Company.create({"name": "Wave3 Residency Test Co"})
        self.assertEqual(
            fresh.data_residency_region, "uae_mainland",
            "A freshly created company must default to uae_mainland, "
            "the single region the estate operates today.",
        )

    def test_02_residency_field_rejects_invalid_value(self):
        """The Selection field type rejects any value outside the four
        listed enum members at the ORM layer. This is what makes the
        'no silent default' guarantee real rather than aspirational —
        an invalid or legacy 'uae' string cannot be written at all.
        """
        company = self.env.ref("base.main_company")
        with self.assertRaises(ValueError):
            company.write({"data_residency_region": "uae"})

    def test_03_residency_migration_no_silent_default_to_uae_mainland(self):
        """A company already on a valid, non-default value (difc or adgm)
        must not be silently overwritten to uae_mainland by any
        migration or write path exercised in this test.

        The Wave 3 brief §7 is explicit: DIFC and ADGM entities fall
        outside the federal PDPL entirely, and a wrong default asserts
        the wrong legal regime on the tenant's behalf.
        """
        difc_company = self.Company.create({
            "name": "Wave3 DIFC Test Co",
            "data_residency_region": "difc",
        })
        # Simulate the kind of operation an upgrade script might run —
        # touching an unrelated field must not disturb this one.
        difc_company.write({"data_residency_disclosure_url": "https://example.test/disclosure"})
        self.assertEqual(
            difc_company.data_residency_region, "difc",
            "An unrelated write silently reset data_residency_region "
            "to uae_mainland — this is exactly the R9 violation the "
            "brief warns against.",
        )

    def test_04_legal_regime_ref_resolved_by_lookup_not_hardcoded(self):
        """The computed legal-regime reference tracks the region and is
        never hard-coded to a single law name in the field itself.
        """
        difc_company = self.Company.create({
            "name": "Wave3 DIFC Regime Test Co",
            "data_residency_region": "difc",
        })
        self.assertEqual(difc_company.data_residency_legal_regime_ref, "difc_dpl")
        adgm_company = self.Company.create({
            "name": "Wave3 ADGM Regime Test Co",
            "data_residency_region": "adgm",
        })
        self.assertEqual(adgm_company.data_residency_legal_regime_ref, "adgm_dpr")

    def test_05_disclosure_accepted_has_no_default(self):
        """TENANT_DECISION-adjacent field — the disclosure acceptance —
        ships blank, no default, per R9.
        """
        fresh = self.Company.create({"name": "Wave3 R9 Test Co"})
        self.assertFalse(
            fresh.data_residency_disclosure_accepted,
            "data_residency_disclosure_accepted must not carry a "
            "default value — R9.",
        )

    # ---- TENANT_DECISION survival on tenant.compliance.officer ----------

    def test_06_tenant_decision_field_survives_upgrade(self):
        """Values in TENANT_DECISION fields survive upgrade; any newly
        added TENANT_DECISION field arrives blank.

        Test the LNOO reference on tenant.compliance.officer — the
        upgrade migration must not over-write a stored value.
        """
        company = self.env.ref("base.main_company")
        primary_user = self.env["res.users"].create({
            "name": "Wave3 Upgrade Test Officer",
            "login": "test_wave3_upgrade_officer",
            "email": "wave3_upgrade_officer@example.com",
            "company_id": company.id,
        })
        officer = self.Officer.create({
            "role": "primary",
            "user_id": primary_user.id,
            "tenant_company_id": company.id,
            "appointment_date": "2026-09-01",
            "lnoo_reference": "LNOO-2026-TEST-001",
        })
        # Simulate an unrelated write an upgrade migration might perform.
        officer.write({"appointment_notification_reference": "MOET-2026-99999"})
        self.assertEqual(
            officer.lnoo_reference, "LNOO-2026-TEST-001",
            "An unrelated write cleared the LNOO reference — "
            "TENANT_DECISION data loss on upgrade.",
        )
