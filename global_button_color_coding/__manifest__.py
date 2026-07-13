# -*- coding: utf-8 -*-
{
    'name': 'Global Button Color Coding',
    'version': '19.0.1.0.0',
    'category': 'Technical/Web',
    'summary': 'Consistent button color coding across all Odoo modules',
    'description': """
        Global Button Color Coding
        =========================

        Applies consistent color coding to ALL buttons across the Odoo database:

        - Green: Confirm, Accept, Approve, Activate, Done, Complete
        - Red: Cancel, Reject, Terminate, Delete
        - Yellow: Draft, Reset, Edit, Hold
        - Light Blue: Start, Submit, Begin, In Progress

        This module uses CSS + JavaScript to dynamically recolor buttons
        based on their text labels. No view modifications are required.

        SAFE TO INSTALL:
        - Non-invasive: Only adds CSS/JS, no view overrides
        - Reversible: Uninstall to restore default colors
        - Compatible: Works with all installed modules
    """,
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['web', 'base'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'global_button_color_coding/static/src/css/button_colors.css',
            'global_button_color_coding/static/src/js/button_color_coding.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
