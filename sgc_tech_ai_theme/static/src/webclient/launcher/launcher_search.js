/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component, useState, useRef } from '@odoo/owl';

/**
 * Launcher search — full WAI-ARIA combobox pattern.
 *
 * - Input is `role="combobox"` with `aria-autocomplete="list"`,
 *   `aria-controls` pointing at the result listbox, `aria-expanded`
 *   reflecting whether results are visible, and `aria-activedescendant`
 *   tracking the currently-focused option. Focus stays on the input;
 *   arrow keys change aria-activedescendant instead of moving focus,
 *   matching the ARIA 1.2 combobox-with-list-autocomplete pattern that
 *   is the standard for screen readers.
 * - Results render inside a `role="listbox"` container; each option is
 *   a `role="option"` with a stable id (`sgc_launcher_result_<index>`)
 *   and `aria-selected="true|false"` tracking active state.
 * - A polite live region announces result counts so screen-reader users
 *   hear feedback when results appear or disappear.
 *
 * Reads `command_provider` registry directly (same providers Odoo's
 * native Ctrl+K palette consumes). Deliberately does NOT use
 * `useService('command')` / `openMainPalette()` — that would stack
 * Odoo's own palette on top of the Launcher, giving two search UIs.
 *
 * VERIFIED against a live Odoo 19.0-20251222 instance (Stage 2,
 * disposable Docker stack): the `command_provider` registry has 4
 * entries — 3 unnamespaced and 1 with `namespace: "/"`. The
 * unnamespaced providers are NOT app/menu search (one is a "visible
 * on-screen elements" focus helper that throws without the richer
 * DOM-context options object this search box doesn't supply; the
 * others returned zero results for real queries). The actual
 * app/menu-name search lives specifically under the "/" namespace
 * and returns `{name, category: 'apps'|'menu_items', action}` entries.
 */
export class LauncherSearch extends Component {
    static template = 'sgc_tech_ai_theme.LauncherSearch';
    static props = {
        onResultsChange: Function, // (results: Array|null) => void; null = show the app grid
        onCommandSelect: Function, // (item) => void; runs the action + closes the launcher
    };

    setup() {
        this.state = useState({
            query: '',
            // null = no search active (parent should show the app grid);
            // [] = active search, no matches; [...] = active search with matches.
            results: null,
            // -1 = input has no active descendant; 0..N-1 = option at that index.
            activeIndex: -1,
        });
        this.inputRef = useRef('searchInput');
    }

    async _onInput(ev) {
        const query = ev.target.value;
        this.state.query = query;
        if (!query) {
            this._reset({ keepQuery: false });
            return;
        }
        const results = await this._search(query);
        this.state.results = results;
        this.state.activeIndex = results.length ? 0 : -1;
        this.props.onResultsChange(results);
    }

    _onKeyDown(ev) {
        if (ev.key === 'Escape') {
            if (this.state.query) {
                // First Escape clears the search; a second one (caught
                // by the Launcher's global listener) closes the dialog.
                ev.stopPropagation();
                this._reset({ keepQuery: false });
            }
            return;
        }

        // All remaining keys only act when there are results to act on.
        const results = this.state.results;
        if (!Array.isArray(results) || !results.length) {
            return;
        }
        const max = results.length - 1;
        switch (ev.key) {
            case 'ArrowDown':
                ev.preventDefault();
                this.state.activeIndex = this.state.activeIndex < max
                    ? this.state.activeIndex + 1
                    : 0;
                break;
            case 'ArrowUp':
                ev.preventDefault();
                this.state.activeIndex = this.state.activeIndex > 0
                    ? this.state.activeIndex - 1
                    : max;
                break;
            case 'Home':
                ev.preventDefault();
                this.state.activeIndex = 0;
                break;
            case 'End':
                ev.preventDefault();
                this.state.activeIndex = max;
                break;
            case 'Enter':
                if (this.state.activeIndex >= 0) {
                    ev.preventDefault();
                    this._selectResult(results[this.state.activeIndex]);
                }
                break;
        }
    }

    /**
     * Clear the search and notify the parent so the app grid returns.
     * Called by Escape (search-clear path), and internally on empty
     * input. Note: we do NOT reset focus — focus naturally stays on the
     * input element, which is exactly what the combobox pattern wants.
     */
    _reset({ keepQuery } = { keepQuery: false }) {
        if (!keepQuery) {
            this.state.query = '';
        }
        this.state.results = null;
        this.state.activeIndex = -1;
        this.props.onResultsChange(null);
    }

    _selectResult(item) {
        this.props.onCommandSelect(item);
    }

    /**
     * Reads registry.category('command_provider') and awaits the "/"
     * (action/menu-name search) provider's provide(env, options). See
     * the class-level comment for the live-verification finding that
     * corrected this from an earlier "default namespace" assumption.
     */
    async _search(searchValue) {
        const category = registry.category('command_provider');
        const providers = typeof category.getAll === 'function' ? category.getAll() : [];
        const options = { searchValue };
        const collected = [];
        for (const provider of providers) {
            if (!provider || typeof provider.provide !== 'function') {
                continue;
            }
            if (provider.namespace !== '/') {
                continue;
            }
            try {
                const provided = await provider.provide(this.env, options);
                if (Array.isArray(provided)) {
                    collected.push(...provided);
                }
            } catch {
                // A single misbehaving provider must never break search
                // for the rest, or block the Launcher from rendering.
                continue;
            }
        }
        return collected;
    }
}