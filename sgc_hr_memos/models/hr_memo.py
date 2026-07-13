# -*- coding: utf-8 -*-

import base64
import io
import uuid

from odoo import _, api, fields, models


class HrMemo(models.Model):
    _name = 'hr.memo'
    _description = 'HR Memo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'memo_date desc, id desc'

    name = fields.Char(
        string='Title',
        required=True,
        tracking=True,
    )
    memo_body = fields.Html(
        string='Message Body',
        required=True,
        sanitize=False,
    )
    memo_body_print = fields.Html(
        string='Memo Body (Print)',
        compute='_compute_memo_body_print',
        sanitize=False,
    )
    memo_date = fields.Date(
        string='Memo Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    prepared_by = fields.Many2one(
        'res.users',
        string='Prepared By',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )

    # --- Approval tracking ---
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        tracking=True,
    )
    approved_date = fields.Datetime(
        string='Approved Date',
        readonly=True,
    )
    rejected_by = fields.Many2one(
        'res.users',
        string='Rejected By',
        readonly=True,
        tracking=True,
    )
    cancelled_by = fields.Many2one(
        'res.users',
        string='Cancelled By',
        readonly=True,
        tracking=True,
    )

    # --- Reference number ---
    memo_reference = fields.Char(
        string='Memo Reference',
        readonly=True,
        copy=False,
    )

    # --- Digital Signature ---
    digital_signature = fields.Binary(
        string='Digital Signature',
        attachment=True,
    )
    signatory_name = fields.Char(
        string='Signatory Name',
    )
    signatory_title = fields.Char(
        string='Signatory Title',
    )

    # --- QR Code / Verification ---
    verification_token = fields.Char(
        string='Verification Token',
        readonly=True,
        copy=False,
    )
    verification_url = fields.Char(
        string='Verification URL',
        compute='_compute_verification_url',
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

    # -------------------------------------------------------------------------
    # COMPUTED METHODS
    # -------------------------------------------------------------------------

    @api.depends('memo_body')
    def _compute_memo_body_print(self):
        for memo in self:
            body = memo.memo_body or ''
            if isinstance(body, bytes):
                body = body.decode('utf-8', errors='ignore')
            body = body.replace('Â&nbsp;', '&nbsp;')
            body = body.replace('\u00a0', ' ')
            body = body.replace('\xa0', ' ')
            body = body.replace('Â', '')
            memo.memo_body_print = body

    @api.depends('verification_token')
    def _compute_verification_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for memo in self:
            if memo.verification_token and base_url:
                memo.verification_url = f"{base_url}/memo/verify/{memo.verification_token}"
            else:
                memo.verification_url = False

    @api.depends('verification_url')
    def _compute_qr_image(self):
        for memo in self:
            memo.qr_image = False
            if not memo.verification_url:
                continue
            try:
                import qrcode
            except ImportError:
                continue
            try:
                qr = qrcode.QRCode(version=1, box_size=6, border=2)
                qr.add_data(memo.verification_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                memo.qr_image = base64.b64encode(buffer.getvalue())
            except Exception:
                memo.qr_image = False

    @api.depends('qr_image')
    def _compute_qr_image_data_uri(self):
        for memo in self:
            if memo.qr_image:
                data = memo.qr_image
                if isinstance(data, bytes):
                    data = data.decode('ascii')
                memo.qr_image_data_uri = 'data:image/png;base64,' + data
            else:
                memo.qr_image_data_uri = False

    # -------------------------------------------------------------------------
    # CRUD OVERRIDES
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('verification_token'):
                vals['verification_token'] = uuid.uuid4().hex
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        for memo in self:
            vals = {
                'state': 'approved',
                'approved_by': self.env.uid,
                'approved_date': fields.Datetime.now(),
            }
            if not memo.memo_reference:
                vals['memo_reference'] = self.env['ir.sequence'].next_by_code('hr.memo') or '/'
            memo.write(vals)

    def action_reject(self):
        self.write({
            'state': 'rejected',
            'rejected_by': self.env.uid,
        })

    def action_cancel(self):
        self.write({
            'state': 'cancelled',
            'cancelled_by': self.env.uid,
        })

    def action_reset_to_draft(self):
        self.write({
            'state': 'draft',
            'approved_by': False,
            'approved_date': False,
            'rejected_by': False,
            'cancelled_by': False,
        })
