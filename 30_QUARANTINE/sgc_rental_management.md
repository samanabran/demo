# sgc_rental_management — Hold (Staging)

> 🧠 **From Hindsight memory** — provenance detail in
> `audit_out/tampering_forensics.md` and `phase9/legal_review_pack.md`.

## Classification
`30_QUARANTINE` per `phase10d/reconciliation_v4.md`; provenance class `UNRESOLVED` (TechKhedut Inc. byline, SmartClinic byline current).

## Audit evidence

1. **Recovered manifest (`.bak`)** carries `author: TechKhedut Inc.`; live `__manifest__.py` reads `author: SmartClinic`.
2. **Operating location**: `/opt/odoo/demo_presentation_staging/addons/sgc_rental_management` (not in the canonical main addon path of `demo_presentation`; this is one reason the hold is documented in `30_QUARANTINE/` for visibility rather than as a runtime block).
3. **No fix branch ever merged to master** (`phase8/legal_review_pack.md`).
4. **Phase 7 fix work collided with this module** before the legal hold was filed; Phase 8 caught and corrected the branches to `legal-hold/sgc_rental_management`.

## Block rules (R1–R5 plus)

- **R1 applies**: no client shipment.
- **R14 — Staging-only**: even within staging, the module is required to sit on a `legal-hold/` addon path and never on the prod addon path.
- **R15 — Origin vendor**: until the TechKhedut→SmartClinic transition is documented (who, when, what licence), the foreign-code fingerprint is presumed un-waived.

## Resolution path

| Step | Owner | Action |
|---|---|---|
| 1 | Founder | Was TechKhedut a contractor and was the work-for-hire transferred? Was SmartClinic a rebrand of SGC or an unrelated entity? |
| 2 | Counsel | Does the work-for-hire document cover derivative works as needed? |
| 3 | Engineer | Once provenance clears, the module may exit `30_QUARANTINE` and re-join the regular `20_FIX` / `10_READY` bucket — but only after `docs/audit/MODULE_PROVENANCE.md` is updated. |

## What you may **not** do

- Promote `sgc_rental_management` from `demo_presentation_staging/` to a production addon path before the legal hold is lifted.
- Use the module in any "real estate brokerage" demo installation without a Law-of-Country clearance note attached.
