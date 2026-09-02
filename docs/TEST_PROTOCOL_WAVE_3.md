# Test Protocol — Wave 3 (Install / Regression / Fresh-tenant Blocking)

> **Authority:** Test protocol for the gap-closure programme. **Controlling for test scope only**; subordinate to `AGENT_BRIEF_REAL_ESTATE_WORKFLOW_GAP_CLOSURE.md` and `AMENDMENT_001_VENDOR_TENANT_BOUNDARY.md`. Where this document conflicts with either, this document wins on test scope; the amendment wins on boundary, classification and representation questions.

---

## 1. What you are verifying

You are verifying a reusable multi-tenant template, not a deployed compliance system. The product ships machinery. Tenants supply licences, appointed officers, thresholds and legal positions. Nothing you test may assume a tenant has supplied anything.

The single most important property under test is this: on a fresh, empty tenant with zero configuration, every regulated capability must be blocked, and it must be blocked by name with a stated reason. A capability that silently works without tenant configuration is a defect of the highest severity in this product — higher than a crash, because a crash is visible and a silent pass is not.

---

## 2. The 80% ship line — read this before writing a single test

Work is partitioned into two sets. You do not get to move an item between them; only the CEO does.

**SHIP SET (must be 100% green — this is the 80% of scope).** Module installation on a clean database. Module upgrade from installed state. Uninstall without orphan constraints. All existing exit-gate tests (7 in sgc_process_control). All existing readiness tests (12 in sgc_tenant_readiness). Fresh-tenant blocking for every capability in the capability catalogue. Fail-closed behaviour on every compliance-gated transition. Regulatory constant integrity (effective-dating, jurisdiction scoping, source attribution, no defaults on TENANT_DECISION). Tenant data isolation. R8 representation audit. No dependency on sgc_offplan_rental_property_management.

**DEFER SET (documented, not blocked — this is the 20%).** UI polish and view ergonomics. Report layout and QWeb pagination. Performance and query-count optimisation. Non-critical PARTIAL gaps. Reference screening adapters beyond the abstract interface. Localisation. Tour/browser tests except where a capability has no server-side equivalent.

A DEFER SET failure is recorded and shipped. A SHIP SET failure blocks. There is no third category and no "minor" SHIP SET failure.

---

## 3. Non-negotiable operating rules (carried forward)

- **R2** — do not touch HELD modules.
- **R3** — no logic inside `sgc_offplan_rental_property_management`; it is UNRESOLVED, portal-path only, and nothing you build or test may import from it.
- **R4** — one gap, one status.
- **R6** — migrated constants carry a migration note.
- **R8** — no compliance claims anywhere in code, manifest, help text, view labels, report text or test names; permitted phrasing is "supports the tenant's AML/CFT/CPF programme".
- **R9** — no default values on any TENANT_DECISION field; blank plus mandatory source citation plus tenant acknowledgement.

**Add for this package:**

- **R10** — no test may create a tenant that is pre-configured by fixture unless the test's explicit purpose is to verify configured behaviour, and such tests must be named `test_configured_*`. Every other test starts from an empty tenant. Fixture convenience is how silent-pass defects get written into the suite.

---

## 4. Environment matrix

Run against the Odoo major version the estate targets. Do not assume; read `__manifest__.py` version strings and the server version, and record both in the report. If the manifests disagree with each other, stop and report — that is a defect, not an environment question.

Three databases, created fresh for each full run and destroyed afterwards:

- `sgc_install` — clean install path.
- `sgc_upgrade` — install at last-known-good, then upgrade to current.
- `sgc_tenant` — multi-tenant isolation, two tenant companies, no configuration.

Never run against a database that has been used before. A dirty database is the second-most-common source of false green in Odoo verification, behind unimported test modules.

---

## 5. Test taxonomy and tagging

Every test class must be tagged. Odoo tags `TransactionCase` and `HttpCase` subclasses with standard and `at_install` implicitly; classes not deriving from `BaseCase` get nothing and will silently not run. **Verify by count, not by assumption.**

Use these tags, added on top of the defaults:

- `sgc_install` for installation and schema-integrity tests.
- `sgc_gate` for fail-closed and readiness-gate tests.
- `sgc_regulatory` for constant integrity and effective-dating.
- `sgc_isolation` for multi-tenant separation.
- `sgc_defer` for DEFER SET tests, tagged `-standard` so they never block a run.

