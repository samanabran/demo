# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AssessmentRanking(models.Model):
    _name = 'assessment.ranking'
    _description = 'Candidate Ranking'
    _order = 'overall_rank asc'
    _rec_name = 'candidate_id'

    candidate_id = fields.Many2one(
        'assessment.candidate',
        string='Candidate',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    ranking_date = fields.Date(
        string='Ranking Date',
        default=fields.Date.today,
        readonly=True,
        index=True
    )
    
    # Rankings
    overall_rank = fields.Integer(
        string='Overall Rank',
        required=True,
        index=True
    )
    technical_rank = fields.Integer(string='Technical Rank')
    sales_rank = fields.Integer(string='Sales Rank')
    communication_rank = fields.Integer(string='Communication Rank')
    
    # Scores (from candidate)
    final_score = fields.Float(
        string='Final Score',
        related='candidate_id.overall_score',
        store=True,
        index=True
    )
    technical_score = fields.Float(
        string='Technical Score',
        related='candidate_id.technical_score',
        store=True
    )
    sales_score = fields.Float(
        string='Sales Score',
        related='candidate_id.sales_score',
        store=True
    )
    
    # Statistics
    total_candidates = fields.Integer(
        string='Total Candidates',
        help='Total candidates in this ranking period'
    )
    percentile = fields.Float(
        string='Percentile',
        compute='_compute_percentile',
        store=True,
        help='Percentile ranking (0-100)'
    )
    
    # Comparison with previous ranking
    previous_rank = fields.Integer(string='Previous Rank')
    rank_change = fields.Integer(
        string='Rank Change',
        compute='_compute_rank_change',
        store=True
    )
    
    _check_candidate_ranking_unique = models.Constraint(
        'unique(candidate_id, ranking_date)',
        'Only one ranking per candidate per date!',
    )

    @api.depends('overall_rank', 'total_candidates')
    def _compute_percentile(self):
        """Calculate percentile ranking"""
        for record in self:
            if record.total_candidates and record.overall_rank:
                record.percentile = ((record.total_candidates - record.overall_rank + 1) / 
                                   record.total_candidates * 100)
            else:
                record.percentile = 0.0
    
    @api.depends('overall_rank', 'previous_rank')
    def _compute_rank_change(self):
        """Calculate rank change"""
        for record in self:
            if record.previous_rank:
                record.rank_change = record.previous_rank - record.overall_rank
            else:
                record.rank_change = 0
    
    @api.model
    def create_or_update_ranking(self, candidate):
        """Create or update ranking for a candidate"""
        today = fields.Date.today()
        
        # Get all scored candidates
        all_candidates = self.env['assessment.candidate'].search([
            ('overall_score', '>', 0)
        ], order='overall_score desc')
        
        total_count = len(all_candidates)
        
        # Calculate ranks
        for idx, cand in enumerate(all_candidates, start=1):
            existing_ranking = self.search([
                ('candidate_id', '=', cand.id),
                ('ranking_date', '=', today)
            ])
            
            # Get previous rank
            previous_ranking = self.search([
                ('candidate_id', '=', cand.id),
                ('ranking_date', '<', today)
            ], order='ranking_date desc', limit=1)
            
            ranking_vals = {
                'candidate_id': cand.id,
                'ranking_date': today,
                'overall_rank': idx,
                'total_candidates': total_count,
                'previous_rank': previous_ranking.overall_rank if previous_ranking else idx,
            }
            
            if existing_ranking:
                existing_ranking.write(ranking_vals)
            else:
                self.create(ranking_vals)
        
        # Also calculate category-specific ranks
        self._update_category_ranks(today)
        
        return True
    
    @api.model
    def _update_category_ranks(self, ranking_date):
        """Update category-specific rankings"""
        rankings = self.search([('ranking_date', '=', ranking_date)])
        
        # Technical ranking
        technical_sorted = rankings.sorted(key=lambda r: r.technical_score, reverse=True)
        for idx, ranking in enumerate(technical_sorted, start=1):
            ranking.technical_rank = idx
        
        # Sales ranking
        sales_sorted = rankings.sorted(key=lambda r: r.sales_score, reverse=True)
        for idx, ranking in enumerate(sales_sorted, start=1):
            ranking.sales_rank = idx
        
        # Communication ranking
        comm_sorted = rankings.sorted(key=lambda r: r.candidate_id.communication_score, reverse=True)
        for idx, ranking in enumerate(comm_sorted, start=1):
            ranking.communication_rank = idx
    
    @api.model
    def get_leaderboard(self, category='overall', limit=50):
        """Get leaderboard for dashboard"""
        today = fields.Date.today()
        
        rankings = self.search([
            ('ranking_date', '=', today)
        ], limit=limit)
        
        if category == 'technical':
            rankings = rankings.sorted(key=lambda r: r.technical_rank)
        elif category == 'sales':
            rankings = rankings.sorted(key=lambda r: r.sales_rank)
        else:
            rankings = rankings.sorted(key=lambda r: r.overall_rank)
        
        return [{
            'rank': r.overall_rank,
            'candidate_name': r.candidate_id.full_name,
            'candidate_id': r.candidate_id.id,
            'score': r.final_score,
            'percentile': r.percentile,
            'rank_change': r.rank_change,
        } for r in rankings]
    
    @api.model
    def regenerate_all_rankings(self):
        """Regenerate all rankings (cron job or manual trigger)"""
        candidates = self.env['assessment.candidate'].search([
            ('overall_score', '>', 0)
        ])
        
        for candidate in candidates:
            self.create_or_update_ranking(candidate)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Rankings regenerated successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_view_candidate(self):
        """Open candidate form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Candidate'),
            'res_model': 'assessment.candidate',
            'res_id': self.candidate_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

