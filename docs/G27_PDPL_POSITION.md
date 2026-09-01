# G27 — PDPL Processor Position

> **Authority:** `AMENDMENT_001_VENDOR_TENANT_BOUNDARY.md` §5; UAE Federal Decree-Law No. 45 of 2021 (PDPL); Amendment §11 DoD addendum criterion 11.
> **Status:** DRAFT, applied before Wave 2 code on the party graph.
> **Date:** 2026-09-01.
> **Architectural status:** This is the document that, when signed off, unblocks the party graph and the readiness gate (G28). Until it is signed off, **no Wave 2 module that captures personal data may be wired**.

---

## 1. Why this document exists

In a multi-tenant deployment we process personal data belonging to our tenants' clients: Emirates ID, passport, UBO records, source-of-funds evidence, screening results, signed documents, and five years of retained records. Under **the applicable regime for the tenant's jurisdiction** — resolved by a rules-pack lookup keyed on the `sgc.data_residency.region` enum — we act as **processor**. Processor duties attach to our architecture, not to tenant conduct.

The five items the amendment §5 requires this position to settle:

1. **Data residency decision, documented.**
2. **Cross-border transfer assessment for every outbound integration.**
3. **Encryption at rest and in transit** for identity documents and UBO records.
4. **Deletion mechanics at end of retention.**
5. **Tenant-level data isolation proof.**

A sixth item, drafted by counsel and referenced from the onboarding pack:

6. **Data Processing Agreement clauses** for the tenant contract.

The reconciliation of 5-year AML retention (Federal Decree-Law 10/2025) and PDPL data minimisation is also documented here so it is defensible rather than assumed.

---

## 2. Data residency (item 1)

