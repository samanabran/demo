"""
SGC TECH AI — Brand Asset Generator
=====================================
Reads brand_asset/banner.png (1536×1024) as read-only master,
fits it into 1500×500 canvas, burns in module title + optional subtitle,
then writes <module>/static/description/banner.png + icon.png for all 19 modules.

Run from the repo root:
    python brand_asset/generate_brand.py

Requires: Pillow (pip install Pillow)
"""

from PIL import Image, ImageDraw, ImageFont
import os, sys

# ── Paths ────────────────────────────────────────────────────────────────────
# __file__ is brand_asset/generate_brand.py, so parent of parent = workspace root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # .../brand_asset
REPO       = os.path.dirname(SCRIPT_DIR)                        # .../sgc-odoo19-apps-marketplace
ASSETS     = SCRIPT_DIR                                          # .../brand_asset
MASTER     = os.path.join(ASSETS, "banner.png")                  # 1536 x 1024, read-only
FAV        = os.path.join(ASSETS, "favicon_io", "favicon-32x32.png")

# ── Canonical brand palette (from brand_prompt.md §5) ───────────────────────
NAVY   = (27,  58,  87)   # #1B3A57 — main titles
GOLD   = (201, 169, 97)   # #C9A961 — subtitles / accents
SHADOW = (0,   0,   0,   60)  # semi-transparent black for text shadow

# ── Output canvas ────────────────────────────────────────────────────────────
OUT_W, OUT_H = 1500, 500

# ── Crop band (center-crop the 1536×1024 master to 3:1 wide) ───────────────
# 1536 × 1024 → crop to 1536 × 512 (center vertically), then scale to 1500 × 500
CROP_TOP = (1024 - 512) // 2   # 256
CROP_BOT = CROP_TOP + 512       # 768

# ── Text placement (from brand_prompt.md §4) ────────────────────────────────
TITLE_X     = int(OUT_W * 0.50)   # 750 — horizontal center
TITLE_Y     = int(OUT_H * 0.49)   # 245 — main title baseline
SAFE_L      = int(OUT_W * 0.297)  # 445 — safe-area left  (logo/skyline left of here)
SAFE_R      = int(OUT_W * 0.813)  # 1220 — safe-area right
TITLE_MAX_W = SAFE_R - SAFE_L     # ~775 px

# ── Module registry ──────────────────────────────────────────────────────────
# (folder_name, title_line1, title_line2_or_None, subtitle_or_None)
MODULES = [
    ("sgc_construction_management",            "Construction",       "Management",       "End-to-End Project Control"),
    ("sgc_commission",                         "Commission",         None,              "Pipeline to Payout Automation"),
    ("sgc_property_sale",                      "Property Sale",      None,              "Streamlined Deal Closing"),
    ("sgc_sale_agreement",                    "Sale Agreement",     None,              "AI-Powered Deal Documents"),
    ("sgc_invoicing_dashboard",                "Invoicing",          "Dashboard",       "Real-Time Finance Visibility"),
    ("sgc_deals_management",                   "Deals Management",   None,              "Pipeline to Close Automation"),
    ("sgc_offplan_rental_property_management","Offplan Rental",     "Property Mgmt",   "Full Leasing Lifecycle"),
    ("sgc_realestate_website",                 "Real Estate",        "Website",         "Modern Property Portals"),
    ("sgc_video_conferencing",                  "Video Conferencing", None,              "Meetings Without Switching Apps"),
    ("sgc_recruitment",                        "Recruitment",        None,              "UAE-Compliant Hiring"),
    ("sgc_lead_scoring",                       "Lead Scoring",       None,              "AI-Powered Deal Prioritization"),
    ("sgc_hr_memos",                           "HR Memos",           None,              "Approvals Done Right"),
    ("sgc_employment_certificate",              "Employment",         "Certificate",     "Professional Credentialing"),
    ("sgc_elearning",                          "E-Learning",         None,              "Sequential Learning Paths"),
    ("sgc_appraisal",                          "Employee Appraisal",  None,              "People Growth Made Measurable"),
    ("sgc_appraisal_questionnaire",             "Appraisal",          "Questionnaire",   "360° Feedback System"),
    ("sgc_assessment",                          "Assessment",         "System",          "AI-Powered Candidate Evaluation"),
    ("sgc_crm_dashboard",                      "CRM Dashboard",      None,              "Visual Sales Intelligence"),
    ("sgc_payment",                           "Payment",            "Management",      "Approval Workflow Automation"),
    ("l10n_ae_corporate_tax",                  "UAE Corporate Tax",  None,              "Federal Decree-Law No. 47 of 2022"),
    ("sgc_dynamic_financial_report",           "Dynamic Financial",  "Reports",         "Enterprise Financial Intelligence"),
]

# ── Font helpers ─────────────────────────────────────────────────────────────
FONT_CANDIDATES_WINDOWS = [
    ("C:\\Windows\\Fonts\\arialbd.ttf",        "Arial Bold"),
    ("C:\\Windows\\Fonts\\georgiab.ttf",       "Georgia Bold"),
    ("C:\\Windows\\Fonts\\timesbd.ttf",        "Times Bold"),
    ("C:\\Windows\\Fonts\\trebucbd.ttf",       "Trebuchet Bold"),
]
FONT_CANDIDATES_LINUX = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVu Sans Bold"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "Liberation Sans Bold"),
]
FONT_CANDIDATES_MAC = [
    ("/System/Library/Fonts/Helvetica.ttc",    "Helvetica Bold"),
]
ALL_FONT_PATHS = (
    FONT_CANDIDATES_WINDOWS
    + FONT_CANDIDATES_LINUX
    + FONT_CANDIDATES_MAC
)


