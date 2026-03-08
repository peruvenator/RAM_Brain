"""Running header and footer HTML builders."""

import html


def build_header(topic_name, logo_html_black):
    """Build the interior page header HTML.

    Structure (matching reference PDF):
    logo (left) | right-aligned titles:
      Line 1: "The Advisor's Guide to" (teal, bold)
      Line 2: "Client Conversations about" (dark)
      Line 3: topic name (dark)
    | teal accent rectangle on far right edge.

    Args:
        topic_name: The topic string (e.g. 'Managed Futures').
        logo_html_black: HTML img tag for the black logo variant.

    Returns:
        HTML string for the page header.
    """
    return f'''<div class="page-header">
        <div class="page-header-logo">{logo_html_black}</div>
        <div class="page-header-titles">
            <div class="page-header-series">The Advisor\u2019s Guide to</div>
            <div class="page-header-topic">Client Conversations about</div>
            <div class="page-header-topic">{html.escape(topic_name)}</div>
        </div>
        <div class="page-header-accent"></div>
    </div>'''


def build_footer(footer_url, icon_svg, copyright_text):
    """Build the interior page footer HTML.

    Structure (matching reference PDF):
    RS icon (dark bg) | teal band | white area with URL in dark text.

    Args:
        footer_url: URL string (e.g. 'www.returnstackedetfs.com').
        icon_svg: HTML string for the RS icon SVG.
        copyright_text: Copyright line (unused in current layout but kept for API compat).

    Returns:
        HTML string for the page footer.
    """
    return f'''<div class="page-footer">
        <div class="page-footer-icon">{icon_svg}</div>
        <div class="page-footer-band"></div>
        <div class="page-footer-url-area">
            <span class="page-footer-url">{html.escape(footer_url)}</span>
        </div>
    </div>'''
