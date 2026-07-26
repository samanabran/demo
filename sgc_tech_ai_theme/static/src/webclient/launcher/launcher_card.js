/** @odoo-module **/

import { Component } from '@odoo/owl';
import { resolveLauncherIconKey } from '@sgc_tech_ai_theme/webclient/launcher/launcher_icon_map';

const ICON_BASE_URL = '/sgc_tech_ai_theme/static/src/webclient/launcher/icons';

/**
 * A single application tile in the Launcher grid.
 *
 * Favorite/notification state is read-only here (US-005 scope); the
 * pin/unpin write path lands in US-008, notification counts stay a
 * stub (0) until a real source is wired.
 */
export class LauncherCard extends Component {
    static template = 'sgc_tech_ai_theme.LauncherCard';
    static props = {
        app: Object,
        favorite: { type: Boolean, optional: true },
        notificationCount: { type: Number, optional: true },
        onSelect: Function,
        onTogglePin: { type: Function, optional: true },
        tabIndex: { type: Number, optional: true },
    };
    static defaultProps = {
        favorite: false,
        notificationCount: 0,
        tabIndex: -1,
    };

    /**
     * Prefers each app's own webIconData (the real per-app icon, set
     * via ir.ui.menu.web_icon) over the generic SGC category SVG map;
     * the generic map (launcher_icon_map.js) is only a fallback for
     * apps with no icon of their own at all.
     */
    get iconSrc() {
        if (this.props.app.webIconData) {
            return this.props.app.webIconData;
        }
        const key = resolveLauncherIconKey(this.props.app);
        if (key) {
            return `${ICON_BASE_URL}/${key}.svg`;
        }
        return '/base/static/description/icon.png';
    }

    _onClick() {
        this.props.onSelect(this.props.app);
    }

    _onKeyDown(ev) {
        if (ev.key === 'Enter' || ev.key === ' ' || ev.key === 'Spacebar') {
            ev.preventDefault();
            this.props.onSelect(this.props.app);
        }
    }

    _onPinClick(ev) {
        ev.stopPropagation();
        if (this.props.onTogglePin) {
            this.props.onTogglePin(this.props.app);
        }
    }
}
