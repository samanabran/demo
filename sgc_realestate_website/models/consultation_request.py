# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ConsultationRequest(models.Model):
    """Consultation Request from Website Visitors"""
    
    _name = 'sgc.realestate.consultation'
    _description = 'Consultation Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'
    
    # ===========================
    # Fields
    # ===========================
    
    name = fields.Char(
        string='Full Name',
        required=True,
        index=True,
        tracking=True,
        help='Requester full name'
    )
    
    email = fields.Char(
        string='Email',
        required=True,
        index=True,
        tracking=True,
        help='Contact email address'
    )
    
    phone = fields.Char(
        string='Phone',
        tracking=True,
        help='Contact phone number'
    )
    
    property_id = fields.Many2one(
        comodel_name='sgc.realestate.property',
        string='Property',
        index=True,
        ondelete='set null',
        tracking=True,
        help='Property of interest'
    )
    
    destination_country_id = fields.Many2one(
        comodel_name='sgc.realestate.destination.country',
        string='Destination Country',
        index=True,
        ondelete='set null',
        tracking=True,
        help='Destination country of interest'
    )
    
    message = fields.Text(
        string='Message',
        help='Additional information or questions'
    )
    
    # Status & Assignment
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('contacted', 'Contacted'),
            ('qualified', 'Qualified'),
            ('converted', 'Converted'),
            ('lost', 'Lost'),
        ],
        string='Status',
        default='new',
        required=True,
        index=True,
        tracking=True,
        help='Request status'
    )
    
    assigned_to_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        index=True,
        tracking=True,
        help='User responsible for follow-up'
    )
    
    # Metadata
    source = fields.Char(
        string='Source',
        default='Website',
        help='Lead source'
    )
    
    ip_address = fields.Char(
        string='IP Address',
        help='Visitor IP address'
    )
    
    user_agent = fields.Text(
        string='User Agent',
        help='Browser user agent string'
    )
    
    # Partner Creation
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        index=True,
        ondelete='set null',
        help='Linked contact/customer'
    )
    
    # ===========================
    # Constraints
    # ===========================
    
    @api.constrains('email')
    def _check_email(self):
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_regex, record.email):
                raise ValidationError(_('Please enter a valid email address.'))
    
    # ===========================
    # Actions
    # ===========================
    
    def action_create_partner(self):
        """Create partner from consultation request"""
        self.ensure_one()
        if self.partner_id:
            raise ValidationError(_('Partner already exists for this request.'))
        
        partner = self.env['res.partner'].create({
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'comment': self.message,
        })
        
        self.write({
            'partner_id': partner.id,
            'state': 'qualified',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_mark_contacted(self):
        """Mark as contacted"""
        self.write({'state': 'contacted'})
    
    def action_mark_qualified(self):
        """Mark as qualified"""
        self.write({'state': 'qualified'})
    
    def action_mark_converted(self):
        """Mark as converted"""
        self.write({'state': 'converted'})
    
    def action_mark_lost(self):
        """Mark as lost"""
        self.write({'state': 'lost'})
    
    # ===========================
    # Auto-assignment
    # ===========================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-assign to property agent on creation"""
        records = super().create(vals_list)
        for record in records:
            if record.property_id and record.property_id.agent_id and not record.assigned_to_id:
                record.assigned_to_id = record.property_id.agent_id
        return records
