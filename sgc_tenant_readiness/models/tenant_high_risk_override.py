# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""High-risk customer override record — first-class, not a comment field.

Per amendment §10.4: the CO/MLRO must be consulted before senior management
onboards or retains a high-risk customer. Where management overrides that
advice the rationale must be recorded with the mitigation. The structure of
the override is therefore:

    - Customer / case reference
    - CO/MLRO recommendation (consulted, dated)
    - Senior management decision (proceed / decline / proceed-with-conditions)
    - Rationale for the override
    - Mitigation measures attached to the override
    - Signatures: who decided, who recorded, when
    - Acknowledgement recorded per the TENANT_DECISION ack log

Class assignment (per amendment §4):
    - The record's structure and state machine are VENDOR.
    - The CO/MLRO recommendation is the CO/MLRO's own judgement (TENANT_DECISION
      via the consultation record).
    - The management decision is the management's own judgement (TENANT_DECISION).
    - The rationale text is TENANT_DECISION — it is the management's rationale.
    - The mitigation text is TENANT_DECISION — it is the management's mitigation.

The product provides the engine. The tenant owns the substance.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TenantHighRiskOverride(models.Model):
    _name = "tenant.high.risk.override"
    _description = "Tenant High-Risk Customer Override"
    _order = "decision_at desc, id desc"
    _inherit = ["mail.thread"]
    _rec_name = "display_name"

    display_name = fields.Char(
        compute="_compute_display_name", store=True,
    )

    @api.depends("decision_at", "subject_customer_id")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"Override {rec.decision_at} — "
                f"{rec.subject_customer_id.name or '(no customer)'}"
            )

    # --- Subject ---------------------------------------------------------

    subject_customer_id = fields.Many2one(
        "res.partner", required=True, index=True,
        help="The customer the override is about. The high-risk classification "
             "is a tenant decision (their risk model); the record is the "
             "override against that classification.",
    )
    tenant_company_id = fields.Many2one(
        "res.company", required=True, index=True,
    )
    risk_classification = fields.Selection(
        selection=[
            ("high", "High risk"),
            ("pep", "PEP"),
            ("high_risk_country", "High-risk country"),
            ("complex_structure", "Complex structure"),
            ("adverse_media", "Adverse media"),
            ("other", "Other (see rationale)"),
        ],
        required=True,
    )
    risk_classification_other = fields.Char(
        help="Where risk_classification='other', record the reason here.",
    )

    # --- CO/MLRO consultation --------------------------------------------

    co_mlro_consulted_id = fields.Many2one(
        "res.users", required=True, index=True,
        help="The CO/MLRO or Alternate who was consulted. Must hold one of "
             "those roles at the time of consultation.",
    )
    co_mlro_consultation_at = fields.Datetime(required=True)
    co_mlro_recommendation = fields.Selection(
        selection=[
            ("proceed", "Proceed"),
            ("proceed_with_conditions", "Proceed with conditions"),
            ("decline", "Decline"),
            ("defer", "Defer pending further information"),
        ],
        required=True,
    )
    co_mlro_recommendation_conditions = fields.Text(
        help="Where the recommendation is 'proceed_with_conditions' or "
             "'defer', record the conditions here.",
    )
    co_mlro_recommendation_rationale = fields.Text(
        help="The CO/MLRO's rationale for the recommendation. Recorded "
             "verbatim. The CO/MLRO is the source; the product does not "
             "rewrite or summarise.",
    )

    # --- Management decision --------------------------------------------

    management_decision = fields.Selection(
        selection=[
            ("proceed", "Proceed"),
            ("proceed_with_conditions", "Proceed with conditions"),
            ("decline", "Decline"),
        ],
        required=True,
    )
    override_rationale = fields.Text(
        required=True,
        help="Where the management decision differs from the CO/MLRO's "
             "recommendation, record the rationale here. Required per "
             "amendment §10.4 — this is the recording of the override.",
    )
    mitigation = fields.Text(
        required=True,
        help="Mitigation measures attached to the override. Required per "
             "amendment §10.4.",
    )
    decision_at = fields.Datetime(
        required=True, default=fields.Datetime.now,
    )
    decided_by_id = fields.Many2one(
        "res.users", required=True, index=True,
        help="The senior manager who decided. Must be distinct from the "
             "CO/MLRO who was consulted (segregation of duties).",
    )

    # --- State machine --------------------------------------------------

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("awaiting_co_mlro", "Awaiting CO/MLRO consultation"),
            ("awaiting_management", "Awaiting management decision"),
            ("acknowledged", "Acknowledged"),
            ("rejected", "Rejected"),
            ("superseded", "Superseded"),
        ],
        required=True, default="draft", index=True,
    )

    # --- Linked acknowledgement -----------------------------------------

    acknowledgement_id = fields.Many2one(
        "tenant.decision.acknowledgement", readonly=True,
    )

    # --- Constraints -----------------------------------------------------

    @api.constrains("co_mlro_consulted_id", "decided_by_id")
    def _check_segregation(self):
        for rec in self:
            if (rec.co_mlro_consulted_id and rec.decided_by_id
                    and rec.co_mlro_consulted_id == rec.decided_by_id):
                raise ValidationError(_(
                    "The CO/MLRO and the deciding senior manager must be "
                    "different people. Segregation of duties is a "
                    "primary-source requirement."
                ))

    @api.constrains("override_rationale", "mitigation")
    def _check_override_text_present(self):
        for rec in self:
            if rec.management_decision and rec.decision_at:
                if not rec.override_rationale:
                    raise ValidationError(_(
                        "Override rationale is required."
                    ))
                if not rec.mitigation:
                    raise ValidationError(_(
                        "Mitigation is required."
                    ))

    def action_consult_co_mlro(self):
        for rec in self:
            rec.state = "awaiting_co_mlro"
        return True

    def action_record_co_mlro_recommendation(self):
        for rec in self:
            if rec.state != "awaiting_co_mlro":
                raise ValidationError(_(
                    "CO/MLRO consultation must be in progress to record "
                    "the recommendation."
                ))
            if not (rec.co_mlro_recommendation
                    and rec.co_mlro_recommendation_rationale):
                raise ValidationError(_(
                    "The CO/MLRO recommendation and its rationale are both "
                    "required."
                ))
            rec.state = "awaiting_management"
        return True

    def action_record_management_decision(self):
        for rec in self:
            if rec.state != "awaiting_management":
                raise ValidationError(_(
                    "Awaiting management decision to record it."
                ))
            if (rec.management_decision != rec.co_mlro_recommendation
                    and not (rec.override_rationale and rec.mitigation)):
                raise ValidationError(_(
                    "Where management's decision differs from the CO/MLRO's "
                    "recommendation, an override rationale and mitigation "
                    "are required. Per amendment §10.4."
                ))
            # Build the acknowledgement record.
            Ack = self.env["tenant.decision.acknowledgement"]
            ack = Ack.create({
                "decision_summary": (
                    f"High-risk override: {rec.subject_customer_id.name}"
                ),
                "decision_field_reference": (
                    f"tenant.high.risk.override/{rec.id}"
                ),
                "decision_value": (
                    f"Management decision: {rec.management_decision}. "
                    f"Rationale: {rec.override_rationale}. "
                    f"Mitigation: {rec.mitigation}"
                ),
                "decision_source_reference": (
                    "Recorded in tenant.high.risk.override"
                ),
                "acknowledged_by_id": rec.decided_by_id.id,
                "acknowledged_for_tenant_id": rec.tenant_company_id.id,
                "high_risk_override_id": rec.id,
            })
            rec.acknowledgement_id = ack.id
            rec.state = "acknowledged"
        return True
