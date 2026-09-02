#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGC audit-driven coupling lint tool.

This tool reproduces the rules behind ``audit_out/coupling_findings.csv`` so
that the patterns the audit flagged can be enforced in CI for any future
audit-phase update.

It is a *static* lint — it cannot reach database rows. The audit's
``multi_tenant_blockers.json`` M3 / M5 SQL evidence is therefore not
in scope; see ``docs/audit/MULTI_TENANT_BLOCKERS.md`` for the matching
runtime preflight.

Usage:

    python tools/audit_coupling_lint.py \\
        --addons-path ./addons \\
        --include-path ./sgc_realestate_brokerage_template \\
        --report-md docs/audit/lint_report.md \\
        [--fail-on-findings] \\
        [--exclude \\.git --exclude __pycache__ --exclude '\\.bak$']

Exit codes:

    0   — no findings (or warnings only).
    1   — at least one hard finding (unless --fail-on-findings is not set).
    2   — configuration error (e.g. invalid --addons-path).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Iterator


# ---------------------------------------------------------------------------
# Pattern catalogue — derived from the SGC audit phase outputs.
# ---------------------------------------------------------------------------
# Each rule records the audit phase / file that drove it. Update this file
# whenever the audit's coupling_findings.csv is updated.

# Tier 1 — hardcoded mailbox / tenant identity.
TIER1_EMAIL_HOSTS = re.compile(
    r"(?P<email>\b[A-Za-z0-9._%+-]+@(?:sgctech\.ai|sgcglobalconsultants\.com"
    r"|osusproperties\.com|kzsoftwares\.com)\b)"
)

# Tier 1 — ir.mail_server / fetchmail.server in XML data
TIER1_IR_MAIL_RECORDS = re.compile(
    r'<record[^>]+model="(?:ir\.mail_server|fetchmail\.server)"',
    re.IGNORECASE,
)

# Tier 1 — hardcoded `localhost` / loopback URLs.
TIER1_LOCALHOST = re.compile(
    r"\bhttps?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?(?:/\S*)?\b",
    re.IGNORECASE,
)

# Tier 1 — meeting AI workspace hardcoded.  # audit-lint: disable=tier1/meeting_ai_workspace, tier1/email
TIER1_MEETING_AI_WORKSPACE = re.compile(
    r"\bcrm@sgctech\.ai\b",  # audit-lint: disable=tier1/meeting_ai_workspace
    re.IGNORECASE,
)

# Tier 2 — Ksolves branding evidence (only flags when the post-tamper
# already changed author — i.e. when the module is held).
TIER2_KSOLVES_BRANDING = re.compile(
    r"\b(?:Ksolves India Ltd\.?|store\.ksolves\.com)\b",
)

# Tamper pattern — auto_install True with OPL-1 after Ksolves recovery
# (audit-recovered: original was LGPL-3 + auto_install False).
TAMPER_AUTOTRUE_OPL = re.compile(
    r'"auto_install"\s*:\s*True.*"license"\s*:\s*"OPL-1"',
    re.DOTALL,
)

# Skip directories
DEFAULT_EXCLUDES = [
    r"[\\/]\.git[\\/]",
    r"__pycache__",
    r"\.pyc$",
    r"\.bak",
    r"node_modules",
    # Avoid scanning our own output files (re-emitting findings every run).
    # Cross-platform path separators handled with `[\\/]`.
    r"[\\/]docs[\\/]audit[\\/]lint_report\.(json|md)$",
    # Server content that is not relevant to the addon-path lint scope.
    r"[\\/]tools[\\/]remotion-demo[\\/]",
    # Markdown under docs/audit is documentation, not source; flagged by
    # inline suppressions at the line level when intentional.
    r"[\\/]docs[\\/]audit[\\/].*\.md$",
    r"[\\/]30_QUARANTINE[\\/].*\.md$",
]

# Files we always skip (generated / decorative).
DEFAULT_FILE_EXCLUDES = [
    r"[\\/]static[\\/].*index\.html$",
    r"/tests/",
]

