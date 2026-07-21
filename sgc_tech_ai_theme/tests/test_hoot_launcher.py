# -*- coding: utf-8 -*-
# Part of SGC TECH AI. See LICENSE file for full copyright and licensing details.
# Copyright (c) 2026 SGC TECH AI (https://sgctech.ai)

"""
Live hoot test runner for the SGC Enterprise Application Launcher.

This is a thin wrapper around Odoo 19's HOOTCommon HttpCase infrastructure
(addons/web/tests/test_js.py) that invokes the headless browser_js runner
scoped to static/tests/launcher.test.js. Without this wrapper, the file is
"unverified against live hoot" (US-014's disclosed gap from the prior
session): there's no odoo-bin entry point that points at a single addon's
test file by default.

Uses the same browser_js(... success_signal="[HOOT] Test suite succeeded",
error_checker=unit_test_error_checker) pattern as web.tests.test_js.WebSuite
so Odoo's own internal headless Chrome does the actual test execution —
no human-in-the-loop browser login required.
"""
from odoo.addons.web.tests.test_js import HOOTCommon, unit_test_error_checker
from odoo.tests import tagged

# Decorator reference: `@odoo.tests.no_retry` needs the module imported
# so the name `odoo` is bound in this file's globals. Without this line
# the import succeeds but the decorator reference raises NameError
# during class definition (caught live 2026-07-21: the test file was
# silently excluded from the runner's discovered-tests set).
import odoo.tests


@tagged('post_install', '-at_install')
class TestSgcLauncherHoot(HOOTCommon):
    """Run the launcher's hoot suite headless and assert it succeeds.

    The URL filter `/SGC Launcher/` matches the `describe('SGC Launcher', ...)`
    block at the top of static/tests/launcher.test.js. The 5 nested tests
    (US-014-A through E) are all children of that suite.
    """

    @odoo.tests.no_retry
    def test_launcher_hoot(self):
        self.browser_js(
            '/web/tests?headless&loglevel=2&preset=desktop&timeout=15000'
            '&filter=/SGC Launcher/' + self.hoot_filters,
            "",
            "",
            login='admin',
            timeout=300,
            success_signal='[HOOT] Test suite succeeded',
            error_checker=unit_test_error_checker,
        )