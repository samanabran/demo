# SGC Regulatory Rules Pack

> The single source of truth for every regulatory constant referenced by the
> real-estate workflow. Closes **G24** of the programme gap register.

This is a foundational module under **Wave 1 of the gap-closure programme**.
It depends only on `base` and `mail` and contains no HELD or UNRESOLVED
modules in its `depends` list. New IP is original and separately attributable.

## What it does

Two models and one helper API:

| Model | Purpose |
|---|---|
| `regulatory.jurisdiction` | Catalogue of regulatory regimes. Dubai populated at Wave 1 exit; Abu Dhabi / DIFC / ADGM present as empty placeholder rows per Q1 answer. |
| `regulatory.constant` | An effective-dated, jurisdiction-scoped, source-attributed value. Mandatory `valid_from` / `valid_to`, `source_url`, `verified_on`, `confidence`. |

```python
# Read a constant
value = self.env['regulatory.constant'].get_effective_value(
    'rear_cash_threshold_aed', 'dubai', as_of=tx_date,
)
# → 55000.0 (float) for AED 55,000 in force on tx_date

# Read a bool constant
ejari = self.env['regulatory.constant'].get_effective_value(
    'ejari_required', 'dubai', as_of=tx_date,
)
# → True (Python bool)

# Read a text constant
form_name = self.env['regulatory.constant'].get_effective_value(
    'dubai_sale_agreement_form', 'dubai', as_of=tx_date,
)
# → 'Form F' (str)
```

## What was migrated

The following hard-coded value was migrated off `aml_compliance` and onto the
rules pack as the first entry:

| Before (aml_compliance/reports/goaml_report_print.xml) | After (this module) |
|---|---|
| Literal `55000` in printed threshold text | Record with `code='rear_cash_threshold_aed'`, `value_numeric=55000`, `unit='aed'`, `confidence='verified'`. The consumer now reads via `get_effective_value()`. |

## What is UNVERIFIED

Two constants ship with `confidence='unverified'`:

| Code | Why |
|---|---|
| `rear_filing_deadline_days` | Public analyses conflict (Q9). Direct MoET/FIU confirmation required before go-live. |
| `rear_cash_commission_triggers_rear` | One source states brokerage commission received in cash ≥ AED 55k does not itself trigger REAR. Direct MoET/FIU confirmation required. |

The rules pack surfaces these as `UNVERIFIED` and consumers must check
`confidence` before treating the value as production-grade.

## Usage rules

1. **Never hard-code a regulatory constant in code.** Call
   `get_effective_value(code, jurisdiction_code, as_of=tx_date)`.
2. **Always pass `as_of`.** The AML regime changed twice in Q4 2025;
   an undated lookup cannot prove which rule applied at the time of a
   transaction.
3. **Surface `confidence` downstream.** UNVERIFIED values must be
   flagged to the calling user; they are not silently averaged with
   verified values.
4. **Do not import HELD modules.** `depends` is `base` + `mail` only.
   Adding a HELD module to `depends` is a R2 violation.

## Tests

```bash
odoo-bin -d test_db -i sgc_regulatory_rules_pack --test-tags sgc_regulatory \
    --addons-path=./addons,./sgc_regulatory_rules_pack --stop-after-init
```

The test module covers: migration off the consumer, lookup correctness,
effective dating, UNVERIFIED handling, confidence validation, value xor,
window sanity, missing-code error, PF/UBO readiness, and a full round-trip
over every seeded constant.

## Adding a new constant

1. Open Regulatory → Constants.
2. Choose the jurisdiction.
3. Set `code`, `value_numeric` or `value_text`, `unit`, `category`.
4. Set `valid_from`; leave `valid_to` empty for open-ended values.
5. If `confidence='verified'`, also set `source_url` and `verified_on`.
6. Add a `notes` line if this record supersedes a hard-coded value in a
   consumer module, naming the source file and the literal removed.

## Superseding an existing constant

Do not edit the original record. Create a new record with the same `code`,
an incremented `version`, a `valid_from` ≥ the original's `valid_from`, and
`supersedes_id` pointing to the original. Lookup will pick the highest
version whose window contains `as_of`.
