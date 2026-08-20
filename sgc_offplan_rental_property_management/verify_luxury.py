import odoo.tools, sys
sys.argv = ['', '--db_host=db', '--db_user=odoo', '--db_password=odoo_demo_pw', '--database=demo_presentation']
odoo.tools.config.parse(sys.argv)
dbname = 'demo_presentation'
registry = odoo.modules.registry.Registry(dbname)
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    pf = env['report.paperformat'].search([('name', 'ilike', '%Luxury%')])
    print('Paperformat:', pf.id, pf.name if pf else 'NOT FOUND')
    report = env['ir.actions.report'].search([('report_name', 'ilike', '%luxury%')])
    print('Report action:', report.id, report.name if report else 'NOT FOUND')
    model = env['ir.model'].search([('model', '=', 'report.sgc_offplan_rental_property_management.report_property_brochure_luxury')])
    print('Report model:', 'FOUND' if model else 'NOT FOUND')
    print('All checks passed!' if pf and report else 'Some checks FAILED')
