# Portal / Reports / Benchmarking Audit
Module: `sgc_offplan_rental_property_management` (Odoo 19.0, v19.0.2.7)
Scope: portal controllers & templates, portal access rules (ir.rule / ACL), QWeb/PDF reports, backend↔portal parity, market benchmarking.
Method: static read-only review of source at baseline commit `20472a9`. No DB writes, no source edits.

---

## 1. Executive Summary

The portal is broad and ambitious — separate tenant, landlord, and customer journeys with dashboards, leases, invoices, maintenance, documents, favorites, inquiries, bookings, and an MVP e-sign seam. The **ir.rule / ACL layer is correctly and thoughtfully scoped** for portal users. However, that layer is almost entirely **bypassed** because every controller queries with `.sudo()`, so record-level protection depends solely on manual ownership checks in Python — and **several read/detail endpoints omit those checks**, producing IDOR data leaks across tenants/landlords/customers. In addition, **two of the most visible portal pages (`/my/properties`, `/my/contracts`) crash with an HTTP 500** due to undefined variables, so the portal is not currently demo-ready.

On reporting: all 8 PDF templates render without a shared branded layout (no logo/header/footer/page numbers), and the **Statement of Account report is bound to `account.move` but references fields that do not exist on that model**, so it will error or render empty when printed.

Counts: **Critical 5, High 4, Medium 5, Low 3.**

Top priorities before any client demo: fix the two 500-crashing pages, add ownership checks to the contract/invoice/property detail endpoints, and fix or hide the Statement of Account report.

---

## 2. Issues Found

### CRITICAL

#### C-1. `/my/properties` crashes (HTTP 500) — undefined variables
- **Severity:** Critical
- **Root Cause:** `portal_my_properties` passes `tenancy_details` and `vendor_bookings` into the render context, but neither variable is defined anywhere in the function. They are only defined inside a *different* function (`portal_my_property_detail`). At runtime this raises `NameError` → 500.
- **Location:** `controllers/portal.py:50-51` (defined only at `:74`/`:78`, out of scope)
- **Fix:** Remove the two keys from the render dict, or define them in this function (e.g. `tenancy_details = request.env['tenancy.details'].sudo().search([('tenant_id','=',partner.id)])` and the analogous `property.vendor` search).
- **Effort:** S

#### C-2. `/my/contracts` crashes (HTTP 500) — undefined variables
- **Severity:** Critical
- **Root Cause:** Same defect as C-1: `tenancy_details` and `vendor_bookings` referenced in the render context but never assigned in this function.
- **Location:** `controllers/portal.py:123-124`
- **Fix:** Remove the keys or define the searches locally.
- **Effort:** S

#### C-3. IDOR — any portal user can view any contract
- **Severity:** Critical
- **Root Cause:** `portal_my_contract_detail` browses `sale.contract`/`rent.contract` with `.sudo()` and only checks `contract.exists()`. There is **no check that `buyer_id`/`tenant_id` belongs to the current partner**. By enumerating the integer `contract_id`, any authenticated portal user reads any contract — prices, parties, financial terms.
- **Location:** `controllers/portal.py:129-148`
- **Fix:** After `browse`, verify ownership, e.g. for `rent`: `contract.tenant_id.id == partner.id or contract.landlord_id.id == partner.id`; for `sale`: `contract.buyer_id.id == partner.id`. Otherwise return `website.page_404`. (The pattern is already used correctly in `portal_my_lease_detail` at `:438`.)
- **Effort:** S

#### C-4. IDOR — any portal user can view (and initiate payment on) any invoice
- **Severity:** Critical
- **Root Cause:** `portal_my_invoice_detail` (`:169`) and `portal_my_invoice_pay` (`:182`) browse `account.move` with `.sudo()` and check only `.exists()`. No `partner_id` ownership check. `portal_my_invoice_pay` additionally calls `invoice._portal_ensure_token()` and redirects to `/payment/pay` for an **arbitrary** invoice — exposing another customer's invoice amount and a usable payment access token.
- **Location:** `controllers/portal.py:169-190`
- **Fix:** Guard both endpoints with `if invoice.partner_id.id != request.env.user.partner_id.id: return request.render('website.page_404')` before rendering / token generation.
- **Effort:** S

