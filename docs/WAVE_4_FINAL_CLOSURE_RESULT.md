# Wave 4 Final Closure Result

**Modules:** `kyc_management`, `aml_compliance`
**Odoo runtime:** 19.0-20260818 (container `wave4_odoo`)
**Database:** PostgreSQL 16 (container `wave4_pg`)
**Code-under-test commit:** `2851db2` — Wave 4 fail-closed migration guard
**Evidence commit (runtime logs):** `35733a2` — Wave 4 final closure: v4 evidence pack tied to 2851db2 (10 v4 evidence files)
**Evidence commit (this report + checksum manifest):** this commit; exact hash recorded in the final delivery response
**Code-under-test commit parent:** `ea11562` — Wave 4 closure pass, second session

This report is the authoritative closure document. The prior append-only report at `docs/WAVE_4_INSTALL_REGRESSION_RESULT.md` is preserved unchanged as historical evidence and is referenced from §16 of its own appendices; it is not modified by this report.

---

## Final status

**Technical status:** CLOSED — runtime closure matrix passed for kyc_management and aml_compliance against code commit `2851db2`.

**Delivery status (as of this commit):** PENDING — evidence committed at `35733a2`; push to `origin/wave3-runtime` and remote hash confirmation are the only remaining steps and are human-review gates per the Wave 4 protocol.

When push and remote hash confirmation complete, the final status becomes:

> CLOSED — ODOO 19 FRESH INSTALL, CLEAN UPGRADE, AND DIRTY-DATA FAIL-CLOSED MIGRATION VERIFIED; EVIDENCE COMMITTED AND PUSHED.

## Source remediation commit

`2851db2` — Wave 4 fail-closed migration guard: kyc_management + aml_compliance.

The remediation introduces two pairs of module migration scripts and three supporting verification tools:

```
kyc_management/migrations/19.0.1.0.2/pre-migrate.py
kyc_management/migrations/19.0.1.0.2/post-migrate.py
aml_compliance/migrations/19.0.1.0.1/pre-migrate.py
aml_compliance/migrations/19.0.1.0.1/post-migrate.py
tools/wave4_pg_secure_exec.py
tools/wave4_migration_regression.py
tools/verify_wave4_claims.py
```

The pre-migrate scripts are **fail-closed guards** that detect historical-data conflicts *before* Odoo attempts to (re)create the required constraints. They raise `UserError` with category counts and roll back the update transaction, leaving no records modified and no partial constraint state. The post-migrate scripts are **second-defense assertions** that verify every required PostgreSQL constraint exists after upgrade. The `wave4_pg_secure_exec` helper places `.pgpass` inside `wave4_odoo` via stdin pipe (mode 0600) and never passes `--db_password` or `PGPASSWORD` in any subprocess argv.

Static review of every guard confirms:

- Only aggregate / read-only queries (`SELECT COUNT(*)`, `to_regclass()`, `pg_constraint` lookup).
- No `DELETE`, `UPDATE`, `INSERT`, or automatic merge.
- No automatic compliance remediation.
- Conflict causes a raised `UserError`, which rolls back the upgrade transaction.
- Error message contains aggregate counts only; no customer-identifying data is logged.

## Evidence commit

`35733a2` — Wave 4 final closure: v4 evidence pack tied to 2851db2.

Parent: `2851db2`. Committed files (12):

```
docs/WAVE_4_FINAL_CLOSURE_RESULT.md
docs/WAVE_4_RUNTIME_LOGS/SHA256SUMS.txt
docs/WAVE_4_RUNTIME_LOGS/preflight_6.0_v4.log
docs/WAVE_4_RUNTIME_LOGS/aml_compliance_6.1_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/aml_compliance_6.2_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/aml_compliance_6.3_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/aml_compliance_6.4_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/kyc_management_6.1_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/kyc_management_6.2_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/kyc_management_6.3_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/kyc_management_6.4_final_v4.log
docs/WAVE_4_RUNTIME_LOGS/migration_regression_final.log
```

Intentionally excluded (untracked / superseded / gitignored / session scratch):

```
2026-09-02-002311-see-the-working-of-previous-agent-and-continue-wh.txt   (prior-agent dump)
docs/WAVE_4_RUNTIME_LOGS/*_final.log        (superseded v3 logs)
docs/WAVE_4_RUNTIME_LOGS/*_summary.md       (interim summary)
docs/WAVE_4_RUNTIME_LOGS/aml_smoke_run.log  (interim smoke)
docs/WAVE_4_RUNTIME_LOGS/migration_guard_*.log (per-checkpoint logs superseded by migration_regression_final.log)
docs/WAVE_4_RUNTIME_LOGS/preflight_6.0_v4_old.log (superseded preflight)
docs/WAVE_4_RUNTIME_LOGS/preflight_6.0.log       (superseded preflight)
session-ses_fa29.md                            (session transcript)
tools/_v4_runner.py                            (gitignored local helper)
tools/_closure_runner.py / tools/_wave4_runner.py (gitignored local helpers)
```

