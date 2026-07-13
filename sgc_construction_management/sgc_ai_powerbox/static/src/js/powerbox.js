/** @odoo-module **/

odoo.define('sgc_ai_powerbox.powerbox', function (require) {
    "use strict";

    const Editor = require('web_editor.Editor');

    Editor.include({
        // -----------------------------------------------------------------
        // Add a custom "/sgcai" command to the Powerbox
        // -----------------------------------------------------------------
        _getPowerboxOptions: function () {
            const options = this._super.apply(this, arguments);

            options.categories.push({
                name: 'SGC AI',
                priority: 100,
            });

            options.commands.push({
                name: 'Ask SGC AI',
                category: 'SGC AI',
                description: 'Send selected text to SGC AI and insert the response.',
                fontawesome: 'fa-robot',
                priority: 1,

                callback: function () {
                    const self = this;
                    const range = self.getSelectedRange();
                    if (!range) {
                        self._notify('Select some text first, then type /sgcai.');
                        return Promise.resolve();
                    }

                    const editable = self.$editable;
                    const selectedText = editable.text(range).trim();

                    if (!selectedText) {
                        self._notify('Selected text is empty. Select some text first.');
                        return Promise.resolve();
                    }

                    // Insert loading placeholder
                    self._replaceRange(range, '\u23f3 Thinking...');
                    self._saveSelection();

                    return self._rpc({
                        route: '/sgc_ai_powerbox/get_response',
                        params: {prompt: selectedText},
                    }).then(function (data) {
                        self._restoreSelection();
                        if (data.error) {
                            self._replaceRange(range, '\u26a0\ufe0f Error: ' + data.error);
                        } else {
                            self._replaceRange(range, data.response);
                        }
                    }).catch(function (err) {
                        self._restoreSelection();
                        self._replaceRange(range, '\u26a0\ufe0f Error: ' + (err.message || err));
                    });
                },
            });

            return options;
        },

        // -----------------------------------------------------------------
        // Helper: show a notification to the user
        // -----------------------------------------------------------------
        _notify: function (message) {
            if (this.displayNotification) {
                this.displayNotification({
                    title: 'SGC AI',
                    message: message,
                    type: 'warning',
                });
            } else {
                console.warn('SGC AI:', message);
            }
        },
    });
});
