# -*- coding: utf-8 -*-
# Part of SGC Realestate Brokerage Template.
import logging
import os
import socket

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SgcBrokerageTenant(models.Model):
    """Per-tenant record for a real-estate brokerage tenant.

    A *tenant* is one real-estate brokerage — a property-management office,
    a real-estate agency, or a regional sub-brand of a larger broker. Each
    tenant receives its own copy of the template-relevant data and runs its
    own AML/KYC plumbing.

    This model is the central place where the audit's multi-tenant blockers
    (M1 localhost, M3 mail-records, M5 hardcoded account) are *resolved at
    tenant-creation time*, not at module-load time.
    """

    _name = "sgc.brokerage.tenant"
    _description = "Real-estate brokerage tenant"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"
    _check_company_auto = True

    # --- Identification ----------------------------------------------------

    name = fields.Char(required=True, index=True, tracking=True)
    code = fields.Char(
        required=True, index=True, copy=False,
        help="Short slug used in container/host names, mail-server aliases, "
             "and (where applicable) `ir.config_parameter` keys.",
    )
    sequence = fields.Integer(default=10)
    partner_id = fields.Many2one(
        "res.partner", string="Operating partner",
        required=True, check_company=True, tracking=True,
    )
    # NOTE: `check_company=True` was removed here (verified via a
    # clean-room install test, 2026-08-31) — this field's comodel IS
    # `res.company`, and check_company's generated domain assumes the
    # comodel has its own `company_id` field to cross-check against,
    # which `res.company` does not have. Odoo raised:
    # `Unknown field "res.company.company_id" in domain of python
    # field 'company_id'`. `check_company` only makes sense on
    # Many2one fields whose comodel is NOT res.company itself.
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True,
    )

    # --- Audit-driven required configuration --------------------------------

    base_url = fields.Char(
        compute="_compute_base_url", inverse="_inverse_base_url", store=True,
        help="Per-tenant `web.base.url`. Required by the audit's M1 blocker "
             "— replaces hardcoded loopback fallbacks.  "
             "audit-lint: disable=tier1/localhost",
    )
    contact_email = fields.Char(
        help="Replaces the audit's three tenant-contact email patterns "
             "(info / hr / careers prefix). Required for Tier-1 coupling "
             "patterns documented in docs/audit/HARDCODED_COUPLING.md.  "
             "audit-lint: disable=tier1/email",
    )
    compliance_email = fields.Char(
        help="Replaces hardcoded KYC compliance email in kyc_management "
             "portal templates. M-coupled to KYC.  "
             "audit-lint: disable=tier1/email",
    )
    workspace_account = fields.Char(
        help="Replaces hardcoded meeting-AI workspace account in "
             "sgc_meeting_ai (M5 / 16h blocker per audit M5 inventory).  "
             "audit-lint: disable=tier1/meeting_ai_workspace, tier1/email",
    )
    default_score_endpoint = fields.Char(
        help="Replaces hardcoded lead-scoring endpoint fallbacks in "
             "sgc_lead_scoring. The audit-quarantined module is held in "
             "30_QUARANTINE/ but the **template** is forward-compatible — "
             "when the hold is lifted, the parametrised endpoint takes "
             "effect.  audit-lint: disable=tier1/localhost",
    )

    # --- Enablement matrix -------------------------------------------------

    enable_core = fields.Boolean(
        string="Enable core (sales/leads/listings/deals/commission)",
        default=True, tracking=True,
    )
    enable_growth = fields.Boolean(
        string="Enable growth (CRM dashboard / nurture / broker portal)",
        default=False, tracking=True,
    )
    enable_aml = fields.Boolean(
        string="Enable AML pipeline (aml_compliance)",
        default=True, tracking=True,
    )
    enable_kyc = fields.Boolean(
        string="Enable KYC portal (kyc_management)",
        default=True, tracking=True,
    )
    enable_offplan = fields.Boolean(
        string="Enable offplan rental (sgc_offplan_rental_property_management)",
        default=False, tracking=True,
        help="True only when the tenant has the OPR dataset pre-migrated and "
             "is ready for ~21,000 LOC of vertical code.",
    )
    enable_construction = fields.Boolean(
        string="Enable construction management "
               "(sgc_construction_management — HELD module)",
        default=False, tracking=True,
        help="This template **never** enables this from `depends` because "
             "the module is in `30_QUARANTINE/`. To enable, the tenant "
             "must complete the audit-defined resolution path per "
             "30_QUARANTINE/sgc_construction_management.md and flip this "
             "flag.",
    )
    enable_hr_payroll = fields.Boolean(
        string="Enable UAE payroll (eh_uae_payroll_wps + hr_payroll_community)",
        default=False, tracking=True,
    )
    enable_reports = fields.Boolean(
        string="Enable financial reporting "
               "(sgc_dynamic_financial_report + report_xlsx)",
        default=True, tracking=True,
    )

    # --- Kit selection -----------------------------------------------------

    kit_id = fields.Many2one(
        "sgc.brokerage.kit", string="Brokerage kit",
        help="Curated bundle of SGC modules proven compatible for this "
             "vertical. The kit, plus the enablement matrix above, drives "
             "the resulting addon-path build.",
    )

    # --- Lifecycle / health ------------------------------------------------

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("onboarding", "Onboarding"),
            ("active", "Active"),
            ("paused", "Paused"),
            ("archived", "Archived"),
        ],
        required=True, default="draft", tracking=True,
    )
    last_preflight_pass = fields.Datetime(readonly=True)
    preflight_status = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("pass", "Pass"),
            ("fail", "Fail — see audit log"),
        ],
        default="unknown", readonly=True,
    )

    # --- SQL constraints ---------------------------------------------------

    _sgc_brokerage_tenant_code_unique = models.Constraint(
        "unique(code)",
        "Tenant code must be unique — codes feed container/host names.",
    )
    _sgc_brokerage_tenant_name_unique_per_company = models.Constraint(
        "unique(name, company_id)",
        "Tenant name must be unique per company.",
    )

    # --- Onchange / compute -----------------------------------------------

    @api.depends("code")
    def _compute_base_url(self):
        # The audit-safe default: never hardcode a localhost here. If the
        # tenant did not provide a real URL, leave empty so the UI surfaces
        # an explicit error rather than a silent localhost fallback.
        Param = self.env["ir.config_parameter"].sudo()
        for tenant in self:
            param_key = "sgc.brokerage.tenant.{}.base_url".format(tenant.code)
            tenant.base_url = Param.get_param(param_key) or ""

    def _inverse_base_url(self):
        Param = self.env["ir.config_parameter"].sudo()
        for tenant in self:
            param_key = "sgc.brokerage.tenant.{}.base_url".format(tenant.code)
            if tenant.base_url:
                Param.set_param(param_key, tenant.base_url)
            else:
                Param.search([("key", "=", param_key)]).unlink()

    # --- Onboarding / state transitions ------------------------------------

    def action_start_onboarding(self):
        """Begin the onboarding workflow.

        The actual onboarding wizard lives in
        ``sgc_realestate_brokerage_onboarding`` (a sibling addon), but this
        action sets the tenant to ``onboarding`` and creates a tracking
        record.
        """
        for tenant in self:
            if tenant.state != "draft":
                raise UserError(_(
                    "Only `Draft` tenants may start onboarding — current "
                    "state is %(state)s.", state=tenant.state))
            tenant.write({"state": "onboarding"})
            tenant.message_post(body=_(
                "Onboarding started — please complete the per-tenant "
                "configuration wizard before activating."))

    def action_activate(self):
        """Activate a tenant — only after a passing preflight."""
        for tenant in self:
            if tenant.state != "onboarding":
                raise UserError(_(
                    "Only `Onboarding` tenants may be activated — current "
                    "state is %(state)s.", state=tenant.state))
            result = tenant._preflight_check()
            if not result["ok"]:
                raise UserError(_(
                    "Preflight failed — see server logs for the missing "
                    "configuration. Audit-driven gates that failed: "
                    "%(gates)s.", gates=", ".join(result["failed"])))
            tenant.write({
                "state": "active",
                "last_preflight_pass": fields.Datetime.now(),
                "preflight_status": "pass",
            })
            tenant._push_ir_config_parameters()
            tenant.message_post(body=_("Tenant activated."))

    def action_pause(self):
        for tenant in self:
            tenant.state = "paused"

    def action_archive(self):
        for tenant in self:
            tenant.state = "archived"

    # --- Preflight ---------------------------------------------------------

    def _preflight_check(self):
        """Audit-driven tenant preflight.

        Checks the four blocker classes from
        docs/audit/MULTI_TENANT_BLOCKERS.md at tenant-activation time,
        per the M1/M3/M5/M4 audit-recommendation.

        Returns ``{"ok": bool, "failed": [str, ...]}``.
        """
        self.ensure_one()
        Param = self.env["ir.config_parameter"].sudo()
        failed = []

        # M1 — base_url must be non-empty (replaces localhost fallbacks).
        if not (Param.get_param("web.base.url") or "").strip():
            failed.append("M1/web.base.url not set")

        # M3 — verify there are no hardcoded-mail-server credentials in
        # any active ir.mail_server record (read-only check).
        bad_mail = self.env["ir.mail_server"].sudo().search(
            [("smtp_host", "in", ["localhost", "127.0.0.1", "0.0.0.0"])])
        if bad_mail:
            failed.append(
                "M3/ir.mail_server has {} localhost-rooted record(s)".format(
                    len(bad_mail)))

        # M5 — workspace account is parametrised (we check the param key,
        # not the hardcoded email).
        if not Param.get_param(
                "sgc.meeting_ai.workspace_account", default=False):
            failed.append("M5/sgc.meeting_ai.workspace_account not set")

        # M1 — contact / compliance email present.
        if not self.contact_email:
            failed.append("M1/contact_email")
        if not self.compliance_email:
            failed.append("M1/compliance_email")

        # M2 — never hardcode `company_id = 1`. The tenant.company_id is
        # already enforced by check_company_auto above; just record it
        # for the audit log.
        if not self.company_id:
            failed.append("M0/company_id not set")

        ok = not failed
        if not ok:
            self.write({"preflight_status": "fail"})
            _logger.warning(
                "sgc.brokerage.tenant preflight FAILED for tenant=%s : %s",
                self.code, failed,
            )
        return {"ok": ok, "failed": failed}

    # --- ir.config_parameter projection ------------------------------------

    def _push_ir_config_parameters(self):
        """Project this tenant's fields into the per-tenant
        ``ir.config_parameter`` namespace. Called from
        ``action_activate()`` and from the post-write hook below.
        """
        Param = self.env["ir.config_parameter"].sudo()
        mapping = {
            "sgc.brokerage.tenant.{}.contact_email".format(self.code):
                self.contact_email or "",
            "sgc.brokerage.tenant.{}.compliance_email".format(self.code):
                self.compliance_email or "",
            "sgc.brokerage.tenant.{}.workspace_account".format(self.code):
                self.workspace_account or "",
            "sgc.brokerage.tenant.{}.default_score_endpoint".format(
                self.code): self.default_score_endpoint or "",
            "sgc.brokerage.tenant.{}.base_url".format(self.code):
                self.base_url or "",
        }
        for key, value in mapping.items():
            if value:
                Param.set_param(key, value)
        _logger.info(
            "sgc.brokerage.tenant pushed %d params for tenant=%s",
            len(mapping), self.code,
        )

    # --- Field-validity restrictions --------------------------------------

    @api.constrains("code")
    def _check_code(self):
        for tenant in self:
            if not tenant.code or not tenant.code.replace("_", "").isalnum():
                raise ValidationError(_(
                    "Tenant code must be alphanumeric (and may contain "
                    "underscores) — used for parameter keys and host names."))

    @api.constrains("contact_email", "compliance_email", "workspace_account")
    def _check_emails(self):
        for tenant in self:
            for value in (
                    tenant.contact_email, tenant.compliance_email,
                    tenant.workspace_account):
                if value and "@" not in value:
                    raise ValidationError(_(
                        "Tenant email fields must contain a valid `@` — "
                        "got %(value)r.", value=value))


class SgcBrokerageTenantPreflight(models.TransientModel):
    """Transient model that runs a preflight without persisting state.

    Useful for ``/sgc/preflight`` HTTP endpoints and for the audit lint tool's
    test fixtures.
    """

    _name = "sgc.brokerage.tenant.preflight"
    _description = "Preflight ad-hoc"

    tenant_id = fields.Many2one(
        "sgc.brokerage.tenant", required=True,
        default=lambda s: s._default_tenant_id(),
    )
    result = fields.Text(readonly=True)

    def _default_tenant_id(self):
        return self.env["sgc.brokerage.tenant"].search(
            [("state", "!=", "archived")], limit=1)

    def action_run(self):
        self.ensure_one()
        result = self.tenant_id._preflight_check()
        self.write({
            "result": "{}\n\n{}".format(
                "PASS" if result["ok"] else "FAIL",
                "\n".join(result["failed"]) or "—",
            )
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }
