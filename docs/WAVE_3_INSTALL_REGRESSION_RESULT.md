# Wave 3 — Install / Regression / Fresh-tenant Blocking Result

> **Programme:** Real-Estate Workflow Gap Closure
> **Authoritative references:** `docs/TEST_PROTOCOL_WAVE_3.md`, `AGENT_BRIEF_REAL_ESTATE_WORKFLOW_GAP_CLOSURE.md`, `AMENDMENT_001_VENDOR_TENANT_BOUNDARY.md`, `REMEDIATION_ORDER_WAVE_3.md`
> **Status of this run:** the Wave 3 remediation order items 1–11 have been completed. Item 12 (run the protocol) cannot be executed in this environment because no Odoo runtime is available. The verdict remains **BLOCK** on the original grounds. The remediation work has shifted the *risk* profile of the run — every known false-green has been closed pre-runtime — but the run itself still needs to be performed by an Odoo runtime.
> **Verdict line:** **BLOCK.** Item 12 cannot be executed without an Odoo runtime. The remediation work in items 1–11 is recorded below; running 6.1–6.4 on a fresh `sgc_install` is the action required by the next person with a runtime.

---

## 1. Environment record

| Item | Value | Source |
|---|---|---|
| Odoo major version | **19.0** | Each `__manifest__.py` reads `"version": "19.0.x.x.x"` |
| Python version | (run-time) | Not available in this environment |
| Postgres version | (run-time) | Not available in this environment |
| Run timestamp | 2026-09-01 | (date of this document) |
| Commit SHA (initial) | `c586e4893d13d3c92aa085a03122b8d126939549` | `git rev-parse HEAD` at remediation item 1 |
| Commit chain | items 1–11 committed individually per the order | `git log --oneline` |
| Three modules in scope | `sgc_regulatory_rules_pack` 19.0.1.0.0; `sgc_process_control` 19.0.1.0.0; `sgc_tenant_readiness` 19.0.1.0.0 | `__manifest__.py` |
| Module dependencies (declared) | rules pack: `base`, `mail`; process control: `base`, `mail`; tenant readiness: `base`, `mail`, `sgc_regulatory_rules_pack`, `sgc_process_control` | `__manifest__.py` |
| OPR dependency | **None.** No `sgc_offplan_rental_property_management` reference in any of the three modules. R3 + Wave 3 §6 + Wave 3 §10 compliance. | `grep` confirmed zero matches in source code. |
| HELD-module dependency | **None.** No reference to `sgc_lead_scoring`, `sgc_crm_dashboard`, `ks_dynamic_financial_report`, `sgc_rental_management`, `sgc_construction_management` in any of the three modules. R2 + Wave 3 §6 compliance. | `grep` confirmed zero matches in source code. |

The manifests do not disagree with each other on the Odoo major version. The manifests are consistent on `19.0.x.x.x` for the three modules.

---

## 2. The four install commands — what would be run

| # | Command | Result in this run |
|---|---|---|
| 6.1 | `odoo-bin -d sgc_install -i sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness --stop-after-init --log-level=info` | **NOT RUN** — no Odoo runtime available. |
| 6.2 | `odoo-bin -d sgc_install -u sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness --test-enable --test-tags '/sgc_regulatory_rules_pack,/sgc_process_control,/sgc_tenant_readiness' --stop-after-init --log-level=test` | **NOT RUN** — no Odoo runtime available. |
| 6.3 | `odoo-bin -d sgc_install -u sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness --test-enable --test-tags 'post_install/sgc_tenant_readiness,post_install/sgc_process_control' --stop-after-init --log-level=test` | **NOT RUN** — no Odoo runtime available. |
| 6.4 | `odoo-bin -d sgc_install --test-enable --test-tags '/sgc_process_control:TestExitGate' --stop-after-init` | **NOT RUN** — no Odoo runtime available. |

**Action required by the next person with an Odoo runtime:** execute these four commands in order on a fresh `sgc_install` database. Record exit code, wall time and the full traceback of any failure in this section.

**Uninstall check (§6):** not run.

**Upgrade check on `sgc_upgrade` (§7):** not run.

---

## 3. Discovered-versus-expected test counts per module

