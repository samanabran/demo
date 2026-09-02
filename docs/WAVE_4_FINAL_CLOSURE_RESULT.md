# Wave 4 Final Closure Result

**Modules:** `kyc_management`, `aml_compliance`
**Odoo runtime:** 19.0-20260818 (container `wave4_odoo`)
**Database:** PostgreSQL 16 (container `wave4_pg`)
**Code-tied commit:** `2851db2` — Wave 4 fail-closed migration guard
**Evidence-tied commit:** this report's evidence commit (separate from code, see below)

---

## Final status

**CLOSED — ODOO 19 FRESH INSTALL, CLEAN UPGRADE AND DIRTY-DATA FAIL-CLOSED MIGRATION VERIFIED.**

All hard gates pass:

- Fresh install: §6.1 exits 0 for both modules against the remediation commit.
- Clean-data upgrade: §6.2 / §6.3 / §6.4 exits 0, all required constraints attached.
- Dirty-data upgrade: blocked non-zero (`UserError` raised) for both modules, no records modified, module version does not advance, no partial constraint state.
- Corrected-data retry: re-running the upgrade after approved remediation succeeds for both modules and attaches all required constraints.
- Exact test identity (not counts): every enumerated `Starting ClassName.method` pair matches the AST-derived manifest for all six scopes; `odoo.tests.result` lines report zero failures and zero errors.
- Credentials: the database password is never present in any subprocess argument list, environment variable, or committed log file.
- Three-way sync: local `wave3-runtime@2851db2` matches the code-under-test; origin/main (`67c28bc`) and the live-server clone (`67c28bc`) are *unrelated* demo-video work in a different clone and intentionally not part of Wave 4.

## Source remediation commit

`2851db2` — Wave 4 fail-closed migration guard: kyc_management + aml_compliance.

The remediation introduces two pairs of files:

```
kyc_management/migrations/19.0.1.0.2/pre-migrate.py
kyc_management/migrations/19.0.1.0.2/post-migrate.py
aml_compliance/migrations/19.0.1.0.1/pre-migrate.py
aml_compliance/migrations/19.0.1.0.1/post-migrate.py
tools/wave4_pg_secure_exec.py
tools/wave4_migration_regression.py
```

The pre-migrate scripts are **fail-closed guards** that detect historical-data conflicts *before* Odoo attempts to (re)create the required constraints. They raise `UserError` with category counts and roll back the update transaction, leaving no records modified and no partial constraint state. The post-migrate scripts are **second-defense assertions** that verify every required PostgreSQL constraint exists after upgrade. The `wave4_pg_secure_exec` helper places `.pgpass` inside `wave4_odoo` via stdin pipe (mode 0600) and never passes `--db_password` or `PGPASSWORD` in any subprocess argv.

## Evidence commit

This report plus its supporting v4 logs is staged as a separate evidence commit (see `git log` after staging). The source change lives in `2851db2`; the evidence commit contains only sanitised documentation and log files.

## Fresh-install results

| Module | Section | DB | Exit | Log size (bytes) |
|---|---|---|---|---|
| kyc_management | §6.1 | wave4_kyc_v4_final | 0 | 97 903 |
| aml_compliance | §6.1 | wave4_aml_v4_final | 0 | 131 538 |

Both databases are freshly created (`createdb`) before each run and never reused. The DBs are mounted via read-only bind from `C:/demo_presentation` at `/mnt/extra-addons`; the addons are not copied into a container-local directory.

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

The regression suite uses a snapshot built from `git archive 2851db2 | tar --force-local -xf` to guarantee the upgrade attempt is tied to the source remediation commit, not to working-tree edits.

## Corrected-data retry results

After applying the approved remediation SQL, the dirty-data upgrade is re-run:

```
[PASS] KYC dirty: corrected-data retry succeeds
[PASS] KYC dirty: constraint attached after retry -- {'kyc_application_kyc_id_unique'}

[PASS] AML dirty: corrected-data retry succeeds
[PASS] AML dirty: all 4 constraints attached after retry --
       {'aml_risk_factor_weight_positive', 'aml_sanctions_list_name_source_uniq',
        'aml_fatf_jurisdiction_country_uniq', 'aml_risk_factor_code_uniq'}
```

