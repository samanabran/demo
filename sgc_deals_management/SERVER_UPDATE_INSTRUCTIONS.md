# Server Update Instructions - Deals Management Module

## 📂 Files to Upload

Upload the entire `deals_management` folder to your server at:
**Server Path:** `/var/odoo/scholarixv2/extra-addons/deals_management`

### File List (summary):
```
deals_management/
├── __init__.py
├── __manifest__.py
├── commission_ax/              # Commission engine (merged)
├── models/
├── reports/
├── security/
├── views/
└── *.md                        # Manuals and references
```

---

## 🚀 Upload Methods

### Method 1: Using SCP (Recommended)
```bash
scp -r "D:\01_WORK_PROJECTS\odoo-mcp-server\deals_management" user@your-server:/var/odoo/scholarixv2/extra-addons/
```

### Method 2: Using WinSCP/FileZilla
1. Connect to your server via SFTP
2. Navigate to `/var/odoo/scholarixv2/extra-addons/`
3. Upload the entire `deals_management` folder
4. Ensure all subdirectories (models, views, security) are uploaded

### Method 3: Using Git (if applicable)
```bash
# On server
cd /var/odoo/scholarixv2/extra-addons/
git pull origin your-branch
```

---

## 🔧 Server Commands (Run After Upload)

SSH into your server and execute these commands:

### Step 1: Set Correct Ownership
```bash
sudo chown -R odoo:odoo /var/odoo/scholarixv2/extra-addons/deals_management
```

### Step 2: Set Correct Permissions
```bash
sudo chmod -R 755 /var/odoo/scholarixv2/extra-addons/deals_management
```

### Step 3: Restart Odoo Service
```bash
sudo systemctl restart odoo
```

### Step 4: Verify Service is Running
```bash
sudo systemctl status odoo
```

### Step 5: Monitor Logs (Optional but Recommended)
```bash
sudo tail -f /var/log/odoo/odoo-server.log
```
*Press Ctrl+C to stop watching logs*

---

## ⚡ Quick One-Line Command

Copy and paste this entire command:

```bash
sudo chown -R odoo:odoo /var/odoo/scholarixv2/extra-addons/deals_management && \
sudo chmod -R 755 /var/odoo/scholarixv2/extra-addons/deals_management && \
sudo systemctl restart odoo && \
sudo systemctl status odoo
```

---

## 🎯 Install Module in Odoo (After Restart)

1. **Login to Odoo** web interface
2. **Navigate to Apps** menu
3. **Click "Update Apps List"** (three dots menu → Update Apps List)
4. **Remove any search filters**
5. **Search for:** "Deals Management Clean"
6. **Click Install**

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Module appears in Apps list
- [ ] "Deals" menu appears in top navigation
- [ ] "Commissions" menu appears in top navigation
- [ ] Can create a new deal (Deals → All Deals → Create)
- [ ] All 5 deal type filters work (Primary, Secondary, Exclusive, Rental)
- [ ] Commission menus are accessible
- [ ] No errors in Odoo logs

---

## 🐛 Troubleshooting

### If module doesn't appear in Apps:
```bash
# Check file permissions
ls -la /var/odoo/scholarixv2/extra-addons/deals_management

# Check Odoo logs for errors
sudo tail -100 /var/log/odoo/odoo-server.log
```

### If installation fails:
1. Check the error message in Odoo
2. Check server logs: `sudo tail -f /var/log/odoo/odoo-server.log`
3. Verify all dependencies are installed:
    - sale
    - purchase
    - account
    - project
    - mail
    - hr
    - utm

### If menus don't appear:
1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache
3. Restart Odoo service again

---

## 📞 Support

If you encounter issues:
1. Check the ODOO17_COMPLIANCE.md file for technical details
2. Review DEVELOPER_GUIDE.md for common issues
3. Check API_REFERENCE.md for field/method documentation

---

**Last Updated:** January 17, 2026
**Module Version:** 17.0.2.0.0
**Odoo Version:** 17.0
