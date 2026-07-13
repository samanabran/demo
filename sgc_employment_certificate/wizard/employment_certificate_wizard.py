# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class HrEmploymentCertificateWizard(models.TransientModel):
    _name = 'hr.employment.certificate.wizard'
    _description = 'Employment Certificate Wizard'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        readonly=True,
    )
    employee_name = fields.Char(
        string='Employee Name',
        related='employee_id.name',
        readonly=True,
    )
    passport_number = fields.Char(
        string='Passport Number',
    )
    job_position = fields.Char(
        string='Job Position',
    )
    pronoun = fields.Selection(
        [
            ('Mr.', 'Mr.'),
            ('Ms.', 'Ms.'),
            ('Mrs.', 'Mrs.'),
        ],
        string='Pronoun',
        default='Mr.',
    )
    employment_status = fields.Selection(
        [
            ('current', 'Current Employee'),
            ('resigned', 'Resigned/Former Employee'),
        ],
        string='Employment Status',
        default='current',
        required=True,
    )
    join_date = fields.Date(
        string='Join Date',
    )
    end_date = fields.Date(
        string='End Date',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    gross_salary = fields.Monetary(
        string='Gross Monthly Salary',
        currency_field='currency_id',
    )
    last_salary = fields.Monetary(
        string='Last Drawn Salary',
        currency_field='currency_id',
    )
    show_salary = fields.Boolean(
        string='Show Salary on Certificate',
        default=False,
    )
    issue_date = fields.Date(
        string='Issue Date',
        default=fields.Date.context_today,
        required=True,
    )
    expiry_date = fields.Date(
        string='Expiry Date',
    )
    employment_duration = fields.Char(
        string='Employment Duration',
        readonly=True,
    )
    reference_number = fields.Char(
        string='Reference Number',
        readonly=True,
    )
    purpose = fields.Char(
        string='Purpose',
    )
    recipient_name = fields.Char(
        string='Recipient Name',
    )
    recipient_title = fields.Char(
        string='Recipient Title',
    )
    recipient_organization = fields.Char(
        string='Recipient Organization',
    )
    signatory_name = fields.Char(
        string='Signatory Name',
    )
    signatory_title = fields.Char(
        string='Signatory Title',
    )
    digital_signature = fields.Binary(
        string='Digital Signature',
        attachment=True,
    )

    def action_print_certificate(self):
        self.ensure_one()
        certificate = self.env['hr.employment.certificate'].create({
            'employee_id': self.employee_id.id,
            'passport_number': self.passport_number,
            'job_position': self.job_position,
            'pronoun': self.pronoun,
            'employment_status': self.employment_status,
            'join_date': self.join_date,
            'end_date': self.end_date,
            'gross_salary': self.gross_salary if self.show_salary else 0,
            'last_salary': self.last_salary if self.show_salary else 0,
            'show_salary': self.show_salary,
            'currency_id': self.currency_id.id,
            'issue_date': self.issue_date,
            'expiry_date': self.expiry_date,
            'employment_duration': self.employment_duration,
            'purpose': self.purpose,
            'recipient_name': self.recipient_name,
            'recipient_title': self.recipient_title,
            'recipient_organization': self.recipient_organization,
            'signatory_name': self.signatory_name,
            'signatory_title': self.signatory_title,
            'digital_signature': self.digital_signature,
            'certificate_type': 'employment',
        })
        return certificate.action_report()

    def action_print_noc(self):
        self.ensure_one()
        certificate = self.env['hr.employment.certificate'].create({
            'employee_id': self.employee_id.id,
            'passport_number': self.passport_number,
            'job_position': self.job_position,
            'pronoun': self.pronoun,
            'employment_status': self.employment_status,
            'join_date': self.join_date,
            'end_date': self.end_date,
            'currency_id': self.currency_id.id,
            'issue_date': self.issue_date,
            'expiry_date': self.expiry_date,
            'employment_duration': self.employment_duration,
            'purpose': self.purpose,
            'recipient_name': self.recipient_name,
            'recipient_title': self.recipient_title,
            'recipient_organization': self.recipient_organization,
            'signatory_name': self.signatory_name,
            'signatory_title': self.signatory_title,
            'digital_signature': self.digital_signature,
            'certificate_type': 'noc',
        })
        return certificate.action_report()
