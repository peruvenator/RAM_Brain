"""
Return Stacked Advisor Guide — SVG Exporter
=============================================
Generates multi-page SVG documents from YAML content files,
matching the branded HTML output with identical visual design.

Each page is output as a separate <svg> element within a single SVG file,
using an approach compatible with browsers and design tools.

Usage:
    python generate_svg.py <content.yaml>
    python generate_svg.py content/managed_futures.yaml

Output:
    Advisor_Guide_Output/<Topic>-Advisor-Guide-<Version>.svg
"""

import os
import sys
import re
import base64
import html as html_mod
import textwrap
import yaml

# Ensure the generator package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator import brand_config
from generator.content_schema import validate_content


# ── Constants ────────────────────────────────────────────────────────────────

PW = 612  # US Letter width in pt
PH = 792  # US Letter height in pt

# Margins
ML = 28   # margin-left
MR = 28   # margin-right
MT = 36   # margin-top (0.5in)
MB = 22   # margin-bottom

CW = PW - ML - MR  # content width = 556

# Cover
BANNER_H = 340

# Interior
HEADER_Y = 35
CONTENT_Y = 72       # Below header (56pt header + 16pt gap)
FOOTER_Y = 770
CONTENT_BOTTOM = 750

# Colors (from brand_config)
C_TEXT = brand_config.TEXT_PRIMARY        # #2c3641
C_TEXT2 = brand_config.TEXT_SECONDARY     # #625c6d
C_DARK = brand_config.COVER_DARK         # #172c3a
C_GRAY = brand_config.SECTION_GRAY       # #f0f1f1
C_WHITE = brand_config.WHITE             # #ffffff
C_TEAL = brand_config.TEAL_PRIMARY       # #14cfa6
C_TEAL_L = brand_config.TEAL_LIGHT       # #a1d7c6
C_BORDER = brand_config.BORDER_GRAY      # #bfbfbf

# Approximate character widths per pt for DM Sans (proportional estimate)
# These are rough heuristics for text wrapping in SVG
CHARS_PER_PT = {
    10: 0.55,   # body text ~5.5px per char at 10pt
    13: 0.58,
    16: 0.6,
    22: 0.6,
    42: 0.62,
    40: 0.62,
    38: 0.62,
    9:  0.53,
    8:  0.52,
    7.5: 0.50,
    12: 0.56,
}


def est_chars_per_line(font_size, width=CW, bold=False):
    """Estimate max characters per line given font size and available width."""
    ratio = CHARS_PER_PT.get(font_size, 0.56)
    char_w = font_size * ratio
    if bold:
        char_w *= 1.08  # bold is slightly wider
    return int(width / char_w)


def wrap_text(text, font_size, width=CW, bold=False):
    """Wrap a string into lines that fit within the given width."""
    max_chars = est_chars_per_line(font_size, width, bold)
    return textwrap.wrap(text, width=max_chars)


def escape(text):
    """XML-escape text for SVG."""
    return html_mod.escape(str(text), quote=True)


