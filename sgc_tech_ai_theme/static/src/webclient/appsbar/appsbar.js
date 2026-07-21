import { url } from '@web/core/utils/urls';
import { useService } from '@web/core/utils/hooks';
import { user } from '@web/core/user';
import { Component, onWillUnmount, useState, onMounted } from '@odoo/owl';


/**
 * SGC Enterprise Sidebar (AppsBar)
 *
 * Renders a vertical left sidebar with all installed app icons.
 * Collapsed by default (icon-only), expandable to show labels.
 * Uses SGC midnight background with gold accent highlights.
 *
 * Accessibility (WCAG 2.1 AA):
 * - Keyboard navigation (Tab, Enter, Space, Arrow keys, Home, End)
 * - Roving tabindex pattern within the menubar
 * - aria-current="page" for the active app
 * - aria-expanded on the toggle button
 * - Screen-reader friendly labels on all interactive elements
 */
export class AppsBar extends Component {
    static template = 'sgc_tech_ai_theme.AppsBar';
    static props = {};

    setup() {
        this.menuService = useService('menu');
        this.state = useState({ expanded: false });
        this.menuRef = { el: null };

        // SGC Enterprise Application Launcher trigger — the service is
        // the shared reactive state between this button (aria-expanded)
        // and the Launcher component (open/close), since they're sibling
        // components with no parent/child relationship.
        this.launcherService = useService('sgc_launcher');
        this.launcherState = useState(this.launcherService.state);

        // Load custom sidebar logo from company if set
        if (user.activeCompany.has_appsbar_image) {
            this.sidebarImageUrl = url('/web/image', {
                model: 'res.company',
                field: 'appbar_image',
                id: user.activeCompany.id,
            });
        }

        // Re-render when the active app changes
        const onAppChanged = () => this.render();
        this.env.bus.addEventListener('MENUS:APP-CHANGED', onAppChanged);
        onWillUnmount(() => {
            this.env.bus.removeEventListener('MENUS:APP-CHANGED', onAppChanged);
        });

        onMounted(() => this._loadTheme());
    }

