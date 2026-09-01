# AMENDMENT 001 — VENDOR/TENANT BOUNDARY

> **To:** `AGENT_BRIEF_REAL_ESTATE_WORKFLOW_GAP_CLOSURE.md`
> **Status:** CONTROLLING. Where this conflicts with the base brief, this wins.
> **Effective:** immediately, before any Wave 2 code.

---

## 1. WHY THIS AMENDMENT EXISTS

Waves 0 and 1 were executed under an unstated assumption: that we are building a compliance system for one operating brokerage. We are not.

**We are building a reusable, multi-tenant template.** Tenants are independent brokerages, property managers and developers. Each is separately licensed, separately supervised, and separately accountable.

This changes what "done" means, unblocks four Wave 2 items, and adds two gaps. Read this before writing further code.

---

## 2. WHAT WE ARE SHIPPING — THE SINGLE PARAGRAPH

We ship the machinery, not the compliance. The product provides controls, gates, evidence trails, terminal states and retention for real estate brokerage, property management and developer sales — configured per tenant, per jurisdiction. The tenant supplies the accountable people, the licences, the provider contracts and every legal position. We are a software vendor. We are not a DNFBP, we are not a regulated entity, and we do not become one by supplying regulated entities.

**Verified legal basis for this position:** under UAE third-party reliance rules, ultimate responsibility for CDD remains with the regulated entity even when it relies on third parties. Cabinet Resolution 134/2025 further requires that any third party relied upon must itself be regulated and supervised. We are neither. The obligation therefore cannot transfer to us, and we must not design as though it has.

**The one exception — see §5.** Data protection obligations *do* attach to us directly, as processor. They cannot be pushed to the tenant.

---

## 3. TWO NEW OPERATING RULES

**R8 — Representation boundary.** The product must never state or imply that it delivers, guarantees or constitutes compliance. This binds UI labels, field help text, report headers and footers, email templates, module descriptions, `__manifest__.py` summaries, docstrings, and any generated documentation.

- Prohibited: "AML compliant", "ensures compliance", "regulatory approved", "meets FATF requirements", "guarantees", "certified".
- Permitted: "supports the tenant's AML/CFT/CPF programme", "records evidence of", "configured by the tenant's appointed Compliance Officer", "as configured".

Rationale: a compliance claim in a product footer is a representation to a supervised entity's regulator. It is also a liability transfer we did not agree to.

**R9 — No default on a tenant legal position.** Any field representing a legal or risk judgement ships blank, with no default, no placeholder value, and a mandatory source citation and acknowledgement by the tenant before the dependent capability activates. Shipping a default here means taking a regulatory position on behalf of a supervised entity we do not represent.

---

## 4. THE CLASSIFICATION RULE — APPLY TO EVERY GAP AND EVERY FIELD

Every remaining gap, and every configurable field within it, carries exactly one class. Add a `class` column to the gap register and populate it for all 28 rows before Wave 2 begins.

| Class | Meaning | Ships as |
|---|---|---|
| `VENDOR` | We build it; it is in the template | Working code |
| `TENANT_CONFIG` | Structurally required, tenant-supplied at onboarding | Blank required field + readiness gate |
| `TENANT_DECISION` | A legal or risk position we must not take for them | Blank field, no default, source + acknowledgement required |

**Worked examples — treat as binding precedent:**

| Item | Class | Note |
|---|---|---|
| Rules pack engine, effective dating, jurisdiction scoping | `VENDOR` | The mechanism is ours |
| Statutory constants with a single unambiguous public source (DLD 4% transfer fee, 90-day notice, 12-month eviction notice, 5-year retention floor, 15-working-day BO update) | `VENDOR` | Seeded, but tenant-overridable with reason logged |
| REAR filing deadline | `TENANT_DECISION` | Sources conflict. **Never ship a default.** |
| Risk-appetite thresholds, EDD trigger levels, high-risk country list | `TENANT_DECISION` | Their EWRA, their board approval |
| Retention beyond the 5-year statutory floor | `TENANT_DECISION` | Floor is ours; anything above is theirs |
| Approved-with-conditions policy set | `TENANT_DECISION` | Their risk committee defines it |
| MLRO / Compliance Officer identity and appointment evidence | `TENANT_CONFIG` | We hold the record, they make the appointment |
| goAML organisation ID and registration status | `TENANT_CONFIG` | |
| Broker / developer / agent licence numbers, Trakheesi credentials | `TENANT_CONFIG` | |
| Screening provider identity, credentials, contracted fallback | `TENANT_CONFIG` | See §6 |
| Escrow bank and project account details | `TENANT_CONFIG` | |
| Jurisdiction activation (Dubai / Abu Dhabi / other) | `TENANT_CONFIG` | |
| ASP appointment for e-invoicing | `TENANT_CONFIG` | Their revenue, their FTA obligation |

