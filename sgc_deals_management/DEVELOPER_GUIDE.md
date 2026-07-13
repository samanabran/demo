# Deals Management Clean - Developer Quick Reference

## 🚀 Quick Start

### Module Location

```
deals_management/
```

### Install Module

```bash
# In Odoo terminal
$ odoo -i deals_management
```

Apps → Deals Management Clean → Install

---

## 📚 File Structure & Purpose

### `__manifest__.py`

- Module metadata and dependencies
- Declares version: **17.0.2.0.0**
- Lists all XML data files to load
- Specifies required modules: sale, purchase, account, project, mail, hr, utm

### `__init__.py`

- Module initialization
- Imports core models and commission subpackage

### Model Files

#### `models/sale_order_deals.py`
**Key Features:**
- Extends `sale.order` model
- Adds deal-specific fields (sales_type, buyers, project, dates)
- Computes financial values (VAT, commissions, totals)
- Handles document attachments

**Key Methods:**
```python
_compute_deal_sales_value()      # Calculates sales value
_compute_primary_commission()     # Computes commission amount
_compute_financial_summary()      # Calculates VAT and totals
_compute_document_counts()        # Counts attached documents
action_view_invoices()           # Smart button for invoices
action_view_commissions()        # Smart button for commissions
action_view_bills()              # Smart button for bills
action_view_kyc_documents()      # Smart button for KYC docs
- `view_order_deals_tree` - Main deal list view
- `view_order_deals_form` - Detailed deal form with smart buttons
- `view_order_deals_search` - Search and filter interface
- `action_all_deals` - View all deals action
- `action_primary_deals` - Filter primary sales
- `action_secondary_deals` - Filter secondary sales
- `action_exclusive_deals` - Filter exclusive sales
- `action_rental_deals` - Filter rental deals

#### `project_unit_views.xml`
- Project management views
- Unit/Sale order line views
- Associated actions and search views

**Contains:**
- Commission line form views

#### `commission_line_views.xml`
- Enhanced commission form with bill creation
- Tree view enhancements
#### `deals_menu.xml`
**Contains:**

### Security Files
#### `security/ir.model.access.csv`
**Access Control Rules:**

## 🎯 Key Fields Added to sale.order

- `primary_buyer_id` - Main buyer (link to res.partner)
- `secondary_buyer_id` - Co-buyer (link to res.partner)
- `project_id` - Property project (link to project.project)

### Char Fields
- `unit_reference` - Unit/property identifier

### Date Fields
- `booking_date` - When deal was booked
- `estimated_invoice_date` - Expected invoice date

### Monetary Fields
- `deal_sales_value` - Sales value
- `vat_amount` - Calculated VAT
- `total_without_vat` - Total excluding VAT

### Float Fields
- `deal_commission_rate` - Commission percentage

### Integer Fields
- `invoice_count` - Number of related invoices
- `commission_count` - Number of commissions
- `bill_count` - Number of vendor bills
- `kyc_document_count` - KYC document count
- `passport_count` - Passport copy count

### Many2many Fields
### Access Deals Module
2. **View all deals:** Click "All Deals"
3. **Filter by type:** Use sidebar filters (Primary Sales, Secondary Sales, etc.)
4. **Create new deal:** Click "Create" button

### Create a Deal
1. Go to Deals → All Deals
2. Click "Create"
3. Fill in deal information:
   - Sales Type (required)
   - Project and Unit Reference
   - Booking Date
   - Estimated Invoice Date
4. Add documents in "Deals Information" tab:
   - KYC Documents
   - Booking Forms/SPA
   - Passports
5. Click "Save"

### Access Financial Summary
1. Open any deal
2. Click "Deals Information" tab
3. View financial details section:
   - Sales Value
   - Commission Rate
   - VAT Amount
   - Total with/without VAT

### Access Related Documents
1. Open any deal
2. Use smart buttons in header:
   - **Invoices** - View related invoices
   - **Commissions** - View commission records
   - **Bills** - View vendor bills
   - **KYC Docs** - View KYC documents
   - **Booking/SPA** - View booking forms
   - **Passports** - View passport copies

### Access Projects
1. Navigate: Menu → Projects
2. **Projects:** View all projects
3. **Units:** View sale order lines from deals

### Access Commissions
1. Navigate: Menu → Commissions
2. **All Commissions** - View all commission records
3. **Pending Bills** - Commissions without bills
4. **Paid Bills** - Commissions with bills
5. **Commission by Partner** - Grouped view
6. **Vendor Bills** - Account bills
7. **Commission Report** - Analytics view

---

## 🛠️ Development Tips

### Adding New Fields to Deals

Add to `models/sale_order_deals.py`:

```python
@api.depends('parent_field')
def _compute_new_field(self):
    for record in self:
        record.new_field = record.parent_field * 2

