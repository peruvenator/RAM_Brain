# Lessons Learned: Interactive Widgets for WordPress/Divi

Guidelines for building interactive widgets embedded in WordPress using the Divi theme. Covers design system, Chart.js conventions, WordPress/Divi technical integration, article-widget integration, state management, and development workflow.

---

## 1. Widget Design System

### Color Palette

| Token | Value | Usage |
|---|---|---|
| Primary navy | `#2A3F5B` | Headings, widget titles, slider value badges, primary buttons, active states, tooltip backgrounds |
| Primary navy hover | `#1d2e44` | Primary button hover |
| Primary light hover | `#e8ecf4` | Outline button hover background |
| CTA green | `#14CFA6` | CTA buttons, "stacked" chart line |
| CTA green hover | `#10b892` | CTA button hover |
| Accent green | `#60CCA8` | Slider thumbs, secondary chart line, positive/improved values, links |
| Warning red | `#e74c3c` | Negative values, validation errors, callout borders |
| Neutral/zero | `#bbb` | Zero values, neutral diffs |
| Secondary text | `#555` | Labels, descriptions, table headers, y-axis titles |
| Tertiary text | `#777` | Subsection labels, disclosure text, meta info |
| Muted text | `#888` | Toggle labels, y-axis labels |
| Faint text | `#999` | Inactive tabs, disclaimers, slider range labels, chart disclaimers |
| Light background | `#f8f9fc` | Slider groups, result displays, callout backgrounds, section backgrounds |
| Card background | `#fff` | Widget card, modal background |
| Page background | `#f5f6fa` | Body background, CTA row background |
| Border | `#dde2eb` | Slider tracks, table header borders, select borders |
| Border subtle | `#f0f0f0` | Table row dividers, chart gridlines |
| Border light | `#eee` | Disclosure separators, tab underlines |
| Success background | `#E6F9F3` | Feasible/success badges (text `#0A8F6A`) |
| Error background | `#FDE8E6` | Infeasible/error badges (text `#C0392B`) |

Asset-specific or category-specific colors should be defined per widget. Use a saturated but not neon palette; pair each with a lighter tinted background and a darker text color for pill/badge states.

### Typography
- **Font:** DM Sans (Google Fonts), loaded via `<link>` tag with weights 400, 500, 600, 700. Fallback chain: `'DM Sans', sans-serif`.
- **Weights:** 400 body, 500 labels/secondary, 600 buttons/emphasis, 700 headings/values.
- **Sizing scale:**
  - 10px — axis labels, bar chart segment labels, source attribution
  - 11px — tooltips, fine-print labels, legend items, disclaimers
  - 12px — subsection labels, disclosure toggles, chart disclaimers, stat labels
  - 13px — section labels (uppercase), tabs, small buttons, stats table body
  - 14px — body text, input fields, standard buttons, CTA text, widget description
  - 15-16px — slider value readout, select dropdowns
  - 18px — modal headings
  - 20px — widget titles
  - 22px — widget heading (desktop)
- **Article typography:**
  - Body: `line-height: 1.75`, `max-width: 740px`, centered with auto margins
  - H1: `2.2rem`, `line-height: 1.2`, navy
  - H2: `1.4rem`, navy, `margin-top: 48px`, `margin-bottom: 16px`
- **Widget typography:**
  - Title: 20px, weight 700, navy
  - Description: 14px, `#555`, `line-height: 1.7`
  - Disclaimer: 11px, `#999`, italic

### Widget Card
```css
background: #fff;
border-radius: 12px;
box-shadow: 0 4px 24px rgba(0,0,0,0.08);
border-top: 4px solid #2A3F5B;
padding: 44px 48px;  /* reduced on mobile */
margin: 32px 0;
max-width: 900px;
```

### Spacing and Layout
- **Section gaps:** 28px between major sections
- **Border radius:** 12px for cards/modals, 10px for section backgrounds, 8px for value badges/tooltips, 6px for buttons/inputs, 4px for bar chart segments, 2px for legend swatches
- **Transitions:** 0.15s for interactive elements, 0.2s for arrow rotations, 0.3s for bar chart height animations
- **Box shadow (modal):** `0 8px 32px rgba(0,0,0,0.18)`

### Interactive Controls

**Slider Controls:** two variants, picked by context.

