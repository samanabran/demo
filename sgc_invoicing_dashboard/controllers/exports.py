# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.tools import float_compare
from odoo.http import request
from odoo.http import content_disposition
import io
import csv


class OsusDashboardExportController(http.Controller):
    def _get_rec(self):
        rec_id = int(request.params.get('rec_id', '0') or 0)
        rec = request.env['sgc.sales.invoicing.dashboard'].sudo().browse(rec_id)
        if not rec.exists():
            return None
        return rec

    def _csv_response(self, filename, headers, rows):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
        content = buf.getvalue()
        buf.close()
        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )

    @http.route(['/sgc_dashboard/export/order_types'], type='http', auth='user')
    def export_order_types(self, **kwargs):
        rec = self._get_rec()
        if not rec:
            return request.not_found()
        rows_data = rec._get_order_type_rows()
        headers = ['Order Type', 'Order Count', 'Total Sales', 'To Invoice', 'Invoiced', 'Outstanding', 'Collected', 'Collection %', 'Status']
        rows = []
        for r in rows_data:
            rows.append([
                r['name'], r['count'],
                r['total_sales'], r['to_invoice'], r['invoiced'], r['outstanding'], r['collected'],
                f"{r['rate']:.1f}%", r['status']
            ])
        return self._csv_response('order_types.csv', headers, rows)

    @http.route(['/sgc_dashboard/export/agent_commissions'], type='http', auth='user')
    def export_agent_commissions(self, **kwargs):
        rec = self._get_rec()
        if not rec:
            return request.not_found()
        order_ids = request.env['sale.order'].sudo().search(rec._get_order_domain()).ids
        headers = ['Agent', 'Lines', 'Total', 'Paid', 'Outstanding', 'Status']
        rows = []
        if order_ids:
            groups = request.env['commission.line'].sudo().read_group(
                [('sale_order_id', 'in', order_ids), ('commission_category', '=', 'internal')],
                ['commission_amount', 'paid_amount', 'id:count', 'partner_id'],
                ['partner_id']
            )
            for g in groups:
                name = (g.get('partner_id') or ['', ''])[1] or 'Agent'
                total = float(g.get('commission_amount', 0.0) or 0.0)
                paid = float(g.get('paid_amount', 0.0) or 0.0)
                out = max(total - paid, 0.0)
                status = 'Paid' if out == 0 else ('Partial' if paid > 0 else 'Pending')
                count = int(g.get('id_count', 0) or g.get('__count', 0) or 0)
                rows.append([name, count, total, paid, out, status])
        return self._csv_response('agent_commissions.csv', headers, rows)

    @http.route(['/sgc_dashboard/export/detailed_orders'], type='http', auth='user')
    def export_detailed_orders(self, **kwargs):
        rec = self._get_rec()
        if not rec:
            return request.not_found()
        today = fields.Date.context_today(request.env.user)
        threshold = 10.0
        orders = request.env['sale.order'].sudo().search(rec._get_order_domain(), order='booking_date desc, id desc')
        headers = ['Order', 'Booking Date', 'Type', 'Customer', 'Salesperson', 'Status', 'Amount', 'Invoiced', 'Outstanding', 'Invoice Status', 'Payment Status', 'Days Since', 'Action Required']
        rows = []
        for o in orders:
            invs = o.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted')
            invoiced = sum(invs.mapped('amount_total'))
            outstanding = sum(invs.mapped('amount_residual'))
            outstanding_company = sum(invs.mapped('amount_residual_signed'))
            rounding = request.env.company.currency_id.rounding
            is_small = float_compare(
                abs(outstanding_company),
                threshold,
                precision_rounding=rounding,
            ) < 0
            if invoiced and is_small:
                pay_status = 'Paid'
            elif invoiced and outstanding > 0:
                overdue = any([inv.invoice_date_due and inv.invoice_date_due < today and (inv.amount_residual or 0) > 0 for inv in invs])
                pay_status = 'Overdue' if overdue else 'Pending'
            else:
                pay_status = '-'
            days_since = (today - (o.booking_date or today)).days if o.booking_date else 0
            if o.invoice_status == 'to invoice':
                action = 'Invoice Pending'
            elif invoiced and outstanding > 0:
                action = 'Payment Overdue' if 'Overdue' in pay_status else 'Payment Pending'
            else:
                action = '-'
            rows.append([
                o.name, o.booking_date or '', o.sale_order_type_id.name or '', o.partner_id.name or '',
                getattr(o, 'agent1_partner_id').name if hasattr(o, 'agent1_partner_id') and o.agent1_partner_id else '',
                o.state, o.amount_total, invoiced, outstanding, o.invoice_status, pay_status, days_since, action
            ])
        return self._csv_response('detailed_orders.csv', headers, rows)

    @http.route(['/sgc_dashboard/export/invoice_aging'], type='http', auth='user')
    def export_invoice_aging(self, **kwargs):
        rec = self._get_rec()
        if not rec:
            return request.not_found()
        today = fields.Date.context_today(request.env.user)
        domain = rec._get_invoice_domain(include_payment_filter=False, unpaid_only=True)
        invs = request.env['account.move'].sudo().search(domain)
        buckets = {
            'current': {'label': 'Current (Not Due)', 'count': 0, 'amount': 0.0},
            '1_30': {'label': '1-30 Days', 'count': 0, 'amount': 0.0},
            '31_60': {'label': '31-60 Days', 'count': 0, 'amount': 0.0},
            '61_90': {'label': '61-90 Days', 'count': 0, 'amount': 0.0},
            '90_plus': {'label': '90+ Days Overdue', 'count': 0, 'amount': 0.0},
        }
        for inv in invs:
            amt = inv.amount_residual or 0.0
            due = inv.invoice_date_due
            if not due or due >= today:
                key = 'current'
            else:
                delta = (today - due).days
                if delta <= 30:
                    key = '1_30'
                elif delta <= 60:
                    key = '31_60'
                elif delta <= 90:
                    key = '61_90'
                else:
                    key = '90_plus'
            buckets[key]['count'] += 1
            buckets[key]['amount'] += amt
        headers = ['Aging Bucket', 'Count', 'Amount']
        rows = []
        for key in ['current','1_30','31_60','61_90','90_plus']:
            b = buckets[key]
            rows.append([b['label'], b['count'], b['amount']])
        return self._csv_response('invoice_aging.csv', headers, rows)

    @http.route('/sgc_dashboard/api/refresh', type='jsonrpc', auth='user')
    def refresh_dashboard(self, dashboard_id):
        """Force refresh dashboard data via AJAX by invalidating cache."""
        try:
            dashboard = request.env['sgc.sales.invoicing.dashboard'].sudo().browse(int(dashboard_id))
            if not dashboard.exists():
                return {'success': False, 'error': 'Dashboard not found'}
            request.env.invalidate_all()
            return {'success': True, 'timestamp': fields.Datetime.now()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
