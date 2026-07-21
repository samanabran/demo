{
    'name': 'Enterprise AI Theme',
    'version': '19.0.1.0.0',
    'sequence': 7,
    'summary': 'SGC TECH AI Corporate Theme for Odoo',
    'author': 'SGC TECH AI',
    'license': 'OPL-1',
    'maintainer': 'SGC TECH AI',
    'company': 'SGC TECH AI',
    'website': 'https://sgctech.ai',
    'support': 'info@sgctech.ai',
    'depends': [
        'web',
    ],
    'category': 'Themes/Backend',
    'description': """
        SGC TECH AI Enterprise Theme
        =============================
        A premium corporate theme for Odoo v19 that delivers an enterprise-grade
        visual experience with the SGC TECH AI brand identity.

        Features:
        - Left sidebar (AppsBar) with gold-accented midnight design
        - SGC Brand color palette (Navy, Gold, Ivory, Charcoal, Slate)
        - Clean white navbar with institutional styling
        - Branded form inputs, buttons, alerts, and status indicators
        - Configurable sidebar logo, favicon, and home menu background
        - User-selectable sidebar mode (expanded / collapsed / hidden)
        - IBM Plex typography system
        - Full Odoo v19 OWL component compatibility
    """,
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'templates/web_layout.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'sgc_tech_ai_theme/static/src/scss/primary_variables_custom.scss'),
            'sgc_tech_ai_theme/static/src/scss/secondary_variables.scss',
        ],
        'web.assets_backend': [
            'sgc_tech_ai_theme/static/src/webclient/**/*.xml',
            'sgc_tech_ai_theme/static/src/webclient/**/*.scss',
            'sgc_tech_ai_theme/static/src/webclient/**/*.js',

            'sgc_tech_ai_theme/static/src/scss/fields_extra_custom.scss',
        ],
        'web.assets_unit_tests': [
            'sgc_tech_ai_theme/static/tests/**/*.test.js',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': '_setup_module',
    'uninstall_hook': '_uninstall_cleanup',
}