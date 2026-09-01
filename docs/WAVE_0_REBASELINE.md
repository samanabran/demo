# Wave 0 — Rebaseline Deliverable

> **Programme:** Real-Estate Workflow Gap Closure
> **Authoritative reference:** `docs/AGENT_BRIEF_REAL_ESTATE_WORKFLOW_GAP_CLOSURE.md`
> **Companion:** `docs/REAL_ESTATE_WORKFLOW_MISALIGNMENT.md`
> **Status of this document:** DRAFT, awaiting §11 answers and user sign-off before Wave 1 may begin.

This deliverable satisfies §3 of the brief. No code beyond the rules-pack skeleton may be written until the §11 questions in §4 below are answered.

---

## §3.1 — Corrected gap register (strict taxonomy)

### Taxonomy applied

| Status | Definition |
|---|---|
| `CLOSED` | Control exists **and is enforced at runtime** and has a passing test |
| `PARTIAL` | Data structures or reports exist; enforcement does not |
| `OPEN` | Neither data nor enforcement exists |
| `BLOCKED` | Closure depends on a HELD or UNRESOLVED module |

### The 26-gap register — one status per row

| # | Gap | Sev (per brief) | Status | Reason / pointer |
|---|---|---|---|---|
| **G1** | Screening began only after deal confirmation, but a holding deposit was taken earlier | Critical | **PARTIAL** | `kyc_management` + `aml_compliance` exist. No pre-money trigger wired into reservation/booking/payment confirmation. The guard does not exist in code. |
| **G2** | Only the buyer or tenant was screened; no party graph | Critical | **PARTIAL** | One KYC application per `res.partner`. No recursive traversal across co-buyer, beneficial owner, POA holder, third-party payer. |
| **G3** | Rejected/escalated cases dead-ended | Critical | **PARTIAL** | Filing lifecycle exists (`goaml_report_views.xml`, `goaml_filing_wizard_views.xml`, `investigation_case_views.xml`). Tipping-off suppression not enforced at the notification layer. No DLQ. |
| **G4** | No SoF, no objective cash / virtual-asset threshold trigger | Critical | **PARTIAL** | AED 55,000 hard-coded in `aml_compliance/reports/goaml_report_print.xml`. No automatic fire-on-facts hook on payment confirmation. |
| **G5** | One identical checklist for every client | High | **CLOSED** | `aml_compliance` Phase 1 risk engine (`risk_factor_data.xml`, `risk_assessment_views.xml`) with Low / Medium / High / Very High tiers, FATF jurisdictions, PEP, EDD triggers. |
| **G6** | Document chase had no attempt limit / SLA | High | **OPEN** | `kyc_management` approval workflow exists. No visible `attempts_exhausted → case_suspended` counter. No scheduled SLA-escalation cron. |
| **G7** | Payment reminder loop was infinite | High | **OPEN** | Recurring invoicing exists. No dunning ladder with capped retries → legal / forfeit / write-off exits. |
| **G8** | Commission paid with no hold-back gate | High | **OPEN** | `sgc_commission` 5-state lifecycle. Three-condition release gate (funds cleared · registration complete · compliance still approved) not implemented. No agent-visible pending state. |
| **G9** | Sale closing had no title / encumbrance / clearance / registration step | High | **PARTIAL** | SPA templates exist (`sales_purchase_agreement_template.xml`). No conditions register with owners + deadlines. No seller-obligations gate. |
| **G10** | Listings published with no permit step / de-listing | High | **PARTIAL** | RERA Form A view + portal publish wizard exist. No hard system-block on publish without permit. No de-listing SLA. |
| **G11** | Leases with no statutory registration / index / notice logic | High | **PARTIAL** | Rent contract views + templates exist. No 90-day statutory notice engine. No Ejari registration gate. No Smart Rental Index / RERA slab modelling. |
| **G12** | Developer side absent | High | **PARTIAL** | Offplan installment plans + SPA template exist inside OPR. Full developer lane (project escrow dedicated, sales permit, Oqood, default ladder, resale, handover) not modelled. OPR itself is UNRESOLVED provenance. |
| **G13** | No demand feedback into pricing / marketing / launch | High | **BLOCKED** | No decision engine exists. Closest match `sgc_lead_scoring` is HELD per `30_QUARANTINE/sgc_lead_scoring.md`. Cannot close without resolving the hold or building the engine independently. |
| **G14** | No service-charge / jointly-owned-property handling | Medium | **OPEN** | No Mollak module. No RERA-approved budget gate. No segregated funds. No reserve / sinking fund. |
| **G15** | Integration failures had no lane | Medium | **OPEN** | No DLQ. No retry-with-backoff. No manual-failover for screening-provider outage. The most dangerous failure mode (silent-clear) is unaddressed. |
| **G16** | No terminal states / retention clocks | Medium → **HIGH** (per Directive Four) | **PARTIAL** | `sgc.brokerage.incident` exists as event log. 5-year retention not enforced per record type. Decree-Law 10/2025 penalties (up to AED 100m) make retention the evidentiary backbone. |
| **G17** | Two arrows created unresolvable cycles | Medium | **CLOSED** | Tenant state machine `draft → onboarding → active` with `_preflight_check()` + `action_activate()`. `sgc_commission_reconcile/security/ir_rule_tenant_isolation.xml` enforces tenant boundaries. |
| **G18** | No agent licence / dual-agency / conflict check | Medium | **OPEN** | No `hr.employee`-level RERA broker permit / dual-agency conflict field. No licence-validity gate at lead assignment. |
| **G19** | No emergency maintenance lane | Medium | **PARTIAL** | Odoo `maintenance` extension exists. No explicit emergency classifier (fire/gas/flood/electrical/security) with bypass-approval authority. |
| **G20** | Auto-deduplication with no arbitration | Medium | **PARTIAL** | `crm_lead_ingestion_hub` dedupe logic exists. Human arbitration step (side-by-side merge/link/keep-separate) not a first-class state. Survivorship rules for source/consent/attribution not explicit. |
| **G21** | Proliferation Financing not modelled | Critical | **OPEN** | `aml_compliance` has no PF dimension. Cabinet Resolution 134/2025 requires PF in EWRA, policies, screening, risk profiling, EDD. Schema change to the risk engine, not a label change. |
| **G22** | UBO definition is stale (nominees cannot be deemed UBOs) | High | **OPEN** | Current `res.partner` / party model treats nominees as eligible UBOs by default. Must correct under 2025 Executive Regulations. |
| **G23** | No 15-working-day BO update clock | High | **OPEN** | No scheduled task for BO / nominee information updates within 15 working days of any identified change. |
| **G24** | Regulatory rules pack not abstracted | Critical (upgraded from Medium) | **OPEN** | AED 55,000 hard-coded in `aml_compliance/reports/goaml_report_print.xml`. Hard-coded constants block multi-emirate operation and Q4 2025 law change. |
| **G25** | Rent-review reference is stale (Smart Rental Index vs RERA slab) | Medium | **OPEN** | C11 PM15 does not distinguish Smart Rental Index (building-level AI, live Jan 2025) from RERA slab (permitted percentage). Two distinct inputs must be modelled. |
| **G26** | E-invoicing readiness unassessed | High (time-critical) | **OPEN** | UAE e-invoicing voluntary phase opened 1 Jul 2026; guidance set ASP appointment by 31 Jul 2026 and go-live 1 Jan 2027 for revenue ≥ AED 50m. `uae_einvoice_core` exists in Phase 6. Current FTA position must be verified within 5 working days. |

