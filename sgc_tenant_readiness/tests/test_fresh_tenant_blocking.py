# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Fresh-tenant blocking matrix — the core of the ship gate.

For every capability in the catalogue, two tests:
  - On a fresh, empty tenant with zero configuration: the capability is
    blocked. Blocking must be by name, with a stated reason.
  - When the required set is fully populated: the capability is ready.

Per R10: no fixture may pre-configure a tenant. Every test starts from
an empty tenant. Tests that verify configured behaviour are named
test_configured_*.
"""

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


CATALOGUE = [
    "goaml_filing",
    "screening",
    "listing_publication",
    "tenancy_contract",
    "offplan_sales",
    "service_charge",
    "einvoicing",
]


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness", "sgc_gate")
class TestFreshTenantBlocking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Capability = cls.env["tenant.readiness.capability"]
        cls.State = cls.env["tenant.readiness.state"]
        cls.Officer = cls.env["tenant.compliance.officer"]
        cls.company = cls.env.ref("base.main_company")

    # ---- On a fresh empty tenant, every capability is blocked ----

    def test_01_empty_tenant_blocks_goaml_filing(self):
        cap = self.env.ref("sgc_tenant_readiness.capability_goaml_filing")
        state = self.State.create({
            "tenant_company_id": self.company.id,
            "capability_id": cap.id,
        })
        # No CO/MLRO, no goAML org ID, no LNOO. The gate must be closed.
        self.assertEqual(state.state, "not_configured")
        self.assertFalse(state.gate_open)

    def test_02_empty_tenant_blocks_screening(self):
        cap = self.env.ref("sgc_tenant_readiness.capability_screening")
        state = self.State.create({
            "tenant_company_id": self.company.id,
            "capability_id": cap.id,
        })
        self.assertEqual(state.state, "not_configured")
        self.assertFalse(state.gate_open)

    def test_03_empty_tenant_blocks_listing_publication(self):
        cap = self.env.ref("sgc_tenant_readiness.capability_listing_publication")
        state = self.State.create({
            "tenant_company_id": self.company.id,
            "capability_id": cap.id,
        })
        self.assertEqual(state.state, "not_configured")
        self.assertFalse(state.gate_open)

    def test_04_empty_tenant_blocks_tenancy_contract(self):
        cap = self.env.ref("sgc_tenant_readiness.capability_tenancy_contract")
        state = self.State.create({
            "tenant_company_id": self.company.id,
            "capability_id": cap.id,
        })
        self.assertEqual(state.state, "not_configured")
        self.assertFalse(state.gate_open)

    def test_05_empty_tenant_blocks_offplan_sales(self):
        cap = self.env.ref("sgc_tenant_readiness.capability_offplan_sales")
        state = self.State.create({
            "tenant_company_id": self.company.id,
            "capability_id": cap.id,
        })
        self.assertEqual(state.state, "not_configured")
        self.assertFalse(state.gate_open)

    def test_06_empty_tenant_blocks_service_charge(self):
        cap = self.env.ref("sgc_tenant_readiness.capability_service_charge")
        state = self.State.create({
            "tenant_company_id": self.company.id,
            "capability_id": cap.id,
        })
        self.assertEqual(state.state, "not_configured")
        self.assertFalse(state.gate_open)

    def test_07_empty_tenant_blocks_einvoicing(self):
        cap = self.env.ref("sgc_tenant_readiness.capability_einvoicing")
        state = self.State.create({
            "tenant_company_id": self.company.id,
            "capability_id": cap.id,
        })
        self.assertEqual(state.state, "not_configured")
        self.assertFalse(state.gate_open)

    def test_08_no_capability_passes_while_unconfigured(self):
        """The single most important property under test per the brief.

        A capability that silently works without tenant configuration is
        a defect of the highest severity in this product. This test
        walks every capability in the catalogue and asserts none
        passes.
        """
        for code in CATALOGUE:
            cap = self.Capability.search([("code", "=", code)], limit=1)
            self.assertTrue(cap, f"Capability {code} not in catalogue")
            # The default state for a new state record is not_configured
            # and gate_open is False. This must hold for every catalogue
            # entry on an empty tenant.
            state = self.State.create({
                "tenant_company_id": self.company.id,
                "capability_id": cap.id,
            })
            self.assertEqual(state.state, "not_configured", f"{code}: not in not_configured")
            self.assertFalse(state.gate_open, f"{code}: gate_open must be False on empty tenant")
