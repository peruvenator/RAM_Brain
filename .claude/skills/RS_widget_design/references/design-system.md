# RS Widget Design System

Visual tokens, typography, and control specs for Return Stacked / ReSolve interactive widgets. Mirrors the starter template in `templates/widget-starter.html` and the production Advanced Visualizer (`projects/portfolio-visualizer-widget/build_widget.py`).

---

## Color Palette

Canonical token block from the production widget. Define on the widget root, never on `:root`:

```css
.rsw-widget {
  --teal: #14cfa6;          /* CTA buttons, active tab text/indicator, focus rings, "stacked" line */
  --teal-dark: #0c7c64;     /* teal button hover, success text */
  --teal-light: #a1d7c6;    /* header subtitle text on dark backgrounds */
  --accent-green: #60cca8;  /* positive values, success borders, slider thumbs */
  --navy: #2a3f5b;          /* headings, compact buttons, tooltip bg, date buttons */
  --blue: #3a6a9c;          /* secondary buttons, info borders, add-row buttons */
  --blue-light: #7da5ce;    /* chart variant */
  --text-primary: #2c3641;  /* body text */
  --text-secondary: #625c6d;/* labels, descriptions, table headers */
  --cover-dark: #172c3a;    /* branded header bg, PDF cover, modal overlay tint */
  --section-gray: #f5f6fa;  /* tab bar bg, summary bar bg, date-range bar bg, table row dividers */
  --border-gray: #bfbfbf;   /* input borders, dividers, disabled states */
  --yellow: #ebe96a;        /* warning borders, chart accent */
  --white: #ffffff;
  --danger: #e74c3c;        /* negative values, errors, remove buttons */
  --success: #60cca8;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --card-radius: 20px;      /* widget outer shell */
  --card-pad: 32px;         /* widget outer padding; header uses negative margins against it */
}
```

Watch-outs from past drift:
- `--text-secondary` is `#625c6d` (warm purple-gray), **not** `#555`.
- `--section-gray` is `#f5f6fa`. Don't invent parallel tokens like `--section-bg`.
- `--navy` is `#2a3f5b`. The darker `#323A46` is the **first chart color**, not the navy token.
- `--cover-dark: #172c3a` is what makes the branded header/PDF cover read as "Return Stacked" — don't substitute navy.

Supplementary hardcoded grays used in production (fine to use as-is): row hover `#f8f9fb`, zebra `#f9fafb`, table hover `#eef1f6`, callout bg `#f8f9fc`, slider track `#dde2eb`.

**Use CSS custom properties, not raw hex.** Asset-specific colors should also be tokenized per widget.

---

## Widget Shell

The production widget is a single rounded card:

```css
.rsw-widget {
  font-family: "DM Sans", sans-serif;
  color: var(--text-primary);
  background: var(--white);
  max-width: 1264px;
  margin: 0 auto;
  padding: var(--card-pad);
  line-height: 1.5;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  isolation: isolate;                       /* stacking-context boundary vs Divi */
  border-radius: var(--card-radius);
  box-shadow: 0 2px 16px rgba(23, 44, 58, 0.07);
}
```

On mobile (<= 768px): `--card-pad: 10px`, base font 13px.

---

## Branded Header (required on Return Stacked widgets)

Dark full-bleed band at the top of the card. Uses negative margins to escape the card padding, then re-rounds the top corners:

```css
.rsw-header {
  background: var(--cover-dark);
  color: var(--white);
  padding: 24px 32px;
  margin: calc(-1 * var(--card-pad)) calc(-1 * var(--card-pad)) 0;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
}
.rsw-header h1 { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
.rsw-header p  { font-size: 13px; color: var(--teal-light); font-weight: 400; }
```

