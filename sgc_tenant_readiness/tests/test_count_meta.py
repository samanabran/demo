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


def _discover_test_classes(test_pkg):
    """Classes live on the submodules ``tests/__init__.py`` imports, not
    directly on the ``tests`` package object — ``inspect.getmembers`` on
    the package alone finds nothing.
    """
    discovered = []
    for _, submodule in inspect.getmembers(test_pkg, inspect.ismodule):
        for _, obj in inspect.getmembers(submodule, inspect.isclass):
            discovered.append(obj)
    return discovered


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness")
class TestCountMeta(TransactionCase):
    # Ground truth as of this commit: TestCountMeta (this class),
    # TestTenantReadiness, TestMlroSegregation, TestFreshTenantBlocking,
    # TestFreshTenantBlockingConfigured, TestR8MechanicalScan,
    # TestIsolationDirectSearch, TestTenantReadinessUpgradeMigrations.
    EXPECTED_CLASS_COUNT = 8

    def test_count_classes_in_module(self):
        from odoo.addons.sgc_tenant_readiness import tests as test_pkg

        discovered = [
            obj.__name__ for obj in _discover_test_classes(test_pkg)
            if obj.__module__.startswith("odoo.addons.sgc_tenant_readiness.tests")
            and issubclass(obj, unittest.TestCase)
        ]
        self.assertEqual(
            len(discovered), self.EXPECTED_CLASS_COUNT,
            f"Expected {self.EXPECTED_CLASS_COUNT} test class(es) "
            f"(including TestCountMeta itself) in sgc_tenant_readiness, "
            f"found {len(discovered)}: {sorted(discovered)}",
        )
