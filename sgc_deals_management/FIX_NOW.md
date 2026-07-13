# IMMEDIATE FIX - Server Has Old Files

## Problem
The error shows line 67 of the menu file on the server STILL contains the old project menu reference.

**Your local file does NOT have this line. Files were uploaded to the WRONG LOCATION.**

**CORRECT PATH:** `/var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/`

---

## Step 1: CHECK SERVER FILE (DO THIS FIRST)

SSH into your server and run:

```bash
wc -l /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml
```

**Expected Output:** `99 /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml`

**If it shows MORE than 99 lines** → The old file is still there. Proceed to Step 2.

---

## Step 2: DELETE OLD MODULE COMPLETELY

```bash
# Remove the entire old module from CORRECT location
sudo rm -rf /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management

# Verify it's gone
ls -la /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/ | grep deals
```

Should show NOTHING.

---

## Step 3: RE-UPLOAD THE MODULE TO CORRECT LOCATION

From your Windows machine (PowerShell):

```powershell
# Create a zip of the clean module
Compress-Archive -Path "D:\01_WORK_PROJECTS\odoo-mcp-server\deals_management\*" -DestinationPath "D:\deals_management.zip" -Force
```

Then upload `deals_management.zip` to your server and extract **IN THE CORRECT LOCATION**:

```bash
# On server - upload the zip to /tmp/ first
cd /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/
sudo unzip /tmp/deals_management.zip -d deals_management
sudo chown -R odoo:odoo deals_management
sudo chmod -R 755 deals_management
```

---

## Step 4: VERIFY THE NEW FILE

```bash
# Check line count (should be 99)
wc -l /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml

# Check for the bad reference (should return NOTHING)
grep "menu_deals_projects" /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml
grep "action_deals_projects" /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml
```

Both grep commands should return **NO OUTPUT**.

---

## Step 5: CLEAN DATABASE

```bash
# One-liner to remove all cached data
sudo -u postgres psql scholarixv2 -c "DELETE FROM ir_ui_menu WHERE id IN (SELECT res_id FROM ir_model_data WHERE module = 'deals_management' AND model = 'ir.ui.menu'); DELETE FROM ir_act_window WHERE id IN (SELECT res_id FROM ir_model_data WHERE module = 'deals_management' AND model = 'ir.actions.act_window'); DELETE FROM ir_ui_view WHERE id IN (SELECT res_id FROM ir_model_data WHERE module = 'deals_management' AND model = 'ir.ui.view'); DELETE FROM ir_model_data WHERE module = 'deals_management'; UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'deals_management';"
```

---

## Step 6: RESTART ODOO

```bash
sudo systemctl restart odoo
sudo systemctl status odoo
```

Wait 30 seconds for Odoo to fully start.

---

## Step 7: INSTALL MODULE

1. Login to Odoo at `https://erp.sgctech.ai`
2. Go to **Apps**
3. Remove all filters
4. Click **Update Apps List**
5. Search for **"Deals Management"**
6. Click **Install**

✅ **It will work this time because:**
- Old file is deleted
- New file is in place (verified with grep)
- Database cache is cleared
- Odoo is restarted

---

## Quick Verification Script

Run this BEFORE Step 7 to verify everything is ready:

```bash
echo "=== VERIFICATION ==="
echo ""
echo "1. File line count (should be 99):"
wc -l /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml
echo ""
echo "2. Bad references (should be EMPTY):"
grep -n "menu_deals_projects\|action_deals_projects" /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml || echo "✅ No bad references found"
echo ""
echo "3. Database cleanup (should be 0 rows):"
sudo -u postgres psql scholarixv2 -c "SELECT COUNT(*) FROM ir_model_data WHERE module = 'deals_management';"
echo ""
echo "4. Odoo status:"
sudo systemctl status odoo | grep "Active:"
echo ""
echo "=== If all checks pass, proceed to install in Odoo UI ==="
```

Expected output:
```
=== VERIFICATION ===

1. File line count (should be 99):
99 /var/odoo/scholarixv2/extra-addons/odooapps.git-68ee71eda34bc/deals_management/views/deals_menu.xml

2. Bad references (should be EMPTY):
✅ No bad references found

3. Database cleanup (should be 0 rows):
 count 
-------
     0
(1 row)

4. Odoo status:
   Active: active (running) since Fri 2026-01-17 14:30:15 UTC; 1min ago

=== If all checks pass, proceed to install in Odoo UI ===
```
