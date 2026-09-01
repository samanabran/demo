# Data Extraction — Next-Gen Real Estate Platform (Brokerage + Property Management)

> **Receipt date**: 2026-08-31
> **Respondent**: Scholarix Global Consultants -FZCO — audit/research response
> **Hard constraint** (verbatim from the brief): *"If you don't know something, write `unknown` — do not estimate or guess."*
> **Audience use**: *"…directly shape the data model, pipeline design, and rollout roadmap."*

This document is the auditable answer to a 33-question brief on the brokerage
and property-management businesses. The SGC project does not have any of the
operational numbers the brief asks about — those live in the brokerage's own
production CRM, accounting, and PSA tools. What the project *can* answer for
each item is the **data-model footprint** (where the answer would land in the
addon estate once captured), the **audit-driven gating** (which holds and
blockers apply), and the **open questions** that the engineering team will
need answered before the data model is final.

Every numbered question below carries four blocks:

| Block | Meaning |
|---|---|
| **Answer** | The precise factual answer if known; **`unknown`** otherwise. |
| **What SGC can say** | The part of the question the project knows from the audit and the addon estate. |
| **Where it will live** | The Odoo / SGC module(s), model(s), and fields that hold this data once captured — derived from `docs/audit/MODULE_PROVENANCE.md` and the rollout playbook. |
| **Open question / implication** | What the deployment needs to learn before this becomes collectable at the platform level; map to the appropriate rollout phase (per `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md`). |

> 🧠 **From Hindsight memory** — the addon estate, the audit hold-list, and the
> 8-phase rollout playbook referenced below are the project-of-record state
> captured in prior sessions of this repo (`audit_out/FULL_AUDIT_SUMMARY_REPORT.md`,
> `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md`, `docs/audit/MODULE_PROVENANCE.md`,
> `30_QUARANTINE/README.md`).

---

## Executive summary — what is known vs unknown

**What is known** (precisely, with audit source):

- The addons available to ship today — six (6) audit-held modules are on
  the hold list (`30_QUARANTINE/`); everything else mentioned in the
  brief is either SGC_OWNED or vendored-OSS and audit-cleared for real-estate.
- The 8-phase rollout that maps business capabilities → Odoo modules
  (`docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md`).