**Decision (revised per the user's sign-off condition and Wave 3 remediation item 7): the SGC estate operates single-region today. Residency is `VENDOR` with a disclosure field, not `TENANT_CONFIG`. The multi-region path stays dormant — present in the schema as a hidden field but not asked of the tenant. The legal-regime mapping is driven by a rules-pack lookup keyed on the enum value, not hard-coded to PDPL.**

### Why the reclassification

Asking a tenant to attest to a residency they cannot change manufactures false assurance in a document a supervisor may later read. The honest position: there is one region today, the product tells the tenant what it is, and the tenant either accepts it or does not use the product. When multi-region operation exists, the field wakes up.

A silent default to `uae_mainland` would assert the wrong legal regime on a DIFC or ADGM tenant's behalf. DIFC and ADGM are separate legal jurisdictions with their own data-protection regimes; entities in either sit outside the federal PDPL entirely. A transfer between any two of the three is treated as cross-border despite all sitting inside the UAE. The enum distinguishes them; the rules pack maps the enum to the applicable regime.

### Residency enum (the new field shape)

`sgc.data_residency.region` is replaced by the **enum** below. The string `"uae"` is no longer accepted. The test `test_02_residency_migration_no_silent_default_to_uae_mainland` will assert that no stored value of `"uae"` is silently mapped.

| Enum value | Where it sits | Applicable regime |
|---|---|---|
| `uae_mainland` | UAE federal territory (Dubai, Abu Dhabi mainland) | The applicable regime is resolved by a rules-pack lookup keyed on this enum value. The current published regime is Federal Decree-Law 45 of 2021 (PDPL) + Cabinet 71/2024, but the product does not hard-code this — the rules pack does. |
| `difc` | Dubai International Financial Centre | DIFC Data Protection Law 1 of 2020 + DFSA Conduct of Business |
| `adgm` | Abu Dhabi Global Market | ADGM Data Protection Regulations 2021 + FSRA Conduct of Business |
| `other` | Reserved — for a future jurisdiction outside the three named above. | Resolved by a rules-pack lookup. |

A transfer between any two of `uae_mainland` / `difc` / `adgm` is **cross-border for the purposes of this product** and engages the §3 safeguard requirement.

### What ships now

```
sgc.data_residency.region                = "uae_mainland"  (VENDOR — single region, today)
sgc.data_residency.region_locked         = true   (VENDOR — locked until multi-region ships)
sgc.data_residency.disclosure_url        = <link to a public document the tenant can read>
sgc.data_residency.disclosure_accepted   = <reference to the tenant's signed acceptance>
sgc.data_residency.legal_regime_ref      = <rules-pack key: pdpl | difc_dpl | adgm_dpr | other>
```

The disclosure is a public document — a one-pager in plain language stating where the data lives, who has access, what the sub-processors are, and the **applicable legal regime** (resolved by the rules-pack lookup, never hard-coded to PDPL). The tenant signs the acceptance at onboarding. **The tenant does not attest to where the data lives; the tenant attests to having read the disclosure.**

### What is dormant for when multi-region exists

```
sgc.data_residency.region_multitenant    = ""  (hidden; activated when VENDOR ships multi-region)
```

When the engineering team builds the multi-region path, the dormant field wakes up, the disclosure is updated, and a future version of this document lifts `region` from `VENDOR` to `TENANT_CONFIG`. **Until then, the tenant's only commitment is to read the disclosure.**

### Class assignment

| Field | Class | Default |
|---|---|---|
| `sgc.data_residency.region` | `VENDOR` | "uae_mainland" |
| `sgc.data_residency.region_locked` | `VENDOR` | true |
| `sgc.data_residency.disclosure_url` | `VENDOR` | populated at deploy time |
| `sgc.data_residency.disclosure_accepted` | `TENANT_CONFIG` (acknowledgement) | blank, no default |
| `sgc.data_residency.legal_regime_ref` | `VENDOR` (engine) / `TENANT_CONFIG` (if tenant overrides) | rules-pack lookup, not hard-coded |
| `sgc.data_residency.region_multitenant` | dormant | "" |

---

## 3. Cross-border transfer assessment (item 2)

Every outbound integration that transmits personal data is in scope. Per amendment §5, the screening adapter is the live risk.

### Constraint the design must respect (per the user's sign-off condition)

The PDPL Executive Regulations were due within six months of the 2021 law and, per current public tracking, **have not been published as of this document's date**. Articles 22 and 23 of PDPL govern transfers. The adequacy mechanism depends on countries being designated as adequate — but with no Executive Regulations there is no published adequacy list.

**Consequence:** nobody, including the tenant's counsel, can currently certify that a screening provider's jurisdiction is "adequate." The product must not ask the tenant to make that certification.

The attestation field must record the **safeguard relied upon** under PDPL Article 23, with the tenant's cited basis. The absence of Executive Regulations is **uncertainty about enforcement mechanics**, not absence of obligation; the law itself is in force. When the Executive Regulations land, the rules pack treats adequacy as a new entry rather than a schema migration.

### What ships now

The attestation is a structured record, not a free-text field. The tenant records **which safeguard** they are relying on and **the cited basis**:

| `sgc.cross_border.safeguard` | When used |
|---|---|
| `contractual_clauses` | Article 23 — binding corporate rules or standard contractual clauses between the controller and the recipient. **This is the default for the screening provider.** |
| `explicit_consent` | Article 23 — the data subject has explicitly consented to the transfer, after being informed of the risks. Used only where the data subject is the contracting party. |
| `contract_performance` | Article 23 — the transfer is necessary for the performance of a contract between the data subject and the controller. |
| `public_interest` | Article 23 — the transfer is necessary for important reasons of public interest. |
| `legal_claims` | Article 23 — the transfer is necessary for the establishment, exercise or defence of legal claims. |
| `vital_interest` | Article 23 — the transfer is necessary to protect the vital interests of the data subject. |
| `public_register` | Article 23 — the transfer is made from a public register. |
| `adequacy_decision` | Article 22 — a published adequacy decision exists for the recipient country. **Cannot be used today; will become available when the Executive Regulations publish the adequacy list.** |

The default is `contractual_clauses` because the screening provider relationship is a controller-processor contract. The tenant's counsel confirms the safeguard is appropriate for the engagement; the product records the conclusion and the cited basis.

### Effective-dating

The whole `sgc.cross_border.*` block is **effective-dated**. The rules pack records:

- The `valid_from` is the date the PDPL Executive Regulations land. Today, `valid_from` is `null` for the `adequacy_decision` entry.
- When the Executive Regulations land, the engineering team adds an `adequacy_decision` entry with a real `valid_from` and the first published adequacy list. **No schema migration.** The screening adapter's safeguard check is data-driven.

### Decision matrix

| Integration | Cross-border? | Data class | Decision |
|---|---|---|---|
| Screening (AML / PEP / adverse media) | **Yes** — provider may be offshore | Emirates ID, name, DOB, country, UBO chain | **Gated.** The screening-adapter interface records the safeguard and the cited basis. Until the safeguard is recorded, the adapter does not call. **Wave 2 item 5.** |
| TFS list refresh | **Yes** — UN list refresh is hosted offshore | Names against the TFS list | **Gated.** Same safeguard pattern. |
| goAML filing | **No** — goAML is hosted in the UAE | REAR/STR/SAR payloads | Always allowed. |
| Trakheesi / DLD / RERA portals | **No** — UAE-hosted | Property master, listing permit | Always allowed. |
| Email (SMTP) | **Depends on relay** | Notification content | `TENANT_CONFIG` — the SMTP relay's data-residency must match the tenant's choice. |
| Bank feeds / payment rails | **Depends on provider** | Account move, payment references | `TENANT_CONFIG` — gated per provider. |
| Public website / portal | **No** | Listing content (no personal data) | Always allowed. |

### What the rules pack records

A new constant in `sgc_regulatory_rules_pack`:

| Code | Status | Notes |
|---|---|---|
| `pdpl_executive_regulations_effective_date` | `UNVERIFIED` (pending) | Public source: the published date when the Executive Regulations land. Today: `null`. |

When the date is known, the rules pack record is updated. **Effective-dating is mandatory on this constant per amendment Directive Three.**

---

## 4. Encryption (item 3)

**Decision: encryption is `VENDOR` at the engine level, `TENANT_CONFIG` at the key-management level.**

### At rest

- **Database-level encryption** (Transparent Data Encryption at rest) is `VENDOR` — the deployment ships it on by default. Tenants cannot disable.
- **Column-level encryption** for the specific personal-data fields (Emirates ID, passport, source-of-funds evidence documents) is `VENDOR` — the column type is encrypted in the schema. Tenants cannot disable.
- **Customer-managed keys (CMK / BYOK)** for the column-level encryption is `TENANT_CONFIG` — the tenant supplies the key reference. The product does not see the key.

### In transit

- **TLS 1.2+** for every external integration is `VENDOR` — the adapter interface rejects any integration that does not negotiate TLS 1.2 or higher.
- **mTLS** for sensitive integrations (screening, goAML, banking) is `VENDOR` — the product's adapter interface provides the client-cert configuration and refuses connections without it.
- **Internal transport** (between Odoo and the database) is `VENDOR` — the deployment ships TLS-enabled Postgres connections.

### What ships in Wave 2

- The column-level encryption is encoded at the schema level. Models that carry personal data fields use `fields.Char(..., encrypted=True)` or an equivalent Odoo pattern. **`sgc_tenant_readiness.tenant.fit.and.proper.integrity_attested_by_name` is not a personal-data field**; **`sgc_realestate_offplan.sale_contract.customer_id.passport_number` would be.**
- The screening adapter interface rejects plain-HTTP endpoints. The interface contract documents this; the test for Wave 2 item 5 enforces it.
- A tenant wanting BYOK is a deployment-level concern, not a module-level concern. The deployment template documents the option; the tenant chooses.

---

## 5. Deletion mechanics (item 4) — anchor at the terminal-state transition, not at creation

**Decision (revised per the user's sign-off condition): the statutory clock does not start when a record is created — it runs from the end of the business relationship or the completion of the transaction, whichever applies to that record type. The Wave 1 `retention_until` computation must be anchored on the right event, not on `created_at`.**

### The defect being closed

The current Wave 1 implementation in `sgc_process_control.models.process_exception._compute_retention_until` reads:

```python
@api.depends("status", "occurred_at")
def _compute_retention_until(self):
    for rec in self:
        anchor = rec.resolved_at or rec.occurred_at or fields.Datetime.now()
        rec.retention_until = (anchor + timedelta(days=5 * 365)).date()
```

The fallback to `occurred_at` is wrong. **The statutory clock runs from the end of the business relationship, not from the moment an event was first logged.** If the retention clock starts at `occurred_at` (= record creation) for record types where the AML obligation runs from relationship-end, every clock in the system fires early. **Early deletion of AML records is a worse failure than late deletion.**

### The fix (Wave 2)

Two new fields on `process.exception` and a per-record-type rule:

| Field | Class | Default | Notes |
|---|---|---|---|
| `retention_anchor_event` | `VENDOR` (per record type) | per record type | Named anchor: `record_creation` / `relationship_end` / `transaction_completion` / `terminal_state_entry`. |
| `retention_anchor_at` | computed | anchor event's timestamp | The datetime the anchor event occurred. |
| `retention_clock_set_at_terminal_state` | `Boolean` (default `True`) | True | When True, the anchor is set at the terminal-state transition. The clock is not ticking during the active life of the record. |

The terminal-state framework is the right place to hook it. When a record transitions to `sealed`, `dead_letter`, or `resolved` (whichever applies to the record type), the model captures the anchor datetime and the `retention_until` is computed from that anchor.

### Per-record-type default anchor

| Record type | Default anchor | Why |
|---|---|---|
| `aml_compliance.risk_assessment` | `relationship_end` | Decree-Law 10/2025 retention runs from end of business relationship. |
| `kyc_management.kyc_application` | `relationship_end` | Same. |
| `crm.lead` | `terminal_state_entry` (closed-lost) | The relationship is closed at terminal state. |
| `process.exception` | `terminal_state_entry` (sealed / dead_letter) | The exception is closed at terminal state. |
| `sgc_realestate_offplan.sale_contract` | `transaction_completion` | Retention runs from completion (transfer registration). |
| `sgc_realestate_offplan.tenancy` | `relationship_end` | Tenancy retention runs from lease end. |
| Signed documents (PDF) | `transaction_completion` | Document retention is tied to the contract lifecycle. |
| Screening results | `relationship_end` | Same as KYC. |
| TFS freeze records | **NEVER** — retained beyond 5 years per sanctions-programme audit | Distinct from AML retention. |

### Soft-delete vs hard-delete (unchanged)

| Record type | Default | Why |
|---|---|---|
| `crm.lead` | Hard-delete after 5y from terminal state | Not personal data. |
| `aml_compliance.risk_assessment` (anonymised) | Soft-delete (anonymise PII; retain aggregate statistics) | Statistics valuable for tuning; PII must go. |
| `kyc_management.kyc_application` (anonymised) | Soft-delete (anonymise PII; retain outcome) | Outcome needed for audit. PII must go. |
| `process.exception` | Soft-delete (retain summary; anonymise user references) | Audit value. |
| Signed documents (PDF) | Hard-delete (or shred with cryptographic proof) | PDPL data minimisation. |
| Screening results | Soft-delete (retain the outcome; remove the underlying data the provider returned) | Same as KYC. |
| TFS freeze records | **NEVER** | Distinct from AML retention. |

### Reconciliation of 5-year AML retention vs PDPL data minimisation

Retention under legal obligation is a lawful basis under PDPL Article 5 (the lawful-basis list — and Decree-Law 10/2025 retention obligation is one). The clock does not delete because the legal basis persists. **The clock anonymises PII while retaining the outcome.** This is the documented reconciliation.

The anchor is the right event, not the act of creation. **The clock starts at the terminal-state transition, runs for the retention period, and then fires anonymisation or deletion.** The clock is not ticking during the active life of the record.

### Where the deletion logic lives

The deletion hook is a method on the source model, not a generic cron. The cron dispatches; the model decides. The anchor datetime is set at the terminal-state transition by the model's own `action_seal` / `action_resolve` / `action_mark_dead_letter` method.

---

## 6. Tenant-level data isolation (item 5)

**Decision: standardise on Odoo's `check_company=True` + per-model `ir.rule` records. The architecture strategy is in `CHECK_COMPANY_VERDICT.md`.**

The brief verdict:

- The removal of `check_company=True` from `company_id` at `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py:54` is a correct technical fix. Not a defect.
- The system-level property is enforced by **per-model `ir.rule` records** with a `('company_id', 'in', company_ids)` domain.
- A `tools/audit_coupling_lint.py` extension to enforce M0 system-wide is part of Wave 2 item 11.

**Until that lint extension is in place and the per-model `ir.rule` audit is complete, no Wave 2 module that captures personal data may be wired.**

---

## 7. Data Processing Agreement clauses (item 6)

**Decision: the DPA clauses are `TENANT_CONFIG` (negotiated) and `VENDOR` (template).** The product provides a default DPA template; the tenant's counsel tailors it.

### Default clauses (template, VENDOR)

1. **Subject matter and duration.** Processor processes personal data on behalf of the controller for the duration of the subscription.
2. **Nature and purpose.** AML / KYC / screening / property management / tenancy administration, per the controller's onboarding configuration.
3. **Categories of data subjects and data.** Tenants' clients (buyers, sellers, landlords, tenants, beneficial owners, agents, employees). Categories: identity, contact, financial, screening results, transaction history.
4. **Controller's obligations.** The controller determines the lawful basis, the retention period, the risk appetite, the EDD triggers, and the data-residency choice.
5. **Processor's obligations.** Process only on documented instructions; ensure confidentiality; implement the technical and organisational measures; engage sub-processors only with consent; assist the controller with data-subject rights; delete or return on termination; audit.
6. **Sub-processors.** A registry of sub-processors, kept current. The screening provider, the email relay, the bank-rail provider, the cloud infrastructure. **Each is `TENANT_CONFIG`** because the tenant chooses.
7. **Data-residency.** The processor hosts in the region the controller selected. The controller can change region subject to the cross-border rules in §3.
8. **Security measures.** Encryption at rest, encryption in transit, access control, audit logging, breach notification within 72 hours.
9. **Personal-data breach.** Notification to the controller within 72 hours; cooperation with the supervisory authority.
10. **Data-subject rights.** Assistance with access, rectification, erasure, restriction, portability, objection.
11. **Audit.** The controller may audit once per year on reasonable notice. The processor provides a SOC 2 Type II equivalent report annually (where applicable) and a security questionnaire on request.
12. **Termination.** On termination, the controller chooses deletion or return of personal data. Deletion is the default.
13. **Cross-border transfer.** The processor honours the cross-border rules in §3 of this document. The screening provider is the principal cross-border surface.
14. **Governing law.** UAE PDPL (Federal Decree-Law 45/2021) for UAE-located controllers.

**The template ships in `sgc_tenant_readiness.data.dpa_template` as a QWeb template. The tenant's counsel edits it. The signed DPA reference is a `TENANT_CONFIG` field on the tenant record.**

---

## 8. PDPL position summary

| Item | Class | Where | Wave |
|---|---|---|---|
| 1. Data residency region (VENDOR: enum + locked) | VENDOR | `sgc.data_residency.region` (enum: `uae_mainland` / `difc` / `adgm` / `other`); `region_locked=true`; surfaced on readiness dashboard | Wave 2 (G28 capability-gated) |
| 1a. Data residency disclosure (VENDOR: link) | VENDOR | `sgc.data_residency.disclosure_url` (public one-pager, plain language, including the legal regime) | Wave 2 |
| 1b. Data residency acceptance (TENANT_CONFIG: signed) | TENANT_CONFIG | `sgc.data_residency.disclosure_accepted` (the tenant's signed acceptance) | Wave 2 |
| 2. Cross-border transfer assessment | TENANT_CONFIG (attestation) / VENDOR (block) | screening-adapter interface; readiness gate | Wave 2 (G28 + screening-adapter item 5) |
| 3. Encryption at rest | VENDOR (engine) / TENANT_CONFIG (key mgmt) | deployment + column-level encryption in personal-data fields | Wave 2 |
| 4. Encryption in transit | VENDOR | adapter interface, mTLS | Wave 2 |
| 5. Deletion mechanics | VENDOR (cron) / TENANT_CONFIG (per record type) | `process.retention.scheduler` | Wave 2 (G16 converts to CLOSED) |
| 6. Tenant-level data isolation | VENDOR (architecture) / TENANT_CONFIG (confirmation) | `check_company=True` + `ir.rule` per model | Wave 2 (item 11) |
| 7. DPA clauses | VENDOR (template) / TENANT_CONFIG (signed) | `dpa_template` + tenant-attestation field | Wave 2 |

**Until every item is signed off, no Wave 2 module that captures personal data may be wired.** This is the gating condition for the party graph (Wave 2 item 1) and the readiness gate (Wave 2 item 3).

---

## 9. Sign-off

This document is a position statement, not a final architectural commitment. It is signed off when:

- The user's counsel has reviewed §2 (residency), §3 (cross-border), §5 (deletion reconciliation), and §7 (DPA).
- The engineering lead has reviewed §4 (encryption) and §6 (isolation).
- The programme lead has reviewed the gating conditions in §8.

Until sign-off, the party graph work-in-progress is design-only. Implementation does not begin.
