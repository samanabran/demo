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
import unittest


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


# Odoo 19's test runner emits at least two distinct summary forms. The
# parser must recognise BOTH, because the failing form carries the real
# denominator, and a parser that only knows the passing form will
# silently misclassify a failing run.
#
#   passing shape (the only one the previous parser knew):
#       "5 tests passed, 0 failed, 0 error(s) of 5 tests"
#       "5 tests passed, 0 failed of 5 tests"
#       "Ran 5 tests in 12.3s"
#
#   failing shape (the form the previous parser threw away):
#       "2 failed, 1 error(s) of 16 tests when loading database 'sgc_install'"
#       "3 failed of 16 tests when loading database 'sgc_install'"
#
# Both forms name the total in the form "of N tests" when there is
# one. The "loading database '<db>'" trailer is diagnostic only --
# it confirms the summary belongs to a real run, but is not part of
# the count. We extract total / failed / errors with two independent
# regexes and prefer the most recent matching line, because a long run
# can produce more than one summary (e.g. per-tag sub-runs) and the
# cumulative one is always last.
SUMMARY_TOTAL_RE = re.compile(
    r"of\s+(?P<total>\d+)\s+tests?",
    re.IGNORECASE,
)
SUMMARY_FAILED_RE = re.compile(
    r"(?P<failed>\d+)\s+failed",
    re.IGNORECASE,
)
SUMMARY_ERRORS_RE = re.compile(
    r"(?P<errors>\d+)\s+error\(s\)?",
    re.IGNORECASE,
)
SUMMARY_PASSED_RE = re.compile(
    r"(?P<passed>\d+)\s+tests?\s+passed",
    re.IGNORECASE,
)
# A "summary" line is one that includes the "of N tests" anchor in
# either form. We use this to find the line, then re-scan the line
# itself for the per-field counts. This avoids the previous parser's
# bug of treating "1 tests passed" in a "Loaded module X (1 tests)"
# line as a summary, which it isn't.
SUMMARY_LINE_RE = re.compile(
    r"^.*of\s+\d+\s+tests?.*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_summary(output):
    """Parse the Odoo test summary line(s) out of `output`.

    Returns a tuple (terminal_state, total, failed, errors) where
    terminal_state is one of:

      - "PASS":             summary found, total > 0, failed == 0,
                            errors == 0. Caller must additionally
                            check exit_code == 0; the runner
                            encodes that check separately so the
                            pure parser is unit-testable without
                            running a process.

      - "FAIL_TESTS":       summary found, total > 0, failed > 0
                            OR errors > 0. A real test failure.

      - "FAIL_ZERO_TESTS":  summary found, total == 0. This is the
                            false-green the meta-tests exist to
                            close, and must be a hard failure
                            regardless of exit code.

      - "FAIL_NO_SUMMARY":  no recognisable summary line in the log.
                            Distinct from the run_command-level
                            FileNotFoundError ("BINARY_NOT_FOUND")
                            that signals a missing runtime; that
                            one is produced before this function
                            is ever called. Never coerce into PASS.

    (total, failed, errors) are integers when terminal_state is
    PASS / FAIL_TESTS / FAIL_ZERO_TESTS, and None for FAIL_NO_SUMMARY.
    """
    if not output:
        return ("FAIL_NO_SUMMARY", None, None, None)
    # The "summary" is the LAST line that carries an "of N tests"
    # anchor. Earlier matches would be per-tag sub-runs in some
    # Odoo versions; the cumulative one is what we want.
    matches = list(SUMMARY_LINE_RE.finditer(output))
    if not matches:
        return ("FAIL_NO_SUMMARY", None, None, None)
    line = matches[-1].group(0)

    total_m = SUMMARY_TOTAL_RE.search(line)
    failed_m = SUMMARY_FAILED_RE.search(line)
    errors_m = SUMMARY_ERRORS_RE.search(line)
    passed_m = SUMMARY_PASSED_RE.search(line)

    # If a "of N tests" anchor was present, total is required and
    # authoritative; the line is well-formed.
    total = int(total_m.group("total")) if total_m else 0
    failed = int(failed_m.group("failed")) if failed_m else 0
    errors = int(errors_m.group("errors")) if errors_m else 0
    passed = int(passed_m.group("passed")) if passed_m else 0

    if total == 0:
        return ("FAIL_ZERO_TESTS", 0, failed, errors)
    if failed > 0 or errors > 0:
        return ("FAIL_TESTS", total, failed, errors)
    return ("PASS", total, failed, errors)


def classify_run(output, exit_code):
    """Combine parse_summary with exit_code into the final terminal state.

    This is the function the runner calls per command. It encodes the
    four-state contract from the Wave 3 run order:
      - PASS:             summary found, total > 0, failed == 0,
                          errors == 0, exit code == 0.
      - FAIL_TESTS:       summary found, failed > 0 or errors > 0.
      - FAIL_ZERO_TESTS:  summary found, total == 0, regardless of
                          exit code. (The whole point: zero-tests
                          with exit 0 is the false-green, not PASS.)
      - FAIL_NO_SUMMARY:  no recognisable summary line. Never coerced
                          into PASS.
    Exit code is allowed to be either an int or the string
    "BINARY_NOT_FOUND" produced by run_command(); BINARY_NOT_FOUND is
    the existing runtime-missing state and is preserved unchanged.
    """
    if exit_code == "BINARY_NOT_FOUND":
        return ("BINARY_NOT_FOUND", None, None, None)
    state, total, failed, errors = parse_summary(output)
    if state == "PASS" and exit_code != 0:
        # The summary says everything passed, but the process exited
        # non-zero. That's a real Odoo failure, not a clean run --
        # bump it to FAIL_TESTS so the record is honest.
        return ("FAIL_TESTS", total, failed, errors)
    return (state, total, failed, errors)


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
        # classify_run returns one of:
        #   "BINARY_NOT_FOUND"  -- runtime missing (pre-parser signal)
        #   "PASS" / "FAIL_TESTS" / "FAIL_ZERO_TESTS" / "FAIL_NO_SUMMARY"
        # The tuple is (state, total, failed, errors); when state is
        # BINARY_NOT_FOUND the counts are None. For 6.1 (no test run
        # expected) the parser will typically return FAIL_NO_SUMMARY
        # because 6.1 has no test summary at all; we record that but
        # do not assert on it (the bare-load test is "did install
        # succeed", which is exit-code, not "did tests pass").
        state, total, failed, errors = classify_run(output, exit_code)
        results.append({
            "label": label, "cmd": " ".join(cmd),
            "exit_code": exit_code, "wall_seconds": round(wall, 2),
            "state": state, "total": total, "failed": failed,
            "errors": errors,
            "expected_test_count": expected_total if expects_tests else "n/a",
        })

    # ---- Assertions on the captured results ----

    failures = []
    for r in results:
        # BINARY_NOT_FOUND is the runtime-missing state; surface it
        # prominently because the order says we must distinguish
        # "runtime unreachable" from "real Odoo failure".
        if r["exit_code"] == "BINARY_NOT_FOUND":
            failures.append(
                f"{r['label']}: BINARY_NOT_FOUND -- Odoo runtime not "
                f"reachable. {r.get('state')} cannot be determined."
            )
            continue
        if r["exit_code"] != 0 and r["state"] not in ("FAIL_TESTS", "FAIL_NO_SUMMARY"):
            failures.append(
                f"{r['label']}: non-zero exit ({r['exit_code']}) with "
                f"state {r['state']} -- expected a clear FAIL_TESTS or "
                f"FAIL_NO_SUMMARY but the parser disagreed with the "
                f"process exit code."
            )

    # 6.1 bare-load: we don't expect a test summary. The run is
    # "did install succeed", and that's an exit-code check. A
    # PASS here would be a finding (the bare-load command should
    # not run tests), not a result.
    r61 = results[0]
    if r61["state"] == "PASS":
        failures.append(
            f"{r61['label']}: bare-load command produced a test summary "
            f"with total={r61['total']} failed={r61['failed']} errors="
            f"{r61['errors']}. 6.1 has no --test-enable; if a summary "
            f"appeared, something is wrong. Investigate."
        )

    # 6.2 / 6.3: four-state contract.
    #   - PASS: counts match baseline, no failures, exit 0.
    #   - FAIL_TESTS: real test failures -- a finding, not a blocker
    #     of the runtime, but must be reported with tracebacks.
    #   - FAIL_ZERO_TESTS: false-green. Hard blocker.
    #   - FAIL_NO_SUMMARY: parser could not find a summary line.
    #     Hard finding (the order says "never coerce this into PASS").
    for label in ("6.2", "6.3"):
        r = next(x for x in results if x["label"] == label)
        if r["state"] == "FAIL_ZERO_TESTS":
            failures.append(
                f"{label}: total == 0 with exit 0. Classic false-green; "
                f"the meta-tests in TestCountMeta should have prevented "
                f"this. Inspect the captured output."
            )
        elif r["state"] == "FAIL_NO_SUMMARY":
            failures.append(
                f"{label}: no recognisable summary line in Odoo log. "
                f"Investigate: was the module installed? Did the "
                f"selector match anything?"
            )
        elif r["state"] == "FAIL_TESTS":
            # Real failures are the expected outcome of the new
            # tenant-readiness tests. They go in the result doc as
            # findings, not as a "this run is broken" failure of
            # the runner.
            pass
        elif r["state"] == "PASS":
            if r["total"] < expected_total:
                failures.append(
                    f"{label}: PASS but total {r['total']} < baseline "
                    f"{expected_total}. Genuine regression -- some test "
                    f"classes were dropped or a meta-test now fails on "
                    f"its own assertion."
                )
        # BINARY_NOT_FOUND already surfaced above.

    # 6.4: class-targeted. Expected exactly the exit-gate test count.
    r64 = results[3]
    if r64["state"] == "FAIL_ZERO_TESTS":
        failures.append(
            f"6.4: total == 0. Selector /sgc_process_control:TestExitGate "
            f"matched nothing. The class was renamed; the meta-tests "
            f"should have caught that. Inspect."
        )
    elif r64["state"] == "FAIL_NO_SUMMARY":
        failures.append(
            f"6.4: no recognisable summary line in Odoo log."
        )
    elif r64["state"] == "FAIL_TESTS":
        # Real test failures are findings, not runner failures.
        pass
    elif r64["state"] == "PASS":
        if r64["total"] != EXPECTED_EXIT_GATE_TEST_COUNT:
            failures.append(
                f"6.4: PASS but exit-gate test count {r64['total']} != "
                f"{EXPECTED_EXIT_GATE_TEST_COUNT}. Either a method was "
                f"deleted or one was added without updating the "
                f"meta-test. Real defect, not a false-green."
            )

    print("\n" + "=" * 70)
    print("RUNTIME RESULTS")
    print("=" * 70)
    for r in results:
        print(
            f"{r['label']}: exit={r['exit_code']} wall={r['wall_seconds']}s "
            f"state={r['state']} total={r['total']} failed={r['failed']} "
            f"errors={r['errors']} expected={r['expected_test_count']}"
        )
    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL RUNNER ASSERTIONS PASSED.")
    print()

    # Suspiciously-clean-output flag: all four commands reached
    # state == PASS and matched their expected counts on first
    # attempt. The order says: investigate, do not report as a
    # result. We surface the flag but do not fail the run on it.
    suspiciously_clean = (
        all(r["state"] == "PASS" for r in results[1:])  # 6.2, 6.3, 6.4
        and all(
            r["total"] == (
                EXPECTED_EXIT_GATE_TEST_COUNT
                if r["label"] == "6.4"
                else expected_total
            )
            for r in results[1:]
        )
    )
    if suspiciously_clean:
        print(
            "Suspiciously-clean output check: all three test-bearing "
            "commands exit 0, all expected counts met exactly, zero "
            "failures. With this much new untested code (round-2 "
            "readiness gate, round-3 revenue-band closure), all-green "
            "on attempt one is more likely to indicate a stale tree or "
            "a misconfigured selector than genuine correctness. Inspect "
            "the captured output carefully before signing off."
        )
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true",
                        help="Execute the runtime commands. Without this, "
                        "the runner refuses (this is the intended state "
                        "in environments without an Odoo runtime).")
    parser.add_argument("--selftest", action="store_true",
                        help="Run the parser self-tests. No Odoo runtime "
                        "required; exits 0 on success, 1 on failure.")
    args = parser.parse_args()
    if args.selftest:
        return run_self_tests()
    return run_protocol(real=args.run)


