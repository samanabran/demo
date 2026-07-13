from odoo import http
from odoo.http import request


class CertificateVerificationController(http.Controller):

    @http.route(
        '/certificate/verify/<string:token>',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
    )
    def certificate_verify(self, token, **kwargs):
        certificate = request.env['hr.employment.certificate'].sudo().search(
            [('verification_token', '=', token)],
            limit=1,
        )
        values = {
            'certificate': certificate,
        }
        return request.render(
            'hr_employment_certificate.certificate_verification_page',
            values,
        )
