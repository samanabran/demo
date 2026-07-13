from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CommissionPaymentWizard(models.TransientModel):
    """Wizard for recording commission payments"""
    _name = 'commission.payment.wizard'
    _description = 'Commission Payment Wizard'

    commission_line_id = fields.Many2one(
        'commission.line',
        string='Commission Line',
        required=True,
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Commission Partner',
        readonly=True,
        compute='_compute_commission_line_fields',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
        compute='_compute_commission_line_fields',
        store=True
    )

    commission_amount = fields.Monetary(
        string='Total Commission',
        readonly=True,
        currency_field='currency_id',
        compute='_compute_commission_line_fields',
        store=True
    )

    # Temporarily disabled related fields for debugging
    # paid_amount_current = fields.Monetary(
    #     related='commission_line_id.paid_amount',
    #     string='Previously Paid',
    #     readonly=True,
    #     currency_field='currency_id'
    # )

    # outstanding_amount = fields.Monetary(
    #     related='commission_line_id.outstanding_amount',
    #     string='Outstanding',
    #     readonly=True,
    #     currency_field='currency_id'
    # )

    payment_amount = fields.Monetary(
        string='Payment Amount',
        required=True,
        help='Amount being paid in this transaction',
        currency_field='currency_id'
    )

    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today
    )

    payment_reference = fields.Char(
        string='Payment Reference',
        help='Reference number for this payment'
    )

    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other')
    ], string='Payment Method', default='bank_transfer')

    notes = fields.Text(
        string='Payment Notes',
        help='Additional notes about this payment'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
        compute='_compute_commission_line_fields',
        store=True
    )

    # Validation fields
    max_amount = fields.Monetary(
        string='Maximum Allowed',
        readonly=True,
        help='Maximum amount that can be paid'
    )

    @api.depends('commission_line_id')
    def _compute_commission_line_fields(self):
        """Compute fields from commission line"""
        for wizard in self:
            if wizard.commission_line_id:
                wizard.partner_id = wizard.commission_line_id.partner_id
                wizard.currency_id = wizard.commission_line_id.currency_id
                wizard.commission_amount = wizard.commission_line_id.commission_amount
            else:
                wizard.partner_id = False
                wizard.currency_id = False
                wizard.commission_amount = 0.0

    @api.constrains('payment_amount')
    def _check_payment_amount(self):
        """Validate payment amount"""
        for wizard in self:
            if wizard.payment_amount <= 0:
                raise ValidationError(_("Payment amount must be positive."))

            if wizard.commission_amount and wizard.payment_amount > wizard.commission_amount:
                raise ValidationError(
                    _("Payment amount cannot exceed commission amount of %s") %
                    wizard.commission_amount
                )

    def action_record_payment(self):
        """Record the payment"""
        self.ensure_one()

        if not self.commission_line_id:
            raise UserError(_("Commission line not found."))

        # Update commission line with payment
        new_paid_amount = self.commission_line_id.paid_amount + self.payment_amount

        self.commission_line_id.write({
            'paid_amount': new_paid_amount,
        })

        # If fully paid, update state and payment date
        if new_paid_amount >= self.commission_line_id.commission_amount:
            self.commission_line_id.write({
                'state': 'paid',
                'payment_date': self.payment_date
            })

        # Log the payment in chatter
        payment_message = _(
            "Payment Recorded:<br/>"
            "• Amount: %s %s<br/>"
            "• Date: %s<br/>"
            "• Method: %s<br/>"
            "• Reference: %s<br/>"
            "• Total Paid: %s %s<br/>"
            "• Outstanding: %s %s"
        ) % (
            self.payment_amount, self.currency_id.name,
            self.payment_date,
            dict(self._fields['payment_method'].selection).get(self.payment_method),
            self.payment_reference or 'N/A',
            new_paid_amount, self.currency_id.name,
            self.commission_line_id.outstanding_amount, self.currency_id.name
        )

        if self.notes:
            payment_message += f"<br/>• Notes: {self.notes}"

        self.commission_line_id.message_post(body=payment_message)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Recorded'),
                'message': _('Payment of %s %s has been recorded successfully.') % (
                    self.payment_amount, self.currency_id.name
                ),
                'type': 'success',
            }
        }

    def action_record_full_payment(self):
        """Record full payment of outstanding amount"""
        self.ensure_one()
        self.payment_amount = self.outstanding_amount
        return self.action_record_payment()


class CommissionBulkPaymentWizard(models.TransientModel):
    """Wizard for bulk commission payment updates"""
    _name = 'commission.bulk.payment.wizard'
    _description = 'Bulk Commission Payment Wizard'

    commission_line_ids = fields.Many2many(
        'commission.line',
        string='Commission Lines',
        required=True,
        domain=[('state', '=', 'processed')]
    )

    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today
    )

    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other')
    ], string='Payment Method', default='bank_transfer', required=True)

    payment_reference = fields.Char(
        string='Payment Reference',
        help='Reference number for this batch payment'
    )

    notes = fields.Text(
        string='Payment Notes',
        help='Additional notes about this payment batch'
    )

    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_total_amount',
        help='Total amount to be paid'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('commission_line_ids')
    def _compute_total_amount(self):
        """Compute total payment amount"""
        for wizard in self:
            wizard.total_amount = sum(
                wizard.commission_line_ids.mapped('outstanding_amount')
            )

    def action_record_bulk_payment(self):
        """Record bulk payment for all selected commission lines"""
        self.ensure_one()

        if not self.commission_line_ids:
            raise UserError(_("No commission lines selected."))

        processed_count = 0
        total_paid = 0

        for line in self.commission_line_ids:
            if line.outstanding_amount > 0:
                # Mark as fully paid
                line.write({
                    'paid_amount': line.commission_amount,
                    'state': 'paid',
                    'payment_date': self.payment_date
                })

                # Log payment
                payment_message = _(
                    "Bulk Payment Recorded:<br/>"
                    "• Date: %s<br/>"
                    "• Method: %s<br/>"
                    "• Reference: %s<br/>"
                    "• Amount: %s %s"
                ) % (
                    self.payment_date,
                    dict(self._fields['payment_method'].selection).get(self.payment_method),
                    self.payment_reference or 'N/A',
                    line.commission_amount, line.currency_id.name
                )

                if self.notes:
                    payment_message += f"<br/>• Notes: {self.notes}"

                line.message_post(body=payment_message)

                processed_count += 1
                total_paid += line.commission_amount

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Payment Recorded'),
                'message': _('Processed %s commission payments totaling %s %s') % (
                    processed_count, total_paid, self.currency_id.name
                ),
                'type': 'success',
            }
        }