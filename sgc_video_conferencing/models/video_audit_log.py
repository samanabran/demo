# -*- coding: utf-8 -*-
###############################################################################
#    Part of the SGC Odoo Suite <https://sgctech.ai>
#
#    SGC TECH AI
#    Copyright (C) 2026 SGC TECH AI (<https://sgctech.ai>)
#
#    This module and its source code are licensed under the Odoo Proprietary
#    License v1.0 (OPL-1). You may not redistribute or resell it. See
#    https://www.odoo.com/documentation/19.0/legal/licenses.html for terms.
###############################################################################

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class VideoAuditLog(models.Model):
    _name = 'video.audit.log'
    _description = 'Video Conferencing Audit Log'
    _order = 'create_date desc, id desc'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        help="User who performed the action"
    )
    action = fields.Char(
        string='Action',
        required=True,
        help="Action performed (e.g., create_meeting, delete_meeting, token_refresh)"
    )
    model = fields.Char(
        string='Model',
        help="Model the action was performed on"
    )
    res_id = fields.Integer(
        string='Record ID',
        help="ID of the record"
    )
    provider_id = fields.Many2one(
        'video.provider',
        string='Provider',
        help="Provider related to this action"
    )
    description = fields.Text(
        string='Description',
        help="Detailed description of the action"
    )
    result = fields.Selection([
        ('success', 'Success'),
        ('failure', 'Failure'),
    ], string='Result', default='success')
    error_message = fields.Text(
        string='Error Message',
        help="Error message if the action failed"
    )
    ip_address = fields.Char(
        string='IP Address',
        help="IP address from which the action was performed"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    @api.model
    def log_action(self, action, model=None, res_id=None, provider_id=None,
                   description=None, result='success', error_message=None):
        """Create an audit log entry"""
        self.create({
            'user_id': self.env.user.id,
            'action': action,
            'model': model,
            'res_id': res_id,
            'provider_id': provider_id,
            'description': description,
            'result': result,
            'error_message': error_message,
            'ip_address': self.env.client or '',
        })