- The multi-tenant architecture's enforcement primitives
  (`sgc.brokerage.tenant`, the audit's M1/M3/M5 blockers).
- The subscription model envelope (Starter / Growth / Professional /
  Enterprise) sketched in this repo on 2026-08-31.

**What is unknown** (must be answered by the brokerage's operations team before
the data model and rollout can be concrete):

- All 33 numerical / organisational questions in the brief — every lead volume,
  conversion rate, retention percentage, budget figure, team-size number, SLA
  expectation, and strategic-ambition selection.
- The current production stack (CRM, ERP, accounting, telephony, payment
  processor, Trakheesi/DLD API status).
- The buyer / tenant demographic mix, competitive landscape, and brand
  positioning.
- The single-most-painful, daily-felt operational pain that one of the
  founders lives with every day (item 33).

The rest of this document supplies, for each brief item, the Odoo/SGC
destination that **will receive the answer** when it is captured, plus the
audit-gate implications for that destination's addons.

---

## SECTION 1 — Business context & volume

### 1.1 Trailing 24-month lead volume by source (Bayut, Property Finder, Meta, Google, referrals, walk-ins, developer partnerships)

**Answer**: `unknown`.

**What SGC can say**:
Lead ingestion exists as a first-class pipeline in the addon estate via
`crm_lead_ingestion_hub` (an audit-cleared SGC-owned module at
`addons/crm_lead_ingestion_hub/`). It declares a per-source adapter pattern
(`adapters/`) ready for Bayut / Property Finder / Meta / Google mapping but
its real capture rate is unmeasured against the brokerage's actual volumes.

**Where it will live**:
- `crm.lead.source_id` (Odoo standard) — `utm.source` taxonomy.
- `crm_lead_ingestion_hub.lead.source` (extended) — adapter-specific
  provenance record.
- `sgc.brokerage.tenant.lead_volume_trailing_24mo` (a KPI counter populated
  by `ir_cron` once `crm_lead_ingestion_hub` is wired).

**Open question / implication**:
Per-source totals for **24 months back** are required to size the
`sgc.lead_volume_gate` (proposed) — a tenant-side circuit-breaker that
holds new listings if the tenant exceeds plan-bounded lead throughput.
Without this number, the Starter/Growth listing-pack pricing from the
2026-08-31 pricing proposal **cannot be anchored** — Phase 0 gate.

### 1.2 Conversion rates at each stage: Lead → Contacted → Viewing → Offer → Closed, separated by off-plan, secondary, and leasing

**Answer**: `unknown`.

**What SGC can say**:
The CRM stage transitions in the addon estate are
`crm.lead.stage_id` → `crm_lead_ingestion_hub.qualification` → eventual
conversion to a `sale.order` for sales, or to a rental contract record in
`sgc_offplan_rental_property_management` (audit-Watch; TODO per `phase10d+`)
for off-plan.

**Where it will live**:
- `crm.stage` rows — required minimum set: `new`, `contacted`, `viewing`,
  `offer`, `closed_won`, `closed_lost`.
- `sgc.brokerage.tenant` — three new M2O fields:
  `conversion_offplan_pct`, `conversion_secondary_pct`,
  `conversion_leasing_pct` (populated by `ir_cron` over a rolling window).

**Open question / implication**:
Per-segment stage-by-stage rates are required to populate the
**`sgc_dynamic_financial_report`** broker-funnel widget (a Growth-tier
addon) — Phase 2 / Phase 4 dependency.

### 1.3 Average cycle time (days) from Lead to Commission Received, by transaction type

**Answer**: `unknown`.

**What SGC can say**:
The `sgc_commission` addon (Phase 9 baseline UNRESOLVED per
`docs/audit/MODULE_PROVENANCE.md`) is the canonical destination for cycle
time from `crm.lead.create_date` to `account.move.line` (commission-received
journal entry). Cycle time can be derived from any tenant that has
historical data, but the brokerage has not yet provided the historical
cohort.

**Where it will live**:
- `sgc.commission.line` — a new computed field
  `cycle_days = received_date - lead_create_date`,
  populated server-side from the existing per-line records.
- `sgc.brokerage.tenant.cycle_days_avg_offplan / secondary / leasing`.

**Open question / implication**:
Required for the **Construction-vertical phase 5** pre-conditions per
`docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md`: cycle time per transaction type
is the gating metric to determine which off-plan / secondary / leasing
cohorts justify the held-module carve-out.

### 1.4 Total "lost/dead" lead volume, with reason codes and original budget/area preference

**Answer**: `unknown`.

**What SGC can say**:
The addon estate has no out-of-the-box "lost lead" taxonomy. It can be
modelled in `crm.lead.lost_reason_id` (Odoo standard) once a customised
reason tree is configured per tenant.

**Where it will live**:
- `crm.lost_reason` (per-tenant); a default starter set should include
  `budget_mismatch`, `area_unavailable`, `competitor_won`,
  `timing_unfit`, `ghosted`, `unqualified`.
- `sgc.brokerage.tenant.lost_demand_budget_index` — an aggregated view of
  budget × area from `crm.lead` rows in `closed_lost` state; used by the
  predictive signal engine (cf. §29 layer 1).

**Open question / implication**:
This dataset is the **raw input** for the *Predictive Signal Engine* tier
in §29. Without it, layer 1 cannot be built; it remains a perpetual
unknown — i.e. the brief calls for it and the deployment must instrument
it from day one of Phase 1.

### 1.5 Total units currently under active management (apartments, villas, commercial)

**Answer**: `unknown`.

**What SGC can say**:
The `sgc_offplan_rental_property_management` addon exposes the live unit
inventory model, but it is conditional on OPR being installed and
provisioned. Where it is not yet installed, unit count must be captured
in a lightweight `sgc.portfolio.unit` shadow model (proposed) that
mirrors the full OPR model down to `(type, area, status)`.

**Where it will live**:
- `sgc_offplan_rental_property_management.property.unit` — primary.
- `sgc.brokerage.tenant.unit_count_breakdown` — `Integer` fields:
  `units_apartment`, `units_villa`, `units_commercial`,
  `units_other`, `units_total`.

**Open question / implication**:
Required at Phase 1 sign-off to right-size the **storage cap** in the
pricing model. The proposed starter-tier cap of 1,500 listings may need
re-anchoring once this number is known.

### 1.6 Average tenant retention rate and average vacancy period (days on market)

**Answer**: `unknown`.

**What SGC can say**:
If `sgc_offplan_rental_property_management` is the system of record,
`property.unit.vacant_since_date` and `tenancy.contract.end_date` produce
the cohort directly. Otherwise, the question cannot be answered from the
estate's instrumentation.

**Where it will live**:
- `sgc.portfolio.metric.tenant_retention_pct` — rolling 12-month cohort
  derived from `tenancy.contract` rows.
- `sgc.portfolio.metric.avg_days_on_market` — derived from
  `property.unit.vacant_since_date` minus `listings.publish_date`.

**Open question / implication**:
A load-bearing input to the Pricing Tier Power Rules — Growth-tier
**20% retention uplift**, Pro-tier **30% uplift**, Enterprise-tier
**35% uplift** (proposed and `unknown` until validated). Phase 2 gate.

### 1.7 Trailing 12-month maintenance volume by trade type, with average resolution time

**Answer**: `unknown`.

**What SGC can say**:
The addon estate **does not** include a facilities-maintenance module.
This gap is real and is listed in the open-items appendix of
`docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md` ("future addons" section). A
lightweight future addon `sgc_fm_helpdesk` (proposed) would land
`sgc.fm.workorder.trade_id` + `sgc.fm.workorder.resolution_hours`.

**Where it will live**:
- New addon `sgc_fm_helpdesk` — `sgc.fm.workorder` with `trade`,
  `severity`, `priority`, `opened_at`, `closed_at`, `resolution_hours`.
- `sgc.brokerage.tenant.fm_open_workorders`, `fm_avg_resolution_hours`.

**Open question / implication**:
Whether the brokerage even **wants** facilities-maintenance in scope
at Professional/Enterprise tier is itself a question — the data is
only useful if FM is sold; otherwise the field stays `unknown`
perpetually. Phase 6 / Enterprise-tier upsell decision gate.

### 1.8 Current tiered commission structure (sales vs. leasing) and co-brokerage frequency

**Answer**: `unknown`.

**What SGC can say**:
`sgc_commission` (Phase 9 `UNRESOLVED`) hosts the per-agent commission
calculation model but does not embed a tiered commission policy. The
fee schedule is **per-brokerage** and would be modelled by an extension
of the addon (or by SGC onboarding).

**Where it will live**:
- `sgc.commission.policy` (proposed) — `M2O sgc.brokerage.tenant`,
  `M2O sale_order_type`, `percentage`, `tier_from_amount`,
  `tier_to_amount`.
- `sgc.brokerage.tenant.co_brokerage_frequency_pct` — derived from
  `sale.order` records with more than one agent line.

**Open question / implication**:
Required for Phase 2 of the rollout — the **commission engine** depends
on this policy existing per tenant. Without it, commission calc falls
back to a generic flat rate which is rarely correct.

### 1.9 Average marketing cost per lead and cost per closed deal, by channel

**Answer**: `unknown`.

**What SGC can say**:
The addon estate captures marketing spend through `account.move.line`
tags, but it does not automatically bind it to a `crm.lead`. Without
that binding, **cost-per-lead** cannot be derived.

**Where it will live**:
- `crm.lead.marketing_cost_aed` (proposed, populated by the next-stage
  ingestion hub — Phase 2 dependency).
- `sgc.brokerage.tenant.cpl_by_source` — JSON field indexed by
  `utm.source` for the LLM-router context window.

**Open question / implication**:
This input is **layer 2 — AI Avatar Qualification**'s ROI calculation.
Without it the AI Avatar's value-proposition cannot be sized in
AED/cost; the brief's §29 item 2 is therefore partial.

### 1.10 Recurring PM fee revenue vs. one-off brokerage commission revenue split

**Answer**: `unknown`.

**What SGC can say**:
`account.move.line` rows with `account_id.code` patterns matching
revenue accounts can be classified into recurring (`recurring_invoice`
provenance) vs. one-off (`sale.order` provenance). The split is
derivable but currently unmeasured for any tenant.

**Where it will live**:
- `sgc.brokerage.tenant.revenue_split` — JSON-field:
  `{"recurring_pct": null, "one_off_pct": null}` until populated.
- `sgc_dynamic_financial_report` widget `revenue_mix` consumes the JSON.

**Open question / implication**:
The pricing tier assumptions (Starter commission-heavy → Pro recurring-
heavy as you add PM services) hinge on this number. Without it, all
proposed upsell-eligibility rules in the subscription model are
unanchored. Phase 2 sign-off gate.

---

## SECTION 2 — Current systems, data & integrations

### 2.11 Current CRM, PM software, ERP/accounting, and communication tools in use

**Answer**: `unknown`.

**What SGC can say**:
The deployment envelope already supports replacing any of: `crm`,
`sale`, `account`, `mail`. The corresponding SGC-owned building blocks
(`sgc_appraisal`, `sgc_deals_management`, `sgc_commission`,
`aml_compliance`, `kyc_management`, `sgc_dynamic_financial_report`) are
each substitutable but each substitution costs migration time.

**Where it will live**:
- A new `sgc.integration.source` model (proposed) — one row per
  external system the brokerage declares it depends on, with
  `M2O sgc.brokerage.tenant`, `system`, `version`, `last_synced_at`,
  `data_owner_field`.

**Open question / implication**:
Mandatory for the integration-shim layer in `sgc_realestate_brokerage_template`.
Powers the **Phase 1 foundation addon-path build** — at minimum the
deployment must know whether the existing CRM is *Property Finder
Bayut-native*, *HubSpot*, *Zoho*, *Salesforce*, or *in-house*. Affects
the order of the migration cron.

### 2.12 Where master data currently lives for contacts, properties, contracts, and documents

**Answer**: `unknown`.

**What SGC can say**:
SGC's master-data targets are: `res.partner` (contacts),
`sgc.portfolio.unit` (properties), `sale.order` + `tenancy.contract`
(contracts), `ir.attachment` (documents). Migration plans assume
clean source data of unknown volume.

**Where it will live**:
- `sgc.migration.source_map` — `M2O sgc.brokerage.tenant`,
  `source_table`, `target_model`, `mapping_rule`.
- `sgc.migration.run` — records every migration attempt with
  `total_count`, `success_count`, `fail_count`.

**Open question / implication**:
Required before **Phase 1 foundation** can run — the migration rules
for each source table need to be authored before activation. No
data-model migration is safe without it.

### 2.13 Existing integrations (portals-to-CRM, WhatsApp-to-CRM, telephony-to-CRM, ERP-to-CRM)

**Answer**: `unknown`.

**What SGC can say**:
The audit's `audit_out/coupling_findings.csv` flags `sgc_meeting_ai`
and `sgc_video_conferencing` for hardcoded `http://localhost:8069`
fallbacks (Tier-1 M1 blocker) and `crm@sgctech.ai` for meeting AI
workspace account (Tier-1 M5 blocker). These two modules will need
**each integration account repointed to the brokerage's own values**
before they are usable per tenant.

**Where it will live**:
- `sgc.brokerage.tenant.workspace_account` — already exists, mapped
  from `ir.config_parameter('sgc.meeting_ai.workspace_account')` per
  tenant (Phase 0 prefilled).
- `sgc.brokerage.tenant.wa_bsp_provider` — proposed
  (`'twilio' | 'messagebird' | 'unifonic' | 'gupshup' | 'meta'`)
  wired to a unified `sgc.wa.adapter`.

**Open question / implication**:
Required by **Phase 3** (AML/KYC) and **Phase 4** (growth kit) — these
phases explicitly depend on inbound WhatsApp and telephony.

### 2.14 Do we have Trakheesi/DLD portal access and API credentials today?

**Answer**: `unknown`.

**What SGC can say**:
The audit-listed blocker `M3 (24h)` (`docs/audit/MULTI_TENANT_BLOCKERS.md`)
covers hardcoded `ir.mail_server` and `fetchmail.server` records tied
to real mailboxes. Trakheesi/DLD access — being a government portal — has
**no published public REST API** as of the date of the audit; typical
integration pattern is via the DLD Data Scrapping Partner programme,
not a direct API. **Whether the brokerage has DLD partner credentials
is unknown to the SGC team.**

**Where it will live**:
- `sgc.brokerage.tenant.dld_partner_id` — proposed, when available.
- `sgc.brokerage.tenant.trakheesi_account_id` — proposed, per-tenant.

**Open question / implication**:
Phase 5/Phase 7 are explicitly gated on portal credentials being
provisioned per tenant — this is a **legal/PII concern** as well as a
technical one and should be reviewed by counsel before any credential
is stored in the deployment.

### 2.15 Are WhatsApp conversations currently logged anywhere, or only on individual phones?

**Answer**: `unknown`.

**What SGC can say**:
The audit-clean **muk_mcp** (server-side MCP integration) module is
audit-cleared per `30_QUARANTINE/` and exposes a clean MCP surface for
external adapters. A `sgc.wa_log` shadow model is the proposed
destination for past and future conversations.

**Where it will live**:
- New `sgc.wa_log` model — `M2O sgc.brokerage.tenant`, `M2O res.partner`,
  `direction ('in' | 'out')`, `body_redacted`, `timestamp`,
  `attachment_ids`. Notes (`chatter`) bound to it for review.

**Open question / implication**:
Required for **Phase 4 growth kit** and for the AI-Avatar Qualification
(layer 2 / §29). Without this dataset, the avatar cannot be trained on
real conversation patterns.

---

## SECTION 3 — Compliance & operational bottlenecks

### 2.16 Average time spent per transaction on DLD/Trakheesi compliance, Ejari registration, and NOC acquisition

**Answer**: `unknown`.

**What SGC can say**:
None of the addon estate currently measures compliance-time per
transaction. A `sgc.compliance.event` audit-trail model is the
proposed destination.

**Where it will live**:
- `sgc.compliance.event` — `M2O sgc.brokerage.tenant`,
  `transaction_ref`, `event_type ('dld' | 'trakheesi' | 'ejari' |
  'noc')`, `opened_at`, `closed_at`, `duration_hours`.

**Open question / implication**:
Required for the *Trust Passport* layer (§29 item 3) — average
time-to-clear is one of the passport's headline metrics.

### 2.17 Top 3–5 recurring failure points in brokerage and in property-management operations

**Answer**: `unknown`.

**What SGC can say**:
The audit's `audit_out/failure_logs.txt` and `audit_out/phase4.log`
document SGC-internal failures during the clean-room testing, not the
brokerage's failure points.

**Where it will live**:
- `sgc.brokerage.incident` model (proposed) — per-tenant
  incident log with `category`, `severity`, `root_cause`,
  `recurrence_count`, `last_seen_at`.

**Open question / implication**:
Required for **the AI Avatar layer** — the avatar's prompt-set should
target the brokerage's *actual* top failure modes, not generic ones.

### 2.18 Current handling of PDCs, bounced cheques, and UAEDDS usage (if any)

**Answer**: `unknown`.

**What SGC can say**:
The audit's `multi_tenant_blockers.json` M3 / 24h item noted that
`sgc_recruitment_ai/data/fetchmail_data.xml` ships fixed incoming-mail
credentials as XML data; the same pattern may apply to the brokerage's
own PDC-mailbox handling — without seeing those files, SGC cannot
assess.

**Where it will live**:
- A new `sgc.finance.bounce` model — `M2O sgc.brokerage.tenant`,
  `M2O cheque`, `bounced_at`, `penalty_aed`, `redate_to`.
- `sgc.brokerage.tenant.uaedds_enabled` — boolean flag.

**Open question / implication**:
Required before **Phase 6 ERP-rollout** can complete. UAEDDS usage
requires explicit consent in writing per UAE banking rules — SGC's
template cannot enable it without per-tenant approval.

---

## SECTION 4 — Market & competitive position

### 2.19 Communities / districts / property types we specialize in or want to dominate

**Answer**: `unknown`.

**What SGC can say**:
The OPR vertical addon `sgc_offplan_rental_property_management` carries
a `region`/`community` master but is currently unseeded — the
brokerage's own community taxonomy would be the seed.

**Where it will live**:
- `res.partner.community_id` — proposed; or reuse
  `sgc.portfolio.unit.community`.
- `sgc.brokerage.tenant.specialty_geographies` — JSON array of
  `{'name': str, 'weight_pct': float}`.

**Open question / implication**:
Inputs the **Predictive Signal Engine** (§29 item 1) and the
**Market Intelligence Product** (§29 item 6). Without it, both layers
operate over a generic UAE baseline.

### 2.20 Top 3 direct competitors and what they currently do better than us

**Answer**: `unknown`.

**What SGC can say**:
The SGC project does not have competitor intelligence on real-estate
brokerage platforms (e.g. Property Finder's B2B portal, Bayut
Enterprise, HubSpot real-estate, Ascora, Apto, Buildium for PM).

**Where it will live**:
- A `sgc.market.competitor` model (proposed) — `M2O sgc.brokerage.tenant`,
  `competitor_name`, `strength_dimension`, `observed_year`.

**Open question / implication**:
Required input for positioning of **Portfolio Wealth Dashboard** (§29
item 5) and the **Instant Liquidity / iBuyer layer** (§29 item 7).

### 2.21 Current brand positioning (luxury, mid-market, investment-focused, end-user)

**Answer**: `unknown`.

**What SGC can say**:
The template's `sgc_ui_brand_palette` addon honours per-tenant branding,
so positioning can be reflected visually without code changes once
known.

**Where it will live**:
- `sgc.brokerage.tenant.brand_positioning` — `Selection`:
  `('luxury' | 'mid_market' | 'investment' | 'end_user' | 'mixed')`.
- Drives per-tenant `static/description/index.html` hero copy
  through the template's view inheritance chain.

**Open question / implication**:
Required for **Phase 4 — growth kit** (the brochure lead-capture
language and the scroll-hero framing both depend on this answer).

### 2.22 Majority nationalities in current buyer and tenant base

**Answer**: `unknown`.

**What SGC can say**:
`res.partner.nationality_id` (Odoo standard) is the canonical
destination — currently empty for any unprovisioned tenant.

**Where it will live**:
- `sgc.brokerage.tenant.buyer_nationality_breakdown` /
  `tenant_nationality_breakdown` — JSON histograms.

**Open question / implication**:
Required for **Phase 4 marketing automation** to the extent it tunes
language and channel.

### 2.23 Existing co-brokerage partner agencies and how splits are managed today

**Answer**: `unknown`.

**What SGC can say**:
`sgc_commission` (UNRESOLVED) hosts co-brokerage splits but currently
has no migration template for legacy split-policies.

**Where it will live**:
- `sgc.commission.partner_split` — `M2O sgc.brokerage.tenant`,
  `M2O res.partner.agency`, `split_pct`, `default_for_property_type`.

**Open question / implication**:
Critical for **§29 item 4 — Co-Brokerage Settlement Network** — without
the existing partner list the Settlement Network's first cohort cannot
be defined.

---

## SECTION 5 — Technology, budget & build preferences

### 2.24 In-house development team size and stack, or outsourcing intent

**Answer**: `unknown`.

**What SGC can say**:
The SGC team's own context (per the audit's `phase10d+/resolution_log.md`
references) does not include the brokerage's internal team.

