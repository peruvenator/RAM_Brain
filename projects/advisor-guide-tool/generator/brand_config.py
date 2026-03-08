"""
Return Stacked Brand Configuration
===================================
Single source of truth for all brand constants.
Derived from analysis of 5 existing Advisor Guide PDFs,
normalized to resolve inconsistencies.
"""

import os

# ── Base Paths ────────────────────────────────────────────────────────────────

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND_DIR = os.path.join(os.path.dirname(TOOL_ROOT), "Brand_elements")
FONT_DIR = os.path.join(BRAND_DIR, "Font_Family")
LOGOS_DIR = os.path.join(BRAND_DIR, "Logos")
BACKDROP_DIR = os.path.join(BRAND_DIR, "Background_images")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
OUTPUT_DIR = os.path.join(TOOL_ROOT, "Advisor_Guide_Output")

# ── Default Backdrop ─────────────────────────────────────────────────────────
BACKDROP_IMAGE = os.path.join(BACKDROP_DIR, "RS-Background-Blue.svg")

# ── Colors ────────────────────────────────────────────────────────────────────

# Text & Backgrounds
TEXT_PRIMARY = "#2c3641"       # Dark blue-gray — all body text, headings
TEXT_SECONDARY = "#625c6d"     # Warm gray — supporting text, chart labels
COVER_DARK = "#172c3a"         # Dark navy — cover page banner
SECTION_GRAY = "#f0f1f1"       # Light gray — content section backgrounds
WHITE = "#ffffff"
BORDER_GRAY = "#bfbfbf"        # Table borders, dividers
BLACK = "#000000"

# Accents
TEAL_PRIMARY = "#14cfa6"       # Callouts, highlights, key messaging
TEAL_LIGHT = "#a1d7c6"         # Decorative watermark text only
BLUE_SECONDARY = "#3a6a9c"     # Links, secondary accents, charts
BLUE_LIGHT = "#7da5ce"         # Chart elements, data viz
YELLOW = "#ebe96a"             # Sparingly, for highlights

# ── Typography ────────────────────────────────────────────────────────────────

FONT_FAMILY = "DM Sans"

# Font file mapping (weight name → filename without extension)
FONT_FILES = {
    "Thin":          "DMSans-Thin",
    "ThinItalic":    "DMSans-ThinItalic",
    "ExtraLight":    "DMSans-ExtraLight",
    "ExtraLightItalic": "DMSans-ExtraLightItalic",
    "Light":         "DMSans-Light",
    "LightItalic":   "DMSans-LightItalic",
    "Regular":       "DMSans-Regular",
    "Italic":        "DMSans-Italic",
    "Medium":        "DMSans-Medium",
    "MediumItalic":  "DMSans-MediumItalic",
    "SemiBold":      "DMSans-SemiBold",
    "SemiBoldItalic": "DMSans-SemiBoldItalic",
    "Bold":          "DMSans-Bold",
    "BoldItalic":    "DMSans-BoldItalic",
    "ExtraBold":     "DMSans-ExtraBold",
    "ExtraBoldItalic": "DMSans-ExtraBoldItalic",
}

# CSS font-weight / font-style mapping
FONT_WEIGHTS = {
    "Thin":          (100, "normal"),
    "ThinItalic":    (100, "italic"),
    "ExtraLight":    (200, "normal"),
    "ExtraLightItalic": (200, "italic"),
    "Light":         (300, "normal"),
    "LightItalic":   (300, "italic"),
    "Regular":       (400, "normal"),
    "Italic":        (400, "italic"),
    "Medium":        (500, "normal"),
    "MediumItalic":  (500, "italic"),
    "SemiBold":      (600, "normal"),
    "SemiBoldItalic": (600, "italic"),
    "Bold":          (700, "normal"),
    "BoldItalic":    (700, "italic"),
    "ExtraBold":     (800, "normal"),
    "ExtraBoldItalic": (800, "italic"),
}

