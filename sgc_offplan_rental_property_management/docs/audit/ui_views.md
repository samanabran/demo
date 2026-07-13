# UI / Views Audit — sgc_offplan_rental_property_management (Odoo 19)

Workstream: menus, actions, form/list/kanban/search/calendar views, wizards, email
templates, dashboards, action buttons, and static JS/OWL assets.
Method: read-only static review of module source + cross-check against the live
`demo_presentation_19` database and `demo_presentation` container runtime logs.
Baseline commit: `20472a9` (pre-audit snapshot).

---

## 1. Executive Summary

The module's **XML view layer is in good shape for Odoo 19**: it consistently uses
modern syntax (`<list>` not `<tree>`, boolean `invisible`/`required` expressions
instead of the removed `attrs=`/`states=`, `widget="badge"`, `statusbar`,
`searchpanel`, `decoration-*`, `<chatter/>`, and `<t t-name="card">` kanban
templates). No deprecated `<tree>` tags, no `attrs=`/`states=`, no `t-raw`/`t-esc`
inside backend kanban templates, and no duplicate `record id`s were found in the
module's own XML.

The **one live, user-visible defect is the `kanban_getcolor` crash**, and its root
cause is **not** in module source at all — it is an **orphaned, DB-only
`property.details` kanban view (DB id 2999)** that survives from a pre-Odoo-17
import/Studio edit. The module already ships a clean replacement kanban and tries
to out-rank the orphan with `priority=1`, but the orphan record still exists and
still throws. This is a **second live instance of the exact "orphaned legacy view
shadowing a modern one" pattern** previously fixed on `property.project` /
`property.sub.project` — here it is only *shadowed*, not *removed*.

Remaining findings are lower-severity: remote CDN assets loaded into the backend
bundle, a portal ACL warning against `property.details`, deprecated/`t-raw`
rendering in two portal/website templates, and log-spam from unset config
parameters.

Issue counts by severity: **Critical 1, High 1, Medium 3, Low 2**.

---

## 2. Issues Found

### 2.1 [CRITICAL] Orphaned DB-only `property.details` kanban still calls removed `kanban_getcolor()` helper

- **Title:** Pre-v17 kanban color helper `kanban_getcolor` throws `TypeError` on every Properties kanban render
- **Severity:** Critical (live, reproducible; 109 identical OwlErrors captured in `property_errors.log`)
- **Root Cause:** A `property.details` kanban view exists **only in the database**
  (DB id **2999**, `priority=15`, `mode=primary`, **no `ir_model_data` / XML id**,
  `create_uid=2`, last written `2026-07-07`). Its arch contains the pre-Odoo-17
  QWeb template:
  ```xml
  <div class="oe_kanban_global_click_fill"
       t-attf-class="oe_kanban_color_#{kanban_getcolor(record.state.raw_value)} oe_kanban_card oe_kanban_global_click">
  ```
  `kanban_getcolor()` was a global QWeb helper injected into the old (pre-17)
  kanban rendering context. Odoo 19 renders kanban cards through the OWL
  `KanbanRecord` component, whose template context does **not** expose that
  function, so evaluation fails with `TypeError: ctx.kanban_getcolor is not a
  function` inside `KanbanRecord.template`, which surfaces as the `OwlError`
  lifecycle error seen in the log.
- **Exact reference:**
  - Offending record: **live DB `ir_ui_view` id 2999** (model `property.details`,
    type `kanban`, no XML id) — verified via
    `SELECT ... FROM ir_ui_view WHERE arch_db::text LIKE '%kanban_getcolor%'`
    which returns **exactly one row: id 2999**.
  - Module-side clean replacement + shadowing workaround:
    `views/core/property_details_view.xml:59-120` (record
    `property_details_kanban_view`, DB id 3007, `priority=1`), with the
    explanatory comment at `views/core/property_details_view.xml:63-66`.
  - The module's own XML **does not** call `kanban_getcolor` anywhere — the only
    textual hit in `views/**` is that explanatory comment.
