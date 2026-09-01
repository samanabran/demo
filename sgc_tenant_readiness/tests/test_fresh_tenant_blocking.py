# -*- coding: utf-8 -*-
# Part of SGC Tenant Readiness.
"""Fresh-tenant blocking matrix — the core of the ship gate.

Per Wave 3 protocol §8 and remediation order (round 1 item 6, round 2
defect 5).

For every capability in the catalogue, two tests:
  - On a fresh, empty tenant with zero configuration: the capability
    is blocked.
  - When the required set is fully populated (test_configured_*):
    the capability is genuinely ready — computed by
    `tenant.readiness.state._recompute_for_tenant()` reading
    `tenant.readiness.config.value`, not set by a human clicking a
    button. `action_mark_ready()` does not exist (round 2 removed it);
    there is no code path left that can open a gate without the data
    behind it being present.

Per R10, the configured tests are the only tests permitted to use a
pre-configured tenant fixture. The blocked tests start from an empty
tenant.

One real test_configured_* per capability (round 2 fix): the round-1
version had a single cumulative loop test standing in for six of the
seven capabilities and one capability whose "configured" test never
actually reached state=ready, because there was no completeness
algorithm to reach it with. That gap is closed here.
"""

from odoo.exceptions import UserError, ValidationError
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
            state = self.State.create({
                "tenant_company_id": self.company.id,
                "capability_id": cap.id,
            })
            self.assertEqual(state.state, "not_configured", f"{code}: not in not_configured")
            self.assertFalse(state.gate_open, f"{code}: gate_open must be False on empty tenant")


def _parse_csv(text):
    if not text:
        return []
    return [k.strip() for k in text.split(",") if k.strip()]


