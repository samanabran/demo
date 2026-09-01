# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Tests for the CO/MLRO segregation mixin.

Per MoJ Notice 247/2026: a user holding the CO/MLRO role cannot be assigned
as agent on a deal or own a customer relationship. The mixin enforces this
in code.
"""

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


class _FakeDeal(models.AbstractModel):
    """A test consumer — a deal that holds an agent and a customer."""

    _name = "test.deal"
    _inherit = "tenant.mlro.segregation.mixin"
    _description = "Test Deal"

    user_id = fields.Many2one("res.users")
    customer_id = fields.Many2one("res.partner")


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness", "sgc_gate")
class TestMlroSegregation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.Officer = cls.env["tenant.compliance.officer"]
        cls.FitAndProper = cls.env["tenant.fit.and.proper"]
        cls.compliance_user = cls.env["res.users"].create({
            "name": "Compliance Officer Test",
            "login": "test_compliance_officer_segregation",
            "email": "compliance_officer_segregation@example.com",
            "company_id": cls.company.id,
            "groups_id": [(4, cls.env.ref("base.group_user").id)],
        })
        cls.normal_user = cls.env["res.users"].create({
            "name": "Normal Agent Test",
            "login": "test_normal_agent_segregation",
            "email": "normal_agent_segregation@example.com",
            "company_id": cls.company.id,
            "groups_id": [(4, cls.env.ref("base.group_user").id)],
        })
        fap = cls.FitAndProper.create({
            "subject_user_id": cls.compliance_user.id,
            "outcome": "pass",
            "integrity_attested": True,
            "skills_attested": True,
            "professional_path_attested": True,
        })
        cls.Officer.create({
            "role": "primary",
            "user_id": cls.compliance_user.id,
            "tenant_company_id": cls.company.id,
            "fit_and_proper_id": fap.id,
            "appointment_date": "2026-09-01",
        })

    def test_01_compliance_user_blocked_from_deal_assignment(self):
        Deal = self.env["test.deal"]
        deal = Deal.new({})
        deal.user_id = self.compliance_user
        with self.assertRaises(UserError):
            deal._assert_not_mlro_on_sales_activity()

    def test_02_normal_user_allowed(self):
        Deal = self.env["test.deal"]
        deal = Deal.new({})
        deal.user_id = self.normal_user
        # No raise.
        deal._assert_not_mlro_on_sales_activity()

    def test_03_override_with_rationale_allows(self):
        Deal = self.env["test.deal"]
        deal = Deal.new({})
        deal.user_id = self.compliance_user
        deal.override_segregation = True
        deal.override_rationale = "Subject of the case, not the agent."
        # No raise — the override is recorded.
        deal._assert_not_mlro_on_sales_activity()

    def test_04_override_without_rationale_blocked(self):
        Deal = self.env["test.deal"]
        deal = Deal.new({})
        deal.user_id = self.compliance_user
        deal.override_segregation = True
        # No rationale → block.
        with self.assertRaises(UserError):
            deal._assert_not_mlro_on_sales_activity()
