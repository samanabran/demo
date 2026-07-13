# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CommissionProfitAnalysisWizard(models.TransientModel):
    """Wizard for generating Commission Profit Analysis Reports"""
    _name = 'commission.profit.analysis.wizard'
    _description = 'Commission Profit Analysis Report Wizard'

    # Date filters
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1)
    )
    date_to = fields.Date(
        string='To Date', 
        required=True,
        default=fields.Date.today
    )

    # Partner filter
    partner_ids = fields.Many2many(
        'res.partner',
        string='Commission Partners',
        help='Select specific partners or leave empty for all commission partners'
    )

    # Report format
    report_format = fields.Selection([
        ('pdf', 'PDF Report'),
        ('excel', 'Excel Export'),
        ('json', 'JSON Data'),
        ('both', 'Both PDF and Excel')
    ], string='Report Format', default='pdf', required=True)

    # Additional filters
    commission_state = fields.Selection([
        ('all', 'All States'),
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('processed', 'Processed'), 
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Commission State', default='all', required=True)
    
    # Analysis options
    include_categories = fields.Boolean(
        string='Include Category Analysis',
        default=True,
        help='Include detailed breakdown by commission categories'
    )
    
    show_profit_impact = fields.Boolean(
        string='Show Profit Impact Analysis',
        default=True,
        help='Include profit impact calculations and margins'
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError(_('From Date cannot be greater than To Date.'))

    def action_generate_report(self):
        """Generate commission profit analysis report using Python generator"""
        self.ensure_one()
        
        try:
            # Prepare wizard data for report generator
            wizard_data = {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'partner_ids': self.partner_ids.ids if self.partner_ids else [],
                'commission_state': self.commission_state,
                'report_format': self.report_format,
                'include_categories': self.include_categories,
                'show_profit_impact': self.show_profit_impact,
            }

            # Get the Python report generator
            report_generator = self.env['commission.report.generator']
            
            # Generate report based on format
            if self.report_format == 'pdf':
                report_data = report_generator.generate_profit_analysis_report(wizard_data, 'pdf')
                return self._download_report(report_data)
            elif self.report_format == 'excel':
                report_data = report_generator.generate_profit_analysis_report(wizard_data, 'excel')
                return self._download_report(report_data)
            elif self.report_format == 'json':
                report_data = report_generator.generate_profit_analysis_report(wizard_data, 'json')
                return self._download_report(report_data)
            elif self.report_format == 'both':
                # Generate both formats
                pdf_data = report_generator.generate_profit_analysis_report(wizard_data, 'pdf')
                excel_data = report_generator.generate_profit_analysis_report(wizard_data, 'excel')
                return self._download_both_reports(pdf_data, excel_data)
                
        except Exception as e:
            raise ValidationError(_("Error generating profit analysis report: %s") % str(e))

    def _download_report(self, report_data):
        """Download a single report"""
        attachment = self.env['ir.attachment'].create({
            'name': report_data['filename'],
            'type': 'binary',
            'datas': report_data['content'],
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': report_data['mimetype']
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _download_both_reports(self, pdf_data, excel_data):
        """Download both PDF and Excel reports"""
        # Create attachments for both reports
        pdf_attachment = self.env['ir.attachment'].create({
            'name': pdf_data['filename'],
            'type': 'binary',
            'datas': pdf_data['content'],
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': pdf_data['mimetype']
        })
        
        excel_attachment = self.env['ir.attachment'].create({
            'name': excel_data['filename'],
            'type': 'binary',
            'datas': excel_data['content'],
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': excel_data['mimetype']
        })
        
        # Return action to show both downloads
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Reports Generated"),
                'message': _("Both PDF and Excel reports have been generated. Download links: ") +
                          f'<a href="/web/content/{pdf_attachment.id}?download=true">PDF</a> | ' +
                          f'<a href="/web/content/{excel_attachment.id}?download=true">Excel</a>',
                'type': 'success',
                'sticky': True,
            }
        }

    def action_preview_data(self):
        """Preview report data before generating full report"""
        try:
            wizard_data = {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'partner_ids': self.partner_ids.ids if self.partner_ids else [],
                'commission_state': self.commission_state,
            }

            # Get the Python report generator and generate JSON preview
            report_generator = self.env['commission.report.generator']
            report_data = report_generator.generate_profit_analysis_report(wizard_data, 'json')
            
            # Create temporary attachment for preview
            attachment = self.env['ir.attachment'].create({
                'name': 'profit_analysis_preview.json',
                'type': 'binary',
                'datas': report_data['content'],
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/json'
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
            
        except Exception as e:
            raise ValidationError(_("Error previewing data: %s") % str(e))