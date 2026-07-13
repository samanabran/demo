# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RealEstateUnit(models.Model):
    _name = 'realestate.unit'
    _description = 'Real Estate Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, name'

    # Basic Info
    name = fields.Char(
        string='Unit Number',
        required=True,
        tracking=True,
        help='Unit number or identifier (e.g., 101, A-205, Villa 12)'
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )

    # Project Link (Required)
    project_id = fields.Many2one(
        'realestate.project',
        string='Project',
        required=True,
        ondelete='restrict',
        tracking=True
    )

    # Unit Type
    unit_type = fields.Selection([
        ('studio', 'Studio'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('penthouse', 'Penthouse'),
        ('townhouse', 'Townhouse'),
        ('office', 'Office'),
        ('shop', 'Shop'),
        ('warehouse', 'Warehouse'),
    ], string='Unit Type', required=True, tracking=True)

    # Physical Attributes
    bedrooms = fields.Integer(string='Bedrooms')
    bathrooms = fields.Integer(string='Bathrooms')
    floor = fields.Char(string='Floor')
    plot_area = fields.Float(
        string='Plot Area (sqm)',
        digits=(10, 2)
    )
    built_up_area = fields.Float(
        string='Built-up Area (sqm)',
        digits=(10, 2)
    )
    balcony_area = fields.Float(
        string='Balcony Area (sqm)',
        digits=(10, 2)
    )

    # Pricing
    list_price = fields.Monetary(
        string='List Price',
        tracking=True,
        currency_field='currency_id',
        help='Standard selling price for this unit'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # Availability Status
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('unavailable', 'Unavailable'),
    ], string='Status', default='available', required=True, tracking=True)

    # Relations
    sale_order_ids = fields.One2many(
        'sale.order',
        'unit_id',
        string='Deals'
    )
    deal_count = fields.Integer(
        string='Deal Count',
        compute='_compute_deal_count',
        store=True
    )

    # Additional Info
    description = fields.Html(string='Description')
    features = fields.Text(
        string='Key Features',
        help='Parking, view, furnishing, etc.'
    )
    notes = fields.Text(string='Internal Notes')

    _check_unit_project_unique = models.Constraint(
        'unique(project_id, name)',
        'Unit number must be unique within a project!',
    )

    @api.depends('sale_order_ids')
    def _compute_deal_count(self):
        for record in self:
            record.deal_count = len(record.sale_order_ids)

    def name_get(self):
        """Display format: 'Project Name - Unit Number'"""
        result = []
        for record in self:
            if record.project_id:
                name = f"{record.project_id.name} - {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike',
                     limit=100, name_get_uid=None, order=None):
        """Enable search by unit number or project name"""
        args = args or []
        if name:
            # Search in unit name or project name
            domain = ['|', ('name', operator, name), ('project_id.name', operator, name)]
            return self._search(
                domain + args,
                limit=limit,
                order=order,
                access_rights_uid=name_get_uid,
            )
        return super()._name_search(
            name,
            args,
            operator,
            limit,
            name_get_uid,
        )

    def action_view_deals(self):
        """Open deals for this unit"""
        self.ensure_one()
        return {
            'name': _('Deals'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('unit_id', '=', self.id)],
            'context': {
                'default_unit_id': self.id,
                'default_project_id': self.project_id.id,
            },
        }
