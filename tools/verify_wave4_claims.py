#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify WAVE_4_INSTALL_REGRESSION_RESULT.md's factual claims against disk.

Companion to ``verify_wave3_claims.py`` for the Wave 4 modules
(``kyc_management`` and ``aml_compliance``). Encodes the
module-specific expected-count manifest from
``docs/WAVE_4_INSTALL_REGRESSION_RESULT.md`` §10 as a hard gate.

Usage:
    python tools/verify_wave4_claims.py [--json]

Exit code 0 if every check is internally consistent and every
manifest-encoded assertion matches the ground truth. Exit code 1
on any manifest violation or stale --test-tags reference. Exit code
2 if the Rule 1 sync check returns MISMATCH (only when all three
endpoints are reachable; soft on offline runs).
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = ["kyc_management", "aml_compliance"]

# Module-specific expected-count manifest. Each entry mirrors §10 of
# the Wave 4 result document.
#
# IMPORTANT — Odoo 19 selector semantics: an explicit selector like
# ``/aml_compliance`` matches ANY class carrying the ``aml_compliance``
# tag, regardless of whether the class is also tagged
# ``post_install`` or excluded with ``-at_install``. The
# ``-at_install`` exclusion is honoured only when no explicit include
# selector is given. As a result, the §6.2 selector includes the
# TestExitGate and TestPostInstall classes too, not just the original
# per-feature tests. The §6.2 expected counts below therefore reflect
# the sum of original + TestExitGate + TestPostInstall methods.
MANIFEST = {
    "kyc_management": {
        # 3 (TestKycOfficerRouting) + 5 (TestExitGate) + 2 (TestPostInstall)
        "section_62_expected": 10,
        # post_install selector: TestKycOfficerRouting (3, tagged
        # post_install) + TestPostInstall (2) = 5.
        "section_63_expected": 5,
        "section_63_post_install_class": "TestPostInstall",
        # /kyc_management:TestExitGate: only TestExitGate
        "section_64_class": "TestExitGate",
        "section_64_min_methods": 5,
        "section_64_expected": 5,
    },
    "aml_compliance": {
        # 14 (4 original classes) + 6 (TestExitGate) + 2 (TestPostInstall)
        "section_62_expected": 22,
        # post_install selector: only TestPostInstall (none of the
        # 4 original classes are tagged post_install).
        "section_63_expected": 2,
        "section_63_post_install_class": "TestPostInstall",
        # /aml_compliance:TestExitGate: only TestExitGate
        "section_64_class": "TestExitGate",
        "section_64_min_methods": 6,
        "section_64_expected": 6,
    },
}

# Re-use the Wave 3 verifier's Rule 1 helper by exec'ing its module
# source. Avoids two divergent implementations of the same logic.
_W3_PATH = os.path.join(ROOT, "tools", "verify_wave3_claims.py")


