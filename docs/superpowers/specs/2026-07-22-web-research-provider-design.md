# Web Research Provider Redesign — sgc_lead_scoring

**Date:** 2026-07-22
**Module:** `sgc_lead_scoring` (SGC TECH AI)
**Status:** Design — pending user review

## Problem

`sgc_lead_scoring/models/web_research_service.py` exposes a single method
`search_google_custom()` against Google Programmable Search Engine. Issues:

1. **Exposure** — every lead enrichment sends company name, website, and email
   domain plaintext to Google under their standard ToS (training on by default
   unless opt-out is configured).
2. **Quota fragility** — 100 queries/day hard cap. One cron batch over 100
   leads silently breaks; no fallback.
3. **No parallelism** — sequential per query. Each lead waits N × latency.
4. **Stub pipeline** — `crm.lead._enrich_lead()` is a stub that never calls
   web research; the UI is wired but the data flow stops.
5. **No fault tolerance** — bad API key blocks every enrichment; no circuit
   breaker, no retry, no cache.

## Goal

Replace the Google-only stub with a multi-provider, parallel, fault-tolerant
web-research layer plus a real enrichment pipeline. Reduce third-party data
exposure, eliminate single-provider outages, and unblock actual lead
enrichment.

## Non-goals

- Replacing the LLM provider layer (`llm.service` / `llm.provider` stay as-is).
- Changing the scoring weights or prompt template structure.
- Adding new CRM fields beyond what is needed to surface provider metadata.

## Approach (chosen)

**Tavily-primary, Exa-secondary, SearXNG self-hosted last-resort, Google
legacy opt-in.** Provider chain configured via `web.research.provider`
records. Per-query fan-out across enabled providers, deduplicated by domain.
Daily quota + circuit breaker per provider. Full rewrite of
`crm.lead._enrich_lead()` to call the orchestrator and write both web results
and LLM summary.

## Components

| Unit | Role | New / Existing |
|---|---|---|
| `web.research.provider` | Per-provider config: name, type, credentials, daily quota, circuit state | New |
| `web.research.service` | Orchestrator. `search()` and `multi_search()` fan out, merge, cache | Refactor |
| `web.research.result` | Persists per-query results with `query_hash` for dedup; 7-day TTL | New |
| `web.research.audit` | Per-call audit log: provider, query_hash, lead, latency, success | New |
| `web.research.circuit` | Circuit breaker helper, state persisted on provider record | New |
| `crm.lead._enrich_lead()` | Rewrite to call orchestrator and LLM with merged results | Rewrite |
| `lead.enrichment.wizard` | Add "parallel" toggle and provider priority editor | Extend |
| `res.config.settings` | Replace Google-only fields with provider table editor; keep Google legacy | Extend |
| `setup.web.research.wizard` | Replaces `google_search_setup.wizard` for new chain | New |
| `google.search.setup.wizard` | Deprecated, retained for one release as compatibility shim | Existing |

## Per-query flow

1. Hash(query) → check `web.research.result` cache. HIT returns cached.
2. Build provider set: enabled, ordered by `sequence asc`, excluding
   OPEN-circuit and at-quota providers.
3. If `parallel=True`: `concurrent.futures.ThreadPoolExecutor` fans out to all
   providers in the set. Else: iterate sequentially, fall through on failure.
4. Merge: dedupe by domain (extracted from url), keep highest-ranked occurrence,
   attach `sources: [provider_name, ...]` per result.
5. If merged count < `min_results`, retry remaining providers with relaxed query
   (drop restrictive tokens).
6. Persist results with TTL=7 days.
7. Audit row written with `query_hash` (raw query never logged).
8. Return `{success, results, providers_used, cache_hit, latency_ms, reason?}`.

## Per-lead pipeline

1. Sanity: skip if `ai_enrichment_status == 'processing'`.
2. Mark `ai_enrichment_status = 'processing'`.
3. Build queries:
   - `q1 = "{company_name} company profile about"`
   - `q2 = "{company_name} news {current_year}"`
   - `q3 = "site:{website} products services"` (only if website present)
4. `results = env['web.research.service'].multi_search(queries, parallel=True)`.
5. Anonymize: strip phone, email, `internal_note`, `partner_id.name`. Replace
   `lead.id` with a pseudonym before sending to provider.
6. Build prompt from `ir.config_parameter` template
   (`llm_lead_scoring.enrichment_prompt_template`).
7. `llm_resp = env['llm.service'].call_llm(messages=[...])`.
8. Persist:
   - `ai_enrichment_data` = JSON of merged results + `providers_used` + `cache_hits`
   - `ai_enrichment_report` = LLM content
   - `ai_enrichment_status` = `completed` or `partial` or `failed`
   - `ai_last_enrichment_date = now()`
9. Post on lead chatter as internal note (existing behavior).

## Circuit breaker (per provider, persisted on `web.research.provider`)

- 5 failures in a rolling 60s window (oldest failure outside window drops off)
  → state CLOSED→OPEN, `open_until = now + 60s`.
