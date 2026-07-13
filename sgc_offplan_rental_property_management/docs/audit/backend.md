# Backend Audit — `sgc_offplan_rental_property_management` (Odoo 19.0)

Workstream: **Backend** — models, security, ORM/query performance, computed fields,
cron/scheduled actions, workflow/state logic, deprecated API, `res.config.settings`.
Audit date: 2026-07-09. Read-only; no source or DB modifications made.
Baseline commit: `20472a9`.

---

## 1. Executive Summary

The core data model is coherent and the recent cleanup work is visible and genuine:
dead crons are documented and removed, the previously-flagged `rent.bill` dead field
is gone, portal record rules are properly scoped, and file-upload validation and feed-
token handling show good security hygiene. The most important defects are in the
**financial/billing flows**: the rent-bill generator mis-charges non-monthly payment
frequencies (a real revenue bug), a stray trailing comma turns a vendor-bill
`partner_id` into a tuple, and the `rent.invoice` model that feeds the executive
dashboard's revenue KPIs is never populated by any reachable code path (so those KPIs
read zero). A cluster of medium/low issues concern draft-vs-posted invoice
inconsistency, image fields that store full-resolution copies, unindexed foreign keys
used inside per-record compute loops, deprecated `read_group`, and dead/broken wizard
code referencing models and selection values that do not exist.

**Issue count:** 2 High, 7 Medium, 6 Low (15 total). Most important: the rent-bill
generator under-bills quarterly/yearly contracts (see BE-01).

---

## 2. Issues Found

### BE-01 — Rent bill generator ignores payment frequency (under-billing) — HIGH
- **Root cause:** `action_generate_rent_bills` steps the schedule by `months_step`
  (1/3/12) but charges a flat `self.rent_amount` per generated bill and per backing
  invoice line, regardless of the period length. `rent_amount` is monthly by
  construction (`_compute_total_rent = rent_amount * duration_months`), so a quarterly
  contract is billed 1 month's rent every 3 months (~1/3 of contract value) and a
  yearly contract 1 month every 12.
- **Reference:** `models/core/rent_contract.py:205` (line amount `self.rent_amount`),
  `:216-217` (`amount` / `rent_amount`), loop `:193-223`; `months_step` at `:183`.
- **Fix:** multiply the per-period amount by `months_step` (or derive the period amount
  explicitly), e.g. `period_amount = self.rent_amount * months_step`, and use it for
  both the `account.move` line `price_unit` and the `rent.bill.amount`/`rent_amount`.
- **Effort:** S

### BE-02 — Trailing comma makes vendor-bill `partner_id` a tuple — HIGH
- **Root cause:** `data['partner_id'] = self.vendor_id.id,` has a stray trailing comma,
  producing a 1-tuple `(id,)` instead of an int. On the vendor branch of
  `action_crete_bill` this feeds a malformed `partner_id` into `account.move.create`,
  which raises / mis-writes. (The customer branch two lines up is correct.)
- **Reference:** `models/core/maintenance.py:163`.
- **Fix:** remove the trailing comma: `data['partner_id'] = self.vendor_id.id`.
- **Effort:** S

### BE-03 — `rent.invoice` never populated → dashboard revenue KPIs always zero — MEDIUM
- **Root cause:** `get_property_stats` sums `rent.invoice.amount` for `rent_total` and
  counts unpaid `rent.invoice` for `pending_invoice`, but the only creators of
  `rent.invoice` are `property.payment.wizard` (explicitly marked deprecated/unreachable
  in its own docstring) and `extend_contract_wizard` (which itself is broken, see
  BE-05). The canonical billing path (`action_generate_rent_bills`) creates
  `rent.bill` + `account.move`, never `rent.invoice`. Result: the executive dashboard's
  rental revenue and pending-rent tiles are effectively hard-zero.
- **Reference:** dashboard reads `models/core/property_details.py:209`, `:214-216`;
  non-populating billing path `models/core/rent_contract.py:170-227`.
- **Fix:** point the dashboard aggregation at the actually-populated model
  (`rent.bill` / its `account.move`s), or make the canonical flow also write
  `rent.invoice`. Pick one source of truth for rent revenue.
- **Effort:** M

### BE-04 — Rent-bill invoices bypass the `invoice_post_type` config and post nothing — MEDIUM
- **Root cause:** every other invoice-creating path
  (`maintenance.action_crete_invoice/bill`, `property_payment_wizard`,
  `extend_contract_wizard`) reads
  `sgc_offplan_rental_property_management.invoice_post_type` and posts when set to
  `automatically`. `action_generate_rent_bills` never reads it, so rent invoices are
  always left in `draft`. The lines also carry no `product_id`, no account, and no
  taxes, so the moves are thin/ambiguous compared to the rest of the module.
- **Reference:** `models/core/rent_contract.py:197-208` (move build, no post, no
  product/tax); config field `models/core/res_config.py:14-16`.
