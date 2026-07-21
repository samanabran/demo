/** @odoo-module **/

import { useService } from '@web/core/utils/hooks';
import { user } from '@web/core/user';
import { url } from '@web/core/utils/urls';
import { Component, useState, useRef, useEffect } from '@odoo/owl';
import { LauncherGrid } from '@sgc_tech_ai_theme/webclient/launcher/launcher_grid';
import { LauncherSearch } from '@sgc_tech_ai_theme/webclient/launcher/launcher_search';
import { LauncherSettings } from '@sgc_tech_ai_theme/webclient/launcher/launcher_settings';

const RECENTS_MAX = 8;
const USAGE_DEBOUNCE_MS = 2000;

function recentsStorageKey() {
    return `sgc_launcher_recents_${user.userId}`;
}

/**
 * SGC Enterprise Application Launcher — full-screen overlay root.
 *
 * Opened on demand from a trigger in AppsBar (via the sgc_launcher
 * service), this is the "premium OS home screen" surface the brief
 * mandates — distinct from and complementary to the always-visible
 * AppsBar rail. See artifacts/launcher-plan.md for the full rationale.
 */
export class Launcher extends Component {
    static template = 'sgc_tech_ai_theme.Launcher';
    static components = { LauncherGrid, LauncherSearch, LauncherSettings };
    static props = {};

    setup() {
        this.launcherService = useService('sgc_launcher');
        this.menuService = useService('menu');
        this.orm = useService('orm');
        this.state = useState(this.launcherService.state);
        this.rootRef = useRef('launcherRoot');
        this._previouslyFocusedEl = null;
        // null = show the app grid; Array = show search results (US-007).
        this.searchState = useState({ results: null });
        // Settings (US-011): seeded from session_info (US-002) so the
        // very first paint already uses the user's real preferences —
        // no flash-of-default before an RPC resolves. user.activeCompany
        // is the same surface appsbar.js reads sgc_theme_mode from.
        const company = user.activeCompany || {};
        this.settingsState = useState({
            grid_density: company.launcher_grid_density || 'comfortable',
            icon_size: company.launcher_icon_size || 'medium',
            animation_speed: company.launcher_animation_speed || 'normal',
            background_style: company.launcher_background_style || 'gradient',
            // imageVersion is a cache-buster counter bumped after every
            // successful per-user background upload so backgroundImageUrl
            // returns a fresh URL the next render.
            imageVersion: 0,
        });
        this.settingsPanelState = useState({ open: false });
        // Favorites (US-008): items are sgc.launcher.favorite records
        // {id, menu_id, sequence}, kept in server order.
        this.favoritesState = useState({ items: [] });
        // Frequently-used (US-010): items are sgc.launcher.usage records
        // {id, menu_id, use_count}, server-ordered by use_count desc.
        // Declared here (not a lazy getter) — useState() must be called
        // synchronously during setup(), never from a getter invoked
        // later during render.
        this.usageState = useState({ items: [] });
        // Per-(uid,menu_id) debounce timers for frequently-used tracking
        // (US-010). Not reactive state on purpose — purely internal
        // bookkeeping, never read by the template.
        this._usageTimers = new Map();

        useEffect(
            (open) => {
                if (!open) {
                    return undefined;
                }
                this._previouslyFocusedEl = document.activeElement;
                this._focusInitialElement();
                // Bubble phase (no `true`): lets the search input's
                // Escape handler stopPropagation work — otherwise the
                // first Escape would close the Launcher before the
                // search component could clear its query.
                document.addEventListener('keydown', this._onGlobalKeyDown);
                this._loadFavorites();
                return () => {
                    document.removeEventListener('keydown', this._onGlobalKeyDown);
                    this._restoreFocus();
                };
            },
            () => [this.state.open],
        );
    }

    // ------------------------------------------------------------------
    // App data + selection
    // ------------------------------------------------------------------

    get apps() {
        return this.menuService.getApps();
    }

