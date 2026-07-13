# -*- coding: utf-8 -*-
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
import json
from datetime import date

from odoo import api, fields, models


class SalesInvoicingDashboard(models.Model):
    """Dashboard singleton for sales and invoicing KPIs, charts, and tables.

    The dashboard is exposed as a singleton record — a single dashboard
    record per company is reused via ``create()``. The JS
    form controller and the CSV export controller both call
    ``update_filters_and_refresh()`` to recompute all computed fields and
    return them as a dictionary; the charts consume JSON-shaped payloads
    produced by ``_compute_metrics``.

    Chart payload schema (all values are strings, designed for direct
    consumption by Chart.js):

        {
            "labels": ["Jan", "Feb", ...],
            "datasets": [{"label": "...", "data": [...], "backgroundColor": "..."}],
            "options": {"currency": "USD"}
        }
    """
    _name = 'sgc.sales.invoicing.dashboard'
    _description = 'Sales & Invoicing Dashboard'

    name = fields.Char(string='Name', default='Sales & Invoicing Dashboard')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='company_id.currency_id',
    )

    # ---- Filter fields (driven by the form view) -----------------------
    booking_date_from = fields.Date(string='Booking Date From')
    booking_date_to = fields.Date(string='Booking Date To')
    invoice_status_filter = fields.Selection([
        ('all', 'All'),
        ('invoiced', 'Fully Invoiced'),
        ('to_invoice', 'Pending to Invoice'),
        ('nothing', 'Nothing to Invoice'),
    ], string='Invoice Status', default='all')
    payment_status_filter = fields.Selection([
        ('all', 'All'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('not_paid', 'Not Paid'),
    ], string='Payment Status', default='all')
    agent_partner_id = fields.Many2one('res.partner', string='Agent')
    partner_id = fields.Many2one('res.partner', string='Customer')

    # ---- KPI cards -----------------------------------------------------
    posted_invoice_count = fields.Integer(
        string='Posted Invoices', compute='_compute_metrics', store=False,
    )
    pending_to_invoice_order_count = fields.Integer(
        string='Orders Pending to Invoice',
        compute='_compute_metrics', store=False,
    )
    unpaid_invoice_count = fields.Integer(
        string='Unpaid Invoices', compute='_compute_metrics', store=False,
    )
    total_booked_sales = fields.Float(
        string='Total Booked Sales',
        compute='_compute_metrics', store=False,
    )
    total_invoiced_amount = fields.Float(
        string='Total Invoiced',
        compute='_compute_metrics', store=False,
    )
    total_pending_amount = fields.Float(
        string='Total Pending',
        compute='_compute_metrics', store=False,
    )
    amount_to_collect = fields.Float(
        string='Amount to Collect',
        compute='_compute_metrics', store=False,
    )
    amount_collected = fields.Float(
        string='Amount Collected',
        compute='_compute_metrics', store=False,
    )
    commission_due = fields.Float(
        string='Commission Due',
        compute='_compute_metrics', store=False,
    )

    # ---- Chart payloads (Chart.js-friendly JSON) -----------------------
    chart_sales_by_type = fields.Char(
        string='Sales by Type Chart',
        compute='_compute_metrics', store=False,
    )
    chart_booking_trend = fields.Char(
        string='Booking Trend Chart',
        compute='_compute_metrics', store=False,
    )
    chart_payment_state = fields.Char(
        string='Payment State Chart',
        compute='_compute_metrics', store=False,
    )
    chart_sales_funnel = fields.Char(
        string='Sales Funnel Chart',
        compute='_compute_metrics', store=False,
    )
    chart_top_customers = fields.Char(
        string='Top Customers Chart',
        compute='_compute_metrics', store=False,
    )
    chart_agent_performance = fields.Char(
        string='Agent Performance Chart',
        compute='_compute_metrics', store=False,
    )
    chart_source_conversion = fields.Char(
        string='Source Conversion Chart',
        compute='_compute_metrics', store=False,
    )

    # ---- HTML tables (rendered server-side for embedded lists) ---------
    table_order_type_html = fields.Html(
        string='Order Type Table',
        compute='_compute_metrics', store=False, sanitize=False,
    )
    table_agent_commission_html = fields.Html(
        string='Agent Commission Table',
        compute='_compute_metrics', store=False, sanitize=False,
    )
    table_detailed_orders_html = fields.Html(
        string='Detailed Orders Table',
        compute='_compute_metrics', store=False, sanitize=False,
    )
    table_invoice_aging_html = fields.Html(
        string='Invoice Aging Table',
        compute='_compute_metrics', store=False, sanitize=False,
    )

    # ===================================================================
    # ORM lifecycle
    # ===================================================================

    @api.model
    def create(self, vals):
        """Singleton pattern: always return the existing record."""
        existing = self.search([], limit=1)
        if existing:
            existing.write(vals)
            return existing
        if not vals.get('name'):
            vals['name'] = 'Sales & Invoicing Dashboard'
        if not vals.get('booking_date_from'):
            today = date.today()
            vals['booking_date_from'] = today.replace(day=1)
        if not vals.get('booking_date_to'):
            vals['booking_date_to'] = today.today() if hasattr(today, 'today') else today
        return super().create(vals)

    @api.onchange('booking_date_from', 'booking_date_to',
                  'invoice_status_filter', 'payment_status_filter',
                  'agent_partner_id', 'partner_id')
    def _onchange_filters(self):
        """Touch all computed fields so the form re-renders on filter change."""
        for f in ('posted_invoice_count', 'total_booked_sales',
                  'amount_to_collect', 'amount_collected',
                  'chart_sales_by_type', 'chart_booking_trend',
                  'chart_payment_state', 'chart_sales_funnel',
                  'chart_top_customers', 'chart_agent_performance',
                  'chart_source_conversion'):
            if hasattr(self, f):
                setattr(self, f, getattr(self, f))

    def _get_order_domain(self):
        """Build the sale.order domain from current filter values."""
        self.ensure_one()
        domain = []
        if self.booking_date_from:
            domain.append(('booking_date', '>=', self.booking_date_from))
        if self.booking_date_to:
            domain.append(('booking_date', '<=', self.booking_date_to))
        if self.invoice_status_filter and self.invoice_status_filter != 'all':
            domain.append(('invoice_status', '=', self.invoice_status_filter))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.agent_partner_id:
            domain.append(('agent1_partner_id', '=', self.agent_partner_id.id))
        return domain

    def _get_invoice_domain(self, include_payment_filter=True, unpaid_only=False):
        self.ensure_one()
        domain = [('move_type', 'in', ('out_invoice', 'out_refund')),
                  ('state', '=', 'posted')]
        if self.booking_date_from:
            domain.append(('invoice_date', '>=', self.booking_date_from))
        if self.booking_date_to:
            domain.append(('invoice_date', '<=', self.booking_date_to))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if include_payment_filter and self.payment_status_filter and self.payment_status_filter != 'all':
            domain.append(('payment_state', '=', self.payment_status_filter))
        elif unpaid_only:
            domain.append(('payment_state', 'in', ('not_paid', 'partial', 'in_payment')))
        return domain

    def _currency_symbol(self):
        self.ensure_one()
        if self.currency_id:
            return self.currency_id.symbol or self.currency_id.name
        return self.company_id.currency_id.symbol if self.company_id else ''

    @staticmethod
    def _to_chart_json(labels, datasets, currency=None):
        payload = {'labels': list(labels), 'datasets': list(datasets)}
        if currency:
            payload['options'] = {'currency': currency}
        return json.dumps(payload)

    def _palette(self):
        return ['#1B3A57', '#C9A961', '#2E7D32', '#5A7A8C',
                '#9C7A3F', '#B85C5C', '#6B8E23', '#4682B4']

    # ===================================================================
    # Computed fields
    # ===================================================================

    @api.depends('booking_date_from', 'booking_date_to',
                 'invoice_status_filter', 'payment_status_filter',
                 'agent_partner_id', 'partner_id')
    def _compute_metrics(self):
        for rec in self:
            SaleOrder = rec.env['sale.order']
            AccountMove = rec.env['account.move']
            order_domain = rec._get_order_domain()
            invoice_domain = rec._get_invoice_domain(include_payment_filter=False)
            orders = SaleOrder.search(order_domain)
            invoices = AccountMove.search(invoice_domain)

            rec.posted_invoice_count = len(invoices)
            rec.pending_to_invoice_order_count = len(
                orders.filtered(lambda o: o.invoice_status == 'to invoice')
            )
            rec.unpaid_invoice_count = len(invoices.filtered(
                lambda m: m.payment_state in ('not_paid', 'partial', 'in_payment')
            ))
            rec.total_booked_sales = sum(orders.mapped('amount_total'))
            rec.total_invoiced_amount = sum(invoices.mapped('amount_total'))
            residual_total = sum((i.amount_residual or 0.0) for i in invoices)
            rec.total_pending_amount = residual_total
            rec.amount_collected = rec.total_invoiced_amount - residual_total
            rec.amount_to_collect = residual_total

            # Commission due (gracefully degrades if commission module missing)
            rec.commission_due = 0.0
            try:
                if orders:
                    lines = rec.env['commission.line'].search([
                        ('sale_order_id', 'in', orders.ids),
                        ('paid', '=', False),
                    ])
                    rec.commission_due = sum(lines.mapped('commission_amount'))
            except Exception:
                pass

            currency = rec._currency_symbol()
            palette = rec._palette()

            # Chart: Sales by order type (doughnut)
            by_type = SaleOrder.read_group(
                order_domain, ['amount_total', 'sale_order_type_id'],
                ['sale_order_type_id'],
            )
            type_labels = [(g['sale_order_type_id'] or ['', 'Untyped'])[1]
                           for g in by_type]
            type_values = [g['amount_total'] for g in by_type]
            rec.chart_sales_by_type = rec._to_chart_json(
                type_labels,
                [{'label': 'Sales',
                  'data': type_values,
                  'backgroundColor': palette[:max(len(type_labels), 1)]}],
                currency=currency,
            )

            # Chart: Booking trend (line, monthly buckets)
            monthly = {}
            for o in orders:
                key = (o.booking_date.strftime('%Y-%m')
                       if o.booking_date else 'unknown')
                monthly[key] = monthly.get(key, 0.0) + (o.amount_total or 0.0)
            trend_keys = sorted(monthly.keys())
            rec.chart_booking_trend = rec._to_chart_json(
                trend_keys,
                [{'label': 'Bookings',
                  'data': [monthly[k] for k in trend_keys],
                  'borderColor': palette[0],
                  'backgroundColor': palette[0] + '33',
                  'fill': True, 'tension': 0.3}],
                currency=currency,
            )

            # Chart: Payment state distribution (bar)
            payment_groups = AccountMove.read_group(
                invoice_domain, ['amount_total', 'payment_state'],
                ['payment_state'],
            )
            pay_labels = [(g['payment_state'] or 'unknown') for g in payment_groups]
            pay_values = [g['amount_total'] for g in payment_groups]
            rec.chart_payment_state = rec._to_chart_json(
                pay_labels,
                [{'label': 'Amount', 'data': pay_values,
                  'backgroundColor': palette[:max(len(pay_labels), 1)]}],
                currency=currency,
            )

            # Chart: Sales funnel (quotation -> confirmed -> invoiced -> paid)
            confirmed = orders.filtered(lambda o: o.state in ('sale', 'done'))
            invoiced_count = len(orders.filtered(
                lambda o: o.invoice_status in ('invoiced', 'upfront')
            ))
            paid_count = len(invoices.filtered(lambda m: m.payment_state == 'paid'))
            funnel_labels = ['Quotations', 'Confirmed', 'Invoiced', 'Paid']
            funnel_values = [len(orders), len(confirmed),
                             invoiced_count, paid_count]
            rec.chart_sales_funnel = rec._to_chart_json(
                funnel_labels,
                [{'label': 'Funnel', 'data': funnel_values,
                  'backgroundColor': [palette[i % len(palette)]
                                      for i in range(len(funnel_labels))]}],
            )

            # Chart: Top customers (horizontal bar)
            top_customers = SaleOrder.read_group(
                order_domain, ['amount_total', 'partner_id'],
                ['partner_id'], orderby='amount_total desc', limit=10,
            )
            cust_labels = [(g['partner_id'] or ['', 'Unknown'])[1]
                           for g in top_customers]
            cust_values = [g['amount_total'] for g in top_customers]
            rec.chart_top_customers = rec._to_chart_json(
                cust_labels,
                [{'label': 'Sales', 'data': cust_values,
                  'backgroundColor': palette[0]}],
                currency=currency,
            )

            # Chart: Agent performance (best-effort, field may not exist)
            agent_labels, agent_values = [], []
            try:
                agent_groups = SaleOrder.read_group(
                    order_domain, ['amount_total', 'agent1_partner_id'],
                    ['agent1_partner_id'], orderby='amount_total desc', limit=10,
                )
                agent_labels = [(g['agent1_partner_id'] or ['', 'Unassigned'])[1]
                                for g in agent_groups]
                agent_values = [g['amount_total'] for g in agent_groups]
            except Exception:
                pass
            rec.chart_agent_performance = rec._to_chart_json(
                agent_labels,
                [{'label': 'Agent Sales', 'data': agent_values,
                  'backgroundColor': palette[1]}],
                currency=currency,
            )

            # Chart: Source conversion
            source_labels, source_values = [], []
            try:
                source_groups = SaleOrder.read_group(
                    order_domain, ['amount_total', 'source_id'],
                    ['source_id'],
                )
                for g in source_groups:
                    if not g['source_id']:
                        continue
                    won = orders.filtered(
                        lambda o: o.source_id
                        and o.source_id.id == g['source_id'][0]
                        and o.state in ('sale', 'done')
                    )
                    source_labels.append(g['source_id'][1])
                    source_values.append(sum(won.mapped('amount_total')))
            except Exception:
                pass
            rec.chart_source_conversion = rec._to_chart_json(
                source_labels,
                [{'label': 'Won Sales', 'data': source_values,
                  'backgroundColor': palette[2]}],
                currency=currency,
            )

            # HTML tables
            rec.table_order_type_html = rec._render_order_type_table(by_type)
            rec.table_agent_commission_html = rec._render_agent_commission_table(orders)
            rec.table_detailed_orders_html = rec._render_detailed_orders_table(orders)
            rec.table_invoice_aging_html = rec._render_invoice_aging_table(invoices)

    # ===================================================================
    # Table renderers
    # ===================================================================

    def _render_order_type_table(self, groups):
        rows = []
        for g in groups:
            label = (g['sale_order_type_id'] or ['', 'Untyped'])[1]
            rows.append(
                f"<tr><td>{label}</td>"
                f"<td>{g.get('sale_order_type_id_count', 0)}</td>"
                f"<td>{g['amount_total']:.2f}</td></tr>"
            )
        if not rows:
            rows.append('<tr><td colspan="3" style="text-align:center;color:#888">'
                        'No data</td></tr>')
        return (
            '<table class="table table-sm table-striped">'
            '<thead><tr><th>Type</th><th>Orders</th><th>Amount</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )

    def _render_agent_commission_table(self, orders):
        rows = []
        try:
            lines = self.env['commission.line'].search([
                ('sale_order_id', 'in', orders.ids),
                ('commission_category', '=', 'internal'),
            ])
            if lines:
                groups = lines.read_group(
                    [('id', 'in', lines.ids)],
                    ['commission_amount', 'paid_amount', 'partner_id'],
                    ['partner_id'],
                )
                for g in groups:
                    partner = (g['partner_id'] or ['', 'Agent'])[1]
                    total = g.get('commission_amount', 0.0) or 0.0
                    paid = g.get('paid_amount', 0.0) or 0.0
                    out = max(total - paid, 0.0)
                    status = ('Paid' if out == 0 else
                              'Partial' if paid > 0 else 'Pending')
                    rows.append(
                        f"<tr><td>{partner}</td>"
                        f"<td>{g.get('partner_id_count', 0)}</td>"
                        f"<td>{total:.2f}</td><td>{paid:.2f}</td>"
                        f"<td>{out:.2f}</td><td>{status}</td></tr>"
                    )
        except Exception:
            pass
        if not rows:
            rows.append('<tr><td colspan="6" style="text-align:center;color:#888">'
                        'No commission data</td></tr>')
        return (
            '<table class="table table-sm table-striped">'
            '<thead><tr><th>Agent</th><th>Lines</th><th>Total</th>'
            '<th>Paid</th><th>Outstanding</th><th>Status</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )

    def _render_detailed_orders_table(self, orders):
        today = date.today()
        sorted_orders = orders.sorted(
            key=lambda x: (x.booking_date or today, x.id),
            reverse=True,
        )[:50]
        rows = []
        for o in sorted_orders:
            invs = o.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
            )
            invoiced = sum(invs.mapped('amount_total'))
            outstanding = sum(invs.mapped('amount_residual'))
            days = ((today - (o.booking_date or today)).days
                    if o.booking_date else 0)
            action = ('Invoice Pending' if o.invoice_status == 'to invoice'
                      else ('Payment Pending' if outstanding > 0 else '-'))
            type_name = (o.sale_order_type_id.name
                         if o.sale_order_type_id else '')
            partner_name = o.partner_id.name if o.partner_id else ''
            rows.append(
                f"<tr><td>{o.name}</td><td>{o.booking_date or ''}</td>"
                f"<td>{type_name}</td><td>{partner_name}</td>"
                f"<td>{o.state}</td>"
                f"<td>{o.amount_total:.2f}</td>"
                f"<td>{invoiced:.2f}</td>"
                f"<td>{outstanding:.2f}</td>"
                f"<td>{action}</td>"
                f"<td>{days}</td></tr>"
            )
        if not rows:
            rows.append('<tr><td colspan="10" style="text-align:center;color:#888">'
                        'No orders match the current filters</td></tr>')
        return (
            '<table class="table table-sm table-striped">'
            '<thead><tr><th>Order</th><th>Date</th><th>Type</th><th>Customer</th>'
            '<th>State</th><th>Total</th><th>Invoiced</th><th>Outstanding</th>'
            '<th>Action</th><th>Days</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )

    def _render_invoice_aging_table(self, invoices):
        today = date.today()
        buckets = [
            ('current', 'Current', lambda d: not d or d >= today),
            ('1_30', '1-30', lambda d: d and 0 < (today - d).days <= 30),
            ('31_60', '31-60', lambda d: d and 30 < (today - d).days <= 60),
            ('61_90', '61-90', lambda d: d and 60 < (today - d).days <= 90),
            ('90_plus', '90+', lambda d: d and (today - d).days > 90),
        ]
        rows = []
        for _key, label, pred in buckets:
            bucket_invs = invoices.filtered(
                lambda m: pred(m.invoice_date_due)
                and m.payment_state in ('not_paid', 'partial', 'in_payment')
            )
            count = len(bucket_invs)
            amount = sum(bucket_invs.mapped('amount_residual'))
            rows.append(
                f"<tr><td>{label}</td><td>{count}</td>"
                f"<td>{amount:.2f}</td></tr>"
            )
        return (
            '<table class="table table-sm table-striped">'
            '<thead><tr><th>Aging Bucket</th><th>Count</th><th>Amount</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )

    # ===================================================================
    # Public actions consumed by JS / controllers / tests
    # ===================================================================

    @api.model
    def update_filters_and_refresh(self, filter_values):
        """Singleton update + recompute. Returns the computed-field dict.

        This is the method the JS form controller calls after any filter
        change. It accepts a flat ``filter_values`` dict (matching the
        ``FILTER_FIELDS`` list) and writes them on the singleton, then
        invalidates the cache so all ``compute`` methods re-run.
        """
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({})
        writable = {
            'booking_date_from', 'booking_date_to',
            'invoice_status_filter', 'payment_status_filter',
            'agent_partner_id', 'partner_id',
        }
        clean = {}
        for k, v in (filter_values or {}).items():
            if k in writable:
                clean[k] = v
        if clean:
            rec.write(clean)
        rec.invalidate_cache()
        # Force recompute explicitly because _auto = False skips ORM tracking.
        rec._compute_metrics()
        return {
            'posted_invoice_count': rec.posted_invoice_count,
            'pending_to_invoice_order_count': rec.pending_to_invoice_order_count,
            'unpaid_invoice_count': rec.unpaid_invoice_count,
            'total_booked_sales': rec.total_booked_sales,
            'total_invoiced_amount': rec.total_invoiced_amount,
            'total_pending_amount': rec.total_pending_amount,
            'amount_to_collect': rec.amount_to_collect,
            'amount_collected': rec.amount_collected,
            'commission_due': rec.commission_due,
            'chart_sales_by_type': rec.chart_sales_by_type,
            'chart_booking_trend': rec.chart_booking_trend,
            'chart_payment_state': rec.chart_payment_state,
            'chart_sales_funnel': rec.chart_sales_funnel,
            'chart_top_customers': rec.chart_top_customers,
            'chart_agent_performance': rec.chart_agent_performance,
            'chart_source_conversion': rec.chart_source_conversion,
            'table_order_type_html': rec.table_order_type_html,
            'table_agent_commission_html': rec.table_agent_commission_html,
            'table_detailed_orders_html': rec.table_detailed_orders_html,
            'table_invoice_aging_html': rec.table_invoice_aging_html,
        }

    def action_refresh_dashboard(self):
        """Reload action (returns client reload action consumed by tests)."""
        self.invalidate_cache()
        self._compute_metrics()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _get_order_type_rows(self):
        self.ensure_one()
        groups = self.env['sale.order'].read_group(
            self._get_order_domain(),
            ['amount_total', 'sale_order_type_id'],
            ['sale_order_type_id'],
        )
        rows = []
        for g in groups:
            type_id = (g['sale_order_type_id'][0]
                       if g['sale_order_type_id'] else False)
            row = {
                'name': (g['sale_order_type_id'] or ['', 'Untyped'])[1],
                'count': g.get('sale_order_type_id_count', 0),
                'total_sales': g['amount_total'],
                'to_invoice': 0.0,
                'invoiced': 0.0,
                'outstanding': 0.0,
                'collected': 0.0,
                'rate': 0.0,
                'status': 'No Orders',
            }
            if type_id:
                type_orders = self.env['sale.order'].search(
                    self._get_order_domain() +
                    [('sale_order_type_id', '=', type_id)]
                )
                invs = self.env['account.move'].search([
                    ('invoice_line_ids.sale_line_ids.order_id', 'in',
                     type_orders.ids),
                    ('state', '=', 'posted'),
                    ('move_type', '=', 'out_invoice'),
                ])
                row['invoiced'] = sum(invs.mapped('amount_total'))
                outstanding = sum(invs.mapped('amount_residual'))
                row['outstanding'] = outstanding
                row['collected'] = max(row['invoiced'] - outstanding, 0.0)
                row['to_invoice'] = max(row['total_sales'] - row['invoiced'], 0.0)
                row['rate'] = (
                    (row['collected'] / row['invoiced'] * 100.0)
                    if row['invoiced'] else 0.0
                )
                if outstanding <= 0 and row['invoiced'] > 0:
                    row['status'] = 'Paid'
                elif row['collected'] > 0:
                    row['status'] = 'Partial'
                elif row['invoiced'] > 0:
                    row['status'] = 'Pending'
                else:
                    row['status'] = 'No Invoice'
            rows.append(row)
        return rows

    def action_export_order_types_csv(self):
        """Return client action for the order_types CSV download."""
        rec = self.search([], limit=1)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/sgc_dashboard/export/order_types?rec_id={rec.id if rec else 0}',
            'target': 'self',
        }