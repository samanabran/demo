# -*- coding: utf-8 -*-
from odoo import models


class IrUiMenu(models.Model):
    """Re-asserts SGC brand icons on every registry load.

    XML data alone is fragile here: when a *target* module (crm, mail,
    hr, ...) reloads on any future upgrade, its own noupdate="0" data
    silently re-writes the default web_icon and clobbers this module's
    override, regardless of load order. _register_hook runs on every
    registry build (every restart, every upgrade of anything), so the
    brand icon self-heals instead of depending on one-shot XML load
    order between unrelated modules.
    """
    _inherit = 'ir.ui.menu'

    _SGC_BRAND_ICONS = {
        'mail.menu_root_discuss': 'sgc_ui_brand_palette,static/icons/core_discuss.png',
        'calendar.mail_menu_calendar': 'sgc_ui_brand_palette,static/icons/core_calendar.png',
        'contacts.menu_contacts': 'sgc_ui_brand_palette,static/icons/core_contacts.png',
        'crm.crm_menu_root': 'sgc_ui_brand_palette,static/icons/core_crm.png',
        'hr.menu_hr_root': 'sgc_ui_brand_palette,static/icons/core_employees.png',
        'account.menu_finance': 'sgc_ui_brand_palette,static/icons/core_invoicing.png',
        'utm.menu_link_tracker_root': 'sgc_ui_brand_palette,static/icons/core_link_tracker.png',
        'maintenance.menu_maintenance_title': 'sgc_ui_brand_palette,static/icons/core_maintenance.png',
        'hr_payroll_community.menu_hr_payroll_community_root': 'sgc_ui_brand_palette,static/icons/core_payroll.png',
        'project.menu_main_pm': 'sgc_ui_brand_palette,static/icons/core_project.png',
        'project_todo.menu_todo_todos': 'sgc_ui_brand_palette,static/icons/core_todo.png',
        'purchase.menu_purchase_root': 'sgc_ui_brand_palette,static/icons/core_purchase.png',
        'hr_recruitment.menu_hr_recruitment_root': 'sgc_ui_brand_palette,static/icons/core_recruitment.png',
        'sale.sale_menu_root': 'sgc_ui_brand_palette,static/icons/core_sales.png',
        'survey.menu_surveys': 'sgc_ui_brand_palette,static/icons/core_surveys.png',
        'hr_holidays.menu_hr_holidays_root': 'sgc_ui_brand_palette,static/icons/core_timeoff.png',
        'hr_attendance.menu_hr_attendance_root': 'sgc_ui_brand_palette,static/icons/core_attendances.png',
        'website.menu_website_configuration': 'sgc_ui_brand_palette,static/icons/core_website.png',
        'eh_uae_payroll_wps.menu_eh_uae_wps_root': 'sgc_ui_brand_palette,static/icons/core_payroll.png',
        'spreadsheet_dashboard.spreadsheet_dashboard_menu_root': 'sgc_ui_brand_palette,static/icons/core_dashboards.png',
        'sgc_employment_certificate.menu_hr_employment_certificates': 'sgc_ui_brand_palette,static/icons/sgc_employment_certificate.png',
        'sgc_hr_memos.menu_hr_memo_root': 'sgc_ui_brand_palette,static/icons/sgc_hr_memos.png',
        'sgc_invoicing_dashboard.menu_sgc_sales_invoicing_dashboard': 'sgc_ui_brand_palette,static/icons/sgc_invoicing_dashboard.png',
    }

    def _register_hook(self):
        super()._register_hook()
        self._apply_sgc_brand_icons()

    def _apply_sgc_brand_icons(self):
        for xmlid, icon in self._SGC_BRAND_ICONS.items():
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu and menu.web_icon != icon:
                menu.web_icon = icon
