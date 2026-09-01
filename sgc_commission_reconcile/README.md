# SGC Commission Reconcile

## 1. Purpose and scope

`sgc_commission_reconcile` resolves the Phase 9 `UNRESOLVED` audit status of
`sgc_commission` (see `docs/audit/MODULE_PROVENANCE.md`) by adding a
tenant-scoped, fully-configurable reconciliation layer on top of the existing
commission engine — configurable tiered rate policies, co-brokerage split
tracking with a hard 100% guard, cycle-time analytics (lead-to-commission,
Brief §1.3), and a lightweight, read-only bridge to invoice/payment
confirmation. It does **not** redefine commission calculation, does **not**
implement payout disbursement, and does **not** touch `account.move` beyond
reading `id` and `state`.

## 2. Dependency chain

```
sgc_commission  →  sgc_commission_reconcile  →  [future] sgc_commission_payout
```

`sgc_commission` remains the calculation engine of record (`commission.line`,
`commission.type`, `commission.dashboard`). This module extends
`commission.line` via `_inherit` and adds four new models
(`sgc.commission.policy`, `sgc.commission.policy.tier`,
`sgc.commission.partner_split`, `sgc.commission.invoice_bridge`) plus one
wizard (`sgc.commission.policy.apply.wizard`). A future
`sgc_commission_payout` addon is the intended home for actual payout
disbursement logic — see the Phase 9 boundary note below.

## 3. Configuration checklist (in order)

1. **Activate and configure real policies/tiers.** Every shipped default
   policy is inactive with all rates at 0.0 by design (see §7 of the
   generation spec). Go to *Real Estate → Commission → Commission Policies*,
   configure real `rate_pct` / `threshold_from` / `threshold_to` values per
   tier, then set `active = True`.
2. **Set `co_broker_default_split_pct` if co-brokerage is used.** This field
   defaults to 0.0 ("not yet configured") on every policy — it is never
   defaulted to an assumed market split. Configure it explicitly per tenant
   if co-brokerage deals are common.
3. **Apply policies to existing lines via the wizard.** Use
   *Real Estate → Commission → Apply Policy to Lines* to bulk-assign a
   configured policy to existing `commission.line` records.
4. **Wire invoice bridges as payments are confirmed.** Create a
   `sgc.commission.invoice_bridge` record linking a `commission.line` to its
   `account.move`, then use the **Confirm Receipt** button (an explicit
   click, never a silent onchange) once the invoice is actually paid.
5. **Confirm receipt to trigger `cycle_days`.** Confirming receipt writes
   `commission_received_date` back onto the commission line, which
   recomputes `cycle_days` (lead-to-commission cycle time, Brief §1.3).

## 4. Phase 9 boundary note

`commission.line.trigger_payout_calculation()` is a **deliberate stub** that
raises `UserError`. This is not a bug and must not be overridden ad hoc —
payout disbursement logic is explicitly out of scope for this module per the
generation brief's non-negotiable constraints. The correct place for that
logic is a future `sgc_commission_payout` addon that extends `commission.line`
the same way this module does.

## 5. Regulatory verification checklist (UNVERIFIED — confirm before go-live)

None of the following are encoded in this module by design. They must be
confirmed directly with your own legal counsel and the relevant regulator
before any policy is activated:

- Current RERA broker commission guidelines and any regulatory caps on
  brokerage commission percentages.
- UAE VAT treatment of brokerage commission invoices (see the open-notes
  log below — a hardcoded "VAT Amount (5%)" **label** already exists
  elsewhere in `sgc_commission`, informational text only, not a rate
  applied by this module).
- Co-brokerage split norms per your own legal counsel and partner
  agreements — `co_broker_default_split_pct` ships at 0.0 specifically so
  no assumed norm is silently applied.

## 6. Open-notes log

### From Section 0 CHECK 0.1 — model-name deviation (resolved)

The generation brief assumed the commission-line model was named
`sgc.commission.line`. The **confirmed** model name in this codebase is
**`commission.line`**, defined in `sgc_commission/models/commission_line.py`
(`_inherit = ['commission.line.mixin']`). All `_inherit` targets and
`Many2one` references in this module use the confirmed name.

### From Section 0 CHECK 0.4 — no existing tenant-isolation `ir.rule` pattern

No model in `sgc_realestate_brokerage_template/security/` had an existing
`tenant_id`-scoped `ir.rule` to mirror. The only existing rule scopes
`sgc.brokerage.tenant` itself by `company_id in company_ids` (that model IS
the anchor, so it has no `tenant_id` field to scope by). This module's
`security/ir_rule_tenant_isolation.xml` implements the most defensive
fallback available: `tenant_id.company_id in company_ids`. **This should be
re-verified** once (if) a direct user-to-tenant mapping is introduced
elsewhere in the estate — see the TODO comment at the top of that file.

