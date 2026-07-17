import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BrochureLeadController(http.Controller):

    @http.route('/brochure/lead/submit', type='json', auth='public', website=True, methods=['POST'])
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
            'download_url': '/report/pdf/sgc_offplan_rental_property_management.report_property_brochure/%s' % property_id,
        }