## Version transitions

Verified directly from each module's `__manifest__.py`:

| Module | Installed before | Candidate manifest | Migration directory |
|---|---|---|---|
| kyc_management | 19.0.1.0.1 | 19.0.1.0.2 | migrations/19.0.1.0.2/ |
| aml_compliance | 19.0.1.0.0 | 19.0.1.0.1 | migrations/19.0.1.0.1/ |

Each migration-directory version is strictly greater than the installed version and equal to the candidate manifest version, so Odoo's upgrade-script mechanism fires on `-u`.

## Fresh-install results

| Module | Section | DB | Exit | Log size (bytes) |
|---|---|---|---|---|
| kyc_management | §6.1 | wave4_kyc_v4_final | 0 | 97 903 |
| aml_compliance | §6.1 | wave4_aml_v4_final | 0 | 131 538 |

Both databases are freshly created (`createdb`) before each run and never reused. The addon source is mounted read-only from `C:/demo_presentation` to `/mnt/extra-addons`; the PostgreSQL databases are created separately for each run.

## Clean-data upgrade results

| Module | Section | testsRun | failed | errors | expected |
|---|---|---|---|---|---|
| kyc_management | §6.2 | 10 | 0 | 0 | 10 |
| kyc_management | §6.3 | 5 | 0 | 0 | 5 |
| kyc_management | §6.4 | 5 | 0 | 0 | 5 |
| aml_compliance | §6.2 | 22 | 0 | 0 | 22 |
| aml_compliance | §6.3 | 2 | 0 | 0 | 2 |
| aml_compliance | §6.4 | 6 | 0 | 0 | 6 |

Exact test identity (the gate that catches the `0 of 0 tests` silent-zero failure mode) is verified by `tools/verify_wave4_claims.py --check-run-log MODULE SCOPE LOG EXIT_CODE`. All six scopes return `ok: true` with `started_count == expected_count`, `testsRun == expected_count`, and `failed == errors == 0`.

## Dirty-data fail-closed results

`tools/wave4_migration_regression.py` runs 30 checks across four scenarios (clean / dirty × KYC / AML). Summary:

```
30 checks, 30 passed, 0 failed
WAVE4_MIGRATION_REGRESSION: PASS
```

Specific dirty-data results:

```
[PASS] KYC dirty: guarded upgrade is BLOCKED (non-zero exit) -- rc=255
[PASS] KYC dirty: blocking message matches required shape -- _id groups=1; affected rows=2;
       no records modified; run the approved KYC data-remediation process before retrying.
[PASS] KYC dirty: no records modified
[PASS] KYC dirty: module version did not advance -- 19.0.1.0.1 -> 19.0.1.0.1
[PASS] KYC dirty: no partial constraint state committed -- set()

[PASS] AML dirty: guarded upgrade is BLOCKED (non-zero exit) -- rc=255
[PASS] AML dirty: blocking message names all 4 conflict categories --
       E_BLOCKED: duplicate FATF countries=1; duplicate risk-factor codes=1;
       negative risk-factor weights=1; duplicate sanctions name/source groups=1;
       no records modified; approved remediation is required before retrying.
[PASS] AML dirty: no records modified -- (27, 13, 2) -> (27, 13, 2)
[PASS] AML dirty: module version did not advance -- 19.0.1.0.0 -> 19.0.1.0.0
[PASS] AML dirty: no partial constraint state committed -- set()
```

The regression suite uses a snapshot built from `git archive 2851db2 | tar --force-local -xf` to guarantee the upgrade attempt is tied to the source remediation commit, not to working-tree edits. All dirty-data conflicts were created by **controlled test-fixture remediation SQL** that runs only inside the regression suite; no production-data remediation was performed or authorised.

## Corrected-data retry results

After applying controlled test-fixture remediation SQL inside the regression suite, the dirty-data upgrade is re-run:

```
[PASS] KYC dirty: corrected-data retry succeeds
[PASS] KYC dirty: constraint attached after retry -- {'kyc_application_kyc_id_unique'}

[PASS] AML dirty: corrected-data retry succeeds
[PASS] AML dirty: all 4 constraints attached after retry --
       {'aml_risk_factor_weight_positive', 'aml_sanctions_list_name_source_uniq',
        'aml_fatf_jurisdiction_country_uniq', 'aml_risk_factor_code_uniq'}
```

This proves the gate releases cleanly when the controlled-fixture remediation is applied: the same dirty seed that was blocked on the first attempt passes the second time and attaches every required constraint.