- **Fix:** honor `invoice_post_type` (post when `automatically`), and set a
  product/account (reuse the configured `installment_item_id`) so the move is complete
  and consistent with the other flows.
- **Effort:** M

### BE-05 — `extend_contract_wizard` writes an invalid `rent.invoice.type` — MEDIUM
- **Root cause:** the wizard creates `rent.invoice` with `type='full_rent'`, but
  `rent.invoice.type` is `Selection([('rent'),('service'),('deposit')])` — `full_rent`
  is not a valid value and raises on write. If this wizard is reachable from the UI
  (it has an ACL for `base.group_user`), the "extend contract" action crashes.
- **Reference:** `wizard/extend_contract_wizard.py:100-107`; selection defined
  `models/core/rent_invoice.py:46-50`.
- **Fix:** use a valid value (`'rent'`) or add `full_rent` to the selection. Verify the
  wizard is exercised before relying on it.
- **Effort:** S

### BE-06 — Dead wizard references non-existent model and field — MEDIUM
- **Root cause:** `property.payment.wizard` (self-documented as unreachable) references
  the model `contract.extra.service.line` and the field `tenancy.details.is_added_services`,
  neither of which exists anywhere in the module. Any invocation raises immediately.
  It is the module's only *other* `rent.invoice` writer, reinforcing BE-03.
- **Reference:** `wizard/property_payment_wizard.py:92-99`; confirmed absent via grep
  (only `contract.duration` defines a `_name` near that string; no
  `is_added_services` field).
- **Fix:** delete the wizard (and its ACL/`__init__` import) since it is dead and
  broken, rather than keeping non-compiling business logic in the tree.
- **Effort:** S

### BE-07 — Image size fields store full-resolution copies (no downscale) — MEDIUM
- **Root cause:** `_compute_property_images` and `_compute_images` assign the raw
  `image_1920` value to `image_1024`/`image_512`/`image_256` with no resizing. Odoo's
  own `image.mixin` exists precisely to generate true thumbnails; here every "resized"
  stored field holds a full-res duplicate, so a property with a 2 MB hero image consumes
  ~4× that and ships full-res bytes to kanban cards, portal lists and the website.
- **Reference:** `models/core/property_details.py:99-104`;
  `models/core/property_project.py:41-45`.
- **Fix:** inherit `image.mixin`, or use `odoo.tools.image_process(...)` to actually
  downscale each size.
- **Effort:** M

### BE-08 — `get_property_stats` swallows all exceptions, returning silent zeros — MEDIUM
- **Root cause:** the dashboard aggregator wraps most reads in bare
  `except Exception: <value> = 0/{}`. A genuine error (bad domain, missing field,
  permission issue) is indistinguishable from "no data", so the dashboard silently
  shows zeros and the failure never surfaces in logs.
- **Reference:** `models/core/property_details.py:196-259` (multiple blocks).
- **Fix:** remove the broad catches (the queries are over models this module owns and
  should not fail), or narrow to the specific expected exception and log at warning.
- **Effort:** S

### BE-09 — `file_validation_mixin` fails open and whitelists SVG — MEDIUM (security)
- **Root cause:** when `python-magic` is absent and the magic-byte fallback cannot
  classify the data, `_validate_file_mime_type` logs and **returns (accepts)** — a
  fail-open policy on a security control. Separately, `image/svg+xml` is in
  `ALLOWED_IMAGE_TYPES`; SVGs can embed JavaScript, so an uploaded SVG rendered inline
  to portal/website visitors is a stored-XSS vector.
- **Reference:** `models/core/file_validation_mixin.py:165-171` (fail-open),
  `:34-42` (SVG whitelisted); document-validation catch also fails open `:213-218`.
- **Fix:** fail closed on undetectable type for untrusted (portal/website) uploads;
  drop `image/svg+xml` from the whitelist or sanitize/force-download SVGs. Ensure
  `python-magic` is a declared dependency rather than optional.
- **Effort:** M

### BE-10 — Unindexed foreign keys searched inside per-record compute loops — MEDIUM
- **Root cause:** several `Many2one` fields that are repeatedly filtered are not
  indexed (Odoo does not auto-index m2o). `rent.bill.contract_id`,
  `tenancy.details.property_id`, and the `property.details` relations used by the
  smart-button counts drive `search_count`/`search` once **per record** in non-stored
  computes, so a project or partner list view issues N×(several) count queries against
  unindexed columns.
- **Reference:** compute loops `models/core/property_project.py:47-76`,
  `models/core/property_details.py:128-146`, `models/core/rent_contract.py:118-121`,
  `models/core/res_partner.py:34-38`; only 4 `index=True` in `models/core` total.
- **Fix:** add `index=True` to hot FKs (`rent.bill.contract_id`,
  `tenancy.details.property_id`, `property.details.project_id` if not already), and
  replace per-record `search_count` loops with a single `read_group`/`_read_group`
  keyed by the parent id.
