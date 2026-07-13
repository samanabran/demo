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

try:
    from odoo.addons.helpdesk import models as helpdesk_models
    _helpdesk_available = True
except ImportError:
    _helpdesk_available = False

if _helpdesk_available:

    class HelpdeskTicket(models.Model):
        _inherit = 'helpdesk.ticket'

        video_meeting_ids = fields.One2many(
            'video.meeting',
            'res_id',
            string='Video Meetings',
            domain=[('res_model', '=', 'helpdesk.ticket')],
            help='Video support meetings for this ticket'
        )
        video_meeting_count = fields.Integer(
            string='Meeting Count',
            compute='_compute_video_meeting_count',
        )
        last_video_meeting_date = fields.Datetime(
            string='Last Meeting',
            compute='_compute_video_meeting_count',
        )

        def _compute_video_meeting_count(self):
            for record in self:
                meetings = self.env['video.meeting'].search([
                    ('res_model', '=', 'helpdesk.ticket'),
                    ('res_id', '=', record.id),
                ], order='start_time desc')
                record.video_meeting_count = len(meetings)
                record.last_video_meeting_date = meetings[:1].start_time if meetings else False

        def action_launch_support_meeting(self):
            self.ensure_one()
            return {
                'name': 'Launch Support Meeting',
                'type': 'ir.actions.act_window',
                'res_model': 'meeting.create.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_res_model': 'helpdesk.ticket',
                    'default_res_id': self.id,
                    'default_partner_id': self.partner_id.id,
                    'default_name': 'Support: %s' % self.name,
                    'default_meeting_type': 'instant',
                },
            }

        def action_send_meeting_link(self):
            self.ensure_one()
            meeting = self.video_meeting_ids[:1]
            if meeting:
                meeting.action_send_invitation()
