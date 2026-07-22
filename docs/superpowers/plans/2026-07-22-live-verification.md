# Web Research Provider — Live Verification Plan

**Goal:** Prove the 15-task web research provider redesign (merged to `main`
at `e6d36a2`, extended with Serper.dev + SerpAPI at `352d003`) works against
real external APIs and the real Odoo UI on `demo_presentation`, not just
mocked unit tests.

**Why:** All 80 tests from the redesign use `unittest.mock.patch` on
`requests.post`/`requests.get`. No test in the suite has ever made a real
HTTP call to Tavily, Exa, Serper.dev, SerpAPI, or clicked the AI Enrich
button in a browser. The provider client code is logically sound but
unverified against live provider behavior (response shape drift, auth
quirks, rate limiting, latency).

## Scope

**In scope:**
- Live HTTP verification of all 4 paid providers (Tavily, Exa, Serper.dev,
  SerpAPI) in priority order.
- Browser-driven end-to-end test: real Odoo UI, real lead record, real
  AI Enrich button click, real chatter note.
- Env-var-first credential wiring so API keys never touch git or the DB.

**Out of scope (explicit decisions, see Global Constraints):**
- SearXNG self-hosting — skipped per user decision (paid providers cover
  the chain; self-hosting SearXNG is extra Docker ops with no test benefit
  here).
- Google Custom Search (legacy) — not part of this live-verify pass; it
  already has separate coverage via `google.search.setup.wizard` and is
  being deprecated per the redesign.
- Load/stress testing of nested thread pools (cron + multi_search) — flagged
  as a known gap in the original confidence assessment, not addressed here.

## Global Constraints

- **Provider chain order:** Tavily (seq 10) → Exa (seq 20) → Serper.dev
  (seq 30) → SerpAPI (seq 40). SearXNG (seq 50) and Google (seq 60) stay
  seeded but inactive.
- **Kill switch:** `llm_lead_scoring.allow_third_party_search` must be
  flipped to `'True'` on `demo_presentation` for any non-SearXNG provider
  to be reachable (see `web_research_provider.py::get_available_chain`).
  Flip it back to `'False'` after verification completes — this instance
  is a shared demo DB, not a dedicated live-traffic environment.
- **Credential handling:** API keys are set as environment variables on the
  `demo_presentation` container (`TAVILY_API_KEY`, `EXA_API_KEY`,
  `SERPER_API_KEY`, `SERPAPI_API_KEY`). They are NEVER written into this
  plan file, a commit, `ir.config_parameter`, or the `web.research.provider`
  `api_key` field's seed value. `_prepare_query()` in
  `web_research_service.py` reads `os.environ` first and falls back to the
  DB field only if no matching env var is set (see commit `352d003`).
  Provider records on the live DB keep their seeded placeholder
  `api_key` values (`your-tavily-api-key-here` etc.) — the env var
  silently overrides at call time.
- **VPS test command pattern** (per project CLAUDE.md):
  `docker exec demo_presentation odoo --http-port=8079 --db_host=db
  --db_user=odoo --db_password=odoo_demo_pw
  --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
  -d demo_presentation --test-enable --stop-after-init -u sgc_lead_scoring
  --test-tags /sgc_lead_scoring:<Class>`
- **Known zombie-process gotcha:** killing a local SSH session does not
  kill the remote `docker exec` process. Check
  `ps aux | grep 'odoo --http-port'` before assuming a port is free; kill
  with `docker exec demo_presentation kill -9 <pid>` if found.

## Steps

### 1. Sync code to VPS
- `git push origin main` (commit `352d003`, Serper/SerpAPI clients +
  env-var-first key resolution).
- On VPS: `cd /opt/odoo/demo_presentation/addons && git checkout main &&
  git pull origin main`.

### 2. Mocked-test regression pass on VPS (sanity gate before touching live keys)
- Run the full `sgc_lead_scoring` suite (`--test-tags /sgc_lead_scoring`)
  to confirm the new Serper/SerpAPI clients + env-var resolution didn't
  break the 80 previously-green tests, and that the 6 new provider-client
  tests (`test_serper_200_returns_results`, `test_serper_401_marks_failure`,
  `test_serpapi_200_returns_results`, `test_serpapi_429_marks_failure`,
  `test_env_var_api_key_overrides_db_field`) pass.