*Variant A — Chunky (prominent, article-embedded widgets):* use when the slider is a primary input users are meant to discover and play with — e.g. Stock/Bond mix slider, rolling-period chooser in a single-purpose explanatory widget. Gives the control visual weight.
- **Group container:** `background: #f8f9fc`, `border-radius: 10px`, `padding: 16px 24px`
- **Label row:** Flexbox with space-between — label text on left, value badge on right
- **Value badge:** `background: #2A3F5B`, `color: #fff`, `border-radius: 8px`, `padding: 4px 12px`, weight 700
- **Track:** `-webkit-appearance: none`, 8px height, `border-radius: 4px`, `background: #dde2eb`
- **Thumb:** 28px circle, `background: #60CCA8`, `border: 3px solid #fff`, `box-shadow: 0 2px 6px rgba(0,0,0,0.2)`. Hover: `transform: scale(1.15)` with 0.15s transition
- **Range labels:** 11px, `#999`, flex with space-between below the track

*Variant B — Compact (data-heavy widgets, inline chart controls):* use when the slider is a secondary chart-tweaker next to many other controls and chart real estate is at a premium — e.g. rolling-window period selector inside a chart-tab header, lookback slider next to a correlation chart. No group container.
- **Layout:** Inline flex row — `<span>Label:</span>` + `<input type="range">` + `<span class="slider-val">…</span>`, gap 12px
- **Value badge (pill):** `background: #2A3F5B`, `color: #fff`, `border-radius: 12px` (pill-shaped), `padding: 4px 12px`, font-size 13px, weight 700
- **Track:** 6px height, `border-radius: 3px`, `background: #dde2eb`
- **Thumb:** 20px circle, `background: #2A3F5B` (navy, not green), `border: 2px solid #fff`, `box-shadow: 0 1px 4px rgba(0,0,0,0.25)`. Hover: `transform: scale(1.1)` with 0.15s transition
- `margin-top: -7px` on the webkit thumb to center it on the 6px track

Both variants: style `-webkit-slider-thumb`, `-webkit-slider-runnable-track`, `-moz-range-thumb`, and `-moz-range-track` separately. Use `-webkit-appearance: none; appearance: none` on the thumb and the input itself.

**Buttons (Primary / Navy):**
- Background `#2A3F5B`, white text, 6px border-radius, no border
- Font-weight 600, 14px, DM Sans
- Hover: darken to `#1d2e44`

**Buttons (Outline):**
- White background, `#2A3F5B` text, 2px solid `#2A3F5B` border, 6px border-radius
- Hover: background `#e8ecf4`

**Buttons (CTA / Teal):**
- Background `#14CFA6`, white text, 6px border-radius
- Hover: darken to `#10b892`
- Full-width variant: 14px vertical padding, 8px border-radius, bold text
- Disabled state: gray background, `not-allowed` cursor

**Toggle Buttons:**
- Default: white background, `#2A3F5B` text, 2px solid `#2A3F5B` border
- Active: `#2A3F5B` background, white text
- Hover (inactive): `#e8ecf4` background

**Pill Toggles:**
- Rounded (20px border-radius), 2px border
- Inactive: gray border on white
- Active: colored border, pale tinted background, dark colored text
- Each category gets its own color

**Inputs:**
- 2px solid `#ddd` border, 6px border-radius
- Focus: border-color `#2A3F5B`, no outline
- Error: border-color `#e74c3c`

**Dropdowns / Selects:**
- DM Sans, 15px, `color: #2A3F5B`, `background: #fff`, `border: 2px solid #dde2eb`, `border-radius: 8px`, `padding: 10px 16px`, `width: 100%`

**Tabs:**
- Underline-style, no background
- Active: `#2A3F5B` text with matching bottom border
- Inactive: `#999` text, transparent bottom border
- Hover: `#555` text

**Section Labels:**
- Uppercase, 13px, font-weight 700, letter-spacing 0.5px, color `#555`
- Preceded by a numbered circle badge: 22px round, `#2A3F5B` background, white text

**Advanced/Collapsible Sections:**
- Small toggle button: 12px, weight 600, uppercase, letter-spacing 0.5px, `#888` text, no background/border
- Arrow indicator: unicode triangle, rotates 90deg when open via CSS transform
- Content revealed with class toggle (`.open`), not CSS transitions on height

