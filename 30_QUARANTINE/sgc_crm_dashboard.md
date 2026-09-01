# sgc_crm_dashboard — Hold

> 🧠 **From Hindsight memory** — provenance detail in `audit_out/coupling_findings.csv`,
> `audit_out/ksolves_derivation.md`, and `phase9/tampering_forensics.md`.

## Classification
`30_QUARANTINE` per `phase10d/reconciliation_v4.md`; provenance class `UNRESOLVED` (Cybrosys-bylined source, SmartClinic-byline database).

## Audit evidence

1. **Source files carry Cybrosys byline**: at least 8 files begin with
   ```python
   # Author: Mruthul Raj (odoo@cybrosys.com)
   ```
2. **`__manifest__.py` `author` field reads "SmartClinic"** on the canonical copy — a third identity, neither Cybrosys nor SGC.
3. **Five divergent copies** in the estate (`audit_out/duplicates.csv`, ranked #1 by risk-weighted divergence).
4. **Coupling trail** (`audit_out/coupling_findings.csv`): includes hardcoded SGC client email addresses that, if the module is genuine SGC work, would be a stretched fit; if it is Cybrosys work, would be an unauthorised appropriation.

## Block rules (R1–R5 plus)

- **R9 — Foreign-code fingerprint**: the Cybrosys header is in source files, which `phase9/tampering_forensics.md` flags as a *non-maskable* attribution marker (compared to manifest edits which are reversible).
- **R10 — SmartClinic authorship claim**: the database `author='SmartClinic'` field cannot be reconciled with either the Cybrosys source or an SGC team identity without external evidence.
- **R11 — Client engagment**: do not deploy to a customer-facing database until the Cybrosys licence text and any work-for-hire agreement covering the fingerprints are produced.

## Resolution path

| Step | Owner | Action |
|---|---|---|
| 1 | Counsel | Was `sgc_crm_dashboard` actually contracted to Cybrosys? Was it licensed under LGPL-3 (Cybrosys default) or another licence? |
| 2 | Counsel | Was any portion of the codebase contributed back / re-licensed under an SGC master agreement? |
| 3 | Founder | If the answer to either (1) or (2) is "no," the foreign-code portions must be rewritten, not just attributed. |
| 4 | All | Update `docs/audit/MODULE_PROVENANCE.md` with the resolution outcome and link it from the master provenance index. |

## What you may **not** do

- Ship `sgc_crm_dashboard` as part of any "vertical pre-packaged" real-estate brokerage shipment.
- Reference the module in a sales deck, partner brief, or RFI response.
- Count hours in `Phase 9-B / restatement.md` against the proven-SGC-owned line.
