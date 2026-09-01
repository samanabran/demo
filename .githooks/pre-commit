#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-commit hook: refuse the commit if verify_wave3_claims.py disagrees.

A one-shot verifier that exited 0 today decays the moment someone adds
a test file. Wiring it as a pre-commit hook puts the gate on the path
of every change to the three modules, not behind a manual `python
tools/verify_wave3_claims.py` invocation that an agent or a human can
forget.

Install once:
    git config core.hooksPath .githooks

Or symlink this script into .git/hooks/pre-commit if you prefer the
default hooksPath.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERIFIER = os.path.join(REPO, "tools", "verify_wave3_claims.py")


def main():
    if not os.path.exists(VERIFIER):
        print(f"WARN: verifier not found at {VERIFIER} -- skipping hook.",
              file=sys.stderr)
        return 0
    result = subprocess.run([sys.executable, VERIFIER], cwd=REPO)
    if result.returncode != 0:
        print("\npre-commit hook refused the commit:",
              "verify_wave3_claims.py reported failures.",
              file=sys.stderr)
        print("Run `python tools/verify_wave3_claims.py` for details.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
