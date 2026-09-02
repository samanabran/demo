# AGENT BRIEF — REAL ESTATE WORKFLOW GAP CLOSURE PROGRAMME

> **Authority:** Founder/CEO · **Classification:** Build-directive
> **Supersedes:** §4 of `REAL_ESTATE_WORKFLOW_MISALIGNMENT.md`
> **Reference role:** This is the controlling brief for the entire gap-closure programme. No existing logic, guardrail, or workflow is being rebuilt; only enforcement gaps in a foundation that is already largely correct at the data layer and largely absent at the enforcement layer.

---

## 1. MISSION

Close the gap between the desired-state blueprint (`FULL REAL ESTATE WORKFLOW.htm`, 15 charts C01–C15) and the current SGC estate at `C:\demo_presentation\`, for three segments — **brokerage, property management, and developer sales & handover** — without breaching provenance holds and without building construction execution.

You are not rebuilding what works. You are closing enforcement gaps.

---

## 2. NON-NEGOTIABLE OPERATING RULES

**R1 — Never fabricate.** Every regulatory constant, form name, threshold, notice period, fee and filing window must trace to a primary regulator source (DLD, RERA, ADREC, MoET, FTA, UAE FIU, Central Bank rulebook, uaelegislation.gov.ae). If you cannot source it, mark it `UNVERIFIED` in the rules pack, set no default, and raise it. A confidently wrong threshold is worse than a blank one.

**R2 — Never touch a HELD module.** `sgc_lead_scoring`, `sgc_crm_dashboard`, `sgc_construction_management`, `ks_dynamic_financial_report`, `sgc_rental_management` must not appear in `depends` of anything you create, and must not be read from, copied from, or referenced in code comments.

**R3 — Never build new IP inside an UNRESOLVED module.** See §4 (Architecture Directive One). This is the rule most likely to be broken by convenience.

**R4 — One gap, one status.** No gap may carry two closure states.

**R5 — Ask, do not assume.** §11 lists the questions you must have answered. If you hit a decision not covered by this brief and not answerable from a primary source, stop and ask. Do not pick the interpretation that lets you keep moving.

**R6 — Every change ships with evidence.** Test, migration note, provenance entry, and a row update in the gap register. A phase that improves speed and weakens evidence is a net loss in a supervised business.

**R7 — No dependency cycles.** Compliance modules must not depend on transaction modules. See Architecture Directive Two.

---

## 3. FIRST TASK — REBASELINE BEFORE YOU BUILD ANYTHING

Do not start Workstream A until this is delivered.

### 3.1 — Repair the gap register

Re-derive §1 of `REAL_ESTATE_WORKFLOW_MISALIGNMENT.md` with exactly one status per gap. Known defects: G11 is counted in both Closed and Partial; the Open list contains seven items but is counted as six; G4 carries a hybrid status.

Adopt this taxonomy and apply it strictly:

| Status | Definition |
|---|---|
| `CLOSED` | Control exists **and is enforced at runtime** and has a passing test |
| `PARTIAL` | Data structures or reports exist; enforcement does not |
| `OPEN` | Neither data nor enforcement exists |
| `BLOCKED` | Closure depends on a HELD or UNRESOLVED module |

Under this taxonomy G4 is `PARTIAL`, not Open. Expect the corrected count to be materially worse than the current headline. Report it accurately anyway.

### 3.2 — Add the gaps the register is missing

Minimum additions:

- **G21 — Proliferation Financing not modelled.** `CRITICAL`. Cabinet Resolution 134/2025 requires PF risk in EWRA, internal policies, name screening, customer risk profiling and EDD triggers. `aml_compliance` has no PF dimension. This is a schema change to the risk engine, not a label change.
- **G22 — UBO definition is stale.** `HIGH`. Nominee shareholders and nominee directors cannot be deemed UBOs under the 2025 Executive Regulations. Verify what the current `res.partner` / party model does and correct it.
- **G23 — No 15-working-day BO update clock.** `HIGH`. New time-bound obligation on beneficial-owner and nominee information changes.
- **G24 — Regulatory rules pack not abstracted.** `CRITICAL` (upgraded from `PARTIAL`). AED 55,000 is hard-coded in `goaml_report_print.xml`. With the governing law replaced in Oct/Dec 2025, hard-coded constants are now a liability, and they block multi-emirate operation entirely.
- **G25 — Rent-review reference is stale.** `MEDIUM`. Dubai's Smart Rental Index (live January 2025) is building-level and AI-assessed; the RERA slab system still governs the permitted increase percentage. C11 PM15 must reference both correctly and must not treat them as the same thing.
- **G26 — E-invoicing readiness unassessed.** `HIGH`, time-critical. UAE e-invoicing voluntary phase opened 1 July 2026; published guidance set ASP appointment by 31 July 2026 and go-live 1 January 2027 for revenue ≥ AED 50m, with at least one report of a deadline extension. **Verify current FTA position within 5 working days** and report. Touches `uae_einvoice_core` in Phase 6.

### 3.3 — Confirm or refute the `check_company` finding

§2.2 records that `check_company=True` was "removed where inappropriate" per a comment at `sgc_realestate_tenant.py` line 47. Read the code. If company scoping was genuinely removed, that is a potential multi-tenant data leak and outranks everything else in this brief. Report within 48 hours either way.

### 3.4 — Deliver a provenance decision on `sgc_offplan_rental_property_management`

See §4.

---

## 4. ARCHITECTURE DIRECTIVES — DECIDED, NOT OPEN FOR DEBATE

### Directive One — Build clean, extend dirty

`sgc_offplan_rental_property_management` is UNRESOLVED provenance at ~21,814 LOC and is currently the named home for five gap closures (G7, G9, G10, G11, G12). Phase 0 of `REAL_ESTATE_BROKERAGE_ROLLOUT.md` treats an unresolved addon on the candidate path as a STOP.

**Do not write new logic inside OPR.** Create clean sibling modules that depend on OPR and inject behaviour through inheritance, overrides and constraints. Rationale: new IP stays unambiguously original and separately attributable in the lender pack; if OPR's provenance later fails, your work survives and can be re-pointed; and the provenance audit of OPR does not have to complete before delivery starts.

Proposed clean siblings:

| New module | Purpose | Closes |
|---|---|---|
| `sgc_regulatory_rules_pack` | All jurisdictional constants as data | G24, enables all |
| `sgc_process_control` | Exception queue, SLA/attempt counters, idempotency, DLQ | G6, G15, G16 |
| `sgc_compliance_gate` | Pre-money enforcement mixin + party graph + PF | G1, G2, G3, G4, G21, G22, G23 |
| `sgc_listing_compliance` | Permit block, de-listing, owner screening hook | G10 |
| `sgc_transaction_conditions` | Conditions register, seller obligations, Ejari gate | G9, G11, G25 |
| `sgc_collections_ladder` | Dunning with named terminal exits | G7 |
| `sgc_commission_gate` | Three-condition release, hold-back, clawback | G8 |
| `sgc_developer_lane` | Escrow, sales permit, Oqood, default ladder, handover | G12 |
| `sgc_jointly_owned_property` | Mollak / budget-then-bill | G14 |
| `sgc_demand_engine` | Signal → decision → outcome → tuning | G13 |
| `sgc_agent_licensing` | Permit validity, dual agency, SoD | G18 |

Run the OPR file-by-file provenance audit in parallel as its own workstream. It must not sit on the critical path.

### Directive Two — Compliance must not depend on transactions

§3.10 correctly identifies that `aml_compliance` and `kyc_management` do not depend on `sgc_commission` or OPR, so G1 cannot be enforced by wiring. **Do not fix this by adding those dependencies** — it inverts the layering and creates a cycle the moment the compliance modules need anything back.

Correct pattern: define an **abstract mixin** in the compliance layer, e.g. `sgc.compliance.gated`, exposing a `_assert_compliance_cleared()` guard. Every money-touching model (reservation, booking, deposit receipt, `account.payment` confirmation, commission release) inherits the mixin and calls the guard in its own transition method. Dependency flows one way: transaction modules depend on compliance; compliance depends on nothing downstream.

The guard must **fail closed**. If the compliance state cannot be determined — screening provider timeout, missing record, integration error — the answer is BLOCK, not ALLOW. Write the test that proves this before writing the guard.

### Directive Three — No regulatory constant in code, ever

Every threshold, notice period, form name, fee rate, filing window and retention clock lives in `sgc_regulatory_rules_pack` as data, scoped by jurisdiction and effective-dated (`valid_from` / `valid_to`). Effective dating is mandatory, not optional — the AML framework changed twice in Q4 2025 and you will need to prove which rule applied on a given transaction date.

Migrate the hard-coded AED 55,000 out of `goaml_report_print.xml` as the first entry. Do not leave a duplicate behind.

### Directive Four — Terminal states and retention are structural

G16 is mis-rated as Medium. Under Decree-Law 10/2025 with penalties reaching AED 100m for legal entities, and a 5-year retention obligation that survives unchanged from the prior regime, retention is the evidentiary backbone of every other control. Treat as `HIGH`. Every workflow gets named terminal states, and each terminal state starts a retention clock defined in the rules pack.

---

## 5. CORRECTED BUILD SEQUENCE

### Wave 0 — Rebaseline (blocks everything)
Deliver §3 in full. No code beyond the rules-pack skeleton.

### Wave 1 — Platform spine
Nothing in Wave 2 is buildable correctly without these.
1. `sgc_regulatory_rules_pack` — effective-dated, jurisdiction-scoped constants (G24)
2. `sgc_process_control` — exception queue with classification routing; SLA clocks; bounded-attempt counters with named exhaustion states; idempotency keys; retry-with-backoff; dead-letter queue with alerting (G6, G15)
3. Retention clocks and terminal-state framework (G16)
4. Segregation-of-duties enforcement at model level: lister ≠ approver, raiser ≠ approver, agent ≠ own compliance reviewer (G18 partial)

**Wave 1 exit gate:** a deliberately failed screening call lands in the DLQ, raises an alert, and is visibly *not* a clear result. Demonstrate this. It is the single most dangerous failure mode in the entire chain.

### Wave 2 — Licence protection
5. Party graph model — client, co-buyer, corporate entity, every UBO above threshold, POA holders, third-party payers, with recursive traversal (G2, G22)
6. PF risk dimension across EWRA, policies, screening, risk profiling, EDD (G21)
7. `sgc.compliance.gated` mixin + fail-closed guard, wired into every money-touching transition (G1)
8. Objective threshold trigger firing on facts at payment time (G4)
9. Screening failover → documented manual fallback; provider outage never clears (G15)
10. Tipping-off suppression — see §7 for the required technique (G3)
11. Bounded document-chase with attempt exhaustion → case suspended (G6)
12. "Approved with conditions" as a real outcome: escrow-only, no-cash, restricted channels, enhanced monitoring frequency
13. 15-working-day BO update clock (G23)
14. Agent licence validity gate at lead assignment and at commission entitlement (G18)
15. Hard publish block without permit number + de-listing across all channels (G10)

**Wave 2 exit gate:** it is technically impossible to bank a deposit, sign a contract or publish an advertisement without the corresponding clearance. Prove it by attempting each and being refused.

### Wave 3 — Transaction spine and recurring revenue
16. Conditions register with owner and deadline; bounded extensions (G9)
17. Seller obligations gate before transfer appointment (G9)
18. Ejari registration gate — keys withheld until registered (G11)
19. 90-day notice engine + Smart Rental Index / RERA slab rent review (G11, G25)
20. Dunning ladder with named terminal exits: legal, forfeiture, write-off with dual approval (G7)
21. Mixed-line tax determination — exempt, zero-rated, standard-rated on one invoice (C10 FI2)
22. Three-condition commission release gate with agent-visible pending reasons (G8)
23. Clawback automation on credit note (C10 FI13)
24. Emergency maintenance lane with bypass authority; vendor licence and insurance validation (G19)
25. De-duplication arbitration with survivorship rules (G20)

### Wave 4 — Segment scale
26. Developer lane: project registration, dedicated project escrow, marketing threshold gate, sales permit, Oqood interim registration, regulated default ladder, resale/assignment consent, handover (G12)
27. Jointly owned property: budget-then-bill, segregated funds, reserve and sinking fund, special levy, arrears blocking transfer (G14)
28. Owners Association kit added to the kit matrix (currently absent)

### Wave 5 — Demand intelligence
29. `sgc_demand_engine` — signal aggregation, decision rules, outcome measurement, threshold tuning (G13)

Wave 5 last, deliberately. It needs clean history from Waves 2–3 to exist.

---

## 6. VERIFIED REGULATORY BASELINE

Seed the rules pack from this. Every entry carries a `source_url`, a `verified_on` date and a `confidence` flag. Re-verify all of it before go-live.

| Constant | Position | Status |
|---|---|---|
| AML governing law | Federal Decree-Law No. 10 of 2025, effective 14/10/2025, repeals the 2018 law | VERIFIED |
| AML executive regulations | Cabinet Resolution No. 134 of 2025, in force 14/12/2025, replaces Cabinet Res. 10/2019 | VERIFIED |
| Proliferation Financing | Now mandatory across EWRA, internal policies, name screening, customer risk profiling, EDD | VERIFIED |
| UBO — nominees | Nominee shareholders and nominee directors **cannot** be deemed UBOs | VERIFIED |
| BO information updates | Within **15 working days** of any identified change | VERIFIED |
| Record retention | **5 years** minimum, unchanged under the new regime | VERIFIED |
| STR/SAR | File with the FIU **immediately, regardless of transaction value** | VERIFIED |
| FIU suspension power | FIU Head may order a **10-day suspension** | VERIFIED |
| Penalties | Legal entities up to **AED 100 million** | VERIFIED |
| REAR trigger — real estate | Cash, single or multiple payments, **at or above AED 55,000** of the property value or part of it; also virtual assets or funds converted from them | VERIFIED |
| REAR filing deadline | CONFLICTING SOURCES — one says no timeline, another says 10 days | **UNVERIFIED — MUST RESOLVE** |
| Cash commission receipt | One source states brokerage commission received in cash ≥ AED 55k does **not** itself trigger REAR | **UNVERIFIED — MUST RESOLVE** |
| Gaming threshold AED 11,000 | Applies to gaming operators only. **Does not apply to real estate.** Do not import it | VERIFIED |
| Dubai advertising | Owner-signed Form A via **Trakheesi**; unique permit number must appear on every advertisement; fee approx. AED 1,020 per ad type | VERIFIED / fee to re-verify |
| Dubai sale forms | Form F sale agreement; Form B buyer-broker | VERIFIED |
| Dubai transfer | **4%** DLD transfer fee plus admin, at a registration trustee office | VERIFIED |
| Tenancy registration | **Ejari** mandatory; landlord's legal obligation; unified tenancy contract; fee approx. AED 221.75 | VERIFIED / fee to re-verify |
| Rent & eviction notice | Law 26/2007 as amended by Law 33/2008 — **90 days** notice for any change to rent or terms; **12 months** notarised notice for eviction on permitted grounds | VERIFIED |
| Rent increase ceiling | **RERA slab system** governs the permitted percentage. **Dubai Smart Rental Index** (live Jan 2025) provides building-level AI-assessed classification. These are two distinct inputs — model both | VERIFIED |
| Off-plan escrow | Law 8 of 2007 — account in the project's name, dedicated exclusively to that project | VERIFIED |
| Off-plan marketing threshold | Law 9/2007 and RERA practice — developer registration, and a threshold such as 20% construction completion or a 20% cash/bank guarantee | VERIFIED / re-verify current practice |
| Oqood | Initial sale registration acts as interim title. DLD published fee **2% seller + 2% buyer** (~4% combined), plus admin fee approx. AED 3,100; commonly shifted wholly to buyer by contract | VERIFIED / admin fee to re-verify |
| Service charges | Law 6 of 2019 with **Mollak** — no imposition or collection before RERA budget approval; owner payments only into Mollak-registered accounts | VERIFIED |
| Abu Dhabi | Law 3 of 2015 with ADREC — project registration, project escrow under executive regulations, registration of buyer's interest before completion. Forms, systems and notice periods differ from Dubai | VERIFIED |
| VAT | 5% on brokerage and management fees. Residential leases exempt; commercial standard-rated; first supply of new residential zero-rated within the qualifying period | VERIFIED |
| E-invoicing | Voluntary phase from 1 July 2026; guidance set ASP appointment by 31 July 2026 and go-live 1 Jan 2027 for revenue ≥ AED 50m; at least one report of extension | **TIME-CRITICAL — VERIFY IN 5 DAYS** |

---

## 7. IMPLEMENTATION NOTES ON THE THREE HARDEST ITEMS

**Tipping-off suppression (G3).** On the reporting path you must: prevent the client partner from being added as a follower on the case record; block portal visibility of the record and any linked document; suppress `mail.thread` outbound notification and any automated status email or WhatsApp triggered by the state change; hide the state from every client-facing view and report; and log every internal access to the record. Also handle the indirect leak — a suddenly frozen transaction with no explanation is itself a signal, so agree a scripted holding position with the compliance officer and store it as a rules-pack entry, not as tribal knowledge.

**Fail-closed guard (G1).** The guard has three outcomes, not two: CLEARED, BLOCKED, and INDETERMINATE. INDETERMINATE must behave as BLOCKED and must raise an exception-queue entry. Most implementations of this pattern fail by treating a missing record as "no adverse finding." Write the negative tests first.

**Three-condition commission gate (G8).** All three conditions must be independently re-evaluated at release time, not cached from earlier in the lifecycle: funds cleared and reconciled, registration completed, compliance case *still* approved. The third is the one people drop — a case can be re-opened between contract and payout. Agents must see pending status with the specific blocking reason; opacity here generates more friction than the hold-back itself.

---

## 8. DEFINITION OF DONE

An item is done when all seven hold:

1. Enforcement is at runtime, not documentation. The bad path is *impossible*, not discouraged.
2. A negative test proves the block, and a fail-closed test proves indeterminate states block.
3. No regulatory constant appears in code; all are rules-pack entries with source and verified date.
4. No HELD module in `depends`; no new logic inside an UNRESOLVED module.
5. `tools/audit_coupling_lint.py --fail-on-findings` exits 0 on the candidate path.
6. The gap register row moves to `CLOSED` with date and commit hash.
7. A migration note exists for tenants with existing data.

---

## 9. REPORTING

Weekly, one page, no narrative padding:
corrected gap counts by status; wave progress against the sequence in §5; rules-pack entries added and any still `UNVERIFIED`; exception-queue volume by classification once Wave 1 lands; blockers with named owner and date; and any regulatory change detected since the last report.

Flag immediately, do not wait for the weekly: any multi-tenant data-scoping finding; any HELD module discovered on the candidate path; any regulatory change affecting a live constant; any instruction in this brief that turns out to be wrong.

---

## 10. SCOPE BOUNDARY — RESTATED

**In:** brokerage sales, brokerage leasing, property management, owners association, developer sales and handover including project registration, escrow, sales permits, inventory release, payment plans, interim registration, snagging, key release and title issuance.

**Out:** construction programme and site management, contractor procurement, variations and materials, engineering design and certification, mortgage origination and lending decisions. Certified construction progress enters the developer lane as an *input to escrow drawdown* only. If you find yourself modelling a work package or a contractor payment, you have crossed the line — stop and raise it.

---

## 11. ANSWER THESE BEFORE WAVE 1

Do not guess. Each of these changes the architecture.

1. **Jurisdiction scope for phase one** — Dubai only, or Dubai plus Abu Dhabi? Are DIFC or ADGM in scope? This determines whether the rules pack ships with one jurisdiction populated or three, and whether ADREC forms are Wave 1 or Wave 4.
2. **Is off-plan developer revenue real now, or next year?** If now, the developer lane moves from Wave 4 into Wave 2/3 and the programme is materially larger.
3. **Is Owners Association actually in scope?** It is absent from the current kit matrix. Half-building it is worse than omitting it — collections without an approved budget is a compliance failure, not a feature gap.
4. **Odoo version and edition.** `module_generator_v19` implies v19; `hr_payroll_community` implies Community. But Appendix C of the rollout playbook flags `project_hr_skills` as Enterprise-licensed with no subscription evidence, installed on 4 of 6 databases. Confirm the target, and confirm that exposure is resolved.
5. **Which screening provider(s), and is there a contracted secondary?** The failover requirement in Wave 2 is unbuildable without a named fallback.
6. **Annual revenue relative to AED 50m** — determines your e-invoicing wave and whether the ASP appointment date is already behind you.
7. **Who is the appointed Compliance Officer / reporting officer of record, and are they goAML-registered?** Reviewer independence in C07 is a role assignment, not a code feature, and Wave 2 cannot be signed off without it.
8. **Is `sgc_deals_management` cleared, held or unresolved?** It is named in G1 as a wiring target but does not appear in the provenance table in §5 of the misalignment document. This is an unclosed reference.
9. **Confirm the REAR filing deadline** with MoET or FIU directly. Public analyses conflict. This is a configured value that carries penalty exposure.

---

## 12. CLOSING NOTE TO THE AGENT

The estate is in better shape than the gap count suggests. The risk engine, goAML export, contract templates, commission lifecycle and portal syndication are real assets. What is missing is almost entirely the same thing repeated twenty times: **a control that exists as data but is not enforced at the moment it matters.**

Build the enforcement layer once, properly, in Wave 1, and most of the remaining gaps become configuration rather than construction. Build it piecemeal inside each business module and you will build it eleven times and test it none.

---

## REFERENCE USE — READ BEFORE EVERY DELIVERABLE

This brief is the controlling reference. Before producing any artefact for this programme:

1. Check the operating rule that governs the work (R1–R7).
2. If the work is a build item, confirm the wave and the gap(s) it closes against §5.
3. If the work touches a regulatory constant, verify it against §6 and the rules pack.
4. If the work touches a HELD module, stop — R2.
5. If the work adds logic inside an UNRESOLVED module, stop — R3.
6. If the work changes a gap status, apply the §3.1 taxonomy strictly — R4.
7. Before signing off, run the seven-point DoD checklist in §8.

Status decisions, regulatory claims and architectural choices that contradict this brief are blocked.