**Tooltips (CSS-only):**
- Hidden by default, appear on `:hover`
- Dark background (`#2A3F5B`), white text, 11px, ~220px wide
- Positioned above the trigger (`bottom: 120%`), centered with `transform: translateX(-50%)`
- 6px border-radius, 8px 10px padding
- Fade in with `opacity` transition

**Modals/Overlays:**
- Fixed position, `inset: 0`, `rgba(0,0,0,0.5)` backdrop
- Content box: white, 12px border-radius, max-width ~480-520px, 32px padding
- Close button: absolute top-right, plain text "X", no border/background
- Show/hide with `.active` / `.hidden` class toggles

### Results Display

**Stat Boxes:**
- Container: `background: #f8f9fc`, `border-radius: 10px`, `padding: 16px 20px`
- Label: 12px, weight 600, uppercase, `letter-spacing: 0.3px`, color-coded to match chart line
- Number: 28px, weight 700, color-coded (or dynamic: green if positive, red if negative)
- Context text: 12px, `#999`
- Layout: Use CSS grid. For 4+ stat boxes, split into rows (e.g. 2-column grid) rather than cramming into one row that overflows on mobile
- Section header above stats: 12px, weight 600, `#555`, uppercase, `letter-spacing: 0.3px`

**Stacked Bar Charts:**
- Column-reverse flex layout so segments stack bottom-to-top
- Fixed height (~320px), ~90px wide bars
- Segments labeled with percentage if tall enough
- Include a dashed 100% reference line when total can exceed 100%
- Y-axis labels positioned absolutely

**Stats Tables:**
- `border-collapse: collapse`, no borders/background/box-shadow on the table itself
- Cell padding: `12px 14px`
- First column left-aligned, all others right-aligned
- Header: weight 700, 13px, uppercase, `letter-spacing: 0.3px`, color `#555`, bottom border `2px solid #dde2eb`
- Body rows: bottom border `1px solid #f0f0f0`
- Zebra striping: `tbody tr:nth-child(even) td { background: #f9fafb; }` — every other row gets a subtle gray tint. Helps horizontal row-tracking on wide or dense tables. Must be set on the `td`, not the `tr`, to override Divi's alternating-row defaults. Use `font-variant-numeric: tabular-nums` on numeric columns so digits align.
- Hover: `tbody tr:hover td { background: #eef1f6; }` — slightly darker than the zebra tint so the hover still registers
- Key value columns: weight 700
- Positive values: `#60CCA8`, weight 700. Negative values: `#e74c3c`, weight 700
- For comparison tables with a Difference column, color only the Difference values (green=improvement, red=degradation). Leave Core/Stacked value columns neutral so the diff stands out.

**Chart-Adjacent Stats Text:**
Short summary lines that sit directly beneath a chart and call out computed values (e.g. "Max drawdown: -24.5% · Longest drawdown: 18 months", "Stacked portfolio outperformed the Core portfolio in 68% of rolling 36-month periods", "Longest streak of annual outperformance: 5 years").
- Wrapper: 13px, weight 600, `color: #555`, `line-height: 1.7`, `padding: 6px 16px 10px`
- Highlighted value (`.hl` span): `color: #60CCA8`, weight 700. Use for favorable outcomes (stacked beats core, longer outperformance streak, smaller max drawdown).
- Negative value (`.neg` span): `color: #e74c3c`, weight 700. Use for raw drawdowns, losses, longer underperformance streaks.
- Break separate portfolios (Core vs Stacked) onto their own lines with `<br>`. Use `·` (middle dot) between metrics on the same line.

**Constraint/Status Badges:**
- Rounded (6px), padded (10px 14px)
- Feasible: green tint background, green text
- Infeasible: red tint background, red text
- Summary line (13px bold) + detail line (12px italic, slight opacity reduction)

**Callout Boxes:**
```css
background: #f8f9fc;
border-left: 4px solid #e74c3c;
padding: 20px 24px;
margin: 32px 0;
border-radius: 0 8px 8px 0;
font-size: 0.95rem;
line-height: 1.7;
```

**CTA Links:**
- Horizontal bar with gradient background (light gray tones), centered text + button layout
- Button: navy background, white text, rounded

### Responsive Design