def load_font(size):
    """Load a bold font at the requested size, trying multiple families."""
    tried = []
    for path, name in ALL_FONT_PATHS:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                print(f"    Loaded font: {name} {size}pt")
                return font
            except Exception:
                tried.append(name)

    # Fallback to Pillow default (bitmap)
    try:
        font = ImageFont.truetype("arialbd.ttf", size)
        return font
    except Exception:
        pass

    # Last resort
    print(f"    WARNING: Could not load any bold font. Tried: {tried}")
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    """Break text into lines that fit within max_width pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ── Core generation ───────────────────────────────────────────────────────────
def build_canvas():
    """Load master, crop to 3:1 band, scale to 1500×500."""
    master = Image.open(MASTER).convert("RGBA")
    cropped = master.crop((0, CROP_TOP, 1536, CROP_BOT))  # 1536 × 512
    canvas  = cropped.resize((OUT_W, OUT_H), Image.LANCZOS)
    return canvas


def load_favicon_img():
    """Load favicon as a 256×256 RGBA image."""
    img = Image.open(FAV).convert("RGBA")
    # Scale to 256×256 for icon output
    return img.resize((256, 256), Image.LANCZOS)


def draw_text(canvas, t1, t2, subtitle):
    """Composite title + subtitle onto the banner canvas."""
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(60)   # primary title
    subt_font  = load_font(28)  # subtitle

    # Title lines
    if t2:
        title_lines = [t1, t2]
    else:
        title_lines = wrap_text(draw, t1, title_font, TITLE_MAX_W)

    # Measure total text block height
    def text_h(line, font):
        bb = draw.textbbox((0, 0), line, font=font)
        return bb[3] - bb[1]

    title_heights = [text_h(l, title_font) for l in title_lines]
    total_title_h = sum(title_heights) + len(title_lines) * 6   # line spacing
    sub_h = text_h(subtitle, subt_font) if subtitle else 0
    total_h = total_title_h + (sub_h + 8 if subtitle else 0)

    # Anchor: vertically centre the text block around TITLE_Y
    y = TITLE_Y - total_title_h * 0.5

    # Draw title lines
    for i, line in enumerate(title_lines):
        bb = draw.textbbox((0, 0), line, font=title_font)
        lw = bb[2] - bb[0]
        x  = TITLE_X - lw // 2
        # Shadow
        draw.text((x + 2, y + 2), line, fill=SHADOW, font=title_font)
        # Navy text
        draw.text((x, y), line, fill=NAVY, font=title_font)
        y += title_heights[i] + 6

    # Draw subtitle in gold
    if subtitle:
        y += 6
        bb  = draw.textbbox((0, 0), subtitle, font=subt_font)
        sw  = bb[2] - bb[0]
        sx  = TITLE_X - sw // 2
        draw.text((sx + 1, y + 1), subtitle, fill=SHADOW, font=subt_font)
        draw.text((sx, y), subtitle, fill=GOLD, font=subt_font)


def save_output(canvas, folder):
    """Save banner + icon for one module."""
    module_path = os.path.join(REPO, folder)
    desc_path   = os.path.join(module_path, "static", "description")
    os.makedirs(desc_path, exist_ok=True)

    banner_out = os.path.join(desc_path, "banner.png")
    canvas.save(banner_out, "PNG")
    print(f"  [OK] banner.png -> {banner_out}  ({OUT_W}x{OUT_H})")

    icon_out = os.path.join(desc_path, "icon.png")
    fav_img  = load_favicon_img()
    fav_img.save(icon_out, "PNG")
    print(f"  [OK] icon.png   -> {icon_out}  (256x256)")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("SGC TECH AI — Brand Asset Generator")
    print("=" * 55)
    print(f"  Master   : {MASTER}")
    print(f"  Canvas   : {OUT_W}x{OUT_H} px  (Odoo standard)")
    print(f"  Crop band: 1536x1024 -> 1536x512 centre -> {OUT_W}x{OUT_H}")
    print(f"  Title    : Navy #1B3A57 · Subtitle: Gold #C9A961")
    print(f"  Text pos : X={TITLE_X}, Y={TITLE_Y}")
    print(f"  Safe area: X={SAFE_L}-{SAFE_R}")
    print()

    canvas = build_canvas()   # load master once, reuse for all modules
    fav_img_global = load_favicon_img()

    for (folder, t1, t2, subtitle) in MODULES:
        print(f"\n{'-'*55}")
        print(f"  Processing: {folder}")
        # Each module gets its own canvas copy so text is unique
        module_canvas = canvas.copy()
        draw_text(module_canvas, t1, t2, subtitle)
        save_output(module_canvas, folder)

    print(f"\n{'='*55}")
    print("[DONE] All 19 modules processed.")
    print()
    print("  Review banners in: <module>/static/description/banner.png")
    print("  Icons are copied from: brand_asset/favicon_io/")
    print()
    print("  If text is too HIGH  -> decrease TITLE_Y")
    print("  If text is too LOW   -> increase TITLE_Y")
    print("  If text is too WIDE  -> reduce TITLE_MAX_W")
    print()
    print("  Then run: git add -A && git commit -m 'Brand: regenerate banners + icons'")


if __name__ == "__main__":
    main()
