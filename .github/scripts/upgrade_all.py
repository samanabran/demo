#!/usr/bin/env python3
"""
Upgrade all outdated modules in the demo_presentation Odoo database.

Runs INSIDE the demo_presentation container (copied there by the deploy
workflow via `docker cp`, then invoked with
`docker exec demo_presentation python3 /tmp/upgrade_all.py`) after the
container's addons source has already been git-reset to the latest commit.

Calls ir.module.module.update_list() to refresh each module's on-disk
version from its manifest, then upgrades only the installed modules whose
on-disk version differs from the version recorded in the database. Safe to
run idempotently — modules with no disk changes are skipped.
"""
import sys
import xmlrpc.client

DB = 'demo_presentation'
LOGIN = 'admin'
PASSWORD = 'admin'
URL = 'http://localhost:8069'


def main():
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, LOGIN, PASSWORD, {})
    if not uid:
        print('auth failed — check admin credentials')
        sys.exit(1)
    print(f'uid: {uid}')

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    update_result = models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'update_list', [])
    print(f'update_list result: {update_result}')

    modules = models.execute_kw(
        DB, uid, PASSWORD, 'ir.module.module', 'search_read',
        [[('state', '=', 'installed')]],
        {'fields': ['id', 'name', 'installed_version', 'latest_version']},
    )
    outdated = [m for m in modules if m['installed_version'] != m['latest_version']]
    print(f'{len(modules)} installed modules, {len(outdated)} outdated')

    if not outdated:
        print('nothing to upgrade')
        return

    for m in outdated:
        print(f"  outdated: {m['name']}  {m['installed_version']} -> {m['latest_version']}")

    try:
        result = models.execute_kw(
            DB, uid, PASSWORD, 'ir.module.module', 'button_immediate_upgrade',
            [[m['id'] for m in outdated]],
        )
        print(f'upgrade triggered: {result}')
    except Exception as e:
        print(f'upgrade call failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
