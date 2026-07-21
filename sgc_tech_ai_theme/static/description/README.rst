==========================================
SGC TECH AI Enterprise Theme
==========================================

A premium corporate theme for Odoo v19 that transforms the visual identity of
your Odoo instance to reflect the architectural precision and institutional
authority of SGC TECH AI.

Designed for enterprises that demand excellence in every detail — from the
navbar to the form fields, every visual element follows the SGC TECH AI Brand
Guidelines v3.0.

Key Features
============

* Navy and gold color system derived from SGC Brand Guidelines v3.0
* IBM Plex typography family (serif for headings, sans for body)
* Architectural gold corner geometry and micro-grid accents
* Clean, institutional navbar with champagne borders
* Enhanced form fields with gold required-field indicators
* Semantic color system: emerald success, amber warning, wine danger
* Consistent spacing and modern card-based UI components
* Full Odoo v19 compatibility (OWL components, SCSS, Bootstrap 5)
* Zero hardcoded colors — all values centralized in SCSS variables

Installation
============

1. Copy the ``sgc_tech_ai_theme`` directory into your Odoo addons path.
2. Update the addons path in your Odoo configuration file.
3. Navigate to Apps > search ``sgc_tech_ai_theme`` then click on and install.
4. The theme applies automatically to the Odoo web backend.

Configuration
=============

All visual parameters are centralized in three SCSS files:

* ``static/src/scss/primary_variables_custom.scss`` — Color palette,
  typography, layout variables.
* ``static/src/scss/secondary_variables.scss`` — Tooltip, form, and
  chatter variables.
* ``static/src/scss/fields_extra_custom.scss`` — Component-level styles
  for forms, lists, buttons, navbar, tabs, alerts, and more.

To customize, modify the SCSS variables and restart Odoo to recompile assets.

Support
=======

SGC TECH AI
DIFC, Dubai, UAE
info@sgctech.ai
https://sgctech.ai

License
=======

LGPL-3