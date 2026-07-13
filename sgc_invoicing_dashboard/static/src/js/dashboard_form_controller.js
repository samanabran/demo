/** @odoo-module **/

import { FormController } from '@web/views/form/form_controller';
import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';

/**
 * Dashboard Form Controller Patch
 *
 * Extends the standard Odoo FormController to add automatic filter refresh
 * functionality for the Sales & Invoicing Dashboard.
 */

// Define which fields are filters that trigger auto-save
const FILTER_FIELDS = [
    'booking_date_from',
    'booking_date_to',
    'invoice_status_filter',
    'payment_status_filter',
    'agent_partner_id',
    'partner_id',
];

// Define which fields are computed and should be refreshed
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
    'chart_sales_by_type',
    'chart_booking_trend',
    'chart_payment_state',
    'chart_sales_funnel',
    'chart_top_customers',
    'chart_agent_performance',
    'table_order_type_html',
    'table_agent_commission_html',
    'table_detailed_orders_html',
    'table_invoice_aging_html',
];

/**
 * Refresh dashboard data by calling the server API
 */
async function refreshDashboardData(filterValues) {
    try {
        const result = await rpc("/web/dataset/call_kw/sgc.sales.invoicing.dashboard/update_filters_and_refresh", {
            model: "sgc.sales.invoicing.dashboard",
            method: "update_filters_and_refresh",
            args: [[], filterValues],
            kwargs: {},
        });
        return result;
    } catch (error) {
        console.error('Dashboard filter refresh error:', error);
        throw error;
    }
}

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this._dashboardFilterInitialized = false;
    },

    async onRecordChanged(record, changes) {
        const result = await super.onRecordChanged(...arguments);

        if (this.props.resModel !== 'sgc.sales.invoicing.dashboard') {
            return result;
        }

        if (!this._dashboardFilterInitialized && this.model.root) {
            this._initializeDashboardFilters();
            this._dashboardFilterInitialized = true;
        }

        if (changes && this._isFilterFieldChanged(changes)) {
            await this._handleFilterChange();
        }

        return result;
    },

    _isFilterFieldChanged(changes) {
        if (!changes || typeof changes !== 'object') {
            return false;
        }

        for (const fieldName of FILTER_FIELDS) {
            if (fieldName in changes) {
                console.debug(`Dashboard: filter field "${fieldName}" changed`);
                return true;
            }
        }
        return false;
    },

    async _handleFilterChange() {
        console.debug('Dashboard: filter changed, refreshing data...');

        if (this._filterChangeTimeout) {
            clearTimeout(this._filterChangeTimeout);
        }

        this._filterChangeTimeout = setTimeout(async () => {
            try {
                if (this.model.root && this.model.root.isDirty) {
                    console.debug('Dashboard: saving form to persist filter changes');
                    await this.model.root.save();
                }

                const filterValues = this._getFilterValues();
                console.debug('Dashboard: collected filter values', filterValues);

                const refreshedData = await refreshDashboardData(filterValues);
                console.debug('Dashboard: received refreshed data', refreshedData);

                await this._updateComputedFields(refreshedData);

                console.debug('Dashboard: form updated with refreshed data');
            } catch (error) {
                console.error('Dashboard: error refreshing after filter change', error);
            }
        }, 300);
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

            if (Array.isArray(fieldValue) && fieldValue.length === 2) {
                filterValues[fieldName] = fieldValue[0] || false;
            } else if (fieldValue && fieldValue.records) {
                filterValues[fieldName] = fieldValue.records.map(r => r.resId);
            } else {
                filterValues[fieldName] = fieldValue;
            }
        }

        return filterValues;
    },

    async _updateComputedFields(refreshedData) {
        if (!refreshedData || !this.model.root) {
            return;
        }

        const record = this.model.root;

        for (const [fieldName, fieldValue] of Object.entries(refreshedData)) {
            if (COMPUTED_FIELDS.includes(fieldName) && fieldName in record.data) {
                record.data[fieldName] = fieldValue;
            }
        }

        await record.model.load();
    },

    _initializeDashboardFilters() {
        console.debug('Dashboard: initializing filter listeners');

        if (this.model.root) {
            const originalDiscard = this.model.root.discard.bind(this.model.root);
            this.model.root.discard = async (...args) => {
                const result = await originalDiscard(...args);
                console.debug('Dashboard: form discarded/reset, ensuring filters persist');

                setTimeout(async () => {
                    try {
                        const filterValues = this._getFilterValues();

                        if (Object.keys(filterValues).length > 0) {
                            const refreshedData = await refreshDashboardData(filterValues);
                            await this._updateComputedFields(refreshedData);
                        }

                        this.render();
                        console.debug('Dashboard: form re-rendered after discard');
                    } catch (error) {
                        console.error('Dashboard: error handling discard', error);
                    }
                }, 100);

                return result;
            };
        }
    },

    async beforeUnload() {
        if (this._filterChangeTimeout) {
            clearTimeout(this._filterChangeTimeout);
        }
        return super.beforeUnload(...arguments);
    },
});

console.debug('Dashboard form controller patch applied');
