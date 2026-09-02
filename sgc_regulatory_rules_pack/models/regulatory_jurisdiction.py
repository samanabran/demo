# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
"""Regulatory jurisdiction catalogue.

A jurisdiction is a regulatory regime. A constant is jurisdiction-scoped;
the jurisdiction record exists to give every constant a home and to make
jurisdiction-population auditable (Dubai populated at Wave 1, others as
empty placeholder rows per Q1 answer).
"""

from odoo import _, api, fields, models


class RegulatoryJurisdiction(models.Model):
    _name = "regulatory.jurisdiction"
    _description = "Regulatory Jurisdiction"
    _order = "sequence, code"
    _rec_name = "name"

    # --- Identification --------------------------------------------------

    name = fields.Char(required=True, index=True, translate=True)
    code = fields.Char(
        required=True,
        index=True,
        copy=False,
        help=(
            "Short machine-readable code, e.g. 'dubai', 'abu_dhabi', "
            "'difc', 'adgm'. Used as the lookup key in get_effective()."
        ),
    )
    sequence = fields.Integer(default=10)

    # --- Regulator metadata ----------------------------------------------

    primary_regulator = fields.Selection(
        selection=[
            ("dld", "Dubai Land Department (DLD)"),
            ("rera", "Real Estate Regulatory Authority (RERA, Dubai)"),
            ("adrec", "Abu Dhabi Real Estate Centre (ADREC)"),
            ("dfsa", "Dubai Financial Services Authority (DFSA)"),
            ("fsra", "Financial Services Regulatory Authority (ADGM)"),
            ("moet", "UAE Ministry of Economy and Tourism"),
            ("fiu", "UAE Financial Intelligence Unit"),
            ("cbuae", "Central Bank of the UAE"),
            ("fta", "Federal Tax Authority"),
            ("dubai_municipality", "Dubai Municipality"),
            ("other", "Other"),
        ],
        required=True,
    )
    notes = fields.Text()

    # --- Population status (Q1 answer-driven) ---------------------------

    population_status = fields.Selection(
        selection=[
            ("populated", "Populated — constants seeded"),
            ("placeholder", "Placeholder — code reserved, no constants"),
            ("out_of_scope", "Out of scope — no plans to populate"),
        ],
        default="placeholder",
        required=True,
        help=(
            "Dubai is 'populated' at Wave 1 exit per Q1. All other "
            "jurisdictions are 'placeholder' until explicitly seeded."
        ),
    )

    # --- Index of constant records -------------------------------------

    constant_ids = fields.One2many(
        "regulatory.constant", "jurisdiction_id",
        string="Constants",
    )
    constant_count = fields.Integer(
        compute="_compute_constant_count", store=True,
    )

    @api.depends("constant_ids")
    def _compute_constant_count(self):
        for rec in self:
            rec.constant_count = len(rec.constant_ids)

    _code_uniq = models.Constraint(
        "UNIQUE(code)", "Jurisdiction code must be unique.",
    )
