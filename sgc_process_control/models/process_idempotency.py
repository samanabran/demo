# -*- coding: utf-8 -*-
# Part of SGC Process Control.
"""Idempotency keys.

Every integration call carries a key. Re-execution with the same key returns
the prior result instead of duplicating side effects. TTL prevents the table
from growing unbounded.

The brief §14 platform services require idempotency on every integration
to prevent duplicate listings, receipts, and commission entitlements.
"""

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


# Default TTL. Consumer code can pass a different value per call.
DEFAULT_TTL_DAYS = 7


class ProcessIdempotency(models.Model):
    _name = "process.idempotency"
    _description = "Process Idempotency Key"
    _order = "created_at desc, id desc"
    _rec_name = "key"

    key = fields.Char(required=True, index=True)
    target_system = fields.Char(required=True, index=True)
    operation = fields.Char(required=True, index=True)

    # --- Result cache ----------------------------------------------------

    status = fields.Selection(
        selection=[
            ("pending", "Pending — first attempt in flight"),
            ("succeeded", "Succeeded — result captured"),
            ("failed", "Failed — last attempt failed; retry via new key"),
            ("dead_letter", "Dead-letter — see process.dlq"),
        ],
        required=True, default="pending", index=True,
    )
    result_payload = fields.Text(
        help="Serialised result on success.",
    )

    # --- Timing ----------------------------------------------------------

    created_at = fields.Datetime(
        required=True, default=fields.Datetime.now,
    )
    expires_at = fields.Datetime(required=True)
    completed_at = fields.Datetime()

    _sql_constraints = [
        ("key_target_op_uniq",
         "UNIQUE(key, target_system, operation)",
         "Idempotency key must be unique per (target_system, operation)."),
    ]

    # --- API -------------------------------------------------------------

    @api.model
    def get_or_create(self, key, target_system, operation, ttl_days=None):
        """Return (record, is_new).

        If the key already exists and is not expired, the existing record
        is returned. Otherwise a new pending record is created.
        """
        existing = self.search([
            ("key", "=", key),
            ("target_system", "=", target_system),
            ("operation", "=", operation),
        ], limit=1)
        if existing:
            if existing.expires_at and existing.expires_at < fields.Datetime.now():
                # Expired — treat as new.
                existing.unlink()
            else:
                return existing, False
        ttl = ttl_days if ttl_days is not None else DEFAULT_TTL_DAYS
        rec = self.create({
            "key": key,
            "target_system": target_system,
            "operation": operation,
            "expires_at": fields.Datetime.now() + timedelta(days=ttl),
            "status": "pending",
        })
        return rec, True

    def action_mark_succeeded(self, result_payload):
        for rec in self:
            rec.status = "succeeded"
            rec.result_payload = result_payload
            rec.completed_at = fields.Datetime.now()

    def action_mark_failed(self):
        for rec in self:
            rec.status = "failed"
            rec.completed_at = fields.Datetime.now()

    def action_mark_dead_letter(self):
        for rec in self:
            rec.status = "dead_letter"
            rec.completed_at = fields.Datetime.now()
