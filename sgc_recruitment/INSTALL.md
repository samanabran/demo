# Installation Guide - Scholarix Recruitment Extension

## Prerequisites

- Odoo 17 installed (Community or Enterprise)
- Docker environment (recommended)
- `hr_recruitment` module enabled

## Installation Steps

### Docker Installation

```bash
# 1. Copy module to extra-addons
cp -r sgc_recruitment /path/to/odoo/extra-addons/

# 2. Restart Odoo
docker-compose restart odoo

# 3. Update apps list
# Go to: Settings > Apps > Update Apps List

# 4. Install module
# Go to: Apps > Search "Scholarix" > Install
```

## Post-Installation

1. **Add Company Logo**
   - Settings > General Settings > Companies
   - Upload PNG logo (recommended: 300x80px)

2. **Configure Email**
   - Settings > Technical > Outgoing Mail Servers
   - Set sender: careers@sgctech.ai

3. **Test Module**
   - Recruitment > Applications
   - Create test applicant
   - Verify new tabs appear
   - Generate sample offer letter

## Verification

✅ Personal Information tab visible
✅ Employment Details tab visible
✅ Compensation & Benefits tab visible
✅ Offer Letter tab visible
✅ "Generate Offer Letter" button present
✅ "Send Offer Letter" button present

## Troubleshooting

**Module not visible:**
```bash
docker-compose exec odoo odoo -u base --stop-after-init
```

**PDF not generating:**
```bash
# Install wkhtmltopdf
apt-get install wkhtmltopdf
```

**Email not sending:**
- Configure outgoing mail server
- Verify SMTP credentials
- Test email configuration

## Support

Email: support@sgctech.ai
Website: www.sgctech.ai