    get apps() {
        return this.menuService.getApps();
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    getMenuItemHref(app) {
        return `/odoo/${app.actionPath || 'action-' + app.actionID}`;
    }

    _onAppClick(app) {
        return this.menuService.selectMenu(app);
    }

    /**
     * Returns true when the given app is the active one.
     * Exposed to the template so each menu item can decide its own
     * aria-current / tabindex without the template re-deriving logic.
     */
    isActiveApp(app) {
        const current = this.currentApp;
        return !!(current && app && app.id === current.id);
    }

    /**
     * Roving-tabindex helper: the active item is the focusable stop,
     * every other item is reachable via arrow keys (tabindex="-1").
     */
    getMenuItemTabIndex(app) {
        return this.isActiveApp(app) ? '0' : '-1';
    }

    _toggleSidebar() {
        this.state.expanded = !this.state.expanded;
        const body = document.body;
        body.classList.toggle('sgc_sidebar_type_expanded', this.state.expanded);
        body.classList.toggle('sgc_sidebar_type_collapsed', !this.state.expanded);
        // Announce the new state to assistive tech.
        const liveRegion = document.getElementById('sgc_appsbar_live_region');
        if (liveRegion) {
            liveRegion.textContent = this.state.expanded
                ? 'Sidebar expanded'
                : 'Sidebar collapsed';
        }
    }

    // ------------------------------------------------------------------
    // Theme (Dark / Light) Toggle
    // ------------------------------------------------------------------

    /**
     * Returns true when data-bs-theme="dark" is set on <html>.
     */
    get isDarkMode() {
        return document.documentElement.getAttribute('data-bs-theme') === 'dark';
    }

    /**
     * Set the theme on <html> and persist the user's override.
     * @param {boolean|null} forceDark - true=dark, false=light, null=toggle
     */
    _applyTheme(forceDark = null) {
        const dark = forceDark !== null ? forceDark : !this.isDarkMode;
        document.documentElement.setAttribute('data-bs-theme', dark ? 'dark' : 'light');
        const html = document.documentElement;
        html.classList.toggle('sgc_theme_dark', dark);
        html.classList.toggle('sgc_theme_light', !dark);
        // Persist user override in session storage (survives page reload)
        sessionStorage.setItem('sgc_theme_override', dark ? 'dark' : 'light');
    }

    /**
     * Load theme from: session override > company default.
     */
    _loadTheme() {
        const override = sessionStorage.getItem('sgc_theme_override');
        if (override === 'dark') {
            this._applyTheme(true);
            return;
        }
        if (override === 'light') {
            this._applyTheme(false);
            return;
        }
        // Fall back to company default
        const companyDark = user.activeCompany.sgc_theme_mode === 'dark';
        if (companyDark) {
            this._applyTheme(true);
        }
    }

    /**
     * Toggle between dark and light themes.
     */
    _toggleTheme() {
        this._applyTheme(!this.isDarkMode);
    }

    // ------------------------------------------------------------------
    // Keyboard navigation (WAI-ARIA Authoring Practices "menubar" pattern)
    // ------------------------------------------------------------------

    /**
     * Returns the list of focusable menuitem elements inside the menubar.
     * Cached per call so we don't re-query the DOM on every keypress.
     */
    _getMenuItemElements() {
        const root = this.menuRef.el;
        if (!root) {
            return [];
        }
        return Array.from(root.querySelectorAll('.sgc_appsbar_menu .nav-link'));
    }

    _focusItemAt(index) {
        const items = this._getMenuItemElements();
        if (!items.length) {
            return;
        }
        const clamped = ((index % items.length) + items.length) % items.length;
        const target = items[clamped];
        if (target && typeof target.focus === 'function') {
            target.focus();
        }
    }

    _focusNextItem(direction) {
        const items = this._getMenuItemElements();
        if (!items.length) {
            return;
        }
        const active = document.activeElement;
        const currentIndex = items.indexOf(active);
        const fallback = currentIndex === -1 ? 0 : currentIndex;
        this._focusItemAt(fallback + direction);
    }

    _focusFirstItem() {
        this._focusItemAt(0);
    }

    _focusLastItem() {
        const items = this._getMenuItemElements();
        this._focusItemAt(items.length - 1);
    }

    /**
     * Bound to each menu item via t-on-keydown. Implements the menubar
     * keyboard contract: Enter/Space activate, arrow keys rove focus,
     * Home/End jump to the ends.
     */
    _onKeyDown(ev, app) {
        switch (ev.key) {
            case 'Enter':
            case ' ':
            case 'Spacebar':
                ev.preventDefault();
                this._onAppClick(app);
                break;
            case 'ArrowDown':
                ev.preventDefault();
                this._focusNextItem(1);
                break;
            case 'ArrowUp':
                ev.preventDefault();
                this._focusNextItem(-1);
                break;
            case 'Home':
                ev.preventDefault();
                this._focusFirstItem();
                break;
            case 'End':
                ev.preventDefault();
                this._focusLastItem();
                break;
            case 'Escape':
                // Returning focus to the toggle is a common escape hatch
                // for menubars; collapse the focus chain back to its
                // entry point when the user bails out.
                ev.preventDefault();
                this._focusToggleButton();
                break;
            default:
                break;
        }
    }

    /**
     * Space scrolls the page on links by default — we already
     * activate on Space, so swallow it on the toggle too.
     */
    _onToggleKeyDown(ev) {
        if (ev.key === ' ' || ev.key === 'Spacebar') {
            ev.preventDefault();
        }
    }

    _focusToggleButton() {
        const root = this.menuRef.el;
        if (!root) {
            return;
        }
        const toggle = root.querySelector('.sgc_appsbar_toggle');
        if (toggle && typeof toggle.focus === 'function') {
            toggle.focus();
        }
    }

    // ------------------------------------------------------------------
    // SGC Enterprise Application Launcher — trigger
    // ------------------------------------------------------------------

    /**
     * Toggle the Launcher open/closed via the shared sgc_launcher
     * service. AppsBar does not own the Launcher component; it only
     * reads/mutates the shared reactive state so its own aria-expanded
     * stays in sync with whether the Launcher is actually open.
     * See static/src/webclient/launcher/launcher.js (US-004).
     */
    _openLauncher() {
        this.launcherService.toggle();
    }

    /**
     * Space is the keyboard activator for menuitem-style buttons. We
     * swallow the default scroll-on-space behavior on the launcher
     * trigger so the open action is consistent with the rest of
     * the AppsBar buttons.
     */
    _onLauncherTriggerKeyDown(ev) {
        if (ev.key === ' ' || ev.key === 'Spacebar') {
            ev.preventDefault();
        }
    }
}