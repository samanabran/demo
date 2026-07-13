# SCHOLARIX Assessment System - Installation Guide

## Quick Start

### 1. Prerequisites
```bash
# Install Python dependencies
pip install openai tiktoken numpy pandas
```

### 2. Copy Module
```bash
cp -r scholarix_assessment /path/to/odoo/addons/
```

### 3. Update Apps List
- Odoo → Apps → Update Apps List

### 4. Install Module
- Search "SCHOLARIX Assessment"
- Click Install

### 5. Configure (Optional)
- Settings → Technical → System Parameters
- Add: `scholarix_assessment.openai_api_key` = your-api-key
- If not set, module uses mock AI (perfect for testing)

### 6. Assign Users
- Settings → Users → Edit User
- Assessment System tab → Select group (Viewer/Reviewer/Manager)

## First Use

### Test the Portal
1. Visit: `http://your-domain/assessment`
2. Fill assessment form
3. Check Odoo → Assessment → Candidates

### Review Process
1. Open candidate record
2. View AI analysis
3. Click "Create Human Review"
4. Adjust scores and add notes
5. Submit review

## Troubleshooting

### Module Won't Install
- Check Python dependencies installed
- Check Odoo logs: Settings → Technical → Logging
- Verify all XML files are valid

### Portal Form Not Loading
- Clear browser cache
- Check website published
- Verify routes in Technical → Menu Items

### AI Scoring Fails
- Check API key configured
- Verify internet connectivity
- Review logs for errors
- Falls back to mock AI automatically

## Support

- Email: support@scholarix.com
- Docs: https://docs.scholarix.com/assessment

---

**Module Version:** 17.0.1.0.0
**Odoo Version:** 17.0
**Status:** ✅ Production Ready