- **Why the current mitigation is insufficient:** `priority=1` only makes the clean
  view *win by default* when Odoo picks "the" kanban for the action. The orphan
  (id 2999) is still a valid, active, primary kanban for `property.details`. It
  still renders (and throws) whenever it is resolved directly — e.g. a saved
  `view_id`/action referencing it, a favourite, an embedded/related kanban, or any
  code path that selects by id or higher priority in a different context — which is
  consistent with the log showing the error still firing live. Neither the
  `19.0.2.3/post-migrate.py` migration (which only repairs `sale_lease`/`state`
  *data* values) nor `models/core/ir_ui_view.py` (which only adds a `tk_map` view
  type) removes it.
- **Recommended Fix (modern Odoo 19 pattern):**
  1. **Delete the orphan permanently.** Add a `post-migrate` step (new version dir,
     e.g. `migrations/19.0.2.8/post-migrate.py`) that removes DB-only
     `property.details` kanban views lacking an XML id:
     ```python
     def migrate(cr, version):
         cr.execute("""
             DELETE FROM ir_ui_view v
             WHERE v.model = 'property.details' AND v.type = 'kanban'
               AND v.arch_db::text LIKE '%kanban_getcolor%'
               AND NOT EXISTS (
                   SELECT 1 FROM ir_model_data d
                   WHERE d.model = 'ir.ui.view' AND d.res_id = v.id)
         """)
     ```
     (Deleting is safe because the module now owns a canonical XML-defined kanban;
     archiving via `active=False` is the more conservative alternative.)
  2. **Correct modern replacement for the color itself** (already done in the clean
     view, keep as the reference pattern): Odoo 19 kanban color is **declarative**,
     not a JS context helper. Use either
     - `decoration-*` attributes on the `<kanban>` element bound to a field
       expression (as the clean view does:
       `decoration-success="state == 'available'"` etc.), or
     - a numeric color field surfaced through the color picker via
       `<field name="color" widget="..."/>` / the kanban `color` attribute
       (`<kanban ... default_group_by="..." >` with a `color` field), i.e. the
       `color`-field mechanism — **never** a `kanban_getcolor()`/`oe_kanban_color_#{...}`
       QWeb call.
  3. Once the orphan is removed, the `priority=1` on
     `property_details_kanban_view` can be dropped back to default, and the
     explanatory comment updated.
- **Effort:** S (one migration script + verification that the console error count drops to 0).

---

### 2.2 [HIGH] Remote CDN assets loaded into the backend bundle

- **Title:** `web.assets_backend` pulls echarts + leaflet from third-party CDNs
- **Severity:** High
- **Root Cause:** `__manifest__.py` registers three remote URLs in the backend
  asset bundle:
  ```python
  "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
  ```
  The executive dashboard (`static/src/components/rental_property_dashboard.js`)
  depends on echarts + leaflet at runtime.
- **Exact reference:** `__manifest__.py:132-134`.
- **Why it matters:** Odoo cannot bundle/minify/version remote assets, so the
  dashboard silently breaks on air-gapped / offline / strict-CSP deployments and
  whenever the CDN is unreachable; it also introduces a third-party runtime
  dependency and a supply-chain surface for an admin-facing page. SGC's own prod
  guidance (in-container rendering, CSP) makes remote backend assets a real risk.
