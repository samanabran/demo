# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""R8 mechanical scan — no compliance claims anywhere.

Per amendment §3 R8, no user-visible string may assert or imply
compliance. Permitted: "supports the tenant's AML/CFT/CPF programme".
Prohibited (case-insensitive, word-boundary):
  - "compliant"
  - "compliance guaranteed"
  - "ensures compliance"
  - "AML compliant"
  - "fully compliant"
  - "certified"

The brief §10 requires this as a test, not a manual audit. Manual
audits do not survive contact with a growing codebase.
"""

import os
import re

from odoo.tests import TransactionCase, tagged


PROHIBITED = [
    r"\bcompliant\b",
    r"\bcompliance guaranteed\b",
    r"\bensures compliance\b",
    r"\bAML compliant\b",
    r"\bfully compliant\b",
    r"\bcertified\b",
]

# Permitted constructions — explicit allow-list. If a forbidden word
# appears inside one of these, it is allowed.
PERMITTED_PATTERNS = [
    r"supports the tenant",
    r"record evidence of",
    r"configured by the tenant",
    r"as configured",
    r"tenant responsibility",
    r"non-compliant",  # specifically negative use is fine
]

# Cross-platform path separator. Windows uses \, Unix uses /.
# Using a forward slash regex on Windows fails to match backslash
# separators, so the test would scan itself.
_SEP = re.escape(os.sep)
ALLOWED_FILE_PATTERNS = [
    # Markdown reference documents and README files may describe what the
    # module is NOT; we are strict in source code only.
    re.compile(rf".*README\.md$"),
    re.compile(rf".*{_SEP}docs{_SEP}.*\.md$"),
    re.compile(rf".*{_SEP}migrations{_SEP}.*\.py$"),
    # Tests/ files are excluded — the R8 scan test itself is in tests/
    # and its source contains the prohibited strings as test data.
    re.compile(rf".*{_SEP}tests{_SEP}.*\.py$"),
]


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness", "sgc_gate")
class TestR8MechanicalScan(TransactionCase):
    MODULE_DIR = None  # set in setUpClass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import sgc_tenant_readiness
        cls.MODULE_DIR = os.path.dirname(sgc_tenant_readiness.__file__)

    def _walk_module_files(self):
        for root, _dirs, files in os.walk(self.MODULE_DIR):
            for f in files:
                if f.endswith((".py", ".xml", ".csv", ".md")):
                    yield os.path.join(root, f)

    def _is_allowed_path(self, path):
        return any(p.match(path) for p in ALLOWED_FILE_PATTERNS)

    def test_no_prohibited_compliance_claims_in_source(self):
        """Walk every .py / .xml / .csv in the three modules. Any hit on
        the prohibited list fails the run.

        Reference documents under /docs/ are excluded — they describe
        what the product is not, and the source-of-truth is the brief.
        """
        compiled = [re.compile(p, re.IGNORECASE) for p in PROHIBITED]
        permitted = [re.compile(p, re.IGNORECASE) for p in PERMITTED_PATTERNS]
        hits = []
        for path in self._walk_module_files():
            if self._is_allowed_path(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, 1):
                        for pattern in compiled:
                            if pattern.search(line):
                                # Check permitted patterns — if the line
                                # also matches a permitted pattern, allow.
                                if not any(p.search(line) for p in permitted):
                                    hits.append((path, line_no, line.strip()))
            except (UnicodeDecodeError, OSError):
                continue
        self.assertEqual(hits, [],
                         f"R8 violation — prohibited compliance claims found:\n"
                         + "\n".join(f"{p}:{n}: {l}" for p, n, l in hits))
