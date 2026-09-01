/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

/**
 * Single filter widget.
 */
export class DfrFilterWidget extends Component {
    static template = "sgc_dynamic_financial_report.DfrFilterWidget";
    static props = {
        filterDef: Object,
        value: { optional: true },
        onChange: Function,
    };

    setup() {
        this.state = useState({
            searchTerm: "",
            searchResults: [],
            searching: false,
        });
    }

    get widget() {
        return this.props.filterDef.widget || "selection";
    }

    get label() {
        return this.props.filterDef.label || this.props.filterDef.name || "";
    }

    get options() {
        return this.props.filterDef.options || [];
    }

    get placeholder() {
        return this.props.filterDef.placeholder || `Select ${this.label}`;
    }

    get hasMore() {
        return this.props.filterDef.has_more || false;
    }

    onSearchInput(ev) {
        const term = ev.target.value;
        this.state.searchTerm = term;
        if (this.widget === "many2one" || this.widget === "many2many_tags") {
            this._runSearch(term);
        }
    }

    async _runSearch(term) {
        this.state.searching = true;
        try {
            const model = this.props.filterDef.model;
            if (!model) return;
            const domain = this.props.filterDef.search_domain || [];
            const nameField = this.props.filterDef.name_field || "name";
            if (term) {
                domain.push([nameField, "=ilike", term]);
            }
            const searchLimit = this.props.filterDef.search_limit || 20;
            const result = await rpc("/web/search/read", {
                model: model,
                fields: [nameField, "id"],
                domain: domain,
                limit: searchLimit,
            });
            this.state.searchResults = result.map((r) => ({
                id: r.id,
                name: r[nameField] || r.display_name || `#${r.id}`,
            }));
        } catch (_err) {
            this.state.searchResults = [];
        } finally {
            this.state.searching = false;
        }
    }

    selectMany2One(record) {
        this.props.onChange(this.props.filterDef.key, record.id);
        this.state.searchTerm = record.name;
        this.state.searchResults = [];
    }

    selectMany2ManyTag(record) {
        const current = Array.isArray(this.props.value) ? this.props.value : [];
        if (!current.some((v) => v === record.id || v.id === record.id)) {
            current.push(record.id);
        }
        this.props.onChange(this.props.filterDef.key, current);
        this.state.searchTerm = "";
        this.state.searchResults = [];
    }

    removeMany2ManyTag(recordId) {
        const current = Array.isArray(this.props.value) ? this.props.value : [];
        const updated = current.filter((v) => v !== recordId && v.id !== recordId);
        this.props.onChange(this.props.filterDef.key, updated);
    }

    onDateFromChange(ev) {
        const current = Array.isArray(this.props.value) ? this.props.value : [null, null];
        current[0] = ev.target.value || null;
        this.props.onChange(this.props.filterDef.key, current);
    }

    onDateToChange(ev) {
        const current = Array.isArray(this.props.value) ? this.props.value : [null, null];
        current[1] = ev.target.value || null;
        this.props.onChange(this.props.filterDef.key, current);
    }

    onBooleanToggle() {
        this.props.onChange(this.props.filterDef.key, !this.props.value);
    }

    onSelectionChange(ev) {
        this.props.onChange(this.props.filterDef.key, ev.target.value);
    }
}

/**
 * Enterprise-grade filter bar aggregating multiple filter widgets.
 */
export class EnterpriseFilterBar extends Component {
    static template = "sgc_dynamic_financial_report.EnterpriseFilterBar";
    static components = { DfrFilterWidget };
    static props = {
        reportType: { type: String, optional: true },
        onGenerate: { type: Function, optional: true },
        onExport: { type: Function, optional: true },
        onExportPdf: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            filters: {},
            filterDefs: null,
            registry: null,
            reportMetadata: null,
            showMore: false,
            generating: false,
            exporting: false,
            exportingPdf: false,
        });

        onWillStart(async () => {
            await Promise.all([this._loadRegistry(), this._loadReportMetadata()]);
        });
    }

    get visibleFilters() {
        const defs = this.state.filterDefs;
        if (!defs || !defs.filters) return [];
        const all = Object.values(defs.filters);
        return this.state.showMore ? all : all.filter((f) => !f.advanced);
    }

    get hasAdvancedFilters() {
        const defs = this.state.filterDefs;
        if (!defs || !defs.filters) return false;
        return Object.values(defs.filters).some((f) => f.advanced);
    }

    get canGenerate() {
        return !this.state.generating && !this.state.exporting && !this.state.exportingPdf;
    }

    get filterCount() {
        return Object.keys(this.state.filters).length;
    }

    get dateFilters() {
        const defs = this.state.filterDefs;
        if (!defs || !defs.filters) return [];
        return Object.values(defs.filters).filter((f) => f.widget === "date_range");
    }

    get comparisonFilters() {
        const defs = this.state.filterDefs;
        if (!defs || !defs.filters) return [];
        return Object.values(defs.filters).filter(
            (f) => f.widget === "boolean_with_date_range" || f.widget === "boolean_with_many2many"
        );
    }

    async _loadRegistry() {
        try {
            const registry = await rpc("/sgc/dfr/registry", {});
            this.state.registry = registry;
        } catch (_err) {
            this.state.registry = {};
        }
    }

    async _loadReportMetadata() {
        try {
            const metadata = await rpc("/sgc/dfr/metadata", {});
            this.state.filterDefs = metadata;
            this.state.reportMetadata = metadata;
        } catch (_err) {
            this.state.filterDefs = { filters: {} };
            this.state.reportMetadata = {};
        }
    }

    toggleMoreFilters() {
        this.state.showMore = !this.state.showMore;
    }

    onFilterValueChange(filterKey, value) {
        const updated = Object.assign({}, this.state.filters);
        if (value === null || value === undefined || value === "") {
            delete updated[filterKey];
        } else {
            updated[filterKey] = value;
        }
        this.state.filters = updated;
    }

    async onGenerateClick() {
        if (!this.canGenerate) return;
        this.state.generating = true;
        try {
            if (this.props.onGenerate) {
                await this.props.onGenerate(this.state.filters);
            }
        } finally {
            this.state.generating = false;
        }
    }

    async onExportClick() {
        if (!this.canGenerate) return;
        this.state.exporting = true;
        try {
            if (this.props.onExport) {
                await this.props.onExport(this.state.filters);
            }
        } finally {
            this.state.exporting = false;
        }
    }

    async onExportPdfClick() {
        if (!this.canGenerate) return;
        this.state.exportingPdf = true;
        try {
            if (this.props.onExportPdf) {
                await this.props.onExportPdf(this.state.filters);
            }
        } finally {
            this.state.exportingPdf = false;
        }
    }

    onResetClick() {
        this.state.filters = {};
        this.state.showMore = false;
    }
}