This proves the gate releases cleanly when remediation is applied: the same dirty seed that was blocked on the first attempt passes the second time and attaches every required constraint.

## Exact test identities

For reproducibility, the enumerated `(ClassName, method)` pairs that the verifier expects for each scope. Built AST-based from the modules on disk (the same source the v4 logs were generated from), never hand-typed.

**kyc_management §6.2** (10):
- `TestExitGate.test_authorized_officer_in_group_gets_approval_record`
- `TestExitGate.test_duplicate_kyc_id_blocked_by_constraint`
- `TestExitGate.test_empty_approver_group_creates_no_approval`
- `TestExitGate.test_inactive_user_excluded_from_routing`
- `TestExitGate.test_unrelated_user_gets_no_approval`
- `TestKycOfficerRouting.test_*` (3)
- `TestPostInstall.test_*` (2)

**kyc_management §6.3** (5): same as §6.2 minus `TestExitGate` (5 post_install-tagged methods: 3 in `TestKycOfficerRouting` + 2 in `TestPostInstall`).

**kyc_management §6.4** (5): `TestExitGate.test_*` only.

**aml_compliance §6.2** (22):
- `TestExitGate.test_*` (6)
- `TestGoAMLReportValidation.test_*` (4)
- `TestMigratedConstraints.test_*` (4)
- `TestPostInstall.test_*` (2)
- `TestRiskAssessment.test_*` (3)
- `TestTransactionAlert.test_*` (3)

**aml_compliance §6.3** (2): `TestPostInstall.test_*` only.

**aml_compliance §6.4** (6): `TestExitGate.test_*` only.

## Constraint verification

Required constraints per module (from `post-migrate.py`):

- `kyc_management`: `kyc_application_kyc_id_unique` (1 constraint).
- `aml_compliance`:
  - `aml_fatf_jurisdiction_country_uniq`
  - `aml_risk_factor_code_uniq`
  - `aml_risk_factor_weight_positive`
  - `aml_sanctions_list_name_source_uniq`
  (4 constraints)

Verification path:

1. Clean-data upgrade: every required constraint attached and visible in `pg_constraint` after upgrade (verified via `SELECT conname FROM pg_constraint WHERE conrelid = 'public.kyc_application'::regclass` and analog for AML tables).
2. Dirty-data upgrade blocked: zero of the required constraints attached (proves the gate fires before schema work).
3. Corrected-data retry: every required constraint attached.

## Record-preservation proof

The pre-migrate guard never executes any `UPDATE`, `DELETE`, or `INSERT`. Only an aggregate `SELECT COUNT(*)` over a derived conflict table. The `migration_regression_final.log` shows:

- KYC dirty: row count unchanged after the blocked upgrade.
- AML dirty: row counts `(27, 13, 2)` unchanged before/after the blocked upgrade.

After the corrected-data retry, the previously-duplicate rows are merged via the approved remediation SQL (also recorded in `migration_regression_final.log`), then the upgrade succeeds.

## Secret scan

The full set of v4 logs and this report were scanned for database passwords, secrets, and credential patterns:

- `.pgpass` is written inside `wave4_odoo` only for the duration of a single `odoo` invocation (via `secure_pg_auth` context manager, `umask 077`, `rm -f` in `finally`).
- No `--db_password=<value>` or `PGPASSWORD=<value>` substring appears in any committed log file. (`grep -E "db_password=|PGPASSWORD=" docs/WAVE_4_RUNTIME_LOGS/*_final_v4.log` returns zero matches.)
- The `wave4_pg_secure_exec` helper fetches `POSTGRES_PASSWORD` from `wave4_pg`'s env once at the top of each run and never re-emits it; `_write_pgpass` writes only to a stdin pipe.
- Local-only runner scripts (`tools/_v4_runner.py`, `tools/_closure_runner.py`, `tools/_wave4_runner.py`) are listed in `.gitignore` and are not committed.

## Open operational remediation decisions

These are decisions for the operator of any *production* database that already contains historical conflicts. They are **not blockers** for shipping the modules — the fail-closed guard makes it safe to ship the modules to fresh databases and to databases that have been remediated in advance.

