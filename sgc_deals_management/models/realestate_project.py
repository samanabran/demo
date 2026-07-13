# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RealEstateProject(models.Model):
    _name = 'realestate.project'
    _description = 'Real Estate Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Basic Info
    name = fields.Char(
        string='Project Name',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Project Code',
        tracking=True,
        help='Internal reference code for the project'
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )

    # Location
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]"
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country'
    )
    zip = fields.Char(string='Zip Code')

    # Developer
    developer_id = fields.Many2one(
        'res.partner',
        string='Developer',
        domain=[('is_company', '=', True)],
        tracking=True
    )

    # Project Details
    project_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('mixed', 'Mixed Use'),
    ], string='Project Type', default='residential', tracking=True)

    # Dates
    start_date = fields.Date(
        string='Start Date',
        tracking=True
    )
    expected_completion_date = fields.Date(
        string='Expected Completion',
        tracking=True
    )
    completion_date = fields.Date(
        string='Actual Completion',
        tracking=True
    )

    # Status
    state = fields.Selection([
        ('planned', 'Planned'),
        ('construction', 'Under Construction'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    ], string='Status', default='planned', required=True, tracking=True)

    # Relations
    unit_ids = fields.One2many(
        'realestate.unit',
        'project_id',
        string='Units'
    )
    sale_order_ids = fields.One2many(
        'sale.order',
        'deal_project_id',
        string='Deals'
    )

    # Computed Fields
    unit_count = fields.Integer(
        string='Unit Count',
        compute='_compute_counts',
        store=True
    )
    deal_count = fields.Integer(
        string='Deal Count',
        compute='_compute_counts',
        store=True
    )
    total_project_value = fields.Monetary(
        string='Total Project Value',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    # Financial
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # Additional Info
    description = fields.Html(string='Description')
    notes = fields.Text(string='Internal Notes')

    @api.depends('unit_ids', 'sale_order_ids')
    def _compute_counts(self):
        for record in self:
            record.unit_count = len(record.unit_ids)
            record.deal_count = len(record.sale_order_ids)

    @api.depends('sale_order_ids.amount_total')
    def _compute_totals(self):
        for record in self:
            record.total_project_value = sum(record.sale_order_ids.mapped('amount_total'))

    def action_view_units(self):
        """Open units for this project"""
        self.ensure_one()
        return {
            'name': _('Units'),
            'type': 'ir.actions.act_window',
            'res_model': 'realestate.unit',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_deals(self):
        """Open deals for this project"""
        self.ensure_one()
        return {
            'name': _('Deals'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('deal_project_id', '=', self.id)],
            'context': {'default_deal_project_id': self.id},
        }
