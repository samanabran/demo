# SGC Tech AI Theme — Enterprise Application Launcher

**Status:** APPROVED 2026-07-20 — user signed off on all three pending decisions; ralph execution begins
**Execution path:** sequential — `oh-my-claudecode:ralph`, repo Stage 1→8 pipeline (Stage 1/2/5 run in MAIN per `CLAUDE.md`)
**Module:** `sgc_tech_ai_theme` only
**Repo:** `module_generator_v19/addons/sgc_tech_ai_theme`
**Scope:** Replace the default Odoo 19 Apps Menu experience with a premium full-screen Enterprise Application Launcher, scoped strictly to a single module. No business/reporting modules touched, no core Odoo file edits.

---

## Decision

Build an **additive full-screen Launcher overlay** in `sgc_tech_ai_theme`, triggered from a new small grid-icon button in the existing `AppsBar` rail. The AppsBar rail is preserved unmodified as the persistent always-visible switcher; the Launcher is the open-on-demand "OS home screen" surface. Search delegates to Odoo's existing `command_provider` registry (the same providers Ctrl+K uses) — exactly one search UI is ever visible. All new per-user state is persisted on `res.users` and exposed through `ir_http.session_info`, fixing a pre-existing dead `sgc_theme_mode` company-default read in the same change.

## Drivers

1. **The brief literally mandates a full-screen, large-icon "OS home screen" experience.** Cited brief text: "Instead of the default Odoo Apps grid, display a beautiful full-screen application launcher" and success criteria "must feel like a premium operating-system home screen rather than a traditional ERP menu. A first-time user should immediately recognize that this is a custom-built SGC TECH AI Enterprise Platform." Option C (rail-only enhancement) cannot meet this.
2. **No dead persistence paths.** Every new field has a verified read path. The `sgc_theme_mode` dead-read is fixed in this same change so the pattern being copied actually works.
3. **No new nav-surface redundancy.** Two complementary surfaces (persistent rail + on-demand overlay) is industry-standard (Fiori, M365, Google Workspace, Android all ship exactly this). Without it, the AppsBar alone already lists every app and Ctrl+K already searches — building a third independent surface would be redundancy.
4. **Palette is user-ratified, not architect-declared.** Four conflicting color sources exist on disk; the brief's own fresh palette is one of them.
5. **Brief text is real.** Quoted passages above were verified against the live brief text provided in the ralplan invocation.

## Alternatives considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **A — additive overlay Launcher, AppsBar unchanged** | Matches the brief's mandated full-screen "OS home screen" experience; AppsBar stays an accessible tested component; reuses Odoo's command-palette search; one search UI | Adds a second visible nav surface (justified by the brief) and 2 new models + 4 new fields; needs `session_info` plumbing | **CHOSEN** |
| **B — replace AppsBar entirely** | One surface | Destroys the working, accessibility-hardened, tested `AppsBar` for no brief requirement; named exemplars (Fiori/M365/Workspace/Android) all keep persistent nav, contradicting the brief's own visual reference set | REJECTED |
| **C — enhance AppsBar in place / register a launcher-style provider into the existing Ctrl+K palette only** | Minimum code; no modal, no new schema, no new session_info plumbing; reuses accessibility already shipped | Cannot deliver the brief's explicit full-screen large-icon "premium OS home screen" visual + centralized background-personalization + favorites drag-reorder UI — these need real screen real estate the rail does not have | REJECTED (but its "reuse search" insight was adopted into Option A) |

Why chosen: the only option that satisfies every brief requirement at acceptable implementation cost is Option A, narrowed by the C insight (reuses `command_provider` registry rather than hand-rolling a parallel fuzzy search) and the v3 follow-ups below.

## Consequences

