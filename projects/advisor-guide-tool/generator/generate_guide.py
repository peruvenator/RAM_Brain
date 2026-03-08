"""
Return Stacked Advisor Guide Generator
=======================================
Generates branded HTML documents from YAML content files.

Usage:
    python generate_guide.py <content.yaml>
    python generate_guide.py content/managed_futures.yaml

Output:
    Advisor_Guide_Output/<Topic>-Advisor-Guide-<Version>.html
"""

import os
import sys
import html as html_mod
import yaml

# Ensure the generator package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator import brand_config
from generator.content_schema import validate_content
from generator.components.cover_page import build_cover_page
from generator.components.content_page import build_interior_page
from generator.components.callout import build_teal_callout, build_dark_panel, build_gray_section
from generator.components.data_table import build_data_table, build_correlation_matrix
from generator.components.disclaimer import build_disclosures


# ── CSS Loader ────────────────────────────────────────────────────────────────

def load_css(output_dir):
    """Load and process the base CSS, resolving font paths.

    Returns the CSS string with font paths relative to the output file.
    """
    css_path = os.path.join(brand_config.TEMPLATES_DIR, "base.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    # Compute relative path from output dir to font dir
    font_rel = os.path.relpath(brand_config.FONT_DIR, output_dir).replace("\\", "/")
    css = css.replace("{{FONT_DIR}}", font_rel)

    # Compute relative path from output dir to backdrop image
    backdrop_path = brand_config.BACKDROP_IMAGE
    backdrop_rel = os.path.relpath(backdrop_path, output_dir).replace("\\", "/")
    css = css.replace("{{BACKDROP_IMG}}", backdrop_rel)

    # Compute relative path from output dir to translucent overlay
    translucent_path = os.path.join(brand_config.BACKDROP_DIR, "Translucent.svg")
    translucent_rel = os.path.relpath(translucent_path, output_dir).replace("\\", "/")
    css = css.replace("{{TRANSLUCENT_IMG}}", translucent_rel)
    return css


# ── Icon SVG Loader ──────────────────────────────────────────────────────────

def load_icon_svg_inline():
    """Load the RS icon SVG and prepare it for inline use in HTML.

    Reads the SVG file and adds styling attributes so it renders as a small
    white icon suitable for dark backgrounds in the footer/cover.

    Returns:
        HTML string with the inline SVG, or a placeholder if not found.
    """
    import re
    svg_content = brand_config.load_icon_svg()
    if svg_content:
        # Strip XML declaration (not valid when inlined in HTML)
        svg_content = re.sub(r'<\?xml[^?]*\?>\s*', '', svg_content)
        # Strip any XML comments (e.g. Adobe Illustrator generator comments)
        svg_content = re.sub(r'<!--.*?-->\s*', '', svg_content, flags=re.DOTALL)
        # Add white fill styling for dark backgrounds and constrain size
        svg_content = svg_content.replace(
            "<svg",
            '<svg style="height:100%;width:100%;fill:white;"',
            1
        )
        return svg_content.strip()
    return '<span style="color:white;font-size:12pt;font-weight:700;">RS</span>'


# ── Helpers ───────────────────────────────────────────────────────────────────

import re as _re


def _is_correlation_matrix(caption):
    """Return True if the caption indicates a correlation matrix table."""
    if not caption:
        return False
    return bool(_re.search(r'correlation\s+matrix', caption, _re.IGNORECASE))


# ── Section Renderers ─────────────────────────────────────────────────────────

def render_section(section):
    """Render a single content section dict to HTML.

    Args:
        section: dict with 'type' key and type-specific fields.

    Returns:
        HTML string.
    """
    sec_type = section.get("type", "")

    if sec_type == "heading":
        return f'<h2 class="section-heading">{html_mod.escape(section["text"])}</h2>'

    elif sec_type == "subsection":
        return f'<h3 class="subsection-heading">{html_mod.escape(section["text"])}</h3>'

    elif sec_type == "body":
        text = section["text"]
        # Support basic markdown-style bold (**text**) and italic (*text*)
        # For full markdown, a library could be used, but this covers common cases
        paragraphs = text.strip().split("\n\n")
        parts = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # Escape HTML first, then apply simple formatting
                escaped = html_mod.escape(para)
                # Bold: **text** → <strong>text</strong>
                import re
                escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
                # Italic: *text* → <em>text</em>
                escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)
                parts.append(f'<p class="body-text">{escaped}</p>')
        return "\n".join(parts)

    elif sec_type == "callout":
        return build_teal_callout(section["text"])

    elif sec_type == "dark_panel":
        return build_dark_panel(
            section["heading"],
            section.get("body", "")
        )

    elif sec_type == "gray_section":
        inner_sections = section.get("sections", [])
        inner_html = "\n".join(render_section(s) for s in inner_sections)
        return build_gray_section(inner_html)

    elif sec_type == "table":
        caption = section.get("caption", "")
        if _is_correlation_matrix(caption):
            return build_correlation_matrix(
                section["headers"],
                section["rows"],
                caption,
            )
        return build_data_table(
            section["headers"],
            section["rows"],
            caption,
        )

    elif sec_type == "chart_image":
        path = section["path"]
        caption = section.get("caption", "")
        caption_html = ""
        if caption:
            caption_html = f'<div class="chart-caption">{html_mod.escape(caption)}</div>'
        return f'''<div class="chart-wrapper">
    <img src="{html_mod.escape(path)}" alt="{html_mod.escape(caption)}">
    {caption_html}
</div>'''

    elif sec_type == "bullet_list":
        items = section.get("items", [])
        li_html = "\n".join(
            f"    <li>{html_mod.escape(str(item))}</li>" for item in items
        )
        return f'<ul class="body-list">\n{li_html}\n</ul>'

    elif sec_type == "source_note":
        return f'<div class="source-note">{html_mod.escape(section.get("text", ""))}</div>'

    elif sec_type == "page_break":
        # Sentinel — handled by the page-splitting logic
        return "<!-- PAGE_BREAK -->"

    else:
        return f'<!-- Unknown section type: {sec_type} -->'


