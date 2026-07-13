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
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class VideoMeeting(models.Model):
    _name = 'video.meeting'
    _description = 'Video Meeting'
    _order = 'start_time desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Meeting Title',
        required=True,
        tracking=True,
        help="Title of the meeting"
    )
    description = fields.Text(
        string='Description',
        help="Description or agenda of the meeting"
    )
    # Provider
    provider_id = fields.Many2one(
        'video.provider',
        string='Provider',
        required=True,
        tracking=True,
        help="Video conferencing provider"
    )
    provider_account_id = fields.Many2one(
        'video.provider.account',
        string='Provider Account',
        tracking=True,
        help="Linked provider account used to create this meeting"
    )
    # Meeting identifiers
    provider_meeting_id = fields.Char(
        string='Provider Meeting ID',
        help="Meeting ID from the provider (e.g., Zoom ID, Google Meet code)"
    )
    join_url = fields.Char(
        string='Join URL',
        required=True,
        help="URL to join the meeting"
    )
    start_url = fields.Char(
        string='Start URL',
        help="URL to start/host the meeting (host-specific)"
    )
    password = fields.Char(
        string='Meeting Password',
        help="Meeting password if required"
    )
    # Timing
    start_time = fields.Datetime(
        string='Start Time',
        required=True,
        help="Meeting start time"
    )
    end_time = fields.Datetime(
        string='End Time',
        compute='_compute_end_time',
        store=True,
        readonly=False,
        help="Meeting end time"
    )
    duration_minutes = fields.Integer(
        string='Duration (minutes)',
        default=60,
        help="Duration of the meeting in minutes"
    )
    duration_hours = fields.Float(
        string='Duration (hours)',
        compute='_compute_duration_hours',
        store=True,
        help="Duration in hours"
    )
    actual_duration_minutes = fields.Integer(
        string='Actual Duration (minutes)',
        help="Actual duration of the meeting in minutes (updated after meeting ends)"
    )
    meeting_type = fields.Selection([
        ('instant', 'Instant'),
        ('scheduled', 'Scheduled'),
        ('recurring', 'Recurring')
    ], string='Meeting Type', default='scheduled', required=True)
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('ongoing', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', tracking=True)
    # Recurrence
    is_recurring = fields.Boolean(
        string='Recurring Meeting',
        help="Whether this is a recurring meeting"
    )
    recurrence_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom')
    ], string='Recurrence Frequency')
    recurrence_interval = fields.Integer(
        string='Recurrence Interval',
        default=1,
        help="Interval for recurrence (e.g., every 2 weeks)"
    )
    recurrence_end_date = fields.Date(
        string='Recurrence End Date',
        help="End date for recurrence"
    )
    recurrence_count = fields.Integer(
        string='Recurrence Count',
        help="Number of occurrences"
    )
    # Attendees / Invitees
    invitee_ids = fields.One2many(
        'video.meeting.invitee',
        'meeting_id',
        string='Invitees',
        help="People invited to this meeting"
    )
    attendee_count = fields.Integer(
        string='Number of Attendees',
        compute='_compute_attendee_count',
        store=True,
        help="Total number of invitees"
    )
    attended_count = fields.Integer(
        string='Attended',
        compute='_compute_attended_count',
        store=True,
        help="Number of people who attended"
    )
    # Recordings
    recording_ids = fields.One2many(
        'video.recording',
        'meeting_id',
        string='Recordings',
        help="Recordings of this meeting"
    )
    recording_count = fields.Integer(
        string='Recording Count',
        compute='_compute_recording_count',
        store=True,
        help="Number of recordings"
    )
    # Integrations
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Calendar Event',
        ondelete='set null',
        help="Related calendar event"
    )
    res_model = fields.Char(
        string='Resource Model',
        help="Odoo model this meeting is linked to (crm.lead, sale.order, etc.)"
    )
    res_id = fields.Integer(
        string='Resource ID',
        help="ID of the linked record"
    )
    # Host info
    user_id = fields.Many2one(
        'res.users',
        string='Host',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="User who created/hosted the meeting"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    # Activity / communication
    meeting_link = fields.Char(
        string='Meeting Link',
        compute='_compute_meeting_link',
        help="Full meeting link for display"
    )
    formatted_start = fields.Char(
        string='Formatted Start Time',
        compute='_compute_formatted_times',
        store=False
    )
    formatted_end = fields.Char(
        string='Formatted End Time',
        compute='_compute_formatted_times',
        store=False
    )

    _check_end_time_after_start = models.Constraint(
        'CHECK(end_time > start_time OR end_time IS NULL)',
        'End time must be after start time.',
    )

    @api.depends('start_time', 'duration_minutes')
    def _compute_end_time(self):
        for record in self:
            if record.start_time and record.duration_minutes and not record.end_time:
                record.end_time = record.start_time + timedelta(minutes=record.duration_minutes)
            elif record.start_time and not record.duration_minutes and not record.end_time:
                record.end_time = record.start_time + timedelta(minutes=60)

    @api.depends('duration_minutes')
    def _compute_duration_hours(self):
        for record in self:
            record.duration_hours = record.duration_minutes / 60.0 if record.duration_minutes else 0.0

    @api.depends('invitee_ids')
    def _compute_attendee_count(self):
        for record in self:
            record.attendee_count = len(record.invitee_ids)

    @api.depends('invitee_ids.attended')
    def _compute_attended_count(self):
        for record in self:
            record.attended_count = len(record.invitee_ids.filtered('attended'))

    @api.depends('recording_ids')
    def _compute_recording_count(self):
        for record in self:
            record.recording_count = len(record.recording_ids)

    @api.depends('join_url')
    def _compute_meeting_link(self):
        for record in self:
            record.meeting_link = record.join_url

    @api.depends('start_time', 'end_time')
    def _compute_formatted_times(self):
        for record in self:
            if record.start_time:
                record.formatted_start = record.start_time.strftime('%Y-%m-%d %H:%M')
            if record.end_time:
                record.formatted_end = record.end_time.strftime('%Y-%m-%d %H:%M')

    @api.model
    def create_instant_meeting(self, provider_id, title, **kwargs):
        """Create an instant meeting that starts now"""
        vals = {
            'provider_id': provider_id,
            'name': title or 'Instant Meeting',
            'start_time': fields.Datetime.now(),
            'duration_minutes': kwargs.get('duration', 60),
            'meeting_type': 'instant',
            'status': 'scheduled',
        }
        vals.update(kwargs)
        # Generate join_url via provider service
        meeting = self.create(vals)
        meeting._generate_meeting_urls()
        return meeting

    def _generate_meeting_urls(self):
        """Call the provider service to generate meeting URLs"""
        self.ensure_one()
        try:
            provider_service = self._get_provider_service()
            if provider_service:
                urls = provider_service.create_meeting(self)
                self.write(urls)
        except Exception as e:
            _logger.error("Failed to generate meeting URLs for %s: %s", self.name, e)

    def _get_provider_service(self):
        """Get the service instance for this meeting's provider"""
        self.ensure_one()
        if not self.provider_id:
            return None
        try:
            # Lazy import to avoid circular deps
            from odoo.addons.sgc_video_conferencing.services.provider_registry import ProviderRegistry
            return ProviderRegistry.get_service(self.provider_id.code, env=self.env)
        except ImportError:
            _logger.warning("ProviderRegistry not available; URLs must be set manually.")
            return None

    def action_start_meeting(self):
        """Open the meeting URL"""
        self.ensure_one()
        self.status = 'ongoing'
        return {
            'type': 'ir.actions.act_url',
            'url': self.start_url or self.join_url,
            'target': 'new',
        }

    def action_join_meeting(self):
        """Open the join URL"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.join_url,
            'target': 'new',
        }

    def action_cancel_meeting(self):
        """Cancel the meeting"""
        self.ensure_one()
        try:
            provider_service = self._get_provider_service()
            if provider_service:
                provider_service.delete_meeting(self)
        except Exception as e:
            _logger.error("Failed to delete meeting on provider: %s", e)
        self.status = 'cancelled'

    @api.model
    def get_upcoming_meetings(self, limit=10):
        """Get upcoming meetings for the current user"""
        return self.search([
            ('user_id', '=', self.env.user.id),
            ('start_time', '>=', fields.Datetime.now()),
            ('status', '=', 'scheduled'),
        ], order='start_time', limit=limit)

    @api.model
    def get_today_meetings(self):
        """Get today's meetings for the current user"""
        today = fields.Datetime.now()
        tomorrow = today + timedelta(days=1)
        return self.search([
            ('user_id', '=', self.env.user.id),
            ('start_time', '>=', today),
            ('start_time', '<', tomorrow),
        ], order='start_time')

    def action_send_invitation(self):
        """Send meeting invitation email to all invitees"""
        self.ensure_one()
        # Use mail template or compose
        template = self.env.ref(
            'sgc_video_conferencing.mail_template_meeting_invitation',
            raise_if_not_found=False
        )
        if template:
            for invitee in self.invitee_ids:
                if invitee.email:
                    template.send_mail(self.id, email_to=invitee.email, force_send=True)

    @api.model
    def _cron_update_meeting_statuses(self):
        """Cron job: update status of meetings that have passed"""
        now = fields.Datetime.now()
        # Mark overdue scheduled meetings as completed
        overdue = self.search([
            ('end_time', '<', now),
            ('status', '=', 'scheduled'),
        ])
        overdue.write({'status': 'completed'})
        # Mark ongoing meetings past end time as completed
        ongoing_overdue = self.search([
            ('end_time', '<', now),
            ('status', '=', 'ongoing'),
        ])
        ongoing_overdue.write({'status': 'completed'})
        return len(overdue) + len(ongoing_overdue)
