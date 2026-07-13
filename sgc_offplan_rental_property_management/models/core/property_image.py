# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyImage(models.Model):
    """Multi-image gallery for properties, projects, and sub-projects."""
    _name = 'property.image'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Image'
    _order = 'sequence, id'

    name = fields.Char(string='Label')
    sequence = fields.Integer(string='Sequence', default=10)
    image_1920 = fields.Binary(string='Image (1920px)', attachment=True, required=True)
    image_1024 = fields.Binary(string='Image (1024px)', compute='_compute_images', store=True, attachment=True)
    image_512 = fields.Binary(string='Image (512px)', compute='_compute_images', store=True, attachment=True)
    image_256 = fields.Binary(string='Image (256px)', compute='_compute_images', store=True, attachment=True)
    active = fields.Boolean(string='Active', default=True)

    # Polymorphic link to parent records
    property_id = fields.Many2one('property.details', string='Property', ondelete='cascade', index=True)
    project_id = fields.Many2one('property.project', string='Project', ondelete='cascade', index=True)
    sub_project_id = fields.Many2one('property.sub.project', string='Sub Project', ondelete='cascade', index=True)

    @api.depends('image_1920')
    def _compute_images(self):
        for rec in self:
            rec.image_1024 = rec.image_1920
            rec.image_512 = rec.image_1920
            rec.image_256 = rec.image_1920


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    image_ids = fields.One2many('property.image', 'property_id', string='Gallery Images',
                                copy=True, help='Additional property images for gallery display')


class PropertyProject(models.Model):
    _inherit = 'property.project'

    image_ids = fields.One2many('property.image', 'project_id', string='Gallery Images',
                                copy=True, help='Additional project images for gallery display')


class PropertySubProject(models.Model):
    _inherit = 'property.sub.project'

    image_ids = fields.One2many('property.image', 'sub_project_id', string='Gallery Images',
                                copy=True, help='Additional sub-project images for gallery display')