# ── Type Scale (in pt for print, converted to CSS units in stylesheet) ────────

# Cover page
COVER_WATERMARK_SIZE = 85       # "Advisor's Guide" decorative
COVER_TITLE_SIZE = 42           # "Client Conversations"
COVER_TOPIC_SIZE = 48           # Topic name (e.g. "Managed Futures")
COVER_CONNECTOR_SIZE = 38       # "about"
COVER_INTRO_HEADING_SIZE = 22   # "Why This Conversation Matters"
COVER_INTRO_TEXT_SIZE = 13      # Introductory paragraph

# Interior pages
HEADER_SERIES_SIZE = 12         # "The Advisor's Guide to Client Conversations"
HEADER_TOPIC_SIZE = 12          # "about [Topic]"
SECTION_HEADING_SIZE = 13       # Section headings (H2) — with teal accent bar
SUBSECTION_HEADING_SIZE = 13    # Subsection headings (H3)
BODY_SIZE = 10                  # Body text
CALLOUT_SIZE = 13               # Teal callout text
PANEL_TEXT_SIZE = 13            # White-on-dark panel text
CHART_LABEL_SIZE = 8            # Chart axis labels
TABLE_HEADER_SIZE = 9           # Table header cells
TABLE_BODY_SIZE = 9             # Table body cells
FOOTER_SIZE = 9                 # Footer URL
DISCLAIMER_SIZE = 8             # Legal/disclaimer text
GLOSSARY_TERM_SIZE = 10         # Glossary term
GLOSSARY_DEF_SIZE = 10          # Glossary definition

# ── Layout (in pt) ────────────────────────────────────────────────────────────

PAGE_WIDTH_PT = 612             # US Letter width
PAGE_HEIGHT_PT = 792            # US Letter height
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0

MARGIN_TOP = 36                 # pt (0.5in)
MARGIN_BOTTOM = 22              # pt
MARGIN_LEFT = 28                # pt (0.39in)
MARGIN_RIGHT = 28               # pt
CONTENT_WIDTH = PAGE_WIDTH_PT - MARGIN_LEFT - MARGIN_RIGHT  # 556pt

# Cover page dimensions
COVER_BANNER_HEIGHT = 340       # pt — dark banner area

# Cover title shadow (duplicate-element approach — CSS text-shadow cannot
# produce visible black shadows on the dark navy banner background)
COVER_SHADOW_OFFSET_X = 6       # px — horizontal offset (right)
COVER_SHADOW_OFFSET_Y = 6       # px — vertical offset (down)
COVER_SHADOW_COLOR = BLACK       # Pure black duplicate behind white text
COVER_SHADOW_OPACITY = 1.0       # Full opacity; contrast comes from offset

# Section heading accent
SECTION_HEADING_ACCENT_WIDTH = 6     # pt — teal rectangle width
SECTION_HEADING_ACCENT_HEIGHT = 14   # pt — teal rectangle height
SECTION_HEADING_ACCENT_COLOR = TEAL_PRIMARY
# Note: subsection headings do NOT get the teal accent rectangle

# Interior page zones
HEADER_ZONE_TOP = 25            # pt from top
HEADER_ZONE_BOTTOM = 55        # pt from top
CONTENT_ZONE_TOP = 65          # pt from top
CONTENT_ZONE_BOTTOM = 750      # pt from top
FOOTER_Y = 770                 # pt from top

# ── Line Spacing ──────────────────────────────────────────────────────────────

LINE_HEIGHT_BODY = 1.5
LINE_HEIGHT_HEADING = 1.2
LINE_HEIGHT_CALLOUT = 1.35
LINE_HEIGHT_DISCLAIMER = 1.25

# ── Spacing (in pt) ──────────────────────────────────────────────────────────

SPACE_AFTER_SECTION_HEADING = 8
SPACE_BEFORE_SECTION_HEADING = 18
SPACE_AFTER_SUBSECTION_HEADING = 6
SPACE_BEFORE_SUBSECTION_HEADING = 14
SPACE_AFTER_BODY_PARA = 8
SPACE_AFTER_CALLOUT = 12
SPACE_BEFORE_CALLOUT = 12

