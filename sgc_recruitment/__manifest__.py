# -*- coding: utf-8 -*-
{
    "name": "SGC - Recruitment",
    "version": "19.0.1.1",
    "category": "Human Resources",
    "summary": "UAE-compliant offer letters and recruitment extensions",
    "description": """
        SGC Recruitment Extension
        ========================================
        
        Features:
        ---------
        * Extended applicant fields for UAE compliance
        * Professional offer letter generation
        * Automated salary calculations
        * Email templates for offer letters
        * UAE Labour Law compliant templates
        * Comprehensive benefits tracking
        * Digital signature support
        * Offer validity tracking
        
        UAE Compliance:
        ---------------
        * Emirates ID and passport tracking
        * Visa sponsorship management
        * UAE standard probation period (180 days)
        * Annual leave entitlement (30 days minimum)
        * Health insurance requirements
        * Working hours and notice periods
        
        Brand Identity: Deep Ocean Palette
        -----------------------------------
        * Deep Navy (#0c1e34) - Authority & Trust
        * Ocean Blue (#1e3a8a) - Professionalism
        * Sky Blue (#4fc3f7) - Innovation
        * Ice White (#e8f4fd) - Clarity
        
        Technical Details:
        ------------------
        * Compatible with Odoo 19 Community & Enterprise
        * Extends standard hr_recruitment module
        * PDF report generation with QWeb
        * Responsive email templates
        * Multi-currency support
        
        Usage:
        ------
        1. Go to Recruitment > Applications
        2. Open any applicant record
        3. Fill Personal Information, Employment Details, Compensation tabs
        4. Navigate to Offer Letter tab
        5. Click "Generate Offer Letter" to preview
        6. Click "Send Offer Letter" to email candidate
        
    """,
    "author": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "license": "OPL-1",
    "depends": [
        "base",
        "hr",
        "hr_recruitment",
        "crm",
        "mail",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/hr_applicant_views.xml",
        "views/crm_lead_views.xml",
        # Reports
        "reports/offer_letter_template.xml",
        # Data
        "data/email_templates.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "sgc_recruitment/static/src/scss/report_styles.scss",
        ],
    },
    "images": [
        "static/description/banner.png",
        "static/description/icon.png",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "price": 28,
    "currency": "USD",
}