    /**
     * Favorites ordered by their persisted sequence, resolved against
     * the live apps list so an unpinned/uninstalled app never renders
     * (Array.filter drops any favorite record whose app no longer
     * exists — e.g. after an uninstall — without needing a DB cleanup).
     */
    get favoriteApps() {
        const appsById = new Map(this.apps.map((a) => [a.id, a]));
        return this.favoritesState.items
            .map((item) => appsById.get(item.menu_id))
            .filter(Boolean);
    }

    get favoriteMenuIds() {
        return new Set(this.favoritesState.items.map((item) => item.menu_id));
    }

    /**
     * Recent apps (US-009): purely client-side, no server round-trip.
     * Stored as an ordered array of menu ids in localStorage, keyed per
     * user so switching accounts on the same browser doesn't bleed
     * recency data across users.
     */
    get recentApps() {
        const ids = this._readRecentIds();
        const appsById = new Map(this.apps.map((a) => [a.id, a]));
        return ids.map((id) => appsById.get(id)).filter(Boolean);
    }

    /**
     * Frequently-used apps (US-010): ordered by the server-side
     * use_count, loaded alongside favorites since both are per-user
     * launcher personalization data.
     */
    get frequentApps() {
        const appsById = new Map(this.apps.map((a) => [a.id, a]));
        return this.usageState.items
            .map((item) => appsById.get(item.menu_id))
            .filter(Boolean);
    }

    /**
     * Selecting an app closes the Launcher, hands off to the same
     * menuService.selectMenu() AppsBar itself uses, records recency
     * (US-009, client-side, synchronous) and schedules a debounced
     * frequently-used increment (US-010, server-side, fire-and-forget,
     * dispatched only after navigation has begun so it never blocks the
     * click-to-navigate path).
     */
    _onAppSelect(app) {
        this.menuService.selectMenu(app);
        this._recordRecent(app.id);
        this._scheduleUsageIncrement(app.id);
        this.close();
    }

    // ------------------------------------------------------------------
    // Favorites (US-008)
    // ------------------------------------------------------------------

    async _loadFavorites() {
        const [favoriteRecords, usageRecords] = await Promise.all([
            this.orm.searchRead(
                'sgc.launcher.favorite',
                [['user_id', '=', user.userId]],
                ['menu_id', 'sequence'],
                { order: 'sequence' },
            ),
            this.orm.searchRead(
                'sgc.launcher.usage',
                [['user_id', '=', user.userId]],
                ['menu_id', 'use_count'],
                { order: 'use_count desc', limit: 8 },
            ),
        ]);
        this.favoritesState.items = favoriteRecords;
        this.usageState.items = usageRecords;
    }

    isFavorite(app) {
        return this.favoriteMenuIds.has(app.id);
    }

    async _onTogglePin(app) {
        const existing = this.favoritesState.items.find((item) => item.menu_id === app.id);
        if (existing) {
            await this.orm.unlink('sgc.launcher.favorite', [existing.id]);
            this.favoritesState.items = this.favoritesState.items.filter(
                (item) => item.id !== existing.id,
            );
            return;
        }
        const maxSequence = this.favoritesState.items.reduce(
            (max, item) => Math.max(max, item.sequence),
            0,
        );
        const [newId] = await this.orm.create('sgc.launcher.favorite', [
            { menu_id: app.id, sequence: maxSequence + 10 },
        ]);
        this.favoritesState.items = [
            ...this.favoritesState.items,
            { id: newId, menu_id: app.id, sequence: maxSequence + 10 },
        ];
    }

    /**
     * Persists a full reordered menu-id list from LauncherGrid's native
     * HTML5 drag/drop by rewriting every favorite's sequence to a fresh
     * 10-step ladder matching the new order. Simpler and more robust
     * than diffing old vs new order for a "handful of pinned apps" list.
     */
    async _onReorderFavorites(orderedMenuIds) {
        const byMenuId = new Map(this.favoritesState.items.map((item) => [item.menu_id, item]));
        const updated = [];
        const writes = [];
        orderedMenuIds.forEach((menuId, index) => {
            const item = byMenuId.get(menuId);
            if (!item) {
                return;
            }
            const sequence = (index + 1) * 10;
            updated.push({ ...item, sequence });
            if (item.sequence !== sequence) {
                writes.push(this.orm.write('sgc.launcher.favorite', [item.id], { sequence }));
            }
        });
        this.favoritesState.items = updated;
        await Promise.all(writes);
    }