```html
<div class="rsw-header" style="display:flex;align-items:center;justify-content:space-between;gap:16px;">
  <div>
    <h1>Return Stacked&reg; Widget Name</h1>
    <p>One-line subtitle describing what the widget does</p>
  </div>
  <img src="{logo_white_uri}" alt="Return Stacked" style="height:40px;opacity:0.9;flex-shrink:0;">
</div>
```

**Logo assets** — base64 data URIs live in the visualizer project's `data/` directory and are injected as f-string variables by the build script:

| File | Variable | Use |
|---|---|---|
| `data/logo_ps_white_uri.txt` | `logo_white_uri` | Header on dark bg (Portfolio Solutions wordmark, white) |
| `data/logo_ps_black_uri.txt` | `logo_ps_black_uri` | PDF cover / light backgrounds |
| `data/logo_white_uri.txt` | `logo_icon_white_uri` | Small icon mark, white (PDF footer square) |
| `data/logo_black_uri.txt` | `logo_black_uri` | Small icon mark, black |
| `data/bg_image_uri.txt` | `bg_image_uri` | PDF cover backdrop |

Copy these files (or reference them across projects) rather than re-encoding logos.

Mobile: header padding `16px 20px`, h1 `18px`.

---

## Typography

**Font:** DM Sans (Google Fonts CDN), weights 400, 500, 600, 700. Fallback: `'DM Sans', sans-serif`.

```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Weights:** 400 body · 500 labels/secondary · 600 buttons, modal titles, chart legend · 700 headings, tab names, stat values, CTA buttons.

**Sizing scale:**
| Size | Usage |
|---|---|
| 10px | Summary-bar labels (uppercase), axis labels, allocation % labels |
| 11px | Tooltips, table headers (uppercase), disclaimers, quick date buttons, chart font |
| 12px | Compact buttons, date buttons, chart tabs, subsection labels |
| 13px | Tabs, inputs/selects, table body, header subtitle, section body |
| 14px | Base widget font, primary buttons |
| 15px | Section titles |
| 18px | Summary-bar values, modal headings (1.125rem) |
| 22px | Page titles (comparison panels) |
| 24px | Header h1 (18px mobile) |

**Numeric alignment:** `font-variant-numeric: tabular-nums` on the widget root and any numeric stat/table cell.

**PDF fonts:** DM Sans is embedded as base64 (`data/dmRegular.txt`, `dmBold.txt`, `dmItalic.txt`, `dmBoldItalic.txt`) and registered with jsPDF via `addFileToVFS`/`addFont` so PDF export never depends on a network font.

---

## Spacing and Radii

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `4px` | Inputs, tooltips, small buttons, bar segments |
| `--radius-md` | `6px` | Buttons, chart-area border, summary bar, CTA strip |
| `--radius-lg` | `8px` | Modal cards, allocation bar, callout right edge |
| `--radius-xl` | `12px` | Reserved for large surfaces |
| `--card-radius` | `20px` | Widget shell + header top corners |

**Section gaps:** 24px panel padding, 16px between controls, 8-12px between related items.

**Transitions:** the house easing is `cubic-bezier(0.23, 1, 0.32, 1)` at `0.15s`-`0.25s`. Replace `transition: all` (antipattern) with explicit property lists.

---

## Structure & Navigation

### Numbered step headers
Steps ("1 Build", "2 Configure"...) use a teal circle + uppercase label:

```css
.rsw-step-num {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--teal); color: var(--white);
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.rsw-step-label {
  font-size: 11px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; color: var(--navy);
}
```

### Section titles
15px, weight 700, navy, with a 2px teal underline: `border-bottom: 2px solid var(--teal); display: inline-block; padding-bottom: 8px;`

### Tabs (top-level)
- Tab bar: `background: var(--section-gray); border-bottom: 2px solid var(--border-gray);` full-bleed via negative margins against `--card-pad`
- Tab: 13px, weight 500, `--text-secondary`; hover `--text-primary`
- Active: **teal** text, weight 700
- Active indicator: `::after` bar, 3px tall teal, `border-radius: 2px 2px 0 0`, animated `transform: scaleX(0) -> scaleX(1)` over `0.25s cubic-bezier(0.23, 1, 0.32, 1)`

### Chart sub-tabs
Smaller variant inside the chart area: 12px font, active = **navy** text on white bg with a 2px teal `::after` indicator (same scaleX entrance at 0.2s).

---

## Controls

### Buttons

Production uses a primary family (`.rsv-compute-btn`) plus modifier variants — replicate the pattern:

| Variant | Colors | Use |
|---|---|---|
| base (primary) | Teal bg, white text, weight 700, `9px 22px`, radius 6px; hover `--teal-dark` | Main action |
| `--secondary` | Blue bg (`--blue`); hover `#2d5580` | Second-rank actions (Share) |
| `--tertiary` | `--text-secondary` bg; hover `#4a4557` | Low-emphasis actions |
| `--compact` | Navy bg, 12px font, `6px 14px`; hover `#232a34` | Inline / table-header actions |

