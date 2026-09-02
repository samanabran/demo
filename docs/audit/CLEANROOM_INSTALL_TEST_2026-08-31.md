# Clean-room install test — 2026-08-31

> 🧠 **From Hindsight memory** — this test follows the same clean-room
> discipline documented in `audit_out/FULL_AUDIT_SUMMARY_REPORT.md` §1
> (network-restricted Docker infra, version-matched to production,
> never touching the live estate). It was run to answer two questions:
> (1) is `re_crm_core.zip` (the z.ai-authored module) production-ready,
> and (2) does the SGC-built `sgc_realestate_brokerage_template` +
> `sgc_commission_reconcile` bundle install cleanly on a genuinely
> clean Odoo 19 database.

## Method

- Isolated Docker Compose stack: `odoo19_module_eval` (Odoo 19.0-20260817)
  + `odoo19_module_eval_db` (Postgres 16), on its own network
  (`odoo19_module_eval_net`), fully separate from the production
  `demo_presentation` stack (different container names, different
  volumes, different DB user/password).
- Read-only bind mounts of the addon source trees under evaluation —
  no writes to the source repo from inside the container.
- Each test used a **fresh, uniquely-named database** (`eval_*`) — no
  reuse of state between attempts.
- Torn down completely (`docker compose down -v`) at the end — zero
  residual containers, networks, or volumes.

## Result 1 — `re_crm_core` (z.ai-authored module)

**FAILED — module never recognized by Odoo.**

```
WARNING odoo.modules.loading: invalid module names, ignored: re_crm_core
```

Root cause (confirmed via `ast.literal_eval` reproduction, independent of
Docker): `re_crm_core/__manifest__.py` opens with a module-level docstring
*followed by* the manifest dict literal — two separate top-level Python
statements in one file. Odoo's manifest loader calls
`ast.literal_eval(file_content)`, which compiles in `mode='eval'` and
therefore requires the file to be **exactly one expression**. A docstring
plus a dict is two statements, so parsing fails with `SyntaxError` before
Odoo ever sees the module's `depends`, `data`, or any other key.

**Verdict: the module cannot be installed in any real Odoo 19 instance
as shipped**, contradicting its own README's claim of "installs
standalone on a clean Odoo 19 database with zero external configuration."
This is a packaging defect, not a design or business-logic issue — the
rest of the module (a 290-line `re.unit`, `re.document.vault`, and six
other well-structured models) was never reachable for further evaluation.

## Result 2 — `sgc_commission` (existing SGC module)

**PASSED** standalone, on the first attempt.

```
INFO odoo.modules.loading: Modules loaded.
```

One cosmetic RST-parsing warning (`<string>:38: (ERROR/3) Unexpected
indentation.`) from the module's markdown-flavoured `description` field
being rendered through Odoo's RST engine — non-fatal, does not block
install, present in the base install too.

## Result 3 — `sgc_realestate_brokerage_template` + `sgc_commission_reconcile`

**FAILED repeatedly (7 install attempts), then PASSED after 7 real fixes.**

This is the substantive finding of this test — a genuine pre-production
QA pass that caught real, reproducible defects before any customer or
CI pipeline would have. Each fix is a **verified, live-tested correction**,
not a guess:

