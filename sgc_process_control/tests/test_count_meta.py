# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Meta-test: discovered test class count must equal hard-coded expected."""

import inspect
import unittest

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_process_control")
class TestCountMeta(TransactionCase):
    EXPECTED_CLASS_COUNT = 3

    def test_count_classes_in_module(self):
        from sgc_process_control import tests as test_pkg

        discovered = []
        for _, obj in inspect.getmembers(test_pkg, inspect.isclass):
            if obj.__module__.startswith("sgc_process_control.tests"):
                if issubclass(obj, unittest.TestCase):
                    discovered.append(obj.__name__)
        real = [c for c in discovered if c != "TestCountMeta"]
        self.assertEqual(
            len(real), self.EXPECTED_CLASS_COUNT,
            f"Expected {self.EXPECTED_CLASS_COUNT} test class(es) in "
            f"sgc_process_control, found {len(real)}: {real}",
        )
