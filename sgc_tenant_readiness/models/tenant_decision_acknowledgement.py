# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""TENANT_DECISION acknowledgement log.

Per amendment §3 R9: any field representing a legal or risk judgement ships
blank, with no default, and a mandatory source citation and acknowledgement
by the tenant before the dependent capability activates. This model records
the acknowledgement — who, when, what was acknowledged, the cited source.

The content of the decision itself is not in this log; the source field is
the citation, and the related field references the underlying record (a
risk-appetite record, an EDD trigger record, an override record, etc.).
"""

from odoo import _, api, fields, models


class TenantDecisionAcknowledgement(models.Model):
    _name = "tenant.decision.acknowledgement"
    _description = "Tenant Decision Acknowledgement"
    _order = "acknowledged_at desc, id desc"
    _inherit = ["mail.thread"]
    _rec_name = "decision_summary"

    decision_summary = fields.Char(
        required=True, translate=True,
        help="One-line description of the decision being acknowledged.",
    )
    decision_field_reference = fields.Char(
        help="Reference to the field or record carrying the decision. E.g. "
             "'sgc_listing_compliance.tenant_config.max_deal_value_aed' or "
             "'tenant.high.risk.override/<id>'.",
    )
    decision_value = fields.Text(
        help="The value the tenant entered. Recorded as text so the log "
             "captures the value as it was acknowledged.",
    )
    decision_source_url = fields.Char(
        help="Source citation. Required per R9: every TENANT_DECISION field "
             "carries a source.",
    )
    decision_source_reference = fields.Char(
        help="Citation: law number, regulation number, internal policy "
             "document, etc.",
    )

    # --- Acknowledgement -------------------------------------------------

    acknowledged_by_id = fields.Many2one(
        "res.users", required=True, index=True,
    )
    acknowledged_at = fields.Datetime(
        required=True, default=fields.Datetime.now, index=True,
    )
    acknowledged_for_tenant_id = fields.Many2one(
        "res.company", required=True, index=True,
    )

    # --- Linked records --------------------------------------------------

    high_risk_override_id = fields.Many2one(
        "tenant.high.risk.override",
        help="Set when this acknowledgement is for a high-risk override.",
    )
