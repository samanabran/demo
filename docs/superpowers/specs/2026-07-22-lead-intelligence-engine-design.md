# Lead Intelligence Engine — Design Spec

## Mission

Replace `sgc_lead_scoring`'s current narrow enrichment (a single narrative
chatter note per lead) with a universal AI Sales Intelligence pipeline that
works for any lead entity type — B2B company, B2C individual, and future
types (vendor, partner, investor, recruit) — through one orchestration flow,
one LLM call, and one versioned JSON contract. The system must answer: who is
this lead, what do they need, are they ready to buy, what should SGCTECH
recommend, how should Sales approach the conversation, and what should happen
next.

This spec covers **both B2B and B2C population logic**, built in one
implementation pass (not phased) per explicit decision during brainstorming.

## Global Constraints

- Exactly **one** LLM call per enrichment run. No second inference.
- **One** orchestration pipeline for every entity type — no separate
  B2B/B2C code paths, no duplicate parsers, no duplicate prompts.
- Reuse the existing search infrastructure unchanged:
  `web.research.provider.get_available_chain()`,
  `web.research.service.multi_search()`, the 4-provider chain
  (Tavily/Exa/Serper.dev/SerpAPI), the circuit breaker, the
  `allow_third_party_search` kill switch. Do not rewrite stable search code.
- The universal JSON contract is versioned and must tolerate missing and
  future sections without parser changes — schema evolution must never
  require a parser rewrite.
- Never fabricate values. Fields with no evidence stay explicitly `Unknown`
  (narrative) or absent/null (structured), never guessed.
- Existing scores (`ai_probability_score`, `ai_completeness_score`,
  `ai_clarity_score`, `ai_engagement_score`) are unrelated to this feature
  (they come from a separate form-completeness heuristic) and are untouched.
- Module: extends `sgc_lead_scoring` (not a new module, not
  `sgc_offplan_rental_property_management`). Version bump to `19.0.1.8`.

## Architecture — Pipeline

```
Lead
  → Deterministic Pre-Classifier → Entity Hint
  → Search Providers (existing, unchanged)
  → Evidence Normalization
  → ONE LLM CALL (existing llm_service.py, new prompt/schema)
  → Universal JSON Contract (parsed + validated)
  → Persistence (3 separate artifacts)
  → Executive Summary → Chatter
  → CRM Notebook Tabs (read from persisted JSON)
```

### Deterministic Pre-Classifier

Runs before any search or LLM call. Produces an **Entity Hint** — a
heuristic guess, not authoritative — from signals already on the lead:

- Company Name filled/empty
- Contact Name filled/empty
- Email domain (public providers — gmail.com, yahoo.com, hotmail.com,
  outlook.com, icloud.com — bias toward B2C; anything else biases B2B)
- Website filled/empty
- Whether the lead is linked to an existing `res.partner` with
  `company_type = 'company'`
- Lead source (`source_id`)

Output: `entity_hint` Selection field with values
`b2b_company / sme / enterprise / government / non_profit / b2c_individual /
investor / vendor / supplier / partner / recruit / unknown`.

This value **only** decides which JSON sections get search evidence and
prompt weight (cost/scope control) — it does not replace classification.
The LLM independently classifies within its own JSON response
(`classification.entity_type`), and both values are persisted for
comparison/QA. Divergence between `entity_hint` and
`classification.entity_type` is expected and informative, not an error.

### Search Layer (unchanged)

No changes to `web_research_service.py`'s provider chain, circuit breaker,
caching, or dedup logic. The orchestrator calls `multi_search()` with a
query built from lead name / company name / website exactly as today.

### Evidence Normalization

New step: before constructing the LLM prompt, `multi_search()`'s raw result
list (`[{title, url, snippet, sources: [...]}]`) is transformed into a
normalized evidence list: `[{title, url, snippet, provider, retrieved_at}]`
— one flat, LLM-friendly structure regardless of which provider(s)
contributed. This normalized list is what gets embedded in the prompt, and
is persisted independently (see Persistence) so a future prompt revision can
re-run the LLM against the same evidence without re-querying providers.