### Closure-count comparison (corrected)

| Status | Original count (misalignment doc) | **Corrected count** |
|---|---|---|
| `CLOSED` | 3 | **2** |
| `PARTIAL` | 11 | **11** |
| `OPEN` | 6 | **12** |
| `BLOCKED` | 0 (implicit) | **1** |
| `TOTAL` | 20 | **26** |

The headline is materially worse, as the brief predicted. Of the four Critical gaps (G1–G4), **all four remain PARTIAL**. The brief's added gaps (G21, G24) add two more Criticals, both OPEN. Of the six High gaps, **four are OPEN**, **four are PARTIAL**, **one is BLOCKED**, **zero are CLOSED**. This is the real estate of the estate.

---

## §3.2 — Added gaps (G21–G26)

All six added gaps are included in the register above with full status and reason. Each was sourced from the brief §3.2; none were carried over from prior documents.

---

## §3.3 — `check_company` finding verification

**File reviewed:** `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py` lines 38–60.

**Finding: NOT a multi-tenant data leak.** The comment at lines 46–53 of `sgc_brokerage_tenant.py` is technically correct. The Odoo `check_company=True` field decorator generates a domain clause that references the comodel's `company_id` field. Since `res.company` does not have a `company_id` field on itself (it IS the company), applying `check_company=True` on a `Many2one("res.company")` field would raise:

