# -*- coding: utf-8 -*-
"""Fix rows still holding pre-refactor sale_lease/state values.

property.details.sale_lease is declared as Selection([('sale', ...), ('lease', ...),
('both', ...)]), but wizard/unit_creation.py and wizard/booking_wizard.py used to
write the older values 'for_sale' and 'for_tenancy'. property.details.state is
declared as Selection([('available', ...), ('booked', ...), ('sold', ...),
('rented', ...), ('maintenance', ...)]), but some rows hold 'draft' (a legacy
pre-publish stage with no wired action anywhere in the current codebase) or
'sale' (data corruption -- the sale_lease value ended up in the state column).
Any row holding an unknown selection value crashes the Properties list
searchpanel/groupby (KeyError on the unknown value) as soon as it tries to
build filter counts. The write sites were fixed in this version; this
migration corrects any rows created before the fix.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        "UPDATE property_details SET sale_lease = 'sale' WHERE sale_lease = 'for_sale'"
    )
    _logger.info("sgc_offplan_rental_property_management: fixed %s row(s) with sale_lease='for_sale'", cr.rowcount)

    cr.execute(
        "UPDATE property_details SET sale_lease = 'lease' WHERE sale_lease = 'for_tenancy'"
    )
    _logger.info("sgc_offplan_rental_property_management: fixed %s row(s) with sale_lease='for_tenancy'", cr.rowcount)

    cr.execute(
        "UPDATE property_details SET state = 'available' WHERE state = 'draft'"
    )
    _logger.info("sgc_offplan_rental_property_management: fixed %s row(s) with state='draft' (unwired legacy status)", cr.rowcount)

    cr.execute(
        "UPDATE property_details SET state = 'available' WHERE state = 'sale'"
    )
    _logger.info("sgc_offplan_rental_property_management: fixed %s row(s) with state='sale' (data corruption -- sale_lease value in state column)", cr.rowcount)
