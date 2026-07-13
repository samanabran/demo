# SGC - E-Learning

![Version](https://img.shields.io/badge/version-19.0.1.0.0-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-LGPL-3-green.svg)
![Application](https://img.shields.io/badge/type-Application-orange.svg)

## Overview

**SGC - E-Learning** — Sequential learning paths for real estate operations with quizzes, badges, and certificates

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **Sequential Learning Paths** — Locked progression through course sections
- **Quiz Engine** — Multiple choice, true/false, and short answer questions
- **Badges & Achievements** — Auto-award on milestone completion
- **Certificates** — PDF certificates with unique verification codes
- **Course Library** — Rental, Sales, Commission, Accounting, and HR tracks
- **Progress Tracking** — Per-user completion percentage and time spent
- **HR Integration** — Assign courses to employees and departments

## Installation

1. Copy the `sgc_elearning` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SGC - E-Learning"
4. Click **Install**

### Dependencies

`base`, `mail`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

eLearning > Courses. Enroll users, then track progress in Reporting > Course Analytics.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_elearning` |
| **Version** | `19.0.1.0.0` |
| **Category** | Education |
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
