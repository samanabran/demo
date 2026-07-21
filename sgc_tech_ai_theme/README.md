# Enterprise AI Theme

Premium corporate backend theme for Odoo 19 by **SGC TECH AI**.

## Features

- **Gold-Accented Midnight Sidebar (AppsBar)**: Left navigation with SGC brand identity
- **Dark/Light Theme Toggle**: Company-aware toggle with per-company theme preset, session persistence, and company default fallback
- **WCAG 2.1 AA Accessibility**: Keyboard navigation with roving tabindex, ARIA labels and roles, focus-visible ring indicators, screen-reader live region announcements
- **Responsive Breakpoints**: LG (default desktop), MD (collapsed sidebar), SM (overlay sidebar with floating toggle button) — verified mobile-friendly
- **SGC Brand Color Palette**: Navy (#0F2C4C), Gold (#C9A227), Ivory (#F5EFE0), Charcoal, Slate — consistent across all views
- **IBM Plex Typography**: IBM Plex Sans body + IBM Plex Serif headings for professional typography
- **Configurable Assets**: Sidebar logo, favicon, home menu background image via Settings with inline help text
- **User-Selectable Sidebar Mode**: Expanded / collapsed / hidden per-user preference
- **Settings Page**: Card-layout config interface with inline help text for logo/favicon/background image requirements
- **Form Elements**: Branded inputs, buttons, alerts, status indicators, dropdowns, modals, tabs, and kanban views
- **Enterprise Application Launcher**: full-screen "OS home screen" style app grid, opened from a new button on the AppsBar sidebar. Search (matches Odoo's own app/menu search), Favorites (pin, unpin, drag-to-reorder), Recent apps, Frequently Used apps, and a personalization panel (grid density, icon size, animation speed, background style). Icons are a hand-authored SVG family in the shipped navy/gold palette — no third-party icon libraries.
- **Full Odoo v19 OWL Component Compatibility**

## Installation

1. Copy this directory into your Odoo addons path
2. Update the apps list: `./odoo-bin -c odoo.conf -u sgc_tech_ai_theme --init-all`
3. Navigate to **Settings > SGC Tech Ai Theme** to configure

## Configuration

- **Theme Mode**: Settings > SGC Tech Ai Theme > Theme Mode (Light/Dark per company)
- **Sidebar Mode**: User menu > Sidebar Mode (Expanded / Collapsed / Hidden)
- **Logo**: Settings > Upload Logo (recommended: 200x40px, PNG/SVG)
- **Favicon**: Settings > Upload Favicon (recommended: 32x32px, PNG/ICO)
- **Home Background**: Settings > Upload Home Image (recommended: 1920x1080px, JPG/PNG)
- **Application Launcher**: click the grid icon at the top of the sidebar (below the logo) to open it. Personalization (density/icon size/animation speed/background) lives behind the gear icon inside the Launcher itself and applies immediately, no page reload needed.

## Dependencies

- `web`

## License

OPL-1

## Author

SGC TECH AI — https://sgctech.ai
