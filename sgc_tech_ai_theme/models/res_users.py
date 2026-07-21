# (c) SGC TECH AI
# License: OPL-1
# See LICENSE in root directory.
"""SGC Tech AI Theme — per-user preferences on ``res.users``.

Sidebar display preference pre-existed. The four ``launcher_*`` fields were
added for the SGC Enterprise Application Launcher; see
``artifacts/launcher-plan.md`` (US-001, US-002, US-011).
"""
from odoo import fields, models


class ResUsers(models.Model):
    """Add sidebar display preference for each user."""

    _inherit = 'res.users'

    sidebar_type = fields.Selection(
        selection=[
            ('expanded', 'Expanded'),
            ('collapsed', 'Collapsed'),
            ('hidden', 'Hidden'),
        ],
        string='Sidebar',
        default='collapsed',
        required=True,
    )

    # ------------------------------------------------------------------
    # SGC Enterprise Application Launcher — per-user preferences
    # ------------------------------------------------------------------

    launcher_grid_density = fields.Selection(
        selection=[
            ('compact', 'Compact'),
            ('comfortable', 'Comfortable'),
            ('spacious', 'Spacious'),
        ],
        string='Launcher Density',
        default='comfortable',
        required=True,
        help='Density of the application launcher grid.',
    )
    launcher_icon_size = fields.Selection(
        selection=[
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('large', 'Large'),
        ],
        string='Launcher Icon Size',
        default='medium',
        required=True,
        help='Icon size in the application launcher grid.',
    )
    launcher_animation_speed = fields.Selection(
        selection=[
            ('none', 'None'),
            ('normal', 'Normal'),
            ('fast', 'Fast'),
        ],
        string='Launcher Animation Speed',
        default='normal',
        required=True,
        help='Hover/click animation speed in the application launcher. '
             'Always overridden to None when the OS reports '
             'prefers-reduced-motion: reduce.',
    )
    launcher_background_style = fields.Selection(
        selection=[
            ('solid', 'Solid'),
            ('gradient', 'Gradient'),
            ('image', 'Image'),
            ('company_branding', 'Company Branding'),
        ],
        string='Launcher Background',
        default='gradient',
        required=True,
        help='Background style of the application launcher.',
    )
    launcher_background_image = fields.Binary(
        string='Launcher Background Image',
        attachment=True,
        help='Per-user background image used when Launcher Background = Image. '
             'Distinct from the company-wide Home Menu Background Image used '
             'when Background = Company Branding.',
    )