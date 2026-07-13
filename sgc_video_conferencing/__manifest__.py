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

{
    "name": "SGC - Unified Video Conferencing",
    "version": "19.0.1.1",
    "category": "Productivity/Video Conferencing",
    "summary": "Unified video conferencing integration — Google Meet, Teams, Zoom, Webex, Jitsi, Zoho, GoTo",
    "description": """
SGC Unified Video Conferencing
===============================
Enterprise-grade unified video conferencing integration layer for Odoo 19.
Single framework connecting all major video conferencing platforms.

Key Features:
- 7+ provider support: Google Meet, Microsoft Teams, Zoom, Cisco Webex,
  Jitsi Meet, Zoho Meeting, GoTo Meeting
- Unified provider abstraction layer — add new providers with minimal code
- OAuth 2.0 with automatic token refresh and encrypted credential storage
- One-click meeting creation from Calendar, CRM, Sales, Helpdesk, Project,
  Recruitment, Employees, and Contacts
- Recurring meetings, instant meetings, and scheduled meetings
- Recording management (URL, duration, attendance tracking)
- Executive dashboard with pivot/graph views
- Multi-company and multi-user access groups
- Wizard-driven provider setup with pre-configured presets
    """,
    "author": "SGC TECH AI",
    "company": "SGC TECH AI",
    "maintainer": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "license": "OPL-1",
    "price": 63,
    "currency": "USD",
    "depends": [
        "base_setup",
        "mail",
        "calendar",
        "crm",
        "sale_management",
        "project",
        "hr",
        "hr_recruitment",
        "contacts",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/video_provider_data.xml",
        "data/mail_template_data.xml",
        "views/actions.xml",
        "views/menu_views.xml",
        "views/video_provider_views.xml",
        "views/video_meeting_views.xml",
        "views/video_provider_account_views.xml",
        "views/video_recording_views.xml",
        "views/calendar_views_inherit.xml",
        "views/crm_views_inherit.xml",
        "views/res_partner_views_inherit.xml",
        "views/sale_views_inherit.xml",
        "views/project_views_inherit.xml",
        # "views/helpdesk_views_inherit.xml",
        "views/hr_applicant_views_inherit.xml",
        "views/hr_employee_views_inherit.xml",
        "views/res_config_settings_views.xml",
        "views/dashboard_views.xml",
        "views/audit_log_views.xml",
        "wizards/provider_setup_wizard_views.xml",
        "wizards/meeting_create_wizard_views.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "sgc_video_conferencing/static/src/css/video_conference.css",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "external_dependencies": {
        "python": [
            "google_auth_oauthlib",
            "google-api-python-client",
            "requests",
            "cryptography",
        ],
    },
}
