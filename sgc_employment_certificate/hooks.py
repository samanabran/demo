# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _apply_report_backgrounds(env):
    report_xmlids = [
        'hr_employment_certificate.action_report_employment_certificate',
        'hr_employment_certificate.action_report_noc_certificate',
    ]
    reports = []
    for xmlid in report_xmlids:
        report = env.ref(xmlid, raise_if_not_found=False)
        if report:
            reports.append(report)

    if not reports:
        _logger.warning(
            "No report actions found for hr_employment_certificate",
        )
        return

    for report in reports:
        report.write({
            'custom_report_background': True,
            'custom_report_type': 'company',
            'is_bg_per_lang': False,
            'custom_report_background_image': False,
        })
        attachments = env['ir.attachment'].search([
            ('res_model', '=', 'ir.actions.report'),
            ('res_id', '=', report.id),
            ('res_field', '=', 'custom_report_background_image'),
        ])
        if attachments:
            attachments.unlink()

    _logger.info(
        "Employment certificate reports set for company background"
    )


def post_init_hook(env):
    if not isinstance(env, api.Environment):
        env = api.Environment(env, SUPERUSER_ID, {})
    _apply_report_backgrounds(env)
