# -*- coding: utf-8 -*-
# Part of SGC Process Control.
# See LICENSE file for full copyright and licensing details.
{
    "name": "SGC Process Control",
    "summary": (
        "Exception queue, SLA clocks, bounded-attempt counters, "
        "idempotency keys, retry-with-backoff, dead-letter queue. "
        "Supports the tenant's programme by recording evidence of "
        "failures and surfacing them for human routing. Closes G6 / "
        "G15 / G16 of the programme gap register as platform primitives."
    ),
    "version": "19.0.1.0.0",
    "category": "Platform / Process Control",
    "author": "Scholarix Global Consultants -FZCO",
    "website": "https://www.sgctech.ai",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        "security/ir_rule_tenant_isolation.xml",
        # Data — exception classification catalogue
        "data/process_classification_data.xml",
        # Views
        "views/process_exception_views.xml",
        "views/process_dlq_views.xml",
        "views/process_idempotency_views.xml",
        "views/process_sla_views.xml",
        "views/process_menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "sequence": 51,
    "description": """
SGC Process Control
===================

The cross-cutting enforcement layer every business module consumes. Closes
G6 (bounded document chase), G15 (integration failures have a lane), and
G16 (terminal states with retention clocks).

What it provides
----------------

* ``process.exception`` — the exception queue. Every module writes here
  when something goes wrong. Classifications: integration / data / process /
  dispute / regulatory. Every exception has an owner, a clock, a retry
  counter, and a status (open / in_progress / resolved / escalated /
  sealed).

* ``process.dlq`` — the dead-letter queue for integration calls that
  have exhausted their retries. A DLQ entry is an exception of
  classification='integration' with state='dead_letter'. **A failed
  integration never reads as a clear result.** This is the Wave 1 exit
  gate.

* ``process.idempotency`` — every integration call carries a key.
  Re-execution with the same key returns the prior result, not a
  duplicate. Required by the brief §14 platform services.

* ``process.sla`` — SLA clocks with named escalation rules. The clock
  starts at the configured trigger and escalates on breach.

* Mixins:
  - ``sgc.process.fail_closed`` — a consumer-side mixin that *blocks*
    state transitions unless an integration call has explicitly returned
    ``CLEARED``. Missing / failed calls are treated as BLOCKED, not
    ALLOW. Three outcomes only: CLEARED / BLOCKED / INDETERMINATE.
    INDETERMINATE behaves as BLOCKED.

Architecture
------------

1. Every integration call goes through ``process.idempotency.with_key()``.
2. Retries use exponential backoff up to ``max_retries`` (default 3).
3. On exhaustion, the call is parked in ``process.dlq`` and an alert is
   raised via ``process.exception``.
4. The consumer's mixin reads the DLQ + exception state. A missing record
   or ``INDETERMINATE`` result is BLOCKED. The downstream code path is
   technically impossible to execute.

Wave 1 exit gate
----------------

A deliberately failed screening call lands in the DLQ, raises an alert,
and is visibly *not* a clear result. The test
``test_exit_gate_failed_screening_is_not_clear`` in
``tests/test_process_control.py`` proves this. It is the single most
dangerous failure mode in the entire chain.

Hard rules
----------

1. **No silent failure.** A failed integration call must produce a DLQ
   entry, an alert, and a visible "INDETERMINATE" state on the
   consumer-side mixin.
2. **Fail closed.** INDETERMINATE == BLOCKED. Missing record == BLOCKED.
3. **No HELD / UNRESOLVED module in depends.** This module depends only
   on ``base`` and ``mail``.
4. **All exceptions carry a retention clock.** Resolved exceptions are
   retained for the period defined in the rules pack
   (``aml_retention_years``); sealed exceptions are retained longer if
   regulator-mandated.
    """,
}
