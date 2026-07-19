# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyDetails(models.Model):
    _inherit = "property.details"

    is_published_portal = fields.Boolean(
        string="Published on Portal", default=False, tracking=True
    )
    portal_line_ids = fields.One2many(
        "property.portal.line", "property_id", string="Portal Listings"
    )
    portal_line_count = fields.Integer(compute="_compute_portal_counts")
    portal_lead_count = fields.Integer(compute="_compute_portal_counts")

    @api.depends("portal_line_ids")
    def _compute_portal_counts(self):
        """Compute portal and lead counts efficiently using batch queries"""
        # Batch count leads for all properties at once (prevents N+1 queries)
        lead_counts = {}
        if self:
            lead_data = self.env["portal.lead"]._read_group(
                [("property_id", "in", self.ids)],
                groupby=["property_id"],
                aggregates=["__count"],
            )
            for property_rec, count in lead_data:
                lead_counts[property_rec.id] = count
        
        for rec in self:
            rec.portal_line_count = len(rec.portal_line_ids)
            rec.portal_lead_count = lead_counts.get(rec.id, 0)

    def action_open_portal_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Portal Listings",
            "res_model": "property.portal.line",
            "view_mode": "list,form",
            "domain": [("property_id", "=", self.id)],
            "context": {"default_property_id": self.id},
            "target": "current",
        }

    def action_open_portal_leads(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Portal Leads",
            "res_model": "portal.lead",
            "view_mode": "list,form",
            "domain": [("property_id", "=", self.id)],
            "context": {"default_property_id": self.id},
            "target": "current",
        }

    def _check_portal_publish_ready(self):
        """Check if property is compliant and ready for portal publishing.

        Validates RERA permit, ownership documentation, portal-visible
        documents, owner assignment, and pricing before allowing portal
        publication. Returns a dict with ``ready`` (bool) and ``errors``
        (list of string messages).
        """
        self.ensure_one()
        errors = []

        if not self.trakheesi_permit_number:
            errors.append(_("Trakheesi permit number is required for portal listing"))
        elif self.permit_expiry_date and self.permit_expiry_date < fields.Date.today():
            errors.append(_("Trakheesi permit has expired"))

        if not self.title_deed_number:
            errors.append(_("Title deed number is required"))

        docs = self.env["property.documents"].sudo().search([
            ("property_id", "=", self.id),
            ("portal_visible", "=", True),
        ])
        if not docs:
            errors.append(_("At least one portal-visible document is required"))

        if not self.owner_id:
            errors.append(_("Property owner is required"))

        if self.sale_lease == "sale" and not self.sale_price:
            errors.append(_("Sale price is required for sale listings"))
        elif self.sale_lease == "rent" and not self.rent_price:
            errors.append(_("Rent price is required for rental listings"))

        return {"ready": len(errors) == 0, "errors": errors}

    def action_publish_portal(self):
        for rec in self:
            check = rec._check_portal_publish_ready()
            if not check["ready"]:
                raise UserError("\n".join(check["errors"]))
            rec.is_published_portal = True

    def action_unpublish_portal(self):
        for rec in self:
            rec.is_published_portal = False
