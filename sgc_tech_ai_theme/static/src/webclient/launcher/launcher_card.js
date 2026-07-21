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
     * Prefers a matching SGC icon (US-006 family) over Odoo's own
     * per-module webIconData; falls back to webIconData, then the
     * generic base icon, when no rule matches. See launcher_icon_map.js.
     */
    get iconSrc() {
        const key = resolveLauncherIconKey(this.props.app);
        if (key) {
            return `${ICON_BASE_URL}/${key}.svg`;
        }
        return this.props.app.webIconData || '/base/static/description/icon.png';
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