### Single LLM Inference

One call via the existing `llm.service` (`call_llm()`), given:

- Normalized evidence
- Entity Hint
- Existing lead field values (name, company, website, contact info)
- The current CRM context (stage, existing notes) where available

The LLM performs classification, reasoning, enrichment, recommendation,
scoring, and summary generation within this single call, returning the
Universal JSON Contract below.

## Universal JSON Contract

Versioned schema (`schema_version` in `metadata`). All top-level keys are
optional except `metadata` and `classification` — a response missing any
other key is valid, not an error. Sections irrelevant to this lead's entity
type are returned as `"not_applicable": true` rather than omitted, so the
UI can distinguish "not asked" from "asked but nothing found."

```json
{
  "metadata": {
    "schema_version": "1.0",
    "prompt_version": "1.0",
    "enrichment_version": "19.0.1.8",
    "timestamp": "2026-07-22T18:00:00Z",
    "execution_duration_ms": 4200,
    "token_usage": {"prompt": 1800, "completion": 900},
    "providers_used": ["tavily", "exa"]
  },
  "classification": {
    "entity_type": "b2c_individual",
    "confidence": "high",
    "reasoning": "..."
  },
  "company_intelligence": {"not_applicable": true},
  "customer_intelligence": {
    "occupation": {"value": "...", "confidence": "medium", "reason": "...", "source": "..."},
    "industry": {...}, "interests": [...], "location": {...},
    "languages": [...], "preferred_communication": {...},
    "buying_profile": {...}, "investment_profile": {...},
    "lifestyle_indicators": [...], "property_interests": {...},
    "financial_readiness_indicators": [...]
  },
  "decision_makers": {"not_applicable": true},
  "business_requirements": {"not_applicable": true},
  "needs_assessment": {
    "current_state": {...}, "desired_state": {...},
    "pain_points": [...], "objectives": [...], "success_criteria": [...]
  },
  "relationship_intelligence": {
    "common_ground": [...], "safe_conversation_topics": [...],
    "ice_breakers": [...], "recent_milestones": [...],
    "regional_insights": {...}, "communication_style": {...},
    "potential_objections": [...], "questions_to_avoid": [...]
  },
  "conversation_intelligence": {
    "conversation_starters": [...], "discovery_questions": [...],
    "rapport_builders": [...], "follow_up_questions": [...],
    "talking_points": [...]
  },
  "buying_intelligence": {
    "budget_readiness": {...}, "timeline": {...}, "urgency": {...},
    "buying_authority": {...}, "buying_intent": {...}
  },
  "implementation_readiness": {"not_applicable": true},
  "opportunity_intelligence": {
    "opportunity_size": {...}, "revenue_potential": {...},
    "suggested_next_action": {...}, "expected_cycle": {...}
  },
  "proposal_intelligence": {"not_applicable": true},
  "recommended_solution": {
    "offerings": ["Off-plan advisory", "Rental management"]
  },
  "scores": {
    "need_score": {"score": 82, "confidence": "high", "reason": "..."},
    "budget_score": {...}, "authority_score": {...}, "timeline_score": {...},
    "urgency_score": {...}, "relationship_score": {...},
    "digital_maturity_score": {...}, "implementation_complexity_score": {...},
    "proposal_confidence_score": {...}, "win_probability_score": {...},
    "opportunity_score": {...}
  },
  "sources": [
    {"provider": "tavily", "url": "...", "retrieved_at": "...", "confidence": "high", "field": "customer_intelligence.occupation"}
  ],
  "summary": {
    "executive_summary": "...", "key_findings": [...],
    "conversation_strategy": "...", "risks": [...],
    "opportunities": [...], "recommended_next_actions": [...]
  }
}
```