Any test that requires all modules present — cross-module gate interaction, isolation, capability catalogue completeness — must be `@tagged('-at_install', 'post_install')`. Anything asserting on a model owned by a module later in the dependency graph will pass vacuously at `at_install` because the model does not exist yet.

Every test module must be imported from `tests/__init__.py`. Add one meta-test that asserts the number of discovered test classes per module equals a hard-coded expected count. This is the only defence against a test file that stops running because someone forgot an import line, and it has caught this exact failure in most estates I would expect to see.

---

## 6. Installation protocol

Run on `sgc_install`, from an empty database, in this order. Record exit code, wall time and the full traceback of any failure.

**§6.0 Pre-flight.** The four runtime commands below assume the verifier passes. The verifier is now wired into the path two ways: (a) the pre-commit hook at `.githooks/pre-commit` (mirrored at `hooks/pre-commit/verify_wave3_claims.py`) refuses any commit that breaks the verifier, so the tree the runtime runs against is one the verifier just signed off on; (b) the runtime runner `tools/run_wave3_protocol.py` re-runs the verifier immediately before the install commands, so the runtime run refuses to start against a tree the verifier disagrees with even if the hook was bypassed or the run is on a different machine.

```bash
# 6.0 Pre-flight — verifier gate (exit non-zero on disagreement)
python tools/verify_wave3_claims.py
# Expected: exit 0, "ALL CHECKS INTERNALLY CONSISTENT." Anything else stops the run.

# 6.1 Bare install, no tests — proves the module loads at all
odoo-bin -d sgc_install -i sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness \
  --stop-after-init --log-level=info

# 6.2 Reinstall same DB with tests enabled, install-time scope
odoo-bin -d sgc_install \
  -u sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness \
  --test-enable --test-tags '/sgc_regulatory_rules_pack,/sgc_process_control,/sgc_tenant_readiness' \
  --stop-after-init --log-level=test

# 6.3 Post-install scope explicitly
odoo-bin -d sgc_install \
  -u sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness \
  --test-enable --test-tags 'post_install/sgc_tenant_readiness,post_install/sgc_process_control' \
  --stop-after-init --log-level=test

# 6.4 Targeted exit gate — must show 7 cases, not 5
odoo-bin -d sgc_install --test-enable \
  --test-tags '/sgc_process_control:TestExitGate' --stop-after-init
```

Split 6.1 from 6.2 deliberately. If 6.1 fails you have a load-order or data-file defect; if 6.1 passes and 6.2 fails you have a logic defect. Collapsing them costs you that signal.

The `--test-tags` syntax is `[-][tag][/module][:class][.method]`, values are additive, and specifying `--test-tags` implies `--test-enable`. Tests only run in installed modules, which is why every command above carries `-i` or `-u`.

**Uninstall check**, on a throwaway copy: uninstall all three modules and assert the database still boots and no orphaned `ir.model.data`, foreign key or `ir.rule` references remain. A template that cannot be cleanly uninstalled cannot be trialled by a prospect, and trials are how this product sells.

---

## 7. Regression protocol

Run on `sgc_upgrade`. Install the last tagged-good revision, load the standing fixture set, then upgrade to HEAD with `-u` and re-run the full SHIP SET scope. The upgrade path is where real damage occurs, because that is where the retention-anchor correction, the residency enum change and the register reclassifications all land on data that already exists.

Three assertions are mandatory on the upgrade run and are not optional at 80%.

**First**, the **retention anchor migration**. Records created before the anchor correction must have their retention clock rebased to end-of-relationship or transaction-completion, not creation date. Assert that no record retains a creation-date-derived expiry after upgrade, and that any record whose anchor event has not yet occurred has a null expiry rather than a computed one. A null is correct; a wrong date deletes evidence.

**Second**, the **residency enum migration**. Any stored value of `uae` must be migrated to an explicit `uae_mainland` / `difc` / `adgm` value or set null and flagged for tenant re-entry. It must not be silently defaulted to `uae_mainland` — DIFC and ADGM entities fall outside the federal PDPL entirely, and a wrong default asserts the wrong legal regime on the tenant's behalf. That is an R9 violation in migration clothing.

**Third**, **no data loss on TENANT_DECISION fields**. Assert values survive upgrade, and that any newly added TENANT_DECISION field arrives blank.

Add a **schema-drift test** that snapshots every model, field, selection value, constraint and `ir.rule` in the three modules and diffs against a committed baseline JSON. Unexpected drift fails the run; intended drift requires the baseline to be updated in the same commit. This is the cheapest regression net available and it will pay for itself the first time someone renames a selection value.

