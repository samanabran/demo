# Deals Management Clean — Admin & Installation Manual

## Overview

This guide covers installation, configuration, and operational setup for the
Deals Management Clean module (technical name: `deals_management`).

## Prerequisites

- Odoo 17 running with access to the Apps menu.
- The following dependencies must be available in your Odoo instance:
  - `sale`
  - `purchase`
  - `account`
  - `project`
  - `mail`
  - `hr`
  - `utm`

## Installation (UI)

1. Copy the module folder `deals_management` into your server addons path.
2. Restart the Odoo server.
3. Go to **Apps** → **Update Apps List**.
4. Search for **Deals Management Clean** and click **Install**.

## Installation (CLI)

1. Restart Odoo with module update:
   - `./odoo-bin -u deals_management -d <db_name>`
2. Confirm the module appears in Apps and is installed.

## Security Groups

The module creates commission-specific groups:

- **Commission User** — can view and create commissions.
- **Commission Manager** — can manage all commission operations.

Assign these via **Settings** → **Users & Companies** → **Users**.

## Configuration

### Commission Expense Account

The purchase order integration uses a configurable expense account:

- System parameter key: `deals_management.commission_expense_account_id`

To set it:

1. Enable **Developer Mode**.
2. Go to **Settings** → **Technical** → **Parameters** → **System Parameters**.
3. Add or update the parameter key above with the account ID.

### Cron Jobs

The module ships scheduled actions for commission processing and cleanup.
Review and enable them under **Settings** → **Technical** → **Automation** →
**Scheduled Actions**.

## Upgrade Notes

- If upgrading from the legacy `commission_ax` module, verify security groups
  and report templates load correctly after installation.
- Re-run the Apps update and restart Odoo after deploying changes.

## Troubleshooting

- **Menus missing**: Update apps list and verify user permissions.
- **Report errors**: Confirm report templates load and dependencies exist.
- **Commission PO errors**: Set the commission expense account parameter.

## Support

If issues persist, review `ODOO17_COMPLIANCE.md` and server logs for details.
