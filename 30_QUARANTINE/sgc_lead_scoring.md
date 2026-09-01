# sgc_lead_scoring — Hold

> 🧠 **From Hindsight memory** — provenance detail in `audit_out/duplicates.csv`,
> `audit_out/multi_tenant_blockers.json` (M5 / 2h item), and `audit_out/fixes_applied.json`.

## Classification
`30_QUARANTINE` per `phase10d/reconciliation_v4.md`; provenance class `UNRESOLVED` (4 divergent copies, foreign-code fingerprints); multi-tenant blocker M5.

## Audit evidence

1. **Four divergent copies** in the estate (`audit_out/duplicates.csv`); the primary copy sits in `addons/sgc_lead_scoring/`, three others are quarantined for divergence.
2. **`UNIQUE(is_default, company_id)` constraint** (`audit_out/multi_tenant_blockers.json` M5 / 2h) is architecturally wrong even for single-tenant use with 2+ scoring providers — a flagged blocking issue.
3. **Hardcoded `http://localhost:8069`** fallbacks across at least one model layer (`audit_out/coupling_findings.csv`). <!-- audit-lint: disable=tier1/localhost -->
4. **Phase 6 partial-unique-index Postgres fix was real** — but is unrelated to the provenance question. Even after the SQL fix, the module does not exit the hold.

## Block rules (R1–R5 plus)

- **R9 (foreign-code fingerprint)** and **R12 — multi-tenant SQL constraint that pretends to be unique without DB enforcement**: do not deploy until the constraint is replaced with a partial unique index that honours `company_id`.
- **R13 — Hardcoded default server URL**: must come from `ir.config_parameter` (`sgc.default_score_endpoint`), not `http://localhost:8069`. <!-- audit-lint: disable=tier1/localhost -->

## Resolution path

| Step | Owner | Action |
|---|---|---|
| 1 | Counsel | Was `sgc_lead_scoring` an SGC build (whole-cloth), a fork, an externally commissioned build, or a handoff from an acquisition? |
| 2 | Engineer | Replace `UNIQUE(is_default, company_id)` with a real partial-index migration. |
| 3 | Engineer | Parameterise the localhost fallback to `ir.config_parameter`. |
| 4 | All | Document the fix-and-resolve in `phase10d+/resolution_log.md`. |

## What you may **not** do

- Ship `sgc_lead_scoring` to a multi-tenant SaaS deployment of SGC.
- Reference the module in a partner brief.
- Use any divergent copy other than the canonical one in `addons/sgc_lead_scoring/`.
