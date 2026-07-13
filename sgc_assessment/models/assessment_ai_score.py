# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AssessmentAiScore(models.Model):
    _name = 'assessment.ai.score'
    _description = 'Assessment AI Score'
    _rec_name = 'candidate_id'
    
    candidate_id = fields.Many2one('assessment.candidate', string='Candidate', required=True, ondelete='cascade')
    assessment_date = fields.Date(string='Assessment Date', default=fields.Date.context_today)
    
    # AI Scores by category (0-100)
    technical_score = fields.Float(string='Technical Score', digits=(4, 2))
    sales_score = fields.Float(string='Sales Score', digits=(4, 2))
    communication_score = fields.Float(string='Communication Score', digits=(4, 2))
    learning_score = fields.Float(string='Learning Score', digits=(4, 2))
    cultural_fit_score = fields.Float(string='Cultural Fit Score', digits=(4, 2))
    
    total_score = fields.Float(string='Total Score', digits=(4, 2))
    overall_score = fields.Float(string='Overall Score', related='percentage_score', store=True)
    percentage_score = fields.Float(string='Percentage Score', digits=(4, 2))
    grade = fields.Char(string='Grade', compute='_compute_grade')
    scoring_date = fields.Datetime(string='Scoring Date', default=fields.Datetime.now)

    # AI recommendation & confidence
    ai_recommendation = fields.Selection([
        ('reject', 'Reject'),
        ('reconsider', 'Reconsider'),
        ('interview', 'Interview'),
        ('strong_hire', 'Strong Hire'),
    ], string='AI Recommendation')
    ai_confidence_score = fields.Float(string='AI Confidence', digits=(4, 2))
    has_red_flags = fields.Boolean(string='Has Red Flags', default=False)

    # Processing details
    processing_time_ms = fields.Float(string='Processing Time (ms)')
    ai_model_version = fields.Char(string='AI Model Version')
    tokens_used = fields.Integer(string='Tokens Used')
    estimated_cost = fields.Monetary(string='Estimated Cost', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')
    response_id = fields.Many2one('assessment.response', string='Response')

    # AI analysis text
    identified_strengths = fields.Text(string='Identified Strengths')
    skill_gaps = fields.Text(string='Skill Gaps')
    red_flags_detail = fields.Text(string='Red Flags Detail')
    question_analysis = fields.Text(string='Question Analysis')

    # Raw AI responses (for debugging/transparency)
    raw_response = fields.Text(string='Raw AI Response')
    processing_time = fields.Float(string='Processing Time (seconds)')
    model_used = fields.Char(string='AI Model Used')
    
    @api.depends('technical_score', 'sales_score', 'communication_score', 'learning_score', 'cultural_fit_score')
    def _compute_total_score(self):
        for record in self:
            record.total_score = (record.technical_score or 0) + (record.sales_score or 0) + (record.communication_score or 0) + (record.learning_score or 0) + (record.cultural_fit_score or 0)
    
    @api.depends('total_score')
    def _compute_percentage_score(self):
        for record in self:
            record.percentage_score = (record.total_score / 500) * 100  # Assuming max 500 points
    
    @api.depends('percentage_score')
    def _compute_grade(self):
        for record in self:
            if record.percentage_score >= 90:
                record.grade = 'A+'
            elif record.percentage_score >= 80:
                record.grade = 'A'
            elif record.percentage_score >= 70:
                record.grade = 'B'
            elif record.percentage_score >= 60:
                record.grade = 'C'
            elif record.percentage_score >= 50:
                record.grade = 'D'
            else:
                record.grade = 'F'

    def action_regenerate_score(self):
        for record in self:
            record._compute_total_score()
            record._compute_percentage_score()
            record._compute_grade()
        return True
