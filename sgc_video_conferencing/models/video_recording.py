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


class VideoRecording(models.Model):
    _name = 'video.recording'
    _description = 'Video Meeting Recording'
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Recording Name',
        required=True,
        help="Name/title of the recording"
    )
    meeting_id = fields.Many2one(
        'video.meeting',
        string='Meeting',
        required=True,
        ondelete='cascade',
        help="The meeting this recording belongs to"
    )
    provider_id = fields.Many2one(
        'video.provider',
        related='meeting_id.provider_id',
        string='Provider',
        store=True,
    )
    # Recording identifiers
    provider_recording_id = fields.Char(
        string='Provider Recording ID',
        help="Recording ID from the provider"
    )
    recording_url = fields.Char(
        string='Recording URL',
        help="URL to view/download the recording"
    )
    download_url = fields.Char(
        string='Download URL',
        help="URL to download the recording"
    )
    # Type
    recording_type = fields.Selection([
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('transcript', 'Transcript'),
        ('chat', 'Chat History'),
        ('screen_share', 'Screen Share'),
    ], string='Recording Type', default='video', required=True)
    # Duration
    duration_seconds = fields.Integer(
        string='Duration (seconds)',
        help="Duration of the recording in seconds"
    )
    duration_minutes = fields.Float(
        string='Duration (minutes)',
        compute='_compute_duration_minutes',
        store=True,
        help="Duration in minutes"
    )
    file_size_bytes = fields.Integer(
        string='File Size (bytes)',
        help="Size of the recording file in bytes"
    )
    file_size_mb = fields.Float(
        string='File Size (MB)',
        compute='_compute_file_size_mb',
        store=True,
        help="File size in megabytes"
    )
    file_format = fields.Char(
        string='Format',
        help="File format (e.g., MP4, M4A, TXT)"
    )
    # Status
    recording_date = fields.Datetime(
        string='Recording Date',
        help="When the recording was made"
    )
    is_password_protected = fields.Boolean(
        string='Password Protected',
        help="Whether the recording is password protected"
    )
    password = fields.Char(
        string='Password',
        help="Password to access the recording if protected"
    )
    # Tracking
    view_count = fields.Integer(
        string='View Count',
        default=0,
        help="Number of times the recording has been viewed"
    )
    download_count = fields.Integer(
        string='Download Count',
        default=0,
        help="Number of times the recording has been downloaded"
    )
    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='meeting_id.company_id',
        store=True,
    )
    # Active
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether this recording is still available"
    )

    _check_recording_provider_unique = models.Constraint(
        'unique(provider_recording_id, provider_id)',
        'Recording ID must be unique per provider!',
    )

    @api.depends('duration_seconds')
    def _compute_duration_minutes(self):
        for record in self:
            record.duration_minutes = record.duration_seconds / 60.0 if record.duration_seconds else 0.0

    @api.depends('file_size_bytes')
    def _compute_file_size_mb(self):
        for record in self:
            record.file_size_mb = record.file_size_bytes / (1024.0 * 1024.0) if record.file_size_bytes else 0.0

    def action_open_recording(self):
        """Open the recording URL"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.recording_url or self.download_url,
            'target': 'new',
        }
