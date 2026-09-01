# -*- coding: utf-8 -*-
"""Phase 0.4 + 0.6 post-migration.

Two idempotent actions:

1. Phase 0.6 — DB-level partial unique index on trakheesi_permit_number so
   that no future code path (raw SQL, misconfigured su(), third-party
   importer) can introduce a duplicate. Empty / NULL values are allowed —
   the compliance gate fires at publish time, not save time. The format
   constraint remains in Python and reads from
   ``ir.config_parameter('sgc_offplan_rental_property_management.trakheesi_permit_format')``.

2. Phase 0.4 — Remove the two test portal.connector rows from the initial
   development cycle: ``(code='dubizzle', name='test')`` and
   ``(code='houza', name='Dubizzle -tesst')``. Legitimate client
   connectors survive because the deletion matches by ``(code, name)``
   pair, not by ``code`` alone.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # --- 0.6 partial unique index on trakheesi_permit_number --------------
    cr.execute(
        "SELECT 1 FROM pg_indexes "
        "WHERE schemaname = 'public' "
        "AND indexname = 'property_details_trakheesi_permit_uniq'"
    )
    if cr.fetchone():
        _logger.info(
            "property_details_trakheesi_permit_uniq already exists; skipping"
        )
    else:
        cr.execute(
            "CREATE UNIQUE INDEX property_details_trakheesi_permit_uniq "
            "ON property_details (trakheesi_permit_number) "
            "WHERE trakheesi_permit_number IS NOT NULL "
            "AND trakheesi_permit_number <> ''"
        )
        _logger.info(
            "Created partial unique index property_details_trakheesi_permit_uniq"
        )

    # --- 0.4 remove test portal.connector rows ----------------------------
    cr.execute(
        "DELETE FROM portal_connector "
        "WHERE (code, name) IN ("
        "  ('dubizzle', 'test'),"
        "  ('houza', 'Dubizzle -tesst')"
        ")"
    )
    _logger.info(
        "Phase 0.4: removed %d test portal.connector row(s)", cr.rowcount,
    )