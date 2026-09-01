#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify WAVE_3_INSTALL_REGRESSION_RESULT.md's factual claims against disk.

Root cause identified in the Wave 3 remediation review (round 2 → round 3):
three of the eight defects raised against the round-1 draft were not real
bugs -- they were a result document whose factual sections (class counts,
R8 file-scan denominators, "is X implemented" claims) were written as
prose, by the same process that writes everything else, with no mechanism
forcing them to agree with the tree. The document can say anything; only
this script's output is grounded in the actual files.

This is not a test suite. It requires no Odoo runtime. It is a plain
Python script an agent or a human runs before writing or reviewing any
claim in the Wave 3 result document, and its output is what gets pasted
into that document -- never hand-typed numbers.

Usage:
    python tools/verify_wave3_claims.py [--json]

Exit code 0 if every check is internally consistent (reconciles), no
matter what the numbers are. This script does not know what the "right"
answer is -- it computes the ground truth and prints it. A human or a
downstream check compares the printed ground truth against what the
document claims.
"""

import argparse
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = ["sgc_regulatory_rules_pack", "sgc_process_control", "sgc_tenant_readiness"]

PROHIBITED = [
    r"\bcompliant\b", r"\bcompliance guaranteed\b", r"\bensures compliance\b",
    r"\bAML compliant\b", r"\bfully compliant\b", r"\bcertified\b",
]
PERMITTED = [
    r"supports the tenant", r"record evidence of", r"configured by the tenant",
    r"as configured", r"tenant responsibility", r"non-compliant",
]
_SEP = re.escape(os.sep)
R8_ALLOWED_PATTERNS = [
    re.compile(rf".*{_SEP}docs{_SEP}.*\.md$"),
    re.compile(rf".*{_SEP}migrations{_SEP}.*\.py$"),
    re.compile(rf".*{_SEP}tests{_SEP}.*\.py$"),
]

# Symbols that must NOT appear anywhere except as prose explaining their
# removal. Extend this list whenever a breaking API removal happens --
# this is what would have caught "action_mark_ready still referenced in
# a view" before install, not after.
REMOVED_SYMBOLS_ALLOWED_ONLY_IN_PROSE = [
    "action_mark_ready",
]


def module_path(module):
    return os.path.join(ROOT, module)


def count_test_classes(module):
    """AST-based count of every TestCase/HttpCase subclass under
    <module>/tests/. Includes the meta-test class itself -- this is the
    single counting convention, fixed in Wave 3 remediation round 2.
    """
    tests_dir = os.path.join(module_path(module), "tests")
    names = []
    if not os.path.isdir(tests_dir):
        return names
    for root, dirs, files in os.walk(tests_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError as e:
                print(f"SYNTAX ERROR in {path}: {e}", file=sys.stderr)
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = [
                        b.id if isinstance(b, ast.Name)
                        else (b.attr if isinstance(b, ast.Attribute) else "?")
                        for b in node.bases
                    ]
                    if "TransactionCase" in bases or "HttpCase" in bases:
                        names.append(node.name)
    return sorted(names)


def find_test_method_names(module, class_name):
    """Return the sorted list of test_* method names on a given class."""
    tests_dir = os.path.join(module_path(module), "tests")
    for root, dirs, files in os.walk(tests_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            tree = ast.parse(open(path, encoding="utf-8").read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    methods = [
                        n.name for n in node.body
                        if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                    ]
                    return path, sorted(methods)
    return None, []


def r8_scan():
    """Reproduce the R8 mechanical scan exactly as
    sgc_tenant_readiness/tests/test_r8_scan.py does it, module by module.
    """
    compiled = [re.compile(p, re.IGNORECASE) for p in PROHIBITED]
    permitted = [re.compile(p, re.IGNORECASE) for p in PERMITTED]
    per_module = {}
    hits = []
    for module in MODULES:
        base = module_path(module)
        total = scope = scanned = excluded = 0
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if f.endswith(".pyc"):
                    continue
                total += 1
                if not f.endswith((".py", ".xml", ".csv", ".md")):
                    continue
                scope += 1
                path = os.path.join(root, f)
                if any(p.match(path) for p in R8_ALLOWED_PATTERNS):
                    excluded += 1
                    continue
                scanned += 1
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        for ln, line in enumerate(fh, 1):
                            for pattern in compiled:
                                if pattern.search(line) and not any(
                                    perm.search(line) for perm in permitted
                                ):
                                    hits.append((path, ln, line.strip()))
                except (UnicodeDecodeError, OSError):
                    continue
        per_module[module] = {
            "total_files": total, "in_scope": scope,
            "scanned": scanned, "excluded": excluded,
            "reconciles": (scanned + excluded == scope),
        }
    grand = {
        "total_files": sum(m["total_files"] for m in per_module.values()),
        "in_scope": sum(m["in_scope"] for m in per_module.values()),
        "scanned": sum(m["scanned"] for m in per_module.values()),
        "excluded": sum(m["excluded"] for m in per_module.values()),
    }
    grand["reconciles"] = (grand["scanned"] + grand["excluded"] == grand["in_scope"])
    grand["violations"] = len(hits)
    return per_module, grand, hits


def check_removed_symbols():
    """For each symbol that was deliberately removed as a breaking API
    change, find every occurrence across the three modules and classify
    each hit as "invocation" (a call/reference that would fail at
    install or runtime) or "prose" (a comment/docstring explaining the
    removal). Any invocation hit is a real defect.
    """
    results = {}
    for symbol in REMOVED_SYMBOLS_ALLOWED_ONLY_IN_PROSE:
        hits = []
        for module in MODULES:
            base = module_path(module)
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in files:
                    if not f.endswith((".py", ".xml")):
                        continue
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8") as fh:
                            for ln, line in enumerate(fh, 1):
                                if symbol in line:
                                    hits.append((path, ln, line.strip()))
                    except (UnicodeDecodeError, OSError):
                        continue
        # Heuristic invocation detection: an XML <button name="symbol"...>
        # or a Python `.symbol(` / `self.symbol` call, not inside a
        # comment (# ...) or a docstring-looking quoted line.
        invocations = []
        prose = []
        for path, ln, text in hits:
            is_xml_call = f'name="{symbol}"' in text
            is_py_call = re.search(rf"\b{re.escape(symbol)}\s*\(", text) and not text.lstrip().startswith("#")
            is_comment_or_docstring = text.lstrip().startswith("#") or text.lstrip().startswith('"""') \
                or text.lstrip().startswith("'") or "`" in text
            if (is_xml_call or is_py_call) and not is_comment_or_docstring:
                invocations.append((path, ln, text))
            else:
                prose.append((path, ln, text))
        results[symbol] = {"invocations": invocations, "prose_mentions": prose}
    return results


def check_test_tags_selectors():
    """Extract every --test-tags string from docs/TEST_PROTOCOL_WAVE_3.md
    and docs/WAVE_3_INSTALL_REGRESSION_RESULT.md, and for any selector
    that names a specific class (":ClassName"), verify that class exists
    in the module named in the same selector.
    """
    findings = []
    docs = [
        os.path.join(ROOT, "docs", "TEST_PROTOCOL_WAVE_3.md"),
        os.path.join(ROOT, "docs", "WAVE_3_INSTALL_REGRESSION_RESULT.md"),
    ]
    all_classes = {m: set(count_test_classes(m)) for m in MODULES}
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
                                       f"-- this selector would match zero tests and exit 0",
                        })
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = {
        "test_classes": {m: count_test_classes(m) for m in MODULES},
        "test_class_counts": {m: len(count_test_classes(m)) for m in MODULES},
        "exit_gate": {},
        "r8": {},
        "removed_symbols": check_removed_symbols(),
        "stale_test_tags_selectors": check_test_tags_selectors(),
    }
    path, methods = find_test_method_names("sgc_process_control", "TestExitGate")
    result["exit_gate"] = {"file": path, "method_count": len(methods), "methods": methods}

    per_module, grand, hits = r8_scan()
    result["r8"] = {"per_module": per_module, "total": grand,
                     "violations_detail": [{"file": h[0], "line": h[1], "text": h[2]} for h in hits]}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print("=" * 70)
    print("WAVE 3 CLAIM VERIFICATION -- ground truth computed from disk")
    print("=" * 70)
    print()
    print("-- Test class counts (one convention: every TestCase incl. meta) --")
    for m in MODULES:
        print(f"  {m}: {result['test_class_counts'][m]}  {result['test_classes'][m]}")
    print()
    print("-- Exit-gate class --")
    print(f"  file: {result['exit_gate']['file']}")
    print(f"  method count: {result['exit_gate']['method_count']}")
    for meth in result["exit_gate"]["methods"]:
        print(f"    {meth}")
    print()
    print("-- R8 scan --")
    for m in MODULES:
        d = result["r8"]["per_module"][m]
        status = "OK" if d["reconciles"] else "MISMATCH"
        print(f"  {m}: total={d['total_files']} in_scope={d['in_scope']} "
              f"scanned={d['scanned']} excluded={d['excluded']} [{status}]")
    g = result["r8"]["total"]
    status = "OK" if g["reconciles"] else "MISMATCH"
    print(f"  TOTAL: total={g['total_files']} in_scope={g['in_scope']} "
          f"scanned={g['scanned']} excluded={g['excluded']} [{status}]")
    print(f"  violations: {g['violations']}")
    for v in result["r8"]["violations_detail"]:
        print(f"    {v['file']}:{v['line']}: {v['text']}")
    print()
    print("-- Removed-symbol invocation check --")
    ok = True
    for symbol, data in result["removed_symbols"].items():
        n_inv = len(data["invocations"])
        n_prose = len(data["prose_mentions"])
        print(f"  {symbol}: {n_inv} invocation(s), {n_prose} prose mention(s)")
        for path, ln, text in data["invocations"]:
            print(f"    INVOCATION {path}:{ln}: {text}")
            ok = False
    print()
    print("-- Stale --test-tags selectors (class not found in named module) --")
    stale = result["stale_test_tags_selectors"]
    if not stale:
        print("  none found")
    else:
        ok = False
        for f in stale:
            print(f"  {f['doc']}: {f['selector']} -> {f['problem']}")
    print()

    reconciles = all(d["reconciles"] for d in result["r8"]["per_module"].values()) and g["reconciles"]
    no_violations = g["violations"] == 0
    no_stale = not stale
    no_bad_invocations = ok

    print("=" * 70)
    if reconciles and no_violations and no_stale and no_bad_invocations:
        print("ALL CHECKS INTERNALLY CONSISTENT.")
        print("This does NOT mean the document's claims are correct -- it means")
        print("this script's own arithmetic reconciles and no known-dangerous")
        print("pattern (stale selector, orphaned invocation, R8 hit) was found.")
        print("Paste the numbers above into the result document. Do not")
        print("hand-type them.")
        return 0
    else:
        print("FAILURES ABOVE. Do not write a result document from prose")
        print("until these are resolved.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
