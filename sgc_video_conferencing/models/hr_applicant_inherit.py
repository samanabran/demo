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


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    video_meeting_ids = fields.One2many(
        'video.meeting',
        'res_id',
        string='Interview Meetings',
        domain=[('res_model', '=', 'hr.applicant')],
        help='Video interview meetings for this applicant'
    )
    video_meeting_count = fields.Integer(
        string='Interviews',
        compute='_compute_video_meeting_count',
    )
    last_interview_date = fields.Datetime(
        string='Last Interview',
        compute='_compute_video_meeting_count',
    )

    def _compute_video_meeting_count(self):
        for record in self:
            meetings = self.env['video.meeting'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', record.id),
            ], order='start_time desc')
            record.video_meeting_count = len(meetings)
            record.last_interview_date = meetings[:1].start_time if meetings else False

    def action_schedule_interview(self):
        self.ensure_one()
        return {
            'name': 'Schedule Interview',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'hr.applicant',
                'default_res_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_name': f'Interview: {self.name} - {self.job_id.name or ""}',
            },
        }
