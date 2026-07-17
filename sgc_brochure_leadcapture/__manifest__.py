{
    'name': 'SGC Brochure Lead Capture',
    'summary': 'Download Brochure button + lead-capture popup on the property detail page',
    'description': """
        Adds a "Download Brochure" button to the offplan property detail
        page. Clicking it opens a modal (Name/Email/Phone). Submitting the
        form creates a crm.lead, then triggers the existing dynamically
        generated PDF report (sgc_offplan_rental_property_management's own
        action_report_property_brochure) for download.

        Button/modal are injected client-side (see static/src/js) rather
        than via QWeb inherit_id/xpath -- the vendor module's own files are
        not modified by this module either way.
    """,
    'version': '19.0.1.0.0',
    'category': 'Website',
    'license': 'LGPL-3',
    'depends': ['website', 'crm', 'sgc_offplan_rental_property_management'],
    'data': [],
    'assets': {
        # The offplan property detail page only references the split
        # web.assets_frontend_minimal/_lazy bundles (Odoo 19), not the
        # generic web.assets_frontend -- registering there alone meant this
        # file never loaded on that page at all. Included in both for
        # compatibility with pages that still reference the older bundle.
        'web.assets_frontend': [
            'sgc_brochure_leadcapture/static/src/css/brochure_lead.css',
            'sgc_brochure_leadcapture/static/src/js/brochure_lead.js',
        ],
        'web.assets_frontend_lazy': [
            'sgc_brochure_leadcapture/static/src/css/brochure_lead.css',
            'sgc_brochure_leadcapture/static/src/js/brochure_lead.js',
        ],
    },
    'installable': True,
}
