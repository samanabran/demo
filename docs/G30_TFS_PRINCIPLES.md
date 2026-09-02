# G30 — TFS Principles and Clocks

> **Authority:** Cabinet Decision 74/2020 Article 21; Wave 3 remediation order item 10; amendment §10 outstanding item 6 (Chambers Data Protection & Privacy 2026, UAE chapter, updated 10 March 2026).
> **Purpose:** Lock in the design principles for the Targeted Financial Sanctions (TFS) freeze / unfreeze workflow so the G30 implementation is grounded in the primary source, not inferred.
> **Status:** Locked. Any deviation must be raised here first.

---

## 1. Three independent clocks

Under Article 21 of Cabinet Decision 74/2020 the obligations run as three distinct clocks, tested independently. A single-clock state machine passes a naive test and fails a tenant.

| Clock | What it measures | When it starts | Deadline | Default state |
|---|---|---|---|---|
| Freeze | Asset freeze ordered and applied | The listing decision by the supervisory authority (EOCN) — **not** our detection | Within 24 hours of the listing decision | `pending` |
| Notification | Notification of the freeze to the Supervisory Authority and the Executive Office | The freeze application | Within 2 business days | `pending` |
| Funds-freeze report | Filing the funds-freeze report through goAML | The freeze application | Within 5 business days | `pending` |

A tenant that has its goAML org ID but lacks its EOCN registration cannot meet the 24-hour clock. The TFS capability is gated on EOCN registration as a `TENANT_CONFIG` field on the readiness gate, named `eocn_registration_reference`. A blank EOCN field blocks the TFS capability.

---

## 2. EOCN is the authoritative source

The EOCN Notification Alert System publication is the authoritative source for the TFS list. A vendor screening response (e.g. from Dow Jones, Refinitiv, ComplyAdvantage) is **evidence**, not the list. Third-party screening lists are explicitly not a compliance guarantee; the official source prevails.

The screening adapter stores the vendor TFS response as evidence — what was checked, when, against which version of the vendor list. A scheduled job reconciles the vendor response against the current EOCN publication, records the reconciliation date, and raises a `process.exception` (classification='data', severity='error') on vendor/EOCN divergence. The reconciliation event is auditable; the divergence is visible to the tenant.

---

## 3. Good-faith protection (Cabinet Decision 74/2020)

A person freezing in good faith under Article 21 is **exempt from civil, criminal and administrative liability** even where the match later proves false. The asymmetry runs entirely toward freezing, not away from it.

Encoded as a design principle rather than a field:

- The freeze transition is **fail-closed without hedging**. A match on a credible list freezes; the user does not get a "are you sure?" prompt that could be used to delay past the 24-hour clock.
- Unfreezing requires documented supervisory-authority instruction. The unfreeze record carries the order reference and the analyst who actioned it.
- False-positive unfreezing is permitted; false-positive freezing is reversed with the evidence of supervisory authority's clearance, not with internal opinion.

This principle is non-negotiable. The freeze is the supervised entity's statutory exposure; the false-positive unfreeze is the tenant's documented remediation.

---

## 4. What ships in Wave 2 item 5 extension

| Component | Class | Notes |
|---|---|---|
| Screening adapter interface extension: `screening.aml.match` and `screening.tfs.match` as distinct call types | VENDOR | Different result schema, different error taxonomy. The interface does not collapse them. |
| TFS hit state machine (party graph node): `none → possible_match → confirmed → freeze_ordered → frozen → unfreeze_ordered → unfrozen → archived` | VENDOR | The transition into `frozen` is a system-block: no funds movement, no contract issue, no disbursement. |
| Freeze record (first-class) | VENDOR | Order source, order date, affected party, assets frozen, reconciliation date, unfreeze rationale. |
| EOCN registration field on the readiness gate | `TENANT_CONFIG` | `eocn_registration_reference`. Blank blocks the TFS capability. |
| Vendor TFS response storage (evidence, not list) | VENDOR | Stored as a structured record on the hit: what was checked, when, vendor list version, response payload. |
| Reconciliation job (vendor ↔ EOCN) | VENDOR | Scheduled. Records reconciliation date. Raises `process.exception` on divergence. |
| Cross-border safeguard (PDPL Article 23) for the screening call | `TENANT_CONFIG` (value) / `VENDOR` (engine) | Captured per the G27 §3 position. |
| Good-faith protection principle | (design principle, not a field) | Encoded in the state machine: freeze is fail-closed without hedging. |

---

## 5. What does NOT ship yet

- The actual TFS state machine code (Wave 2 item 5).
- A reference screening adapter for any specific vendor (DEFER set; per the screening-adapter pattern, the interface is VENDOR and any adapter is a tenant choice).
- The reconciliation job (D-15a).
- The unfreeze record UI (D-15a).
- The vendor/EOCN divergence exception-queue event (D-15a).

These are tracked in the DEFER 20 register as D-13 (G30 TFS) and D-15a (safeguard field).

---

## 6. Re-verification

The TFS clock triad and the EOCN-as-source principle are sourced to public regulator material. They must be re-confirmed against primary sources at the start of each wave, not inherited from this document. The `tfs_freeze_clock_acknowledgement` and `tfs_freeze_action_acknowledgement` fields on the readiness gate are `TENANT_CONFIG` — the tenant acknowledges the current published regime at contract signature. If the regime changes, the tenant re-acknowledges.
