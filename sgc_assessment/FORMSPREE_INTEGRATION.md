# Formspree Integration for SCHOLARIX Assessment System

## Overview
This integration automatically backs up all assessment submissions to Formspree, providing:
- External backup of candidate data
- Email notifications for new submissions
- Alternative data storage for compliance

## Setup Instructions

### 1. Create Formspree Account
1. Go to [https://formspree.io](https://formspree.io)
2. Sign up for a free or paid account
3. Create a new form project

### 2. Get Your Form ID
After creating a form, you'll get a Form ID like: `xyzabc123`

Your form endpoint will look like: `https://formspree.io/f/xyzabc123`

### 3. Configure in Odoo

#### Option A: Via System Parameters (Recommended)
1. Go to **Settings → Technical → System Parameters**
2. Add/Edit these parameters:

| Key | Value | Description |
|-----|-------|-------------|
| `scholarix_assessment.formspree_form_id` | `xyzabc123` | Your Formspree form ID |
| `scholarix_assessment.formspree_enabled` | `True` | Enable/disable integration |

#### Option B: Via Data File
Edit the file: `data/formspree_config_data.xml`

```xml
<record id="formspree_form_id" model="ir.config_parameter">
    <field name="key">scholarix_assessment.formspree_form_id</field>
    <field name="value">YOUR_ACTUAL_FORM_ID</field>
</record>
```

Then update the module:
```bash
docker-compose exec odoo odoo --update=scholarix_assessment --stop-after-init
```

### 4. Test the Integration
1. Submit a test assessment via the portal
2. Check Formspree dashboard for the submission
3. Check Odoo logs for confirmation:
   ```
   Assessment backed up to Formspree for candidate@email.com
   ```

## What Data is Sent

### Candidate Information
- Full name
- Email address
- Phone number
- Location
- Odoo experience
- Sales experience
- Submission date

### Assessment Responses
All 10 question answers with their corresponding questions

### AI Analysis (if available)
- Overall score
- Category scores (Technical, Sales, Communication, Learning, Cultural Fit)
- AI recommendation
- Identified strengths
- Skill gaps
- Confidence score

### Summary
A formatted text summary of the entire assessment

## Email Notifications

Configure Formspree to send email notifications:

1. In Formspree dashboard, go to your form settings
2. Set **Notification Email** to your recruitment team email
3. Customize the email template (optional)
4. Enable notifications

You'll receive an email for each new assessment submission.

## Security Considerations

### Data Privacy
- Formspree complies with GDPR
- Data is encrypted in transit (HTTPS)
- Configure data retention policies in Formspree

### Access Control
- Only authorized Formspree account users can access data
- Use Formspree's team features for multi-user access
- Enable 2FA on your Formspree account

### API Security
- Integration uses HTTPS POST requests
- No authentication credentials stored in Odoo
- Non-blocking implementation (won't fail submissions)

## Troubleshooting

### Integration Not Working

**Check System Parameters:**
```bash
# Via Odoo shell
docker-compose exec odoo odoo shell -d odoo
>>> env = api.Environment(cr, SUPERUSER_ID, {})
>>> env['ir.config_parameter'].get_param('scholarix_assessment.formspree_enabled')
>>> env['ir.config_parameter'].get_param('scholarix_assessment.formspree_form_id')
```

**Check Logs:**
```bash
docker-compose logs -f odoo | grep -i formspree
```

**Common Issues:**

| Issue | Solution |
|-------|----------|
| "Formspree form ID not configured" | Set the `formspree_form_id` system parameter |
| "Formspree integration disabled" | Set `formspree_enabled` to `True` |
| "Request timeout" | Check internet connectivity, increase timeout |
| "401/403 error" | Verify form ID is correct |

### Disable Integration Temporarily
Set `formspree_enabled` to `False`:
```bash
Settings → Technical → System Parameters
Key: scholarix_assessment.formspree_enabled
Value: False
```

### Test Connection Manually
```python
import requests

form_id = "YOUR_FORM_ID"
endpoint = f"https://formspree.io/f/{form_id}"

test_data = {
    "_subject": "Test Submission",
    "test_field": "Hello from Odoo"
}

response = requests.post(endpoint, json=test_data)
print(response.status_code)  # Should be 200
print(response.json())
```

## Integration Flow

```
Assessment Submitted
        ↓
Create Candidate Record
        ↓
Create Response Record
        ↓
Run AI Scoring
        ↓
[Commit Transaction]
        ↓
Send to Formspree ← Non-blocking, won't fail submission
        ↓
Send Confirmation Email
        ↓
Redirect to Thank You Page
```

## Formspree Limits

### Free Plan
- 50 submissions/month
- Email notifications
- Spam filtering
- Data retention: 1 month

### Paid Plans
- 1,000+ submissions/month
- Extended data retention
- Custom integrations
- Priority support

### Recommendations
- **Small teams (< 50 assessments/month):** Free plan
- **Medium teams (50-500 assessments/month):** Gold plan ($10/month)
- **Large teams (500+ assessments/month):** Platinum plan ($40/month)

## Advanced Configuration

### Custom Form Fields
Edit `utils/formspree_integration.py` to add/modify fields:

```python
def _prepare_payload(self, candidate, response, ai_score=None):
    payload = {
        # Add custom fields here
        'custom_field': 'custom_value',
        # ... existing fields
    }
```

### Multiple Form IDs
Use different form IDs for different purposes:

```python
# In controller
if assessment_type == 'junior':
    form_id = 'formspree_junior_form_id'
elif assessment_type == 'senior':
    form_id = 'formspree_senior_form_id'
```

### Webhooks
Configure Formspree webhooks to trigger actions in other systems:
1. Formspree Dashboard → Form Settings → Webhooks
2. Add webhook URL (e.g., Slack, Zapier, custom API)
3. Configure payload format

## Support

### Documentation
- [Formspree Docs](https://help.formspree.io/)
- [API Reference](https://formspree.io/docs)

### Contact
- Formspree Support: support@formspree.io
- SCHOLARIX Support: Check main README

## Changelog

### Version 1.0.0 (2025-11-15)
- Initial Formspree integration
- Automatic backup on submission
- System parameter configuration
- Non-blocking implementation
- Comprehensive data payload
- Error handling and logging
