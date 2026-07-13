# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ConstructionProjectContractDoc(models.Model):
    _name = 'construction.project.contract.doc'
    _description = 'Project Contract Document'
    _order = 'date desc, id desc'

    project_id = fields.Many2one(
        'construction.project', string='Project',
        required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Document Title', required=True)
    category = fields.Selection([
        ('contract', 'Contract'),
        ('agreement', 'Agreement'),
        ('tender', 'Tender / RFP'),
        ('permit', 'Permit / License'),
        ('insurance', 'Insurance'),
        ('bank', 'Bank Guarantee / Bond'),
        ('scope', 'Scope of Work'),
        ('schedule', 'Project Schedule'),
        ('spec', 'Specification'),
        ('report', 'Feasibility / Survey Report'),
        ('legal', 'Legal Document'),
        ('other', 'Other'),
    ], string='Category', default='contract', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    notes = fields.Text(string='Notes')

    # attachment=True auto-stores binary data in ir.attachment, survives re-read
    original_file = fields.Binary(string='Upload File', attachment=True)
    original_filename = fields.Char(string='File Name')
