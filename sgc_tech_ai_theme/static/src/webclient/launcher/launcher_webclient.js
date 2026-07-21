/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { WebClient } from '@web/webclient/webclient';
import { Launcher } from '@sgc_tech_ai_theme/webclient/launcher/launcher';

/**
 * Register the SGC Enterprise Application Launcher into the WebClient.
 * Kept as its own patch file (mirroring appsbar/webclient.js) so the two
 * features stay independently traceable in the diff, even though both
 * patches target the same WebClient.components object.
 */
patch(WebClient, {
    components: {
        ...WebClient.components,
        Launcher,
    },
});
