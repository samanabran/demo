# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certificate_count = fields.Integer(
        string='Certificate Count',
        compute='_compute_certificate_count',
    )

    def _compute_certificate_count(self):
        """Compute the number of certificates issued for this employee."""
        for employee in self:
            # Count certificates from ir.attachment or just set to 0
            employee.certificate_count = 0

    def action_print_employment_certificate(self):
        """Open wizard to configure and print employment certificate."""
        self.ensure_one()
        return {
            'name': 'Employment Certificate',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employment.certificate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
            },
        }
