# -*- coding: utf-8 -*-
###############################################################################
#    Part of the SGC Odoo Suite <https://sgctech.ai>
#
#    SGC TECH AI
#    Copyright (C) 2026 SGC TECH AI (<https://sgctech.ai>)
#
#    This module and its source code are licensed under the Odoo Proprietary
#    License v1.0 (OPL-1). You may not redistribute or resell it. See
#    https://www.odoo.com/documentation/19.0/legal/licenses.html for terms.
###############################################################################

from odoo import fields, models, api, _


class AppraisalSurveyFormReport(models.AbstractModel):
    """Report model for appraisal survey forms"""
    _name = 'report.oh_appraisal.appraisal_survey_form_report'
    _description = 'Appraisal Survey Form Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate report values"""
        survey_forms = self.env['appraisal.survey.form'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'appraisal.survey.form',
            'docs': survey_forms,
            'data': data,
            'get_survey_data': self._get_survey_data,
            'get_response_summary': self._get_response_summary,
        }

    def _get_survey_data(self, survey_form):
        """Get detailed survey data"""
        return {
            'title': survey_form.title,
            'description': survey_form.description,
            'survey_type': survey_form.survey_type,
            'created_date': survey_form.created_date,
            'start_date': survey_form.start_date,
            'deadline_date': survey_form.deadline_date,
            'assigned_count': len(survey_form.assigned_to_ids),
            'total_responses': survey_form.response_count,
            'completed_responses': survey_form.completed_count,
            'pending_responses': survey_form.pending_count,
        }

    def _get_response_summary(self, survey_form):
        """Get summary of responses"""
        responses = self.env['appraisal.survey.response'].search([
            ('survey_form_id', '=', survey_form.id)
        ])

        summary = {
            'total': len(responses),
            'completed': len(responses.filtered(lambda r: r.state == 'submitted')),
            'pending': len(responses.filtered(lambda r: r.state == 'pending')),
            'in_progress': len(responses.filtered(
                lambda r: r.state == 'in_progress'
            )),
            'responses': []
        }

        for response in responses:
            summary['responses'].append({
                'respondent': response.respondent_name or 'Anonymous',
                'email': response.respondent_email,
                'status': response.state,
                'created': response.created_date,
                'submitted': response.submitted_date,
                'completion': response.completion_percentage,
            })

        return summary


class AppraisalSurveyResponseReport(models.AbstractModel):
    """Report model for detailed appraisal survey responses"""
    _name = 'report.oh_appraisal.appraisal_survey_response_report'
    _description = 'Appraisal Survey Response Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate response report values"""
        responses = self.env['appraisal.survey.response'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'appraisal.survey.response',
            'docs': responses,
            'data': data,
            'get_response_details': self._get_response_details,
            'get_answer_analysis': self._get_answer_analysis,
        }

    def _get_response_details(self, response):
        """Get detailed response information"""
        return {
            'survey_title': response.survey_form_id.title,
            'respondent': response.respondent_name or 'Anonymous',
            'respondent_email': response.respondent_email,
            'status': response.state,
            'created_date': response.created_date,
            'submitted_date': response.submitted_date,
            'completion_percentage': response.completion_percentage,
            'comments': response.comments,
        }

    def _get_answer_analysis(self, response):
        """Analyze answers from response data"""
        if not response.response_data:
            return {}

        survey_form = response.survey_form_id
        answers = {}

        for question in survey_form.question_ids:
            question_id = str(question.id)
            answer = response.response_data.get(question_id, None)

            answers[question_id] = {
                'question': question.question_text,
                'question_type': question.question_type,
                'answer': answer,
                'required': question.required,
            }

        return answers


class AppraisalSurveyAnalyticsReport(models.AbstractModel):
    """Report model for appraisal survey analytics"""
    _name = 'report.oh_appraisal.appraisal_survey_analytics_report'
    _description = 'Appraisal Survey Analytics Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate analytics report"""
        survey_forms = self.env['appraisal.survey.form'].browse(docids)

        analytics = {}
        for survey in survey_forms:
            analytics[survey.id] = self._compute_analytics(survey)

        return {
            'doc_ids': docids,
            'doc_model': 'appraisal.survey.form',
            'docs': survey_forms,
            'data': data,
            'analytics': analytics,
            'get_rating_analysis': self._get_rating_analysis,
        }

    def _compute_analytics(self, survey_form):
        """Compute analytics for a survey"""
        responses = self.env['appraisal.survey.response'].search([
            ('survey_form_id', '=', survey_form.id)
        ])

        total_responses = len(responses)
        completed = len(responses.filtered(lambda r: r.state == 'submitted'))

        analytics = {
            'total_assigned': len(survey_form.assigned_to_ids),
            'total_responses': total_responses,
            'completed_responses': completed,
            'pending_responses': len(
                responses.filtered(lambda r: r.state == 'pending')
            ),
            'response_rate': (completed / total_responses * 100) if
                           total_responses > 0 else 0,
            'average_completion': self._get_average_completion(responses),
        }

        return analytics

    def _get_average_completion(self, responses):
        """Calculate average completion percentage"""
        if not responses:
            return 0
        total_completion = sum(r.completion_percentage for r in responses)
        return total_completion / len(responses)

    def _get_rating_analysis(self, survey_form):
        """Analyze rating-type questions"""
        rating_analysis = {}

        for question in survey_form.question_ids:
            if question.question_type == 'rating':
                responses = self.env['appraisal.survey.response'].search([
                    ('survey_form_id', '=', survey_form.id)
                ])

                ratings = []
                for response in responses:
                    if response.response_data:
                        rating = response.response_data.get(
                            str(question.id), None
                        )
                        if rating is not None:
                            ratings.append(float(rating))

                if ratings:
                    rating_analysis[question.id] = {
                        'question': question.question_text,
                        'responses': len(ratings),
                        'average': sum(ratings) / len(ratings),
                        'min': min(ratings),
                        'max': max(ratings),
                        'distribution': self._get_distribution(ratings),
                    }

        return rating_analysis

    def _get_distribution(self, ratings):
        """Get distribution of ratings"""
        distribution = {}
        for rating in ratings:
            rating_int = int(rating)
            distribution[rating_int] = distribution.get(rating_int, 0) + 1
        return distribution
