# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AssessmentQuestion(models.Model):
    _name = 'assessment.question'
    _description = 'Assessment Question'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(string='Question Title', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    question_text = fields.Text(string='Question', required=True)
    correct_answer = fields.Text(string='Correct Answer')
    help_text = fields.Text(string='Help Text')
    
    question_type = fields.Selection([
        ('technical', 'Technical'),
        ('sales', 'Sales'),
        ('communication', 'Communication'),
        ('learning', 'Learning Agility'),
        ('cultural_fit', 'Cultural Fit'),
        ('general', 'General'),
    ], string='Question Type', required=True, default='general')
    
    category = fields.Selection([
        ('automation', 'Automation'),
        ('ai_tools', 'AI Tools'),
        ('client_management', 'Client Management'),
        ('estimation', 'Estimation'),
        ('learning', 'Learning'),
        ('objection', 'Objection Handling'),
        ('conflict', 'Conflict Resolution'),
        ('simplification', 'Simplification'),
        ('boundaries', 'Setting Boundaries'),
        ('motivation', 'Motivation'),
    ], string='Category')
    
    scoring_weight = fields.Float(
        string='Scoring Weight',
        default=1.0,
        help='Weight in category score calculation'
    )
    
    min_char_count = fields.Integer(
        string='Minimum Characters',
        default=50,
        help='Minimum expected answer length'
    )
    max_char_count = fields.Integer(
        string='Maximum Characters',
        default=1000,
        help='Maximum allowed answer length'
    )
    
    is_required = fields.Boolean(string='Required', default=True)
    is_active = fields.Boolean(string='Active', default=True)
    
    # Scoring Criteria (for AI)
    scoring_criteria = fields.Text(
        string='Scoring Criteria',
        help='Detailed criteria for AI scoring'
    )
    
    # Example Answers
    good_answer_example = fields.Text(string='Good Answer Example')
    bad_answer_example = fields.Text(string='Bad Answer Example')
    
    notes = fields.Text(string='Notes')
    
    @api.model
    def get_active_questions(self):
        """Get all active questions in sequence"""
        return self.search([('is_active', '=', True)], order='sequence')
    
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name = f"Q{record.sequence}: {record.name}"
            result.append((record.id, name))
        return result
