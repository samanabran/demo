# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    tenancy_id = fields.Many2one(
        'tenancy.details',
        string='Tenancy',
        readonly=True,
        help='Related tenancy contract'
    )
    
    tenancy_property_id = fields.Many2one(
        'property.details',
        string='Tenancy Property',
        related='tenancy_id.property_id',
        store=True,
        readonly=True
    )
    
    sold_id = fields.Many2one(
        'property.vendor',
        string='Sale Contract',
        readonly=True,
        help='Related sale contract'
    )
    
    sold_property_id = fields.Many2one(
        'property.details',
        string='Sold Property',
        related='sold_id.property_id',
        store=True,
        readonly=True
    )
    
    maintenance_request_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        readonly=True,
        help='Related maintenance request'
    )
