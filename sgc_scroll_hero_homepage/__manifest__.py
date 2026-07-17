{
    'name': 'SGC Scroll Hero Homepage',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Cinematic scroll-triggered frame-sequence hero homepage with property search',
    'description': """
Adds a cinematic scroll-triggered frame-sequence hero as a native Website
Builder snippet ("Storytelling" category), wires its search bar to the
existing property search route, and republishes it as the site homepage.
Purely additive: does not modify sgc_offplan_rental_property_management or
sgc_realestate_website.
""",
    'author': 'SGC',
    'depends': ['website', 'sgc_offplan_rental_property_management'],
    'data': [
        'views/snippets/s_re_scroll_hero.xml',
        'views/snippets/snippets.xml',
        'views/homepage.xml',
        'data/set_homepage_url.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sgc_scroll_hero_homepage/static/src/css/scroll_hero.css',
            'sgc_scroll_hero_homepage/static/src/js/scroll_hero.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'uninstall_hook': 'uninstall_hook',
}