## Combined-update scope

Independent module upgrades were verified. Combined dirty-data behaviour under `-u kyc_management,aml_compliance` or `-u all` was not executed. If the production procedure uses a combined update, perform one focused combined dirty-data validation before deployment.

## Test identity groups and verified counts

The complete method-level identities are enforced by `tools/verify_wave4_claims.py --check-run-log MODULE SCOPE LOG EXIT_CODE` and preserved in the v4 logs themselves. The list below names the test classes and the count of `test_*` methods per scope, not an enumerated `(ClassName, method)` list.

**kyc_management §6.2** (10): `TestExitGate` (5), `TestKycOfficerRouting` (3), `TestPostInstall` (2).

**kyc_management §6.3** (5): `TestKycOfficerRouting` (3) + `TestPostInstall` (2); `TestExitGate` is excluded (no `post_install` tag).

**kyc_management §6.4** (5): `TestExitGate` only (5).

**aml_compliance §6.2** (22): `TestExitGate` (6), `TestGoAMLReportValidation` (4), `TestMigratedConstraints` (4), `TestPostInstall` (2), `TestRiskAssessment` (3), `TestTransactionAlert` (3).

**aml_compliance §6.3** (2): `TestPostInstall` only (2).

**aml_compliance §6.4** (6): `TestExitGate` only (6).

The exact `(ClassName, method)` pairs that the verifier expects for each scope are computed AST-based from the modules on disk (the same source the v4 logs were generated from) and matched one-for-one against every `Starting ClassName.method` line parsed from each log. Any mismatch in either direction fails the verifier with `ok: false`. All six scopes passed this gate against the v4 logs committed at `35733a2`.

## Constraint verification

Required constraints per module (verified directly from each `post-migrate.py`):

- `kyc_management`: `kyc_application_kyc_id_unique` (1 constraint).
- `aml_compliance`:
  - `aml_fatf_jurisdiction_country_uniq`
  - `aml_risk_factor_code_uniq`
  - `aml_risk_factor_weight_positive`
  - `aml_sanctions_list_name_source_uniq`
  (4 constraints)

Verification path:

1. Clean-data upgrade: every required constraint attached and visible in `pg_constraint` after upgrade.
2. Dirty-data upgrade blocked: zero of the required constraints attached (proves the gate fires before schema work).
3. Corrected-data retry: every required constraint attached.

## Record-preservation result

Row counts, module versions, and required-constraint sets were unchanged after the blocked upgrade. Static review confirms that the guards execute aggregate read-only queries, and the raised `UserError` rolls back the upgrade transaction. The dirty-data evidence log reports:

- KYC dirty: row count unchanged after the blocked upgrade.
- AML dirty: row counts `(27, 13, 2)` unchanged before/after the blocked upgrade.

This measures row counts, module versions, and required-constraint sets only. It does **not** measure the contents of individual rows; it confirms no row was inserted, deleted, or changed in any controlled-fixture column referenced by the guards, because the guard's only database actions are aggregate `SELECT COUNT(*)` queries and the surrounding upgrade transaction is rolled back by the raised `UserError`.

## Secret / credential / PII scan

Scope scanned: current worktree, staged diff, commit `2851db2`, the v4 evidence files committed at `35733a2`, the full `wave3-runtime` branch history, and the command lines recorded in logs.

Search patterns: `PGPASSWORD`, `POSTGRES_PASSWORD=<value>`, `--db_password=<value>`, database URLs containing credentials, private keys, access tokens, API keys, bearer tokens, passwords, customer names or identifiers exposed by dirty-data fixtures, unsanitized container inspect output.

The password was not passed in Odoo command-line arguments, was not propagated through PGPASSWORD, and was not written to committed logs. It was retrieved from the PostgreSQL container environment and transferred through stdin to a temporary mode-0600 `.pgpass` file.

No secret values appear in any committed file. No customer or fixture PII appears in any committed log.

Outcome: **PASS**.

## Open operational remediation decisions (separate from controlled test-fixture remediation)

These are decisions for the operator of any *production* database that already contains historical conflicts. They are **not blockers** for shipping the modules to fresh or pre-remediated databases. No production-data remediation was performed or authorised in this evidence pack.

1. **KYC historical conflicts.** For each `kyc_id` group with `COUNT(*) > 1`, a controlled human-approved remediation process must decide which row is canonical, reconcile any external references, then `UPDATE` or `DELETE` duplicates until no group has more than one non-empty `kyc_id`. The guard reports `(dup_groups, affected_rows)` to drive that decision. This evidence pack used controlled test-fixture remediation SQL inside the regression suite only.
2. **AML historical conflicts.** Four independent conflict categories — duplicate FATF jurisdiction country, duplicate risk-factor code, negative risk-factor weight, duplicate sanctions name/source. Each is reported in the same `UserError`. A controlled human-approved remediation must address each independently.
3. **Migration ordering.** If production uses `-u all`, the upgrade must be run as a single Odoo process so the guard for each module sees the same historical state. Per-module upgrades are also valid because each guard is module-scoped.
4. **Re-running the migration regression suite in CI.** `tools/wave4_migration_regression.py` builds its snapshot from `git archive $HEAD`. Pin the CI runner to a known commit hash, not a branch ref.