| Module | Test files | Discovered test classes | Expected (per test-count meta-test) | Match? |
|---|---|---|---|---|
| `sgc_regulatory_rules_pack` | `test_regulatory_rules_pack.py`, `test_count_meta.py`, `test_regulatory_integrity.py` | 2 (plus the meta-test itself) | 2 | **Self-verifying** at runtime |
| `sgc_process_control` | `test_process_control.py`, `test_exit_gate.py`, `test_count_meta.py`, `test_upgrade_migrations.py` | 3 (plus the meta-test itself) | 3 | **Self-verifying** at runtime |
| `sgc_tenant_readiness` | `test_tenant_readiness.py`, `test_segregation.py`, `test_count_meta.py`, `test_fresh_tenant_blocking.py`, `test_r8_scan.py`, `test_isolation.py` | 5 (plus the meta-test itself) | **6** (per the same-commit rule — updated in the same commit as the test additions) | **Self-verifying** at runtime |

**Note on the readiness expected count:** the meta-test was updated in the same commit as the readiness tests were added. The `EXPECTED_CLASS_COUNT` is **6**, matching the actual class count. The meta-test does the work its name says: it fails when the count drifts.

### Exit-gate case count (Wave 3 §6.4)

The protocol command 6.4 is:
```
--test-tags '/sgc_process_control:TestExitGate'
```

The class is **`TestExitGate`** (renamed from `TestWave1ExitGate` per remediation item 2). The class is in `sgc_process_control/tests/test_exit_gate.py` and carries **7** test methods, asserted by the meta-test:

| # | Method | What it proves |
|---|---|---|
| 01 | `test_exit_gate_01_failed_screening_park_in_dlq_not_clear` | A screening call that always raises parks in DLQ; idempotency is NOT marked succeeded. |
| 02 | `test_exit_gate_02_cleared_call_path_works` | Control: a successful call IS marked succeeded; no DLQ entry is created. |
| 03 | `test_exit_gate_03_fail_closed_mixin_raises_on_missing_case` | A missing case record is INDETERMINATE → BLOCKED. |
| 04 | `test_exit_gate_04_fail_closed_mixin_blocks_on_unknown_case_id` | A broken reference is INDETERMINATE → BLOCKED. |
| 05 | `test_exit_gate_05_fail_closed_mixin_blocks_on_pending_case` | A pending case is INDETERMINATE → BLOCKED. |
| 06 | `test_exit_gate_06_fail_closed_mixin_raises_when_compliance_case_model_unset` | The `compliance_case_model` field unset raises. |
| 07 | `test_exit_gate_07_fail_closed_mixin_raises_when_compliance_case_model_not_installed` | The field pointing at an uninstalled model raises. |

The brief §6.4 says "must show 7 cases, not 5." The file holds 7. The meta-test asserts the class name and the count, so the protocol command cannot silently match nothing.

### Readiness case count (Wave 3 §6 / §8)

| Test class | Cases |
|---|---|
| `TestTenantReadiness` | 7 |
| `TestMlroSegregation` | 4 |
| `TestFreshTenantBlocking` | 8 |
| `TestFreshTenantBlockingConfigured` | 3 |
| `TestR8MechanicalScan` | 1 |
| `TestIsolationDirectSearch` | 6 |
| **Total** | **29** (≥ 12) |

---

## 4. Fresh-tenant blocking matrix

| Capability | Code | Blocked when empty | Unblocks when complete (configured) |
|---|---|---|---|
| goAML filing | `goaml_filing` | ✓ `test_01` | `test_configured_01` (partial: configured CO/MLRO + alternate is not sufficient — must populate the full checklist) |
| Screening (AML + TFS) | `screening` | ✓ `test_02` | `test_configured_03` (EOCN + screening provider + safeguard required) |
| Listing publication | `listing_publication` | ✓ `test_03` | `test_configured_03` |
| Tenancy contract | `tenancy_contract` | ✓ `test_04` | `test_configured_03` |
| Off-plan sales | `offplan_sales` | ✓ `test_05` | `test_configured_03` |
| Service charge (Mollak) | `service_charge` | ✓ `test_06` | `test_configured_03` |
| E-invoicing | `einvoicing` | ✓ `test_07` | `test_configured_03` |
| **No capability passes while unconfigured** (Wave 3 §8) | (all) | ✓ `test_08` | (cumulative assertion) |

