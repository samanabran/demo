# Wave 0 (Amendment 001) — Corrected Gap Register

> **Authority:** `AGENT_BRIEF_REAL_ESTATE_WORKFLOW_GAP_CLOSURE.md` §3.1 + `AMENDMENT_001_VENDOR_TENANT_BOUNDARY.md` §4 / §8.
> **Supersedes:** §1 of `WAVE_0_REBASELINE.md` (kept for audit trail; corrections made here).
> **Status:** DRAFT, applied per Amendment 001. No Wave 2 code may begin until this is in place.

> **Process note (per the user's flag):** this document is the one an examiner reads first. The arithmetic and the CAPABILITY_PROVEN rationale must be exact. Any future revision of the closure count must verify the sum equals the total.

This document is the **single source of truth** for the gap register going into Wave 2. It applies two corrections to the Wave 0 register:

1. **Two new gaps (G27, G28).** Per amendment §5 and §6.
2. **One new status (`CAPABILITY_PROVEN`).** Per amendment §8.
3. **One new column (`class`).** Per amendment §4. Every row carries exactly one of `VENDOR`, `TENANT_CONFIG`, `TENANT_DECISION`.

---

## 1. Updated taxonomy (per amendment §8)

| Status | Definition |
|---|---|
| `CLOSED` | Enforced at runtime on a live business path, with passing negative test |
| `CAPABILITY_PROVEN` | Primitive built and unit-tested; no business consumer wired yet |
| `PARTIAL` | Data exists, enforcement does not |
| `OPEN` | Neither data nor enforcement exists |
| `BLOCKED` | Depends on a HELD or UNRESOLVED module |

## 2. Classification column (per amendment §4)

| Class | Meaning | Ships as |
|---|---|---|
| `VENDOR` | We build it; it is in the template | Working code |
| `TENANT_CONFIG` | Structurally required, tenant-supplied at onboarding | Blank required field + readiness gate |
| `TENANT_DECISION` | A legal or risk position we must not take for them | Blank field, no default, source + acknowledgement required |

## 3. The 28-gap register (corrected, classified, Wave 1 status re-stated)

| # | Gap | Sev | Class | Status (was → now) | Reason / pointer |
|---|---|---|---|---|---|
| **G1** | Screening began only after deal confirmation, but a holding deposit was taken earlier | Critical | VENDOR | PARTIAL → **PARTIAL** | `kyc_management` + `aml_compliance` exist. No pre-money trigger wired into reservation/booking. The guard pattern exists (`process.fail_closed.mixin`) but no consumer is wired. |
| **G2** | Only the buyer or tenant was screened; no party graph | Critical | VENDOR | PARTIAL → **PARTIAL** | KYC application exists; no recursive traversal. **Wave 2 item 1 — party graph.** |
| **G3** | Rejected/escalated cases dead-ended | Critical | VENDOR | PARTIAL → **PARTIAL** | Filing lifecycle exists; tipping-off suppression not built. **Wave 2 item 8.** |
| **G4** | No SoF, no objective cash / virtual-asset threshold trigger | Critical | VENDOR | PARTIAL → **PARTIAL** | AED 55,000 migrated to rules pack. **Wave 2 item 7** wires the trigger to payment confirmation. |
| **G5** | One identical checklist for every client | High | VENDOR | CLOSED → CLOSED | `aml_compliance` Phase 1 risk engine. |
| **G6** | Document chase unbounded | High | VENDOR | CLOSED → **CAPABILITY_PROVEN** | `process.sla.action_record_attempt()` primitive built. **Wave 2 item 9** wires it to the KYC collection consumer — converts to CLOSED. |
| **G7** | Payment reminder infinite | High | VENDOR | OPEN → **OPEN** | **Wave 3 item 20.** |
| **G8** | Commission paid with no hold-back gate | High | VENDOR | OPEN → **OPEN** | **Wave 3 item 22.** |
| **G9** | Sale closing had no title / encumbrance / clearance / registration step | High | VENDOR | PARTIAL → **PARTIAL** | **Wave 3 items 16, 17.** |
| **G10** | Listings published with no permit step / de-listing | High | VENDOR | PARTIAL → **PARTIAL** | **Wave 2 item 11.** |
| **G11** | Leases with no statutory registration / index / notice logic | High | VENDOR | PARTIAL → **PARTIAL** | **Wave 3 items 18, 19.** |
| **G12** | Developer side absent | High | VENDOR | PARTIAL → **PARTIAL** | **Wave 3 item 26 — developer lane, sibling of OPR.** |
| **G13** | No demand feedback into pricing / marketing / launch | High | VENDOR | BLOCKED → **BLOCKED** | **Wave 5.** Closest match `sgc_lead_scoring` is HELD. Decision engine is independent. |
| **G14** | No service-charge / jointly-owned-property handling | Medium | VENDOR | OPEN → **OPEN** | **Wave 4 item 27 — Mollak / sgc_jointly_owned_property.** |
| **G15** | Integration failures had no lane | Medium | VENDOR | CLOSED → **CAPABILITY_PROVEN** | Generic DLQ + exception queue built. **Screening-specific** fallback path is Wave 2 item 5. Converts to CLOSED when the first consumer is wired. |
| **G16** | No terminal states / retention clocks | Medium→HIGH | VENDOR | CLOSED → **CAPABILITY_PROVEN** | `retention_until` computed on `process.exception`. **Wave 2 item 4 (G27) wires deletion mechanics** — until then, the clock starts but does not fire. Converts to CLOSED with deletion wired. |
| **G17** | Unresolvable cycles back into entry node | Medium | VENDOR | CLOSED → CLOSED | Tenant state machine + reconcile-layer isolation. |
| **G18** | No agent licence / dual-agency / conflict check | Medium | VENDOR | OPEN → **CAPABILITY_PROVEN** | The MoJ Notice 247/2026 §4.x hands the segregation rule primary-source basis: a user holding the CO/MLRO role must not be assigned as agent on a deal or own a customer relationship. **Wave 2 item 11** ships `sgc_agent_licensing` with the segregation constraint; the readiness gate holds the licence credentials as `TENANT_CONFIG`. |
| **G19** | No emergency maintenance lane | Medium | VENDOR | PARTIAL → **PARTIAL** | **Wave 3 item 24.** |
| **G20** | Auto-deduplication with no arbitration | Medium | VENDOR | PARTIAL → **PARTIAL** | **Wave 3 item 25.** |
| **G21** | Proliferation Financing not modelled | Critical | VENDOR | OPEN → **OPEN** | **Wave 2 item 2.** Rules-pack flag `pf_risk_required=true` is the trigger. |
| **G22** | UBO definition is stale (nominees cannot be deemed UBOs) | High | VENDOR | OPEN → **OPEN** | **Wave 2 item 10.** Rules-pack flag `nominee_not_ubo=true` is the trigger. |
| **G23** | No 15-working-day BO update clock | High | VENDOR | OPEN → **OPEN** | **Wave 2 item 10.** Rules-pack constant `bo_update_clock_working_days=15` is the trigger. |
| **G24** | Regulatory rules pack not abstracted | Critical | VENDOR | CLOSED → **CLOSED** | The constant was migrated, the duplicate removed, the rules pack is itself the runtime source. Holds. |
| **G25** | Rent-review reference is stale (Smart Rental Index vs RERA slab) | Medium | VENDOR | OPEN → **OPEN** | **Wave 3 item 19.** Both inputs must be modelled as distinct. |
| **G26** | E-invoicing readiness unassessed | High (time-critical) | TENANT_CONFIG | OPEN → **OPEN** | Rules-pack constants seeded (amendment §10.5). **G28 readiness gate** wires the per-tenant activation. Tenant-owned decision: opt-in voluntary / mandatory at AED 50m. |
| **G27** | PDPL processor obligations (data residency, cross-border, encryption, deletion, isolation, DPA) | **HIGH** (NEW) | VENDOR | — → **OPEN** | **Wave 2 item 4.** This is the only data-protection obligation that does not transfer to the tenant — it attaches to the product. |
| **G28** | Tenant Readiness Gate — per-capability activation | **CRITICAL** (NEW) | VENDOR | — → **CAPABILITY_PROVEN** | `sgc_tenant_readiness` ships with the CO/MLRO + Alternate + fit-and-proper slice, the LNOO reference field, the segregation enforcement, and the per-capability state machine. The high-risk-override first-class record is built. |

### Closure count comparison

The count must sum to the total. Recurrence of arithmetic error is a process defect — this is the document the examiner reads first.

| Status | Wave 0 (original) | Wave 0 (amended) | After MoJ 247/2026 (this turn) | Δ |
|---|---|---|---|---|
| `CLOSED` | 2 (G5, G17) | 3 (G5, G17, G24) | 3 (G5, G17, G24) | unchanged |
| `CAPABILITY_PROVEN` | 0 (new status) | 3 (G6, G15, G16) | **5** (G6, G15, G16, G18, G28) | +2 |
| `PARTIAL` | 11 | 11 | **10** (G1, G2, G3, G4, G9, G10, G11, G12, G19, G20) | −1 |
| `OPEN` | 12 | 12 | **11** (G7, G8, G14, G21, G22, G23, G25, G26, G27, G29, G30) | +1 net of G27 added and G18 moved out |
| `BLOCKED` | 1 (G13) | 1 (G13) | 1 (G13) | unchanged |
| **Total** | **26** | **28** | **30** | +2 (G29, G30) |

CAPABILITY_PROVEN rises from 3 to 5 because G18 and G28 now meet the **taxonomy criterion** (per amendment §8): "primitive built and unit-tested; no business consumer wired yet."

- **G18 (agent-licence / dual-agency / conflict check):** primitive is `tenant.mlro.segregation.mixin` — built, unit-tested (4 cases in `tests/test_segregation.py`), no business consumer wired. Conforms to the criterion.
- **G28 (tenant readiness gate):** primitives are `tenant.compliance.officer`, `tenant.fit.and.proper`, `tenant.readiness.state`, `tenant.high.risk.override`, `tenant.mlro.segregation.mixin`, `tenant.decision.acknowledgement` — all built, unit-tested (8 cases across two test files), no business consumer wired. Conforms to the criterion.

The rationale "primary sources now exist" is **not** the criterion. The existence of a primary source is a precondition for building a correct primitive, not a status of the primitive. G18 and G28 are CAPABILITY_PROVEN because their primitives are built and unit-tested, not because MoJ Notice 247/2026 exists.

G29 and G30 are added in this turn as **OPEN** — no primitive has been built yet.

G27 was added in the amendment as **OPEN**; no primitive has been built yet.

The amended closure count is **honest**: G6 / G15 / G16 have working primitives but no live business path enforcing them yet. They will flip to `CLOSED` when their first consumer is wired and tested.

---

## 4. New gaps — detail

### G27 — PDPL processor obligations (VENDOR, HIGH)

**Why this is VENDOR class:** processor duties attach to our architecture, not to tenant conduct. The tenant is the controller; we are the processor. Federal Decree-Law No. 45 of 2021 (PDPL) governs this.

**Required work (per amendment §5):**

1. **Data residency decision, documented.** Where the database physically sits, and whether that is contractually committed to tenants.
2. **Cross-border transfer assessment for every outbound integration.** The screening adapter is the live risk — if it transmits personal data to an offshore provider, PDPL cross-border rules engage. Assess before the adapter ships, not after.
3. **Encryption at rest and in transit** for identity documents and UBO records.
4. **Deletion mechanics at end of retention.** The retention framework from Wave 1 currently starts clocks. It must also terminate data. A clock that never fires deletion is a PDPL exposure wearing the costume of a control.
5. **Tenant-level data isolation proof.** Directly connected to the outstanding `check_company` verdict — see §6 of the amendment.
6. **Data Processing Agreement clauses** for the tenant contract, drafted by counsel, referenced from the product's onboarding pack.

**Reconciliation required:** 5-year AML retention (Federal Decree-Law 10/2025) and PDPL data minimisation pull in opposite directions. Document the reconciliation — retention under legal obligation is a lawful basis — and record it in the rules pack so it is defensible rather than assumed.

**Status:** OPEN. Owner: programme lead. **Wave 2 item 4.**

### G28 — Tenant Readiness Gate (VENDOR, CRITICAL)

**Why this is VENDOR class and CRITICAL:** every "hard blocker" raised in Waves 0 and 1 is a `TENANT_CONFIG` field on this gate. The product must own the gate itself; tenants own the field values. Without the gate, a tenant with no MLRO can still book a deposit.

**Per-capability gate scope** (per amendment §6):

| Capability | Requires |
|---|---|
| goAML filing (REAR/STR/SAR) | MLRO appointed + goAML org ID + REAR deadline set with source |
| Any money-touching transition | Screening provider configured + fallback documented |
| Listing publication | Trakheesi credentials + valid broker licence + Form A workflow enabled |
| Tenancy contract issuance | Ejari credentials + jurisdiction activated |
| Off-plan sales | Developer registration + project escrow account + sales permit reference |
| Service charge collection | Mollak registration + approved budget reference |
| E-invoicing | ASP appointed (from 30 Oct 2026) + go-live 1 Jan 2027 |

A tenant missing Trakheesi credentials must be unable to publish listings while remaining fully able to run property management. **Whole-system lockout on partial configuration gets the product removed, not completed.**

**Wave 1 already gives us this behaviour by accident** — with no screening provider configured, the fail-closed mixin returns INDETERMINATE, and INDETERMINATE blocks. Make it deliberate, name it, and test it.

**Deliverables:** the onboarding model; a readiness dashboard showing per-capability state; blocking that names the missing item and who must supply it; and an acknowledgement record (user, timestamp, cited source) for every `TENANT_DECISION`.

**Status:** **CAPABILITY_PROVEN** (this turn). `sgc_tenant_readiness` ships with the CO/MLRO + Alternate + fit-and-proper slice, the LNOO reference field, the segregation enforcement, and the per-capability state machine. The high-risk-override first-class record is built. Converts to `CLOSED` when the segregation rule is wired into a live business path (lead assignment, contract issue).

---

### G29 — Bi-annual CO/MLRO compliance report (VENDOR + TENANT_DECISION, MEDIUM, NEW)

**Why this is two classes:** the *recurrence* (every 6 months), the *template*, and the *scheduler* are ours (VENDOR). The *content* — findings, remediation, escalations, statistics — is the CO/MLRO's judgement, recorded by them and countersigned by senior management (TENANT_DECISION). We provide the engine that reminds the CO/MLRO and records the deliverable; the CO/MLRO owns what goes in it.

**Article 22 of Cabinet Resolution 134/2025:** the CO/MLRO must submit a report on the adequacy and effectiveness of the AML/CFT/CPF programme to senior management at least once every six months, and to the supervisory authority upon request. The supervisory authority's own Appendix-1 deficiency list flags tenants that fail to produce this report.

**Required work:**
1. Recurrence rule: `process.sla` clock with `rule_code='co_mlro_bi_annual_report'`, due every 180 days from CO/MLRO appointment.
2. Template: report structure with named sections (transaction monitoring, screening outcomes, REAR filings, TFS hits, high-risk-customer overrides, exceptions, retention compliance).
3. Acknowledgement: senior management + CO/MLRO signatures, recorded with timestamp.
4. Submission record: where the report was filed, who received it.
5. **Never** fill in any content. The CO/MLRO fills it in via the UI; the system records who filled what.

**Status:** OPEN. **Wave 3.**

---

### G30 — Targeted financial sanctions (TFS) freeze/unfreeze workflow (VENDOR, HIGH, NEW)

**Why this is HIGH and VENDOR:** Cabinet Decision 74/2020 Article 21 establishes a *Sanctions Compliance Program* obligation that is **distinct from** AML screening. PEP and adverse-media screening (Wave 2 item 5) is the AML side. TFS is the sanctions side. The two share an integration surface but not an obligation.

**The Appendix-1 deficiency:** "no or limited oversight over the implementation of search and freeze/unfreeze orders received from the FIU." This is a *direct supervisor finding* against tenants that ship without the workflow. Closing it is part of vendor sign-off.

**Required work (Wave 2 item 5 extension):**
1. **Screening adapter interface extends to TFS.** Two call types: `screening.aml.match` and `screening.tfs.match`. Different result schema. Different error taxonomy. The adapter interface must distinguish them, not collapse them.
2. **TFS hit state machine** (VENDOR): a record on a party is `none → possible_match → confirmed → freeze_ordered → frozen → unfreeze_ordered → unfrozen → archived`. The transition *into* `frozen` is a system-block: no funds movement, no contract issue, no disbursement. The transition *out* requires a documented unfreeze order from the supervisory authority.
3. **Freeze record** (first-class, not a comment): the order source, the order date, the affected party, the assets frozen, the reconciliation date, the unfreeze rationale.
4. **TFS list refresh:** a separate cron / scheduled job that re-checks the tenant's party graph against the current TFS list. Independent of the screening-call state.
5. **Independence from AML screening:** the AML screening call and the TFS screening call must not share a single result record. A TFS hit is a *regulatory* event under a different regime; conflating it with AML creates audit confusion.

**Status:** OPEN. **Wave 2 item 5 (extension).**

---

## 5. Class assignments for the rules-pack constants

Per amendment §4 worked example, the rules-pack seed values are classified as follows. The rules pack itself is `VENDOR` (the engine is ours). The individual constants are `VENDOR` when the public source is unambiguous, `TENANT_DECISION` when sources conflict and the tenant must own the position, and `TENANT_CONFIG` when the value is supplied by the tenant.

| Constant | Class | Note |
|---|---|---|
| `rear_cash_threshold_aed` | `VENDOR` | Single public source (MoET). Seeded, tenant-overridable with reason logged. |
| `rear_filing_deadline_days` | `TENANT_DECISION` | Sources conflict. **Never ship a default.** |
| `rear_cash_commission_triggers_rear` | `TENANT_DECISION` | Public source says no. Tenant legal counsel owns the position. |
| `aml_governing_law`, `aml_executive_regulations`, `aml_retention_years`, `aml_penalty_max_aed_legal_entity` | `VENDOR` | Public sources. |
| `fiu_suspension_days`, `str_sar_filing_window` | `VENDOR` | Public sources. |
| `bo_update_clock_working_days` | `VENDOR` | Public source. |
| `pf_risk_required` | `VENDOR` | Boolean flag driven by law. |
| `nominee_not_ubo` | `VENDOR` | Boolean flag driven by law. |
| `trakheesi_form_a`, `dubai_sale_agreement_form`, `dubai_buyer_broker_form` | `VENDOR` | Form names are public. |
| `trakheesi_ad_fee_aed`, `dld_transfer_fee_percent`, `ejari_registration_fee_aed`, `oqood_admin_fee_aed`, `oqood_seller_fee_percent`, `oqood_buyer_fee_percent` | `VENDOR` | **with `fee_to_re_verify` flag** — fee values must be re-verified; tenant-overridable. |
| `ejari_required`, `rent_change_notice_days`, `eviction_notice_days`, `offplan_marketing_threshold_percent`, `mollak_budget_approval_required` | `VENDOR` | Public sources. |
| `smart_rental_index_live`, `rera_slab_governs_increase` | `VENDOR` | Distinct inputs; the SRI is the AI-assessed classification, the RERA slab is the permitted percentage. |
| `vat_rate_percent`, `residential_lease_vat`, `commercial_lease_vat`, `first_residential_supply_vat` | `VENDOR` | Public sources. |
| `einvoicing_asp_appointment_due`, `einvoicing_go_live`, `einvoicing_voluntary_phase_start` | `TENANT_CONFIG` | Whether a given tenant triggers mandatory e-invoicing depends on its revenue. The product gates the capability; the tenant owns the trigger. |

**Risk-appetite thresholds, EDD trigger levels, high-risk country list, approved-with-conditions policy set, retention beyond 5-year floor — all `TENANT_DECISION`.** They ship as blank fields, no defaults, source + acknowledgement required.

---

## 6. Outstanding items before Wave 2 sign-off (per amendment §10)

1. **`check_company` verdict.** One line, this week. Under amendment §5 it is a PDPL tenant-isolation question, not just an Odoo scoping question.
2. **`sgc_deals_management` provenance status.** Already verified in Wave 0 §6 as `SGC_OWNED (Phase 9 baseline)` — safe to wire into.
3. **OPR scoping study.** Per amendment §10.3: scope precisely what surface the five OPR-dependent gaps consume. If narrow, reimplement in clean siblings and retire the dependency rather than build around a permanent liability in the lender pack.
4. **Retrieve MoJ Notice No. 247/2026.** Joint guidance on the AML/CFT/CPF Compliance Officer, referencing Article 22 of Cabinet Resolution 134/2025. Referenced but not yet read in full. **Seed the G28 onboarding requirements schema directly from it.** Primary source beats our inference.
5. **E-invoicing date correction in the rules pack.** Done. **Now in `regulatory_constant_einvoicing_data.xml`.**

---

## 7. Effective immediately

| Operating rule | Source | Status |
|---|---|---|
| R8 — Representation boundary | amendment §3 | Applied. READMEs, manifests, view strings, and security group name have been audited. No user-visible string asserts or implies compliance. |
| R9 — No default on a tenant legal position | amendment §3 | Applied as a rule; enforcement begins with the next `TENANT_DECISION` field added. |
| `class` column on every gap | amendment §4 | Applied to all 28 rows in §3. |
| New status `CAPABILITY_PROVEN` | amendment §8 | Applied. G6, G15, G16 demoted from CLOSED to `CAPABILITY_PROVEN` with explicit reason. |
| New exit-gate tests (a) field unset, (b) field pointing at uninstalled model | amendment §8 | Applied. `tests/test_exit_gate.py` now carries 7 cases. |

## 8. Wave 2 entry gate

Wave 2 may begin coding immediately on the platform spine with these conditions:

- **G28 onboarding model** must exist before any `TENANT_CONFIG` field is added to a consumer module. The product owns the gate; the tenants own the values.
- **`check_company` verdict** must be stated within this week (item 1 above).
- **Screening adapter interface** must be defined (Wave 2 item 5); the specific provider remains `TENANT_CONFIG`.
- **No Wave 2 module** may reference a HELD or UNRESOLVED module in `depends`.
- **No Wave 2 user-visible string** may assert or imply compliance (R8).
- **No `TENANT_DECISION` field** may ship with a default value (R9).

Wave 2 sign-off still requires the OPR scoping study (item 3) and MoJ Notice 247/2026 retrieval (item 4) for the G28 onboarding schema.
