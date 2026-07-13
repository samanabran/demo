/** @odoo-module **/

import { Component, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useBus } from "@web/core/utils/hooks";

/**
 * DashboardChart field widget
 *
 * Renders a Chart.js chart onto a canvas from a JSON payload stored in a
 * `Char` field on the dashboard record. The payload format is produced by
 * `SalesInvoicingDashboard._to_chart_json()` and looks like:
 *
 *     {
 *         "labels": ["Jan", "Feb", ...],
 *         "datasets": [{"label": "...", "data": [...], ...}],
 *         "options": {"currency": "USD"}
 *     }
 *
 * The widget listens for `dashboard:filter-changed` events on the env bus
 * (emitted by `dashboard_form_controller_enhanced.js` whenever the user
 * edits a filter field) and re-renders the chart with the fresh payload.
 */
export class DashboardChart extends Component {
    static template = "sgc_invoicing_dashboard.DashboardChart";
    static props = {
        ...standardFieldProps,
        chartType: { type: String, optional: true },
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chartInstance = null;

        this.state = useState({
            loading: true,
            hasData: false,
            error: null,
        });

        // Re-render whenever the field value changes (filter edits).
        useEffect(
            () => {
                this._renderChart();
                return () => this._destroyChart();
            },
            () => [this.props.record.data[this.props.name]]
        );

        // Listen for filter changes broadcast on the bus.
        useBus(this.env.bus, "dashboard:filter-changed", () => {
            // The form controller will have updated the record fields by now;
            // re-render on the next tick so the new value is observable.
            this._renderChart();
        });
    }

    get chartState() {
        return this.state;
    }

    _safeParse(raw) {
        if (!raw) {
            return null;
        }
        try {
            const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
            if (
                !parsed ||
                typeof parsed !== "object" ||
                !Array.isArray(parsed.labels) ||
                !Array.isArray(parsed.datasets)
            ) {
                return null;
            }
            return parsed;
        } catch (err) {
            console.warn("[DashboardChart] failed to parse payload:", err, raw);
            return null;
        }
    }

    async _ensureChartLib() {
        if (typeof window.Chart !== "undefined") {
            return window.Chart;
        }
        try {
            const mod = await import("@web/chart");
            return mod.Chart || (mod.default && mod.default.Chart) || null;
        } catch (err) {
            console.warn("[DashboardChart] @web/chart import failed:", err);
            return null;
        }
    }

    async _renderChart() {
        this.state.loading = true;
        this.state.error = null;
        this._destroyChart();

        const payload = this._safeParse(this.props.record.data[this.props.name]);
        if (!payload || !payload.labels.length) {
            this.state.loading = false;
            this.state.hasData = false;
            return;
        }

        const Chart = await this._ensureChartLib();
        if (!Chart) {
            this.state.error = "Chart.js is not available in this build.";
            this.state.loading = false;
            this.state.hasData = false;
            return;
        }

        const canvas = this.canvasRef.el;
        if (!canvas) {
            this.state.loading = false;
            this.state.hasData = false;
            return;
        }

        try {
            const chartType = this.props.chartType || this._guessType(payload);
            this.chartInstance = new Chart(canvas.getContext("2d"), {
                type: chartType,
                data: {
                    labels: payload.labels,
                    datasets: payload.datasets.map((ds, idx) => ({
                        ...ds,
                        borderWidth: ds.borderWidth != null ? ds.borderWidth : 1,
                    })),
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: chartType !== "bar" || payload.labels.length <= 6 },
                    },
                    scales: chartType === "line" || chartType === "bar"
                        ? { y: { beginAtZero: true } }
                        : undefined,
                },
            });
            this.state.hasData = true;
        } catch (err) {
            console.error("[DashboardChart] render error:", err);
            this.state.error = err.message || String(err);
            this.state.hasData = false;
        } finally {
            this.state.loading = false;
        }
    }

    _guessType(payload) {
        // Heuristic: doughnut for short categorical lists, bar for longer.
        if (payload.labels.length <= 5 && payload.datasets.length <= 1) {
            return "doughnut";
        }
        return "bar";
    }

    _destroyChart() {
        if (this.chartInstance && typeof this.chartInstance.destroy === "function") {
            this.chartInstance.destroy();
        }
        this.chartInstance = null;
    }
}

export const sgcDashboardChartField = {
    component: DashboardChart,
    supportedTypes: ["char", "text"],
    extractProps: ({ attrs }) => ({
        chartType: attrs.chartType,
    }),
};

registry.category("fields").add("sgc_dashboard_chart", sgcDashboardChartField);