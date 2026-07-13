# Changelog — SGC - Employment Certificate

All notable changes to `sgc_employment_certificate` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [19.0.1.0.0] - 2026-06-19

### Added
- Odoo 19 compatibility release
- Updated manifest to Odoo 19 format and conventions
- Consistent SGC TECH AI branding (logo, banner, icon)
- Premium Odoo Apps Store description (`static/description/index.html`)
- Comprehensive README.md with usage and architecture details

### Changed
- Verified and refreshed all Python imports for Odoo 19 API
- Validated XML view files for Odoo 19 compatibility
- Refreshed `__manifest__.py` metadata
- Updated documentation and inline help strings

### Fixed
- Resolved deprecated API usage where present
- Standardized security group and ACL structure
- Cleaned up residual assets and stale documentation

### Security
- Audited controller routes (`auth=`, `csrf=`)
- Verified `sudo()` usage scope in controllers and models
- Confirmed record rules match Odoo 19 multi-company patterns
- Confirmed ACL coverage in `security/ir.model.access.csv`

## Notes

- Run `odoo-bin --update=sgc_employment_certificate --stop-after-init` after upgrading
- Clear browser cache and restart Odoo service for asset regeneration
- Refer to `static/description/index.html` for the Apps Store listing

---

**Format**: [Keep a Changelog](https://keepachangelog.com/)
**Versioning**: [Semantic Versioning](https://semver.org/)