# Inline-suppression mechanism (escape hatch for documentary examples).
# Recognised on the same line as a finding:
#   Python:  ...      # audit-lint: disable=<rule>
#   XML/HTML: ...    <!-- audit-lint: disable=<rule> -->
# Replaces the audit's previous "false positives bleed into the security gate"
# pattern. The suppression is documented at the top of each use site so the
# reason is durable, not just a comment.
INLINE_DISABLE_PYTHON = re.compile(
    r"#\s*audit-lint\s*:\s*disable\s*=\s*(?P<rules>[A-Za-z0-9_,/\s\-]+)"
)
INLINE_DISABLE_MARKUP = re.compile(
    r"<!--\s*audit-lint\s*:\s*disable\s*=\s*(?P<rules>[A-Za-z0-9_,/\s\-]+)\s*-->"
)


def parse_disabled_rules(snippet: str, extension: str) -> set[str]:
    """Return set of rule names disabled for the *line* that produced this
    snippet.  The snippet covers the line already; we look at the trailing
    portion for the inline suppression token.
    """
    if extension in {".xml", ".html", ".md"}:
        candidates = INLINE_DISABLE_MARKUP
    else:
        candidates = INLINE_DISABLE_PYTHON
    m = candidates.search(snippet)
    if not m:
        return set()
    return {
        rule.strip().strip("/")
        for rule in m.group("rules").split(",")
        if rule.strip()
    }

# ---------------------------------------------------------------------------
# Data classes.
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    severity: str   # 'hard' | 'warning' | 'info'
    rule: str
    message: str
    path: str
    line: int = 0
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditReport:
    started_at: str = field(default_factory=lambda: _dt.datetime.utcnow().isoformat() + "Z")
    finished_at: str = ""
    addons_paths: list[str] = field(default_factory=list)
    include_paths: list[str] = field(default_factory=list)
    file_count: int = 0
    findings: list[Finding] = field(default_factory=list)
    hard_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add(self, f: Finding) -> None:
        self.findings.append(f)
        if f.severity == "hard":
            self.hard_count += 1
        elif f.severity == "warning":
            self.warning_count += 1
        else:
            self.info_count += 1


# ---------------------------------------------------------------------------
# Walker.
# ---------------------------------------------------------------------------


