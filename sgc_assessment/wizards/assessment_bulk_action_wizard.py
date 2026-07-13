# -*- coding: utf-8 -*-
from odoo import models, fields


class AssessmentBulkActionWizard(models.TransientModel):
    _name = 'assessment.bulk.action.wizard'
    _description = 'Bulk Action on Candidates'

    action_type = fields.Selection([
        ('status', 'Update Status'),
        ('shortlist', 'Shortlist'),
        ('reject', 'Reject'),
    ], string='Action', required=True)
    
    new_status = fields.Selection([
        ('submitted', 'Submitted'),
        ('ai_scored', 'AI Scored'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
    ], string='New Status')

    def action_apply(self):
        """Apply bulk action"""
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        candidates = self.env['assessment.candidate'].browse(active_ids)
        
        if self.action_type == 'status' and self.new_status:
            candidates.write({'status': self.new_status})
        elif self.action_type == 'shortlist':
            candidates.write({'status': 'shortlisted'})
        elif self.action_type == 'reject':
            candidates.write({'status': 'rejected'})
        
        return {'type': 'ir.actions.act_window_close'}