---

## 8. Fresh-tenant blocking matrix — the core of the ship gate

For every capability in the `sgc_tenant_readiness` catalogue, write one test asserting the capability is blocked on an empty tenant, and one asserting it unblocks only when its complete required set is present. Partial configuration must still block.

At minimum, and stated by name so the assertion messages are auditable:

- **goAML filing** blocks without goAML organisation ID and appointed CO/MLRO and LNOO reference.
- **TFS freeze** blocks without EOCN Notification Alert System registration — this is a separate obligation from goAML registration and a tenant lacking it cannot meet the freeze deadline, so the gate must say so explicitly.
- **Listings** block without Trakheesi credentials.
- **Money-touching transitions** block without escrow bank configuration.
- **Any screening-dependent transition** blocks without a configured screening provider.
- **E-invoicing** blocks unless tenant revenue and ASP appointment are present.
- **Every TENANT_DECISION threshold** blocks its consuming capability while blank.

Gating is per capability, never system-wide. A test that asserts the whole system is blocked is testing the wrong thing and will mask the case where property management is wrongly frozen by a missing brokerage licence.

---

## 9. Regulatory constant integrity

Assert mechanically, not by eye. Every constant carries a source attribution, a jurisdiction scope and an effective date. No constant classified `TENANT_DECISION` has a stored default. Every constant whose status is `UNVERIFIED` has a null `valid_from` and cannot be consumed by any gate — add a test that attempts consumption and asserts it raises.

Freeze these into the fixture as the expected baseline, with their verification posture:

- The e-invoicing ASP appointment deadline is **30 October 2026** (Ministerial Decision 244/2025) with go-live 1 January 2027, applying to tenants at or above AED 50 million revenue; classified `TENANT_CONFIG` because the revenue test is the tenant's.
- **TFS obligations** under Cabinet Decision 74/2020 run as three distinct clocks: freeze within 24 hours of the listing decision — not of your detection — notification to the Supervisory Authority and the Executive Office within two business days, and the goAML funds-freeze report within five business days. Test all three independently; a single-clock state machine will pass a naive test and fail a tenant.
- The AML foundation is **Federal Decree-Law 10/2025** and **Cabinet Resolution 134/2025**, with CO/MLRO requirements per **MoJ Notice 247/2026** including the non-outsourceable role and the alternate-officer requirement.
- PDPL is **Federal Decree-Law 45 of 2021** with **Executive Regulations not yet issued** as of the most recent authoritative commentary available (Chambers Data Protection & Privacy 2026, UAE chapter, updated 10 March 2026) — this constant stays `UNVERIFIED` with null `valid_from`, and re-verification is a named pre-go-live task, not a test.

Add one test asserting the EOCN publication is modelled as the authoritative sanctions source and that a vendor screening response is stored as evidence rather than as the list, with vendor/EOCN divergence raising an exception-queue event. Guidance is explicit that third-party lists are not a compliance guarantee and the official source prevails.

---

## 10. Isolation and R8

On `sgc_tenant`, with two tenant companies and no configuration: assert no record of any SGC model is readable across companies, that `ir.rule` coverage exists for every model holding personal or case data with a test that enumerates models and fails on any uncovered one, and that configuring tenant A leaves tenant B fully blocked. Confirm the check_company removal is reflected on whichever file is authoritative — the register still carries an unreconciled citation between `sgc_realestate_tenant.py:47` and `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py:54`, and this run is where that gets settled by inspection.

For **R8**, run a mechanical scan across all Python, XML, CSV and Markdown in the three modules for prohibited strings — "compliant", "compliance guaranteed", "ensures compliance", "AML compliant", "fully compliant", "certified" — excluding permitted constructions. Fail the run on any hit. Manual audit does not survive contact with a growing codebase; this must be a test.

---

## 11. Triage rules

- A **SHIP SET** failure stops the run; fix and re-run the full protocol, not the failing test alone.
- A **DEFER SET** failure is logged to `docs/DEFERRED_20_REGISTER.md` with gap ID, class, severity, evidence and the trigger condition that would promote it to SHIP SET.
- An **ambiguous** item defaults to SHIP SET and is escalated.
- Never mark a test **skipped** to achieve green; convert it to `sgc_defer` with a written justification, or leave it failing.

