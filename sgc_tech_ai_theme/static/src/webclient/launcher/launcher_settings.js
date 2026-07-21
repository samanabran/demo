/** @odoo-module **/

import { Component, useState } from '@odoo/owl';

/**
 * Launcher personalization panel: grid density, icon size, animation
 * speed, background style, and (when background style = Image) a file
 * input that uploads a per-user background image via orm.write.
 *
 * Each non-file field writes immediately on change (no separate Save step
 * — matches the brief's "each user may customize" framing as live
 * preferences, not a form to submit). The file input is fire-and-forget
 * per file selection: the parent (Launcher) reads the file's bytes,
 * strips the data-URL prefix, and persists via orm.write on res.users.
 */
export class LauncherSettings extends Component {
    static template = 'sgc_tech_ai_theme.LauncherSettings';
    static props = {
        settings: Object, // reactive {grid_density, icon_size, animation_speed, background_style, imageVersion}
        hasBackgroundImage: Boolean, // mirrors user.activeCompany.has_launcher_background_image
        onChange: Function, // (field: string, value: string) => void
        onImageUpload: Function, // (base64: string) => Promise<void>
        onImageRemove: Function, // () => Promise<void>
        onClose: Function,
    };

    setup() {
        // Pure UI flag — controls disabled state of the upload button
        // while the FileReader + orm.write round-trip is in flight, so
        // a fast double-click can't fire two concurrent uploads.
        this.uploadState = useState({ uploading: false });
    }

    _onFieldChange(field, ev) {
        this.props.onChange(field, ev.target.value);
    }

    /**
     * Read the picked file as a base64 data URL, strip the
     * `data:<mime>;base64,` prefix (Odoo stores Binary fields as raw
     * base64, not as a data URL), and hand the bytes to the parent.
     */
    _onFileChange(ev) {
        const file = ev.target.files && ev.target.files[0];
        if (!file) {
            return;
        }
        const reader = new FileReader();
        reader.onload = async () => {
            this.uploadState.uploading = true;
            try {
                const dataUrl = String(reader.result || '');
                const commaIdx = dataUrl.indexOf(',');
                const base64 = commaIdx >= 0 ? dataUrl.slice(commaIdx + 1) : dataUrl;
                await this.props.onImageUpload(base64);
            } finally {
                this.uploadState.uploading = false;
                // Clear the input so re-selecting the same file fires onchange.
                ev.target.value = '';
            }
        };
        reader.onerror = () => {
            // Silent: a read failure here is rare and the upload button
            // is hidden behind background_style=image, so a stale UI
            // (button not resetting) is preferable to a user-facing
            // toast they can't act on.
            this.uploadState.uploading = false;
            ev.target.value = '';
        };
        reader.readAsDataURL(file);
    }

    _onRemoveClick() {
        this.props.onImageRemove();
    }
}
