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
        if not b64_source:
            return b""
        from PIL import Image

        raw = base64.b64decode(b64_source)
        fd, tmp_path = tempfile.mkstemp(suffix=self._guess_suffix(raw))
        try:
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(raw)
            image = Image.open(tmp_path)
            if image.format == "JPEG":
                return b64_source
            image = image.convert("RGB")
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=92)
            return base64.b64encode(buf.getvalue())
        except Exception:
            _logger.warning("Could not convert image to JPEG for luxury brochure; skipping.", exc_info=True)
            return b""
        finally:
            os.unlink(tmp_path)

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

        return {
            "doc_ids": docids,
            "doc_model": "property.details",
            "docs": docs,
            "convert_image": self._convert_to_jpeg_b64,
            "diamond_border_uri": border_uri,
            "monogram_uri": monogram_uri,
            "quote_plus": quote_plus,
            "base_url": base_url,
        }