## Deployment decision

The modules are safe to ship to:

- Fresh databases (no historical rows): §6.1 fresh install path is verified.
- Databases pre-remediated via a controlled human-approved process: dirty-data fail-closed retry confirms the gate releases cleanly.
- Databases with known historical conflicts are **blocked by the fail-closed guard itself**, which raises `UserError` and prevents the upgrade from completing with non-zero exit.

For the Wave 4 closure scope specifically: no production data exists yet. The decision is recorded here so the next deployment reads it before re-running the upgrade against a live database.

Local evidence packaging is complete. Repository delivery remains pending until the evidence branch is pushed and local HEAD is confirmed equal to origin/wave3-runtime. Production deployment is not authorised by this verification alone. Databases with conflicts will be blocked pending approved business remediation.

## Evidence index and hashes

All final evidence files live under `docs/WAVE_4_RUNTIME_LOGS/`. SHA-256 hashes are recorded in `docs/WAVE_4_RUNTIME_LOGS/SHA256SUMS.txt`. Re-verify with `sha256sum -c docs/WAVE_4_RUNTIME_LOGS/SHA256SUMS.txt` from the repo root.

| File | Stage | DB | Odoo / PG | Code-under-test | SHA-256 |
|---|---|---|---|---|---|
| `preflight_6.0_v4.log` | §6.0 preflight | n/a | 19.0-20260818 / PG 16 | 2851db2 | `09631b03eb3222d0452290ad657c28f83eb3095c69d19a187a718592a1408b8f` |
| `aml_compliance_6.1_final_v4.log` | §6.1 fresh install | wave4_aml_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `8c1ac40701bc428eada4095e43601728933bc3102a0ad05fcb682dc49ae70569` |
| `aml_compliance_6.2_final_v4.log` | §6.2 module tests | wave4_aml_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `273bf02f2b7c23a9225213c113c8a2c8c72ffead99d2e84ffde23114604620b3` |
| `aml_compliance_6.3_final_v4.log` | §6.3 post-install tests | wave4_aml_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `f3a53d718806e821fee77e4507821e8b12943914fe020591fe2e0f110907eece` |
| `aml_compliance_6.4_final_v4.log` | §6.4 TestExitGate | wave4_aml_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `ecf245b6fda610d34147f34a9ec0f34ca7b2bbc2067a93124d6cddaffd3fd0ed` |
| `kyc_management_6.1_final_v4.log` | §6.1 fresh install | wave4_kyc_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `6402e353d2c5d001a02597452c6d6c1366fe0de4a852d7f0a48c88fbabe82fda` |
| `kyc_management_6.2_final_v4.log` | §6.2 module tests | wave4_kyc_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `cc0282783996b4feebb58132e69759fdab04c6484a02bb3cc84fb847a38024d4` |
| `kyc_management_6.3_final_v4.log` | §6.3 post-install tests | wave4_kyc_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `7788ff394060d6e0e99edbbb7396db2027f474c6b8785442bce6eb9f83cd70d1` |
| `kyc_management_6.4_final_v4.log` | §6.4 TestExitGate | wave4_kyc_v4_final | 19.0-20260818 / PG 16 | 2851db2 | `be16a07f636411eee54188480cc261dfc9eb3f07bdad8e1f779f97ac837dfa6c` |
| `migration_regression_final.log` | 30-check dirty/clean migration regression | wave4_migreg_* (clean + dirty per module) | 19.0-20260818 / PG 16 | 2851db2 (via `git archive`) | `050c5afeee31a4004bb26ea104a179993b94265d27743a7f55cafc64aba8ac62` |
| `WAVE_4_FINAL_CLOSURE_RESULT.md` (this file) | Authoritative closure report | n/a | n/a | 2851db2 (evidence) | see `SHA256SUMS.txt` — a hash of this file cannot be embedded inside itself without becoming stale on the next edit |

The historical report at `docs/WAVE_4_INSTALL_REGRESSION_RESULT.md` is preserved unchanged and serves as the supporting / historical record.

---

Closure evidence is committed at `35733a2` (v4 evidence pack) and finalised in a documentation-only commit that updates this report and `SHA256SUMS.txt`. The push to `origin/wave3-runtime` remains the final human-review gate per the Wave 4 protocol.