Additional button species:
- **Add-row** (`.rsw-add-btn`): transparent bg, 1px **dashed** blue border, blue text; hover: faint blue bg + teal border. `--filled` variant: solid teal.
- **Remove-row**: borderless `×`, `--danger` text, faint red bg on hover.
- **Date buttons**: white bg, 1px navy border, navy text; hover/active state inverts to navy bg + white text.
- **Chart download** (`.rsw-dl-btn`): 11px, semi-transparent white bg, absolute top-right of chart, `opacity: 0.55` until hover.

All buttons get `transform: scale(0.97)` on `:active`. Disabled: `background: var(--border-gray); cursor: not-allowed`.

### Inputs / Selects
- 1px solid `--border-gray`, 4px radius, `6px 10px` padding, 13px
- Focus: `border-color: var(--teal); box-shadow: 0 0 0 2px rgba(20, 207, 166, 0.15);`
- Number inputs: hide spinners (`::-webkit-outer/inner-spin-button { -webkit-appearance: none }`, `appearance: textfield`), center text, fixed width (~80px)

### Searchable combobox
For long option lists (55+ assets) production replaced `<select>` with a searchable combobox: trigger button + dropdown panel (`box-shadow: 0 6px 18px rgba(0,0,0,0.12)`, `z-index: 1000`) + search field + grouped options. States are namespaced: `.is-open`, `.is-selected` (teal, weight 600), `.is-disabled`, `.is-active`. Group headers: 11px uppercase `--text-secondary`.

### Sliders
- Track: 6px tall, `#dde2eb`, radius 3px
- Thumb: 20px navy circle, 2px white border, `0 1px 4px rgba(0,0,0,0.25)` shadow; hover `scale(1.1)`; `margin-top: -7px` on the webkit thumb
- Value pill: navy bg, white text, `border-radius: 12px`, `4px 12px`, 13px, weight 700, `tabular-nums`
- Style `-webkit-slider-thumb` and `-moz-range-thumb` separately; `-webkit-appearance: none` on input and thumb

### Date-range bar
Shared control pattern for period filtering:
- Container: `--section-gray` bg, radius 6px, `12px 16px`, flex + wrap
- Contents: year select, two `input[type=date]` (140px), Reset button, then quick buttons (3M/6M/YTD/1Y/3Y/5Y/10Y/20Y/All) separated by a `border-left: 1px solid var(--border-gray)` divider
- Quick buttons: 11px, weight 600; `.active` (namespaced if needed) and hover invert to navy

### Tooltips
- Trigger: `?` icon (`cursor: help`) or a `.rsw-btn-tooltip` wrapper around buttons
- Popup: navy bg, white text, 11px, 240px wide, radius 4px, `8px 10px`, positioned above (`bottom: 125%`, centered)
- Entrance: `opacity` + `transform: translateY(4px) scale(0.98) -> translateY(0) scale(1)` at `0.2s` house easing
- `pointer-events: none` on the popup