- **Determine the appropriate mobile breakpoint per project** (typically 600-800px). Do not assume a fixed breakpoint — confirm based on the widget's layout complexity.
- Mobile adjustments:
  - Reduce widget padding (e.g. `28px 20px`)
  - Switch flex rows to columns (`flex-direction: column`)
  - Stack side-by-side layouts (chart + table) vertically
  - Reduce chart height (e.g. 400px desktop to 280px mobile)
  - Reduce heading sizes
  - Widget width: `95%` on mobile
  - Use `flex-wrap: wrap` on button groups and pill groups
- Tables: wrap in a horizontally scrollable container with `-webkit-overflow-scrolling: touch`
- Desktop tables can be replaced with card-based layouts on mobile:
  - Background `#f8f9fc`, `border-radius: 10px`, `padding: 16px`
  - Rows: flex with `justify-content: space-between`
  - Labels: weight 500, `#777`. Values: weight 700

---

## 2. Chart.js Configuration

### Setup
- **Chart.js v4** loaded via CDN: `https://cdn.jsdelivr.net/npm/chart.js@4`
- **Annotation plugin v3**: `https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3`
- `responsive: true`, `maintainAspectRatio: false`
- Chart container: relative-positioned div with explicit height (e.g. 340-400px desktop, 280px mobile)

### Theme Defaults
```javascript
// Lines
tension: 0.1,
pointRadius: 0,
pointHitRadius: 8,
borderWidth: 2.5,

// Animation
animation: { duration: 300, easing: 'easeOutCubic' },

// Tooltip
tooltip: {
  mode: 'index',
  intersect: false,
  backgroundColor: 'rgba(42,63,91,0.95)',
  titleFont: { family: 'DM Sans', size: 13 },
  bodyFont: { family: 'DM Sans', size: 13 },
  padding: 12,
  cornerRadius: 8,
},

// Legend — circle icons with dark ring + low-alpha interior fill
legend: {
  labels: {
    font: { family: 'DM Sans', size: 13, weight: 600 },
    usePointStyle: true,
    pointStyle: 'circle',
    boxWidth: 10,
    boxHeight: 10,
    padding: 20,
  }
},

// Axes
x: {
  ticks: { font: { family: 'DM Sans', size: 11 }, color: '#555', maxTicksLimit: 12 },
  grid: { display: false },
  border: { color: '#000', width: 1.5 },
},
y: {
  ticks: { font: { family: 'DM Sans', size: 11 }, color: '#555' },
  grid: { color: '#f0f0f0' },
  border: { color: '#000', width: 1.5 },
  title: { font: { family: 'DM Sans', size: 12, weight: 600 }, color: '#555' },
},

// Layout
layout: { padding: { left: 10 } },
```

**Legend icon convention — dark ring, light interior.** With `pointStyle: 'circle'` and `usePointStyle: true`, Chart.js renders the legend swatch as a circle using the dataset's `borderColor` for the outline and `backgroundColor` for the fill. To get the "dark ring on a lighter tint of the same color" look, each line-chart dataset should be set up as:
```javascript
{
  borderColor: '#2A3F5B',                          // full-strength line color
  backgroundColor: 'rgba(42, 63, 91, 0.25)',       // ~25% alpha of the line color
  borderWidth: 2.5,
  fill: false,
  pointBorderColor: '#2A3F5B',                     // matches borderColor
  pointBackgroundColor: 'rgba(42, 63, 91, 0.25)',  // matches backgroundColor
}
```
If `fill: true` and you want a visible area fill, use a lower alpha (~0.12) for `backgroundColor` instead — but then the legend swatch interior will be very faint. For line charts with no area fill, 0.25 is the sweet spot: visible legend fill without muddying the plot.

For bar and scatter datasets, the dataset's `backgroundColor` fills both the bars/points and the legend circle, so the dark-ring-light-fill convention doesn't apply — just use the full-strength color for both.

**Time-series x-axis formatting.** When the category axis holds ISO date labels (e.g. `2024-03-31`), reformat them to `MM/YYYY` and rotate the labels so they fit on dense axes:
```javascript
x: {
  type: 'category',
  ticks: {
    maxRotation: 35,
    minRotation: 35,     // force the rotation so label density doesn't toggle it
    autoSkip: true,
    maxTicksLimit: 12,
    callback: function(v) {
      const l = this.getLabelForValue(v);
      if (!l) return '';
      const parts = l.split('-');
      return parts.length >= 2 ? parts[1] + '/' + parts[0] : l.substring(0, 4);
    },
  },
  grid: { display: false },
}
```
Apply this to growth-of-$1, drawdown, rolling-returns, and rolling-correlation charts. Do NOT apply to calendar-year bar charts (labels are already just `YYYY` strings — keep those at 45° rotation without the callback).

