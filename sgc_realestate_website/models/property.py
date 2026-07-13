# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SGCProperty(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    """Website-facing real estate property listing."""
    _name = 'sgc.realestate.property'
    _description = 'Real Estate Property'
    _order = 'sequence, id desc'
    _rec_name = 'title'

    name = fields.Char(string='Internal Reference', required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('sgc.realestate.property') or 'New')
    title = fields.Char(string='Title', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Html(string='Description', translate=True)
    property_type = fields.Selection([
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('townhouse', 'Townhouse'),
        ('penthouse', 'Penthouse'),
        ('commercial', 'Commercial'),
        ('land', 'Land'),
    ], string='Property Type', default='apartment', required=True)
    sale_lease = fields.Selection([
        ('for_sale', 'For Sale'),
        ('for_rent', 'For Rent'),
    ], string='Sale/Rent', default='for_sale', required=True)
    destination_country_id = fields.Many2one('sgc.realestate.destination.country', string='Country')
    city = fields.Char(string='City', translate=True)
    address = fields.Text(string='Address')
    postal_code = fields.Char(string='Postal Code')
    price = fields.Monetary(string='Price', currency_field='currency_id')
    price_per_sqm = fields.Monetary(string='Price per m²', compute='_compute_price_per_sqm',
                                    store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    agent_id = fields.Many2one('res.partner', string='Agent',
                               domain=[('is_company', '=', False)])

    # Specifications
    bedrooms = fields.Integer(string='Bedrooms', default=0)
    bathrooms = fields.Integer(string='Bathrooms', default=0)
    area = fields.Float(string='Area (m²)')
    lot_size = fields.Float(string='Lot Size (m²)')
    year_built = fields.Integer(string='Year Built')
    latitude = fields.Float(string='Latitude', digits=(9, 6))
    longitude = fields.Float(string='Longitude', digits=(9, 6))

    # Status
    status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
    ], string='Status', default='available', required=True)
    active = fields.Boolean(string='Active', default=True)
    website_published = fields.Boolean(string='Published on Website', default=False)
    website_url = fields.Char(string='Website URL')

    # Media
    image_1920 = fields.Binary(string='Image (1920px)', attachment=True)
    image_1024 = fields.Binary(string='Image (1024px)', compute='_compute_images', store=True)
    image_512 = fields.Binary(string='Image (512px)', compute='_compute_images', store=True)
    image_256 = fields.Binary(string='Image (256px)', compute='_compute_images', store=True)
    image_ids = fields.One2many('sgc.realestate.property.image', 'property_id', string='Gallery Images')
    feature_ids = fields.Many2many('sgc.realestate.property.feature', string='Features')

    # Gated content (lead-gen downloads)
    brochure = fields.Binary(string='Brochure (PDF)', attachment=True)
    brochure_filename = fields.Char(string='Brochure Filename')
    floor_plan = fields.Binary(string='Floor Plan (PDF)', attachment=True)
    floor_plan_filename = fields.Char(string='Floor Plan Filename')

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    @api.depends('image_1920')
    def _compute_images(self):
        for rec in self:
            rec.image_1024 = rec.image_1920
            rec.image_512 = rec.image_1920
            rec.image_256 = rec.image_1920

    @api.depends('price', 'area')
    def _compute_price_per_sqm(self):
        for rec in self:
            rec.price_per_sqm = (rec.price / rec.area) if rec.area else 0.0

    def toggle_website_published(self):
        self.website_published = not self.website_published


class SGCPropertyImage(models.Model):
    """Gallery images for a property."""
    _name = 'sgc.realestate.property.image'
    _description = 'Property Image'
    _order = 'sequence, id'

    name = fields.Char(string='Label')
    sequence = fields.Integer(string='Sequence', default=10)
    property_id = fields.Many2one('sgc.realestate.property', string='Property',
                                  ondelete='cascade')
    image_1920 = fields.Binary(string='Image (1920px)', attachment=True)
    image_1024 = fields.Binary(string='Image (1024px)', compute='_compute_images', store=True)
    image_512 = fields.Binary(string='Image (512px)', compute='_compute_images', store=True)
    image_256 = fields.Binary(string='Image (256px)', compute='_compute_images', store=True)

    @api.depends('image_1920')
    def _compute_images(self):
        for rec in self:
            rec.image_1024 = rec.image_1920
            rec.image_512 = rec.image_1920
            rec.image_256 = rec.image_1920


class SGCPropertyFeature(models.Model):
    """Features/amenities for a property."""
    _name = 'sgc.realestate.property.feature'
    _description = 'Property Feature'
    _order = 'name'

    name = fields.Char(string='Feature', required=True, translate=True)
    color = fields.Integer(string='Color Index')
    property_ids = fields.Many2many('sgc.realestate.property', string='Properties')
