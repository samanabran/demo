# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Multi-tenant isolation — direct search, not with_company.

Wave 3 protocol §10: the test must attempt a direct search as a
tenant-B user for a tenant-A record — not a `with_company` read. The
test enumerates every model in the three modules that holds
tenant-scoped or personal data and asserts each has rule coverage.

Without per-model `ir.rule` records, a user with model access can
reach another tenant's records by direct search or RPC. `with_company`
governs default company scoping but does not prevent direct reads.
"""

import inspect

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


# Models in scope: every model in the three modules that holds
# tenant-scoped or personal data. Per the isolation ir.rule records
# written in this remediation pass, the domains for these are:
#   - process_control models: ('company_id', 'in', company_ids)
#   - tenant_readiness models with tenant_company_id: ('tenant_company_id', 'in', company_ids)
#   - tenant.fit.and.proper: ('subject_user_id.company_id', 'in', company_ids)
#   - tenant.decision.acknowledgement: ('acknowledged_for_tenant_id', 'in', company_ids)
# Models without `company_id` (e.g. the shared regulatory catalogue)
# are intentionally excluded — they are global machinery, not
# tenant-scoped data.
SCOPED_MODELS = {
    # process_control
    "process.exception": ("company_id",),
    "process.dlq": ("company_id",),
    "process.idempotency": ("company_id",),
    "process.sla": ("company_id",),
    # tenant_readiness
    "tenant.compliance.officer": ("tenant_company_id",),
    "tenant.fit.and.proper": ("subject_user_id",),
    "tenant.readiness.state": ("tenant_company_id",),
    "tenant.decision.acknowledgement": ("acknowledged_for_tenant_id",),
    "tenant.high.risk.override": ("tenant_company_id",),
    "tenant.readiness.config.value": ("tenant_company_id",),
}


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness", "sgc_isolation")
class TestIsolationDirectSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Two tenant companies, no configuration.
        cls.Company = cls.env["res.company"]
        cls.tenant_a = cls.Company.create({"name": "Tenant A (Direct-Search Isolation)"})
        cls.tenant_b = cls.Company.create({"name": "Tenant B (Direct-Search Isolation)"})
        # Two users, one per tenant, base.group_user only.
        cls.user_a = cls.env["res.users"].create({
            "name": "Tenant A User",
            "login": "test_isolation_tenant_a_user",
            "email": "iso_a@example.com",
            "company_id": cls.tenant_a.id,
            "company_ids": [(4, cls.tenant_a.id)],
            "group_ids": [(4, cls.env.ref("base.group_user").id)],
        })
        cls.user_b = cls.env["res.users"].create({
            "name": "Tenant B User",
            "login": "test_isolation_tenant_b_user",
            "email": "iso_b@example.com",
            "company_id": cls.tenant_b.id,
            "company_ids": [(4, cls.tenant_b.id)],
            "group_ids": [(4, cls.env.ref("base.group_user").id)],
        })

    def _seed_tenant_a_record(self, model_name):
        """Create a record on tenant A. Return the id."""
        Model = self.env[model_name]
        if model_name == "process.exception":
            return Model.create({
                "summary": "tenant A exception",
                "classification": "integration",
                "company_id": self.tenant_a.id,
            }).id
        if model_name == "process.dlq":
            exc = self.env["process.exception"].create({
                "summary": "tenant A exc for dlq",
                "classification": "integration",
                "company_id": self.tenant_a.id,
            })
            exc.write({"status": "dead_letter"})
            return self.env["process.dlq"].create({
                "summary": "tenant A dlq",
                "target_system": "DowJones",
                "operation": "screening.match",
                "exception_id": exc.id,
                "company_id": self.tenant_a.id,
            }).id
        if model_name == "process.idempotency":
            rec, _ = Model.get_or_create(
                "key_a", "DowJones", "screening.match",
            )
            rec.write({"company_id": self.tenant_a.id})
            return rec.id
        if model_name == "process.sla":
            return Model.create({
                "name": "tenant A SLA",
                "rule_code": "tenant_a_sla",
                "due_at": "2030-01-01 00:00:00",
                "company_id": self.tenant_a.id,
            }).id
        if model_name == "tenant.compliance.officer":
            return Model.create({
                "role": "primary",
                "user_id": self.user_a.id,
                "tenant_company_id": self.tenant_a.id,
                "appointment_date": "2026-09-01",
            }).id
        if model_name == "tenant.fit.and.proper":
            return Model.create({
                "subject_user_id": self.user_a.id,
                "outcome": "pass",
                "integrity_attested": True,
                "skills_attested": True,
                "professional_path_attested": True,
            }).id
        if model_name == "tenant.readiness.state":
            cap = self.env.ref("sgc_tenant_readiness.capability_screening")
            return Model.create({
                "tenant_company_id": self.tenant_a.id,
                "capability_id": cap.id,
            }).id
        if model_name == "tenant.decision.acknowledgement":
            return Model.create({
                "decision_summary": "tenant A ack",
                "decision_field_reference": "x",
                "decision_value": "y",
                "decision_source_reference": "z",
                "acknowledged_by_id": self.user_a.id,
                "acknowledged_for_tenant_id": self.tenant_a.id,
            }).id
        if model_name == "tenant.high.risk.override":
            return Model.create({
                "subject_customer_id": self.env["res.partner"].create(
                    {"name": "Tenant A Customer", "company_id": self.tenant_a.id}
                ).id,
                "tenant_company_id": self.tenant_a.id,
                "risk_classification": "high",
                "co_mlro_consulted_id": self.user_a.id,
                "co_mlro_consultation_at": "2026-09-01 10:00:00",
                "co_mlro_recommendation": "decline",
                "co_mlro_recommendation_rationale": "test",
                "management_decision": "decline",
                "decided_by_id": self.user_b.id,
                "decision_at": "2026-09-01 11:00:00",
            }).id
        raise ValueError(f"Unknown model: {model_name}")

    # ---- Rule coverage enumeration -----------------------------------

    def test_01_every_scoped_model_has_ir_rule_coverage(self):
        """Walk SCOPED_MODELS. For each, assert an ir.rule exists that
        scopes the model on the appropriate tenant field.

        Failure here means a model is uncovered — a green light over
        a real exposure. The test fails rather than skips.
        """
        IrRule = self.env["ir.rule"]
        missing = []
        for model_name, _fields in SCOPED_MODELS.items():
            rules = IrRule.search([("model_id.model", "=", model_name)])
            if not rules:
                missing.append(model_name)
                continue
            # Each rule must carry a `company_id` / `tenant_company_id`
            # / `subject_user_id` / `acknowledged_for_tenant_id` field
            # in its domain_force.
            ok = False
            for r in rules:
                d = r.domain_force or ""
                if any(field in d for field in SCOPED_MODELS[model_name]):
                    ok = True
                    break
            if not ok:
                missing.append(f"{model_name} (no tenant-scoped field in domain_force)")
        self.assertEqual(
            missing, [],
            f"Models without ir.rule tenant isolation coverage: {missing}. "
            f"Per Wave 3 protocol §10, every model holding personal or "
            f"tenant-scoped data MUST have a per-tenant ir.rule.",
        )

    # ---- Direct search blocks -----------------------------------------

    def test_02_tenant_b_direct_search_cannot_read_tenant_a_exception(self):
        Model = self.env["process.exception"]
        # Seed tenant A.
        a_id = self._seed_tenant_a_record("process.exception")
        # Tenant B user attempts a direct search by id. The
        # ir.rule must return an empty result OR raise AccessError.
        Model_as_b = Model.with_user(self.user_b).with_company(self.tenant_b)
        try:
            hits = Model_as_b.search([("id", "=", a_id)])
        except AccessError:
            return  # AccessError is a valid isolation outcome
        self.assertFalse(
            hits,
            f"Tenant B user read tenant A's process.exception id={a_id}. "
            f"Ir.rule tenant isolation failed.",
        )

    def test_03_tenant_b_direct_search_cannot_read_tenant_a_officer(self):
        Model = self.env["tenant.compliance.officer"]
        a_id = self._seed_tenant_a_record("tenant.compliance.officer")
        Model_as_b = Model.with_user(self.user_b).with_company(self.tenant_b)
        try:
            hits = Model_as_b.search([("id", "=", a_id)])
        except AccessError:
            return
        self.assertFalse(
            hits,
            f"Tenant B user read tenant A's tenant.compliance.officer "
            f"id={a_id}. Ir.rule tenant isolation failed.",
        )

    def test_04_tenant_b_direct_search_cannot_read_tenant_a_state(self):
        Model = self.env["tenant.readiness.state"]
        a_id = self._seed_tenant_a_record("tenant.readiness.state")
        Model_as_b = Model.with_user(self.user_b).with_company(self.tenant_b)
        try:
            hits = Model_as_b.search([("id", "=", a_id)])
        except AccessError:
            return
        self.assertFalse(
            hits,
            f"Tenant B user read tenant A's tenant.readiness.state "
            f"id={a_id}. Ir.rule tenant isolation failed.",
        )

    def test_05_tenant_b_direct_search_cannot_read_tenant_a_override(self):
        Model = self.env["tenant.high.risk.override"]
        a_id = self._seed_tenant_a_record("tenant.high.risk.override")
        Model_as_b = Model.with_user(self.user_b).with_company(self.tenant_b)
        try:
            hits = Model_as_b.search([("id", "=", a_id)])
        except AccessError:
            return
        self.assertFalse(
            hits,
            f"Tenant B user read tenant A's tenant.high.risk.override "
            f"id={a_id}. Ir.rule tenant isolation failed.",
        )

    def test_06_configuring_tenant_a_leaves_tenant_b_fully_blocked(self):
        """Configuration on A must not change the gate on B."""
        cap = self.env.ref("sgc_tenant_readiness.capability_screening")
        state_a = self.env["tenant.readiness.state"].create({
            "tenant_company_id": self.tenant_a.id,
            "capability_id": cap.id,
        })
        state_b = self.env["tenant.readiness.state"].create({
            "tenant_company_id": self.tenant_b.id,
            "capability_id": cap.id,
        })
        state_a.write({"state_reason": "Tenant A populated required fields."})
        # Tenant B's state must remain not_configured and gate_open=False.
        state_b_in_ctx = self.env["tenant.readiness.state"].with_user(
            self.user_b
        ).with_company(self.tenant_b).browse(state_b.id)
        # The state must either not be visible (isolation) or remain
        # not_configured.
        if state_b_in_ctx:
            self.assertEqual(
                state_b_in_ctx.state, "not_configured",
                "Tenant B's capability state changed when tenant A was configured",
            )
            self.assertFalse(
                state_b_in_ctx.gate_open,
                "Tenant B's gate opened when tenant A was configured",
            )
