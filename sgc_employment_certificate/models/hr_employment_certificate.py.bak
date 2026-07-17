# -*- coding: utf-8 -*-

import base64
import io
import uuid

from odoo import _, api, fields, models


class HrEmploymentCertificate(models.Model):
    _name = 'hr.employment.certificate'
    _description = 'Employment Certificate'
    _order = 'issue_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('issued', 'Issued'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )

    certificate_type = fields.Selection(
        [
            ('employment', 'Employment Certificate'),
            ('noc', 'No Objection Certificate'),
        ],
        string='Certificate Type',
        required=True,
        default='employment',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
    )
    requester_user_id = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    requester_email = fields.Char(
        string='Requester Email',
        compute='_compute_requester_email',
    )
    hr_department_emails = fields.Char(
        string='HR Department Emails',
        compute='_compute_hr_department_emails',
    )
    employee_name = fields.Char(
        related='employee_id.name',
        string='Employee Name',
        readonly=True,
    )
    passport_number = fields.Char(
        string='Passport Number',
    )
    job_position = fields.Char(
        string='Job Position',
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
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    employment_duration = fields.Char(
        string='Employment Duration',
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
    issue_date = fields.Date(
        string='Issue Date',
        default=fields.Date.context_today,
        required=True,
    )
    expiry_date = fields.Date(
        string='Expiry Date',
    )
    reference_number = fields.Char(
        string='Reference Number',
        required=True,
        copy=False,
    )
    verification_token = fields.Char(
        string='Verification Token',
        readonly=True,
        copy=False,
    )
    verification_url = fields.Char(
        string='Verification URL',
        compute='_compute_verification_url',
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
    pronoun = fields.Selection(
        [
            ('Mr.', 'Mr.'),
            ('Ms.', 'Ms.'),
            ('Mrs.', 'Mrs.'),
        ],
        string='Pronoun',
        default='Mr.',
    )
    qr_image = fields.Binary(
        string='QR Code',
        compute='_compute_qr_image',
        store=True,
    )
    qr_image_data_uri = fields.Char(
        string='QR Data URI',
        compute='_compute_qr_image_data_uri',
    )

    @api.depends('verification_url')
    def _compute_qr_image(self):
        for certificate in self:
            certificate.qr_image = False
            if not certificate.verification_url:
                continue
            try:
                import qrcode
            except Exception:
                continue
            try:
                qr = qrcode.QRCode(
                    version=1,
                    box_size=6,
                    border=2,
                )
                qr.add_data(certificate.verification_url)
                qr.make(fit=True)
                img = qr.make_image(
                    fill_color="black",
                    back_color="white",
                )
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                certificate.qr_image = base64.b64encode(buffer.getvalue())
            except Exception:
                certificate.qr_image = False

    @api.depends('qr_image')
    def _compute_qr_image_data_uri(self):
        for certificate in self:
            certificate.qr_image_data_uri = False
            if not certificate.qr_image:
                continue
            data = certificate.qr_image
            if isinstance(data, str):
                data = data.encode()
            if not data:
                continue
            if data.startswith(b'\x89PNG'):
                data = base64.b64encode(data)
            elif data.startswith(b'data:image'):
                certificate.qr_image_data_uri = data.decode()
                continue
            try:
                certificate.qr_image_data_uri = (
                    'data:image/png;base64,' + data.decode()
                )
            except Exception:
                certificate.qr_image_data_uri = False

    @api.depends('verification_token')
    def _compute_verification_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url'
        )
        for certificate in self:
            if certificate.verification_token and base_url:
                certificate.verification_url = (
                    f"{base_url}/certificate/verify/"
                    f"{certificate.verification_token}"
                )
            else:
                certificate.verification_url = False

    @api.depends('requester_user_id')
    def _compute_requester_email(self):
        for certificate in self:
            certificate.requester_email = (
                certificate.requester_user_id.partner_id.email
                if certificate.requester_user_id
                else False
            )

    @api.depends('requester_user_id')
    def _compute_hr_department_emails(self):
        group = self.env.ref(
            'hr_employment_certificate.group_hr_certificate_notification',
            raise_if_not_found=False,
        )
        emails = []
        if group:
            emails = [
                partner.email
                for partner in group.users.mapped('partner_id')
                if partner.email
            ]
        hr_emails = ','.join(sorted(set(emails)))
        for certificate in self:
            certificate.hr_department_emails = hr_emails or False

    def _send_status_email(self, template_xmlid):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            return
        for certificate in self:
            if not certificate.requester_email and not certificate.hr_department_emails:
                continue
            template.sudo().send_mail(certificate.id, force_send=True)

    def action_submit_for_approval(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_mark_issued(self):
        self.write({'state': 'issued'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self._send_status_email(
            'hr_employment_certificate.mail_template_certificate_cancelled'
        )

    def action_mark_expired(self):
        self.write({'state': 'expired'})
        self._send_status_email(
            'hr_employment_certificate.mail_template_certificate_expired'
        )

    def action_remove(self):
        self.write({'active': False})

    def action_report(self):
        self.ensure_one()
        report = self.env.ref(
            'hr_employment_certificate.action_report_employment_certificate'
            if self.certificate_type == 'employment'
            else 'hr_employment_certificate.action_report_noc_certificate',
            raise_if_not_found=False,
        )
        if report:
            return report.report_action(self)
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('verification_token'):
                vals['verification_token'] = uuid.uuid4().hex
            if not vals.get('state'):
                vals['state'] = 'issued'
        return super().create(vals_list)