def embed_backdrop_base64():
    """Read the backdrop image and return a base64 data URI, or empty string."""
    path = brand_config.BACKDROP_IMAGE
    if os.path.exists(path):
        ext = os.path.splitext(path)[1].lower()
        mime = {".svg": "image/svg+xml", ".png": "image/png",
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{data}"
    return ""


def embed_logo_base64(family_key, variant="white"):
    """Read a logo and return base64 data URI."""
    path = brand_config.get_logo_path(family_key, variant)
    if os.path.exists(path):
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/svg+xml"
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{data}"
    return ""


# ── SVG Page Builder ─────────────────────────────────────────────────────────

class SVGPageBuilder:
    """Builds a single SVG page with positioned elements."""

    def __init__(self, page_index=0):
        self.elements = []
        self.y = 0  # current y cursor
        self.page_index = page_index

    def add_raw(self, svg_str):
        """Add raw SVG markup."""
        self.elements.append(svg_str)

    def add_rect(self, x, y, w, h, fill, rx=0):
        self.elements.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{fill}" rx="{rx}"/>'
        )

    def add_text(self, x, y, text, font_size=10, fill=C_TEXT,
                 weight=400, italic=False, anchor="start"):
        style_parts = [
            f"font-family: 'DM Sans', Helvetica, Arial, sans-serif",
            f"font-size: {font_size}pt",
            f"font-weight: {weight}",
            f"fill: {fill}",
        ]
        if italic:
            style_parts.append("font-style: italic")
        style = "; ".join(style_parts)
        self.elements.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'style="{style}">{escape(text)}</text>'
        )

    def add_tspan_line(self, x, y, segments, font_size=10, line_height=1.5):
        """Add a text element with mixed bold/italic <tspan> segments.

        segments: list of (text, bold, italic) tuples
        """
        dy = font_size * line_height
        parts = []
        for text_part, bold, ital in segments:
            w = 700 if bold else 400
            fs = "italic" if ital else "normal"
            parts.append(
                f'<tspan font-weight="{w}" font-style="{fs}">'
                f'{escape(text_part)}</tspan>'
            )
        inner = "".join(parts)
        self.elements.append(
            f'<text x="{x}" y="{y}" '
            f'style="font-family: \'DM Sans\', Helvetica, Arial, sans-serif; '
            f'font-size: {font_size}pt; fill: {C_TEXT}">{inner}</text>'
        )

    def add_wrapped_text(self, x, y, text, font_size=10, fill=C_TEXT,
                         weight=400, italic=False, line_height=1.5,
                         width=CW, max_lines=None):
        """Add text that wraps within width. Returns new y position."""
        lines = wrap_text(text, font_size, width, bold=(weight >= 700))
        if max_lines:
            lines = lines[:max_lines]
        dy = font_size * line_height
        for i, line in enumerate(lines):
            self.add_text(x, y + i * dy, line, font_size, fill, weight, italic)
        return y + len(lines) * dy

    def add_wrapped_rich_text(self, x, y, text, font_size=10, fill=C_TEXT,
                              line_height=1.5, width=CW):
        """Add body text with basic **bold** and *italic* support.

        Strips markdown, wraps, and renders. Returns new y.
        """
        # Strip markdown markers for wrapping, render plain
        plain = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        plain = re.sub(r'\*(.+?)\*', r'\1', plain)
        return self.add_wrapped_text(
            x, y, plain, font_size, fill, 400, False, line_height, width
        )

    def add_image(self, x, y, w, h, data_uri):
        """Add an embedded image."""
        if data_uri:
            self.elements.append(
                f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
                f'href="{data_uri}" preserveAspectRatio="xMidYMid slice"/>'
            )

    def add_line(self, x1, y1, x2, y2, stroke=C_BORDER, width=0.5):
        self.elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{width}"/>'
        )

    def render(self):
        """Return the full SVG for this page."""
        y_offset = self.page_index * (PH + 20)
        inner = "\n    ".join(self.elements)
        return f"""<g transform="translate(0, {y_offset})">
    <!-- Page {self.page_index + 1} background -->
    <rect x="0" y="0" width="{PW}" height="{PH}" fill="{C_WHITE}"
          stroke="#cccccc" stroke-width="0.5"/>
    {inner}
</g>"""


# ── Page Generators ──────────────────────────────────────────────────────────

