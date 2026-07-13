# -*- coding: utf-8 -*-
from odoo import models


class CommissionPythonGenerator(models.AbstractModel):
    _name = 'report.deals_management.commission_python_generator'
    _description = 'Commission Python Report Generator'

    def generate_report(self, docids, data=None):
        """Base report generator - can be overridden by specific reports."""
        return {
            'doc_ids': docids,
            'doc_model': 'commission.line',
            'docs': self.env['commission.line'].browse(docids) if docids else [],
            'data': data or {},
        }
