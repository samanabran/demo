# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import secrets


class PortalConnector(models.Model):
    _name = "portal.connector"
    _description = "Property Portal Connector"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    code = fields.Selection(
        [
            ("bayut", "Bayut"),
            ("dubizzle", "Dubizzle"),
            ("property_finder", "Property Finder"),
            ("houza", "Houza"),
            ("property_monitor", "Property Monitor"),
            ("custom", "Custom Portal"),
        ],
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    sync_frequency = fields.Selection(
        [
            ("realtime", "Real-time"),
            ("15min", "Every 15 Minutes"),
            ("30min", "Every 30 Minutes"),
            ("hourly", "Hourly"),
            ("daily", "Daily"),
            ("manual", "Manual Only"),
        ],
        default="manual",
        required=True,
        tracking=True,
    )
    xml_feed_token = fields.Char(
        default=lambda self: secrets.token_urlsafe(32),
        copy=False,
        tracking=False,  # SECURITY: Never track tokens in chatter
        groups="sgc_offplan_rental_property_management.group_portal_admin",
        help="Security token required to access the XML feed. Keep this confidential.",
    )
    token_last_used = fields.Datetime(readonly=True, help="Last time the feed was accessed")
    token_usage_count = fields.Integer(readonly=True, default=0, help="Number of times feed accessed")
    xml_feed_url = fields.Char(
        compute="_compute_xml_feed_url",
        store=True,
        groups="sgc_offplan_rental_property_management.group_portal_admin",
        help="Contains the feed token in the query string. Keep this confidential.",
    )

    api_key = fields.Char(groups="sgc_offplan_rental_property_management.group_portal_admin")
    api_secret = fields.Char(groups="sgc_offplan_rental_property_management.group_portal_admin")
    api_endpoint = fields.Char()

    last_sync_date = fields.Datetime(readonly=True, tracking=True)
    last_sync_status = fields.Selection(
        [
            ("success", "Success"),
            ("partial", "Partial Success"),
            ("failed", "Failed"),
            ("pending", "Pending"),
        ],
        readonly=True,
    )
    last_sync_message = fields.Text(readonly=True)

    listing_line_ids = fields.One2many(
        "property.portal.line",
        "portal_id",
        string="Listings",
    )
    log_ids = fields.One2many(
        "portal.sync.log",
        "portal_id",
        string="Sync Logs",
    )

    _check_connector_unique = models.Constraint(
        'unique(code, company_id)',
        'Connector per portal per company must be unique.',
    )

    @api.depends("xml_feed_token", "code", "company_id")
    def _compute_xml_feed_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", default="")
        for record in self:
            if base_url and record.xml_feed_token:
                record.xml_feed_url = "%s/portal-feed/%s?token=%s" % (
                    base_url.rstrip("/"), record.code or "custom", record.xml_feed_token
                )
            else:
                record.xml_feed_url = False

    @api.constrains("xml_feed_token")
    def _check_token_length(self):
        for record in self:
            if record.xml_feed_token and len(record.xml_feed_token) < 16:
                raise ValidationError(_("Feed token is too short."))