def build_cover_svg(cover_data, metadata, logo_family):
    """Build the cover page SVG matching the reference PDF layout.

    Layout (top to bottom):
    - White top area with logo (black variant, larger) top-left
    - Full-width banner with teal accent bar on far left, backdrop image,
      left-aligned title, watermark at bottom
    - White intro zone with centered heading + text
    - No footer bar on cover (per reference PDF)
    """
    pg = SVGPageBuilder(0)

    topic = cover_data["topic_display"]
    intro_heading = cover_data["intro_heading"]
    intro_text = cover_data["intro_text"]
    intro_highlight = cover_data.get("intro_highlight", "")
    footer_url = metadata.get("footer_url") or brand_config.get_footer_url(logo_family)

    ACCENT_W = 10

    # ── White top area with logo (taller, larger logo) ──
    TOP_BAR_H = 80
    pg.add_rect(0, 0, PW, TOP_BAR_H, C_WHITE)

    # Logo (black variant, top-left — larger)
    logo_uri = embed_logo_base64(logo_family, "black")
    if logo_uri:
        pg.add_image(28, 18, 220, 44, logo_uri)

    # ── Banner with backdrop ──
    banner_top = TOP_BAR_H
    banner_h = BANNER_H
    pg.add_rect(0, banner_top, PW, banner_h, C_DARK)

    backdrop_uri = embed_backdrop_base64()
    if backdrop_uri:
        pg.add_image(0, banner_top, PW, banner_h, backdrop_uri)

    # Teal accent bar on far left of banner only
    pg.add_rect(0, banner_top, ACCENT_W, banner_h, C_TEAL)

    # Watermark text (faded, positioned at bottom of banner)
    pg.elements.append(
        f'<text x="{PW/2}" y="{banner_top + banner_h - 10}" text-anchor="middle" '
        f'style="font-family: \'DM Sans\', sans-serif; font-size: 85pt; '
        f'font-weight: 700; fill: {C_TEAL_L}; opacity: 0.15">'
        f"Advisor&#x2019;s Guide</text>"
    )

    # Title block (left-aligned within banner, offset from accent bar)
    # Text shadow effect via duplicate text offset behind (matching Leverage PDF)
    title_x = ACCENT_W + 34
    title_y = banner_top + 80
    shadow_dx, shadow_dy = 2, 3
    shadow_color = "rgba(0,0,0,0.55)"

    # Shadow layer (rendered first, behind the main text)
    line1_esc = escape("The Advisor\u2019s Guide to")
    line2_esc = escape("Client Conversations")
    topic_esc = escape(topic)

    pg.add_raw(
        f'<text x="{title_x + shadow_dx}" y="{title_y + shadow_dy}" '
        f'style="font-family: \'DM Sans\', sans-serif; font-size: 42pt; '
        f'font-weight: 500; fill: {shadow_color}; filter: blur(3px)">'
        f'{line1_esc}</text>'
    )
    pg.add_raw(
        f'<text x="{title_x + shadow_dx}" y="{title_y + 48 + shadow_dy}" '
        f'style="font-family: \'DM Sans\', sans-serif; font-size: 42pt; '
        f'font-weight: 500; fill: {shadow_color}; filter: blur(3px)">'
        f'{line2_esc}</text>'
    )
    pg.add_raw(
        f'<text x="{title_x + shadow_dx}" y="{title_y + 96 + shadow_dy}" '
        f'style="font-family: \'DM Sans\', sans-serif; font-size: 38pt; '
        f'font-weight: 400; fill: {shadow_color}; filter: blur(3px)">'
        f'about</text>'
    )
    pg.add_raw(
        f'<text x="{title_x + shadow_dx}" y="{title_y + 144 + shadow_dy}" '
        f'style="font-family: \'DM Sans\', sans-serif; font-size: 48pt; '
        f'font-weight: 700; fill: rgba(0,0,0,0.45); filter: blur(3px)">'
        f'{topic_esc}</text>'
    )

    # Main title text
    pg.add_text(title_x, title_y, "The Advisor\u2019s Guide to",
                42, C_WHITE, 500)
    pg.add_text(title_x, title_y + 48, "Client Conversations",
                42, C_WHITE, 500)
    pg.add_text(title_x, title_y + 96, "about",
                38, C_WHITE, 400)
    pg.add_text(title_x, title_y + 144, topic,
                48, C_TEAL, 700)

    # ── Intro section below banner ──
    intro_zone_top = banner_top + banner_h
    intro_y = intro_zone_top + 40

    # Intro heading (centered)
    pg.add_text(PW / 2, intro_y, intro_heading,
                22, C_TEXT, 700, anchor="middle")
    intro_y += 36

    # Intro body (centered — wrap then center each line)
    body_lines = wrap_text(intro_text, 13, CW - 40, bold=False)
    for line in body_lines:
        pg.add_text(PW / 2, intro_y, line,
                    13, C_TEXT, 500, anchor="middle")
        intro_y += 13 * 1.5
    intro_y += 8

    # Highlight text (centered, teal)
    if intro_highlight:
        highlight_lines = wrap_text(intro_highlight, 13, CW - 40, bold=True)
        for line in highlight_lines:
            pg.add_text(PW / 2, intro_y, line,
                        13, C_TEAL, 700, anchor="middle")
            intro_y += 13 * 1.5

    # Cover page has NO footer bar (per reference PDF)

    return pg