    // ------------------------------------------------------------------
    // Recent apps (US-009) — client-side only
    // ------------------------------------------------------------------

    _readRecentIds() {
        try {
            const raw = window.localStorage.getItem(recentsStorageKey());
            const parsed = raw ? JSON.parse(raw) : [];
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            // Corrupted/unavailable localStorage must never break the
            // Launcher — recents degrade to empty, nothing else does.
            return [];
        }
    }

    _recordRecent(menuId) {
        try {
            const ids = this._readRecentIds().filter((id) => id !== menuId);
            ids.unshift(menuId);
            window.localStorage.setItem(
                recentsStorageKey(),
                JSON.stringify(ids.slice(0, RECENTS_MAX)),
            );
        } catch {
            // Same as above: storage failures are silently ignored.
        }
    }

    // ------------------------------------------------------------------
    // Frequently used (US-010) — debounced server-side counter
    // ------------------------------------------------------------------

    /**
     * Trailing debounce keyed by menu_id: repeat clicks on the same app
     * within USAGE_DEBOUNCE_MS collapse into a single increment. The
     * RPC itself is fire-and-forget and failure-silent — a dropped
     * usage-count write must never surface an error to the user or
     * affect navigation, which has already been dispatched by the time
     * this timer fires.
     */
    _scheduleUsageIncrement(menuId) {
        const existingTimer = this._usageTimers.get(menuId);
        if (existingTimer) {
            clearTimeout(existingTimer);
        }
        const timer = setTimeout(() => {
            this._usageTimers.delete(menuId);
            this.orm
                .call('sgc.launcher.usage', 'increment_use', [[menuId]])
                .catch(() => {
                    // Failure-silent by design; see class docstring.
                });
        }, USAGE_DEBOUNCE_MS);
        this._usageTimers.set(menuId, timer);
    }

    // ------------------------------------------------------------------
    // Background styles (US-012)
    // ------------------------------------------------------------------

    /**
     * `image` -> per-user res.users.launcher_background_image (binary
     * uploaded via the settings panel's file input).
     * `company_branding` -> company-wide res.company.background_image
     * (admin-managed from Settings / SGC Theme Branding).
     * Anything else returns null and the panel uses solid/gradient rules.
     */
    get backgroundImageUrl() {
        const style = this.settingsState.background_style;
        if (style === 'image') {
            const company = user.activeCompany;
            if (!company || !company.has_launcher_background_image) {
                return null;
            }
            const base = url('/web/image', {
                model: 'res.users',
                field: 'launcher_background_image',
                id: user.userId,
            });
            // Cache-bust after an upload: bumping imageVersion forces the
            // getter to return a fresh URL the next render, sidestepping
            // the browser's /web/image cache (which is keyed on the static
            // model/field/id tuple and would otherwise serve the prior bytes).
            return this.settingsState.imageVersion ? `${base}?v=${this.settingsState.imageVersion}` : base;
        }
        if (style === 'company_branding') {
            const company = user.activeCompany;
            if (!company || !company.has_background_image) {
                return null;
            }
            return url('/web/image', {
                model: 'res.company',
                field: 'background_image',
                id: company.id,
            });
        }
        return null;
    }

    get panelStyle() {
        const bgUrl = this.backgroundImageUrl;
        return bgUrl ? `--sgc-launcher-bg-image: url('${bgUrl}')` : '';
    }

    // ------------------------------------------------------------------
    // Settings (US-011)
    // ------------------------------------------------------------------

    _onOpenSettings() {
        this.settingsPanelState.open = true;
    }

    _onCloseSettings() {
        this.settingsPanelState.open = false;
    }

    /**
     * Optimistic local update (reflected immediately, no wait on the
     * network) followed by a real write to res.users so the value
     * survives reload and reaches session_info on next boot (US-002).
     */
    async _onSettingsChange(field, value) {
        this.settingsState[field] = value;
        await this.orm.write('res.users', [user.userId], {
            [`launcher_${field}`]: value,
        });
    }

