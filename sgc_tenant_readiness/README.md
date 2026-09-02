# SGC Tenant Readiness

> Per-tenant onboarding model. Closes **G28** and provides the primary-source basis for **G18**.
> Built from MoJ Notice 247/2026 and the MoET DNFBP Guidelines of March 2026, not from inference.

## What it provides

| Model | Purpose | Closes |
|---|---|---|
| `tenant.compliance.officer` | The CO/MLRO and Alternate. One Primary + one Alternate per tenant. Activation requires a fit-and-proper assessment. | G28 onboarding |
| `tenant.fit.and.proper` | The fit-and-proper assessment: integrity, qualifications, experience, skills, professional path. Records the assessment outcome. | G28 onboarding, MoJ 247/2026 |
| `tenant.readiness.capability` | The catalogue of capabilities a tenant activates (goAML filing, screening, listing, tenancy, off-plan, service charge, e-invoicing). | G28 capability gating |
| `tenant.readiness.state` | Per-capability state per tenant: `not_configured` / `in_progress` / `ready` / `blocked`. Computed `gate_open` boolean. | G28 per-capability gate |
| `tenant.decision.acknowledgement` | The TENANT_DECISION acknowledgement log. Records who, when, what was acknowledged, the cited source. | R9, amendment §3 |
| `tenant.high.risk.override` | The first-class override record. The CO/MLRO's consultation, the management's decision, the override rationale, the mitigation. Segregation enforced: the CO/MLRO and the deciding manager cannot be the same person. | amendment §10.4 |
| `tenant.mlro.segregation.mixin` | Consumer-side mixin. A user holding the CO/MLRO or Alternate role cannot be assigned as agent on a deal or own a customer relationship. | G18 segregation, MoJ 247/2026 |

## Primary sources

This module is built from the following primary sources, not from inference:

| Source | What it provides |
|---|---|
| UAE MoJ Notice 247/2026 | CO/MLRO cannot be outsourced at all (§4.2). Specific tasks may be outsourced only with an LNOO. Alternate required. Fit-and-proper test required. |
| MoET DNFBP Guidelines, March 2026 | Records of qualification assessments and background verification must be maintained. The appointment is notified to the supervisory authority. |
| Cabinet Resolution 134/2025, Article 22 | CO/MLRO report cycle to senior management at least every 6 months. |
| Cabinet Decision 74/2020, Article 21 | Sanctions Compliance Program — distinct from AML screening. Drives the G30 TFS freeze workflow. |

## Class assignment (per amendment §4)

| Field | Class | Default |
|---|---|---|
| CO/MLRO identity, Alternate identity | `TENANT_CONFIG` | Blank |
| Fit-and-proper assessment content | `TENANT_CONFIG` | Blank |
| LNOO reference | `TENANT_CONFIG` | Blank |
| Broker / agent licence credentials | `TENANT_CONFIG` | Blank |
| Screening provider identity, contracted fallback | `TENANT_CONFIG` | Blank |
| goAML organisation ID, registration status | `TENANT_CONFIG` | Blank |
| Trakheesi / Ejari / Mollak / Oqood credentials | `TENANT_CONFIG` | Blank |
| ASP appointment for e-invoicing | `TENANT_CONFIG` | Blank |
| Risk-appetite thresholds, EDD trigger levels, high-risk country list | `TENANT_DECISION` | Blank |
| CO/MLRO recommendation | `TENANT_DECISION` | Blank |
| Management decision | `TENANT_DECISION` | Blank |
| Override rationale | `TENANT_DECISION` | Blank |
| Mitigation | `TENANT_DECISION` | Blank |
| Override segregation rationale (when set) | `TENANT_DECISION` | Blank |

The product provides the engine. The tenants own the values. **No `TENANT_DECISION` field ships with a default value (R9).**

## Tests

```bash
odoo-bin -d test_db -i sgc_tenant_readiness --test-tags sgc_tenant_readiness \
    --addons-path=./addons,./sgc_tenant_readiness --stop-after-init
```

Coverage:
- One Primary + one Alternate per tenant (uniqueness).
- Activation requires a passing fit-and-proper assessment.
- High-risk override segregation (CO/MLRO ≠ deciding manager).
- Override rationale + mitigation required when management overrides.
- Acknowledgement record created on full override lifecycle.
- MLRO segregation mixin: blocks compliance users on deal assignment, allows normal users, requires rationale on override.

## Out of scope

- G29 (bi-annual CO/MLRO report) — Wave 3, template + scheduler.
- G30 (TFS freeze workflow) — Wave 2 item 5 extension.

These will land in their respective waves with their own primary-source derivation.

## Hard rules

- No compliance claim in any user-visible string (R8).
- No `TENANT_DECISION` field ships with a default value (R9).
- No HELD or UNRESOLVED module in `depends` (R2).
- The engine, the capability catalogue, the segregation mixin, the override structure — VENDOR. The values — TENANT_CONFIG / TENANT_DECISION.