def build_interior_header(pg, topic, logo_family=None):
    """Add the standard interior page header matching reference PDF.

    Structure: logo (left) | right-aligned titles (3 lines) | teal accent bar (far right).
    No italic on series title. No bottom border line.
    """
    # Logo (black variant, top-left — larger)
    if logo_family:
        logo_uri = embed_logo_base64(logo_family, "black")
        if logo_uri:
            pg.add_image(ML, 10, 190, 36, logo_uri)

    # Right-aligned title block
    title_x = PW - MR - 14  # offset from accent bar
    pg.add_text(title_x, 20, "The Advisor\u2019s Guide to",
                11, C_TEAL, 700, anchor="end")
    pg.add_text(title_x, 33, "Client Conversations about",
                11, C_TEXT, 500, anchor="end")
    pg.add_text(title_x, 46, topic,
                11, C_TEXT, 500, anchor="end")

    # Teal accent bar on far right
    pg.add_rect(PW - 10, 0, 10, 56, C_TEAL)

    # No bottom border line — clean separation per reference PDF


def build_interior_footer(pg, footer_url):
    """Add the standard interior page footer matching reference PDF.

    Structure: dark icon square (left) | teal band (center) | white area with URL (right).
    """
    footer_h = 28
    footer_y = PH - footer_h

    # Dark icon square
    pg.add_rect(0, footer_y, footer_h, footer_h, C_DARK)
    # RS icon placeholder
    pg.add_text(footer_h / 2, footer_y + footer_h / 2 + 3, "RS",
                8, C_WHITE, 700, anchor="middle")

    # Teal band (fills center)
    teal_x = footer_h
    url_area_w = 160  # width for URL area on the right
    teal_w = PW - footer_h - url_area_w
    pg.add_rect(teal_x, footer_y, teal_w, footer_h, C_TEAL)

    # White URL area (right)
    pg.add_rect(teal_x + teal_w, footer_y, url_area_w, footer_h, C_WHITE)
    pg.add_text(PW - MR, footer_y + footer_h / 2 + 3, footer_url,
                9, C_TEXT, 700, anchor="end")


def _estimate_svg_section_height(sec):
    """Estimate height in pt of a section when rendered in SVG."""
    sec_type = sec.get("type", "")
    w = CW

    if sec_type == "heading":
        lines = len(wrap_text(sec.get("text", ""), 13, w, bold=True))
        return 10 + lines * 13 * 1.2 + 6

    elif sec_type == "subsection":
        lines = len(wrap_text(sec.get("text", ""), 13, w - 14, bold=True))
        return 8 + lines * 13 * 1.2 + 4

    elif sec_type == "body":
        text = sec.get("text", "")
        plain = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        plain = re.sub(r'\*(.+?)\*', r'\1', plain)
        lines = len(wrap_text(plain, 10, w))
        return lines * 10 * 1.5 + 4

    elif sec_type == "callout":
        lines = len(wrap_text(sec.get("text", ""), 13, w - 16, bold=True))
        return 6 + lines * 13 * 1.35 + 4 + 6

    elif sec_type == "dark_panel":
        heading_h = 12 * 1.2 + 12
        body = sec.get("body", "")
        body_lines = len(wrap_text(body, 10, w - 24)) if body else 0
        body_h = body_lines * 10 * 1.5 + 20 if body_lines else 0
        return 8 + heading_h + body_h + 8

    elif sec_type == "table":
        rows = sec.get("rows", [])
        caption_h = 16 if sec.get("caption") else 0
        return 6 + caption_h + 22 + len(rows) * 22 + 8

    elif sec_type == "source_note":
        lines = len(wrap_text(sec.get("text", ""), 7.5, w))
        return lines * 7.5 * 1.25 + 4

    elif sec_type == "bullet_list":
        items = sec.get("items", [])
        total = 0
        for item in items:
            lines = len(wrap_text(str(item), 10, w - 20))
            total += lines * 10 * 1.5 + 4
        return total + 4

    return 20


