# Lead Intelligence Engine — Implementation Progress

## Status

- Spec: APPROVED + committed (`b8f3c06`, builds on `f3074c1` → `6a60c6e`)
- Plan: WRITTEN, uncommitted at `docs/superpowers/plans/2026-07-22-lead-intelligence-engine.md`
- Implementation: not started (next gate: plan review, then execution choice)

## Resolved Decisions (frozen into spec at `f3074c1`)

| ID | Decision |
|---|---|
| A | Pre-classifier outputs only `b2b_company` / `b2c_individual` / `unknown`; 12-value enum stays on field Selection |
| B | Max 2 LLM attempts per enrichment; deterministic retry; `parse_failure` status on terminal failure |
| C | JSON-schema-constrained mode via new `response_schema` kwarg on `llm_service.call_llm()` |
| D | Prompt-injection defense via delimited `<<BEGIN_EVIDENCE>>` blocks with "untrusted data" instruction |
| E | Array fields are plain strings; reasons belong in `summary.*`; `sources[]` stays structured |
| F | `anonymize_customer_names` hashes contact name for search AND LLM; no separate LLM kill switch |
| F.1 | Accepted trade-off: anonymization intentionally weakens `relationship_intelligence` and `conversation_intelligence` (those sections degrade to Unknown / empty arrays). Scoring engine stays load-bearing. Partial anonymized enrichment beats a leak. |
| G | Native-field promotion mapping table (entity_hint, ai_entity_type, 11 scores, tier/industry/readiness/mismatch/evidence) |
| H | `ai_scoring_rationale` = exactly 11 lines, `{Label} ({score}, {confidence}): {reason}` |
| I | `ai_classification_mismatch` computed boolean surfaced in UI on family disagreement at High confidence |

## Plan Outline (to be elaborated in next step)

| # | Task |
|---|---|
| 1 | Bump `__manifest__.py` to `19.0.1.8` |
| 2 | Create `models/lead_intelligence.py` — pre-classifier, schema constant, evidence normalization, parser, native-field promotion, score clamping, rationale formatter |
| 3 | Add `response_schema` kwarg to `llm_service.py::call_llm()` + provider-conditional structured-output mode |
| 4 | Extend `crm_lead.py` — 11 score floats, entity_hint, ai_entity_type, ai_entity_type_confidence, ai_budget_tier, ai_industry, ai_readiness, ai_classification_mismatch, ai_scoring_rationale, ai_enrichment_evidence; rewrite `_enrich_lead()` to full pipeline |
| 5 | Add `anonymize_customer_names` `ir.config_parameter` + handling in `crm_lead.py` and `web_research_service.py` prep |
| 6 | Migration script `migrations/19.0.1.8/pre_migrate.py` for new fields with null/False defaults |
| 7 | Update `views/crm_lead_views.xml` — extend AI Scoring tab, add 8 new notebook tabs (Company Intelligence, Customer Intelligence, Relationship Intelligence, Buying Intelligence, Opportunity Intelligence, Proposal Intelligence, Executive Summary, Evidence), list-view column |
| 8 | Rewrite `tests/test_crm_lead_enrichment.py` against new contract |
| 9 | Rewrite `tests/test_lead_enrichment_e2e.py` against new contract |
| 10 | Add new tests: parser tolerance (missing/future sections), pre-classifier matrix, B2C end-to-end, B2B end-to-end |
| 11 | Module update on `demo_presentation` + `--stop-after-init` + full test pass |
| 12 | Live verification — real B2C lead, browser-driven AI Enrich, capture chatter + screenshot |

## Latest commits

- `e6b1110` docs(lead-intelligence): implementation plan + F resolution recorded
- `b8f3c06` docs(lead-intelligence): F.1 trade-off note for LLM-leg anonymization
- `f3074c1` docs(lead-intelligence): add resolved decisions A-I to spec
- `6a60c6e` docs: design spec for universal lead intelligence engine
- `352d003` feat(web-research): add serper + serpapi providers
- `e6d36a2` Merge branch 'worktree-web-research-provider'