---

## Results Display

### Summary bar
Horizontal strip of key numbers above results:
- Container: `--section-gray` bg, radius 6px, `16px 20px`, flex gap 24px, `box-shadow: inset 0 0 0 1px rgba(0,0,0,0.04)`
- Label: 10px, weight 700, uppercase, letter-spacing 0.5px, `--text-secondary`
- Value: 18px, weight 700, navy; `.warning` state colors it `--danger`

### Tables
- No table backgrounds/borders at the `table` level (strip Divi defaults via the `:where()` reset)
- Header: 11px, weight 700, uppercase, `--text-secondary`, `border-bottom: 2px solid var(--navy)`
- Body cells: `8px 10px` padding, `border-bottom: 1px solid var(--section-gray)`
- Zebra: `tbody tr:nth-child(even) td { background: #f9fafb; }` — set on `td`, not `tr`, to beat Divi
- Hover: `tbody tr:hover td { background: #eef1f6; }`
- `.positive` (accent-green) / `.negative` (danger) cell classes, weight 700
- Matrix variant: center-align everything except the first column

For comparison tables (Core vs Stacked vs Difference), color **only** the Difference column. Keep Core/Stacked neutral. Tracking Error stays black even in the Difference column.

### Allocation bar
Vertical stacked bar (60px wide, radius 8px, `flex-direction: column-reverse`) with a dashed 100% reference line (`border-top: 2px dashed var(--border-gray)`), color-dot legend rows, and `transition: flex 0.25s ease` on segments so weights animate.

### Chart area
- Container: white bg, `1px solid var(--section-gray)` border, radius 6px, `box-shadow: 0 1px 4px rgba(0,0,0,0.06)`
- Chart canvas container: `height: 420px` fixed, `padding: 16px` (280px on mobile)

### Callouts & validation
- Callout: `#f8f9fc` bg, 4px left border, `14px 20px`, `border-radius: 0 8px 8px 0`
- Validation strip: same shape, 12px font
- **State classes are namespaced**: `.rsw-error` (danger), `.rsw-success` (accent-green border, `--teal-dark` text), `.rsw-info` (blue), `.rsw-warning` (yellow). Never bare `.error`/`.success`/`.info` — Divi defines those (see `wordpress-divi.md`).

### Chart-adjacent stats text
13px, weight 600, `--text-secondary`. Highlight spans are **prefixed**: `.rsw-hl` (accent-green, favorable) and `.rsw-neg` (danger, drawdowns), weight 700. Middle dot (`&middot;`) between metrics.

---

## Modals & Overlays

Production two-layer pattern (consultant modal, feedback dialogs, intake gates):

```css
.rsw-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(23, 44, 58, 0.72);      /* cover-dark at 72% */
  display: flex; align-items: center; justify-content: center;
  z-index: 9998;
  opacity: 0; pointer-events: none;
  transition: opacity 0.2s;
  backdrop-filter: blur(3px);
}
.rsw-modal-overlay.rsw-active { opacity: 1; pointer-events: all; }
.rsw-modal-card {
  background: #fff; border-radius: var(--radius-lg);
  padding: 36px; max-width: 460px; width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.28);
  position: relative; max-height: 90vh; overflow-y: auto;
}
.rsw-modal-close {
  position: absolute; top: 14px; right: 16px;
  background: none; border: none; font-size: 1.375rem;
  color: var(--text-secondary); cursor: pointer;
}
.rsw-modal-step { display: none; }
.rsw-modal-step.rsw-active { display: block; }
```

- Multi-step flows switch `.rsw-modal-step` visibility (step 1 form, step 2 result/thanks)
- Field pattern: uppercase 0.75rem label + full-width select/input with teal focus border
- Submit button: full-width, teal or navy bg, `12px` padding
- Close on: × button, backdrop click (`e.target === overlay`), and Escape key — wire all three
- Note production still uses bare `.active` for modal state internally; new widgets should namespace (`.rsw-active`) per the bare-class rule