def _render_section_to_svg(pg, sec, y):
    """Render a single section onto an SVG page. Returns new y position."""
    sec_type = sec.get("type", "")

    if sec_type == "heading":
        if y > CONTENT_Y + 5:
            y += 10  # space before heading (not first)
        # Small teal rectangle (6pt x 14pt) to the left of heading text
        text_h = 13 * 1.2
        rect_y = y + (text_h - 14) / 2  # vertically centered
        pg.add_rect(ML, rect_y, 6, 14, C_TEAL)
        pg.add_text(ML + 14, y + 13, sec["text"], 13, C_TEXT, 700)
        y += 13 * 1.2 + 6

    elif sec_type == "subsection":
        y += 8
        text = sec["text"].replace('"', '\u201c').replace('"', '\u201d')
        # Plain bold dark text, no decoration
        pg.add_text(ML, y + 13, text, 13, C_TEXT, 700)
        y += 13 * 1.2 + 4

    elif sec_type == "body":
        text = sec["text"]
        plain = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        plain = re.sub(r'\*(.+?)\*', r'\1', plain)
        y = pg.add_wrapped_text(
            ML, y, plain,
            font_size=10, fill=C_TEXT, weight=400,
            line_height=1.5, width=CW
        )
        y += 4

    elif sec_type == "callout":
        y += 6
        callout_lines = wrap_text(sec["text"], 13, CW - 16, bold=True)
        border_h = len(callout_lines) * 13 * 1.35 + 4
        pg.add_rect(ML, y - 13, 3, border_h, C_TEAL)
        for i, line in enumerate(callout_lines):
            pg.add_text(ML + 14, y + i * (13 * 1.35), line,
                        13, C_TEAL, 700, italic=True)
        y += border_h + 6

    elif sec_type == "dark_panel":
        y += 8
        heading = sec.get("heading", "")
        body = sec.get("body", "")

        heading_h = 12 * 1.2 + 12
        body_lines = wrap_text(body, 10, CW - 24) if body else []
        body_h = len(body_lines) * 10 * 1.5 + 20 if body_lines else 0
        total_h = heading_h + body_h

        pg.add_rect(ML, y, CW, heading_h, C_TEAL, rx=2)
        if heading:
            pg.add_text(ML + 12, y + heading_h - 6, heading, 12, C_WHITE, 700)

        if body_lines:
            pg.add_rect(ML, y + heading_h, CW, body_h, C_GRAY)
            body_text_y = y + heading_h + 14
            for i, line in enumerate(body_lines):
                pg.add_text(ML + 12, body_text_y + i * (10 * 1.5), line,
                            10, C_TEXT, 400)

        y += total_h + 8

    elif sec_type == "table":
        y += 6
        caption = sec.get("caption", "")
        headers = sec.get("headers", [])
        rows = sec.get("rows", [])

        if caption:
            pg.add_text(ML, y, caption, 10, C_TEXT, 700)
            y += 16

        n_cols = len(headers)
        col_w = CW / n_cols
        row_h = 22

        pg.add_rect(ML, y, CW, row_h, C_TEXT)
        for ci, hdr in enumerate(headers):
            pg.add_text(ML + ci * col_w + 8, y + 15, hdr, 9, C_WHITE, 700)
        y += row_h

        for ri, row in enumerate(rows):
            bg = C_GRAY if ri % 2 == 1 else C_WHITE
            pg.add_rect(ML, y, CW, row_h, bg)
            pg.add_line(ML, y, ML + CW, y, C_BORDER, 0.5)
            for ci, cell in enumerate(row):
                pg.add_text(ML + ci * col_w + 8, y + 15, str(cell), 9, C_TEXT, 400)
            y += row_h

        pg.add_line(ML, y, ML + CW, y, C_BORDER, 0.5)
        for ci in range(n_cols + 1):
            x = ML + ci * col_w
            pg.add_line(x, y - (len(rows) + 1) * row_h, x, y, C_BORDER, 0.5)
        y += 8

    elif sec_type == "source_note":
        y = pg.add_wrapped_text(
            ML, y, sec.get("text", ""),
            font_size=7.5, fill=C_TEXT2, weight=400,
            italic=True, line_height=1.25, width=CW
        )
        y += 4

    elif sec_type == "bullet_list":
        items = sec.get("items", [])
        for item in items:
            pg.add_text(ML + 8, y, "\u2022", 10, C_TEXT, 400)
            y = pg.add_wrapped_text(
                ML + 20, y, str(item),
                font_size=10, fill=C_TEXT, weight=400,
                line_height=1.5, width=CW - 20
            )
            y += 4
        y += 4

    elif sec_type == "gray_section":
        inner_sections = sec.get("sections", [])
        y += 6
        est_h = len(inner_sections) * 40 + 32
        pg.add_rect(ML, y, CW, est_h, C_GRAY, rx=2)
        inner_y = y + 16
        for inner_sec in inner_sections:
            if inner_sec.get("type") == "heading":
                pg.add_text(ML + 16, inner_y, inner_sec["text"], 16, C_TEXT, 700)
                inner_y += 24
            elif inner_sec.get("type") == "body":
                plain = re.sub(r'\*\*(.+?)\*\*', r'\1', inner_sec["text"])
                plain = re.sub(r'\*(.+?)\*', r'\1', plain)
                inner_y = pg.add_wrapped_text(
                    ML + 16, inner_y, plain,
                    font_size=10, fill=C_TEXT, weight=400,
                    line_height=1.5, width=CW - 32
                )
                inner_y += 8
        y = inner_y + 16

    return y


