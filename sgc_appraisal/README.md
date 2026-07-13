# SGC - Employee Appraisal

![Version](https://img.shields.io/badge/version-19.0.1.0.0-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-OPL-1-green.svg)
![Module](https://img.shields.io/badge/type-Module-lightgrey.svg)

## Overview

**SGC - Employee Appraisal** — Roll out appraisal plans and get the best of your 
    workforce

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **Appraisal Plans** — Create structured plans with configurable durations, stages, and target audiences
- **360° Feedback** — Self, manager, peer, and subordinate evaluations in a single workflow
- **Automated Reminders** — Email notifications to overdue employees and managers
- **Goal Tracking** — Set and track SMART goals linked to appraisal outcomes
- **Analytics Dashboard** — Department-level metrics, completion rates, and rating distributions
- **PDF Reports** — Branded appraisal reports with signature blocks

## Installation

1. Copy the `sgc_appraisal` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SGC - Employee Appraisal"
4. Click **Install**

### Dependencies

`hr`, `survey`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

HR > Appraisal Plans > Create. Add employees, set timeline, configure stages. Employees receive email invitations automatically.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_appraisal` |
| **Version** | `19.0.1.0.0` |
| **Category** | Human Resources |
| **Author** | SGC TECH AI |
| **License** | OPL-1 |
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

This module is licensed under OPL-1.

---

**Maintained by**: SGC TECH AI
**Odoo Version**: 19.0
