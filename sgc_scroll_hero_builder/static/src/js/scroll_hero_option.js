/** @odoo-module **/

import { BaseOptionComponent } from "@html_builder/core/utils";
import { withSequence } from "@html_editor/utils/resource";
import { before, SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";

export class ScrollHeroOption extends BaseOptionComponent {
    static template = "sgc_scroll_hero_builder.ScrollHeroOption";
    static selector = ".s_re_scroll_hero, .s_re_scroll_hero_v2";
}

class ScrollHeroOptionPlugin extends Plugin {
    static id = "sgcScrollHeroOption";
    resources = {
        builder_options: [withSequence(before(SNIPPET_SPECIFIC_END), ScrollHeroOption)],
    };
}

registry.category("website-plugins").add(ScrollHeroOptionPlugin.id, ScrollHeroOptionPlugin);
