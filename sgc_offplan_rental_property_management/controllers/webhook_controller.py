# -*- coding: utf-8 -*-
#
# Listing Syndication — Inbound Lead Webhook
# ------------------------------------------------------------------
# This module parses inbound lead payloads from Bayut / Property Finder /
# Dubizzle style portals into `portal.lead` records.
#
# CREDENTIAL GAP (intentional, not a bug): there is no live partner
# agreement with Bayut/Property Finder/Dubizzle yet, so no real webhook
# payload spec is available. The schema below is a reasonable, generic
# assumption based on the lead fields these portals commonly send.
# Once real credentials/webhook docs are available, only
# `_parse_lead_payload` needs to change to match the real field names.
#
# ASSUMED WEBHOOK PAYLOAD SCHEMA (JSON body, sent to
# /portal-webhook/<portal_code>):
# {
#     "name": "string, required — lead's full name",
#     "email": "string, optional — validated against portal.lead's email format constraint",
#     "phone": "string, optional — validated against portal.lead's phone format constraint",
#     "property_reference": "string, optional — matched against property.details.property_code,
#                             falling back to property.portal.line.external_id for this portal,
#                             falling back to a numeric property.details id",
#     "message": "string, optional — free-text inquiry body"
# }
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class WebhookController(http.Controller):

    def _find_listing_line(self, portal, property_reference):
        """Resolve an incoming property_reference to a property.portal.line, if any."""
        if not property_reference:
            return request.env["property.portal.line"].sudo().browse()

        listing_line = request.env["property.portal.line"].sudo().search(
            [("portal_id", "=", portal.id), ("external_id", "=", property_reference)],
            limit=1,
        )
        if listing_line:
            return listing_line

        property_rec = request.env["property.details"].sudo().search(
            [("property_code", "=", property_reference)], limit=1
        )
        if not property_rec and str(property_reference).isdigit():
            property_rec = request.env["property.details"].sudo().browse(int(property_reference)).exists()

        if property_rec:
            listing_line = request.env["property.portal.line"].sudo().search(
                [("portal_id", "=", portal.id), ("property_id", "=", property_rec.id)], limit=1
            )
        return listing_line

    def _parse_lead_payload(self, portal, payload):
        """Validate/normalize the assumed payload schema. Raises ValueError on malformed input."""
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a JSON object")

        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("Missing required field: name")

        listing_line = self._find_listing_line(portal, payload.get("property_reference"))

        return {
            "name": name,
            "email": (payload.get("email") or "").strip() or False,
            "phone": (payload.get("phone") or "").strip() or False,
            "message": (payload.get("message") or "").strip() or False,
            "portal_id": portal.id,
            "listing_line_id": listing_line.id if listing_line else False,
        }

    @http.route(['/portal-webhook/<string:portal_code>'], type='jsonrpc', auth='public', csrf=False)
    def portal_webhook(self, portal_code, **payload):
        """Webhook endpoint for receiving lead data from portals"""
        # Input validation
        if not portal_code or not portal_code.replace('_', '').isalnum():
            _logger.warning(
                "Invalid portal code in webhook: %s from IP %s",
                portal_code,
                request.httprequest.remote_addr
            )
            return {"status": "error", "message": "Invalid portal code"}

        # Find portal
        portal = request.env['portal.connector'].sudo().search(
            [('code', '=', portal_code)],
            limit=1
        )

        if not portal:
            _logger.warning(
                "Unknown portal in webhook: %s from IP %s",
                portal_code,
                request.httprequest.remote_addr
            )
            return {"status": "error", "message": "Unknown portal"}

        # Log webhook receipt
        _logger.info(
            "Webhook received: portal=%s, payload_size=%d, ip=%s",
            portal_code,
            len(str(payload)),
            request.httprequest.remote_addr
        )

        try:
            lead_vals = self._parse_lead_payload(portal, payload)
            lead = request.env['portal.lead'].sudo().create(lead_vals)
        except (ValueError, ValidationError) as exc:
            request.env['portal.sync.log'].sudo().create({
                'portal_id': portal.id,
                'status': 'failed',
                'failed_count': 1,
                'message': 'Malformed webhook payload: %s' % exc,
            })
            return {"status": "error", "message": str(exc)}
        except Exception:
            _logger.exception("Unexpected error processing webhook for portal=%s", portal_code)
            request.env['portal.sync.log'].sudo().create({
                'portal_id': portal.id,
                'status': 'failed',
                'failed_count': 1,
                'message': 'Unexpected error while processing webhook payload.',
            })
            return {"status": "error", "message": "Internal error processing webhook"}

        request.env['portal.sync.log'].sudo().create({
            'portal_id': portal.id,
            'status': 'success',
            'created_count': 1,
            'message': 'Lead #%d created from webhook payload.' % lead.id,
        })

        return {
            "status": "success",
            "lead_id": lead.id,
        }
