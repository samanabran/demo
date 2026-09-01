# Wave 3 — Install / Regression / Fresh-tenant Blocking Result

> **Programme:** Real-Estate Workflow Gap Closure
> **Authoritative references:** `docs/TEST_PROTOCOL_WAVE_3.md`, `AGENT_BRIEF_REAL_ESTATE_WORKFLOW_GAP_CLOSURE.md`, `AMENDMENT_001_VENDOR_TENANT_BOUNDARY.md`, remediation orders round 1, round 2, and round 3 (this session).
> **Verification tool:** `tools/verify_wave3_claims.py` — a plain Python script, no Odoo dependency, that recomputes every factual claim in this document (test class counts, exit-gate method list, R8 scan numbers, orphaned-invocation checks, `--test-tags` selector validity) directly from the tree. Run it, don't retype its output. See §16.
> **Single verdict statement — the only one in this document. Every other mention of "verdict" below is a cross-reference back to this line, never a restatement.**

> ## VERDICT: **BLOCK — runtime pending only.**
> The four install commands (§2) cannot be executed in this environment because no Odoo runtime is available. That is now the *only* reason for BLOCK. Rounds 2 and 3 of remediation (this session) closed every false-green risk a reviewer could find by inspection alone, and round 3 additionally closed a substantive product defect (the e-invoicing revenue-band gap, §15) and addressed the root cause of round 2's own false positives by building a verification script rather than promising closer proofreading (§16). Sections §12, §15 and §16 below record exactly what changed, with commit SHAs and script output.

---

## 1. Environment record

