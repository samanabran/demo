/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";

/**
 * Format a number with accounting-style formatting.
 * @param {number} value
 * @param {Object} [opts]
 * @param {boolean} [opts.creditNegative=true] Show negative as (123.45)
 * @param {number} [opts.decimals=2]
 * @returns {string}
 */
function _fmt(value, opts) {
    if (value === null || value === undefined || isNaN(value)) return "";
    const cfg = Object.assign({ creditNegative: true, decimals: 2 }, opts);
    const abs = Math.abs(value);
    const formatted = abs.toLocaleString(undefined, {
        minimumFractionDigits: cfg.decimals,
        maximumFractionDigits: cfg.decimals,
    });
    if (value < 0 && cfg.creditNegative) {
        return `(${formatted})`;
    }
    return value < 0 ? `-${formatted}` : formatted;
}

/**
 * Render inline drill-down HTML for move lines (journal entries).
 * @param {string} accountName
 * @param {Object} data - { lines: Array, totals: Object }
 * @returns {string}
 */
function renderMoveLinesHtml(accountName, data) {
    const lines = data.lines || [];
    const totals = data.totals || {};
    const rows = lines
        .map(
            (line) => `
        <tr>
            <td class="sgc-col-text">${line.date || ""}</td>
            <td class="sgc-col-text">${_escapeHtml(line.move_name || "")}</td>
            <td class="sgc-col-text">${_escapeHtml(line.partner || "")}</td>
            <td class="sgc-col-text">${_escapeHtml(line.ref || line.description || "")}</td>
            <td class="sgc-col-text" style="text-align: right;">${_fmt(line.debit)}</td>
            <td class="sgc-col-text" style="text-align: right;">${_fmt(line.credit)}</td>
            <td class="sgc-col-text" style="text-align: right;">${_fmt(line.balance)}</td>
        </tr>`
        )
        .join("");

    return `
    <div class="sgc-drilldown-panel">
        <table class="table table-sm table-striped o_sgc_report_table sgc-drilldown-table mb-0">
            <thead>
                <tr>
                    <th class="sgc-col-text">Date</th>
                    <th class="sgc-col-text">Move</th>
                    <th class="sgc-col-text">Partner</th>
                    <th class="sgc-col-text">Ref / Description</th>
                    <th class="sgc-col-text" style="text-align: right;">Debit</th>
                    <th class="sgc-col-text" style="text-align: right;">Credit</th>
                    <th class="sgc-col-text" style="text-align: right;">Balance</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td colspan="4" class="sgc-col-text" style="text-align: right;"><strong>Total</strong></td>
                    <td style="text-align: right;">${_fmt(totals.debit)}</td>
                    <td style="text-align: right;">${_fmt(totals.credit)}</td>
                    <td style="text-align: right;">${_fmt(totals.balance)}</td>
                </tr>
            </tfoot>
        </table>
        <p class="small text-muted text-end mt-1 mb-0">
            <i class="fa fa-chevron-up me-1"/> Click again to collapse
        </p>
    </div>`;
}

/**
 * Escape HTML special characters in a string.
 * @param {string} str
 * @returns {string}
 */
function _escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

/**
 * Attach a click-delegated drilldown handler to a report container.
 * Idempotent — guarded by a dataset flag so it can safely be called
 * on every OWL patched cycle.
 *
 * @param {HTMLElement} containerEl - The .o_sgc_report_container element
 * @param {number} wizardId - The active wizard ID for RPC calls
 */
export function attachDrilldownHandler(containerEl, wizardId) {
    if (!containerEl) return;
    if (containerEl.dataset.sgcDrilldownAttached) return;

    containerEl.dataset.sgcDrilldownAttached = "1";

    containerEl.addEventListener("click", async (ev) => {
        const expandBtn = ev.target.closest(".o_sgc_expand_drilldown");
        if (!expandBtn) return;

        const accountRow = expandBtn.closest("tr");
        if (!accountRow) return;

        const accountId = parseInt(accountRow.dataset.accountId, 10);
        if (!accountId) return;

        // Check if already expanded
        const existingPanel = accountRow.nextElementSibling;
        if (existingPanel && existingPanel.classList.contains("sgc-drilldown-panel-row")) {
            // Collapse
            existingPanel.remove();
            expandBtn.innerHTML = '<i class="fa fa-chevron-down me-1"/> Expand';
            return;
        }

        // Toggle icon to loading
        expandBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"/>';

        try {
            const response = await fetch(`/sgc/dfr/drilldown/${wizardId}/${accountId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": session.csrf_token,
                },
                body: JSON.stringify({}),
            });
            const data = await response.json();

            if (data.error) {
                expandBtn.innerHTML = '<i class="fa fa-exclamation-triangle text-danger me-1"/> Error';
                return;
            }

            // Render drill-down row
            const drilldownRow = document.createElement("tr");
            drilldownRow.className = "sgc-drilldown-panel-row";
            const drilldownCell = document.createElement("td");
            drilldownCell.setAttribute("colspan", accountRow.cells.length);
            drilldownCell.innerHTML = renderMoveLinesHtml(
                accountRow.dataset.accountName || "",
                data
            );
            drilldownRow.appendChild(drilldownCell);
            accountRow.insertAdjacentElement("afterend", drilldownRow);

            expandBtn.innerHTML = '<i class="fa fa-chevron-up me-1"/> Collapse';
        } catch (_err) {
            expandBtn.innerHTML = '<i class="fa fa-exclamation-triangle text-danger me-1"/> Failed';
        }
    });
}
