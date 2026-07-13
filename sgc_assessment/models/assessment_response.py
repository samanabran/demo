# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssessmentResponse(models.Model):
    _name = 'assessment.response'
    _description = 'Assessment Response'
    _rec_name = 'question_id'
    
    candidate_id = fields.Many2one('assessment.candidate', string='Candidate', required=True, ondelete='cascade')
    question_id = fields.Many2one('assessment.question', string='Question', required=True, ondelete='cascade')
    answer_text = fields.Text(string='Answer Text')
    answer_file = fields.Binary(string='Answer File')
    answer_file_name = fields.Char(string='File Name')
    score = fields.Float(string='Score Obtained', digits=(4, 2))
    ai_score = fields.Float(string='AI Score', digits=(4, 2))
    feedback = fields.Text(string='Feedback')
    reviewer_id = fields.Many2one('res.users', string='Reviewer')
    is_correct = fields.Boolean(string='Is Correct', compute='_compute_is_correct')
    
    @api.depends('answer_text', 'question_id.correct_answer')
    def _compute_is_correct(self):
        for record in self:
            if record.question_id.correct_answer and record.answer_text:
                record.is_correct = record.question_id.correct_answer.strip().lower() == record.answer_text.strip().lower()
            else:
                record.is_correct = False
