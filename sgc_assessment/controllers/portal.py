# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging

_logger = logging.getLogger(__name__)


class AssessmentPortal(CustomerPortal):
    
    @http.route('/assessment', type='http', auth='public', website=True, csrf=False)
    def assessment_landing(self):
        """Assessment landing page with information, start button, and top performers leaderboard"""
        try:
            # Get top 10 candidates by overall score
            top_candidates = request.env['assessment.candidate'].sudo().search([
                ('status', 'in', ['ai_scored', 'reviewed']),
                ('overall_score', '>', 0)
            ], order='overall_score desc, submission_date desc', limit=10)
            
            values = {
                'top_candidates': top_candidates,
                'total_candidates': request.env['assessment.candidate'].sudo().search_count([('status', '!=', 'draft')])
            }
            
            return request.render('sgc_assessment.portal_assessment_landing', values)
        except (ValueError, KeyError) as e:
            _logger.error("Error rendering assessment landing page: %s", str(e), exc_info=True)
            return request.render('http_routing.404')
    
    @http.route('/assessment/start', type='http', auth='public', website=True, csrf=False)
    def assessment_form(self):
        """Public assessment form with timer"""
        try:
            # Ensure we're in a clean transaction
            request.env.cr.commit()
            
            questions = request.env['assessment.question'].sudo().get_active_questions()
            
            if not questions:
                _logger.warning("No active questions found for assessment")
                return request.render('sgc_assessment.portal_assessment_error', {
                    'error_message': 'Assessment questions are not configured. Please contact support.'
                })
            
            values = {
                'questions': questions,
                'page_name': 'assessment',
                'time_limit': 45,  # 45 minutes
            }
            
            return request.render('sgc_assessment.portal_assessment_form', values)
        except (ValueError, KeyError, AttributeError) as e:
            _logger.error("Error rendering assessment form: %s", str(e), exc_info=True)
            # Rollback transaction on error
            request.env.cr.rollback()
            return request.render('sgc_assessment.portal_assessment_error', {
                'error_message': 'An error occurred loading the assessment. Please try again later.'
            })
    
    @http.route('/assessment/view/<string:access_token>', type='http', auth='public', website=True, csrf=False)
    def view_assessment(self, access_token):
        """View submitted assessment using access token"""
        try:
            # Ensure clean transaction
            request.env.cr.commit()
            
            candidate = request.env['assessment.candidate'].sudo().search([
                ('access_token', '=', access_token)
            ], limit=1)
            
            if not candidate:
                return request.render('sgc_assessment.portal_assessment_not_found')
            
            values = {
                'candidate': candidate,
                'response': candidate.response_id,
                'ai_score': candidate.ai_score_id,
                'human_review': candidate.human_review_id,
                'ranking': candidate.ranking_id,
                'page_name': 'assessment_view',
            }
            
            return request.render('sgc_assessment.portal_assessment_view', values)
        except (ValueError, KeyError) as e:
            _logger.error("Error viewing assessment: %s", str(e), exc_info=True)
            request.env.cr.rollback()
            return request.render('sgc_assessment.portal_assessment_not_found')
    
    @http.route('/assessment/thank-you', type='http', auth='public', website=True, csrf=False)
    def assessment_thank_you(self):
        """Thank you page after submission"""
        try:
            return request.render('sgc_assessment.portal_assessment_thank_you')
        except (ValueError, KeyError) as e:
            _logger.error("Error rendering thank you page: %s", str(e), exc_info=True)
            return request.render('http_routing.404')
