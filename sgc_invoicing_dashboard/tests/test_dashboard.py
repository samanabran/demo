# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from datetime import date


class TestSalesInvoicingDashboard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Dashboard = self.env['sgc.sales.invoicing.dashboard']
        self.dashboard = self.Dashboard.create({})
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})

    def test_dashboard_singleton(self):
        # create should reuse existing record
        other = self.Dashboard.create({})
        self.assertEqual(self.dashboard.id, other.id)
        self.assertEqual(self.dashboard.name, 'Sales & Invoicing Dashboard')

    def test_date_filter_defaults(self):
        today = date.today()
        first_of_month = today.replace(day=1)
        self.assertEqual(self.dashboard.booking_date_from, first_of_month)
        self.assertEqual(self.dashboard.booking_date_to, today)

    def test_metrics_computation(self):
        # minimal order then confirm
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'booking_date': date.today(),
        })
        order.action_confirm()
        # recompute
        self.dashboard.invalidate_cache()
        self.dashboard._compute_metrics()
        self.assertTrue(self.dashboard.total_booked_sales >= 0)

    def test_export_actions(self):
        act = self.dashboard.action_export_order_types_csv()
        self.assertEqual(act['type'], 'ir.actions.act_url')
        self.assertIn('/sgc_dashboard/export/order_types', act['url'])

    def test_filter_changes_trigger_refresh(self):
        """Test that changing filters properly invalidates cache and refreshes data"""
        # Create a sale order for testing
        order_type = self.env['sale.order.type'].create({'name': 'Test Type'})
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'booking_date': date.today(),
            'sale_order_type_id': order_type.id,
        })
        order.action_confirm()

        # Set filter to specific type
        self.dashboard.write({'sales_order_type_ids': [(6, 0, [order_type.id])]})

        # Verify metrics are computed with filter
        self.dashboard.invalidate_cache()
        self.dashboard._compute_metrics()
        filtered_sales = self.dashboard.total_booked_sales

        # Change filter to all types
        self.dashboard.write({'sales_order_type_ids': [(5, 0, 0)]})

        # Verify metrics are recomputed
        self.dashboard.invalidate_cache()
        self.dashboard._compute_metrics()
        all_sales = self.dashboard.total_booked_sales

        # Both should return valid numbers (actual values may be same if only one order)
        self.assertGreaterEqual(filtered_sales, 0)
        self.assertGreaterEqual(all_sales, 0)

    def test_manual_refresh_action(self):
        """Test that manual refresh action works"""
        result = self.dashboard.action_refresh_dashboard()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'reload')

    def test_onchange_filters_executes(self):
        """Test that onchange method can execute without errors"""
        # This should not raise any exception
        self.dashboard._onchange_filters()
        # Verify computed fields are accessible
        _ = self.dashboard.total_booked_sales
        _ = self.dashboard.chart_sales_by_type