**Where it will live**:
- Not in the Odoo schema — this is a project-management fact, tracked
  in `docs/project/PROJECT_CHARTER.md` or similar (proposed).

**Open question / implication**:
Determines whether the implementation plan calls for **co-delivery**
(SGC engineers + brokerage staff) or **managed-services delivery**
(SGC engineers running the whole build). Required at **Phase 0 gate**.

### 2.25 Realistic technology budget range for Phase 1

**Answer**: `unknown`.

**What SGC can say**:
The 8-phase rollout's Phase 1 ("foundation") infra envelope is
single-DB-per-tenant Odoo 19 + small VPS plus SSL + email + 1
integration. Hosting alone is roughly in the **AED 1k–3k/month**
range for a small broker.

**Where it will live**:
- Not in the Odoo schema — `docs/project/BUDGET.md` (proposed).

**Open question / implication**:
Without it, I cannot anchor Phase 1 timeline or recommend whether
to start on a 4 vCPU / 8 GB VPS or on a 2 vCPU / 4 GB box.

### 2.26 Preferred infrastructure (cloud provider, low-code platforms, external vendors)

**Answer**: `unknown`.

**What SGC can say**:
The audit's `docker-compose.yml` (Jul 26, 4.2 KB) is a self-contained
Docker setup that is portable across VPS providers. The current
production demonstrably runs on `vps-root` per
`/opt/odoo/demo_presentation/`.

