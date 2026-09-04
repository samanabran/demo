# Property Hardening — 2026-09-05 Execution Summary

**Branch**: `property/production-hardening`, cut from `0a747ba6c920bad3ab203b230e24b7189f092c83`.
**Basis**: `PROPERTY_CANONICAL_SOURCE_DECISION.md` (merge plan) + `PROPERTY_PHASE2_STATIC_REVIEW.md` (P0 findings) at the repo root.
**Guardrail check (AGENTS.md Rule 1)**: confirmed before any edit — `property/production-hardening` HEAD, `main` HEAD, and `origin/main` all resolved to `0a747ba6c920bad3ab203b230e24b7189f092c83`.

## 1. Additive file recovery (commit `b2f4f62`)

Purely additive per the decision doc — zero files replaced or deleted.

| File | Source | SHA-256 | Verified against decision doc |
|---|---|---|---|
| `LICENSE` | lab 02 (vendor-identical) | `c505f38baaff032aae5a8accef5135220d3f8f51d2939fecbc5efaf446ce72a4` | matches `c505f38baaff...` |
| `CHANGELOG.md` | lab 02 | `8063fc9dd8fe0b23b05f6b9e41016025d099e8689c0f231887f78007539f1f81` | matches `8063fc9dd8fe...` |
| `PRODUCTION.md` | lab 02 | `19ea79d5a427c2cc56d4722d8c9b3360ffb292ec8c8a4ba5681a8626d052e515` | matches `19ea79d5a427...` |
| `tests/test_prop_d1_double_booking.py` | lab 06 | `20f44a70433dd75d76aa0ac41cd18a01734ce5ed53ed6d11b920dcfd3bef5567` | matches `20f44a70433d...` |
| `tests/test_prop_d4_company_consistency.py` | lab 06 | `55efb8d0fe701f7aea88d3a01860c6e60f17ae57d1e47534f5c44b5157b3ff2a` | matches `55efb8d0fe70...` |
| `tests/__init__.py` | merged (GH + lab 06 imports) | `6dda69cf739684cc69d7d41c0c7297a9205066b63e34989a3a496ddf387e666d` | new merged content |

`models/core/property_wizards.py` and `views/core/booking_wizard_views.xml` were **not** ported — both already inspected and ruled superseded by the richer `wizard/property_publish_wizard.py` / `wizard/booking_wizard.py` / `wizard/views/booking_wizard_views.xml` implementations already in production (decision doc blockers 1 & 2, resolved).

## 2. P0 security fix — unauthenticated webhook (commit `45d1ade`)

`controllers/webhook_controller.py`, route `/portal-webhook/<portal_code>`:
- Added `_webhook_enabled()` — checks `ir.config_parameter` `sgc_offplan_rental_property_management.portal_webhook_enabled`, **disabled by default**. The route now refuses (generic `{"status": "error", "message": "Not found"}`) before any DB lookup if the switch is off.
- Added `_verify_signature(portal)` — HMAC-SHA256 over the raw request body (`request.httprequest.get_data()`) keyed by a new `portal.connector.webhook_secret` field, compared via `hmac.compare_digest` against the `X-Signature` header (accepts a `sha256=<hex>` prefix). Fails closed on missing secret, missing header, or mismatch.
- `models/portal/portal_connector.py`: added `webhook_secret` field (admin-group-gated, `tracking=False`, random `secrets.token_urlsafe(32)` default — same pattern as the existing `xml_feed_token`).
- Both the kill-switch and signature failure paths return the same generic message so a probing client can't distinguish "disabled" from "bad portal_code" from "bad signature".

**Not done**: no HMAC key rotation UI, no IP allowlist, no rate limiting — those remain P1/P2 per Phase 2 §5.3 and are out of scope for this pass. The kill-switch means the route is inert in production until someone deliberately turns it on and configures secrets per connector.

## 3. P0 security fix — multi-company isolation (commit `1e2492f`)

`security/security.xml`: added 7 new `ir.rule` records, same domain (`['|', ('company_id','=',False), ('company_id','in',company_ids)]`) and naming convention (`rental_company_restricted_<model>`) as the 10 existing rules:

- `rent.contract`, `sale.contract`, `payment.schedule`, `rera.form.a`, `portal.connector`, `maintenance.product.line` — all confirmed via grep to declare `company_id` and have no prior rule.
- `property.images` — confirmed it independently declares `company_id = fields.Many2one('res.company', ...)` at `models/core/property_details.py:110` before adding its rule (condition satisfied).

## 4. Regression gates (static only — no Docker/DB, per instructions)

| Gate | Result |
|---|---|
| `py_compile` on all 5 changed/added `.py` files | PASS, exit 0, no errors |
| XML well-formedness (`xml.etree.ElementTree.parse`) on `security.xml` | PASS |
| `git diff --check` (whitespace) | PASS, exit 0, no errors |

**Not run** (explicitly out of scope for this pass, needs a live Odoo+Postgres stack): the actual Odoo test suite (`test_prop_d1_double_booking`, `test_prop_d4_company_consistency`, `test_smoke`, etc.), a module install/upgrade.

## 5. Open items carried forward (not attempted, per instructions)

1. **PROP-D5 live psql duplicate-cron check** — needs `ssh vps-root` to the production DB. Decision doc §6.3 / LIVE-CODE-01 §6. Out of scope here.
2. **PROP-D3 forward-migration smoke test** — clean install + upgrade of the module against a disposable Odoo/Postgres stack, to confirm `migrations/19.0.2.27/post-migrate.py` is forward-compatible with the Rule B invariant in `rent_contract.py`. Needs a live stack; not attempted.
3. **LICENSE legal-compatibility confirmation** — business/legal decision for the user (decision doc blocker 7), not a code task.
4. **Running the ported PROP-D1/PROP-D4 tests** — they were written against lab 06's tree (vendor 19.0.2.12 baseline); they have not been executed against the GitHub production tree's post-baseline model code. They import cleanly at the Python-syntax level (py_compile passed) but functional correctness against the current `rent_contract.py`/`sale_contract.py` is unverified.
5. **P3-0** (shadowed duplicate methods in `sale_contract.py`, lines 442/475 and 458/492) — left untouched, per the decision doc's own conclusion ("no code change to make" / "blocked on regression tests").
6. **Phase 2 secondary findings** (not P0): no rate limiting on the public brochure/inquiry routes, `data/update_ir_cron.xml` no-op cleanup, `property_dashboard_register.js` missing an `ir.asset` record, unused portal-role group scaffolding. None addressed in this pass — all were rated Medium/Low/Cosmetic in Phase 2 §8.

## 6. Commits on `property/production-hardening` (this pass)

```
1e2492f fix(sgc_offplan_rental_property_management): add multi-company record rules for 7 unscoped models
45d1ade fix(sgc_offplan_rental_property_management): auth-gate the inbound portal webhook
b2f4f62 fix(sgc_offplan_rental_property_management): recover lost-in-production LICENSE/CHANGELOG/PRODUCTION.md and port PROP-D1/PROP-D4 Rule B tests
```

Nothing pushed anywhere. `main`, the live server, and `docs/PR03_RUNTIME_LOGS/` (the separate, still-paused tenant-isolation mission) were not touched.
