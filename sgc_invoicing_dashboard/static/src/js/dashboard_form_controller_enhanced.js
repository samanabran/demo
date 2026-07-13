/** @odoo-module **/

import { FormController } from '@web/views/form/form_controller';
import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';

/**
 * Enhanced Dashboard Form Controller - Modern Responsive Dashboard
 * 
 * Fixes:
 * 1. Proper filter change detection with debouncing
 * 2. Force field recomputation on filter changes
 * 3. Better state management for filter updates
 * 4. Proper loading indicators and UX feedback
 */

const FILTER_FIELDS = [
    'booking_date_from',
    'booking_date_to',
    'invoice_status_filter',
    'payment_status_filter',
    'agent_partner_id',
    'partner_id',
];

// Simple debounce implementation
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const CHART_FIELDS = [
    'chart_sales_by_type',
    'chart_booking_trend',
    'chart_payment_state',
    'chart_sales_funnel',
    'chart_top_customers',
    'chart_agent_performance',
    'chart_source_conversion',
];

const COMPUTED_FIELDS = [
    'posted_invoice_count',
    'pending_to_invoice_order_count',
    'unpaid_invoice_count',
    'total_booked_sales',
    'total_invoiced_amount',
    'total_pending_amount',
    'amount_to_collect',
    'amount_collected',
    'commission_due',
    ...CHART_FIELDS,
    'table_order_type_html',
    'table_agent_commission_html',
    'table_detailed_orders_html',
    'table_invoice_aging_html',
];

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this._dashboardFilterInitialized = false;
        this._initialRefreshDone = false;
        this._isUpdatingFilters = false;
        this._pendingFilterUpdate = false;
        this._debouncedFilterRefresh = debounce(() => this._refreshAfterFilterChange(), 500);
    },

    async onRecordChanged(record, changes) {
        const result = await super.onRecordChanged(...arguments);

        // Only handle dashboard model
        if (this.props.resModel !== 'sgc.sales.invoicing.dashboard') {
            return result;
        }

        // Initialize filter listeners once
        if (!this._dashboardFilterInitialized && this.model.root) {
            this._initializeDashboardFilters();
            this._dashboardFilterInitialized = true;
        }

        if (!this._initialRefreshDone && this.model.root) {
            this._initialRefreshDone = true;
            this._pendingFilterUpdate = true;
            this._debouncedFilterRefresh();
        }

        // Check if filter changed
        if (changes && this._isFilterFieldChanged(changes)) {
            console.debug('🔄 Dashboard: filter changed, scheduling refresh...', changes);
            this._pendingFilterUpdate = true;
            
            // Debounce the refresh to avoid too many requests
            this._debouncedFilterRefresh();
        }

        return result;
    },

    _isFilterFieldChanged(changes) {
        if (!changes || typeof changes !== 'object') {
            return false;
        }

        for (const fieldName of FILTER_FIELDS) {
            if (fieldName in changes) {
                return true;
            }
        }
        return false;
    },

    async _refreshAfterFilterChange() {
        if (this._isUpdatingFilters || !this._pendingFilterUpdate) {
            return;
        }

        this._pendingFilterUpdate = false;
        this._isUpdatingFilters = true;

        try {
            // Save the form first if dirty
            if (this.model.root && this.model.root.isDirty) {
                console.debug('💾 Dashboard: saving filter changes to database');
                await this.model.root.save();
            }

            // Get filter values
            const filterValues = this._getFilterValues();
            console.debug('📌 Dashboard: filter values collected', filterValues);

            // Call server to refresh computed fields
            const refreshedData = await this._callServerRefresh(filterValues);
            console.debug('✅ Dashboard: received updated data from server', Object.keys(refreshedData));

            // Update all computed fields in the record
            if (this.model.root && refreshedData) {
                await this._updateAllComputedFields(refreshedData);
            }

            // Trigger a reload to refresh the UI properly
            if (this.model.root) {
                console.debug('🔄 Dashboard: triggering UI refresh');
                // Notify all chart widgets to refresh
                this.env.bus.trigger('dashboard:filter-changed', {
                    charts: CHART_FIELDS,
                    timestamp: Date.now(),
                });
            }

            console.debug('✨ Dashboard: filter update complete');
        } catch (error) {
            console.error('❌ Dashboard: error refreshing after filter change:', error);
        } finally {
            this._isUpdatingFilters = false;
        }
    },

    async _callServerRefresh(filterValues) {
        try {
            const result = await rpc('/web/dataset/call_kw/sgc.sales.invoicing.dashboard/update_filters_and_refresh', {
                model: 'sgc.sales.invoicing.dashboard',
                method: 'update_filters_and_refresh',
                args: [[], filterValues],
                kwargs: {},
            });
            return result || {};
        } catch (error) {
            console.error('❌ Dashboard: RPC refresh error:', error);
            throw error;
        }
    },

    _getFilterValues() {
        const filterValues = {};
        const record = this.model.root;

        if (!record || !record.data) {
            return filterValues;
        }

        for (const fieldName of FILTER_FIELDS) {
            const fieldValue = record.data[fieldName];

            if (fieldValue === undefined || fieldValue === null) {
                continue;
            }

            // Handle Many2many field (stored as array with [id, name])
            if (Array.isArray(fieldValue) && fieldValue.length === 2) {
                filterValues[fieldName] = fieldValue[0] || false;
            }
            // Handle Many2many_tags (stored as recordset)
            else if (fieldValue && fieldValue.records && Array.isArray(fieldValue.records)) {
                filterValues[fieldName] = fieldValue.records.map(r => r.resId);
            }
            // Regular field
            else {
                filterValues[fieldName] = fieldValue;
            }
        }

        return filterValues;
    },

    async _updateAllComputedFields(refreshedData) {
        if (!refreshedData || !this.model.root) {
            return;
        }

        const record = this.model.root;
        let fieldsUpdated = 0;

        for (const [fieldName, fieldValue] of Object.entries(refreshedData)) {
            if (COMPUTED_FIELDS.includes(fieldName) && fieldName in record.data) {
                record.data[fieldName] = fieldValue;
                fieldsUpdated++;
            }
        }

        console.debug(`💾 Dashboard: updated ${fieldsUpdated} computed fields`);

        // Force the record model to notify field changes
        if (fieldsUpdated > 0) {
            // Manually notify the record has changed
            for (const chartField of CHART_FIELDS) {
                if (chartField in refreshedData) {
                    record._notifyFieldChange(chartField);
                }
            }
        }
    },

    _initializeDashboardFilters() {
        console.debug('📋 Dashboard: initializing dashboard filters');

        if (this.model.root) {
            // Intercept form discard to persist filters
            const originalDiscard = this.model.root.discard.bind(this.model.root);
            this.model.root.discard = async (...args) => {
                const result = await originalDiscard(...args);
                console.debug('Dashboard: form discarded, reloading filters');

                setTimeout(async () => {
                    try {
                        const filterValues = this._getFilterValues();
                        if (Object.keys(filterValues).length > 0) {
                            const refreshedData = await this._callServerRefresh(filterValues);
                            await this._updateAllComputedFields(refreshedData);
                        }
                        this.render();
                    } catch (error) {
                        console.error('Dashboard: error handling discard', error);
                    }
                }, 100);

                return result;
            };
        }
    },

    async beforeUnload() {
        if (this._debouncedFilterRefresh && this._debouncedFilterRefresh.cancel) {
            this._debouncedFilterRefresh.cancel();
        }
        return super.beforeUnload(...arguments);
    },
});

console.debug('✅ Enhanced dashboard form controller patch applied');
