# -*- coding: utf-8 -*-
# Part of SGC Commission Reconcile.
#
# Not independently executed in this generation session (no local
# Odoo runtime available). See README.md open-notes.
#
# ODOO 19 API NOTE: creating a bare `commission.line` record here
# assumes its other required fields (e.g. `sale_order_id`,
# `commission_type_id` per the confirmed view in
# sgc_commission/views/commission_actions.xml) either have sane
# defaults or are not actually required at the ORM level. This was
# NOT independently verified against `commission_line.py`'s full field
# list during Section 0 (out of scope for CHECK 0.1-0.6, which only
# confirmed the model NAME). Flagged for human verification before
# trusting this test to pass as written.
from datetime import date, datetime

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCycleDaysComputation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tenant = cls.env["sgc.brokerage.tenant"].create({
            "name": "Test Tenant — Cycle",
            "code": "test_cycle_tenant",
            "partner_id": cls.env.ref("base.res_partner_1").id,
        })

    def test_cycle_days_59(self):
        line = self.env["commission.line"].create({
            "tenant_id": self.tenant.id,
            "lead_create_date": datetime(2026, 1, 1, 9, 0, 0),
            "commission_received_date": date(2026, 3, 1),
        })
        # 30 days remaining in January (31 - 1) + 28 days in
        # non-leap-year February 2026 + 1 day into March = 59.
        self.assertEqual(line.cycle_days, 59)

    def test_cycle_days_zero_when_received_unset(self):
        line = self.env["commission.line"].create({
            "tenant_id": self.tenant.id,
            "lead_create_date": datetime(2026, 1, 1, 9, 0, 0),
        })
        self.assertEqual(line.cycle_days, 0)

    def test_cycle_days_clamped_to_zero_when_negative(self):
        line = self.env["commission.line"].create({
            "tenant_id": self.tenant.id,
            "lead_create_date": datetime(2026, 3, 1, 9, 0, 0),
            "commission_received_date": date(2026, 1, 1),
        })
        self.assertEqual(line.cycle_days, 0)