```
Unknown field "res.company.company_id" in domain of python field 'company_id'
```

This was correctly verified via a clean-room install test (2026-08-31), per the comment in the file. The `company_id` field on lines 54–56 remains:

```python
company_id = fields.Many2one(
    "res.company", required=True, default=lambda s: s.env.company,
)
```

— `required=True`, defaulted to `env.company`. Tenant scoping through `company_id` is **preserved**. Other Many2one fields on the same model (e.g. `partner_id` at line 42–45) correctly carry `check_company=True` because `res.partner` *does* have a `company_id` field.

**Action:** No change required. The comment should remain as a guard against re-introducing the bad decorator.

**Status:** CLOSED (verification step, not a gap closure).

---

## §3.4 — OPR provenance decision

**Module:** `sgc_offplan_rental_property_management`, 21,814 LOC (largest single module in the estate).

**Provenance class:** UNRESOLVED per `docs/audit/MODULE_PROVENANCE.md` line 31. File-by-file provenance audit was unstarted per the `phase10d+/` TODO at the time of writing. The module is correctly excluded from the brokerage template's `depends` (`sgc_realestate_brokerage_template/__manifest__.py` lines 30–39) but is referenced via the `enable_offplan` flag and is the practical home of five gap closures in the misalignment document (G7, G9, G10, G11, G12).

**Decision (per brief §4 Directive One):** **Do not write new logic inside OPR.** All five gap closures that name OPR as the home will be implemented in clean sibling modules that depend on OPR and inject behaviour through inheritance, overrides, and constraints. The proposed sibling mapping is in §4 of the brief and is reproduced below for completeness.

| New module | Closes | Inherits from / depends on |
|---|---|---|
| `sgc_collections_ladder` | G7 | `account` (and OPR models for invoicing record references) |
| `sgc_transaction_conditions` | G9, G11, G25 | `sale`, OPR contract models |
| `sgc_listing_compliance` | G10 | OPR property model, `portal` |
| `sgc_developer_lane` | G12 | OPR offplan models, `account` |
| `sgc_jointly_owned_property` | G14 | OPR property model, `account` |

**OPR file-by-file provenance audit runs in parallel as its own workstream. It does not sit on the critical path.** When the audit completes, gap closures built as siblings remain valid (R2-style independence).

---

## §4 — §11 questions — must be answered before Wave 1

Per brief §11, do not guess. Each answer changes the architecture. Question Q8 has been verified as **CLEARED** (see §3 below) and does not need to be re-asked.

These questions are now routed to the user via structured prompts. Wave 1 cannot start until at minimum Q1, Q2, Q3, Q5, Q7 are answered.

---

## §5 — Wave 0 deliverable summary

| § | Deliverable | Status |
|---|---|---|
| §3.1 | Corrected gap register with strict taxonomy, one status per gap | **DELIVERED** |
| §3.2 | Added G21–G26 with severities, statuses, reasons | **DELIVERED** |
| §3.3 | `check_company` finding verified — not a data leak, no action | **DELIVERED** |
| §3.4 | OPR provenance decision recorded — sibling modules only | **DELIVERED** |
| §11 | §11 questions to user — must be answered before Wave 1 | **PENDING** |

---

## §7 — §11 answers (recorded, signed off by user)

