# Skill: Generate Cover

Generate a branded ReSolve Asset Management cover page for white papers, reports, and presentations.

## When to Use

When the user asks to create a cover page, front page, or title page for any ReSolve report or white paper.

## How It Works

The cover template and all assets live in `references/brand-assets/resolve-am/cover-template/`. The generator produces a self-contained HTML file with embedded base64 images that can be opened in a browser and printed to PDF at US Letter size.

### Design Elements (locked in, do not modify)

- ReSolve black logo, top-left
- Thin gray border (4 segments), stops before corner decoration
- Hexagonal cube corner decoration, bottom-right (extracted from reference papers at 600 DPI)
- Centered title block with configurable text
- Optional date line at bottom center
- US Letter proportions (8.5 x 11)

### Border Geometry (calibrated to reference PDFs)

- `border_inset = 3.5%` (all sides)
- `border_right_stop = 78%` (right border stops here, hex starts ~80%)
- `border_bottom_stop = 62%` (bottom border stops here, hex starts ~66%)

Do not change these values -- they were calibrated pixel-by-pixel against the Risk Parity reference report.

## Usage

### From the command line

```bash
python references/brand-assets/resolve-am/cover-template/generate_cover.py \
  --title "Report Title" \
  --subtitle "Optional Subtitle" \
  --doc-type "White Paper" \
  --date "January 2026" \
  --output path/to/cover.html
```

### From Python (in another script)

```python
import sys
sys.path.insert(0, "references/brand-assets/resolve-am/cover-template")
from generate_cover import generate_cover

html = generate_cover(
    title="All Terrain Strategy",
    subtitle="Annual Review",
    doc_type="Performance Report",
    date_line="2025",
    output="my-cover.html",
)
```

### From Claude Code

When the user asks you to generate a cover, run the generator script with the appropriate arguments. Place the output HTML in the relevant project folder.

## Customizable Fields

| Field | Argument | Default |
|-------|----------|---------|
| Title | `--title` | "Report Title" |
| Subtitle | `--subtitle` | (none) |
| Document type | `--doc-type` | "White Paper" |
| Date line | `--date` | (none) |
| Output path | `--output` | cover.html |

## Assets (in `references/brand-assets/resolve-am/cover-template/`)

| File | Description |
|------|-------------|
| `generate_cover.py` | Generator script (CLI + importable) |
| `corner-decoration.png` | Pre-extracted hexagonal decoration (2142x2112 px, 600 DPI) |
| `corner-decoration_b64.txt` | Same, base64-encoded for HTML embedding |
| `logo-black_b64.txt` | ReSolve black logo, base64-encoded |
| `logo-white_b64.txt` | ReSolve white logo, base64-encoded |

## Dependencies

None beyond Python standard library. All images are pre-extracted as base64.
