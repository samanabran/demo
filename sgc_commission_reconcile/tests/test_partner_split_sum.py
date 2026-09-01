# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# Not independently executed in this generation session (no local
# Odoo runtime available). See README.md open-notes.
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPartnerSplitSum(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tenant = cls.env["sgc.brokerage.tenant"].create({
            "name": "Test Tenant — Splits",
            "code": "test_split_tenant",
            "partner_id": cls.env.ref("base.res_partner_1").id,
        })
        cls.agency_a = cls.env["res.partner"].create({"name": "Agency A"})
        cls.agency_b = cls.env["res.partner"].create({"name": "Agency B"})
        cls.agency_c = cls.env["res.partner"].create({"name": "Agency C"})

    def test_two_splits_40_each_no_error(self):
        Split = self.env["sgc.commission.partner_split"]
        Split.create({
            "tenant_id": self.tenant.id,
            "deal_ref": "DEAL-001",
            "partner_agency_id": self.agency_a.id,
            "split_pct": 40.0,
            "gross_commission_aed": 100000.0,
        })
        Split.create({
            "tenant_id": self.tenant.id,
            "deal_ref": "DEAL-001",
            "partner_agency_id": self.agency_b.id,
            "split_pct": 40.0,
            "gross_commission_aed": 100000.0,
        })
        total = sum(Split.search([
            ("tenant_id", "=", self.tenant.id),
            ("deal_ref", "=", "DEAL-001"),
        ]).mapped("split_pct"))
        self.assertEqual(total, 80.0)

    def test_two_splits_60_each_raises(self):
        Split = self.env["sgc.commission.partner_split"]
        Split.create({
            "tenant_id": self.tenant.id,
            "deal_ref": "DEAL-002",
            "partner_agency_id": self.agency_a.id,
            "split_pct": 60.0,
            "gross_commission_aed": 100000.0,
        })
        with self.assertRaises(ValidationError):
            Split.create({
                "tenant_id": self.tenant.id,
                "deal_ref": "DEAL-002",
                "partner_agency_id": self.agency_c.id,
                "split_pct": 60.0,
                "gross_commission_aed": 100000.0,
            })

    def test_split_aed_computation(self):
        split = self.env["sgc.commission.partner_split"].create({
            "tenant_id": self.tenant.id,
            "deal_ref": "DEAL-003",
            "partner_agency_id": self.agency_a.id,
            "split_pct": 30.0,
            "gross_commission_aed": 100000.0,
        })
        self.assertEqual(split.split_aed, 30000.0)

    def test_split_aed_zero_when_gross_unset(self):
        split = self.env["sgc.commission.partner_split"].create({
            "tenant_id": self.tenant.id,
            "deal_ref": "DEAL-004",
            "partner_agency_id": self.agency_a.id,
            "split_pct": 30.0,
        })
        self.assertEqual(split.split_aed, 0.0)