- Expected: same 10 pre-existing unrelated failures as Task 15 baseline,
  zero new failures.

### 3. Provision VPS environment
- Set `TAVILY_API_KEY`, `EXA_API_KEY`, `SERPER_API_KEY`, `SERPAPI_API_KEY`
  as environment variables visible to the `demo_presentation` container's
  Odoo process (container restart or `docker exec ... env` injection,
  whichever the container's env-loading mechanism supports — confirm at
  execution time, don't assume `docker-compose.yaml` edits are safe on a
  shared instance without checking first).
- Verify: `docker exec demo_presentation env | grep -E 'TAVILY|EXA|SERPER'`
  shows all 4 (values redacted in any output captured to a file/log).

### 4. Seed + activate provider records
- Via `odoo shell` (or the `setup.web.research.wizard` UI), set
  `active=True` on the 4 seeded provider records
  (`web_research_provider_tavily`, `_exa`, `_serper`, `_serpapi`). Leave
  their `api_key` DB field at the seeded placeholder — env vars override.
- Flip `llm_lead_scoring.allow_third_party_search` to `'True'` via
  `ir.config_parameter`.

### 5. Live provider smoke test (server-side, no UI)
- Via `odoo shell` on `demo_presentation`, call
  `env['web.research.service'].search('Microsoft Corporation',
  providers=['tavily'])` (then repeat with `['exa']`, `['serper']`,
  `['serpapi']` individually) and print `result['success']`,
  `len(result['results'])`, and the first result's `title`/`url`.
- This isolates provider-level failures (bad key, deprecated endpoint,
  unexpected response shape) from orchestration-level failures before
  moving to the browser.
- Any provider that fails here gets its own investigation — do not
  proceed to step 6 with a provider chain that has zero working entries.

### 6. Live browser-driven E2E (the actual deliverable)
- Open `demo_presentation`'s Odoo UI via Chrome browser automation.
- Create or reuse a test lead ("Live Verify Lead", `partner_name`: an
  identifiable real company for meaningful search results, e.g.
  "Microsoft Corporation").
- Open the lead form, invoke "Enrich Leads with AI" (the
  `lead.enrichment.wizard`), click **Enrich Leads**.
- Wait for `ai_enrichment_status` to reach `completed` (or `partial`).
- Confirm a chatter message containing "AI Research Summary" was posted,
  and that it names a real provider (`tavily`, `exa`, `serper`, or
  `serpapi`) with a genuine URL/snippet — not a mocked placeholder.
- Screenshot the chatter note as evidence.

### 7. Roll back + document
- Flip `llm_lead_scoring.allow_third_party_search` back to `'False'`
  (providers stay configured+active in the DB but unreachable behind the
  kill switch — matches the redesign's default-off posture).
- Write `docs/superpowers/plans/2026-07-22-live-verification-report.md`
  with: which providers actually returned live results, latencies
  observed, any response-shape surprises vs. the canonical docs fetched
  during planning, the chatter-note screenshot reference, and any
  follow-up items.
- Commit plan + report to `main`.

## Provider API Reference (verified against canonical docs during planning)

| Provider | Endpoint | Auth | Query key | Result field | Verified against |
|---|---|---|---|---|---|
| Tavily | `POST api.tavily.com/search` | body `api_key` | `query` | `results[].content` | Task 6 (unchanged, still current) |
| Exa | `POST api.exa.ai/search` | header `x-api-key` | `query` | `results[].text` | https://exa.ai/docs/reference/search-api-guide-for-coding-agents (fetched 2026-07-22) |
| Serper.dev | `POST google.serper.dev/search` | header `X-API-KEY` | `q` | `organic[].snippet` | serper.dev docs (verified via web search 2026-07-22) |
| SerpAPI | `GET serpapi.com/search?engine=google` | query param `api_key` | `q` | `organic_results[].snippet` | https://serpapi.com/search-api (fetched 2026-07-22) |

**Staleness note:** Exa's current response also includes a `highlights`
list and `highlightScores` array (query-relevant excerpts) that the
existing `_call_exa` client does not use — it reads the full `text` field
instead, which still exists and works. Switching to `highlights` would be
a token-efficiency improvement, not a correctness fix; not part of this
plan's scope.