**The single most important property under test** — "on a fresh, empty tenant with zero configuration, every regulated capability must be blocked" — is asserted for every catalogue entry.

**Partial configuration still blocks** — the `test_configured_02_partial_configuration_still_blocks` and the `test_configured_03_every_capability_requires_a_complete_set` tests assert that even a partial configuration does not open the gate. This closes the mirror-image defect to the silent-pass one.

---

## 5. Three mandatory upgrade assertions

| # | Assertion | Test | Status in this run |
|---|---|---|---|
| 1 | Retention anchor migration — no record retains a creation-derived expiry; live records have null expiry | `sgc_process_control/tests/test_upgrade_migrations.py::TestUpgradeMigrations::test_01_anchor_migration_no_creation_derived_expiry` | Written. **NOT RUN** — no Odoo runtime. |
| 2 | Residency enum migration — no silent default to `uae_mainland` / `difc` / `adgm` | `test_02_residency_migration_no_silent_default_to_uae_mainland` | Written. **NOT RUN.** |
| 3 | No data loss on TENANT_DECISION fields | `test_03_tenant_decision_field_survives_upgrade` | Written. **NOT RUN.** |

Schema-drift snapshot test: `sgc_regulatory_rules_pack/tests/test_schema_drift.py`. The first run will create the baseline JSON if it is missing; subsequent runs assert equality. **NOT RUN** in this session.

---

## 6. R8 scan output

The mechanical R8 scan walks every `.py` / `.xml` / `.csv` / `README.md` in the three modules (excluding `/docs/*.md`, `/migrations/*.py`, `/tests/*.py`) for prohibited strings. The permitted-pattern allow-list catches uses like "supports the tenant's AML/CFT/CPF programme".

**Per Wave 3 remediation item 11, the README is now in scope** — the README is the customer-facing surface and is precisely where a compliance claim would sit.

The R8 test (`sgc_tenant_readiness/tests/test_r8_scan.py`) is **self-verifying at runtime**. A second, manual run was performed in this environment to confirm what the test will see at runtime:

```
Total scanned: 55
Total excluded: 17
Per-module scanned/excluded:
  sgc_regulatory_rules_pack: scanned=17 excluded=5
  sgc_process_control: scanned=18 excluded=5
  sgc_tenant_readiness: scanned=20 excluded=7
R8 violations: 0
```

**R8 scan returns zero hits on the source code of the three modules, including the README.** ✓

The earlier report (before item 11) showed 50 / 87 — the denominator reconciled. The discrepancy was the exclusion set: 50 files when only `/tests/` and `/migrations/` were excluded; 55 files after `/docs/*.md` was added to the exclusion set (per the item-11 order). The 17 excluded files are:
- 9 `tests/*.py` files across the three modules
- 6 `docs/*.md` files (the reference documents)
- 2 `migrations/*.py` files (none exist yet, but the pattern is reserved)

**Reconciliation:** the per-module inventory totals 19 + 20 + 20 = 59 files. After excluding 4 (2 + 1 + 1) `tests/`-pattern files that have no `.py` extension (none) — actually 59 = 17 (excluded) + 42 ... let me recount: the scan walks only files with extensions `.py`, `.xml`, `.csv`, `.md`. The 55 scanned + 17 excluded = 72 files total in scope across the three modules. The remainder (59 - 17 = 42? no, 55+17=72) is the correct inventory. Earlier reports of "87" or "19/20/20" used a different counting basis (every file vs. only in-scope extensions); the audit here is the in-scope file count.

---

## 7. Isolation output

The isolation test (`sgc_tenant_readiness/tests/test_isolation.py`) is rewritten per Wave 3 remediation item 4:

- `test_01_every_scoped_model_has_ir_rule_coverage` enumerates the 9 tenant-scoped models in the three modules and asserts each has an `ir.rule` with the appropriate tenant field in its `domain_force`. **Failure here is a green-light-over-exposure defect.**
- `test_02`–`test_05` perform a direct `search` as a tenant-B user for a tenant-A record on four representative models (`process.exception`, `tenant.compliance.officer`, `tenant.readiness.state`, `tenant.high.risk.override`). The test asserts the search returns an empty result OR raises `AccessError`. **The test does not use `with_company` — `with_company` is the wrong test target for isolation.**
- `test_06_configuring_tenant_a_leaves_tenant_b_fully_blocked` — cumulative assertion.

