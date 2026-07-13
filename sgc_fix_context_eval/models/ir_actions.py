# -*- coding: utf-8 -*-
"""
Permanent model-level fix for client-side context evaluation errors.

Overrides `write()` and `create()` on models whose context/domain fields
are evaluated by the JavaScript browser client (not the Python server).

When the Odoo web client evaluates expressions like:

    {"default_company_id": uid and user.company_id.id}

the `user` variable does not exist in the browser evaluation context.
The `user` object is a server-side concept (res.users).

This module replaces known broken patterns with browser-safe equivalents
at write time, so the data stored in the database is already correct.
"""
import logging
import re

from odoo import api, models

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared sanitisation logic
# ---------------------------------------------------------------------------

# Patterns that are safe to evaluate in the browser vs. server-only ones:
REPLACEMENTS = [
    # user.company_id.id → first active company id (browser-safe)
    (re.compile(r"""user\.company_id\.id"""), "allowed_company_ids[0]"),
    # user.company_id → first active company id (browser-safe)
    (re.compile(r"""user\.company_id"""), "allowed_company_ids[0]"),
]

# user.X patterns that should NEVER reach the client (for warning-only)
USER_DOT_PATTERN = re.compile(r"""\buser\.\w+""")


def _sanitize_expr(value):
    """Replace known server-side-only patterns with browser-safe equivalents.

    Returns (patched_string, changed_bool). Non-strings pass through unchanged.
    """
    if not value or not isinstance(value, str):
        return value, False
    result = value
    changed = False
    for pattern, replacement in REPLACEMENTS:
        result, n = pattern.subn(replacement, result)
        if n:
            changed = True
            _logger.info(
                "  _sanitize_expr: replaced %d occurrence(s) of %r with %r",
                n, pattern.pattern, replacement,
            )
    return result, changed


def _warn_remaining_user_refs(value, label=""):
    """Log a warning if *value* still contains user. references."""
    if not value or not isinstance(value, str):
        return
    remaining = sorted(set(USER_DOT_PATTERN.findall(value)))
    if remaining:
        _logger.warning(
            "  %s — expression still contains server-side-only refs: %s",
            label, remaining,
        )


# ---------------------------------------------------------------------------
# ir.actions.act_window — context & domain are evaluated in the browser
# ---------------------------------------------------------------------------

class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def write(self, vals):
        _sanitize_act_window_vals(vals, self._name)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _sanitize_act_window_vals(vals, self._name)
        return super().create(vals_list)


# ---------------------------------------------------------------------------
# ir.ui.menu — context is evaluated in the browser
# ---------------------------------------------------------------------------

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def write(self, vals):
        _sanitize_menu_vals(vals, self._name)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _sanitize_menu_vals(vals, self._name)
        return super().create(vals_list)


# ---------------------------------------------------------------------------
# Field-level sanitizers (shared between write & create)
# ---------------------------------------------------------------------------

def _sanitize_act_window_vals(vals, model_name):
    """Sanitize context and domain on ir.actions.act_window writes."""
    for field in ('context', 'domain'):
        if field not in vals:
            continue
        original = vals[field]
        sanitized, changed = _sanitize_expr(original)
        if changed:
            vals[field] = sanitized
            _logger.info(
                "%s write/create: sanitized %s (was %r)",
                model_name, field, original,
            )
        _warn_remaining_user_refs(
            vals.get(field, original),
            f"{model_name}.{field}",
        )


def _sanitize_menu_vals(vals, model_name):
    """Sanitize context on ir.ui.menu writes."""
    if 'context' not in vals:
        return
    original = vals['context']
    sanitized, changed = _sanitize_expr(original)
    if changed:
        vals['context'] = sanitized
        _logger.info(
            "%s write/create: sanitized context (was %r)",
            model_name, original,
        )
    _warn_remaining_user_refs(
        vals.get('context', original),
        f"{model_name}.context",
    )
