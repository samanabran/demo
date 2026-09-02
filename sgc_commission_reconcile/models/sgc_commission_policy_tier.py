# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# NEW MODEL. `threshold_to == 0.0` is the explicit sentinel for
# "open-ended top tier, no upper bound" — this is a real modelling
# choice (not a bug) so a tenant configuring "everything above 2M AED"
# does not need a synthetic upper bound.
#
# CRITICAL CONSTRAINT: `rate_pct` and `fixed_aed_amount` default to
# 0.0. No rate is pre-populated with a plausible-looking market figure.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SgcCommissionPolicyTier(models.Model):
    _name = "sgc.commission.policy.tier"
    _description = "Commission Policy Tier"
    _order = "policy_id, threshold_from"

    name = fields.Char(
        compute="_compute_name", store=True, readonly=True,
    )
    policy_id = fields.Many2one(
        "sgc.commission.policy",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    threshold_from = fields.Monetary(
        currency_field="currency_id",
        required=True,
        default=0.0,
    )
    threshold_to = fields.Monetary(
        currency_field="currency_id",
        default=0.0,
        help="0.0 = open-ended top tier, no upper bound. Any positive "
             "value must exceed `threshold_from`.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="policy_id.currency_id",
        store=True,
        readonly=True,
    )
    rate_pct = fields.Float(
        string="Rate (%)",
        digits=(5, 4),
        required=True,
        default=0.0,
        help="Must be set explicitly per tenant — no default rate is "
             "encoded by this module.",
    )
    fixed_aed_amount = fields.Monetary(
        string="Fixed amount (AED)",
        currency_field="currency_id",
        default=0.0,
        help="Used only when the parent policy's calculation_basis is "
             "'fixed_aed'.",
    )
    active = fields.Boolean(default=True)

    @api.depends("threshold_from", "threshold_to", "rate_pct")
    def _compute_name(self):
        for tier in self:
            upper = (
                "{:,.0f}".format(tier.threshold_to)
                if tier.threshold_to
                else "∞"  # infinity symbol for open-ended top tier
            )
            tier.name = _(
                "Tier: %(lower)s–%(upper)s %(currency)s @ "
                "%(rate).2f%%"
            ) % {
                "lower": "{:,.0f}".format(tier.threshold_from),
                "upper": upper,
                "currency": tier.currency_id.name or "AED",
                "rate": tier.rate_pct,
            }

    @api.constrains("rate_pct")
    def _check_rate_pct_range(self):
        for tier in self:
            if not (0.0 <= tier.rate_pct <= 100.0):
                raise ValidationError(_(
                    "Tier %(name)s: rate_pct must be between 0 and 100.",
                    name=tier.name or tier.id))

    @api.constrains("threshold_from")
    def _check_threshold_from_non_negative(self):
        for tier in self:
            if tier.threshold_from < 0.0:
                raise ValidationError(_(
                    "Tier %(name)s: threshold_from must be >= 0.",
                    name=tier.name or tier.id))

    @api.constrains("threshold_from", "threshold_to")
    def _check_threshold_order(self):
        for tier in self:
            # threshold_to == 0.0 is the valid open-ended exception.
            if tier.threshold_to and tier.threshold_to <= tier.threshold_from:
                raise ValidationError(_(
                    "Tier %(name)s: threshold_to must exceed "
                    "threshold_from, unless threshold_to is 0.0 "
                    "(open-ended top tier).",
                    name=tier.name or tier.id))
