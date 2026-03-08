"""Interior content page HTML builder."""

import html as html_mod
from .header_footer import build_header, build_footer


def build_interior_page(sections_html, topic_name, footer_url, logo_html_black,
                        icon_svg, copyright_text):
    """Build a single interior page with header, footer, and content.

    Args:
        sections_html: Pre-built HTML string for the content area.
        topic_name: Topic for the header.
        footer_url: URL for the footer.
        logo_html_black: HTML img tag for the black logo variant.
        icon_svg: HTML string for the RS icon SVG.
        copyright_text: Copyright line for the footer.

    Returns:
        HTML string for one interior page.
    """
    header = build_header(topic_name, logo_html_black)
    footer = build_footer(footer_url, icon_svg, copyright_text)

    return f'''<div class="page interior-page">
    {header}
    <div class="interior-content">
        {sections_html}
    </div>
    {footer}
</div>'''
