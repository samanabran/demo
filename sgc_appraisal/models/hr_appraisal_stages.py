# -*- coding: utf-8 -*-
###############################################################################
#    Part of the SGC Odoo Suite <https://sgctech.ai>
#
#    SGC TECH AI
#    Copyright (C) 2026 SGC TECH AI (<https://sgctech.ai>)
#
#    This module and its source code are licensed under the Odoo Proprietary
#    License v1.0 (OPL-1). You may not redistribute or resell it. See
#    https://www.odoo.com/documentation/19.0/legal/licenses.html for terms.
###############################################################################

from odoo import fields, models


class HrAppraisalStages(models.Model):
    """Create the model Appraisal Stages to show the stages of the appraisal"""
    _name = 'hr.appraisal.stages'
    _description = 'Appraisal Stages'

    name = fields.Char(string="Name", help="Name of the appraisal stage")
    sequence = fields.Integer(string="Sequence", default=10,
                              help="Sequence of the appraisal stage to be "
                                   "shown")
    fold = fields.Boolean(string='Folded in Appraisal Pipeline',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')
