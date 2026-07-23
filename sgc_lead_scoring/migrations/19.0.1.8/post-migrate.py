# -*- coding: utf-8 -*-
"""Post-migrate for 19.0.1.8: no data migration needed.
All new fields get safe ORM defaults on schema sync. No backfill required."""


def migrate(cr, version):
    return
