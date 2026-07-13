# SGC - HR Memos

![Version](https://img.shields.io/badge/version-19.0.2.0.0-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-LGPL-3-green.svg)
![Module](https://img.shields.io/badge/type-Module-lightgrey.svg)

## Overview

**SGC - HR Memos** — HR memos with approval workflow, QR verification, and digital signature

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **Memo Types** — Warning, appreciation, salary adjustment, and custom categories
- **Approval Workflow** — Draft → Review → Approve → Publish with audit trail
- **Digital Signatures** — Sign memos with employee acknowledgment
- **QR Code Verification** — Public verification page confirms memo authenticity
- **Email Distribution** — Auto-send to employee and CC HR/Manager
- **Memo History** — Complete timeline per employee

## Installation

1. Copy the `sgc_hr_memos` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SGC - HR Memos"
4. Click **Install**

### Dependencies

`hr`, `mail`, `website`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

HR > Memos > Create. Select employee and type, route through approval, then publish to deliver.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_hr_memos` |
| **Version** | `19.0.2.0.0` |
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
