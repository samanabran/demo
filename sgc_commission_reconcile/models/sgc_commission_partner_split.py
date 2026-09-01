# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# NEW MODEL — co-brokerage partner split tracking. This is the "single
# most important financial guard" per the generation brief: the
# `_check_split_sum_le_100` constraint below prevents a tenant's total
# co-broker splits on one deal from ever exceeding 100%.
#
# `deal_ref` is kept as a plain Char (not an M2O) deliberately — the
# "deal" may currently live as a crm.lead, a sale.order, or a
# tenancy record depending on tenant configuration, and this model
# must stay agnostic of which. `crm_lead_id` is offered as an optional
# convenience link when the deal IS a CRM lead.
#
# ODOO 19 API NOTE (flagged for verification, not guessed): the domain
# `[('contact_type', '=', 'Co-Broker')]` on `partner_agency_id` assumes
# `res.partner` was extended elsewhere in the estate with a
# `contact_type` field carrying a 'Co-Broker' value. This field/value
# was NOT found during Section 0 verification (Section 0 did not
# check res.partner extensions — out of scope for the mandated checks).
# The domain below is commented out and replaced with a permissive
# no-op domain plus a TODO, rather than guessing at a field that may
# not exist. See README.md open-notes.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SgcCommissionPartnerSplit(models.Model):
    _name = "sgc.commission.partner_split"
    _description = "Co-Brokerage Partner Split"
    _inherit = ["mail.thread"]
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(
        compute="_compute_name", store=True, readonly=True,
    )
    tenant_id = fields.Many2one(
        "sgc.brokerage.tenant",
        required=True,
        ondelete="restrict",
        index=True,
        check_company=True,
        tracking=True,
    )
    deal_ref = fields.Char(
        required=True,
        index=True,
        help="crm.lead or sale.order reference — kept as Char, not "
             "M2O, so this model stays agnostic of which model the "
             "deal currently lives in.",
    )
    crm_lead_id = fields.Many2one(
        "crm.lead",
        ondelete="set null",
        index=True,
        help="Optional convenience link when the deal is a CRM lead.",
    )
    partner_agency_id = fields.Many2one(
        "res.partner",
        required=True,
        # TODO(human-verify): the brief's suggested domain
        # [('contact_type', '=', 'Co-Broker')] assumes a `contact_type`
        # Selection field with a 'Co-Broker' value was added to
        # res.partner elsewhere in the SGC estate. This was NOT
        # confirmed in Section 0 (out of scope for the mandated
        # checks — CHECK 0.1-0.6 do not cover res.partner). Left
        # undomained pending confirmation; add the real domain once
        # the field name/value is verified against the live schema.
        help="The co-broker agency (a res.partner record). NOTE: no "
             "domain filter is applied pending confirmation of how "
             "'co-broker' contacts are tagged in this estate — see "
             "README.md open-notes.",
    )
    split_pct = fields.Float(
        digits=(5, 2),
        required=True,
        default=0.0,
        help="Must be configured explicitly — never defaulted to an "
             "assumed market split.",
    )
    gross_commission_aed = fields.Monetary(currency_field="currency_id")
    split_aed = fields.Monetary(
        compute="_compute_split_aed", store=True, readonly=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.ref("base.AED"),
    )
    commission_line_id = fields.Many2one(
        "commission.line",
        ondelete="set null",
        index=True,
        help="Link to the sgc_commission line this split derives from. "
             "Model name confirmed via Section 0 CHECK 0.1 as "
             "`commission.line` (NOT `sgc.commission.line`).",
    )
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("paid", "Paid"),
            ("disputed", "Disputed"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    agreement_date = fields.Date()
    payment_date = fields.Date()
    notes = fields.Text()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("sgc_commission_partner_split_unique",
         "unique(tenant_id, deal_ref, partner_agency_id)",
         "A split for this partner agency on this deal already exists "
         "for this tenant."),
    ]

    @api.depends("deal_ref", "partner_agency_id", "split_pct")
    def _compute_name(self):
        for split in self:
            split.name = _("%(deal)s — %(partner)s @ %(pct).2f%%") % {
                "deal": split.deal_ref or "?",
                "partner": split.partner_agency_id.display_name or "?",
                "pct": split.split_pct,
            }

    @api.depends("gross_commission_aed", "split_pct")
    def _compute_split_aed(self):
        for split in self:
            if not split.gross_commission_aed or not split.split_pct:
                split.split_aed = 0.0
            else:
                split.split_aed = (
                    split.gross_commission_aed * split.split_pct / 100.0
                )

    @api.constrains("split_pct", "deal_ref", "tenant_id", "active")
    def _check_split_sum_le_100(self):
        """The single most important financial guard in this module:
        sum of split_pct across all active records sharing
        (tenant_id, deal_ref) must never exceed 100.0.
        """
        seen = set()
        for split in self:
            key = (split.tenant_id.id, split.deal_ref)
            if key in seen:
                continue
            seen.add(key)
            siblings = self.search([
                ("tenant_id", "=", split.tenant_id.id),
                ("deal_ref", "=", split.deal_ref),
                ("active", "=", True),
            ])
            total = sum(siblings.mapped("split_pct"))
            if total > 100.0 + 1e-6:
                raise ValidationError(_(
                    "Deal %(deal)s: total co-broker split_pct across all "
                    "partner_split records is %(total).2f%%, which "
                    "exceeds 100%%. Reduce one or more splits before "
                    "saving.",
                    deal=split.deal_ref, total=total))