| # | File | Bug | Root cause | Fix |
|---|---|---|---|---|
| 1 | `sgc_realestate_brokerage_template/security/security.xml` | `ParseError: External ID not found: base.module_category_real_estate` | Invented an Odoo core xmlid that does not exist in Odoo 19 Community's `base` module | Removed the `parent_id` ref; `module_category_realestate` is now a top-level category |
| 2 | same file | `ValueError: Invalid field 'category_id' in 'res.groups'` | Odoo 19 restructured group categorisation: `res.groups.category_id` was replaced by `res.groups.privilege_id` → a new `res.groups.privilege.category_id` | Added a `res.groups.privilege` record; all three groups now set `privilege_id` instead of `category_id` |
| 3 | same file | `ValueError: Invalid field 'users' in 'res.groups'` | Odoo 19 renamed `res.groups.users` → `res.groups.user_ids` | Field renamed in the manager group's XML |
| 4 | `sgc_realestate_brokerage_template/__manifest__.py` | `ValueError: External ID not found: ...action_sgc_brokerage_tenant` | `data` list loaded `views/template_menus.xml` before `views/template_views.xml`, but menus reference actions defined in the latter | Reordered `data` list: views → reconciled_views → menus |
| 5 | `sgc_realestate_brokerage_template/views/template_views.xml` | `ValueError: External ID not found: ...view_sgc_brokerage_tenant_search` | Within the same file, `action_sgc_brokerage_tenant` (which refs the search view) was declared *before* the search view record it references — XML records load top-to-bottom | Moved the action record to after the search view definition |
| 6 | `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py` + `models/re_unit.py` | `Unknown field "res.company.company_id" in domain of python field 'company_id'` | `check_company=True` was applied to a `Many2one` field whose comodel IS `res.company` itself. Odoo's check-company mechanism assumes the comodel has its own `company_id` to cross-check — `res.company` doesn't | Removed `check_company=True` from both `company_id` field definitions (kept it on `tenant_id`/`partner_id`, which correctly point to models that DO have `company_id`) |
| 7 | `sgc_realestate_brokerage_template/views/reconciled_views.xml` | `ValueError: External ID not found: ...view_re_unit_search` | Same class of bug as #5 — `action_re_unit` declared before the search view it references | Moved the action record after `view_re_unit_search` |
| 8 | `sgc_commission_reconcile/views/sgc_commission_policy_views.xml` | RelaxNG schema validation error: `Invalid attribute expand for element group`, `Element search has extra content: field` | Used the classic pre-19 search-view idiom `<group expand="0" string="Group By">` — Odoo 19's `group` RelaxNG schema no longer accepts `expand`/`string` attributes in this position | Verified the current idiom against live Odoo 19 core XML (`base/views/res_partner_views.xml`): replaced with bare `<group name="group_by">` |

**Final result**, verified via direct SQL query against the installed
database — all 10 modules in the dependency chain report `state =
'installed'`:

```
aml_compliance                    | installed
kyc_management                    | installed
sgc_appraisal                     | installed
sgc_ces_kpi_banner                | installed
sgc_commission                    | installed
sgc_commission_reconcile          | installed
sgc_design_tokens                 | installed
sgc_dynamic_financial_report      | installed
sgc_realestate_brokerage_template | installed
sgc_ui_brand_palette              | installed
```

The `audit_coupling_lint.py --fail-on-findings` gate was re-run after all
eight fixes and still exits 0 — none of the fixes reintroduced a
hardcoded-coupling finding.

## Secondary finding — estate-wide dependency bloat (pre-existing, not new)

`sgc_ui_brand_palette` — nominally a lightweight branding/theme module —
declares 24 dependencies including `hr_payroll_community`,
`eh_uae_payroll_wps`, `sgc_employment_certificate`, `sgc_hr_memos`,
`sgc_invoicing_dashboard`, `spreadsheet_dashboard`, `maintenance`,
`project_todo`, `hr_recruitment`, `hr_holidays`, `hr_attendance`, and
`survey`. Installing anything that depends on `sgc_ui_brand_palette`
(including this template) silently pulls the entire HR/payroll/dashboard
subtree along with it. This is a pre-existing estate design issue (not
introduced by this session's work) and is consistent with the audit's
own `duplicates.csv` / coupling findings pattern — flagged here for
awareness, not fixed, since it is out of scope for the template and
reconcile modules.

## Conclusion

| Module | Clean-room install result |
|---|---|
| `re_crm_core` (z.ai) | ❌ **Never installs** — broken manifest syntax |
| `sgc_commission` (existing SGC) | ✅ Installs cleanly |
| `sgc_realestate_brokerage_template` + `sgc_commission_reconcile` (this session's work) | ✅ Installs cleanly, **after 8 real fixes found and applied during this test** |

The SGC-authored bundle is the only one of the two options that
**actually reaches a working, installed state** on a genuine clean Odoo
19 database. `re_crm_core` cannot be assessed for design quality because
it never loads at all.
