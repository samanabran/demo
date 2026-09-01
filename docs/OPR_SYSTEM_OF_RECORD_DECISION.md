# OPR System-of-Record Decision

> **Authority:** `AMENDMENT_001_VENDOR_TENANT_BOUNDARY.md` §4 Directive One + `OPR_SCOPING_STUDY.md`.
> **Purpose:** define which model is system-of-record for each shared entity, given that the clean Wave 2/3/4/5 siblings and the existing OPR will both carry property / unit / lease / project records on the same database.
> **Status:** DRAFT, applied to Wave 2 entry gate.
> **Date:** 2026-09-01.

---

## 1. The risk

Per `OPR_SCOPING_STUDY.md`, the clean-sibling decision means:

- **`sgc_offplan_rental_property_management` (OPR)** keeps its existing models in `models/core/` — `property.details`, `property.project`, `tenancy.details`, `rent.contract`, `sale.contract`, `payment.schedule`, `rera.form.a`, etc.
- **Clean siblings** built in Wave 2 / Wave 3 (`sgc_listing_compliance`, `sgc_transaction_conditions`, `sgc_developer_lane`, `sgc_collections_ladder`) will carry **parallel** models for the same entities.

If both are installed and both write to the same database, a single tenant has:

- `property.details` (OPR) with the property master.
- `sgc_listing_compliance.property` (clean) with the same property master.

Two models diverging under the same tenant's data is a hard failure to unwind later. **This decision fixes the SoR before any Wave 2 code is written.**

## 2. Decision: clean siblings are system of record. OPR is consumer / read-only bridge.

For each shared entity, the clean-sibling model is the **system of record**. The OPR's existing model — if installed — is a **read-only consumer** that fetches via a bridge view or a thin proxy.

| Entity | System of record | OPR's model becomes | Bridge pattern |
|---|---|---|---|
| Property master | `sgc_listing_compliance.property_master` (Wave 2) | Read-only proxy, points at the SoR | OPR's `property.details` records become bridge records: `def compute_display_name(self): return self.system_of_record_id.display_name`. **No writes from OPR.** |
| Sale contract | `sgc_transaction_conditions.sale_contract` (Wave 3) | Read-only proxy | Same pattern. |
| Rent contract / tenancy | `sgc_transaction_conditions.tenancy` (Wave 3) | Read-only proxy | Same pattern. |
| Offplan project | `sgc_developer_lane.project` (Wave 3) | Read-only proxy | Same pattern. |
| Payment schedule (offplan) | `sgc_developer_lane.payment_schedule` (Wave 3) | Read-only proxy | Same pattern. |
| RERA Form A | `sgc_listing_compliance.trakheesi_form_a` (Wave 2) | Read-only proxy | Same pattern. |
| Recurring invoice | `sgc_collections_ladder.invoice` (Wave 3) | Read-only proxy | Same pattern. |
| Account.move / journal entry | Odoo `account.move` (unchanged) | Direct | No SoR conflict. |

## 3. Implementation pattern

The bridge is a **thin `_inherits` extension** of the OPR's model, NOT a re-declaration. The OPR module is *extended* in place by the clean-sibling module:

```python
class SgcListingComplianceProperty(models.Model):
    _name = "sgc_listing_compliance.property_master"
    _description = "Property master (system of record)"

    name = fields.Char(required=True)
    # ... all SoR fields ...
    permit_id = fields.Many2one("sgc_listing_compliance.trakheesi_form_a")
    # OPR's property.details exists on disk for tenants that ship OPR.
    # We point at it as a foreign key for legacy data references only.
    legacy_opr_property_id = fields.Integer(
        help="Foreign-key reference to OPR's property.details.id, "
             "populated only for tenants that previously used OPR. "
             "Read-only after migration. OPR's record is a proxy."
    )
```

The OPR's `property.details` model is **not modified** by the clean siblings. A migration script (one-time) reads OPR's records, creates clean-sibling records, and writes `legacy_opr_property_id` on each. After migration, OPR's record is a stale read-only bridge.

## 4. What this means in practice

For a tenant that has never used OPR:
- They install the clean siblings only.
- The SoR is the clean-sibling model.
- OPR is not installed.

For a tenant currently on OPR:
- They keep OPR installed (so the portal / website / public-rental surface keep working).
- They install the clean siblings alongside.
- A one-time migration script reads OPR's data, creates clean-sibling records, sets the legacy foreign key, and retires OPR's writes.
- OPR's records become read-only bridges. Any OPR code that *writes* the property master is a bug and must be patched or reported.

For a tenant that has OPR and chooses not to install the clean siblings:
- They keep OPR as-is.
- They have no `sgc_listing_compliance.property_master` records.
- The system-of-record is OPR by default — but with no clean-sibling overlay, the G24, G10, G18, G12, G11, G7, G8, G9 gaps remain at the OPR's existing closure status.
- The product does not enforce the system-of-record decision; tenants choose.

## 5. What this decision does NOT cover

- **OPR's controllers, QWeb templates, portal front-end, public-rental website** — unchanged. The OPR's broken QWeb templates (`rental_listings`, `rental_detail`, `thank_you`) remain broken. They are out of scope for the gap-closure programme; a separate OPR maintenance workstream owns them.
- **OPR's commission lines, vendor module, amenities, image gallery, brochure template, sales offer template, rent invoice report, maintenance contract report, statement of account template, payment schedule template, sales SPA template, rent contract report, sales purchase agreement template, property publish wizard, offplan property listing / detail, offplan project listing / detail, res.city view, res.region view, res.config settings view, the property tag / specification / document / connectivity views, the ir_action override, the ir_ui_view override, the file validation mixin, the rent commission line, the property vendor commission line, the property broker / customer / tenant / landlord dashboard** — out of scope. OPR tenants keep these; new tenants use the clean siblings.
- **OPR's existing views, menus, access rights** — unchanged. The OPR is a complete module; it is just no longer the system of record for the entities the clean siblings own.

## 6. What the clean siblings must NOT do

- **No clean sibling depends on OPR.** R3.
- **No clean sibling reads OPR's models at runtime.** If the migration script reads OPR once, the data is in the clean sibling. After that, OPR is irrelevant to the clean sibling.
- **No clean sibling writes to OPR's models.** OPR's models are read-only from the clean sibling's perspective; OPR's own code may still read them.

## 7. Test surface

The clean siblings' tests should cover:

- `legacy_opr_property_id` is read-only after creation.
- The bridge pattern in §3 produces a single source of truth per entity, not a duplicate.
- The SoR is enforced at the SQL constraint level (unique index on the SoR; no uniqueness on the bridge).
- A tenant with both OPR and the clean sibling installed does not produce duplicate SoR records.

## 8. Decision summary

| Question | Answer |
|---|---|
| Which model is system of record? | The clean sibling, always. |
| Does OPR change? | No. OPR's own code may write to its own models as before. The clean siblings do not write to OPR's models. |
| Are the two parallel implementations? | No. The clean sibling is the SoR. OPR's record is a legacy bridge, read-only. |
| What about a tenant that has OPR and chooses not to install the clean siblings? | OPR remains the working system. The G24, G10, G18, G12, G11, G7, G8, G9 gaps remain at the OPR's closure status for that tenant. The product does not enforce the SoR decision; the tenant chooses. |
| What about a tenant that has neither OPR nor the clean siblings? | They install the clean siblings only. No OPR. |

This is the cleanest path. It is the path the OPR scoping study recommended. It is applied to all Wave 2 / Wave 3 / Wave 4 / Wave 5 module design.
