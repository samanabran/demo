# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Data residency — the real field, not just a document reference.

Per `docs/G27_PDPL_POSITION.md` §2 and the Wave 3 remediation order round
2 (defect: "Residency enum change is unevidenced"): the SGC estate
operates single-region today. This module extends `res.company` with the
enum and the disclosure/acceptance fields so the position document has a
concrete, testable implementation behind it — not just a comment in a
test docstring.

Class assignment (per amendment §4):
    * `data_residency_region` — VENDOR. Enum, defaults to
      'uae_mainland'. NOT a value the tenant chooses today (single
      region); the field exists so multi-region has somewhere to land
      without a schema migration.
    * `data_residency_region_locked` — VENDOR. True until the engineering
      team ships multi-region.
    * `data_residency_disclosure_url` — VENDOR. Populated at deploy
      time; blank in the template.
    * `data_residency_disclosure_accepted` — TENANT_CONFIG. Blank by
      default, no default value (R9) — the tenant's signed acceptance
      that they read the disclosure, not an attestation about where
      the data lives.
    * `data_residency_legal_regime_ref` — computed. Resolved by a
      rules-pack lookup keyed on the region, never hard-coded to a
      specific law. See `get_legal_regime_ref()`.

Why an enum and not a free-text field: DIFC and ADGM are separate legal
jurisdictions with their own data-protection regimes; entities in either
sit outside the federal PDPL entirely. A silent default to
'uae_mainland' for a DIFC or ADGM tenant would assert the wrong legal
regime on their behalf — an R9 violation in migration clothing. The
Selection field type rejects any value outside the four listed here at
the ORM layer, which is what makes the upgrade-migration test
(`sgc_process_control/tests/test_upgrade_migrations.py::test_02`)
meaningful rather than aspirational.
"""

from odoo import _, api, fields, models


# The mapping from region to legal-regime rules-pack key. This dict is
# the ONE place a hard-coded regime name is permitted: it maps the
# enum value to the *rules-pack lookup key*, not to a legal citation.
# The citation itself lives in sgc_regulatory_rules_pack as data.
_REGION_TO_REGIME_KEY = {
    "uae_mainland": "pdpl",
    "difc": "difc_dpl",
    "adgm": "adgm_dpr",
    "other": "other",
}


class ResCompanyDataResidency(models.Model):
    _inherit = "res.company"

    data_residency_region = fields.Selection(
        selection=[
            ("uae_mainland", "UAE Mainland"),
            ("difc", "DIFC (Dubai International Financial Centre)"),
            ("adgm", "ADGM (Abu Dhabi Global Market)"),
            ("other", "Other (reserved)"),
        ],
        default="uae_mainland",
        required=True,
        help=(
            "Where this tenant's data resides. VENDOR-set today because "
            "the estate operates single-region. The enum exists so a "
            "future multi-region deployment has somewhere to land "
            "without a schema migration and without ever silently "
            "defaulting a DIFC or ADGM tenant into the wrong regime."
        ),
    )
    data_residency_region_locked = fields.Boolean(
        default=True,
        help="True until the engineering team ships multi-region "
             "deployment. While locked, data_residency_region is not "
             "user-editable through the readiness UI (it remains "
             "editable by an administrator for correction purposes).",
    )
    data_residency_disclosure_url = fields.Char(
        help="Link to the public, plain-language disclosure describing "
             "where this tenant's data lives, who has access, the "
             "sub-processors, and the applicable legal regime. VENDOR — "
             "populated at deploy time.",
    )
    data_residency_disclosure_accepted = fields.Char(
        help=(
            "The tenant's signed acceptance that they have read the "
            "disclosure. TENANT_CONFIG. Blank by default, no default "
            "value (R9) — the tenant attests to having read the "
            "disclosure, not to where the data lives, which they "
            "cannot change today."
        ),
    )
    data_residency_legal_regime_ref = fields.Char(
        compute="_compute_data_residency_legal_regime_ref",
        store=True,
        help="Rules-pack lookup key for the applicable legal regime, "
             "resolved from data_residency_region. Never hard-coded to "
             "a specific law in code — see sgc_regulatory_rules_pack.",
    )

    @api.depends("data_residency_region")
    def _compute_data_residency_legal_regime_ref(self):
        for rec in self:
            rec.data_residency_legal_regime_ref = _REGION_TO_REGIME_KEY.get(
                rec.data_residency_region, "other",
            )
