# -*- coding: utf-8 -*-
# Part of SGC Regulatory Rules Pack.
# See LICENSE file for full copyright and licensing details.
{
    "name": "SGC Regulatory Rules Pack",
    "summary": (
        "Effective-dated, jurisdiction-scoped regulatory constants. "
        "Supports the tenant's regulatory programme by holding every "
        "threshold, notice period, form name, fee rate, filing window, "
        "and retention clock as data — never in code."
    ),
    "version": "19.0.1.0.0",
    "category": "Tools / Regulatory",
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
        # Data — jurisdictions first (constants reference them)
        "data/regulatory_jurisdiction_data.xml",
        # Constants data — Dubai only at Wave 1 exit (per Q1)
        "data/regulatory_constant_dubai_aml_data.xml",
        "data/regulatory_constant_dubai_real_estate_data.xml",
        # E-invoicing (per amendment 001 §10.5)
        "data/regulatory_constant_einvoicing_data.xml",
        # Primary-source guidance references (per amendment §10 item 4)
        "data/regulatory_constant_uae_guidance_data.xml",
        # Views
        "views/regulatory_jurisdiction_views.xml",
        "views/regulatory_constant_views.xml",
        "views/regulatory_constant_template_views.xml",
        "views/regulatory_menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "sequence": 50,
    "description": """
SGC Regulatory Rules Pack
========================

The single source of truth for every regulatory constant referenced by the
real-estate workflow. Closes G24 of the programme gap register.

Architecture
------------

Two models:

* ``regulatory.jurisdiction`` — the catalogue of jurisdictions in scope
  (Dubai populated at Wave 1 exit; Abu Dhabi and DIFC/ADGM left as empty
  placeholder rows with ``valid_from=null`` per Q1 answer).

* ``regulatory.constant`` — an effective-dated, jurisdiction-scoped,
  source-attributed record. The model exposes a Python helper
  ``get_effective(code, jurisdiction_code, as_of)`` that returns the
  value in force at the given date.

Mandatory attributes on every constant:

* ``jurisdiction_id`` — which regulator's rule this is.
* ``code`` — the machine-readable key (e.g. ``rear_cash_threshold_aed``).
* ``value_numeric`` / ``value_text`` — one of these, depending on type.
* ``unit`` — what the value represents (AED, days, percent, …).
* ``source_url`` — primary regulator source.
* ``verified_on`` — date the rule was last verified.
* ``confidence`` — ``verified`` / ``unverified``.
* ``valid_from`` / ``valid_to`` — the effective window.
* ``version`` — increments on each revision.

Hard rules
----------

1. **No regulatory constant in code.** Every consumer reads through
   ``get_effective()``. A constants table has no executable business
   logic; consumers translate the value.

2. **Effective dating is mandatory.** Decree-Law 10/2025 (effective
   14/10/2025) replaced Decree-Law 20/2018. Cabinet Resolution 134/2025
   (in force 14/12/2025) replaced Cabinet Resolution 10/2019. A consumer
   that ignores ``as_of`` cannot prove which rule applied at the time
   of a transaction.

3. **UNVERIFIED is a real state.** When the rules pack ships an entry
   with ``confidence=unverified``, the consumer must surface that
   state. ``confidence=verified`` requires a ``source_url`` and a
   ``verified_on`` date.

4. **No held/unresolved module in depends.** This module depends only
   on ``base`` and ``mail``. Any future addition is reviewed against
   ``30_QUARANTINE/``.

5. **Migration rule.** When migrating a hard-coded constant out of an
   existing module (e.g. the AED 55,000 from ``aml_compliance``), the
   consumer's XML data file is updated to *read* the constant from
   this module via ``get_effective()``; the literal value is removed
   from the consumer's source. The constant's first record in this
   module carries a ``supersedes_value`` reference to the literal that
   was removed.

Migration status
----------------

* AED 55,000 REAR cash threshold — migrated from
  ``aml_compliance/reports/goaml_report_print.xml`` (Wave 1, item 1).
* Dubai Smart Rental Index vs RERA slab — entries seeded (G25).
* Dubai Trakheesi Form A, Ejari, Oqood, Mollak — entries seeded
  (G10, G11, G12, G14).

Pending migrations (Wave 2 onwards):

* Penalties ceiling (AED 100m) under Decree-Law 10/2025.
* FIU suspension period (10 days).
* Retention clock (5 years) per record type — moves to
  ``sgc_process_control`` retention framework (Wave 1, item 3).
* Rent notice periods (90 / 365 days).
* E-invoicing constants (Wave 6 / G26).
    """,
}
