# -*- coding: utf-8 -*-
from odoo import models


class CommissionReport(models.AbstractModel):
    _name = 'report.deals_management.commission_report'
    _description = 'Commission Report'

    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'commission.line',
            'docs': self.env['commission.line'].browse(docids) if docids else [],
            'data': data or {},
        }
