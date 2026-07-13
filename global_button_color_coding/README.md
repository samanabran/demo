# Global Button Color Coding Module

A non-invasive Odoo module that applies consistent color coding to ALL buttons across the entire database.

## Color Scheme

| Color | Button Actions |
|-------|----------------|
| 🟢 **Green** | Confirm, Accept, Approve, Activate, Done, Complete, Validate, Post |
| 🔴 **Red** | Cancel, Reject, Terminate, Delete, Remove, Close, Reset to Draft |
| 🟡 **Yellow** | Draft, Reset, Edit, Hold, Pause, Revert, Undo |
| 🔵 **Light Blue** | Start, Submit, Begin, Create, Generate, Save, Update, Print |

## Installation

### Prerequisites
- Odoo 19.0 or later
- `web` module (core)

### Steps

1. **Copy the module** to your Odoo addons path:
   ```bash
   cp -r global_button_color_coding /path/to/odoo/addons/
   ```

2. **Update the module list**:
   - Go to Apps → Update Apps List
   - Or run: `./odoo-bin -u base`

3. **Install the module**:
   - Go to Apps → Search for "Global Button Color Coding"
   - Click Install

4. **Clear browser cache**:
   - Press Ctrl+Shift+R (hard refresh)
   - Or clear browser cache manually

## How It Works

This module uses a **CSS + JavaScript approach** that:

1. **No view modifications**: Does NOT override any XML view files
2. **Dynamic detection**: Scans buttons on page load and applies colors based on text labels
3. **Mutation observer**: Watches for dynamically added buttons (e.g., when switching views)
4. **Safe to uninstall**: Removing the module restores default colors

### Button Detection Rules

The JavaScript module uses regex patterns to match button text:

```javascript
// GREEN patterns
/confirm/i, /approve/i, /accept/i, /activate/i, /done/i, /complete/i

// RED patterns
/cancel/i, /reject/i, /terminate/i, /delete/i, /reset to draft/i

// YELLOW patterns
/draft/i, /reset/i, /edit/i, /hold/i

// BLUE patterns
/start/i, /begin/i, /submit/i, /create/i, /save/i, /update/i
```

### Excluded Buttons

The following button types are NOT recolored:
- Icon-only buttons (no text)
- Link buttons (`btn-link`)
- Close buttons (`btn-close`)
- Very small buttons (`btn-sm` with < 3 chars)

## Customization

### Adding New Patterns

Edit `static/src/js/button_color_coding.js` and add patterns to `BUTTON_COLOR_RULES`:

```javascript
const BUTTON_COLOR_RULES = [
    {
        class: "btn-action-confirm",
        patterns: [
            /confirm/i,
            /approve/i,
            // Add your custom patterns here
            /my custom action/i,
        ],
    },
    // ... other rules
];
```

### Changing Colors

Edit `static/src/css/button_colors.css` and modify the color values:

```css
.btn-action-confirm {
    background-color: #28a745 !important;  /* Change this */
    border-color: #28a745 !important;
    color: #fff !important;
}
```

## Compatibility

- ✅ Works with all Odoo modules
- ✅ Compatible with Odoo 19.0
- ✅ No conflicts with existing themes
- ✅ Safe to install/uninstall
- ✅ No database changes

## Troubleshooting

### Buttons not changing color?

1. **Clear browser cache**: Ctrl+Shift+R
2. **Update module list**: Apps → Update Apps List
3. **Upgrade the module**: Apps → Global Button Color Coding → Upgrade

### Wrong color applied?

The JavaScript matches buttons by text content. If a button has unexpected text, it may get the wrong color. Check the button's actual text content.

### Module not appearing in Apps?

1. Ensure the module is in the correct addons path
2. Run: `./odoo-bin -u base`
3. Restart Odoo server

## Technical Details

### File Structure

```
global_button_color_coding/
├── __init__.py
├── __manifest__.py
├── README.md
└── static/
    └── src/
        ├── css/
        │   └── button_colors.css
        └── js/
            └── button_color_coding.js
```

### Dependencies

- `web` (core Odoo web module)
- `base` (core Odoo base module)

### No Python Models

This module contains no Python models, views, or data files. It operates entirely through:
- CSS for styling
- JavaScript for dynamic class assignment
- MutationObserver for dynamic content

## License

LGPL-3.0
