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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    video_meeting_ids = fields.One2many(
        'video.meeting.invitee',
        'partner_id',
        string='Video Meetings',
        help='Video meetings this contact was invited to'
    )
    video_meeting_count = fields.Integer(
        string='Meeting Count',
        compute='_compute_video_meeting_stats',
        help='Total number of video meetings'
    )
    video_meeting_attended_count = fields.Integer(
        string='Meetings Attended',
        compute='_compute_video_meeting_stats',
        help='Number of meetings attended'
    )
    upcoming_video_meeting_ids = fields.One2many(
        'video.meeting',
        string='Upcoming Meetings',
        compute='_compute_upcoming_video_meetings',
        help='Upcoming video meetings for this contact'
    )

    def _compute_video_meeting_stats(self):
        for record in self:
            invitees = self.env['video.meeting.invitee'].search([
                ('partner_id', '=', record.id),
            ])
            record.video_meeting_count = len(invitees)
            record.video_meeting_attended_count = len(invitees.filtered('attended'))

    def _compute_upcoming_video_meetings(self):
        for record in self:
            invitees = self.env['video.meeting.invitee'].search([
                ('partner_id', '=', record.id),
            ])
            meetings = invitees.mapped('meeting_id').filtered(
                lambda m: m.status == 'scheduled' and m.start_time >= fields.Datetime.now()
            )
            record.upcoming_video_meeting_ids = meetings
