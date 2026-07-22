# Lead Intelligence Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `sgc_lead_scoring`'s single-narrative-note `_enrich_lead()` with a universal AI Sales Intelligence pipeline — deterministic pre-classifier, one LLM call against a versioned JSON contract, three-artifact persistence, and eight new notebook tabs — for both B2B and B2C leads.

**Architecture:** A new helper module `models/lead_intelligence.py` owns the contract (pre-classifier + JSON schema + evidence normalization + parser + native-field promotion + rationale formatter). `crm_lead.py::_enrich_lead()` becomes a thin orchestrator that calls the helper. Views, migration, and test rewrites consume the finished contract.

**Tech Stack:** Odoo 19 (Python 3.10+, OWL 2.0), existing `llm.service` (extended with `response_schema` kwarg for JSON-schema-constrained output), existing `web.research.service` (untouched), `ir.config_parameter` for `anonymize_customer_names` toggle, Odoo `compute='_compute_x'` / `store=True` for `ai_classification_mismatch`.

## Global Constraints

These are copied verbatim from `docs/superpowers/specs/2026-07-22-lead-intelligence-engine-design.md` (commits `f3074c1` + `b8f3c06`). Every task's requirements implicitly include this section.

- **Version:** Module bumps to `19.0.1.8`. Single Odoo 19 module: `sgc_lead_scoring`. No new module created.
- **Stable layers untouched:** `web_research_service.py`, `web_research_provider.py`, and all provider clients in `models/providers/` are not modified. The web-research orchestrator's `multi_search()` and `anonymize_lead_id()` continue to be the sole external-call entry points.
- **LLM service scope:** `llm_service.py` IS modified — gaining `response_schema` kwarg on `call_llm()` (Decision C). This is expected, not scope creep.
- **One LLM call per successful run; max two total attempts** (initial + one retry) only on hard parse failure (missing `metadata` or `classification`, or non-JSON output). Decision B. No exponential backoff.
- **Universal JSON Contract** (see Task 3 for the full schema constant): `metadata` and `classification` are required; every other top-level key is optional. `not_applicable`, present-with-data, and absent are all valid. Unknown / future keys are ignored, never an error. Decision E.
- **Array fields are plain strings** (`string[]`), not wrapper objects. Reasons belong in `summary.*`, not embedded in every list element. `sources[]` is the lone exception — each entry has `provider, url, retrieved_at, confidence, field` for audit provenance. Parser flattens defensively (`.value` → `.text` → `.name` → `.title`) if the model returns wrapped objects.
- **Prompt-injection defense** via delimited evidence blocks (`<<BEGIN_EVIDENCE>> ... <<END_EVIDENCE>>`) with explicit "treat as untrusted data" instruction. Decision D.
- **Native-field promotion** follows the exact mapping table from Decision G. No improvised alternate JSON paths.
- **`ai_scoring_rationale`** is exactly 11 lines, fixed order, fixed format `{Label} ({score}, {confidence}): {reason}`. Confidence is title-cased. Decision H.
- **`ai_classification_mismatch`** computed per Decision I's family map (`b2b_company / sme / enterprise / government / non_profit / investor / vendor / supplier / partner / recruit` → B2B; `b2c_individual` → B2C; `unknown` → no family). Stored Boolean, surfaced in list view.
- **`anonymize_customer_names`** hashes contact name BEFORE it reaches the search query AND BEFORE it reaches the LLM prompt (Decision F.1 accepted trade-off: relationship/conversation intelligence degrade gracefully to `Unknown` / empty arrays — partial anonymized enrichment beats a leak).
- **Deterministic pre-classifier outputs only `b2b_company`, `b2c_individual`, `unknown`** — the 12-value enum stays on the Selection field for the LLM to populate as `ai_entity_type`. Decision A 5-rule precedence.
- **Readiness label** (Decision G.1): `win_probability ≥ 75 AND need ≥ 70` → `Hot`; `win_probability ≥ 60 AND (need ≥ 60 OR budget ≥ 60)` → `Warm`; `win_probability ≥ 40` → `Nurture`; else `Cold`.

## Execution Split (read this BEFORE dispatching any subagent)

