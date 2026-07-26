# Guardrail: local / GitHub / live-server sync

This repo is mirrored in three places and **all three must be at the exact
same git commit at all times**:

| Copy | Location | How to check HEAD |
|---|---|---|
| Local | `C:\Users\USER\vps-root-planning` | `git log -1 --oneline` |
| GitHub | `https://github.com/samanabran/demo.git` (`origin`) | `git ls-remote origin main` |
| Live server | `vps-root:/opt/odoo/demo_presentation/addons` | `ssh vps-root "cd /opt/odoo/demo_presentation/addons && git log -1 --oneline"` |

This is not optional and not a "nice to have." Every incident that has cost
real, live fixes on this project (the listing-agent fields, the launcher-icon
fix, the brochure PDF layout) happened because one of these three drifted
from the other two and something got silently overwritten.

## Rule 1 — Verify before you touch anything

Before making **any** edit, on any of the three copies, run the three
commands above and confirm all HEADs match. If they don't match:

1. **Stop. Do not edit yet.**
2. Find out why they diverged (see "Reconciling drift" below).
3. Reconcile until all three match.
4. Only then start the actual work the user asked for.

This applies to every agent and every session — no one skips this step, no
one assumes "it was probably fine last time."

## Rule 2 — Never leave an edit uncommitted on the live server

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs
`git fetch && git reset --hard origin/main` on the server on every push to
`main` that touches a watched path. `git reset --hard` **silently destroys
any uncommitted change** on the server, no warning, no backup.

- If you must hotfix directly on the server (SSH), **commit it immediately**
  (`git add` + `git commit`, on the server, in the same session) before doing
  anything else. Do not "come back to it later."
- Then push that commit to `origin/main` from the server, or pull it down
  locally and push from there — either way, get it into GitHub the same
  session. An uncommitted server edit is a ticking time bomb: the next
  unrelated push to `main` (by anyone, for any module) will wipe it.

## Rule 3 — Never overwrite a file (local→server or server→local) without diffing first

Before `scp`-ing or copying a file over its counterpart:

```
ssh vps-root "docker exec demo_presentation cat <path>" > /tmp/live_version
diff /tmp/live_version <local_path>
```

If they differ and you don't know why, that's drift — go resolve it via
Rule 1 before overwriting. Do not assume the git-tracked copy is
automatically the correct one; live hotfixes can exist that were never
committed (see Rule 2).

## Rule 4 — A model field is not "done" until it's visible and verified live

Adding a field to a Python model is only step one. Before calling any field
addition complete, all of the following must be true:

1. Field is added to the model (`fields.py`/model file).
2. Field is added to **at least one view** that a user will actually see
   (form/list/kanban/portal — whichever is relevant). A field that exists
   only on the model and never appears in a view is invisible and, from the
   user's perspective, "not there."
3. The module has been upgraded (`-u <module>`) so the DB column exists —
   check with:
   ```
   ssh vps-root "docker exec demo_presentation_db psql -U odoo -d demo_presentation -c \"SELECT column_name FROM information_schema.columns WHERE table_name='<table>' AND column_name='<field>';\""
   ```
4. The change is committed and pushed, and the deploy ran successfully
   (`gh run list --repo samanabran/demo --limit 3`).
5. You have actually confirmed (live UI screenshot, or at minimum the DB
   query in step 3 plus the view grep in step 2) that the field renders.
   "The code is right" is not the same as "the user can see it."

## Rule 5 — Know what does and doesn't trigger a deploy

`.github/workflows/deploy.yml` only fires on pushes touching an explicit
allowlist of paths (currently the `sgc_*` module dirs, `kyc_management`,
and the workflow file itself — check the file for the current list, it
changes). If you edit something **outside** that list (e.g. a shared
top-level dir, a doc, a script), pushing to GitHub will **not** auto-sync
the server. You must manually `ssh vps-root "cd /opt/odoo/demo_presentation/addons && git pull origin main"` afterward, and re-verify Rule 1's three-way
check before considering the task done.

## Rule 6 — Don't delete "duplicate-looking" directories on a hunch

If you find what looks like a duplicate/orphaned copy of a module's files
(this has happened before with `sgc_construction_management`), before
deleting anything:

1. `diff -rq` the two copies — know exactly which files differ, not just
   that the directories differ.
2. Compare mtimes (or git log history) of the differing files to establish
   which copy is actually newer/current.
3. Grep every `__manifest__.py` in the repo to confirm the directory you're
   about to delete is not referenced anywhere (Odoo manifest data-file paths
   are always relative to that module's own folder, so a directory with no
   `__manifest__.py` next to it is never loaded — confirm this, don't assume
   it).
4. Only then delete, and do it as a single git commit with the evidence
   (diff summary, mtimes, manifest check) in the commit message, so the next
   person/agent can see why it was safe.

## Backup snapshot

A full byte-identical mirror of the live server addons directory lives at
`demo_presentation_addons/` in this repo's parent folder (local-only, not
committed — it's a safety net, not a source of truth). Refresh it
periodically or before any risky operation:

```
ssh vps-root 'cd /opt/odoo/demo_presentation && tar --exclude="__pycache__" --exclude="*.pyc" -czf /tmp/snapshot.tar.gz addons'
scp vps-root:/tmp/snapshot.tar.gz .
tar -xzf snapshot.tar.gz --strip-components=1 -C demo_presentation_addons/
```

## Summary — the one rule that matters

**Local, GitHub, and the live server are the same repo. Treat them as one
thing with three windows into it, not three independent copies.** If you
ever find yourself editing without having just confirmed all three match,
stop and check first.
