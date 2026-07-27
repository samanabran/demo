# -*- coding: utf-8 -*-
import base64
import io
import logging
import os
import tempfile

from werkzeug.urls import url_quote_plus as quote_plus

from odoo import api, models

_logger = logging.getLogger(__name__)


class PropertyBrochureLuxuryReport(models.AbstractModel):
    """Report values for the luxury property brochure PDF.

    Full-bleed A4 luxury design with deep navy/gold aesthetic.
    All images go through WebP-to-JPEG conversion identical to the
    standard brochure report to ensure wkhtmltopdf compatibility.
    """
    _name = "report.sgc_offplan_rental_property_management.report_property_brochure_luxury"
    _description = "Property Brochure Luxury Report"
    _table = "sgc_offplan_report_brochure_luxury"

    @staticmethod
    def _guess_suffix(raw):
        if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
            return ".webp"
        if raw[:3] == b"\xff\xd8\xff":
            return ".jpg"
        if raw[:8] == b"\x89PNG\r\n\x1a\n":
            return ".png"
        if raw[:6] in (b"GIF87a", b"GIF89a"):
            return ".gif"
        return ".img"

    @api.model
    def _convert_to_jpeg_b64(self, b64_source):
        # Always returns bytes (possibly empty), never a str/False/None:
        # the value flows straight into image_data_uri(), which calls
        # .decode() on it unconditionally and crashes on a plain str.
        if not b64_source:
            return b''
        from PIL import Image

        raw = base64.b64decode(b64_source)
        fd, tmp_path = tempfile.mkstemp(suffix=self._guess_suffix(raw))
        try:
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(raw)
            image = Image.open(tmp_path)
            if image.format == 'JPEG':
                return b64_source
            image = image.convert('RGB')
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=92)
            return base64.b64encode(buf.getvalue())
        except Exception:
            _logger.warning(
                "Could not convert image to JPEG for luxury brochure; skipping.",
                exc_info=True,
            )
            return b''
        finally:
            os.unlink(tmp_path)

    @api.model
    def _render_cover_full_bleed(self, b64_source, target_w=794, target_h=1123):
        """Return a JPEG data URI of the cover photo pre-rendered at A4 size.

        Why this exists: wkhtmltopdf doesn't support CSS object-fit / background-size
        reliably on QWeb images, so a container-stretch attempt to fill 210mm
        x 297mm either leaves a dark right-edge gap (photo's natural aspect
        ratio narrower than A4) or stretches (looking very wrong on tall
        crops). The reliable fix is what the other PIL helpers in this file
        already do -- build the target bytes server-side. We center-crop the
        source into the exact A4 aspect ratio, then resize to the print dpi
        target so the template can render it as a plain <img style="width
        100%; height: 100%"> that the engine can actually lay out.
        """
        from PIL import Image
        if not b64_source:
            return None
        try:
            raw = base64.b64decode(b64_source)
            fd, tmp_path = tempfile.mkstemp(
                suffix=self._guess_suffix(raw)
            )
            try:
                with os.fdopen(fd, "wb") as tmp:
                    tmp.write(raw)
                src = Image.open(tmp_path).convert("RGB")
            finally:
                os.unlink(tmp_path)
        except Exception:
            _logger.warning(
                "Cover image open failed for full-bleed render; skipping.",
                exc_info=True,
            )
            return None

        src_w, src_h = src.size
        # Center-crop into the target A4 aspect ratio without stretching.
        target_ratio = target_w / target_h  # 0.7071 = 210/297
        src_ratio = src_w / src_h if src_h else target_ratio
        if src_ratio > target_ratio:
            # Source is wider than target -- crop horizontally.
            new_w = int(src_h * target_ratio)
            offset = (src_w - new_w) // 2
            src = src.crop((offset, 0, offset + new_w, src_h))
        else:
            # Source is taller than target -- crop vertically.
            new_h = max(1, int(src_w / target_ratio))
            offset = (src_h - new_h) // 2
            src = src.crop((0, offset, src_w, offset + new_h))
        # Resize to the actual print pixel size at 96 dpi (~ 72-100 dpi range
        # for typical wkhtmltopdf screen dpi). quality=88 keeps file size sane
        # without visible JPEG artifacts at A4.
        src = src.resize((target_w, target_h), Image.LANCZOS)
        buf = io.BytesIO()
        src.save(buf, format="JPEG", quality=88)
        return (
            "data:image/jpeg;base64,"
            + base64.b64encode(buf.getvalue()).decode("ascii")
        )

    @api.model
    def _get_diamond_border_data_uri(self):
        """Return a base64 data URI for the Art Deco diamond border tile.

        wkhtmltopdf does not reliably render SVG as CSS background-image, so
        this generates a 20x200 PNG pixel-by-pixel with PIL (no external deps)
        and returns a data URI that can be used as `background: url(...)`.
        """
        from PIL import Image, ImageDraw

        w, h = 20, 200
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        gold = (201, 169, 97, 200)       # #c9a961 semi-opaque
        gold_light = (212, 175, 106, 120)  # #d4af6a lighter

        # Vertical rule down left side
        draw.rectangle([2, 0, 4, h], fill=gold)

        # Diamond pattern every 20px
        for y in range(0, h, 20):
            cx, cy = 11, y + 10
            # Outer diamond
            pts = [(cx, cy - 6), (cx + 5, cy), (cx, cy + 6), (cx - 5, cy)]
            draw.polygon(pts, fill=gold)
            # Inner dot
            draw.point((cx, cy), fill=gold_light)
            # Tiny horizontal rule connector
            draw.rectangle([5, cy - 1, 8, cy + 1], fill=gold)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return "data:image/png;base64," + b64

    @api.model
    def _get_monogram_svg_uri(self):
        """Return a data URI for the monogram/crest used on the cover.

        Returns a PNG data URI (not SVG) because wkhtmltopdf's QtWebKit
        engine does not reliably render inline SVG in <img> tags.
        PIL generates the PNG from the SVG-like description.
        """
        from PIL import Image, ImageDraw, ImageFont

        size = 100
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2
        gold = (201, 169, 97, 255)

        # Crown
        points = [
            (cx - 35, cy + 20),
            (cx - 28, cy - 12),
            (cx - 14, cy + 4),
            (cx, cy - 18),
            (cx + 14, cy + 4),
            (cx + 28, cy - 12),
            (cx + 35, cy + 20),
        ]
        draw.line(points, fill=gold, width=2)
        draw.line([(cx - 35, cy + 20), (cx + 35, cy + 20)], fill=gold, width=2)
        # Crown dots
        for dx, dy in [(-25, -8), (0, -20), (25, -8)]:
            draw.ellipse(
                [cx + dx - 3, cy + dy - 3, cx + dx + 3, cy + dy + 3],
                fill=gold,
            )

        # Try to use a built-in font for "AE"
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except (OSError, IOError):
            font = ImageFont.load_default()

        draw.text((cx - 16, cy - 6), "AE", fill=gold, font=font)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return "data:image/png;base64," + b64

    @api.model
    def _get_gallery_pairs(self, images):
        """Return images as list of (left, right) tuples for two-column gallery.

        Each tuple contains two images or (image, None) for odd counts.
        This avoids QWeb's inability to conditionally open/close tr tags.
        """
        pairs = []
        raw = list(images)
        for i in range(0, len(raw), 2):
            left = raw[i]
            right = raw[i + 1] if i + 1 < len(raw) else None
            pairs.append((left, right))
        return pairs

    @api.model
    def _get_gallery_pages(self, images, per_page=6):
        """Chunk images into fixed-size groups, one group per gallery page.

        The gallery page previously rendered every image into one
        unbounded container (no fixed height, just min-height: 297mm), so
        wkhtmltopdf's continuous-flow rendering let it overflow past a
        single A4 page's worth of content for any property with more than
        a handful of images — producing extra physical PDF pages that
        never got the page's border/header chrome. Splitting into
        explicit per-page chunks up front means each chunk gets its own
        bounded `.gallery-page` div with a real `page-break-after`.
        """
        raw = list(images)
        return [raw[i:i + per_page] for i in range(0, len(raw), per_page)]



    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["property.details"].browse(docids)

        # Pre-build expensive data URIs once
        border_uri = self._get_diamond_border_data_uri()
        monogram_uri = self._get_monogram_svg_uri()

        # wkhtmltopdf renders from a local file with no browser context, so
        # relative URLs (e.g. "/report/barcode/...") never resolve: the QR
        # <img> silently fails to load and the PDF shows its alt text
        # instead. Build an absolute URL so the barcode image actually loads.
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

        # Pre-build a full-bleed cover image per property. Doing it here (not
        # inside the t-foreach) would cache once for the multi-property case
        # too, but for now (most reports are single-property) the inner loop
        # is fine and easier to read.
        def _cover_for(prop):
            return self._render_cover_full_bleed(prop.image_1920)

        return {
            "doc_ids": docids,
            "doc_model": "property.details",
            "docs": docs,
            "convert_image": self._convert_to_jpeg_b64,
            "diamond_border_uri": border_uri,
            "monogram_uri": monogram_uri,
            "quote_plus": quote_plus,
            "base_url": base_url,
            "gallery_pages": self._get_gallery_pages,
            # Set both here AND via <t t-set> inside the template: web.html_container
            # resolves class="container" vs "container-fluid" from the binding
            # context, and depending on Odoo version the t-set inside a t-foreach
            # is either local to the iteration or hoisted -- making it explicit
            # in the report_values dict guarantees body.class becomes
            # container-fluid so the 210mm page divs are never clipped to the
            # Bootstrap .container max-width of 540px (or 720/960/1140 at
            # wider breakpoints).
            "full_width": True,
            "cover_image_uri_for": _cover_for,
        }
