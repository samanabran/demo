# ks_dynamic_financial_report — Hold

> 🧠 **From Hindsight memory** — the canonical location for this hold rationale is
> `audit_out/FULL_AUDIT_SUMMARY_REPORT.md` Sections 4 and 9, and `phase10d/lender_pack.md`.

## Classification
`30_QUARANTINE` per `phase10d/reconciliation_v4.md`; provenance class `UNRESOLVED` (was manifest-attributed SGC, recovered to Ksolves India Ltd.).

## Audit evidence

1. **Recovered `.bak` manifest, byte-identical across 5 snapshot locations:**
   ```yaml
   author: Ksolves India Ltd.
   website: store.ksolves.com
   licence: LGPL-3        # not the live OPL-1
   auto_install: False    # not the live True
   ```
2. **`static/description/index.html`** still carries live, untouched Ksolves branding and an Odoo Apps Store search link.
3. **Database proof** (`osusproperties_v18`): a row `ks_dynamic_financial_report.old_backup` (`author='Ksolves India Ltd.'`, dated 2026-03-13) and `ks_dynamic_financial_report` (`author='SGC TECH AI'`, dated 2026-07-14). The `.bak` row pre-dates the tamper.
4. **Phase 9-B defence**: the original installation trace shows the module arrived LGPL-3; later overwriting licence/auto_install fields does not retroactively grant rights.
5. **Clean-room result**: `sgc_dynamic_financial_report` (SGC's own module) was confirmed *not derived from* `ks_dynamic_financial_report` (0% file overlap by md5). The two are unrelated.

## Block rules (R1–R5 plus)

- **R1 applies**: no client shipment under any name.
- **R6 — Tampering artefact**: the live manifest's `licence` field and `auto_install` flag were edited after the canonical Ksolves release shipped (Phase 9 evidence: `tampering_forensics.md`). Restoring the original values is a *remediation requirement*, not an optional improvement.
- **R7 — Live load behaviour**: `auto_install: True` is the Phase 6 "landmine" (a `groups_id`→`group_ids` rename in v19). It will crash the first dependency-graph evaluation but, per Phase 7, it does *not* re-trigger on already-stable databases. The crash is gone in production but the licence defect remains.
- **R8 — Vendor-license search**: before shipping ever, confirm with `legal@ksolves.com` whether an Odoo Apps Store licence purchase covers any customer in this hold list.

## Resolution path

| Step | Owner | Action |
|---|---|---|
| 1 | Counsel | Was Ksolves ever licensed from Odoo Apps Store (any SKU, any period)? If yes, attach receipt + entitlement matrix. |
| 2 | Counsel | Is the installed copy in `osusproperties_v18` covered by an active subscription? |
| 3 | Founder | Restore the post-tamper manifest in git (`legal-hold/ks-dfr-revert` branch) and rebuild from that HEAD. |
| 4 | All | Once R6 is cleared, the module may exit the hold but will retain `R1` until counsel sign-off is on file at `docs/audit/MODULE_PROVENANCE.md`. |

## What you may **not** do while the hold is active

- Re-license (`licence: OPL-1`) the module in your fork and re-publish.
- Strip the `Ksolves India Ltd.` author string and the Ksolves URL from `static/description/index.html`.
- Replace `auto_install: True` with the original `False` while claiming SGC authorship.
- Add the module to any production addon path or any Docker compose consumed by a client.
