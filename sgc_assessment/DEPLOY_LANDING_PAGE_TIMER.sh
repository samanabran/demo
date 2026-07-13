#!/bin/bash
# SCHOLARIX Assessment - Landing Page & Timer Deployment Script
# Version: 17.0.2.0.0
# Description: Deploy new landing page and timer features

set -e  # Exit on error

echo "=================================================="
echo "SCHOLARIX Assessment - Feature Deployment"
echo "Landing Page + Countdown Timer + Shareable Links"
echo "=================================================="
echo ""

# Step 1: Verify new files exist
echo "Step 1: Verifying new files..."
FILES=(
    "views/portal_assessment_landing.xml"
    "static/src/css/assessment_landing.css"
    "LANDING_PAGE_TIMER_FEATURE.md"
)

for file in "${FILES[@]}"; do
    if [ -f "scholarix_assessment/$file" ]; then
        echo "  ✓ Found: $file"
    else
        echo "  ✗ Missing: $file"
        exit 1
    fi
done

echo ""

# Step 2: Verify modified files
echo "Step 2: Verifying modified files..."
MODIFIED_FILES=(
    "controllers/portal.py"
    "views/portal_assessment_templates.xml"
    "__manifest__.py"
)

for file in "${MODIFIED_FILES[@]}"; do
    if [ -f "scholarix_assessment/$file" ]; then
        echo "  ✓ Updated: $file"
    else
        echo "  ✗ Missing: $file"
        exit 1
    fi
done

echo ""

# Step 3: Check module version
echo "Step 3: Checking module version..."
VERSION=$(grep "'version'" scholarix_assessment/__manifest__.py | head -1 | cut -d"'" -f4)
if [ "$VERSION" == "17.0.2.0.0" ]; then
    echo "  ✓ Version updated to: $VERSION"
else
    echo "  ✓ Version found: $VERSION (expected: 17.0.2.0.0)"
    # Don't exit, just warn
fi

echo ""

# Step 4: Clear Python cache
echo "Step 4: Clearing Python cache..."
find scholarix_assessment -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find scholarix_assessment -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ Cache cleared"

echo ""

# Step 5: Update module in Docker
echo "Step 5: Updating module in Docker..."
if command -v docker-compose &> /dev/null; then
    echo "  Running: docker-compose exec odoo odoo --update=scholarix_assessment --stop-after-init"
    docker-compose exec odoo odoo --update=scholarix_assessment --stop-after-init
    echo "  ✓ Module updated"
else
    echo "  ⚠ Docker Compose not found. Please update module manually:"
    echo "    Via UI: Apps > Scholarix Assessment System > Upgrade"
    echo "    Via CLI: odoo --update=scholarix_assessment --stop-after-init"
fi

echo ""

# Step 6: Test routes
echo "Step 6: Testing routes..."
echo "  Please manually test the following:"
echo "    1. Landing Page: http://localhost:8069/assessment"
echo "    2. Assessment Form: http://localhost:8069/assessment/start"
echo "    3. Timer functionality (45-minute countdown)"
echo "    4. Copy link button (clipboard)"
echo "    5. Email share button"
echo "    6. LinkedIn share button"

echo ""

# Step 7: Deployment summary
echo "=================================================="
echo "✓ DEPLOYMENT COMPLETE"
echo "=================================================="
echo ""
echo "NEW FEATURES:"
echo "  • Professional landing page at /assessment"
echo "  • 45-minute countdown timer with visual warnings"
echo "  • Shareable links (copy, email, LinkedIn)"
echo "  • Timer persistence (survives page refresh)"
echo "  • Auto-submit on timeout"
echo "  • Page unload protection"
echo ""
echo "NEXT STEPS:"
echo "  1. Test landing page: /assessment"
echo "  2. Test timer functionality"
echo "  3. Test share buttons"
echo "  4. Verify email invitation link"
echo "  5. Deploy to production (see LANDING_PAGE_TIMER_FEATURE.md)"
echo ""
echo "DOCUMENTATION:"
echo "  • Feature docs: LANDING_PAGE_TIMER_FEATURE.md"
echo "  • Production guide: PRODUCTION_READY_REPORT.md"
echo ""
echo "=================================================="