### Color Assignments
When a chart has multiple lines, assign colors from the palette in a consistent order:
1. Navy `#2A3F5B` — benchmark / primary reference
2. Green `#60CCA8` — secondary / alternative strategy
3. Steel blue `#5B8DB8` — stacking / lump-sum variant
4. Slate `#8896AB` — funding / tranche variant
5. Additional lines: pull from a muted, professional palette (no bright primaries)

For bar chart segments, typical assignments:
- Stocks: `#456998` (muted steel blue)
- Bonds: `#7B9EC2` (lighter complement)
- Alt segments: `#14CFA6` (green), `#F5A623` (amber), `#E06D5E` (coral), `#D4AF37` (gold)

### Line Charts
- Primary line: navy `#2A3F5B`, `fill: false`
- Secondary/accent line: green `#60CCA8`, optionally with gradient fill from `rgba(96,204,168,0.25)` to `rgba(96,204,168,0.02)`
- Use `order` property to control z-layering of datasets
- Dashed lines for alternative scenarios: `borderDash` arrays like `[8,4]` or `[6,3]`
- Null data points to start a line partway through: set array values to `null`
- Logarithmic scale as an optional toggle (swap `type: 'linear'` to `type: 'logarithmic'`)
- Background fills: low-alpha versions of line colors (e.g. `rgba(69,105,152,0.08)`)

### Annotations
- Baseline reference lines: solid black, `borderWidth: 1`
- $100 reference line (growth charts): `{ type: 'line', yMin: 100, yMax: 100, borderColor: '#000', borderWidth: 1 }`
- Vertical event markers: dashed line, `borderColor: '#999'`, `borderDash: [6,4]`, label at `position: 'start'` or `'end'`

---

## 3. WordPress / Divi Technical Integration

### Architecture: Single-File HTML
- The widget (and optionally the full article) is a single self-contained HTML file — all CSS in a `<style>` block, all JavaScript inline.
- External dependencies loaded via CDN `<link>` and `<script>` tags (Google Fonts, Chart.js, jsPDF if needed).
- No build step. The file runs as-is in a browser.
- All data is embedded directly in JavaScript (no external fetch calls). For moderate datasets (up to a few MB), base64-encode and embed, then decode at runtime into typed arrays. This eliminates CORS issues, fetch failures, and CDN dependencies.

### Embedding in Divi
- Use a Divi **Code Module** to paste the HTML content.
- When embedding inline, strip `<html>`, `<head>`, `<body>` wrappers and include only the `<style>`, `<script>` tags, and the widget `<div>`.
- Google Fonts `<link>` tag goes above the `<style>` block, outside the namespaced container. If Divi strips it, add via the theme's header injection settings.
- WordPress's visual editor may strip or mangle inline `<style>` and `<script>` tags. Always use the Code/Text editor or a Code Module.
- WordPress may add `<p>` and `<br>` tags around raw HTML. Wrapping everything in a single container div helps prevent this.

### CSS Namespacing (Critical)
WordPress and Divi inject aggressive global styles that target bare element selectors (`input`, `label`, `button`, `select`, `h2`, `p`, `table`, etc.) with high-specificity selectors. Without namespacing, the widget will inherit Divi's styles and break.

1. **Root namespace:** Wrap the entire widget in a single root element with a unique ID (e.g. `#rs-optimal-stack`) or class (e.g. `.rst-article`).
2. **Use a consistent class prefix** for all internal classes (e.g. `rsw-` or `rst-`). All element IDs must also be prefixed to avoid collisions.
3. **Universal reset inside the namespace:**
   ```css
   #widget-id *, #widget-id *::before, #widget-id *::after {
     box-sizing: border-box !important;
   }
   ```
4. **Every single CSS rule** must be prefixed with the namespace. No bare element selectors, no bare class selectors. Always `#widget-id .classname`, never `.classname` alone.
5. **Scope selectors as tightly as possible** (e.g. `#widget-id .input-group input` rather than just `#widget-id input`) to minimize unintended side-effects while still winning the specificity battle.
6. **Keyframe animations** must be namespaced (e.g. `@keyframes rs-optimal-spin`, not `@keyframes spin`) to avoid conflicts.

