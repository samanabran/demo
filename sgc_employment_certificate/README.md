# SGC - Employment Certificate

![Version](https://img.shields.io/badge/version-19.0.1.0.0-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-LGPL-3-green.svg)
![Module](https://img.shields.io/badge/type-Module-lightgrey.svg)

## Overview

**SGC - Employment Certificate** — Generate Employment Certificates for Employees

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **Professional Certificate Template** — A4 print-ready with company branding
- **OSUS Maroon & Gold Theme** — Premium corporate identity
- **Configurable Content** — Editable fields for position, salary, and tenure
- **Reference Number Tracking** — Unique certificate numbers for audit
- **QR Code Verification** — Public URL to verify authenticity
- **Multi-Language** — Supports English and Arabic

## Installation

1. Copy the `sgc_employment_certificate` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SGC - Employment Certificate"
4. Click **Install**

### Dependencies

`hr`, `hr_contract`, `mail`, `website`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

HR > Employment Certificates > Create. Select employee, set validity, then Print > Certificate.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_employment_certificate` |
| **Version** | `19.0.1.0.0` |
| **Category** | Human Resources |
| **Author** | SGC TECH AI |
| **License** | LGPL-3 |
| **Odoo Version** | 19.0 |
| **Application** | No |

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
