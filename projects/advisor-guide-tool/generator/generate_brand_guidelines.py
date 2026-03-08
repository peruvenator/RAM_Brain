"""
Return Stacked Brand Guidelines Generator
==========================================
Generates a beautifully designed brand guidelines document
using the brand system itself — DM Sans, our color palette,
our layout conventions.

Usage:
    python generate_brand_guidelines.py

Output:
    Advisor_Guide_Output/Return-Stacked-Brand-Guidelines.html
"""

import os
import sys
import html as h
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator import brand_config

# ── Paths ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = brand_config.OUTPUT_DIR
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "RS Advisor Guide Brand Guidelines.html")

# Relative paths from output dir
FONT_REL = os.path.relpath(brand_config.FONT_DIR, OUTPUT_DIR).replace("\\", "/")
LOGOS_REL = os.path.relpath(brand_config.LOGOS_DIR, OUTPUT_DIR).replace("\\", "/")
BRAND_DIR_REL = os.path.relpath(brand_config.BRAND_DIR, OUTPUT_DIR).replace("\\", "/")
BACKDROP_DIR_REL = os.path.relpath(brand_config.BACKDROP_DIR, OUTPUT_DIR).replace("\\", "/")
BACKDROP_BLUE_REL = f"{BACKDROP_DIR_REL}/RS-Background-Blue.png"
BACKDROP_GREEN_REL = f"{BACKDROP_DIR_REL}/RS-Background-Green.png"


# ── Font-face CSS ────────────────────────────────────────────────────────────

def build_font_faces():
    lines = []
    for name, (weight, style) in brand_config.FONT_WEIGHTS.items():
        filename = brand_config.FONT_FILES[name]
        lines.append(
            f"@font-face {{ font-family: 'DM Sans'; "
            f"src: url('{FONT_REL}/{filename}.ttf'); "
            f"font-weight: {weight}; font-style: {style}; }}"
        )
    return "\n".join(lines)


# ── Color swatch HTML ────────────────────────────────────────────────────────

def swatch(hex_color, name, usage, text_color="#ffffff"):
    """Build a single color swatch card."""
    # Determine a nice contrasting text
    return f'''<div class="swatch-card">
    <div class="swatch-block" style="background:{hex_color}; color:{text_color};">
        <span class="swatch-hex">{hex_color.upper()}</span>
    </div>
    <div class="swatch-label">{h.escape(name)}</div>
    <div class="swatch-usage">{h.escape(usage)}</div>
</div>'''