#### C-5. IDOR — property detail record leaks to any portal user
- **Severity:** Critical
- **Root Cause:** `portal_my_property_detail` browses `property.details` with `.sudo()` and checks only `property.exists()`. The child recordsets (contracts, invoices) are correctly scoped by partner, but the **`property` record itself is rendered regardless of ownership**, leaking property name, address, title-deed/Makani/DEWA numbers, and pricing for any `property_id`.
- **Location:** `controllers/portal.py:56-105`
- **Fix:** Call the existing helper `self._check_user_can_access_property(property_id, partner)` (defined at `:233`) and 404 on failure. Note the helper covers owner/landlord/active-tenant; extend it (or add a parallel check) to also allow buyers via `sale.contract` if a purchaser should see the property page.
- **Effort:** S

### HIGH

#### H-1. Statement of Account report references non-existent fields on `account.move`
- **Severity:** High
- **Root Cause:** `action_report_statement_of_account` is bound to `account.move`, but the template reads `o.property_id`, `o.contract_id`, `o.total_outstanding`, and treats `o.line_ids` as statement rows with `line.description`/`line.state`/`line.amount`. The module's `account.move` extension only adds `tenancy_property_id` and `sold_property_id` (`models/core/account_move.py:15,30`). `o.total_outstanding` will raise `AttributeError` at render; `line.description`/`line.state`/`line.amount` are not standard `account.move.line` fields, so transaction rows render blank/incorrect.
- **Location:** `report/statement_of_account_template.xml:43,51,73,74,85`
- **Fix:** Either point the report at the real fields (`amount_residual`, `tenancy_property_id`/`sold_property_id`, `line.name`, `line.balance`) or build a dedicated statement model/wizard that supplies these values. Until fixed, unbind the report so staff cannot print a crashing document.
- **Effort:** M

#### H-2. No branded layout on any PDF report (no logo / header / footer / page numbers)
- **Severity:** High
- **Root Cause:** All 8 templates call `web.html_container` directly and wrap content in a raw `<div class="page">`. None call `web.external_layout` / `web.internal_layout`, so there is no company logo, address band, page-number footer, or consistent margins. Branding is a hard-coded `<h4>SGC TECH AI</h4>` text string. These documents (Tenancy Contract, Sales Purchase Agreement, Statement, Booking Agreement) are client/landlord/tenant-facing and read as unbranded drafts. (A prior `report/UAE_REPORT_AUDIT.md` reaches the same conclusion.)
- **Location:** `report/*.xml` (all 8 templates, e.g. `rent_contract_report_template.xml:4-16`)
- **Fix:** Wrap each report body in `<t t-call="web.external_layout">` and move the company block into the layout header; add the real `res.company` logo. Standardize a paper format (see M-4).
- **Effort:** M

#### H-3. CSRF protection disabled on landlord maintenance approve/reject
- **Severity:** High
- **Root Cause:** Both state-changing POST endpoints set `csrf=False`. A malicious page can forge a landlord's approval/rejection of a maintenance request (which can drive cost/works authorization). Ownership is checked, but CSRF is a separate vector and there is no reason to disable it here — the corresponding forms can include `request.csrf_token()` (as the maintenance-create form already does at `portal_my_maintenance.xml:59`).
- **Location:** `controllers/portal.py:816,828`
- **Fix:** Remove `csrf=False` and add the CSRF hidden input to the approve/reject forms in the landlord maintenance template.
- **Effort:** S