- **Two nav surfaces by design** (rail + overlay), consistent with every exemplar the brief cites.
- **New schema: 2 models, 4 fields, 1 session_info extension.** `sgc.launcher.favorite (user_id, menu_id, sequence)` and `sgc.launcher.usage (user_id, menu_id, use_count, last_used)`. `res.users.launcher_{grid_density, icon_size, animation_speed, background_style}`. `ir_http.session_info` exposes all four new user fields and additionally `sgc_theme_mode`.
- **`sgc_theme_mode` is being revived from a silent no-op.** Companies that set Theme Mode = Dark today see nothing — that field is dead because `ir_http.py:session_info` never exposes it. After this change ships, dark-mode-enabling companies will actually default their users to dark. This is a **user-visible behavior change**, deliberately correcting a latent bug; recorded in `CHANGES.md`; trivially reversible.
- **Palette decision is pending user approval.** Tier 1 reuse of the already-shipped `appsbar.scss` tokens (no sign-off needed). The two NEW accent tokens (gold `#D4AF37`, highlight `#4DA3FF` from the brief's fresh palette) and the configurable background-style CSS are NOT shipped until the Palette Proposal (next section) is user-ratified.
- **Tier 1-supplement (mmx-cli / MiniMax concept renders):** possible to ship alongside Tier 1; we use MiniMax's raster output as design reference only — the shipped icon set is hand-authored SVG, matching the brief's own "SVG Master" requirement.

## Follow-ups (capture at execution; do not silently drop)

1. **Contrast (Fix 4):** WCAG-AA is the authoritative gate — the specific example scrim value `rgba(9,21,40,0.55)` is illustrative, not contracted. It fails the plan's own 4.5:1 body-text criterion in the worst case (e.g. light foreground over bright image ⇒ ≈3.8:1). Resolution: declare AA 4.5:1 authoritative, declare which text tier sits directly on raw wallpaper (large icon labels at 3:1 only) vs. must sit on a scrimmed card (body text at 4.5:1); raise scrim opacity to ≈0.7+ OR route body text through a scrimmed card whenever the background is `image` or `company_branding`.
2. **Usage throttle (Fix 1):** pin ONE pruning mechanism for the 50-row-per-user cap — **prefer a nightly cron** over a per-write `DELETE ... NOT IN (SELECT menu_id ORDER BY use_count DESC LIMIT 50)`. State debounce key as `(uid, menu_id)`, trailing (not leading), 2 s window.
3. **Search integration (Fix 2):** invocation contract — invoke providers via `this.env` (NOT `useService('command')`), `await` async providers, filter to default/empty namespace. Explicitly forbid `commandService.openMainPalette()` from the launcher's search code path.
4. **Palette (Fix 3):** reconcile new `#D4AF37` against shipped `#B79554` at sign-off so only one gold ships in the final launcher.
5. **Theme fix location (Fix 5):** the patch lives in `models/ir_http.py` `session_info` (server-side field exposure), not the JS consumer (`appsbar.js:_loadTheme` already reads `user.activeCompany.sgc_theme_mode` correctly). Track in `CHANGES.md`.

---

## Acceptance criteria (testable, gate at Stage 4 readiness-auditor / Stage 5 production-qa)

1. **Open / close.** Launcher opens from the new AppsBar button and from keyboard activation of that button; closes on `Esc`, backdrop click, and after an app selection that begins navigation. Read CB theorem: `Lifecycle event` assertion in a hoot test.
2. **Responsive grid.** 6–8 icons per row at desktop (≥1280 px), 4–5 at tablet (768–1279 px), 3 at mobile (<768 px). Verified by hoot test asserting `getComputedStyle().gridTemplateColumns`.
3. **Search.** Typing in the launcher's search box filters in-palette results in real time and never opens Odoo's separate Ctrl+K dialog. Test asserts both: keyboard-only paths of Ctrl+K don't accidentally fire while the launcher's search is focused.
4. **Favorites.** Pinning / unpinning / drag-reordering writes to `sgc.launcher.favorite`; reloading the page restores the same order. Verified via Python `TransactionCase` writing favorites then asserting server-side order on second read.
5. **Recents.** Most-recently-used apps appear in a "Recent Apps" section, sourced from client-side localStorage (no server round-trip), deduplicated, capped at 8.
6. **Frequently used.** Backing model `sgc.launcher.usage` records per-(uid, menu_id) counts; writes are debounced 2 s per `(uid, menu_id)`, dispatched post-navigation (never blocks the click), failure-silent, table capped at 50 rows/user.
7. **Settings persistence.** All four `res.users.launcher_*` fields round-trip through `ir_http.session_info` on reload — i.e. changing the user's icon size in the Settings panel reflects on next page load before any other user input. Python regression test.
8. **Theme revival.** `sgc_theme_mode` = Dark now actually produces a dark default; verified by integration test that sets the company field and asserts `<html data-bs-theme="dark">` at boot.
9. **Accessibility — keyboard.** All launcher-interactive elements participate in a roving-tabindex menubar (Arrow Up/Down rove, Home/End jump, Enter/Space activate, `Esc` returns focus to trigger). Mirror of the existing AppsBar pattern.
10. **Accessibility — ARIA.** Launcher has `role="dialog" aria-modal="true" aria-label="Application launcher"`. Each app card has `role="menuitem"`. Search input has `role="searchbox"` and an `aria-controls`/`aria-activedescendant` link to the result list.
11. **Accessibility — `prefers-reduced-motion`.** When `prefers-reduced-motion: reduce` matches, all hover/click animations are turned off regardless of the `launcher_animation_speed` user setting.
12. **Accessibility — contrast.** Body text (4.5:1) and large/icon text (3:1) contrast holds against every `launcher_background_style` value at QA. For `image` and `company_branding` backgrounds, body text must be on a scrimmed card or have a heavier scrim applied (see Follow-up #1). Verifiable with an automated contrast tool at QA stage.
13. **No core file diffs.** `git diff` shows changes confined to `addons/sgc_tech_ai_theme/**` and `artifacts/**`. No `odoo/`, no `addons/web/**`, no `enterprise/**` modifications.
14. **Branding compliance.** All deliverables match `branding/SGC-BRAND.md` for what it governs (manifest author/maintainer, headers, thumbnail template, etc.) and `brand_asset/braand_prompt.md` for what it governs (marketplace banners). The launcher's in-product palette is a deliberate UI-chrome split per Follow-up #4 (separate from marketplace banners — not a contradiction, a scope split).
15. **Module isolation.** `git diff --stat addons/` lists ONLY files under `addons/sgc_tech_ai_theme/`.
16. **Performance.** Launcher grid first paint ≤ 200 ms after trigger on a 30-app install (DomContentLoaded; hoot test). Search filter update ≤ 50 ms per keystroke on a 60-app install. Preference summary in Stage 5 production-qa.

---

## Scope

### Tier 1 — code-complete this build
- Launcher OWL component tree: `Launcher` root, `LauncherSearch` (delegates to `command_provider` registry), `LauncherGrid`, `LauncherCard`, `LauncherSettings`, `LauncherBackground`.
- Responsive grid (6–8 / 4–5 / 3 by viewport breakpoint).
- Favorites (`sgc.launcher.favorite`, pin / unpin / drag-reorder).
- Recents (client-side localStorage, no server cost).
- Frequently-used (`sgc.launcher.usage`, throttle contract above).
- Hover / click animations (CSS transform, `prefers-reduced-motion` honored).
- Keyboard navigation mirroring `AppsBar`'s existing roving-tabindex menubar pattern.
- Light / dark theme reuse.
- Settings panel wired to the 4 new `res.users` fields, exposed through `session_info`.
- Trigger affordance added to `AppsBar` (a dedicated grid-icon button at the top of the rail; `AppsBar` itself otherwise unmodified).
- ~30 hand-authored original SVG icons in one consistent design language (flat + soft gradient + rounded geometry, no third-party icon libraries).
- Fix the existing `sgc_theme_mode` dead read in the same change.

### Tier 1-supplement (parallelizable, not blocking)
- MiniMax prompt sheet (`artifacts/icon-prompts.md`) — prompt + negative prompt + export-size table per app.
- `mmx-cli` concept renders used as design reference only (shipped assets stay hand-authored SVG).

### Explicit non-scope
- Business / reporting modules — not touched.
- Odoo core files — not touched.
- Enterprise-only APIs — not used (this module depends only on `web`, per `__manifest__.py`).
- Replacing or hiding the existing `AppsBar`.

---

## Test plan (short mode — short mode gates prep; deliberate mode not invoked for this UI-feature request)

- **hoot / QUnit (frontend):** Launcher open/close (trigger + Esc/backdrop), search delegates to `command_provider` registry correctly and never opens Odoo's native Ctrl+K dialog, favorite pin/unpin/reorder persistence, keyboard-nav parity test mirroring `AppsBar`'s existing pattern, settings panel writes reach `res.users` and round-trip through `session_info` on reload, `prefers-reduced-motion` honored.
- **Python (`tests/test_regression.py` extension):** new models install/uninstall clean, `session_info` exposes all new fields for an internal user, `sgc_theme_mode` company default now reaches the client, no core file diffs (grep-based check), favorites reorder persistence round-trip.
- **Manual:** Stage 4 readiness-auditor + Stage 5 production-qa per repo `CLAUDE.md` pipeline; screenshots at 3 breakpoints (desktop / tablet / mobile); `prefers-reduced-motion` + high-contrast verification; automated WCAG-AA contrast tool pass against every `launcher_background_style` value.

---

## User-approved decisions (2026-07-20)

1. **Palette — REUSE SHIPPED.** Stage 1 ships only with the existing `appsbar.scss` token set (navy `#091528`, gold `#B79554`, focus `#FFD66B`, plus any other already-shipped `--sgc-*` custom properties). The two new accent tokens from the brief's fresh palette (gold `#D4AF37`, highlight `#4DA3FF`) are NOT introduced — they remain parked pending a future change. The reconciliation question (one gold ship vs two) is implicitly resolved: ship `#B79554` everywhere. `launcher_background_style` defaults to `gradient` (shipped navy→midnight) with `solid` always available; `image` and `company_branding` options ship with the scrim contract from Follow-up #1 (AA 4.5:1 authoritative over any scrim example). Per-repo `braand_prompt.md` remains authoritative for marketplace banners only — it has never been in scope for in-app UI chrome.
2. **Execution path — SEQUENTIAL.** `oh-my-claudecode:ralph`, sequential-with-verification. Per repo `CLAUDE.md` the actual stage agents used are still product-analyst (Stage 0, already passed), module-architect (Stage 1), debugger (Stage 2), test-engineer (Stage 3), readiness-auditor (Stage 4), production-qa (Stage 5), remotion-producer (Stage 6), manual-writer (Stage 7), brand-labeler (Stage 8). Stages 1, 2, 5 run in MAIN; Stages 3, 6, 8 are chunked; Stages 0, 4, 7 are bounded single deliverables.
3. **MiniMax / `mmx-cli` — TIER 1-SUPPLEMENT RUNS.** `mmx-cli` is available for Tier 1-supplement reference renders, used as design input for the hand-authored SVG set only (shipped assets remain hand-authored SVG per brief's "SVG Master" requirement). The MiniMax prompt sheet (`artifacts/icon-prompts.md`) is a separate delivered artifact. Tier 1-supplement runs alongside Stage 1 hand-authored SVG work where it can; it never blocks Stage 1.

---

## What this plan does NOT promise

- A ready-to-install binary at the end of this skill invocation. This skill produces an approved plan; execution (Stages 1–8) is a separate explicit step.
- Disruption of the existing `AppsBar` rail or any third-party module's menus — all changes stay inside `sgc_tech_ai_theme`.
- Compatibility with Odoo Enterprise paid-only features. The module declares `depends: ['web']` only and stays that way.
- Real-time sync of usage/frequency data across devices (the table is per-DB, per-user; no signal of cross-device expected usage).
