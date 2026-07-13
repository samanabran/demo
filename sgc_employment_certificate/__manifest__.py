# -*- coding: utf-8 -*-
{
    "name": "SGC - Employment Certificate",
    "version": "19.0.1.1",
    "category": "Human Resources",
    "summary": "Generate Employment Certificates for Employees",
    "description": """
SGC Employment Certificate
=========================
This module adds the ability to generate and print professional 
Employment Certificates for employees.

Features:
---------
* Professional Employment Certificate template
* SGC TECH AI branded design (maroon and gold theme)
* Configurable certificate content
* Print-ready PDF output
* Reference number tracking
    """,
    "author": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "images": ["static/description/banner.png"],
    "license": "OPL-1",
    "price": 18,
    "currency": "USD",
    "depends": [
        "hr",
        "mail",
        "website",
    ],
    "data": [
        "security/hr_employment_certificate_groups.xml",
        "security/ir.model.access.csv",
        "data/certificate_sequence.xml",
        "data/hr_employment_certificate_mail_templates.xml",
        "wizard/employment_certificate_wizard_views.xml",
        "report/employment_certificate_report.xml",
        "report/employment_certificate_template.xml",
        "report/noc_certificate_template.xml",
        "views/hr_employment_certificate_views.xml",
        "views/hr_employee_views.xml",
        "views/certificate_verification_templates.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}

