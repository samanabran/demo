/** @odoo-module **/

import { Component, useState, useRef } from '@odoo/owl';
import { LauncherCard } from '@sgc_tech_ai_theme/webclient/launcher/launcher_card';

/**
 * Responsive CSS-grid of LauncherCard tiles.
 *
 * Column count is CSS-driven (launcher_grid.scss), not JS-computed:
 * `repeat(auto-fill, minmax(var(--sgc-launcher-icon-col), 1fr))` sized
 * off the user's icon-size preference at desktop/tablet widths, with a
 * hard `repeat(3, 1fr)` override under 768px. See launcher_grid.scss for
 * the exact breakpoint values.
 *
 * When `reorderable` is set, cards become native-HTML5-draggable and
 * dropping one over another calls `onReorder(orderedMenuIds)` with the
 * full new order — used for the Favorites section (US-008). Deliberately
 * plain HTML5 drag/drop rather than an Odoo internal sortable hook,
 * since that internal API surface is unverified in this checkout (see
 * launcher_search.js's command_provider note for why unverified Odoo
 * internals get live-checked before being trusted).
 */
export class LauncherGrid extends Component {
    static template = 'sgc_tech_ai_theme.LauncherGrid';
    static components = { LauncherCard };
    static props = {
        apps: Array,
        iconSize: { type: String, optional: true },
        favoriteMenuIds: { type: Object, optional: true }, // Set<number>
        onSelect: Function,
        onTogglePin: { type: Function, optional: true },
        reorderable: { type: Boolean, optional: true },
        onReorder: { type: Function, optional: true }, // (orderedMenuIds: number[]) => void
        ariaLabel: { type: String, optional: true },
    };
    static defaultProps = {
        iconSize: 'medium',
        favoriteMenuIds: new Set(),
        reorderable: false,
        ariaLabel: 'All applications',
    };

    setup() {
        this.dnd = useState({ draggedId: null, overId: null });
        this.gridRef = useRef('gridRoot');
    }

    isFavorite(app) {
        return this.props.favoriteMenuIds.has(app.id);
    }

    // ------------------------------------------------------------------
    // Roving tabindex (WAI-ARIA menu pattern, mirrors AppsBar's existing
    // menubar keyboard contract) — US-013.
    // ------------------------------------------------------------------

    _getCardElements() {
        const root = this.gridRef.el;
        if (!root) {
            return [];
        }
        return Array.from(root.querySelectorAll(':scope > .sgc_launcher_card, :scope > .sgc_launcher_dnd_wrap > .sgc_launcher_card'));
    }

    _focusItemAt(index) {
        const items = this._getCardElements();
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
        const items = this._getCardElements();
        if (!items.length) {
            return;
        }
        const active = document.activeElement;
        const currentIndex = items.indexOf(active);
        const fallback = currentIndex === -1 ? 0 : currentIndex;
        this._focusItemAt(fallback + direction);
    }

    _onGridKeyDown(ev) {
        switch (ev.key) {
            case 'ArrowRight':
            case 'ArrowDown':
                ev.preventDefault();
                this._focusNextItem(1);
                break;
            case 'ArrowLeft':
            case 'ArrowUp':
                ev.preventDefault();
                this._focusNextItem(-1);
                break;
            case 'Home':
                ev.preventDefault();
                this._focusItemAt(0);
                break;
            case 'End':
                ev.preventDefault();
                this._focusItemAt(this._getCardElements().length - 1);
                break;
            default:
                break;
        }
    }

    _onDragStart(app, ev) {
        this.dnd.draggedId = app.id;
        ev.dataTransfer.effectAllowed = 'move';
        // Some browsers require setData to enable the drag; the value
        // itself is unused since reordering is driven by component state.
        ev.dataTransfer.setData('text/plain', String(app.id));
    }

    _onDragOver(app, ev) {
        ev.preventDefault();
        this.dnd.overId = app.id;
    }

    _onDragEnd() {
        this.dnd.draggedId = null;
        this.dnd.overId = null;
    }

    _onDrop(targetApp, ev) {
        ev.preventDefault();
        const draggedId = this.dnd.draggedId;
        this.dnd.draggedId = null;
        this.dnd.overId = null;
        if (draggedId === null || draggedId === targetApp.id) {
            return;
        }
        const order = this.props.apps.map((a) => a.id);
        const fromIndex = order.indexOf(draggedId);
        const toIndex = order.indexOf(targetApp.id);
        if (fromIndex === -1 || toIndex === -1) {
            return;
        }
        order.splice(toIndex, 0, order.splice(fromIndex, 1)[0]);
        if (this.props.onReorder) {
            this.props.onReorder(order);
        }
    }
}
