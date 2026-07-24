{
    "name": "SGC Design Tokens",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "Deep Navy + Gold + Ivory design-token system shared across all SGC public-facing pages",
    "description": """
Single source of truth for the SGC brand palette, typography, and base
component styling (cards, buttons, badges, forms, hairlines). Loaded into
web.assets_frontend, which is the common ancestor bundle for website pages,
the customer portal, and the /web/login page alike - one stylesheet reaches
all three surfaces without per-surface wiring.

Purely additive: does not replace or duplicate any existing module's
functionality, only supplies shared CSS variables and generic-class styling
that sgc_scroll_hero_homepage, sgc_scroll_hero_v2, and
sgc_offplan_rental_property_management build on top of.
""",
    "author": "SGC",
    "depends": ["web"],
    "data": [
        "views/frontend_layout_head.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "sgc_design_tokens/static/src/css/01_tokens.css",
            "sgc_design_tokens/static/src/css/02_base.css",
            "sgc_design_tokens/static/src/css/03_components.css",
        ],
    },
    "installable": True,
    "application": False,
    "license": "OPL-1",
}
