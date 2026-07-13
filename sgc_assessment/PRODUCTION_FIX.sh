#!/bin/bash
# Fix circular import error on production server
# Run this on the production server: /var/odoo/scholarixv2/

echo "🔧 Fixing scholarix_assessment circular import error..."

# Navigate to the module directory
cd /var/odoo/scholarixv2/extra-addons/odooapps.git-*/scholarix_assessment

echo "📁 Current directory: $(pwd)"

# Remove all Python cache files
echo "🧹 Cleaning Python cache files..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove any duplicate or backup files
echo "🧹 Removing backup files..."
find . -type f \( -name "*~" -o -name "*.bak" -o -name "*.orig" \) -delete

# Verify controllers structure
echo "✅ Verifying module structure..."
ls -la controllers/

# Restart Odoo service
echo "🔄 Restarting Odoo service..."
sudo systemctl restart odoo

echo "✅ Done! Check Odoo logs with: sudo journalctl -u odoo -f"
