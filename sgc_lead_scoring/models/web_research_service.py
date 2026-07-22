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
