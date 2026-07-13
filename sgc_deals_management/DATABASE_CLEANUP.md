# CRITICAL FIX - Remove Cached Module Data

## Problem
The server has cached the old version of deals_management in the database. Even after uploading new files and restarting, Odoo loads the old menu structure from the database cache.

## Solution: Clean Database Before Reinstalling

### Step 1: SSH into Your Server

### Step 2: Run These SQL Commands

```bash
# Connect to PostgreSQL (adjust database name if different)
sudo -u postgres psql scholarixv2
```

### Step 3: Delete Old Module Data

```sql
-- Delete all deals_management menu items
DELETE FROM ir_ui_menu WHERE id IN (
    SELECT res_id FROM ir_model_data 
    WHERE module = 'deals_management' AND model = 'ir.ui.menu'
);

-- Delete all deals_management actions
DELETE FROM ir_act_window WHERE id IN (
    SELECT res_id FROM ir_model_data 
    WHERE module = 'deals_management' AND model = 'ir.actions.act_window'
);

-- Delete all deals_management views
DELETE FROM ir_ui_view WHERE id IN (
    SELECT res_id FROM ir_model_data 
    WHERE module = 'deals_management' AND model = 'ir.ui.view'
);

-- Delete all ir_model_data entries for deals_management
DELETE FROM ir_model_data WHERE module = 'deals_management';

-- Mark module as not installed
UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'deals_management';

-- Exit PostgreSQL
\q
```

### Step 4: Clear Odoo Cache & Restart

```bash
# Remove Odoo cache
sudo rm -rf /var/odoo/scholarixv2/.local/share/Odoo/filestore/scholarixv2/deals_management
sudo rm -rf /var/odoo/scholarixv2/src/odoo/addons/__pycache__/deals_management*

# Restart Odoo
sudo systemctl restart odoo

# Check status
sudo systemctl status odoo
```

### Step 5: Verify Files Are Updated

```bash
# Check the menu file to ensure it doesn't have the old reference
cat /var/odoo/scholarixv2/extra-addons/deals_management/views/deals_menu.xml | grep -n "menu_deals_projects"

# Should return NOTHING. If it returns results, the file wasn't updated properly.
```

### Step 6: Re-upload Files (If Needed)

If Step 5 shows the old file is still there:

```bash
# Backup the old module
sudo mv /var/odoo/scholarixv2/extra-addons/deals_management /var/odoo/scholarixv2/extra-addons/deals_management.old

# Re-upload the new module from your local machine
# Then set permissions again:
sudo chown -R odoo:odoo /var/odoo/scholarixv2/extra-addons/deals_management
sudo chmod -R 755 /var/odoo/scholarixv2/extra-addons/deals_management
```

### Step 7: Install Module

1. Login to Odoo
2. Go to Apps
3. Remove all filters
4. Click "Update Apps List"
5. Search for "Deals Management"
6. Click Install

---

## Alternative: Use Odoo Shell (Easier Method)

```bash
# Access Odoo shell
sudo -u odoo /var/odoo/scholarixv2/venv/bin/python /var/odoo/scholarixv2/src/odoo-bin shell -c /var/odoo/scholarixv2/src/odoo.conf -d scholarixv2
```

Then run in the shell:

```python
# Find the module
module = env['ir.module.module'].search([('name', '=', 'deals_management')])

# Uninstall completely (removes all data)
module.button_immediate_uninstall()

# Exit
exit()
```

Then restart Odoo and install fresh:

```bash
sudo systemctl restart odoo
```

---

## Quick One-Liner Solution

```bash
sudo -u postgres psql scholarixv2 -c "DELETE FROM ir_ui_menu WHERE id IN (SELECT res_id FROM ir_model_data WHERE module = 'deals_management' AND model = 'ir.ui.menu'); DELETE FROM ir_act_window WHERE id IN (SELECT res_id FROM ir_model_data WHERE module = 'deals_management' AND model = 'ir.actions.act_window'); DELETE FROM ir_ui_view WHERE id IN (SELECT res_id FROM ir_model_data WHERE module = 'deals_management' AND model = 'ir.ui.view'); DELETE FROM ir_model_data WHERE module = 'deals_management'; UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'deals_management';" && sudo systemctl restart odoo
```

---

## After Cleanup - Verify

```bash
# Check if old data is gone
sudo -u postgres psql scholarixv2 -c "SELECT * FROM ir_model_data WHERE module = 'deals_management' LIMIT 5;"

# Should return 0 rows
```

Then proceed with fresh installation through Odoo UI.