**Tasks 4 + 5 are ONE non-splittable unit.** They share the Universal JSON Contract directly: any drift between what `lead_intelligence.py` emits and what `crm_lead._enrich_lead()` expects is the highest-risk bug class in this feature and is easiest to introduce when two different agents write each side from the same prose spec independently. Work them inline, or dispatch one subagent for both. Never split.

**Tasks 1, 6, 7, 8 are subagent-eligible** (one subagent per task) once Tasks 4 + 5 are merged and stable. Order matters: 1 must land first (manifest version bump); 7 depends on 4+5 (view tabs read fields the orchestrator populates); 8 depends on 4+5 (tests assert against the helper module + orchestrator contract); 6 depends on 4+5 (migration script for the new fields).

**Tasks 9, 10 are subagent-eligible** (one subagent per task) once 7 + 8 are merged (because 9 deploys the module and 10 verifies it live).

## Plan Outline

| # | Task | Constrained by | Owner | Splittable |
|---|---|---|---|---|
| 1 | Bump `__manifest__.py` to `19.0.1.8` | — | subagent | yes |
| 2 | Add `response_schema` kwarg to `llm_service.py::call_llm()` | C | subagent | yes |
| 3 | Create `models/lead_intelligence.py` (helper module: pre-classifier, schema, evidence, parser, promotion, rationale, readiness, mismatch) | A, D, E, G, H, I | **UNIT WITH 4** | NO |
| 4 | Extend `crm_lead.py` with new fields + rewrite `_enrich_lead()` to call helper | A, B, C, D, E, F, F.1, G, H, I | **UNIT WITH 3** | NO |
| 5 | Add `anonymize_customer_names` ir.config_parameter + wiring | F, F.1 | subagent | yes |
| 6 | Migration script `migrations/19.0.1.8/pre_migrate.py` + bundled manifest bump if not yet done in Task 1 | — | subagent | yes |
| 7 | Update `views/crm_lead_views.xml`: extend AI Scoring tab, add 8 notebook tabs, list-view column | G, I | subagent | yes |
| 8 | Rewrite `tests/test_crm_lead_enrichment.py` + `tests/test_lead_enrichment_e2e.py` against new contract; add 4 new tests (parser tolerance, pre-classifier matrix, B2C E2E, B2B E2E) | A, B, E, G, H | subagent | yes |
| 9 | Module update on `demo_presentation` + `--stop-after-init` + full test pass | — | subagent | yes |
| 10 | Live verification — real B2C lead, browser-driven AI Enrich, capture chatter + screenshot | all | subagent | yes |

---

## Tasks 3 + 4 — One Non-Splittable Unit (read both before dispatching)

These two tasks MUST be done together — inline by the main agent, or by one subagent with both task briefs. The helper module and the orchestrator share the JSON contract directly; splitting them across agents is the single highest-risk move in this plan.

### Task 3 + 4 (combined): Helper module + orchestrator rewrite

