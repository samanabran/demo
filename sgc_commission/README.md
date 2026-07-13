# SGC - Commission

![Version](https://img.shields.io/badge/version-19.0.3.2.2-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-LGPL-3-green.svg)
![Application](https://img.shields.io/badge/type-Application-orange.svg)

## Overview

**SGC - Commission** — Professional commission management with full workflow and analytics

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **Multi-Method Calculation** — Percentage or fixed amount per rule
- **Workflow States** — Draft → Calculated → Confirmed → Processed → Paid
- **Sale Order Integration** — Auto-attach commission partners to sales lines
- **Purchase Order Generation** — Auto-create POs for external commission agents
- **Multi-Currency** — Full support with conversion at posting date
- **Commission Dashboard** — Real-time KPIs, top performers, pending payouts
- **Performance Reports** — Pivot and graph views by agent, period, or product
- **Audit Trail** — Complete history of calculations, confirmations, and adjustments

## Installation

1. Copy the `sgc_commission` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SGC - Commission"
4. Click **Install**

### Dependencies

`base`, `sale`, `purchase`, `account`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

Sales > Sale Orders > Commission tab. Configure agents and rates, then click "Process Commissions".

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_commission` |
| **Version** | `19.0.3.2.2` |
| **Category** | Sales |
| **Author** | SGC TECH AI |
| **License** | LGPL-3 |
| **Odoo Version** | 19.0 |
| **Application** | Yes |

## Architecture

- **Models**: Located in `models/`
- **Views**: Located in `views/`
- **Security**: ACL and record rules in `security/`
- **Controllers**: HTTP routes in `controllers/`
- **Static Assets**: Branding and descriptions in `static/`
- **Reports**: QWeb templates in `reports/`
- **Wizards**: Interactive wizards in `wizard/` or `wizards/`

## Security

This module implements:

- **Access Control Lists** (`security/ir.model.access.csv`) — model-level permissions
- **Record Rules** — row-level access where applicable
- **Security Groups** — role-based access via `res.groups`
- **Public/Portal Routes** — token-based authentication where exposed

## Support

For issues, feature requests, or integration support, contact the SGC TECH AI team.

## License

This module is licensed under LGPL-3.

---

**Maintained by**: SGC TECH AI
**Odoo Version**: 19.0
