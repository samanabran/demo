# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Meta-test: discovered test class count must equal hard-coded expected.

Counting convention (fixed across all three modules per Wave 3
remediation round 2): count EVERY unittest.TestCase subclass, INCLUDING
this meta-test class itself.
"""

import inspect
import unittest

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness")
class TestCountMeta(TransactionCase):
    # Ground truth as of this commit: TestCountMeta (this class),
    # TestTenantReadiness, TestMlroSegregation, TestFreshTenantBlocking,
    # TestFreshTenantBlockingConfigured, TestR8MechanicalScan,
    # TestIsolationDirectSearch, TestTenantReadinessUpgradeMigrations.
    EXPECTED_CLASS_COUNT = 8

    def test_count_classes_in_module(self):
        from sgc_tenant_readiness import tests as test_pkg

        discovered = []
        for _, obj in inspect.getmembers(test_pkg, inspect.isclass):
            if obj.__module__.startswith("sgc_tenant_readiness.tests"):
                if issubclass(obj, unittest.TestCase):
                    discovered.append(obj.__name__)
        self.assertEqual(
            len(discovered), self.EXPECTED_CLASS_COUNT,
            f"Expected {self.EXPECTED_CLASS_COUNT} test class(es) "
            f"(including TestCountMeta itself) in sgc_tenant_readiness, "
            f"found {len(discovered)}: {sorted(discovered)}",
        )
