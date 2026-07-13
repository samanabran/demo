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

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class VideoMeetingInvitee(models.Model):
    _name = 'video.meeting.invitee'
    _description = 'Video Meeting Invitee'
    _order = 'create_date, id'

    meeting_id = fields.Many2one(
        'video.meeting',
        string='Meeting',
        required=True,
        ondelete='cascade',
        help="The meeting this invitee is linked to"
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        help="Related contact (if exists in Odoo)"
    )
    name = fields.Char(
        string='Name',
        required=True,
        help="Name of the invitee"
    )
    email = fields.Char(
        string='Email',
        help="Email address of the invitee"
    )
    attended = fields.Boolean(
        string='Attended',
        help="Whether the invitee attended the meeting"
    )
    attendance_duration_minutes = fields.Integer(
        string='Attendance Duration (min)',
        help="How long the invitee attended in minutes"
    )
    invitation_sent = fields.Boolean(
        string='Invitation Sent',
        default=False,
        help="Whether the invitation email was sent"
    )
    joined_at = fields.Datetime(
        string='Joined At',
        help="When the invitee joined the meeting"
    )
    left_at = fields.Datetime(
        string='Left At',
        help="When the invitee left the meeting"
    )
    response_status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('tentative', 'Tentative'),
        ('no_response', 'No Response'),
    ], string='Response Status', default='pending')