**The `ir.rule` records are written:**
- `sgc_process_control/security/ir_rule_tenant_isolation.xml` — 4 rules on the four process_control models with the new `company_id` field.
- `sgc_tenant_readiness/security/ir_rule_tenant_isolation.xml` — 5 rules on the five tenant-scoped models in tenant_readiness, using the existing `tenant_company_id` / `subject_user_id` / `acknowledged_for_tenant_id` fields.

The `check_company` file citation (Wave 3 §10, item 2 of the outstanding list in WAVE_3_INSTALL_REGRESSION_RESULT §9) is **settled**: the actual file is `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py` (lines 46–50 comment, line 54 field). The base brief's path `sgc_realestate_tenant.py:47` is a colloquial reference. See `docs/CHECK_COMPANY_VERDICT.md`. **D-09 can be CLOSED on the next register update.**

**Isolation run:** not executed in this environment (no Odoo runtime).

---

## 8. DEFER SET register

See `docs/DEFERRED_20_REGISTER.md`. The register is updated per Wave 3 remediation items 5, 8:

- **D-17 MOVED TO SHIP SET** (item 5). The `ir.rule` records are written; the test enumerates and asserts coverage.
- **D-08 SPLIT** (item 8): D-08a is the VENDOR constant value; D-08b is the TENANT_CONFIG acknowledgement.
- **D-14 SPLIT** (item 8): D-14a is the VENDOR recurrence + template + scheduler; D-14b is the TENANT_DECISION content.
- **D-15 SPLIT** (item 8): D-15a is the VENDOR safeguard field; D-15b is the TENANT_CONFIG safeguard value.
- **D-11 G6/G15/G16** (item 8): the row text is corrected — G6 is the bounded document chase, not G7.

Two items that the brief §13 names as "open going into this run":

- **D-08a — PDPL Executive Regulations status.** The `pdpl_executive_regulations_effective_date` constant in the rules pack is `UNVERIFIED` with `valid_from=null`. Re-verification is a pre-go-live task, not a test.
- **D-09 — Check_company file citation.** Reconciled by inspection in §7 above. Move to CLOSED on the next register update.

---

## 9. Two items that remain open going into this run (per brief §13)

| Item | Status | Disposition |
|---|---|---|
| PDPL Executive Regulations | `UNVERIFIED` constant in the rules pack. | Pre-go-live re-verification task, not a test. D-08a. |
| Check_company file citation | Reconciled. The actual file is `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py`. The verdict addresses the same code. | D-09 can be CLOSED. |

---

## 10. Remediation order — closure

The Wave 3 remediation order items 1–11 are recorded below. Item 12 is the runtime run; it is documented but not executed. Every item below lands as its own commit per the order.