For this implementation pass, the LLM prompt requests full population of:
`metadata`, `classification`, `customer_intelligence`, `needs_assessment`,
`relationship_intelligence`, `conversation_intelligence`,
`buying_intelligence`, `opportunity_intelligence`, `recommended_solution`,
`scores`, `sources`, `summary` — for **every** entity type, B2B and B2C
alike (per confirmed scope). B2B-specific sections
(`company_intelligence`, `decision_makers`, `business_requirements`,
`implementation_readiness`, `proposal_intelligence`) are populated when
`entity_hint` indicates a company-type lead, and returned
`not_applicable: true` for individual leads.

### Parser Requirements

- `metadata` and `classification` required; a response missing either is a
  parse failure (triggers the existing retry/failure path).
- Every other top-level key optional.
- Unknown keys in the response are ignored (forward compatible with future
  schema additions without a parser change).
- A section can be present-but-`not_applicable`, present-with-data, or
  absent — all three are valid states, never an error.
- Per-field wrapper `{value, confidence, reason, source}` — the parser
  reads `.value` for structured field promotion and treats a missing
  `.value` as unknown, never substituting a default.

## Scoring Engine

11 scores, each `{score: 0-100, confidence: high/medium/low, reason: str}`
in the JSON: Need, Budget, Authority, Timeline, Urgency, Relationship,
Digital Maturity, Implementation Complexity, Proposal Confidence, Win
Probability, Opportunity.

Each becomes a real stored `Float` field on `crm.lead`
(`ai_need_score`, `ai_budget_score`, ... `ai_opportunity_score`) —
standard, cheap Odoo pattern, filterable/sortable/groupable in list and
pivot views. All 11 `reason` strings are concatenated into one
`ai_scoring_rationale` Text field for display (reconciles "every score
needs an explanation" with the earlier decision to avoid 11 separate
explanation fields) — the granular per-score reason still exists in the
full JSON blob for anyone who needs it broken out.

Digital Maturity Score and Opportunity Score are B2B-flavored by nature;
for individual leads the LLM should still attempt a B2C-appropriate proxy
(e.g., digital maturity = the buyer's own tech-savviness/channel
preference; opportunity = repeat-investment/referral potential) or mark
`confidence: "low"` / omit rather than force a meaningless number.

## Persistence Strategy — 3 Independent Artifacts