- OPEN until `open_until` → HALF_OPEN.
- HALF_OPEN success → CLOSED.
- HALF_OPEN failure → OPEN with backoff doubled, max 600s.

## Quota counter

- `daily_quota_used` resets at midnight UTC via cron
  (`web.research.reset.daily.quota`).
- When `daily_quota_used >= daily_quota_limit`, provider is skipped without
  network call. Skipped state is logged at INFO.

## Parallel lead processing in cron

- `_cron_enrich_leads()` processes up to 50 leads per cron tick.
- Uses `concurrent.futures.ThreadPoolExecutor(max_workers=5)`.
- Each worker opens its own cursor and commits per-lead
  (`with env.registry.cursor() as cr:` pattern from `odoo.addons.queue_job`).
- Failed leads set `ai_enrichment_status = 'failed'` and continue.

## Error handling

| Scenario | Behavior |
|---|---|
| Provider 5xx | Retry once with `time.sleep(2^attempt)`; second failure opens circuit 60s, skip |
| Provider 429 | Read `Retry-After` header; default 30s; mark at-quota for the day; skip |
| Provider 401/403 | No retry; UserError in setup wizard; in prod, log + disable + `mail.activity` to admin |
| All providers exhausted | Return `{success: False, reason: 'all_providers_unavailable'}`; `_enrich_lead` falls back to LLM-knowledge-only path |
| LLM call fails | Persist web results anyway; status='partial'; "web research saved, AI summary failed" |
| `< min_results` | Log warning, don't fail |

## Security & privacy

- **Credentials** — stored in `ir.config_parameter` with `groups_id` =
  `base.group_system` only (admin-readable). Migration step copies existing
  `google_*` keys forward.
- **Log redaction** — never log raw query; only `query_hash`. Centralized
  redaction filter in `__init__.py` logger handler.
- **Anonymization** — phone/email/internal_note/partner_name stripped before
  sending to any provider. `lead.id` replaced with a deterministic SHA-256 hash
  (so cross-query reassociation is still possible locally).
- **CSP/SSRF guard** — `web.research.provider.base_url` validated against
  domain allowlist at write time (no `localhost`, RFC1918, link-local).
- **Master kill switch** — `res.config.settings.allow_third_party_search`
  (default False on upgrade). When off, only SearXNG (self-hosted) is allowed.
- **Optional anonymization** — `res.config.settings.anonymize_company_names`
  hashes company name before query; results re-associated client-side.
- **Audit log** — `web.research.audit` with `(provider_id, query_hash, lead_id,
  success, latency_ms, result_count, ts)`. 90-day retention, cron-purged.

## Backward compatibility

- `google.search.setup.wizard` retained for one release with banner "deprecated,
  use setup.web.research.wizard".
- `search_google_custom` retained as compat method delegating to orchestrator
  with `providers=['google']` filter.
- `llm_lead_scoring.google_search_api_key` and `..._google_search_engine_id`
  config params retained; `pre-migrate.py` seeds one `web.research.provider`
  record from those values on upgrade.

## Testing

- **Unit** (`tests/test_web_research_orchestrator.py`) — provider mock injection;
  hash determinism; circuit state transitions; quota skip; anonymizer output.
  Target 90% coverage on `models/web_research_*.py`.
- **Integration** (`tests/test_provider_clients.py`) — VCR.py fixtures per
  provider: 200, 429, 500. CI runs offline.
- **E2E** (`tests/test_lead_enrichment_e2e.py`) — HttpCase: click AI Enrich on
  a lead, assert internal note has research section + providers_used list.
- **Cron concurrency** — `_cron_enrich_leads()` runs 3-lead batch, asserts all
  reach terminal status, no DB lock contention.

## Rollout

1. **Phase 1 — Shadow** — add new models, seed providers from existing config.
   `_enrich_lead` still calls `search_google_custom`. Verify install/upgrade on
   `sgc_theme_dev`.
2. **Phase 2 — Opt-in** — new UI exposed, default off. Users enable Tavily/Exa.
3. **Phase 3 — Default flip** — after 2 weeks stable opt-in, default chain on.
   Google stays as one of the providers.
4. **Phase 4 — Deprecate** — hide old wizard; remove in 19.0.2.0.

## Risk register

| Risk | Mitigation |
|---|---|
| Provider API shape change | Versioned parser; `api_version` field on provider; pinned fixture versions in CI |
| SearXNG instance down | Treated as provider failure; fall through |
| Cron DB lock contention | Per-lead commit + thread pool max=5 |
| Credential leakage in logs | Redaction filter at logger handler level |
| Backup restore drops new models | Document in `DEPLOYMENT_GUIDE.md`, add to readiness checklist |

## Open questions

- Tavily free tier is 1000/mo. Is that enough headroom for the cron batch
  cadence we want, or should we plan to start on paid immediately?
- SearXNG instance — run on the same VPS as Odoo, or separate container?
  (Affects network policy + deploy doc.)
- Default `min_results` — 3? 5? Driven by typical prompt token budget for the
  LLM we use most.
