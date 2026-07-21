# (c) SGC TECH AI
# License: OPL-1
# See LICENSE in root directory.
"""SGC Tech AI Enterprise Application Launcher — persistence models.

Two small persisted records back the launcher's user-driven features:

* ``sgc.launcher.favorite`` — pinned apps in user-defined order, backing the
  Favorites section and drag-to-reorder UX.
* ``sgc.launcher.usage`` — incremented frequency counter backing the
  Frequently Used section. Writes are debounced client-side and fire-and-forget
  post-navigation; the table is capped at 50 rows per user via a daily cron
  (see ``models/launcher.py::_cron_prune_usage``).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from odoo import api, fields, models


class SgcLauncherFavorite(models.Model):
    """A single pinned application for a single user, ordered by ``sequence``.

    Mirrors Odoo's standard Sequence-field favorite/ordering pattern. Keeping
    it as its own model (rather than a vanilla ``Many2many``) is what makes
    drag-reorder survive a reload.
    """

    _name = "sgc.launcher.favorite"
    _description = "SGC Launcher — Pinned Application"
    _order = "sequence, id"
    _rec_name = "menu_id"

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        ondelete="cascade",
        index=True,
        default=lambda self: self.env.user,
    )
    menu_id = fields.Integer(
        required=True,
        index=True,
        help="``ir.ui.menu`` id this favorite refers to.",
    )
    sequence = fields.Integer(
        required=True,
        default=10,
        index=True,
        help="Drag-to-reorder target: lower values sort first. Step of 10 leaves "
             "room for in-between inserts without renumbering the whole list.",
    )

    _user_menu_uniq = models.Constraint(
        'unique(user_id, menu_id)',
        'Each application can be pinned at most once per user.',
    )


class SgcLauncherUsage(models.Model):
    """A frequency counter for a single user/app pair.

    The Launcher client sends a debounced ``increment_use`` RPC after each
    navigation begins (never blocks the click). A daily cron prunes each
    user's table to the top 50 rows by ``use_count``.
    """

    _name = "sgc.launcher.usage"
    _description = "SGC Launcher — Application Use Counter"
    _order = "use_count desc, last_used desc"
    _rec_name = "menu_id"

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        ondelete="cascade",
        index=True,
    )
    menu_id = fields.Integer(
        required=True,
        index=True,
        help="``ir.ui.menu`` id this counter refers to.",
    )
    use_count = fields.Integer(
        required=True,
        default=1,
        help="Total number of times the user has selected this app.",
    )
    last_used = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        help="Last time the user selected this app.",
    )

    _user_menu_uniq = models.Constraint(
        'unique(user_id, menu_id)',
        'One counter row per (user, app) pair.',
    )

    # ------------------------------------------------------------------
    # Client-facing helpers
    # ------------------------------------------------------------------

    @api.model
    def increment_use(self, menu_ids):
        """Increment use_count for the calling user/app set.

        Idempotent on missing rows. Called by the Launcher client via
        :func:`rpc` *after* navigation has begun — failure must be silent
        (the caller should not await, and any exception is swallowed).

        :param menu_ids: iterable of ``ir.ui.menu`` ids to increment.
        """
        now = fields.Datetime.now()
        rows = self.search(
            [("user_id", "=", self.env.user.id), ("menu_id", "in", list(menu_ids))],
        )
        existing = {row.menu_id: row for row in rows}
        to_create = [
            {
                "user_id": self.env.user.id,
                "menu_id": menu_id,
                "use_count": 1,
                "last_used": now,
            }
            for menu_id in menu_ids
            if menu_id not in existing
        ]
        if to_create:
            self.create(to_create)
        for row in rows:
            row.write({"use_count": row.use_count + 1, "last_used": now})
        return True

    # ------------------------------------------------------------------
    # Daily cron: prune each user to the top 50 rows by use_count
    # ------------------------------------------------------------------

    @api.model
    def _cron_prune_usage(self):
        """Drop everything past the top 50 rows per user.

        Runs from ``ir.cron`` once per day. We pick the 50 highest-use_count
        rows per user and delete everything else for the same user.
        """
        # Identify candidate survivors in one query, then delete the rest.
        self.env.cr.execute(
            """
            DELETE FROM sgc_launcher_usage u
            WHERE id IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY user_id ORDER BY use_count DESC, last_used DESC
                           ) AS rn
                    FROM sgc_launcher_usage
                ) t
                WHERE rn > 50
            )
            """
        )
        return True
