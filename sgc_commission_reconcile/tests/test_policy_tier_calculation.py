# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# ODOO 19 API NOTE: `TransactionCase` and `tagged` are the standard
# Odoo test-framework imports; this follows the conventional pattern
# used across Odoo core and OCA addons. Not independently executed in
# this generation session (no local Odoo runtime available) — flagged
# in README.md open-notes for human verification against a live
# Odoo 19 instance before this test is trusted as passing.
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPolicyTierCalculation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tenant = cls.env["sgc.brokerage.tenant"].create({
            "name": "Test Tenant — Commission",
            "code": "test_commission_tenant",
            "partner_id": cls.env.ref("base.res_partner_1").id,
        })
        cls.policy = cls.env["sgc.commission.policy"].create({
            "name": "Test Off-Plan Policy",
            "tenant_id": cls.tenant.id,
            "transaction_type": "sale_offplan",
            "calculation_basis": "property_value",
        })

    def test_tier_name_contains_threshold_and_rate(self):
        tier = self.env["sgc.commission.policy.tier"].create({
            "policy_id": self.policy.id,
            "threshold_from": 0.0,
            "threshold_to": 2000000.0,
            "rate_pct": 2.0,
        })
        self.assertIn("2.00%", tier.name)
        self.assertIn("2,000,000", tier.name)

    def test_negative_rate_pct_raises(self):
        with self.assertRaises(ValidationError):
            self.env["sgc.commission.policy.tier"].create({
                "policy_id": self.policy.id,
                "threshold_from": 0.0,
                "threshold_to": 2000000.0,
                "rate_pct": -1.0,
            })

    def test_threshold_to_less_than_from_raises(self):
        with self.assertRaises(ValidationError):
            self.env["sgc.commission.policy.tier"].create({
                "policy_id": self.policy.id,
                "threshold_from": 2000000.0,
                "threshold_to": 1000000.0,
                "rate_pct": 1.5,
            })

    def test_open_ended_top_tier_no_error(self):
        # threshold_to == 0.0 is the valid open-ended exception.
        tier = self.env["sgc.commission.policy.tier"].create({
            "policy_id": self.policy.id,
            "threshold_from": 2000001.0,
            "threshold_to": 0.0,
            "rate_pct": 1.5,
        })
        self.assertEqual(tier.threshold_to, 0.0)
