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
    doc_category = fields.Selection([('lease', 'Lease'), ('certificate', 'Certificate'), ('inspection', 'Inspection'), ('invoice', 'Invoice'), ('id', 'ID Document'), ('other', 'Other')], string='Category', default='other')
    uploaded_by_partner_id = fields.Many2one('res.partner', string='Uploaded By')
    approval_state = fields.Selection([('n_a', 'N/A'), ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], string='Approval Status', default='n_a')

    @api.constrains('portal_visible', 'approval_state')
    def _check_approval_state_portal_visible(self):
        for rec in self:
            if rec.approval_state != 'n_a' and not rec.portal_visible:
                raise ValidationError(_("Approval status can only be set for documents that are visible on the portal."))