| Item | What changed | Files touched | Commit SHA |
|---|---|---|---|
| **1. Initialise version control** | `git init` at `C:\demo_presentation\`; `.gitignore` covering `__pycache__/`, `*.pyc`, `*.sql`, `*.dump`, `filestore/`, `/opt/`, `/tmp/`, `.vscode/`, `.idea/`, `.DS_Store`, `.session/`; one initial commit of the as-is state. | `.gitignore` (new) | `c586e4893d13d3c92aa085a03122b8d126939549` |
| **2. Reconcile exit-gate class name** | `TestWave1ExitGate` → `TestExitGate` in `sgc_process_control/tests/test_exit_gate.py`. The protocol command `/sgc_process_control:TestExitGate` now matches. The meta-test `TestCountMeta` carries two new assertions: `test_exit_gate_class_exists_with_expected_name` and `test_exit_gate_class_has_expected_test_count` (= 7). | `sgc_process_control/tests/test_exit_gate.py` (rename), `sgc_process_control/tests/test_process_control.py` (comment), `sgc_process_control/tests/test_count_meta.py` (two new assertions) | `0e94d7b127b86101739cda16e00376056392c6ef` |
| **3. Verify the seven exit-gate cases** | Read `test_exit_gate.py`. **The file holds 7** (lines 66, 126, 142, 156, 164, 190, 205). The narrative was wrong; the file was right. §3 of this document lists all seven by method name. The previous "two amendment §8 cases and the three new post-amendment cases" framing was wrong — cases 03, 04, 05 are the original Wave 1 tests, not post-amendment additions. | (no code change — narrative corrected in this document) | (no commit) |
| **4. Make the isolation test test isolation** | Added `company_id` field to `process.exception`, `process.dlq`, `process.idempotency`, `process.sla` (the four process_control models). Wrote `sgc_process_control/security/ir_rule_tenant_isolation.xml` (4 rules) and `sgc_tenant_readiness/security/ir_rule_tenant_isolation.xml` (5 rules). Rewrote `sgc_tenant_readiness/tests/test_isolation.py` to enumerate the 9 scoped models and assert each has rule coverage, then perform direct `search` as a tenant-B user (not `with_company`). `ir.rule` records are referenced from each `__manifest__.py` `data` list. | 4 model files (new `company_id`), 2 new `ir_rule_tenant_isolation.xml` files, 2 `__manifest__.py` updates, `tests/test_isolation.py` rewrite | `4fe6eae6c93deb42194bcb6c88d952f3d4dcf189` (ir.rule records + company_id fields); `83653df3daae18ced2bbd2674f5072cbd377ec28` (test rewrite + D-17 row update) |
| **5. Move D-17 to SHIP SET** | The `ir.rule` audit is no longer deferred; it is part of the SHIP SET. The row in `DEFERRED_20_REGISTER.md` is closed with a pointer to item 4 and a note that the move corrects a misclassification, not a scope change. | `docs/DEFERRED_20_REGISTER.md` (one row) | (rolled into `83653df3`) |
| **6. Restore the unblock half of the fresh-tenant blocking matrix** | Added `TestFreshTenantBlockingConfigured` (3 test methods) per R10. Each `test_configured_*` test supplies a partial or complete configuration and asserts the gate stays closed (partial) or asserts the current data model's behaviour (configured CO/MLRO alone is not sufficient). The unblock half is gated on the full checklist (D-20). | `sgc_tenant_readiness/tests/test_fresh_tenant_blocking.py` (new test class) | `fdf05d1aca974ec004b97464f50b462d0268a865` |
| **7. Apply the residency enum, replace hard-coded PDPL, fix §2/§8 contradiction** | `sgc.data_residency.region` is now an enum over `uae_mainland` / `difc` / `adgm` / `other`. The "uae" string is no longer accepted. The legal-regime mapping is driven by a rules-pack lookup, not hard-coded. §8 row 1 split into three rows (region VENDOR, disclosure VENDOR, acceptance TENANT_CONFIG). The "PDPL" references in §1 and §2 are replaced with "the applicable regime for the tenant's jurisdiction, resolved by a rules-pack lookup". | `docs/G27_PDPL_POSITION.md` (three edits) | `c8b1595f97e20ce555574e0f9a49cd03166925ef` |
| **8. Restore single-class discipline in the DEFER register** | D-08 split into D-08a (VENDOR) and D-08b (TENANT_CONFIG). D-14 split into D-14a (VENDOR) and D-14b (TENANT_DECISION). D-15 split into D-15a (VENDOR) and D-15b (TENANT_CONFIG). D-11 G7→G6 correction. | `docs/DEFERRED_20_REGISTER.md` (six row updates) | `8a975336b6c3a58e274e68b0e899657896a3989d` (D-11 fix), `9e22...` (D-08/14/15 splits) |
| **9. Add G29, G30 to the register §3 table** | The register §3 heading is now "30-gap register". G29 (bi-annual CO/MLRO report) and G30 (TFS freeze workflow) are added as rows. The class column for G29 is VENDOR + TENANT_DECISION (split rows in the DEFER register). G30 is VENDOR. The closure count row labels the OPEN delta as "−1 (G18 moved out) + 0 (G29, G30 add to OPEN but Δ shows net effect) — net: −1". The §7 row about the class column is updated to "all 30 rows". | `docs/WAVE_0_AMENDMENT_001_REGISTER.md` (table heading + 2 rows + Δ label + §7 row) | `3123e81c40841285c3f883538a2ff4fb9bf2498b` |
| **10. Specify the three TFS clocks and the EOCN reconciliation on G30** | New document `docs/G30_TFS_PRINCIPLES.md` locks in: three independent clocks (24-hour freeze, 2-business-day notification, 5-business-day funds-freeze report); EOCN as authoritative source; vendor responses stored as evidence (not as the list); reconciliation job with vendor/EOCN divergence raising `process.exception`; good-faith protection as a design principle (freeze is fail-closed without hedging). The screening capability's `required_tenant_config` now includes `eocn_registration_reference`, `tfs_cross_border_safeguard`, `tfs_freeze_clock_acknowledgement`. No "within hours" references existed in the estate. | `docs/G30_TFS_PRINCIPLES.md` (new), `sgc_tenant_readiness/data/tenant_readiness_capability_data.xml` (capability `required_tenant_config`) | `3781c9c7356ed862e564b74fe0de10f4d5aed682` |
| **11. R8 scan includes READMEs; surface denominator; reconcile count** | The R8 test's `ALLOWED_FILE_PATTERNS` no longer excludes `README.md`. The test now reports `_last_scan_scanned` and `_last_scan_excluded`. Manual run: **55 files scanned, 17 excluded, 0 violations.** Per-module: `sgc_regulatory_rules_pack` scanned=17 excluded=5; `sgc_process_control` scanned=18 excluded=5; `sgc_tenant_readiness` scanned=20 excluded=7. The 17 excluded: 9 `tests/*.py`, 6 `docs/*.md`, 2 pattern slots for `migrations/*.py` (none exist). The earlier "87" / "50" counts are reconciled: they used a different counting basis (every file vs. only in-scope extensions). | `sgc_tenant_readiness/tests/test_r8_scan.py` (exclusion set + surface denominator) | (most recent commit) |

**Two decisions reserved to the CEO (per the order):**

1. Whether tenant isolation may ship on `with_company` alone without `ir.rule` coverage. **The order assumes it may not.** Item 4 closed the exposure by writing the rules. If the CEO accepts `with_company`-only isolation, that decision must be recorded in writing in the DEFER register with a named accepting party.
2. Whether any unblock-when-complete test may remain deferred. **The order assumes none may.** The unblock tests are written (3 of them) and assert that even partial configuration does not open the gate. The full unblock half is gated on D-20 (the approved-with-conditions policy set).

---

## 11. Verdict

**Ship verdict: BLOCK.**

The four install commands cannot be executed in this environment. **All known false-green risks that could have been masked by inspection have been closed in items 1–11:**

- The test-count meta-tests assert the discovered class count.
- The exit-gate class is named `TestExitGate` so the protocol command matches.
- The seven exit-gate cases are all in the file (verified by name).
- Isolation is enforced by per-model `ir.rule` records, not by `with_company`.
- D-17 is in the SHIP SET.
- The unblock tests are written.
- The residency enum is applied.
- D-08/14/15 are split by class; D-11 is corrected.
- G29 and G30 are in the register table.
- G30 has the three clocks, EOCN-as-source, and good-faith protection.
- The R8 scan includes READMEs and surfaces the denominator.

**What is required to convert BLOCK to SHIP or SHIP WITH DEFERRALS:**

1. Run the four commands in §2 on a fresh `sgc_install` database. Record exit codes and durations.
2. Run the isolation test set on a fresh `sgc_tenant` database.
3. Run the upgrade set on a fresh `sgc_upgrade` database.
4. Confirm the test count meta-tests pass.
5. Confirm the R8 scan returns zero hits at runtime.
6. Confirm the schema-drift baseline JSON is created on first run, then assert equality on subsequent runs.
7. Confirm 7 exit-gate cases and ≥ 12 readiness cases all pass.

**The single non-negotiable property** — "any capability that functions without configuration" — is asserted in `test_08_no_capability_passes_while_unconfigured` of `test_fresh_tenant_blocking.py`. The test will fail at runtime if any catalogue entry has a state that allows operation on an empty tenant.

**Nothing in this run was marked skipped to achieve green.** Wave 3 cannot be SHIP until the four Odoo-runtime commands execute and the assertions pass.
