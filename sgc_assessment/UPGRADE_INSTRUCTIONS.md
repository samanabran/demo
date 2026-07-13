# scholarix_assessment Module Upgrade Instructions

## Issues Fixed in Latest Update

1. ✅ **Submit button error** - Removed duplicate email validation
2. ✅ **Duplicate submission constraint** - Users can now submit multiple assessments
3. ✅ **Regenerate score deleting records** - Now updates instead of deleting

## Current Error: Report Action Not Found

**Error Message:**
```
External ID not found in the system: scholarix_assessment.action_report_assessment_candidate
```

**Cause:** The module needs to be upgraded in Odoo to register the report action in the database.

## Upgrade Steps

### Method 1: Via Odoo UI (Recommended)

1. **Access Apps Menu:**
   - Log in to Odoo as Administrator
   - Go to: **Apps** menu

2. **Upgrade Module:**
   - Remove the "Apps" filter from the search bar
   - Search for: `scholarix_assessment`
   - Click on the module
   - Click **"Upgrade"** button
   - Wait for upgrade to complete

3. **Restart Odoo Server (Optional but Recommended):**
   ```bash
   sudo systemctl restart odoo
   # or
   sudo service odoo restart
   ```

### Method 2: Via Command Line

```bash
# Navigate to Odoo directory
cd /var/odoo/scholarixv2

# Upgrade the module
./odoo-bin -u scholarix_assessment -d YOUR_DATABASE_NAME --stop-after-init

# Restart Odoo
sudo systemctl restart odoo
```

### Method 3: Via Python Shell

```python
# Connect to Odoo shell
# odoo shell -d YOUR_DATABASE_NAME

# In Odoo shell:
env['ir.module.module'].search([('name', '=', 'scholarix_assessment')]).button_immediate_upgrade()
env.cr.commit()
```

## Database Migration Required

Since we removed the SQL constraint on email uniqueness, you need to drop the existing constraint:

### SQL Migration Script

```sql
-- Connect to your PostgreSQL database
-- psql -U odoo -d YOUR_DATABASE_NAME

-- Drop the old email unique constraint
ALTER TABLE assessment_candidate DROP CONSTRAINT IF EXISTS assessment_candidate_email_unique;

-- Verify constraint is removed
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'assessment_candidate';
```

### Run Migration via Odoo Shell (Alternative)

```python
# odoo shell -d YOUR_DATABASE_NAME

# Drop the constraint using raw SQL
env.cr.execute("""
    ALTER TABLE assessment_candidate
    DROP CONSTRAINT IF EXISTS assessment_candidate_email_unique;
""")
env.cr.commit()
print("Constraint dropped successfully")
```

## Verification Steps

After upgrade, verify the following:

### 1. Check Report Action Registration

```python
# In Odoo shell
report = env.ref('scholarix_assessment.action_report_assessment_candidate', raise_if_not_found=False)
if report:
    print(f"✅ Report found: {report.name}")
    print(f"   Model: {report.model}")
    print(f"   Type: {report.report_type}")
else:
    print("❌ Report NOT found - upgrade may have failed")
```

### 2. Test Duplicate Submission

1. Go to assessment portal: `/assessment/start`
2. Submit an assessment with email: `test@example.com`
3. Submit another assessment with the same email
4. **Expected:** Second submission should succeed ✅
5. **Old behavior:** Would show error ❌

### 3. Test Report Generation

1. Go to: **Assessment > Candidates**
2. Open any candidate with scores
3. Click: **Print** > **Assessment Report**
4. **Expected:** PDF should download successfully ✅
5. **Old behavior:** Would show "External ID not found" error ❌

### 4. Test Regenerate Score

1. Go to any candidate with AI score
2. Click: **Regenerate Score** button
3. **Expected:** Score updates and notification shows success ✅
4. **Old behavior:** Record would be deleted ❌

## Troubleshooting

### Issue: Upgrade fails with constraint error

**Solution:**
```sql
-- Manually drop the constraint first
ALTER TABLE assessment_candidate DROP CONSTRAINT IF EXISTS assessment_candidate_email_unique;
```

Then retry the upgrade.

### Issue: Report still not found after upgrade

**Possible causes:**
1. Upgrade didn't complete successfully - check logs
2. XML file has syntax error - validate XML
3. Module dependency issue - ensure all dependencies installed

**Solution:**
```bash
# Force module update with no cache
./odoo-bin -u scholarix_assessment -d YOUR_DATABASE_NAME --stop-after-init --no-http

# Check Odoo logs
tail -f /var/log/odoo/odoo-server.log
```

### Issue: Some candidates can't submit due to existing constraint

**Solution:**
Run the SQL migration script above to drop the constraint.

## Rollback Plan (If Needed)

If you need to rollback these changes:

1. **Restore email uniqueness:**
```sql
ALTER TABLE assessment_candidate
ADD CONSTRAINT assessment_candidate_email_unique UNIQUE(email);
```

2. **Revert code changes:**
```bash
git checkout HEAD~1
# Then upgrade module again
```

## Expected Behavior After Upgrade

✅ Users can submit multiple assessments with same email
✅ No errors when clicking submit button
✅ Regenerate score updates existing record
✅ PDF reports can be generated
✅ All existing functionality continues to work

## Support

If issues persist after following these steps:
1. Check Odoo logs: `/var/log/odoo/odoo-server.log`
2. Verify all files are updated: `git status`
3. Ensure PostgreSQL version compatibility
4. Contact system administrator for database access if needed

---

**Last Updated:** 2025-11-15
**Module Version:** 17.0.2.0.0
**Odoo Version:** 17.0
