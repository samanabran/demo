# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentSchedule(models.Model):
    _name = 'payment.schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payment Schedule Template'
    _order = 'sequence, name'
    
    name = fields.Char(string='Schedule Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    schedule_type = fields.Selection([
        ('sale', 'Sale Contract'),
        ('rental', 'Rental Contract')
    ], string='Schedule Type', required=True, default='sale')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    total_percentage = fields.Float(
        string='Total Percentage',
        compute='_compute_total_percentage',
        store=True,
        help='Must equal 100%'
    )
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    schedule_line_ids = fields.One2many('payment.schedule.line', 'schedule_id',
                                       string='Payment Lines')
    
    @api.depends('schedule_line_ids.percentage')
    def _compute_total_percentage(self):
        for schedule in self:
            schedule.total_percentage = sum(schedule.schedule_line_ids.mapped('percentage'))
    
    @api.constrains('total_percentage')
    def _check_total_percentage(self):
        for schedule in self:
            if abs(schedule.total_percentage - 100.0) > 0.01:  # Allow small rounding difference
                raise ValidationError(_(
                    'Total percentage must equal 100%%. Current total: %.2f%%'
                ) % schedule.total_percentage)


class PaymentScheduleLine(models.Model):
    _name = 'payment.schedule.line'
    _description = 'Payment Schedule Line'
    _order = 'schedule_id, days_after, sequence'
    
    schedule_id = fields.Many2one('payment.schedule', string='Payment Schedule',
                                  required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True, translate=True,
                      help='e.g., "Booking Payment", "Handover Payment", "Monthly Installment 1"')
    sequence = fields.Integer(string='Sequence', default=10)
    percentage = fields.Float(string='Percentage (%)', required=True, digits=(5, 2),
                             help='Percentage of total amount')
    days_after = fields.Integer(string='Days After Contract', default=0, required=True,
                               help='Invoice due date = Contract Start Date + Days')
    installment_frequency = fields.Selection([
        ('one_time', 'One Time Payment'),
        ('monthly', 'Monthly (30 days)'),
        ('quarterly', 'Quarterly (90 days)'),
        ('bi_annual', 'Bi-Annual (180 days)'),
        ('annual', 'Annual (365 days)')
    ], string='Frequency', default='one_time', required=True,
       help='For recurring payments, this determines the interval between invoices')
    number_of_installments = fields.Integer(string='Number of Installments', default=1,
                                           help='1 for one-time payment, >1 for split payments')
    note = fields.Text(string='Internal Notes', translate=True)
    
    @api.constrains('percentage')
    def _check_percentage(self):
        for line in self:
            if line.percentage <= 0 or line.percentage > 100:
                raise ValidationError(_('Percentage must be between 0 and 100'))
    
    @api.constrains('days_after')
    def _check_days_after(self):
        for line in self:
            if line.days_after < 0:
                raise ValidationError(_('Days after contract cannot be negative'))
    
    @api.constrains('number_of_installments')
    def _check_installments(self):
        for line in self:
            if line.number_of_installments < 1:
                raise ValidationError(_('Number of installments must be at least 1'))
    
    @api.onchange('installment_frequency')
    def _onchange_installment_frequency(self):
        """Update number of installments based on common patterns"""
        if self.installment_frequency == 'monthly' and self.number_of_installments == 1:
            # Suggest 12 months for annual contract
            self.number_of_installments = 12
        elif self.installment_frequency == 'quarterly' and self.number_of_installments == 1:
            self.number_of_installments = 4
        elif self.installment_frequency == 'bi_annual' and self.number_of_installments == 1:
            self.number_of_installments = 2
