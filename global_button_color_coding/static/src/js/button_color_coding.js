/**
 * Global Button Color Coding - JavaScript Module
 * ================================================
 * Dynamically assigns color classes to buttons based on their text labels.
 *
 * Color Scheme:
 * - Green:  Confirm, Accept, Approve, Activate, Done, Complete
 * - Red:    Cancel, Reject, Terminate, Delete
 * - Yellow: Draft, Reset, Edit, Hold
 * - Blue:   Start, Submit, Begin, In Progress
 *
 * Performance notes:
 * - Observers are scoped to .o_content + .o_form_view (not the entire body)
 *   to avoid triggering on every DOM mutation across the page.
 * - A debounce prevents redundant scans during rapid OWL re-renders.
 * - Already-colored buttons are tracked via a WeakSet so we skip them on
 *   subsequent scans.
 */

/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Button text patterns mapped to color classes.
 * Order matters — first match wins.
 */
const BUTTON_COLOR_RULES = [
    // GREEN — Confirm/Approve/Success actions
    {
        class: "btn-action-confirm",
        patterns: [
            /confirm/i,
            /approve/i,
            /accept/i,
            /activate/i,
            /enable/i,
            /done/i,
            /complete/i,
            /finish/i,
            /submit for approval/i,
            /mark as paid/i,
            /mark paid/i,
            /set active/i,
            /validate/i,
            /post/i,
            /publish/i,
            /open/i,
            /resume/i,
            /reopen/i,
        ],
    },

    // RED — Cancel/Reject/Danger actions
    {
        class: "btn-action-cancel",
        patterns: [
            /cancel/i,
            /reject/i,
            /terminate/i,
            /delete/i,
            /remove/i,
            /close/i,
            /decline/i,
            /deny/i,
            /refuse/i,
            /stop/i,
            /abort/i,
            /void/i,
            /reset to draft/i,
        ],
    },

    // YELLOW — Draft/Reset/Warning actions
    {
        class: "btn-action-draft",
        patterns: [
            /draft/i,
            /reset/i,
            /edit/i,
            /hold/i,
            /pause/i,
            /set to draft/i,
            /back to draft/i,
            /return to draft/i,
            /revert/i,
            /undo/i,
        ],
    },

    // BLUE — Start/Submit/Progress actions
    {
        class: "btn-action-progress",
        patterns: [
            /start/i,
            /begin/i,
            /submit/i,
            /send/i,
            /create/i,
            /new/i,
            /add/i,
            /generate/i,
            /run/i,
            /execute/i,
            /process/i,
            /apply/i,
            /save/i,
            /update/i,
            /refresh/i,
            /load/i,
            /import/i,
            /export/i,
            /print/i,
            /download/i,
            /sign/i,
            /review/i,
        ],
    },
];

/** CSS classes this module manages — used to detect already-processed buttons. */
const MANAGED_CLASSES = [
    "btn-action-confirm",
    "btn-action-cancel",
    "btn-action-draft",
    "btn-action-progress",
];

/**
 * Tracks buttons we have already processed so we skip them on re-scans
 * without querying classList repeatedly.
 */
const processedButtons = new WeakSet();

/**
 * Get the appropriate color class for a button based on its text.
 * @param {string} buttonText
 * @returns {string|null}
 */
function getButtonColorClass(buttonText) {
    if (!buttonText) return null;
    const text = buttonText.trim();
    for (const rule of BUTTON_COLOR_RULES) {
        for (const pattern of rule.patterns) {
            if (pattern.test(text)) {
                return rule.class;
            }
        }
    }
    return null;
}

/**
 * Check whether a button should be recolored.
 * @param {HTMLElement} button
 * @returns {boolean}
 */
