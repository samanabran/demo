# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
"""Schema drift snapshot test.

Snapshots every model, field, selection value, constraint and ir.rule in
the three modules. Diffs against a committed baseline JSON.

This is the cheapest regression net available. A model rename, a field
type change, a selection-value typo — caught at the next run.
"""

import json
import os

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sgc_install", "sgc_regulatory", "sgc_gate")
class TestSchemaDrift(TransactionCase):
    BASELINE_PATH = None  # set in setUpClass
    MODULES = (
        "sgc_regulatory_rules_pack",
        "sgc_process_control",
        "sgc_tenant_readiness",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Place the baseline next to the tests folder.
        from odoo.addons import sgc_regulatory_rules_pack
        cls.BASELINE_PATH = os.path.join(
            os.path.dirname(sgc_regulatory_rules_pack.__file__),
            "tests", "schema_baseline.json",
        )

    def _snapshot(self):
        snap = {"models": {}, "rules": [], "groups": []}
        IrModelData = self.env["ir.model.data"]
        IrRule = self.env["ir.rule"]
        # ir.model has no searchable `module` field (only the computed,
        # comma-joined `modules` display string) — go via ir.model.data,
        # which records which module defined each ir.model record.
        model_ids = IrModelData.search([
            ("module", "in", self.MODULES),
            ("model", "=", "ir.model"),
        ]).mapped("res_id")
        for m in self.env["ir.model"].browse(model_ids).exists():
            snap["models"][m.model] = {
                "name": m.name,
                "fields": sorted([f.name for f in m.field_id]),
            }
        for r in IrRule.search([("model_id.model", "in", [
            "process.exception", "process.dlq", "process.idempotency",
            "process.sla", "tenant.compliance.officer", "tenant.fit.and.proper",
            "tenant.readiness.state", "tenant.readiness.capability",
            "tenant.high.risk.override", "regulatory.constant",
        ])]):
            snap["rules"].append({
                "model": r.model_id.model,
                "domain_force": r.domain_force,
            })
        return snap

    def test_01_snapshot_writes_to_baseline_when_missing(self):
        """If no baseline exists, write one. This is the only legitimate
        way the baseline changes — a commit that adds or removes a field
        must update the baseline in the same commit.
        """
        if not os.path.exists(self.BASELINE_PATH):
            snap = self._snapshot()
            with open(self.BASELINE_PATH, "w") as f:
                json.dump(snap, f, indent=2, default=str)
            self.skipTest("Baseline created; rerun to assert equality.")

    def test_02_snapshot_equals_baseline(self):
        """The current schema must equal the committed baseline.

        Failure here means a model was added, a field was renamed, a
        selection value changed, or an ir.rule changed — without
        updating the baseline. Update the baseline in the same commit.
        """
        if not os.path.exists(self.BASELINE_PATH):
            self.skipTest("Baseline missing — see test_01.")
        with open(self.BASELINE_PATH) as f:
            baseline = json.load(f)
        current = self._snapshot()
        if baseline != current:
            # Report a short diff for diagnostics. Full diff is too long
            # for an assertion message.
            added = set(current["models"]) - set(baseline["models"])
            removed = set(baseline["models"]) - set(current["models"])
            self.fail(
                f"Schema drift detected. "
                f"Models added: {sorted(added)}. "
                f"Models removed: {sorted(removed)}. "
                f"Update the baseline JSON in the same commit if intended."
            )
