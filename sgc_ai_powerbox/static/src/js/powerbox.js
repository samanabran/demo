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
 *   2. Patch HtmlField.prototype.getConfig so it appends our plugin class to
 *      the existing `Plugins` array (which already contains MAIN_PLUGINS, etc.).
 *
 * Runtime behavior:
 *   - Type `/sgcai` in any editable area to open the Powerbox.
 *   - The item appears under a new category "SGC AI".
 *   - When selected, the plugin opens a dialog with a textarea so the user
 *     can type a prompt OR (if text was pre-selected in the editor) edit /
 *     extend it before sending. The response is inserted into the editor at
 *     the selection position via dom.insert + history.addStep.
 *   - This avoids the previous UX failure where running /sgcai with an empty
 *     selection just bounced back a "please select text first" warning.
 */

import { Plugin } from "@html_editor/plugin";
import { HtmlField } from "@html_editor/fields/html_field";
import { Dialog } from "@web/core/dialog/dialog";
import { withSequence } from "@html_editor/utils/resource";
import { Component, useState, xml } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

const RPC_URL = "/sgc_ai_powerbox/get_response";

export class SgcAIPromptDialog extends Component {
    static template = xml`
        <Dialog title="props.title" size="'md'" onClose="() => this.props.close()">
            <div class="o_sgc_ai_powerbox_dialog p-3">
                <p t-if="props.helpText" class="text-muted small mb-2" t-esc="props.helpText"/>
                <textarea
                    class="form-control"
                    rows="6"
                    placeholder="props.placeholder"
                    t-model="state.prompt"
                    t-ref="textarea"
                />
                <div t-if="state.error" class="alert alert-danger mt-3 mb-0" role="alert">
                    <t t-esc="state.error"/>
                </div>
            </div>
            <t t-set-slot="footer">
                <button class="btn btn-secondary" t-on-click="cancel" disabled="state.busy">
                    Cancel
                </button>
                <button class="btn btn-primary" t-on-click="confirm" disabled="state.busy or !state.prompt.trim()">
                    <span t-if="state.busy">Thinking…</span>
                    <span t-else="">Ask SGC AI</span>
                </button>
            </t>
        </Dialog>
    `;
    static components = { Dialog };
    static props = {
        initialPrompt: { type: String, optional: true },
        title: { type: String, optional: true },
        helpText: { type: String, optional: true },
        placeholder: { type: String, optional: true },
        onConfirm: { type: Function },
        close: { type: Function },
    };

    setup() {
        this.notificationService = useService("notification");
        this.state = useState({
            prompt: this.props.initialPrompt || "",
            busy: false,
            error: "",
        });
    }

    cancel() {
        if (this.state.busy) return;
        this.props.close();
    }

    async confirm() {
        const prompt = this.state.prompt.trim();
        if (!prompt) return;
        this.state.busy = true;
        this.state.error = "";
        try {
            const response = await this.props.onConfirm(prompt);
            if (response && response.error) {
                this.state.error = response.error;
                this.state.busy = false;
                return;
            }
            this.props.close();
        } catch (error) {
            const message =
                error?.data?.message ||
                error?.message ||
                _t("SGC AI request failed. Check the server logs.");
            this.state.error = message;
            this.state.busy = false;
        }
    }
}

export class SgcAIPowerboxPlugin extends Plugin {
    static id = "sgc_ai";
    static dependencies = ["history", "dom", "selection", "userCommand", "dialog"];
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
                description: _t("Open a chat prompt. The response is inserted at the cursor."),
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

        // dom.insert already deletes the current selection when not collapsed,
        // so we don't need to do anything special here — we just need to know
        // whether the user had pre-selected text so the dialog can be helpful.

        this.dependencies.dialog.addDialog(SgcAIPromptDialog, {
            title: _t("Ask SGC AI"),
            initialPrompt: selectedText || "",
            placeholder: _t(
                "Ask anything. The AI response will be inserted into the editor."
            ),
            helpText: selectedText
                ? _t("Editing your selected text. The AI will rewrite / extend it.")
                : _t("Type a prompt. The AI response will be inserted at the cursor."),
            onConfirm: async (prompt) => {
                return await this._askAiAndInsert(prompt);
            },
        });
    }

    async _askAiAndInsert(prompt) {
        let response;
        try {
            response = await rpc(RPC_URL, { prompt });
        } catch (error) {
            return {
                error:
                    error?.data?.message ||
                    error?.message ||
                    _t("SGC AI request failed. Check the server logs."),
            };
        }

        const aiText = response?.response;
        const errText = response?.error;
        if (errText) return { error: errText };
        if (!aiText) return { error: _t("SGC AI returned an empty response.") };

        // dom.insert(content) deletes the current selection (if not collapsed)
        // and inserts the content at the caret. This is exactly the behavior
        // we want for both "replace selection" and "insert at cursor" cases.
        this.dependencies.dom.insert(aiText);
        this.dependencies.history.addStep();
        this.dependencies.selection.focusEditable();
        this.services.notification.add(_t("SGC AI content inserted."), { type: "success" });
        return null;
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