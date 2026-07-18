# vps-root Host Inventory — Cleanup Planning Reconnaissance

**Date:** 2026-07-18
**Scope:** All 4 Postgres instances, all databases, all 19 containers on `vps-root` (80.241.218.108). Read-only reconnaissance — no action taken at time of writing.

**Update 2026-07-18 (later same day):** All 5 Tier C archived databases and all 5 stopped one-off containers listed below have since been removed, per explicit per-item user sign-off. Each database was re-verified immediately before drop (fresh `pg_stat_activity` zero-connection check + independent `pg_restore -l` against the locally-pulled Phase 1 dump); each container was re-confirmed still `exited` with unchanged `FinishedAt` before removal. See the "Actions taken" section at the bottom of this file for the full record. Every Tier A/B/D item below was left untouched.

---

## Answers to the three critical questions

**2.1 — Is `demo_presentation` Tier A?**
**Yes.** `pg_stat_database` shows 1 active backend, `xact_commit` incrementing in real time (303,847 → 303,859 over a ~5 min window during this pass). `demo.sgctech.ai` reverse-proxies to `127.0.0.1:18030` (the `demo_presentation` container's mapped port), and `/var/log/nginx/demo.sgctech.ai.access.log` was last written at 13:25 today. This is the 8,912-lead live CRM instance referenced in Phase 1 backup planning.

**2.2 — Is `odoo19-sgc` (odoo-prod-db) currently receiving live traffic?**
**Yes — Tier A, confirmed, not assumed from the name.** `pg_stat_activity` shows 11 backends with `COMMIT`/`ROLLBACK` cycling every few seconds. Two live domains route to it: `app.sgctech.ai` (`upstream odoo_sgc_v19 → 127.0.0.1:18069`) and `sgctech.ai`/`www.sgctech.ai` (`upstream sgctech_odoo → 127.0.0.1:18069`, same port). `docker port odoo-prod` confirms `8069/tcp → 18069`. The default nginx access log shows a genuine browser request at 13:44:38 today: `POST /bus/has_missed_notifications` with referrer `https://app.sgctech.ai/odoo/sales?debug=1`, plus point-of-sale asset requests seconds earlier. This is live, real-user production traffic right now.

**2.3 — Is `odoo_gmail_addin` currently in active use by any live Gmail integration?**
**No — not by real end-user traffic; classify Tier B/D, not Tier A.** `pg_stat_database` shows 0 backends at every sample. The nginx route that would carry Gmail add-in requests, `location /mail-plugins/gmail/ → proxy_pass http://127.0.0.1:5000` on `app.sgctech.ai`, has **zero hits** anywhere in today's full access log (`grep -ic mail-plugins /var/log/nginx/access.log` → 0, covering 00:00–13:44 today, ~13,600 requests total). The `gmail-addin` container (`Up 5 days`) is alive and its own logs show only a repeating internal "Clean the email logging table..." housekeeping message — that accounts for the small `xact_commit` trickle (17,156 → 17,160 over ~5 min) with 0 backends between polls. There is no evidence of a live Gmail user hitting this integration today. Do not drop the DB without confirming with whoever owns the Gmail add-in feature, since "no traffic today" is not the same as "permanently unused."

---

## Notable anomalies found during this pass (not requested, but relevant to cleanup risk)

1. **`odoo-staging` container (port 18028) is running but has no nginx site pointing to it anywhere** (`grep -rl 18028 /etc/nginx/` → nothing). Its `odoo.conf` has `dbfilter = ^traffexcel_staging$` — **identical** to the `staging-traffexcel` container, meaning two separate running containers are both configured to serve/write the same `traffexcel_staging` database, but only `staging-traffexcel` (port 18025) is actually reachable via `staging.sgctech.ai` and `traffexcel.sgctech.ai` (both domains point at the same port 18025 — also worth someone's attention, since `staging.sgctech.ai` "looks like" it should be a separate staging site but is actually just an alias onto the traffexcel container). `odoo-staging` appears to be an orphaned/duplicate deployment. Flagging only — no action taken.
2. **`traffexcel_staging` DB is Tier A despite its "staging" name** — real active query at 11:47:49 today, and real browser traffic on `staging.sgctech.ai` at 12:59:51 today (`POST /bus/has_missed_notifications`, referrer `staging.sgctech.ai/odoo/action-445`). Naming should not be used to infer risk tier here.
3. **`demo_presentation_staging` (port 18040/18041, DB `demo_presentation_19`) has no nginx site either**, yet shows a genuinely active backend (`state=active`, `query_start` 11:50:21 today). This is consistent with the known autopush/CI cron job for this project (see prior session memory) — real automated activity, not orphaned, just not internet-facing.
4. **`osusproperties_source_v18` (931 MB) and `demo_presentation_archived_20260717` (71 MB) live inside the `demo_presentation_db` Postgres instance** — the same instance as the live `demo_presentation` production DB — with no owning container of their own. Their `numbackends=1` readings are an artifact of the `demo_presentation` container's internal cron thread scanning every database on its Postgres host (confirmed via its logs: `"Skipping database osusproperties_source_v18 as its base version is not 19.0.1.3"`), not real usage. Same artifact explains most `numbackends=1` rows on `odoo-test-db`.
5. **`osusproperties` (non-v18, 915 MB) on `odoo-test-db` has no identifiable owning container**, despite being nearly as large as the live `osusproperties_v18` (1,347 MB). Purpose unconfirmed — Tier D, not to be assumed safe.
6. **`odoo_test_v19` DB has a defined nginx upstream (`test19.tachimao.com → 127.0.0.1:18027`) but no container currently publishes port 18027** — that route is dead. `test18.tachimao.com` (`→ 18018`) is live-mapped but coincidentally to the same port as `osusproperties-v18`; its access log has 0 bytes today, so no real traffic either way.

---

## Full inventory table

| Database | Instance | Container(s) using it | Tier | Evidence |
|---|---|---|---|---|
| `demo_presentation` | demo_presentation_db | `demo_presentation` (odoo:19.0) | **A** | 1 active backend, xact_commit incrementing live; `demo.sgctech.ai` → 18030; access log written 13:25 today |
| `demo_presentation_archived_20260717` | demo_presentation_db | none (cron-scan artifact only, from `demo_presentation`) | **C** | Name = explicit archive+date; no owning container; 71 MB |
| `osusproperties_source_v18` | demo_presentation_db | none found | **D** | No owning container; ambiguous "source" naming; 931 MB; do not assume safe |
| `demo_presentation_19` | demo_presentation_staging_db | `demo_presentation_staging` (odoo:19.0) | **B** (active, not orphaned) | 3-4 backends, one `state=active` at 11:50:21 today; no nginx route (internal/CI use per prior autopush cron); not internet-facing |
| `odoo19-sgc` | odoo-prod-db | `odoo-prod` (odoo:19.0-sgc) | **A** | 11 backends, live COMMIT/ROLLBACK cycling; `app.sgctech.ai` + `sgctech.ai`/`www.sgctech.ai` → 18069; real browser POST logged 13:44:38 today; 912 MB |
| `odoo_gmail_addin` | odoo-prod-db | `gmail-addin` (node:20-alpine, via `PSQL_DB` env) | **B/D** | 0 backends; container alive (`Up 5 days`) but `/mail-plugins/gmail/` route has 0 hits in today's full access log; only internal housekeeping cron writes; 7.7 MB — confirm with feature owner before any action |
| `erposus_archived_20260630` | odoo-prod-db | none | **C** | Explicit archive+date name; 0 backends; 7.4 MB |
| `odoo_prod_archived_20260630` | odoo-prod-db | none | **C** | Explicit archive+date name; 0 backends; 22 MB |
| `scholarix_master_archived_20260630` | odoo-prod-db | none | **C** | Explicit archive+date name; 0 backends; 7.7 MB |
| `sgctech_archived_20260630` | odoo-prod-db | none | **C** | Explicit archive+date name; 0 backends; 22 MB |
| `osusproperties_v18` | odoo-test-db | `osusproperties-v18` (odoo:18.0) | **A** | 12 backends; `osusproperties.sgctech.ai` → 18018 (confirmed via `docker port`); real bot + human traffic logged 13:48:50 today; 1,347 MB |
| `traffexcel_staging` | odoo-test-db | `staging-traffexcel` **and** `odoo-staging` (both odoo:19.0, duplicate config — see anomaly #1) | **A** | 4 backends, active query 11:47:49 today; `staging.sgctech.ai` + `traffexcel.sgctech.ai` both → 18025; real user traffic 12:59:51 today; 106 MB |
| `osusproperties` (non-v18) | odoo-test-db | none found | **D** | No owning container; 915 MB, sizeable and ambiguous — do not assume safe |
| `sgc_qa_appraisal_vps` | odoo-test-db | none found | **D** | 3 backends (elevated above the 1-backend cron-scan baseline) — possible real QA activity, unconfirmed; 38 MB |
| `odoo_test_v19` | odoo-test-db | none (nginx upstream defined but port 18027 unpublished by any container) | **B** | Dead route; "test" naming; 0 backends beyond cron-scan baseline; 89 MB |
| `odoo_test_v17` | odoo-test-db | none found | **B** | "test" naming; no owning container found; 21 MB |
| `odoo_test_v18` | odoo-test-db | none found | **B** | "test" naming; no owning container found; 23 MB |
| `sgc_release_test_0612` | odoo-test-db | none found | **B** | "test" naming; no owning container found; 30 MB |
| `sgc_staging_v18` | odoo-test-db | none found | **B** | "staging" naming; no owning container found; 60 MB |
| `oca_project_v19_test` | odoo-test-db | none found | **B** | "test" naming; no owning container found; 64 MB |
| `oca_project_v19_demo` | odoo-test-db | none found | **B** | "demo" naming; no owning container found; 64 MB |
| `staging_odoo19_construction_test` | odoo-test-db | none found | **B** | "staging"/"test" naming; no owning container found; 69 MB |
| `merged_odoo19_test` | odoo-test-db | none found | **B** | "test" naming; no owning container found; 79 MB |
| `construction_staging` | odoo-test-db | none found | **B** | "staging" naming; no owning container found; 52 MB |
| `construction_management` | odoo-test-db | none found | **D** | No qualifying name pattern, no owning container found; 78 MB |
| `construction_test_v2` | odoo-test-db | none found | **B** | "test" naming; no owning container found; 49 MB |
| `sgc_recruitment` | odoo-test-db | none found | **D** | No qualifying name pattern, no owning container found; 93 MB |
| `construction_management_fresh` | odoo-test-db | none found | **B** | "fresh" naming; no owning container found; 106 MB |

**Note on `numbackends=1` across most `odoo-test-db` rows above:** this is a repeated artifact of Odoo's internal cron thread on `odoo-staging`/`staging-traffexcel` scanning every database visible on the Postgres host it's pointed at, regardless of `dbfilter` (`dbfilter` only restricts *web* access). It is not evidence of real usage by itself — treated as baseline noise, not "active," per-row unless a container/domain/elevated-backend-count is independently confirmed (as done for the Tier A rows).

---

## Stopped containers

| Container | Image | Stopped since (FinishedAt) | Writable-layer size |
|---|---|---|---|
| `odoo-prod-odoo-prod-run-7beb470ebb1d` | odoo:19.0-sgc | 2026-07-13T14:08:40Z | 8.19 kB |
| `odoo-prod-odoo-prod-run-bd62d44d5726` | odoo:19.0-sgc | 2026-07-13T14:08:27Z | 8.19 kB |
| `odoo-prod-odoo-prod-run-5778a194261d` | odoo:19.0-sgc | 2026-07-13T14:08:12Z | 8.19 kB |
| `sgc-upgrade2` | odoo:19.0 | 2026-07-15T06:08:41Z | 77.8 kB |
| `merged-odoo19` | odoo:19.0 | 2026-07-16T05:50:57Z | 101 MB |

All five appear to be one-off upgrade/run containers (`odoo ... --stop-after-init`-style invocations), not services with their own compose lifecycle. `docker system df` reports 0 dangling images, so the underlying image layers are shared with running containers and would not be reclaimed by removing these stopped containers alone.

---

## Cleanup risk summary (no action taken)

**Tier C/D database disk space:**

| DB | Tier | Size |
|---|---|---|
| `osusproperties_source_v18` | D | 931 MB |
| `osusproperties` (non-v18) | D | 915 MB |
| `demo_presentation_archived_20260717` | C | 71 MB |
| `sgc_recruitment` | D | 93 MB |
| `construction_management` | D | 78 MB |
| `sgc_qa_appraisal_vps` | D | 38 MB |
| `odoo_prod_archived_20260630` | C | 22 MB |
| `sgctech_archived_20260630` | C | 22 MB |
| `scholarix_master_archived_20260630` | C | 7.7 MB (7,887 kB) |
| `erposus_archived_20260630` | C | 7.4 MB (7,575 kB) |
| **Total Tier C/D** | | **≈ 2,185 MB (~2.13 GB)** |

**Stopped containers:** 5 containers, 101.1 MB total writable-layer size (matches `docker system df` "Containers ... 101.1MB (11%) reclaimable").

**Total reclaimable if every Tier C/D database and every stopped container were removed:** **≈ 2.23 GB** (2,185 MB DB + 101.1 MB containers). This does **not** include the separately-reported 12.91 GB of reclaimable Docker *images* or 135.2 MB of unused *volumes* (`docker system df`), which are a distinct cleanup category from what Part 3 asked for and were not itemized per-item here since they weren't tied to specific databases in this pass.

Note: several Tier B databases (the `odoo-test-db` "test"/"staging"/"fresh"-named group with no identifiable owning container) total roughly another 615 MB and were intentionally *not* included in the Tier C/D sum above, since the prompt's own tier definitions place named-test/staging databases in Tier B ("likely safe" candidate), not C/D — surfacing them here only for visibility, not as part of the requested C/D total.

---

"Inventory complete. Awaiting your Tier classification review and explicit per-item go-ahead before any drop/stop/remove action begins."

---

## Actions taken (2026-07-18, post-approval)

User gave explicit per-item sign-off to remove the 5 Tier C archived databases and 5 stopped one-off containers below (Tier A/B/D items were explicitly excluded from scope and left untouched). Executed one item at a time; each database was re-verified via a fresh `pg_stat_activity` zero-connection check and an independent `pg_restore -l` against the locally-pulled Phase 1 dump immediately before drop; each container was re-confirmed still `exited` with unchanged `FinishedAt` immediately before removal.

| Item | Type | Size reclaimed | Pre-drop verification |
|---|---|---|---|
| `demo_presentation_archived_20260717` | DB (demo_presentation_db) | 71 MB | 0 active backends (1 idle cron-artifact conn, terminated via `WITH (FORCE)`); dump verified 13,032 TOC entries |
| `erposus_archived_20260630` | DB (odoo-prod-db) | 7.4 MB | 0 connections; dump verified 6 TOC entries |
| `odoo_prod_archived_20260630` | DB (odoo-prod-db) | 22 MB | 0 connections; dump verified 2,504 TOC entries |
| `scholarix_master_archived_20260630` | DB (odoo-prod-db) | 7.7 MB | 0 connections; dump verified 55 TOC entries |
| `sgctech_archived_20260630` | DB (odoo-prod-db) | 22 MB | 0 connections; dump verified 2,504 TOC entries |
| `odoo-prod-odoo-prod-run-7beb470ebb1d` | Container | ~8 kB | Confirmed exited, FinishedAt unchanged since inventory |
| `odoo-prod-odoo-prod-run-bd62d44d5726` | Container | ~8 kB | Confirmed exited, FinishedAt unchanged since inventory |
| `odoo-prod-odoo-prod-run-5778a194261d` | Container | ~8 kB | Confirmed exited, FinishedAt unchanged since inventory |
| `sgc-upgrade2` | Container | ~78 kB | Confirmed exited, FinishedAt unchanged since inventory |
| `merged-odoo19` | Container | ~101 MB | Confirmed exited, FinishedAt unchanged since inventory |

**Total reclaimed:** ≈130 MB (databases) + ≈101 MB (container writable layers) ≈ 231 MB. Container count on host: 19 → 14. `docker system df` post-cleanup: Containers 0B reclaimable (was 101.1 MB), Local Volumes still 135.2 MB reclaimable (untouched — not in scope), Images still 12.81 GB reclaimable (untouched — not in scope, shared layers with running containers).

All Tier A (`demo_presentation`, `odoo19-sgc`, `osusproperties_v18`, `traffexcel_staging`), Tier B, and Tier D items (including the two ambiguous-ownership `osusproperties`/`osusproperties_source_v18` databases and the `odoo-staging`/`staging-traffexcel` duplicate-config anomaly) were explicitly out of scope for this batch and were not touched.

## Actions taken (2026-07-18, second batch — Tier D content-inspection pass)

User requested dropping all 5 remaining Tier D databases, asserting they were unused AI-agent-generated scaffolding ("slop"). Before dropping any, each was content-inspected (`res_company`/`res_users`/`res_partner` row counts and creation timestamps) to independently confirm that characterization rather than take it on assertion, per the same evidence standard used throughout this engagement.

**Inspection found 2 of the 5 were NOT test data — dropping was declined:**

| Database | Finding | Action |
|---|---|---|
| `osusproperties_source_v18` (demo_presentation_db) | Company `OSUS REAL ESTATE BROKERAGE LLC`, created `2025-05-28 18:20:16.000764`, 1,891 partners, ~10 months of real activity — **identical company name and creation timestamp to the live `osusproperties_v18`**, near-identical partner count (1891 vs 1891/1892) | **NOT dropped** — real business data, likely the source snapshot the live v18 instance was migrated from |
| `osusproperties` (odoo-test-db) | Same company, same creation timestamp, 1,892 partners — sits on the same Postgres instance as the live `osusproperties_v18` (1,347 MB) | **NOT dropped** — real business data, possible independent point-in-time copy of the live production instance |

**Inspection confirmed 3 of the 5 were genuine test/demo scaffolding — dropped after standard verify (zero-connection recheck + independent `pg_restore -l`):**

| Database | Finding | Size reclaimed |
|---|---|---|
| `sgc_qa_appraisal_vps` | Company `YourCompany` (unrenamed Odoo default), every record created at one identical instant (2026-06-24 21:40:47) | 38 MB |
| `construction_management` | Company `YourCompany` (default), all activity confined to a 5-day window | 78 MB |
| `sgc_recruitment` | Companies `My Company (San Francisco)`/`My Company (Chicago)` (Odoo stock demo companies), all activity within one 8-hour window | 93 MB |

**Total reclaimed this batch:** 209 MB. `osusproperties_source_v18` (931 MB) and `osusproperties` (915 MB) remain on the host, unresolved, pending a real decision about their relationship to the live `osusproperties_v18` instance — do not default these to "safe to drop" in any future session without re-confirming against the live instance's current state first.
