# OPR Scoping Study

> **Authority:** `AMENDMENT_001_VENDOR_TENANT_BOUNDARY.md` §10.3.
> **Purpose:** scope precisely the surface that the five OPR-dependent gaps consume, and decide whether to wire into the existing module or reimplement in clean siblings.
> **Status:** DRAFT, applied to Wave 2 entry gate.
> **Date:** 2026-09-01.

---

## 1. Five OPR-dependent gaps

Per Wave 0 misalignment catalogue (now superseded by `WAVE_0_AMENDMENT_001_REGISTER.md`):

| Gap | Description | Class |
|---|---|---|
| G7 | Payment reminder infinite (dunning ladder) | VENDOR |
| G9 | Sale conditions register | VENDOR |
| G10 | Listing permit block + de-listing | VENDOR |
| G11 | Lease statutory registration / index / notice | VENDOR |
| G12 | Developer lane (escrow, sales permit, Oqood, handover) | VENDOR |

## 2. OPR structure

`sgc_offplan_rental_property_management/` is **UNRESOLVED** provenance, ~21,814 LOC, the largest module in the estate. The module bundles four previously separate code-dependent sub-modules:

- `models/core/` — 38 Python files: property master, sale contract, rent contract, offplan project, payment schedule, account.move, RERA Form A, tenancy, maintenance, vendors, commission lines, etc.
- `models/portal/` — portal connector and sync log
- `models/website/` — public website views
- `models/compat/` — CRM compatibility shim
- `views/portal/` — portal front-end
- `wizard/`, `report/`, `controllers/`, `static/`, `data/`, etc.

The merge log (`MERGE_NOTES.md`) flags inherited defects: **three QWeb templates referenced by the controllers do not exist** (`rental_listings`, `rental_detail`, `thank_you`). The OPR is **provenance-unresolved *and* functionally defective** — a permanent lender-pack liability per the amendment.

## 3. Surface mapping — what the five gaps actually need

The five gaps do not need the 38 models in `core/`. They need **eight**. This is the narrow surface.

| Gap | OPR models used | OPR views used |
|---|---|---|
| G7 (dunning) | `account_move.py`, `rent_bill.py`, `rent_invoice.py` | `property_invoice_inherit.xml`, `rent_bill_view.xml`, `rent_invoice_view.xml` |
| G9 (sale conditions) | `sale_contract.py`, `property_details.py`, `property_project.py` | `sale_contract_views.xml`, `property_details_view.xml` |
| G10 (listing permit) | `rera_form_a.py`, `property_details.py` | `rera_form_a_view.xml`, `property_publish_wizard_views.xml` |
| G11 (lease registration) | `tenancy_details.py`, `rent_contract.py` | `rent_contract_views.xml`, `tenancy_details_view.xml` |
| G12 (developer lane) | `property_project.py`, `sale_contract.py`, `payment_schedule.py` | `property_project_views.xml`, `sale_contract_views.xml`, `payment_schedule_views.xml` |

**Distinct model files needed: 8** (some shared across gaps). The remaining 30+ model files in `models/core/` are not on the five-gap critical path. Same for `models/portal/`, `models/website/`, `models/compat/` — out of scope for these gaps.

**Distinct view files needed: 11** (counting shared). The portal front-end (`views/portal/`), the public website (`views/website/`), the maintenance extension, the vendor module, the commission lines, the agreement template, the certificate type, the contract duration, the amenities, the connectivity, the document template, the image gallery, the rent contract report template, the brochure template, the sales SPA template, the rent invoice report, the maintenance contract report, the statement of account template, the payment schedule template, the sales offer template, the property publish wizard, the offplan property listing, the offplan property detail, the offplan project listing, the offplan project detail, the res.city view, the res.region view, the res.config settings view, the property tag view, the property specification view, the property document view, the nearby connectivity view, the user type view, the ir_action override, the ir_ui_view override, the file validation mixin, the rent commission line, the property vendor commission line, the property broker dashboard, the property customer dashboard, the property tenant dashboard, the property landlord dashboard, the portal my_home inherit, the portal my_properties, the portal my_contracts, the portal my_invoices, the portal my_maintenance, the portal my_statements, the portal sync log, the portal lead, the property feed source, the property portal line, the xml feed config, the portal menus, the portal actions, the portal connector, the wizard booking, the wizard publish, the wizard integrations — are all **out of scope for the five-gap surface**.