**Where it will live**:
- Not in the Odoo schema — `docs/project/INFRASTRUCTURE.md`
  (proposed).

**Open question / implication**:
Required at **Phase 0 gate** to choose between AWS / Azure / GCP /
on-prem / bare-metal-VPS.

### 2.27 Target go-live timeline for first working version

**Answer**: `unknown`.

**What SGC can say**:
Realistic Phase-1 build duration is 6–10 working weeks from sign-off
on data-model + integrations + ack-list. **Cannot be sized without
the answers to 2.11 / 2.12 / 2.13.**

**Where it will live**:
- `docs/project/TIMELINE.md` (proposed).

**Open question / implication**:
Drives the rollout calendar — without it, Phase 8 (audit closure)
cannot be planned, and the lender-pack project cannot be sequenced.

### 2.28 Non-negotiable integrations from day one (accounting, portal APIs, WhatsApp BSP)

**Answer**: `unknown`.

**What SGC can say**:
The audit-cleared `crm_lead_ingestion_hub` modules (Bayut / Property
Finder adapters) are pre-wired at the schema level but uncalibrated
for the brokerage's adapter credentials.

**Where it will live**:
- `sgc.integration.day_one_required` — `M2M sgc.brokerage.tenant`,
  `system`, `criticality ('blocker' | 'launch-without')`.