def render_sections_to_svg(sections, topic, footer_url, start_page_index=1,
                           logo_family=None):
    """Render content sections into SVG pages with continuous flow.

    Uses height estimation to auto-split content across pages,
    eliminating white space. Explicit page_break markers force a new page.
    """
    available = CONTENT_BOTTOM - CONTENT_Y  # ~678pt

    pages = []
    pg = SVGPageBuilder(start_page_index + len(pages))
    build_interior_header(pg, topic, logo_family)
    build_interior_footer(pg, footer_url)
    y = CONTENT_Y

    for sec in sections:
        sec_type = sec.get("type", "")

        if sec_type == "page_break":
            # Force new page
            pages.append(pg)
            pg = SVGPageBuilder(start_page_index + len(pages))
            build_interior_header(pg, topic, logo_family)
            build_interior_footer(pg, footer_url)
            y = CONTENT_Y
            continue

        # Estimate if this section fits on the current page
        sec_h = _estimate_svg_section_height(sec)
        sec_type = sec.get("type", "")

        # Look-ahead: if heading/subsection, include next section's height
        # to prevent orphaned headings at page bottom.
        # Covers heading→body, heading→subsection→body, subsection→body
        combined_h = sec_h
        sec_idx = sections.index(sec)
        if sec_type in ("heading", "subsection") and sec_idx + 1 < len(sections):
            next_sec = sections[sec_idx + 1]
            next_type = next_sec.get("type", "")
            if next_type in ("body", "bullet_list", "subsection"):
                combined_h += _estimate_svg_section_height(next_sec)
                # If heading→subsection→body, also include the body
                if next_type == "subsection" and sec_idx + 2 < len(sections):
                    next_next_sec = sections[sec_idx + 2]
                    if next_next_sec.get("type") in ("body", "bullet_list"):
                        combined_h += _estimate_svg_section_height(next_next_sec)

        if y + combined_h > CONTENT_BOTTOM and y > CONTENT_Y + 10:
            # Doesn't fit — start a new page
            pages.append(pg)
            pg = SVGPageBuilder(start_page_index + len(pages))
            build_interior_header(pg, topic, logo_family)
            build_interior_footer(pg, footer_url)
            y = CONTENT_Y

        y = _render_section_to_svg(pg, sec, y)

    pages.append(pg)
    return pages


