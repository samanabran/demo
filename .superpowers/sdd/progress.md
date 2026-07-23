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

## Plan Outline (10 tasks per `docs/superpowers/plans/2026-07-22-lead-intelligence-engine.md`)

| # | Task | Constrained by | Splittable |
|---|---|---|---|
| 1 | Bump `__manifest__.py` to `19.0.1.8` | — | yes |
| 2 | Add `response_schema` kwarg to `llm_service.py::call_llm()` | C | yes |
| 3+4 | **Non-splittable unit:** `models/lead_intelligence.py` helper module + `crm_lead.py` orchestrator rewrite | A, B, C, D, E, F.1, G, H, I | NO |
| 5 | `anonymize_customer_names` ir.config_parameter + wiring | F, F.1 | yes |
| 6 | Migration script `migrations/19.0.1.8/pre_migrate.py` | — | yes |
| 7 | Update `views/crm_lead_views.xml` (8 new tabs + extended AI Scoring + list-view column) | G, I | yes |
| 8 | Test rewrites + 4 new test classes (parser tolerance, pre-classifier matrix, B2C E2E, B2B E2E) | A, B, E, G, H | yes |
| 9 | Deploy to `demo_presentation` + full test pass | — | yes |
| 10 | Live verification — real B2C lead, browser-driven | all | yes |

## Task execution log

- Task 1: complete (commits bbfd742..a2d8dd0, review clean)
- Task 2: complete (commits 23ed3c3..aafc023, 1 fix round for 3 Important findings [missing mistral/google test coverage, unused _supports_structured_output(), missing Anthropic tool_choice], re-review clean)
- Task 3+4: complete (commits 40afb47..a1dabeb, review Approved with 1 Important finding [lead.name/partner_name sent to LLM in cleartext under anonymize_customer_names] escalated to user; user chose to extend anonymization to lead.name+partner_name; recorded as spec Decision F.2 at commit 079aa44; fix folded into Task 5 dispatch). test_cron_concurrency.py mock-fixture update (2 lines) verified as legitimate stale-fixture fix, not weakened coverage. 8 pre-existing TestLeadScoring/TestLLMProvider failures confirmed unrelated via baseline diff.
- Task 5: complete (commits 3b5a3d3..3775add, review clean — F.2 fix [shared _anonymize_name_if_enabled helper + lead_name/company_name coverage in prompt+query] + original Settings UI toggle both verified; implementer's self-flagged 4th fix [fallback-subject leak in _build_research_queries] independently judged legitimate, not scope creep)
- Task 6: complete (commits d22878f..0b70c29, 1 fix round for 1 Critical finding [unrequested post-migrate.py stub removed as scope creep], re-review clean). pre-migrate.py uses hyphenated filename per 19.0.1.6 precedent (plan doc's pre_migrate.py with underscore was a typo, corrected during dispatch).
- Task 7: complete (commits 8d59f5e..2ac54c2, review clean — 8 computed Html fields with verified markupsafe escaping discipline, 8 new notebook tabs, tree/kanban additions, 8 new tests all real content assertions; implementer's first pass ran out of turns mid-verification without committing, resumed via SendMessage to finish/commit/report).
- Task 8: complete (commit d46b6e4..c189be9, review Approved, 1 Minor nit [B2B E2E test docstring claims corporate-email fixture but only exercises Rule 4, not Rule 2 — not blocking]). Rewrote test_crm_lead_enrichment.py (6 stale points fixed, 2 dead-behavior tests removed) + test_lead_enrichment_e2e.py + added B2C/B2B E2E tests, all verified against live pipeline code, not guessed. Pre-existing 8-failure baseline corroborated independently across Task 7 and Task 8 reports (13 pre-Task-8 minus 5 fixed-by-rewrite = 8). OUT-OF-DIFF FINDING escalated: crm_lead.py::_lead_intelligence_note() (merged in Task 3+4) interpolates LLM-controlled summary.* text into HTML with zero escaping, then message_post() receives a plain str — Odoo's own anti-XSS default then escapes the WHOLE body (rendering bug: chatter shows literal tags) AND the code has a latent injection gap if that were naively "fixed" by wrapping in Markup() without also escaping per-value. Reviewer recommended a follow-up fix mirroring Task 7's already-established markupsafe.escape() + Markup() pattern before Tasks 9/10 ship. Dispatching that fix now as an unplanned task before Task 9.

## Latest commits

- `bbfd742` docs(lead-intelligence): record plan commit in progress ledger tail
- `e6b1110` docs(lead-intelligence): implementation plan + F resolution recorded
- `b8f3c06` docs(lead-intelligence): F.1 trade-off note for LLM-leg anonymization
- `f3074c1` docs(lead-intelligence): add resolved decisions A-I to spec
- `6a60c6e` docs: design spec for universal lead intelligence engine
- `352d003` feat(web-research): add serper + serpapi providers
- `e6d36a2` Merge branch 'worktree-web-research-provider'
