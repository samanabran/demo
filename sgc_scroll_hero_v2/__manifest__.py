{
    'name': 'SGC Scroll Hero V2 (Test Page)',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Second cinematic scroll-triggered frame-sequence hero, with scroll-scrubbed audio, on its own test page',
    'description': """
Standalone test page at /scroll-hero-v2 reusing the proven scroll-hero engine
(DPR-clamped canvas, settle-pass redraw, smoothed scroll choreography,
centered pill search bar) from sgc_scroll_hero_homepage, applied to a second
video source, plus scroll-scrubbed soundtrack audio and an idle ambient loop.
Purely additive: does not modify sgc_scroll_hero_homepage, does not touch the
site homepage.
""",
    'author': 'SGC',
    'depends': ['website', 'sgc_offplan_rental_property_management'],
    'data': [
        'views/snippets/s_re_scroll_hero_v2.xml',
        'views/snippets/snippets.xml',
        'views/page_v2.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sgc_scroll_hero_v2/static/src/css/scroll_hero_v2.css',
            'sgc_scroll_hero_v2/static/src/js/scroll_hero_v2.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