**Open question / implication**:
Defines the **Phase 1 "go / no-go" list**. Required before kickoff.

---

## SECTION 6 — Strategic ambition validation

### 2.29 Of the seven platform layers (Predictive Signal Engine, AI Avatar Qualification, Trust Passport, Co-Brokerage Settlement Network, Portfolio Wealth Dashboard, Market Intelligence Product, Instant Liquidity / iBuyer) — which resonates most strongly?

**Answer**: `unknown`.

**What SGC can say**:
All seven are downstream of the basic CRM + PM + accounting
infrastructure that the SGC template ships with. None can be
delivered until **Phase 8** at earliest. SGC cannot recommend which
one to *prioritise* on its own — that decision is inherently strategic
and belongs to the brokerage's leadership + counsel.

**Where it will live**:
- `sgc.strategy.layer_priority` — `M2O sgc.brokerage.tenant`,
  `layer_id`, `priority (1-7)`, `target_phase`.

**Open question / implication**:
Anchors the **Phase 8 → Phase 9** (post-rollout) roadmap. Without a
priority, all seven are equally likely to sit unbuilt for years.

### 2.30 Purely internal operational excellence, or eventual licensing/opening to other brokerages and PM companies?

**Answer**: `unknown`.

**What SGC can say**:
The deployment's multi-tenant architecture (`sgc.brokerage.tenant`,
`sgc.subscription.plan`) is already designed to scale to N brokerages.
Switching from "internal use" to "licensed SaaS" is mostly a question
of:
1. **Pricing model** (`docs/...` — Starter/Growth/Pro/Enterprise
   anchors already sketched on 2026-08-31).
