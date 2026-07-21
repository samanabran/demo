import { patch } from '@web/core/utils/patch';
import { WebClient } from '@web/webclient/webclient';
import { AppsBar } from '@sgc_tech_ai_theme/webclient/appsbar/appsbar';

/**
 * Register the SGC-branded AppsBar sidebar into the WebClient.
 * The sidebar appears between the navbar and the main content area.
 */
patch(WebClient, {
    components: {
        ...WebClient.components,
        AppsBar,
    },
});