### The `!important` Rule
**Default to `!important` on all CSS properties inside the widget namespace.** Divi uses high-specificity selectors with its own `!important` declarations on elements like headings, tables, form elements, and more. Trying to be surgical about which properties need `!important` leads to whack-a-mole debugging. Since the namespace scoping prevents any bleed into the rest of the page, the `!important` declarations are contained and harmless.

Form elements (`input`, `label`, `button`, `select`, `textarea`) need the heaviest overrides. Labels are particularly tricky — Divi styles them with borders, backgrounds, padding, and box-shadows. Override all of these explicitly.

**Properties Divi commonly overrides** (proactively set `!important` on all of these for form elements):
- `font-family`, `font-size`, `font-weight`, `color`
- `letter-spacing`, `text-transform`
- `line-height`, `height`, `min-height`
- `padding`, `margin`
- `border`, `border-radius`, `border-color`
- `background`, `box-shadow`
- `width`, `max-width`
- `-webkit-appearance`, `appearance`
- `outline`

**Additional Divi resets:**
- Headings: explicitly reset `text-transform: none !important` and `letter-spacing: normal !important` (Divi often forces uppercase)
- Tables: strip Divi's backgrounds, borders, box-shadows, and alternating row colors with explicit `none !important` on `table`, `th`, `td`, and `tbody tr:nth-child(even) td`
- Font declarations must be repeated on `button`, `input`, `select` since browsers apply their own defaults to form elements

### JavaScript Isolation
- Wrap all JS in an IIFE `(function(){ ... })()` to avoid polluting the global scope.
- If using Web Workers, create them from inline Blob URLs rather than external files (external `.js` files may not resolve correctly inside WordPress).
- Scope all DOM queries to the root element: `document.querySelector('#widget-id .target')` or cache a root reference. Avoid generic selectors.

