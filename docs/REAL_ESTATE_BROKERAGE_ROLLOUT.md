# Real-estate brokerage + full-ERP rollout playbook

> 🧠 **From Hindsight memory** — this playbook is the **operational** companion to
> `audit_out/FULL_AUDIT_SUMMARY_REPORT.md`. The audit produces the evidence; this
> playbook produces the deployment plan.

This document maps **eight rollout phases** for any real-estate brokerage tenant
(brokerage-core, offplan-rental, construction-management, full ERP). Each phase
is gated, has a clear in/out criterion, and maps to specific SGC modules plus
the audit's blocker inventory.

The reusable template that walks every tenant through this playbook is
[`sgc_realestate_brokerage_template/`](../sgc_realestate_brokerage_template/README.md).

---

## Phase 0 — Provenance gate

**Goal**: before any client-facing work begins, every addon on the candidate
addon-path has its provenance known.

**In**:

1. `python tools/audit_coupling_lint.py --addons-path ./addons \
        --include-path ./sgc_realestate_brokerage_template \
        --report-md docs/audit/lint_report.md --fail-on-findings` → exits 0.
2. Every addon in `addons/` has a row in `docs/audit/MODULE_PROVENANCE.md`.
3. No addon on the candidate path is in `30_QUARANTINE/` *unless* a `legal-hold/`
   branch resolution is attached to a SGC founder sign-off.

**Out**:

- `lint_report.md` published to `docs/audit/`.
- `MODULE_PROVENANCE.md` updated to reflect any addon-path changes.
- All quarantine markers (R1-R18) honoured.

**Failure modes**:

- ⚠️ Any held addon appears on the candidate path → **STOP**.
- ⚠️ Lint reports a hard finding → **STOP**, resolve in `30_QUARANTINE/` and
  `docs/audit/HARDCODED_COUPLING.md`, re-run.

---

## Phase 1 — Foundation (always-on addons)

**Goal**: install the base addon-path; no tenant data yet.

**Addons (canonical)**: `crm`, `account`, `sale_management`, `contacts`,
`website`, `hr`, `mail`.

**Addons (SGC building blocks)**: `aml_compliance`, `kyc_management`.

**Mandatory**:

- Configure `web.base.url` per tenant (≥ `https://` in any non-internal env).
- Create at least one `res.users` with no superuser rights; restrict superuser
  access to the deployment break-glass key.

**Out**:

- Audit lint run with `--fail-on-findings` → 0 findings.
- A demo tenant record created in `sgc.brokerage.tenant` with state `draft`.

---

## Phase 2 — Vertical core (brokerage foundation)

**Goal**: enable the **brokerage core** kit.

**Addons**: `sgc_appraisal`, `sgc_deals_management`, `sgc_commission`,
`sgc_dynamic_financial_report`, `report_xlsx`, optionally
`sgc_design_tokens` + `sgc_ui_brand_palette`.

**Excludes**: `ks_dynamic_financial_report` (HELD, Ksolves provenance),
`sgc_crm_dashboard` (HELD, Cybrosys fingerprint), `sgc_lead_scoring` (HELD,
multi-tenant SQL constraint broken).

**In**:

1. `sgc_realestate_brokerage_template/data/realestate_growth_defaults.xml`
   references each addon: the kit `brokerage_core` is installed.
2. Per-tenant:
   - `enable_core = True`
   - `kit_id` = `brokerage_core`
3. `tools/audit_coupling_lint.py` re-run with the vertical-core addon path →
   0 findings.

**Out**:

- A listing can be created and viewed in the broker portal.
- A deal can move from `draft` → `won` and generate a `sale.order`.
- A `commission` row is created automatically off `sale.order`.
- `sgc_dynamic_financial_report` renders the GL report for the tenant.

---

## Phase 3 — Compliance (AML + KYC)

**Goal**: full audit-driven compliance plumbing per tenant.

**Addons**: `aml_compliance`, `kyc_management`. (Already in phase 1, but
the per-tenant configuration is phase-3 work.)

**Audit-driven requirements**:

