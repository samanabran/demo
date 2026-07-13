/** @odoo-module **/

/**
 * Chart.js Global Shim
 * Ensures Chart.js is available both as window.Chart and as an Odoo module
 */

// Chart.js should already be loaded via the UMD bundle in assets
// This shim just verifies it's available
if (!window.Chart) {
    console.error('[Chart Shim] Chart.js not found on window. Check asset bundle loading order.');
} else {
    console.log('[Chart Shim] Chart.js v' + (window.Chart.version || 'unknown') + ' loaded successfully');
}

export const Chart = window.Chart;