def iter_files(
    roots: Iterable[Path],
    excludes: list[re.Pattern],
) -> Iterator[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            spath = str(path)
            if path in seen:
                continue
            if any(ex.search(spath) for ex in excludes):
                continue
            # Skip binary inside our filter set
            if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
                continue
            seen.add(path)
            yield path


def matches_any(path_str: str, patterns: Iterable[re.Pattern]) -> bool:
    return any(p.search(path_str) for p in patterns)


def line_for(content: str, offset: int) -> int:
    """Return 1-based line number for a character offset."""
    return content.count("\n", 0, offset) + 1


def snippet_at(content: str, offset: int, window: int = 80) -> str:
    start = max(0, offset - window // 2)
    end = min(len(content), offset + window // 2)
    s = content[start:end].replace("\n", " ⏎ ")
    return s[:window]


# ---------------------------------------------------------------------------
# Rule functions.
# ---------------------------------------------------------------------------


def rule_tier1_email(report: AuditReport, path: Path, content: str) -> None:
    for m in TIER1_EMAIL_HOSTS.finditer(content):
        report.add(Finding(
            severity="hard",
            rule="tier1/email",
            message=(
                "Hardcoded tenant email address "
                f"({m.group('email')}); replace with an "
                "`ir.config_parameter` lookup."
            ),
            path=str(path),
            line=line_for(content, m.start()),
            snippet=snippet_at(content, m.start()),
        ))


def rule_tier1_ir_mail_server(report: AuditReport, path: Path, content: str) -> None:
    if not path.suffix.lower() == ".xml":
        return
    for m in TIER1_IR_MAIL_RECORDS.finditer(content):
        report.add(Finding(
            severity="hard",
            rule="tier1/ir_mail_server",
            message=(
                "Hardcoded <record model='ir.mail_server'> or "
                "<record model='fetchmail.server'> in XML data; "
                "create them via the onboarding wizard instead."
            ),
            path=str(path),
            line=line_for(content, m.start()),
            snippet=snippet_at(content, m.start()),
        ))


def rule_tier1_localhost(report: AuditReport, path: Path, content: str) -> None:
    for m in TIER1_LOCALHOST.finditer(content):
        report.add(Finding(
            severity="hard",
            rule="tier1/localhost",
            message=(
                f"Hardcoded localhost/loopback URL ({m.group(0)}); "
                "use `ir.config_parameter('web.base.url')`."
            ),
            path=str(path),
            line=line_for(content, m.start()),
            snippet=snippet_at(content, m.start()),
        ))


def rule_tier1_meeting_ai(report: AuditReport, path: Path, content: str) -> None:
    for m in TIER1_MEETING_AI_WORKSPACE.finditer(content):
        report.add(Finding(
            severity="hard",
            rule="tier1/meeting_ai_workspace",
            message=(
                "Hardcoded `crm@sgctech.ai` (M5 / 16h audit blocker); "  # audit-lint: disable=tier1/meeting_ai_workspace, tier1/email
                "use `ir.config_parameter('sgc.meeting_ai.workspace_account')`."  # audit-lint: disable=tier1/meeting_ai_workspace, tier1/email
            ),  # audit-lint: disable=tier1/meeting_ai_workspace, tier1/email
            path=str(path),
            line=line_for(content, m.start()),
            snippet=snippet_at(content, m.start()),
        ))


def rule_tier2_ksolves(report: AuditReport, path: Path, content: str) -> None:
    """Detect unrecovered Ksolves branding; only fire if module is held."""

    # Only flag in modules known to be the held ones.
    if "/ks_dynamic_financial_report/" not in str(path):
        return
    for m in TIER2_KSOLVES_BRANDING.finditer(content):
        report.add(Finding(
            severity="warning",
            rule="tier2/ksolves_branding",
            message=(
                "Ksolves branding evidence still present; this module is "
                "in 30_QUARANTINE/ and should not be re-shipped under an "
                "SGC byline."
            ),
            path=str(path),
            line=line_for(content, m.start()),
            snippet=snippet_at(content, m.start()),
        ))


def rule_manifest_tamper(report: AuditReport, path: Path, content: str) -> None:
    """Detect the Ksolves-tamper pattern recovered by Phase 9."""

    if path.name != "__manifest__.py":
        return
    for m in TAMPER_AUTOTRUE_OPL.finditer(content):
        report.add(Finding(
            severity="hard",
            rule="manifest/tamper_pattern",
            message=(
                "Manifest carries the post-tamper pattern: "
                "`auto_install: True` paired with `licence: OPL-1`. Per "
                "audit Phase 9, this is the Ksolves-tamper signature; "
                "verify the recovery or stop shipping this manifest."
            ),
            path=str(path),
            line=line_for(content, m.start()),
            snippet=snippet_at(content, m.start()),
        ))


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------


def run_audit(roots: list[Path], excludes: list[re.Pattern]) -> AuditReport:
    report = AuditReport(addons_paths=[str(r) for r in roots])
    file_excludes = [re.compile(p) for p in DEFAULT_FILE_EXCLUDES]
    for path in iter_files(roots, excludes + file_excludes):
        report.file_count += 1
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rule_tier1_email(report, path, content)
        rule_tier1_ir_mail_server(report, path, content)
        rule_tier1_localhost(report, path, content)
        rule_tier1_meeting_ai(report, path, content)
        rule_tier2_ksolves(report, path, content)
        rule_manifest_tamper(report, path, content)
        # Apply inline suppressions (audit-doc discipline).
        _apply_inline_suppressions(report, path, content)
    report.finished_at = _dt.datetime.utcnow().isoformat() + "Z"
    return report


def _apply_inline_suppressions(
    report: AuditReport, path: Path, content: str,
) -> None:
    """Filter findings whose line carries an `audit-lint: disable=...`
    comment. Operates only on the line that produced the finding.

    Accepts the full rule name (e.g. `tier1/email`) or the rule root
    (e.g. `tier1`) in the disable token, comma-separated.

    Decrements the matching severity counter so that suppressed findings
    do not falsely fail the gate.
    """
    ext = path.suffix.lower()
    kept: list[Finding] = []
    for f in report.findings:
        if f.path != str(path):
            kept.append(f)
            continue
        line_no = f.line
        if line_no <= 0:
            kept.append(f)
            continue
        line_text = (
            content.splitlines()[line_no - 1] if content else ""
        )
        disabled = parse_disabled_rules(line_text, ext)
        if disabled and (
            f.rule in disabled or rule_root(f.rule) in disabled
        ):
            if f.severity == "hard":
                report.hard_count = max(0, report.hard_count - 1)
            elif f.severity == "warning":
                report.warning_count = max(0, report.warning_count - 1)
            else:
                report.info_count = max(0, report.info_count - 1)
            report.info_count += 1
            f.severity = "info"
            f.message = (
                f.message
                + "  [suppressed inline — re-enable by removing the "
                + "audit-lint disable annotation]"
            )
        kept.append(f)
    report.findings = kept


def rule_root(name: str) -> str:
    """`tier1/email` -> `tier1`. The disable token uses the rule root."""
    return name.split("/", 1)[0]


def render_markdown(report: AuditReport) -> str:
    lines: list[str] = []
    lines.append("# Audit coupling lint report")
    lines.append("")
    lines.append(f"Started: `{report.started_at}`")
    lines.append(f"Finished: `{report.finished_at}`")
    lines.append("")
    lines.append(
        f"Files scanned: **{report.file_count}** | "
        f"Findings: hard **{report.hard_count}** | "
        f"warning **{report.warning_count}** | "
        f"info **{report.info_count}**"
    )
    lines.append("")
    lines.append("## Per-rule summary")
    lines.append("")
    rules: dict[str, int] = {}
    for f in report.findings:
        rules[f.rule] = rules.get(f.rule, 0) + 1
    if rules:
        for rule, count in sorted(rules.items()):
            lines.append(f"- `{rule}`: {count}")
    else:
        lines.append("- (no findings)")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if not report.findings:
        lines.append("No findings — audit-safe.")
    for f in sorted(report.findings, key=lambda x: (x.severity, x.path, x.line)):
        lines.append(f"### `{f.severity}` · `{f.rule}` · {f.path}:{f.line}")
        lines.append("")
        lines.append(f.message)
        if f.snippet:
            lines.append("")
            lines.append("```")
            lines.append(f.snippet)
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="SGC audit-driven coupling lint")
    parser.add_argument(
        "--addons-path", action="append", default=[],
        help="Repeat to scan multiple addon paths. May be relative.",
    )
    parser.add_argument(
        "--include-path", action="append", default=[],
        help="Repeat to scan non-addon directories (e.g. the template).",
    )
    parser.add_argument(
        "--report-md", default="",
        help="Write a markdown report to this path (in addition to stdout).",
    )
    parser.add_argument(
        "--report-json", default="",
        help="Write a JSON report to this path.",
    )
    parser.add_argument(
        "--fail-on-findings", action="store_true",
        help="Exit non-zero if at least one hard finding is present.",
    )
    parser.add_argument(
        "--exclude", action="append", default=[],
        help="Repeat to add directory/file exclusion patterns (regex).",
    )
    args = parser.parse_args(argv)

    if not args.addons_path and not args.include_path:
        print("No paths provided. Use --addons-path and/or --include-path.",
              file=sys.stderr)
        return 2

    excludes = [re.compile(p) for p in (args.exclude + DEFAULT_EXCLUDES)]
    roots = [Path(p).resolve() for p in (args.addons_path + args.include_path)]
    for r in roots:
        if not r.exists():
            print(f"Skipping non-existent path: {r}", file=sys.stderr)

    report = run_audit([r for r in roots if r.exists()], excludes)

    # Always emit a machine-readable report.
    print(json.dumps({
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "file_count": report.file_count,
        "hard_count": report.hard_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "findings": [f.to_dict() for f in report.findings],
    }, indent=2))

    if args.report_json:
        Path(args.report_json).write_text(json.dumps({
            "started_at": report.started_at,
            "finished_at": report.finished_at,
            "file_count": report.file_count,
            "hard_count": report.hard_count,
            "warning_count": report.warning_count,
            "info_count": report.info_count,
            "findings": [f.to_dict() for f in report.findings],
        }, indent=2), encoding="utf-8")

    if args.report_md:
        Path(args.report_md).write_text(render_markdown(report), encoding="utf-8")

    if args.fail_on_findings and report.hard_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