- **Effort:** M

### BE-11 — Deprecated `read_group` API — LOW
- **Root cause:** public `read_group` is deprecated from Odoo 17 in favor of
  `_read_group` / `formatted_read_group` and is scheduled for removal. Still functional
  in 19 but will warn/break on upgrade.
- **Reference:** `models/core/property_details.py:180,185,197,214,227`;
  `controllers/portal.py:538`; `models/portal/property_details_portal.py:20`.
- **Fix:** migrate to `_read_group(domain, groupby, aggregates)` (returns tuples) at the
  next touch.
- **Effort:** M

### BE-12 — Non-stored count computes without `@api.depends`, recomputed every read — LOW
- **Root cause:** the various `_compute_*_count` methods lack dependencies and run a
  `search_count` on every read. For smart buttons this is the accepted Odoo pattern,
  but where these fields appear in list/kanban views (e.g. `res_partner.properties_count`,
  the `property.details` counts) they add a query per row per render.
- **Reference:** `models/core/property_details.py:128-146`,
  `models/core/rent_invoice.py:55-61`, `models/core/rent_bill.py:49-55`,
  `models/core/res_partner.py:34-38`.
- **Fix:** keep them off list views, or make cheap ones stored/`related`
  (`res_partner.properties_count` can be `len(properties_ids)` off the existing o2m).
- **Effort:** S

### BE-13 — `action_request_renewal` missing `ensure_one()` — LOW
- **Root cause:** it writes `self.renewal_requested = True` and `self.message_post(...)`
  without `ensure_one()`; called on a multi-record set it raises on the singleton
  assignment. Every sibling state action in the file uses `ensure_one()` or iterates.
- **Reference:** `models/core/rent_contract.py:146-148`.
- **Fix:** add `self.ensure_one()` or iterate `for rec in self`.
- **Effort:** S

### BE-14 — Committed backup / empty data artifacts — LOW
- **Root cause:** `models/core/property_details.py.bak` is a stale duplicate of the model
  committed to the tree (and still references the removed `property.vendor` dashboard
  path). `data/cleanup_orphaned_fields.xml` is an intentionally-empty loaded data file,
  and `data/update_ir_cron.xml` is an empty comment-only file (not in the manifest).
- **Reference:** `models/core/property_details.py.bak`;
  `data/cleanup_orphaned_fields.xml`; `data/update_ir_cron.xml`.
- **Fix:** delete the `.bak`; drop the empty data files (or the manifest entry for the
  cleanup file) to avoid confusion.
- **Effort:** S

### BE-15 — External CDN assets loaded into the backend bundle — LOW
- **Root cause:** `web.assets_backend` pulls `echarts` from jsdelivr and `leaflet`
  JS/CSS from unpkg over the network. This breaks offline/air-gapped installs, adds a
  third-party runtime dependency and privacy/CSP exposure, and is fragile if the CDN
  changes. (Config/manifest concern; frontend workstream may also flag.)
- **Reference:** `__manifest__.py` `assets.web.assets_backend` (first three entries).
- **Fix:** vendor these libraries into `static/src/lib/` and reference them locally.
- **Effort:** M

---

## 3. Positive Findings Worth Preserving

- **Portal record rules are correctly scoped.** `security/portal_security.xml` limits
  portal users to their own leases (tenant *and* landlord variants OR'd), purchases,
  bookings, maintenance, invoices, and only `portal_visible` documents — no broad
  cross-tenant read despite the permissive read ACLs. This is the right pattern; keep it.
- **Feed-token security hygiene.** `portal.connector.xml_feed_token` uses
  `secrets.token_urlsafe(32)`, is `groups`-restricted to portal admin, `tracking=False`
  with an explicit "never track tokens in chatter" note, `copy=False`, and has a
  minimum-length constraint. Well done.
- **Cron cleanup is documented and correct.** `data/ir_cron.xml` explains each removed
  dead cron and retains a single real, idempotent `cron_expire_contracts` that reuses
  the audited `action_expire` transition.
- **`payment.schedule` constraints are solid** — total must equal 100% (with rounding
  tolerance), per-line percentage bounds, non-negative `days_after`, ≥1 installments.
- **Defensive migration.** `migrations/19.0.2.3/post-migrate.py` repairs legacy
  selection-value corruption (`for_sale`/`for_tenancy`, stray `state` values) that would
  otherwise crash search-panel groupby, with clear logging.
- **Multi-company isolation.** Global `ir.rule`s apply the `company_id in company_ids`
  filter across all major models.
- **No pre-17 API debt in Python.** No `@api.one/@api.multi`, `osv`, `_columns`,
  `fields.function`, or `cr, uid` patterns remain; state machines use guarded
  transitions with `UserError`.
- **Modern constraint style.** `portal.connector` uses the new
  `models.Constraint(...)` declaration rather than the legacy `_sql_constraints` tuple.
