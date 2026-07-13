# -*- coding: utf-8 -*-
"""
Pre-migration script to handle commission_calculation_time field type change
from Float to Datetime
"""

def migrate(cr, version):  # pylint: disable=unused-argument
    """
    Migrate commission_calculation_time field from double precision to timestamp
    """
    # Check if the column exists and is double precision
    cr.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'sale_order' 
        AND column_name = 'commission_calculation_time'
    """)
    
    result = cr.fetchone()
    if result and result[1] == 'double precision':
        # Drop the old column since conversion from double precision to timestamp
        # is not straightforward and the old data (milliseconds) isn't meaningful
        # as datetime anyway
        cr.execute("ALTER TABLE sale_order DROP COLUMN IF EXISTS commission_calculation_time")
        
        # The new column will be automatically created by Odoo when it processes
        # the field definition in the model