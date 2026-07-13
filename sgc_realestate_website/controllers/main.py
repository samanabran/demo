# -*- coding: utf-8 -*-
###############################################################################
#    SGC - Real Estate Website
#    Copyright (C) 2025 SGC TECH AI (https://sgctech.ai)
#    License LGPL-3 - See LICENSE file for details
###############################################################################
from odoo import http, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

SORT_OPTIONS = {
    'newest': 'create_date desc',
    'price_asc': 'price asc',
    'price_desc': 'price desc',
}


class RealEstateWebsiteController(http.Controller):
    """Main HTTP routes for SGC Real Estate Website"""

    def _build_domain(self, kwargs):
        domain = [('website_published', '=', True)]
        if kwargs.get('search'):
            domain += ['|', ('title', 'ilike', kwargs['search']),
                       ('description', 'ilike', kwargs['search'])]
        if kwargs.get('property_type'):
            domain += [('property_type', '=', kwargs['property_type'])]
        if kwargs.get('sale_lease'):
            domain += [('sale_lease', '=', kwargs['sale_lease'])]
        if kwargs.get('min_price'):
            domain += [('price', '>=', float(kwargs['min_price']))]
        if kwargs.get('max_price'):
            domain += [('price', '<=', float(kwargs['max_price']))]
        if kwargs.get('bedrooms'):
            domain += [('bedrooms', '>=', int(kwargs['bedrooms']))]
        if kwargs.get('bathrooms'):
            domain += [('bathrooms', '>=', int(kwargs['bathrooms']))]
        if kwargs.get('country'):
            domain += [('destination_country_id', '=', int(kwargs['country']))]
        if kwargs.get('city'):
            domain += [('city', 'ilike', kwargs['city'])]
        return domain

    @http.route(['/properties', '/realestate/properties'], type='http', auth='public', website=True, sitemap=True)
    def property_listing(self, **kwargs):
        """Public property listing page with search and filters"""
        try:
            domain = self._build_domain(kwargs)
            order = SORT_OPTIONS.get(kwargs.get('sort'), 'create_date desc')
            properties = request.env['sgc.realestate.property'].sudo().search(domain, order=order)
            countries = request.env['sgc.realestate.destination.country'].sudo().search([])
            property_types = dict(request.env['sgc.realestate.property']._fields['property_type'].selection)
            return request.render('sgc_realestate_website.property_listing_page', {
                'properties': properties,
                'countries': countries,
                'property_types': property_types,
                'filters': kwargs,
                'search_term': kwargs.get('search'),
            })
        except Exception as e:
            _logger.error("Error in property listing: %s", str(e), exc_info=True)
            return request.render('website.page_404')

    @http.route(['/property/<model("sgc.realestate.property"):property_id>',
                 '/realestate/property/<model("sgc.realestate.property"):property_id>'],
                type='http', auth='public', website=True, sitemap=True)
    def property_detail(self, property_id, **kwargs):
        """Property detail page with gallery, amenities, inline inquiry and gated download"""
        try:
            if not property_id.exists() or not property_id.website_published:
                return request.render('website.page_404')

            related = request.env['sgc.realestate.property'].sudo().search([
                ('website_published', '=', True),
                ('id', '!=', property_id.id),
                '|', ('property_type', '=', property_id.property_type),
                     ('destination_country_id', '=', property_id.destination_country_id.id),
            ], limit=4)
            return request.render('sgc_realestate_website.property_detail_page', {
                'property': property_id,
                'related_properties': related,
            })
        except Exception as e:
            _logger.error("Error in property detail: %s", str(e), exc_info=True)
            return request.render('website.page_404')

    @http.route('/realestate/destination/<model("sgc.realestate.destination.country"):country>', type='http',
                auth='public', website=True, sitemap=True)
    def destination_page(self, country, **kwargs):
        """Country/city destination landing page with SEO"""
        try:
            properties = request.env['sgc.realestate.property'].sudo().search([
                ('website_published', '=', True),
                ('destination_country_id', '=', country.id),
            ])
            return request.render('sgc_realestate_website.destination_page', {
                'country': country,
                'properties': properties,
            })
        except Exception as e:
            _logger.error("Error in destination page: %s", str(e), exc_info=True)
            return request.render('website.page_404')

    def _create_consultation(self, kwargs, property_rec=None):
        vals = {
            'name': kwargs.get('name') or 'Website Visitor',
            'email': kwargs.get('email'),
            'phone': kwargs.get('phone'),
            'message': kwargs.get('message', ''),
            'source': 'Website',
            'ip_address': request.httprequest.remote_addr,
            'user_agent': request.httprequest.headers.get('User-Agent'),
        }
        if property_rec:
            vals['property_id'] = property_rec.id
            vals['destination_country_id'] = property_rec.destination_country_id.id
        elif kwargs.get('destination_country_id'):
            vals['destination_country_id'] = int(kwargs['destination_country_id'])
        return request.env['sgc.realestate.consultation'].sudo().create(vals)

    @http.route('/consultation', type='http', auth='public', website=True)
    def consultation_page(self, property_id=None, **kwargs):
        """Standalone consultation/lead-capture page"""
        countries = request.env['sgc.realestate.destination.country'].sudo().search([])
        selected_property = None
        if property_id:
            selected_property = request.env['sgc.realestate.property'].sudo().browse(int(property_id)).exists()
        return request.render('sgc_realestate_website.consultation_form_page', {
            'countries': countries,
            'selected_property': selected_property,
        })

    @http.route(['/consultation/submit', '/realestate/consultation'], type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def consultation_submit(self, **kwargs):
        """Lead capture form submission.

        The module's bundled consultation_form.js submits this via fetch() and expects
        a JSON {success, message} body, so this always responds with JSON rather than
        a redirect (the JS drives the success/error UI transition after the call).
        """
        import json as _json
        from odoo.http import Response
        try:
            if not kwargs.get('name') or not kwargs.get('email'):
                body = {'success': False, 'message': _('Name and email are required.')}
                return Response(_json.dumps(body), content_type='application/json', status=400)
            property_rec = None
            if kwargs.get('property_id'):
                property_rec = request.env['sgc.realestate.property'].sudo().browse(
                    int(kwargs['property_id'])).exists()
            self._create_consultation(kwargs, property_rec)
            return Response(_json.dumps({'success': True}), content_type='application/json')
        except Exception as e:
            _logger.error("Error creating consultation: %s", str(e), exc_info=True)
            body = {'success': False, 'message': _('Something went wrong, please try again.')}
            return Response(_json.dumps(body), content_type='application/json', status=500)

    @http.route(['/consultation/thank-you', '/realestate/thank-you'], type='http', auth='public', website=True)
    def thank_you(self, **kwargs):
        """Thank you page after consultation submission"""
        return request.render('sgc_realestate_website.thank_you')

    @http.route('/realestate/inquiry', type='jsonrpc', auth='public', website=True)
    def property_inquiry(self, **kwargs):
        """Inline AJAX inquiry endpoint used from the property detail page"""
        try:
            if not kwargs.get('name') or not kwargs.get('email'):
                return {'success': False, 'error': _('Name and email are required.')}
            property_rec = None
            if kwargs.get('property_id'):
                property_rec = request.env['sgc.realestate.property'].sudo().browse(
                    int(kwargs['property_id'])).exists()
            consultation = self._create_consultation(kwargs, property_rec)
            return {'success': True, 'id': consultation.id}
        except Exception as e:
            _logger.error("Error in property inquiry: %s", str(e), exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/realestate/gated-download', type='jsonrpc', auth='public', website=True)
    def gated_download(self, **kwargs):
        """Gated content download: capture lead info, then return a download URL for the requested doc"""
        try:
            if not kwargs.get('name') or not kwargs.get('email') or not kwargs.get('property_id'):
                return {'success': False, 'error': _('Name, email and property are required.')}
            doc_type = kwargs.get('doc_type', 'brochure')
            property_rec = request.env['sgc.realestate.property'].sudo().browse(
                int(kwargs['property_id'])).exists()
            if not property_rec:
                return {'success': False, 'error': _('Property not found.')}

            field_map = {'brochure': 'brochure', 'floor_plan': 'floor_plan'}
            field_name = field_map.get(doc_type, 'brochure')
            if not getattr(property_rec, field_name):
                return {'success': False, 'error': _('This document is not available for this property yet.')}

            consultation = self._create_consultation(kwargs, property_rec)
            consultation.write({'message': (consultation.message or '') + f'\n[Gated download: {doc_type}]'})
            download_url = f'/web/content/sgc.realestate.property/{property_rec.id}/{field_name}?download=true'
            return {'success': True, 'url': download_url}
        except Exception as e:
            _logger.error("Error in gated download: %s", str(e), exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/realestate/api/properties', type='jsonrpc', auth='public')
    def api_properties(self, **kwargs):
        """JSON API for property search (used by OWL components)"""
        try:
            domain = [('website_published', '=', True)]
            if kwargs.get('domain'):
                domain += kwargs['domain']
            Property = request.env['sgc.realestate.property'].sudo()
            properties = Property.search_read(
                domain,
                fields=['id', 'title', 'price', 'bedrooms', 'bathrooms',
                        'area', 'city', 'destination_country_id', 'property_type', 'sale_lease',
                        'image_256', 'create_date'],
                limit=kwargs.get('limit', 20),
                offset=kwargs.get('offset', 0),
                order='create_date desc'
            )
            return {
                'properties': properties,
                'total': Property.search_count(domain),
            }
        except Exception as e:
            _logger.error("Error in API properties: %s", str(e), exc_info=True)
            return {'error': str(e), 'properties': [], 'total': 0}
