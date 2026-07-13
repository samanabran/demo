# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class AssessmentCandidate(models.Model):
    _name = 'assessment.candidate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Assessment Candidate'
    _rec_name = 'name'
    _order = 'create_date desc'
    
    name = fields.Char(string='Full Name', required=True, tracking=True)
    candidate_name = fields.Char(string='Candidate Name', related='name', store=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone Number')
    date_of_birth = fields.Date(string='Date of Birth')
    address = fields.Text(string='Address')
    
    # Assessment details
    job_position = fields.Many2one('hr.job', string='Job Position')
    department = fields.Many2one('hr.department', string='Department')
    date_applied = fields.Date(string='Date Applied', default=fields.Date.context_today)
    expiration_date = fields.Date(string='Assessment Expiration Date')
    
    # Assessment results
    total_score = fields.Float(string='Total Score', digits=(4, 2))
    percentage_score = fields.Float(string='Percentage Score', digits=(4, 2))
    overall_score = fields.Float(string='Overall Score', digits=(4, 2))
    technical_score = fields.Float(string='Technical Score', digits=(4, 2))
    sales_score = fields.Float(string='Sales Score', digits=(4, 2))
    grade = fields.Char(string='Grade', compute='_compute_grade')
    state = fields.Selection(related='status', string='State')
    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected')
    ], string='Status', default='new', tracking=True)
    
    # Assessment components
    response_ids = fields.One2many('assessment.response', 'candidate_id', string='Responses')
    ai_score_ids = fields.One2many('assessment.ai.score', 'candidate_id', string='AI Scores')
    audit_log_ids = fields.One2many('assessment.audit.log', 'candidate_id', string='Audit Log')
    
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
