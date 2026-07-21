# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertySubProject(models.Model):
    _name = 'property.sub.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Sub Project'
    _order = 'name'

    name = fields.Char(string='Sub Project Name', required=True)
    code = fields.Char(string='Sub Project Code')
    project_id = fields.Many2one('property.project', string='Project', required=True)
    description = fields.Html(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    image_1920 = fields.Binary(string='Image', attachment=True)
    image_512 = fields.Binary(string='Image (512px)', compute='_compute_images', store=True, attachment=True)
    image_256 = fields.Binary(string='Image (256px)', compute='_compute_images', store=True, attachment=True)
    property_count = fields.Integer(string='Properties', compute='_compute_property_count')

    @api.depends('image_1920')
    def _compute_images(self):
        for rec in self:
            rec.image_512 = rec.image_1920
            rec.image_256 = rec.image_1920

    @api.depends()
    def _compute_property_count(self):
        for rec in self:
            rec.property_count = self.env['property.details'].search_count(
                [('sub_project_id', '=', rec.id)]
            )

    def action_view_properties(self):
        return {
            "name": "Properties",
            "type": "ir.actions.act_window",
            "domain": [("sub_project_id", "=", self.id)],
            "view_mode": "kanban,list,form",
            "context": {"create": False, "default_sub_project_id": self.id},
            "res_model": "property.details",
            "target": "current",
        }
