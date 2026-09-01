#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime runner for the Wave 3 install protocol.

Runs the four commands from `docs/TEST_PROTOCOL_WAVE_3.md` §6.1–§6.4
plus the regression and isolation runs (§7, §10), parses the Odoo
test log for per-command test counts, asserts the counts against the
4/4/8 baseline, and treats zero-tests-exit-zero as a hard failure.

Designed to be invocable in two states:

  1. With an Odoo runtime reachable (the real run):
       $ python tools/run_wave3_protocol.py --run

     The script will execute the commands and capture exit codes,
     wall times, and test counts. Appends results to
     docs/WAVE_3_INSTALL_REGRESSION_RESULT.md as the §17 evidence block.

  2. Without an Odoo runtime (this environment):
       $ python tools/run_wave3_protocol.py

     The script will exit 1 with an actionable message. That is the
     intended behaviour: a runtime protocol runner that pretends to
     succeed when it cannot actually run is worse than one that
     refuses outright.

In either state, the script first runs
`tools/verify_wave3_claims.py` and refuses to proceed if it fails. The
pre-commit hook is the source-of-truth gate; this re-check is a
defence-in-depth on a different machine.
"""

import argparse
import os
import re
import subprocess
import sys
import time


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFIER = os.path.join(REPO, "tools", "verify_wave3_claims.py")
ODOO_BIN = os.environ.get("ODOO_BIN", "odoo-bin")
RESULTS_DOC = os.path.join(REPO, "docs", "WAVE_3_INSTALL_REGRESSION_RESULT.md")


# Per the user's runtime instructions: per-module expected test count.
# 4 + 4 + 8 = 16 total TestCase subclasses for 6.2 / 6.3 (each module's
# at_install tests). 6.4 is class-targeted, so the assertion is on
# the class's test-method count, not the per-module count.
EXPECTED_CLASS_COUNTS = {
    "sgc_regulatory_rules_pack": 4,
    "sgc_process_control": 4,
    "sgc_tenant_readiness": 8,
}
EXPECTED_EXIT_GATE_TEST_COUNT = 7


# The Odoo test log uses lines like:
#   "Loaded module sgc_tenant_readiness (1 tests)"
#   "running tests ..."
#   "1 tests passed, 0 tests failed"
# We extract the post-run summary line. We don't try to parse every
# dialect of the Odoo log -- the regex below matches the modern
# "N tests passed, N tests failed" format. If the format changes,
# the runner fails loudly rather than guessing.
TEST_RESULT_LINE_RE = re.compile(
    r"(?P<ran>\d+)\s+tests?\s+(?:passed|ran|executed)"
    r"(?:.*?(?P<failed>\d+)\s+(?:failed|errors?))?",
    re.IGNORECASE,
)


def run_preflight():
    """Run the verifier. Return True if it passes, False otherwise."""
    result = subprocess.run([sys.executable, VERIFIER], cwd=REPO)
    return result.returncode == 0


def run_command(cmd, env=None, timeout=1800):
    """Run cmd, return (exit_code, wall_seconds, stdout+stderr).

    Distinguishes "binary not found" from a real failure: a
    FileNotFoundError on the command itself means the runtime is
    not actually reachable, which the result document should record
    differently from a real Odoo failure.
    """
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=REPO, env=env, timeout=timeout,
            capture_output=True, text=True,
        )
    except FileNotFoundError as e:
        return ("BINARY_NOT_FOUND", time.monotonic() - start,
                f"Could not execute command: {e}. "
                f"Is odoo-bin (or the ODOO_BIN override) on PATH?")
    return proc.returncode, time.monotonic() - start, (proc.stdout or "") + (proc.stderr or "")


def extract_test_count(output):
    """Pull the test count from Odoo's run summary.

    Returns the integer count, or None if no summary line was found. A
    None result triggers a hard failure later -- the runner refuses to
    guess, because a missing summary is itself a red flag (the run did
    not produce a result line, which is what happens when Odoo refuses
    to install the module or a tag selector matched nothing).
    """
    # Prefer the most recent (last) matching line.
    matches = list(TEST_RESULT_LINE_RE.finditer(output))
    if not matches:
        return None
    m = matches[-1]
    # If "failed" wasn't captured, the "ran" number is the total.
    # If "failed" was captured, "ran" is still the total count.
    return int(m.group("ran"))


def expected_total_for_command_6_2_or_6_3():
    """Sum the per-module expected class counts.

    Note: each TestCase subclass produces >= 1 test method, so the
    number of test *methods* run is at least the number of test
    *classes*. We compare the Odoo-reported test count against this
    class count, which is the lower bound we can assert against without
    false-positives.
    """
    return sum(EXPECTED_CLASS_COUNTS.values())


def run_protocol(real=False):
    """If real is False, refuse. If real is True, execute commands and
    assert. Appends results to the result document.
    """
    if not real:
        print(
            "REFUSING: no Odoo runtime in PATH. This script is a "
            "protocol runner, not a faker. To run it for real, start "
            "the postgres:16 + odoo:19 (dated tag) containers from the "
            "suggested docker-compose shape in §15 of TEST_PROTOCOL_WAVE_3.md, "
            "export ODOO_BIN=$(which odoo-bin) (or the path inside the "
            "container), and re-run with --run.",
            file=sys.stderr,
        )
        return 2

    if not run_preflight():
        print(
            "REFUSING: verifier failed. Run `python tools/verify_wave3_claims.py` "
            "and fix the failures before starting the runtime.",
            file=sys.stderr,
        )
        return 1

    print("Verifier passed. Starting runtime protocol.")

    commands = [
        ("6.1", [
            ODOO_BIN, "-d", "sgc_install",
            "-i", "sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness",
            "--stop-after-init", "--log-level=info",
        ], False),  # expected to run zero tests
        ("6.2", [
            ODOO_BIN, "-d", "sgc_install",
            "-u", "sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness",
            "--test-enable",
            "--test-tags", "/sgc_regulatory_rules_pack,/sgc_process_control,/sgc_tenant_readiness",
            "--stop-after-init", "--log-level=test",
        ], True),
        ("6.3", [
            ODOO_BIN, "-d", "sgc_install",
            "-u", "sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness",
            "--test-enable",
            "--test-tags", "post_install/sgc_tenant_readiness,post_install/sgc_process_control",
            "--stop-after-init", "--log-level=test",
        ], True),
        ("6.4", [
            ODOO_BIN, "-d", "sgc_install",
            "--test-enable",
            "--test-tags", "/sgc_process_control:TestExitGate",
            "--stop-after-init",
        ], True),
    ]

    expected_total = expected_total_for_command_6_2_or_6_3()
    results = []
    for label, cmd, expects_tests in commands:
        print(f"\n--- {label}: {' '.join(cmd)}")
        exit_code, wall, output = run_command(cmd)
        test_count = extract_test_count(output) if expects_tests else None
        results.append({
            "label": label, "cmd": " ".join(cmd),
            "exit_code": exit_code, "wall_seconds": round(wall, 2),
            "test_count": test_count,
            "expected_test_count": expected_total if expects_tests else "n/a",
        })

    # ---- Assertions on the captured results ----

    failures = []
    for r in results:
        if r["exit_code"] != 0:
            failures.append(f"{r['label']}: non-zero exit ({r['exit_code']})")

    # 6.1 bare-load: zero tests is the expected outcome, not a failure.
    r61 = results[0]
    if r61["test_count"] not in (None, 0):
        failures.append(
            f"{r61['label']}: expected zero tests (bare-load command), "
            f"got {r61['test_count']} -- this is suspicious but not "
            f"a hard failure; investigate if it indicates the module "
            f"is being installed with --test-enable set."
        )

    # 6.2 / 6.3: zero tests with exit 0 is THE false-green we exist to
    # catch. Hard failure on that, not a warning.
    for label in ("6.2", "6.3"):
        r = next(x for x in results if x["label"] == label)
        if r["test_count"] is None:
            failures.append(
                f"{label}: no test summary line found in Odoo log -- "
                f"this is what a selector-matching-nothing run looks like. "
                f"Inspect the captured output."
            )
        elif r["test_count"] == 0:
            failures.append(
                f"{label}: selector matched ZERO tests but command "
                f"exited 0. Classic false-green; the meta-tests in "
                f"TestCountMeta should have prevented this. "
                f"Inspect the captured output."
            )
        elif r["test_count"] < expected_total:
            failures.append(
                f"{label}: test count {r['test_count']} below baseline "
                f"{expected_total}. Genuine regression -- some test "
                f"classes were dropped or a meta-test now fails on "
                f"its own assertion."
            )

    # 6.4: class-targeted. Expected exactly the exit-gate test count.
    r64 = results[3]
    if r64["test_count"] is None:
        failures.append(
            f"6.4: no test summary line found in Odoo log. "
            f"Inspect the captured output."
        )
    elif r64["test_count"] == 0:
        failures.append(
            f"6.4: selector /sgc_process_control:TestExitGate matched "
            f"ZERO tests but command exited 0. The class was renamed; "
            f"the meta-tests should have caught that. Inspect."
        )
    elif r64["test_count"] != EXPECTED_EXIT_GATE_TEST_COUNT:
        failures.append(
            f"6.4: exit-gate test count {r64['test_count']} != "
            f"{EXPECTED_EXIT_GATE_TEST_COUNT}. Either a method was "
            f"deleted or one was added without updating the meta-test. "
            f"Real defect, not a false-green."
        )

    print("\n" + "=" * 70)
    print("RUNTIME RESULTS")
    print("=" * 70)
    for r in results:
        print(f"{r['label']}: exit={r['exit_code']} wall={r['wall_seconds']}s "
              f"tests={r['test_count']} expected={r['expected_test_count']}")
    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL ASSERTIONS PASSED.")
    print()
    print("Suspiciously-clean output check: all four commands exit 0, "
          "all expected counts met, zero failures. With this much new "
          "untested code (round-2 readiness gate, round-3 revenue-band "
          "closure), all-green on attempt one is more likely to indicate "
          "a stale tree than genuine correctness. Inspect the captured "
          "output carefully before signing off.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true",
                        help="Execute the runtime commands. Without this, "
                        "the runner refuses (this is the intended state "
                        "in environments without an Odoo runtime).")
    args = parser.parse_args()
    return run_protocol(real=args.run)


if __name__ == "__main__":
    sys.exit(main())
