# -*- coding: utf-8 -*-
"""Delete orphaned DB-only property.details kanban views that reference the
removed pre-Odoo-17 ``kanban_getcolor`` QWeb helper. The module now owns a
canonical XML-defined kanban, so these orphaned views are safe to remove.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        DELETE FROM ir_ui_view v
        WHERE v.model = 'property.details'
          AND v.type = 'kanban'
          AND v.arch_db::text LIKE '%%kanban_getcolor%%'
          AND NOT EXISTS (
              SELECT 1 FROM ir_model_data d
              WHERE d.model = 'ir.ui.view' AND d.res_id = v.id
          )
    """)
    _logger.info(
        "Removed %d orphaned property.details kanban view(s) referencing kanban_getcolor",
        cr.rowcount,
    )