| Q | Question | Answer | Architectural consequence |
|---|---|---|---|
| Q1 | Jurisdiction scope for phase one | **Dubai only** | Rules pack ships with Dubai (DLD / RERA / Ejari / Trakheesi / Mollak) populated. Abu Dhabi and free-zone jurisdictions are deferred (not in `depends` of Wave 1 modules, present as documented empty placeholder rows in the rules pack with `valid_from=null`). |
| Q2 | Off-plan developer revenue real now? | **Real now — move developer lane to Wave 3** | `sgc_developer_lane` moves up from Wave 4 to Wave 3. The build sequence is renumbered: Wave 3 picks up items 26 + 27 in addition to the transaction spine. Wave 4 is reduced to Owners Association and Mollak. |
| Q3 | Is Owners Association in scope? | **In scope — add Mollak module in Wave 4** | `sgc_jointly_owned_property` is in scope, sibling of OPR. New kit option added. Wave 4 now reads: "Jointly Owned Property + Mollak + Owners Association kit". |
| Q4 | Odoo version and edition | **Odoo 19.0 Community** | All Wave 1+ modules target v19 Community. `project_hr_skills` Enterprise exposure is irrelevant — but verify no live DB has it installed before signing off Wave 1. |
| Q5 | Screening providers | **One provider, no fallback yet** | Wave 1 still builds `INDETERMINATE → DLQ + manual fallback` (the Wave 1 exit gate). Provider-name is not required to satisfy the gate — only the failure-detection path. The secondary-provider integration is deferred to a follow-on wave. **Action item:** name the single provider before Wave 2 builds the screening call. |
| Q6 | Annual revenue vs AED 50m | **Under AED 50m — voluntary only** | `uae_einvoice_core` ships as opt-in in Wave 6 / Phase 6. G26 reduces to readiness preparation. No go-live date pressure. |
| Q7 | Compliance Officer / MLRO of record | **NO APPOINTED MLRO** | **HARD BLOCKER** — surfaced immediately per brief §9. Wave 2 cannot be signed off without a named MLRO (reviewer-independence is a role assignment, not a code feature). All technical work in Wave 2 may proceed; sign-off is blocked until MLRO is appointed and goAML-registered. |
| Q8 | `sgc_deals_management` provenance | **CLEARED — SGC_OWNED (`Phase 9` baseline)** | Verified via `docs/audit/MODULE_PROVENANCE.md` line 34. Safe to wire into. No further action. |
| Q9 | REAR filing deadline | **UNVERIFIED** | Rules pack ships with `deadline_days=null` and a visible `UNVERIFIED` flag. The technical auto-trigger fires on facts regardless of the deadline value. Wave 2 exit gate requires resolution before go-live. |

### Architecture changes locked in by these answers

1. **Single jurisdiction at start** — Rules pack data model is generic (jurisdiction-scoped, effective-dated) but only Dubai rows are populated in Wave 1.
2. **Developer lane → Wave 3** — Re-numbered sequence below.
3. **Mollak → Wave 4** — `sgc_jointly_owned_property` is built before `sgc_demand_engine`.
4. **Screening failover shape** — Wave 1 builds the *detection* path, not the *secondary-provider integration*. Provider name to be confirmed before Wave 2.
5. **MLRO block** — Wave 2 sign-off deferred until appointed.

### Renumbered build sequence (after Q1–Q9 answers)

| Wave | Items | Description |
|---|---|---|
| **Wave 0** | §3 deliverables | **COMPLETE.** |
| **Wave 1** — Platform spine | 1, 2, 3, 4 | `sgc_regulatory_rules_pack`, `sgc_process_control`, retention framework, segregation of duties. Exit gate: failed screening → DLQ + alert + visibly-not-clear. |
| **Wave 2** — Licence protection | 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 | Party graph, PF, fail-closed guard, threshold trigger, screening fail-detection, tipping-off suppression, bounded document chase, approved-with-conditions, BO update clock, agent licence gate, hard publish block. Exit gate: deposit, contract, advertisement cannot proceed without clearance. **Sign-off blocked by Q7 (no MLRO).** |
| **Wave 3** — Transaction spine + recurring revenue + developer lane | 17, 18, 19, 20, 21, 22, 23, 24, 25, **26 (moved up from Wave 4)** | Conditions register, seller obligations, Ejari gate, 90-day notice + SRI/RERA slab, dunning ladder, mixed-line tax, three-condition commission gate, clawback, emergency maintenance, dedupe arbitration, **developer lane** (project registration, dedicated escrow, sales permit, Oqood, default ladder, resale, handover). |
| **Wave 4** — Segment scale | **27 (Mollak)** | `sgc_jointly_owned_property` — budget-then-bill, segregated funds, reserve / sinking fund, special levy, arrears blocking transfer. Owners Association kit added. |
| **Wave 5** — Demand intelligence | 28 | `sgc_demand_engine` — signal aggregation, decision rules, outcome measurement, threshold tuning. Last by design. |
| Wave 6 — ERP rollup | (separate programme) | `eh_uae_payroll_wps`, `hr_payroll_community`, `uae_einvoice_core` (voluntary phase), `account_statement_import_*`. |