Failure screenshots for browser-based cases land in `/tmp/odoo_tests/{db_name}/screenshots/`; attach them for any DEFER SET UI failure.

---

## 12. Deliverable

Produce `docs/WAVE_3_INSTALL_REGRESSION_RESULT.md` containing:

- Environment record (Odoo version, Python version, Postgres version, commit SHA, run timestamp).
- The four install commands with exit codes and durations.
- Discovered-versus-expected test counts per module.
- The SHIP SET results table with pass/fail per area.
- The fresh-tenant blocking matrix, one row per capability, showing blocked-when-empty and unblocked-when-complete.
- The three mandatory upgrade assertions with evidence.
- The schema-drift diff or a statement of none.
- The R8 scan output.
- The DEFER SET register.
- A single explicit verdict line.

---

## 13. Final result — acceptance template and thresholds

This is what a passing run must produce. Fill it from observed output only; do not pre-populate.

- **Ship verdict is SHIP only when all of the following hold:**
  - Install commands 6.1 through 6.4 exit zero.
  - Discovered test count equals expected count in every module — a shortfall is a failure even if everything discovered passed.
  - Exit-gate cases number 7, not 5.
  - Readiness cases number 12 or higher.
  - Every capability in the catalogue has both a blocked-when-empty and an unblocked-when-complete result, with **zero capabilities passing while unconfigured**.
  - All three upgrade assertions pass, with the residency migration showing zero silent defaults to `uae_mainland`.
  - Schema drift is either empty or fully accounted for in the same commit.
  - R8 scan returns zero hits.
  - Isolation shows zero cross-company reads and zero uncovered models.
  - No import of `sgc_offplan_rental_property_management` appears anywhere in the three modules.

- **Ship verdict is SHIP WITH DEFERRALS** when the above hold and the DEFER SET register is non-empty but every entry carries a promotion trigger. This is the expected outcome and is what your 80% looks like in practice.

- **Ship verdict is BLOCK** on any SHIP SET failure, on any discovered/expected test count mismatch, or on **any capability that functions without configuration**. The last of these is the only one I would treat as non-negotiable regardless of commercial pressure, because a template that quietly lets an unconfigured tenant transact is a liability transfer in the wrong direction — the tenant's regulator will look at what the system allowed, and "the tenant did not configure it" is a defence you would rather not have to make.

Two items remain open going into this run and belong in the deferral register rather than the ship gate: the **PDPL Executive Regulations** status needs re-verification before any tenant go-live, and the **check_company file citation** needs settling by inspection during the isolation run.

---

## 14. Per-command test-count assertion (the asymmetry that the meta-tests exist to close)

`odoo-bin --test-enable` returns non-zero on test failure — but a `--test-tags` selector that matches nothing returns zero with exit code **zero**. That asymmetry is the entire reason the meta-tests (`test_count_classes_in_module`, `test_exit_gate_class_exists_with_expected_name`, `test_exit_gate_class_has_expected_test_count`, `stale_test_tags_selectors` in the verifier) exist. Reading exit code alone is insufficient — a green-on-paper run can hide a selector that matched nothing.

Per-command assertions on the live run:

| Command | Assertion |
|---|---|
| 6.1 | Exit code == 0. **No test count** — this is the bare-load command; it should run zero tests. Exit 0 with zero tests here is the expected outcome, not a red flag. |
| 6.2 | Exit code == 0. **Test count must equal the per-module baseline sum**: `sgc_regulatory_rules_pack=4 + sgc_process_control=4 + sgc_tenant_readiness=8 = 16` distinct TestCase subclasses run, each producing ≥ 1 test method that ran. A count of 0 against this command with exit 0 is the false-green the meta-tests exist to catch — the run stops and reports. |
| 6.3 | Exit code == 0. **Test count must equal the per-module `post_install` baseline sum**: only the `-at_install` (default) tests are excluded; both modules' `post_install` tests must run. `sgc_tenant_readiness=8 + sgc_process_control=4 = 12` distinct TestCase subclasses run; a count of 0 with exit 0 is the same false-green signal and stops the run. |
| 6.4 | Exit code == 0. **Exactly 7 test methods run on `TestExitGate`.** This is the most specific assertion — a missing method (e.g. one deleted accidentally) would lower the count below 7; an extra method would raise it above 7. Either is a real defect, not a false-green to suppress. |

The mechanical check lives in `tools/run_wave3_protocol.py` (the runtime runner). It invokes each of the four commands above, scrapes the Odoo test log for the per-command test count, and treats the following as a hard failure:

