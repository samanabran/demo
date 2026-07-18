# Investigation: `sgc_offplan_rental_property_management` "Deletion" — 2026-07-18

**Scope:** production host vps-root (80.241.218.108), project demo_presentation, live DB with real CRM leads. All commands below are read-only; nothing was restored, reset, cleaned, or modified on the host or in the demo_presentation-addons repo.

## Part 1 — Raw command output

### 1.1 — Filesystem state of the module

```
$ ls -la /opt/odoo/demo_presentation/addons/ | grep -i offplan
drwxr-xr-x 17 197609 197609  4096 Jul 13 20:03 sgc_offplan_rental_property_management

$ find /opt/odoo/demo_presentation/addons -maxdepth 1 -iname "*offplan*"
/opt/odoo/demo_presentation/addons/sgc_offplan_rental_property_management

$ du -sh sgc_offplan_rental_property_management
76M     sgc_offplan_rental_property_management
```

**The directory exists on disk right now, with content (76M).**

### tmux pane cwd re-check (PID derived fresh — see note below)

No specific PID for the audit-session panes was recorded in the prior investigation turns; only tmux pane addresses (`session:window.pane`) and the string `(deleted)` for `pane_current_path` were captured. Derived the actual PIDs now via `tmux list-panes -a -F '#{pane_pid}'` rather than guessing:

```
omc-team-audit-only-do-not-modify-any-c-mrdtro2s:0.0 pid=3078841 path=/opt/odoo/demo_presentation/addons/sgc_offplan_rental_property_management (deleted)
omc-team-audit-only-do-not-modify-any-c-mrdtro2s:0.1 pid=3078873 path=/opt/odoo/demo_presentation/addons/sgc_offplan_rental_property_management (deleted)
omc-team-audit-only-do-not-modify-any-c-mrdtro2s:0.2 pid=3080559 path=/opt/odoo/demo_presentation/addons/sgc_offplan_rental_property_management (deleted)
omc-team-audit-only-do-not-modify-any-c-mrdtro2s:0.3 pid=3081675 path=/opt/odoo/demo_presentation/addons/sgc_offplan_rental_property_management (deleted)
```

**Meaning:** these shells' cwd *handle* is stale (the directory's inode was replaced while they had it open — a normal side effect of a `git reset --hard` rewriting a directory's contents), but the path itself resolves fine right now, as 1.1 shows. This is not evidence of deletion — it's evidence the directory was rewritten while a shell sat inside it.

### 1.2 — Database module state