### From Section 0 CHECK 0.5 — CLI-invocation mismatch (informational)

The brief's literal invocation, `python tools/audit_coupling_lint.py
--fail-on-findings` with no path argument, exits 2 ("No paths provided") —
a config error, not a findings failure. The tool requires an explicit
`--addons-path` / `--include-path`. Running the tool in its actual required
form against this module's scope returned `hard_count: 0` (exit 0). This
mismatch between the brief's assumed CLI and the tool's actual signature
should be reconciled in a future revision of either document.

### From Section 0 CHECK 0.6 — pre-existing hardcoded values (informational)

`grep` found two informational (non-blocking) matches inside `sgc_commission`
itself, **not** inside this module:

- `sgc_commission/data/commission_report_template.xml:68` and the duplicate
  copy at `sgc_commission/commission_ax/data/commission_report_template.xml:68`
  — both contain the literal label text `"VAT Amount (5%)"`. This is a
  UAE-VAT-rate hardcoded as **display text** in a report template, not a
  calculation input. Flag for the regulatory checklist above; this module
  does not touch or duplicate this template.
- `sgc_commission/models/commission_type.py:109` / the `commission_ax`
  duplicate — a validation message `"Percentage-based commission rate cannot
  exceed 100%."`. This is a validation bound (100% ceiling), not a default
  rate, and requires no action.

Also observed during Section 0 exploration (not requested by CHECK 0.6, but
worth recording): a stray `sgc_commission/models/commission_line.py.bak`
backup file exists alongside the live model file, and a nested
`sgc_commission/commission_ax/` sub-directory duplicates the
`commission.dashboard` and `commission.type` model names found in
`sgc_commission/models/`. Both look like leftover artefacts from a prior
merge or vendoring step; neither is referenced by this module, but both are
worth a cleanup pass given the audit estate's existing duplicate-module
findings (`audit_out/duplicates.csv`).

### Odoo 19 API uncertainty flagged during generation

1. **`partner_agency_id` domain** (`sgc_commission_partner_split.py`): the
   generation brief suggested filtering `res.partner` by
   `[('contact_type', '=', 'Co-Broker')]`. This field/value was **not**
   confirmed present on `res.partner` anywhere in the codebase context
   available during this generation (Section 0's mandated checks do not
   cover `res.partner` extensions). The domain was **left unset** rather
   than guessed at, with a `TODO(human-verify)` comment in the source file.
   Add the real domain once the field name is confirmed.
2. **`commission.line` required-field surface** (tests): the tests in
   `tests/test_cycle_days_computation.py` create bare `commission.line`
   records with only `tenant_id`, `lead_create_date`, and
   `commission_received_date` set. Whether `commission.line`'s other fields
   (e.g. `sale_order_id`, `commission_type_id`) are actually required at
   the ORM level was **not** independently verified — Section 0's checks
   confirmed only the model *name*, not its full field/constraint surface.
   **Flagged for human verification** against the live schema before
   trusting these tests to pass as written.
3. **Tests not executed.** No local Odoo 19 runtime was importable in the
   generation environment (`from odoo import fields` failed with
   `ModuleNotFoundError`). All three test files are syntactically valid
   Python (AST-verified — see the verification matrix in the delivery
   message) but have **not** been run against a live Odoo instance. Run
   `odoo-bin -d <test_db> -i sgc_commission_reconcile --test-enable
   --test-tags sgc_commission_reconcile --stop-after-init` before trusting
   them as passing.
4. **`<widget name="web_ribbon">`** used in
   `views/sgc_commission_policy_views.xml` to flag unconfigured
   (inactive) policies. This widget is standard in Odoo 17+ but its exact
   attribute set (`title`, `bg_color`) was not independently re-verified
   against the Odoo 19 web module source in this session — a low-risk,
   commonly-used widget, but flagged per the "do not invent APIs you are
   unsure of" instruction.
5. **Default data placeholder policies were NOT loaded as records.**
   `sgc.commission.policy.tenant_id` is `required=True`, but the brief's
   Section 7 default-data spec did not supply a `tenant_id` value (no
   demo tenant was designated). Loading four `required`-field-incomplete
   records would fail module installation, so the four placeholder policies
   in `data/sgc_commission_policy_default_data.xml` are shipped as XML
   **comments** with a clear `__REPLACE_WITH_TENANT_XMLID__` marker,
   rather than as live records missing a required field. A human (or the
   onboarding wizard) must uncomment and complete these once a concrete
   tenant exists.
