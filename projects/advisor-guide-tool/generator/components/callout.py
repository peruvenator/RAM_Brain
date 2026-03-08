"""Callout and panel HTML builders."""

import html


def build_teal_callout(text):
    """Build a teal callout block (BoldItalic, teal, left border).

    Args:
        text: The callout text string.

    Returns:
        HTML string.
    """
    return f'<div class="callout-teal">{html.escape(text)}</div>'


def build_dark_panel(heading, body=""):
    """Build a white-on-dark panel block.

    Args:
        heading: Panel heading text.
        body: Optional body text.

    Returns:
        HTML string.
    """
    body_html = ""
    if body:
        body_html = f'<p class="dark-panel-body">{html.escape(body)}</p>'

    return f'''<div class="dark-panel">
    <div class="dark-panel-heading">{html.escape(heading)}</div>
    {body_html}
</div>'''


def build_gray_section(inner_html):
    """Wrap content in a gray background section.

    Args:
        inner_html: Pre-built HTML to place inside the gray block.

    Returns:
        HTML string.
    """
    return f'<div class="gray-section">{inner_html}</div>'