Where a tenant overrides a `VENDOR`-seeded statutory constant, the system records who, when, and the stated reason. We do not block the override — jurisdictions and tenant legal advice vary — but we make it visible and attributable.

---

## 5. G27 — PDPL PROCESSOR OBLIGATIONS · VENDOR · HIGH

**This one does not transfer, and it is the amendment's most important addition.**

In a multi-tenant deployment we process personal data belonging to our tenants' clients: Emirates ID, passport, UBO records, source-of-funds evidence, and five years of retained records. Under Federal Decree-Law No. 45 of 2021 (PDPL) we act as processor, and processor duties attach to our architecture, not to tenant conduct.

Required work, `VENDOR` class, scheduled in Wave 2 alongside the party graph because both touch the same personal data surface:

1. **Data residency decision, documented.** Where the database physically sits, and whether that is contractually committed to tenants.
2. **Cross-border transfer assessment for every outbound integration.** The screening adapter is the live risk — if it transmits personal data to an offshore provider, PDPL cross-border rules engage. Assess before the adapter ships, not after.
3. **Encryption at rest and in transit** for identity documents and UBO records.
4. **Deletion mechanics at end of retention.** The retention framework from Wave 1 currently starts clocks. It must also terminate data. A clock that never fires deletion is a PDPL exposure wearing the costume of a control.
5. **Tenant-level data isolation proof.** Directly connected to the outstanding `check_company` verdict — see §8.
6. **Data Processing Agreement clauses** for the tenant contract, drafted by counsel, referenced from the product's onboarding pack.

Note the tension to resolve explicitly, not silently: the 5-year AML retention obligation and PDPL data minimisation pull in opposite directions. Document the reconciliation — retention under legal obligation is a lawful basis — and record it in the rules pack so it is defensible rather than assumed.

---

## 6. G28 — TENANT READINESS GATE · VENDOR · CRITICAL

Every item previously logged as a "hard blocker for Wave 2 sign-off" was misclassified. None of them were programme blockers. All of them are **product features**: they are the fields a tenant fills in at onboarding.

Build a first-class onboarding model that holds every `TENANT_CONFIG` and `TENANT_DECISION` value, with a completeness state per regulated capability.

**Gate scope is per capability, never system-wide.**

| Capability | Requires |
|---|---|
| goAML filing (REAR/STR/SAR) | MLRO appointed + goAML org ID + REAR deadline set with source |
| Any money-touching transition | Screening provider configured + fallback documented |
| Listing publication | Trakheesi credentials + valid broker licence + Form A workflow enabled |
| Tenancy contract issuance | Ejari credentials + jurisdiction activated |
| Off-plan sales | Developer registration + project escrow account + sales permit reference |
| Service charge collection | Mollak registration + approved budget reference |
| E-invoicing | ASP appointed (from 30 Oct 2026) + go-live 1 Jan 2027 |

A tenant missing Trakheesi credentials must be unable to publish listings while remaining fully able to run property management. Whole-system lockout on partial configuration gets the product removed, not completed.

**Wave 1 already gives us this behaviour for free.** With no screening provider configured, the fail-closed mixin returns INDETERMINATE, and INDETERMINATE blocks. That is correct by accident. Make it deliberate, name it, and test it.

Deliverables: the onboarding model; a readiness dashboard showing per-capability state; blocking that names the missing item and who must supply it; and an acknowledgement record (user, timestamp, cited source) for every `TENANT_DECISION`.

---

## 7. THE CONFUSION TRIPWIRE — STOP IF YOU CATCH YOURSELF DOING ANY OF THESE

You have read a great deal of UAE AML law. The predictable failure mode is drifting from *building a tool a regulated entity operates* into *acting as the regulated entity*. Stop and re-read §2 if you find yourself:

- Hard-coding a threshold, deadline or risk level that a tenant's compliance officer should own.
- Writing "compliant", "guaranteed", or "approved" into any user-visible string.
- Designing a workflow that assumes one company, one MLRO, one licence, one bank.
- Treating a missing tenant configuration as a bug to be worked around rather than a gate to be enforced.
- Selecting a specific screening vendor rather than defining an interface.
- Filling in a value because the build would otherwise stall. That impulse is the signal to raise it, not to resolve it.
- Building anything a construction contractor would recognise as their job.

---

## 8. WAVE 1 STATUS CORRECTION — DO THIS FIRST

The §3.1 taxonomy defines `CLOSED` as *enforced at runtime, with a passing test*. Four Wave 1 transitions do not meet that bar yet, because the primitives have no business consumers. Add a fifth status and restate:

| Status | Definition |
|---|---|
| `CLOSED` | Enforced at runtime on a live business path, with passing negative test |
| `CAPABILITY_PROVEN` | Primitive built and unit-tested; no business consumer wired yet |
| `PARTIAL` | Data exists, enforcement does not |
| `OPEN` | Neither |
| `BLOCKED` | Depends on a HELD or UNRESOLVED module |

Restated Wave 1: **G24 `CLOSED`** (the constant was migrated, the duplicate removed, the rules pack is itself the runtime source). **G6, G15, G16, G18 `CAPABILITY_PROVEN`**, each converting to `CLOSED` when its first consumer is wired and tested.

G15 in particular cannot be `CLOSED` while screening failover is listed as outstanding — the generic DLQ lane exists, the screening-specific fallback does not. The register will be read by an auditor, a regulator or a lender. A row marked CLOSED that means "framework built, nothing wired" costs more under examination than it saves today.

**Add two exit-gate tests.** The abstract `compliance_case_model` string field is a configuration hole the current five do not probe: (a) field unset, and (b) field pointing at a model not installed on that database. Both must raise. Both are how this pattern fails silently in production.

---

## 9. WAVE 2 IS FULLY UNBLOCKED — REVISED SEQUENCE

Items 7 through 10 were blocked pending a named screening provider. Under the template model **there is no provider to name.** We build the interface; tenants bring the provider.

**Screening adapter pattern, `VENDOR`:**
- An abstract adapter interface with a documented contract: submit, poll, result states, error taxonomy, timeout semantics.
- The failover state machine — primary → contracted fallback → documented manual process — as a `VENDOR` capability, with the specific endpoints as `TENANT_CONFIG`.
- The reference adapter is opt-in, not default.
- Cross-border transfer assessment per §5 before any adapter transmits personal data.

Revised Wave 2 order:
1. Party graph with recursive UBO traversal and the 2025 nominee exclusion — **strongest engineer, longest pole**
2. PF risk dimension across EWRA, policies, screening, profiling, EDD (G21)
3. G28 Tenant Readiness Gate model
4. G27 PDPL processor controls, alongside the party graph
5. Screening adapter interface and failover state machine (G15 → `CLOSED`)
6. Compliance-gated mixin wired into money-touching transitions (G1)
7. Objective threshold trigger at payment time (G4)
8. Tipping-off suppression, full technique per base brief §7 (G3)
9. Bounded document chase wired to KYC collection (G6 → `CLOSED`)
10. BO 15-working-day clock (G23), nominee/UBO correction (G22)
11. Agent licence gate (G18 → `CLOSED`), listing permit block (G10)

---

## 10. STILL OUTSTANDING — ANSWER BEFORE WAVE 2 SIGN-OFF

1. **`check_company` verdict.** Asked in the base brief with a 48-hour window; the finding has not been stated. Now materially more urgent: under §5 it is a PDPL tenant-isolation question, not just an Odoo scoping question. One line, this week.
2. **`sgc_deals_management` provenance status.** Named as the G1 wiring target, absent from the provenance table. If HELD or UNRESOLVED, item 6 above needs a different home.
3. **OPR scoping study.** Three referenced-but-absent QWeb templates mean the module is provenance-unresolved *and* functionally defective. Scope precisely what surface the five dependent gaps consume. If narrow, reimplement in clean siblings and retire the dependency rather than build around a permanent liability in the lender pack.
4. **Retrieve MoJ Notice No. 247/2026** — joint guidance on the AML/CFT/CPF Compliance Officer, referencing Article 22 of Cabinet Resolution 134/2025. Referenced but not yet read in full. Seed the G28 onboarding requirements schema directly from it: competence criteria, appointment evidence, notification duties. Primary source beats our inference about what tenants need.
5. **E-invoicing date correction in the rules pack.** ASP appointment extended to **30 October 2026**; go-live remains **1 January 2027**. Extension covers appointment only. `TENANT_CONFIG`, gated on tenant revenue ≥ AED 50m.

---

## 11. DEFINITION OF DONE — ADDENDUM

To the base brief's seven criteria, add:

8. The item carries exactly one class: `VENDOR`, `TENANT_CONFIG` or `TENANT_DECISION`.
9. No `TENANT_DECISION` field ships with a default value.
10. No user-visible string asserts or implies compliance (R8).
11. Where the item touches personal data, the PDPL position is documented: residency, any cross-border transfer, retention clock, deletion path.
12. The item functions correctly on a freshly provisioned tenant with no configuration — meaning it blocks cleanly and names what is missing, rather than erroring or defaulting through.

Criterion 12 is the multi-tenant test. Run it on every item.
