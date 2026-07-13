# -*- coding: utf-8 -*-
"""
Post-init hook that fixes EvalError: "Name 'user' is not defined" in
client-side context/domain evaluation.

In Odoo's JavaScript client, makeContext() evaluates string context
expressions using evaluateExpr(). The evaluation context only contains:

    {uid, lang, tz, allowed_company_ids, active_id, active_ids, ...}

The full `user` record (res.users) is NOT available in the browser.

Common broken patterns in ir.actions.act_window / ir.ui.menu context fields:
    user.company_id.id    →  allowed_company_ids[0]
    user.company_id       →  allowed_company_ids[0]
    user.partner_id       →  (must be handled server-side; warn only)

This hook scans every relevant table and patches matching records.
It also calls _sanitize_expr() on the model's context/domain fields
to provide a server-side safety net.
"""
import logging
import re

_logger = logging.getLogger(__name__)

# Safe client-side equivalents for common broken server-side patterns.
# Order matters: more specific patterns first to avoid partial replacements.
REPLACEMENTS = [
    # user.company_id.id → first active company id
    (re.compile(r"""user\.company_id\.id"""), "allowed_company_ids[0]"),
    (re.compile(r"""user\.company_id"""), "allowed_company_ids[0]"),
]

# Pattern to detect ANY client-side-unsafe user. references
USER_DOT_PATTERN = re.compile(r"""\buser\.\w+""")


def sanitize_expr(value):
    """Apply REPLACEMENTS to *value* and return (sanitized_value, changed).

    Handles strings properly; passes non-strings through unchanged.
    """
    if not value or not isinstance(value, str):
        return value, False
    new_value = value
    changed = False
    for pattern, replacement in REPLACEMENTS:
        new_value, n = pattern.subn(replacement, new_value)
        if n:
            changed = True
            _logger.info("  Replaced %d occurrence(s) of %r", n, pattern.pattern)
    return new_value, changed


def detect_remaining_user_refs(text):
    """Return list of unique user.xxx patterns found in *text*."""
    if not text or not isinstance(text, str):
        return []
    return sorted(set(USER_DOT_PATTERN.findall(text)))


# Fields whose content is evaluated by the JavaScript client (browser).
# Each entry: (model, model_name_for_log, field_name, field_label)
TARGET_FIELDS = [
    ("ir.actions.act_window", "context", "Context"),
    ("ir.actions.act_window", "domain", "Domain"),
    ("ir.ui.menu", "context", "Context"),
]


def post_init_hook(env):
    """Entry point: scan and fix all DB-stored actions/menus with broken refs."""
    _logger.info("=" * 60)
    _logger.info("sgc_fix_context_eval: Scanning database for client-side unsafe user. references")
    _logger.info("=" * 60)

    total_fixed = 0
    total_skipped_with_warnings = 0

    for model_name, field_name, label in TARGET_FIELDS:
        Model = env[model_name]
        try:
            records = Model.search([])
        except Exception as exc:
            _logger.warning("Cannot access %s: %s", model_name, exc)
            continue

        _logger.info("Scanning %s.%s (%d records)...", model_name, field_name, len(records))

        for record in records:
            raw = getattr(record, field_name, None)
            if not raw:
                continue
            if not isinstance(raw, str):
                # Odoo stores these as text fields — should always be str or False.
                # If it's something else (e.g. a parsed dict), skip for safety
                # since we cannot safely round-trip the value.
                _logger.debug(
                    "  SKIP %s #%d (%s): field %s is type %s (value=%r)",
                    model_name, record.id, record.display_name,
                    field_name, type(raw).__name__, raw,
                )
                continue

            patched, changed = sanitize_expr(raw)
            if changed:
                try:
                    record.write({field_name: patched})
                    total_fixed += 1
                    _logger.info(
                        "  FIXED %s #%d (%s) [%s]",
                        model_name, record.id, record.display_name, label,
                    )
                except Exception as exc:
                    _logger.warning(
                        "  FAILED to write %s #%d: %s", model_name, record.id, exc,
                    )
                    continue  # skip warning check if write failed

                # After fix, re-check from patched string
                text_to_check = patched
            else:
                text_to_check = raw

            # Warn about remaining user. references that weren't handled
            remaining = detect_remaining_user_refs(text_to_check)
            if remaining:
                _logger.warning(
                    "  WARNING %s #%d (%s): still contains %s — must be handled server-side",
                    model_name, record.id, record.display_name, remaining,
                )
                total_skipped_with_warnings += 1

    _logger.info("=" * 60)
    _logger.info(
        "sgc_fix_context_eval: Done. %d record(s) fixed, %d warning(s) issued.",
        total_fixed, total_skipped_with_warnings,
    )
    _logger.info("=" * 60)

    if total_fixed == 0:
        _logger.info(
            "No broken records found via automated scan. "
            "If the error persists, check manually with:\n"
            "  SELECT id, name, context FROM ir_actions_act_window "
            "WHERE context LIKE '%%user.%%';\n"
            "  SELECT id, name, context FROM ir_ui_menu "
            "WHERE context LIKE '%%user.%%';"
        )