- Exit code non-zero.
- `6.2` test count = 0 (selector matched nothing — exactly the false-green the meta-tests exist to close).
- `6.3` test count = 0 (same).
- `6.4` test count ≠ 7 (the targeted exit-gate case count is wrong — a real bug, not a false-green).
- `6.2` or `6.3` test count < baseline (genuine test regression, e.g. a meta-test now fails on its own assertion after a code change).

`6.1` with exit 0 and zero tests is **not** a false-green — it is the expected shape of a bare-load command. It is logged as such; it is not flagged.

Suspiciously clean output — all four commands exit 0, all expected counts met, zero failures — is itself a finding to investigate, not a result to report. With this much new untested code (the computed-state readiness gate was rewritten in round 2, the e-invoicing revenue-band gap was closed in round 3, the residency enum was promoted from docstring to real field), all-green on attempt one is more likely to indicate the verifier passing through a stale tree than genuine correctness. The runtime runner appends the per-command evidence to the result document as it goes, so the review can see the trajectory; the verdict moves off BLOCK only when counts are positive and failures are zero across both `sgc_install` runs and the subsequent `sgc_upgrade` and `sgc_tenant` runs.

---

## 15. Environment

Per the runtime instructions:

- **Odoo base image**: `odoo:19` is the floating tag; the runtime **must pin a dated tag** (e.g. `odoo:19.0-20260815`) rather than the latest. The official Odoo images rebuild on roughly two-week intervals; a mid-run base image change would make any failure unattributable to a specific build. Pin the tag at the start of the run, record it in the result document.
- **Postgres image**: `postgres:16`.
- **Addons path**: mounted read-write so the runtime can also exercise an upgrade path on the same image.
- **Network**: the Odoo image pulls Python deps at build, so the image-build step needs network access; the runtime run does not.

Suggested `docker-compose.yml` shape (not committed — kept as a starter for whoever spins up the runtime; the actual values are recorded in the result document at run time):

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: sgc_install
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
    volumes:
      - pgdata:/var/lib/postgresql/data

  odoo:
    # PIN a dated tag. Do NOT use the floating :19 — a mid-run rebuild
    # would make failures unattributable.
    image: odoo:19.0-20260815
    depends_on:
      - postgres
    environment:
      PGPASSWORD: odoo
    volumes:
      # Mount the addons path read-write so the same image can exercise
      # an upgrade path (sgc_upgrade) after the sgc_install run.
      - .:/mnt/sgc:rw
    command:
      - odoo-bin
      - -d sgc_install
      - -i sgc_regulatory_rules_pack,sgc_process_control,sgc_tenant_readiness
      - --addons-path=/mnt/sgc
      - --db_host=postgres
      - --db_user=odoo
      - --db_password=odoo
      - --stop-after-init
      - --log-level=info

volumes:
  pgdata:
```

Run order: start `postgres`, then 6.1 alone first on `sgc_install`. If 6.1 fails, stop and report — view-validation failures at install time are a different defect from test failures and would only add noise to the remaining commands.

---

## 16. Sign-off conditions (resolved, captured as runtime protocol gates)

The user's four conditions on the sign-off are encoded into this protocol:

1. **Verifier in the loop, not in memory.** Wired at two paths: `.githooks/pre-commit` (refuses the commit) and `tools/run_wave3_protocol.py` (refuses the runtime run). The verifier is also still invokable as a standalone (`python tools/verify_wave3_claims.py`) for review-time spot checks.
2. **Non-parseable constant raises.** Asserted by `test_12_conflicting_constant_value_text_is_not_a_parseable_date` in `test_regulatory_integrity.py` (added in round 3 alongside the government-entity `conflicting`-tier constant). The test converts a deliberate design from latent crash to contract: anyone tempted to "fix" the unparseable value_text into a plausible-looking date fails the test loudly rather than silently introducing the wrong-date defect.
3. **Test counts from the log, not exit codes alone.** Section 14 above. The runtime runner parses the Odoo log, not just exit codes, and treats zero-tests-exit-zero as a hard failure for 6.2 and 6.3 (the two commands that are most likely to silently match nothing). Suspiciously clean output is itself a finding to investigate.
4. **Pin the Odoo base image.** Section 15 above. `odoo:19.0-<date>` (dated), not the floating `:19`. Mid-run rebuilds would corrupt attribution of any failure.
