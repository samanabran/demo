# SGC - Recruitment

![Version](https://img.shields.io/badge/version-19.0.1.0.3-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-LGPL-3-green.svg)
![Module](https://img.shields.io/badge/type-Module-lightgrey.svg)

## Overview

**SGC - Recruitment** — UAE-compliant offer letters and recruitment extensions

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **UAE-Compliant Applicant Fields** — Emirates ID, visa status, labour card tracking
- **Offer Letter Generation** — Professional PDF with company branding
- **Salary Calculations** — Auto-compute total compensation package
- **Email Templates** — Pre-built UAE Labour Law compliant offers
- **Digital Signatures** — Accept and reject offers with audit trail
- **Validity Tracking** — Auto-expire offers after configurable days
- **Deep Ocean Branding** — Navy, ocean blue, sky blue palette

## Installation

1. Copy the `sgc_recruitment` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SGC - Recruitment"
4. Click **Install**

### Dependencies

`base`, `hr`, `hr_recruitment`, `crm`, `mail`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

Recruitment > Applications. Open applicant, fill UAE fields, then Offer Letter > Generate.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_recruitment` |
| **Version** | `19.0.1.0.3` |
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
