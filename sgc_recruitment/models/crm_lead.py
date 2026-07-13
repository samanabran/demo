# -*- coding: utf-8 -*-
from odoo import models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _get_recruitment_applicant_vals(self):
        self.ensure_one()
        partner_name = (
            self.contact_name or self.partner_name or self.name
        )
        phone = self.mobile or self.phone
        vals = {
            'name': self.name,
            'partner_name': partner_name,
            'email_from': self.email_from,
            'partner_phone': phone,
            'description': self.description,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'campaign_id': self.campaign_id.id,
        }
        return {key: value for key, value in vals.items() if value}

    def action_open_recruitment_applicant(self):
        self.ensure_one()
        applicant = self.env['hr.applicant'].create(
            self._get_recruitment_applicant_vals()
        )
        self.env.user.notify_info(
            message=_('Applicant created from Won opportunity.')
        )
        return {
            'name': _('Create Recruitment Applicant'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'res_id': applicant.id,
            'view_mode': 'form',
            'target': 'current',
        }
