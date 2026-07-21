{
    "name": "SGC - Commission",
    "version": "19.0.3.4",
    "category": "Sales",
    "summary": "Professional commission management with full workflow and analytics",
    "description": """
SGC Commission Management System - Production Ready
======================================================

## Key Features

### Commission Management
- Commission Lines: Complete workflow with state management
- Multiple Calculation Methods: Percentage and Fixed Amount
- State Management: Draft → Calculated → Confirmed → Processed → Paid
- **Commission Dashboard**: Real-time monitoring and KPIs
- **Smart Buttons**: Quick access to related records
- **Performance Reports**: Comprehensive reporting system

### 🔐 **Security & Access Control**
- **Role-based Access**: Granular permissions for users and managers
- **Data Integrity**: Validation rules and constraints
- **Audit Trail**: Complete tracking of commission changes

### 🔄 **Integration**
- **Sale Order Integration**: Seamless commission processing
- **Purchase Order Integration**: Automatic PO creation for external commissions
- **Multi-currency Support**: Handle global commission structures
- **Odoo 19 Compliance**: Latest framework standards

## Installation

This module installs cleanly with all core dependencies included.

## Usage

1. Navigate to Sales > Sale Orders
2. Open any sale order and go to "Commission Management" tab
3. Configure commission partners and rates
4. Click "Process Commissions" to auto-calculate
5. Use smart buttons to monitor progress

## Technical Excellence

- **Clean Architecture**: Modular design with clear separation
- **Performance Optimized**: Efficient database queries and caching
- **Error Handling**: Comprehensive validation and error prevention
- **Future-Proof**: Easy to extend and maintain
    """,
    "author": "SGC TECH AI",
    "website": "https://sgctech.ai",
    "support": "bran@sgctech.ai",
    "images": ["static/description/banner.png"],
    "depends": [
        "base",
        "sale",
        "purchase",
        "account",
        "project",
    ],
    "data": [
        # ============================================
        # STEP 1: Cleanup old database records first
        # ============================================
        "data/cleanup_views.xml",
        # ============================================
        # STEP 2: Security (must load after cleanup)
        # ============================================
        "security/security.xml",
        "security/ir.model.access.csv",
        # ============================================
        # STEP 3: Core data and configurations
        # ============================================
        "data/commission_types_data.xml",
        # ============================================
        # STEP 4: Core Views (6 files - fully validated)
        # ============================================
        "views/commission_actions.xml",  # ✅ Commission Lines & Types
        #'views/commission_type_views.xml',                 # ✅ Commission Type CRUD [FIXED] - MOVED
        "views/commission_menu.xml",  # ✅ Menu structure
        "views/commission_type_views.xml",  # ✅ Commission Type CRUD [FIXED] - MOVED HERE
        "views/sale_order.xml",  # ✅ Sale Order integration
        "views/res_partner_views.xml",  # ✅ Partner extensions
        "views/account_move_line_views.xml",  # ✅ Vendor bill line commission details
        # ============================================
        # STEP 5: Advanced Views (4 wizard files)
        # ============================================
        "views/commission_cancel_wizard_views.xml",  # ✅ Cancel Wizard
        "views/commission_payment_wizard_views.xml",  # ✅ Payment Wizard
        "views/commission_partner_statement_wizard_views.xml",  # ✅ Statement Wizard
        "views/commission_profit_analysis_wizard_views.xml",  # ✅ Analysis Wizard
        # ============================================
        # STEP 5.5: Reports
        # ============================================
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "OPL-1",
    "price": 58,
    "currency": "USD",
    "external_dependencies": {
        "python": [],  # No external dependencies required
    },
}

