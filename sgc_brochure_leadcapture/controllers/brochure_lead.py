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

        # Serve the uploaded attachment fields directly (public-safe via
        # /web/content), not /report/pdf/... - that route requires an
        # authenticated res.users session, so it silently fails/redirects
        # for anonymous website visitors, which is why the button looked
        # "dead" after a successful lead submission.
        download_url = False
        if property_rec.brochure:
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
