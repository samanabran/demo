# Multi-tenant blockers — audit-derived checklist

> 🧠 **From Hindsight memory** — the canonical blocker inventory is in
> `audit_out/multi_tenant_blockers.json` and `audit_out/coupling_findings.csv`.
> This file is the actionable checklist for the real-estate brokerage template.

The audit's blocker count is `total_evidenced_hours = 55` — explicitly a **floor**, not a ceiling. One class is unresolved (M4 below) and may add materially more.

## M3 — Incoming mail (24h) and recruitment fetchmail (6h) — **BLOCKING**

**Where**: `ir_mail_server` and `fetchmail_server` records tied to real named mailboxes (Zoho, Mailjet, Brevo, Resend, self-hosted Mailcow) — duplicated into any tenant DB.

**Where (recruitment)**: `sgc_recruitment_ai/data/fetchmail_data.xml` ships fixed incoming-mail credentials as XML data.

**Fix**:

```python
# pattern used across the audited modules
mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
# replaced by:
param = request.env['ir.config_parameter'].sudo().get_param('sgc.mail_server_id')
mail_server = request.env['ir.mail_server'].sudo().browse(int(param)) if param else None
```

**XML data fix** (`sgc_recruitment_ai/data/fetchmail_data.xml`):

```xml
<record id="fetchmail_recruitment_default" model="fetchmail.server">
    <field name="name">Recruitment — set per tenant via onboarding wizard</field>
    <field name="server">placeholder.invalid</field>
    <field name="port">993</field>
    <field name="active">0</field>  <!-- disabled by default — onboarding enables -->
</record>
```

## M5 — Hardcoded Google Workspace in meeting AI (16h) and lead-scoring unique constraint (2h) — **BLOCKING**

**Where**: `sgc_meeting_ai` assumes exactly one Google Workspace account (`crm@sgctech.ai`) platform-wide, referenced directly in code across 8+ locations. <!-- audit-lint: disable=tier1/email, tier1/meeting_ai_workspace -->

**Fix**:

```python
def _workspace_account(self):
    return self.env['ir.config_parameter'].sudo().get_param(
        'sgc.meeting_ai.workspace_account',
        default=False  # NO default — multi-tenant requires tenant-set value
    )
```

**Where**: `sgc_lead_scoring`'s `UNIQUE(is_default, company_id)` is architecturally wrong (see `30_QUARANTINE/sgc_lead_scoring.md`).

## M1 — Hardcoded localhost fallbacks (4h) and missing dependency (3h) — **DEGRADING**

**Where**: `http://localhost:8069` / `:8080` fallback defaults across 4 modules (`kyc_management`, `sgc_meeting_ai`, `sgc_video_conferencing`, `sgc_lead_scoring`). <!-- audit-lint: disable=tier1/localhost -->

**Fix**:

```python
def _base_url(self):
    return (
        self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        or self.env['ir.config_parameter'].sudo().get_param('sgc.default_base_url')
        or ''  # empty triggers operator-visible config error, not silent fallback
    )
```

**Where**: `resource_booking`'s `web_calendar_slot_duration` dependency lives outside the documented addon path.

## M4 — `company_id` gap (hours NULL, **OPEN**) — **COSMETIC + STRUCTURAL**

**Where**: 140–141 models across 27 modules (audit re-derived figure; refuted a prior 120/24 estimate). 193/187 tables carry `company_id` per database — broad signal only.

**What we can verify now without DB access**:

```python
# tools/audit_coupling_lint.py covers the static side of this; for the
# dynamic side, the audit's Phase 9-B re-statement schedule still applies.
```

## Pre-deploy gate (recommended)

Before any "real-estate brokerage" tenant goes live:

1. **M1** — run `python tools/audit_coupling_lint.py` and confirm 0 findings in the addon paths the tenant loads.
2. **M3** — confirm 0 active `ir_mail_server` / `fetchmail_server` records with hardcoded credentials in any shipped XML data.
3. **M5** — confirm tenant onboarding writes `sgc.meeting_ai.workspace_account` and `sgc.default_base_url` *before* first sale-order confirmation.
4. **M4** — open a tracking ticket for each model flagged in audit's `q18_company_scoped_tables.csv`. Triage is owner-discretionary; closure requires a per-model signed verdict (not a global one).

## Audit lint tool

```bash
python tools/audit_coupling_lint.py \
    --addons-path ./addons \
    --report-md docs/audit/lint_report.md
```

The tool flags:

- Hardcoded `@*.com` / `@*.ai` email addresses in Python + XML.
- Hardcoded `http(s)://localhost:*` URLs in Python + XML.
- Hardcoded `<record model="ir.mail.server">` / `<record model="fetchmail.server">` in any XML data file.
- References to `sgctech.ai`, `sgc tech ai`, `osusproperties.com` in any addon file.
- References to `crm@sgctech.ai` in any `ir.config_parameter` default. <!-- audit-lint: disable=tier1/email, tier1/meeting_ai_workspace -->
- References to non-current `defaults` in `__manifest__.py` `installable`/`auto_install` (matches the `ksolves_derivation` tamper pattern).

The lint tool is **defence-in-depth**, not a substitute for review. It catches the patterns Phase 9 found; it does not catch patterns it has never seen.