# ── Height Estimator ──────────────────────────────────────────────────────────

# Available content height per interior page (in pt).
# Page = 792pt (11in). Header zone = 60pt top. Footer zone = 32pt bottom.
# We use a 20pt safety margin to absorb height-estimation rounding errors
# (character-width heuristic, font kerning, bold text width variance).
# CSS overflow: hidden on .interior-content hard-clips anything beyond the
# boundary, but this margin keeps visible content comfortably within bounds.
CONTENT_HEIGHT_PT = 792 - 60 - 32 - 20  # = 680pt (700pt available, 20pt safety)

# Content width in pt for text wrapping estimates.
# Page width 612pt (8.5in) minus left/right margins (28pt each) = 556pt
CONTENT_WIDTH_PT = 612 - 28 - 28  # = 556pt


def _estimate_text_lines(text, font_size_pt, available_width_pt):
    """Estimate how many lines a text string will wrap into.

    Uses a simple character-width heuristic based on average character width
    for DM Sans at common sizes.
    """
    if not text:
        return 0
    # Average character width ≈ 0.52 × font_size for DM Sans Regular
    avg_char_width = font_size_pt * 0.52
    chars_per_line = max(1, int(available_width_pt / avg_char_width))
    # Count actual text length (strip HTML tags for estimation)
    import re
    clean = re.sub(r'<[^>]+>', '', text)
    return max(1, -(-len(clean) // chars_per_line))  # Ceiling division


def estimate_section_height(section):
    """Estimate the rendered height (in pt) of a single content section.

    Args:
        section: dict with 'type' key and type-specific fields.

    Returns:
        Estimated height in points.
    """
    sec_type = section.get("type", "")
    w = CONTENT_WIDTH_PT

    if sec_type == "heading":
        # Bold 13pt text + 10pt top margin + 6pt bottom margin
        lines = _estimate_text_lines(section.get("text", ""), 13, w)
        return 10 + (lines * 13 * 1.2) + 6

    elif sec_type == "subsection":
        # Bold 13pt text + 8pt top margin + 4pt bottom margin
        lines = _estimate_text_lines(section.get("text", ""), 13, w - 14)
        return 8 + (lines * 13 * 1.2) + 4

    elif sec_type == "body":
        text = section.get("text", "")
        paragraphs = text.strip().split("\n\n")
        total = 0
        for para in paragraphs:
            para = para.strip()
            if para:
                lines = _estimate_text_lines(para, 10, w)
                total += lines * 10 * 1.5 + 4  # line-height 1.5 + 4pt margin
        return total

    elif sec_type == "callout":
        lines = _estimate_text_lines(section.get("text", ""), 13, w - 15)
        return 6 + (lines * 13 * 1.35) + 6  # margins + line height

    elif sec_type == "dark_panel":
        heading_h = 12 * 1.2 + 12  # heading line + padding
        body = section.get("body", "")
        if body:
            lines = _estimate_text_lines(body, 10, w - 24)
            body_h = lines * 10 * 1.5 + 20  # padding
        else:
            body_h = 0
        return 8 + heading_h + body_h + 8  # margins

    elif sec_type == "gray_section":
        # Approximate: 20pt padding + inner content
        inner_sections = section.get("sections", [])
        inner_h = sum(estimate_section_height(s) for s in inner_sections)
        return 6 + 20 + inner_h + 6

    elif sec_type == "table":
        rows = section.get("rows", [])
        caption_h = 16 if section.get("caption") else 0
        header_h = 9 * 1.5 + 12  # header row
        row_h = len(rows) * (9 * 1.5 + 10)  # data rows
        return 6 + caption_h + header_h + row_h + 6

    elif sec_type == "chart_image":
        # Conservative chart height estimate.
        # CSS caps images at max-height: 400pt; most charts render ~200-300pt.
        # Using 300pt keeps estimation safely above the common case while still
        # allowing content after the chart on the same page.
        return 6 + 300 + 12 + 6  # image + caption + margins

    elif sec_type == "bullet_list":
        items = section.get("items", [])
        total = 0
        for item in items:
            lines = _estimate_text_lines(str(item), 10, w - 20)
            total += lines * 10 * 1.5 + 2
        return total + 4  # bottom margin

    elif sec_type == "source_note":
        lines = _estimate_text_lines(section.get("text", ""), 7.5, w)
        return 4 + lines * 7.5 * 1.25

    elif sec_type == "page_break":
        return 0  # Handled separately

    return 20  # Default fallback


# ── Page Splitter ─────────────────────────────────────────────────────────────

def split_into_pages(sections_html_list, sections_raw=None):
    """Split rendered section HTML strings into page groups.

    Uses height estimation to auto-fill pages with continuous content,
    eliminating white space at the bottom of pages. Explicit page_break
    markers force a new page. Content flows continuously otherwise.

    Args:
        sections_html_list: List of HTML strings (one per section).
        sections_raw: Optional list of raw section dicts for height estimation.

    Returns:
        List of lists, where each inner list is one page's HTML sections.
    """
    if sections_raw is None:
        # Fallback: use old page_break-only logic
        pages = [[]]
        for section_html in sections_html_list:
            if "<!-- PAGE_BREAK -->" in section_html:
                pages.append([])
            else:
                pages[-1].append(section_html)
        return [p for p in pages if p]

    pages = [[]]
    current_height = 0
    available = CONTENT_HEIGHT_PT

    for i, section_html in enumerate(sections_html_list):
        if "<!-- PAGE_BREAK -->" in section_html:
            # Forced page break
            if pages[-1]:  # Only start new page if current has content
                pages.append([])
                current_height = 0
            continue

        # Estimate height of this section
        section_h = estimate_section_height(sections_raw[i])

        # Look-ahead: if this is a heading/subsection, include the next
        # section's height to prevent orphaned headings at page bottom.
        # This covers heading→body, heading→subsection, subsection→body, etc.
        sec_type = sections_raw[i].get("type", "")
        combined_h = section_h
        if sec_type in ("heading", "subsection"):
            if i + 1 < len(sections_raw):
                next_type = sections_raw[i + 1].get("type", "")
                if next_type in ("body", "bullet_list", "subsection"):
                    combined_h += estimate_section_height(sections_raw[i + 1])
                    # If heading→subsection→body, also include the body
                    if next_type == "subsection" and i + 2 < len(sections_raw):
                        next_next_type = sections_raw[i + 2].get("type", "")
                        if next_next_type in ("body", "bullet_list"):
                            combined_h += estimate_section_height(sections_raw[i + 2])

        # Check if this section (+ its body if heading) fits on current page
        if current_height + combined_h > available and pages[-1]:
            # Start a new page
            pages.append([])
            current_height = 0

        pages[-1].append(section_html)
        current_height += section_h

    return [p for p in pages if p]  # Remove empty pages


# ── Main Generator ────────────────────────────────────────────────────────────

def generate_guide(yaml_path):
    """Generate a branded HTML advisor guide from a YAML content file.

    Args:
        yaml_path: Path to the YAML content file.

    Returns:
        Path to the generated HTML file.
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

    # ── Build reusable HTML fragments ─────────────────────────────────────

    # Black logo for headers / cover top bar (on white background)
    logo_path_black = brand_config.get_logo_path(logo_family, "black")
    logo_rel_black = os.path.relpath(logo_path_black, brand_config.OUTPUT_DIR).replace("\\", "/")
    logo_html_black = f'<img src="{logo_rel_black}" alt="{brand_config.LOGO_FAMILIES[logo_family]["name"]}">'

    # Icon SVG for footer
    icon_svg = load_icon_svg_inline()

    # Copyright text
    copyright_text = brand_config.build_copyright_text(logo_family)

    # ── Build cover page ──────────────────────────────────────────────────

    cover_html = build_cover_page(cover, logo_html_black, icon_svg, footer_url)

    # ── Render all content sections ───────────────────────────────────────

    rendered_sections = [render_section(sec) for sec in sections]

    # Split into pages using height estimation for continuous flow
    page_groups = split_into_pages(rendered_sections, sections_raw=sections)

    # If no explicit page breaks, put everything on one page
    if not page_groups:
        page_groups = [rendered_sections]

    # Build interior pages
    interior_pages = []
    for page_sections in page_groups:
        content_html = "\n".join(page_sections)
        page_html = build_interior_page(
            content_html, topic, footer_url,
            logo_html_black, icon_svg, copyright_text
        )
        interior_pages.append(page_html)

    # Build disclosures page
    disclosures_content = build_disclosures(
        legal_text=disclosures.get("legal_text", ""),
        glossary_terms=disclosures.get("glossary"),
        logo_family=logo_family,
    )
    disclosures_page = build_interior_page(
        disclosures_content, topic, footer_url,
        logo_html_black, icon_svg, copyright_text
    )

    # Load CSS
    css = load_css(brand_config.OUTPUT_DIR)

    # Assemble full HTML document
    all_pages = [cover_html] + interior_pages + [disclosures_page]

    safe_topic = topic.replace(" ", "-")
    title = f"{safe_topic} Advisor Guide {version}"

    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_mod.escape(title)}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="edit-hint screen-only">
        Return Stacked Advisor Guide \u2014 Edit text directly, then Print \u2192 PDF
    </div>

{"".join(all_pages)}

</body>
</html>'''

    # Write output
    output_filename = f"{safe_topic}-Advisor-Guide-{version}.html"
    output_path = os.path.join(brand_config.OUTPUT_DIR, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Generated: {output_path}")
    return output_path


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_guide.py <content.yaml>")
        print("Example: python generate_guide.py content/managed_futures.yaml")
        sys.exit(1)

    yaml_file = sys.argv[1]
    if not os.path.exists(yaml_file):
        print(f"Error: File not found: {yaml_file}")
        sys.exit(1)

    generate_guide(yaml_file)
