from odoo import models, api


class CommissionPartnerStatementReport(models.AbstractModel):
    _name = 'report.deals_management.commission_partner_statement_report'
    _description = 'Commission Partner Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prepare data for the PDF report template with comprehensive debugging
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info("PDF REPORT GENERATION DEBUG")
        _logger.info("Docids: %s", docids)
        _logger.info("Data parameter: %s", data)
        
        try:
            # Initialize default data structure
            report_context = {
                'report_data': [],
                'date_from': '',
                'date_to': '',
                'commission_state': 'all',
                'partner_names': 'No Partners Selected',
                'project_names': 'All Projects',
                'error_message': 'No data available',
                'record_count': 0,
                'has_data': False
            }

            # Get wizard record
            wizard = None
            if docids:
                wizards = self.env['commission.partner.statement.wizard'].browse(docids)
                if wizards.exists():
                    wizard = wizards[0]
                    _logger.info("Found wizard ID: %s", wizard.id)
                    
                    # Get commission data from wizard
                    report_data = wizard._get_commission_data()
                    _logger.info("Retrieved %s records from wizard", len(report_data))
                    
                    # Log sample data
                    if report_data:
                        sample = report_data[0]
                        _logger.info("Sample record keys: %s", list(sample.keys()))
                        _logger.info("Sample record: %s", sample)
                    
                    # Update report context with wizard data
                    report_context.update({
                        'report_data': report_data,
                        'date_from': wizard.date_from.strftime('%d/%m/%Y') if wizard.date_from else '',
                        'date_to': wizard.date_to.strftime('%d/%m/%Y') if wizard.date_to else '',
                        'commission_state': wizard.commission_state,
                        'partner_names': ', '.join(wizard.partner_ids.mapped('name')) if wizard.partner_ids else 'All Partners',
                        'error_message': None if report_data else 'No commission data found',
                        'record_count': len(report_data),
                        'has_data': bool(report_data)
                    })
                    
                    _logger.info("Report context prepared with %s records", len(report_data))
                else:
                    _logger.error("No wizard found for docids: %s", docids)
            else:
                _logger.error("No docids provided to report")

            # Override with data parameter if provided
            if data and isinstance(data, dict):
                _logger.info("Updating context with data parameter")
                report_context.update(data)
                
            # Final debug output
            _logger.info("Final report context keys: %s", list(report_context.keys()))
            _logger.info("Final record count: %s", report_context.get('record_count', 0))

            return {
                'doc_ids': docids,
                'doc_model': 'commission.partner.statement.wizard',
                'docs': [wizard] if wizard else [],
                'data': report_context,
                'wizard': wizard,
                # Make data accessible directly in template
                **report_context
            }
            
        except Exception as e:
            _logger.error("Error in report generation: %s", str(e))
            import traceback
            _logger.error("Traceback: %s", traceback.format_exc())
            
            # Return error data for debugging
            return {
                'doc_ids': docids,
                'doc_model': 'commission.partner.statement.wizard',
                'docs': [],
                'data': {
                    'report_data': [],
                    'date_from': '',
                    'date_to': '',
                    'partner_names': 'Error in Data Generation',
                    'commission_state': 'all',
                    'error_message': f'Report generation error: {str(e)}',
                    'record_count': 0,
                    'has_data': False
                },
                'error': str(e)
            }