from odoo import models, fields, api

class ResPartner(models.Model):
    """Extension of res.partner to add commission agent functionality"""
    _inherit = 'res.partner'

    # Commission Agent Fields
    is_commission_agent = fields.Boolean(
        string='Is Commission Agent',
        default=False,
        help='Check this box if this partner is a commission agent'
    )
    
    commission_rate = fields.Float(
        string='Default Commission Rate (%)',
        help='Default commission rate percentage for this agent'
    )
    
    commission_type_id = fields.Many2one(
        'commission.type',
        string='Default Commission Type',
        help='Default commission type for this agent'
    )

    # Commission Statistics (computed fields)
    total_commission_amount = fields.Monetary(
        string='Total Commission Amount',
        compute='_compute_commission_stats',
        store=False,
        currency_field='currency_id'
    )
    
    commission_count = fields.Integer(
        string='Commission Lines Count',
        compute='_compute_commission_stats',
        store=False
    )
    
    pending_commission_amount = fields.Monetary(
        string='Pending Commission Amount',
        compute='_compute_commission_stats',
        store=False,
        currency_field='currency_id'
    )

    @api.depends('is_commission_agent')
    def _compute_commission_stats(self):
        """Compute commission statistics for commission agents"""
        for partner in self:
            if partner.is_commission_agent:
                # Get commission lines for this partner
                commission_lines = self.env['commission.line'].search([
                    ('partner_id', '=', partner.id)
                ])
                
                partner.commission_count = len(commission_lines)
                partner.total_commission_amount = sum(commission_lines.mapped('commission_amount'))
                
                # Calculate pending commissions
                pending_lines = commission_lines.filtered(lambda l: l.state in ['draft', 'calculated'])
                partner.pending_commission_amount = sum(pending_lines.mapped('commission_amount'))
            else:
                partner.commission_count = 0
                partner.total_commission_amount = 0.0
                partner.pending_commission_amount = 0.0

    def action_view_commission_lines(self):
        """Action to view commission lines for this partner"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Commission Lines - {self.name}',
            'res_model': 'commission.line',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
            }
        }