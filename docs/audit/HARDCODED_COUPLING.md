# Hardcoded coupling — audit-derived inventory

> 🧠 **From Hindsight memory** — the canonical evidence lives in
> `audit_out/coupling_findings.csv` and `audit_out/coupling_findings.txt`.

This file captures what the audit found that **must be parameterised** before any client deployment, plus the file/line evidence trail.

## Tier 1 — hardcoded mailbox / tenant identity (BLOCKING)

| File | Pattern | Recommendation |
|---|---|---|
| `sgc_meeting_ai/**.py` (8+ locations) | `crm@sgctech.ai` (hardcoded) | Replace with `ir.config_parameter('sgc.meeting_ai.workspace_account')` <!-- audit-lint: disable=tier1/email, tier1/meeting_ai_workspace --> |
| `sgc_video_conferencing/views/**.xml` | `info@sgctech.ai` / `hr@sgctech.ai` / `careers@sgctech.ai` | Replace with `<t t-esc="request.env['ir.config_parameter'].get_param('sgc.contact_email')"/>` <!-- audit-lint: disable=tier1/email --> |
| `kyc_management/views/portal_templates.xml` | `compliance@osusproperties.com` (client's real compliance email) | Replace with `ir.config_parameter('kyc.compliance_email')` <!-- audit-lint: disable=tier1/email --> |
| `kyc_management/data/*.xml` (5 files) | `http://localhost:8069` / `http://localhost:8080` | Replace with `request.env['ir.config_parameter'].get_param('web.base.url', '')` <!-- audit-lint: disable=tier1/localhost --> |

## Tier 2 — hardcoded URLs that are not tenant but are fingerprint-y

| Pattern | Locations | Recommendation |
|---|---|---|
| `https://store.ksolves.com/...` | `ks_dynamic_financial_report/static/description/index.html` (Ksolves branding, untouched) | If module exits the hold, this branding belongs to Ksolves and **must not** be edited. |
| GSAP / ScrollTrigger headers (`Jack Doyle`) | Two `sgc_scroll_hero_*` modules | **Noise**: third-party library correctly bundled. The audit correctly classifies this as bundling, not theft. No action needed beyond a clear LICENCE/THIRD_PARTY file. |

## Tier 3 — fine-grained: per-file hard-coded coupling

The 234-row `audit_out/coupling_findings.csv` is the source of truth. The lint tool at `tools/audit_coupling_lint.py` reproduces this scan deterministically.

## Parameter naming convention

Every hardcoded value above should map to exactly one `ir.config_parameter` key. The naming convention is:

```
<addon_technical_name>.<purpose>[.subpurpose]
```

Examples:

- `sgc.mail_server_id`
- `sgc.default_base_url`
- `sgc.meeting_ai.workspace_account`
- `sgc.contact_email`
- `kyc.compliance_email`
- `webmail.fetchmail.recruitment.enabled` (default `False` until onboarding enables)

The `sgc_realestate_brokerage_template/__manifest__.py` ships a starter set of these in `data/ir_config_parameter_defaults.xml` so that a fresh tenant gets all defaults set to the **expected** placeholder values, not the shipped hardcoded ones.

## Resolution workflow

For each finding in this file:

1. Engineer adds the parameter to `data/ir_config_parameter_defaults.xml`.
2. Engineer replaces the hardcoded reference with an `ir.config_parameter().get_param(...)` lookup, with an explicit empty-string default (so missing config surfaces as a UI error, not a silent localhost fallback).
3. Engineer re-runs `python tools/audit_coupling_lint.py` and confirms the finding is gone.
4. Engineer adds the lint tool to the CI gating job (`tools/audit_coupling_lint.py --fail-on-findings`).
5. Counsel + engineer sign-off on the resolution in `phase10d+/resolution_log.md`.
