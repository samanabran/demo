# SGC TECH — Branding Compliance Contract
Root: D:\01_WORK_PROJECTS\module_generator_v19
Every builder MUST apply these. Verified at Stage 4 and Stage 5.

## Brand assets (place these in brand_asset\ — use, never regenerate from scratch)
- Logo:        brand_asset\sgc-logo.png
- Favicon set: brand_asset\favicon_io\   (favicon.ico + PNG sizes + touch icons)
- Banner ref:  brand_asset\banner.png    (thumbnail template — replicate its layout)
- Brand spec:  brand_asset\braand_prompt.md   ← if it has exact hex/fonts, it WINS over values below
- Generator:   brand_asset\generate_brand.py  ← REUSE for all derived assets

## Company identity
- Brand name:     SGC TECH AI   (use the FULL name — not the "SGC TECH" short form)
- Tagline:        "Finance. Systems. Technology."
- Website:        https://sgctech.ai
- Support email:  info@sgctech.ai
- Author string:  "SGC TECH AI"
- Maintainer:     "SGC TECH AI"
- License:        OPL-1   (proprietary / paid marketplace apps)

## Visual identity (approx hex from banner — braand_prompt.md overrides if defined)
- Primary (navy):     #0F2C4C   (deep navy — headlines, feature icons)
- Accent (gold):      #C9A227   (metallic gold — badges, logo, dividers; gold gradient ok)
- Background (cream): #F5EFE0   (warm off-white)
- Headline font:      elegant serif (as in banner), navy
- Body font:          clean sans-serif
- Motifs:             gold hexagon feature badges; gold circuit-board pattern;
                      corner dashboard mockups; subtle skyline/mosque base-left.

## Thumbnail template (replicate banner.png for EVERY module)
- Left: SGC TECH gold logo + tagline "Finance. Systems. Technology."
- Center: large navy serif product name (e.g. "SGC Employee Appraisal")
- Center-bottom: a row of circular navy feature icons
- Corners/edges: light dashboard/report mockups showing the module in use
- Right edge: 3 gold hexagon feature badges (e.g. AI/tech, cloud/data, security)
- Base: faded cream skyline motif. Consistent across the whole product line.

## Where SGC branding MUST appear
- __manifest__.py: author/maintainer="SGC TECH AI", website="https://sgctech.ai",
  support="info@sgctech.ai", license="OPL-1".
- Module technical name prefix: sgc_<name>.
- Every .py file header: "(c) SGC TECH AI" copyright block.
- Module icon: derive static/description/icon.png (128x128) from brand_asset\sgc-logo.png.
- static/description/index.html: navy/gold/cream palette, banner-style hero, contact.
- Marketplace thumbnail & banners: produced via brand_asset\generate_brand.py,
  matching the banner.png template above.

## Where SGC branding MUST NOT go (Odoo store rules)
- Public display `name` in manifest: <=25 chars, descriptive, NO company name.
  e.g. "Employee Appraisal" — NOT "SGC Employee Appraisal". Brand shows via
  author/website/icon/thumbnail/description instead.
- No promo/discount text or external-store links in the description page.

## Compliance checklist (readiness-auditor runs this)
[ ] tech-name starts sgc_            [ ] author/maintainer = SGC TECH AI
[ ] website=https://sgctech.ai       [ ] support=info@sgctech.ai
[ ] license=OPL-1 in manifest        [ ] "(c) SGC TECH AI" headers present
[ ] icon derived from sgc-logo.png   [ ] index.html uses navy/gold/cream + banner style
[ ] thumbnail matches banner template
[ ] display name <=25 chars, no company name, not misleading