new_field = fields.Float(
    string='New Field',
    compute='_compute_new_field',
    tracking=True
)
```

### Adding New Views

Create in `views/deals_views.xml`:

```xml
<record id="view_order_deals_custom" model="ir.ui.view">
    <field name="name">sale.order.deals.custom</field>
    <field name="model">sale.order</field>
    <field name="arch" type="xml">
        <form string="Custom Form">
            <sheet>
                <field name="name"/>
                <!-- Add fields here -->
            </sheet>
        </form>
    </field>
</record>
```

### Adding New Actions

Create in `views/deals_views.xml`:

```xml
<record id="action_new_deals" model="ir.actions.act_window">
    <field name="name">New Deals</field>
    <field name="res_model">sale.order</field>
    <field name="view_mode">tree,form</field>
    <field name="domain">[('sales_type', '=', 'primary')]</field>
</record>
```

### Adding New Menus

Create in `views/deals_menu.xml`:

```xml
<menuitem id="menu_new_action"
    name="New Menu Item"
    parent="menu_deals_root"
    action="action_new_deals"
    sequence="10"/>
```

---

## 📊 Smart Buttons Implementation

All smart buttons use the following pattern:

```xml
<button name="action_method_name" 
    type="object" 
    class="oe_stat_button" 
    icon="fa-icon-name"
    invisible="counter_field == 0">
    <field name="counter_field" widget="statinfo" string="Label"/>
</button>
```

---

## 🔐 Security & Permissions

### User Permissions
- Read: Can view all deals
- Write: Can edit deals
- Create: Can create new deals
- Delete: Can delete deals

### Manager Permissions
- All user permissions plus:
- Full control over all records

### Custom Rules
To add group-based security rules, create `security/sale_order_rule.xml`:

```xml
<record id="sale_order_rule_user" model="ir.rule">
    <field name="name">User can see own deals</field>
    <field name="model_id" ref="sale.model_sale_order"/>
    <field name="domain_force">[('user_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
</record>
```

---

## 🧪 Testing

### Test Deal Creation
```python
def test_create_deal(self):
    deal = self.env['sale.order'].create({
        'partner_id': self.partner.id,
        'sales_type': 'primary',
        'primary_buyer_id': self.partner.id,
        'booking_date': fields.Date.today(),
    })
    self.assertEqual(deal.sales_type, 'primary')
```

### Test Computed Fields
```python
def test_financial_summary(self):
    deal = self.env['sale.order'].create({...})
    deal.amount_untaxed = 100000
    deal.deal_commission_rate = 5
    self.assertEqual(deal.primary_commission, 5000)
```

---

## 📝 Common Issues & Solutions

### Issue: Smart buttons not showing
**Solution:** Ensure counter field is computed and has value > 0

### Issue: Documents not attaching
**Solution:** Check context includes `'default_res_model': 'sale.order'`

### Issue: Commission not calculating
**Solution:** Verify `deal_commission_rate` field is filled

### Issue: Menu items not appearing
**Solution:** Ensure `action` attribute in menu references existing action

---

## 🚀 Performance Tips

1. **Use `optional="hide"`** for rarely-used fields in trees
2. **Index frequently searched fields** in database
3. **Use `widget="statinfo"`** for fast counter display
4. **Avoid complex computed fields** in list views
5. **Use domains** to filter data at source

---

## 📦 Deployment Checklist

- [ ] Module installed successfully
- [ ] All menus appear in UI
- [ ] Can create deals
- [ ] Can attach documents
- [ ] Commissions display correctly
- [ ] Smart buttons work
- [ ] Search filters work
- [ ] Proper access controls applied

---

## 📞 Support

For issues or questions:
1. Check ODOO17_COMPLIANCE.md for technical details
2. Review model definitions in `models/sale_order_deals.py`
3. Check view definitions in `views/`
4. Verify security rules in `security/ir.model.access.csv`

---

**Last Updated:** 2024  
**Odoo Version:** 17.0  
**Module Version:** 17.0.1.0.0
