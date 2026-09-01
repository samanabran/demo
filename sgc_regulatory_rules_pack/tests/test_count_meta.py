# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
"""Meta-test: asserts the discovered test class count equals a hard-coded expected count.

The only defence against a test file that stops running because someone
forgot an import line. This has caught this exact failure in most estates.
"""

import unittest

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_regulatory")
class TestCountMeta(TransactionCase):
    EXPECTED_CLASS_COUNT = 2

    def test_count_classes_in_module(self):
        """The test loader must find this exact number of test classes in
        the rules pack's tests/ tree.

        Hard-code the expected count. If a class is added, update this
        number in the same commit. If a class is silently dropped
        (broken import), this test fails and the SHIP SET is BLOCKed.
        """
        import inspect
        from sgc_regulatory_rules_pack import tests as test_pkg

        discovered = []
        for _, obj in inspect.getmembers(test_pkg, inspect.isclass):
            if obj.__module__.startswith("sgc_regulatory_rules_pack.tests"):
                if issubclass(obj, unittest.TestCase):
                    discovered.append(obj.__name__)

        # The meta-test class itself counts. Subtract it.
        real = [c for c in discovered if c != "TestCountMeta"]
        self.assertEqual(
            len(real), self.EXPECTED_CLASS_COUNT,
            f"Expected {self.EXPECTED_CLASS_COUNT} test class(es) in "
            f"sgc_regulatory_rules_pack, found {len(real)}: {real}",
        )
