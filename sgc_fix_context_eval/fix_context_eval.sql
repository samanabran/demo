-- ============================================================================
-- FIX: Client-side EvalError "Name 'user' is not defined"
-- ============================================================================
--
-- Root Cause:
--   Context/domain fields on ir_actions_act_window and ir_ui_menu are
--   evaluated by Odoo's JavaScript client using evaluateExpr(). The browser
--   evaluation context only provides {uid, lang, tz, allowed_company_ids, ...}
--   but NOT the full `user` record (res.users).
--
--   Expressions like `user.company_id.id` work server-side (Python) but
--   throw EvalError when evaluated in the browser.
--
-- Fix:
--   Replace `user.company_id.id`   →  `allowed_company_ids[0]`
--   Replace `user.company_id`      →  `allowed_company_ids[0]`
--
--   `allowed_company_ids[0]` is the first active company ID in the user's
--   current session — the browser-side equivalent.
--
-- Run this as superuser on your Odoo database.
-- ============================================================================

-- 1. Check which records are affected (dry-run preview)
-- ============================================================================
SELECT '=== ir_actions_act_window (context) ===' AS "Table";
SELECT id, name AS "Action Name", res_model AS "Model",
       context AS "Original Context"
FROM ir_actions_act_window
WHERE context LIKE '%user.company_id%';

SELECT '=== ir_actions_act_window (domain) ===' AS "Table";
SELECT id, name AS "Action Name", res_model AS "Model",
       domain AS "Original Domain"
FROM ir_actions_act_window
WHERE domain LIKE '%user.company_id%';

SELECT '=== ir_ui_menu (context) ===' AS "Table";
SELECT id, name AS "Menu Name",
       context AS "Original Context"
FROM ir_ui_menu
WHERE context LIKE '%user.company_id%';


-- 2. APPLY the fix (uncomment and run after reviewing the preview above)
-- ============================================================================

-- Fix ir_actions_act_window.context
-- UPDATE ir_actions_act_window
-- SET context = REPLACE(
--     REPLACE(context,
--         'user.company_id.id',
--         'allowed_company_ids[0]'
--     ),
--     'user.company_id',
--     'allowed_company_ids[0]'
-- )
-- WHERE context LIKE '%user.company_id%';

-- Fix ir_actions_act_window.domain
-- UPDATE ir_actions_act_window
-- SET domain = REPLACE(
--     REPLACE(domain,
--         'user.company_id.id',
--         'allowed_company_ids[0]'
--     ),
--     'user.company_id',
--     'allowed_company_ids[0]'
-- )
-- WHERE domain LIKE '%user.company_id%';

-- Fix ir_ui_menu.context
-- UPDATE ir_ui_menu
-- SET context = REPLACE(
--     REPLACE(context,
--         'user.company_id.id',
--         'allowed_company_ids[0]'
--     ),
--     'user.company_id',
--     'allowed_company_ids[0]'
-- )
-- WHERE context LIKE '%user.company_id%';


-- 3. Verify the fix (should return 0 rows after applying)
-- ============================================================================
SELECT '=== VERIFY: ir_actions_act_window (context) ===' AS "Check";
SELECT id, name, context
FROM ir_actions_act_window
WHERE context LIKE '%user.company%';

SELECT '=== VERIFY: ir_actions_act_window (domain) ===' AS "Check";
SELECT id, name, domain
FROM ir_actions_act_window
WHERE domain LIKE '%user.company%';

SELECT '=== VERIFY: ir_ui_menu (context) ===' AS "Check";
SELECT id, name, context
FROM ir_ui_menu
WHERE context LIKE '%user.company%';

-- Should be empty if all fixed.
-- If rows remain, check for variations like 'user . company_id' (with spaces).


-- 4. BROADER SCAN: Find any other client-side-evaluated user. references
--    that might cause similar errors.
-- ============================================================================
SELECT '=== OTHER CLIENT-SIDE user. REFERENCES ===' AS "Check";
SELECT id, name, 'ir_actions_act_window' AS "Table", 'context' AS "Field", context AS "Value"
FROM ir_actions_act_window
WHERE context ~ '\buser\.'
  AND context NOT LIKE '%user.company_id%'
UNION ALL
SELECT id, name, 'ir_actions_act_window', 'domain', domain
FROM ir_actions_act_window
WHERE domain ~ '\buser\.'
  AND domain NOT LIKE '%user.company_id%'
UNION ALL
SELECT id, name, 'ir_ui_menu', 'context', context
FROM ir_ui_menu
WHERE context ~ '\buser\.'
  AND context NOT LIKE '%user.company_id%'
ORDER BY 3, 4;
