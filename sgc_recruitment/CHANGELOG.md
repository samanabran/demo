# Changelog - Scholarix Recruitment Extension

All notable changes to this module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [17.0.1.0.3] - 2024-11-15

### Enhanced
- Complete redesign of offer letter PDF template with optimized readability
- Increased font sizes across all sections (body: 13px, headings: 16px, tables: 13-15px)
- Simplified layout using web.basic_layout instead of external_layout for cleaner output
- Enhanced professional letterhead with improved branding
- Improved table styling with better contrast and larger text
- Optimized spacing and padding throughout document
- Better visual hierarchy with larger section headings and underlines
- Enhanced signature section with clearer boxes and larger fonts
- Improved footer with better readability (10px vs 8px)

## [17.0.1.0.2] - 2024-11-14

### Fixed
- Fixed email template report attachment field name from 'report_template' to 'report_name'
- Resolved "Invalid field 'report_template' on model 'mail.template'" error
- Email template now correctly attaches offer letter PDF using Odoo 17 standard field

## [17.0.1.0.1] - 2024-11-14

### Fixed
- Fixed tree view inheritance error by creating standalone tree view instead of inheriting non-existent base view
- Resolved "External ID not found: hr_recruitment.hr_applicant_view_tree" installation error
- Tree view now displays all essential applicant fields with optional visibility controls

## [17.0.1.0.0] - 2024-11-14

### Added
- Initial release of Scholarix Recruitment Extension
- Extended applicant model with 30+ new fields for UAE compliance
- Personal Information tab (Arabic name, Emirates ID, passport, nationality)
- Employment Details tab (position, department, contract type, start date)
- Compensation & Benefits tab (salary breakdown with auto-calculations)
- Offer Letter tab (reference number, validity tracking, signatures)
- Professional PDF offer letter template with Deep Ocean branding
- Automated salary calculations (monthly + annual totals)
- Email template for offer letter distribution
- UAE Labour Law compliance features
- Multi-currency support
- Digital signature upload capability
- Offer validity auto-calculation (+14 days)
- Unique offer reference number generation (SGO-YYYYMMDD-XXXX format)
- Benefits tracking (health insurance, visa, flight tickets)
- Working hours and notice period fields
- Security rules and access rights
- SCSS styling for branded reports
- Comprehensive README documentation
- Installation guide
- Troubleshooting documentation

### Features
- One-click offer letter PDF generation
- One-click email sending with PDF attachment
- Success notifications for user actions
- Responsive form layouts
- Tree view extensions with salary totals
- Search view filters by nationality and employment type
- Smart buttons for quick actions
- Conditional field visibility based on employment type
- Print-optimized PDF layout
- Mobile-responsive email templates
- Gradient headers and dividers
- Professional signature sections
- Required documents checklist
- Confidentiality clause reference

### Technical
- Compatible with Odoo 17 Community & Enterprise
- Extends `hr.applicant` model via inheritance
- QWeb PDF reports with external layout
- Mail template with auto-attachment
- Computed fields with dependencies
- Date calculations using timedelta
- Monetary fields with currency support
- Binary field for signature storage
- Selection fields for enumerations
- Many2one relations to res.country, hr.department, hr.employee
- Custom actions for PDF generation and email sending
- Notification system integration

### Documentation
- Comprehensive README with 400+ lines
- Installation guide (INSTALL.md)
- Changelog (CHANGELOG.md)
- Usage examples with step-by-step instructions
- Troubleshooting section
- Database schema documentation
- API reference for custom methods
- Brand identity guidelines
- UAE compliance checklist

### Assets
- SCSS report styling
- Company logo placeholder
- Module icon and banner placeholders
- Email template with inline CSS

---

## [Unreleased]

### Planned for v17.0.2.0.0
- Multi-language support (Arabic + English)
- Digital signature integration (DocuSign API)
- Custom branding per company (multi-company scenarios)
- Offer letter templates library
- Candidate portal for self-service offer acceptance
- Integration with onboarding module
- Advanced analytics dashboard
- Mobile app support
- Bulk offer generation
- Template customization UI

### Under Consideration
- Video call scheduling integration
- WhatsApp notification support
- SMS offer delivery
- QR code for offer verification
- Blockchain-based document verification
- AI-powered salary recommendations
- Market rate comparison
- Automated background check integration

---

## Version History

| Version | Release Date | Status | Key Features |
|---------|--------------|--------|---------------|
| 17.0.1.0.0 | 2024-11-14 | ✅ Released | Initial UAE-compliant system |
| 17.0.2.0.0 | TBD | 🔄 Planned | Multi-language, digital signatures |

---

## Migration Guide

### From Standard hr_recruitment

This module extends the standard `hr_recruitment` module without breaking existing functionality.

**No migration required** - all existing applicant data remains intact.

**New fields added:**
- All new fields are optional
- Existing workflows continue to work
- New tabs appear alongside standard tabs
- Standard offer letter process unchanged

**Steps to adopt:**
1. Install module alongside existing setup
2. Gradually populate new fields for new applicants
3. Generate offer letters using new template
4. Optionally backfill existing applicants with new data

---

## Support & Feedback

**Found a bug?**
- Email: support@sgctech.ai
- Include: Odoo version, module version, error logs

**Feature request?**
- Email: features@sgctech.ai
- Describe: Use case, expected behavior, benefits

**Contributing:**
- Fork repository
- Create feature branch
- Submit pull request with tests

---

**Maintained by:** Scholarix Global Development Team
**License:** LGPL-3
**Website:** www.sgctech.ai

Navigate. Innovate. Transform.
