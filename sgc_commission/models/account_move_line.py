from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Commission-specific fields for vendor bills
    commission_rate = fields.Float(
        string="Commission Rate (%)",
        digits=(16, 4),
        help="Commission rate percentage for easy reference"
    )
    
    commission_base_amount = fields.Monetary(
        string="Commission Base",
        currency_field='currency_id',
        help="Base amount on which commission was calculated"
    )
    
    commission_line_id = fields.Many2one(
        'commission.line',
        string="Commission Line",
        ondelete='set null',
        help="Link to original commission line"
    )
