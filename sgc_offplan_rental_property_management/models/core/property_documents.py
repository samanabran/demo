# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyDocuments(models.Model):
    _name = 'property.documents'
    _description = 'Property Documents'
    _inherit = ['file.validation.mixin']
    _order = 'document_date desc, id desc'

    property_id = fields.Many2one('property.details', string='Property', required=True)
    document_date = fields.Date(string='Document Date')
    doc_type = fields.Many2one('certificate.type', string='Document Type')
    file_name = fields.Char(string='File Name')
    document = fields.Binary(string='Document', attachment=True)
    portal_visible = fields.Boolean(string='Visible on Portal', default=False)
    doc_category = fields.Selection([('lease', 'Lease'), ('certificate', 'Certificate'), ('inspection', 'Inspection'), ('invoice', 'Invoice'), ('id', 'ID Document'), ('form_a', 'Form A'), ('title_deed', 'Title Deed'), ('passport', 'Passport'), ('noc', 'NOC (No Objection Certificate)'), ('oqood', 'Oqood (Interim Property Register)'), ('trust_escrow', 'Trust/Escrow Account Statement'), ('rera_permit', 'RERA Permit'), ('ejari', 'Ejari Certificate'), ('valuation', 'Property Valuation'), ('spa', 'Sale Purchase Agreement'), ('other', 'Other')], string='Category', default='other')
    uploaded_by_partner_id = fields.Many2one('res.partner', string='Uploaded By')
    approval_state = fields.Selection([('n_a', 'N/A'), ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], string='Approval Status', default='n_a')

    # --------------------------------------------------------------------------
    # COMPLIANCE TRACKING FIELDS
    # --------------------------------------------------------------------------
    expiry_date = fields.Date(string='Document Expiry Date',
        help="Date when this document expires (e.g., passport, visa, trade license)")
    ownership_verified = fields.Boolean(string='Ownership Verified',
        help="Document has been verified as proof of ownership")
    verified_by = fields.Many2one('res.users', string='Verified By')
    verification_date = fields.Datetime(string='Verification Date')
    document_reference_number = fields.Char(string='Reference Number',
        help="Document reference number (e.g., Title Deed number, passport number)")
    notes = fields.Text(string='Verification Notes')

    # --------------------------------------------------------------------------
    # COMPUTED EXPIRY FIELDS
    # --------------------------------------------------------------------------
    is_expired = fields.Boolean(compute='_compute_is_expired', string='Expired')
    days_until_expiry = fields.Integer(compute='_compute_is_expired', string='Days Until Expiry')

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                rec.is_expired = rec.expiry_date < today
                delta = (rec.expiry_date - today).days
                rec.days_until_expiry = -1 if rec.is_expired else delta
            else:
                rec.is_expired = False
                rec.days_until_expiry = 0

    @api.onchange('doc_category')
    def _onchange_doc_category(self):
        compliance_types = ['form_a', 'title_deed', 'passport', 'noc', 'oqood']
        if self.doc_category in compliance_types:
            self.approval_state = 'n_a'

    @api.constrains('portal_visible', 'approval_state')
    def _check_approval_state_portal_visible(self):
        for rec in self:
            if rec.approval_state != 'n_a' and not rec.portal_visible:
                raise ValidationError(_("Approval status can only be set for documents that are visible on the portal."))