First attempt used the wrong role name and failed cleanly (no data exposed):
```
$ docker exec demo_presentation_db psql -U odoo_demo -d demo_presentation -c "..."
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  role "odoo_demo" does not exist
```
Retried with the correct role (`odoo`, per prior session's recorded topology):
```
$ docker exec demo_presentation_db psql -U odoo -d demo_presentation -c "SELECT name, state, latest_version FROM ir_module_module WHERE name='sgc_offplan_rental_property_management';"
                  name                  |   state   | latest_version
----------------------------------------+-----------+----------------
 sgc_offplan_rental_property_management | installed | 19.0.2.13
(1 row)
```

**Module shows `installed` in the DB, version 19.0.2.13.**

### 1.3 — Container-side view (`/mnt/extra-addons`)

```
$ docker exec demo_presentation find /mnt/extra-addons -maxdepth 1 -iname "*offplan*"
/mnt/extra-addons/sgc_offplan_rental_property_management
```

**Present inside the container's own view of the mount too — host and container agree.**

### 1.4 — Git history for the path

```
$ git log --oneline --all -- sgc_offplan_rental_property_management | head -20
a001b4f auto: sync 2026-07-17T21:20:04Z
9a90fd0 auto: sync 2026-07-17T14:25:02Z
8794fd3 auto: sync 2026-07-17T03:35:01Z
b6bf390 chore: normalize line endings (server checkout)
edde07b Initial import: demo_presentation addons
```

Diffstat of the most recent commit touching this path:
```
$ git show --stat a001b4f -- sgc_offplan_rental_property_management
commit a001b4facc4a0f3f3e85eb6ecd174db5534a0711
Author: contabo-sgc-server <deploy@contabo-sgc.local>
Date:   Fri Jul 17 23:20:04 2026 +0200

    auto: sync 2026-07-17T21:20:04Z

 .../report/property_brochure_template.xml | 105 +++++++++++++--------
 1 file changed, 64 insertions(+), 41 deletions(-)
```

**No commit in this module's history removes the directory.** The most recent touch is a content edit (64 insertions / 41 deletions in one report template file) — a modification, not a deletion. It's a normal auto-sync commit, additions and deletions within one file, not the directory being dropped.

### 1.5 — Tracked or ignored?

```
$ git check-ignore -v sgc_offplan_rental_property_management
(no output — not ignored)

$ git ls-files sgc_offplan_rental_property_management | head -5
sgc_offplan_rental_property_management/MERGE_NOTES.md
sgc_offplan_rental_property_management/PORTAL_INTEGRATION.md
sgc_offplan_rental_property_management/README.md
sgc_offplan_rental_property_management/__init__.py
sgc_offplan_rental_property_management/__manifest__.py

$ git ls-files sgc_offplan_rental_property_management | wc -l
564
```

**This module is fully tracked (564 files), not ignored, not one of the untracked OCA-staging directories from the earlier autopush diagnosis.** This directly contradicts the premise in the prompt that framed it as "untracked."

### 1.6 — Deploy pipeline steps (verbatim, relevant lines)

Trigger block:
```
on:
  push:
    branches:
      - main
    paths:
      - '.github/workflows/deploy.yml'
      - 'sgc_scroll_hero_homepage/**'
      - 'sgc_scroll_hero_v2/**'
      - 'sgc_offplan_rental_property_management/**'
      ... (16 more sgc_* paths)
  workflow_dispatch:
```
Only destructive-adjacent lines in the whole file:
```
git fetch origin main
git reset --hard origin/main
```
**There is no `git clean`, no `rm -rf`, anywhere in this file against the production host.** The only `clean` reference anywhere is `actions/checkout@v4`'s own internal `clean: true` default, which runs against the GitHub-hosted ephemeral runner's throwaway checkout — not against vps-root at all (confirmed in 1.7's log below).

### 1.7 — Recent pipeline run history + log of the one successful run

```
$ gh run list --repo samanabran/demo --limit 15
completed  success  Fix: move SGC paths from workflow_dispatch to push...   Deploy to VPS  main  push  29635923610  31s  2026-07-18T07:32:55Z
completed  failure  ci: trigger workflow run                               Deploy to VPS  main  push  29635833006  0s   2026-07-18T07:29:54Z
completed  failure  Fix YAML: workflow_dispatch must be sibling of push... Deploy to VPS  main  push  29635423193  0s   2026-07-18T07:15:13Z
completed  failure  Add workflow_dispatch trigger for manual testing       Deploy to VPS  main  push  29635243751  0s   2026-07-18T07:09:06Z
completed  failure  Add GitHub Actions deploy workflow: pull + XML-RPC...  Deploy to VPS  main  push  29633152146  17s  2026-07-18T05:57:28Z
completed  success  Graph Update: pip in /report_xlsx, ...                 Dependency Graph main  dynamic  29632099619  49s  2026-07-18T05:20:39Z
completed  success  Graph Update: pip in /report_xlsx, ...                 Dependency Graph test-throwaway-sisan dynamic 29632024750 51s 2026-07-18T05:18:01Z
```

**Exactly one "Deploy to VPS" run has ever succeeded: `29635923610`, at 2026-07-18T07:32:55Z, 31 seconds, triggered by the commit that was HEAD (`4896017`) at the time of this investigation's earlier rounds.** This ran roughly 12 minutes before this session's first SSH command today.

Grep of that run's log for clean/reset/offplan/rm -rf:
```
$ gh run view --repo samanabran/demo 29635923610 --log | grep -i -E "clean|reset|offplan|rm -rf"
Pull and upgrade modules  Checkout (needed to verify commit)  2026-07-18T07:32:59Z   clean: true
Pull and upgrade modules  SSH to VPS and pull latest          2026-07-18T07:33:04Z   git reset --hard origin/main
Pull and upgrade modules  Cleanup                             2026-07-18T07:33:23Z   ##[group]Run rm -f /tmp/deploy_key
Pull and upgrade modules  Cleanup                             2026-07-18T07:33:23Z   rm -f /tmp/deploy_key
```
**The only `rm -f` is the temp SSH deploy-key cleanup, unrelated to any addons directory. The `clean: true` line is `actions/checkout`'s own runner-side default, not a step that touches vps-root.** The single host-touching command was `git reset --hard origin/main`, executed 2026-07-18T07:33:04Z.

### 1.8 — Odoo runtime logs, last 12h, grep offplan

```
$ docker logs demo_presentation --since 12h 2>&1 | grep -i offplan
2026-07-17 21:26:21,050 1 WARNING ... Error while generating report sgc_offplan_rental_property_management.sales_purchase_agreement_template
2026-07-17 21:26:40,339 1 WARNING ... Error while generating report sgc_offplan_rental_property_management.sales_purchase_agreement_template
2026-07-18 07:49:13,258 1 WARNING ... odoo.addons.sgc_offplan_rental_property_management.models.core.maintenance: AI triage LLM call failed for request 17: HTTPConnectionPool(host='freellmapi-prod', port=3001): ... Failed to resolve 'freellmapi-prod' ...
```
No module-load errors, no "module not found", no traceback about a missing directory. The two 07-17 entries predate today's deploy run and are an unrelated report-template issue. The 07-18 07:49 entry (16 minutes after the successful deploy run) is a DNS-resolution failure for an internal AI-triage feature reaching `freellmapi-prod` — worth separate follow-up, but it is not a "module missing" error; the module loaded and ran code that then hit a network failure.

### 1.9 — Recovery copy sanity check

```
$ ls backups/                                    (local, C:\Users\USER\vps-root-planning)
demo_presentation_20260718_012533.dump   (10,942,302 bytes — confirmed earlier this session)

$ ls addons/sgc_offplan_rental_property_management/   (local copy)
(substantial content present: controllers/, models/, i18n/*.pot, __pycache__ artifacts, etc.)

$ find . -iname "addons_full_*.tar.gz"
(no matches anywhere in the repo)
```

**Correction to the prompt's premise: only 2 of the 3 assumed recovery copies exist.** The DB dump and the local addons copy are present and non-empty. **No `addons_full_*.tar.gz` exists anywhere** — Phase 1 of the backup/cleanup plan (which would create such a tarball) has not yet been executed; this engagement has been in Phase 0 confirmation rounds the whole time, no full-addons tarball has ever been made.

## Part 1 — Conclusion

**a) Is the module directory actually missing from disk right now? NO.** Confirmed present on the host filesystem (1.1, 76M, 564 tracked files) and inside the container's own mount view (1.3).

**b) Does the DB still show it as "installed"? YES** (1.2: `state=installed`, `latest_version=19.0.2.13`).

