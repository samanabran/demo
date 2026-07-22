# -*- coding: utf-8 -*-
import hashlib
import logging
import time

import requests

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

    @api.model
    def search_google_custom(self, query, num_results=_DEFAULT_NUM_RESULTS):
        """Backward-compat shim: pre-redesign callers (google.search.setup.wizard)
        keep this exact signature; it now delegates to the orchestrator restricted
        to the google provider type."""
        return self.search(query, num_results=num_results, providers=['google'])

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
            query_hash = self.hash_query(query)
            _logger.warning(
                'web.research.service: %s request failed (%s) for query_hash=%s',
                provider.provider_type, type(exc).__name__, query_hash,
            )
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
