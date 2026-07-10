"""Build the branded ReSolve SMA Guide HTML using WhitePaperBuilder.

Reads draft.md, converts to HTML sections, and produces a branded
self-contained HTML file ready for print-to-PDF.
"""

import re
import sys
from pathlib import Path

# Add WhitePaperBuilder to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(
    0,
    str(ROOT / "references" / "brand-assets" / "resolve-am" / "white-paper-template"),
)
from white_paper_template import WhitePaperBuilder


def md_to_html(md: str) -> str:
    """Convert markdown text to HTML (subset needed for this guide)."""
    lines = md.split("\n")
    html_parts = []
    in_table = False
    table_rows = []
    in_list = False
    list_items = []
    in_blockquote = False
    bq_lines = []

    def flush_list():
        nonlocal in_list, list_items
        if in_list and list_items:
            html_parts.append("<ul>")
            for item in list_items:
                html_parts.append(f"  <li>{inline_format(item)}</li>")
            html_parts.append("</ul>")
            list_items = []
            in_list = False

    def flush_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html_parts.append("<table>")
            # Header row
            html_parts.append("  <tr>")
            for cell in table_rows[0]:
                html_parts.append(f"    <th>{inline_format(cell)}</th>")
            html_parts.append("  </tr>")
            # Data rows (skip separator row)
            for row in table_rows[1:]:
                if re.match(r"^[\s\-:|]+$", "|".join(row)):
                    continue
                html_parts.append("  <tr>")
                for cell in row:
                    html_parts.append(f"    <td>{inline_format(cell)}</td>")
                html_parts.append("  </tr>")
            html_parts.append("</table>")
            table_rows = []
            in_table = False

    def flush_blockquote():
        nonlocal in_blockquote, bq_lines
        if in_blockquote and bq_lines:
            content = "<br>\n".join(inline_format(l) for l in bq_lines)
            html_parts.append(f'<div class="callout">{content}</div>')
            bq_lines = []
            in_blockquote = False

    def inline_format(text: str) -> str:
        """Handle bold, italic, and links."""
        # Bold + italic
        text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Italic
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # Links
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        # En dash
        text = text.replace(" -- ", " \u2014 ")
        return text

    for line in lines:
        stripped = line.strip()

        # Table row
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_list()
            flush_blockquote()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not in_table:
                in_table = True
            table_rows.append(cells)
            continue
        elif in_table:
            flush_table()

        # Blockquote
        if stripped.startswith("> ") or stripped == ">":
            flush_list()
            in_blockquote = True
            content = stripped[2:] if stripped.startswith("> ") else ""
            if content:
                bq_lines.append(content)
            continue
        elif in_blockquote and stripped and not stripped.startswith("#"):
            # Continuation of blockquote (non-prefixed lines within a quote block)
            bq_lines.append(stripped)
            continue
        elif in_blockquote:
            flush_blockquote()

        # Headings
        heading_match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading_match:
            flush_list()
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            html_parts.append(f"<h{level}>{inline_format(text)}</h{level}>")
            continue

        # List items
        if stripped.startswith("- "):
            in_list = True
            list_items.append(stripped[2:])
            continue
        elif in_list:
            flush_list()

        # Empty line
        if not stripped:
            continue

        # Regular paragraph
        html_parts.append(f"<p>{inline_format(stripped)}</p>")

    flush_list()
    flush_table()
    flush_blockquote()

    return "\n".join(html_parts)


def split_into_sections(md: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, content) pairs at ## boundaries."""
    # Remove frontmatter
    md = re.sub(r"^---\n.*?\n---\n*", "", md, flags=re.DOTALL)

    sections = []
    current_heading = ""
    current_lines = []

    for line in md.split("\n"):
        if re.match(r"^## ", line):
            if current_heading or current_lines:
                sections.append((current_heading, "\n".join(current_lines)))
            current_heading = line
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading or current_lines:
        sections.append((current_heading, "\n".join(current_lines)))

    return sections


def build():
    here = Path(__file__).parent
    draft = (here / "draft.md").read_text(encoding="utf-8")

    # Split into sections and convert to HTML
    raw_sections = split_into_sections(draft)

    html_sections = []
    for heading, content in raw_sections:
        full_md = f"{heading}\n{content}" if heading else content
        section_html = md_to_html(full_md)
        # Determine section class
        heading_text = heading.replace("## ", "").strip().lower() if heading else ""
        if "disclosure" in heading_text:
            css_class = "disclosure-section"
        else:
            css_class = "section"
        html_sections.append(f'<div class="{css_class}">\n{section_html}\n</div>')

    # Build the document
    builder = WhitePaperBuilder(
        header_line1="ReSolve SMA Guide",
        header_line2="Structure, Strategies & Operations",
        document_title="ReSolve SMA Guide - ReSolve Asset Management",
    )

    # Cover page
    cover = builder.build_cover(
        title="ReSolve SMA Guide",
        subtitle="Understanding Your ReSolve SMA:\nStructure, Strategies, and Operations",
        doc_type="Client Guide",
        date_line="March 2026",
    )

    # Page mapping: distribute sections across pages
    # Each section gets its own page for now; we can merge short sections later
    pages = [cover]
    for i, section in enumerate(html_sections):
        pages.append(builder.interior_page(i + 2, section))

    html = builder.wrap_document(pages)

    out = here / "output" / "resolve-sma-guide.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {len(html):,} chars ({len(pages)} pages) to {out}")


if __name__ == "__main__":
    build()