def build_disclosures_svg(disclosures, topic, footer_url, page_index,
                          logo_family=None):
    """Build the disclosures/glossary SVG page."""
    pg = SVGPageBuilder(page_index)
    build_interior_header(pg, topic, logo_family)
    build_interior_footer(pg, footer_url)

    y = CONTENT_Y

    # Glossary (above disclosures per user request)
    glossary = disclosures.get("glossary", [])
    if glossary:
        pg.add_text(ML, y, "Glossary", 13, C_TEXT, 700)
        y += 20

        for entry in glossary:
            term = entry.get("term", "")
            definition = entry.get("definition", "")

            pg.add_text(ML, y, term, 10, C_TEXT, 700)
            y += 14

            y = pg.add_wrapped_text(
                ML, y, definition,
                font_size=10, fill=C_TEXT, weight=400,
                line_height=1.5, width=CW
            )
            y += 6

        y += 10

    # Disclosures heading
    pg.add_text(ML, y, "Disclosures", 12, C_TEXT, 700)
    y += 20

    # Legal text
    legal = disclosures.get("legal_text", "")
    if legal:
        paragraphs = legal.strip().split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if para:
                y = pg.add_wrapped_text(
                    ML, y, para,
                    font_size=8, fill=C_TEXT, weight=400,
                    line_height=1.25, width=CW
                )
                y += 4

    # Copyright
    y += 8
    year = "2026"
    pg.add_text(ML, y, f"\u00a9 Return Stacked\u00ae Portfolio Solutions, {year}. All rights reserved.",
                8, C_TEXT, 400)

    return pg


# ── Main Generator ────────────────────────────────────────────────────────────

def generate_svg(yaml_path):
    """Generate a branded SVG advisor guide from a YAML content file.

    Args:
        yaml_path: Path to the YAML content file.

    Returns:
        Path to the generated SVG file.
    """
    # Load YAML
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Validate
    errors = validate_content(data)
    if errors:
        print("Content validation errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    metadata = data["metadata"]
    cover = data["cover"]
    sections = data.get("sections", [])
    disclosures = data.get("disclosures", {})

    topic = metadata["topic"]
    version = metadata["version"]
    logo_family = metadata["logo_family"]
    footer_url = metadata.get("footer_url") or brand_config.get_footer_url(logo_family)

    # Ensure output directory exists
    os.makedirs(brand_config.OUTPUT_DIR, exist_ok=True)

    # ── Build pages ──
    all_pages = []

    # 1. Cover page
    cover_pg = build_cover_svg(cover, metadata, logo_family)
    all_pages.append(cover_pg)

    # 2. Interior pages
    interior_pages = render_sections_to_svg(
        sections, topic, footer_url, start_page_index=1,
        logo_family=logo_family
    )
    all_pages.extend(interior_pages)

    # 3. Disclosures page
    disc_pg = build_disclosures_svg(
        disclosures, topic, footer_url,
        page_index=len(all_pages),
        logo_family=logo_family
    )
    all_pages.append(disc_pg)

    # ── Assemble SVG ──
    total_h = len(all_pages) * (PH + 20) - 20  # pages stacked with 20pt gaps
    page_svgs = "\n\n".join(pg.render() for pg in all_pages)

    safe_topic = topic.replace(" ", "-")
    title = f"{safe_topic} Advisor Guide {version}"

    svg_doc = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {PW} {total_h}"
     width="{PW}" height="{total_h}">

<title>{escape(title)}</title>

<!-- Background -->
<rect width="{PW}" height="{total_h}" fill="#e0e0e0"/>

{page_svgs}

</svg>'''

    # Write output
    output_filename = f"{safe_topic}-Advisor-Guide-{version}.svg"
    output_path = os.path.join(brand_config.OUTPUT_DIR, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_doc)

    print(f"Generated SVG: {output_path}")
    print(f"  Pages: {len(all_pages)}")
    print(f"  Dimensions: {PW}x{total_h} pt")
    return output_path


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_svg.py <content.yaml>")
        print("Example: python generate_svg.py content/managed_futures.yaml")
        sys.exit(1)

    yaml_file = sys.argv[1]
    if not os.path.exists(yaml_file):
        print(f"Error: File not found: {yaml_file}")
        sys.exit(1)

    generate_svg(yaml_file)
