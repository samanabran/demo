# `check_company` Verdict

> **One-line answer (per amendment §10 outstanding item 1):**
> **The removal of `check_company=True` from `company_id` at `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py:54` is a correct technical fix. PDPL tenant-isolation (G27 item 5) is a *system-level* property that depends on per-module `check_company=True` and per-model `ir.rule` records, neither of which is currently enforced across the estate. Wave 2 code on the party graph and the onboarding model must not begin until the architecture-wide isolation strategy is in writing — that document is `G27_PDPL_POSITION.md` (delivered as part of this turn).**

> **Citation reconciliation (per the user's flag):** the base brief cited `sgc_realestate_tenant.py:47`. That file does not exist in the estate (`ls` confirms). The actual file is `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py`. The base brief's path is a colloquial reference; the file and the line it points to are the same code the verdict addresses. Specifically:
>
> - The comment about the `check_company=True` removal is at **lines 46–50** of the actual file.
> - The `company_id` field declaration that the comment annotates is at **lines 53–55**; the field name itself (`company_id`) is on **line 54**.
> - Line 47 of the actual file is the second line of the comment block (the clean-room install test date line).
>
> The verdict addresses the same field. The path discrepancy is in the base brief, not in the verdict. **Citation corrected and reconciled in this revision.**

---

## What the code says

`sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py:42-56`:

```python
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
```

The comment is technically correct. The Odoo `check_company=True` decorator generates a domain clause that references the comodel's `company_id` field. Since `res.company` does not have a `company_id` field on itself (it IS the company), applying `check_company=True` on a `Many2one("res.company")` field raises `Unknown field "res.company.company_id"`. The decorator is correctly omitted on this one field.

## Why this is not a PDPL verdict

`check_company=True` on the `company_id` field of `sgc.brokerage.tenant` is the wrong thing to test. The right questions for PDPL tenant isolation are:

1. **Does every other model in the estate have a `company_id` field that is required, defaulted to `env.company`, and never user-editable on a different tenant's record?**
2. **Does every company-scoped `Many2one` field on every model carry `check_company=True`?**
3. **Does every company-scoped model have a corresponding `ir.rule` record with a `('company_id', 'in', company_ids)` domain, applied to the appropriate user group?**
4. **Is the OPR's tenant-isolation status known, given the module is UNRESOLVED?**
5. **Are there access paths that bypass `company_id` — SQL, controllers, RPC, mail-follower add, attachments?**

The current state per the audit (`docs/audit/MULTI_TENANT_BLOCKERS.md`):

- **M1 (URLs):** resolved by the brokerage template's `web.base.url` override. ✓
- **M3 (mail):** resolved by the brokerage template's per-tenant `contact_email` and `compliance_email`. ✓
- **M5 (workspace):** resolved by the brokerage template's per-tenant `workspace_account`. ✓
- **M0 (company):** **not resolved at system scope.** The `sgc.brokerage.tenant` model is `check_company=True` on `partner_id` only. The other ~38 modules in the estate carry their own per-model handling.

The SGC estate has **at least one** `ir_rule_tenant_isolation.xml` (`sgc_commission_reconcile/security/ir_rule_tenant_isolation.xml`). The audit's `tools/audit_coupling_lint.py` enforces no tenant-scope on M0 at the system level. **It has never been verified across the whole estate.**

## The honest verdict

- **The `check_company` removal at line 54 is correct.** Not a defect.
- **PDPL tenant isolation is a system property, not a one-field property.** The Odoo `company_id` field is necessary but not sufficient.
- **Wave 2 must not begin** on the party graph, the G28 onboarding model, or any module that captures personal data **until** the G27 PDPL position document (`G27_PDPL_POSITION.md`) is in writing and signed off.
- The G27 PDPL position documents the residency, cross-border transfer, encryption, deletion, isolation, and DPA clause decisions — including the concrete `ir.rule` strategy that makes `check_company=True` and `company_id` enforcement actually work across the estate.

## What the user must decide

The user's "one-line answer" is here. The architectural decision is whether to:

- **A) Standardise on Odoo's `check_company=True` + `ir.rule` per model** (the orthodox Odoo multi-company pattern). Requires adding `check_company=True` to every Many2one and writing an `ir.rule` for every model. **All Wave 2 personal-data modules** must include these.
- **B) Build a per-tenant record-rule at the database level** via `ir.rule` on a single shared `company_id` column on every table, with a hand-rolled record-creation hook. **More invasive, but more visible to PDPL auditors.**
- **C) Use a database-per-tenant pattern** (the strongest isolation, the highest cost). Out of scope for a productised template.

**Recommendation: A.** It is the Odoo-native path, has the largest body of audit precedent in the OCA community, and is the smallest surface to maintain. The PDPL position document specifies the rules.

## Wave 2 code start hold

Per the user's instruction, **Wave 2 code start is held on this verdict and on the G27 PDPL position document.** The G28 onboarding model can be drafted (data model only, no enforcement wiring) but cannot be wired into any model that captures personal data until the isolation strategy is in place.

## References

- `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py:42-56` — the field in question.
- `docs/audit/MULTI_TENANT_BLOCKERS.md` — M0/M1/M3/M5 inventory.
- `sgc_commission_reconcile/security/ir_rule_tenant_isolation.xml` — the one working `ir.rule` tenant-isolation in the estate.
- `tools/audit_coupling_lint.py` — the lint that should be extended to enforce M0 system-wide.
- `G27_PDPL_POSITION.md` — the position document, delivered as part of this turn.
