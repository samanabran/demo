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


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    video_meeting_ids = fields.One2many(
        'video.meeting',
        'res_id',
        string='Video Meetings',
        domain=[('res_model', '=', 'crm.lead')],
        help='Video meetings related to this lead/opportunity'
    )
    video_meeting_count = fields.Integer(
        string='Meeting Count',
        compute='_compute_video_meeting_count',
        help='Number of video meetings held for this lead'
    )
    last_video_meeting_date = fields.Datetime(
        string='Last Meeting',
        compute='_compute_video_meeting_count',
        help='Date of the most recent video meeting'
    )

    def _compute_video_meeting_count(self):
        for record in self:
            meetings = self.env['video.meeting'].search([
                ('res_model', '=', 'crm.lead'),
                ('res_id', '=', record.id),
            ])
            record.video_meeting_count = len(meetings)
            record.last_video_meeting_date = meetings[:1].start_time if meetings else False

    def action_schedule_meeting(self):
        """Schedule a video meeting for this lead"""
        self.ensure_one()
        return {
            'name': 'Schedule Video Meeting',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'crm.lead',
                'default_res_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_name': f'Meeting: {self.name}',
            },
        }

    def action_send_meeting_invite(self):
        """Send meeting invitation to lead contact"""
        self.ensure_one()
        meeting = self.video_meeting_ids[:1]
        if meeting:
            meeting.action_send_invitation()
