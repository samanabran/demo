# Module provenance — audit-driven index

> 🧠 **From Hindsight memory** — this file is the curated manifestation of
> `audit_out/FULL_AUDIT_SUMMARY_REPORT.md` Section 5 and
> `phase10d/tier1_provenance_final.md`. The audit's most-current numbers live
> in those source files; this file is the actionable version for this repo's
> own addon paths.

## Headline numbers

| Basis | Modules | LOC | Caveat |
|---|---|---|---|
| Manifest-derived (Phase 8) | 152 | 259,575 | Editable in place — 5 manifests proven tampered, so this is **not** defensible. |
| TIER_1, git-corroborated (Phase 9) | 37 | 57,423 | Tests who *committed*, not who *authored*. |
| Provenance-screened (Phase 10-C) | 27 | 55,209 | Offline-only screening; 4 stayed unresolved. |
| **ORIGINAL_SGC, final (Phase 10-D)** | **24** | **44,274** | Public-registry check covered only 4 flagged names, not all 24. |
| — of which product code (excluding marketing-site) | **20** | **35,212** | Same caveat. |

After Phase 10-C and 10-D, **the intersection of proven-original-SGC-authorship and independently-verified production-ready is currently zero modules**, per `phase10d/lender_pack.md`. The 20 product modules are *cleared of the prior foreign-code fingerprints* but **not yet** independently verified as live-and-ready.

## What this repository ships with

Path lookup: addon paths in this repo's `docker-compose.yml` are scanned here. The list is **not** a guarantee of SGC ownership — see the hold-list at `30_QUARANTINE/` for modules that audit-flagged.

| Module | Audit class | Held? | Notes |
|---|---|---|---|
| `aml_compliance` | SGC_OWNED (`Phase 9`) | No | Real loaders verified post-fix (3 defects cleared — see `fixes_applied.json`). |
| `kyc_management` | SGC_OWNED (`Phase 9`) | No | Hardcoded SGC/client emails **must** be parameterised (see `HARDCODED_COUPLING.md`). |
| `sgc_dynamic_financial_report` | SGC_OWNED; **0% file overlap with `ks_dynamic_financial_report`** | No | Genuine SGC work — `audit_out/ksolves_derivation.md` Section 3 is the proof. |
| `sgc_realestate_website` | UNRESOLVED (Phase 9) | Watch | Live audit evidence required before client-shipment claim. |
| `sgc_offplan_rental_property_management` | 21,814 LOC (largest single module in the estate) | Watch | Native domain — but its file-by-file provenance is unstarted per `phase10d+/` TODO. |
| `sgc_appraisal` | SGC_OWNED (`Phase 9` baseline) | No | Add as a real-estate template building block. |
| `sgc_assessment` | UNRESOLVED | Watch | Held in audit's `Phase 9` follow-up TODO. |
| `sgc_deals_management` | SGC_OWNED (`Phase 9` baseline) | No | Real-estate vertical core. |
| `sgc_commission` | UNRESOLVED | Watch | Phase 9 unstarted. |
| `sgc_construction_management` | **UNDETERMINED_DISPUTED** (`Phase 10-D`) | **YES** | See `30_QUARANTINE/sgc_construction_management.md`. |
| `sgc_ces_kpi_banner` | SGC_OWNED (`Phase 9`) | No | Lightweight addon, no dependencies. |
| `ks_dynamic_financial_report` | **UNRESOLVED / tamper-recovered** | **YES** | See `30_QUARANTINE/ks_dynamic_financial_report.md`. |
| `sgc_crm_dashboard` | **UNRESOLVED / foreign-code fingerprint** | **YES** | See `30_QUARANTINE/sgc_crm_dashboard.md`. |
| `sgc_lead_scoring` | **UNRESOLVED / 4 divergent copies + M5 constraint** | **YES** | See `30_QUARANTINE/sgc_lead_scoring.md`. |
| `sgc_rental_management` | **UNRESOLVED / staging-only hold** | **YES (staging)** | See `30_QUARANTINE/sgc_rental_management.md`. |

## Per-module template flag

The template addon `sgc_realestate_brokerage_template/__manifest__.py` makes its `depends` list match `SGC_OWNED` or `UNRESOLVED but not HELD` modules. **No quarantined module is in that `depends` list, by design.**

## Updating this file

Any re-derivation by an audit phase must:

1. Update this file with the new numbers.
2. Cross-link the phase file (e.g. `phase10d/lender_pack.md`) and the prose report (`FULL_AUDIT_SUMMARY_REPORT.md`).
3. If a module moves *into* `HELD` status, create a new `30_QUARANTINE/<module>.md` mirroring the four-section template.
4. If a module moves *out of* `HELD` status, the corresponding `30_QUARANTINE/<module>.md` is kept (for audit trail) but the entry in the table above flips to `No` and links to the `Resolution path` block in the hold file.
