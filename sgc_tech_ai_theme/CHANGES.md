# Changelog — sgc_tech_ai_theme

## 2026-07-21 — Enterprise Application Launcher

Adds a full-screen, on-demand Application Launcher overlay (US-001 through
US-017 in `artifacts/launcher-plan.md`), triggered from a new button on the
existing AppsBar sidebar. The AppsBar rail itself is unchanged and remains
the persistent quick-switch surface; the Launcher is the deliberately-opened
"OS home screen" experience layered on top — the same pattern SAP Fiori,
Microsoft 365, and Google Workspace all use (persistent nav + on-demand
launcher, not one replacing the other).

### Added

- Full-screen Launcher overlay: dialog semantics, focus trap, Escape/backdrop
  close, `prefers-reduced-motion` and `forced-colors` support.
- Responsive application grid (6–8 / 4–5 / 3 columns by breakpoint, scaled by
  icon-size preference).
- 36 hand-authored SVG icons in one consistent design language (flat, soft
  gradient, rounded geometry) — no third-party icon libraries. Mapped to real
  installed apps by name/xmlid keyword matching, with a safe fallback to
  Odoo's own icon for anything unmapped.
- Search: reads Odoo's own `command_provider` registry (the same source
  Ctrl+K uses) and renders matches inline — never opens a second, stacked
  search dialog.
- Favorites: pin/unpin, drag-to-reorder (persisted via a new
  `sgc.launcher.favorite` model).
- Recent apps: client-side only (localStorage), no server round-trip.
- Frequently used apps: server-tracked (`sgc.launcher.usage`), debounced
  writes, capped at 50 rows/user via a new daily cron.
- Personalization panel: grid density, icon size, animation speed, and
  background style (solid / gradient / image / company branding), persisted
  per-user and applied immediately.
- Full keyboard/ARIA support: roving-tabindex grid navigation (mirrors the
  existing AppsBar keyboard pattern), visible focus rings throughout.

### Fixed

- **`sgc_theme_mode` (company-level dark-mode default) now actually reaches
  the client.** This was a pre-existing, silent dead-read: `ir_http.py`'s
  `session_info()` never exposed the field, so `appsbar.js`'s
  `user.activeCompany.sgc_theme_mode` check always read `undefined` and the
  company default never applied. **This is a user-visible behavior change**:
  any company that already has Theme Mode set to Dark will now see its
  users actually default to dark mode on next load. Trivially reversible
  (toggle the field back to Light) if unwanted.
- Deprecated `_sql_constraints` list syntax replaced with Odoo 19's
  `models.Constraint(...)` declarative API on the two new launcher models.

### Branding

- No new brand colors were introduced. The Launcher reuses the palette
  already shipped in `appsbar.scss` (navy `#091528`, gold `#B79554`, focus
  ring `#FFD66B`) — a deliberate decision made when this feature was
  approved, over the brief's own alternative palette suggestion
  (`#D4AF37`/`#4DA3FF`), to keep the sidebar and Launcher visually
  consistent rather than introduce a second gold/accent pairing.
- `brand_asset/braand_prompt.md`'s palette remains authoritative for
  marketplace banners and store listings only — it was never in scope for
  in-app UI chrome, and this Launcher work does not touch it.
