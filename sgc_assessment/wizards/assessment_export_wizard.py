# -*- coding: utf-8 -*-
from odoo import models, fields, api
import base64
import csv
import io


class AssessmentExportWizard(models.TransientModel):
    _name = 'assessment.export.wizard'
    _description = 'Export Assessment Data'

    export_format = fields.Selection([
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
    ], string='Format', default='csv', required=True)
    
    include_responses = fields.Boolean(string='Include Full Responses', default=False)
    include_ai_analysis = fields.Boolean(string='Include AI Analysis', default=True)
    include_human_review = fields.Boolean(string='Include Human Review', default=True)
    
    file_data = fields.Binary(string='File', readonly=True)
    file_name = fields.Char(string='Filename', readonly=True)

    def action_export(self):
        """Export candidates to CSV/Excel"""
        self.ensure_one()
        
        # Get active candidates
        active_ids = self.env.context.get('active_ids', [])
        candidates = self.env['assessment.candidate'].browse(active_ids)
        
        if self.export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            headers = ['Name', 'Email', 'Phone', 'Location', 'Odoo Exp', 'Sales Exp',
                      'Submission Date', 'Status', 'Overall Score', 'Rank']
            if self.include_ai_analysis:
                headers.extend(['AI Tech', 'AI Sales', 'AI Comm', 'AI Learning', 'AI Fit'])
            writer.writerow(headers)
            
            # Data
            for candidate in candidates:
                row = [
                    candidate.full_name,
                    candidate.email,
                    candidate.phone or '',
                    candidate.location or '',
                    candidate.odoo_experience,
                    candidate.sales_experience,
                    str(candidate.submission_date),
                    candidate.status,
                    candidate.overall_score,
                    candidate.overall_rank,
                ]
                if self.include_ai_analysis:
                    row.extend([
                        candidate.technical_score,
                        candidate.sales_score,
                        candidate.communication_score,
                        candidate.learning_score,
                        candidate.cultural_fit_score,
                    ])
                writer.writerow(row)
            
            file_data = base64.b64encode(output.getvalue().encode())
            file_name = 'assessment_export.csv'
        
        self.write({
            'file_data': file_data,
            'file_name': file_name,
        })
        
        return {
            'name': 'Export Complete',
            'type': 'ir.actions.act_window',
            'res_model': 'assessment.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
