# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# NEW MODEL — does not compete with `commission.line` / `commission.type`
# defined in `sgc_commission`. This is a per-tenant *policy* container:
# it configures WHICH rate bands apply to a transaction type, but the
# actual commission calculation engine remains inside `sgc_commission`
# (see `sgc_commission_line_reconcile.py` for the `_inherit` bridge).
#
# CRITICAL CONSTRAINT: no percentage, split ratio, or AED threshold is
# hardcoded anywhere in this file. `co_broker_default_split_pct` defaults
# to 0.0 — this is a "not yet configured" sentinel, never an assumed
# market rate.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SgcCommissionPolicy(models.Model):
    _name = "sgc.commission.policy"
    _description = "Commission Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    tenant_id = fields.Many2one(
        "sgc.brokerage.tenant",
        required=True,
        ondelete="cascade",
        index=True,
        check_company=True,
        tracking=True,
        help="Owning tenant. This policy applies only within this "
             "tenant's scope — see the tenant-isolation ir.rule in "
             "security/ir_rule_tenant_isolation.xml.",
    )
    transaction_type = fields.Selection(
        selection=[
            ("sale_offplan", "Sale — Off-Plan"),
            ("sale_secondary", "Sale — Secondary"),
            ("leasing", "Leasing"),
            ("pm_management", "Property Management Fee"),
        ],
        required=True,
        tracking=True,
        help="Brief 1.2 / 1.3 segmentation — off-plan, secondary, "
             "leasing each get independently configurable policies.",
    )
    calculation_basis = fields.Selection(
        selection=[
            ("property_value", "Percentage of Property Value"),
            ("fixed_aed", "Fixed AED Amount"),
            ("rent_value", "Percentage of Annual Rent"),
        ],
        required=True,
        default="property_value",
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.ref("base.AED"),
    )
    tier_ids = fields.One2many(
        "sgc.commission.policy.tier",
        "policy_id",
        string="Rate tiers",
    )
    co_broker_default_split_pct = fields.Float(
        string="Default co-broker split (%)",
        digits=(5, 2),
        default=0.0,
        help="Default percentage allocated to a co-broker when no "
             "explicit sgc.commission.partner_split record exists for "
             "a deal. 0.0 means 'not yet configured', NOT 'no split'. "
             "This value must be set explicitly by the tenant — it is "
             "NEVER defaulted to an assumed market figure (e.g. 50.0) "
             "by this module.",
    )
    active = fields.Boolean(default=True)
    notes = fields.Text()

    _sql_constraints = [
        ("sgc_commission_policy_unique",
         "unique(tenant_id, transaction_type, name)",
         "A policy with this name already exists for this tenant and "
         "transaction type."),
    ]

    @api.constrains("co_broker_default_split_pct")
    def _check_co_broker_default_split_pct(self):
        for policy in self:
            if not (0.0 <= policy.co_broker_default_split_pct <= 100.0):
                raise ValidationError(_(
                    "Policy %(name)s: co_broker_default_split_pct must be "
                    "between 0 and 100.", name=policy.name))