Since (a) is NO, **this is not an ACTIVE BROKEN INSTALL.** The module is present on disk, present in the container's addons path, and installed in the database — a consistent, non-broken state.

**c) Does the deploy.yml clean/reset logic, combined with the module being untracked, plausibly explain a deletion? NO — the premise doesn't hold.** The module is not untracked (1.5: fully tracked, 564 files, not gitignored). The pipeline's only host-touching command is `git reset --hard origin/main` (1.6, confirmed via the actual run log in 1.7) — no `git clean`, no `rm -rf` against the host. `git reset --hard` alone cannot delete a directory that remains present in the target commit's tree, and no commit in this module's git history (1.4) removes it — the most recent commit is a content edit to one report template file. The observed "(deleted)" symptom was a stale cwd handle in four idle tmux panes from a shell that was sitting inside the directory when `git reset --hard` rewrote its contents — a normal Linux behavior for an open directory handle across a checkout, not data loss. Nothing in the DB (still installed), the filesystem (still present, 76M), the container view (still present), or the runtime logs (no missing-module errors) corroborates an actual deletion.

**d) Recovery copies: 2 of 3 confirmed present and non-empty; 1 does not exist.**
- DB dump (`backups/demo_presentation_20260718_012533.dump`): present, 10,942,302 bytes. ✓
- Local addons copy (`addons/sgc_offplan_rental_property_management/`): present, non-empty. ✓
- Full addons tarball (`addons_full_*.tar.gz`): **does not exist anywhere in this repo.** Phase 1 of the backup plan has not yet run.

## What this changes

The original premise — "the offplan module was deleted, likely by the deploy pipeline's clean/reset step" — is not supported by any of the raw evidence gathered. The module is intact, installed, and unmodified in a way that would indicate loss. The one real finding worth carrying forward: **the deploy pipeline did fire for real and succeed once (07:32:55Z, `git reset --hard origin/main`), roughly 12 minutes before this session's first host check today** — meaning any assumption "the pipeline hasn't run yet" made in earlier confirmation rounds was already stale by the time this investigation started. Part 2 (pipeline containment) does not apply as scoped, since Part 1 did not confirm the reset/clean theory — recommend discussing with the user whether Part 2 is still wanted given this finding, or whether attention should shift to the unrelated `freellmapi-prod` DNS resolution warning (1.8) and the missing `addons_full_*.tar.gz` recovery copy (1.9d) instead.

No credentials, tokens, or passwords were encountered or written anywhere in this investigation.
