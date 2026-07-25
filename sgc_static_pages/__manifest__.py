{
    "name": "SGC Static Pages",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "About and Services pages for the public real estate website",
    "description": """
Adds /about and /services as new website pages, in the Deep Navy + Gold +
Ivory design language established by sgc_design_tokens. Purely additive:
new pages and menu entries only, no changes to any existing template.
""",
    "author": "SGC",
    "depends": ["website", "sgc_design_tokens", "sgc_offplan_rental_property_management"],
    "data": [
        "views/about_page.xml",
        "views/services_page.xml",
        "data/website_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "OPL-1",
}
