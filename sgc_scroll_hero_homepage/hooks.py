def uninstall_hook(env):
    website = env['website'].search([], limit=1)
    if website and website.homepage_url == '/scroll-hero-home':
        website.homepage_url = False
