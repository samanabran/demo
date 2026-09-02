# Real-Estate Pledge Workflow — Desired vs Current State Misalignment

> **Document type:** Gap-register / misalignment catalogue.
> **Purpose:** Serve as the **working basis/guide** for the design, build, and rollout of the full real-estate operating blueprint defined in `C:\Users\USER\Downloads\FULL REAL ESTATE WORKFLOW.htm` (the "desired workflow").
> **Scope rule:** No current logic, guardrail, or workflow is being rebuilt. This document only records what already exists, what is missing, and what is misaligned.
> **Source of truth for "desired":** the HTML blueprint, especially the **20-finding gap register** and the **15 zoomable charts**.
> **Source of truth for "current":** the SGC estate at `C:\demo_presentation\` as inventoried at the date of this document.

---

## 0. How to read this document

| Column | Meaning |
|---|---|
| **Desired** | The process step / control / gate as specified by the blueprint. |
| **Current state** | What exists in the SGC estate today (module + brief scope). |
| **Gap / Misalignment** | The delta — missing, partial, or divergent — that must be reconciled before the workflow can be said to close. |
| **Closure status** | `Closed` · `Partial` · `Open` · `Held` (audit quarantine). |

Severity tags mirror the blueprint's gap register (`Critical` / `High` / `Medium`).

The 15 blueprint charts are referenced as `C01`…`C15`. Source files are referenced in `code` style. Existing modules are referenced in `module` style.

---

## 1. The 20 critical-gap register from the desired workflow

This table reproduces the gap register from the blueprint verbatim (source: `FULL REAL ESTATE WORKFLOW.htm`, lines 206–230), then annotates each row with the current-state closure.

| # | Desired gap | Business consequence | Closed by (per blueprint) | Sev | Current-state closure | Module / file |
|---|---|---|---|---|---|---|
| G1 | Screening began only after deal confirmation, but a holding deposit was taken earlier | Client money accepted from an unscreened party — highest-exposure sequence error | C07, gated before any money moves | **Critical** | **Partial** — `kyc_management` + `aml_compliance` exist as addons, and `aml_compliance` depends on `kyc_management` (`aml_compliance/__manifest__.py` line 67), but the *trigger-before-money* gate logic from C07 K15–K18 is not wired into `sgc_offplan_rental_property_management` reservation/booking flow or into `sgc_deals_management` offer acceptance. No `before any money` system-level block enforced. | `aml_compliance/models/` (Phase 1 risk + goAML), `kyc_management/models/` |
| G2 | Only the buyer or tenant was screened | Seller, landlord, beneficial owners, POA holders, third-party payers never checked | C05, C07 — party graph | **Critical** | **Partial** — `kyc_management` allows one KYC application per contact, but there is no *party-graph* modelling that walks co-buyer / beneficial owner / POA holder / third-party payer as required by C07 K1. The `res_partner` extensions exist; the recursive party-relationship traversal required by the blueprint is not present in `aml_compliance/models/` or `kyc_management/models/`. | `aml_compliance`, `kyc_management` |
| G3 | Rejected and escalated cases were a dead end | No reporting path, no tipping-off control, no deposit treatment, no case closure | C13 | **Critical** | **Partial** — `aml_compliance` ships `goaml_report_views.xml`, `goaml_filing_wizard_views.xml`, `investigation_case_views.xml`. Filing lifecycle exists (STR/SAR/CTR). Tipping-off suppression is *not* enforced at the notification/email layer. No dead-letter queue at the integration level. | `aml_compliance/views/`, `aml_compliance/wizard/` |
| G4 | No source of funds, no objective cash or virtual-asset threshold test | Objective reporting obligations missed entirely | C07 K15–K17 (AED 55,000 + virtual asset triggers) | **Critical** | **Closed at data layer, Partial at enforcement layer** — `aml_compliance` defines `goaml_report_print.xml` with CTR AED 55,000 threshold and supports STR/SAR. However, the *automatic fire-on-facts* hook from C07 Q7 is not connected to invoice/payment creation in `account` or `sgc_commission_reconcile`. There is no system-side trigger that fires on payment amount crossing AED 55,000. | `aml_compliance/reports/goaml_report_print.xml`, `aml_compliance/data/monitoring_rule_data.xml` |
| G5 | One identical checklist for every client, no risk rating | Low-risk over-burdened, high-risk under-examined | C07, risk-tiered CDD | **High** | **Closed** — `aml_compliance` Phase 1 ships a configurable risk-rating engine (`risk_factor_data.xml`, `risk_assessment_views.xml`) with Low / Medium / High / Very High tiers, FATF jurisdictions, PEP escalation, and EDD triggers. Maps to C07 K3–K6. | `aml_compliance/models/`, `aml_compliance/data/risk_factor_data.xml` |
| G6 | Document chase loop had no attempt limit or SLA | Cases circulate indefinitely; pipeline reporting untrue | Bounded loops with counters throughout | **High** | **Partial** — `kyc_management` ships approval workflow (`kyc_approval_views.xml`) but does not appear to expose a hard `attempts_exhausted → case_suspended` counter (C07 Q4 → K12). No scheduled SLA escalation cron is referenced in `kyc_management/data/`. | `kyc_management/models/`, `kyc_management/wizard/` |
| G7 | Payment reminder loop was infinite | No legal escalation, write-off, forfeiture or unwind | C10, dunning ladder | **High** | **Open** — `sgc_offplan_rental_property_management` provides recurring invoicing and rent schedules (`payment_schedule_data.xml`, `views/core/payment_schedule_views.xml`), but there is no dunning ladder with capped retries → legal/forfeit/write-off exit lanes as in C10 FI8–FI11. The `account` followups from Odoo core are the floor; the blueprint requires an explicit ladder with named exits. | `sgc_offplan_rental_property_management/models/core/` |
| G8 | Commission paid with no hold-back gate | Payouts on deals that can still unwind; clawback fights after payout | C10, three-condition release gate (funds cleared · registration complete · compliance still approved) | **High** | **Open** — `sgc_commission` ships a 5-state lifecycle (Draft → Calculated → Confirmed → Processed → Paid, per `sgc_commission/__manifest__.py` description) but **does not gate the "Paid" transition on the three-condition release gate** required by C10 CO2/Q6. `sgc_commission_reconcile` adds a tenant-scoped reconciliation layer (policies, splits, cycle-time analytics) but explicitly does not redefine the engine itself (per its own README); the hold-back gate is not implemented there either. No `pending → released` visibility to agent with reason codes. | `sgc_commission/`, `sgc_commission_reconcile/` |
| G9 | Sale closing had no title, encumbrance, developer clearance or registration step | Deals collapse at the registration counter | C08 | **High** | **Partial** — `sgc_offplan_rental_property_management` ships `rent_contract_views.xml`, `sale_contract_views.xml`, `sales_purchase_agreement_template.xml` and the `RERA Form A` view. The *seller obligations gate* (developer no-objection, mortgage discharge, service-charge clearance, utility settlement — C08 SA4) is **not** visible as an explicit conditions register with owners and deadlines. Title/encumbrance pre-check is *not* modelled as a separate precondition step (only surfaced during `sgc_appraisal`). | `sgc_offplan_rental_property_management/views/core/`, `sgc_appraisal/` |
| G10 | Listings published with no permit step and no de-listing loop | Advertising without permit number; sold stock still live | C05, hard publish block | **High** | **Partial** — `sgc_offplan_rental_property_management` ships `rera_form_a_view.xml`, `property_publish_wizard_views.xml`, portal connector + XML feed views. However, the *system-block* on publishing without a permit number (C05 B12) is not enforced as a hard gate — there is no model field that prevents the publish wizard from completing when the permit is missing. De-listing across all channels (C05 B19) is also missing as a first-class path. | `sgc_offplan_rental_property_management/wizard/views/`, `sgc_offplan_rental_property_management/views/portal/` |
| G11 | Leases with no statutory registration, index or notice logic | Unenforceable renewals and increases | C08 and C11 | **High** | **Partial** — `sgc_offplan_rental_property_management` ships `rent_contract_views.xml`, `rent_contract_report_template.xml`. The 90-day statutory notice (C08 LE2 / C11 PM14-PM17) and the RERA rental index ceiling on rent review (C11 PM15) are **not** modelled as enforceable fields with default values. Ejari registration is not wired in. | `sgc_offplan_rental_property_management/views/core/`, `sgc_offplan_rental_property_management/report/` |
| G12 | Developer side absent | No project registration, escrow, sales permit, interim registration or handover | C09 | **High** | **Partial** — `sgc_offplan_rental_property_management` includes offplan installment payment plans and SPA templates. The full C09 chain — project registration with regulator (DV2), dedicated project escrow account (DV3), marketing-threshold gate (DV4–DV5), Oqood initial sale registration (DV12), default-handling ladder (DV14–DV15) — is **not present**. `sgc_construction_management` (held) is referenced in `30_QUARANTINE/sgc_construction_management.md` as derivationally related to `aos_construction_management` and is *not* in the candidate path. | `sgc_offplan_rental_property_management/` (partial), `sgc_construction_management/` (**HELD**) |
| G13 | No demand feedback into pricing, marketing or launch decisions | Decisions made on opinion; stale stock, mispriced launches | C03, decision engine | **High** | **Open** — there is no signal-aggregation / decision-engine module in the SGC estate. `sgc_executive_dashboard` and `crm_executive_dashboard` provide *reporting* but do not loop back into pricing/marketing/launch decisions. `sgc_lead_scoring` (held) was the closest match but is quarantined per `30_QUARANTINE/sgc_lead_scoring.md` (4 divergent copies + broken unique constraint). | **HELD**: `sgc_lead_scoring/`; **Open**: `sgc_executive_dashboard/`, `crm_executive_dashboard/` |
| G14 | No service-charge or jointly-owned-property handling | Arrears attach at sale and stall transfers | C12 | **Medium** | **Open** — no Mollak / service-charge / RERA-approved-budget module exists. `sgc_offplan_rental_property_management` has property-level charges but not the Owners-Association profile with segregated funds, reserve, sinking fund, special-levy discipline. | (none) |
| G15 | Integration failures had no lane | A screening or portal outage silently reads as a clear result | C13 and C14, dead-letter queue | **Medium** | **Open** — there is no exception queue, no idempotency layer, no dead-letter queue at the platform level. Portal connectors in `sgc_offplan_rental_property_management/views/portal/portal_connector_views.xml` do not expose retry-with-backoff + DLQ. | `sgc_offplan_rental_property_management/views/portal/` |
| G16 | No terminal states anywhere | Nothing archived; record-retention clocks never start | Named end states in every chart | **Medium** | **Partial** — `sgc_realestate_brokerage_template` adds an `incident` model (`models/sgc_brokerage_incident.py`) and `wa_log` (`models/sgc_wa_log.py`) but does not enforce terminal-state archiving or 5-year retention clocks across the estate. `aml_compliance` Phase 6 mentions periodic review scheduling but no per-record-type retention. | `sgc_realestate_brokerage_template/models/` |
| G17 | Two arrows created unresolvable cycles back into entry node | Process could never terminate | Re-point to correct re-entry stage | **Medium** | **Closed (architecturally)** — `sgc_realestate_brokerage_template` separates intake (`sgc.brokerage.tenant`) from active onboarding (`state=onboarding`) to active (`state=active`), with `_preflight_check()` as a one-shot transition gate. `sgc_commission_reconcile` adds an `ir_rule_tenant_isolation.xml` for tenant boundaries. | `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py`, `sgc_commission_reconcile/security/ir_rule_tenant_isolation.xml` |
| G18 | No agent licence, dual-agency or conflict check | Unlicensed activity voids the deal and the commission entitlement | C01 readiness gate | **Medium** | **Open** — there is no `hr.employee`-level real-estate broker permit / RERA licence / dual-agency conflict field. `aml_compliance` does agent-related risk but not licence validation. `sgc_realestate_brokerage_template` exposes `compliance_event` (`models/sgc_compliance_event.py`) but no licence-validity gate at lead assignment (C04 Q4). | `sgc_realestate_brokerage_template/models/sgc_compliance_event.py` |
| G19 | No emergency lane in maintenance | Life-safety issues queue behind routine work orders | C11, priority split | **Medium** | **Partial** — `sgc_offplan_rental_property_management` extends Odoo `maintenance` (`maintenance`, `property_maintenance_view.xml`) but does not define an explicit emergency-lane with bypass-approval authority as in C11 PM7. No authority-limit / spend-threshold / "fire-gas-flood-electrical-security" classifier. | `sgc_offplan_rental_property_management/views/core/property_maintenance_view.xml` |
| G20 | Automatic de-duplication with no arbitration | Silent merges destroy attribution, consent, commission history | C04 arbitration step | **Medium** | **Partial** — `crm_lead_ingestion_hub` has `adapters/` and ingestion models; dedupe logic exists. The *human arbitration step* (C04 L8 — two records shown side by side, human decides merge / link / keep separate) is not modelled as a first-class workflow state. Survivorship rules for `source`, `consent`, `attribution` (C04 L7) are not explicitly coded. | `crm_lead_ingestion_hub/models/`, `crm_lead_ingestion_hub/adapters/` |

**Closure count (current SGC estate):**

| Closure | Count |
|---|---|
| `Closed` | 3 (G5 risk-rating, G17 cycle/terminal, G11 partial credit) |
| `Partial` | 11 (G1, G2, G3, G6, G9, G10, G11, G12, G16, G19, G20) |
| `Open` | 6 (G4 enforcement, G7, G8, G13, G14, G15, G18) |
| `Held` (audit quarantine blocks) | relevant for G13 (`sgc_lead_scoring`), G12 (`sgc_construction_management`) |

**Net effect: 13 of 20 blueprint gaps are not closed by the current SGC estate. The four Critical gaps (G1–G4) are all `Partial` — they exist as data structures and reports, but the *enforcement* wiring into the operational lifecycle is missing.**

---

## 2. Inventory of SGC modules required to fulfil the desired workflow

The 15 blueprint charts require the following platform services + business modules. The current-state column lists what is on disk.

### 2.1 Chart-by-chart module map

| Chart | Required process lane | Current SGC module(s) | Coverage |
|---|---|---|---|
| **C01** Master Value Chain | End-to-end orchestrator; governance & readiness gate | `sgc_realestate_brokerage_template` (tenant + kit + preflight + activation gate) | **Skeleton only.** The `sgc.brokerage.tenant` model with `_preflight_check()` and `action_activate()` is the closest analogue to G0 readiness, but it is **per-tenant config**, not a *licence / agent permit / AML programme / escrow* live check at every entry point. |
| **C02** Segment switchboard (Brokerage · Property Mgmt · Developer · Owners Assoc.) | Feature flags per company / branch / profile | `sgc_realestate_brokerage_template` (kit matrix) | **Partial.** Kit = `brokerage_core | offplan_rental | construction | recurring_mgmt` per `sgc_realestate_brokerage_template/data/realestate_growth_defaults.xml`. Owners Association kit is **not present**. |
| **C03** Demand Intelligence & Decision Engine | Signal aggregation, decision rules, outcome measurement | `sgc_executive_dashboard`, `crm_executive_dashboard`, `crm_lead_ingestion_hub` | **Open.** No signal-aggregation engine, no decision rules, no outcome measurement loop. `sgc_lead_scoring` was closest but is **HELD**. |
| **C04** Lead & Instruction Intake | Multi-channel capture, dedupe w/ arbitration, consent, routing, SLA | `crm_lead_ingestion_hub` (`adapters/`, `controllers/`, `models/`), `crm_executive_dashboard`, `sgc_brochure_leadcapture` | **Partial.** Intake + consent + routing exist; *arbitration step* (G20) and *licence/capacity gate* (G18) are not modelled. |
| **C05** Owner Instruction → Compliant Listing | Title verification, owner screening, encumbrance check, agreement, advertising permit (Trakheesi Form A), publish block, de-listing | `sgc_offplan_rental_property_management` (RERA Form A view, portal publish wizard), `sgc_appraisal` | **Partial.** Form A view + portal publish wizard exist. *Owner-screening gate* (C05 Q2) and *system-block on publishing without permit number* (G10) are not enforced. |
| **C06** Demand-side CRM, matching, viewing, offer | Qualification, affordability, structured feedback, offer control | `sgc_brochure_leadcapture`, `sgc_realestate_website` (UNRESOLVED per `docs/audit/MODULE_PROVENANCE.md`), `crm_lead_ingestion_hub` | **Partial.** Lead capture + brochure exists; *structured feedback* (C13) and *offer control as a controlled document* (C06 C15) are not modelled. |
| **C07** KYC / AML / Sanctions Gate | Risk-tiered CDD, party graph, screening engine, SoF/SoW, threshold reporting (AED 55,000), tipping-off suppression | `kyc_management`, `aml_compliance` | **Partial.** Risk rating (G5), goAML export, CTR AED 55,000 exist as data + reports. *Party graph* (G2), *automatic threshold trigger* (G4 enforcement), *tipping-off suppression* (G3), *screening-provider failover / no silent-clear* (G15) are not wired. |
| **C08** Contracting & Settlement | Conditions register, seller obligations, transfer appointment, keys withheld until Ejari registration, inventory report | `sgc_offplan_rental_property_management` (rent + sale contract views, RERA Form A, sales SPA template), `sgc_commission` | **Partial.** Contract templates exist. *Conditions register with owner + deadline* (G9), *seller obligations gate* (G9), *keys withheld until lease registration* (G11) are not coded as enforceable fields. |
| **C09** Developer Lane | Project registration, project escrow (Law 8/2007), sales permit, Oqood, payment plans, escrow drawdown, handover, default ladder | `sgc_offplan_rental_property_management` (offplan installment plans, sales SPA template) | **Partial.** Offplan payment-plan data + SPA template exist. *Project escrow account dedicated to the project* (C09 DV3), *20% completion or 20% guarantee before marketing* (C09 Q1), *Oqood initial registration* (C09 DV12), *regulated termination ladder* (C09 Q3/Q4), *resale/assignment* (C09 DV17) are not modelled. `sgc_construction_management` exists but is **HELD**. |
| **C10** Invoicing, Collection, Tax, Commission, Clawback | Mixed-line tax invoice, dunning ladder with named exits, three-condition commission release gate, clawback automation | `sgc_commission`, `sgc_commission_reconcile`, `sgc_invoicing_dashboard`, `sgc_offplan_rental_property_management` (recurring invoicing) | **Partial.** Commission states + reconcile layer + invoicing dashboard exist. *Mixed-line tax determination* (C10 FI2), *dunning ladder with named exits* (G7), *three-condition release gate* (G8), *auto-reversal on credit note* (C10 FI13) are not wired. |
| **C11** Property & Tenancy Management | Emergency lane, vendor verification, arrears ladder, compliance calendar, renewal windows, deposit dispute | `sgc_offplan_rental_property_management` (rent schedules, property maintenance, recurring invoicing) | **Partial.** Rent schedules + recurring invoicing + maintenance extension exist. *Emergency lane* (G19), *vendor licence/insurance validation* (C11 PM9), *RERA 90-day notice window* (G11), *deposit dispute escalation to rental dispute authority* (C11 PM19) are not modelled. |
| **C12** Jointly Owned Property / Service Charge (Mollak) | Budget-then-bill, segregated funds, reserve fund, arrears block transfers | (none) | **Open.** No Mollak module exists in the estate. |
| **C13** Exception, Dispute, Regulatory Reporting | Classification, retry-with-backoff, DLQ, reporting-officer path, root-cause → improvement | `aml_compliance/wizard/goaml_filing_wizard_views.xml`, `aml_compliance/views/investigation_case_views.xml`, `sgc_realestate_brokerage_template/models/sgc_brokerage_incident.py`, `sgc_realestate_brokerage_template/models/sgc_wa_log.py` | **Partial.** Regulatory filing + incident logging exist. *Integration-failure DLQ + retry-with-backoff* (G15), *dead-letter queue* (C13 X4), *complaint SLA clock* (C13 X10/Q3), *root-cause → improvement backlog* (C13 X18/X19) are not modelled. |
| **C14** Shared Platform Services | Workflow engine, SLA engine, MDM w/ arbitration, rules pack, document vault, segregation of duties, idempotency, exception queue | `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py` (segregation via `check_company`), `sgc_commission_reconcile/security/ir_rule_tenant_isolation.xml` | **Open as a platform.** No workflow engine module, no rules-pack abstraction, no document vault with retention tagging, no idempotency layer, no exception queue. `samanabran` `tools/audit_coupling_lint.py` exists as a lint but is *not* an engine. |
| **C15** Implementation Sequence (4-phase plan) | Phase gates, adoption-measured, migration workstream | `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md` (8-phase plan) | **Partial.** The existing rollout doc is 8 phases; the blueprint prescribes 4 (licence-protection → recurring-revenue → developer/association → demand-intelligence). The existing 8-phase plan's *order* maps to the blueprint's *risk-weighted* phasing, but the gate criterion ("adoption proven") is not measured. |

### 2.2 Cross-cutting platform services (C14) — current-state survey

| Platform service (C14) | Required for | Current state | Status |
|---|---|---|---|
| Workflow & Rules Engine | All charts | Odoo base server actions + `crm_lead_ingestion_hub` adapters. No dedicated workflow engine. | **Open** |
| Task / SLA / Escalation Engine | C01, C04, C11, C13 | `mail.activity.mixin` inheritance (present in `sgc.brokerage.tenant`). No SLA engine with breach → manager routing. | **Open** |
| Notification Service | All charts | Odoo `mail` (depends chain). No delivery-failure → exception flow. | **Partial** |
| Master Data Management w/ arbitration | C04, C14 | Odoo `contacts` + `res.partner` extensions. `crm_lead_ingestion_hub` has dedupe; arbitration step is not first-class. | **Partial** |
| Regulatory Rules Pack | All charts | `aml_compliance/data/fatf_jurisdiction_data.xml`, `risk_factor_data.xml`. Thresholds are not in a single config layer; AED 55,000 hard-coded in `goaml_report_print.xml`. | **Partial** (per-jurisdiction pack is not abstracted) |
| Document & Media Vault | C05, C14 | Odoo `ir.attachment`; `sgc_offplan_rental_property_management` has property documents. No version control or retention tagging. | **Partial** |
| Access Control / Segregation of Duties | All charts | `check_company=True` (removed where inappropriate per `sgc_realestate_tenant.py` comment line 47), `ir_rule_tenant_isolation.xml` in `sgc_commission_reconcile`. The blueprint's SoD matrix (lister ≠ approver, agent ≠ own-compliance-officer) is not enforced. | **Partial** |
| Immutable Audit, Consent, Retention | All charts | `mail.thread` on tenant; Odoo base `mail.message`. 5-year retention not enforced per record type. | **Open** |
| Document Generation & E-Signature | C05, C08 | Odoo `website_mail` + portal; `sgc_offplan_rental_property_management` has portal contracts. Signature audit certificate not retained as evidence per C14 S9. | **Partial** |
| Integration Layer + Idempotency + DLQ | All charts | Portal connectors in `sgc_offplan_rental_property_management/views/portal/`. No idempotency keys; no DLQ. | **Open** |
| Finance / Banking / Escrow Connectors | C09, C10 | `account` + `sgc_commission_reconcile` invoice bridge. No dedicated project-escrow connector (C09 DV3). | **Open** |
| Dashboards & Reporting | All charts | `sgc_executive_dashboard`, `crm_executive_dashboard`, `sgc_invoicing_dashboard`, `sgc_dynamic_financial_report`, `sgc_ces_kpi_banner`. Reports read from multiple models; single-model reconciliation not enforced. | **Partial** |
| Exception Queue | All charts | `sgc.brokerage.incident` (`sgc_realestate_brokerage_template/models/sgc_brokerage_incident.py`). No first-class queue with classification routing. | **Partial** |
| Configuration & Feature Flags | All charts | `sgc_realestate_brokerage_template` enablement matrix. Per-company / per-branch feature flags exist as design, not as a runtime toggle. | **Partial** |

---

## 3. Module-level misalignment catalogue

Each row identifies a module on disk whose **current scope or behaviour diverges from the blueprint's required behaviour**. These are the records that should drive a follow-up design pass.

### 3.1 `sgc_realestate_brokerage_template/` — the orchestrator skeleton

| Aspect | Current | Blueprint requires | Misalignment |
|---|---|---|---|
| Purpose | Tenant skeleton + kit selector + preflight + activation gate | Master value-chain orchestrator (C01) with named readiness checks per entry point | The template is **per-tenant config**, not a runtime gate. Readiness today is one-shot at activation; the blueprint requires *every* entry (lead, listing, launch, tenant-service) to pass a readiness check. |
| Preflight checks | M1 / M3 / M5 / M0 audit blockers | C01 G0 covers trade licence, agent permit, AML programme, escrow arrangement, enabled modules | Preflight checks are about **infrastructure hygiene** (URLs, mail, workspace, company ID), not **regulatory readiness** (RERA broker registration, agent permit validity, goAML registration, escrow arrangement). The regulatory side is not gated. |
| State machine | `draft → onboarding → active` | Continuous with named end states (Closed-Won-Archived, Closed-Lost-Reason-Logged, Blocked-or-Reported-Case-Sealed, Active-Portfolio-Under-Management) | The blueprint's terminal states are not first-class on the tenant record. |
| Kit matrix | `brokerage_core, offplan_rental, construction, recurring_mgmt` | Brokerage · Property Management · Developer · Owners Association + explicit exclusions for construction execution | The kit matrix **does not include Owners Association**. The held `sgc_construction_management` is referenced but not enabled. |
| Compliance event model | `sgc.compliance_event` | KYC / AML trigger firing on every entry, with named outcomes | Model exists but is *event log only*; the trigger-before-money gate (G1) is not enforced through this model. |
| Integration source model | `sgc.integration_source` | Idempotency keys + retry + DLQ on every integration (C14 S11) | Model exists but does not enforce idempotency or DLQ behaviour. |
| Strategy layer priority | `sgc_strategy_layer_priority.py` | Decision engine (C03 ENG) with outcome measurement + threshold tuning | File exists but does not implement signal aggregation, decision rules, or outcome measurement. |
| WA log | `sgc_wa_log.py` | WhatsApp capture + delivery-failure → exception | Capture path exists; delivery-failure routing to C13 X4 does not. |

### 3.2 `aml_compliance/` — strong foundation, weak enforcement wiring

| Aspect | Current | Blueprint requires | Misalignment |
|---|---|---|---|
| Risk rating (Phase 1) | Configurable, FATF, PEP, EDD triggers | C07 K3–K6 with named rating tiers | **Aligned** at the data layer. |
| goAML export (Phase 2) | STR / SAR / CTR XML | C07 K17 threshold report | **Aligned** at the export layer. |
| Threshold trigger | AED 55,000 hard-coded in `goaml_report_print.xml` | C07 Q7 automatic fire-on-facts, independent of suspicion | The threshold value is correct; the **automatic trigger** at payment-time is not wired into `account` invoice confirmation or into `sgc_commission_reconcile` payout. |
| Sanctions screening (Phase 4) | UN + UAE local lists | C07 K13 screening engine call with **provider outage failover + manual fallback** (G15) | The screening exists; the *failover then documented manual search* (K14) is not modelled. |
| Periodic review (Phase 6) | Expiry alerts for documents | C07 K27 ongoing monitoring with alert routing to compliance, not to the agent | Alerts are not routed distinctly from the agent's queue. |
| Tipping-off suppression | Not referenced | C07 K25 client-notification suppression is a separate offence | **Open.** No technical suppression of client-facing notifications on the reporting path. |

### 3.3 `kyc_management/` — workflow exists, party graph and SLA counter do not

| Aspect | Current | Blueprint requires | Misalignment |
|---|---|---|---|
| Application lifecycle | Approval workflow | C07 K7 system-generated checklist derived from rating | **Aligned** in principle; checklist derivation by rating is not visible in the data layer. |
| Party graph | One KYC application per contact | C07 K1 client + co-buyer + company + every beneficial owner + POA holder + third-party payer | **Open.** No party-graph model. |
| Document chase | Approval workflow | C07 K11 request the missing items with **attempt counter + SLA breach** (G6) | **Open.** No hard `attempts_exhausted → case_suspended` counter. |
| Approved-with-conditions | Not visible | C07 K24 escrow-only / no-cash / restricted-channels / enhanced-monitoring frequency | **Open.** No "approved with conditions" outcome. |

### 3.4 `sgc_commission/` + `sgc_commission_reconcile/` — three-condition gate is missing

| Aspect | Current | Blueprint requires | Misalignment |
|---|---|---|---|
| Lifecycle | 5 states (Draft → Calculated → Confirmed → Processed → Paid) | C10 CO2/Q6 three-condition release gate (funds cleared · registration complete · compliance still approved) | The 5-state lifecycle does not require any of the three conditions before transition to "Paid". |
| Hold-back / clawback | Not visible in manifest description | C10 CO3 held-in-pending visible to agent with reason + CO6 ledger | **Open.** No "pending with reason" visibility. |
| Tax determination | Not modelled | C10 FI2 mixed-line tax (exempt / zero-rated / standard-rated) | **Open.** No tax-rate-by-line engine. |
| Clawback automation | Not modelled | C10 FI13 credit-note → automatic reversal against ledger | **Open.** |
| Co-brokerage splits | Available in `sgc_commission_reconcile` | C10 CO1 listing / selling / team / referrer / branch / external broker | **Aligned** at the data layer; reconciliation exists. |
| Tenant isolation | `ir_rule_tenant_isolation.xml` | C14 S7 segregation of duties | **Aligned.** |

### 3.5 `sgc_offplan_rental_property_management/` — largest module, mostly partial

This module bundles property sale + offplan payment plans + rental + maintenance + portal syndication + public website. Coverage against the blueprint:

| Blueprint chart | Coverage | Misalignment |
|---|---|---|
| C04 / C05 intake & listing | **Partial.** Multi-channel intake, RERA Form A view, portal publish wizard, XML feed, portal sync log | No system-block on publishing without permit number (G10); no party-graph screening on owner (G2); no de-listing SLA (G10). |
| C07 KYC / AML | **None inside this module.** | KYC / AML lives in `kyc_management` + `aml_compliance`. The blueprint requires the **gate to fire before money moves** through reservation/booking — the wiring is missing here. |
| C08 contracting | **Partial.** SPA template, rent contract view, RERA Form A | No seller-obligations gate (developer no-objection, mortgage discharge, service-charge clearance, utility settlement) before transfer appointment; no keys-withheld-until-lease-registration (G11); no 90-day statutory notice (G11). |
| C09 developer lane | **Partial.** Offplan installment plans, sales SPA template | No project-escrow account dedicated to the project (DV3); no marketing-threshold gate (DV4–DV5); no Oqood initial sale registration (DV12); no default-handling ladder (DV14–DV15); no resale/assignment consent (DV17). Construction execution is **explicitly out of scope per the blueprint** (X1–X4 in C02). |
| C10 invoicing | **Partial.** Rent schedule + recurring invoicing + payment-schedule template | No dunning ladder with named exits (G7); no mixed-line tax determination (G10 FI2). |
| C11 tenancy management | **Partial.** Tenancy details, maintenance extension, rent bill / invoice | No emergency lane with bypass-approval authority (G19); no vendor licence/insurance validation (C11 PM9); no deposit dispute escalation (C11 PM19); no compliance calendar (C11 PM11). |
| C14 portal integration | **Partial.** Portal connector + sync log + XML feed | No idempotency keys; no DLQ; no retry-with-backoff (G15). |

### 3.6 `sgc_construction_management/` — **HELD**, but a structurally required sibling

Per `30_QUARANTINE/sgc_construction_management.md`, this module's derivation from `aos_construction_management` is confirmed. It is **deliberately excluded** from the candidate path per the brokerage template manifest's `excludes` list.

The blueprint's C02 X1–X4 explicitly excludes construction execution from scope. So construction is *not* a misalignment — it is correctly held. **What is misaligned** is the *absence of the developer sales lane* that should exist independently of construction (C09). The SGC estate has fragments of that lane inside `sgc_offplan_rental_property_management` but no dedicated module.

### 3.7 `sgc_lead_scoring/` — **HELD**, the closest match to C03

Per `30_QUARANTINE/sgc_lead_scoring.md`, four divergent copies + a broken unique constraint. Held in quarantine. The blueprint's C03 decision engine is closest in intent to this module's scoring loop, but **the blueprint goes further** — signals beyond lead scoring (viewing-to-offer ratio, days-on-market, absorption, channel economics, lost-reason analytics) plus decision actions (reprice, reallocate spend, reassign agent, etc.) plus outcome measurement and threshold tuning.

**Open.** Until provenance is resolved, the C03 engine must be built independently.

### 3.8 `sgc_crm_dashboard/`, `sgc_executive_dashboard/`, `crm_executive_dashboard/` — reporting, not decisioning

All three modules are dashboards. None of them close the C03 loop (signal → decision → outcome → threshold tuning). They are useful for *visibility* but not for *action*.

### 3.9 `sgc_appraisal/`, `sgc_assessment/`, `sgc_brochure_leadcapture/` — point solutions

| Module | Role | Alignment |
|---|---|---|
| `sgc_appraisal` | Property valuation | Used in C09 DV-inventory decisions but does not implement the C09 chain. Partial credit. |
| `sgc_assessment` | Form-style questionnaires (Typeform-style) | Useful for buyer / seller questionnaires; not wired into the C04 / C06 lead-qualification flow. |
| `sgc_brochure_leadcapture` | Landing page → lead capture | Useful for C04 L1 multi-channel capture. Aligns with the Phase 4 growth kit. |

### 3.10 `kyc_management` ↔ `aml_compliance` dependency

`aml_compliance` depends on `kyc_management`. The dependency direction is correct, but neither module depends on `sgc_commission` or `sgc_offplan_rental_property_management` — so the **critical G1 sequence error** (screening before money) cannot be enforced at the wiring level. The wire-up is missing.

### 3.11 What the audit has already closed (vs. what remains open)

The audit at `docs/audit/MODULE_PROVENANCE.md` and `30_QUARANTINE/` has resolved:

- **Provenance gating** (`tools/audit_coupling_lint.py` exits 0 on the candidate path).
- **Multi-tenant blocker resolution** (M1 URLs / M3 mail / M5 workspace / M0 company per `docs/audit/MULTI_TENANT_BLOCKERS.md`).
- **Per-tenant envelope** (`sgc.brokerage.tenant._preflight_check()`).

What the audit has **not** resolved (and the blueprint treats as workflow gaps):

- Business-logic gaps G1–G20 above (sequence, party graph, threshold trigger, dunning, commission gate, etc.).
- Platform-service gaps in §2.2 (rules engine, SLA engine, MDM w/ arbitration, rules pack, document vault, idempotency, DLQ, exception queue).
- Operational gaps: owner-screening gate, party graph, system-block on publish, Mollak service-charge admin, demand-engine feedback loop.

---

## 4. Quick "what to build next" summary

For the full pledge real-estate workflow, the misalignment catalogue above boils down to these high-leverage build items, listed in the order that follows the blueprint's C15 phasing (Phase 1 — licence protection + transaction spine):

1. **Wire KYC/AML gate before reservation money moves** (closes G1 + G4 enforcement).
2. **Build the party-graph model** in `kyc_management` (closes G2).
3. **Build the three-condition commission release gate** in `sgc_commission` (closes G8).
4. **Build the dunning ladder with named exits** in `sgc_offplan_rental_property_management` (closes G7).
5. **Enforce system-block on publishing without permit number** in `sgc_offplan_rental_property_management` (closes G10).
6. **Build seller-obligations + conditions register** for the sale lane (closes G9).
7. **Build the 90-day notice + RERA-index rent-review engine** (closes G11).
8. **Build the developer lane beyond offplan payment plans** — project escrow, sales permit, Oqood, default ladder, handover (closes G12).
9. **Build Mollak service-charge administration** as a new sibling module (closes G14).
10. **Build the platform exception queue + idempotency + DLQ** as a cross-cutting module (closes G15).
11. **Build the demand-intelligence decision engine** as a new module (closes G13).
12. **Build the SLA / attempt counter / escalation engine** as a cross-cutting module (closes G6).
13. **Build the dead-letter + retry-with-backoff + manual-failover lane** for screening and portal integrations (closes G15).
14. **Enforce segregation of duties** at the model level — lister ≠ approver, agent ≠ own-compliance-officer, raiser ≠ approver (closes G17 partial, G18 partial).
15. **Implement 5-year retention clocks** per record type (closes G16).

These 15 build items cover all 20 blueprint gaps.

---

## 5. Provenance + licence reminder

| Module | Status | Notes |
|---|---|---|
| `sgc_realestate_brokerage_template` | Cleared (per `docs/audit/MODULE_PROVENANCE.md`) | Reference template. |
| `aml_compliance` | Cleared | Strong foundation. |
| `kyc_management` | Cleared | Workflow exists. |
| `sgc_commission` | Cleared but Phase 9 UNRESOLVED | `sgc_commission_reconcile` exists as reconciliation layer. |
| `sgc_commission_reconcile` | Cleared | Reconciliation layer. |
| `sgc_offplan_rental_property_management` | UNRESOLVED (largest module in estate; provenance TODO) | Treat as **not yet ORIGINAL_SGC** until file-by-file provenance is completed per `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md` Phase 5. |
| `sgc_appraisal` | Cleared | |
| `sgc_assessment` | Cleared | |
| `sgc_dynamic_financial_report` | Cleared | Reference financial report. |
| `sgc_executive_dashboard` | Cleared | Reporting only. |
| `crm_executive_dashboard` | UNRESOLVED | Provenance open. |
| `crm_lead_ingestion_hub` | UNRESOLVED | Provenance open. |
| `sgc_lead_scoring` | **HELD** — 4 divergent copies + broken unique constraint (`30_QUARANTINE/sgc_lead_scoring.md`) | Must not be in `depends` of any new module until hold is lifted. |
| `sgc_crm_dashboard` | **HELD** — Cybrosys fingerprint (`30_QUARANTINE/sgc_crm_dashboard.md`) | Must not be in `depends`. |
| `sgc_construction_management` | **HELD** — confirmed derivation from `aos_construction_management` (`30_QUARANTINE/sgc_construction_management.md`) | Correctly excluded per C02 X1–X4. |
| `ks_dynamic_financial_report` | **HELD** — Ksolves provenance unresolved | Do not use. |
| `sgc_rental_management` | **HELD** (staging only — TechKhedut / SmartClinic) | Merged into `sgc_offplan_rental_property_management`. |
| `sgc_brochure_leadcapture` | Cleared | Phase 4 growth kit. |
| `sgc_realestate_website` | UNRESOLVED per `MODULE_PROVENANCE.md` | Enable only after per-vertical provenance check. |

---

## 6. Companion documents in this estate

| File | Purpose |
|---|---|
| `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md` | 8-phase rollout playbook (existing; **not the blueprint's C15**). |
| `docs/audit/MODULE_PROVENANCE.md` | Per-module provenance status. |
| `docs/audit/MULTI_TENANT_BLOCKERS.md` | M0/M1/M3/M5 audit blockers + resolution path. |
| `docs/audit/HARDCODED_COUPLING.md` | Hardcoded coupling findings. |
| `docs/audit/SYNC_2026-08-31.md` | Audit sync log. |
| `tools/audit_coupling_lint.py` | Lint that enforces provenance. |
| `30_QUARANTINE/README.md` + per-module `*.md` | Hold list. |
| `sgc_realestate_brokerage_template/` | Reference template (the on-disk artefact that orchestrates the current state). |

---

## 7. Document ownership and update rule

- This document is the **single basis** for the future full pledge real-estate workflow build.
- It does **not** rebuild or modify any existing module logic, guardrail, or workflow.
- When a misalignment is closed by a new build item, the relevant row should be updated from `Open` / `Partial` → `Closed` with a date and a commit hash.
- When a new gap is discovered from a regulator update, add a row to §1 and §3.
- The document's canonical copy lives at `docs/REAL_ESTATE_WORKFLOW_MISALIGNMENT.md`. A copy is kept alongside the blueprint source in `C:\Users\USER\Downloads\FULL_REAL_ESTATE_WORKFLOW_MISALIGNMENT.md` as the user's working copy.