| Block | Action |
|---|---|
| M1 (URLs) | Set `web.base.url`, `sgc.brokerage.tenant.<code>.base_url`. |
| M1 (emails) | Set `contact_email`, `compliance_email` per tenant. |
| M3 (mail) | Confirm `kyc_management/data/portal_templates.xml` has no hardcoded `@osusproperties.com`. |
| M3 (incoming mail) | Confirm `ir.mail_server` rows were created via wizard, not XML data. |
| M5 (workspace) | If `sgc_meeting_ai` is installed, set `sgc.meeting_ai.workspace_account`. |
| M0 (company) | Per-tenant `company_id` set, no `company_id = 1` literals. |

**Out**:

- `sgc.brokerage.tenant._preflight_check()` returns `ok=True` for every active
  tenant.
- An end-to-end AML alert can be raised on a synthetic suspect profile.
- A KYC record can be created, exported, and re-imported across tenants
  (proves the per-tenant `company_id` is clean).

---

## Phase 4 — Growth (CRM + broker portal + marketing)

**Goal**: enable the **growth** kit.

**Addons**: `sgc_brochure_leadcapture`, `sgc_scroll_hero_homepage`,
`sgc_realestate_website` (when provenance clears),
`sgc_ui_brand_palette`, `sgc_design_tokens`.

**Audit considerations**:

- `sgc_scroll_hero_*` modules bundle GSAP / ScrollTrigger. This is **third-party
  bundling**, not theft (per audit Phase 6). Maintain a `THIRD_PARTY` file in each
  `static/` that lists the version and license.
- `sgc_realestate_website` is **UNRESOLVED** per `MODULE_PROVENANCE.md` — enable
  only after the per-vertical provenance check.

**In**:

- `enable_growth = True`
- `kit_id` ∈ `{brokerage_core, growth}` (kit selection is multi-valued; select
  whichever fits the tenant's vertical).

**Out**:

- A brochure landing page can be served from a published website.
- A brochure-submission creates a `crm.lead` with the right `team_id` and
  `tag_ids`.
- `sgc_realestate_website` (once cleared) becomes the broker-facing portal.

---

## Phase 5 — Offplan rental + construction (vertical scale)

**Goal**: enable the **offplan_rental** kit, optionally the held
`sgc_construction_management` module (after resolution).

**Addons**:

- Always-on: `sgc_offplan_rental_property_management` (~21,814 LOC; the single
  largest module in the estate).
- Held: `sgc_construction_management` (`30_QUARANTINE/sgc_construction_management.md`).
- Staging-only: `sgc_rental_management` (`30_QUARANTINE/sgc_rental_management.md`).

**Audit considerations**:

- OPR (offplan rental) is the largest single module — its file-by-file
  provenance was unstarted per `phase10d+/` TODO. **Treat as
  UNRESOLVED**, not as `ORIGINAL_SGC`.
- Construction is HELD (R16-R18). Phase-5 enablement is blocked unless founder
  sign-off is on file at `docs/audit/MODULE_PROVENANCE.md`.

**Out**:

- OPR is installed without triggering the OPR-version-gate pass-criterion
  bug (see `30_QUARANTINE/README.md` and `audit_out/`).
- Construction: only enabled post-resolution.

---

## Phase 6 — ERP-rollout (HR, payroll, financials, reports)

**Goal**: enable the **ERP** layer.

**Addons**: `eh_uae_payroll_wps`, `hr_payroll_community`, optionally
`uae_einvoice_core`, `report_xlsx`, `account_statement_import_*`,
`account_statement_*`, `module_generator_v19` (scaffold-only).

**Audit considerations**:

- `eh_uae_payroll_wps` is a UAE-specific payroll module with `wizard/` and
  `data/` parts; verify compliance with `hr_payroll_community` base.
- `hr_payroll_community` carries `.omc/` operational state — must not be
  shipped to a customer without that directory stripped.

**Out**:

- Payslip can be generated and posted.
- Bank statement can be imported (`account_statement_import_*`).
- Invoice can be e-invoiced via `uae_einvoice_core`.

---

## Phase 7 — Multi-tenant hardening (audit M1/M3/M5)

**Goal**: every tenant passes the audit preflight.

**Action**:

```bash
# For each tenant DB:
odoo shell -d <tenant_db> --addons-path=./addons,./sgc_realestate_brokerage_template \
    --no-http <<'EOF'
tenants = env['sgc.brokerage.tenant'].search([('state','=','onboarding')])
for t in tenants:
    r = t._preflight_check()
    print(t.code, r)
EOF
```

**Per-tenant envelope**:

- `web.base.url` set, no localhost fallback anywhere.
- `contact_email`, `compliance_email`, `workspace_account` set.
- No active `ir.mail_server` with `smtp_host in ('localhost', '127.0.0.1', '0.0.0.0')`.
- No `ir.mail_server` or `fetchmail.server` rows created by `<record>` in any
  shipped XML data.

**Out**:

- All on-boarding tenants move to `state=active`.
- Audit lint report (`docs/audit/lint_report.md`) regenerated with 0
  findings across all tenant addon paths.

---

## Phase 8 — Audit closure + lender-pack re-derivation

**Goal**: keep the audit's headline figures honest.

**Action**:

```bash
# Regenerate the lint report (defence-in-depth)
python tools/audit_coupling_lint.py \
    --addons-path ./addons \
    --include-path ./sgc_realestate_brokerage_template \
    --report-md docs/audit/lint_report.md
```

**Per-phase deliverables**:

| Phase | Deliverable | File |
|---|---|---|
| 0 | Provenance index | `docs/audit/MODULE_PROVENANCE.md` |
| 0 | Lint pass | `docs/audit/lint_report.md` |
| 2 | Brokerage kit | `sgc_realestate_brokerage_template/data/realestate_growth_defaults.xml` (`brokerage_core`) |
| 3 | Preflight pass | `sgc.brokerage.tenant._preflight_check()` |
| 4 | Growth kit | `sgc_realestate_brokerage_template/data/realestate_growth_defaults.xml` (`growth`) |
| 5 | Offplan kit | same file (`offplan_rental`) |
| 6 | ERP rollup | sibling addon `sgc_realestate_brokerage_erp_rollout` |
| 7 | Multi-tenant preflight | `docs/audit/MULTI_TENANT_BLOCKERS.md` |
| 8 | Closure log | `docs/audit/SYNC_*.md` |

---

## Appendix A — KPIs and acceptance criteria

A real-estate brokerage rollout is **accepted** when:

1. **Phase 0 lint passes**: 0 hard findings on the addon path the tenant runs.
2. **Phase 3 preflight passes**: every active tenant returns `ok=True`.
3. **Phase 6 ERP-kit enables** without traceback on a clean DB.
4. **Phase 8 closure log** is signed by both engineering + counsel.
5. **No held module is on the candidate addon path.** A held module appearing
   in `depends` of any addon shipped to a customer is a contractual event, not
   a deploy bug.

## Appendix B — Who owns each phase

| Phase | Engineering | Counsel | SGC founder |
|---|---|---|---|
| 0 | ✅ | ✅ | ✅ |
| 1 | ✅ | — | — |
| 2 | ✅ | — | ✅ (sign-off on kit) |
| 3 | ✅ | ✅ (mail-records review) | ✅ |
| 4 | ✅ | — | ✅ |
| 5 | ✅ | ✅ (OPR + construction) | ✅ |
| 6 | ✅ | — | — |
| 7 | ✅ | — | — |
| 8 | ✅ | ✅ (closure review) | ✅ |

## Appendix C — Risks the audit did not yet resolve

These are open items that block a *fully-clean* rollout, listed for the record:

1. **Synconics `bi_dashboard`** — suspected 2nd rebadge (audit Phase 9 §9).
2. **`le_sale_type`** — 5 of its "passing" tests were very likely never
   actually executed (Phase 9-B follow-up).
3. **Public-registry check** for the remaining 20 ORIGINAL_SGC product
   modules — only 4 were checked; the 35,212-LOC figure is a floor, not a
   cleared number.
4. **`/opt/staging/sgc_sales_playbook.tar`** — never extracted.
5. **`project_hr_skills`** — Enterprise licence exposure with no subscription
   evidence, installed on 4/6 databases.

See `audit_out/FULL_AUDIT_SUMMARY_REPORT.md` §15 for the full open-items
list and the audit's own final conclusions.