def build_color_section():
    """Build the full color palette section."""
    primary_swatches = [
        swatch("#2c3641", "Text Primary", "Body text, headings, table headers"),
        swatch("#625c6d", "Text Secondary", "Supporting text, chart labels, captions"),
        swatch("#172c3a", "Cover Dark", "Cover banner, dark panels"),
        swatch("#f0f1f1", "Section Gray", "Content backgrounds, alternating rows", "#2c3641"),
        swatch("#ffffff", "White", "Page background, text on dark surfaces", "#2c3641"),
        swatch("#bfbfbf", "Border Gray", "Table borders, divider lines", "#2c3641"),
    ]

    accent_swatches = [
        swatch("#14cfa6", "Teal Primary", "Callouts, highlights, key messaging"),
        swatch("#a1d7c6", "Teal Light", "Decorative watermark text only", "#172c3a"),
        swatch("#3a6a9c", "Blue Secondary", "Links, secondary accents, charts"),
        swatch("#7da5ce", "Blue Light", "Chart elements, data visualization", "#172c3a"),
        swatch("#ebe96a", "Yellow", "Sparingly, for emphasis highlights", "#2c3641"),
    ]

    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Color Palette</h2>
    <p class="guideline-body">Every color in the Return Stacked system serves a specific purpose. Consistent usage across all materials strengthens brand recognition and ensures visual harmony.</p>

    <h3 class="guideline-subheading">Text &amp; Backgrounds</h3>
    <div class="swatch-grid">
        {"".join(primary_swatches)}
    </div>

    <h3 class="guideline-subheading" style="margin-top:24pt;">Accent Colors</h3>
    <div class="swatch-grid">
        {"".join(accent_swatches)}
    </div>

    <div class="rule-box">
        <div class="rule-box-heading">Usage Rules</div>
        <ul class="rule-list">
            <li><strong>Teal Primary (#14CFA6)</strong> is the signature accent. Use it for callout text, key insights, the cover topic name, and page header series titles.</li>
            <li><strong>Cover Dark (#172C3A)</strong> is reserved for the cover banner background and white-on-dark panels. Do not use it for body text.</li>
            <li><strong>Text Primary (#2C3641)</strong> is used for all body text, headings, table headers, and footer URLs. Never use pure black (#000000) for text.</li>
            <li><strong>Yellow (#EBE96A)</strong> should be used sparingly and only as a highlight accent, never for large areas or text.</li>
        </ul>
    </div>
</div>'''


# ── Typography section ───────────────────────────────────────────────────────

def type_specimen(label, size_pt, weight, style, color, sample, css_weight, css_style="normal"):
    """Build a single typography specimen row.

    Large sizes are capped at 24pt for display so they don't blow out the page.
    The actual size is always shown in the spec label.
    """
    display_size = min(size_pt, 18)
    return f'''<div class="type-specimen">
    <div class="type-meta">
        <span class="type-label">{h.escape(label)}</span>
        <span class="type-spec">{size_pt}pt &middot; {weight} &middot; {h.escape(color)}</span>
    </div>
    <div class="type-sample" style="font-size:{display_size}pt; font-weight:{css_weight}; font-style:{css_style}; color:{color};">
        {h.escape(sample)}
    </div>
</div>'''


def build_typography_section_page1():
    """Build the first typography page: font showcase + cover type scale."""
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Typography</h2>
    <p class="guideline-body">DM Sans is the exclusive typeface across all Return Stacked materials. No other fonts should appear in any branded content, including charts, tables, and footnotes.</p>

    <div class="font-showcase">
        <div class="font-showcase-name">DM Sans</div>
        <div class="font-showcase-weights">
            <span style="font-weight:100;">Thin 100</span>
            <span style="font-weight:200;">ExtraLight 200</span>
            <span style="font-weight:300;">Light 300</span>
            <span style="font-weight:400;">Regular 400</span>
            <span style="font-weight:500;">Medium 500</span>
            <span style="font-weight:600;">SemiBold 600</span>
            <span style="font-weight:700;">Bold 700</span>
            <span style="font-weight:800;">ExtraBold 800</span>
        </div>
        <div class="font-showcase-sample" style="font-size:22pt; font-weight:300; line-height:1.3; color:#2c3641;">
            ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>
            abcdefghijklmnopqrstuvwxyz<br>
            0123456789 &amp; @ # $ % !?
        </div>
    </div>

    <h3 class="guideline-subheading">Cover Page Type Scale</h3>
    <div class="type-scale">
        {type_specimen("Watermark", 85, "Bold", "normal", "#a1d7c6", "Advisor's Guide", 700)}
        {type_specimen("Main Title", 42, "Medium", "normal", "#ffffff", "The Advisor's Guide to Client Conversations", 500)}
        {type_specimen("Topic Name", 48, "Bold", "normal", "#14cfa6", "Managed Futures", 700)}
        {type_specimen("Connector", 38, "Regular", "normal", "#ffffff", "about", 400)}
        {type_specimen("Intro Heading", 22, "Bold", "normal", "#2c3641", "Why This Conversation Matters", 700)}
        {type_specimen("Intro Paragraph", 13, "Medium", "normal", "#2c3641", "When both stocks and bonds experience extended drawdowns...", 500)}
    </div>
</div>'''


def build_typography_section_page2():
    """Build the second typography page: interior type scale."""
    rsq = "\u2019"  # right single quote
    ldq = "\u201c"   # left double quote
    rdq = "\u201d"   # right double quote
    subsection_sample = f"{ldq}I don{rsq}t understand how this works.{rdq}"
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Typography <span style="font-size:14pt; font-weight:400; color:var(--text-secondary);">(continued)</span></h2>

    <h3 class="guideline-subheading">Interior Page Type Scale</h3>
    <div class="type-scale">
        {type_specimen("Page Header (Series)", 12, "Bold", "normal", "#14cfa6", "The Advisor's Guide to Client Conversations", 700)}
        {type_specimen("Page Header (Topic)", 12, "Medium", "normal", "#2c3641", "about Managed Futures", 500)}
        {type_specimen("Section Heading", 13, "Bold", "normal", "#2c3641", "What Are Managed Futures?", 700)}
        {type_specimen("Subsection Heading", 13, "Bold", "normal", "#2c3641", subsection_sample, 700)}
        {type_specimen("Body Text", 10, "Regular", "normal", "#2c3641", "Managed futures are systematic strategies that trade across global futures markets, including equities, bonds, currencies, and commodities.", 400)}
        {type_specimen("Callout / Key Insight", 13, "Bold Italic", "italic", "#14cfa6", "It doesn't look into the future, it reacts to the recent past to find useful trends.", 700, "italic")}
        {type_specimen("Dark Panel Text", 13, "Bold", "normal", "#ffffff", "Long and Short Flexibility", 700)}
        {type_specimen("Table Header", 9, "Bold", "normal", "#ffffff", "STRATEGY  |  ANN. RETURN  |  VOLATILITY", 700)}
        {type_specimen("Table Body", 9, "Regular", "normal", "#2c3641", "Managed Futures    8.2%    12.1%", 400)}
        {type_specimen("Footer URL", 9, "Bold", "normal", "#2c3641", "www.returnstacked.com", 700)}
        {type_specimen("Disclaimer Text", 8, "Regular", "normal", "#2c3641", "This material is for informational purposes only...", 400)}
        {type_specimen("Chart Labels", 8, "Regular", "normal", "#625c6d", "Jan 2020    Feb 2020    Mar 2020", 400)}
    </div>
</div>'''


# ── Layout section ───────────────────────────────────────────────────────────

def build_layout_section():
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Page Layout</h2>
    <p class="guideline-body">All Advisor Guides use US Letter format (8.5 × 11 inches) with consistent margins and content zones across every page.</p>

    <div class="layout-specs-grid">
        <div class="layout-spec-card">
            <div class="layout-spec-title">Page Dimensions</div>
            <div class="layout-spec-detail">8.5 × 11 in (612 × 792 pt)</div>
        </div>
        <div class="layout-spec-card">
            <div class="layout-spec-title">Margins</div>
            <div class="layout-spec-detail">Top: 36pt &middot; Bottom: 22pt &middot; Left/Right: 28pt</div>
        </div>
        <div class="layout-spec-card">
            <div class="layout-spec-title">Content Width</div>
            <div class="layout-spec-detail">556pt (7.72 in)</div>
        </div>
        <div class="layout-spec-card">
            <div class="layout-spec-title">Cover Banner Height</div>
            <div class="layout-spec-detail">340pt on #172C3A dark navy</div>
        </div>
    </div>

    <h3 class="guideline-subheading">Cover Page Structure</h3>
    <div class="layout-diagram">
        <div class="diagram-cover">
            <div class="diagram-banner">
                <div class="diagram-label-light">Dark Banner #172C3A &mdash; 340pt</div>
                <div class="diagram-watermark-hint">Watermark: 85pt Bold, #A1D7C6 at 15% opacity</div>
                <div class="diagram-title-hint">Title Block: left-aligned, with 6px black drop shadow offset bottom-right</div>
                <div class="diagram-logo-hint">Logo: bottom-right, 30pt height</div>
            </div>
            <div class="diagram-intro">
                <div class="diagram-label-dark">Intro Zone &mdash; padding: 24pt 28pt</div>
                <div class="diagram-intro-hint">Heading (22pt Bold) + Text (13pt Medium) + optional Highlight (13pt Bold Teal)</div>
            </div>
        </div>
    </div>

    <h3 class="guideline-subheading">Interior Page Structure</h3>
    <div class="layout-diagram">
        <div class="diagram-interior">
            <div class="diagram-header-zone">
                <div class="diagram-label-dark">Header &mdash; y: 25pt</div>
                <div class="diagram-header-hint">Line 1: Series title (12pt Bold Teal) &middot; Line 2: "about [Topic]" (12pt Medium)</div>
            </div>
            <div class="diagram-content-zone">
                <div class="diagram-label-dark">Content Zone &mdash; y: 65pt to ~750pt</div>
                <div class="diagram-content-hint">All body content flows here: headings, text, callouts, panels, tables, images</div>
            </div>
            <div class="diagram-footer-zone">
                <div class="diagram-label-dark">Footer &mdash; bottom: 10pt</div>
                <div class="diagram-footer-hint">Right-aligned URL (9pt Bold)</div>
            </div>
        </div>
    </div>


</div>'''


# ── Component Showcase ───────────────────────────────────────────────────────

def build_components_section_page1():
    """Components page 1: headings, callout, dark panel."""
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Component Library</h2>
    <p class="guideline-body">These are the reusable building blocks that make up every Advisor Guide. Each component has strict styling rules to maintain consistency.</p>

    <h3 class="guideline-subheading">Section Heading (with Teal Accent)</h3>
    <p class="guideline-caption">Major section headings display a 6pt × 14pt teal rectangle on the left, vertically centered. 13pt Bold, #2C3641. This accent distinguishes top-level sections from subsections.</p>
    <div class="component-preview">
        <div style="font-size:13pt; font-weight:700; color:#2c3641; line-height:1.2; padding-left:14pt; position:relative;">
            <span style="position:absolute; left:0; top:50%; transform:translateY(-50%); width:6pt; height:14pt; background:#14cfa6; display:block;"></span>
            What Are Managed Futures?
        </div>
    </div>

    <h3 class="guideline-subheading">Subsection Heading (no accent)</h3>
    <p class="guideline-caption">Subsection headings are plain bold text without any accent decoration. 13pt Bold, #2C3641. Used for Q&amp;A items, sub-topics, and supporting sections.</p>
    <div class="component-preview">
        <div style="font-size:13pt; font-weight:700; color:#2c3641; line-height:1.2;">
            "I don't understand how this works."
        </div>
    </div>

    <h3 class="guideline-subheading">Teal Callout</h3>
    <p class="guideline-caption">Used for key insights and important takeaways. Always DM Sans Bold Italic, 13pt, teal. 3pt left border.</p>
    <div class="component-preview">
        <div class="callout-teal">It doesn't look into the future, it reacts to the recent past to find useful trends.</div>
    </div>

    <h3 class="guideline-subheading">White-on-Dark Panel</h3>
    <p class="guideline-caption">Used for important concepts that need visual emphasis. Background: #172C3A. Heading: 13pt Bold white. Body: 10pt Regular white.</p>
    <div class="component-preview">
        <div class="dark-panel">
            <div class="dark-panel-heading">Long and Short Flexibility</div>
            <p class="dark-panel-body">Unlike most traditional strategies, managed futures can profit from falling markets just as easily as rising ones. This gives them a structural advantage during periods of market stress.</p>
        </div>
    </div>
</div>'''


def build_components_section_page2():
    """Components page 2: data table, gray section, source note."""
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Component Library <span style="font-size:14pt; font-weight:400; color:var(--text-secondary);">(continued)</span></h2>

    <h3 class="guideline-subheading">Data Table</h3>
    <p class="guideline-caption">Header row: #2C3641 background, white Bold 9pt text. Body: 9pt Regular, alternating row shading with #F0F1F1. Borders: 0.5pt #BFBFBF.</p>
    <div class="component-preview">
        <div class="data-table-wrapper">
            <div class="data-table-caption">Figure 1. Correlation Matrix</div>
            <table class="data-table">
                <thead><tr><th>Correlations</th><th>Equities</th><th>Bonds</th><th>Managed Futures</th></tr></thead>
                <tbody>
                    <tr><td>Equities</td><td>1.00</td><td>-0.03</td><td>0.00</td></tr>
                    <tr><td>Bonds</td><td>-0.03</td><td>1.00</td><td>-0.04</td></tr>
                    <tr><td>Managed Futures</td><td>0.00</td><td>-0.04</td><td>1.00</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <h3 class="guideline-subheading">Gray Section Block</h3>
    <p class="guideline-caption">Background: #F0F1F1. Padding: 16pt. Border radius: 2pt. Contains any child components.</p>
    <div class="component-preview">
        <div class="gray-section" style="padding:16pt;">
            <p class="body-text">This content sits inside a gray section block, used when content needs a subtle visual container to differentiate it from surrounding material.</p>
        </div>
    </div>

    <h3 class="guideline-subheading">Source Note</h3>
    <p class="guideline-caption">7.5pt Regular Italic, #625C6D. Used below charts and tables.</p>
    <div class="component-preview">
        <div class="source-note">Source: CSI Data, Bloomberg and ReSolve Asset Management. Data reflects full history available for the underlying indexes.</div>
    </div>
</div>'''


# ── Logo Families ────────────────────────────────────────────────────────────

def build_logo_section():
    logo_cards = []
    for family_key, info in brand_config.LOGO_FAMILIES.items():
        black_file = info.get("black", "")
        white_file = info.get("white", "")

        black_path = f"{LOGOS_REL}/{family_key}/{black_file}" if black_file else ""
        white_path = f"{LOGOS_REL}/{family_key}/{white_file}" if white_file else ""

        black_img = f'<img src="{black_path}" alt="{h.escape(info["name"])} Black">' if black_file else '<span class="logo-na">N/A</span>'
        white_img = f'<img src="{white_path}" alt="{h.escape(info["name"])} White">' if white_file else '<span class="logo-na">N/A</span>'

        logo_cards.append(f'''<div class="logo-card">
    <div class="logo-card-name">{h.escape(info["name"])}</div>
    <div class="logo-card-key">{family_key}</div>
    <div class="logo-variants">
        <div class="logo-variant-light">
            {black_img}
        </div>
        <div class="logo-variant-dark">
            {white_img}
        </div>
    </div>
    <div class="logo-card-footer">Footer URL: {h.escape(info["footer_url"])}</div>
</div>''')

    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Logo Families</h2>
    <p class="guideline-body">Return Stacked operates under multiple business lines, each with its own logo. The correct logo must be selected based on the material being produced. Every logo has a black (for light backgrounds) and white (for dark backgrounds) variant.</p>

    <div class="logo-grid">
        {"".join(logo_cards)}
    </div>

    <div class="rule-box">
        <div class="rule-box-heading">Logo Usage Rules</div>
        <ul class="rule-list">
            <li>Cover pages always use the <strong>white variant</strong> on the dark banner, positioned bottom-right at 30pt height.</li>
            <li>The footer URL is determined by the logo family: ETF materials use returnstackedetfs.com, all others use returnstacked.com.</li>
            <li>Never stretch, rotate, recolor, or add effects to logos.</li>
            <li>Maintain clear space around the logo equal to at least the height of the icon mark.</li>
        </ul>
    </div>
</div>'''


# ── Document Structure ───────────────────────────────────────────────────────

def build_document_structure_page1():
    """Document Structure page 1: page sequence + cover title pattern."""
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Document Structure</h2>
    <p class="guideline-body">Every Advisor Guide follows the same page sequence. This ensures a consistent reading experience across all topics.</p>

    <div class="structure-flow">
        <div class="structure-step">
            <div class="structure-step-num">1</div>
            <div class="structure-step-content">
                <div class="structure-step-title">Cover Page</div>
                <div class="structure-step-desc">Dark banner with title, topic in teal, logo. Below: "Why This Conversation Matters" intro with optional highlight.</div>
            </div>
        </div>
        <div class="structure-connector"></div>
        <div class="structure-step">
            <div class="structure-step-num">2</div>
            <div class="structure-step-content">
                <div class="structure-step-title">Content Pages</div>
                <div class="structure-step-desc">Running header + footer on every page. Body content uses headings, text, callouts, panels, tables, and charts as needed.</div>
            </div>
        </div>
        <div class="structure-connector"></div>
        <div class="structure-step">
            <div class="structure-step-num">3</div>
            <div class="structure-step-content">
                <div class="structure-step-title">Disclosures Page</div>
                <div class="structure-step-desc">Legal text in 8pt, copyright line with current year, optional glossary of terms. Always the final page.</div>
            </div>
        </div>
    </div>

    <h3 class="guideline-subheading">Cover Title Pattern</h3>
    <p class="guideline-body">The title always follows this exact structure:</p>
    <div class="title-pattern-demo">
        <div class="tpd-line1">The Advisor's Guide to</div>
        <div class="tpd-line2">Client Conversations</div>
        <div class="tpd-line3">about</div>
        <div class="tpd-line4">[Topic Name]</div>
    </div>
    <p class="guideline-caption" style="margin-top:8pt;">The topic name is always rendered in Teal Primary (#14CFA6) in Bold 48pt. The word "about" appears in Regular 38pt white.</p>

    <h3 class="guideline-subheading">Content Flow &amp; Page Breaks</h3>
    <p class="guideline-body">Content flows continuously across interior pages. The generator automatically splits content at natural page boundaries with orphan prevention: section headings and subsection headings are never stranded alone at the bottom of a page. If a heading would land at the bottom without at least its first body paragraph, both are moved to the next page together. This applies to heading\u2192body, heading\u2192subsection, and heading\u2192subsection\u2192body chains.</p>
</div>'''


def build_document_structure_page2():
    """Document Structure page 2: cover title drop shadow details."""
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Document Structure <span style="font-size:14pt; font-weight:400; color:var(--text-secondary);">(continued)</span></h2>

    <h3 class="guideline-subheading">Cover Title Drop Shadow</h3>
    <p class="guideline-body">All cover title text has a hard drop shadow offset to the bottom-right. This is implemented as a duplicate HTML layer (not CSS text-shadow, which is invisible on dark backgrounds). The shadow layer is pure black (#000000) at full opacity, offset 6px right and 6px down, rendered behind the foreground text via z-index stacking.</p>
    <div class="rule-box">
        <div class="rule-box-heading">Shadow Implementation</div>
        <ul class="rule-list">
            <li><strong>Technique:</strong> Duplicate text elements in an absolutely-positioned container behind the foreground text. CSS text-shadow cannot produce visible shadows on the dark navy (#172C3A) background.</li>
            <li><strong>Offset:</strong> 6px right, 6px down (top: 6px; left: 6px)</li>
            <li><strong>Color:</strong> #000000 (pure black), full opacity</li>
            <li><strong>Z-index:</strong> Shadow container at z-index: 0; foreground text at z-index: 2. Shadow children must reset to position: static to avoid inheriting the foreground z-index rules.</li>
        </ul>
    </div>

    <h3 class="guideline-subheading">Spacing Rules</h3>
    <div class="rule-box">
        <div class="rule-box-heading">Element Spacing Reference</div>
        <ul class="rule-list">
            <li>Section headings: 10pt space before (0pt if first on page), 6pt after. Includes 14pt left padding for teal accent bar.</li>
            <li>Subsection headings: 8pt space before, 4pt after. No left padding, no accent decoration.</li>
            <li>Body paragraphs: 8pt space after</li>
            <li>Callouts and panels: 12pt space before and after</li>
            <li>Line heights: Body 1.5, Headings 1.2, Callouts 1.35, Disclaimers 1.25</li>
        </ul>
    </div>
</div>'''


# ── Cover Backdrops ─────────────────────────────────────────────────────────

def build_backdrops_section():
    """Cover Backdrops page: showcase the two available backdrop images."""
    return f'''
<div class="section-block">
    <h2 class="guideline-heading">Cover Backdrops</h2>
    <p class="guideline-body">Two backdrop images are available for the cover banner. The <strong>Blue</strong> variant is the default. Both are available in SVG (vector) and PNG (raster) formats in <code>../Brand_elements/Background_images/</code>.</p>

    <h3 class="guideline-subheading">Blue (Default)</h3>
    <div class="backdrop-preview">
        <img src="{BACKDROP_BLUE_REL}" alt="RS Background Blue" style="width:100%; height:auto; border-radius:3pt;">
    </div>
    <p class="guideline-caption" style="margin-top:6pt;">File: RS-Background-Blue.png / .svg &mdash; Used as the standard cover banner background for all Advisor Guides.</p>

    <h3 class="guideline-subheading">Green (Alternate)</h3>
    <div class="backdrop-preview">
        <img src="{BACKDROP_GREEN_REL}" alt="RS Background Green" style="width:100%; height:auto; border-radius:3pt;">
    </div>
    <p class="guideline-caption" style="margin-top:6pt;">File: RS-Background-Green.png / .svg &mdash; Available as an alternate when visual variety is needed.</p>

    <div class="rule-box" style="margin-top:16pt;">
        <div class="rule-box-heading">Usage Notes</div>
        <ul class="rule-list">
            <li><strong>Default:</strong> Blue is the standard backdrop. Use it unless there is a specific reason to vary.</li>
            <li><strong>Translucent overlay:</strong> A translucent overlay (<code>Translucent.svg</code>) is automatically layered on top of the backdrop in generated guides to soften the image.</li>
            <li><strong>Format:</strong> The generator uses PNG for browser compatibility. SVG originals are provided for design work.</li>
            <li><strong>Configuration:</strong> The default backdrop is set in <code>generator/brand_config.py</code> via the <code>BACKDROP_IMAGE</code> constant.</li>
        </ul>
    </div>
</div>'''


# ── CSS for the guidelines document ──────────────────────────────────────────

def build_guidelines_css():
    return f'''
{build_font_faces()}

:root {{
    --text-primary: #2c3641;
    --text-secondary: #625c6d;
    --cover-dark: #172c3a;
    --section-gray: #f0f1f1;
    --white: #ffffff;
    --border-gray: #bfbfbf;
    --teal-primary: #14cfa6;
    --teal-light: #a1d7c6;
    --blue-secondary: #3a6a9c;
    --blue-light: #7da5ce;
    --yellow: #ebe96a;
    --font-family: 'DM Sans', sans-serif;
}}

@page {{ size: letter; margin: 0; }}

@media print {{
    body {{ margin: 0; padding: 0; background: white; }}
    .page {{
        page-break-after: always;
        page-break-inside: avoid;
        box-shadow: none;
        margin: 0;
        height: 11in;
        max-height: 11in;
        overflow: hidden;
    }}
    .page:last-child {{ page-break-after: auto; }}
    .screen-only {{ display: none; }}
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html {{ font-size: 10pt; }}

body {{
    font-family: var(--font-family);
    font-weight: 400;
    color: var(--text-primary);
    background: white;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}}

/* ── Page container ── */

.page {{
    width: 8.5in;
    height: 11in;
    background: var(--white);
    position: relative;
    margin: 0 auto;
    overflow: hidden;
}}

/* Screen-only: gray background and shadows for visual separation between pages */
@media screen {{
    body {{ background: #e0e0e0; }}
    .page {{ margin: 20px auto; box-shadow: 0 2px 10px rgba(0,0,0,0.15); }}
}}

/* ── Guidelines Cover ── */

.guidelines-cover {{
    height: 11in;
    display: flex;
    flex-direction: column;
}}

.guidelines-cover-banner {{
    background: var(--cover-dark);
    background-image: url('{BACKDROP_BLUE_REL}');
    background-size: cover;
    background-position: center;
    padding: 60pt 40pt 50pt;
    flex-shrink: 0;
}}

.guidelines-cover-eyebrow {{
    font-size: 11pt;
    font-weight: 700;
    color: var(--teal-primary);
    letter-spacing: 3pt;
    text-transform: uppercase;
    margin-bottom: 12pt;
}}

.guidelines-cover-title {{
    font-size: 48pt;
    font-weight: 700;
    color: var(--white);
    line-height: 1.05;
    margin-bottom: 6pt;
}}

.guidelines-cover-title-line2 {{
    font-size: 48pt;
    font-weight: 700;
    color: var(--white);
    line-height: 1.05;
    margin-bottom: 6pt;
}}

.guidelines-cover-subtitle {{
    font-size: 22pt;
    font-weight: 300;
    color: var(--teal-light);
    line-height: 1.3;
}}

.guidelines-cover-body {{
    padding: 32pt 40pt;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

.guidelines-cover-intro {{
    font-size: 13pt;
    font-weight: 400;
    color: var(--text-primary);
    line-height: 1.6;
    max-width: 480pt;
}}

.guidelines-cover-meta {{
    font-size: 9pt;
    font-weight: 400;
    color: var(--text-secondary);
    border-top: 1pt solid var(--border-gray);
    padding-top: 12pt;
}}

/* ── Interior Guidelines Pages ── */

.guidelines-interior {{
    height: 11in;
    display: flex;
    flex-direction: column;
    padding: 36pt 40pt 0 40pt;
}}

.guidelines-interior-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 2pt solid var(--teal-primary);
    padding-bottom: 8pt;
    margin-bottom: 24pt;
    flex-shrink: 0;
}}

.guidelines-interior-content {{
    flex: 1;
    overflow: hidden;
}}

.guidelines-interior-title {{
    font-size: 10pt;
    font-weight: 700;
    color: var(--teal-primary);
    letter-spacing: 2pt;
    text-transform: uppercase;
}}

.guidelines-interior-section {{
    font-size: 10pt;
    font-weight: 500;
    color: var(--text-secondary);
}}

.guidelines-footer {{
    flex-shrink: 0;
    padding: 10pt 0 14pt;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: var(--text-secondary);
}}

/* ── Section Blocks ── */

.section-block {{
    margin-bottom: 0;
}}

.guideline-heading {{
    font-size: 22pt;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
    margin-bottom: 10pt;
    padding-bottom: 6pt;
    border-bottom: 1pt solid var(--section-gray);
}}

.guideline-subheading {{
    font-size: 14pt;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
    margin-top: 20pt;
    margin-bottom: 8pt;
}}

.guideline-body {{
    font-size: 10pt;
    font-weight: 400;
    color: var(--text-primary);
    line-height: 1.6;
    margin-bottom: 10pt;
}}

.guideline-caption {{
    font-size: 9pt;
    font-weight: 400;
    color: var(--text-secondary);
    line-height: 1.4;
    margin-bottom: 8pt;
}}

/* ── Color Swatches ── */

.swatch-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12pt;
    margin-top: 8pt;
}}

.swatch-card {{
    border: 0.5pt solid var(--border-gray);
    border-radius: 3pt;
    overflow: hidden;
}}

.swatch-block {{
    height: 44pt;
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    padding: 6pt 8pt;
}}

.swatch-hex {{
    font-size: 9pt;
    font-weight: 700;
    font-family: var(--font-family);
    opacity: 0.9;
}}

.swatch-label {{
    font-size: 9pt;
    font-weight: 700;
    color: var(--text-primary);
    padding: 6pt 8pt 2pt;
}}

.swatch-usage {{
    font-size: 8pt;
    font-weight: 400;
    color: var(--text-secondary);
    padding: 0 8pt 6pt;
    line-height: 1.3;
}}

/* ── Typography Specimens ── */

.font-showcase {{
    background: var(--section-gray);
    padding: 16pt;
    border-radius: 3pt;
    margin: 8pt 0;
}}

.font-showcase-name {{
    font-size: 36pt;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 10pt;
}}

.font-showcase-weights {{
    display: flex;
    flex-wrap: wrap;
    gap: 6pt 16pt;
    font-size: 9pt;
    color: var(--text-secondary);
    margin-bottom: 14pt;
}}

.font-showcase-sample {{
    color: var(--text-primary);
}}

.type-scale {{
    margin: 8pt 0;
}}

.type-specimen {{
    padding: 8pt 0;
    border-bottom: 0.5pt solid var(--section-gray);
}}

.type-specimen:last-child {{
    border-bottom: none;
}}

.type-meta {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4pt;
}}

.type-label {{
    font-size: 9pt;
    font-weight: 700;
    color: var(--text-primary);
}}

.type-spec {{
    font-size: 8pt;
    font-weight: 400;
    color: var(--text-secondary);
}}

.type-sample {{
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

/* ── Rule Boxes ── */

.rule-box {{
    background: var(--section-gray);
    border-left: 3pt solid var(--teal-primary);
    padding: 14pt 16pt;
    margin-top: 16pt;
    border-radius: 0 3pt 3pt 0;
}}

.rule-box-heading {{
    font-size: 11pt;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 8pt;
}}

.rule-list {{
    font-size: 9pt;
    font-weight: 400;
    color: var(--text-primary);
    line-height: 1.5;
    padding-left: 16pt;
}}

.rule-list li {{
    margin-bottom: 4pt;
}}

.rule-list li strong {{
    font-weight: 700;
}}

/* ── Layout Specs Grid ── */

.layout-specs-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10pt;
    margin: 10pt 0;
}}

.layout-spec-card {{
    border: 0.5pt solid var(--border-gray);
    padding: 12pt;
    border-radius: 3pt;
}}

.layout-spec-title {{
    font-size: 9pt;
    font-weight: 700;
    color: var(--teal-primary);
    margin-bottom: 4pt;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
}}

.layout-spec-detail {{
    font-size: 10pt;
    font-weight: 400;
    color: var(--text-primary);
}}

/* ── Layout Diagrams ── */

.layout-diagram {{
    margin: 12pt 0;
}}

.diagram-cover, .diagram-interior {{
    border: 1pt solid var(--border-gray);
    border-radius: 3pt;
    overflow: hidden;
    max-width: 320pt;
}}

.diagram-banner {{
    background: var(--cover-dark);
    padding: 16pt;
    min-height: 110pt;
}}

.diagram-intro {{
    padding: 14pt 16pt;
    background: var(--white);
    min-height: 60pt;
}}

.diagram-label-light {{
    font-size: 8pt;
    font-weight: 700;
    color: var(--teal-light);
    margin-bottom: 6pt;
}}

.diagram-label-dark {{
    font-size: 8pt;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4pt;
}}

.diagram-watermark-hint, .diagram-title-hint, .diagram-logo-hint,
.diagram-intro-hint, .diagram-header-hint, .diagram-content-hint, .diagram-footer-hint {{
    font-size: 7pt;
    font-weight: 400;
    color: var(--text-secondary);
    line-height: 1.4;
    margin-top: 3pt;
}}

.diagram-watermark-hint {{ color: rgba(161,215,198,0.6); }}

.diagram-header-zone {{
    background: var(--white);
    padding: 10pt 14pt;
    border-bottom: 0.5pt solid var(--section-gray);
}}

.diagram-content-zone {{
    background: var(--white);
    padding: 14pt;
    min-height: 70pt;
}}

.diagram-footer-zone {{
    background: var(--white);
    padding: 8pt 14pt;
    border-top: 0.5pt solid var(--section-gray);
}}

/* ── Component Previews ── */

.component-preview {{
    border: 0.5pt solid var(--border-gray);
    padding: 16pt;
    border-radius: 3pt;
    margin: 8pt 0 16pt;
    background: var(--white);
}}

/* Re-use actual component styles inside previews */
.callout-teal {{
    font-size: 13pt;
    font-weight: 700;
    font-style: italic;
    color: var(--teal-primary);
    line-height: 1.35;
    padding-left: 12pt;
    border-left: 3pt solid var(--teal-primary);
}}

.dark-panel {{
    background-color: var(--cover-dark);
    padding: 16pt;
    border-radius: 2pt;
}}

.dark-panel-heading {{
    font-size: 13pt;
    font-weight: 700;
    color: var(--white);
    margin-bottom: 8pt;
    line-height: 1.2;
}}

.dark-panel-body {{
    font-size: 10pt;
    font-weight: 400;
    color: var(--white);
    line-height: 1.5;
}}

.gray-section {{
    background-color: var(--section-gray);
    border-radius: 2pt;
}}

.body-text {{
    font-size: 10pt;
    font-weight: 400;
    color: var(--text-primary);
    line-height: 1.5;
}}

.source-note {{
    font-size: 7.5pt;
    font-weight: 400;
    font-style: italic;
    color: var(--text-secondary);
    line-height: 1.25;
}}

.data-table-wrapper {{ margin: 0; }}
.data-table-caption {{
    font-size: 10pt;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 6pt;
}}
.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
}}
.data-table th {{
    background-color: var(--text-primary);
    color: var(--white);
    font-weight: 700;
    text-align: left;
    padding: 6pt 8pt;
    border: 0.5pt solid var(--border-gray);
}}
.data-table td {{
    padding: 5pt 8pt;
    border: 0.5pt solid var(--border-gray);
    font-weight: 400;
    color: var(--text-primary);
}}
.data-table tr:nth-child(even) td {{
    background-color: var(--section-gray);
}}

/* ── Logo Section ── */

.logo-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14pt;
    margin: 12pt 0;
}}

.logo-card {{
    border: 0.5pt solid var(--border-gray);
    border-radius: 3pt;
    overflow: hidden;
}}

.logo-card-name {{
    font-size: 10pt;
    font-weight: 700;
    color: var(--text-primary);
    padding: 10pt 12pt 4pt;
}}

.logo-card-key {{
    font-size: 8pt;
    font-weight: 400;
    color: var(--text-secondary);
    padding: 0 12pt 8pt;
    font-family: var(--font-family);
}}

.logo-variants {{
    display: flex;
}}

.logo-variant-light {{
    flex: 1;
    background: #f8f8f8;
    padding: 14pt 12pt;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 50pt;
}}

.logo-variant-dark {{
    flex: 1;
    background: var(--cover-dark);
    padding: 14pt 12pt;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 50pt;
}}

.logo-variant-light img, .logo-variant-dark img {{
    max-height: 24pt;
    max-width: 100%;
    width: auto;
}}

.logo-card-footer {{
    font-size: 8pt;
    font-weight: 400;
    color: var(--text-secondary);
    padding: 6pt 12pt;
    border-top: 0.5pt solid var(--section-gray);
}}

.logo-na {{
    font-size: 8pt;
    color: var(--text-secondary);
}}

/* ── Document Structure ── */

.structure-flow {{
    margin: 14pt 0;
    padding-left: 20pt;
}}

.structure-step {{
    display: flex;
    align-items: flex-start;
    gap: 12pt;
}}

.structure-step-num {{
    width: 28pt;
    height: 28pt;
    background: var(--teal-primary);
    color: var(--white);
    font-size: 13pt;
    font-weight: 700;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

.structure-step-content {{
    padding-top: 2pt;
}}

.structure-step-title {{
    font-size: 11pt;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 2pt;
}}

.structure-step-desc {{
    font-size: 9pt;
    font-weight: 400;
    color: var(--text-secondary);
    line-height: 1.4;
}}

.structure-connector {{
    width: 2pt;
    height: 16pt;
    background: var(--teal-primary);
    opacity: 0.3;
    margin-left: 13pt;
}}

/* ── Title Pattern Demo ── */

.title-pattern-demo {{
    background: var(--cover-dark);
    padding: 20pt 24pt;
    border-radius: 3pt;
    margin: 8pt 0;
}}

.tpd-line1, .tpd-line2 {{
    font-size: 20pt;
    font-weight: 500;
    color: var(--white);
    line-height: 1.15;
}}

.tpd-line3 {{
    font-size: 18pt;
    font-weight: 400;
    color: var(--white);
    line-height: 1.15;
}}

.tpd-line4 {{
    font-size: 19pt;
    font-weight: 700;
    color: var(--teal-primary);
    line-height: 1.15;
    margin-top: 2pt;
}}

/* ── Screen-only hint ── */

.edit-hint {{
    display: none;
}}

@media screen {{
    .edit-hint {{
        display: block;
        position: fixed;
        top: 10px;
        right: 10px;
        background: var(--teal-primary);
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 11pt;
        font-weight: 500;
        z-index: 9999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
}}
'''


# ── Page builder helpers ─────────────────────────────────────────────────────

def guidelines_page(section_label, page_num, total_pages, content_html):
    """Wrap content in a guidelines interior page with bounded content area."""
    return f'''<div class="page guidelines-interior">
    <div class="guidelines-interior-header">
        <div class="guidelines-interior-title">Return Stacked Brand Guidelines</div>
        <div class="guidelines-interior-section">{h.escape(section_label)}</div>
    </div>
    <div class="guidelines-interior-content">
    {content_html}
    </div>
    <div class="guidelines-footer">
        <span>© Return Stacked® Portfolio Solutions, {date.today().year}</span>
        <span>{page_num} / {total_pages}</span>
    </div>
</div>'''


# ── Assemble ─────────────────────────────────────────────────────────────────

def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Resolve a logo for the cover
    logo_family = "RS_Portfolio_Solutions_logos"
    logo_info = brand_config.LOGO_FAMILIES[logo_family]
    white_logo = f"{LOGOS_REL}/{logo_family}/{logo_info['white']}"

    year = date.today().year

    # ── Cover page ──
    cover_html = f'''<div class="page guidelines-cover">
    <div class="guidelines-cover-banner">
        <div class="guidelines-cover-eyebrow">Brand Guidelines</div>
        <div class="guidelines-cover-title">Return Stacked®</div>
        <div class="guidelines-cover-title-line2">Advisor Guides</div>
        <div class="guidelines-cover-subtitle">Visual Identity &amp; Style Guide</div>
    </div>
    <div class="guidelines-cover-body">
        <div class="guidelines-cover-intro">
            This document codifies the visual identity for all Return Stacked branded materials. It was derived from a systematic analysis of five existing Advisor Guide documents, resolving inconsistencies and establishing a single definitive standard for colors, typography, layout, components, and logo usage across every business line.
        </div>
        <div class="guidelines-cover-meta">
            <img src="{white_logo}" alt="Return Stacked Portfolio Solutions" style="height:18pt; margin-bottom:8pt; filter: brightness(0);"><br>
            Version 1.0 &middot; {date.today().strftime("%B %Y")} &middot; Return Stacked Portfolio Solutions
        </div>
    </div>
</div>'''

    total = 11  # cover + 10 interior pages

    # ── Content pages ──
    page2  = guidelines_page("Color Palette",        2,  total, build_color_section())
    page3  = guidelines_page("Typography",           3,  total, build_typography_section_page1())
    page4  = guidelines_page("Typography",           4,  total, build_typography_section_page2())
    page5  = guidelines_page("Page Layout",          5,  total, build_layout_section())
    page6  = guidelines_page("Components",           6,  total, build_components_section_page1())
    page7  = guidelines_page("Components",           7,  total, build_components_section_page2())
    page8  = guidelines_page("Logo Families",        8,  total, build_logo_section())
    page9  = guidelines_page("Document Structure",   9,  total, build_document_structure_page1())
    page10 = guidelines_page("Document Structure",   10, total, build_document_structure_page2())
    page11 = guidelines_page("Cover Backdrops",      11, total, build_backdrops_section())

    all_pages = [cover_html, page2, page3, page4, page5, page6, page7, page8, page9, page10, page11]

    css = build_guidelines_css()

    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Return Stacked Brand Guidelines</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="edit-hint screen-only">
        Return Stacked Brand Guidelines \u2014 Print \u2192 PDF
    </div>

{"".join(all_pages)}

</body>
</html>'''

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Generated: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    generate()
