# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionLine(models.Model):
    """Individual commission line for a sale order.

    Inherits commission.line.mixin (shared field set: beneficiary/role/category,
    tax_ids, billing, display_name). Adds sale-order-specific parent and an
    extended 6-state workflow (mixin's 4-state + calculated/confirmed/processed).
    """
    _name = 'commission.line'
    _inherit = ['commission.line.mixin']
    _description = 'Commission Line'
    _order = 'id desc'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        ondelete='cascade'
    )
    commission_type_id = fields.Many2one(
        'commission.type',
        string='Commission Type'
    )
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(16, 4)
    )
    base_amount = fields.Monetary(
        string='Base Amount',
        currency_field='currency_id',
        compute='_compute_commission_amount',
        store=True,
        readonly=False,
        help='Auto-filled from the Sale Order according to the selected '
             'Commission Type\'s Calculation Base (Sale Value / Order Total '
             'excl. tax / Order Total incl. tax). Overridable.',
    )
    commission_amount = fields.Monetary(string='Commission Amount', currency_field='currency_id', compute='_compute_commission_amount', store=True, readonly=False, help='Commission amount before tax.')
    source_invoice_id = fields.Many2one(
        'account.move',
        string='Source Invoice',
        ondelete='set null',
        index=True,
        readonly=True,
        help='Customer invoice whose posting generated (calculated) this '
             'commission bill can only be posted once '
             'this invoice is fully paid.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection(
        selection_add=[
            ('calculated', 'Calculated'),
            ('confirmed', 'Confirmed'),
            ('processed', 'Processed'),
        ],
        ondelete={'calculated': 'cascade', 'confirmed': 'cascade', 'processed': 'cascade'},
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.partner_id.is_commission_agent:
            if not self.commission_type_id and self.partner_id.commission_type_id:
                self.commission_type_id = self.partner_id.commission_type_id
            if not self.commission_rate and self.partner_id.commission_rate:
                self.commission_rate = self.partner_id.commission_rate

    @api.onchange('commission_type_id')
    def _onchange_commission_type_id(self):
        if self.commission_type_id and not self.commission_rate:
            self.commission_rate = self.commission_type_id.default_rate

    @api.depends('sale_order_id.amount_untaxed', 'sale_order_id.amount_total',
                 'sale_order_id.order_line.price_subtotal',
                 'commission_type_id.calculation_base',
                 'commission_type_id.calculation_method',
                 'commission_type_id.default_rate',
                 'commission_rate')
    @api.depends('base_amount', 'commission_rate', 'commission_percentage', 'commission_fixed_amount', 'computation_type')
    def _compute_commission_amount(self):
        """Sale-order-aware computation. Populates base_amount from the Sale
        Order per the Commission Type's calculation base, syncs the mixin
        computation fields from the rate, then routes through the mixin's
        _set_commission_amounts so commission_amount and any cascaded lines
        stay consistent with property-mgmt's concrete lines."""
        for line in self:
            order = line.sale_order_id
            ctype = line.commission_type_id
            base = order.amount_untaxed if order else 0.0
            if order and ctype:
                if ctype.calculation_base == 'unit_price':
                    base = sum(order.order_line.mapped('price_subtotal'))
                elif ctype.calculation_base == 'order_total':
                    base = order.amount_total
                else:
                    base = order.amount_untaxed
            line.base_amount = base
            line.currency_id = order.currency_id or self.env.company.currency_id

            rate = line.commission_rate or (ctype.default_rate if ctype else 0.0)
            if ctype and ctype.calculation_method == 'fixed':
                line.computation_type = 'fixed_amount'
                line.commission_fixed_amount = rate
            else:
                line.computation_type = 'property_price'
                line.commission_percentage = rate
        self._set_commission_amounts()

    # ----- mixin hooks (sale.order doesn't have a per-line contract value
    #       beyond what commission_type_id gave us — base_amount carries it) --

    def _get_contract_value_base(self):
        self.ensure_one()
        return self.base_amount or 0.0

    def _get_parent_contract(self):
        self.ensure_one()
        return self.sale_order_id

    def _get_base_line(self):
        # commission.line has no self-referencing base_line_id; commission-
        # received style cascading is reserved for property-mgmt's concrete
        # lines. Empty recordset keeps _check_base_line valid.
        self.ensure_one()
        return self.browse()

    # ----- billing overrides ------------------------------------------------
    # No PO step: bills are generated directly from calculated/confirmed
    # lines, and can only be posted once the related customer invoice of the
    # same sale order is fully paid (see _check_commission_eligible).

    def _get_billable_lines(self):
        return self.filtered(
            lambda l: l.state in ('calculated', 'confirmed') and not l.bill_id)

    def _get_bill_line_vals(self, line, contract):
        vals = super()._get_bill_line_vals(line, contract)
        vals['commission_line_id'] = line.id
        return vals

    def _check_commission_eligible(self):
        """A commission bill may only be posted once payment has been received
        against the related customer invoice of the same sale order. Legacy
        lines with neither a sale order nor a source invoice have no related
        invoice to gate on and stay billable."""
        for line in self:
            invoice = line.source_invoice_id
            if not invoice and line.sale_order_id:
                invoice = line.sale_order_id.invoice_ids.filtered(
                    lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
                )[:1]
            if not line.sale_order_id and not line.source_invoice_id:
                continue
            if not invoice:
                raise UserError(_(
                    'Invalid operation: commission "%s" cannot be billed yet.\n'
                    'No source invoice found for sale order %s — the commission '
                    'is generated when the customer invoice of the sale order is '
                    'posted, and the bill can only be posted once that invoice '
                    'is fully paid.'
                ) % (line.display_name, line.sale_order_id.name or _('(none)')))
            if invoice.payment_state != 'paid':
                raise UserError(_(
                    'Invalid operation: the commission bill for "%s" cannot be '
                    'posted yet.\n\n'
                    'The related customer invoice %s (sale order %s) is %s — it '
                    'must be fully paid first. Register the customer payment '
                    'against invoice %s, then retry the billing.'
                ) % (
                    line.display_name,
                    invoice.name,
                    line.sale_order_id.name or _('(none)'),
                    dict(invoice._fields['payment_state'].selection).get(
                        invoice.payment_state, invoice.payment_state),
                    invoice.name,
                ))

    def _no_billable_message(self):
        return _(
            'Invalid operation: no calculated or confirmed, unbilled commission '
            'lines to process.\n\n'
            'Commissions are generated automatically when the customer invoice '
            'of the sale order is posted. Confirm the lines you want to bill '
            '(state must be "Calculated" or "Confirmed"), then retry.')

    def _generate_bills(self, post=False):
        zero_lines = self._get_billable_lines().filtered(
            lambda l: not l.commission_amount)
        if zero_lines:
            raise UserError(_(
                'Invalid operation: cannot generate commission bill(s) for %s '
                '— the commission amount is zero. Set the rate or base amount '
                'first, then retry.'
            ) % ', '.join(zero_lines.mapped('display_name')))
        result = super()._generate_bills(post=post)
        self.filtered(lambda l: l.bill_id).write({'state': 'processed'})
        return result

    def action_mark_calculated(self):
        for line in self:
            if line.state == 'draft':
                line.state = 'calculated'
        return True

    def action_confirm(self):
        for line in self:
            if line.state == 'calculated':
                line.state = 'confirmed'
        return True
