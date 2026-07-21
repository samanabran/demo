/** @odoo-module **/

/**
 * Maps a real installed app (matched against its xmlid + display name,
 * case-insensitive) to one of the 36 hand-authored icon keys generated
 * in US-006 (see static/src/webclient/launcher/icons/*.svg).
 *
 * Odoo core menu xmlids vary across editions/versions and this addon
 * checkout has no Odoo core source to verify exact strings against, so
 * matching is done by keyword/substring against "<xmlid> <name>"
 * rather than hardcoded exact xmlids — more portable, at the cost of
 * being probabilistic for edge cases. Order matters: more specific
 * patterns are listed before more general ones that could also match
 * (e.g. "email marketing" before the generic "marketing").
 *
 * Unmatched apps fall back to Odoo's own webIconData — see
 * launcher_card.js:iconSrc. Some of the 36 icon keys may end up unused
 * by any given install; that's an accepted, disclosed limitation, not
 * a bug (see artifacts/progress.md US-006B entry).
 */
export const LAUNCHER_ICON_RULES = [
    ['email_marketing', /email marketing/],
    ['marketing', /marketing automation|\bmarketing\b/],
    ['crm', /\bcrm\b/],
    ['hrm', /\bhr\b|human resources|employees/],
    ['recruitment', /recruit/],
    ['payroll', /payroll/],
    ['approvals', /approval/],
    ['timesheets', /timesheet/],
    ['expenses', /expense/],
    ['accounting', /accounting|invoic/],
    ['finance', /\bfinance\b/],
    ['inventory', /inventory|warehouse|\bstock\b/],
    ['purchase', /purchase/],
    ['sales', /\bsale/],
    ['pos', /point of sale|\bpos\b/],
    ['rental', /rental/],
    ['subscriptions', /subscription/],
    ['manufacturing', /manufactur|\bmrp\b/],
    ['maintenance', /maintenance/],
    ['fleet', /fleet/],
    ['projects', /project/],
    ['planning', /planning/],
    ['helpdesk', /helpdesk/],
    ['knowledge', /knowledge/],
    ['documents', /document/],
    ['discuss', /discuss|messaging/],
    ['calendar', /calendar/],
    ['appointments', /appointment/],
    ['events', /\bevent/],
    ['website', /website/],
    ['studio', /studio/],
    ['ai_center', /\bai\b|artificial intelligence/],
    ['dashboard', /dashboard/],
    ['reports', /\breport/],
    ['notifications', /notification/],
    ['settings', /settings/],
];

export function resolveLauncherIconKey(app) {
    const haystack = `${app.xmlid || ''} ${app.name || ''}`.toLowerCase();
    for (const [key, pattern] of LAUNCHER_ICON_RULES) {
        if (pattern.test(haystack)) {
            return key;
        }
    }
    return null;
}
