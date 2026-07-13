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


class ProjectProject(models.Model):
    _inherit = 'project.project'

    video_meeting_ids = fields.One2many(
        'video.meeting',
        'res_id',
        string='Video Meetings',
        domain=[('res_model', '=', 'project.project')],
        help='Video meetings related to this project'
    )
    video_meeting_count = fields.Integer(
        string='Meeting Count',
        compute='_compute_video_meeting_stats',
    )
    video_total_duration_minutes = fields.Integer(
        string='Total Duration (min)',
        compute='_compute_video_meeting_stats',
    )

    def _compute_video_meeting_stats(self):
        for record in self:
            meetings = self.env['video.meeting'].search([
                ('res_model', '=', 'project.project'),
                ('res_id', '=', record.id),
            ])
            record.video_meeting_count = len(meetings)
            record.video_total_duration_minutes = sum(
                meetings.mapped('actual_duration_minutes')) or sum(
                meetings.mapped('duration_minutes'))

    def action_schedule_project_meeting(self):
        self.ensure_one()
        return {
            'name': 'Schedule Project Meeting',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'project.project',
                'default_res_id': self.id,
                'default_name': f'Project Meeting: {self.name}',
            },
        }


class ProjectTask(models.Model):
    _inherit = 'project.task'

    video_meeting_ids = fields.One2many(
        'video.meeting',
        'res_id',
        string='Video Meetings',
        domain=[('res_model', '=', 'project.task')],
        help='Video meetings related to this task'
    )
    video_meeting_count = fields.Integer(
        string='Meeting Count',
        compute='_compute_video_meeting_count',
    )

    def _compute_video_meeting_count(self):
        for record in self:
            record.video_meeting_count = self.env['video.meeting'].search_count([
                ('res_model', '=', 'project.task'),
                ('res_id', '=', record.id),
            ])

    def action_schedule_task_meeting(self):
        self.ensure_one()
        return {
            'name': 'Schedule Task Meeting',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'project.task',
                'default_res_id': self.id,
                'default_name': f'Task Meeting: {self.name}',
            },
        }