---

## §8 — Immediate flags (per brief §9)

These are raised the moment they are identified, not held for the weekly report:

| Flag | Severity | Owner | Action |
|---|---|---|---|
| **No appointed MLRO / Compliance Officer of record (Q7)** | **HIGH** — Wave 2 sign-off cannot proceed | Programme lead → user | User must appoint an MLRO and confirm goAML registration before Wave 2 sign-off. Technical Wave 2 work proceeds in parallel. |
| **REAR filing deadline UNVERIFIED (Q9)** | **HIGH** — rules pack cannot carry an unverified deadline | Compliance lead → user → MoET/FIU | Direct confirmation required with MoET or FIU. Ship rules pack with `deadline_days=null` + `UNVERIFIED` flag in the interim. |
| **`sgc_offplan_rental_property_management` provenance UNRESOLVED** | **HIGH** — 21,814 LOC | Audit workstream (parallel) | File-by-file provenance audit runs in parallel, not on critical path. |
| **OPR render-blocking defects (template references 3 QWeb views that don't exist)** | **HIGH** | Dev team | Per `MERGE_NOTES.md` lines 32–33: `rental_listings`, `rental_detail`, `thank_you` templates don't exist. Inherited defect, not introduced by merge. Flagged for the dev team to fix in the source module — must be resolved before any OPR-dependent sibling ships to production. |
| **`project_hr_skills` Enterprise exposure (Q4 follow-up)** | **MEDIUM** | Audit | Confirm not installed on any DB the rules-pack sibling will touch. |
| **E-invoicing current FTA position (G26)** | **HIGH** (time-critical per brief) | Compliance lead | Verify within 5 working days. Mandatory only if Q6 answer were "at or above AED 50m" — but voluntary-phase guidance should still be reviewed. |

---

## §9 — Wave 0 closure

Wave 0 is **complete** pending user acknowledgement of this document. The next step is Wave 1 item 1: `sgc_regulatory_rules_pack`. Wave 1 may start immediately on the platform spine; Wave 2 work may proceed in parallel but its sign-off remains blocked by Q7.

---

## §6 — Provenance snapshot at end of Wave 0

| Module | Status | Notes |
|---|---|---|
| `sgc_realestate_brokerage_template` | SGC_OWNED | Reference template, cleared. |
| `aml_compliance` | SGC_OWNED | Strong foundation. Needs G21 PF schema change, G24 rules-pack migration. |
| `kyc_management` | SGC_OWNED | Workflow exists. Needs party graph (G2), bounded attempts (G6). |
| `sgc_commission` | UNRESOLVED | Phase 9 unstarted. Holds gate is in `sgc_commission_reconcile` which is cleared. |
| `sgc_commission_reconcile` | SGC_OWNED | Reconciliation layer. |
| `sgc_deals_management` | **SGC_OWNED** (`Phase 9` baseline) | **Confirmed CLEARED** per Q8 — safe to wire into. |
| `sgc_offplan_rental_property_management` | UNRESOLVED | Sibling-only pattern per Directive One. |
| `sgc_appraisal` | SGC_OWNED | |
| `sgc_assessment` | UNRESOLVED | Watch. |
| `sgc_dynamic_financial_report` | SGC_OWNED | |
| `sgc_executive_dashboard` | UNRESOLVED | Watch. |
| `crm_executive_dashboard` | UNRESOLVED | Watch. |
| `crm_lead_ingestion_hub` | UNRESOLVED | Watch. |
| `sgc_lead_scoring` | **HELD** | Cannot be in `depends` of anything new (R2). |
| `sgc_crm_dashboard` | **HELD** | Cannot be in `depends` (R2). |
| `sgc_construction_management` | **HELD** | Out of scope per C02 X1–X4. |
| `ks_dynamic_financial_report` | **HELD** | Cannot be in `depends` (R2). |
| `sgc_rental_management` | **HELD** (staging) | Merged into OPR. |
| `sgc_brochure_leadcapture` | SGC_OWNED | |
| `sgc_realestate_website` | UNRESOLVED | Watch. |
| `uae_einvoice_core` | (status unverified — out of Wave 0 scope, in Wave 6 / G26) | Verify in 5 working days per brief §6. |