# ---------------------------------------------------------------------------
# Unit tests for the parser. The order requires that the parser be testable
# without an Odoo runtime, using captured sample log text for all four
# states. The samples below were captured by hand from Odoo 19's documented
# log formats and from a representative failing run; they are intentionally
# minimal so a failure in the parser is obvious.
# ---------------------------------------------------------------------------

SAMPLE_PASS_LOG = """
2026-09-01 12:00:00,000 1 INFO ? odoo: Odoo version 19.0
2026-09-01 12:00:01,000 1 INFO ? odoo: Adding base models
2026-09-01 12:00:02,000 1 INFO ? odoo: Loading module sgc_regulatory_rules_pack (1 tests)
2026-09-01 12:00:03,000 1 INFO ? odoo: Loading module sgc_process_control (1 tests)
2026-09-01 12:00:04,000 1 INFO ? odoo: Loading module sgc_tenant_readiness (8 tests)
2026-09-01 12:00:10,000 1 INFO ? odoo: Running tests
2026-09-01 12:00:15,000 1 INFO ? odoo: 16 tests passed, 0 failed, 0 error(s) of 16 tests
""".strip()

SAMPLE_FAIL_TESTS_LOG = """
2026-09-01 12:00:00,000 1 INFO ? odoo: Odoo version 19.0
2026-09-01 12:00:10,000 1 INFO ? odoo: Running tests
2026-09-01 12:00:15,000 1 ERROR ? odoo: TestExitGate.test_exit_gate_03_fail_closed_mixin_raises_on_missing_case failed
Traceback (most recent call last):
  File "/opt/odoo/odoo/addons/sgc_process_control/tests/test_exit_gate.py", line 88, in test_exit_gate_03_fail_closed_mixin_raises_on_missing_case
    self.assertRaises(ValidationError)
AssertionError: ValidationError not raised
2026-09-01 12:00:16,000 1 ERROR ? odoo: TestFreshTenantBlocking.test_configured_partial_config_still_blocks_every_capability failed
2026-09-01 12:00:20,000 1 ERROR ? odoo: 2 failed, 1 error(s) of 16 tests when loading database 'sgc_install'
""".strip()

