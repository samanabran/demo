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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    video_meeting_ids = fields.One2many(
        'video.meeting',
        'res_id',
        string='Video Meetings',
        domain=[('res_model', '=', 'sale.order')],
        help='Video meetings related to this sales order'
    )
    video_meeting_count = fields.Integer(
        string='Meeting Count',
        compute='_compute_video_meeting_count',
    )

    def _compute_video_meeting_count(self):
        for record in self:
            record.video_meeting_count = self.env['video.meeting'].search_count([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', record.id),
            ])

    def action_schedule_demo(self):
        """Schedule a product demo meeting"""
        self.ensure_one()
        return {
            'name': 'Schedule Demo',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'sale.order',
                'default_res_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_name': f'Demo: {self.name}',
            },
        }

    def action_schedule_discovery_call(self):
        """Schedule a discovery call"""
        self.ensure_one()
        return {
            'name': 'Schedule Discovery Call',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'sale.order',
                'default_res_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_name': f'Discovery: {self.name}',
            },
        }

    def action_schedule_presentation(self):
        """Schedule a client presentation"""
        self.ensure_one()
        return {
            'name': 'Schedule Presentation',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'sale.order',
                'default_res_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_name': f'Presentation: {self.name}',
            },
        }