def _load_w3_module():
    """Import verify_wave3_claims as a module via importlib."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("verify_wave3_claims", _W3_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {_W3_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def module_path(module):
    return os.path.join(ROOT, module)


def _parse_test_file(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return ast.parse(fh.read())
    except (SyntaxError, OSError, UnicodeDecodeError) as e:
        print(f"WARN: could not parse {path}: {e}", file=sys.stderr)
        return None


def list_test_classes(module):
    """AST-based: every TestCase/HttpCase subclass under module/tests/.
    Returns a list of (class_name, file_path, node) sorted by class name."""
    tests_dir = os.path.join(module_path(module), "tests")
    out = []
    if not os.path.isdir(tests_dir):
        return out
    for root, dirs, files in os.walk(tests_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            tree = _parse_test_file(path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                bases = [
                    b.id if isinstance(b, ast.Name)
                    else (b.attr if isinstance(b, ast.Attribute) else "?")
                    for b in node.bases
                ]
                if "TransactionCase" in bases or "HttpCase" in bases:
                    out.append((node.name, path, node))
    return sorted(out, key=lambda x: x[0])


def _has_post_install_tag(class_node):
    """True if the class has ``@tagged('post_install', ...)`` decorator."""
    for dec in class_node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        # The first positional arg of tagged('post_install', ...) is the
        # tag string. Look for the literal 'post_install'.
        for arg in dec.args:
            if isinstance(arg, ast.Constant) and arg.value == "post_install":
                return True
            # Older AST: ast.Str
            if hasattr(ast, "Str") and isinstance(arg, ast.Str) and arg.s == "post_install":
                return True
    return False


def find_class_methods(module, class_name):
    """Return sorted list of test_* method names on the named class."""
    for name, path, node in list_test_classes(module):
        if name != class_name:
            continue
        methods = [
            n.name for n in node.body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        return path, sorted(methods)
    return None, []


def section_62_method_count(module):
    """Sum of test_* method counts across EVERY TestCase subclass in
    ``module``. The Odoo 19 selector ``/<module>`` matches every
    class carrying the module tag, including TestExitGate (no tag)
    and TestPostInstall (tagged ``post_install``). The §6.2 expected
    count therefore equals the sum across all four (or three)
    classes. This function counts them all."""
    total = 0
    per_class = {}
    for name, _path, node in list_test_classes(module):
        methods = [
            n.name for n in node.body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        per_class[name] = len(methods)
        total += len(methods)
    return total, per_class


def section_63_method_count(module):
    """Sum of test_* method counts across EVERY class tagged
    ``post_install``.

    The ``post_install/<module>`` selector matches every class in
    the module that carries the ``post_install`` tag, regardless of
    whether it is also tagged ``-at_install``. In kyc_management,
    ``TestKycOfficerRouting`` is tagged
    ``@tagged("post_install", "-at_install", "kyc_management")`` and
    therefore runs under §6.3 in addition to its §6.2 inclusion."""
    total = 0
    classes_found = []
    for name, _path, node in list_test_classes(module):
        if not _has_post_install_tag(node):
            continue
        methods = [
            n.name for n in node.body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        classes_found.append(name)
        total += len(methods)
    return total, classes_found


def section_64_method_count(module):
    """Method count on the §6.4 ``TestExitGate`` class."""
    manifest = MANIFEST[module]
    return find_class_methods(module, manifest["section_64_class"])


def check_manifest():
    """For each module, compare ground-truth §6.2/§6.3/§6.4 method
    counts against the manifest expectations. Returns a list of
    failures (empty list = pass)."""
    failures = []
    report = {}
    for module, manifest in MANIFEST.items():
        s62, per_class = section_62_method_count(module)
        s63, classes_found = section_63_method_count(module)
        s64_path, s64_methods = section_64_method_count(module)
        s64_count = len(s64_methods)
        report[module] = {
            "section_62": {"actual": s62, "expected": manifest["section_62_expected"],
                           "per_class": per_class},
            "section_63": {"actual": s63, "expected": manifest["section_63_expected"],
                           "post_install_classes": classes_found},
            "section_64": {"actual": s64_count, "expected": manifest["section_64_expected"],
                           "min_required": manifest["section_64_min_methods"],
                           "class": manifest["section_64_class"], "path": s64_path,
                           "methods": s64_methods},
        }
        if s62 != manifest["section_62_expected"]:
            failures.append(
                f"§6.2 {module}: expected {manifest['section_62_expected']}, "
                f"got {s62} (per-class: {per_class})"
            )
        if s63 != manifest["section_63_expected"]:
            failures.append(
                f"§6.3 {module}: expected {manifest['section_63_expected']} on "
                f"post_install class, got {s63} (classes: {classes_found})"
            )
        if s64_path is None:
            failures.append(
                f"§6.4 {module}: class {manifest['section_64_class']!r} missing -- "
                f"§6.4 selector would match zero tests"
            )
        elif s64_count != manifest["section_64_expected"]:
            failures.append(
                f"§6.4 {module}: expected exactly {manifest['section_64_expected']} "
                f"methods on {manifest['section_64_class']!r}, got {s64_count}"
            )
    return failures, report


def check_test_tags_selectors():
    """Every :ClassName selector in any Wave 4 doc must point at an
    existing class in the named module."""
    findings = []
    docs = [
        os.path.join(ROOT, "docs", "WAVE_4_INSTALL_REGRESSION_RESULT.md"),
        os.path.join(ROOT, "docs", "TEST_PROTOCOL_WAVE_3.md"),
    ]
    all_classes = {m: {n for n, _p, _n in list_test_classes(m)} for m in MODULES}
    selector_re = re.compile(r"--test-tags '([^']+)'")
    for doc in docs:
        if not os.path.exists(doc):
            continue
        text = open(doc, encoding="utf-8").read()
        for match in selector_re.finditer(text):
            selector_str = match.group(1)
            for selector in selector_str.split(","):
                selector = selector.strip()
                m = re.match(r"^-?/([a-zA-Z0-9_]+):([A-Za-z0-9_]+)", selector)
                if m:
                    module, cls = m.group(1), m.group(2)
                    if module in all_classes and cls not in all_classes[module]:
                        findings.append({
                            "doc": doc, "selector": selector,
                            "module": module, "class": cls,
                            "problem": f"class {cls!r} not found in {module}/tests/ "
                                       f"-- selector would match zero tests and exit 0",
                        })
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    # Reuse the Rule 1 sync logic from the Wave 3 verifier.
    try:
        w3 = _load_w3_module()
        rule1 = w3.check_rule1_sync()
    except Exception as exc:
        rule1 = {"match": None, "unreachable": [f"verify_wave3_claims load failed: {exc}"]}

    failures, manifest_report = check_manifest()
    stale = check_test_tags_selectors()

    result = {
        "modules": MODULES,
        "manifest": manifest_report,
        "manifest_failures": failures,
        "stale_test_tags_selectors": stale,
        "rule1_sync": rule1,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if not failures and not stale else 1

    print("=" * 70)
    print("WAVE 4 CLAIM VERIFICATION -- ground truth computed from disk")
    print("=" * 70)
    print()
    for module, data in manifest_report.items():
        print(f"-- {module} --")
        s62 = data["section_62"]
        match = "OK" if s62["actual"] == s62["expected"] else "MISMATCH"
        print(f"  §6.2 actual={s62['actual']} expected={s62['expected']} [{match}]")
        for cls, n in s62["per_class"].items():
            print(f"      {cls}: {n}")
        s63 = data["section_63"]
        match = "OK" if s63["actual"] > 0 else "MISMATCH"
        print(f"  §6.3 actual={s63['actual']} [{match}] (post_install classes: {s63['post_install_classes']})")
        s64 = data["section_64"]
        if s64["path"] is None:
            match = "MISMATCH"
            actual = "MISSING"
        else:
            actual = s64["actual"]
            match = "OK" if actual >= s64["min_required"] else "MISMATCH"
        print(f"  §6.4 actual={actual} min={s64['min_required']} [{match}] (path: {s64['path']})")
        for meth in s64["methods"]:
            print(f"      {meth}")
        print()

    print("-- Manifest failures --")
    if not failures:
        print("  none")
    else:
        for f in failures:
            print(f"  {f}")
    print()

    print("-- Stale --test-tags selectors (class not found in named module) --")
    if not stale:
        print("  none")
    else:
        for f in stale:
            print(f"  {f['doc']}: {f['selector']} -> {f['problem']}")
    print()

    print("-- AGENTS.md Rule 1 sync check (delegated to verify_wave3_claims) --")
    print(f"  local: {rule1.get('local') or '<unreachable>'} [branch: {rule1.get('local_branch') or '(detached)'}]")
    if rule1.get("upstream"):
        print(f"  upstream: {rule1['upstream']} = {rule1.get('upstream_origin') or '<unreachable>'}")
    print(f"  origin/main: {rule1.get('origin_main') or '<unreachable>'}")
    print(f"  live server: {rule1.get('live_server') or '<unreachable>'}")
    if rule1.get("match") is True:
        print("  STATUS: MATCH (Rule 1 satisfied)")
    elif rule1.get("match") is False:
        print("  STATUS: MISMATCH -- Rule 1 VIOLATED")
    else:
        print("  STATUS: indeterminate -- one or more endpoints unreachable")
    print()

    ok_manifest = not failures
    ok_stale = not stale
    ok_rule1 = rule1.get("match") is not False

    print("=" * 70)
    if ok_manifest and ok_stale and ok_rule1:
        print("ALL MANIFEST ASSERTIONS PASS.")
        return 0
    else:
        print("FAILURES ABOVE. Do not write a result document from prose")
        print("until these are resolved.")
        return 1


if __name__ == "__main__":
    sys.exit(main())