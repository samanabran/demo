# Deals Management Clean

![Version](https://img.shields.io/badge/version-19.0.2.1.0-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-LGPL-3-green.svg)
![Application](https://img.shields.io/badge/type-Application-orange.svg)

## Overview

**Deals Management Clean** — Real estate deals + commission + project/unit management

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **Real Estate Deals** — Offplan, resale, and rental deal tracking
- **Project & Unit Inventory** — Custom models for projects and available units
- **Document Vault** — KYC, booking forms, passport scans attached to deals
- **Financial Summaries** — VAT, totals, commissions, and net payable per deal
- **Commission Workflows** — Auto-calculate and route commissions to agents
- **Vendor Bill Integration** — Match external commission payouts to bills
- **Reports** — Deal pipeline, commission payouts, and unit availability

## Installation

1. Copy the `sgc_deals_management` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "Deals Management Clean"
4. Click **Install**

### Dependencies

`base`, `sale`, `purchase`, `account`, `mail`, `hr`, `utm`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

Sales > Deals > Create. Add buyer, project, unit, then track through offer → contract → close.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_deals_management` |
| **Version** | `19.0.2.1.0` |
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