function shouldRecolorButton(button) {
    if (processedButtons.has(button)) return false;

    if (button.querySelector(".fa") && !button.textContent.trim()) return false;

    if (button.classList.contains("btn-sm") && button.textContent.trim().length < 3) return false;

    if (button.classList.contains("btn-link") || button.classList.contains("btn-close")) return false;

    if (button.classList.contains("btn-default")) return false;

    for (const cls of MANAGED_CLASSES) {
        if (button.classList.contains(cls)) return false;
    }

    if (button.closest(".o_statusbar_status")) return false;

    if (button.classList.contains("oe_stat_button")) return false;

    if (button.closest("header")) return false;

    return true;
}

/**
 * Apply color coding to buttons within a container.
 * @param {HTMLElement} container
 */
function applyColorCoding(container) {
    if (!container || !container.querySelectorAll) return;

    const buttons = container.querySelectorAll("button.btn, .btn, a.btn");
    if (!buttons.length) return;

    for (const button of buttons) {
        if (!shouldRecolorButton(button)) continue;

        const buttonText = button.textContent;
        const colorClass = getButtonColorClass(buttonText);
        if (!colorClass) continue;

        // Store original class for potential restoration (first encounter only).
        if (!button.dataset.originalClass) {
            button.dataset.originalClass = button.className;
        }

        // Remove any previously-applied color classes from other rules.
        button.classList.remove(
            "btn-primary",
            "btn-success",
            "btn-danger",
            "btn-warning",
            "btn-info",
            ...MANAGED_CLASSES
        );

        // Add the matched class.
        button.classList.add(colorClass);
        processedButtons.add(button);
    }
}

// ---------------------------------------------------------------------------
// Debounced observer — fires at most once per animation frame.
// ---------------------------------------------------------------------------
let debounceTimer = null;

function scheduleScan(target) {
    if (debounceTimer) return;
    debounceTimer = requestAnimationFrame(() => {
        debounceTimer = null;
        scanContentAreas();
    });
}

/** Known content containers to scan. Built up over time as DOM grows. */
const knownContainers = new Set();

function ensureContainer(el) {
    if (el && el.querySelectorAll && !knownContainers.has(el)) {
        knownContainers.add(el);
    }
}

function scanContentAreas() {
    // Always re-check for the main content wrappers in case Odoo swapped them.
    const content = document.querySelector(".o_content");
    if (content) ensureContainer(content);

    // Scan every known container.
    for (const container of knownContainers) {
        // Skip detached containers.
        if (!document.contains(container)) {
            knownContainers.delete(container);
            continue;
        }
        applyColorCoding(container);
    }
}

// ---------------------------------------------------------------------------
// Observers — scoped to high-level wrappers only.
// ---------------------------------------------------------------------------
let observersStarted = false;
let contentObserver = null;
let mainObserver = null;

function startObservers() {
    if (observersStarted) return;
    observersStarted = true;

    // Watch the main content area for new buttons (e.g. after view switches).
    const content = document.querySelector(".o_content");
    if (content) {
        contentObserver = new MutationObserver(() => scheduleScan());
        contentObserver.observe(content, { childList: true, subtree: true });
    }

    // Watch the body for new .o_content / .o_form_view wrappers (app switching).
    mainObserver = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType !== Node.ELEMENT_NODE) continue;
                const el = /** @type {HTMLElement} */ (node);
                if (
                    el.matches(".o_content, .o_form_view, .o_form_sheet") ||
                    el.querySelector?.(".o_content, .o_form_view, .o_form_sheet")
                ) {
                    scheduleScan();
                    return; // one scan per batch is enough
                }
            }
        }
    });
    mainObserver.observe(document.body, { childList: true, subtree: false });
}

let colorCodingInitialized = false;

function initColorCoding() {
    if (colorCodingInitialized) return;
    colorCodingInitialized = true;
    scanContentAreas();
    startObservers();
}

// Initialize when DOM is ready.
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initColorCoding);
} else {
    initColorCoding();
}

// Register as a service so Odoo starts it with the backend lifecycle.
registry.category("services").add("global_button_color_coding", {
    start() {
        initColorCoding();
        window.addEventListener("focus", () => {
            setTimeout(scanContentAreas, 100);
        });
    },
});

export { getButtonColorClass, applyColorCoding };
