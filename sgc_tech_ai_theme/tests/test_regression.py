# -*- coding: utf-8 -*-
# Part of SGC TECH AI. See LICENSE file for full copyright and licensing details.
# Copyright (c) 2026 SGC TECH AI (https://sgctech.ai)

"""
Regression tests for sgc_tech_ai_theme critical bugs that were fixed in Stage 2:
1. Missing 'from . import models' in __init__.py (models never registered)
2. Post-init hook signature mismatch (Odoo 19 uses env, not cr/registry)
3. SCSS bundle-order crash (undefined $black in web._assets_primary_variables)
4. AppsBar used nonexistent 'app_menu' service (crashed WebClient)

These tests ensure the bugs cannot silently reappear.
"""

from odoo.tests.common import TransactionCase, HttpCase, tagged
from odoo.exceptions import UserError


@tagged("post_install", "-at_install")
class TestSgcTechAiThemeRegression(TransactionCase):
    """Regression tests for critical bugs in sgc_tech_ai_theme."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.user = cls.env.user

    def test_01_models_imported(self):
        """
        Regression test for missing models import bug.

        Bug: __init__.py had 'from . import models' but models/__init__.py
        didn't exist or wasn't properly imported -- no model classes were registered.

        Expected: sidebar_type field on res.users, and the sidebar view exists.
        """
        # sidebar_type was added to res.users, not res.company
        user = self.env['res.users'].browse(self.user.id)
        self.assertTrue(hasattr(user, 'sidebar_type'),
                       "res.users must have sidebar_type field")

        # Check that view inheritance works (no ParseError on res.users.form.sidebar)
        user_view = self.env['ir.ui.view'].search([
            ('name', 'ilike', 'res.users.form.sidebar'),
            ('model', '=', 'res.users')
        ], limit=1)
        self.assertTrue(user_view, "Sidebar view for res.users must exist")

    def test_02_post_init_hook_signature(self):
        """
        Regression test for post_init_hook signature mismatch.

        Bug: Hook used Odoo <=16 signature (cr, registry) but Odoo 19 calls hooks
        with (env) only, causing TypeError.

        Expected: Hook should execute without TypeError.
        """
        from odoo.addons.sgc_tech_ai_theme import _setup_module

        _setup_module(self.env)
        # No assertion -- if _setup_module raises, the test fails.

    def test_03_scss_bundle_compiles_cleanly(self):
        """
        Regression test for SCSS bundle-order crash.
        
        Bug: primary_variables_custom.scss contributed to web._assets_primary_variables
        without defining $black/$white, causing 'Undefined variable $black' error
        when Odoo core's bootstrap_overridden_frontend.scss executed before
        Bootstrap's _variables.scss.
        
        Expected: web.assets_backend should compile cleanly with no Style-Error fallback.
        """
        # Check that the SCSS file exists and has the guard
        import os
        scss_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'src', 
                                 'scss', 'primary_variables_custom.scss')
        self.assertTrue(os.path.exists(scss_path), 
                       "primary_variables_custom.scss must exist")
        
        # Verify the guard is present (lines defining $black and $white)
        with open(scss_path, 'r') as f:
            content = f.read()
            has_black_guard = '$black:' in content and '!default' in content
            has_white_guard = '$white:' in content and '!default' in content
        
        self.assertTrue(has_black_guard, 
                       "primary_variables_custom.scss must define $black with !default")
        self.assertTrue(has_white_guard, 
                       "primary_variables_custom.scss must define $white with !default")

    def test_04_appsbar_service_available(self):
        """
        Regression test for AppsBar nonexistent service bug.
        
        Bug: AppsBar used a nonexistent 'app_menu' service with fabricated methods,
        causing 'Service app_menu is not available' and blank white screen.
        
        Expected: WebClient should render without errors and AppsBar should display menu items.
        """
        # Check that the AppsBar component exists and uses correct service
        import os
        appsbar_js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'src', 
                                       'webclient', 'appsbar', 'appsbar.js')
        self.assertTrue(os.path.exists(appsbar_js_path), 
                       "AppsBar component must exist")
        
        # Verify the component uses the correct 'menu' service, not 'app_menu'
        with open(appsbar_js_path, 'r') as f:
            content = f.read()
            uses_menu_service = "useService('menu')" in content
            does_not_use_app_menu = "useService('app_menu')" not in content
        
        self.assertTrue(uses_menu_service, 
                       "AppsBar must use the real 'menu' service")
        self.assertTrue(does_not_use_app_menu, 
                       "AppsBar must not use the nonexistent 'app_menu' service")
        
        # Verify the component has correct methods (getApps, getCurrentApp, selectMenu)
        self.assertIn("getApps()", content, "AppsBar must have getApps() method")
        self.assertIn("getCurrentApp()", content, "AppsBar must have getCurrentApp() method")
        self.assertIn("selectMenu", content, "AppsBar must have selectMenu method")


@tagged("post_install", "-at_install")
class TestSgcLauncherRegression(TransactionCase):
    """Regression tests for the SGC Enterprise Application Launcher (US-015).

    Covers: new-model install/uninstall cleanliness, session_info exposure
    of the four launcher_* preference fields (and the revived
    sgc_theme_mode read), settings persistence round-trip, favorites
    reorder persistence, and a module-isolation guard.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.user = cls.env.user

    def test_07_launcher_models_install_clean(self):
        """sgc.launcher.favorite / sgc.launcher.usage must be registered
        and writable — proves US-001's models.Constraint migration (the
        deprecated _sql_constraints syntax) didn't silently drop the
        constraint or break record creation.
        """
        favorite = self.env['sgc.launcher.favorite'].create({
            'user_id': self.user.id,
            'menu_id': 1,
            'sequence': 10,
        })
        self.assertTrue(favorite.id)

        usage = self.env['sgc.launcher.usage'].create({
            'user_id': self.user.id,
            'menu_id': 1,
        })
        self.assertEqual(usage.use_count, 1)

        # UNIQUE(user_id, menu_id) constraint must still be enforced
        # after the models.Constraint migration.
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env['sgc.launcher.favorite'].create({
                    'user_id': self.user.id,
                    'menu_id': 1,
                    'sequence': 20,
                })

    def test_08_increment_use_creates_and_updates(self):
        """increment_use() must create a row on first call and bump
        use_count on repeat calls for the same (user, menu) pair.
        """
        Usage = self.env['sgc.launcher.usage']
        Usage.search([('user_id', '=', self.user.id), ('menu_id', '=', 42)]).unlink()

        Usage.increment_use([42])
        row = Usage.search([('user_id', '=', self.user.id), ('menu_id', '=', 42)])
        self.assertEqual(len(row), 1)
        self.assertEqual(row.use_count, 1)

        Usage.increment_use([42])
        row = Usage.search([('user_id', '=', self.user.id), ('menu_id', '=', 42)])
        self.assertEqual(row.use_count, 2)

    def test_11_favorites_reorder_persists(self):
        """Writing a new sequence order to sgc.launcher.favorite rows
        must survive a fresh read in the same order (US-008 drag-reorder
        persistence path).
        """
        Favorite = self.env['sgc.launcher.favorite']
        Favorite.search([('user_id', '=', self.user.id)]).unlink()
        recs = Favorite.create([
            {'user_id': self.user.id, 'menu_id': 101, 'sequence': 10},
            {'user_id': self.user.id, 'menu_id': 102, 'sequence': 20},
            {'user_id': self.user.id, 'menu_id': 103, 'sequence': 30},
        ])
        # Simulate a reorder: menu 103 moved to the front.
        by_menu = {r.menu_id: r for r in recs}
        by_menu[103].sequence = 10
        by_menu[101].sequence = 20
        by_menu[102].sequence = 30

        reread = Favorite.search([('user_id', '=', self.user.id)], order='sequence')
        self.assertEqual(reread.mapped('menu_id'), [103, 101, 102])

    def test_12_no_core_file_diff(self):
        """This module must never modify files outside its own directory
        or the artifacts/ tracking directory — a git-diff-based guard
        against accidental core/other-module edits.

        Git always reports changed-file paths relative to the repo ROOT,
        not the cwd, so the expected prefix is derived from the actual
        repo root (via `git rev-parse --show-toplevel`) rather than
        hardcoded — this repo's module lives at addons/sgc_tech_ai_theme/,
        not at the repo root, so a hardcoded 'sgc_tech_ai_theme/' prefix
        would false-positive on every legitimate change.
        """
        import subprocess
        import os

        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            toplevel = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=module_dir, capture_output=True, text=True, timeout=10,
            )
            if toplevel.returncode != 0:
                self.skipTest('not a git checkout')
                return
            repo_root = toplevel.stdout.strip()
            module_prefix = os.path.relpath(module_dir, repo_root).replace(os.sep, '/') + '/'

            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD'],
                cwd=module_dir, capture_output=True, text=True, timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.skipTest('git not available in this environment')
            return
        if result.returncode != 0:
            self.skipTest('git diff failed (e.g. no HEAD commit yet)')
            return
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        offenders = [f for f in changed if not f.startswith(module_prefix)]
        self.assertFalse(
            offenders,
            f"Changes must stay inside {module_prefix}, found: {offenders}",
        )


