# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class MemoVerificationController(http.Controller):

    @http.route(
        '/memo/verify/<string:token>',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
    )
    def memo_verify(self, token, **kwargs):
        memo = request.env['hr.memo'].sudo().search(
            [('verification_token', '=', token)],
            limit=1,
        )
        return request.render(
            'sgc_hr_memos.memo_verification_page',
            {'memo': memo},
        )