- **Recommended Fix:** Vendor `echarts.min.js`, `leaflet.js`, `leaflet.css` (and
  Leaflet's marker/image assets) into `static/src/lib/` and reference them by local
  module path so they are bundled normally.
- **Effort:** M.

---

### 2.3 [MEDIUM] Portal/website flow triggers `property.details` access-denied warning

- **Title:** Runtime ACL warning: "You are not allowed to access 'Property Details' (property.details) records"
- **Severity:** Medium
- **Root Cause:** A live request path (portal or website, given the surrounding
  `odoo.http` context) resolves to `property.details` for a user without the
  `property_rental_manager` / `property_rental_officer` group or a matching record
  rule, producing an `AccessError`-level warning. This indicates a portal-facing
  view/controller reads the backend model without a portal-scoped rule (or a menu/
  action leaks into a context it should not).
- **Exact reference:** `docker logs demo_presentation` —
  `2026-07-09 17:44:39 WARNING demo_presentation_19 odoo.http: You are not allowed
  to access 'Property Details' (property.details) records.` Cross-check portal
  readers under `views/portal/portal_my_properties.xml` /
  `controllers/` and the record rules in `security/portal_security.xml`.
- **Recommended Fix:** Add/adjust an `ir.rule` giving portal users read access to
  the `property.details` rows they're entitled to (or route the portal view through
  a `sudo()`-backed controller returning only published/owned records). Confirm the
  warning disappears from the log after the fix.
- **Effort:** M.

---

### 2.4 [MEDIUM] Deprecated `t-raw` used for message body and injected JS in portal/website templates

- **Title:** `t-raw` rendering (deprecated in v17+, unescaped) in two frontend templates
- **Severity:** Medium (deprecation + XSS/JS-injection surface)
- **Root Cause:** Odoo 17+ deprecates `t-raw` in favour of `t-out` (which escapes
  unless the value is `Markup`). Two occurrences render **unescaped** content:
  - a chatter message body, and
  - a raw JavaScript blob variable.
- **Exact reference:**
  - `views/portal/portal_customer_dashboard.xml:242` — `<div t-raw="msg.body"/>`
  - `views/website/offplan_property_detail.xml:273` — `<t t-raw="gated_inquiry_js"/>`
- **Why it matters:** On the public/portal surface, `t-raw` on any value that can be
  influenced by user-supplied data is a stored/reflected XSS vector; the
  `gated_inquiry_js` injection is effectively arbitrary inline script and should be
  tightly controlled. Even where the source is trusted, these will warn/behave
  differently as `t-raw` is phased out.
- **Recommended Fix:** Switch to `t-out`. For genuinely trusted HTML
  (`msg.body` is typically already sanitized `Markup`), `t-out` preserves it; for
  the JS blob, prefer a bundled asset or an explicitly `Markup`-wrapped,
  server-controlled value rather than a template-level raw injection.
- **Effort:** S.

---

### 2.5 [MEDIUM] Settings load spams warnings for unset `ir.config.parameter` defaults

- **Title:** `res.config.settings` item-mapping params return `None` and log a warning on every settings open
- **Severity:** Medium (noise + indicates unconfigured accounting product mappings the wizards depend on)
- **Root Cause:** Several `res.config.settings` fields
  (`installment_item_id`, `deposit_item_id`, `broker_item_id`,
  `maintenance_item_id`) back onto `ir.config.parameter` values that are unset,
  so conversion of `None` warns repeatedly. These product mappings feed the booking/
  contract wizards, so unset values are also a latent functional gap.
- **Exact reference:** `views/core/res_config_setting_view.xml` (the settings view
  exposing these fields) + repeated `docker logs demo_presentation` lines
  `odoo.addons.base.models.res_config: Error when converting value None of field
  res.config.settings.<x>_item_id ...`.
- **Recommended Fix:** Provide sensible defaults (seed the products/params in
  `data/`), or make the getter tolerate an unset param without warning. Primarily a
  models/data fix, surfaced through the settings view.
- **Effort:** S.

---

### 2.6 [LOW] Split menu ownership + documented "V17 items skipped" gaps