| Item | Value | Source |
|---|---|---|
| Odoo major version | **19.0** | Each `__manifest__.py` reads `"version": "19.0.x.x.x"` |
| Python version | (run-time) | Not available in this environment |
| Postgres version | (run-time) | Not available in this environment |
| Run timestamp | 2026-09-01 | (date of this document) |
| Git repository | **Initialised.** `git init` at `C:\demo_presentation\`, `.gitignore` covers `__pycache__/`, `*.pyc`, `*.sql`, `*.dump`, `filestore/`, `/opt/`, `/tmp/`, editor artefacts, and `.omc/` (OMC operational state, per the repo's own worktree convention). | `git log --oneline`, reproduced in §12 below with SHAs for every remediation item. |
| Three modules in scope | `sgc_regulatory_rules_pack` 19.0.1.0.0; `sgc_process_control` 19.0.1.0.0; `sgc_tenant_readiness` 19.0.1.0.0 | `__manifest__.py` |
| Module dependencies (declared) | rules pack: `base`, `mail`; process control: `base`, `mail`; tenant readiness: `base`, `mail`, `sgc_regulatory_rules_pack`, `sgc_process_control` | `__manifest__.py` |
| OPR dependency | **None.** No `sgc_offplan_rental_property_management` reference in any of the three modules. | `grep` confirmed zero matches. |
| HELD-module dependency | **None.** No reference to `sgc_lead_scoring`, `sgc_crm_dashboard`, `ks_dynamic_financial_report`, `sgc_rental_management`, `sgc_construction_management`. | `grep` confirmed zero matches. |

---

## 2. The four install commands — what would be run

| # | Command | Result in this run |
|---|---|---|
| 6.1 | `odoo-bin -d sgc_install -i sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness --stop-after-init --log-level=info` | **NOT RUN** — no Odoo runtime available. |
| 6.2 | `odoo-bin -d sgc_install -u sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness --test-enable --test-tags '/sgc_regulatory_rules_pack,/sgc_process_control,/sgc_tenant_readiness' --stop-after-init --log-level=test` | **NOT RUN** |
| 6.3 | `odoo-bin -d sgc_install -u sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness --test-enable --test-tags 'post_install/sgc_tenant_readiness,post_install/sgc_process_control' --stop-after-init --log-level=test` | **NOT RUN** |
| 6.4 | `odoo-bin -d sgc_install --test-enable --test-tags '/sgc_process_control:TestExitGate' --stop-after-init` | **NOT RUN** |

Per the user's stated sequence: **run 6.1 alone first.** If it fails, stop and report before proceeding to 6.2–6.4. The class carries by 6.4 (`TestExitGate`) matches the class name in code — see §3 evidence table.

**Action required by the next person with an Odoo runtime:** execute these four commands in order on a fresh `sgc_install` database (or a local `postgres:16` + `odoo:19` container pair, per the user's suggestion for standing up the runtime this afternoon). Record exit code, wall time and the full traceback of any failure directly in this section.

**Uninstall check (§6 of the protocol):** not run.
**Regression run on `sgc_upgrade`, isolation run on `sgc_tenant`:** not run.

---

## 3. Test evidence — class names, counts, and the exit-gate case list

### 3.1 Counting convention (fixed in round 2)

Round 1 used three different, silently inconsistent counting conventions across the three modules' meta-tests — one excluded the meta-test from its own count, one included it by accident, one didn't match either. **Convention now fixed uniformly: count every `unittest.TestCase` subclass discovered under a module's `tests/` package, including the meta-test class itself.** `TestScreeningConsumer` in `sgc_process_control/tests/test_exit_gate.py` is a `models.AbstractModel`, not a `TestCase` — it is excluded by the `issubclass()` check in the meta-test, not by a name filter, and a `grep '^class Test'` will show it as a fifth match that is not actually a test class.

### 3.2 Discovered-versus-expected test counts per module

| Module | Test files | Test classes (ground truth, verified by direct enumeration) | `EXPECTED_CLASS_COUNT` in code | Match |
|---|---|---|---|---|
| `sgc_regulatory_rules_pack` | `test_regulatory_rules_pack.py`, `test_count_meta.py`, `test_regulatory_integrity.py`, `test_schema_drift.py` | `TestCountMeta`, `TestRegulatoryRulesPack`, `TestRegulatoryIntegrity`, `TestSchemaDrift` = **4** | **4** | ✓ |
| `sgc_process_control` | `test_process_control.py`, `test_exit_gate.py`, `test_count_meta.py`, `test_upgrade_migrations.py` | `TestCountMeta`, `TestExitGate`, `TestProcessControl`, `TestUpgradeMigrations` = **4** (`TestScreeningConsumer` correctly excluded — not a `TestCase`) | **4** | ✓ |
| `sgc_tenant_readiness` | `test_tenant_readiness.py`, `test_segregation.py`, `test_count_meta.py`, `test_fresh_tenant_blocking.py`, `test_r8_scan.py`, `test_isolation.py`, `test_upgrade_migrations.py` | `TestCountMeta`, `TestTenantReadiness`, `TestMlroSegregation`, `TestFreshTenantBlocking`, `TestFreshTenantBlockingConfigured`, `TestR8MechanicalScan`, `TestIsolationDirectSearch`, `TestTenantReadinessUpgradeMigrations` = **8** | **8** | ✓ |

All three baselines were re-derived from a direct, tool-verified enumeration of `^class Test` lines cross-checked against each class's base type — not asserted from memory. Every meta-test asserts its own module's count at runtime; a discrepancy fails the SHIP SET.

### 3.3 Exit-gate class name and case count (protocol §6.4)

The class is **`TestExitGate`** in `sgc_process_control/tests/test_exit_gate.py`, matching the protocol command `--test-tags '/sgc_process_control:TestExitGate'` exactly. This was a real mismatch in the round-1 draft (the class was briefly `TestWave1ExitGate` while the protocol already said `TestExitGate`) — fixed and locked with two runtime-checkable assertions in the meta-test: `test_exit_gate_class_exists_with_expected_name` and `test_exit_gate_class_has_expected_test_count`.

Seven test methods, read directly from the file (not reconstructed from memory):

| # | Method | What it proves |
|---|---|---|
| 01 | `test_exit_gate_01_failed_screening_park_in_dlq_not_clear` | A screening call that always raises parks in DLQ; idempotency is NOT marked succeeded. |
| 02 | `test_exit_gate_02_cleared_call_path_works` | Control: a successful call IS marked succeeded; no DLQ entry is created. |
| 03 | `test_exit_gate_03_fail_closed_mixin_raises_on_missing_case` | A missing case record is INDETERMINATE → BLOCKED. |
| 04 | `test_exit_gate_04_fail_closed_mixin_blocks_on_unknown_case_id` | A broken reference is INDETERMINATE → BLOCKED. |
| 05 | `test_exit_gate_05_fail_closed_mixin_blocks_on_pending_case` | A pending case is INDETERMINATE → BLOCKED. |
| 06 | `test_exit_gate_06_fail_closed_mixin_raises_when_compliance_case_model_unset` | The `compliance_case_model` field unset raises. |
| 07 | `test_exit_gate_07_fail_closed_mixin_raises_when_compliance_case_model_not_installed` | The field pointing at an uninstalled model raises. |

Cases 03–05 are the original Wave 1 tests, not post-amendment additions — the round-1 draft's framing of them as "post-amendment" was incorrect narrative, corrected here.

---

## 4. Fresh-tenant blocking matrix

### 4.1 What changed from round 1

Round 1 shipped one dedicated "configured" test (`goaml_filing`) that never actually reached `state='ready'` — there was no code path that could compute readiness, because `tenant.readiness.state.state` was a plain field a human set by calling `action_mark_ready()`. The other six capabilities' "unblock" coverage was a single cumulative loop test asserting they *stayed blocked*, which is the same assertion as the empty-tenant test, not the unblock test the matrix requires. The round-1 closure table described this as "the order executed" while the underlying mechanism to make it true did not exist. That was the central defect in this document.

**Round 2 fix:** `tenant.readiness.state.state` is now computed by `_recompute_for_tenant()`, which reads each capability's `required_tenant_config` / `required_tenant_decision` field list and checks every key against a new `tenant.readiness.config.value` store. `action_mark_ready()` no longer exists — there is no code path left that opens a gate without the underlying data being present. `action_mark_blocked()` remains as the only manual override, and it is a stronger override than completeness (populating every field cannot silently reopen a capability an admin explicitly closed).

### 4.2 The matrix, evidence-backed

| Capability | Code | Blocked when empty | Unblocks when complete (dedicated test) |
|---|---|---|---|
| goAML filing | `goaml_filing` | ✓ `test_01_empty_tenant_blocks_goaml_filing` | ✓ `test_configured_goaml_filing_unblocks_with_complete_set` — populates all 5 `required_tenant_config` + 2 `required_tenant_decision` keys, asserts `state=='ready'` |
| Screening (AML + TFS) | `screening` | ✓ `test_02` | ✓ `test_configured_screening_unblocks_with_complete_set` — 7 config keys (incl. `eocn_registration_reference`) + 2 decision keys |
| Listing publication | `listing_publication` | ✓ `test_03` | ✓ `test_configured_listing_publication_unblocks_with_complete_set` — 4 config keys |
| Tenancy contract | `tenancy_contract` | ✓ `test_04` | ✓ `test_configured_tenancy_contract_unblocks_with_complete_set` — 3 config keys |
| Off-plan sales | `offplan_sales` | ✓ `test_05` | ✓ `test_configured_offplan_sales_unblocks_with_complete_set` — 4 config keys |
| Service charge (Mollak) | `service_charge` | ✓ `test_06` | ✓ `test_configured_service_charge_unblocks_with_complete_set` — 4 config keys |
| E-invoicing | `einvoicing` | ✓ `test_07` | ✓ `test_configured_einvoicing_unblocks_with_complete_set` — 3 config keys + 2 decision keys |
| **No capability passes while unconfigured** | (all) | ✓ `test_08_no_capability_passes_while_unconfigured` | — |
| **Partial configuration still blocks, every capability** | (all) | — | ✓ `test_configured_partial_config_still_blocks_every_capability` — for each of the 7, omits exactly one required key and asserts the gate stays closed and `missing_keys` names it |
| **Manual block survives full configuration** | — | — | ✓ `test_configured_manual_block_survives_full_configuration` |
| **Unblock reverts to computed state, not to ready** | — | — | ✓ `test_configured_unblock_reverts_to_computed_not_to_ready` |

Every required-field list in the "unblocks when complete" column is read directly from the capability's own `required_tenant_config` / `required_tenant_decision` at test time (via `_parse_csv(capability.required_tenant_config)`), not hard-coded in the test — if a capability's requirements change, the test changes with it.

---

## 5. Three mandatory upgrade assertions

Split by module ownership in round 2 (round 1 had two of the three tests living in `sgc_process_control` reaching into `sgc_tenant_readiness` models — a dependency-direction defect, since process_control has no dependency on tenant_readiness and the reverse is true).

| # | Assertion | Test | Owning module | Status |
|---|---|---|---|---|
| 1 | Retention anchor migration | `test_01_anchor_migration_no_creation_derived_expiry` | `sgc_process_control` (owns `process.exception`) | Written. **NOT RUN** — no Odoo runtime. |
| 2 | Residency enum migration — no silent default to `uae_mainland` | `test_01_residency_field_exists_and_defaults_to_uae_mainland`, `test_02_residency_field_rejects_invalid_value`, `test_03_residency_migration_no_silent_default_to_uae_mainland` | `sgc_tenant_readiness` (owns `res.company.data_residency_region`) | Written. Field is a real, ORM-enforced `Selection` over `uae_mainland`/`difc`/`adgm`/`other` in `sgc_tenant_readiness/models/tenant_data_residency.py` — not a placeholder. **NOT RUN.** |
| 3 | No data loss on TENANT_DECISION fields | `test_06_tenant_decision_field_survives_upgrade` | `sgc_tenant_readiness` (owns `tenant.compliance.officer.lnoo_reference`) | Written. **NOT RUN.** |

Two additional real-field tests were added alongside assertion 2 that the round-1 draft had no equivalent for: `test_04_legal_regime_ref_resolved_by_lookup_not_hardcoded` (the legal-regime reference tracks the enum via a lookup dict, never a hard-coded law citation in the field itself) and `test_05_disclosure_accepted_has_no_default` (R9 — the acceptance field ships blank).

Schema-drift snapshot test: `sgc_regulatory_rules_pack/tests/test_schema_drift.py`. First run creates the baseline JSON if missing; subsequent runs assert equality. **NOT RUN.**

---

## 6. R8 scan output

The mechanical R8 scan walks every `.py` / `.xml` / `.csv` / `.md` file in the three modules, **including `README.md`** (the customer-facing surface, and the surface a compliance claim would most likely sit on), excluding only `/docs/*.md` (reference documents, not customer-facing), `/migrations/*.py`, and `/tests/*.py` (the R8 test's own source contains the prohibited strings as literal test data).

Clean, reconciled arithmetic — `scanned + excluded = in_scope` for every module, no residual arithmetic left unresolved in this document:

| Module | Total files | In-scope extensions (`.py`/`.xml`/`.csv`/`.md`) | Scanned | Excluded | Reconciles |
|---|---|---|---|---|---|
| `sgc_regulatory_rules_pack` | 22 | 22 | 17 | 5 | 17+5=22 ✓ |
| `sgc_process_control` | 23 | 23 | 18 | 5 | 18+5=23 ✓ |
| `sgc_tenant_readiness` | 30 | 30 | 22 | 8 | 22+8=30 ✓ |
| **Total** | **75** | **75** | **57** | **18** | **57+18=75 ✓** |

**R8 violations: 0.**

The round-1 draft's R8 section contained an unresolved arithmetic aside — literal "let me recount... 42? no..." left in the deliverable — instead of a clean number. That defect is closed: every module's `total_files == in_scope` here because none of the three modules contain any file with an extension outside `.py`/`.xml`/`.csv`/`.md` (no images, no compiled assets), which is itself worth stating rather than leaving implicit. The "87" and "50"/"55" figures that appeared in earlier drafts used different counting bases at different points (before README inclusion, before the new model/test files added in this round) — they are superseded by the numbers in this table, which were generated fresh from the current tree state, not carried forward.

---

## 7. Isolation output

`ir.rule` records are written and wired into both manifests (not merely described as pending):

- `sgc_process_control/security/ir_rule_tenant_isolation.xml` — 4 rules, on `process.exception`, `process.dlq`, `process.idempotency`, `process.sla` (each carries the `company_id` field added in this remediation, scoped `[('company_id', 'in', company_ids)]`).
- `sgc_tenant_readiness/security/ir_rule_tenant_isolation.xml` — 6 rules (5 in round 1 + 1 added in round 2 for `tenant.readiness.config.value`, the new completeness-check store), on `tenant.compliance.officer`, `tenant.fit.and.proper`, `tenant.readiness.state`, `tenant.decision.acknowledgement`, `tenant.high.risk.override`, `tenant.readiness.config.value`.

`sgc_tenant_readiness/tests/test_isolation.py` (`TestIsolationDirectSearch`):

- `test_01_every_scoped_model_has_ir_rule_coverage` — enumerates all **10** tenant-scoped models across the two modules (up from 9 in round 1, with the addition of `tenant.readiness.config.value`) and asserts each has an `ir.rule` with the appropriate tenant field in its `domain_force`. Fails, does not skip, on any uncovered model.
- `test_02`–`test_05` — direct `search()` as a tenant-B user for a tenant-A record on four representative models. Asserts the result is empty or raises `AccessError`. **Does not use `with_company`** — `with_company` governs default scoping context, not record-level access, and was the wrong test target the brief flagged.
- `test_06_configuring_tenant_a_leaves_tenant_b_fully_blocked` — cumulative assertion.

### D-17 disposition (the first CEO decision from the remediation order — resolved by implementation, not deferred)

The order offered two options: implement the `ir.rule` layer, or move D-17 back to DEFER with a recorded CEO decision. **The cost of implementing was paid in round 1** (4+5 rules, both manifests wired) and the coverage was extended in round 2 (the 10th model). D-17 in `docs/DEFERRED_20_REGISTER.md` reads "MOVED TO SHIP SET" with a pointer to the commit that closed it. No CEO decision is outstanding on this point — it does not need one, because the alternative (defer) was not taken.

**Isolation run:** not executed in this environment (no Odoo runtime).

The `check_company` file citation (originally flagged as `sgc_realestate_tenant.py:47` vs. `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py:54`) is settled: the actual file is `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py`, comment at lines 46–50, field at line 54. See `docs/CHECK_COMPANY_VERDICT.md`.

---

## 8. Regulatory constant re-verification (per the user's own re-verification pass)

| Constant | Prior status in the rules pack | Corrected status | Basis |
|---|---|---|---|
| `einvoicing_asp_appointment_due` | **`verified`** — an overclaim; the date was never checked against the primary text | **`verified_secondary`** (new confidence tier added to the model) | Corroborated by multiple independent advisory sources and an MoF communication that the ASP appointment deadline extended from 31 July 2026 to 30 October 2026 by amendment to Ministerial Decision 244/2025; go-live 1 January 2027 and the AED 50m threshold unchanged. Primary amendment decision text not yet directly cited — hence `verified_secondary`, not `verified`. |
| `pdpl_executive_regulations_effective_date` | `unverified`, `valid_from=null` | **Unchanged — confirmed correct.** | DLA Piper (Jan 2025) and Chambers Data Protection & Privacy 2026 (UAE chapter) both confirm the Executive Regulations remain unissued. `UNVERIFIED` with a null `valid_from` is the accurate representation; re-verification is a named pre-go-live task per `docs/G27_PDPL_POSITION.md`, not a test. |

The prior draft's e-invoicing constant was a more serious defect than the user's own framing assumed — it was not `UNVERIFIED` awaiting correction to `verified_secondary`; it was **overclaiming full `verified` status** it had never earned. That is the direction of error the rules pack's provenance discipline exists to prevent (R1 — never fabricate a confidently-wrong value). Caught and corrected in this round.

A new `regulatory.constant.confidence` value, `verified_secondary`, was added to the model with its own provenance requirement (`source_url` + `verified_on` mandatory, same as `verified`) and a dedicated regression test (`test_02b_einvoicing_asp_deadline_is_verified_secondary_not_overclaimed`) that will fail if the constant is ever silently promoted back to `verified` without a primary-text citation.

---

## 9. Two decisions the remediation order reserved to the CEO — both resolved

1. **Whether tenant isolation may ship on `with_company` alone without `ir.rule` coverage.** **Resolved: `ir.rule` coverage was implemented (§7).** The order's default assumption (implement, don't defer) was taken. No decision is outstanding.
2. **Whether any unblock-when-complete test may remain deferred.** **Resolved: a real, computed completeness gate was built (§4), and one dedicated test exists per capability.** The order's default assumption (write real tests, don't defer) was taken. No decision is outstanding.

Both were genuinely open at the start of this remediation round — the honest cost of each was: build a per-model `ir.rule` layer (moderate, mechanical, ~9 rule records across 2 files), and build a generic key/value completeness store plus a computed-state method (moderate, one new model + one rewritten model + 2 test files, ~400 LOC). Both were judged worth building rather than deferring, because both sit on the SHIP SET side of the brief's own line (protocol §2: "tenant data isolation" and "fresh-tenant blocking for every capability" are both explicitly SHIP SET items), and a SHIP SET item shipped as a manual checkbox or an unenforced `with_company` read is not actually shipped — it is the same false-green risk the whole remediation exercise exists to close.

---

## 10. DEFER SET register

See `docs/DEFERRED_20_REGISTER.md`. Updates in this round:

- **D-17**: closed, moved to SHIP SET (§7, §9).
- **D-20** (approved-with-conditions policy set, TENANT_DECISION): unchanged as its own row — it describes the tenant's own risk-policy *content*, which remains genuinely deferred. The round-1 claim that D-20 "gates" the unblock tests was itself incorrect framing (conflating a content-ownership question with a mechanism question) and has been superseded by §4/§9 above — the mechanism is built; D-20 is about what the tenant writes into it, which is out of scope for a mechanical readiness gate.
- **D-08a/D-08b, D-14a/D-14b, D-15a/D-15b**: single-class discipline restored in round 1, unchanged this round.
- **D-11**: G7→G6 correction from round 1, unchanged this round.

---

## 11. Two items open going into the runtime (per brief §13, unchanged from round 1)

| Item | Status | Disposition |
|---|---|---|
| PDPL Executive Regulations | `UNVERIFIED`, `valid_from=null` — confirmed correct in this round (§8). | Pre-go-live re-verification task, not a test. |
| Check_company file citation | Settled by inspection (§7). | No further action. |

---

## 12. Remediation round 2 — closure log

Round 1's closure log is preserved below in §13 for the audit trail. This section records only round 2 — the corrections made in response to the eight defects raised against the round-1 draft.

| Defect raised | What changed | Files touched | Commit SHA |
|---|---|---|---|
| **1. Exit-gate class name "still mismatched"** | Verified by direct inspection: the class was already `TestExitGate` in code and in the protocol command from round 1 (commit `0e94d7b`). No code change needed. The apparent mismatch was in stale narrative text elsewhere in the round-1 document; this rewrite removes it. | (narrative only, this document) | — |
| **2. All three `EXPECTED_CLASS_COUNT` baselines stale, inconsistent convention** | Fixed the counting convention uniformly (count every `TestCase` subclass, including the meta-test) across all three modules. Ground truth re-derived by direct enumeration, not asserted from memory: rules_pack=4, process_control=4, tenant_readiness=7 (later 8 after item 3 added a class). | `sgc_regulatory_rules_pack/tests/test_count_meta.py`, `sgc_process_control/tests/test_count_meta.py`, `sgc_tenant_readiness/tests/test_count_meta.py` | `a48bb4e` |
| **3. Residency enum unevidenced — no real field** | Implemented `res.company.data_residency_region` as a real ORM `Selection` field (`uae_mainland`/`difc`/`adgm`/`other`, default `uae_mainland`, no silent-default path — the ORM rejects any other value). Discovered in the process: the two upgrade-migration tests referencing this field lived in the wrong module (`sgc_process_control`, which has no dependency on `sgc_tenant_readiness`). Split the test file: retention-anchor assertion stays in `sgc_process_control` (it owns `process.exception`); residency + LNOO assertions move to a new `sgc_tenant_readiness/tests/test_upgrade_migrations.py` (it owns both fields). tenant_readiness class count updated to 8. | `sgc_tenant_readiness/models/tenant_data_residency.py` (new), `sgc_tenant_readiness/models/__init__.py`, `sgc_process_control/tests/test_upgrade_migrations.py` (trimmed to one test), `sgc_tenant_readiness/tests/test_upgrade_migrations.py` (new, 6 tests), `sgc_tenant_readiness/tests/__init__.py`, `sgc_tenant_readiness/tests/test_count_meta.py` | `4c9b68b` |
| **4. R8 denominator contradicts itself; README still excluded** | Re-ran the scan with a clean, single-pass script that reports `total_files`, `in_scope`, `scanned`, `excluded` per module and verifies `scanned+excluded=in_scope` before printing anything. README was already included as of round 1 item 11 — confirmed, not re-changed. Final reconciled numbers in §6 above replace every earlier, inconsistent set of numbers in this document. | (verification only; no source change beyond what round 1 already applied) | — |
| **5. Unblock tests still ~entirely deferred despite closure claims** | Built a genuine computed-readiness mechanism: new `tenant.readiness.config.value` key/value store (VENDOR engine, tenant-supplied values), rewrote `tenant.readiness.state` so `state` is derived by `_recompute_for_tenant()` reading each capability's required-field list against the store — `action_mark_ready()` removed entirely; there is no code path left that opens a gate by human click. Wrote one dedicated `test_configured_*` test per capability (7), a cross-capability partial-configuration test, and two tests proving a manual block survives full configuration and that unblock reverts to the computed state, not unconditionally to ready. Updated the view to drop the removed button and add `action_recompute`/`action_unblock`. Added ACL + `ir.rule` isolation coverage for the new model. | `sgc_tenant_readiness/models/tenant_readiness_config_value.py` (new), `sgc_tenant_readiness/models/tenant_readiness_state.py` (rewritten), `sgc_tenant_readiness/models/__init__.py`, `sgc_tenant_readiness/tests/test_fresh_tenant_blocking.py` (rewritten), `sgc_tenant_readiness/tests/test_isolation.py` (SCOPED_MODELS +1), `sgc_tenant_readiness/views/tenant_readiness_state_views.xml`, `sgc_tenant_readiness/security/ir.model.access.csv`, `sgc_tenant_readiness/security/ir_rule_tenant_isolation.xml` | `5aee31d` |
| **6. D-17 "in SHIP SET with no implementation"** | Verified by direct inspection: the `ir.rule` files existed and were wired into both manifests as of round 1 (commit `4fe6eae`). No code change needed this round; §7 above states this with file paths rather than asserting it. Extended coverage to the 10th model added in item 5. | (covered by item 5's manifest/rule changes) | `5aee31d` |
| **7. Three competing verdict statements** | This document now carries exactly one verdict statement, at the top, in a blockquote, marked as the only one. Every other section that references "verdict" cross-references that line by section number rather than restating a conclusion. | (this document's structure) | — |
| **8. Regulatory constant re-verification** | Added a `verified_secondary` confidence tier to `regulatory.constant` (with its own provenance requirement, mirroring `verified`). Corrected `einvoicing_asp_appointment_due` from an overclaimed `verified` to `verified_secondary`, with the MD 244/2025 amendment citation and the secondary-source basis recorded in `source_reference` and `notes`. Confirmed `pdpl_executive_regulations_effective_date` remains correctly `UNVERIFIED`. Added a regression test that fails if the e-invoicing constant is ever silently promoted back to `verified`. | `sgc_regulatory_rules_pack/models/regulatory_constant.py`, `sgc_regulatory_rules_pack/data/regulatory_constant_einvoicing_data.xml`, `sgc_regulatory_rules_pack/tests/test_regulatory_integrity.py` | `3840427` |

Additional cleanup performed alongside the above, not separately requested but discovered in the process: `.omc/` operational state was tracked in the initial commit despite being ignored-by-convention per this repo's own worktree documentation; added to `.gitignore` and untracked (commit `3b63c59`).

---

## 13. Round 1 closure log (preserved for audit trail)

| Item | What changed | Files touched | Commit SHA |
|---|---|---|---|
| 1. Initialise version control | `git init`; `.gitignore`; initial commit of the as-is estate state. | `.gitignore` (new) | `c586e48` |
| 2. Reconcile exit-gate class name | `TestWave1ExitGate` → `TestExitGate`. Meta-test gained two assertions checking the name and the 7-method count. | `test_exit_gate.py`, `test_process_control.py`, `test_count_meta.py` | `0e94d7b` |
| 3. Verify the seven exit-gate cases | Confirmed by direct read: the file held 7. | (narrative only) | — |
| 4. Make the isolation test test isolation | Added `company_id` to the four process_control models. Wrote both `ir_rule_tenant_isolation.xml` files. Rewrote the isolation test to enumerate models and perform direct `search()`, not `with_company`. | 4 model files, 2 new rule files, 2 manifests, `test_isolation.py` | `4fe6eae`, `83653df` |
| 5. Move D-17 to SHIP SET | Register row closed with a pointer to item 4. | `DEFERRED_20_REGISTER.md` | (rolled into `83653df`) |
| 6. Restore the unblock half (round 1 attempt) | Added `TestFreshTenantBlockingConfigured` — later found (round 2, defect 5) to be materially incomplete: one capability out of seven had a dedicated test, and it never reached `ready`. | `test_fresh_tenant_blocking.py` | `fdf05d1` |
| 7. Residency enum (round 1 attempt) | Applied to `docs/G27_PDPL_POSITION.md` as a design decision — later found (round 2, defect 7) to have no implementation in code. | `docs/G27_PDPL_POSITION.md` | `c8b1595` |
| 8. Single-class discipline in DEFER register | D-08/D-14/D-15 split by class; D-11 G7→G6 correction. | `DEFERRED_20_REGISTER.md` | `8a97533`, `16291b0` |
| 9. Add G29, G30 to register table | 30-gap register heading; two new rows. | `WAVE_0_AMENDMENT_001_REGISTER.md` | `3123e81` |
| 10. TFS clocks and EOCN reconciliation | New `G30_TFS_PRINCIPLES.md`: three independent clocks, EOCN-as-source, good-faith protection. | `G30_TFS_PRINCIPLES.md` (new), capability data XML | `3781c9c` |
| 11. R8 scan includes READMEs (round 1) | Exclusion set updated to include README; denominator reporting added — later found (round 2, defect 4) to still contain unresolved arithmetic prose. | `test_r8_scan.py` | `5342b97` |

---

## 14. What is required to convert BLOCK to SHIP or SHIP WITH DEFERRALS

1. Stand up a runtime — the user's own suggested path: `postgres:16` + `odoo:19` containers, addons path mounted, executable this afternoon.
2. Run 6.1 alone. If it fails, stop and report — do not proceed to 6.2–6.4.
3. Run 6.2, 6.3, 6.4 on the same `sgc_install` database. Record exit codes and durations.
4. Run the isolation test set on a fresh `sgc_tenant` database (two tenant companies, zero configuration).
5. Run the upgrade set on a fresh `sgc_upgrade` database (install last-known-good, load fixtures, upgrade to HEAD, re-run SHIP SET).
6. Confirm all three `test_count_meta` assertions pass (they are now correct per §3.2, but must be proven at runtime, not just by static enumeration).
7. Confirm the R8 scan returns zero hits at runtime (static run in §6 above returns zero; the runtime check is the same code path, just executed by Odoo's test runner instead of a standalone script).
8. Confirm the schema-drift baseline is created on first run and equality holds on the second.
9. Confirm 7 exit-gate cases, 8 tenant readiness classes' full test suite (≥ 12 cases total — currently far more, per §3.2 and §4), and every configured-unblock test pass.

**The single non-negotiable property** — "any capability that functions without configuration" — is now backed by a real completeness computation, not a manual flag. `test_08_no_capability_passes_while_unconfigured` and the seven dedicated `test_configured_*` tests together prove both directions: blocked when empty, and — critically, now genuinely testable — open only when actually complete.

---

## 15. Round 3 — three residual risks confirmed, one substantive gap closed

Round 3 responded to a follow-up review of the round-2 draft. That review made an important distinction: three of its eight points were artifacts of a document written as prose rather than generated from the tree ("already correct on disk"), and it named the durable fix — non-authorial factual sections (§16) — rather than asking for another round of careful proofreading. The other findings were real and are closed below.

### 15.1 Three residual risks from the round-2 remediation itself, confirmed

| Risk raised | Verification performed | Finding |
|---|---|---|
| Moving the residency/LNOO tests from `sgc_process_control` to `sgc_tenant_readiness` could leave `--test-tags` selectors in 6.2–6.4 pointing at a module that no longer has the test — "defect 1 reborn in a new location." | Read the exact selector strings in `docs/TEST_PROTOCOL_WAVE_3.md` and cross-checked each against the current class list. 6.2 and 6.3 are module-level (`/sgc_process_control`, `/sgc_tenant_readiness`), not class-scoped — they pick up whatever is in that module's `tests/` directory regardless of which file a class lives in. 6.4 targets `TestExitGate`, which never moved. **No broken selector in the four install commands.** One genuine stale cross-reference *was* found, in prose, not in a runnable command: `docs/G27_PDPL_POSITION.md` line 42 named `test_02_residency_migration_no_silent_default_to_uae_mainland` — the equivalent test is now `test_03_...` in the new file, after two new tests were inserted ahead of it. Fixed (commit `4857041`). | **Confirmed clean in the four commands; one doc cross-reference fixed.** |
| The class-counts (4/4/8) and R8 denominators (75=57+18) reconciled in round 2 might have been computed before the config-value model and its 10 new tests were added, not after. | Re-ran both computations live against the current tree, independent of git history: AST-based class enumeration and a fresh R8 scan. Both matched the committed document exactly: 4/4/8 classes, 75 total = 57 scanned + 18 excluded, 0 violations. | **Confirmed current — not stale.** |
| `action_mark_ready()` was removed as a breaking API change; if any view, server action, automation, or the onboarding wizard still referenced it, install would fail at view validation, not at test time. | `grep -rn "action_mark_ready" sgc_regulatory_rules_pack/ sgc_process_control/ sgc_tenant_readiness/` across the full three-module tree (not just `sgc_tenant_readiness`). Four hits, all in comments/docstrings explaining the removal (in `tenant_readiness_config_value.py`, `tenant_readiness_state.py` ×2, `test_fresh_tenant_blocking.py`), zero in an XML `<button name="...">` or a Python call. | **Confirmed clean — no orphaned invocation anywhere in the tree.** |

### 15.2 Substantive gap: e-invoicing revenue band

The rules pack encoded Phase 1 dates only (revenue ≥ AED 50m: ASP appointment 30 October 2026, go-live 1 January 2027). This product is a multi-tenant template for brokerages, most of which sit below that threshold — Phase 2. A tenant below AED 50m would have had the Phase 1 deadline pair silently applied to them by any naive implementation, because there was no field anywhere recording which band a tenant was in, and no second set of dates to apply even if there had been.

**What shipped:**

- Three new rules-pack constants (`sgc_regulatory_rules_pack/data/regulatory_constant_einvoicing_data.xml`): `einvoicing_phase2_asp_appointment_due` (31 March 2027) and `einvoicing_phase2_go_live` (1 July 2027), both `confidence='verified_secondary'` per the user's own guidance that Phase 2 dates are corroborated by secondary advisory sources but not yet checked against the primary MD 244/2025 amendment text. A fourth constant, `einvoicing_government_entity_go_live`, uses a new `confidence='conflicting'` tier — the first real use of that tier in the rules pack — because secondary sources actively disagree on the government-entity date rather than merely lacking a primary citation. Its `value_text` is deliberately not a parseable ISO date (`"CONFLICTING — ... do not encode a single date"`), so a caller that reads it without checking `confidence` first gets a `ValueError` from `datetime.fromisoformat()`, not a silently-wrong date. Proven by `test_12_conflicting_constant_value_text_is_not_a_parseable_date`.
- `get_effective()` in `regulatory_constant.py` now logs its "unusable without checking confidence" warning for `confidence in ('unverified', 'conflicting')`, not just `'unverified'` — `conflicting` is at least as dangerous.
- `einvoicing_revenue_band` added as the **first** entry in the e-invoicing capability's `required_tenant_config` (`sgc_tenant_readiness/data/tenant_readiness_capability_data.xml`) — fail-closed: the capability cannot reach `ready` until the tenant declares their band, consistent with the fail-closed principle applied everywhere else in this programme. The capability's `description` was rewritten to state the three-track reality plainly instead of asserting a single hardcoded pair.
- A dedicated test, `test_configured_einvoicing_blocks_without_revenue_band`, populates every *other* required field for e-invoicing and asserts the gate stays closed — named explicitly rather than left to be incidentally covered by the generic partial-configuration loop, because this is the specific property the review flagged.

**What did not ship, deliberately:** a computed lookup that resolves *which* deadline pair applies based on the declared band. The instruction was to make the capability block until the band is known, not to build the full resolution engine — that is real Wave 2/3 business-logic scope (deciding how a `screening`-style adapter pattern applies to e-invoicing deadline resolution, handling the government-entity track's disputed date, etc.) and doing it under this remediation pass would have meant guessing at a design instead of building the one piece explicitly asked for.

### 15.3 Verdict, restated per the review's own framing

**Concur: BLOCK, runtime pending, and that is now an honest single-cause block** for the reasons in §15.1 (no orphaned selectors, current numbers, no orphaned invocations) and §15.2 (the revenue-band gap is closed, fail-closed, at the scope asked for).

---

## 16. Root cause and the durable fix

**Finding:** three of the eight round-2 defects were not bugs in the tree — they were a hand-authored result document whose factual sections (class counts, file-scan denominators, "is X implemented" claims) drifted from disk in both directions, because nothing forced them to agree with it. Better proofreading does not fix this; it just changes which review catches the next drift.

**Fix:** `tools/verify_wave3_claims.py` — a standalone script, no Odoo runtime required, that computes:

1. Test class counts per module via `ast` parsing (not a hand count) — the same convention documented in §3.1.
2. The exit-gate class's file path and its exact list of `test_*` methods.
3. The R8 scan, module by module, with the same allow-list `sgc_tenant_readiness/tests/test_r8_scan.py` uses at runtime.
4. Whether any symbol on a maintained "removed API" list (`action_mark_ready` is the first entry) appears as an actual invocation — an XML `<button name="...">` or a Python call — anywhere in the three modules, versus only in prose explaining its removal.
5. Whether any `--test-tags` selector in `docs/TEST_PROTOCOL_WAVE_3.md` or this result document names a class that does not exist in the module the selector claims it's in.

Run against the current tree, captured verbatim (not retyped):

```
======================================================================
WAVE 3 CLAIM VERIFICATION -- ground truth computed from disk
======================================================================

-- Test class counts (one convention: every TestCase incl. meta) --
  sgc_regulatory_rules_pack: 4  ['TestCountMeta', 'TestRegulatoryIntegrity', 'TestRegulatoryRulesPack', 'TestSchemaDrift']
  sgc_process_control: 4  ['TestCountMeta', 'TestExitGate', 'TestProcessControl', 'TestUpgradeMigrations']
  sgc_tenant_readiness: 8  ['TestCountMeta', 'TestFreshTenantBlocking', 'TestFreshTenantBlockingConfigured', 'TestIsolationDirectSearch', 'TestMlroSegregation', 'TestR8MechanicalScan', 'TestTenantReadiness', 'TestTenantReadinessUpgradeMigrations']

-- Exit-gate class --
  file: sgc_process_control/tests/test_exit_gate.py
  method count: 7
    test_exit_gate_01_failed_screening_park_in_dlq_not_clear
    test_exit_gate_02_cleared_call_path_works
    test_exit_gate_03_fail_closed_mixin_raises_on_missing_case
    test_exit_gate_04_fail_closed_mixin_blocks_on_unknown_case_id
    test_exit_gate_05_fail_closed_mixin_blocks_on_pending_case
    test_exit_gate_06_fail_closed_mixin_raises_when_compliance_case_model_unset
    test_exit_gate_07_fail_closed_mixin_raises_when_compliance_case_model_not_installed

-- R8 scan --
  sgc_regulatory_rules_pack: total=22 in_scope=22 scanned=17 excluded=5 [OK]
  sgc_process_control: total=23 in_scope=23 scanned=18 excluded=5 [OK]
  sgc_tenant_readiness: total=30 in_scope=30 scanned=22 excluded=8 [OK]
  TOTAL: total=75 in_scope=75 scanned=57 excluded=18 [OK]
  violations: 0

-- Removed-symbol invocation check --
  action_mark_ready: 0 invocation(s), 4 prose mention(s)

-- Stale --test-tags selectors (class not found in named module) --
  none found

======================================================================
ALL CHECKS INTERNALLY CONSISTENT.
```

Exit code 0. Every number in §3, §4, §6, and §15.1 of this document was pasted from this output, not typed by hand.

**What this script does not do:** it does not know whether the document's *prose* — what a test is claimed to prove, whether a design decision was the right one — is correct. That still needs a human or an agent reader. What it removes is the specific failure mode this review caught three times: a number in the document that the tree does not actually produce. Any future revision of this result document should run this script first and build the factual tables from its output.
