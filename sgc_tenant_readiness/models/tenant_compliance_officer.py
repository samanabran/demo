# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Compliance Officer / MLRO and Alternate, with fit-and-proper records.

Per UAE MoJ Notice 247/2026:
    - The CO/MLRO role cannot be outsourced at all (Section 4.2).
    - Specific tasks may be outsourced only after a Letter of No Objection
      (LNOO) from the supervisory authority. The guidance lists "System
      Support" among the examples. Whether a SaaS licence to this product
      constitutes outsourcing an AML task is a question for each tenant's
      counsel — the product does not answer it for them.
    - An Alternate CO/MLRO is required (deputy, not single officer).
    - Both officers pass a fit-and-proper test on integrity, qualifications,
      experience, skills, and a documented professional path.
    - Records of qualification assessments and background verification are
      maintained (per MoET DNFBP Guidelines March 2026).
    - The appointment is notified to the supervisory authority.

Class assignment (per amendment §4):
    - All identity fields are TENANT_CONFIG. Blank by default. No defaults.
    - The LNOO reference field is TENANT_CONFIG. Blank by default.
    - The fit-and-proper record is a first-class child record of this one.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TenantComplianceOfficer(models.Model):
    _name = "tenant.compliance.officer"
    _description = "Tenant Compliance Officer / MLRO"
    _order = "role, id"
    _inherit = ["mail.thread"]
    _rec_name = "display_name"

    # --- Identity --------------------------------------------------------

    role = fields.Selection(
        selection=[
            ("primary", "Primary CO/MLRO"),
            ("alternate", "Alternate CO/MLRO"),
        ],
        required=True, index=True,
    )
    user_id = fields.Many2one(
        "res.users", required=True, index=True, tracking=True,
        help="The Odoo user account that holds the role.",
    )
    tenant_company_id = fields.Many2one(
        "res.company", required=True, index=True, tracking=True,
    )
    display_name = fields.Char(
        compute="_compute_display_name", store=True,
    )

    @api.depends("user_id.name", "role")
    def _compute_display_name(self):
        for rec in self:
            role_label = "Primary" if rec.role == "primary" else "Alternate"
            rec.display_name = f"{role_label} — {rec.user_id.name or '(no user)'}"

    # --- Identity verification ------------------------------------------

    fit_and_proper_id = fields.Many2one(
        "tenant.fit.and.proper",
        string="Fit-and-proper assessment",
        help="Required for both Primary and Alternate. Per MoJ Notice 247/2026.",
    )
    appointment_date = fields.Date(
        help="The date the appointment takes effect. The tenant notifies the "
             "supervisory authority per MoET DNFBP Guidelines March 2026.",
    )
    appointment_notification_date = fields.Date(
        help="The date the appointment was notified to the supervisory "
             "authority. Required for the readiness gate to consider the "
             "appointment complete.",
    )
    appointment_notification_reference = fields.Char(
        help="Reference / case number from the supervisory authority.",
    )

    # --- LNOO reference -------------------------------------------------

    lnoo_reference = fields.Char(
        help=(
            "Letter of No Objection reference from the supervisory authority, "
            "where one is required for outsourced tasks. Per MoJ Notice "
            "247/2026: 'System Support' is among the examples of an "
            "outsourced task. Whether this product's role requires an LNOO "
            "is for the tenant's counsel to determine. The product does "
            "not assert that an LNOO is or is not required. Blank by default."
        ),
    )

    # --- Status ----------------------------------------------------------

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("active", "Active"),
            ("superseded", "Superseded"),
        ],
        required=True, default="draft", index=True,
    )

    # --- Constraints -----------------------------------------------------

    _sql_constraints = [
        ("role_per_company_uniq",
         "UNIQUE(role, tenant_company_id)",
         "Each tenant company may have only one Primary and one Alternate."),
    ]

    @api.constrains("user_id", "tenant_company_id", "role")
    def _check_user_belongs_to_tenant(self):
        for rec in self:
            if rec.user_id and rec.user_id.company_id and rec.tenant_company_id:
                if rec.user_id.company_id != rec.tenant_company_id:
                    raise ValidationError(_(
                        "The officer's user account must belong to the same "
                        "company as the tenant."
                    ))

    def action_activate(self):
        for rec in self:
            if not rec.fit_and_proper_id:
                raise ValidationError(_(
                    "Cannot activate officer without a fit-and-proper "
                    "assessment. The CO/MLRO and Alternate must each pass "
                    "a fit-and-proper test per MoJ Notice 247/2026."
                ))
            rec.state = "active"
        return True