## CTA Strip

Conversion banner used for "Talk to a Consultant":

```css
.rsw-cta-strip {
  display: flex; align-items: center; justify-content: center; gap: 24px;
  background: linear-gradient(120deg, var(--navy) 0%, #2a4a6e 100%);
  border-radius: var(--radius-md);
  padding: 14px 24px; margin: 12px 0;
}
```

- Text: bold white headline + `rgba(255,255,255,0.7)` subline
- Button: teal bg, white text, `11px 28px` — this gradient strip is the **one sanctioned gradient** in the system

---

## Motion & Polish

- **House easing:** `cubic-bezier(0.23, 1, 0.32, 1)` everywhere
- **Fade-in for results:**
  ```css
  @keyframes rsw-fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .rsw-animate-in { animation: rsw-fade-in 0.35s cubic-bezier(0.23, 1, 0.32, 1) both; }
  ```
- **Tactile press:** `transform: scale(0.97)` on `:active` for every button
- **Tab indicators:** scaleX entrance (see Tabs)
- **Tooltip entrance:** translateY + scale (see Tooltips)
- Depth shadows stay subtle: shell `0 2px 16px rgba(23,44,58,0.07)`, chart area `0 1px 4px rgba(0,0,0,0.06)`, dropdown panels `0 6px 18px rgba(0,0,0,0.12)`, modals `0 20px 60px rgba(0,0,0,0.28)`

---

## Disclosures

### Placement
- **Figure/table-level:** 11px italic beneath each chart or table
- **Widget-level:** collapsible section at widget bottom

### Collapsible styling
- Toggle: 13px, weight 500, `--text-secondary`, full-width, `border-top: 1px solid var(--border-gray)`
- Arrow: **namespaced `.rsw-arrow`** (never bare `.arrow` — Divi's icon font hijacks it and renders `?`). Give it fallback fonts for the U+25B6 glyph since DM Sans lacks it: `font-family: Arial, "Segoe UI Symbol", "Apple Symbols", sans-serif;` Rotate 90deg when open, 0.2s
- Content: 11px, line-height 1.6, `--text-secondary`; h3 headings 13px weight 700 navy

---

## Accessibility

- `:focus-visible` outlines on ALL interactive elements: `outline: 2px solid var(--teal); outline-offset: 2px;` (1px offset for form fields)
- `prefers-reduced-motion` media query zeroes animation/transition durations (the one sanctioned use of `!important`)
- `cursor: pointer` on interactives, `cursor: help` on tooltip triggers
- `title` attributes on icon-only buttons
- Body text never pure black; use `--text-primary` (`#2c3641`)

---

## Responsive

Breakpoint: **768px** (production), 720px for side-by-side chart grids.

Mobile adjustments:
- `--card-pad: 10px`, base font 13px
- Header: `16px 20px` padding, h1 18px
- Tab bar: `overflow-x: auto; -webkit-overflow-scrolling: touch;` with `white-space: nowrap` tabs
- Multi-column grids → `grid-template-columns: 1fr`
- Chart height: 420px → 280px
- Number inputs: 80px → 60px
- Tables: horizontally scrollable container

---

## What NOT to do

- Bright primary backgrounds for large hero sections (the `--cover-dark` header is the exception)
- Drop shadows heavier than the sanctioned set above
- Gradients on buttons or cards (exception: the CTA strip's navy gradient)
- `transition: all` (use explicit property list)
- Hard-coded hex in component styles (use CSS custom properties)
- `!important` (use `:where()` for resets instead — see `wordpress-divi.md`; only sanctioned use is the reduced-motion guard)
- Bare state/utility classes (`.active`, `.error`, `.arrow`, `.hl`, `.neg`) — prefix everything
- Emojis in UI copy
