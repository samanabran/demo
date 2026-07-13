# -*- coding: utf-8 -*-
###############################################################################
#    Production-Ready Enhancements for OH_APPRAISAL
#
#    This file contains additional production-ready features and improvements
###############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class AppraisalSurveyFormProduction(models.Model):
    """Production-ready enhancements for AppraisalSurveyForm"""
    _inherit = 'appraisal.survey.form'

    # Production Fields
    is_active = fields.Boolean(
        string="Is Active",
        default=True,
        help="Deactivate survey without deleting it"
    )
    version = fields.Integer(
        string="Version",
        default=1,
        help="Track survey version changes"
    )
    max_attempts = fields.Integer(
        string="Maximum Attempts",
        default=1,
        help="Maximum number of times respondent can fill the survey"
    )
    randomize_questions = fields.Boolean(
        string="Randomize Questions",
        default=False,
        help="Display questions in random order"
    )
    require_all_questions = fields.Boolean(
        string="Require All Questions",
        default=True,
        help="Respondent must answer all questions"
    )

    # Audit Trail
    created_by = fields.Many2one(
        'res.users',
        string="Created By",
        readonly=True,
        compute='_compute_audit_fields'
    )
    last_modified_by = fields.Many2one(
        'res.users',
        string="Last Modified By",
        readonly=True,
        compute='_compute_audit_fields'
    )
    created_timestamp = fields.Datetime(
        string="Created Date",
        readonly=True,
        default=fields.Datetime.now
    )
    last_modified_timestamp = fields.Datetime(
        string="Last Modified Date",
        readonly=True
    )

    def _compute_audit_fields(self):
        """Compute audit trail fields"""
        for record in self:
            record.created_by = record.create_uid
            record.last_modified_by = record.write_uid

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add logging"""
        records = super().create(vals_list)
        for record in records:
            _logger.info(
                f"Survey Form created: {record.title} "
                f"by {self.env.user.name}"
            )
        return records

    def write(self, values):
        """Override write to log changes"""
        result = super().write(values)
        _logger.info(
            f"Survey Form updated: {self.title} "
            f"by {self.env.user.name}"
        )
        return result

    def unlink(self):
        """Override delete with logging"""
        for record in self:
            _logger.warning(
                f"Survey Form deleted: {record.title} "
                f"by {self.env.user.name}"
            )
        return super().unlink()

    @api.constrains('max_attempts')
    def _check_max_attempts(self):
        """Ensure max attempts is positive"""
        for record in self:
            if record.max_attempts < 1:
                raise ValidationError(
                    _("Maximum attempts must be at least 1")
                )

    def action_duplicate_survey(self):
        """Create a copy of the survey"""
        self.ensure_one()
        new_survey = self.copy({
            'title': f"{self.title} (Copy)",
            'version': self.version + 1,
        })
        _logger.info(f"Survey duplicated: {self.title} → {new_survey.title}")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'appraisal.survey.form',
            'res_id': new_survey.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_archive(self):
        """Archive survey instead of deleting"""
        self.write({'is_active': False, 'state': 'closed'})
        _logger.info(f"Survey archived: {self.title}")

    def action_unarchive(self):
        """Restore archived survey"""
        self.write({'is_active': True})
        _logger.info(f"Survey restored: {self.title}")


class AppraisalSurveyResponseProduction(models.Model):
    """Production-ready enhancements for AppraisalSurveyResponse"""
    _inherit = 'appraisal.survey.response'

    # IP Address Tracking for security
    ip_address = fields.Char(
        string="IP Address",
        readonly=True,
        help="IP address of respondent's device"
    )
    user_agent = fields.Char(
        string="User Agent",
        readonly=True,
        help="Browser information"
    )
    submission_timestamp = fields.Datetime(
        string="Submission Time",
        readonly=True,
        help="Exact time of submission"
    )
    time_to_complete = fields.Float(
        string="Time to Complete (minutes)",
        compute='_compute_time_to_complete',
        help="Minutes taken to complete survey"
    )

    # Quality Control
    flagged = fields.Boolean(
        string="Flagged",
        default=False,
        help="Flag suspicious or problematic responses"
    )
    flag_reason = fields.Text(
        string="Flag Reason",
        help="Reason for flagging this response"
    )
    requires_review = fields.Boolean(
        string="Requires Review",
        default=False,
        help="Mark for manual review"
    )

    def _compute_time_to_complete(self):
        """Calculate time taken to complete survey"""
        for record in self:
            if record.created_date and record.submission_timestamp:
                duration = record.submission_timestamp - record.created_date
                record.time_to_complete = duration.total_seconds() / 60
            else:
                record.time_to_complete = 0

    @api.constrains('response_data')
    def _validate_response_data(self):
        """Validate response data integrity"""
        for record in self:
            if record.response_data and isinstance(record.response_data, dict):
                # Check all required questions are answered
                if record.survey_id.question_ids:
                    for question in record.survey_id.question_ids:
                        if question.required and \
                           question.id not in record.response_data:
                            raise ValidationError(
                                _(f"Missing answer for required question: "
                                  f"{question.question_text}")
                            )

    def action_flag_response(self):
        """Flag response for review"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Flag Response'),
            'res_model': 'appraisal.survey.response',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_flagged': True,
                'default_requires_review': True
            }
        }


class AppraisalSurveyQuestionProduction(models.Model):
    """Production-ready enhancements for Questions"""
    _inherit = 'appraisal.survey.question'

    # Advanced Options
    conditional_display = fields.Boolean(
        string="Conditional Display",
        default=False,
        help="Show this question based on previous answers"
    )
    conditional_question_id = fields.Many2one(
        'appraisal.survey.question',
        string="Depends on Question",
        help="This question depends on answer to another"
    )
    conditional_answer = fields.Char(
        string="Show if Answer is",
        help="Show this question if dependent answer matches this value"
    )
    point_value = fields.Float(
        string="Point Value",
        default=0,
        help="Point value for scoring"
    )
    display_order = fields.Integer(
        string="Display Order",
        default=0,
        help="Order in which question is displayed"
    )

    _order = 'display_order, sequence'

    @api.constrains('question_type')
    def _check_question_type(self):
        """Validate question type"""
        valid_types = [
            'text', 'textarea', 'radio', 'checkbox',
            'rating', 'date', 'numeric'
        ]
        for record in self:
            if record.question_type not in valid_types:
                raise ValidationError(
                    _(f"Invalid question type: {record.question_type}")
                )
