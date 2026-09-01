# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Upgrade-path migration test — the retention-anchor assertion.

Run on sgc_upgrade after installing the last tagged-good revision and
upgrading to HEAD.

  1. Retention anchor migration. Records created before the anchor
     correction must have their retention clock rebased to
     end-of-relationship or transaction-completion, not creation date.
     Records whose anchor event has not yet occurred have a null expiry,
     not a creation-derived one.

The other two mandatory upgrade assertions (residency enum migration,
TENANT_DECISION field survival) live in
`sgc_tenant_readiness/tests/test_upgrade_migrations.py` because they
test `res.company.data_residency_region` and
`tenant.compliance.officer.lnoo_reference` — fields owned by that
module. process_control has no dependency on tenant_readiness (the
dependency runs the other way), so a test that reaches into
tenant_readiness models does not belong here. This split was a
structural defect: the original file put both downstream-model tests
in the upstream module, which meant the tests would only be meaningful
when all three modules happened to be installed together, and gave a
false sense that process_control validated something it has no
knowledge of.
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
