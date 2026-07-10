# Skill: Generate White Paper

Generate a branded ReSolve Asset Management white paper or report using the shared paged layout system.

## When to Use

When the user asks to create a new white paper, research report, performance report, or any multi-page PDF-style document branded for ReSolve Asset Management (not Return Stacked).

## How It Works

The white paper template lives in `references/brand-assets/resolve-am/white-paper-template/`. It provides a Python class (`WhitePaperBuilder`) that handles the entire paged layout: CSS, embedded Helvetica Neue fonts, page headers with logo, page footers with numbers, cover page, and print-to-PDF styles.

### Architecture

```
references/brand-assets/resolve-am/
  white-paper-template/
    white_paper_template.py    <-- shared layout engine (import this)
  cover-template/              <-- cover assets (used automatically)
  Fonts/                       <-- Helvetica Neue (embedded automatically)
  Logo/                        <-- SVG logo (embedded automatically)
```

The template produces self-contained HTML (all fonts/images base64-embedded) at US Letter size. Print to PDF from Chrome with no margins and background graphics enabled.

## Usage

### Quick start (Python)

```python
import sys
from pathlib import Path

# Add template to path
ROOT = Path(__file__).parent.parent.parent  # adjust to reach RAM_Brain root
sys.path.insert(0, str(ROOT / "references" / "brand-assets" / "resolve-am" / "white-paper-template"))
from white_paper_template import WhitePaperBuilder

builder = WhitePaperBuilder(
    header_line1="Report Title",
    header_line2="Subtitle or Date Range",
    document_title="Report Title - ReSolve Asset Management",
)

# Build pages
cover = builder.build_cover(
    title="Report Title",
    subtitle="Optional Subtitle",
    doc_type="White Paper",
    date_line="March 2026",
)
pages = [cover]
for i, section_html in enumerate(my_sections):
    pages.append(builder.interior_page(i + 2, section_html))

html = builder.wrap_document(pages)
Path("output.html").write_text(html)
```

### High-level shortcut

If you already have sections and a page map (list of section-index lists):

```python
html = builder.build_from_page_map(
    sections=my_sections,
    page_map=[[0], [1], [2, 3], [4]],  # which sections go on each page
    title="Report Title",
    subtitle="Subtitle",
    doc_type="White Paper",
    date_line="March 2026",
)
```

### Reformatting existing HTML

If a build script produces raw HTML with `<div class="section">` blocks, use the extraction utilities:

```python
from white_paper_template import (
    WhitePaperBuilder, extract_sections, extract_cover,
    split_section_at, extract_doc_footer,
)

raw_html = Path("raw-report.html").read_text()
sections = extract_sections(raw_html)
cover = extract_cover(raw_html)
doc_footer = extract_doc_footer(raw_html)

# Split long sections across pages
part_a, part_b = split_section_at(sections[5], '<h3>Rolling Analysis</h3>')
sections[5] = part_a
sections.insert(6, part_b)

builder = WhitePaperBuilder(header_line1="My Report", header_line2="2026")
html = builder.build_from_page_map(sections, page_map, cover_html=cover, doc_footer=doc_footer)
```

## Component Vocabulary

Use these CSS classes when building section HTML content. The template CSS styles them automatically.

### Sections

| Class | Usage |
|-------|-------|
| `section` | Standard content section (`<div class="section">`) |
| `disclosure-section` | Back-matter sections (glossary, disclosures) with smaller text |

### Section Content

| Element | Example |
|---------|---------|
| `<h2>` | Section title (blue, gold underline) |
| `<h3>` | Subsection title (blue, smaller) |
| `<p>` | Body text |

### Charts and Figures

```html
<div class="figure-block">
  <p class="figure-caption">Figure 1: Growth of $1</p>
  <div class="chart-container">
    <img src="data:image/png;base64,..." alt="Growth of $1">
  </div>
  <p class="figure-disclosure">Source: Bloomberg. Past performance...</p>
</div>
```

### Stat Cards

```html
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-label">Annualized Return</div>
    <div class="stat-value">8.2%</div>
    <div class="stat-detail">vs. 7.1% benchmark</div>
  </div>
  <div class="stat-card benchmark">
    <div class="stat-label">Benchmark Return</div>
    <div class="stat-value">7.1%</div>
  </div>
</div>
```

### Tables

Standard `<table>` elements are styled automatically. First column left-aligned, others centered. Header row is dark blue.

### Callouts

```html
<div class="callout">Key finding or important note.</div>
<div class="callout callout-warn">Warning or caveat.</div>
```

### Utility Classes

| Class | Effect |
|-------|--------|
| `highlight` | Blue bold text |
| `neg` | Red text (negative values) |
| `pos` | Green text (positive values) |
| `two-col` | Two-column grid layout |
| `disclaimer` | Small gray disclaimer text with top border |

## Design Tokens (from RAM brand)

These are baked into the CSS. For reference:

| Token | Hex | Usage |
|-------|-----|-------|
| Brand Blue | `#00478D` | Headings, stat card borders, highlights |
| Accent Blue | `#177BBB` | Header/footer rules |
| Footer Box | `#007FBF` | Page number background |
| Gold | `#FBBA00` | Section title underlines, warning callouts |
| Table Header | `#04367B` | Table header background |
| Dark Text | `#0E2841` | Stat values, table first column |
| Body Text | `#1a1a1a` | Paragraphs |

## Existing Reports Using This Template

- **Trend Replication Report** (`projects/trend-replication-report/reformat_html.py`)

## Dependencies

- Python 3.10+ (for `str | None` union syntax)
- No third-party packages (standard library only)
