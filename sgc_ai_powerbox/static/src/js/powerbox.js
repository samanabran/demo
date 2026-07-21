/** @odoo-module **/

/**
 * SGC AI Powerbox — registers the /sgcai Powerbox command on Odoo 19.
 *
 * Strategy:
 *   1. Define a Plugin class (SgcAIPowerboxPlugin) with `resources =
 *      { user_commands, powerbox_categories, powerbox_items }` following the
 *      same pattern as emoji_plugin.js / banner_plugin.js / chatgpt_translate_plugin.js.
 *   2. Patch HtmlField.prototype.getConfig so it appends our plugin class to
 *      the existing `Plugins` array (which already contains MAIN_PLUGINS, etc.).
 *
 * Runtime behavior:
 *   - Type `/sgcai` in any html_field to open the Powerbox.
 *   - The item appears under a new category "SGC AI".
 *   - When selected, the plugin opens a dialog with a textarea so the user
 *     can type a prompt (or, if text was pre-selected, edit / extend it).
 *     The response is inserted at the caret via dom.insert + history.addStep.
 *   - The backend (controllers/main.py) is also passed the current record
 *     context (resModel, resId, fieldName) and the current field value so
 *     the AI can answer with awareness of the open record.
 */

import { Plugin } from "@html_editor/plugin";
import { HtmlField } from "@html_editor/fields/html_field";
import { withSequence } from "@html_editor/utils/resource";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";

const RPC_URL = "/sgc_ai_powerbox/get_response";

// Inline template is intentionally simple: we forward `prompt` and `busy` via
// component state and call `props.onConfirm(prompt)`. The parent (the plugin)
// owns the actual RPC + insert logic and returns `{ error }` to surface
// failures, otherwise closes the dialog.
const SgcAIPromptDialog = {
    name: "SgcAIPromptDialog",
    props: {
        initialPrompt: { type: String, optional: true },
        title: { type: String, optional: true },
        helpText: { type: String, optional: true },
        placeholder: { type: String, optional: true },
        onConfirm: { type: Function },
        close: { type: Function },
    },
    data() {
        return {
            prompt: this.props.initialPrompt || "",
            busy: false,
            error: "",
        };
    },
    methods: {
        async confirm() {
            const value = (this.prompt || "").trim();
            if (!value) return;
            this.busy = true;
            this.error = "";
            try {
                const result = await this.props.onConfirm(value);
                if (result && result.error) {
                    this.error = result.error;
                    this.busy = false;
                    return;
                }
                this.props.close();
            } catch (e) {
                this.error =
                    e?.data?.message ||
                    e?.message ||
                    "SGC AI request failed. Check the server logs.";
                this.busy = false;
            }
        },
        cancel() {
            if (this.busy) return;
            this.props.close();
        },
    },
    template: /* xml */ `
        <Dialog title="props.title" size="'md'" footer="true">
            <div class="o_sgc_ai_powerbox_dialog p-3">
                <p t-if="props.helpText" class="text-muted small mb-2" t-esc="props.helpText"/>
                <textarea
                    class="form-control"
                    rows="6"
                    t-att-placeholder="props.placeholder"
                    t-model="prompt"
                />
                <div t-if="error" class="alert alert-danger mt-3 mb-0" role="alert">
                    <t t-esc="error"/>
                </div>
            </div>
            <t t-set-slot="footer">
                <button class="btn btn-secondary" t-on-click="cancel" t-att-disabled="busy">
                    Cancel
                </button>
                <button class="btn btn-primary"
                        t-on-click="confirm"
                        t-att-disabled="busy || !prompt.trim()">
                    <span t-if="busy">Thinking…</span>
                    <span t-else="">Ask SGC AI</span>
                </button>
            </t>
        </Dialog>
    `,
};

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

    _getRecordContext() {
        // HtmlField exposes `getRecordInfo` via its config; the plugin context
        // (set up by editor.js getEditorContext) passes `this.config` through.
        try {
            const info = this.config?.getRecordInfo?.();
            if (!info) return {};
            return {
                res_model: info.resModel,
                res_id: info.resId,
                record_name: info.data?.display_name || info.data?.name || "",
            };
        } catch (_) {
            return {};
        }
    }

    _getCurrentFieldText() {
        // The current field's html is what the user is editing. dom doesn't
        // give us the live value, but we can read `editable.textContent` which
        // for collapsed selections at the end is essentially the whole doc.
        try {
            return (this.editable.textContent || "").slice(0, 4000);
        } catch (_) {
            return "";
        }
    }

    async executeSgcai() {
        const selection = this.dependencies.selection.getEditableSelection();
        const selectedText = (selection?.textContent?.() || "").trim();

        const recordContext = this._getRecordContext();
        const fieldSnapshot = this._getCurrentFieldText();

        this.dependencies.dialog.addDialog(SgcAIPromptDialog, {
            title: _t("Ask SGC AI"),
            initialPrompt: selectedText || "",
            placeholder: _t(
                "Ask anything. The AI response will be inserted into the editor."
            ),
            helpText: selectedText
                ? _t("Editing your selected text. The AI will rewrite / extend it.")
                : _t(
                    "Type a prompt. The AI response will be inserted at the cursor."
                ),
            onConfirm: async (prompt) => {
                return await this._askAiAndInsert(prompt, {
                    ...recordContext,
                    field_text: fieldSnapshot,
                });
            },
        });
    }

    async _askAiAndInsert(prompt, context) {
        let response;
        try {
            response = await rpc(RPC_URL, { prompt, context });
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
        // and inserts the content at the caret.
        this.dependencies.dom.insert(aiText);
        this.dependencies.history.addStep();
        this.dependencies.selection.focusEditable();
        this.services.notification.add(_t("SGC AI content inserted."), {
            type: "success",
        });
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