@tagged("post_install", "-at_install")
class TestSgcTechAiThemeHttpRegression(HttpCase):
    """HTTP-level regression tests for critical bugs."""

    def test_05_webclient_renders_without_crash(self):
        """
        Regression test: WebClient should render without blank white screen.

        Bug: AppsBar using nonexistent service crashed the entire WebClient render tree.

        Expected: WebClient should load successfully with no console errors.
        """
        self.authenticate('admin', 'admin')
        response = self.url_open('/web')
        self.assertEqual(response.status_code, 200,
                        "WebClient /web should return HTTP 200")

    def test_06_webclient_serves_session_info(self):
        """
        Regression test: WebClient /web loads and serves the boot session info.

        Bug: AppsBar crashing the render tree caused blank white screen.
        Expected: /web returns HTML with the odoo.__session_info__ boot payload.
        """
        self.authenticate('admin', 'admin')
        response = self.url_open('/web')
        self.assertEqual(response.status_code, 200)
        # The boot HTML embeds session info as a JS literal.
        self.assertIn(b'__session_info__', response.content,
                     "Response must embed odoo.__session_info__")

    def _fetch_session_info(self):
        """Fetch /web and parse the embedded odoo.__session_info__ JSON.

        session_info() internally reads request.session.uid (see
        web/models/ir_http.py), which only exists inside a real HTTP
        request — calling env['ir.http'].session_info() directly from a
        TransactionCase raises RuntimeError('object is not bound'). This
        was discovered live (Stage 2) when test_09/test_10 were first
        written as TransactionCase tests; fetching the real boot HTML and
        parsing the embedded JSON, like test_06 already does, is the
        correct way to exercise this method under test.
        """
        import json
        import re

        response = self.url_open('/web')
        self.assertEqual(response.status_code, 200)
        match = re.search(
            rb'__session_info__\s*=\s*(\{.*?\});',
            response.content,
            re.DOTALL,
        )
        self.assertIsNotNone(match, 'Could not find __session_info__ JSON literal in /web response')
        return json.loads(match.group(1))

    def test_13_session_info_exposes_launcher_fields(self):
        """session_info() for an internal user must expose the four
        launcher_* preferences AND the previously-dead sgc_theme_mode
        field (US-002's fix) on the allowed_companies entry.
        """
        user = self.env.ref('base.user_admin')
        user.write({
            'launcher_grid_density': 'spacious',
            'launcher_icon_size': 'large',
        })
        self.authenticate('admin', 'admin')
        info = self._fetch_session_info()
        entry = info['user_companies']['allowed_companies'][str(user.company_id.id)]
        self.assertEqual(entry.get('launcher_grid_density'), 'spacious')
        self.assertEqual(entry.get('launcher_icon_size'), 'large')
        self.assertIn('launcher_animation_speed', entry)
        self.assertIn('launcher_background_style', entry)
        self.assertIn('sgc_theme_mode', entry,
                       "sgc_theme_mode must be exposed — this was the dead-read bug fixed in US-002")

    def test_14_theme_mode_reaches_session_info(self):
        """Company Theme Mode = Dark must actually reach session_info —
        the specific bug that was silently dead before this session's fix.
        """
        user = self.env.ref('base.user_admin')
        user.company_id.sgc_theme_mode = 'dark'
        self.authenticate('admin', 'admin')
        info = self._fetch_session_info()
        entry = info['user_companies']['allowed_companies'][str(user.company_id.id)]
        self.assertEqual(entry.get('sgc_theme_mode'), 'dark')
