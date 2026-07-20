# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, timedelta


class PropertyImages(models.Model):
    _name = 'property.images'
    _description = 'Property Images (legacy — use property.image for new galleries)'
    _order = 'sequence, id'

    name = fields.Char(string='Title', default='Property Image')
    sequence = fields.Integer(string='Sequence', default=0)
    image = fields.Binary(string='Image', attachment=True)
    property_id = fields.Many2one(
        'property.details',
        string='Property',
        required=True,
        ondelete='cascade',
    )


class PropertyDetails(models.Model):
    _name = 'property.details'
    _description = 'Property Details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Property Name', required=True)
    property_code = fields.Char(string='Property Code')
    property_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('land', 'Land'),
    ], string='Property Type', default='residential')
    region_id = fields.Many2one('property.region', string='Region', index=True)
    project_id = fields.Many2one('property.project', string='Project', index=True)
    sub_project_id = fields.Many2one('property.sub.project', string='Sub Project', index=True)
    address = fields.Text(string='Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string='ZIP')
    area = fields.Float(string='Area (sq ft)')
    bedrooms = fields.Integer(string='Bedrooms')
    bathrooms = fields.Integer(string='Bathrooms')
    sale_price = fields.Monetary(string='Sale Price', currency_field='currency_id')
    rent_price = fields.Monetary(string='Rent Price', currency_field='currency_id')
    price = fields.Monetary(string='Price', currency_field='currency_id')
    dld_fee = fields.Monetary(string='DLD Fee', currency_field='currency_id')
    dld_fee_percentage = fields.Float(string='DLD Fee %', default=4.0)
    # UAE-standard document identifiers (Makani/DEWA/Title Deed) — used by the
    # Ejari-style rental contract report and the resale purchase agreement.
    # Added for report field coverage; not yet exposed on any form view.
    makani_number = fields.Char(string='Makani Number')
    dewa_premises_number = fields.Char(string='DEWA Premises Number')
    title_deed_number = fields.Char(string='Title Deed Number')
    admin_fee = fields.Monetary(string='Admin Fee', currency_field='currency_id')
    admin_fee_percentage = fields.Float(string='Admin Fee %', default=2.0)
    is_maintenance_service = fields.Boolean(string='Maintenance Service', default=False)
    total_maintenance = fields.Monetary(string='Total Maintenance', currency_field='currency_id')
    is_extra_service = fields.Boolean(string='Extra Service', default=False)
    extra_service_cost = fields.Monetary(string='Extra Service Cost', currency_field='currency_id')
    total_customer_obligation = fields.Monetary(string='Total Customer Obligation', currency_field='currency_id')

    is_payment_plan = fields.Boolean(string='Payment Plan', default=False)
    payment_schedule_id = fields.Many2one('payment.schedule', string='Payment Schedule')
    booking_percentage = fields.Float(string='Booking %', default=10.0)
    booking_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ], string='Booking Type', default='percentage')
    sold_booking_id = fields.Many2one('property.vendor', string='Sold Booking')
    property_vendor_ids = fields.One2many('property.vendor', 'property_id', string='Bookings/Contracts')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    owner_id = fields.Many2one('res.partner', string='Owner')
    landlord_id = fields.Many2one('res.partner', string='Landlord')
    state = fields.Selection([
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
        ('maintenance', 'Under Maintenance'),
    ], string='Status', default='available', tracking=True)
    sale_lease = fields.Selection([
        ('sale', 'Sale'),
        ('lease', 'Lease'),
        ('both', 'Both'),
    ], string='Sale/Lease')
    active = fields.Boolean(string='Active', default=True)
    is_published_website = fields.Boolean(string='Published on Website', default=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    description = fields.Text(string='Description')
    amenity_ids = fields.Many2many(
        'property.amenities',
        'property_details_amenity_rel',
        'property_id', 'amenity_id',
        string='Amenities',
    )
    connectivity_ids = fields.Many2many(
        'property.connectivity',
        'property_details_connectivity_rel',
        'property_id', 'connectivity_id',
        string='Nearby Connectivity',
    )
    maintenance_count = fields.Integer(string='Maintenance Requests', compute='_compute_maintenance_count')
    document_count = fields.Integer(string='Documents', compute='_compute_document_count')

    # ------------------------------------------------------------------
    # Main image (hero / form avatar)
    # ------------------------------------------------------------------
    image_1920 = fields.Binary(string='Image (1920px)', attachment=True)
    image_1024 = fields.Binary(string='Image (1024px)', compute='_compute_property_images', store=True, attachment=True)
    image_512 = fields.Binary(string='Image (512px)', compute='_compute_property_images', store=True, attachment=True)
    image_256 = fields.Binary(string='Image (256px)', compute='_compute_property_images', store=True, attachment=True)

    @api.depends('image_1920')
    def _compute_property_images(self):
        for rec in self:
            rec.image_1024 = rec.image_1920
            rec.image_512 = rec.image_1920
            rec.image_256 = rec.image_1920

    # ------------------------------------------------------------------
    # RERA / DLD COMPLIANCE FIELDS
    # ------------------------------------------------------------------
    trakheesi_permit_number = fields.Char(
        string="Trakheesi Permit #", size=50,
        help="DLD/RERA Trakheesi permit number required for all property listings")
    permit_issue_date = fields.Date(string="Permit Issue Date")
    permit_expiry_date = fields.Date(
        string="Permit Expiry Date",
        help="Trakheesi permits typically valid for 90 days")
    permit_status = fields.Selection([
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
        ('revoked', 'Revoked'),
    ], string="Permit Status", default='pending')
    rera_form_a_ref = fields.Many2one(
        'rera.form.a', string="RERA Form A",
        help="Linked Form A listing agreement")
    owner_noc_date = fields.Date(
        string="Owner NOC Date",
        help="Date of No Objection Certificate from owner")
    owner_noc_document = fields.Many2one(
        'property.documents', string="Owner NOC Document")
    portal_ready = fields.Boolean(
        compute='_compute_portal_ready', string="Portal Ready",
        help="All compliance checks passed")
    portal_compliance_errors = fields.Text(
        string="Compliance Errors",
        help="Description of what's blocking portal publishing")
    title_deed_verified = fields.Boolean(
        string="Title Deed Verified",
        help="Title deed has been verified against DLD")
    title_deed_verified_by = fields.Many2one(
        'res.users', string="Verified By")
    title_deed_verified_date = fields.Date(string="Verification Date")

    # ------------------------------------------------------------------
    # Contract smart-button counts
    # ------------------------------------------------------------------
    sale_contract_count = fields.Integer(
        string='Sale Contracts',
        compute='_compute_sale_contract_count',
    )
    rent_contract_count = fields.Integer(
        string='Rent Contracts',
        compute='_compute_rent_contract_count',
    )
    tenancy_details_count = fields.Integer(
        string='Tenancy Details',
        compute='_compute_tenancy_details_count',
    )
    property_vendor_count = fields.Integer(
        string='Vendor/Booking Records',
        compute='_compute_property_vendor_count',
    )

    def _compute_sale_contract_count(self):
        for rec in self:
            rec.sale_contract_count = self.env['sale.contract'].search_count(
                [('property_id', '=', rec.id)])

    def _compute_rent_contract_count(self):
        for rec in self:
            rec.rent_contract_count = self.env['rent.contract'].search_count(
                [('property_id', '=', rec.id)])

    def _compute_tenancy_details_count(self):
        for rec in self:
            rec.tenancy_details_count = self.env['tenancy.details'].search_count(
                [('property_id', '=', rec.id)])

    def _compute_property_vendor_count(self):
        for rec in self:
            rec.property_vendor_count = self.env['property.vendor'].search_count(
                [('property_id', '=', rec.id)])

    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = self.env['maintenance.request'].search_count(
                [('property_id', '=', rec.id)])

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = self.env['property.documents'].search_count(
                [('property_id', '=', rec.id)])

    @api.depends('trakheesi_permit_number', 'permit_expiry_date',
                 'title_deed_number', 'owner_id',
                 'portal_line_ids')
    def _compute_portal_ready(self):
        for rec in self:
            errors = []
            # Check 1: trakheesi_permit_number is set and not expired
            if not rec.trakheesi_permit_number:
                errors.append("Trakheesi Permit Number is missing")
            elif rec.permit_expiry_date and rec.permit_expiry_date < date.today():
                errors.append("Trakheesi Permit has expired")
                if rec.permit_status != 'revoked':
                    rec.permit_status = 'expired'

            # Check 2: title_deed_number or oqood number is present
            if not rec.title_deed_number:
                errors.append("Title Deed Number is missing")

            # Check 3: At least one valid document of category 'title_deed' or 'oqood'
            has_valid_doc = False
            try:
                for doc in self.env['property.documents'].search([
                    ('property_id', '=', rec.id),
                    '|', ('doc_category', '=', 'title_deed'),
                    ('doc_category', '=', 'oqood'),
                ]):
                    has_valid_doc = True
                    break
            except Exception:
                pass
            if not has_valid_doc:
                errors.append("No valid Title Deed or Oqood document on file")

            # Check 4: owner_id is set
            if not rec.owner_id:
                errors.append("Property Owner is not set")

            # Check 5: portal listings exist
            has_portal_docs = False
            try:
                if rec.portal_line_ids:
                    has_portal_docs = True
            except Exception:
                pass
            if not has_portal_docs:
                errors.append("No portal listings configured")

            rec.portal_ready = len(errors) == 0
            rec.portal_compliance_errors = "\n".join(errors) if errors else False

    @api.onchange('trakheesi_permit_number')
    def _onchange_trakheesi_permit_number(self):
        if self.trakheesi_permit_number:
            today = date.today()
            self.permit_issue_date = today
            self.permit_expiry_date = today + timedelta(days=90)
            self.permit_status = 'valid'

    def action_open_rera_form_a(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'RERA Form A',
            'res_model': 'rera.form.a',
            'view_mode': 'form',
            'res_id': self.rera_form_a_ref.id,
            'target': 'current',
        }

    def action_view_sale_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Contracts',
            'res_model': 'sale.contract',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_view_rent_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rent Contracts',
            'res_model': 'rent.contract',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_publish(self):
        for rec in self:
            rec.is_published_website = True

    def action_unpublish(self):
        for rec in self:
            rec.is_published_website = False

    def action_archive(self):
        for rec in self:
            rec.active = False

    def action_unarchive(self):
        for rec in self:
            rec.active = True

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Requests',
            'res_model': 'maintenance.request',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Property Documents',
            'res_model': 'property.documents',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_print_brochure(self):
        self.ensure_one()
        return self.env.ref(
            'sgc_offplan_rental_property_management.action_report_property_brochure'
        ).report_action(self)

    def action_create_sale_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Sale Contract',
            'res_model': 'sale.contract',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_property_id': self.id,
                'default_seller_id': self.owner_id.id if self.owner_id else False,
                'default_sale_price': self.sale_price or self.price or 0,
                'default_currency_id': self.currency_id.id if self.currency_id else self.company_id.currency_id.id,
                'default_payment_schedule_id': self.payment_schedule_id.id if self.payment_schedule_id else False,
                'default_company_id': self.company_id.id,
            },
        }

    def action_create_rent_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Rent Contract',
            'res_model': 'rent.contract',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_property_id': self.id,
                'default_landlord_id': self.landlord_id.id if self.landlord_id else False,
                'default_rent_amount': self.rent_price or 0,
                'default_currency_id': self.currency_id.id if self.currency_id else self.company_id.currency_id.id,
                'default_payment_schedule_id': self.payment_schedule_id.id if self.payment_schedule_id else False,
                'default_company_id': self.company_id.id,
            },
        }

    def action_create_booking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Booking / Hold',
            'res_model': 'property.vendor',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_property_id': self.id,
                'default_vendor_id': self.owner_id.id if self.owner_id else False,
                'default_sale_price': self.sale_price or self.price or 0,
                'default_currency_id': self.currency_id.id if self.currency_id else self.company_id.currency_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    # ------------------------------------------------------------------
    # Dashboard API
    # ------------------------------------------------------------------
    @api.model
    def get_property_stats(self):
        """Aggregated KPIs for the SGC Real Estate Executive Dashboard."""
        company_domain = [('company_id', 'in', self.env.companies.ids)]
        currency_symbol = self.env.company.currency_id.symbol or ''

        # property state breakdown
        state_groups = self.env['property.details'].sudo()._read_group(
            company_domain, groupby=['state'], aggregates=['__count'])
        state_counts = {state: count for state, count in state_groups}

        # property type breakdown
        type_groups = self.env['property.details'].sudo()._read_group(
            company_domain, groupby=['property_type'], aggregates=['__count'])
        type_counts = {property_type: count for property_type, count in type_groups}

        total_property = sum(type_counts.values())
        avail_property = state_counts.get('available', 0)
        sold_property = state_counts.get('sold', 0)
        rented_property = state_counts.get('rented', 0)
        maintenance_property = state_counts.get('maintenance', 0)

        # tenancy contracts
        try:
            contract_groups = self.env['tenancy.details'].sudo()._read_group(
                company_domain, groupby=['contract_type'], aggregates=['__count'])
            contract_counts = {contract_type: count for contract_type, count in contract_groups}
        except Exception:
            contract_counts = {}
        draft_contract = contract_counts.get('new_contract', 0)
        running_contract = contract_counts.get('running_contract', 0)
        expire_contract = contract_counts.get('expire_contract', 0)
        close_contract = contract_counts.get('close_contract', 0)

        # rent bills — rent.bill is the model actually populated by the canonical
        # billing path (rent.contract.action_generate_rent_bills); rent.invoice is
        # never written by that flow, so aggregate rent.bill for the rent KPIs.
        try:
            pending_invoice = self.env['rent.bill'].sudo().search_count(
                [('payment_state', '=', 'not_paid')] + company_domain)
        except Exception:
            pending_invoice = 0
        try:
            rent_groups = self.env['rent.bill'].sudo()._read_group(
                company_domain, aggregates=['amount:sum'])
            full_tenancy_total = (rent_groups[0][0] or 0.0) if rent_groups else 0.0
        except Exception:
            full_tenancy_total = 0.0

        # Booked comes directly from property.details.state, already computed above.
        booked = state_counts.get('booked', 0)

        # sale.contract is the canonical, actively-wired sales pipeline (action_sign/
        # action_complete/action_cancel keep property.details.state in sync with it).
        # property.vendor has no view/actions reachable from the UI and is not used here.
        try:
            sale_groups = self.env['sale.contract'].sudo()._read_group(
                company_domain + [('state', '=', 'completed')],
                aggregates=['sale_price:sum'])
            sold_total = (sale_groups[0][0] or 0.0) if sale_groups else 0.0
        except Exception:
            sold_total = 0.0
        sale_sold = self.env['sale.contract'].sudo().search_count(
            [('state', '=', 'completed')] + company_domain)

        # unpaid sale invoices
        try:
            pending_invoice_sale = self.env['account.move'].sudo().search_count(
                [('sold_id', '!=', False), ('payment_state', '=', 'not_paid')] + company_domain)
        except Exception:
            pending_invoice_sale = 0

        # partners
        try:
            customer_count = self.env['res.partner'].sudo().search_count(
                [('user_type', '=', 'customer')])
            landlord_count = self.env['res.partner'].sudo().search_count(
                [('user_type', '=', 'landlord')])
        except Exception:
            customer_count = 0
            landlord_count = 0

        # geography
        region_count = self.env['property.region'].sudo().search_count([])
        project_count = self.env['property.project'].sudo().search_count(company_domain)
        try:
            subproject_count = self.env['property.sub.project'].sudo().search_count(company_domain)
        except Exception:
            subproject_count = 0

        return {
            'total_property': total_property,
            'avail_property': avail_property,
            'sold_property': sold_property,
            'rented_property': rented_property,
            'maintenance_property': maintenance_property,
            'draft_contract': draft_contract,
            'running_contract': running_contract,
            'expire_contract': expire_contract,
            'close_contract': close_contract,
            'pending_invoice': pending_invoice,
            'pending_invoice_sale': pending_invoice_sale,
            'rent_total': round(full_tenancy_total, 2),
            'sold_total': round(sold_total, 2),
            'booked': booked,
            'sale_sold': sale_sold,
            'customer_count': customer_count,
            'landlord_count': landlord_count,
            'region_count': region_count,
            'project_count': project_count,
            'subproject_count': subproject_count,
            'currency_symbol': currency_symbol,
            'property_type': [
                ['Land', 'Residential', 'Commercial', 'Industrial'],
                [type_counts.get('land', 0), type_counts.get('residential', 0),
                 type_counts.get('commercial', 0), type_counts.get('industrial', 0)],
            ],
            'property_state': [
                ['Available', 'Sold', 'Rented', 'Maintenance'],
                [avail_property, sold_property, rented_property, maintenance_property],
            ],
        }