# ── Logo Families ─────────────────────────────────────────────────────────────
# Each family maps to a business silo with its own logo variants and footer URL.
# Footer URLs follow this mapping:
#   - Return Stacked ETFs (US)     → www.returnstackedetfs.com
#   - Return Stacked ETFs (Canada) → www.returnstackedetfs.ca
#   - Return Stacked Funds         → www.returnstackedfunds.com
#   - Return Stacked Portfolio Solutions → www.returnstacked.com

LOGO_FAMILIES = {
    "RS_ETF_Logos": {
        "name": "Return Stacked ETFs (US)",
        "business_name": "Return Stacked\u00ae ETFs",
        "white": "ReturnStackedEtfs-inline-white.png",
        "black": "ReturnStackedEtfs-inline-black.png",
        "footer_url": "www.returnstackedetfs.com",
    },
    "RS_ETF_Canada_Logos": {
        "name": "Return Stacked ETFs (Canada)",
        "business_name": "Return Stacked\u00ae ETFs Canada",
        "white": "RS-ETFs-longpoint-Canada-Logo-White.png",
        "black": "RS-ETFs-longpoint-Canada-Logo-Black.png",
        "footer_url": "www.returnstackedetfs.ca",
    },
    "RS_Funds_Logos": {
        "name": "Return Stacked Funds",
        "business_name": "Return Stacked\u00ae Funds",
        "white": "ReturnStacked-Funds-White.png",
        "black": "ReturnStacked-Funds-black.png",
        "footer_url": "www.returnstackedfunds.com",
    },
    "RS_Portfolio_Solutions_logos": {
        "name": "Return Stacked Portfolio Solutions",
        "business_name": "Return Stacked\u00ae Portfolio Solutions",
        "white": "Return Stacked Portfolio Solutions White.png",
        "black": "Return Stacked Portfolio Solutions Black.png",
        "footer_url": "www.returnstacked.com",
    },
    "RS_Icons": {
        "name": "Return Stacked Icon",
        "business_name": "Return Stacked\u00ae",
        "svg": "ReturnStacked-Icon.svg",
        "footer_url": "www.returnstacked.com",
    },
}


def get_logo_path(family_key, variant="white"):
    """Get the full path to a logo file.

    Args:
        family_key: Key from LOGO_FAMILIES (e.g. 'RS_ETF_Logos')
        variant: 'white', 'black', or 'svg'

    Returns:
        Full filesystem path to the logo file.
    """
    family = LOGO_FAMILIES[family_key]
    filename = family.get(variant, family.get("black", ""))
    return os.path.join(LOGOS_DIR, family_key, filename)


def get_footer_url(family_key):
    """Get the footer URL for a given logo family."""
    return LOGO_FAMILIES[family_key]["footer_url"]


def get_business_name(family_key):
    """Get the business name for a given logo family (used in copyright line)."""
    return LOGO_FAMILIES[family_key]["business_name"]


def get_icon_svg_path():
    """Get the full path to the Return Stacked icon SVG."""
    return os.path.join(LOGOS_DIR, "RS_Icons", "ReturnStacked-Icon.svg")


def load_icon_svg():
    """Load the Return Stacked icon SVG content.

    Returns:
        SVG markup string, or an empty string if file not found.
    """
    svg_path = get_icon_svg_path()
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def build_copyright_text(family_key, year=None):
    """Build the standard copyright line for a business silo.

    Format: \u00a9 [Business Name], [Year]. All rights reserved.

    Args:
        family_key: Key from LOGO_FAMILIES.
        year: Copyright year (defaults to current year).

    Returns:
        Copyright string.
    """
    if year is None:
        from datetime import date
        year = date.today().year
    business = get_business_name(family_key)
    return f"\u00a9 {business}, {year}. All rights reserved."