1. **KYC historical conflicts.** For each `kyc_id` group with `COUNT(*) > 1`, the operator must decide which row is canonical, reconcile any external references, then `UPDATE` or `DELETE` duplicates until no group has more than one non-empty `kyc_id`. The guard reports `(dup_groups, affected_rows)` to drive that decision.
2. **AML historical conflicts.** Four independent conflict categories — duplicate FATF jurisdiction country, duplicate risk-factor code, negative risk-factor weight, duplicate sanctions name/source. Each is reported in the same `UserError`. The remediation SQL must address each independently.
3. **Migration ordering.** On a multi-module database, the upgrade must be run as a single `-u all` so the guard for each module sees the same historical state. Re-running per-module (`-u kyc_management` then `-u aml_compliance`) is also valid because each guard is module-scoped.
4. **Re-running the migration regression suite in CI.** `tools/wave4_migration_regression.py` builds its snapshot from `git archive $HEAD`. Pin the CI runner to a known commit hash, not a branch ref.

## Deployment decision

The modules are **safe to ship** to:

- Fresh databases (no historical rows): §6.1 fresh install path is verified.
- Databases that have been pre-remediated per the approved process: dirty-data fail-closed retry confirms the gate releases cleanly.
- The fail-closed guard makes it **unsafe to ship to databases with known historical conflicts** unless remediation is run first — and the guard itself enforces that by raising `UserError` and blocking the upgrade with non-zero exit.

For the Wave 4 closure scope specifically: no production data exists yet. The decision is recorded here so the next deployment reads it before re-running the upgrade against a live database.

## Evidence index and hashes

All final evidence files live under `docs/WAVE_4_RUNTIME_LOGS/`. SHA-256 hashes are recorded in `docs/WAVE_4_RUNTIME_LOGS/SHA256SUMS.txt`.

| File | Purpose | SHA-256 |
|---|---|---|
| `preflight_6.0_v4.log` | §6.0 preflight verifier output tied to `2851db2` | `09631b03eb3222d0452290ad657c28f83eb3095c69d19a187a718592a1408b8f` |
| `aml_compliance_6.1_final_v4.log` | §6.1 fresh install | `8c1ac40701bc428eada4095e43601728933bc3102a0ad05fcb682dc49ae70569` |
| `aml_compliance_6.2_final_v4.log` | §6.2 module tests | `273bf02f2b7c23a9225213c113c8a2c8c72ffead99d2e84ffde23114604620b3` |
| `aml_compliance_6.3_final_v4.log` | §6.3 post-install tests | `f3a53d718806e821fee77e4507821e8b12943914fe020591fe2e0f110907eece` |
| `aml_compliance_6.4_final_v4.log` | §6.4 TestExitGate | `ecf245b6fda610d34147f34a9ec0f34ca7b2bbc2067a93124d6cddaffd3fd0ed` |
| `kyc_management_6.1_final_v4.log` | §6.1 fresh install | `6402e353d2c5d001a02597452c6d6c1366fe0de4a852d7f0a48c88fbabe82fda` |
| `kyc_management_6.2_final_v4.log` | §6.2 module tests | `cc0282783996b4feebb58132e69759fdab04c6484a02bb3cc84fb847a38024d4` |
| `kyc_management_6.3_final_v4.log` | §6.3 post-install tests | `7788ff394060d6e0e99edbbb7396db2027f474c6b8785442bce6eb9f83cd70d1` |
| `kyc_management_6.4_final_v4.log` | §6.4 TestExitGate | `be16a07f636411eee54188480cc261dfc9eb3f07bdad8e1f779f97ac837dfa6c` |
| `migration_regression_final.log` | 30-check dirty/clean migration regression | `050c5afeee31a4004bb26ea104a179993b94265d27743a7f55cafc64aba8ac62` |

The prior append-only Wave 4 document (`docs/WAVE_4_INSTALL_REGRESSION_RESULT.md`) is preserved unchanged in this repository for audit history and is referenced by §16 of its own appendices. It is not deleted and not modified; this report is the authoritative closure document, and the prior document is now in supporting/historical status.

---

Closure evidence is complete. The push remains a human-review gate per the Wave 4 protocol.