### Performance
- WordPress pages are often heavy. Minimize DOM manipulation and avoid layout thrashing.
- For computationally intensive work, use Web Workers to keep the UI responsive.
- Lazy-initialize expensive resources (e.g. don't spin up workers until the user interacts with the widget).

### Testing
- **Always test in the actual WordPress/Divi environment**, not just standalone. Divi injects styles that can break layouts in ways that don't reproduce locally.
- Check both desktop and mobile in the Divi preview and on actual devices.
- Test slider interactions and chart rendering after embedding — Divi's JS can occasionally interfere with event listeners.
- Verify that Divi's visual builder doesn't strip or reformat the HTML (Code Modules are generally safe, but verify).

---

## 4. Disclosure Styling

### Placement
- **Figure-level disclosures** sit directly beneath each figure in small muted text (11px, italic, `#999`).
- **Table-level disclosures** sit directly beneath each table.
- **Widget-level disclosures** go at the bottom of each widget in a collapsible section.
- **Full article disclosures** go at the end of the post in a collapsible section.
- Both the article and embedded widgets need their own disclosure sections.

### Styling
- Collapsible toggle: separated from main content by `border-top: 1px solid #eee` with `margin-top: 32px`, `padding-top: 20px`.
- Toggle button: DM Sans, 12px, weight 600, uppercase, `letter-spacing: 0.5px`, `#888` text, no background/border.
- Arrow indicator: unicode triangle, rotates 90deg when open.
- Content text: 11px, `line-height: 1.6`, `#777`, `text-align: justify`.
- Section headings within disclosures: weight 600, `#555`, `margin-top: 16px`.

---

## 5. Article + Widget Integration

### Layout
- The article and widget live inside the same namespaced root container.
- The article comes first; the widget appears at the natural point in the narrative where the reader is ready to explore interactively.
- Provide a "skip to tool" affordance early in the article for returning readers who want to jump straight to the widget. Style it as a subtle horizontal bar (light background, centered text + button), not a garish banner.
- When the widget is embedded mid-article, remove vertical margin between article bottom and widget top so they feel like one continuous experience.

### Widget Introduction
- The widget should feel like a natural extension of the article's argument, not a bolted-on appendix.
- Briefly restate the key parameters the reader will be adjusting and why those parameters matter (referencing the preceding analysis).

### Widget Anatomy
Each widget follows this structure:
1. Widget container (`.rst-widget` or namespaced equivalent)
2. Title — concise, descriptive name
3. Description — 1-2 sentences explaining what the reader should look for
4. Compliance disclaimer
5. Controls (sliders, dropdowns) in grouped containers
6. Chart canvas in a sized container div
7. Stat boxes in a grid layout below the chart
8. Source attribution — data source and methodology notes

### Deliverable Structure
1. **`<head>`**: charset, viewport, Google Fonts link, Chart.js CDN, annotation plugin CDN, `<style>` block
2. **`<body>`**: Single namespaced wrapper containing:
   - Title, subtitle, meta (author/date)
   - Article prose (H2 sections with body paragraphs)
   - Widgets interspersed at appropriate points in the narrative
   - Footer / disclosures section (collapsible)
3. **`<script>`**: All widget logic in a single inline script block, using IIFEs or scoped functions

---

## 6. State Management & Special Patterns

### State Persistence
- **localStorage** for persisting user identity across sessions (keyed by a single constant)
- **URL query parameters** for shareable state — encode the full widget configuration into search params so a link reproduces the exact view
- Parse URL params on load (before any rendering) and apply them to set initial widget state
- State is kept in plain JavaScript variables/objects — no framework, no reactive state library

### Intake Gate Pattern
- Widget renders blurred (`filter: blur(6px); pointer-events: none`) behind a modal overlay
- User fills out the intake form, which stores data to localStorage and removes the blur
- Returning visitors (detected via localStorage) skip the gate
- "Not you?" link clears localStorage and re-shows the gate
- Gate form validation: disable submit button until all required fields are filled; enable via input event listeners

### HubSpot Integration
- Form submissions go to the HubSpot Forms API
- Fire-and-forget: submissions use `fetch()` with `.catch(function() {})` — never block the UX on form submission success/failure
- Fields use HubSpot's `objectTypeId` / `name` / `value` format

### PDF Generation (jsPDF)
- jsPDF v2 loaded via CDN
- Landscape letter orientation
- Charts rendered to off-screen canvases, exported as JPEG (0.92 quality) or PNG, then placed as images
- Text uses jsPDF's built-in fonts (no custom font embedding)
- Colors set with `doc.setFillColor(r, g, b)` using decimal RGB values
- Multi-page support with `doc.addPage()`

---

## 7. Build & Development Workflow

### Iterative Process
- Start with the article prose and overall structure.
- Build widgets one at a time, testing each before moving to the next.
- Embed data directly in JS — precompute as much as possible to keep the runtime logic simple.
- After all widgets are working, do a styling pass to ensure consistency across all widgets.
- Test in a browser at multiple viewport widths (desktop, tablet, mobile).

### Data Pipeline
- Analysis scripts (Python) generate figures and precomputed data.
- A build script assembles the final HTML by combining the template with embedded data.
- Keep analysis scripts separate from the widget code. The widget should only consume precomputed outputs, never run analysis at runtime.
- Raw CSV data should be processed offline; the final HTML should not fetch or parse CSVs.
- When working with financial time series, be explicit about whether values are returns or levels, and whether returns are arithmetic or geometric.

### Reproducibility
- Keep a master "run all" script that regenerates all figures and data from source.
- Pin random seeds or save simulation indices so results are reproducible.
- Store shared utilities (data loading, common statistics) in a shared module rather than duplicating across scripts.

### Common Pitfalls
- Accidentally reverting widget logic when editing surrounding prose (or vice versa). Keep edits surgical.
- Formulas getting silently changed during refactors — always verify financial calculations after any code change.
- Dead code accumulating from removed widgets — clean up all associated JS, CSS, and data when removing a widget.
- Stat box layouts overflowing on mobile — test grid layouts at narrow widths and split into multiple rows if needed.
- Chart.js annotation plugin not loading — make sure both `chart.js@4` and `chartjs-plugin-annotation@3` CDN scripts are included.

### Accessibility
- Use semantic HTML where possible.
- Ensure sufficient color contrast.
- Add `title` attributes to interactive buttons.
- Use `cursor: pointer` on interactive elements.
- Animations should be subtle: 0.15s for interactive feedback, 0.3s for layout changes. Nothing flashy.
