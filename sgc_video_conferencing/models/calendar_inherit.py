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


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_video_meeting = fields.Boolean(
        string='Has Video Meeting',
        help='Whether this event has a video conferencing meeting'
    )
    video_provider_id = fields.Many2one(
        'video.provider',
        string='Video Provider',
        help='Video conferencing provider for this event'
    )
    video_meeting_id = fields.Many2one(
        'video.meeting',
        string='Video Meeting',
        help='Associated video meeting record',
        ondelete='set null',
    )
    video_join_url = fields.Char(
        string='Video Meeting URL',
        related='video_meeting_id.join_url',
        readonly=True,
        help='URL to join the video meeting'
    )
    video_start_url = fields.Char(
        string='Video Start URL',
        related='video_meeting_id.start_url',
        readonly=True,
        help='URL to start the video meeting'
    )

    @api.model_create_multi
    def create(self, vals_list):
        events = super().create(vals_list)
        for event in events:
            if event.is_video_meeting and event.video_provider_id and not event.video_meeting_id:
                event._create_video_meeting()
        return events

    def write(self, vals):
        res = super().write(vals)
        if 'is_video_meeting' in vals or 'video_provider_id' in vals:
            for event in self:
                if event.is_video_meeting and event.video_provider_id:
                    if event.video_meeting_id:
                        event.video_meeting_id.write({
                            'name': event.name,
                            'start_time': event.start,
                            'duration_minutes': event.duration,
                        })
                    else:
                        event._create_video_meeting()
                elif not event.is_video_meeting and event.video_meeting_id:
                    event.video_meeting_id.action_cancel_meeting()
        return res

    def _create_video_meeting(self):
        """Create a video meeting linked to this calendar event"""
        self.ensure_one()
        if not self.video_provider_id:
            return False

        # Collect attendees
        partner_emails = self.partner_ids.mapped('email')
        invitee_vals = []
        for partner in self.partner_ids:
            invitee_vals.append((0, 0, {
                'partner_id': partner.id,
                'name': partner.name,
                'email': partner.email,
            }))

        meeting = self.env['video.meeting'].create({
            'name': self.name,
            'provider_id': self.video_provider_id.id,
            'start_time': self.start,
            'duration_minutes': self.duration or 60,
            'meeting_type': 'scheduled',
            'description': self.description,
            'calendar_event_id': self.id,
            'invitee_ids': invitee_vals,
        })

        # Generate URLs via provider service
        meeting._generate_meeting_urls()
        self.video_meeting_id = meeting.id
        self.video_join_url = meeting.join_url

        # Update calendar event with meeting link
        if meeting.join_url:
            self.write({'video_join_url': meeting.join_url})

        return meeting

    def action_join_video_meeting(self):
        """Join the video meeting"""
        self.ensure_one()
        if self.video_meeting_id:
            return self.video_meeting_id.action_join_meeting()
        return False

    def action_start_video_meeting(self):
        """Start the video meeting"""
        self.ensure_one()
        if self.video_meeting_id:
            return self.video_meeting_id.action_start_meeting()
        return False
