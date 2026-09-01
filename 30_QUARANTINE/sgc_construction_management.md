# sgc_construction_management — Hold

> 🧠 **From Hindsight memory** — derivation detail in
> `audit_out/enumeration_gap.md` and `phase5/derivation_proofs/`.

## Classification
`30_QUARANTINE` per `phase10d/reconciliation_v4.md`; provenance class `UNDETERMINED_DISPUTED` (Phase 10-D moved it off the clean `ORIGINAL_SGC` line — `sgc_construction_management` is 10,455 LOC and is *the* largest single TIER_1 module).

## Audit evidence

1. **Confirmed derivation**: 39 of 41 files in upstream `aos_construction_management` share exact relative paths and names with `sgc_construction_management` (173 files) — `audit_out/enumeration_gap.md` explicitly states this is a **confirmed** (not suspected) relationship.
2. **`aos_construction_management` original author**: `leapai.ai` (per manifest recovery).
3. **Code surface expansion**: 41 → 173 files is consistent with "fork + add features." The added surface is presumed-original SGC work but was never independently verified in the audit.
4. **Single largest SGC-claimed module**: by LOC and by file count.

## Block rules (R1–R5 plus)

- **R16 — Provider of record**: the `aos_construction_management` base has not been shown to be SGC-authored or licensed-for-derivative. Anyone shipping `sgc_construction_management` is implicitly shipping a derivative of a third-party base without an established licence trail.
- **R17 — File-by-file provenance**: every file the audit cannot show as SGC-original must be presumed upstream until cleared. The audit's `Phase 10-C` provenance-screened only headline modules; the file-by-file check is unstarted.
- **R18 — Vertical scope**: this module is heavy in real-estate construction-management vertical work and is therefore directly in scope for any "real-estate brokerage template" rollout. **The template does not depend on this module** — see `sgc_realestate_brokerage_template/__manifest__.py`'s `depends` and the comments at the top.

## Resolution path

| Step | Owner | Action |
|---|---|---|
| 1 | Counsel | Was `aos_construction_management` ever licensed for the kind of derivative that produced `sgc_construction_management`? |
| 2 | Engineer | Per-file provenance check: flag every shared-name file and decide whether the current `sgc_construction_management` content matches upstream byte-for-byte or has been rewritten. |
| 3 | Founder | If upstream-derived, relicense or rewrite; if SGC-independent, get explicit per-file proof (not manifest derivation) and document the result. |
| 4 | All | Resolution log under `phase10d+/resolution_log.md`. |

## What you may **not** do

- Include `sgc_construction_management` in any "real-estate brokerage + construction" pre-packaged shipment until R17 clears.
- Reference the module as SGC-original in a client deck, an RFI, or a partner agreement.
- Count its LOC against any defensible IP-ownership figure.
