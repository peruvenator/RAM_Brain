# Funding Problem Widget

Interactive single-file widget that extends "The Funding Problem" interactive from the RSSB blog post (*How RSSB Helps Create Room for Diversification Without Reducing the Core*). Goal: take the existing top-of-post slider widget as the base and add a couple more capabilities.

## Top Priority

Build a self-contained, Divi-embeddable HTML widget that visualizes the funding problem of diversification and how RSSB resolves it. Must match the existing blog's visual language exactly so it can drop into the same post (or a future one) without restyling.

## Files

- `funding-problem-widget.html` -- standalone working baseline, extracted verbatim from the blog. This is the iteration surface. Open in a browser to preview.
- Source blog: `../rssb-product-blog (1).html` (the team member's post; do not edit unless asked)

## What the base widget does (`#rssb-fp2`)

The widget the user wants to clone-and-extend. Currently it shows ONLY the traditional funding problem (no RSSB path yet -- that lives in the separate "Build Your Stack" widget further down the post).

- **Benchmark selector**: preset buttons 0/100, 20/80, 40/60, 60/40 (default), 80/20, 100/0 (equity/bond)
- **Alternatives slider**: 0-50%, step 1
- **Stacked bar chart**: two bars (benchmark vs new portfolio), Equities / U.S. Bonds / Alternatives. Proceeds for the alt allocation are raised by selling equities and bonds in proportion to benchmark weights, so the core shrinks.
- **Portfolio Changes**: Sold (equities/bonds) vs Bought (alternatives)
- **Historical Hurdle Rate**: growth of $100 in the selected benchmark (log scale), with a CAGR/yr badge. Any alt must beat this to add value.
- **Disclosures**: collapsible

## Data & methodology (embedded, no fetch)

- Two hardcoded monthly index series, base 100, Dec 1987 - Dec 2025 (~458 points):
  - `GEQ` = Global Equities = MSCI ACWI Index
  - `USB` = U.S. Bonds = Bloomberg U.S. Aggregate Bond Index
  - Source: Bloomberg. Growth of $100, monthly.
- Hurdle blend: monthly rebalanced to selected eq/bond weights; `computeBlend()` chains monthly returns. CAGR uses 38-year horizon (`Math.pow(cum, 1/38)`).
- Funding math (`compute()`): sells bonds first up to the bond-weight share of the alt, remainder from equities.

## Brand conventions (match the blog exactly)

- Font: DM Sans (Google Fonts)
- Colors: ink `#2A3F5B`, equities `#323A46`, bonds `#3A6A9C`, alternatives/accent green `#60CCA8`, slider track `#dde2eb`, panel bg `#f8f9fc` / `#f5f6fa`, sell red `#C0392B`/`#e74c3c`, buy green `#0A8F6A`/`#60CCA8`
- Card: white, `border-radius:12px`, `box-shadow:0 4px 24px rgba(0,0,0,0.08)`, `border-top:4px solid #2A3F5B`
- Every rule is `!important` and namespaced under the widget id -- this is Divi-defensive. Keep that pattern.
- Charts: Chart.js v4 + chartjs-plugin-annotation v3. `animation` short, custom inline label plugins draw % on bars.
- Disclaimers required on anything illustrative ("For illustrative purposes only", "Past performance is not indicative of future results", diversification language). See the `.fp2-disc-content` block for the full approved text.

Relevant skill: **RS_widget_design** (Chart.js + vanilla JS single-file widgets for returnstacked.com). Relevant writing skill: **rs-writing-style** (em-dash ban, we/our, hedging language) for any copy.

## Planned additions ("a couple more things")

TBD with Rodrigo -- ideation in progress. Candidate directions captured during the first session:
- (to be filled in)

## Conventions for this project

- Single file, no build step, no external data files. All data inlined.
- Test by opening the HTML directly in a browser.
- Keep the widget id namespace and `!important` pattern so it stays Divi-safe.
- New widget must be droppable into the existing post alongside (or replacing) the current `#rssb-fp2` block.
