# -*- coding: utf-8 -*-
{
    'name': 'SGC Fix Client-Side Context Evaluation',
    'version': '19.0.2.0.0',
    'summary': 'Fix EvalError: user not defined in JavaScript context evaluation',
    'description': """
SGC Fix Client-Side Context Evaluation
========================================
Fixes EvalError: "Name 'user' is not defined" thrown by Odoo's JavaScript
evaluateExpr when window action / menu context fields reference Python
server-side variables (e.g. `user.company_id.id`) that don't exist in the
browser evaluation context.

What it does:
- Scans all `ir.actions.act_window` and `ir.ui.menu` records
- Replaces `user.company_id.id` → `allowed_company_ids[0]`
  (the correct client-side equivalent)
- Replaces `user.company_id` → `allowed_company_ids[0]`
- Logs every changed record for audit

Post-init hook patches all existing records; model overrides (write/create)
prevent new broken records from being created, so the fix stays in effect
as long as the module remains installed.
    """,
    'category': 'Technical',
    'author': 'SGC',
    'website': 'https://sgc-tech.ai',
    'depends': ['base', 'web'],
    'post_init_hook': 'post_init_hook',
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
