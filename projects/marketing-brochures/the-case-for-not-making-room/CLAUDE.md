# The Case for NOT Making Room for Alternatives — HTML Brochure

## Project Overview

This is a 7-page print-ready HTML brochure for **Return Stacked Portfolio Solutions**, converted from an 11-slide PowerPoint deck (`The_Case_for_NOT_Making_Room_for_Alternatives.pptx`). The HTML is designed for US Letter (8.5" x 11") and renders correctly when printed via browser Print > Save as PDF.

## Key Files

| File | Purpose |
|------|---------|
| `The-Case-for-NOT-Making-Room-for-Alternatives.html` | **Main deliverable** — the 7-page HTML brochure (single self-contained file with inline CSS) |
| `The_Case_for_NOT_Making_Room_for_Alternatives.pptx` | Source PowerPoint deck (11 slides) |
| `Managed-Futures-Advisor-Guide-V3.html` | Reference template from a prior brochure — use for brand/style patterns |
| `../../../references/brand-assets/return-stacked/` | Shared brand assets: DM Sans font files, logos, backdrop image, color definitions |
| `extracted_images/` | Images extracted from the PPTX (used for contact page backdrop: `image3.jpg`) |
| `chart_exports/` | High-res chart PNGs cropped from PowerPoint slide exports |

## Chart Exports (`chart_exports/`)

Charts were exported from PowerPoint at 4000x2250 resolution (~300 DPI) using COM automation, then cropped and auto-trimmed.

| File | Source Slide | Dimensions | Content |
|------|-------------|------------|---------|
| `slide2.png` | Slide 2 (full) | 4000x2250 | Growth-of-$100 line chart |
| `slide3.png` | Slide 3 (full) | 4000x2250 | Two donut/pie charts (60/40 vs 50/30/20) |
| `slide5.png` | Slide 5 (full) | 4000x2250 | Stacked bar diagram |
| `chart_growth.png` | Cropped from slide2 | ~3028x789 | Growth-of-$100 line chart (5 series) |
| `chart_pies.png` | Cropped from slide3 | ~3038x745 | Both donut charts with arrow and labels |
| `chart_stackedbar.png` | Cropped from slide5 | ~1070x1268 | Return Stacked fund structure diagram |

### Re-exporting Charts

If the PowerPoint charts change, re-run these scripts in order:

1. **`export_charts.ps1`** — Opens PPTX via PowerPoint COM, exports slides 2, 3, 5 at 4000x2250
2. **`crop_charts.ps1`** — Crops and auto-trims the exported slides to isolate chart content

**Critical gotcha**: When using `System.Drawing` to crop images, you MUST call `$bmp.SetResolution($src.HorizontalResolution, $src.VerticalResolution)` on the destination bitmap before drawing. PowerPoint exports at ~300 DPI, but `System.Drawing.Bitmap` defaults to 96 DPI. Without matching DPI, `DrawImage` scales content to ~1/3 size.

### Crop Coordinates (in `crop_charts.ps1`)

```
chart_growth:     x=160,  y=885,  w=3360, h=850
chart_pies:       x=80,   y=1005, w=3300, h=830
chart_stackedbar: x=2020, y=375,  w=1520, h=1380
```

Auto-trim treats pixels with ALL channels in 237..247 as slide background (#F2F2F2) and removes them, adding 25px padding.

## HTML Brochure Structure

### 7 Pages

1. **Cover** — Title, banner with backdrop image, intro text, teal highlight
2. **Theory vs. Reality** — Growth-of-$100 chart (PNG), pie charts (PNG), source notes
3. **The Constraint** — Dark panels with behavioral challenges, gray section with narrative
4. **The Solution** — Stacked bar diagram (PNG), two-column comparison panels
5. **Offense + Implementation** — Three approach cards, implementation table
6. **Contact** — Full-bleed dark backdrop, CTA button, logo
7. **Disclosures** — Dark background, legal text, copyright

### CSS Architecture

All styles are inline in `<style>` within the HTML `<head>`. No external CSS files.

**Brand tokens** (CSS custom properties in `:root`):
```css
--text-primary: #2c3641      /* Dark navy — body text */
--text-secondary: #625c6d    /* Gray-purple — secondary text */
--cover-dark: #172c3a        /* Deep navy — cover/panels */
--teal-primary: #14cfa6      /* Brand teal — accents, CTAs */
--teal-light: #a1d7c6        /* Light teal — watermarks */
--blue-secondary: #3a6a9c    /* Blue — approach cards */
--blue-light: #7da5ce        /* Light blue — bonds color */
--yellow: #ebe96a            /* Yellow — highlights */
--section-gray: #f0f1f1      /* Light gray — panel backgrounds */
--font-family: 'DM Sans'     /* Brand font (loaded via @font-face) */
```

**Page dimensions**: 8.5in x 11in, margins ~0.4in sides, 0.5in top, 0.31in bottom.

**Key CSS classes**:
- `.page` — Each page is a fixed-size container
- `.cover-page` / `.interior-page` / `.contact-page` / `.disclosures-page` — Page types
- `.page-header` / `.page-footer` — Consistent header/footer with logo, teal accent bar
- `.section-heading` — Green bar left-border headings
- `.body-text` — Standard body text (10pt DM Sans)
- `.dark-panel` — Teal-header panel with gray body
- `.callout-teal` — Italic teal quote with left border
- `.pptx-chart` — Container for PowerPoint-exported chart images
- `.pptx-chart-wide img` — max-height: 180pt (growth chart, pie charts)
- `.pptx-chart-tall img` — max-height: 260pt, max-width: 50% (stacked bar)
- `.source-note` — 7pt italic disclaimer text

### Print Workflow

Open the HTML in a browser, then **Print > Save as PDF** with:
- Paper size: Letter
- Margins: None
- Background graphics: ON

## Helper Scripts (PowerShell)

| Script | Purpose |
|--------|---------|
| `export_charts.ps1` | PowerPoint COM automation — exports slides as high-res PNGs |
| `crop_charts.ps1` | Crops + auto-trims chart regions from full slide PNGs |
| `broad_probe.ps1` | Pixel scanner — finds content boundaries in slide images |
| `debug_crop.ps1` | Diagnostic — identified the DPI mismatch bug |
| `precise_probe.ps1` | Earlier pixel probe (less useful, exact color matching) |
| `find_edges.ps1` | Edge detection helper |
| `probe_pixels.ps1` | General pixel inspection |

## Conventions

- Font: **DM Sans** (all weights from Thin to ExtraBold, loaded via `@font-face`)
- Logo: `../../../references/brand-assets/return-stacked/Logos/RS_Portfolio_Solutions_logos/Return Stacked Portfolio Solutions Black.png`
- White logo variant used on contact page
- Backdrop image: `../../../references/brand-assets/return-stacked/Background_images/RS-Background-Blue.png` (cover banner) and `extracted_images/image3.jpg` (contact page)
- Slide background color: `#F2F2F2` (RGB 242,242,242)
- Chart internal gray: `#D9D9D9` (RGB 217,217,217)
