# -*- coding: utf-8 -*-
from odoo import fields, models


class XmlFeedConfig(models.Model):
    _name = "xml.feed.config"
    _description = "XML Feed Configuration"

    name = fields.Char(required=True)
    portal_id = fields.Many2one("portal.connector", required=True, ondelete="cascade")
    version = fields.Selection([
        ("v1", "Version 1"),
        ("v2", "Version 2"),
        ("v3", "Version 3"),
    ], default="v3")
    enabled = fields.Boolean(default=True)
    notes = fields.Text()