1. **Native Odoo fields** (business-critical, searchable) — new fields on
   `crm.lead`:
   - `entity_hint` (Selection, deterministic pre-classifier output)
   - `ai_entity_type` (Selection, LLM's own classification)
   - `ai_entity_type_confidence` (Selection: high/medium/low)
   - 11 score Floats (listed above) + `ai_scoring_rationale` (Text)
   - `ai_budget_tier`, `ai_industry`, `ai_readiness` (Char/Selection —
     curated "business-critical" promoted values per the examples given)
   - `ai_enrichment_evidence` (Text, JSON) — see artifact 3
   - Existing `ai_enrichment_data` field is reused for artifact 2 below

2. **Full AI JSON** — the complete validated LLM response (including
   `not_applicable` sections) stored verbatim in the existing
   `ai_enrichment_data` Text field. Nothing discarded. `metadata`
   (schema_version, token_usage, execution_duration, etc.) is audit/debug
   data, not something Sales filters leads by — it stays inside this JSON
   blob only, with no matching native Odoo field.

3. **Normalized evidence** — the pre-LLM normalized search result list
   (see Evidence Normalization) stored in the new `ai_enrichment_evidence`
   field, independent of the LLM's output. Enables re-running enrichment
   against the same evidence after a prompt change, without re-querying
   Tavily/Exa/Serper/SerpAPI.

## Odoo UI — Notebook Tabs

The lead form already has a 4-tab notebook (Notes / Property Details /
Extra Info / **AI Scoring**). "Modular widgets" are implemented as notebook
tabs (readonly `Html`/`Text` computed fields parsing the stored JSON), not
custom OWL components — matches the existing pattern, ships in this pass,
no new JS/asset-bundle work.

- **Existing "AI Scoring" tab is extended**, not duplicated, to show the
  11 scores + rationale.
- New tabs added: Company Intelligence, Customer Intelligence, Relationship
  Intelligence, Buying Intelligence, Opportunity Intelligence, Proposal
  Intelligence, Executive Summary, Evidence. Each `invisible` unless its
  corresponding JSON section is present and not `not_applicable` (mirrors
  the existing pattern used for Google Maps / provider-specific settings
  fields).

## Privacy & Anonymization

- New `anonymize_customer_names` `ir.config_parameter` toggle (default
  `False`), separate from the existing `anonymize_company_names`. When on,
  hashes/pseudonymizes the lead's contact name before it's sent to any
  third-party search provider — mirrors the existing company-name pattern.
- The existing `allow_third_party_search` kill switch and the
  enrichment wizard's "Force Customer Research" checkbox remain the
  operative consent gates — no new consent flow.
- "Never infer or collect sensitive personal data without consent" is
  enforced at the prompt level (explicit instruction to the LLM) and by
  the confidence-wrapper's `Unknown` convention — not by a new technical
  control beyond what's listed above.

## Backward Compatibility & Migration

This is **not purely additive**. `crm_lead.py::_enrich_lead()`'s current
behavior — one narrative chatter note built from a simple
`{success, results, providers_used}` response — is replaced by the new
pipeline for every lead, not just B2C ones. Existing tests
(`test_crm_lead_enrichment.py`, `test_lead_enrichment_e2e.py`) assert
against the old note shape and old return contract; they will need
rewriting against the new JSON contract and new chatter format, not just
extending. `web_research_service.py`, `web_research_provider.py`, and the
provider clients are unaffected — only the LLM-call/parse/persist layer
in `crm_lead.py` (and the prompt-construction logic, likely a new
`llm_service.py` or `crm_lead.py` helper) changes.

Migration: version bump to `19.0.1.8`, new migration script adding the new
fields (defaults: null/False). Historical `ai_enrichment_data` from before
this change is left as-is (old shape) — not backfilled or re-parsed; the
UI tabs handle a missing/old-shape JSON gracefully (no crash, just empty
tabs) via the same "missing section is valid" parser rule.

## Testing & Validation

- Regression: full existing `sgc_lead_scoring` suite must still pass
  (excluding the intentionally-rewritten enrichment tests above) —
  confirms the untouched search/provider layer stays green.
- New tests: parser tolerates missing sections, missing optional keys,
  unknown/future keys, and a response with only `metadata` +
  `classification` (minimal valid response).
- New tests: entity_hint deterministic classifier against representative
  inputs (public-email + no company → b2c_individual; corporate-email +
  no company → still biased b2b per the corrected heuristic).
- New tests: B2C sample lead (real estate buyer profile) end-to-end
  through the full pipeline, asserting scores/tabs/chatter populate.
- New tests: B2B sample lead end-to-end, asserting B2C-only sections
  return `not_applicable` and B2B sections populate.
- Live verification (browser-driven, same pattern as the just-completed
  web-research-provider live test): confirm a real B2C lead produces a
  genuine LLM-synthesized JSON response, not a mock, before considering
  this feature demo-ready.

## Definition of Done

- One orchestration pipeline handles B2B and B2C (and any future type)
  through the same code path.
- Deterministic pre-classifier produces `entity_hint`; LLM produces its own
  `ai_entity_type` independently; both persist for comparison.
- Exactly one LLM call per enrichment.
- Universal JSON contract implemented, versioned, and tolerant of
  missing/future sections without parser changes.
- Three persistence artifacts (native fields / full JSON / normalized
  evidence) are stored separately as specified.
- All 11 scores + confidence + reason available and displayed.
- Relationship, Conversation, Opportunity, and Proposal Intelligence
  produce actionable content, not just descriptive facts.
- Executive summary is structured into named sections, not one paragraph.
- Existing search/provider infrastructure is untouched and its own tests
  still pass.
- New/rewritten tests cover the new pipeline per the Testing section above.
- A real B2C lead has been live-verified end-to-end (not mocked) before
  this is called demo-ready.