@tagged("post_install", "-at_install", "sgc_install", "sgc_tenant_readiness", "sgc_gate")
class TestFreshTenantBlockingConfigured(TransactionCase):
    """The configured half of the matrix. Per R10, these are the only
    tests permitted to use a pre-configured tenant fixture. Each test
    names itself test_configured_* to make the deviation from the
    empty-tenant default visible.

    One dedicated test per capability, plus a shared helper that
    populates the FULL required_tenant_config + required_tenant_decision
    set read directly from the capability record — so if a capability's
    required-field list changes, the test changes with it rather than
    silently testing a stale list.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Capability = cls.env["tenant.readiness.capability"]
        cls.State = cls.env["tenant.readiness.state"]
        cls.ConfigValue = cls.env["tenant.readiness.config.value"]
        cls.Ack = cls.env["tenant.decision.acknowledgement"]
        cls.company = cls.env.ref("base.main_company")

    def _populate_full_set(self, capability, tenant_company_id=None, skip_key=None):
        """Populate every required_tenant_config and
        required_tenant_decision key for `capability` on the given
        tenant. Decision keys get a linked acknowledgement, matching
        the constraint in tenant.readiness.config.value.

        skip_key, if given, is left unpopulated — used for the
        partial-configuration tests.
        """
        tenant_company_id = tenant_company_id or self.company.id
        config_keys = _parse_csv(capability.required_tenant_config)
        decision_keys = _parse_csv(capability.required_tenant_decision)

        for key in config_keys:
            if key == skip_key:
                continue
            self.ConfigValue.set_value(
                tenant_company_id, key, f"test-value-{key}",
                field_class="tenant_config",
            )
        for key in decision_keys:
            if key == skip_key:
                continue
            ack = self.Ack.create({
                "decision_summary": f"Test acknowledgement for {key}",
                "decision_field_reference": key,
                "decision_value": f"test-value-{key}",
                "decision_source_url": "https://example.test/source",
                "decision_source_reference": "Test source citation",
                "acknowledged_by_id": self.env.uid,
                "acknowledged_for_tenant_id": tenant_company_id,
            })
            self.ConfigValue.set_value(
                tenant_company_id, key, f"test-value-{key}",
                field_class="tenant_decision",
                acknowledgement_id=ack.id,
            )

    def _get_state(self, code):
        cap = self.env.ref(f"sgc_tenant_readiness.capability_{code}")
        state = self.State.search([
            ("tenant_company_id", "=", self.company.id),
            ("capability_id", "=", cap.id),
        ], limit=1)
        if not state:
            state = self.State.create({
                "tenant_company_id": self.company.id,
                "capability_id": cap.id,
            })
        return cap, state

    # ---- One real unblock test per capability -------------------------

    def test_configured_goaml_filing_unblocks_with_complete_set(self):
        cap, state = self._get_state("goaml_filing")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(state.state, "ready",
                         f"goaml_filing did not reach ready; missing={state.missing_keys}")
        self.assertTrue(state.gate_open)

    def test_configured_screening_unblocks_with_complete_set(self):
        cap, state = self._get_state("screening")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(state.state, "ready",
                         f"screening did not reach ready; missing={state.missing_keys}")
        self.assertTrue(state.gate_open)

    def test_configured_listing_publication_unblocks_with_complete_set(self):
        cap, state = self._get_state("listing_publication")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(state.state, "ready",
                         f"listing_publication did not reach ready; missing={state.missing_keys}")
        self.assertTrue(state.gate_open)

    def test_configured_tenancy_contract_unblocks_with_complete_set(self):
        cap, state = self._get_state("tenancy_contract")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(state.state, "ready",
                         f"tenancy_contract did not reach ready; missing={state.missing_keys}")
        self.assertTrue(state.gate_open)

    def test_configured_offplan_sales_unblocks_with_complete_set(self):
        cap, state = self._get_state("offplan_sales")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(state.state, "ready",
                         f"offplan_sales did not reach ready; missing={state.missing_keys}")
        self.assertTrue(state.gate_open)

    def test_configured_service_charge_unblocks_with_complete_set(self):
        cap, state = self._get_state("service_charge")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(state.state, "ready",
                         f"service_charge did not reach ready; missing={state.missing_keys}")
        self.assertTrue(state.gate_open)

    def test_configured_einvoicing_unblocks_with_complete_set(self):
        cap, state = self._get_state("einvoicing")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(state.state, "ready",
                         f"einvoicing did not reach ready; missing={state.missing_keys}")
        self.assertTrue(state.gate_open)

    def test_configured_einvoicing_blocks_without_revenue_band(self):
        """Wave 3 remediation round 3: UAE e-invoicing has at least three
        deadline tracks (Phase 1 ≥ AED 50m, Phase 2 below AED 50m,
        government entities on a separate and disputed track). Without
        knowing which band a tenant is in, applying a single hard-coded
        deadline pair gives the wrong date to whichever bands aren't the
        one that was hard-coded — which, for this product's actual
        target market of brokerages, is the majority of tenants (most
        sit below AED 50m, i.e. Phase 2, not Phase 1).

        This test proves the fail-closed property explicitly, by name,
        rather than relying on it being incidentally covered by the
        generic partial-configuration loop: every OTHER required field
        for e-invoicing can be fully populated, and the capability must
        still be blocked while einvoicing_revenue_band is unset.
        """
        cap, state = self._get_state("einvoicing")
        self._populate_full_set(cap, skip_key="einvoicing_revenue_band")
        state.action_recompute()
        self.assertFalse(
            state.gate_open,
            "einvoicing became ready with the revenue band unset — the "
            "wrong-deadline-to-most-tenants defect this test exists to "
            "catch.",
        )
        self.assertIn(
            "einvoicing_revenue_band", state.missing_keys or "",
            "missing_keys did not name einvoicing_revenue_band as the "
            "reason the gate is closed.",
        )

    # ---- Partial configuration still blocks, one per capability ------

    def test_configured_partial_config_still_blocks_every_capability(self):
        """For each capability, populate every required key EXCEPT the
        first one, and assert the gate stays closed. Missing even a
        single required field must not open the gate — the mirror
        image of test_08_no_capability_passes_while_unconfigured.
        """
        for code in CATALOGUE:
            cap, state = self._get_state(code)
            all_keys = _parse_csv(cap.required_tenant_config) + \
                _parse_csv(cap.required_tenant_decision)
            self.assertTrue(all_keys, f"{code} has no required fields declared")
            skip = all_keys[0]
            self._populate_full_set(cap, skip_key=skip)
            state.action_recompute()
            self.assertFalse(
                state.gate_open,
                f"{code}: gate opened with '{skip}' still missing",
            )
            self.assertIn(
                skip, state.missing_keys or "",
                f"{code}: missing_keys did not name '{skip}'",
            )

    # ---- Blocked override cannot be bypassed by completeness ---------

    def test_configured_manual_block_survives_full_configuration(self):
        """An administrator's manual block is a stronger override than
        completeness. Populating every field must not silently reopen
        a capability an admin explicitly closed.
        """
        cap, state = self._get_state("goaml_filing")
        state.action_mark_blocked("Held pending counsel review")
        self._populate_full_set(cap)
        state.action_recompute()
        self.assertEqual(
            state.state, "blocked",
            "A manual block was silently lifted by populating the "
            "required fields — action_recompute must not override "
            "action_mark_blocked.",
        )

    def test_configured_unblock_reverts_to_computed_not_to_ready(self):
        """action_unblock reverts to the computed state, not
        unconditionally to 'ready'. An unblocked-but-incomplete
        capability must land back in not_configured/in_progress, not
        ready.
        """
        cap, state = self._get_state("screening")
        state.action_mark_blocked("Held pending review")
        state.action_unblock()
        self.assertNotEqual(
            state.state, "ready",
            "action_unblock opened the gate without the required data "
            "being present.",
        )
        self.assertFalse(state.gate_open)
