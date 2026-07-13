/** @odoo-module **/

import { rpc } from '@web/core/network/rpc';

/**
 * Dashboard Filter Handler
 *
 * Manages filter changes and automatic form saving for the Sales & Invoicing Dashboard
 *
 * Key Features:
 * 1. Listens to filter field changes via FormController patch
 * 2. Automatically saves the form record to database
 * 3. Fetches updated computed field values
 * 4. Updates form display with fresh data
 *
 * This ensures that when users change filters, the dashboard data updates
 * in real-time by persisting changes and recalculating metrics.
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

const DashboardFilterHandler = {
    /**
     * Refresh dashboard data by calling the server API
     *
     * @param {Object} filterValues - Dictionary of filter field names and their values
     * @returns {Promise<Object>} Updated computed field values
     */
    async refreshDashboardData(filterValues) {
        try {
            // Use the correct RPC format for Odoo 17 to call a model method
            const result = await rpc("/web/dataset/call_kw/sgc.sales.invoicing.dashboard/update_filters_and_refresh", {
                model: "sgc.sales.invoicing.dashboard",
                method: "update_filters_and_refresh",
                args: [[], filterValues],  // First arg is record IDs (empty for @api.model), second is method args
                kwargs: {},
            });
            return result;
        } catch (error) {
            console.error('Dashboard filter refresh error:', error);
            throw error;
        }
    },
};

export default DashboardFilterHandler;
export { FILTER_FIELDS, COMPUTED_FIELDS };


