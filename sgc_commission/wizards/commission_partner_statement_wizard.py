# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CommissionPartnerStatementWizard(models.TransientModel):
    _name = 'commission.partner.statement.wizard'
    _description = 'Commission Partner Statement Wizard'

    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    partner_ids = fields.Many2many('res.partner', string='Partners')
    project_ids = fields.Many2many('project.project', string='Projects')
    commission_state = fields.Selection([
        ('', 'All'),
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Commission Status')
    report_format = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ], string='Report Format', default='pdf')

    def action_generate_report(self):
        self.ensure_one()
        if self.report_format == 'excel':
            return self._generate_excel_report()
        return self._generate_pdf_report()

    def _generate_pdf_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'deals_management.commission_partner_statement_report',
            'report_type': 'qweb-pdf',
            'data': self._get_report_data(),
        }

    def _generate_excel_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/deals_management.commission_partner_statement_report/%s' % self.id,
            'target': 'new',
        }

    def _get_report_data(self):
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'commission_state': self.commission_state or 'all',
            'partner_ids': self.partner_ids.ids,
            'project_ids': self.project_ids.ids,
        }

    def _get_commission_data(self):
        domain = [('create_date', '>=', self.date_from.isoformat()),
                  ('create_date', '<=', self.date_to.isoformat())]
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.commission_state:
            domain.append(('state', '=', self.commission_state))
        lines = self.env['commission.line'].search(domain)
        result = []
        for line in lines:
            result.append({
                'partner_name': line.partner_id.name or '',
                'sale_order': line.sale_order_id.name or '',
                'commission_amount': line.commission_amount or 0.0,
                'state': line.state or 'draft',
                'date': line.create_date,
            })
        return result
