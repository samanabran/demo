# SCHOLARIX Assessment System

![Version](https://img.shields.io/badge/version-19.0.2.0.1-blue.svg)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)
![License](https://img.shields.io/badge/license-LGPL-3-green.svg)
![Application](https://img.shields.io/badge/type-Application-orange.svg)

## Overview

**SCHOLARIX Assessment System** — AI-Powered Candidate Assessment and Evaluation System

Part of the **SGC TECH AI** Odoo 19 module suite for enterprise real estate, HR, CRM, and productivity workflows.

## Key Features

- **Public Assessment Portal** — Candidates access assessments via unique token URLs
- **10-Question Framework** — Standardized assessment covering 5 categories
- **AI NLP Scoring** — Automatic scoring across Technical, Sales, Communication, Learning, and Cultural Fit
- **Human Review Workflow** — Reviewer queue with comments, ratings, and overrides
- **Rankings & Leaderboard** — Top candidates surfaced with composite scores
- **Advanced Analytics** — Funnel conversion, time-to-complete, score distribution
- **PDF Reports** — Per-candidate detailed score reports
- **GDPR Compliant** — Data retention policies and right-to-erasure tooling

## Installation

1. Copy the `sgc_assessment` folder into your Odoo `addons` directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "SCHOLARIX Assessment System"
4. Click **Install**

### Dependencies

`base`, `web`, `portal`, `mail`, `hr_recruitment`

## Configuration

After installation:

1. Set up user access rights in **Settings > Users & Companies > Users**
2. Assign the relevant SGC security groups to your users
3. Configure module-specific parameters as needed

## Usage

Recruitment > Assessments > Create Campaign. Share public URL with candidates, review results in the queue.

## Module Information

| Field | Value |
|-------|-------|
| **Technical Name** | `sgc_assessment` |
| **Version** | `19.0.2.0.1` |
| **Category** | Human Resources/Recruitment |
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
