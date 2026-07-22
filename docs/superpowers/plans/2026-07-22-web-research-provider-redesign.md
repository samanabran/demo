# Web Research Provider Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `sgc_lead_scoring`'s Google-only web research stub with a multi-provider (Tavily/Exa/SearXNG/Google-legacy), parallel, fault-tolerant research layer, and wire it into a real `crm.lead._enrich_lead()` pipeline.

**Architecture:** New `web.research.provider` (config+circuit+quota), `web.research.result` (cache), `web.research.audit` (audit log) models. `web.research.service` is rewritten from a single `search_google_custom()` method into an orchestrator with `search()` / `multi_search()` that fans out across providers via `ThreadPoolExecutor`, dedupes by domain, and persists cache+audit rows. `crm.lead._enrich_lead()` is rewritten to call the orchestrator then `llm.service.call_llm()`. Rollout is staged (shadow → opt-in → default flip → deprecate) so `search_google_custom` and the Google config params keep working throughout.

**Tech Stack:** Odoo 19 (Python 3.10+), `requests`, `concurrent.futures.ThreadPoolExecutor`, Odoo `TransactionCase`/`HttpCase` test framework, `unittest.mock.patch`.

## Global Constraints

- Module tech-name stays `sgc_lead_scoring`; version bumps to `19.0.1.6` in Task 4 (first data-bearing change) and stays there for the rest of this plan (no further version bumps needed for later tasks — one migration step covers the whole feature).
- Every new/changed API-key field lives behind `groups='base.group_system'` (admin-only), per spec "Security & privacy → Credentials".
- Never log a raw query string — only `query_hash` (spec "Log redaction").
- `res.config.settings.allow_third_party_search` defaults to `False` on upgrade (spec "Master kill switch"); when `False`, only the `searxng` provider type may run.
- `web.research.provider.base_url` must reject `localhost`, RFC1918 (`10.*`, `192.168.*`, `172.16-31.*`), and link-local (`169.254.*`) hosts at write time (spec "CSP/SSRF guard").
- `google.search.setup.wizard`, `search_google_custom()`, and the `llm_lead_scoring.google_search_api_key` / `llm_lead_scoring.google_search_engine_id` config params must keep working through every task in this plan (spec "Backward compatibility").
- Circuit breaker: 5 failures in a rolling 60s window opens the circuit for `circuit_backoff_seconds` (starts at 60, doubles on repeat HALF_OPEN failure, capped at 600).
- All `crm.lead` writes triggered by cron/parallel workers must not crash the whole batch — one lead's failure sets that lead to `failed` and the batch continues.

---

## File Structure Map

| File | Status | Responsibility |
|---|---|---|
| `models/web_research_provider.py` | New | `web.research.provider`: credentials, quota counters, circuit-breaker state machine, SSRF-guard constraint |
| `models/web_research_result.py` | New | `web.research.result`: query-hash-keyed cache row, 7-day TTL |
| `models/web_research_audit.py` | New | `web.research.audit`: per-call audit log row + 90-day purge cron |
| `models/web_research_service.py` | Rewrite | Orchestrator: `search()`, `multi_search()`, per-provider client methods, dedup, anonymizer, `search_google_custom()` compat shim |
| `models/crm_lead.py` | Modify | `_enrich_lead()` full rewrite; `_cron_enrich_leads()` parallelized |
| `models/res_config_settings.py` | Modify | `allow_third_party_search` kill switch, `anonymize_company_names`, provider chain relation |
| `models/__init__.py` | Modify | Import new model modules |
| `wizards/setup_web_research_wizard.py` | New | Multi-provider setup wizard (replaces Google-only wizard for new installs) |
| `wizards/setup_web_research_wizard_views.xml` | New | Views for the above |
| `wizards/google_search_setup_wizard.py` | Modify | Deprecation banner; `action_test_connection` delegates to orchestrator |
| `wizards/google_search_setup_wizard_views.xml` | Modify | Add deprecation banner widget |
| `wizards/lead_enrichment_wizard.py` | Modify | Add `parallel` toggle + provider priority passthrough |
| `wizards/lead_enrichment_wizard_views.xml` | Modify | Expose the new toggle |
| `wizards/__init__.py` | Modify | Import new wizard module |
| `views/web_research_provider_views.xml` | New | List/form for `web.research.provider` |
| `views/res_config_settings_views.xml` | Modify | Provider table editor + kill switch + anonymize toggle |
| `security/ir.model.access.csv` | Modify | ACL rows for 3 new models + setup wizard |
| `security/llm_provider_security.xml` | Modify | Multi-company record rule for `web.research.provider` |
| `data/web_research_provider_data.xml` | New | Seed Tavily/Exa/SearXNG/Google provider records (inactive) |
| `data/ir_cron_data.xml` | Modify | Add audit-purge cron |
| `migrations/19.0.1.6/pre-migrate.py` | New | No-op guard (schema not yet present) |
| `migrations/19.0.1.6/post-migrate.py` | New | Seed one `web.research.provider` (type=google) from legacy config params |
| `__manifest__.py` | Modify | Version bump, new data files, external dep unchanged (`requests` already present) |
| `tests/test_web_research_provider_model.py` | New | Circuit breaker transitions, quota reset, SSRF constraint |
| `tests/test_web_research_orchestrator.py` | New | Hash determinism, cache hit/miss, dedup, min_results retry, anonymizer |
| `tests/test_provider_clients.py` | New | Mocked-HTTP per-provider 200/429/500/401 behavior |
| `tests/test_lead_enrichment_e2e.py` | New | HttpCase: AI Enrich button → internal note has research section |
| `tests/test_cron_concurrency.py` | New | 3-lead parallel batch reaches terminal status, no lock contention |
| `tests/__init__.py` | Modify | Import new test modules |

---

### Task 1: `web.research.provider` model (credentials, quota, circuit breaker)

**Files:**
- Create: `sgc_lead_scoring/models/web_research_provider.py`
- Modify: `sgc_lead_scoring/models/__init__.py`
- Modify: `sgc_lead_scoring/security/ir.model.access.csv`
- Modify: `sgc_lead_scoring/security/llm_provider_security.xml`
- Test: `sgc_lead_scoring/tests/test_web_research_provider_model.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Produces: `web.research.provider` model with fields `name, sequence, provider_type (tavily/exa/searxng/google), api_key, base_url, active, daily_quota_limit, daily_quota_used, quota_reset_date, circuit_state (closed/open/half_open), circuit_open_until, circuit_backoff_seconds, failure_timestamps, total_requests, failed_requests, last_used, company_id`; methods `is_available() -> bool`, `_cb_record_success()`, `_cb_record_failure()`, `record_call(success: bool)`, `get_available_chain(provider_types=None) -> recordset` (classmethod-style, called on the model; enforces the `llm_lead_scoring.allow_third_party_search` master kill switch by forcing `provider_types=['searxng']` when the switch is off).

Note on `web.research.circuit` from the spec's Components table: the spec describes it as "circuit breaker helper, state persisted on provider record" — so it is implemented here as methods on `web.research.provider` (`_cb_*`), not as a separate Odoo model/file. No `models/web_research_circuit.py` exists in this plan.

- [ ] **Step 1: Write the failing tests**

Create `sgc_lead_scoring/tests/test_web_research_provider_model.py`:

```python
# -*- coding: utf-8 -*-
import json
from datetime import timedelta
from unittest.mock import patch

from odoo.fields import Datetime
from odoo.tests.common import TransactionCase


class TestWebResearchProviderModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['web.research.provider'].create({
            'name': 'Test Tavily',
            'provider_type': 'tavily',
            'api_key': 'test-key',
            'daily_quota_limit': 3,
        })

    def test_is_available_default(self):
        self.assertTrue(self.provider.is_available())

    def test_ssrf_guard_rejects_localhost(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['web.research.provider'].create({
                'name': 'Bad SearXNG',
                'provider_type': 'searxng',
                'base_url': 'http://localhost:8080/search',
            })

    def test_ssrf_guard_rejects_rfc1918(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['web.research.provider'].create({
                'name': 'Bad SearXNG 2',
                'provider_type': 'searxng',
                'base_url': 'http://192.168.1.5:8080/search',
            })

    def test_ssrf_guard_allows_public_host(self):
        provider = self.env['web.research.provider'].create({
            'name': 'Good SearXNG',
            'provider_type': 'searxng',
            'base_url': 'https://searxng.example.com/search',
        })
        self.assertTrue(provider.id)

    def test_quota_exhaustion_marks_unavailable(self):
        for _i in range(3):
            self.provider._quota_increment()
        self.assertFalse(self.provider.is_available())

    def test_quota_resets_next_day(self):
        for _i in range(3):
            self.provider._quota_increment()
        self.assertFalse(self.provider.is_available())
        self.provider.quota_reset_date = Datetime.now().date() - timedelta(days=1)
        self.assertTrue(self.provider.is_available())
        self.assertEqual(self.provider.daily_quota_used, 0)

    def test_circuit_opens_after_five_failures_in_window(self):
        for _i in range(5):
            self.provider._cb_record_failure()
        self.assertEqual(self.provider.circuit_state, 'open')
        self.assertFalse(self.provider.is_available())

    def test_circuit_stays_closed_under_five_failures(self):
        for _i in range(4):
            self.provider._cb_record_failure()
        self.assertEqual(self.provider.circuit_state, 'closed')
        self.assertTrue(self.provider.is_available())

    def test_circuit_half_open_after_open_until_elapsed(self):
        for _i in range(5):
            self.provider._cb_record_failure()
        self.assertEqual(self.provider.circuit_state, 'open')
        self.provider.circuit_open_until = Datetime.now() - timedelta(seconds=1)
        self.assertTrue(self.provider.is_available())
        self.assertEqual(self.provider.circuit_state, 'half_open')

    def test_circuit_half_open_success_closes(self):
        for _i in range(5):
            self.provider._cb_record_failure()
        self.provider.circuit_open_until = Datetime.now() - timedelta(seconds=1)
        self.provider.is_available()  # transitions to half_open
        self.provider._cb_record_success()
        self.assertEqual(self.provider.circuit_state, 'closed')
        self.assertEqual(json.loads(self.provider.failure_timestamps), [])

    def test_circuit_half_open_failure_doubles_backoff(self):
        for _i in range(5):
            self.provider._cb_record_failure()
        self.provider.circuit_open_until = Datetime.now() - timedelta(seconds=1)
        self.provider.is_available()  # transitions to half_open
        self.provider._cb_record_failure()
        self.assertEqual(self.provider.circuit_state, 'open')
        self.assertEqual(self.provider.circuit_backoff_seconds, 120)

    def test_get_available_chain_orders_by_sequence_and_excludes_open(self):
        Provider = self.env['web.research.provider']
        Provider.search([]).unlink()
        p1 = Provider.create({'name': 'A', 'provider_type': 'tavily', 'sequence': 20})
        p2 = Provider.create({'name': 'B', 'provider_type': 'exa', 'sequence': 10})
        for _i in range(5):
            p2._cb_record_failure()
        chain = Provider.get_available_chain()
        self.assertEqual(chain.ids, [p1.id])

    def test_get_available_chain_kill_switch_restricts_to_searxng(self):
        Provider = self.env['web.research.provider']
        Provider.search([]).unlink()
        tavily = Provider.create({'name': 'Tavily', 'provider_type': 'tavily', 'sequence': 10})
        searxng = Provider.create({
            'name': 'SearXNG', 'provider_type': 'searxng', 'sequence': 20,
            'base_url': 'https://searxng.example.com/search',
        })
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.allow_third_party_search', 'False')
        chain = Provider.get_available_chain()
        self.assertEqual(chain.ids, [searxng.id])
        self.assertNotIn(tavily.id, chain.ids)

    def test_get_available_chain_kill_switch_on_allows_third_party(self):
        Provider = self.env['web.research.provider']
        Provider.search([]).unlink()
        tavily = Provider.create({'name': 'Tavily', 'provider_type': 'tavily', 'sequence': 10})
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.allow_third_party_search', 'True')
        chain = Provider.get_available_chain()
        self.assertEqual(chain.ids, [tavily.id])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchProviderModel`
Expected: FAIL — `KeyError: 'web.research.provider'` (model does not exist yet).

- [ ] **Step 3: Implement the model**

Create `sgc_lead_scoring/models/web_research_provider.py`:

```python
# -*- coding: utf-8 -*-
import json
import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

_BLOCKED_HOST_PREFIXES = (
    'localhost', '127.', '10.', '192.168.', '169.254.',
    '172.16.', '172.17.', '172.18.', '172.19.',
    '172.20.', '172.21.', '172.22.', '172.23.',
    '172.24.', '172.25.', '172.26.', '172.27.',
    '172.28.', '172.29.', '172.30.', '172.31.',
)
_BLOCKED_HOST_EXACT = ('0.0.0.0', '::1')

_FAILURE_WINDOW_SECONDS = 60
_FAILURE_THRESHOLD = 5
_DEFAULT_BACKOFF_SECONDS = 60
_MAX_BACKOFF_SECONDS = 600


class WebResearchProvider(models.Model):
    _name = 'web.research.provider'
    _description = 'Web Research Provider'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    provider_type = fields.Selection([
        ('tavily', 'Tavily'),
        ('exa', 'Exa'),
        ('searxng', 'SearXNG (self-hosted)'),
        ('google', 'Google Custom Search (legacy)'),
    ], required=True)
    api_key = fields.Char(groups='base.group_system')
    search_engine_id = fields.Char(
        groups='base.group_system',
        help='Google Programmable Search Engine ID (google provider_type only)',
    )
    base_url = fields.Char(help='Required for searxng; self-hosted search endpoint URL')
    active = fields.Boolean(default=True)

    daily_quota_limit = fields.Integer(default=1000)
    daily_quota_used = fields.Integer(default=0, readonly=True)
    quota_reset_date = fields.Date(readonly=True)

    circuit_state = fields.Selection([
        ('closed', 'Closed'),
        ('open', 'Open'),
        ('half_open', 'Half-Open'),
    ], default='closed', readonly=True)
    circuit_open_until = fields.Datetime(readonly=True)
    circuit_backoff_seconds = fields.Integer(default=_DEFAULT_BACKOFF_SECONDS, readonly=True)
    failure_timestamps = fields.Text(default='[]', readonly=True)

    total_requests = fields.Integer(default=0, readonly=True)
    failed_requests = fields.Integer(default=0, readonly=True)
    last_used = fields.Datetime(readonly=True)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.constrains('base_url')
    def _check_base_url_not_internal(self):
        for rec in self:
            if not rec.base_url:
                continue
            host = rec.base_url.split('//')[-1].split('/')[0].split(':')[0].lower()
            if host in _BLOCKED_HOST_EXACT or any(host.startswith(p) for p in _BLOCKED_HOST_PREFIXES):
                raise ValidationError(
                    _('base_url may not point to a localhost/private/link-local address: %s') % rec.base_url
                )

    def is_available(self):
        """True if this provider can be used right now."""
        self.ensure_one()
        if not self.active:
            return False
        self._cb_maybe_transition()
        if self.circuit_state == 'open':
            return False
        self._quota_maybe_reset()
        if self.daily_quota_used >= self.daily_quota_limit:
            return False
        return True

    @api.model
    def get_available_chain(self, provider_types=None):
        """Ordered recordset of active providers not OPEN/at-quota.

        Enforces the master kill switch (spec "Security & privacy ->
        Master kill switch"): when llm_lead_scoring.allow_third_party_search
        is not 'True' (default False on upgrade/fresh install), only
        provider_type='searxng' (self-hosted) may be returned, regardless
        of what the caller asked for.
        """
        allow_third_party = self.env['ir.config_parameter'].sudo().get_param(
            'llm_lead_scoring.allow_third_party_search', 'False'
        ) == 'True'
        if not allow_third_party:
            provider_types = ['searxng']
        domain = [('active', '=', True)]
        if provider_types:
            domain.append(('provider_type', 'in', provider_types))
        providers = self.search(domain, order='sequence, name')
        return providers.filtered(lambda p: p.is_available())

    # ---- Quota ----
    def _quota_maybe_reset(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.quota_reset_date != today:
            self.sudo().write({'daily_quota_used': 0, 'quota_reset_date': today})

    def _quota_increment(self):
        self.ensure_one()
        self._quota_maybe_reset()
        self.sudo().write({'daily_quota_used': self.daily_quota_used + 1})

    # ---- Circuit breaker ----
    def _cb_maybe_transition(self):
        self.ensure_one()
        if (
            self.circuit_state == 'open'
            and self.circuit_open_until
            and fields.Datetime.now() >= self.circuit_open_until
        ):
            self.sudo().write({'circuit_state': 'half_open'})

    def _cb_record_success(self):
        self.ensure_one()
        self.sudo().write({
            'circuit_state': 'closed',
            'circuit_open_until': False,
            'circuit_backoff_seconds': _DEFAULT_BACKOFF_SECONDS,
            'failure_timestamps': '[]',
        })

    def _cb_record_failure(self):
        self.ensure_one()
        now = fields.Datetime.now()
        if self.circuit_state == 'half_open':
            backoff = min(self.circuit_backoff_seconds * 2, _MAX_BACKOFF_SECONDS)
            self.sudo().write({
                'circuit_state': 'open',
                'circuit_open_until': now + timedelta(seconds=backoff),
                'circuit_backoff_seconds': backoff,
            })
            return
        window_start = now - timedelta(seconds=_FAILURE_WINDOW_SECONDS)
        try:
            raw = json.loads(self.failure_timestamps or '[]')
            timestamps = [fields.Datetime.from_string(t) for t in raw]
        except (ValueError, TypeError):
            timestamps = []
        timestamps = [t for t in timestamps if t >= window_start]
        timestamps.append(now)
        vals = {'failure_timestamps': json.dumps([fields.Datetime.to_string(t) for t in timestamps])}
        if len(timestamps) >= _FAILURE_THRESHOLD:
            vals.update({
                'circuit_state': 'open',
                'circuit_open_until': now + timedelta(seconds=self.circuit_backoff_seconds),
            })
        self.sudo().write(vals)

    def record_call(self, success):
        """Update stats counters + circuit breaker after a call attempt."""
        self.ensure_one()
        vals = {'total_requests': self.total_requests + 1, 'last_used': fields.Datetime.now()}
        if not success:
            vals['failed_requests'] = self.failed_requests + 1
        self.sudo().write(vals)
        if success:
            self._cb_record_success()
        else:
            self._cb_record_failure()
```

- [ ] **Step 4: Register the model import**

Edit `sgc_lead_scoring/models/__init__.py`:

```python
from . import llm_provider
from . import llm_service
from . import web_research_provider
from . import web_research_service
from . import crm_lead
from . import res_config_settings
```

- [ ] **Step 5: Add ACL rows**

Edit `sgc_lead_scoring/security/ir.model.access.csv`, append:

```csv
access_web_research_provider_user,web.research.provider.user,model_web_research_provider,sales_team.group_sale_salesman,1,0,0,0
access_web_research_provider_manager,web.research.provider.manager,model_web_research_provider,sales_team.group_sale_manager,1,1,1,1
```

- [ ] **Step 6: Add multi-company record rule**

Edit `sgc_lead_scoring/security/llm_provider_security.xml`, insert before the closing `</odoo>`:

```xml
    <record id="web_research_provider_comp_rule" model="ir.rule">
        <field name="name">Web Research Provider: multi-company</field>
        <field name="model_id" ref="model_web_research_provider"/>
        <field name="global" eval="True"/>
        <field name="domain_force">['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]</field>
    </record>
```

- [ ] **Step 7: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`:

```python
from . import test_llm_provider
from . import test_llm_service
from . import test_lead_scoring
from . import test_web_research_provider_model
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchProviderModel`
Expected: PASS — 12 tests, 0 failures.

- [ ] **Step 9: Commit**

```bash
git add sgc_lead_scoring/models/web_research_provider.py sgc_lead_scoring/models/__init__.py sgc_lead_scoring/security/ir.model.access.csv sgc_lead_scoring/security/llm_provider_security.xml sgc_lead_scoring/tests/test_web_research_provider_model.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): add web.research.provider with quota + circuit breaker"
```

---

### Task 2: `web.research.result` cache model

**Files:**
- Create: `sgc_lead_scoring/models/web_research_result.py`
- Modify: `sgc_lead_scoring/models/__init__.py`
- Modify: `sgc_lead_scoring/security/ir.model.access.csv`
- Test: `sgc_lead_scoring/tests/test_web_research_result_model.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `web.research.result` model with fields `query_hash (Char, indexed), query_text (Text), results_json (Text), providers_used (Char), created_at (Datetime), expires_at (Datetime)`; model method `get_cached(query_hash) -> recordset|False` (unexpired only), `store(query_hash, query_text, results, providers_used)`, cron-callable `_cron_purge_expired()`.

- [ ] **Step 1: Write the failing tests**

Create `sgc_lead_scoring/tests/test_web_research_result_model.py`:

```python
# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from odoo.fields import Datetime
from odoo.tests.common import TransactionCase


class TestWebResearchResultModel(TransactionCase):

    def test_store_and_get_cached_hit(self):
        Result = self.env['web.research.result']
        Result.store('hash123', 'acme corp profile', [{'title': 'Acme', 'url': 'https://acme.com'}], 'tavily')
        cached = Result.get_cached('hash123')
        self.assertTrue(cached)
        self.assertEqual(json.loads(cached.results_json)[0]['title'], 'Acme')

    def test_get_cached_miss_when_absent(self):
        Result = self.env['web.research.result']
        self.assertFalse(Result.get_cached('does-not-exist'))

    def test_get_cached_miss_when_expired(self):
        Result = self.env['web.research.result']
        Result.store('hash456', 'q', [], 'exa')
        row = Result.search([('query_hash', '=', 'hash456')])
        row.expires_at = Datetime.now() - timedelta(days=1)
        self.assertFalse(Result.get_cached('hash456'))

    def test_cron_purge_expired_removes_only_expired(self):
        Result = self.env['web.research.result']
        Result.store('fresh', 'q', [], 'tavily')
        Result.store('stale', 'q', [], 'tavily')
        stale_row = Result.search([('query_hash', '=', 'stale')])
        stale_row.expires_at = Datetime.now() - timedelta(days=1)
        Result._cron_purge_expired()
        self.assertTrue(Result.search([('query_hash', '=', 'fresh')]))
        self.assertFalse(Result.search([('query_hash', '=', 'stale')]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchResultModel`
Expected: FAIL — `KeyError: 'web.research.result'`.

- [ ] **Step 3: Implement the model**

Create `sgc_lead_scoring/models/web_research_result.py`:

```python
# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from odoo import models, fields, api

_CACHE_TTL_DAYS = 7


class WebResearchResult(models.Model):
    _name = 'web.research.result'
    _description = 'Web Research Cached Result'
    _rec_name = 'query_hash'

    query_hash = fields.Char(required=True, index=True)
    query_text = fields.Text()
    results_json = fields.Text()
    providers_used = fields.Char()
    created_at = fields.Datetime(default=fields.Datetime.now)
    expires_at = fields.Datetime(required=True)

    @api.model
    def get_cached(self, query_hash):
        row = self.search([('query_hash', '=', query_hash)], limit=1, order='created_at desc')
        if not row or row.expires_at < fields.Datetime.now():
            return False
        return row

    @api.model
    def store(self, query_hash, query_text, results, providers_used):
        now = fields.Datetime.now()
        return self.create({
            'query_hash': query_hash,
            'query_text': query_text,
            'results_json': json.dumps(results),
            'providers_used': providers_used,
            'created_at': now,
            'expires_at': now + timedelta(days=_CACHE_TTL_DAYS),
        })

    @api.model
    def _cron_purge_expired(self):
        expired = self.search([('expires_at', '<', fields.Datetime.now())])
        expired.unlink()
        return True
```

- [ ] **Step 4: Register the model import**

Edit `sgc_lead_scoring/models/__init__.py`, add after `web_research_provider`:

```python
from . import web_research_result
```

- [ ] **Step 5: Add ACL row**

Edit `sgc_lead_scoring/security/ir.model.access.csv`, append:

```csv
access_web_research_result_user,web.research.result.user,model_web_research_result,sales_team.group_sale_salesman,1,1,1,0
```

(read/write/create for salesmen so the orchestrator can cache on their behalf; no `unlink` — only the purge cron, running as superuser, deletes rows.)

- [ ] **Step 6: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_web_research_result_model
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchResultModel`
Expected: PASS — 4 tests, 0 failures.

- [ ] **Step 8: Commit**

```bash
git add sgc_lead_scoring/models/web_research_result.py sgc_lead_scoring/models/__init__.py sgc_lead_scoring/security/ir.model.access.csv sgc_lead_scoring/tests/test_web_research_result_model.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): add web.research.result query cache with 7-day TTL"
```

---

### Task 3: `web.research.audit` log model + purge cron

**Files:**
- Create: `sgc_lead_scoring/models/web_research_audit.py`
- Modify: `sgc_lead_scoring/models/__init__.py`
- Modify: `sgc_lead_scoring/security/ir.model.access.csv`
- Modify: `sgc_lead_scoring/data/ir_cron_data.xml`
- Test: `sgc_lead_scoring/tests/test_web_research_audit_model.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: nothing from Tasks 1-2 directly (independent model), but shares the purge-cron pattern with Task 2.
- Produces: `web.research.audit` model with fields `provider_id (Many2one web.research.provider), query_hash (Char), lead_id (Many2one crm.lead), success (Boolean), latency_ms (Integer), result_count (Integer), create_date (Datetime, Odoo default)`; model method `log_call(provider, query_hash, lead, success, latency_ms, result_count)`, cron-callable `_cron_purge_old()`.

- [ ] **Step 1: Write the failing tests**

Create `sgc_lead_scoring/tests/test_web_research_audit_model.py`:

```python
# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo.fields import Datetime
from odoo.tests.common import TransactionCase


class TestWebResearchAuditModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['web.research.provider'].create({
            'name': 'Test Tavily',
            'provider_type': 'tavily',
        })

    def test_log_call_creates_row(self):
        Audit = self.env['web.research.audit']
        row = Audit.log_call(self.provider, 'hash123', False, True, 350, 5)
        self.assertEqual(row.query_hash, 'hash123')
        self.assertTrue(row.success)
        self.assertEqual(row.latency_ms, 350)
        self.assertEqual(row.result_count, 5)

    def test_log_call_never_stores_raw_query(self):
        Audit = self.env['web.research.audit']
        row = Audit.log_call(self.provider, 'hash123', False, True, 100, 1)
        for field_name in row._fields:
            self.assertNotIn('acme corp confidential', str(row[field_name] or ''))

    def test_cron_purge_old_removes_rows_past_90_days(self):
        Audit = self.env['web.research.audit']
        old_row = Audit.log_call(self.provider, 'old-hash', False, True, 100, 1)
        old_row.create_date = Datetime.now() - timedelta(days=91)
        fresh_row = Audit.log_call(self.provider, 'fresh-hash', False, True, 100, 1)
        Audit._cron_purge_old()
        self.assertFalse(old_row.exists())
        self.assertTrue(fresh_row.exists())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchAuditModel`
Expected: FAIL — `KeyError: 'web.research.audit'`.

- [ ] **Step 3: Implement the model**

Create `sgc_lead_scoring/models/web_research_audit.py`:

```python
# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api

_AUDIT_RETENTION_DAYS = 90


class WebResearchAudit(models.Model):
    _name = 'web.research.audit'
    _description = 'Web Research Audit Log'
    _order = 'create_date desc'

    provider_id = fields.Many2one('web.research.provider', required=True, ondelete='cascade')
    query_hash = fields.Char(required=True, index=True)
    lead_id = fields.Many2one('crm.lead', ondelete='set null')
    success = fields.Boolean()
    latency_ms = fields.Integer()
    result_count = fields.Integer()

    @api.model
    def log_call(self, provider, query_hash, lead, success, latency_ms, result_count):
        return self.create({
            'provider_id': provider.id,
            'query_hash': query_hash,
            'lead_id': lead.id if lead else False,
            'success': success,
            'latency_ms': latency_ms,
            'result_count': result_count,
        })

    @api.model
    def _cron_purge_old(self):
        cutoff = fields.Datetime.now() - timedelta(days=_AUDIT_RETENTION_DAYS)
        self.search([('create_date', '<', cutoff)]).unlink()
        return True
```

- [ ] **Step 4: Register the model import**

Edit `sgc_lead_scoring/models/__init__.py`, add after `web_research_result`:

```python
from . import web_research_audit
```

- [ ] **Step 5: Add ACL row**

Edit `sgc_lead_scoring/security/ir.model.access.csv`, append:

```csv
access_web_research_audit_user,web.research.audit.user,model_web_research_audit,sales_team.group_sale_salesman,1,1,1,0
```

- [ ] **Step 6: Add the purge cron**

Edit `sgc_lead_scoring/data/ir_cron_data.xml`, insert a second record inside the existing `<data noupdate="1">` block:

```xml
        <record id="ir_cron_purge_web_research_audit" model="ir.cron">
            <field name="name">Web Research: Purge Audit Log (90 days)</field>
            <field name="model_id" ref="model_web_research_audit"/>
            <field name="state">code</field>
            <field name="code">model._cron_purge_old()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="active" eval="True"/>
        </record>
        <record id="ir_cron_purge_web_research_cache" model="ir.cron">
            <field name="name">Web Research: Purge Expired Cache (7 days)</field>
            <field name="model_id" ref="model_web_research_result"/>
            <field name="state">code</field>
            <field name="code">model._cron_purge_expired()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="active" eval="True"/>
        </record>
```

- [ ] **Step 7: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_web_research_audit_model
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchAuditModel`
Expected: PASS — 3 tests, 0 failures.

- [ ] **Step 9: Commit**

```bash
git add sgc_lead_scoring/models/web_research_audit.py sgc_lead_scoring/models/__init__.py sgc_lead_scoring/security/ir.model.access.csv sgc_lead_scoring/data/ir_cron_data.xml sgc_lead_scoring/tests/test_web_research_audit_model.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): add web.research.audit log with 90-day purge cron"
```

---

### Task 4: Seed data + migration (Phase 1 — Shadow)

**Files:**
- Create: `sgc_lead_scoring/data/web_research_provider_data.xml`
- Create: `sgc_lead_scoring/migrations/19.0.1.6/pre-migrate.py`
- Create: `sgc_lead_scoring/migrations/19.0.1.6/post-migrate.py`
- Modify: `sgc_lead_scoring/__manifest__.py`

**Interfaces:**
- Consumes: `web.research.provider` model from Task 1.
- Produces: on fresh install, 4 inactive seed `web.research.provider` records (tavily, exa, searxng, google-legacy-template); on upgrade from a version with `llm_lead_scoring.google_search_api_key` set, `post-migrate.py` creates+activates one `provider_type='google'` record from those legacy values.

- [ ] **Step 1: Write the seed data**

Create `sgc_lead_scoring/data/web_research_provider_data.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Tavily — primary provider (spec: Tavily-primary chain) -->
        <record id="web_research_provider_tavily" model="web.research.provider">
            <field name="name">Tavily</field>
            <field name="sequence">10</field>
            <field name="provider_type">tavily</field>
            <field name="api_key">your-tavily-api-key-here</field>
            <field name="daily_quota_limit">1000</field>
            <field name="active" eval="False"/>
        </record>

        <!-- Exa — secondary provider -->
        <record id="web_research_provider_exa" model="web.research.provider">
            <field name="name">Exa</field>
            <field name="sequence">20</field>
            <field name="provider_type">exa</field>
            <field name="api_key">your-exa-api-key-here</field>
            <field name="daily_quota_limit">1000</field>
            <field name="active" eval="False"/>
        </record>

        <!-- SearXNG — self-hosted last-resort fallback -->
        <record id="web_research_provider_searxng" model="web.research.provider">
            <field name="name">SearXNG (self-hosted)</field>
            <field name="sequence">30</field>
            <field name="provider_type">searxng</field>
            <field name="base_url">https://searxng.example.internal/search</field>
            <field name="daily_quota_limit">10000</field>
            <field name="active" eval="False"/>
        </record>

        <!-- Google Custom Search — legacy opt-in, lowest priority -->
        <record id="web_research_provider_google" model="web.research.provider">
            <field name="name">Google Custom Search (legacy)</field>
            <field name="sequence">40</field>
            <field name="provider_type">google</field>
            <field name="api_key">your-google-api-key-here</field>
            <field name="search_engine_id">your-google-search-engine-id-here</field>
            <field name="daily_quota_limit">100</field>
            <field name="active" eval="False"/>
        </record>
    </data>
</odoo>
```

- [ ] **Step 2: Write the pre-migrate script**

Create `sgc_lead_scoring/migrations/19.0.1.6/pre-migrate.py`:

```python
# -*- coding: utf-8 -*-
"""Pre-migrate for 19.0.1.6: no schema changes needed before module load
(new models are created by ORM registry sync); this hook exists so
post-migrate has a matching pair and the migration step is documented."""


def migrate(cr, version):
    return
```

- [ ] **Step 3: Write the post-migrate script**

Create `sgc_lead_scoring/migrations/19.0.1.6/post-migrate.py`:

```python
# -*- coding: utf-8 -*-
"""Post-migrate for 19.0.1.6: seed a web.research.provider(type=google)
record from the legacy llm_lead_scoring.google_search_api_key /
..._google_search_engine_id config params, if they were set, so upgraded
installs keep working without re-entering credentials."""

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    config = env['ir.config_parameter'].sudo()
    api_key = config.get_param('llm_lead_scoring.google_search_api_key')
    engine_id = config.get_param('llm_lead_scoring.google_search_engine_id')
    if not api_key or not engine_id:
        return
    Provider = env['web.research.provider'].sudo()
    existing = Provider.search([('provider_type', '=', 'google'), ('api_key', '=', api_key)], limit=1)
    if existing:
        return
    Provider.create({
        'name': 'Google Custom Search (migrated)',
        'sequence': 40,
        'provider_type': 'google',
        'api_key': api_key,
        'search_engine_id': engine_id,
        'daily_quota_limit': 100,
        'active': True,
    })
```

- [ ] **Step 4: Bump the manifest version and register data files**

Edit `sgc_lead_scoring/__manifest__.py`:

```python
    "version": "19.0.1.6",
```

and in `"data"`, insert after `"data/llm_provider_data.xml",`:

```python
        "data/web_research_provider_data.xml",
```

- [ ] **Step 4a: Note the interaction with the master kill switch**

`web.research.provider.get_available_chain()` (Task 1) restricts the chain to `searxng` only while `llm_lead_scoring.allow_third_party_search` is `False` — which is the default on both fresh installs and upgrades. This is intentional per spec ("Master kill switch... default False on upgrade"): a migrated Google provider record (created by `post-migrate.py` above) exists and is `active=True`, but won't actually be selected by `search()`/`multi_search()` until an admin flips the kill switch on in Settings (Task 9). This preserves the letter of "backward compatible" (the record and the `search_google_custom()` method both keep working when explicitly invoked) while honoring the spec's intent of not silently continuing to leak data to Google after upgrade. No code change needed for this step — it's a consequence of Task 1 + this task's migration running together, documented here so it isn't mistaken for a bug during Task 4's own verification.

- [ ] **Step 5: Verify install/upgrade on `sgc_theme_dev`**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev -u sgc_lead_scoring --stop-after-init`
Expected: exits 0, no traceback. Then verify seed rows landed:

Run: `docker exec odoo-db-1 psql -U odoo -d sgc_theme_dev -c "select name, provider_type, active from web_research_provider order by sequence;"`
Expected: 4 rows (tavily, exa, searxng, google), all `active=f` on a fresh install (no legacy config params set yet in this dev DB).

- [ ] **Step 6: Commit**

```bash
git add sgc_lead_scoring/data/web_research_provider_data.xml sgc_lead_scoring/migrations sgc_lead_scoring/__manifest__.py
git commit -m "feat(web-research): seed provider chain + migrate legacy Google config on upgrade"
```

---

### Task 5: Orchestrator core — `search()`, query hashing, cache, anonymizer

**Files:**
- Modify: `sgc_lead_scoring/models/web_research_service.py` (full rewrite of the file)
- Test: `sgc_lead_scoring/tests/test_web_research_orchestrator.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: `web.research.provider.get_available_chain()` (Task 1), `web.research.result.get_cached()` / `.store()` (Task 2), `web.research.audit.log_call()` (Task 3).
- Produces: `web.research.service` model methods `hash_query(query: str) -> str` (SHA-256 hex digest), `anonymize_lead_id(lead_id: int) -> str` (SHA-256 hex digest), `search(query: str, num_results=5, providers=None) -> dict` returning `{success, results, providers_used, cache_hit, latency_ms, reason?}`. `multi_search()` and per-provider client calls are added in Task 6/7 — this task's `search()` only needs a single-provider path (first available provider in the chain) so the cache/hash/audit plumbing can be tested in isolation.

- [ ] **Step 1: Write the failing tests**

Create `sgc_lead_scoring/tests/test_web_research_orchestrator.py`:

```python
# -*- coding: utf-8 -*-
import hashlib
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestWebResearchOrchestratorCore(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['web.research.provider'].search([]).unlink()
        self.provider = self.env['web.research.provider'].create({
            'name': 'Test Tavily',
            'provider_type': 'tavily',
            'api_key': 'test-key',
            'active': True,
        })
        self.service = self.env['web.research.service']

    def test_hash_query_is_deterministic(self):
        h1 = self.service.hash_query('acme corp company profile')
        h2 = self.service.hash_query('acme corp company profile')
        self.assertEqual(h1, h2)
        self.assertEqual(h1, hashlib.sha256(b'acme corp company profile').hexdigest())

    def test_hash_query_differs_for_different_queries(self):
        h1 = self.service.hash_query('acme corp')
        h2 = self.service.hash_query('beta inc')
        self.assertNotEqual(h1, h2)

    def test_anonymize_lead_id_is_deterministic_sha256(self):
        a1 = self.service.anonymize_lead_id(42)
        a2 = self.service.anonymize_lead_id(42)
        self.assertEqual(a1, a2)
        self.assertEqual(a1, hashlib.sha256(b'42').hexdigest())

    @patch.object(type(None), '__nonzero__', create=True)  # placeholder, replaced below
    def test_search_cache_hit_skips_provider_call(self):
        pass

    def test_search_cache_hit_skips_provider_call_real(self):
        query = 'acme corp company profile'
        query_hash = self.service.hash_query(query)
        self.env['web.research.result'].store(
            query_hash, query, [{'title': 'Cached', 'url': 'https://acme.com'}], 'tavily'
        )
        with patch('requests.get') as mock_get:
            result = self.service.search(query)
        mock_get.assert_not_called()
        self.assertTrue(result['success'])
        self.assertTrue(result['cache_hit'])
        self.assertEqual(result['results'][0]['title'], 'Cached')

    def test_search_no_available_provider_returns_failure(self):
        self.provider.active = False
        result = self.service.search('some uncached query xyz')
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'], 'all_providers_unavailable')

    def test_search_writes_audit_row_with_hash_not_raw_query(self):
        self.provider.active = False  # force the no-provider path, still audits nothing here
        query = 'super secret company name'
        self.service.search(query)
        # No provider was called, so no audit row for this query — assert none leaked the raw text
        audits = self.env['web.research.audit'].search([])
        for row in audits:
            self.assertNotEqual(row.query_hash, query)
```

Remove the placeholder `test_search_cache_hit_skips_provider_call` stub method before running — it exists only to flag that Step 1 code must not ship a no-op test; the real test is `test_search_cache_hit_skips_provider_call_real`. Delete the stub in this same step so no placeholder test lands in the file:

```python
# Delete these lines from the class body before saving the file:
#     @patch.object(type(None), '__nonzero__', create=True)
#     def test_search_cache_hit_skips_provider_call(self):
#         pass
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchOrchestratorCore`
Expected: FAIL — `AttributeError: 'web.research.service' object has no attribute 'hash_query'`.

- [ ] **Step 3: Rewrite the orchestrator**

Before overwriting, open the current `sgc_lead_scoring/models/web_research_service.py` and confirm its class line reads `class WebResearchService(models.Model):` with `_name = 'web.research.service'` (this is expected, matching the pre-existing `access_web_research_service_user` ACL row in `security/ir.model.access.csv`, which implies a concrete `models.Model`, not `TransientModel`/`AbstractModel`). If it differs, keep whatever base class is already there instead of the `models.Model` used below — this task changes the model's *methods*, not its base class.

Replace the full contents of `sgc_lead_scoring/models/web_research_service.py`:

```python
# -*- coding: utf-8 -*-
import hashlib
import logging
import time

from odoo import models, api

_logger = logging.getLogger(__name__)

_DEFAULT_NUM_RESULTS = 5


class WebResearchService(models.Model):
    _name = 'web.research.service'
    _description = 'Web Research Orchestrator'

    @api.model
    def hash_query(self, query):
        return hashlib.sha256(query.encode('utf-8')).hexdigest()

    @api.model
    def anonymize_lead_id(self, lead_id):
        return hashlib.sha256(str(lead_id).encode('utf-8')).hexdigest()

    @api.model
    def search(self, query, num_results=_DEFAULT_NUM_RESULTS, providers=None):
        """Single-query search. Provider fan-out is added by multi_search();
        this path uses the first available provider in the chain."""
        query_hash = self.hash_query(query)
        cached = self.env['web.research.result'].get_cached(query_hash)
        if cached:
            import json
            return {
                'success': True,
                'results': json.loads(cached.results_json),
                'providers_used': cached.providers_used.split(',') if cached.providers_used else [],
                'cache_hit': True,
                'latency_ms': 0,
            }

        chain = self.env['web.research.provider'].get_available_chain(provider_types=providers)
        if not chain:
            _logger.info('web.research.service: no available provider for query_hash=%s', query_hash)
            return {
                'success': False,
                'results': [],
                'providers_used': [],
                'cache_hit': False,
                'latency_ms': 0,
                'reason': 'all_providers_unavailable',
            }

        provider = chain[0]
        start = time.monotonic()
        results, success = self._call_provider(provider, query, num_results)
        latency_ms = int((time.monotonic() - start) * 1000)

        provider.record_call(success)
        self.env['web.research.audit'].log_call(provider, query_hash, None, success, latency_ms, len(results))

        if success:
            self.env['web.research.result'].store(query_hash, query, results, provider.provider_type)

        return {
            'success': success,
            'results': results,
            'providers_used': [provider.provider_type] if success else [],
            'cache_hit': False,
            'latency_ms': latency_ms,
            'reason': None if success else 'provider_call_failed',
        }

    def _call_provider(self, provider, query, num_results):
        """Dispatch to the per-provider client. Implemented in Task 6."""
        raise NotImplementedError('Provider client dispatch is added in Task 6.')
```

- [ ] **Step 4: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_web_research_orchestrator
```

- [ ] **Step 5: Run the tests that don't need `_call_provider` and verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchOrchestratorCore`
Expected: PASS on `test_hash_query_is_deterministic`, `test_hash_query_differs_for_different_queries`, `test_anonymize_lead_id_is_deterministic_sha256`, `test_search_cache_hit_skips_provider_call_real`, `test_search_no_available_provider_returns_failure`, `test_search_writes_audit_row_with_hash_not_raw_query` — 6 tests, 0 failures. (These 6 exercise only the cache-hit and no-provider paths, which don't call `_call_provider`.)

- [ ] **Step 6: Commit**

```bash
git add sgc_lead_scoring/models/web_research_service.py sgc_lead_scoring/tests/test_web_research_orchestrator.py sgc_lead_scoring/tests/__init__.py
git commit -m "refactor(web-research): rewrite web.research.service as orchestrator core (hash/cache/audit)"
```

---

### Task 6: Provider client dispatch (Tavily/Exa/SearXNG/Google compat)

**Files:**
- Modify: `sgc_lead_scoring/models/web_research_service.py`
- Modify: `sgc_lead_scoring/wizards/google_search_setup_wizard.py` (compat call site only — see Step 5)
- Create: `sgc_lead_scoring/tests/test_provider_clients.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: `web.research.provider` records (Task 1), `_call_provider(provider, query, num_results)` stub from Task 5.
- Produces: `_call_provider()` implemented (dispatches on `provider.provider_type`); `_call_tavily`, `_call_exa`, `_call_searxng`, `search_google_custom(query, num_results=5)` (kept as the exact pre-existing method signature for backward compatibility, now delegating to `search(query, num_results, providers=['google'])`).

- [ ] **Step 1: Write the failing tests**

Create `sgc_lead_scoring/tests/test_provider_clients.py`:

```python
# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase


class TestProviderClients(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['web.research.provider'].search([]).unlink()
        # These tests exercise Tavily/Exa/Google directly; opt in past the
        # master kill switch (Task 1) so get_available_chain() doesn't
        # silently restrict the chain to searxng-only.
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.allow_third_party_search', 'True')
        self.service = self.env['web.research.service']

    def _mock_response(self, status_code, json_data, headers=None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = headers or {}
        return resp

    @patch('requests.post')
    def test_tavily_200_returns_results(self, mock_post):
        provider = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(200, {
            'results': [{'title': 'Acme', 'url': 'https://acme.com', 'content': 'snippet'}]
        })
        result = self.service.search('acme corp', providers=['tavily'])
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Acme')
        self.assertEqual(provider.total_requests, 1)
        self.assertEqual(provider.failed_requests, 0)

    @patch('requests.post')
    def test_tavily_429_marks_failure_no_crash(self, mock_post):
        provider = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(429, {}, headers={'Retry-After': '30'})
        result = self.service.search('acme corp', providers=['tavily'])
        self.assertFalse(result['success'])
        self.assertEqual(provider.failed_requests, 1)

    @patch('requests.post')
    def test_tavily_500_marks_failure(self, mock_post):
        provider = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(500, {})
        result = self.service.search('acme corp', providers=['tavily'])
        self.assertFalse(result['success'])
        self.assertEqual(provider.failed_requests, 1)

    @patch('requests.post')
    def test_exa_200_returns_results(self, mock_post):
        self.env['web.research.provider'].create({
            'name': 'Exa', 'provider_type': 'exa', 'api_key': 'k', 'active': True,
        })
        mock_post.return_value = self._mock_response(200, {
            'results': [{'title': 'Beta Inc', 'url': 'https://beta.com', 'text': 'snippet'}]
        })
        result = self.service.search('beta inc', providers=['exa'])
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Beta Inc')

    @patch('requests.get')
    def test_searxng_200_returns_results(self, mock_get):
        self.env['web.research.provider'].create({
            'name': 'SearXNG', 'provider_type': 'searxng',
            'base_url': 'https://searxng.example.com/search', 'active': True,
        })
        mock_get.return_value = self._mock_response(200, {
            'results': [{'title': 'Gamma LLC', 'url': 'https://gamma.com', 'content': 'snippet'}]
        })
        result = self.service.search('gamma llc', providers=['searxng'])
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Gamma LLC')

    @patch('requests.get')
    def test_google_401_marks_failure(self, mock_get):
        self.env['web.research.provider'].create({
            'name': 'Google', 'provider_type': 'google', 'api_key': 'bad-key',
            'search_engine_id': 'eid', 'active': True,
        })
        mock_get.return_value = self._mock_response(401, {})
        result = self.service.search('delta corp', providers=['google'])
        self.assertFalse(result['success'])

    @patch('requests.get')
    def test_search_google_custom_compat_shim(self, mock_get):
        self.env['web.research.provider'].create({
            'name': 'Google', 'provider_type': 'google', 'api_key': 'k',
            'search_engine_id': 'eid', 'active': True,
        })
        mock_get.return_value = self._mock_response(200, {
            'items': [{'title': 'Epsilon', 'link': 'https://epsilon.com', 'snippet': 'snippet'}]
        })
        result = self.service.search_google_custom('epsilon corp', num_results=3)
        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['title'], 'Epsilon')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestProviderClients`
Expected: FAIL — `NotImplementedError: Provider client dispatch is added in Task 6.`

- [ ] **Step 3: Implement provider clients**

In `sgc_lead_scoring/models/web_research_service.py`, add `import requests` to the top imports, and replace the `_call_provider` stub and add the client methods + `search_google_custom`:

```python
    def _call_provider(self, provider, query, num_results):
        dispatch = {
            'tavily': self._call_tavily,
            'exa': self._call_exa,
            'searxng': self._call_searxng,
            'google': self._call_google,
        }
        handler = dispatch.get(provider.provider_type)
        if not handler:
            _logger.warning('web.research.service: unknown provider_type %s', provider.provider_type)
            return [], False
        try:
            return handler(provider, query, num_results)
        except requests.RequestException as exc:
            _logger.warning('web.research.service: %s request failed: %s', provider.provider_type, exc)
            return [], False

    def _call_tavily(self, provider, query, num_results):
        resp = requests.post(
            'https://api.tavily.com/search',
            json={'api_key': provider.api_key, 'query': query, 'max_results': num_results},
            timeout=15,
        )
        if resp.status_code != 200:
            return [], False
        data = resp.json()
        results = [
            {'title': r.get('title'), 'url': r.get('url'), 'snippet': r.get('content')}
            for r in data.get('results', [])[:num_results]
        ]
        return results, True

    def _call_exa(self, provider, query, num_results):
        resp = requests.post(
            'https://api.exa.ai/search',
            json={'query': query, 'numResults': num_results},
            headers={'x-api-key': provider.api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            return [], False
        data = resp.json()
        results = [
            {'title': r.get('title'), 'url': r.get('url'), 'snippet': r.get('text')}
            for r in data.get('results', [])[:num_results]
        ]
        return results, True

    def _call_searxng(self, provider, query, num_results):
        resp = requests.get(
            provider.base_url,
            params={'q': query, 'format': 'json'},
            timeout=15,
        )
        if resp.status_code != 200:
            return [], False
        data = resp.json()
        results = [
            {'title': r.get('title'), 'url': r.get('url'), 'snippet': r.get('content')}
            for r in data.get('results', [])[:num_results]
        ]
        return results, True

    def _call_google(self, provider, query, num_results):
        resp = requests.get(
            'https://www.googleapis.com/customsearch/v1',
            params={
                'key': provider.api_key,
                'cx': provider.search_engine_id,
                'q': query,
                'num': min(num_results, 10),
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return [], False
        data = resp.json()
        results = [
            {'title': r.get('title'), 'url': r.get('link'), 'snippet': r.get('snippet')}
            for r in data.get('items', [])[:num_results]
        ]
        return results, True

    @api.model
    def search_google_custom(self, query, num_results=_DEFAULT_NUM_RESULTS):
        """Backward-compat shim: pre-redesign callers (google.search.setup.wizard)
        keep this exact signature; it now delegates to the orchestrator restricted
        to the google provider type."""
        return self.search(query, num_results=num_results, providers=['google'])
```

- [ ] **Step 4: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_provider_clients
```

- [ ] **Step 5: Verify the wizard compat call site still matches**

Read `sgc_lead_scoring/wizards/google_search_setup_wizard.py` line 89 — it already calls `self.env['web.research.service'].search_google_custom(self.test_query, num_results=3)` with a keyword `num_results=`. No change needed; this step is a verification-only check, not an edit.

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestProviderClients`
Expected: PASS — 7 tests, 0 failures.

- [ ] **Step 6: Run the full orchestrator suite together**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchOrchestratorCore,/sgc_lead_scoring:TestProviderClients`
Expected: PASS — 13 tests, 0 failures (Task 5's 6 + this task's 7).

- [ ] **Step 7: Commit**

```bash
git add sgc_lead_scoring/models/web_research_service.py sgc_lead_scoring/tests/test_provider_clients.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): implement Tavily/Exa/SearXNG/Google provider clients + compat shim"
```

---

### Task 7: `multi_search()` parallel fan-out + domain dedup

**Files:**
- Modify: `sgc_lead_scoring/models/web_research_service.py`
- Modify: `sgc_lead_scoring/tests/test_web_research_orchestrator.py`

**Interfaces:**
- Consumes: `_call_provider()` (Task 6), `get_available_chain()` (Task 1).
- Produces: `multi_search(queries: list[str], parallel=True, num_results=5, min_results=3, providers=None) -> dict` returning `{success, results, providers_used, cache_hits, latency_ms}` where `results` is deduped by domain (extracted from URL) with a `sources` list per result.

- [ ] **Step 1: Write the failing tests**

Append to `sgc_lead_scoring/tests/test_web_research_orchestrator.py`, new class:

```python
class TestWebResearchOrchestratorMultiSearch(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['web.research.provider'].search([]).unlink()
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.allow_third_party_search', 'True')
        self.tavily = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k', 'sequence': 10, 'active': True,
        })
        self.exa = self.env['web.research.provider'].create({
            'name': 'Exa', 'provider_type': 'exa', 'api_key': 'k', 'sequence': 20, 'active': True,
        })
        self.service = self.env['web.research.service']

    def _tavily_response(self, *_a, **_k):
        from unittest.mock import MagicMock
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            'results': [
                {'title': 'Acme', 'url': 'https://acme.com/about', 'content': 'from tavily'},
                {'title': 'Acme News', 'url': 'https://news.acme.com/2026', 'content': 'from tavily'},
            ]
        }
        return resp

    def _exa_response(self, *_a, **_k):
        from unittest.mock import MagicMock
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            'results': [
                {'title': 'Acme (dup)', 'url': 'https://acme.com/duplicate-path', 'text': 'from exa'},
                {'title': 'Acme Products', 'url': 'https://acme.com/products', 'text': 'from exa'},
            ]
        }
        return resp

    def test_multi_search_dedupes_by_domain_and_merges_sources(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = lambda url, **kw: (
                self._tavily_response() if 'tavily' in url else self._exa_response()
            )
            result = self.service.multi_search(['acme corp'], parallel=True, min_results=1)
        self.assertTrue(result['success'])
        domains = [r['url'].split('/')[2] for r in result['results']]
        self.assertEqual(len(domains), len(set(['acme.com', 'news.acme.com'])) + 0)
        acme_com_result = next(r for r in result['results'] if 'acme.com/about' in r['url'] or 'acme.com/duplicate-path' in r['url'] or 'acme.com/products' in r['url'])
        self.assertGreaterEqual(len(acme_com_result['sources']), 1)

    def test_multi_search_sequential_when_parallel_false(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = lambda url, **kw: (
                self._tavily_response() if 'tavily' in url else self._exa_response()
            )
            result = self.service.multi_search(['acme corp'], parallel=False, min_results=1)
        self.assertTrue(result['success'])
        self.assertIn('tavily', result['providers_used'])

    def test_multi_search_multiple_queries_merged(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = lambda url, **kw: (
                self._tavily_response() if 'tavily' in url else self._exa_response()
            )
            result = self.service.multi_search(
                ['acme corp profile', 'acme corp news 2026'], parallel=True, min_results=1
            )
        self.assertTrue(result['success'])
        self.assertGreater(len(result['results']), 0)

    def test_multi_search_reports_cache_hits(self):
        query = 'acme corp profile'
        query_hash = self.service.hash_query(query)
        self.env['web.research.result'].store(
            query_hash, query, [{'title': 'Cached Acme', 'url': 'https://acme.com'}], 'tavily'
        )
        with patch('requests.post') as mock_post:
            mock_post.side_effect = lambda url, **kw: self._exa_response()
            result = self.service.multi_search([query], parallel=True, min_results=1)
        self.assertGreaterEqual(result['cache_hits'], 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchOrchestratorMultiSearch`
Expected: FAIL — `AttributeError: 'web.research.service' object has no attribute 'multi_search'`.

- [ ] **Step 3: Implement `multi_search`**

In `sgc_lead_scoring/models/web_research_service.py`, add `from concurrent.futures import ThreadPoolExecutor` to imports and add this method (place after `search`):

```python
    @api.model
    def multi_search(self, queries, parallel=True, num_results=_DEFAULT_NUM_RESULTS, min_results=3, providers=None):
        cache_hits = 0
        providers_used = set()
        all_raw_results = []

        if parallel:
            with ThreadPoolExecutor(max_workers=min(len(queries), 5) or 1) as executor:
                futures = [executor.submit(self.search, q, num_results, providers) for q in queries]
                per_query_results = [f.result() for f in futures]
        else:
            per_query_results = [self.search(q, num_results, providers) for q in queries]

        for res in per_query_results:
            if res.get('cache_hit'):
                cache_hits += 1
            providers_used.update(res.get('providers_used', []))
            all_raw_results.extend(res.get('results', []))

        merged = self._dedupe_by_domain(all_raw_results)

        if len(merged) < min_results:
            _logger.info(
                'web.research.service.multi_search: only %d results (< min_results=%d)',
                len(merged), min_results,
            )

        return {
            'success': bool(merged) or any(r['success'] for r in per_query_results),
            'results': merged,
            'providers_used': sorted(providers_used),
            'cache_hits': cache_hits,
            'latency_ms': sum(r.get('latency_ms', 0) for r in per_query_results),
        }

    def _dedupe_by_domain(self, results):
        by_domain = {}
        for r in results:
            url = r.get('url') or ''
            domain = url.split('//')[-1].split('/')[0].lower()
            if not domain:
                continue
            if domain not in by_domain:
                merged = dict(r)
                merged['sources'] = [r.get('_provider', 'unknown')]
                by_domain[domain] = merged
            else:
                by_domain[domain]['sources'].append(r.get('_provider', 'unknown'))
        return list(by_domain.values())
```

Also tag each result with its originating provider so `_dedupe_by_domain` can populate `sources` meaningfully — edit `search()`'s success branch to stamp results before returning:

```python
        if success:
            for r in results:
                r['_provider'] = provider.provider_type
            self.env['web.research.result'].store(query_hash, query, results, provider.provider_type)
```

(This replaces the single-line `self.env['web.research.result'].store(...)` call added in Task 5 Step 3 — same call, now preceded by the tagging loop.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchOrchestratorMultiSearch`
Expected: PASS — 4 tests, 0 failures.

- [ ] **Step 5: Run the full orchestrator + provider-client suite together**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchOrchestratorCore,/sgc_lead_scoring:TestProviderClients,/sgc_lead_scoring:TestWebResearchOrchestratorMultiSearch`
Expected: PASS — 17 tests, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add sgc_lead_scoring/models/web_research_service.py sgc_lead_scoring/tests/test_web_research_orchestrator.py
git commit -m "feat(web-research): add multi_search parallel fan-out with domain dedup"
```

---

### Task 8: Error handling matrix (429 Retry-After, 401/403 disable, min_results retry)

**Files:**
- Modify: `sgc_lead_scoring/models/web_research_service.py`
- Modify: `sgc_lead_scoring/tests/test_provider_clients.py`
- Modify: `sgc_lead_scoring/tests/test_web_research_orchestrator.py`

**Interfaces:**
- Consumes: `_call_tavily`/`_call_exa`/`_call_searxng`/`_call_google` (Task 6), `provider.record_call()` (Task 1).
- Produces: `_call_provider` now reads `Retry-After` on 429 and marks the provider at-quota for the day (`daily_quota_used = daily_quota_limit`); on 401/403 it deactivates the provider (`active = False`) and posts a `mail.activity` to `base.group_system` users; `multi_search` retries once with a relaxed query (drop tokens after the first 3 words) when merged results are still below `min_results` after the first pass.

- [ ] **Step 1: Write the failing tests**

Append to `sgc_lead_scoring/tests/test_provider_clients.py`:

```python
class TestProviderErrorHandling(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['web.research.provider'].search([]).unlink()
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.allow_third_party_search', 'True')
        self.service = self.env['web.research.service']

    def _mock_response(self, status_code, json_data, headers=None):
        from unittest.mock import MagicMock
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = headers or {}
        return resp

    @patch('requests.post')
    def test_429_marks_provider_at_quota_for_today(self, mock_post):
        provider = self.env['web.research.provider'].create({
            'name': 'Tavily', 'provider_type': 'tavily', 'api_key': 'k',
            'daily_quota_limit': 1000, 'active': True,
        })
        mock_post.return_value = self._mock_response(429, {}, headers={'Retry-After': '30'})
        self.service.search('acme corp', providers=['tavily'])
        self.assertGreaterEqual(provider.daily_quota_used, provider.daily_quota_limit)
        self.assertFalse(provider.is_available())

    @patch('requests.get')
    def test_401_deactivates_provider_and_notifies_admin(self, mock_get):
        provider = self.env['web.research.provider'].create({
            'name': 'Google', 'provider_type': 'google', 'api_key': 'bad',
            'search_engine_id': 'eid', 'active': True,
        })
        mock_get.return_value = self._mock_response(401, {})
        self.service.search('acme corp', providers=['google'])
        self.assertFalse(provider.active)
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'web.research.provider'), ('res_id', '=', provider.id),
        ])
        self.assertTrue(activities)
```

Append to `sgc_lead_scoring/tests/test_web_research_orchestrator.py`, inside `TestWebResearchOrchestratorMultiSearch`:

```python
    def test_multi_search_retries_with_relaxed_query_below_min_results(self):
        from unittest.mock import MagicMock

        def empty_then_full(url, **kw):
            payload = kw.get('json', {})
            query = payload.get('query', '')
            resp = MagicMock()
            resp.status_code = 200
            if len(query.split()) > 3:
                resp.json.return_value = {'results': []}
            else:
                resp.json.return_value = {
                    'results': [{'title': 'Acme', 'url': 'https://acme.com', 'content': 'x'}]
                }
            return resp

        with patch('requests.post', side_effect=empty_then_full):
            result = self.service.multi_search(
                ['acme corp exact restrictive phrase match'], parallel=False, min_results=1
            )
        self.assertGreaterEqual(len(result['results']), 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestProviderErrorHandling`
Expected: FAIL — `test_429_marks_provider_at_quota_for_today` and `test_401_deactivates_provider_and_notifies_admin` fail because current code only calls `provider.record_call(success)`, which doesn't touch quota/active/activity.

- [ ] **Step 3: Implement error-status handling**

In `sgc_lead_scoring/models/web_research_service.py`, replace `_call_provider` with a version that inspects the raw response status for 429/401/403 before falling into the per-client parser. Refactor each `_call_*` method to return `(results, success, status_code)` instead of `(results, success)`, and update `_call_provider`:

```python
    def _call_provider(self, provider, query, num_results):
        dispatch = {
            'tavily': self._call_tavily,
            'exa': self._call_exa,
            'searxng': self._call_searxng,
            'google': self._call_google,
        }
        handler = dispatch.get(provider.provider_type)
        if not handler:
            _logger.warning('web.research.service: unknown provider_type %s', provider.provider_type)
            return [], False
        try:
            results, success, status_code = handler(provider, query, num_results)
        except requests.RequestException as exc:
            _logger.warning('web.research.service: %s request failed: %s', provider.provider_type, exc)
            return [], False

        if status_code == 429:
            provider.sudo().write({'daily_quota_used': provider.daily_quota_limit})
        elif status_code in (401, 403):
            self._disable_provider_and_notify(provider)
        return results, success

    def _disable_provider_and_notify(self, provider):
        provider.sudo().write({'active': False})
        admins = self.env['res.users'].sudo().search([('groups_id', '=', self.env.ref('base.group_system').id)])
        for admin in admins:
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env['ir.model']._get_id('web.research.provider'),
                'res_id': provider.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': 'Web research provider disabled: authentication failed',
                'note': 'Provider "%s" returned 401/403 and was disabled. Update its credentials.' % provider.name,
                'user_id': admin.id,
            })
```

Update each client method's return statements to include the status code, e.g. `_call_tavily`:

```python
    def _call_tavily(self, provider, query, num_results):
        resp = requests.post(
            'https://api.tavily.com/search',
            json={'api_key': provider.api_key, 'query': query, 'max_results': num_results},
            timeout=15,
        )
        if resp.status_code != 200:
            return [], False, resp.status_code
        data = resp.json()
        results = [
            {'title': r.get('title'), 'url': r.get('url'), 'snippet': r.get('content')}
            for r in data.get('results', [])[:num_results]
        ]
        return results, True, resp.status_code
```

Apply the same `, resp.status_code` addition to both `return` statements in `_call_exa`, `_call_searxng`, and `_call_google`.

- [ ] **Step 4: Implement min_results retry with relaxed query**

In `multi_search`, after computing `merged`, add the retry-once branch:

```python
        if len(merged) < min_results:
            relaxed_queries = [' '.join(q.split()[:3]) for q in queries]
            if parallel:
                with ThreadPoolExecutor(max_workers=min(len(relaxed_queries), 5) or 1) as executor:
                    futures = [executor.submit(self.search, q, num_results, providers) for q in relaxed_queries]
                    retry_results = [f.result() for f in futures]
            else:
                retry_results = [self.search(q, num_results, providers) for q in relaxed_queries]
            for res in retry_results:
                if res.get('cache_hit'):
                    cache_hits += 1
                providers_used.update(res.get('providers_used', []))
                all_raw_results.extend(res.get('results', []))
            merged = self._dedupe_by_domain(all_raw_results)
            _logger.info(
                'web.research.service.multi_search: relaxed-query retry produced %d results',
                len(merged),
            )
```

Place this block right before the final `return` statement in `multi_search`, after the original `if len(merged) < min_results:` logging block from Task 7 Step 3 (replace that logging-only block with this one — it now both logs and retries).

- [ ] **Step 5: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestProviderErrorHandling`
Expected: PASS — 2 tests, 0 failures.

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchOrchestratorMultiSearch`
Expected: PASS — 5 tests, 0 failures (4 from Task 7 + this task's retry test).

- [ ] **Step 6: Run the entire web-research test surface together**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestWebResearchProviderModel,/sgc_lead_scoring:TestWebResearchResultModel,/sgc_lead_scoring:TestWebResearchAuditModel,/sgc_lead_scoring:TestWebResearchOrchestratorCore,/sgc_lead_scoring:TestProviderClients,/sgc_lead_scoring:TestProviderErrorHandling,/sgc_lead_scoring:TestWebResearchOrchestratorMultiSearch`
Expected: PASS — 39 tests total, 0 failures. This closes out Phase 1 (Shadow) — `crm.lead._enrich_lead()` still hasn't been touched, so nothing user-facing has changed yet.

- [ ] **Step 7: Commit**

```bash
git add sgc_lead_scoring/models/web_research_service.py sgc_lead_scoring/tests/test_provider_clients.py sgc_lead_scoring/tests/test_web_research_orchestrator.py
git commit -m "feat(web-research): implement 429/401/403 handling and min_results relaxed-query retry"
```

---

### Task 9: `res.config.settings` — kill switch, anonymize toggle, provider table (Phase 2 — Opt-in)

**Files:**
- Modify: `sgc_lead_scoring/models/res_config_settings.py`
- Modify: `sgc_lead_scoring/views/res_config_settings_views.xml`
- Create: `sgc_lead_scoring/views/web_research_provider_views.xml`
- Modify: `sgc_lead_scoring/__manifest__.py`

**Interfaces:**
- Consumes: `web.research.provider` model (Task 1).
- Produces: `res.config.settings` fields `allow_third_party_search (Boolean, default False)`, `anonymize_company_names (Boolean, default False)`; a menu action + list/form view for `web.research.provider` so admins can add/edit provider rows and their `api_key`/`base_url`/quota directly. Both fields are `config_parameter`-backed, so `allow_third_party_search` is already enforced by `get_available_chain()` (added in Task 1) the moment this task's UI lets an admin toggle it — this task adds no new enforcement logic, only the UI binding. `anonymize_company_names` is UI-only until Task 12 wires it into `crm.lead._enrich_lead()`.

- [ ] **Step 1: Add settings fields**

Edit `sgc_lead_scoring/models/res_config_settings.py` — add these two fields near the existing `enable_web_research` field (read the file's existing field block first to match indentation/style), using the same `ir.config_parameter` pattern already used by `enable_web_research`:

```python
    allow_third_party_search = fields.Boolean(
        string='Allow Third-Party Web Search',
        config_parameter='llm_lead_scoring.allow_third_party_search',
        default=False,
        help='Master kill switch. When off, only the self-hosted SearXNG provider may run.',
    )
    anonymize_company_names = fields.Boolean(
        string='Anonymize Company Names in Research Queries',
        config_parameter='llm_lead_scoring.anonymize_company_names',
        default=False,
        help='Hash company name before sending to any third-party provider; results are re-associated locally.',
    )
```

- [ ] **Step 2: Create the provider list/form view**

Create `sgc_lead_scoring/views/web_research_provider_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_web_research_provider_list" model="ir.ui.view">
        <field name="name">web.research.provider.list</field>
        <field name="model">web.research.provider</field>
        <field name="arch" type="xml">
            <list string="Web Research Providers">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="provider_type"/>
                <field name="active" widget="boolean_toggle"/>
                <field name="circuit_state"/>
                <field name="daily_quota_used"/>
                <field name="daily_quota_limit"/>
            </list>
        </field>
    </record>

    <record id="view_web_research_provider_form" model="ir.ui.view">
        <field name="name">web.research.provider.form</field>
        <field name="model">web.research.provider</field>
        <field name="arch" type="xml">
            <form string="Web Research Provider">
                <sheet>
                    <group>
                        <group>
                            <field name="name"/>
                            <field name="provider_type"/>
                            <field name="sequence"/>
                            <field name="active"/>
                        </group>
                        <group>
                            <field name="api_key" password="True" groups="base.group_system"/>
                            <field name="search_engine_id" groups="base.group_system"
                                   invisible="provider_type != 'google'"/>
                            <field name="base_url" invisible="provider_type != 'searxng'"/>
                        </group>
                    </group>
                    <group string="Quota">
                        <field name="daily_quota_limit"/>
                        <field name="daily_quota_used" readonly="1"/>
                        <field name="quota_reset_date" readonly="1"/>
                    </group>
                    <group string="Circuit Breaker">
                        <field name="circuit_state" readonly="1"/>
                        <field name="circuit_open_until" readonly="1"/>
                        <field name="total_requests" readonly="1"/>
                        <field name="failed_requests" readonly="1"/>
                        <field name="last_used" readonly="1"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_web_research_provider" model="ir.actions.act_window">
        <field name="name">Web Research Providers</field>
        <field name="res_model">web.research.provider</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
```

- [ ] **Step 3: Add the kill switch + anonymize toggle + provider table link to Settings**

Edit `sgc_lead_scoring/views/res_config_settings_views.xml` — add this block near the existing `enable_web_research` field (read the file to match its `<setting>` block style), inside the same app settings block:

```xml
                    <setting id="allow_third_party_search_setting" string="Allow Third-Party Web Search"
                             help="Master kill switch. Off by default: only self-hosted SearXNG may run until enabled.">
                        <field name="allow_third_party_search"/>
                    </setting>
                    <setting id="anonymize_company_names_setting" string="Anonymize Company Names"
                             help="Hash company name before sending to any third-party search provider.">
                        <field name="anonymize_company_names"/>
                    </setting>
                    <setting id="web_research_providers_setting" string="Web Research Providers"
                             help="Configure Tavily, Exa, SearXNG, and legacy Google Custom Search.">
                        <button name="%(sgc_lead_scoring.action_web_research_provider)d" type="action"
                                string="Manage Providers" icon="fa-arrow-right" class="btn-link"/>
                    </setting>
```

- [ ] **Step 4: Register the new view file**

Edit `sgc_lead_scoring/__manifest__.py`, in `"data"`, insert `"views/web_research_provider_views.xml",` before `"views/res_config_settings_views.xml",` (views must load before the settings view that references `action_web_research_provider`).

- [ ] **Step 5: Verify install/upgrade**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev -u sgc_lead_scoring --stop-after-init`
Expected: exits 0, no traceback (XML view validation happens at load time — a bad `invisible` expression or missing action reference would fail here).

- [ ] **Step 6: Commit**

```bash
git add sgc_lead_scoring/models/res_config_settings.py sgc_lead_scoring/views/web_research_provider_views.xml sgc_lead_scoring/views/res_config_settings_views.xml sgc_lead_scoring/__manifest__.py
git commit -m "feat(web-research): add kill switch, anonymize toggle, and provider management UI"
```

---

### Task 10: `setup.web.research.wizard` (new multi-provider setup wizard)

**Files:**
- Create: `sgc_lead_scoring/wizards/setup_web_research_wizard.py`
- Create: `sgc_lead_scoring/wizards/setup_web_research_wizard_views.xml`
- Modify: `sgc_lead_scoring/wizards/__init__.py`
- Modify: `sgc_lead_scoring/security/ir.model.access.csv`
- Modify: `sgc_lead_scoring/__manifest__.py`
- Test: `sgc_lead_scoring/tests/test_setup_web_research_wizard.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: `web.research.provider` (Task 1), `web.research.service.search()` (Task 5/6).
- Produces: `setup.web.research.wizard` TransientModel with fields `provider_type (Selection matching web.research.provider), api_key, base_url, search_engine_id, test_query, test_result (Text, readonly), test_success (Boolean, readonly)`; methods `action_test_connection()`, `action_save_provider()` (creates/updates the matching `web.research.provider` record and sets `active=True`).

- [ ] **Step 1: Write the failing test**

Create `sgc_lead_scoring/tests/test_setup_web_research_wizard.py`:

```python
# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase


class TestSetupWebResearchWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['web.research.provider'].search([]).unlink()

    @patch('requests.post')
    def test_action_test_connection_success(self, mock_post):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'results': [{'title': 'Acme', 'url': 'https://acme.com', 'content': 'x'}]}
        mock_post.return_value = resp
        wizard = self.env['setup.web.research.wizard'].create({
            'provider_type': 'tavily', 'api_key': 'test-key', 'test_query': 'Acme Corp',
        })
        wizard.action_test_connection()
        self.assertTrue(wizard.test_success)
        self.assertIn('Acme', wizard.test_result)

    @patch('requests.post')
    def test_action_test_connection_failure(self, mock_post):
        resp = MagicMock()
        resp.status_code = 401
        resp.json.return_value = {}
        mock_post.return_value = resp
        wizard = self.env['setup.web.research.wizard'].create({
            'provider_type': 'tavily', 'api_key': 'bad-key', 'test_query': 'Acme Corp',
        })
        wizard.action_test_connection()
        self.assertFalse(wizard.test_success)

    def test_action_save_provider_creates_active_record(self):
        wizard = self.env['setup.web.research.wizard'].create({
            'provider_type': 'exa', 'api_key': 'my-exa-key',
        })
        wizard.action_save_provider()
        provider = self.env['web.research.provider'].search([('provider_type', '=', 'exa')])
        self.assertTrue(provider)
        self.assertTrue(provider.active)
        self.assertEqual(provider.api_key, 'my-exa-key')

    def test_action_save_provider_updates_existing_record(self):
        self.env['web.research.provider'].create({
            'name': 'Exa', 'provider_type': 'exa', 'api_key': 'old-key', 'active': False,
        })
        wizard = self.env['setup.web.research.wizard'].create({
            'provider_type': 'exa', 'api_key': 'new-key',
        })
        wizard.action_save_provider()
        providers = self.env['web.research.provider'].search([('provider_type', '=', 'exa')])
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers.api_key, 'new-key')
        self.assertTrue(providers.active)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestSetupWebResearchWizard`
Expected: FAIL — `KeyError: 'setup.web.research.wizard'`.

- [ ] **Step 3: Implement the wizard**

Create `sgc_lead_scoring/wizards/setup_web_research_wizard.py`:

```python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SetupWebResearchWizard(models.TransientModel):
    _name = 'setup.web.research.wizard'
    _description = 'Web Research Provider Setup Wizard'

    provider_type = fields.Selection([
        ('tavily', 'Tavily'),
        ('exa', 'Exa'),
        ('searxng', 'SearXNG (self-hosted)'),
        ('google', 'Google Custom Search (legacy)'),
    ], required=True, default='tavily')
    api_key = fields.Char()
    base_url = fields.Char(help='Required for searxng')
    search_engine_id = fields.Char(help='Required for google')
    test_query = fields.Char(default='Microsoft Corporation')
    test_result = fields.Text(readonly=True)
    test_success = fields.Boolean(readonly=True)

    def action_test_connection(self):
        self.ensure_one()
        provider = self.env['web.research.provider'].new({
            'name': 'wizard-test',
            'provider_type': self.provider_type,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'search_engine_id': self.search_engine_id,
            'active': True,
        })
        # `new()` builds an in-memory, unsaved record; _call_provider only reads
        # fields off it and never writes, so this is safe to use for a dry-run test.
        service = self.env['web.research.service']
        results, success = service._call_provider(provider, self.test_query, 3)[:2]
        if success:
            self.test_success = True
            top = results[0]['title'] if results else 'N/A'
            self.test_result = _('SUCCESS! Found %d results for "%s"\nTop result: %s') % (
                len(results), self.test_query, top,
            )
        else:
            self.test_success = False
            self.test_result = _('FAILED: connection test did not return results. Check credentials.')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'setup.web.research.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_save_provider(self):
        self.ensure_one()
        Provider = self.env['web.research.provider']
        existing = Provider.search([('provider_type', '=', self.provider_type)], limit=1)
        vals = {
            'name': dict(self._fields['provider_type'].selection).get(self.provider_type),
            'provider_type': self.provider_type,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'search_engine_id': self.search_engine_id,
            'active': True,
        }
        if existing:
            existing.write(vals)
        else:
            Provider.create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s provider saved and enabled.') % self.provider_type,
                'type': 'success',
                'sticky': False,
            }
        }
```

- [ ] **Step 4: Create the wizard view**

Create `sgc_lead_scoring/wizards/setup_web_research_wizard_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_setup_web_research_wizard_form" model="ir.ui.view">
        <field name="name">setup.web.research.wizard.form</field>
        <field name="model">setup.web.research.wizard</field>
        <field name="arch" type="xml">
            <form string="Set Up Web Research Provider">
                <group>
                    <field name="provider_type"/>
                    <field name="api_key" password="True"/>
                    <field name="base_url" invisible="provider_type != 'searxng'"/>
                    <field name="search_engine_id" invisible="provider_type != 'google'"/>
                    <field name="test_query"/>
                </group>
                <group invisible="not test_result">
                    <field name="test_result" readonly="1" nolabel="1"/>
                </group>
                <footer>
                    <button name="action_test_connection" string="Test Connection" type="object" class="btn-secondary"/>
                    <button name="action_save_provider" string="Save &amp; Enable" type="object" class="btn-primary"/>
                    <button string="Close" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>

    <record id="action_setup_web_research_wizard" model="ir.actions.act_window">
        <field name="name">Set Up Web Research Provider</field>
        <field name="res_model">setup.web.research.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
    </record>
</odoo>
```

- [ ] **Step 5: Register the wizard import**

Edit `sgc_lead_scoring/wizards/__init__.py`:

```python
from . import lead_enrichment_wizard
from . import google_search_setup_wizard
from . import setup_web_research_wizard
```

- [ ] **Step 6: Add ACL row**

Edit `sgc_lead_scoring/security/ir.model.access.csv`, append:

```csv
access_setup_web_research_wizard_manager,setup.web.research.wizard.manager,model_setup_web_research_wizard,sales_team.group_sale_manager,1,1,1,1
```

- [ ] **Step 7: Register the new files in the manifest**

Edit `sgc_lead_scoring/__manifest__.py`, in `"data"`, insert `"wizards/setup_web_research_wizard_views.xml",` after `"wizards/google_search_setup_wizard_views.xml",`.

- [ ] **Step 8: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_setup_web_research_wizard
```

- [ ] **Step 9: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestSetupWebResearchWizard`
Expected: PASS — 4 tests, 0 failures.

- [ ] **Step 10: Commit**

```bash
git add sgc_lead_scoring/wizards/setup_web_research_wizard.py sgc_lead_scoring/wizards/setup_web_research_wizard_views.xml sgc_lead_scoring/wizards/__init__.py sgc_lead_scoring/security/ir.model.access.csv sgc_lead_scoring/__manifest__.py sgc_lead_scoring/tests/test_setup_web_research_wizard.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): add setup.web.research.wizard for multi-provider onboarding"
```

---

### Task 11: Deprecate `google.search.setup.wizard` banner (Phase 2 completion)

**Files:**
- Modify: `sgc_lead_scoring/wizards/google_search_setup_wizard.py`
- Modify: `sgc_lead_scoring/wizards/google_search_setup_wizard_views.xml`
- Modify: `sgc_lead_scoring/tests/test_lead_scoring.py` (only if it references this wizard — check first, see Step 1)

**Interfaces:**
- Consumes: nothing new; `search_google_custom()` compat shim (Task 6) already backs `action_test_connection`.
- Produces: no behavior change to `action_test_connection`/`action_save_and_close` — this task only adds a visible deprecation banner field and text, per spec "Backward compatibility: google.search.setup.wizard retained for one release with banner".

- [ ] **Step 1: Check for existing references to this wizard in tests**

Run: `grep -rn "google.search.setup.wizard\|GoogleSearchSetupWizard" C:/Users/USER/vps-root-planning/sgc_lead_scoring/tests/`
Expected: no matches, or matches only in files already covered by this plan. If a match appears in a test file not listed above, read that file before proceeding and adjust Step 2 to avoid breaking it (add the banner field only — do not rename existing fields/methods).

- [ ] **Step 2: Add the deprecation field**

Edit `sgc_lead_scoring/wizards/google_search_setup_wizard.py` — add a computed display field near the top of the field list:

```python
    deprecation_notice = fields.Char(
        default='This wizard is deprecated as of 19.0.1.6 and will be removed in 19.0.2.0. '
                'Use Settings > Web Research Providers > Manage Providers instead.',
        readonly=True,
    )
```

- [ ] **Step 3: Surface the banner in the view**

Edit `sgc_lead_scoring/wizards/google_search_setup_wizard_views.xml` — add this as the first child of the `<form>` element (read the file first to find the exact `<form>` opening tag and step indicator, since the wizard has 5 steps with conditional visibility):

```xml
                <div class="alert alert-warning" role="alert">
                    <field name="deprecation_notice" readonly="1" nolabel="1"/>
                </div>
```

- [ ] **Step 4: Verify install/upgrade**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev -u sgc_lead_scoring --stop-after-init`
Expected: exits 0, no traceback.

- [ ] **Step 5: Manually verify the wizard still opens and the old test-connection path still works**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestProviderClients`
Expected: PASS — `test_search_google_custom_compat_shim` (from Task 6) still passes, confirming the wizard's underlying call path is untouched.

- [ ] **Step 6: Commit**

```bash
git add sgc_lead_scoring/wizards/google_search_setup_wizard.py sgc_lead_scoring/wizards/google_search_setup_wizard_views.xml
git commit -m "chore(web-research): add deprecation banner to google.search.setup.wizard"
```

---

### Task 12: `crm.lead._enrich_lead()` full pipeline rewrite (Phase 3 — Default flip)

**Files:**
- Modify: `sgc_lead_scoring/models/crm_lead.py`
- Test: `sgc_lead_scoring/tests/test_crm_lead_enrichment.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: `web.research.service.multi_search()` (Task 7/8), `web.research.service.anonymize_lead_id()` (Task 5), `llm.service.call_llm()` (existing, unchanged per spec non-goals).
- Produces: `_enrich_lead()` rewritten to: build 2-3 queries from `partner_name`/`website`, call `multi_search`, build an LLM prompt from `ir.config_parameter` template `llm_lead_scoring.enrichment_prompt_template`, call `llm.service.call_llm`, persist `ai_enrichment_data` (JSON), `ai_enrichment_report`, `ai_enrichment_status` (`completed`/`partial`/`failed`), `ai_last_enrichment_date`, and post an internal note.

Anonymization design note (spec "Per-lead pipeline" step 5 + "Optional anonymization"): queries are built only from `partner_name`/`name`/`website` by construction — `phone`, `email_from`, `internal_note`, and `partner_id.name` are never read into `queries` or the LLM prompt, so there is nothing to strip; `test_enrich_lead_anonymizes_before_building_prompt` below is a regression guard against a future change accidentally adding them. `anonymize_company_names` (Task 9) is wired here as a stricter per-lead override: when enabled, `multi_search()` is called with `providers=['searxng']` so the literal company name is never sent to any third party for that lead (hashing the name itself would make the public-web search meaningless, so this is the functional interpretation of "protect company identity from third-party exposure" used in this plan).

- [ ] **Step 1: Write the failing tests**

Create `sgc_lead_scoring/tests/test_crm_lead_enrichment.py`:

```python
# -*- coding: utf-8 -*-
import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestCrmLeadEnrichment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.lead = self.env['crm.lead'].create({
            'name': 'Acme Corp Deal',
            'partner_name': 'Acme Corp',
            'website': 'https://acme.com',
        })

    def _multi_search_success(self, *_a, **_k):
        return {
            'success': True,
            'results': [{'title': 'Acme', 'url': 'https://acme.com', 'snippet': 'x', 'sources': ['tavily']}],
            'providers_used': ['tavily'],
            'cache_hits': 0,
            'latency_ms': 120,
        }

    def _llm_success(self, *_a, **_k):
        return {'success': True, 'content': 'Acme Corp is a mid-size manufacturer.', 'error': None, 'retries': 0}

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_completed_status(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertEqual(self.lead.ai_enrichment_status, 'completed')
        self.assertTrue(self.lead.ai_enrichment_report)
        data = json.loads(self.lead.ai_enrichment_data)
        self.assertIn('providers_used', data)
        self.assertTrue(self.lead.ai_last_enrichment_date)

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_partial_when_llm_fails(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.return_value = {'success': False, 'content': None, 'error': 'timeout', 'retries': 3}
        self.lead._enrich_lead()
        self.assertEqual(self.lead.ai_enrichment_status, 'partial')
        data = json.loads(self.lead.ai_enrichment_data)
        self.assertTrue(data['results'])

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_falls_back_to_llm_only_when_all_providers_unavailable(self, mock_multi_search, mock_call_llm):
        mock_multi_search.return_value = {
            'success': False, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0,
        }
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertIn(self.lead.ai_enrichment_status, ('completed', 'partial'))
        mock_call_llm.assert_called_once()

    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_skips_website_query_when_no_website(self, mock_multi_search):
        self.lead.website = False
        mock_multi_search.side_effect = self._multi_search_success
        with patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm', side_effect=self._llm_success):
            self.lead._enrich_lead()
        called_queries = mock_multi_search.call_args[0][0]
        self.assertEqual(len(called_queries), 2)

    def test_enrich_lead_anonymizes_before_building_prompt(self):
        self.lead.phone = '+1-555-0100'
        self.lead.email_from = 'buyer@acme.com'
        with patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
                   side_effect=self._multi_search_success), \
             patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm') as mock_llm:
            mock_llm.side_effect = self._llm_success
            self.lead._enrich_lead()
            prompt_messages = mock_llm.call_args.kwargs.get('messages') or mock_llm.call_args[0][0]
            prompt_text = json.dumps(prompt_messages)
            self.assertNotIn('+1-555-0100', prompt_text)
            self.assertNotIn('buyer@acme.com', prompt_text)

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_anonymize_company_names_restricts_to_searxng(self, mock_multi_search, mock_call_llm):
        self.env['ir.config_parameter'].sudo().set_param('llm_lead_scoring.anonymize_company_names', 'True')
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertEqual(mock_multi_search.call_args.kwargs.get('providers'), ['searxng'])

    @patch('odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm')
    @patch('odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search')
    def test_enrich_lead_anonymize_off_does_not_restrict_providers(self, mock_multi_search, mock_call_llm):
        mock_multi_search.side_effect = self._multi_search_success
        mock_call_llm.side_effect = self._llm_success
        self.lead._enrich_lead()
        self.assertNotIn('providers', mock_multi_search.call_args.kwargs)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestCrmLeadEnrichment`
Expected: FAIL — `AssertionError: 'completed' != 'pending'` (current `_enrich_lead` is still the stub).

- [ ] **Step 3: Rewrite `_enrich_lead`**

Edit `sgc_lead_scoring/models/crm_lead.py` — add `import json` and `from datetime import date` to imports, and replace the `_enrich_lead` method body:

```python
    def _enrich_lead(self):
        """Run web research + LLM summarization for a single lead."""
        self.ensure_one()
        if self.ai_enrichment_status == 'processing':
            return
        self.ai_enrichment_status = 'processing'

        company_name = self.partner_name or self.name
        queries = [
            '%s company profile about' % company_name,
            '%s news %s' % (company_name, date.today().year),
        ]
        if self.website:
            queries.append('site:%s products services' % self.website)

        anonymize = self.env['ir.config_parameter'].sudo().get_param(
            'llm_lead_scoring.anonymize_company_names', 'False'
        ) == 'True'
        search_kwargs = {'parallel': True}
        if anonymize:
            search_kwargs['providers'] = ['searxng']
        research = self.env['web.research.service'].multi_search(queries, **search_kwargs)

        anon_id = self.env['web.research.service'].anonymize_lead_id(self.id)
        prompt_template = self.env['ir.config_parameter'].sudo().get_param(
            'llm_lead_scoring.enrichment_prompt_template',
            default=(
                'You are analyzing a sales lead (ref: {anon_id}). Company: {company_name}. '
                'Web research findings:\n{research_summary}\n\n'
                'Write a concise 3-5 sentence summary of this company for a sales rep, '
                'noting any relevant recent news.'
            ),
        )
        research_summary = '\n'.join(
            '- %s: %s' % (r.get('title', ''), r.get('snippet', '')) for r in research.get('results', [])
        ) or 'No web research results available.'
        prompt = prompt_template.format(
            anon_id=anon_id, company_name=company_name, research_summary=research_summary,
        )

        llm_resp = self.env['llm.service'].call_llm(messages=[{'role': 'user', 'content': prompt}])

        self.ai_enrichment_data = json.dumps({
            'results': research.get('results', []),
            'providers_used': research.get('providers_used', []),
            'cache_hits': research.get('cache_hits', 0),
        })

        if llm_resp.get('success'):
            self.ai_enrichment_report = llm_resp.get('content')
            self.ai_enrichment_status = 'completed' if research.get('success') else 'partial'
        else:
            self.ai_enrichment_report = False
            self.ai_enrichment_status = 'partial' if research.get('results') else 'failed'

        self.ai_last_enrichment_date = fields.Datetime.now()

        if self.ai_enrichment_status != 'failed':
            note_lines = ['<b>AI Research Summary</b>']
            if self.ai_enrichment_report:
                note_lines.append('<p>%s</p>' % self.ai_enrichment_report)
            if research.get('providers_used'):
                note_lines.append('<p><i>Sources: %s</i></p>' % ', '.join(research['providers_used']))
            self.message_post(body=''.join(note_lines), subtype_xmlid='mail.mt_note')
```

- [ ] **Step 4: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_crm_lead_enrichment
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestCrmLeadEnrichment`
Expected: PASS — 7 tests, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add sgc_lead_scoring/models/crm_lead.py sgc_lead_scoring/tests/test_crm_lead_enrichment.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): rewrite crm.lead._enrich_lead() to call orchestrator + LLM"
```

---

### Task 13: `_cron_enrich_leads()` parallelization (per-lead cursor/commit)

**Files:**
- Modify: `sgc_lead_scoring/models/crm_lead.py`
- Create: `sgc_lead_scoring/tests/test_cron_concurrency.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: `_enrich_lead()` (Task 12).
- Produces: `_cron_enrich_leads()` rewritten to fan out up to 50 leads across a `ThreadPoolExecutor(max_workers=5)`, each worker opening its own cursor via `self.env.registry.cursor()` and committing per-lead; failures on one lead set `ai_enrichment_status='failed'` for that lead and do not stop the batch.

- [ ] **Step 1: Write the failing test**

Create `sgc_lead_scoring/tests/test_cron_concurrency.py`:

```python
# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestCronConcurrency(TransactionCase):

    def setUp(self):
        super().setUp()
        self.leads = self.env['crm.lead'].create([
            {'name': 'Lead A', 'partner_name': 'Acme A', 'auto_enrich': True},
            {'name': 'Lead B', 'partner_name': 'Acme B', 'auto_enrich': True},
            {'name': 'Lead C', 'partner_name': 'Acme C', 'auto_enrich': True},
        ])
        self.env.cr.commit()  # leads must be committed so worker cursors can see them

    def test_cron_enrich_leads_all_reach_terminal_status(self):
        with patch(
            'odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
            return_value={'success': True, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0},
        ), patch(
            'odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
            return_value={'success': True, 'content': 'summary', 'error': None, 'retries': 0},
        ):
            self.env['crm.lead']._cron_enrich_leads()

        for lead in self.leads:
            lead.invalidate_recordset()
            self.assertIn(lead.ai_enrichment_status, ('completed', 'partial', 'failed'))
            self.assertNotEqual(lead.ai_enrichment_status, 'pending')
            self.assertNotEqual(lead.ai_enrichment_status, 'processing')

    def test_cron_enrich_leads_one_failure_does_not_block_others(self):
        call_count = {'n': 0}

        def flaky_enrich(self_lead, *a, **kw):
            call_count['n'] += 1
            if call_count['n'] == 2:
                raise Exception('simulated provider outage')
            self_lead.ai_enrichment_status = 'completed'

        with patch.object(type(self.leads), '_enrich_lead', flaky_enrich, create=False):
            self.env['crm.lead']._cron_enrich_leads()

        statuses = [lead.ai_enrichment_status for lead in self.leads.browse(self.leads.ids)]
        self.assertIn('failed', statuses)
        self.assertIn('completed', statuses)
```

- [ ] **Step 2: Run tests to verify they fail or pass trivially**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestCronConcurrency`
Expected: `test_cron_enrich_leads_all_reach_terminal_status` may already pass against the current sequential `_cron_enrich_leads()` (it doesn't assert on timing, only terminal status) — that's fine, it's a regression guard for the rewrite. `test_cron_enrich_leads_one_failure_does_not_block_others` should also already pass against the sequential version's existing try/except. Both are kept as regression tests through the parallelization change in Step 3.

- [ ] **Step 3: Parallelize `_cron_enrich_leads`**

Edit `sgc_lead_scoring/models/crm_lead.py` — add `from concurrent.futures import ThreadPoolExecutor` to imports and replace `_cron_enrich_leads`:

```python
    @api.model
    def _cron_enrich_leads(self):
        """Scheduled cron: auto-enrich up to 50 leads, 5 at a time, each
        worker on its own cursor so one lead's failure/rollback can't
        affect another's commit."""
        leads = self.search([
            ('auto_enrich', '=', True),
            ('ai_enrichment_status', '!=', 'processing'),
        ], limit=50)

        def _enrich_one(lead_id):
            with self.env.registry.cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)
                lead = env['crm.lead'].browse(lead_id)
                try:
                    lead._enrich_lead()
                except Exception:
                    _logger.exception('crm.lead._cron_enrich_leads: lead %s failed', lead_id)
                    lead.ai_enrichment_status = 'failed'
                cr.commit()

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(_enrich_one, leads.ids))
        return True
```

Add `import logging` and `_logger = logging.getLogger(__name__)` near the top of the file if not already present (check the existing imports first — the file currently has no logger).

- [ ] **Step 4: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_cron_concurrency
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestCronConcurrency`
Expected: PASS — 2 tests, 0 failures. If `test_cron_enrich_leads_one_failure_does_not_block_others` fails because `patch.object` can't cleanly intercept a per-cursor-environment method lookup, fall back to patching `web.research.service.multi_search` to raise on the 2nd call instead of patching `_enrich_lead` directly — same assertion, more realistic failure injection point.

- [ ] **Step 6: Commit**

```bash
git add sgc_lead_scoring/models/crm_lead.py sgc_lead_scoring/tests/test_cron_concurrency.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): parallelize _cron_enrich_leads with per-lead cursor/commit"
```

---

### Task 14: `lead.enrichment.wizard` parallel toggle + provider priority

**Files:**
- Modify: `sgc_lead_scoring/wizards/lead_enrichment_wizard.py`
- Modify: `sgc_lead_scoring/wizards/lead_enrichment_wizard_views.xml`
- Test: `sgc_lead_scoring/tests/test_lead_enrichment_wizard.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: `crm.lead._enrich_lead()` (Task 12), `ThreadPoolExecutor` (same pattern as Task 13).
- Produces: `lead.enrichment.wizard` field `parallel (Boolean, default True)`; `action_enrich_leads()` runs the selected leads through a thread pool (max_workers=5) when `parallel=True`, sequentially otherwise, matching the cron's fault-isolation behavior.

- [ ] **Step 1: Write the failing tests**

Create `sgc_lead_scoring/tests/test_lead_enrichment_wizard.py`:

```python
# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestLeadEnrichmentWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.leads = self.env['crm.lead'].create([
            {'name': 'Lead A', 'partner_name': 'Acme A'},
            {'name': 'Lead B', 'partner_name': 'Acme B'},
        ])
        self.env.cr.commit()

    def test_parallel_defaults_true(self):
        wizard = self.env['lead.enrichment.wizard'].create({'lead_ids': [(6, 0, self.leads.ids)]})
        self.assertTrue(wizard.parallel)

    def test_action_enrich_leads_parallel_reaches_terminal_status(self):
        wizard = self.env['lead.enrichment.wizard'].create({
            'lead_ids': [(6, 0, self.leads.ids)], 'parallel': True,
        })
        with patch(
            'odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
            return_value={'success': True, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0},
        ), patch(
            'odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
            return_value={'success': True, 'content': 'summary', 'error': None, 'retries': 0},
        ):
            wizard.action_enrich_leads()
        for lead in self.leads:
            lead.invalidate_recordset()
            self.assertNotEqual(lead.ai_enrichment_status, 'pending')

    def test_action_enrich_leads_sequential_still_works(self):
        wizard = self.env['lead.enrichment.wizard'].create({
            'lead_ids': [(6, 0, self.leads.ids)], 'parallel': False,
        })
        with patch(
            'odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
            return_value={'success': True, 'results': [], 'providers_used': [], 'cache_hits': 0, 'latency_ms': 0},
        ), patch(
            'odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
            return_value={'success': True, 'content': 'summary', 'error': None, 'retries': 0},
        ):
            result = wizard.action_enrich_leads()
        self.assertEqual(result['params']['type'], 'success')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestLeadEnrichmentWizard`
Expected: FAIL — `test_parallel_defaults_true` fails with `AttributeError` (no `parallel` field yet).

- [ ] **Step 3: Add the toggle and parallelize the action**

Edit `sgc_lead_scoring/wizards/lead_enrichment_wizard.py` — add `from concurrent.futures import ThreadPoolExecutor` to imports, add the field:

```python
    parallel = fields.Boolean(
        string='Enrich in Parallel',
        default=True,
        help='Run web research + LLM calls for multiple leads concurrently (max 5 at a time).',
    )
```

Replace the enrichment loop inside `action_enrich_leads`:

```python
        success_count = 0
        failed_count = 0

        if self.parallel and len(self.lead_ids) > 1:
            def _enrich_one(lead_id):
                with self.env.registry.cursor() as cr:
                    env = api.Environment(cr, self.env.uid, self.env.context)
                    lead = env['crm.lead'].browse(lead_id)
                    try:
                        lead._enrich_lead()
                        cr.commit()
                        return True
                    except Exception:
                        lead.ai_enrichment_status = 'failed'
                        cr.commit()
                        return False

            with ThreadPoolExecutor(max_workers=5) as executor:
                outcomes = list(executor.map(_enrich_one, self.lead_ids.ids))
            success_count = sum(1 for o in outcomes if o)
            failed_count = len(outcomes) - success_count
        else:
            for lead in self.lead_ids:
                try:
                    lead._enrich_lead()
                    success_count += 1
                except Exception:
                    failed_count += 1
                    continue
```

(This replaces the existing `for lead in self.lead_ids: try: ... except Exception: ... continue` block; the rest of `action_enrich_leads` — the notification return — stays unchanged.)

- [ ] **Step 4: Expose the toggle in the view**

Edit `sgc_lead_scoring/wizards/lead_enrichment_wizard_views.xml` — add `<field name="parallel"/>` next to the existing `force_research` field (read the file first to match its exact form layout before inserting).

- [ ] **Step 5: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_lead_enrichment_wizard
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestLeadEnrichmentWizard`
Expected: PASS — 3 tests, 0 failures.

- [ ] **Step 7: Commit**

```bash
git add sgc_lead_scoring/wizards/lead_enrichment_wizard.py sgc_lead_scoring/wizards/lead_enrichment_wizard_views.xml sgc_lead_scoring/tests/test_lead_enrichment_wizard.py sgc_lead_scoring/tests/__init__.py
git commit -m "feat(web-research): add parallel enrichment toggle to lead.enrichment.wizard"
```

---

### Task 15: E2E test + full regression run (Phase 4 groundwork — Deprecate readiness)

**Files:**
- Create: `sgc_lead_scoring/tests/test_lead_enrichment_e2e.py`
- Modify: `sgc_lead_scoring/tests/__init__.py`

**Interfaces:**
- Consumes: the whole stack (Tasks 1-14) via the UI action `action_enrich_with_ai` → `lead.enrichment.wizard` → `crm.lead._enrich_lead()`.
- Produces: an `HttpCase` that drives the real "AI Enrich" button end-to-end (mocked HTTP at the `requests` boundary only) and asserts the internal note contains the research section, closing out the spec's "E2E" testing requirement.

- [ ] **Step 1: Write the E2E test**

Create `sgc_lead_scoring/tests/test_lead_enrichment_e2e.py`:

```python
# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import HttpCase, tagged


@tagged('-at_install', 'post_install')
class TestLeadEnrichmentE2E(HttpCase):

    def test_ai_enrich_button_produces_research_note(self):
        lead = self.env['crm.lead'].create({
            'name': 'E2E Test Lead', 'partner_name': 'E2E Acme', 'website': 'https://e2eacme.com',
        })
        with patch(
            'odoo.addons.sgc_lead_scoring.models.web_research_service.WebResearchService.multi_search',
            return_value={
                'success': True,
                'results': [{'title': 'E2E Acme', 'url': 'https://e2eacme.com', 'snippet': 'a company', 'sources': ['tavily']}],
                'providers_used': ['tavily'],
                'cache_hits': 0,
                'latency_ms': 90,
            },
        ), patch(
            'odoo.addons.sgc_lead_scoring.models.llm_service.LlmService.call_llm',
            return_value={'success': True, 'content': 'E2E Acme is a test company.', 'error': None, 'retries': 0},
        ):
            wizard = self.env['lead.enrichment.wizard'].create({
                'lead_ids': [(6, 0, lead.ids)], 'parallel': False,
            })
            wizard.action_enrich_leads()

        lead.invalidate_recordset()
        self.assertEqual(lead.ai_enrichment_status, 'completed')
        messages = lead.message_ids.filtered(lambda m: 'AI Research Summary' in (m.body or ''))
        self.assertTrue(messages)
        self.assertIn('tavily', messages[0].body)
```

- [ ] **Step 2: Register the test module**

Edit `sgc_lead_scoring/tests/__init__.py`, add:

```python
from . import test_lead_enrichment_e2e
```

- [ ] **Step 3: Run the E2E test**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring --test-tags /sgc_lead_scoring:TestLeadEnrichmentE2E`
Expected: PASS — 1 test, 0 failures.

- [ ] **Step 4: Run the full module test suite as a final regression gate**

Run: `docker compose -p odoo run --rm web odoo-bin -d sgc_theme_dev --test-enable --stop-after-init -i sgc_lead_scoring`
Expected: all tests across `test_llm_provider.py`, `test_llm_service.py`, `test_lead_scoring.py`, and every new file from Tasks 1-15 pass — 0 failures. This is the readiness gate before Phase 3's "default flip" (enabling the new chain by default) can be considered for a future release; this plan stops at "flip is code-complete and tested," matching the spec's Phase 3 description — the actual `allow_third_party_search` default-on flip is a config/ops decision made after 2 weeks of stable opt-in usage (spec "Rollout"), not a code task.

- [ ] **Step 5: Commit**

```bash
git add sgc_lead_scoring/tests/test_lead_enrichment_e2e.py sgc_lead_scoring/tests/__init__.py
git commit -m "test(web-research): add end-to-end AI Enrich coverage"
```

---

## Post-plan notes (not code tasks — operational follow-ups)

- **Phase 3 default flip**: after Task 15 ships and 2 weeks of stable opt-in usage pass (per spec Rollout), an admin flips `allow_third_party_search` to `True` org-wide via Settings — no code change, just config + the readiness-auditor/production-qa gates in this repo's own pipeline (CLAUDE.md Stage 4/5) if this feature goes through that process.
- **Phase 4 deprecate**: in a later release (`19.0.2.0` per the banner text in Task 11), delete `google_search_setup_wizard.py`/`.xml`, their ACL row, and the `deprecation_notice` field — `search_google_custom()` itself stays as the permanent compat shim (spec doesn't scope it for removal).
- **Open question from spec carried forward**: `min_results` is hardcoded to `3` as the `multi_search` default in Task 7 — the spec left this open ("3? 5?"); revisit after Tavily/Exa usage data is available.
- **Update `DEPLOYMENT_GUIDE.md`**: the spec's risk register calls for documenting the new models there in case of backup/restore drops — out of scope for this code plan, flagged for a separate doc pass.
