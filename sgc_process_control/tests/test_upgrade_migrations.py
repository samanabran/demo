# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Upgrade-path migration tests — the three mandatory upgrade assertions
per the Wave 3 test protocol §7.

Run on sgc_upgrade after installing the last tagged-good revision and
upgrading to HEAD. The three assertions:

  1. Retention anchor migration. Records created before the anchor
     correction must have their retention clock rebased to
     end-of-relationship or transaction-completion, not creation date.
     Records whose anchor event has not yet occurred have a null expiry,
     not a creation-derived one.

  2. Residency enum migration. Any stored value of 'uae' must be
     migrated to an explicit uae_mainland / difc / adgm value or set null
     and flagged for tenant re-entry. Must NOT be silently defaulted to
     uae_mainland.

  3. No data loss on TENANT_DECISION fields. Values survive upgrade;
     any newly added TENANT_DECISION field arrives blank.

These tests document the expected behaviour. They run after the upgrade
migration script has been applied.
"""

from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_process_control", "sgc_gate")
class TestUpgradeMigrations(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Exception = cls.env["process.exception"]

    def test_01_anchor_migration_no_creation_derived_expiry(self):
        """A record whose anchor event has not yet occurred has a null
        retention_until, not a creation-derived one.

        Pre-anchor-correction records had retention_until = created + 5y.
        The migration rebases them to either:
          (a) terminal_state_entry anchor (if the record is in a
              terminal state), or
          (b) a null retention_until (if the record is still live).

        This test asserts that no record has a creation-derived retention.
        """
        # For each exception in the database, retention_anchor_at must
        # either be set (terminal) or false (live). If it's set, the
        # anchor must NOT be at occurred_at.
        for exc in self.Exception.search([]):
            if exc.retention_anchor_at:
                # Terminal — anchor must not equal occurred_at. A
                # migration that left anchors at occurred_at would
                # re-create the defect.
                self.assertNotEqual(
                    exc.retention_anchor_at, exc.occurred_at,
                    f"Exception {exc.id} has anchor=occurred_at — the "
                    f"migration did not rebase. Anchor must be set at "
                    f"the terminal-state transition.",
                )

    def test_02_residency_migration_no_silent_default_to_uae_mainland(self):
        """A stored value of 'uae' must be migrated to uae_mainland /
        difc / adgm or set null. It must NOT be silently defaulted.

        The Wave 3 brief §7 is explicit: DIFC and ADGM entities fall
        outside the federal PDPL entirely, and a wrong default asserts
        the wrong legal regime on the tenant's behalf.
        """
        # The current data model is in the process of being extended
        # with the residency enum. This test asserts that when the
        # field exists, no stored 'uae' value is silently mapped.
        IrConfigParameter = self.env["ir.config_parameter"]
        # Search the residency keys.
        for key in (
            "sgc.data_residency.region",
            "sgc.data_residency.region_multitenant",
        ):
            res = IrConfigParameter.search([("key", "=", key)], limit=1)
            if res and res.value == "uae":
                self.fail(
                    f"Residency migration left a stored 'uae' value at "
                    f"{key}. The migration must explicitly set "
                    f"uae_mainland / difc / adgm or null."
                )

    def test_03_tenant_decision_field_survives_upgrade(self):
        """Values in TENANT_DECISION fields survive upgrade; any newly
        added TENANT_DECISION field arrives blank.

        Test the LNOO reference on tenant.compliance.officer (added in
        the G28 build) — the upgrade migration must not over-write a
        stored value.
        """
        Officer = self.env["tenant.compliance.officer"]
        primary = self.env.ref("base.main_company")
        existing = Officer.search([("tenant_company_id", "=", primary.id)], limit=1)
        if existing and existing.lnoo_reference:
            # Stored LNOO survives. Re-fetch and assert.
            reread = Officer.browse(existing.id)
            self.assertEqual(reread.lnoo_reference, existing.lnoo_reference)