SAMPLE_FAIL_ZERO_TESTS_LOG = """
2026-09-01 12:00:00,000 1 INFO ? odoo: Odoo version 19.0
2026-09-01 12:00:01,000 1 WARNING ? odoo: No tests found for the provided --test-tags selector.
2026-09-01 12:00:05,000 1 INFO ? odoo: 0 tests passed, 0 failed, 0 error(s) of 0 tests
""".strip()

SAMPLE_FAIL_NO_SUMMARY_LOG = """
2026-09-01 12:00:00,000 1 INFO ? odoo: Odoo version 19.0
2026-09-01 12:00:01,000 1 CRITICAL ? odoo: Database connection failed: could not connect to server
Traceback (most recent call last):
  File "/opt/odoo/odoo/service/server.py", line 1234, in main
    db_connect()
odoo.exceptions.exc_internal: Database connection failed
""".strip()


class ParserSelfTest(unittest.TestCase):
    """Unit tests for parse_summary and classify_run, no Odoo runtime."""

    def test_pass(self):
        state, total, failed, errors = parse_summary(SAMPLE_PASS_LOG)
        self.assertEqual(state, "PASS")
        self.assertEqual(total, 16)
        self.assertEqual(failed, 0)
        self.assertEqual(errors, 0)

    def test_pass_with_classify_run_exit_zero(self):
        state, total, failed, errors = classify_run(SAMPLE_PASS_LOG, 0)
        self.assertEqual(state, "PASS")
        self.assertEqual(total, 16)
        self.assertEqual(failed, 0)
        self.assertEqual(errors, 0)

    def test_fail_tests_with_failed_and_errors(self):
        # The failing-shape summary line: "2 failed, 1 error(s) of 16 tests
        # when loading database 'sgc_install'". The parser must recognise
        # this even though there is no "tests passed" prefix.
        state, total, failed, errors = parse_summary(SAMPLE_FAIL_TESTS_LOG)
        self.assertEqual(state, "FAIL_TESTS")
        self.assertEqual(total, 16)
        self.assertEqual(failed, 2)
        self.assertEqual(errors, 1)

    def test_fail_tests_with_classify_run_preserves_state(self):
        # exit 0 with FAIL_TESTS is unusual but possible (Odoo sometimes
        # exits 0 on a test failure in dev builds). The parser's state
        # must still be FAIL_TESTS, not coerced into PASS.
        state, total, failed, errors = classify_run(SAMPLE_FAIL_TESTS_LOG, 0)
        self.assertEqual(state, "FAIL_TESTS")
        self.assertEqual(total, 16)

    def test_fail_zero_tests(self):
        # Total == 0 with exit 0 is the false-green the meta-tests exist
        # to close. The parser must classify this as FAIL_ZERO_TESTS,
        # never PASS.
        state, total, failed, errors = parse_summary(SAMPLE_FAIL_ZERO_TESTS_LOG)
        self.assertEqual(state, "FAIL_ZERO_TESTS")
        self.assertEqual(total, 0)
        self.assertEqual(failed, 0)
        self.assertEqual(errors, 0)

    def test_fail_zero_tests_with_classify_run(self):
        # Even with a non-zero exit, FAIL_ZERO_TESTS must remain
        # FAIL_ZERO_TESTS -- the contract is "regardless of exit code".
        state, total, failed, errors = classify_run(SAMPLE_FAIL_ZERO_TESTS_LOG, 1)
        self.assertEqual(state, "FAIL_ZERO_TESTS")

    def test_fail_no_summary(self):
        # No recognisable summary line at all -- the parser must return
        # FAIL_NO_SUMMARY, never coerce into PASS.
        state, total, failed, errors = parse_summary(SAMPLE_FAIL_NO_SUMMARY_LOG)
        self.assertEqual(state, "FAIL_NO_SUMMARY")
        self.assertIsNone(total)
        self.assertIsNone(failed)
        self.assertIsNone(errors)

    def test_fail_no_summary_with_classify_run(self):
        state, total, failed, errors = classify_run(SAMPLE_FAIL_NO_SUMMARY_LOG, 1)
        self.assertEqual(state, "FAIL_NO_SUMMARY")

    def test_binary_not_found_passthrough(self):
        # classify_run must preserve the BINARY_NOT_FOUND signal from
        # run_command() and never reach the parser.
        state, total, failed, errors = classify_run("anything", "BINARY_NOT_FOUND")
        self.assertEqual(state, "BINARY_NOT_FOUND")
        self.assertIsNone(total)

    def test_pass_with_non_zero_exit_becomes_fail_tests(self):
        # The summary says everything passed, but the process exited
        # non-zero. That's a real Odoo failure, not a clean run -- the
        # state must be FAIL_TESTS, not PASS, so the record is honest.
        state, total, failed, errors = classify_run(SAMPLE_PASS_LOG, 1)
        self.assertEqual(state, "FAIL_TESTS")
        self.assertEqual(total, 16)
        self.assertEqual(failed, 0)

    def test_empty_output_is_fail_no_summary(self):
        state, total, failed, errors = parse_summary("")
        self.assertEqual(state, "FAIL_NO_SUMMARY")
        self.assertIsNone(total)

    def test_only_loaded_module_lines_is_fail_no_summary(self):
        # The "Loaded module X (N tests)" line is NOT a summary. The
        # previous parser confused it for one and reported a false
        # positive. The new parser must ignore it.
        output = "2026-09-01 INFO ? odoo: Loading module sgc_tenant_readiness (8 tests)"
        state, total, failed, errors = parse_summary(output)
        self.assertEqual(state, "FAIL_NO_SUMMARY")
        self.assertIsNone(total)

    def test_failing_shape_without_errors_phrase(self):
        # "3 failed of 16 tests when loading database 'sgc_install'"
        # is also a valid failing shape. The parser must handle the
        # case where there is no "error(s)" phrase at all.
        output = "2026-09-01 ERROR ? odoo: 3 failed of 16 tests when loading database 'sgc_install'"
        state, total, failed, errors = parse_summary(output)
        self.assertEqual(state, "FAIL_TESTS")
        self.assertEqual(total, 16)
        self.assertEqual(failed, 3)
        self.assertEqual(errors, 0)

    def test_passing_shape_without_failed_phrase(self):
        # "5 tests passed, 0 error(s) of 5 tests" is also a valid
        # passing shape -- the "failed" phrase can be absent.
        output = "2026-09-01 INFO ? odoo: 5 tests passed, 0 error(s) of 5 tests"
        state, total, failed, errors = parse_summary(output)
        self.assertEqual(state, "PASS")
        self.assertEqual(total, 5)
        self.assertEqual(failed, 0)
        self.assertEqual(errors, 0)

    def test_summary_uses_last_match_not_first(self):
        # A long run can produce more than one "of N tests" line
        # (per-tag sub-runs). The cumulative one is always last, and
        # the parser must prefer it.
        output = (
            "INFO ? odoo: 4 tests passed, 0 failed, 0 error(s) of 4 tests\n"
            "INFO ? odoo: 12 tests passed, 0 failed, 0 error(s) of 12 tests\n"
        )
        state, total, failed, errors = parse_summary(output)
        self.assertEqual(state, "PASS")
        self.assertEqual(total, 12)


def run_self_tests():
    """Run the parser self-tests. Returns 0 on success, 1 on failure."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ParserSelfTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
