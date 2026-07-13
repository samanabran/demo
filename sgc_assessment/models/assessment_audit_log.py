# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AssessmentAuditLog(models.Model):
    _name = 'assessment.audit.log'
    _description = 'Assessment Audit Log'
    _order = 'timestamp desc'
    _rec_name = 'action'

    candidate_id = fields.Many2one(
        'assessment.candidate',
        string='Candidate',
        ondelete='cascade',
        index=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )
    
    action = fields.Char(
        string='Action',
        required=True,
        index=True,
        help='Action performed (e.g., create, status_change, review)'
    )
    
    description = fields.Text(
        string='Description',
        required=True
    )
    
    entity_type = fields.Char(string='Entity Type')
    entity_id = fields.Integer(string='Entity ID')
    
    old_value = fields.Text(string='Old Value')
    new_value = fields.Text(string='New Value')
    
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Text(string='User Agent')
    
    timestamp = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        readonly=True,
        index=True
    )
    
    @api.model
    def log_action(self, candidate_id, action, description, **kwargs):
        """Convenience method to create audit log"""
        vals = {
            'candidate_id': candidate_id,
            'action': action,
            'description': description,
            'entity_type': kwargs.get('entity_type'),
            'entity_id': kwargs.get('entity_id'),
            'old_value': kwargs.get('old_value'),
            'new_value': kwargs.get('new_value'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent'),
        }
        return self.create(vals)
    
    @api.model
    def get_candidate_timeline(self, candidate_id, limit=50):
        """Get audit timeline for a candidate"""
        logs = self.search([
            ('candidate_id', '=', candidate_id)
        ], order='timestamp desc', limit=limit)
        
        return [{
            'timestamp': log.timestamp,
            'user': log.user_id.name,
            'action': log.action,
            'description': log.description,
        } for log in logs]
