# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
"""Regulatory constant — effective-dated, jurisdiction-scoped, source-attributed.

This model is the canonical home for every regulatory constant referenced by
the real-estate workflow. Consumers read through ``get_effective()`` and never
hard-code the value. Migrating a hard-coded constant out of a consumer module
(e.g. the AED 55,000 out of ``aml_compliance/reports/goaml_report_print.xml``)
is done by inserting the record here and updating the consumer to look it up.
"""

from datetime import date, datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


def _coerce_date(value):
    """Coerce a date / datetime / string to a date for comparison."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return date.fromisoformat(value)
    raise TypeError(f"Cannot coerce {type(value).__name__} to date")


class RegulatoryConstant(models.Model):
    _name = "regulatory.constant"
    _description = "Regulatory Constant"
    _order = "jurisdiction_id, code, valid_from DESC, id DESC"
    _rec_name = "name"
    _inherit = ["mail.thread"]

    # --- Identification --------------------------------------------------

    name = fields.Char(
        required=True, index=True, translate=True,
        help="Human-readable label.",
    )
    code = fields.Char(
        required=True, index=True,
        help=(
            "Machine-readable key, e.g. 'rear_cash_threshold_aed'. "
            "Consumers call get_effective(code, jurisdiction_code, as_of) "
            "to read the value in force at a given date."
        ),
    )
    description = fields.Text(translate=True)
    notes = fields.Text(
        help="Migration provenance, deferral rationale, cross-references.",
    )

    # --- Scope -----------------------------------------------------------

    jurisdiction_id = fields.Many2one(
        "regulatory.jurisdiction", required=True, index=True,
        ondelete="restrict",
    )
    jurisdiction_code = fields.Char(
        related="jurisdiction_id.code", store=True, index=True,
    )

    category = fields.Selection(
        selection=[
            ("aml_threshold", "AML threshold (cash / virtual asset)"),
            ("filing_window", "Filing window / deadline"),
            ("notice_period", "Statutory notice period"),
            ("fee_rate", "Fee rate / amount"),
            ("form_name", "Regulatory form name"),
            ("retention_clock", "Record retention clock"),
            ("penalty", "Penalty ceiling"),
            ("index", "Index / market reference"),
            ("other", "Other"),
        ],
        required=True, index=True,
    )

    # --- Value -----------------------------------------------------------
    #
    # The value is one of value_numeric, value_text. Exactly one must be set
    # on each record. Consumers are responsible for choosing the right slot
    # based on the constant's category and unit.

    value_numeric = fields.Float(
        help="Numeric value when the constant is a number.",
    )
    value_text = fields.Char(
        help="Text value when the constant is a name, label, or code.",
    )
    unit = fields.Selection(
        selection=[
            ("aed", "AED"),
            ("percent", "Percent"),
            ("days", "Days"),
            ("working_days", "Working days"),
            ("months", "Months"),
            ("years", "Years"),
            ("hours", "Hours"),
            ("count", "Count (integer)"),
            ("text", "Free text"),
            ("bool", "Boolean"),
        ],
        required=True,
    )

    # --- Provenance ------------------------------------------------------

    source_url = fields.Char(
        help="Primary regulator source URL.",
    )
    source_reference = fields.Char(
        help="Citation: law number, resolution number, article, etc.",
    )
    verified_on = fields.Date(
        help="Date the rule was last verified against the primary source.",
    )
    verified_by = fields.Char(
        help="Name or identifier of the verifier.",
    )
    confidence = fields.Selection(
        selection=[
            ("verified", "Verified — primary source confirmed"),
            ("verified_secondary", "Verified (secondary) — multiple independent "
             "advisory/press sources corroborate; primary decision/law text not "
             "yet directly cited"),
            ("unverified", "UNVERIFIED — awaiting primary source confirmation"),
            ("conflicting", "Conflicting sources — see notes"),
        ],
        default="unverified", required=True, index=True,
        help="'verified' requires source_url + verified_on pointing at the "
             "primary legal text. 'verified_secondary' is for a fact that is "
             "corroborated by multiple independent secondary sources (advisory "
             "firms, press, an MoF/MoET communication) but where the primary "
             "decision text has not itself been directly cited yet — a real "
             "step above UNVERIFIED, still short of a primary-source citation.",
    )

    # --- Effective dating (mandatory) -----------------------------------

    valid_from = fields.Date(required=True, index=True)
    valid_to = fields.Date(
        index=True,
        help="Leave empty for an open-ended effective period.",
    )

    # --- Versioning ------------------------------------------------------

    version = fields.Integer(default=1, required=True)
    supersedes_id = fields.Many2one(
        "regulatory.constant",
        string="Supersedes",
        help="Previous record this entry replaces (for audit trail).",
    )
    superseded_by_id = fields.Many2one(
        "regulatory.constant",
        string="Superseded by",
        compute="_compute_superseded_by", store=True,
    )

    @api.depends("supersedes_id", "supersedes_id.superseded_by_id")
    def _compute_superseded_by(self):
        for rec in self:
            if rec.supersedes_id:
                rec.superseded_by_id = rec.id

    # --- Constraints -----------------------------------------------------

    @api.constrains("value_numeric", "value_text")
    def _check_value_xor(self):
        for rec in self:
            has_num = rec.value_numeric not in (False, None, 0.0) or rec.unit == "bool"
            has_txt = bool(rec.value_text)
            if rec.unit == "bool":
                # value_text carries "true"/"false"; numeric is ignored.
                continue
            if has_num and has_txt:
                raise ValidationError(_(
                    "Constant '%s' has both value_numeric and value_text. "
                    "Exactly one must be set."
                ) % rec.code)
            if not has_num and not has_txt:
                raise ValidationError(_(
                    "Constant '%s' has neither value_numeric nor value_text. "
                    "Exactly one must be set."
                ) % rec.code)

    @api.constrains("valid_from", "valid_to")
    def _check_validity_window(self):
        for rec in self:
            if rec.valid_to and rec.valid_to < rec.valid_from:
                raise ValidationError(_(
                    "Constant '%s': valid_to (%s) is before valid_from (%s)."
                ) % (rec.code, rec.valid_to, rec.valid_from))

    @api.constrains("confidence", "source_url", "verified_on")
    def _check_confidence_requires_provenance(self):
        for rec in self:
            if rec.confidence in ("verified", "verified_secondary"):
                if not rec.source_url:
                    raise ValidationError(_(
                        "Constant '%s' is marked '%s' but source_url "
                        "is empty. Both verified and verified_secondary "
                        "require source_url."
                    ) % (rec.code, rec.confidence))
                if not rec.verified_on:
                    raise ValidationError(_(
                        "Constant '%s' is marked '%s' but verified_on "
                        "is empty. Both verified and verified_secondary "
                        "require verified_on."
                    ) % (rec.code, rec.confidence))

    _code_version_uniq = models.Constraint(
        "UNIQUE(code, version)",
        "Constant code + version must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Odoo only re-validates @api.constrains fields that were present
        # in vals on create; a record created with neither value_numeric
        # nor value_text in vals (both left at their field defaults) would
        # otherwise pass silently. Force the check explicitly.
        records._check_value_xor()
        return records

    # --- API -------------------------------------------------------------

    @api.model
    def get_effective(self, code, jurisdiction_code, as_of=None):
        """Return the regulatory.constant record effective on ``as_of``.

        Lookup logic:
            - Match ``code`` and ``jurisdiction_code``.
            - Among matches, pick the record whose
              ``valid_from <= as_of < valid_to`` (or open-ended).
            - If multiple records match at the same effective date, the
              one with the highest ``version`` wins (latest revision).
            - If ``as_of`` is None, today is used.
            - If no record matches, raise ``UserError`` with a clear message.

        Returns the record. Consumers read ``value_numeric`` or
        ``value_text`` based on ``unit`` and ``category``.
        """
        if as_of is None:
            as_of = fields.Date.today()
        as_of = _coerce_date(as_of)

        domain = [
            ("code", "=", code),
            ("jurisdiction_id.code", "=", jurisdiction_code),
            ("valid_from", "<=", as_of),
            "|",
            ("valid_to", "=", False),
            ("valid_to", ">=", as_of),
        ]
        candidates = self.search(domain)
        if not candidates:
            raise UserError(_(
                "No regulatory.constant effective on %(date)s for "
                "code=%(code)s jurisdiction=%(jur)s. "
                "Add the entry to sgc_regulatory_rules_pack."
            ) % {"date": as_of, "code": code, "jur": jurisdiction_code})
        # Highest version wins.
        candidates_sorted = candidates.sorted("version", reverse=True)
        winner = candidates_sorted[0]
        if winner.confidence in ("unverified", "conflicting"):
            # Log but do not raise — the caller decides whether to block.
            # 'conflicting' is at least as dangerous as 'unverified': it
            # means sources actively disagree, not merely that no
            # primary source has been checked yet. A caller that reads
            # value_text off a conflicting constant and treats it as a
            # usable date has ignored a warning that fires either way.
            _logger = __import__("logging").getLogger(__name__)
            _logger.warning(
                "regulatory.constant %s (jurisdiction=%s, as_of=%s) "
                "is %s. source_url=%s verified_on=%s",
                code, jurisdiction_code, as_of, winner.confidence.upper(),
                winner.source_url, winner.verified_on,
            )
        return winner

    @api.model
    def get_effective_value(self, code, jurisdiction_code, as_of=None):
        """Convenience wrapper returning the raw value.

        Returns:
            - For ``unit='bool'``: Python ``bool`` parsed from value_text.
            - For numeric units: ``float(value_numeric)``.
            - For ``unit='text'``: ``str(value_text)``.
        """
        rec = self.get_effective(code, jurisdiction_code, as_of=as_of)
        if rec.unit == "bool":
            return str(rec.value_text or "").strip().lower() in ("true", "1", "yes")
        if rec.unit in ("aed", "percent", "days", "working_days",
                        "months", "years", "hours", "count"):
            return float(rec.value_numeric)
        if rec.unit == "text":
            return rec.value_text or ""
        # Fallback
        return rec.value_text or rec.value_numeric
