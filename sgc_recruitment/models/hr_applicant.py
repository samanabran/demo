# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class HrApplicantExtended(models.Model):
    _inherit = 'hr.applicant'
    
    # ==========================================
    # UAE OFFER LETTER REQUIRED FIELDS
    # ==========================================
    
    # Personal Information
    full_name_arabic = fields.Char(
        string='Full Name (Arabic)',
        help='Full legal name in Arabic as per Emirates ID'
    )
    
    nationality = fields.Many2one(
        'res.country',
        string='Nationality',
        required=False
    )
    
    emirates_id = fields.Char(
        string='Emirates ID',
        help='UAE Emirates ID Number (15 digits)'
    )
    
    passport_number = fields.Char(
        string='Passport Number',
        help='Valid passport number'
    )
    
    date_of_birth = fields.Date(
        string='Date of Birth',
        help='Date of birth as per passport'
    )
    
    # Contact Information
    uae_mobile = fields.Char(
        string='UAE Mobile Number',
        help='UAE mobile number with country code'
    )
    
    personal_email = fields.Char(
        string='Personal Email',
        help='Personal email address for official communication'
    )
    
    current_address = fields.Text(
        string='Current Address in UAE',
        help='Complete residential address in UAE'
    )
    
    # Employment Details
    position_title = fields.Char(
        string='Position Title',
        help='Official job title for offer letter'
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department assignment'
    )
    
    reporting_manager = fields.Many2one(
        'hr.employee',
        string='Reports To',
        help='Direct reporting manager'
    )
    
    employment_type = fields.Selection([
        ('unlimited', 'Unlimited Contract'),
        ('limited', 'Limited Contract (Fixed Term)'),
        ('part_time', 'Part-Time'),
        ('consultant', 'Consultant/Freelance')
    ], string='Employment Type', default='unlimited', required=True)
    
    contract_duration_months = fields.Integer(
        string='Contract Duration (Months)',
        help='For limited contracts only'
    )
    
    probation_period_days = fields.Integer(
        string='Probation Period (Days)',
        default=180,
        help='Probation period in days (UAE standard: 180 days)'
    )
    
    proposed_start_date = fields.Date(
        string='Proposed Start Date',
        help='Expected date of joining'
    )
    
    work_location = fields.Char(
        string='Work Location',
        default='Dubai, United Arab Emirates',
        help='Primary work location'
    )
    
    # Compensation & Benefits
    basic_salary = fields.Monetary(
        string='Basic Salary (Monthly)',
        currency_field='company_currency_id',
        help='Monthly basic salary in AED'
    )
    
    housing_allowance = fields.Monetary(
        string='Housing Allowance (Monthly)',
        currency_field='company_currency_id',
        help='Monthly housing allowance in AED'
    )
    
    transport_allowance = fields.Monetary(
        string='Transport Allowance (Monthly)',
        currency_field='company_currency_id',
        help='Monthly transport allowance in AED'
    )
    
    other_allowances = fields.Monetary(
        string='Other Allowances (Monthly)',
        currency_field='company_currency_id',
        help='Any other monthly allowances in AED'
    )
    
    total_monthly_salary = fields.Monetary(
        string='Total Monthly Salary',
        currency_field='company_currency_id',
        compute='_compute_total_salary',
        store=True,
        help='Total monthly compensation in AED'
    )
    
    annual_salary = fields.Monetary(
        string='Annual Salary',
        currency_field='company_currency_id',
        compute='_compute_total_salary',
        store=True,
        help='Total annual compensation in AED'
    )
    
    # Benefits
    annual_leave_days = fields.Integer(
        string='Annual Leave Days',
        default=30,
        help='Annual leave entitlement (UAE minimum: 30 days)'
    )
    
    health_insurance = fields.Selection([
        ('basic', 'Basic Plan'),
        ('enhanced', 'Enhanced Plan'),
        ('premium', 'Premium Plan (Family Coverage)')
    ], string='Health Insurance', default='basic')
    
    visa_provided = fields.Boolean(
        string='Visa Provided',
        default=True,
        help='Employment visa sponsored by company'
    )
    
    flight_tickets = fields.Selection([
        ('none', 'Not Provided'),
        ('annual', 'Annual Return Ticket'),
        ('biannual', 'Bi-Annual Return Tickets')
    ], string='Flight Tickets', default='annual')
    
    additional_benefits = fields.Text(
        string='Additional Benefits',
        help='Other benefits (training, gym, phone allowance, etc.)'
    )
    
    # Notice Period
    notice_period_days = fields.Integer(
        string='Notice Period (Days)',
        default=30,
        help='Notice period required for resignation'
    )
    
    # Offer Letter Details
    offer_letter_date = fields.Date(
        string='Offer Letter Date',
        default=fields.Date.today,
        help='Date of offer letter issuance'
    )
    
    offer_valid_until = fields.Date(
        string='Offer Valid Until',
        compute='_compute_offer_validity',
        store=True,
        help='Offer expiry date (14 days from issue)'
    )
    
    offer_letter_reference = fields.Char(
        string='Offer Letter Reference',
        compute='_compute_offer_reference',
        store=True,
        help='Unique offer letter reference number'
    )
    
    # Signature & Acceptance
    candidate_signature = fields.Binary(
        string='Candidate Signature',
        help='Digital signature of candidate'
    )
    
    acceptance_date = fields.Date(
        string='Acceptance Date',
        help='Date when candidate accepted the offer'
    )
    
    company_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    
    @api.depends('basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances')
    def _compute_total_salary(self):
        for record in self:
            monthly = (
                record.basic_salary + 
                record.housing_allowance + 
                record.transport_allowance + 
                record.other_allowances
            )
            record.total_monthly_salary = monthly
            record.annual_salary = monthly * 12
    
    @api.depends('offer_letter_date')
    def _compute_offer_validity(self):
        for record in self:
            if record.offer_letter_date:
                record.offer_valid_until = record.offer_letter_date + timedelta(days=14)
            else:
                record.offer_valid_until = False
    
    @api.depends('partner_name', 'create_date')
    def _compute_offer_reference(self):
        for record in self:
            if record.id and record.create_date:
                date_str = record.create_date.strftime('%Y%m%d')
                record.offer_letter_reference = f"SGO-{date_str}-{record.id:04d}"
            else:
                record.offer_letter_reference = "SGO-DRAFT-NEW"
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def action_generate_offer_letter(self):
        """Generate and download offer letter PDF"""
        self.ensure_one()
        return self.env.ref('sgc_recruitment.action_report_offer_letter').report_action(self)
    
    def action_send_offer_letter(self):
        """Send offer letter via email"""
        self.ensure_one()
        template = self.env.ref('sgc_recruitment.email_template_offer_letter')
        template.send_mail(self.id, force_send=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Offer letter sent successfully!',
                'type': 'success',
                'sticky': False,
            }
        }
