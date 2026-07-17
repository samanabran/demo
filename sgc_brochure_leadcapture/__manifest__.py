{
    'name': 'SGC Brochure Lead Capture',
    'summary': 'Download Brochure button + lead-capture popup on the property detail page',
    'description': """
        Adds a "Download Brochure" button to the offplan property detail
        page. Clicking it opens a modal (Name/Email/Phone). Submitting the
        form creates a crm.lead, then triggers the existing dynamically
        generated PDF report (sgc_offplan_rental_property_management's own
        action_report_property_brochure) for download.

        Extends offplan_property_detail via inherit_id/xpath only -- the
        vendor module's own files are not modified by this module.
    """,
    'version': '19.0.1.0.0',
    'category': 'Website',
    'license': 'LGPL-3',
    'depends': ['website', 'crm', 'sgc_offplan_rental_property_management'],
    'data': [
        'views/brochure_button_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sgc_brochure_leadcapture/static/src/css/brochure_lead.css',
            'sgc_brochure_leadcapture/static/src/js/brochure_lead.js',
        ],
    },
    'installable': True,
}