- **Title:** Root menu declared outside `menus.xml`; several v17 menu targets intentionally absent
- **Severity:** Low
- **Root Cause / Notes:** `main_menu_rental_management` and `menu_property_details`
  are declared in `property_details_view.xml` while the rest of the tree lives in
  `menus.xml` (documented in the header note). Separately, `menus.xml` documents a
  set of v17 menu items skipped because their actions don't exist in v19
  (Renting/Selling "Contracts" legacy actions, Developers, report wizards, Config →
  Types sub-menu). These are **not dead/broken actions** (they were deliberately not
  ported), but they represent an incomplete feature surface a reviewer should be
  aware of.
- **Exact reference:** `views/core/menus.xml:6-18` (header note),
  `views/core/property_details_view.xml:251-253` (root + Properties menu),
  `views/core/menus.xml:12-18` (skipped-items list).
- **Recommended Fix:** Either consolidate the two root menu declarations into
  `menus.xml` for single-source ownership, or keep the current split but leave the
  explanatory note (already present). Decide per-item whether the skipped v17
  targets should be built or formally dropped.
- **Effort:** L (only if the skipped features are to be completed; S to consolidate menu ownership).

---

### 2.7 [LOW] `property.details` action offers no `search_view` benefit on secondary kanbans / no calendar view present

- **Title:** No calendar views defined; secondary models rely on default search
- **Severity:** Low (informational)
- **Root Cause / Notes:** No `<calendar>` views exist anywhere in the module (in
  scope per brief — none found, so none to audit). The `property.project` /
  `property.sub.project` actions (`view_mode="kanban,list,form"`) have no dedicated
  search view, so grouping/filtering there falls back to defaults. Not a defect,
  but a polish opportunity given the rich search view built for `property.details`.
- **Exact reference:** `views/core/property_project_views.xml:141-150` and
  `:250-259` (actions without `search_view_id`).
- **Recommended Fix:** Optionally add lightweight search views for projects/
  sub-projects (group by region / state). Purely enhancement.
- **Effort:** S.

---

## 3. Positive Findings Worth Preserving

- **Modern Odoo 19 view syntax throughout the module XML.** `<list>` (not `<tree>`),
  boolean `invisible`/`required` expressions (no removed `attrs=`/`states=`),
  `widget="badge"`, `<field name="state" widget="statusbar">`, `<searchpanel>`,
  `decoration-*`, `<chatter/>`, and `<t t-name="card">` kanban templates. Keep this
  as the module's baseline convention.
- **The clean `property_details_kanban_view`** (`views/core/property_details_view.xml:59-120`)
  is a correct v19 kanban: image card, `decoration-*` state coloring, `sample="1"`,
  `records_draggable="0"`, and an explicit explanatory comment about the priority
  workaround. Once the orphan (2.1) is deleted, this is the reference kanban to keep.
- **`property.project` / `property.sub.project` kanbans** are clean, consistent card
  layouts with graceful image fallbacks — the previously-fixed orphan pattern
  remains fixed for these models (verified: no `kanban_getcolor` in their arch and
  no additional DB orphans for those models).
- **Well-documented data migration** (`migrations/19.0.2.3/post-migrate.py`) repairs
  legacy `sale_lease`/`state` selection values with clear logging — good practice to
  emulate for the orphan-view cleanup in 2.1.
- **Consistent group-based menu security** — every backend menu item carries the
  `property_rental_manager` / `property_rental_officer` groups.
- **Booking wizard form** (`wizard/views/booking_wizard_views.xml`) uses correct
  conditional `invisible`/`required` pairing (e.g. broker fields keyed off
  `is_any_broker`/`commission_type`) — modifier logic is coherent.
- **No duplicate `record id`s** within the module's view XML and **no `t-raw`/`t-esc`
  in backend kanban templates.**

---

*Known-fixed items re-verified and NOT re-flagged:* the `property.project` /
`property.sub.project` orphaned legacy views remain archived/absent, and the
`rent.bill` form no longer dead-requires `tenancy_id`
(`views/core/rent_bill_view.xml` — no unconditional `required` on `tenancy_id`).
