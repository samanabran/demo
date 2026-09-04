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
        # Written to a real file and reopened by path, not Image.open(BytesIO(raw)):
        # extended-format WebP (VP8X container -- ICC profile/alpha/EXIF present,
        # common on real property photos) fails with PIL.UnidentifiedImageError
        # when read from an in-memory stream on this server's Pillow/libwebp
        # build, even though the identical bytes decode fine from a path. Cost
        # a real brochure its cover photo (silently fell back to a blank navy
        # rectangle) before this was caught -- see debug session notes for the
        # repro. The disk round-trip is not the render-time bottleneck anyway
        # (measured ~3.7s for all image processing combined vs wkhtmltopdf's
        # own ~9-12s), so there's no performance reason to avoid it here.
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
    def _render_crop_fit(self, b64_source, target_w, target_h, quality=90):
        """Return a JPEG data URI center-cropped to exactly target_w:target_h.

        Why this exists: wkhtmltopdf's QtWebKit engine does not honor CSS
        object-fit, so any <img> forced into a box via width:100%;
        height:100% on a mismatched aspect ratio gets stretched, not
        cropped -- this is what produced the visibly squashed banner/thumb
        photos on the interior page. Doing the "cover" crop with PIL before
        the image ever reaches the template sidesteps the limitation
        entirely: once the JPEG's own aspect ratio already matches the CSS
        box, a plain width:100%/height:100% is a lossless 1:1 fit, not a
        stretch.

        target_w/target_h should be the box's real physical print size in
        pixels at the print DPI we want (300dpi), not CSS/screen pixels --
        the resulting JPEG is embedded as-is, so its own pixel count is what
        determines print sharpness regardless of wkhtmltopdf's render dpi.
        We never upscale past what the source can honestly deliver: if the
        cropped source is smaller than the requested target, we keep the
        source's native resolution instead of fabricating detail with
        Lanczos upsampling.
        """
        from PIL import Image
        if not b64_source:
            return None
        try:
            raw = base64.b64decode(b64_source)
            # See _convert_to_jpeg_b64 for why this goes through a real file
            # path rather than Image.open(BytesIO(raw)) -- extended-format
            # WebP fails to decode from an in-memory stream here.
            fd, tmp_path = tempfile.mkstemp(suffix=self._guess_suffix(raw))
            try:
                with os.fdopen(fd, "wb") as tmp:
                    tmp.write(raw)
                src = Image.open(tmp_path).convert("RGB")
            finally:
                os.unlink(tmp_path)
        except Exception:
            _logger.warning(
                "Image open failed for crop-fit render; skipping.",
                exc_info=True,
            )
            return None

        src_w, src_h = src.size
        # Center-crop into the target aspect ratio without stretching.
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h if src_h else target_ratio
        if src_ratio > target_ratio:
            # Source is wider than target -- crop horizontally.
            new_w = max(1, int(src_h * target_ratio))
            offset = (src_w - new_w) // 2
            src = src.crop((offset, 0, offset + new_w, src_h))
        else:
            # Source is taller than target -- crop vertically.
            new_h = max(1, int(src_w / target_ratio))
            offset = (src_h - new_h) // 2
            src = src.crop((0, offset, src_w, offset + new_h))

        cropped_w, cropped_h = src.size
        if cropped_w > target_w and cropped_h > target_h:
            src = src.resize((target_w, target_h), Image.LANCZOS)
        # else: cropped source is already at or below the print target, so
        # leave it at native resolution rather than upscale it.

        buf = io.BytesIO()
        src.save(buf, format="JPEG", quality=quality)
        return (
            "data:image/jpeg;base64,"
            + base64.b64encode(buf.getvalue()).decode("ascii")
        )

    @api.model
    def _resize_max_dim(self, b64_source, max_dim=1200, quality=85):
        """Return JPEG base64 bytes downsized so neither side exceeds max_dim.

        Why this exists: the gallery-grid photos (page 3+) used to pass
        image_1920 straight through convert_image() with zero resizing --
        fine for the old image_512 source, but once that call site switched
        to the full 1920px source it meant embedding photos 2-4x larger (in
        each dimension) than the ~278pt print box ever needed, across up to
        18 photos per brochure. That's what pushed a 20-photo brochure's
        render time to ~26s and its PDF to ~30MB, long enough that visitors
        were abandoning the download (nginx logs it as HTTP 499) before it
        finished. 1200px covers a real 300dpi print at this box size with
        room to spare; downsizing before embedding is what actually cuts
        wkhtmltopdf's and the browser's work, not just the file size.
        """
        if not b64_source:
            return b''
        from PIL import Image
        raw = base64.b64decode(b64_source)
        # See _convert_to_jpeg_b64 for why this goes through a real file path.
        fd, tmp_path = tempfile.mkstemp(suffix=self._guess_suffix(raw))
        try:
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(raw)
            image = Image.open(tmp_path).convert('RGB')
            w, h = image.size
            if max(w, h) > max_dim:
                scale = max_dim / max(w, h)
                image = image.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=quality)
            return base64.b64encode(buf.getvalue())
        except Exception:
            _logger.warning(
                "Could not resize image for luxury brochure gallery; skipping.",
                exc_info=True,
            )
            return b''
        finally:
            os.unlink(tmp_path)

    @api.model
    def _render_cover_full_bleed(self, b64_source, target_w=2480, target_h=3508):
        """Return a JPEG data URI of the cover photo pre-rendered at A4 size.

        target_w/target_h default to A4 at 300dpi (210mm/297mm) instead of
        the previous 794x1123 (A4 at 96dpi screen resolution) so the cover
        photo -- the single largest image in the brochure -- prints sharp
        rather than screen-soft. _render_crop_fit already refuses to upscale
        past the source's real resolution, so this is a ceiling, not a
        guarantee: a low-res source still won't be fabricated into 300dpi
        detail, it just won't be needlessly downsampled to 96dpi either.
        """
        return self._render_crop_fit(b64_source, target_w, target_h, quality=88)

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
            "crop_fit_uri": self._render_crop_fit,
            "resize_image": self._resize_max_dim,
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
