# -*- coding: utf-8 -*-
##############################################################################
#    SCHOLARIX Assessment System
#    Copyright (C) 2025 SGC TECH AI (https://sgctech.ai)
#    License LGPL-3 - See LICENSE file for details
##############################################################################

from odoo import http, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class AssessmentAdminController(http.Controller):
    """Backend HTTP routes for SCHOLARIX Assessment management"""

    @http.route('/assessment/api/candidates', type='jsonrpc', auth='user')
    def api_candidates(self, **kwargs):
        """JSON API for assessment candidates"""
        try:
            domain = kwargs.get('domain', [])
            Candidate = request.env['assessment.candidate'].sudo()
            candidates = Candidate.search_read(
                domain,
                fields=['id', 'name', 'email', 'overall_score', 'status',
                        'submission_date', 'access_token'],
                limit=kwargs.get('limit', 50),
                offset=kwargs.get('offset', 0),
                order=kwargs.get('order', 'create_date desc')
            )
            return {
                'candidates': candidates,
                'total': Candidate.search_count(domain),
            }
        except Exception as e:
            _logger.error("Error fetching assessment candidates: %s", str(e), exc_info=True)
            return {'error': str(e), 'candidates': [], 'total': 0}

    @http.route('/assessment/api/stats', type='jsonrpc', auth='user')
    def api_assessment_stats(self, **kwargs):
        """JSON API for assessment analytics"""
        try:
            Candidate = request.env['assessment.candidate'].sudo()
            total = Candidate.search_count([])
            completed = Candidate.search_count([('status', 'in', ['ai_scored', 'reviewed'])])
            pending_review = Candidate.search_count([('status', '=', 'ai_scored')])

            return {
                'total_candidates': total,
                'completed': completed,
                'pending_review': pending_review,
                'completion_rate': round((completed / total * 100) if total else 0, 1),
            }
        except Exception as e:
            _logger.error("Error fetching assessment stats: %s", str(e), exc_info=True)
            return {'error': str(e)}

    @http.route('/assessment/report/<model("assessment.candidate"):candidate>',
                type='http', auth='user', website=True)
    def candidate_report(self, candidate, **kwargs):
        """Detailed candidate assessment report page"""
        try:
            if not candidate.exists():
                return request.not_found()

            return request.render('sgc_assessment.candidate_report', {
                'candidate': candidate,
                'response': candidate.response_id,
                'ai_score': candidate.ai_score_id,
                'human_review': candidate.human_review_id,
                'ranking': candidate.ranking_id,
            })
        except Exception as e:
            _logger.error("Error rendering candidate report: %s", str(e), exc_info=True)
            return request.not_found()