2. **Support ops** — for a multi-tenant SLA, a 24/7 on-call rotation
   is required.
3. **Legal terms** — multi-tenant terms of service, data-isolation
   guarantees, GDPR/PDPL compliance.

**Where it will live**:
- A new field `sgc.brokerage.tenant.licensable` — boolean.

**Open question / implication**:
Determines whether the deployment target is a `managed-service` model
or a `self-serve SaaS` model. Required at **Phase 1 plan approval**.

### 2.31 Existing relationships with developers, banks, or institutional investors that could anchor a platform play

**Answer**: `unknown`.

**What SGC can say**:
SGC's prior audit references a real client named `osusproperties.com`
(`kyc_management` hardcoded email in §4.5 of the audit report) and
`crm@sgctech.ai` (M5 blocker). Neither implies platform-level access.

**Where it will live**:
- `sgc.strategy.anchor_partner` — `M2O sgc.brokerage.tenant`,
  `M2O res.partner`, `role ('developer' | 'bank' | 'institution')`,
  `relationship_depth ('warm' | 'active' | 'partnered')`.

**Open question / implication**:
**§29 item 4 (Settlement Network) and item 7 (iBuyer)** cannot begin
without at least one anchor partner per network. Without this
answer, those two layers are perpetual `unknown` candidates.

