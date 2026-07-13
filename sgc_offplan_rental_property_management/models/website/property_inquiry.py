# -*- coding: utf-8 -*-
from odoo import models, fields


class PropertyWebsiteInquiry(models.Model):
    _name = 'property.website.inquiry'
    _description = 'Property Website Inquiry'
    _order = 'create_date desc'

    property_id = fields.Many2one('property.details', string='Property', required=True, ondelete='cascade')
    lead_id = fields.Many2one('crm.lead', string='CRM Lead', ondelete='set null')
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    message = fields.Text(string='Message')
    property_url = fields.Char(string='Property URL')
