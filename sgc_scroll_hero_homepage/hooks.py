# -*- coding: utf-8 -*-


def uninstall_hook(env):
    """Revert the website homepage redirect this module set up on install.

    We only ever point homepage_url at our own page; clearing it here keeps
    the swap fully reversible instead of leaving a dangling redirect once
    this module's page record is deleted.
    """
    website = env['website'].search([], limit=1)
    if website and website.homepage_url == '/property-showcase-home':
        website.homepage_url = False