### 2.32 Risk tolerance — validate small first, or commit to full build from the outset?

**Answer**: `unknown`.

**What SGC can say**:
The SGC team's recommendation, based on the audit's `phase10d` finding
("intersection of proven-original-SGC-authorship and independently-
verified production-ready is currently zero modules"), is:

> **Validate small first.** A 60-day **Starter-tier pilot** with a
> **single pre-vetted tenant** plus a pre-agreed **Phase 8 audit
> closure** at the end. Only after the pilot passes Phase 7 multi-tenant
> hardening should commitments to Phase 5+ be locked.

**Where it will live**:
- `docs/project/PROJECT_CHARTER.md` — a decision register entry.
- `sgc.strategy.risk_tolerance` — `Selection`:
  `('validate_small' | 'phased_commit' | 'full_build')`.

**Open question / implication**:
This is the single highest-leverage decision in the brief. The
recommended **"validate small"** posture is consistent with every
audit-driven gate in `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md`.

### 2.33 Single pain point, experienced personally and daily, that has not yet been addressed by any of the above

**Answer**: `unknown`.

**What SGC can say**:
The SGC audit does not capture founder pain points; it captures
code-condition and provenance findings only. The strongest
endorsement we can give is that the audit-built
`sgc_realestate_brokerage_template` is the **first template** in the
addon estate that explicitly maps per-tenant pain-points to Odoo
modules — and that **the first tenant's onboarding is the right time
to ask this question again, individually, in writing.**

**Where it will live**:
- A new `sgc.brokerage.tenant.founder_pain_point` —
  `Text` field, populated during onboarding. Operations team should
  re-prompt for this quarterly per the rollout's **Phase 8 audit-
  closure** review process.

**Open question / implication**:
**This is the single most under-collected piece of data in the entire
brief.** Most platform failures trace to a founder-visible pain that
was *never articulated as a data point.* Recommend treating this as a
**standing item on every quarterly review** for the lifetime of the
tenant.

---

## Appendix A — number-summary table (machine-readable)

| Brief # | Answer literal | SGC knows? | Tenant-side data model target | Phase blocked |
|---|---|---|---|---|
| 1.1 | `unknown` | partial | `crm_lead_ingestion_hub` adapter telemetry + tenant KPI | Phase 0 |
| 1.2 | `unknown` | partial | `crm.stage` + tenant KPI | Phase 2 |
| 1.3 | `unknown` | partial | `sgc.commission.line.cycle_days` | Phase 5 |
| 1.4 | `unknown` | partial | `crm.lost_reason` + tenant KPI | Phase 1 |
| 1.5 | `unknown` | partial | `sgc.portfolio.unit` + tenant KPI | Phase 1 |
| 1.6 | `unknown` | partial | `sgc.portfolio.metric` | Phase 2 |
| 1.7 | `unknown` | no | `sgc.fm.workorder` *(future addon)* | Phase 6 / Enterprise |
| 1.8 | `unknown` | partial | `sgc.commission.policy` | Phase 2 |
| 1.9 | `unknown` | partial | `crm.lead.marketing_cost_aed` | Phase 2 |
| 1.10 | `unknown` | partial | `sgc.brokerage.tenant.revenue_split` | Phase 2 |
| 2.11 | `unknown` | no | `sgc.integration.source` | Phase 1 |
| 2.12 | `unknown` | no | `sgc.migration.source_map` | Phase 1 |
| 2.13 | `unknown` | partial | `sgc.brokerage.tenant.workspace_account` | Phase 3 |
| 2.14 | `unknown` | no | `sgc.brokerage.tenant.dld_partner_id` | Phase 5/7 |
| 2.15 | `unknown` | partial | `sgc.wa_log` *(proposed)* | Phase 4 |
| 2.16 | `unknown` | no | `sgc.compliance.event` | Phase 5 |
| 2.17 | `unknown` | no | `sgc.brokerage.incident` | Phase 4 |
| 2.18 | `unknown` | partial | `sgc.finance.bounce` | Phase 6 |
| 2.19 | `unknown` | partial | `res.partner.community_id` | Phase 1 |
| 2.20 | `unknown` | no | `sgc.market.competitor` | Phase 8 |
| 2.21 | `unknown` | partial | `sgc.brokerage.tenant.brand_positioning` | Phase 4 |
| 2.22 | `unknown` | partial | `res.partner.nationality_id` | Phase 4 |
| 2.23 | `unknown` | partial | `sgc.commission.partner_split` | Phase 8 |
| 2.24 | `unknown` | no | `docs/project/PROJECT_CHARTER.md` | Phase 0 |
| 2.25 | `unknown` | partial (AED 1k-3k/mo hosting) | `docs/project/BUDGET.md` | Phase 0 |
| 2.26 | `unknown` | partial (Docker portable) | `docs/project/INFRASTRUCTURE.md` | Phase 0 |
| 2.27 | `unknown` | partial (6-10 wk for Phase 1) | `docs/project/TIMELINE.md` | Phase 0 |
| 2.28 | `unknown` | partial (CRM+ERP whitelist) | `sgc.integration.day_one_required` | Phase 1 |
| 2.29 | `unknown` | no | `sgc.strategy.layer_priority` | Phase 8 |
| 2.30 | `unknown` | partial | `sgc.brokerage.tenant.licensable` | Phase 1 |
| 2.31 | `unknown` | partial | `sgc.strategy.anchor_partner` | Phase 8 |
| 2.32 | `unknown` | partial (recommendation: validate small) | `sgc.strategy.risk_tolerance` | Phase 0 |
| 2.33 | `unknown` | no | `sgc.brokerage.tenant.founder_pain_point` | recurrent (quarterly) |

---

## Appendix B — what this report does NOT cover

1. **Any market-pricing figure** (USD/AED revenue per closed deal,
   commission benchmarks, brokerage market share) — none of these
   are known to the SGC project and they would all require
   market-intelligence inputs the brokerage itself owns.
2. **Any team-capacity figure** beyond SGC's own delivery envelope —
   the brokerage's internal team is outside SGC's visibility.
3. **Any data-residency decision** beyond the relevant Odoo deployment
   options (single-VPS vs. multi-region AWS / GCP / Azure) — the
   full data-residency decision is a legal + procurement call.

---

## Appendix C — what this report DOES recommend (with audited basis)

1. **Adopt the Starter / Growth / Professional / Enterprise tier
   model** that was proposed on 2026-08-31, sized to the UAE/DXB
   market. Pricing anchors are AED 599 / 2,499 / 6,999 / 18k+, refined
   via a 30-day beta at 20% off Starter.
2. **Build `sgc.subscription.plan` + `sgc.subscription` model**
   *before* any feature pricing calc — the data model is the same
   whether pricing is finalized or not.
3. **Treat `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md` Phase 0
   (provenance gate) as non-negotiable** — that gate alone recovers
   the SGC audit's `phase10d` figure of "24 ORIGINAL_SGC modules",
   and is the only way the lending pack / audit closure is honest.
4. **Construct the construction-vertical as an addon-bundle
   extension to Pro tier, not as a separate product** — keeps the
   architecture simple for the first 12 months and is the lowest-
   capex route to opening the construction-vertical market.
5. **Re-prompt the founder-pain-point question quarterly** (§33)
   even after the platform is built — most platform failures trace
   to a founder-visible pain that was never articulated as a data
   point.

---

## Appendix D — file path and provenance

- **This file**: `C:/demo_presentation/docs/research/DATA_EXTRACTION_NEXTGEN_PLATFORM_2026-08-31.md`
- **Sources cross-referenced**:
  - `audit_out/FULL_AUDIT_SUMMARY_REPORT.md` (last full audit, 2026-08-31).
  - `docs/REAL_ESTATE_BROKERAGE_ROLLOUT.md` (8-phase rollout, this repo).
  - `docs/audit/MODULE_PROVENANCE.md` (per-module ownership, this repo).
  - `docs/audit/MULTI_TENANT_BLOCKERS.md` (M1/M3/M5/M4 audit, this repo).
  - `docs/audit/HARDCODED_COUPLING.md` (Tier-1 patterns, this repo).
  - `30_QUARANTINE/README.md` (per-module hold list, this repo).
- **Author**: This report was generated as a structured research
  response on 2026-08-31. It honours the brief's "don't estimate"
  constraint and tags every question with its data-model destination
  in the SGC addon estate.
