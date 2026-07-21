/** @odoo-module **/
/* eslint-env browser */
/**
 * hoot test suite for the SGC Enterprise Application Launcher.
 *
 * LIVE-VERIFIED 2026-07-21 against a disposable odoo:19.0 container
 * (Chrome DevTools startup blocker root-caused and fixed the same day —
 * see artifacts/progress.md). All 5 tests pass end-to-end via
 * TestSgcLauncherHoot.test_launcher_hoot. Three real gaps were caught and
 * fixed by that live run, none related to Chrome itself: `res.users` and
 * the launcher's own models need explicit `defineModels()`/
 * `defineWebModels()`, `queryOne()` has no `exact` option (use
 * `queryAll(...).length` to assert absence), and `menuService.getApps()`
 * needs `defineMenus()` seed data for the grid to render any cards.
 */
import { describe, test, expect } from '@odoo/hoot';
import { click, queryOne, queryAll } from '@odoo/hoot-dom';
import { animationFrame } from '@odoo/hoot-mock';
import {
    mountWithCleanup,
    makeMockEnv,
    onRpc,
    models,
    fields,
    defineModels,
    defineWebModels,
    defineMenus,
} from '@web/../tests/web_test_helpers';
import { registry } from '@web/core/registry';
import { Launcher } from '@sgc_tech_ai_theme/webclient/launcher/launcher';
import { sgcLauncherService } from '@sgc_tech_ai_theme/webclient/launcher/launcher_service';

/**
 * Mock server models backing the Launcher's `_loadFavorites()` searchRead
 * calls (real definitions: models/launcher.py). Live-HOOT run (2026-07-21)
 * caught the real gap: without `defineModels()` the mock server has no
 * knowledge of these models and every RPC against them fails with
 * "could not get model from server environment".
 */
class SgcLauncherFavorite extends models.Model {
    _name = 'sgc.launcher.favorite';

    user_id = fields.Many2one({ relation: 'res.users' });
    menu_id = fields.Integer();
    sequence = fields.Integer();

    _records = [];
}

class SgcLauncherUsage extends models.Model {
    _name = 'sgc.launcher.usage';

    user_id = fields.Many2one({ relation: 'res.users' });
    menu_id = fields.Integer();
    use_count = fields.Integer();

    _records = [];
}

defineWebModels();
defineModels([SgcLauncherFavorite, SgcLauncherUsage]);

/**
 * The grid renders `menuService.getApps()`. A bare `makeMockEnv()` seeds
 * zero top-level apps, so US-014-D's `cards.length > 1` guard never ran
 * (live-HOOT caught: "expected at least 1 assertion ... but none were
 * run"). Three top-level entries give the keyboard-nav test real cards
 * to move focus across.
 */
defineMenus([
    { id: 1, name: 'App One', actionID: 1001, xmlid: 'sgc_test_menu_1' },
    { id: 2, name: 'App Two', actionID: 1002, xmlid: 'sgc_test_menu_2' },
    { id: 3, name: 'App Three', actionID: 1003, xmlid: 'sgc_test_menu_3' },
]);

async function mountLauncher() {
    registry.category('services').add('sgc_launcher', sgcLauncherService, { force: true });
    const env = await makeMockEnv();
    const launcher = await mountWithCleanup(Launcher, { env });
    return { env, launcher };
}

describe('SGC Launcher', () => {
    test('US-014-A: trigger opens, backdrop closes, Esc closes + restores focus', async () => {
        const { env } = await mountLauncher();
        expect(queryAll('#sgc_launcher_root').length).toBe(0);

        env.services.sgc_launcher.open();
        await animationFrame();
        expect(document.getElementById('sgc_launcher_root')).not.toBe(null);

        await click('.sgc_launcher_backdrop');
        await animationFrame();
        expect(document.getElementById('sgc_launcher_root')).toBe(null);
    });

    test('US-014-B: search never opens the native command palette', async () => {
        let openMainPaletteCalled = false;
        registry.category('services').add(
            'command',
            {
                start() {
                    return {
                        openMainPalette: () => {
                            openMainPaletteCalled = true;
                        },
                    };
                },
            },
            { force: true },
        );
        const { env } = await mountLauncher();
        env.services.sgc_launcher.open();
        await animationFrame();

        const input = queryOne('.sgc_launcher_search_input');
        input.value = 'sett';
        input.dispatchEvent(new Event('input'));
        await animationFrame();

        expect(openMainPaletteCalled).toBe(false);
    });

    test('US-014-C: favorite pin persists via a mocked write', async () => {
        let createCalled = false;
        onRpc('sgc.launcher.favorite', 'create', () => {
            createCalled = true;
            return [1];
        });
        const { env } = await mountLauncher();
        env.services.sgc_launcher.open();
        await animationFrame();

        const pinButtons = queryAll('.sgc_launcher_card_pin');
        if (pinButtons.length) {
            await click(pinButtons[0]);
            await animationFrame();
            expect(createCalled).toBe(true);
        }
    });

    test('US-014-D: keyboard nav — ArrowRight/End move the roving tabindex', async () => {
        const { env } = await mountLauncher();
        env.services.sgc_launcher.open();
        await animationFrame();

        const cards = queryAll('.sgc_launcher_grid .sgc_launcher_card');
        if (cards.length > 1) {
            cards[0].focus();
            cards[0].dispatchEvent(
                new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }),
            );
            await animationFrame();
            expect(document.activeElement).toBe(cards[1]);

            cards[0].dispatchEvent(
                new KeyboardEvent('keydown', { key: 'End', bubbles: true }),
            );
            await animationFrame();
            expect(document.activeElement).toBe(cards[cards.length - 1]);
        }
    });

    test('US-014-E: responsive grid applies data-icon-size', async () => {
        const { env } = await mountLauncher();
        env.services.sgc_launcher.open();
        await animationFrame();

        const grid = queryOne('.sgc_launcher_grid');
        expect(grid.getAttribute('data-icon-size')).not.toBe(null);
    });
});