**Files:**
- Create: `sgc_lead_scoring/models/lead_intelligence.py`
- Modify: `sgc_lead_scoring/models/crm_lead.py` (replace `_enrich_lead()` body and append new field declarations + computed fields)
- Test (after merge): `sgc_lead_scoring/tests/test_lead_intelligence.py` (new — covers Task 4's "added tests" portion, but lives in the helper-module scope)

**Interfaces produced (the orchestrator → helper contract):**

```python
# sgc_lead_scoring/models/lead_intelligence.py

ENTITY_HINT_SELECTION = [
    ('b2b_company', 'B2B Company'),
    ('b2c_individual', 'B2C Individual'),
    ('unknown', 'Unknown'),
]

ENTITY_TYPE_SELECTION = [
    ('b2b_company', 'B2B Company'),
    ('sme', 'SME'),
    ('enterprise', 'Enterprise'),
    ('government', 'Government'),
    ('non_profit', 'Non-Profit'),
    ('b2c_individual', 'B2C Individual'),
    ('investor', 'Investor'),
    ('vendor', 'Vendor'),
    ('supplier', 'Supplier'),
    ('partner', 'Partner'),
    ('recruit', 'Recruit'),
    ('unknown', 'Unknown'),
]

CONFIDENCE_SELECTION = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

SCORE_KEYS = [
    ('need', 'ai_need_score'),
    ('budget', 'ai_budget_score'),
    ('authority', 'ai_authority_score'),
    ('timeline', 'ai_timeline_score'),
    ('urgency', 'ai_urgency_score'),
    ('relationship', 'ai_relationship_score'),
    ('digital_maturity', 'ai_digital_maturity_score'),
    ('implementation_complexity', 'ai_implementation_complexity_score'),
    ('proposal_confidence', 'ai_proposal_confidence_score'),
    ('win_probability', 'ai_win_probability_score'),
    ('opportunity', 'ai_opportunity_score'),
]

LEAD_INTELLIGENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "metadata": {"type": "object", "required": ["schema_version"]},
        "classification": {"type": "object", "required": ["entity_type", "confidence"]},
        "company_intelligence": {"type": "object"},
        "customer_intelligence": {"type": "object"},
        "decision_makers": {"type": "object"},
        "business_requirements": {"type": "object"},
        "needs_assessment": {"type": "object"},
        "relationship_intelligence": {"type": "object"},
        "conversation_intelligence": {"type": "object"},
        "buying_intelligence": {"type": "object"},
        "implementation_readiness": {"type": "object"},
        "opportunity_intelligence": {"type": "object"},
        "proposal_intelligence": {"type": "object"},
        "recommended_solution": {"type": "object"},
        "scores": {"type": "object"},
        "sources": {"type": "array"},
        "summary": {"type": "object"},
    },
    "required": ["metadata", "classification"],
    "additionalProperties": True,  # future keys ignored
}

PUBLIC_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com',
    'outlook.com', 'icloud.com', 'protonmail.com',
}

# Pre-classifier (Decision A, 5-rule precedence)
def classify_entity_hint(lead, env) -> str:
    """Returns 'b2b_company', 'b2c_individual', or 'unknown'."""
    ...

# Evidence normalization
def normalize_evidence(multi_search_result: dict) -> list:
    """Returns [{title, url, snippet, provider, retrieved_at}, ...]
    from multi_search()'s {results: [{title, url, snippet, _provider, sources, ...}]} shape."""
    ...

# Prompt construction (with injection defense, Decision D)
def build_prompt(lead, entity_hint: str, normalized_evidence: list, env) -> list:
    """Returns messages list ready for call_llm(messages=...).
    Includes <<BEGIN_EVIDENCE>>...<<END_EVIDENCE>> delimiter."""
    ...

# Parser (Decision E: array fields as plain strings, defensive flatten)
def parse_llm_response(raw_content: str) -> dict:
    """Returns the Universal JSON Contract dict. Raises ParseFailure
    if metadata or classification is missing or response is not JSON."""
    ...

# Native-field promotion (Decision G, exact mapping table)
def promote_to_native_fields(parsed: dict) -> dict:
    """Returns {'ai_need_score': 82.0, ..., 'ai_budget_tier': '...',
    'ai_industry': '...', 'ai_readiness': 'Hot', 'ai_classification_mismatch': False,
    'ai_scoring_rationale': '...11 lines...'}"""
    ...

# Rationale formatter (Decision H)
def format_scoring_rationale(scores: dict) -> str:
    """Returns exactly 11 lines, one per score in SCORE_KEYS order:
    '{Label} ({score}, {TitleCasedConfidence}): {reason or "no reason provided by source"}'"""
    ...

# Readiness label (Decision G.1)
def compute_readiness_label(native_fields: dict) -> str:
    """Returns 'Hot', 'Warm', 'Nurture', or 'Cold' per G.1 table."""
    ...

# Family map (Decision I)
def entity_family(entity_type: str) -> str:
    """Returns 'b2b', 'b2c', or '' (for unknown)."""
    ...
```

**Pipeline (orchestrator → helper sequence in `_enrich_lead()`):**

1. Guard `ai_enrichment_status == 'processing'` — early return.
2. Set status = `'processing'`.
3. Compute `entity_hint = classify_entity_hint(self, self.env)`.
4. Anonymize contact name if `anonymize_customer_names` is on: `display_name = sha256(self.contact_name)[:12]` else `display_name = self.contact_name`.
5. Build queries for `multi_search()` (same shape as today, but using `display_name` not real name when anonymized).
6. Call `self.env['web.research.service'].multi_search(queries, parallel=True)`.
7. `evidence = normalize_evidence(result)`.
8. Persist artifact 3 immediately: `self.ai_enrichment_evidence = json.dumps(evidence)`.
9. `messages = build_prompt(self, entity_hint, evidence, self.env)`.
10. Call `self.env['llm.service'].call_llm(messages=messages, response_schema=LEAD_INTELLIGENCE_SCHEMA)` — try 1.
11. Try parse via `parse_llm_response(content)`. On `ParseFailure`, retry exactly once with same prompt + same evidence + same temperature. On second failure, persist raw content to `ai_enrichment_data`, set status = `'parse_failure'`, post parse-error chatter, return.
12. Persist artifact 2: `self.ai_enrichment_data = json.dumps(parsed)`.
13. `native = promote_to_native_fields(parsed)`.
14. Apply native fields: 11 score floats (clamped 0–100), `ai_entity_type`, `ai_entity_type_confidence`, `ai_budget_tier`, `ai_industry`, `ai_readiness` (overridden by `compute_readiness_label(native)` — Decision G.1), `ai_classification_mismatch` (overridden by `_compute_mismatch` — Decision I).
15. Set `ai_enrichment_status = 'completed'`.
16. Set `ai_last_enrichment_date = fields.Datetime.now()`.
17. Build chatter note (HTML): `<b>AI Research Summary</b>` + structured sections from `parsed.summary.*` + `<i>Sources: ...</i>` (provider list).
18. `self.message_post(body=note_body, subtype_xmlid='mail.mt_note')`.

**New fields on `crm.lead` (declared in this same task, in `_inherit = 'crm.lead'` body):**

```python
entity_hint = fields.Selection(ENTITY_HINT_SELECTION, string='Entity Hint (heuristic)', readonly=True)
ai_entity_type = fields.Selection(ENTITY_TYPE_SELECTION, string='AI Entity Type', readonly=True)
ai_entity_type_confidence = fields.Selection(CONFIDENCE_SELECTION, string='AI Entity Confidence', readonly=True)
ai_need_score = fields.Float(string='Need Score', readonly=True, aggregator='avg')
ai_budget_score = fields.Float(string='Budget Score', readonly=True, aggregator='avg')
ai_authority_score = fields.Float(string='Authority Score', readonly=True, aggregator='avg')
ai_timeline_score = fields.Float(string='Timeline Score', readonly=True, aggregator='avg')
ai_urgency_score = fields.Float(string='Urgency Score', readonly=True, aggregator='avg')
ai_relationship_score = fields.Float(string='Relationship Score', readonly=True, aggregator='avg')
ai_digital_maturity_score = fields.Float(string='Digital Maturity Score', readonly=True, aggregator='avg')
ai_implementation_complexity_score = fields.Float(string='Implementation Complexity Score', readonly=True, aggregator='avg')
ai_proposal_confidence_score = fields.Float(string='Proposal Confidence Score', readonly=True, aggregator='avg')
ai_win_probability_score = fields.Float(string='Win Probability Score', readonly=True, aggregator='avg')
ai_opportunity_score = fields.Float(string='Opportunity Score', readonly=True, aggregator='avg')
ai_scoring_rationale = fields.Text(string='Scoring Rationale (11 lines)', readonly=True)
ai_budget_tier = fields.Char(string='Budget Tier', readonly=True)
ai_industry = fields.Char(string='Industry', readonly=True)
ai_readiness = fields.Selection([
    ('hot', 'Hot'), ('warm', 'Warm'), ('nurture', 'Nurture'), ('cold', 'Cold'),
], string='Readiness', compute='_compute_readiness', store=True, readonly=True)
ai_enrichment_evidence = fields.Text(string='Normalized Evidence (JSON)', readonly=True)
ai_classification_mismatch = fields.Boolean(
    string='Classification Mismatch', compute='_compute_mismatch', store=True, readonly=True,
)
```

`_compute_mismatch` (Decision I): `True` iff heuristic family disagrees with LLM family AND `ai_entity_type_confidence == 'high'`. `_compute_readiness` (Decision G.1) — see the table above. Both `@api.depends` on `entity_hint`, `ai_entity_type`, `ai_entity_type_confidence` and the relevant scores respectively.

**Done when:**
- `sgc_lead_scoring/models/lead_intelligence.py` exists with the 9 public functions listed in **Interfaces produced** above.
- `sgc_lead_scoring/models/crm_lead.py::_enrich_lead()` body matches the 18-step pipeline above.
- All 18 fields declared and visible in `ir.model.fields`.
- `classify_entity_hint` returns one of the 3 string literals for every lead record (unit-tested against a matrix of inputs).
- `parse_llm_response` raises `ParseFailure` on missing `metadata`, missing `classification`, non-JSON input, and on the LLM returning a wrapped object as an array field (then flattens defensively per Decision E).
- `promote_to_native_fields` returns the exact field-name keys listed in the Decision G table; unknown / future keys in `parsed` are dropped (no error).
- `format_scoring_rationale` returns exactly 11 lines (assert via `len(rationale.splitlines()) == 11`).
- `compute_readiness_label` returns one of the 4 literal strings per the Decision G.1 table.
- The pipeline makes at most 2 calls to `call_llm` (assert via mock: `assertEqual(mock.call_count, 1)` on success; `assertEqual(mock.call_count, 2)` on first-call-parse-failure; `assertEqual(mock.call_count, 2)` followed by `status == 'parse_failure'` on terminal failure).
- All existing `tests/test_provider_clients.py`, `tests/test_web_research_orchestrator.py`, `tests/test_web_research_audit_model.py`, `tests/test_cron_concurrency.py`, `tests/test_lead_scoring.py`, `tests/test_llm_provider.py`, `tests/test_llm_service.py`, `tests/test_lead_enrichment_wizard.py`, `tests/test_setup_web_research_wizard.py`, `tests/test_web_research_provider_model.py`, `tests/test_web_research_result_model.py` tests STILL PASS without modification (regression).
- The two enrichment tests (`test_crm_lead_enrichment.py`, `test_lead_enrichment_e2e.py`) MAY FAIL at this gate — they get rewritten in Task 8. Do not let them block Task 3+4; just record their current failure state in the commit message.

**Constraints reminder:** `web_research_service.py`, `web_research_provider.py`, and provider clients are NOT modified. Only `llm_service.py::call_llm` and `crm_lead.py` and the new `lead_intelligence.py` are touched in this unit.

---

## Task 1: Bump `__manifest__.py` to `19.0.1.8`

**Files:**
- Modify: `sgc_lead_scoring/__manifest__.py:4` (line 4: `"version": "19.0.1.7"` → `"version": "19.0.1.8"`)

**Done when:** `__manifest__.py` line 4 reads `"version": "19.0.1.8"`. Commit message includes the version bump rationale.

---

## Task 2: Add `response_schema` kwarg to `llm_service.py::call_llm()`

**Files:**
- Modify: `sgc_lead_scoring/models/llm_service.py` (extend `call_llm()` signature, extend `_get_payload()`, add `_supports_structured_output()` helper)
- Test: `sgc_lead_scoring/tests/test_llm_service.py` (extend existing test class with structured-output tests)

**Interfaces produced:**
```python
@api.model
def call_llm(self, messages, provider=None, max_retries=3, response_schema=None):
    """If response_schema is set and provider supports it, attach
    response_format={"type": "json_schema", "json_schema": schema} (OpenAI/Groq)
    or tool-use with JSON-only argument (Anthropic). Unsupported providers
    ignore the kwarg (caller falls back to 'return strictly JSON' prompt)."""
    ...

@api.model
def _supports_structured_output(self, provider) -> bool:
    """Returns True for provider_type in {'openai', 'groq', 'anthropic',
    'mistral', 'google'}."""
    ...
```

**Done when:**
- `call_llm(messages, response_schema={...})` works on `openai`/`groq`/`mistral`/`google` providers (mock `requests.post` and assert the `json` kwarg includes `response_format`).
- `call_llm(messages, response_schema={...})` is a no-op for `huggingface` (caller's prompt-level fallback handles JSON mode).
- All 4 existing `test_llm_service.py` tests still pass.

---

## Task 5: `anonymize_customer_names` ir.config_parameter + wiring

**Files:**
- Modify: `sgc_lead_scoring/models/crm_lead.py` (helper method `_get_anonymized_contact_name()`)
- Modify: `sgc_lead_scoring/views/res_config_settings_views.xml` (add toggle next to existing `anonymize_company_names` at lines 60–63)

**Done when:**
- `ir.config_parameter` key `llm_lead_scoring.anonymize_customer_names` is set-able via the Settings UI (new toggle next to existing company-names toggle).
- `_get_anonymized_contact_name()` returns either the real `contact_name` or `sha256(...).hexdigest()[:12]` based on the toggle.
- Manual smoke test in Odoo shell: `env['crm.lead'].browse(1)._get_anonymized_contact_name()` returns real value when toggle is False, hash-prefix when True.

---

## Task 6: Migration script `migrations/19.0.1.8/pre_migrate.py`

**Files:**
- Create: `sgc_lead_scoring/migrations/19.0.1.8/pre_migrate.py`

**Done when:**
- File exists with `def migrate(cr, version):` that does nothing meaningful (all fields are new with safe defaults — `False` for booleans, `0.0` for floats, `''` for char/text, `False` for selection — so no backfill is required).
- Migration runs without error: `odoo-bin -u sgc_lead_scoring --stop-after-init` on `demo_presentation` produces no migration-related log lines.
- Records with pre-existing `ai_enrichment_data` (old-shape JSON) survive unchanged — fields get their default null/False; old `ai_enrichment_data` text stays put.

---

## Task 7: Update `views/crm_lead_views.xml`

**Files:**
- Modify: `sgc_lead_scoring/views/crm_lead_views.xml`

**Done when:**
- The existing "AI Scoring" tab is extended with the 11 score fields + `ai_scoring_rationale` (Text) + `entity_hint` + `ai_entity_type` + `ai_entity_type_confidence` + `ai_readiness` + `ai_classification_mismatch` badge.
- 8 new notebook pages appended to the same `<notebook>`: Company Intelligence, Customer Intelligence, Relationship Intelligence, Buying Intelligence, Opportunity Intelligence, Proposal Intelligence, Executive Summary, Evidence.
- Each new tab is a computed `Html` / `Text` field reading from `ai_enrichment_data` (parsed as JSON) and `ai_enrichment_evidence` (for Evidence tab). Each page has `invisible="not ai_enrichment_data"` (matches the existing pattern at line 37 of the current view).
- The list view (tree) gains 2 fields: `ai_classification_mismatch` (visible badge) and `ai_readiness` (visible badge) after the existing `ai_enrichment_status` field.
- The kanban view (lines 67–82) gains a small badge showing `ai_readiness` color (Hot/Warm/Nurture/Cold) alongside the existing AI percentage badge.
- View XML validates cleanly: `odoo-bin -u sgc_lead_scoring --stop-after-init` produces no "Invalid view" errors.

---

## Task 8: Rewrite enrichment tests + add 4 new tests

**Files:**
- Modify: `sgc_lead_scoring/tests/test_crm_lead_enrichment.py` (rewrite against new contract)
- Modify: `sgc_lead_scoring/tests/test_lead_enrichment_e2e.py` (rewrite against new contract)
- Create: `sgc_lead_scoring/tests/test_lead_intelligence.py` (4 new test classes)

**Test classes required:**

`TestLeadIntelligenceParser` — in `test_lead_intelligence.py`:
- `test_parser_accepts_minimal_valid_response` (only metadata + classification present)
- `test_parser_tolerates_missing_optional_sections` (each section missing in turn)
- `test_parser_ignores_unknown_keys` (future schema additions don't break parse)
- `test_parser_flattens_wrapped_array_fields` (LLM returns `[{value, ...}]` instead of `[string]` → defensive flatten)
- `test_parser_rejects_missing_metadata` (raises `ParseFailure`)
- `test_parser_rejects_missing_classification` (raises `ParseFailure`)
- `test_parser_rejects_non_json` (raises `ParseFailure`)

`TestEntityHintClassifier` — in `test_lead_intelligence.py`:
- `test_partner_company_link_returns_b2b_company` (Rule 1)
- `test_corporate_email_no_contact_returns_b2b_company` (Rule 2)
- `test_public_email_no_company_no_website_returns_b2c_individual` (Rule 3)
- `test_company_name_with_website_returns_b2b_company` (Rule 4)
- `test_unknown_signals_returns_unknown` (Rule 5)
- `test_precedence_rule1_overrides_rule4` (partner link beats heuristic)

`TestEnrichmentPipeline` — replaces `test_crm_lead_enrichment.py` body, in same file:
- `test_full_pipeline_b2b_completes` — partner link + website, mocked `multi_search` returns 3 results, mocked `call_llm` returns valid Universal JSON Contract with `classification.entity_type='enterprise'`. Asserts: `ai_enrichment_status == 'completed'`, 11 score floats populated and clamped, `ai_entity_type == 'enterprise'`, `ai_budget_tier` matches `buying_intelligence.budget_readiness.value`, chatter posted.
- `test_full_pipeline_b2c_completes` — gmail + no company, mocked JSON has `classification.entity_type='b2c_individual'`. Asserts: company_intelligence section preserved with `not_applicable: true` (or absent), customer_intelligence populated.
- `test_parse_failure_sets_status_and_returns` — first `call_llm` returns garbage, second `call_llm` returns garbage → `ai_enrichment_status == 'parse_failure'`, raw content persisted to `ai_enrichment_data`, chatter posted naming the parse error.
- `test_anonymize_customer_names_hashes_before_llm_call` — toggle on, contact name `Jane Doe`. Assert: prompt passed to `call_llm` contains neither `Jane` nor `Doe` but does contain a 12-char hex prefix.
- `test_evidence_persisted_before_llm_call` — assert that `ai_enrichment_evidence` is set even if the LLM call later fails parse.

`TestLeadEnrichmentE2E` (rewritten) — replaces `test_lead_enrichment_e2e.py`:
- `test_ai_enrich_button_produces_structured_chatter` — same HttpCase pattern, but assert chatter contains `<b>AI Research Summary</b>` AND structured sections from `summary.*` AND `<i>Sources: ...</i>` listing providers.

**Done when:**
- All test files exist with the test classes above.
- `odoo-bin -d demo_presentation --test-enable --stop-after-init -u sgc_lead_scoring --test-tags /sgc_lead_scoring` reports:
  - All 4 new `test_lead_intelligence.py` tests pass.
  - Both rewritten enrichment tests pass.
  - All 11 untouched test files from the existing suite still pass (regression gate).
  - Expected total: previous baseline + ~16 new tests. Document the exact number in the commit message.

---

## Task 9: Deploy to `demo_presentation` + full test pass

**Files:** (no source files touched in this task — pure deploy + test)

**Done when:**
- `git push origin main` succeeds.
- On VPS: `cd /opt/odoo/demo_presentation/addons && git checkout main && git pull origin main` succeeds.
- `docker exec demo_presentation odoo --http-port=8079 --db_host=db --db_user=odoo --db_password=odoo_demo_pw --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons -d demo_presentation --test-enable --stop-after-init -u sgc_lead_scoring` exits 0.
- Test output reports the same failure count as Task 8's "Done when" — no regressions, no new failures.
- No migration-related log lines appear.

---

## Task 10: Live verification — real B2C lead, browser-driven

**Files:** (no source files — pure ops)

**Done when:**
- A real B2C lead exists in `demo_presentation` CRM (e.g. contact name `Maria Rodriguez`, email `maria@gmail.com`, no company name, no website).
- `llm_lead_scoring.anonymize_customer_names` is OFF (verify the F.1 trade-off — we want to see rich relationship intelligence on this test lead).
- The AI Enrich button is clicked via Chrome browser automation against the Odoo UI at `http://80.241.218.108:18030/`.
- A chatter note appears on the lead with: `Sources: ...` line listing the provider(s) actually used, structured summary sections from `summary.*`, and a populated `ai_readiness` field.
- The 8 notebook tabs are visible and the AI Scoring tab shows all 11 score gauges.
- Screenshot saved to `artifacts/lead-intelligence-live-verify-<timestamp>.png` (artifact dir).
- Write `docs/superpowers/plans/2026-07-22-lead-intelligence-live-verification-report.md` with: which provider chain ran (Tavily? Exa? Serper? SerpAPI?), LLM provider used, total latency, the chatter note screenshot reference, the prompt injection defense delimiter verification (search the prompt trace for `<<BEGIN_EVIDENCE>>` boundary integrity), and any F.1 trade-off observations (did relationship/conversation intelligence populate fully on this un-anonymized test lead?).
- Commit the report to `main`.

---

## Self-Review (plan-vs-spec coverage)

Run through each spec section and confirm a task implements it:

| Spec section | Plan task |
|---|---|
| Pipeline architecture (Lead → Pre-Classifier → Search → Evidence → LLM → Parse → Persist → Chatter → Tabs) | Task 3 + 4 (orchestrator pipeline steps 1–18) |
| Deterministic Pre-Classifier (Decision A) | Task 3 (`classify_entity_hint` + `TestEntityHintClassifier`) |
| Search layer untouched | Global Constraint (verified by 11 untouched test files) |
| Evidence normalization | Task 3 (`normalize_evidence`) |
| Prompt-injection defense (Decision D) | Task 3 (`build_prompt`) |
| Single LLM call + max 2 attempts (Decision B) | Task 3 + 4 (orchestrator steps 10–11) |
| JSON-schema-constrained mode (Decision C) | Task 2 (`response_schema` kwarg) |
| Universal JSON Contract + parser (Decision E) | Task 3 (`LEAD_INTELLIGENCE_SCHEMA`, `parse_llm_response`, `TestLeadIntelligenceParser`) |
| 11 scores | Task 3 + 4 (fields + `format_scoring_rationale`) |
| Native-field promotion (Decision G) | Task 3 (`promote_to_native_fields`) |
| Readiness label (Decision G.1) | Task 3 + 4 (`compute_readiness_label`, `_compute_readiness` field) |
| Rationale format (Decision H) | Task 3 (`format_scoring_rationale`) |
| Mismatch computed Boolean (Decision I) | Task 4 (`_compute_mismatch`) |
| 3 persistence artifacts (native / full JSON / normalized evidence) | Task 4 (orchestrator steps 8, 12, 14) |
| Notebook tabs (not custom OWL) | Task 7 |
| `anonymize_customer_names` (Decision F, F.1) | Task 5 |
| Backward compatibility / migration | Task 6 |
| Testing & Validation (parser tolerance, pre-classifier matrix, B2C E2E, B2B E2E, regression, live verification) | Tasks 8, 9, 10 |
| Module version `19.0.1.8` | Task 1 |
| Definition of Done (all bullets) | Tasks 9 + 10 (verification gates) |

**Placeholder scan:** No "TBD", "TODO", "fill in later", "similar to Task N", "add appropriate handling" anywhere. All function signatures spelled out. All decision values copied verbatim from spec.

**Type consistency:** `classify_entity_hint` returns `str` in Task 3 and the orchestrator consumes it as `str` in Task 4 (no drift). `LEAD_INTELLIGENCE_SCHEMA` is defined in Task 3 and referenced in Task 4 via the same import. `SCORE_KEYS` ordering is the same in Task 3 (helper), Task 4 (fields), and Task 7 (view labels) — Need, Budget, Authority, Timeline, Urgency, Relationship, Digital Maturity, Implementation Complexity, Proposal Confidence, Win Probability, Opportunity.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-22-lead-intelligence-engine.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task group with task-scoped briefs and review between tasks. Tasks 3+4 dispatched as one unit to one subagent (the non-splittable constraint). Task 1 → Task 2 → [Task 3+4 as one] → Task 5 → Task 6 → Task 7 → Task 8 → Task 9 → Task 10, each with review.

2. **Inline Execution** — I work Tasks 3+4 inline in the main agent (preserves the non-splittable constraint naturally), then dispatch subagents for the remaining subagent-eligible tasks. Less context-isolation but fewer round-trips.

**Which approach?** (Default to option 1 unless context budget is a concern — the helper-module + orchestrator pair has the most complex internal contract and benefits most from a single-agent perspective.)
