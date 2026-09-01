# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Fit-and-proper assessment record.

Per UAE MoJ Notice 247/2026 and the MoET DNFBP Guidelines of March 2026,
the CO/MLRO and Alternate must each pass a fit-and-proper test on:

    * integrity (no criminal record, no regulatory action, no disqualification)
    * qualifications (formal credentials, professional certifications)
    * experience (years in the field, role history)
    * skills (screening, investigation, regulatory reporting, training currency)
    * documented professional path (CV, references, employment history)

Records of qualification assessments and background verification are
maintained. The assessment is performed by the tenant; the product records
the outcome. The product does not perform the assessment.

Class assignment (per amendment §4): the record structure is VENDOR. The
content (integrity outcome, qualifications, etc.) is TENANT_CONFIG — the
tenant owns the assessment.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


ASSESSMENT_OUTCOMES = [
    ("pass", "Pass"),
    ("pass_with_conditions", "Pass with conditions"),
    ("fail", "Fail"),
    ("deferred", "Deferred pending verification"),
]


class TenantFitAndProper(models.Model):
    _name = "tenant.fit.and.proper"
    _description = "Tenant Fit-and-proper Assessment"
    _order = "assessment_date desc, id desc"
    _inherit = ["mail.thread"]
    _rec_name = "subject_user_id"

    # --- Subject ---------------------------------------------------------

    subject_user_id = fields.Many2one(
        "res.users", required=True, index=True,
        help="The user the assessment is about — the CO/MLRO or Alternate.",
    )
    assessment_date = fields.Date(required=True, default=fields.Date.today)
    assessor_name = fields.Char(
        help="Name of the person who performed the assessment. The "
             "assessment is the tenant's responsibility; the product "
             "records who performed it.",
    )
    assessor_role = fields.Char()

    # --- Five fit-and-proper criteria ------------------------------------

    integrity_attested = fields.Boolean(
        help="Integrity criterion (no criminal record, no regulatory action, "
             "no disqualification) has been attested. The attestation is "
             "the tenant's; the product records the outcome.",
    )
    integrity_attested_by_name = fields.Char()
    integrity_attested_on = fields.Date()
    integrity_source_url = fields.Char(
        help="Source of the integrity check (regulatory letter, screening "
             "result, etc.). The product does not perform the check.",
    )

    qualifications_summary = fields.Text(
        help="Formal credentials, professional certifications. Recorded "
             "as text — the tenant's HR system holds the documents.",
    )
    qualifications_attested_by_name = fields.Char()
    qualifications_attested_on = fields.Date()

    experience_years = fields.Integer(
        help="Years of relevant experience in the field.",
    )
    experience_summary = fields.Text()

    skills_attested = fields.Boolean(
        help="Skills criterion (screening, investigation, regulatory "
             "reporting, training currency) has been attested.",
    )
    skills_summary = fields.Text()

    professional_path_attested = fields.Boolean(
        help="Documented professional path (CV, references, employment "
             "history) has been reviewed and recorded.",
    )
    professional_path_reference = fields.Char(
        help="Reference to the tenant's HR file or equivalent.",
    )

    # --- Outcome ---------------------------------------------------------

    outcome = fields.Selection(
        ASSESSMENT_OUTCOMES, required=True, default="deferred", index=True,
    )
    conditions = fields.Text(
        help="Where outcome='pass_with_conditions', record the conditions here.",
    )
    notes = fields.Text()

    # --- Constraints -----------------------------------------------------

    @api.constrains("integrity_attested", "skills_attested",
                    "professional_path_attested")
    def _check_required_attestations(self):
        for rec in self:
            if rec.outcome in ("pass", "pass_with_conditions"):
                if not (rec.integrity_attested and rec.skills_attested):
                    raise ValidationError(_(
                        "A passing fit-and-proper assessment requires the "
                        "integrity and skills criteria to be attested."
                    ))

    _sql_constraints = [
        ("subject_date_uniq",
         "UNIQUE(subject_user_id, assessment_date)",
         "Only one fit-and-proper assessment per subject per date."),
    ]
