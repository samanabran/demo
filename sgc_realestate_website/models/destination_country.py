# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DestinationCountry(models.Model):
    """Destination Country for Real Estate Properties"""
    
    _name = 'sgc.realestate.destination.country'
    _description = 'Destination Country'
    _inherit = ['mail.thread', 'website.published.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'
    
    # ===========================
    # Fields
    # ===========================
    
    name = fields.Char(
        string='Country Name',
        required=True,
        translate=True,
        index=True,
        tracking=True,
        help='Country name for display'
    )
    
    code = fields.Char(
        string='Country Code',
        required=True,
        size=2,
        index=True,
        help='ISO 3166-1 alpha-2 country code (e.g., US, GB, AE)'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        index=True,
        help='Display order'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    # Description & Details
    description = fields.Html(
        string='Description',
        translate=True,
        sanitize=True,
        help='Detailed information about this destination'
    )
    
    short_description = fields.Text(
        string='Short Description',
        translate=True,
        help='Brief overview (max 300 chars)'
    )
    
    # Images
    image_1920 = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920,
        help='Country/destination image'
    )
    
    image_512 = fields.Image(
        related='image_1920',
        max_width=512,
        max_height=512,
        store=True
    )
    
    image_256 = fields.Image(
        related='image_1920',
        max_width=256,
        max_height=256,
        store=True
    )
    
    # Statistics
    property_count = fields.Integer(
        string='Properties',
        compute='_compute_property_count',
        help='Number of properties in this country'
    )
    
    # Website & SEO
    website_url = fields.Char(
        string='Website URL',
        compute='_compute_website_url',
        help='Full URL to country page'
    )
    
    # ===========================
    # Computed Fields
    # ===========================
    
    def _compute_property_count(self):
        """Count available properties for this country"""
        for record in self:
            record.property_count = self.env['sgc.realestate.property'].search_count([
                ('destination_country_id', '=', record.id),
                ('website_published', '=', True),
                ('active', '=', True),
            ])
    
    def _compute_website_url(self):
        """Generate URL to country listing page"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.id and record.name:
                slug = record.name.lower().replace(' ', '-')[:50]
                record.website_url = f"{base_url}/properties/country/{slug}-{record.id}"
            else:
                record.website_url = False
    
    # ===========================
    # Constraints
    # ===========================
    
    _sql_constraints = [
        models.Constraint('UNIQUE(code)', 'Country code must be unique!'),
    ]
    
    @api.constrains('code')
    def _check_code(self):
        """Ensure country code is uppercase and 2 chars"""
        for record in self:
            if record.code:
                if len(record.code) != 2:
                    raise ValidationError(_('Country code must be exactly 2 characters.'))
                if record.code != record.code.upper():
                    record.code = record.code.upper()
    
    # ===========================
    # Actions
    # ===========================
    
    def action_view_properties(self):
        """Open properties for this country"""
        self.ensure_one()
        return {
            'name': _('Properties in %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sgc.realestate.property',
            'view_mode': 'kanban,tree,form',
            'domain': [('destination_country_id', '=', self.id)],
            'context': {'default_destination_country_id': self.id},
        }
