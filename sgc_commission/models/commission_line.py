# -*- coding: utf-8 -*-
from odoo import api, fields, models


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
        compute='_compute_amounts',
        store=True,
        readonly=False,
        help='Auto-filled from the Sale Order according to the selected '
             'Commission Type\'s Calculation Base (Sale Value / Order Total '
             'excl. tax / Order Total incl. tax). Overridable.',
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
    def _compute_amounts(self):
        """Sale-order-aware base amount. After populating base_amount, route
        through the mixin's _set_commission_amounts so commission_amount is
        recomputed via the shared hook chain (and stays consistent with
        property-mgmt's concrete lines)."""
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

            rate = line.commission_rate or (ctype.default_rate if ctype else 0.0)
            if ctype and ctype.calculation_method == 'fixed':
                line.commission_amount = rate
            else:
                line.commission_amount = base * (rate / 100.0)

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
