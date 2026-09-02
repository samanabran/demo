# SGC Process Control

> The cross-cutting enforcement layer every business module consumes.
> Closes **G6** (bounded document chase), **G15** (integration failures have a
> lane), and **G16** (terminal states with retention clocks) of the programme
> gap register. Demonstrates the **Wave 1 exit gate**.

This is a foundational module under **Wave 1 of the gap-closure programme**.
It depends only on `base` and `mail` and contains no HELD or UNRESOLVED
modules in its `depends` list. New IP is original and separately attributable.

## What it provides

| Model / mixin | Purpose | Closes |
|---|---|---|
| `process.exception` | Exception queue. Every module writes here when something fails. Classifications: integration / data / process / dispute / regulatory. | G15 (integration failures have a lane) |
| `process.dlq` | Dead-letter queue. Holds failed integration calls after retry exhaustion. **A failed integration never reads as a clear result.** | G15 exit gate |
| `process.idempotency` | Every integration call carries a key. Re-execution with the same key returns the prior result. | G15 platform hygiene |
| `process.sla` | SLA clocks with named escalation rules and bounded-attempt counters. | G6 (bounded document chase with attempt counter) |
| `process.fail_closed.mixin` | Consumer-side mixin that returns CLEARED / BLOCKED / INDETERMINATE. INDETERMINATE == BLOCKED. Missing records == BLOCKED. | G1 (compliance gate), G15 |
| Retention framework | `retention_until` field on `process.exception`, computed from rules-pack retention constants. | G16 (5-year retention per record type) |

## Wave 1 exit gate

The brief §5 requires:

> a deliberately failed screening call lands in the DLQ, raises an
> alert, and is visibly *not* a clear result. Demonstrate this. It is
> the single most dangerous failure mode in the entire chain.

This is proven by `tests/test_exit_gate.py`:

- **`test_exit_gate_01_failed_screening_park_in_dlq_not_clear`** — A
  screening adapter that always raises (provider timeout) is called three
  times with exponential backoff. All three attempts fail. The exception is
  raised with `severity='critical'`, `alert=True`, `classification='integration'`,
  parked in `process.dlq`. The idempotency key is **not** marked succeeded.
  Result: a clearly visible DLQ entry, a clearly visible critical alert,
  and zero indication of a CLEARED result anywhere in the chain.

- **`test_exit_gate_02_cleared_call_path_works`** — A control test
  demonstrating that a successful screening call IS marked succeeded and
  produces no DLQ entry.

- **`test_exit_gate_03_fail_closed_mixin_raises_on_missing_case`** — The
  fail-closed mixin raises `UserError` when no compliance case is linked.
  A missing record is INDETERMINATE, never ALLOW.

- **`test_exit_gate_04_fail_closed_mixin_blocks_on_unknown_case_id`** —
  The mixin raises when the linked case record does not exist (deleted,
  broken reference). INDETERMINATE.

- **`test_exit_gate_05_fail_closed_mixin_blocks_on_pending_case`** — A
  pending compliance case blocks the consumer. INDETERMINATE.

The exit gate is **proven**, not asserted.

## Hard rules

1. **No silent failure.** A failed integration call must produce a DLQ
   entry, an alert, and a visible "INDETERMINATE" state on the
   consumer-side mixin.
2. **Fail closed.** INDETERMINATE == BLOCKED. Missing record == BLOCKED.
3. **No HELD / UNRESOLVED module in depends.** This module depends only
   on `base` and `mail`.
4. **All exceptions carry a retention clock.** The `retention_until` field
   on `process.exception` is computed from the rules-pack retention
   constant (`aml_retention_years`) so changes to that constant flow
   through automatically.

## Use of the fail-closed mixin

Consumers inherit the mixin and implement one method:

```python
class MyMoneyTouchingModel(models.Model):
    _name = "my.model"
    _inherit = "process.fail_closed.mixin"

    kyc_case_id = fields.Many2one("kyc.application")

    def _compliance_check_record_id(self):
        return self.kyc_case_id.id

    def action_bank_deposit(self):
        # Guard runs first. INDETERMINATE / BLOCKED → UserError + queue entry.
        self._assert_compliance_cleared()
        # ... only reached if CLEARED
```

## Use of the exception queue

```python
exc = self.env["process.exception"].raise_exception(
    summary="Screening call exhausted retries",
    classification="integration",
    severity="critical",
    target_system="DowJones",
    integration_key=idem.key,
    alert=True,
)
exc.write({"status": "dead_letter", "retry_count": 3})

self.env["process.dlq"].park(
    summary="Screening call exhausted retries",
    target_system="DowJones",
    operation="screening.match",
    exception_id=exc,
    idempotency_key=idem.key,
    attempt_count=3,
)
```

## Use of the SLA clock

```python
sla = self.env["process.sla"].create({
    "name": "Document chase",
    "rule_code": "kyc_document_chase",
    "due_at": datetime.now() + timedelta(days=2),
    "max_attempts": 3,
})

# On each attempt to chase a missing document:
sla.action_record_attempt()
# Raises an exception in the queue when the attempt counter reaches max.
```

## Tests

```bash
odoo-bin -d test_db -i sgc_process_control --test-tags sgc_process_control \
    --addons-path=./addons,./sgc_process_control --stop-after-init
```

The test suite covers: exception lifecycle, retry-count validation,
DLQ parking, idempotency get-or-create semantics, SLA exhaustion, and the
five-case exit gate.

## Provenance

- depends only on `base` and `mail` — no HELD or UNRESOLVED modules.
- All new IP is original and attributable.
- `audit_coupling_lint.py --fail-on-findings` exits 0 on the candidate path
  (per the brief §8 Definition of Done item 5).
