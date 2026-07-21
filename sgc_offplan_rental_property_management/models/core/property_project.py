# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyProject(models.Model):
    _name = 'property.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Project'
    _order = 'name'

    name = fields.Char(string='Project Name', required=True, tracking=True)
    code = fields.Char(string='Project Code')
    region_id = fields.Many2one('property.region', string='Region')
    description = fields.Html(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    image_1920 = fields.Binary(string='Image', attachment=True)
    image_512 = fields.Binary(string='Image (512px)', compute='_compute_images', store=True, attachment=True)
    image_256 = fields.Binary(string='Image (256px)', compute='_compute_images', store=True, attachment=True)

    # State tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Property counts by state
    property_count = fields.Integer(string='Properties', compute='_compute_property_counts')
    available_count = fields.Integer(string='Available', compute='_compute_property_counts')
    booked_count = fields.Integer(string='Booked', compute='_compute_property_counts')
    sold_count = fields.Integer(string='Sold', compute='_compute_property_counts')
    rented_count = fields.Integer(string='Rented', compute='_compute_property_counts')

    # Booking count (property.vendor records across all units in this project)
    booking_count = fields.Integer(string='Bookings', compute='_compute_booking_count')

    # Sub-project count (for smart button navigation)
    sub_project_count = fields.Integer(string='Sub Projects', compute='_compute_sub_project_count')

    @api.depends('image_1920')
    def _compute_images(self):
        for rec in self:
            rec.image_512 = rec.image_1920
            rec.image_256 = rec.image_1920

    @api.depends()
    def _compute_property_counts(self):
        """Compute property counts broken down by state for the project."""
        PropertyDetails = self.env['property.details']
        for rec in self:
            domain = [('project_id', '=', rec.id)]
            rec.property_count = PropertyDetails.search_count(domain)
            rec.available_count = PropertyDetails.search_count(
                domain + [('state', '=', 'available')]
            )
            rec.booked_count = PropertyDetails.search_count(
                domain + [('state', '=', 'booked')]
            )
            rec.sold_count = PropertyDetails.search_count(
                domain + [('state', '=', 'sold')]
            )
            rec.rented_count = PropertyDetails.search_count(
                domain + [('state', '=', 'rented')]
            )

    @api.depends()
    def _compute_booking_count(self):
        """Number of property.vendor booking records across all project units."""
        for rec in self:
            property_ids = self.env['property.details'].search(
                [('project_id', '=', rec.id)]
            ).ids
            rec.booking_count = self.env['property.vendor'].search_count(
                [('property_id', 'in', property_ids)]
            )

    @api.depends()
    def _compute_sub_project_count(self):
        """Number of sub-projects linked to this project."""
        for rec in self:
            rec.sub_project_count = self.env['property.sub.project'].search_count(
                [('project_id', '=', rec.id)]
            )

    # -------------------------------------------------------------------------
    # Smart-button actions
    # -------------------------------------------------------------------------

    def action_view_sub_projects(self):
        self.ensure_one()
        return {
            "name": "Sub Projects",
            "type": "ir.actions.act_window",
            "domain": [("project_id", "=", self.id)],
            "view_mode": "kanban,list,form",
            "context": {"create": False, "default_project_id": self.id},
            "res_model": "property.sub.project",
            "target": "current",
        }

    def action_view_properties(self):
        self.ensure_one()
        return {
            "name": "Properties",
            "type": "ir.actions.act_window",
            "domain": [("project_id", "=", self.id)],
            "view_mode": "kanban,list,form",
            "context": {"create": False, "default_project_id": self.id},
            "res_model": "property.details",
            "target": "current",
        }

    def action_view_bookings(self):
        self.ensure_one()
        property_ids = self.env['property.details'].search(
            [('project_id', '=', self.id)]
        ).ids
        return {
            "name": "Bookings",
            "type": "ir.actions.act_window",
            "domain": [("property_id", "in", property_ids)],
            "view_mode": "tree,form",
            "res_model": "property.vendor",
            "target": "current",
        }

    def action_open_booking_wizard(self):
        """Open the booking wizard pre-filled with this project's context."""
        self.ensure_one()
        return {
            'name': _('Create Booking'),
            'type': 'ir.actions.act_window',
            'res_model': 'booking.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
            },
        }

    # -------------------------------------------------------------------------
    # State transitions
    # -------------------------------------------------------------------------

    def action_start(self):
        """Mark project as in-progress (selling/leasing active)."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft projects can be started.'))
            rec.state = 'in_progress'
        return True

    def action_complete(self):
        """Mark project as completed."""
        for rec in self:
            if rec.state not in ('draft', 'in_progress'):
                raise UserError(_('Only draft or in-progress projects can be completed.'))
            rec.state = 'completed'
        return True

    def action_cancel(self):
        """Cancel the project."""
        for rec in self:
            if rec.state == 'cancelled':
                raise UserError(_('Project is already cancelled.'))
            rec.state = 'cancelled'
        return True

    def action_draft(self):
        """Reset project back to draft."""
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_('Only cancelled projects can be reset to draft.'))
            rec.state = 'draft'
        return True
