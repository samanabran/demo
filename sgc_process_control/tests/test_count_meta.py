# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Meta-test: discovered test class count must equal hard-coded expected.

Also asserts the exit-gate class exists by the name the Wave 3 install
protocol command 6.4 targets, and contains exactly seven test methods.
A class name mismatch between code and the protocol command would
silently match nothing — exit zero, no coverage, false green.

Counting convention (fixed across all three modules per Wave 3
remediation round 2): count EVERY unittest.TestCase subclass, INCLUDING
this meta-test class itself. `TestScreeningConsumer` in test_exit_gate.py
is a models.AbstractModel, not a TestCase, and is correctly excluded by
the issubclass check, not by a name filter.
"""

import inspect
import unittest

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_process_control")
class TestCountMeta(TransactionCase):
    # Ground truth as of this commit: TestCountMeta (this class),
    # TestExitGate, TestProcessControl, TestUpgradeMigrations.
    EXPECTED_CLASS_COUNT = 4
    EXPECTED_EXIT_GATE_TEST_COUNT = 7
    EXPECTED_EXIT_GATE_CLASS_NAME = "TestExitGate"

    def test_count_classes_in_module(self):
        from sgc_process_control import tests as test_pkg

        discovered = []
        for _, obj in inspect.getmembers(test_pkg, inspect.isclass):
            if obj.__module__.startswith("sgc_process_control.tests"):
                if issubclass(obj, unittest.TestCase):
                    discovered.append(obj.__name__)
        self.assertEqual(
            len(discovered), self.EXPECTED_CLASS_COUNT,
            f"Expected {self.EXPECTED_CLASS_COUNT} test class(es) "
            f"(including TestCountMeta itself) in sgc_process_control, "
            f"found {len(discovered)}: {sorted(discovered)}",
        )

    def test_exit_gate_class_exists_with_expected_name(self):
        """The Wave 3 install protocol command 6.4 is:
            --test-tags '/sgc_process_control:TestExitGate'

        If the class is renamed, the command matches nothing, exits
        zero, and the run is recorded green with zero exit-gate coverage.
        This assertion catches that drift.
        """
        from sgc_process_control import tests as test_pkg

        cls = None
        for _, obj in inspect.getmembers(test_pkg, inspect.isclass):
            if obj.__name__ == self.EXPECTED_EXIT_GATE_CLASS_NAME:
                if issubclass(obj, unittest.TestCase):
                    cls = obj
                    break
        self.assertIsNotNone(
            cls,
            f"Test class {self.EXPECTED_EXIT_GATE_CLASS_NAME!r} not found. "
            f"Wave 3 install protocol command 6.4 would match nothing. "
            f"Either restore the class or update the protocol command.",
        )

    def test_exit_gate_class_has_expected_test_count(self):
        """Exactly seven test methods. Any drift is a regression — the
        brief §6.4 says the exit-gate must show 7 cases, not 5.
        """
        from sgc_process_control import tests as test_pkg

        cls = None
        for _, obj in inspect.getmembers(test_pkg, inspect.isclass):
            if obj.__name__ == self.EXPECTED_EXIT_GATE_CLASS_NAME:
                cls = obj
                break
        self.assertIsNotNone(cls, "Exit-gate class not found.")
        methods = [
            name for name, _ in inspect.getmembers(cls, inspect.isfunction)
            if name.startswith("test_")
        ]
        self.assertEqual(
            len(methods), self.EXPECTED_EXIT_GATE_TEST_COUNT,
            f"Expected {self.EXPECTED_EXIT_GATE_TEST_COUNT} test methods "
            f"in {self.EXPECTED_EXIT_GATE_CLASS_NAME}, found {len(methods)}: "
            f"{methods}",
        )
