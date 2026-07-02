---
name: RS_widget_design
description: Build interactive single-file widgets (Chart.js + vanilla JS) for embedding in WordPress/Divi using Return Stacked brand conventions. Use when creating portfolio visualizers, interactive calculators, chart-driven explainers, or any self-contained HTML widget that will live on returnstacked.com, returnstackedetfs.com, or a ReSolve site. Covers design tokens, control specs, Chart.js defaults, and Divi-defensive CSS patterns proven on the production Portfolio Visualizer.
---

# RS Widget Design

Build and maintain interactive single-file HTML widgets (Chart.js + vanilla JS) for embedding in WordPress/Divi pages using Return Stacked brand conventions.

## When to Use

- Creating a new interactive widget (portfolio calculator, chart explorer, fee visualizer, allocation slider, etc.)
- Adapting an existing widget to a new topic while keeping the design language
- Debugging CSS collisions between a widget and Divi's global styles
- Reviewing a widget for brand, accessibility, or Chart.js consistency
- Any single-file HTML deliverable destined for returnstacked.com, returnstackedetfs.com, or a ReSolve Divi page

## How It Works

Before writing any code, read the relevant reference file(s) based on the task:

| Task | Read |
|------|------|
| New widget from scratch | All four reference files + open the starter template |
| Styling / token question | `references/design-system.md` |
| Chart.js config / type | `references/chartjs.md` |
| Divi breakage / CSS collision | `references/wordpress-divi.md` |
| Large/complex widget breaking in Divi (inline JS mangled, `:where()` losing, blank charts) | `references/wordpress-divi.md` → "Scaling Up: When the Single-File Model Breaks" |
| State, persistence, embedding, PDF | `references/state-and-workflow.md` |

**Always start from the starter template** (`templates/widget-starter.html`) rather than writing markup from scratch. It already has the `:where()` Divi defense, CSS custom properties, Chart.js defaults, IIFE scaffold, and one working example of each control type.

## Quick Reference

### Core conventions
- **Font:** DM Sans (400/500/600/700) via Google Fonts CDN
- **Branded header:** Return Stacked widgets open with a dark `--cover-dark` header band with the white logo (base64 data URI) — pattern in `references/design-system.md` → "Branded Header", markup in the starter template
- **Namespace prefix:** pick one per widget (`.rsw-` for generic; `.rsv-` is taken by the production visualizer; `.rst-` for article, etc.) — apply to every class and ID, **including state classes** (`.rsw-active`, `.rsw-open`, not bare `active`/`open`)
- **Brand tokens:** CSS custom properties on the widget root, never raw hex in component styles
- **Divi defense:** `:where()` selectors for bare element resets (NOT blanket `!important`). For a LARGE widget this is necessary but NOT sufficient — add an ID-scoped `!important` override block for the globals Divi punches through (`input{width:100%}`, button styling, `p` spacing). See `references/wordpress-divi.md`.
- **Numbers:** `font-variant-numeric: tabular-nums` on root + any numeric cell
- **Charts:** Chart.js v4 + annotation plugin v3, `responsive: true`, `maintainAspectRatio: false`, explicit container height
- **JS:** wrapped in IIFE, all DOM queries scoped to widget root
- **Accessibility:** `:focus-visible` outlines, `prefers-reduced-motion` media query

### Color tokens (abbreviated)
```
--navy: #2a3f5b        (primary brand, headings, compact buttons)
--teal: #14cfa6        (CTA buttons, active tabs, focus rings, "stacked" line)
--cover-dark: #172c3a  (branded header bg, PDF cover, overlay tint)
--accent-green: #60cca8  (positive values, slider thumb)
--blue: #3a6a9c        (secondary buttons)
--text-secondary: #625c6d  (labels — NOT #555)
--danger: #e74c3c      (negative values, errors)
```
Full palette in `references/design-system.md`. Note: `#323A46` is the first *chart* color, not the navy token.

### File structure for a new widget
```
<project>/
├── widget.html          # Deliverable — single file, all inline
├── build_widget.py      # Optional: if generating from data
└── data/                # Optional: source data for build script
```

## Starter Template

Location: `.claude/skills/RS_widget_design/templates/widget-starter.html`

Copy this as the starting point. It includes:
- Full namespaced root + `:where()` Divi resets
- All brand CSS custom properties (production-canonical set incl. `--cover-dark`, `--section-gray`)
- Branded header block with logo slot (dark band, negative-margin full-bleed)
- Working examples: chunky slider, compact slider, pill toggles, tab bar, primary/outline/CTA/compact buttons, stat grid, results table, tooltip, callout, disclosures
- Namespaced state classes throughout (`.rsw-active`, `.rsw-open`, `.rsw-positive`, `.rsw-arrow`) and `rsw-fade-in` results animation
- Chart.js v4 setup with time-series x-axis callback
- IIFE JS scaffold with debounced recompute, state object, event wiring
- Mobile responsive breakpoint (<=720px)

## Reference Implementation

The **Portfolio Visualizer Widget** (`projects/portfolio-visualizer-widget/RS_advanced_visualizer_widget.html`) is the production reference. It exercises nearly every pattern in this skill — 5 portfolios, 5 chart types per portfolio, comparison panels, custom data upload, PDF export, intake gate, localStorage. When in doubt on a pattern, check how it's done there.

Project CLAUDE.md: `projects/portfolio-visualizer-widget/CLAUDE.md` — covers the build pipeline (`build_widget.py`), compute engine, known gotchas.

## Source Material

The original design document that seeded this skill: `projects/portfolio-visualizer-widget/Branding_for_widget_design.md`. It remains unchanged as the historical reference. Where the skill reconciles doc vs. production-widget drift, the skill reflects what's actually shipping (notably: `:where()` over `!important` for Divi defense).

## Deliverable Checklist

Before shipping a widget:

- [ ] Namespaced root; every class/ID carries the prefix — **including modifiers/children** (`active`, `arrow`, `error`, not bare). Sweep `class="…"` for un-prefixed tokens Divi could hijack (see `references/wordpress-divi.md` → "bare-modifier-class trap")
- [ ] `:where()` resets for bare elements (h1-h6, p, a, button, input, label, table, th, td, img)
- [ ] CSS custom properties for all colors and radii
- [ ] `isolation: isolate` on root
- [ ] DM Sans loaded via `<link>` before `<style>`
- [ ] Chart.js + annotation plugin CDNs both included if annotations used
- [ ] `chart.destroy()` called before any rebuild
- [ ] JS wrapped in IIFE, DOM queries scoped to root
- [ ] `font-variant-numeric: tabular-nums` on stats and table cells
- [ ] `:focus-visible` outlines + `prefers-reduced-motion` media query
- [ ] Mobile breakpoint tested at widget-appropriate width (600-800px typical)
- [ ] Disclosures collapsible at widget bottom
- [ ] Tested in actual Divi Code Module on staging — not just standalone
- [ ] **Python-generated?** `node --check` passes on the generated JS after EVERY build (single-backslash `\n` in an f-string kills the whole widget — see `references/state-and-workflow.md` → f-string gotchas)
- [ ] **Large widget?** Also run the extended checklist in `references/wordpress-divi.md` (external JS file, `wp_enqueue` CDN deps, PHP shortcode, ID-`!important` overrides, z-index, glyph fallbacks)
