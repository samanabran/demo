# -*- coding: utf-8 -*-
# Copyright 2025 SGC TECH AI
# Part of SGC Odoo Suite. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class CertificateType(models.Model):
    _name = 'certificate.type'
    _description = 'Certificate Types'
    _order = 'type'

    type = fields.Char(string='Type', required=True)
