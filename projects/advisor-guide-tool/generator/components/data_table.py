"""Branded data table HTML builder."""

import html


# ── Correlation matrix helpers ───────────────────────────────────────────────

# Brand teal RGB components: #14cfa6 → (20, 207, 166)
_TEAL_R, _TEAL_G, _TEAL_B = 20, 207, 166


def _correlation_cell_style(value_str):
    """Compute inline background-color and text color for a correlation value.

    Uses an ease-in curve (t²) so low correlations stay very subtle/white
    and mid-to-high correlations ramp up toward brand teal.

    Args:
        value_str: Cell value as a string (e.g. "0.72", "-0.03", "1.00").

    Returns:
        CSS inline style string, or empty string if value is not numeric.
    """
    try:
        val = abs(float(value_str))
    except (ValueError, TypeError):
        return ""

    val = min(val, 1.0)  # clamp

    # Ease-in: square the value so low correlations stay nearly white
    t = val ** 2

    # Interpolate white (255,255,255) → teal (20,207,166)
    r = int(255 + t * (_TEAL_R - 255))
    g = int(255 + t * (_TEAL_G - 255))
    b = int(255 + t * (_TEAL_B - 255))

    bg = f"#{r:02x}{g:02x}{b:02x}"

    # Text contrast: switch to white when background luminance is low
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    fg = "#ffffff" if luminance < 160 else "#2c3641"

    return f"background-color:{bg};color:{fg};"


def build_correlation_matrix(headers, rows, caption=""):
    """Build a heat-mapped correlation matrix table.

    Cell backgrounds interpolate from white (0) to brand teal (1) based on
    the absolute value, using an ease-in curve for natural shading.

    Args:
        headers: List of column header strings.
        rows: List of lists (each inner list is one row of cell values).
        caption: Optional table caption string.

    Returns:
        HTML string.
    """
    caption_html = ""
    if caption:
        caption_html = f'<div class="data-table-caption">{html.escape(caption)}</div>'

    header_cells = "".join(
        f'<th class="corr-header">{html.escape(str(h))}</th>' for h in headers
    )

    body_rows = []
    for row in rows:
        cells = []
        for col_idx, cell in enumerate(row):
            if col_idx == 0:
                # Row label — left-aligned, no color
                cells.append(
                    f'<td class="corr-label">{html.escape(str(cell))}</td>'
                )
            else:
                # Value cell with computed background
                style = _correlation_cell_style(str(cell))
                style_attr = f' style="{style}"' if style else ""
                cells.append(
                    f'<td class="corr-value"{style_attr}>'
                    f'{html.escape(str(cell))}</td>'
                )
        body_rows.append(f'<tr>{"".join(cells)}</tr>')

    return f'''<div class="data-table-wrapper">
    {caption_html}
    <table class="correlation-matrix">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{"".join(body_rows)}</tbody>
    </table>
</div>'''


# ── Standard data table ──────────────────────────────────────────────────────

def build_data_table(headers, rows, caption=""):
    """Build a branded data table.

    Args:
        headers: List of column header strings.
        rows: List of lists (each inner list is one row of cell values).
        caption: Optional table caption string.

    Returns:
        HTML string.
    """
    caption_html = ""
    if caption:
        caption_html = f'<div class="data-table-caption">{html.escape(caption)}</div>'

    header_cells = "".join(
        f"<th>{html.escape(str(h))}</th>" for h in headers
    )

    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{html.escape(str(cell))}</td>" for cell in row
        )
        body_rows.append(f"<tr>{cells}</tr>")

    return f'''<div class="data-table-wrapper">
    {caption_html}
    <table class="data-table">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{"".join(body_rows)}</tbody>
    </table>
</div>'''
