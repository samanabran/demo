/** @odoo-module **/

/**
 * SGC AI Powerbox — registers the /sgcai Powerbox command on Odoo 19.
 *
 * Rewritten for Odoo 19's html_editor plugin architecture (released ~Q1 2025),
 * which replaces the pre-19 Wysiwyg.prototype.getConfig hook with proper
 * Plugin classes registered on the editor's Plugins array.
 *
 * Strategy:
 *   1. Define a Plugin class (SgcAIPowerboxPlugin) with `resources =
 *      { user_commands, powerbox_categories, powerbox_items }` following the
 *      same pattern as emoji_plugin.js / banner_plugin.js / chatgpt_translate_plugin.js.
 *   2. Patch HtmlField.prototype.getConfig so it appends our plugin class to the
 *      existing `Plugins` array (which already contains MAIN_PLUGINS, etc.).
 *      We can't mutate MAIN_PLUGINS directly because it's a frozen constant.
 *
 * Runtime behavior:
 *   - Type `/sgcai` in any editable area to open the Powerbox.
 *   - The item appears under a new category "SGC AI".
 *   - When selected, the plugin reads the selection text, calls the
 *     /sgc_ai_powerbox/get_response RPC route (see controllers/main.py), and
 *     replaces the selection with the AI response.
 */

import { Plugin } from "@html_editor/plugin";
import { HtmlField } from "@html_editor/fields/html_field";
import { withSequence } from "@html_editor/utils/resource";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";

const RPC_URL = "/sgc_ai_powerbox/get_response";
const THINKING_PLACEHOLDER = "🌀 Asking SGC AI…";

export class SgcAIPowerboxPlugin extends Plugin {
    static id = "sgc_ai";
    static dependencies = ["history", "dom", "selection", "userCommand"];
    /** @type {import("plugins").EditorResources} */
    resources = {
        powerbox_categories: [
            withSequence(80, {
                id: "sgc_ai",
                name: _t("SGC AI"),
            }),
        ],
        user_commands: [
            {
                id: "sgcai",
                title: _t("Ask SGC AI"),
                description: _t("Replace the selection with a response from SGC AI."),
                icon: "fa-magic",
                run: () => this.executeSgcai(),
            },
        ],
        powerbox_items: [
            {
                categoryId: "sgc_ai",
                commandId: "sgcai",
            },
        ],
    };

    async executeSgcai() {
        const selection = this.dependencies.selection.getEditableSelection();
        const selectedText = (selection?.textContent?.() || "").trim();
        if (!selectedText) {
            this.services.notification.add(
                _t("Select some text first, then run the /sgcai command."),
                { type: "warning" }
            );
            return;
        }

        // Insert a placeholder while waiting for the response so the user sees
        // something is happening. dom.insert wraps plain strings in a paragraph
        // when needed — emojipicker-style insertion here replaces the selection.
        const insertedNodes = this.dependencies.dom.insert(THINKING_PLACEHOLDER);
        this.dependencies.history.addStep();

        let response;
        try {
            response = await rpc(RPC_URL, { prompt: selectedText });
        } catch (error) {
            // Best-effort: remove the placeholder block and surface the error.
            if (Array.isArray(insertedNodes)) {
                for (const node of insertedNodes) {
                    node?.parentNode?.removeChild(node);
                }
            }
            const message =
                error?.data?.message ||
                error?.message ||
                _t("SGC AI request failed. Check the server logs.");
            this.services.notification.add(message, { type: "danger" });
            return;
        }

        // Backend returns either { response: "..." } or { error: "..." }.
        const aiText = response?.response;
        const errText = response?.error;

        // Remove the placeholder nodes we inserted.
        if (Array.isArray(insertedNodes)) {
            for (const node of insertedNodes) {
                node?.parentNode?.removeChild(node);
            }
        }

        if (errText) {
            this.services.notification.add(errText, { type: "danger" });
            return;
        }
        if (!aiText) {
            this.services.notification.add(_t("SGC AI returned an empty response."), {
                type: "warning",
            });
            return;
        }

        this.dependencies.dom.insert(aiText);
        this.dependencies.history.addStep();
        this.dependencies.selection.focusEditable();
        this.services.notification.add(_t("SGC AI content inserted."), { type: "success" });
    }
}

// Inject our Plugin class into the editor. We patch HtmlField.getConfig so the
// append happens in the same merge step that includes MAIN_PLUGINS.
patch(HtmlField.prototype, {
    getConfig() {
        const config = super.getConfig();
        const plugins = Array.isArray(config.Plugins) ? config.Plugins : [];
        if (!plugins.includes(SgcAIPowerboxPlugin)) {
            config.Plugins = [...plugins, SgcAIPowerboxPlugin];
        }
        return config;
    },
});
