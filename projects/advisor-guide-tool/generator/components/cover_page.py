"""Cover page HTML builder."""

import html


def build_cover_page(cover_data, logo_html_black, icon_svg, footer_url):
    """Build the cover page HTML.

    Args:
        cover_data: dict with keys: topic_display, intro_heading, intro_text,
                    and optional intro_highlight.
        logo_html_black: HTML string for the logo image tag (black variant for
                         the white top bar).
        icon_svg: HTML string for the RS icon (SVG) used in the footer.
        footer_url: URL string for the footer band (e.g. 'www.returnstackedetfs.com').

    Returns:
        HTML string for the cover page.
    """
    topic = html.escape(cover_data.get("topic_display", ""))
    intro_heading = html.escape(cover_data.get("intro_heading", "Why This Conversation Matters"))
    intro_text = html.escape(cover_data.get("intro_text", ""))
    intro_highlight = cover_data.get("intro_highlight", "")

    highlight_html = ""
    if intro_highlight:
        highlight_html = f'<p class="cover-intro-highlight">{html.escape(intro_highlight)}</p>'

    return f'''<div class="page cover-page">
    <div class="page-content">
        <div class="cover-top-bar">
            <div class="cover-top-logo">{logo_html_black}</div>
        </div>
        <div class="cover-banner">
            <div class="cover-watermark">Advisor\u2019s Guide</div>
            <div class="cover-title-block">
                <!-- Shadow layer: black duplicate offset behind for drop shadow effect -->
                <div class="cover-title-shadow" aria-hidden="true">
                    <div class="cover-title-line">The <strong>Advisor\u2019s Guide</strong> to</div>
                    <div class="cover-title-line">Client Conversations</div>
                    <div class="cover-connector">about</div>
                    <div class="cover-topic">{topic}</div>
                </div>
                <!-- Foreground text -->
                <div class="cover-title-line">The <strong>Advisor\u2019s Guide</strong> to</div>
                <div class="cover-title-line">Client Conversations</div>
                <div class="cover-connector">about</div>
                <div class="cover-topic">{topic}</div>
            </div>
        </div>
        <div class="cover-intro">
            <h2 class="cover-intro-heading">{intro_heading}</h2>
            <p class="cover-intro-text">{intro_text}</p>
            {highlight_html}
        </div>
    </div>
</div>'''
