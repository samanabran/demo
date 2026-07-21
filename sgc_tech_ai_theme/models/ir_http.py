# (c) SGC TECH AI
# License: OPL-1
# See LICENSE in root directory.
"""SGC Tech AI Theme — ``session_info`` extension.

Patches :func:`ir.http.session_info` to expose per-company branding flags
(``has_background_image``, ``has_appsbar_image``) — pre-existing — AND the
``sgc_theme_mode`` company default that was previously a silent no-op
(see ``appsbar.js:_loadTheme`` reading ``user.activeCompany.sgc_theme_mode``
without this method exposing it).

Adds the four SGC Enterprise Application Launcher per-user preferences on the
same per-company entry. They are sourced from the *user* record but mirrored
on every company the user has access to, because the JS client reads them off
``user.activeCompany.*`` for consistency with the existing theme-mode read.
"""
from __future__ import annotations

from odoo import models


class IrHttp(models.AbstractModel):
    """Expose company branding flags through session info."""

    _inherit = 'ir.http'

    def session_info(self) -> dict:
        result = super().session_info()
        if not self.env.user._is_internal():
            return result
        allowed = result['user_companies']['allowed_companies']
        # Read user prefs once (the user is the same for every loop iter).
        user = self.env.user
        user_prefs = {
            'launcher_grid_density': user.launcher_grid_density,
            'launcher_icon_size': user.launcher_icon_size,
            'launcher_animation_speed': user.launcher_animation_speed,
            'launcher_background_style': user.launcher_background_style,
            # has_* mirrors launcher_background_image so the JS can decide
            # whether to render a background-image URL without ever having
            # to pull the binary through session_info (bin_size=True would
            # still inflate every boot with the user's uploaded bytes).
            'has_launcher_background_image': bool(user.launcher_background_image),
        }
        companies = self.env.user.company_ids.with_context(bin_size=True)
        for company in companies:
            entry = allowed.get(company.id)
            if not entry:
                continue
            entry.update({
                # Pre-existing branding flags (preserved unchanged).
                'has_background_image': bool(company.background_image),
                'has_appsbar_image': bool(company.appbar_image),
                # Revived company default — previously dead because never
                # exposed here. After this ships, companies with Theme
                # Mode = Dark will actually default their users to dark.
                # Recorded as a deliberate behavior change in CHANGES.md.
                'sgc_theme_mode': company.sgc_theme_mode,
                # Per-user Launcher preferences mirrored on each company
                # entry so JS reads them off the same user.activeCompany.*
                # surface as the theme-mode flag above.
                **user_prefs,
            })
        return result
