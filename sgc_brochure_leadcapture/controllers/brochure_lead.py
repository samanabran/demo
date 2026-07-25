import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BrochureLeadController(http.Controller):

    @http.route('/brochure/lead/submit', type='jsonrpc', auth='public', website=True, methods=['POST'])
    def submit_lead(self, property_id=None, name=None, email=None, phone=None, **kwargs):
        try:
            property_id = int(property_id)
        except (TypeError, ValueError):
            return {'success': False, 'error': 'Invalid property.'}

        property_rec = request.env['property.details'].sudo().browse(property_id)
        if not property_rec.exists():
            return {'success': False, 'error': 'Property not found.'}

        name = (name or '').strip()
        email = (email or '').strip()
        phone = (phone or '').strip()
        if not name or not email or not phone:
            return {'success': False, 'error': 'Name, email, and phone are required.'}

        # Primary asset is the generated premium brochure report (see
        # /brochure/property/<id>/pdf below) - it's rendered on demand from
        # live property data, so it doesn't depend on anyone having manually
        # uploaded a file. Only fall back to the uploaded attachment fields
        # (public-safe via /web/content) if the property isn't published/
        # renderable for some reason.
        download_url = False
        if property_rec.is_published_website:
            download_url = '/brochure/property/%s/pdf' % property_id
        elif property_rec.brochure:
            download_url = '/web/content/property.details/%s/brochure?download=true' % property_id
        elif property_rec.floor_plan:
            download_url = '/web/content/property.details/%s/floor_plan?download=true' % property_id

        if not download_url:
            return {'success': False, 'error': 'No brochure is available for this property yet.'}

        request.env['crm.lead'].sudo().create({
            'name': 'Brochure request: %s' % (property_rec.name or 'Property #%s' % property_id),
            'contact_name': name,
            'email_from': email,
            'phone': phone,
            'description': 'Requested brochure download for "%s" (property.details id=%s) via website.' % (
                property_rec.name or '', property_id),
        })

        return {
            'success': True,
            'download_url': download_url,
        }

    @http.route('/brochure/property/<int:property_id>/pdf', type='http', auth='public', website=True)
    def download_property_brochure_pdf(self, property_id, **kwargs):
        property_rec = request.env['property.details'].sudo().browse(property_id)
        if not property_rec.exists() or not property_rec.is_published_website:
            return request.not_found()

        report = request.env.ref(
            'sgc_offplan_rental_property_management.action_report_property_brochure'
        ).sudo()
        try:
            pdf_content, _content_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                report, [property_rec.id]
            )
        except Exception:
            _logger.exception('Failed to render property brochure PDF for property.details id=%s', property_id)
            return request.not_found()

        filename = '%s-brochure.pdf' % (property_rec.name or 'property').replace('/', '-')
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', 'attachment; filename="%s"' % filename),
        ]
        return request.make_response(pdf_content, headers=headers)
