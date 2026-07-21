/** @odoo-module **/

import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";

/**
 * SGC Enterprise Application Launcher — shared open/close state.
 *
 * A plain bus event can signal "open" but can't drive a boolean the
 * trigger button's aria-expanded needs to track, since AppsBar (the
 * trigger owner) and Launcher (the dialog owner) are sibling components
 * with no parent/child relationship. A service exposing a single
 * reactive state object is the standard Odoo/OWL way to share that state:
 * both components call useState() on the same underlying reactive object
 * and re-render whenever either mutates it.
 */
export const sgcLauncherService = {
    start() {
        const state = reactive({ open: false });
        return {
            state,
            open() {
                state.open = true;
            },
            close() {
                state.open = false;
            },
            toggle() {
                state.open = !state.open;
            },
        };
    },
};

registry.category("services").add("sgc_launcher", sgcLauncherService);
