# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CommissionReportWizard(models.TransientModel):
    _name = 'commission.report.wizard'
    _description = 'Commission Report Wizard'

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    partner_id = fields.Many2one('res.partner', string='Commission Agent')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status')

    def action_generate_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commission Report'),
            'res_model': 'commission.line',
            'view_mode': 'list,form',
            'domain': self._build_domain(),
            'target': 'current',
        }

    def _build_domain(self):
        domain = []
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.state:
            domain.append(('state', '=', self.state))
        return domain