    /**
     * Persist a freshly uploaded per-user background image. Updates the
     * in-memory has_* flag immediately (so the settings panel's Remove
     * button can render without waiting on a /web reload) and bumps
     * imageVersion so backgroundImageUrl cache-busts on the next render.
     */
    async _onImageUpload(base64) {
        await this.orm.write('res.users', [user.userId], {
            launcher_background_image: base64,
        });
        const company = user.activeCompany;
        if (company) {
            company.has_launcher_background_image = true;
        }
        this.settingsState.imageVersion = Date.now();
    }

    /**
     * Clear the per-user background image. Same optimistic-local +
     * real-write pattern as _onImageUpload, plus the imageVersion bump
     * so the next render drops the cache-bust param entirely.
     */
    async _onImageRemove() {
        await this.orm.write('res.users', [user.userId], {
            launcher_background_image: false,
        });
        const company = user.activeCompany;
        if (company) {
            company.has_launcher_background_image = false;
        }
        this.settingsState.imageVersion = 0;
    }

    // ------------------------------------------------------------------
    // Search (US-007)
    // ------------------------------------------------------------------

    _onSearchResultsChange(results) {
        this.searchState.results = results;
    }

    /**
     * A command_provider result's `action` may be a callable or an
     * action descriptor depending on the provider; both are handled by
     * Odoo's own action service pattern of "call it, or dispatch it".
     * Defensive: an unrecognized shape just closes the Launcher without
     * throwing, rather than crashing the component tree.
     */
    _onCommandSelect(item) {
        try {
            if (typeof item.action === 'function') {
                item.action();
            }
        } finally {
            this.close();
        }
    }

    // ------------------------------------------------------------------
    // Open / close
    // ------------------------------------------------------------------

    close() {
        this.launcherService.close();
        // Reset search on every close path (X button, backdrop, Escape,
        // app select) so reopening always starts at the fresh app grid
        // rather than showing a stale result list from the prior session
        // — confirmed live (Stage 2) that without this reset, the old
        // LauncherSearch instance is destroyed/remounted with query=''
        // on reopen, but this component's own searchState.results
        // survives (it lives on Launcher, not LauncherSearch) and stays
        // stale until a new keystroke overwrites it.
        this.searchState.results = null;
    }

    _onCloseClick() {
        this.close();
    }

    /**
     * Close only when the click target is the backdrop itself, not a
     * descendant — the dialog panel stops propagation via t-on-click.stop
     * in the template, but this guard is kept as defense-in-depth.
     */
    _onBackdropClick(ev) {
        if (ev.target === ev.currentTarget) {
            this.close();
        }
    }

    // ------------------------------------------------------------------
    // Focus management (WAI-ARIA dialog pattern)
    // ------------------------------------------------------------------

    _getFocusableElements() {
        const root = this.rootRef.el;
        if (!root) {
            return [];
        }
        const selector = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
        ].join(',');
        return Array.from(root.querySelectorAll(selector)).filter(
            (el) => el.offsetParent !== null,
        );
    }

    _focusInitialElement() {
        // Close button is always present even before search/grid land.
        const root = this.rootRef.el;
        if (!root) {
            return;
        }
        const initial = root.querySelector('.sgc_launcher_close');
        if (initial && typeof initial.focus === 'function') {
            initial.focus();
        }
    }

    _restoreFocus() {
        const el = this._previouslyFocusedEl;
        this._previouslyFocusedEl = null;
        if (el && typeof el.focus === 'function') {
            el.focus();
        }
    }

    /**
     * Bound as a class field (not a prototype method) so the same
     * reference can be added/removed from document in useEffect.
     */
    _onGlobalKeyDown = (ev) => {
        if (!this.state.open) {
            return;
        }
        if (ev.key === 'Escape') {
            ev.preventDefault();
            this.close();
            return;
        }
        if (ev.key === 'Tab') {
            this._trapTabKey(ev);
        }
    };

    _trapTabKey(ev) {
        const focusable = this._getFocusableElements();
        if (!focusable.length) {
            return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const active = document.activeElement;
        if (ev.shiftKey && active === first) {
            ev.preventDefault();
            last.focus();
        } else if (!ev.shiftKey && active === last) {
            ev.preventDefault();
            first.focus();
        }
    }
}