## 4. Defects within the narrow surface

Even within the eight model files, MERGE_NOTES flagged the three QWeb templates that are *not* in the OPR's own controllers but in the renamed `sgc_rental_website` controller. None of the three (`rental_listings`, `rental_detail`, `thank_you`) is on the five-gap critical path. The narrow surface is **functionally less broken** than the wider OPR — but it is still **provenance-unresolved**.

## 5. Recommendation: clean siblings, retire the OPR dependency

The cleanest path, per the amendment §4 Architecture Directive One, is to:

1. **Reimplement the eight model files as part of the new clean sibling modules** (`sgc_collections_ladder`, `sgc_transaction_conditions`, `sgc_listing_compliance`, `sgc_developer_lane`).
2. **Reimplement the eleven view files as part of those siblings.** The view files are small, mostly list/form over the model.
3. **No `depends` on `sgc_offplan_rental_property_management`** in any new module. R3 compliance.
4. **The OPR itself remains on disk** for tenants that need the full portal / website / public-rental-site surface — those are out of scope for the gap-closure programme.

This means:

- **No OPR file is touched.** R3 compliant.
- **No OPR file is required to compile or load.** The clean siblings do not depend on it.
- **The five gaps are closed by clean IP** that is unambiguously original and separately attributable in the lender pack.
- **The OPR's three broken QWeb templates remain broken** — they are a separate concern for the OPR's own maintenance team.
- **The OPR's `__manifest__.py` UNRESOLVED status remains** for the OPR's own audit. The clean siblings do not inherit that uncertainty.

This is the recommended path.

## 6. Cost of the recommended path

| Item | Cost |
|---|---|
| 8 Python model files re-implemented as ~8-12 new model files in clean siblings | ~1,500–2,500 LOC, distributed across 4 sibling modules. |
| 11 view files re-implemented | ~1,000–1,500 LOC across 4 sibling modules. |
| Tests for each clean sibling | ~500–1,000 LOC across 4 sibling modules. |
| Migration notes for any tenant that was on OPR | Each sibling carries a migration note describing how to import OPR records. |
| Total | ~3,000–5,000 LOC across 4 new modules. This is comparable to the existing `sgc_offplan_rental_property_management` build but with clean provenance. |

The cost is bounded and reasonable. The benefit is that **no Wave 2 module depends on a module with inherited defects, broken QWeb templates, and UNRESOLVED provenance**.

## 7. What this means for Wave 2 entry

- **Wave 2 item 1 (party graph)** is unaffected. It is a new model in a new module.
- **Wave 2 item 5 (screening adapter interface)** is unaffected. It is a new module with no OPR dependency.
- **Wave 2 item 11 (G10 listing permit block, G18 agent licence gate)** is implemented in `sgc_listing_compliance` with its own property master model. The OPR's `property_details` is not imported.
- **Wave 3 items 16–26** (sale conditions, Ejari gate, rent review, dunning, commission gate, emergency maintenance, dedupe, developer lane) are all implemented in their own siblings with their own narrow models.

## 8. Decision

**Adopt the recommended path: clean siblings, no `depends` on `sgc_offplan_rental_property_management`.**

The amendment's liability framing is decisive: a clean sibling has clean provenance in the lender pack. A module that depends on OPR inherits OPR's UNRESOLVED status, OPR's inherited defects, and OPR's audit timeline. The dependency cost is permanent; the LOC cost is one-time. The choice is clear.

## 9. Migration path for tenants currently on OPR

Tenants that already use OPR for the full portal / website / public-rental-site surface continue to do so. OPR remains in the estate. Wave 2 / Wave 3 / Wave 4 siblings do not depend on it.

A migration note in each sibling's README explains:

- "This module does not import `sgc_offplan_rental_property_management`. Tenants on the OPR stack can run this sibling in parallel; data models are independent."
- "Tenants that have been using OPR's property master will see this sibling's property master as a separate, parallel model. Data migration is a separate workstream — out of scope for the gap-closure programme."

A future "OPR retirement" workstream — not in this programme — can map data between the parallel models. That is a v2 problem.

## 10. Outstanding flag

The OPR file-by-file provenance audit remains a parallel workstream. It does not sit on the critical path of this programme. The recommended path means **its outcome does not block Wave 2 / Wave 3 / Wave 4 / Wave 5** of this programme.
