# XML Syntax Error Fix - Portal Assessment Templates

## Error Details
**File:** `portal_assessment_templates.xml`  
**Line:** 201  
**Error:** `lxml.etree.XMLSyntaxError: StartTag: invalid element name, line 201, column 44`

## Root Cause
The JavaScript code inside the `<script>` tag contained HTML tags (like `<i>` and `<span>`) that were being interpreted as XML elements, causing a parsing error.

Additionally:
1. The `t-esc` QWeb directive was embedded directly in JavaScript without proper escaping
2. The `&amp;&amp;` XML entity was used instead of `&&` in JavaScript

## Fixes Applied

### 1. Wrapped JavaScript in CDATA Section
```xml
<!-- BEFORE -->
<script type="text/javascript">
    (function() {
        // JavaScript code with HTML strings
        timerWarning.innerHTML = '<i class="fa fa-exclamation-triangle"></i>';
    })();
</script>

<!-- AFTER -->
<script type="text/javascript">
    <![CDATA[
    (function() {
        // JavaScript code with HTML strings (now safe)
        timerWarning.innerHTML = '<i class="fa fa-exclamation-triangle"></i>';
    })();
    ]]>
</script>
```

### 2. Fixed QWeb Directive Embedding
```xml
<!-- BEFORE -->
const TIMER_DURATION = parseInt('<t t-esc="time_limit or 45"/>') * 60;

<!-- AFTER -->
const TIMER_DURATION = parseInt(']]><t t-esc="time_limit or 45"/><![CDATA[') * 60;
```

This temporarily closes the CDATA section, allows QWeb to process the directive, then reopens CDATA.

### 3. Fixed JavaScript Operators
```javascript
// BEFORE (XML-escaped)
if (timeRemaining > 0 &amp;&amp; timeRemaining < TIMER_DURATION) {

// AFTER (proper JavaScript inside CDATA)
if (timeRemaining > 0 && timeRemaining < TIMER_DURATION) {
```

## Changes Summary

**File:** `scholarix_assessment/views/portal_assessment_templates.xml`

**Lines Modified:**
- **Line ~131:** Added `<![CDATA[` after opening `<script>` tag
- **Line ~137:** Fixed QWeb embedding: `']]><t t-esc="time_limit or 45"/><![CDATA['`
- **Line ~283:** Changed `&amp;&amp;` to `&&`
- **Line ~304:** Added `]]>` before closing `</script>` tag

## Why This Works

**CDATA Section Benefits:**
1. Treats content as raw character data, not XML
2. Allows `<`, `>`, `&` without escaping
3. Preserves HTML strings in JavaScript
4. No conflict with XML parser

**QWeb Directive Handling:**
- Temporarily break out of CDATA to allow QWeb processing
- Pattern: `']]><t t-esc="..."/><![CDATA['`
- Ensures dynamic values are still rendered

## Testing

After this fix, the module should:
- ✅ Load without XML parsing errors
- ✅ Timer JavaScript executes correctly
- ✅ HTML strings in JavaScript render properly
- ✅ QWeb directives still process dynamic values
- ✅ All timer functionality works as designed

## Deployment

```bash
# Clear cache
bash clean_cache.sh

# Update module (local Docker)
docker-compose exec odoo odoo --update=scholarix_assessment --stop-after-init

# Update module (production)
cd /var/odoo/scholarixv2
sudo -u odoo venv/bin/python3 src/odoo-bin -c odoo.conf --no-http --stop-after-init --update scholarix_assessment
```

## Verification

```bash
# Check for XML errors in logs
tail -f /var/log/odoo/odoo.log | grep "XMLSyntaxError"

# If no errors, test the routes:
# - http://your-domain.com/assessment
# - http://your-domain.com/assessment/start
```

---

**Status:** ✅ Fixed  
**Date:** 2025-11-14  
**Files Changed:** 1 (`portal_assessment_templates.xml`)  
**Lines Changed:** 4
