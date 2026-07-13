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
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MeetingCreateWizard(models.TransientModel):
    _name = 'meeting.create.wizard'
    _description = 'Meeting Creation Wizard'

    name = fields.Char(string='Meeting Title', required=True)
    description = fields.Text(string='Description / Agenda')
    provider_id = fields.Many2one(
        'video.provider',
        string='Provider',
        required=True,
        default=lambda self: self._default_provider(),
    )
    provider_account_id = fields.Many2one(
        'video.provider.account',
        string='Account',
        domain="[('provider_id', '=', provider_id), ('state', '=', 'verified')]",
    )
    meeting_type = fields.Selection([
        ('instant', 'Instant Meeting (Start Now)'),
        ('scheduled', 'Scheduled Meeting'),
        ('recurring', 'Recurring Meeting'),
    ], string='Meeting Type', default='instant', required=True)

    # Scheduling
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    start_time = fields.Float(string='Start Time', default=9.0, help='Hour in 24h format (e.g., 9.0 = 09:00, 14.5 = 14:30)')
    duration_minutes = fields.Integer(string='Duration (minutes)', default=60)

    # Recurrence
    is_recurring = fields.Boolean(string='Recurring')
    recurrence_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ], string='Frequency', default='weekly')
    recurrence_count = fields.Integer(string='Number of Occurrences', default=4)

    # Attendees
    partner_ids = fields.Many2many('res.partner', string='Attendees')
    attendee_emails = fields.Text(string='Additional Emails', help='Additional email addresses (one per line)')

    # Context for linking
    res_model = fields.Char(string='Resource Model')
    res_id = fields.Integer(string='Resource ID')
    partner_id = fields.Many2one('res.partner', string='Related Contact')

    @api.model
    def _default_provider(self):
        return self.env['video.provider'].search([('active', '=', True)], limit=1)

    @api.onchange('meeting_type')
    def _onchange_meeting_type(self):
        if self.meeting_type == 'instant':
            self.start_date = fields.Date.today()
            self.start_time = datetime.now().hour + datetime.now().minute / 60.0

    def action_create_meeting(self):
        """Create the video meeting"""
        self.ensure_one()

        # Calculate start datetime
        if self.meeting_type == 'instant':
            start_dt = fields.Datetime.now()
        else:
            hour = int(self.start_time)
            minute = int((self.start_time - hour) * 60)
            start_dt = datetime.combine(
                self.start_date,
                datetime.min.time().replace(hour=hour, minute=minute)
            )

        # Build invitees
        invitee_vals = []
        for partner in self.partner_ids:
            invitee_vals.append((0, 0, {
                'partner_id': partner.id,
                'name': partner.name,
                'email': partner.email,
            }))
        if self.attendee_emails:
            for email in self.attendee_emails.strip().split('\n'):
                email = email.strip()
                if email:
                    invitee_vals.append((0, 0, {
                        'name': email.split('@')[0],
                        'email': email,
                    }))

        # Create meeting
        meeting_vals = {
            'name': self.name,
            'description': self.description or '',
            'provider_id': self.provider_id.id,
            'provider_account_id': self.provider_account_id.id,
            'start_time': start_dt,
            'duration_minutes': self.duration_minutes,
            'meeting_type': self.meeting_type,
            'status': 'scheduled',
            'invitee_ids': invitee_vals,
        }

        if self.is_recurring or self.meeting_type == 'recurring':
            meeting_vals['is_recurring'] = True
            meeting_vals['recurrence_frequency'] = self.recurrence_frequency
            meeting_vals['recurrence_count'] = self.recurrence_count

        if self.res_model and self.res_id:
            meeting_vals['res_model'] = self.res_model
            meeting_vals['res_id'] = self.res_id

        meeting = self.env['video.meeting'].create(meeting_vals)
        meeting._generate_meeting_urls()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'video.meeting',
            'view_mode': 'form',
            'res_id': meeting.id,
            'target': 'current',
        }
