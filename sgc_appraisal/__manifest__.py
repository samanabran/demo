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
    "name": "SGC - Employee Appraisal",
    "version": "19.0.1.2",
    "category": "Human Resources",
    "summary": """Roll out appraisal plans and get the best of your 
    workforce""",
    "description": """This app is a powerful and versatile tool that can help 
    organizations improve their employee appraisal process and boost employee 
    performance.""",
    "author": "SGC TECH AI",
    "company": "SGC TECH AI",
    "maintainer": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "depends": ["hr", "survey"],
    "data": [
        "security/oh_appraisal_groups.xml",
        "security/hr_appraisal_security.xml",
        "security/ir.model.access.csv",
        "security/appraisal_survey_security.xml",
        "views/appraisal_templates.xml",
        "views/survey_user_input_views.xml",
        "views/hr_appraisal_views.xml",
        "views/menuitems.xml",
        "views/appraisal_survey_views.xml",
        "views/appraisal_survey_reports.xml",
        "views/appraisal_survey_menus.xml",
    ],
    "demo": [],
    "images": ["static/description/banner.png"],
    "license": "OPL-1",
    "price": 25,
    "currency": "USD",
    "installable": True,
    "auto_install": False,
    "application": False,
}

