# SGC - Unified Video Conferencing

![Version](https://img.shields.io/badge/version-19.0.1.0.2-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-OPL-1-green.svg)
![Application](https://img.shields.io/badge/type-Application-orange.svg)

## Overview

**SGC - Unified Video Conferencing** — Unified video conferencing integration — Google Meet, Teams, Zoom, Webex, Jitsi, Zoho, GoTo

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **7+ Provider Support** — Google Meet, Teams, Zoom, Webex, Jitsi, Zoho, GoTo
- **Unified Abstraction Layer** — Add new providers with single class
- **OAuth 2.0 Integration** — Auto-refresh tokens, encrypted storage
- **One-Click Meetings** — Create from Calendar, CRM, Sales, Helpdesk, Project, Recruitment
- **Recurring & Instant** — Scheduled, recurring, or ad-hoc meetings
- **Recording Management** — URL, duration, attendance tracking
- **Executive Dashboard** — Pivot and graph views of meeting usage
- **Multi-Company** — Isolated provider accounts per company

## Installation

1. Copy the `sgc_video_conferencing` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SGC - Unified Video Conferencing"
4. Click **Install**

### Dependencies

`base_setup`, `mail`, `calendar`, `crm`, `sale_management`, `project`, `hr`, `hr_recruitment`, `contacts`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

Settings > Video Conferencing > Configure Provider. Then use Meeting wizard from any module.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_video_conferencing` |
| **Version** | `19.0.1.0.2` |
| **Category** | Productivity/Video Conferencing |
| **Author** | SGC TECH AI |
| **License** | OPL-1 |
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

This module is licensed under OPL-1.

---

**Maintained by**: SGC TECH AI
**Odoo Version**: 19.0
