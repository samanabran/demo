# 30_QUARANTINE — Audit-Derived Module Hold List

This directory exists **because of the SGC Odoo estate audit (`scratchpad/audit_out/FULL_AUDIT_SUMMARY_REPORT.md`)** and contains nothing executable — only per-module READMEs that document the legal/provenance status, the evidence trail, and the rules around shipping the corresponding source modules.

The actual source files for each quarantined module remain in their canonical addon location (e.g. `addons/ks_dynamic_financial_report/`). **Do not move them into `30_QUARANTINE/`** — the audit expects the canonical copy to remain so that provenance, version-gate tests, and clean-room re-testing continue to operate against a stable filesystem path.

## How to read this directory

For each module there is a sibling markdown file (`<module_name>.md`) with four blocks:

1. **Classification** — `30_QUARANTINE` per `phase10d/reconciliation_v4.md` cross-tab.
2. **Audit evidence** — the specific phase/file/timestamp that drove the classification.
3. **Block rules** — what is and is not allowed for the module.
4. **Resolution path** — what action(s) by the founder or counsel would lift the hold.

## Quarantine rules (universal)

R1. **No client shipment.** The module may be installed in a development or audit clean-room environment only. It must not appear in any addon-path provided to a customer.
R2. **No white-labeling / re-branding.** Re-publishing the module under any name other than the audit-confirmed author is a breach of the audit and the underlying vendor licence.
R3. **No IP-hours claim.** Until provenance is resolved, the module may not be counted in any deliverable hours invoice, licencing bundle, or IP-asset valuation.
R4. **Strict mode required in production addon paths.** A deployment that wires the addon path must place any quarantined module under a separate `addons_hold/` directory and reference it only via `--addons-hold-path` for legal/IP audit purposes — never via the normal prod path.
R5. **No automatic fix branch.** Automated remediation branches may not touch quarantined modules. Use the `legal-hold/*` branch-naming convention from `phase8/legal_review_pack.md` if founder action is required.

## Module hold list (initial)

| Module | Classification basis | Resolution owner | File |
|---|---|---|---|
| `ks_dynamic_financial_report` | Phase 8 manifest-tampering proof, LGPL-3 (not OPL-1) recovery | Founder + counsel | [`ks_dynamic_financial_report.md`](ks_dynamic_financial_report.md) |
| `sgc_crm_dashboard` | Phase 9 foreign-code fingerprint (Cybrosys header, SmartClinic manifest author) | Founder + counsel | [`sgc_crm_dashboard.md`](sgc_crm_dashboard.md) |
| `sgc_lead_scoring` | Phase 9 four divergent copies, foreign-code fingerprints, broken `UNIQUE(is_default, company_id)` constraint | Founder + counsel | [`sgc_lead_scoring.md`](sgc_lead_scoring.md) |
| `sgc_rental_management` (in `demo_presentation_staging`) | Phase 7+8 quarantine; manifest originally `TechKhedut Inc.`, currently `SmartClinic` | Founder + counsel | [`sgc_rental_management.md`](sgc_rental_management.md) |
| `sgc_construction_management` | Phase 5 confirmed `aos_construction_management` derivation (39/41 shared paths) | Founder + counsel | [`sgc_construction_management.md`](sgc_construction_management.md) |

## Future additions

Add a new module to this directory **only** when:

1. An audit phase (or successor audit) assigns the module to a `3A_*` / `30_QUARANTINE` / `UNDETERMINED_DISPUTED` bucket **and**
2. The `legal-hold/<module-slug>`-named branch in git history is the source of truth, **and**
3. A per-module `30_QUARANTINE/<module>.md` file has been written with classification, evidence, rules, and resolution-path blocks (mirroring the four-module template here).

Do not invent new quarantines from vibes or convention. The hold list is durable state, and the audit's `phase10d/lender_pack.md` reports on it directly.
