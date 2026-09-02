# DEFER 20 Register

> **Per the Wave 3 test protocol §11:** every DEFER SET failure is logged here with gap ID, class, severity, evidence and the trigger condition that would promote it to SHIP SET. A SHIP SET failure blocks; a DEFER SET failure ships.

The DEFER SET is the 20% of scope that is documented, not blocked. UI polish, report layout, performance, non-critical PARTIAL gaps, reference screening adapters beyond the abstract interface, localisation, tour/browser tests except where a capability has no server-side equivalent.

| ID | Item | Class | Severity | Why deferred | Promotion trigger |
|---|---|---|---|---|---|
| D-01 | UI polish — view ergonomics across the three modules | VENDOR | LOW | Stated in Wave 3 protocol §2 as DEFER SET. Functional surface is correct; visual is rough. | A signed-off design system. |
| D-02 | Report layout and QWeb pagination | VENDOR | LOW | Same. | A design system + report-template library. |
| D-03 | Performance and query-count optimisation | VENDOR | LOW | Not ship-blocking; functional correctness is the bar. | A performance budget per page load. |
| D-04 | Reference screening adapters (real providers) | VENDOR | LOW | The Wave 3 brief §6 only requires the abstract interface to be tested. Real adapters are tenant-side configuration. | A tenant selecting a provider and writing the adapter. |
| D-05 | Localisation (ar-AE, en-AE, hi-IN, ur-PK, etc.) | VENDOR | LOW | Not ship-blocking; translation files are added per language. | Tenant request for a specific locale. |
| D-06 | Tour / browser tests | VENDOR | LOW | Stated in Wave 3 protocol §2 as DEFER SET. | A signed-off test protocol for browser flows. |
| D-07 | Tour / browser tests for capabilities with no server-side equivalent | VENDOR | LOW | Same. | The capability is a screen-only flow. |
| **D-08a** | **PDPL Executive Regulations - constant value (`UNVERIFIED`)** | **VENDOR (regulatory)** | **HIGH - pre-go-live** | The constant `pdpl_executive_regulations_effective_date` is `UNVERIFIED` with `valid_from=null` in the rules pack. Re-verification is a named pre-go-live task, **not a test**. | The Executive Regulations publish. |
| **D-08b** | **PDPL Executive Regulations - tenant acknowledgement that the regime is in flux** | **TENANT_CONFIG** | **HIGH - pre-go-live** | The tenant's signed acknowledgement that they have read the regulatory-status disclosure and accept that the regime is the current published regime (resolved at the time of contract signature). | The tenant's onboarding wizard captures this. |
| **D-09** | **Check_company file citation** | **VENDOR (architecture)** | **MEDIUM** | The base brief cited `sgc_realestate_tenant.py:47`; the actual file is `sgc_realestate_brokerage_template/models/sgc_brokerage_tenant.py` (lines 46–50 comment, line 54 field). The verdict addresses the same code; the path discrepancy is in the base brief. | Inspection on the `sgc_tenant` DB during the isolation run. |
| D-10 | G18 (agent licence / dual-agency / conflict check) `ir.rule` enforcement | VENDOR | MEDIUM | The segregation mixin is built (4 unit tests, all green). The `ir.rule` records that bind lead-assignment and customer-relationship records to the CO/MLRO exclusion are not yet written. | The Wave 2 G18 item-11 implementation. |
| D-11 | G6 / G15 / G16 conversion from `CAPABILITY_PROVEN` to `CLOSED` (G6 is the bounded document chase; G7 is OPEN and out of scope here) | VENDOR | MEDIUM | The primitives are built and unit-tested. Conversion requires the first consumer wired (per the CAPABILITY_PROVEN definition). | The first consumer module installed. |
| D-12 | G21 PF dimension in `aml_compliance` schema | VENDOR | HIGH | A schema change to `aml_compliance` is needed. Cannot proceed until the OPR scoping decision is final and the host module is upgraded. | Wave 2 item 2. |
| D-13 | G30 TFS freeze / unfreeze state machine | VENDOR | HIGH | The screening adapter interface extension is not yet built. The freeze/unfreeze workflow is its own state machine. | Wave 2 item 5 extension. |
| D-14a | G29 bi-annual CO/MLRO report - recurrence rule + template + scheduler | VENDOR | MEDIUM | The recurrence (every 6 months from appointment), the template structure, and the scheduler are ours. | Wave 3. |
| D-14b | G29 bi-annual CO/MLRO report - content (findings, remediation, escalations, statistics) | TENANT_DECISION | MEDIUM | The content is the CO/MLRO's judgement. The product provides the engine; the CO/MLRO owns the substance. | The CO/MLRO fills it in via the UI. |
| D-15a | Cross-border safeguard field on the screening adapter (the field itself) | VENDOR | MEDIUM | The safeguard enum is in the rules pack. The screening adapter's attestation field is not yet wired to the readiness gate. | Wave 2 item 5. |
| D-15b | Cross-border safeguard value chosen by the tenant | TENANT_CONFIG | MEDIUM | The tenant chooses which safeguard (contractual_clauses, explicit_consent, contract_performance, etc.) they rely on. | The tenant's screening configuration. |
| D-16 | EOCN publication modelled as authoritative source | VENDOR | MEDIUM | The constant `uae_cabinet_74_2020_article_21` is in the rules pack. The screening adapter's EOCN-vs-vendor divergence path is not yet wired. | Wave 2 item 5. |
| D-17 | ~~`ir.rule` estate-wide tenant-isolation audit~~ — **MOVED TO SHIP SET.** Per Wave 3 remediation order item 5, this was misclassified as DEFER. The brief §2 places tenant data isolation in the SHIP SET and §13 requires zero uncovered models. The `ir.rule` records are now written for the 9 tenant-scoped models across the three modules (4 in process_control, 5 in tenant_readiness; the rules pack is shared catalogue and does not need tenant isolation). Item 4 of the remediation order closes the row. **Move corrects a misclassification, not a scope change.** |
| D-18 | Multi-region deployment path (dormant) | VENDOR | LOW | Single-region today. The dormant field `sgc.data_residency.region_multitenant` is in the schema but unused. | Engineering builds multi-region. |
| D-19 | UBO model and 15-working-day BO update clock (G22, G23) | VENDOR | HIGH | Party graph (Wave 2 item 1) is the longest pole. PDPL position must be signed off first. | Wave 2 item 1. |
| D-20 | Approved-with-conditions policy set as TENANT_DECISION | TENANT_DECISION | MEDIUM | The override record ships; the policy set itself is the tenant's. The product provides the engine; the tenant provides the policy. | Tenant configuration. |

## Process

- **Add** an entry: open a PR, name the new D-NN, fill all five columns.
- **Promote** a D-NN to SHIP SET: this is a CEO decision. The change includes a brief amendment to this register.
- **Resolve** a D-NN: close the row, link the commit that closed it, and bump the closest future wave's SHIP SET to include a regression test.

This register is the source of truth for what is and is not ship-blocking. It is reviewed weekly.