#### H-4. Landlord statement XLS export does not deliver a file
- **Severity:** High (functional)
- **Root Cause:** `portal_landlord_statement_xls` creates the XLS wizard and calls `action_generate_report()`, but (per the code's own docstring) that action returns only `ir.actions.act_window_close`, so **no file is streamed to the portal user**; the controller just redirects back to the HTML statement. The "Export XLS" affordance silently does nothing. It also blindly tries two wizard model names in a loop, swallowing exceptions.
- **Location:** `controllers/portal.py:757-788`
- **Fix:** Have the wizard return report bytes (or reuse the report's `_render_xlsx`) and stream them via a proper `request.make_response` with content-disposition headers. Drop the two-model guessing loop once the correct wizard is confirmed.
- **Effort:** M

### MEDIUM

#### M-1. Blanket `.sudo()` in portal controllers nullifies the ir.rule layer
- **Severity:** Medium (systemic / defense-in-depth)
- **Root Cause:** `security/portal_security.xml` defines correct record rules (tenant/landlord/buyer/customer scoping for `rent.contract`, `tenancy.details`, `sale.contract`, `property.vendor`, `maintenance.request`, `account.move`, `property.documents`). But **every** portal query uses `.sudo()`, so these rules never apply on the portal paths. Security then rests entirely on hand-written checks — which is exactly why C-3/C-4/C-5 leak. This is a fragile pattern: any future endpoint that forgets a check leaks data.
- **Location:** `controllers/portal.py` (pervasive `.sudo()`); rules at `security/portal_security.xml:3-56`
- **Fix:** Prefer non-sudo queries so ir.rule enforces scoping automatically, reserving `.sudo()` only for genuinely cross-partner reads (e.g. landlord viewing tenant sub-data) with an explicit ownership gate. At minimum, add a shared ownership-check helper and route every detail endpoint through it.
- **Effort:** L

#### M-2. `_get_user_property_ids` recomputed per request with multiple searches
- **Severity:** Medium (performance / correctness)
- **Root Cause:** Maintenance list/new/submit each call `_get_user_property_ids`, which runs 3 searches; the property/contract listing pages run several more `.sudo().search` calls and combine recordsets with `+` (`:44`), which can duplicate records. On accounts with many properties this is N+1-ish and the `+` dedup is left to chance.
- **Location:** `controllers/portal.py:44,209-231,242,261`
- **Fix:** De-duplicate with `|` domains or recordset `|` union; cache the id list per request.
- **Effort:** S

#### M-3. Lease renewal silently unsupported for `tenancy.details`
- **Severity:** Medium
- **Root Cause:** `portal_my_lease_renew` calls `action_request_renewal()` only for `rent_contract`; for `tenancy.details` it just logs a warning and redirects, so a tenant on a legacy `tenancy.details` lease clicks "Renew" and nothing happens with no user feedback.
- **Location:** `controllers/portal.py:459-465`
- **Fix:** Either implement renewal on `tenancy.details` or hide/disable the renew button for that model and surface a message.
- **Effort:** M

#### M-4. Euro paper format on AED/UAE documents
- **Severity:** Medium (cosmetic/regional)
- **Root Cause:** All report actions use `base.paperformat_euro`. For UAE-market documents A4 is expected; euro format margins/size can misalign the tenancy/Ejari-style layouts.
- **Location:** `data/report_actions.xml:17,30,43,56,69,82,95,108`
- **Fix:** Define/assign an A4 paper format.
- **Effort:** S

#### M-5. Inquiry/lead list scoping relies on `partner_id` only
- **Severity:** Medium
- **Root Cause:** `portal_customer_inquiries` lists `crm.lead` filtered by `partner_id == partner` with `.sudo()`. If staff create leads for that partner via other channels, they surface in the portal; conversely leads not linked to the partner are hidden. Acceptable, but worth confirming this matches intent since `crm.lead` has no portal ir.rule here.
- **Location:** `controllers/portal.py:996-1009`
- **Fix:** Confirm intended visibility; consider an explicit "created via portal" flag for the inquiry list.
- **Effort:** S

### LOW

#### L-1. Hard-coded AED currency in reports
- Reports format money as `'AED %s'` string literals rather than the record/company currency, so a multi-currency deployment mislabels amounts. `report/*.xml` (e.g. `rent_contract_report_template.xml:93,105,117`). Fix: use `t-esc` with `widget="monetary"` and the record currency. Effort: S

#### L-2. Statement transaction rows use wrong line fields
- Even setting aside H-1, `line.description`/`line.state` are not `account.move.line` fields; rows would render empty. `report/statement_of_account_template.xml:72,74`. Effort: S

#### L-3. Broad `except Exception` swallows errors on write paths
- Maintenance submit (`:292`) and inquiry submit (`:992`) catch bare `Exception` and redirect back with no user-visible error, making failures invisible in the demo. Prefer surfacing a flash/error param as the document-upload path does (`:497`). Effort: S

---

## 3. Market Benchmarking Gap List (vs. Buildium / AppFolio / Yardi Breeze)

Each gap below is grounded in code actually observed (or absent) in this module.

1. **No photo/attachment upload on tenant maintenance requests.** The maintenance form exposes only `subject`, `property_id`, `description` — no file input (`views/portal/portal_my_maintenance.xml:41-89`; controller `portal_my_maintenance_submit:271-294` reads no file). Buildium/AppFolio let tenants attach photos/video to a request, which is table stakes for triage.

2. **E-signature is a non-cryptographic stub.** `/my/contracts/<id>/sign` just sets `signed_via_portal=True` and posts a chatter note — the code itself labels it an "MVP e-sign seam … Phase 4 will replace this with a real … provider" (`controllers/portal.py:1079-1117`; template `portal_customer_dashboard.xml:395-396`). There is no signed-document artifact, no audit trail, no identity verification. Buildium/AppFolio/Yardi provide legally-binding lease e-sign with audit logs.

3. **Online payment is present but not competitive (and currently IDOR-broken).** A `/my/invoice/<id>/pay` → `/payment/pay` redirect exists (`:182-190`), so single-invoice payment is possible via Odoo payment providers. But there is **no tenant autopay/recurring rent setup, no saved payment methods, and no ACH/bank-debit onboarding** in the portal. Buildium/AppFolio center on tenant-configured recurring autopay and ACH.

4. **No rental application / tenant screening workflow.** Inquiries create a `crm.lead` (`:955-994`); there is no online application form, background/credit-check integration, or applicant-to-lease conversion. AppFolio/Buildium bundle screening as a core funnel step.

5. **No tenant↔landlord↔manager messaging center.** Communication relies on backend chatter notes (e.g. maintenance/inquiry `message_post`). There is no portal-native conversation thread or notification center. All three benchmark platforms offer a resident/owner communication hub.

6. **Owner (landlord) statement delivery is manual and partly broken.** The landlord statement is a hand-rendered HTML page (`portal_landlord_statement:705-755`) and its XLS export delivers no file (H-4). There is no scheduled owner statement email or owner disbursement/eft workflow. Yardi Breeze/AppFolio automate owner statements and ACH disbursements.

7. **No lease-renewal automation for legacy leases.** Renewal works only for `rent.contract`; `tenancy.details` renewals are a no-op (M-3). Competitors offer automated renewal offers with rent-increase workflows.

8. **Reporting is not client-grade.** Unbranded PDFs (H-2) and a broken Statement of Account (H-1) fall short of the polished, logo'd owner/tenant statements standard in Buildium/AppFolio.

*Positive vs. benchmarks:* this module includes **multi-portal listing syndication + XML feed export** (`controllers/xml_feed_controller.py`, `models/portal/*`) — a marketing/syndication capability that Buildium/AppFolio charge extra for or gate behind add-ons.

---

## 4. Positive Findings Worth Preserving

- **Well-designed portal ir.rule set.** `security/portal_security.xml` scopes every sensitive model to the acting portal user by `*.user_ids in [user.id]`, including the dual tenant/landlord rules on leases and maintenance, and `portal_visible=True` on documents. This is the right model — it just needs the controllers to stop bypassing it (M-1).
- **Correct ownership pattern already exists** in `portal_my_lease_detail` (`:438`), `portal_customer_contract_sign` (`:1093`), booking cancel (`:1064`), and inquiry detail (`:1016`) — the C-3/C-4/C-5 endpoints just need the same one-line guard.
- **Good write-path hygiene in places:** maintenance submit validates property access before create (`_check_user_can_access_property`, `:277`); document upload validates the property is one of the tenant's active properties and stores `uploaded_by_partner_id` + `approval_state='pending'` (`:490-515`); favorites/inquiry restricted to `is_published_website` properties.
- **Open-redirect guard** `_safe_redirect_referrer` correctly confines referrer redirects to the same host (`:868-874`).
- **Thoughtful dual-model bridging** (`rent.contract` + legacy `tenancy.details`) so tenants on either model see a unified lease/dashboard experience.
- **Least-privilege portal ACLs:** `security/ir.model.access.csv` grants portal groups read-only on financial models and read+create (no write/unlink) only where needed (maintenance, documents) — matches the intended flows.
- **Tenancy/Ejari contract report** is detailed and UAE-appropriate (Makani, DEWA, Ejari registration, cheque count) — good domain fit; it only needs the branded layout wrapper.
