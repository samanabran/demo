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


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    video_meeting_ids = fields.One2many(
        'video.meeting',
        'res_id',
        string='Video Meetings',
        domain=[('res_model', '=', 'hr.employee')],
        help='Video meetings related to this employee'
    )
    hosted_meeting_ids = fields.One2many(
        'video.meeting',
        'user_id',
        string='Hosted Meetings',
        help='Meetings hosted by this employee'
    )
    video_meeting_count = fields.Integer(
        string='Meeting Count',
        compute='_compute_video_meeting_count',
    )

    def _compute_video_meeting_count(self):
        for record in self:
            record.video_meeting_count = self.env['video.meeting'].search_count([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', record.id),
            ])

    def action_schedule_team_meeting(self):
        self.ensure_one()
        return {
            'name': 'Schedule Team Meeting',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'hr.employee',
                'default_res_id': self.id,
                'default_name': f'Team Meeting - {self.name}',
            },
        }

    def action_schedule_department_meeting(self):
        self.ensure_one()
        return {
            'name': 'Schedule Department Meeting',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'hr.employee',
                'default_res_id': self.id,
                'default_name': f'Department Meeting - {self.department_id.name or ""}',
            },
        }
