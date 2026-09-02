# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
"""Meta-test: asserts the discovered test class count equals a hard-coded expected count.

The only defence against a test file that stops running because someone
forgot an import line. This has caught this exact failure in most estates.

Counting convention (fixed across all three modules per Wave 3 remediation
round 2): count EVERY unittest.TestCase subclass discovered under this
module's tests/ package, INCLUDING the meta-test class itself. Do not
subtract the meta-test — that produced three different, silently
inconsistent counting conventions across the three modules and was itself
a false-green risk in the deliverable that reviews this test suite.
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


@tagged("post_install", "-at_install", "sgc_install", "sgc_regulatory")
class TestCountMeta(TransactionCase):
    # Ground truth as of this commit: TestCountMeta (this class),
    # TestRegulatoryRulesPack, TestRegulatoryIntegrity, TestSchemaDrift.
    EXPECTED_CLASS_COUNT = 4

    def test_count_classes_in_module(self):
        """The test loader must find this exact number of test classes in
        the rules pack's tests/ tree, counting every TestCase subclass
        including this one.

        Hard-code the expected count. If a class is added, update this
        number in the same commit. If a class is silently dropped
        (broken import), this test fails and the SHIP SET is BLOCKed.
        """
        from odoo.addons.sgc_regulatory_rules_pack import tests as test_pkg

        discovered = [
            obj.__name__ for obj in _discover_test_classes(test_pkg)
            if obj.__module__.startswith("odoo.addons.sgc_regulatory_rules_pack.tests")
            and issubclass(obj, unittest.TestCase)
        ]
        self.assertEqual(
            len(discovered), self.EXPECTED_CLASS_COUNT,
            f"Expected {self.EXPECTED_CLASS_COUNT} test class(es) "
            f"(including TestCountMeta itself) in "
            f"sgc_regulatory_rules_pack, found {len(discovered)}: "
            f"{sorted(discovered)}",
        )
