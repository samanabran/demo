from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CommissionCancelWizard(models.TransientModel):
    """Wizard for confirming commission-related cancellations"""
    _name = 'commission.cancel.wizard'
    _description = 'Commission Cancellation Confirmation Wizard'

    sale_order_ids = fields.Many2many(
        'sale.order',
        string='Sale Orders',
        required=True,
        readonly=True
    )

    message = fields.Text(
        string='Cancellation Impact',
        readonly=True,
        help="Information about what will be cancelled"
    )

    force_cancel = fields.Boolean(
        string='Force Cancellation',
        default=False,
        help="Force cancellation even if there are commission-related documents"
    )

    def action_confirm_cancel(self):
        """Confirm the cancellation and proceed"""
        for order in self.sale_order_ids:
            order._execute_cancellation()
        
        return {'type': 'ir.actions.act_window_close'}

