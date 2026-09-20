# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# RS Advanced Visualizer Widget -- Return Stacked Explorer

## Project Overview

An interactive single-file web application that lets advisors and investors build up to 5 custom portfolios with return stacking overlays, compare them side-by-side, and analyze risk/return characteristics. Supports 55+ asset classes, custom CSV data uploads, advanced fee configuration, and saved portfolio presets. Designed for embedding on returnstacked.com (Divi theme).

---

## MANDATORY: Developer Handoff After Every Change

**After any change to `build_widget.py` or any file under `data/`, you MUST run the build on the `web-authenticated` branch before the session ends:**

```
py -3.11 build_widget.py
```

This single command regenerates all three developer handoff files automatically:

| File | Goes to |
|------|---------|
| `rsv_widget_embed.html` | WP plugin directory (same folder as `rsv-portfolios.php`) |
| `rsv_widget.js` | Server at `/wp-content/uploads/rsv-widget/rsv_widget.js` |
| `RS_advanced_visualizer_widget_web.html` | Local test only -- never deployed |

Also check `backend/rsv-portfolios.php` if any PHP-side changes were made (REST routes, shortcode, enqueue logic).

**Never hand off a stale build.** The `.html` file in the repo is what gets deployed -- if the build hasn't run, the developer will deploy old code.

---

## Commands

```bash
# Build the widget HTML (output filename depends on branch — see Branches table)
py -3.11 build_widget.py

# Re-extract index data from the source Excel workbook
py -3.11 extract_data.py

# Regenerate ticker info JSON after editing the Bloomberg mapping in gen_ticker_info.py
py -3.11 gen_ticker_info.py

# QC: validate widget math against Excel (run before/after any compute logic change)
py -3.11 qc_stacked_portfolio.py

# Export all embedded series + calendar-year returns to Excel (useful when adding/renaming assets)
py -3.11 export_all_data.py

# Regenerate the Bloomberg ticker reference workbook used by sales/marketing
py -3.11 build_ticker_map.py
```

There are no tests, linter, or dev server. The build output is a self-contained HTML file — open it directly in a browser to test.

---

## Key Files

| File | Purpose |
|------|---------|
| `RS_advanced_visualizer_widget.html` | **The entire app** -- single ~1.9MB HTML file with inline CSS, JS, and embedded data (local/Divi version) |
| `RS_advanced_visualizer_widget_web.html` | Web-authenticated version (output of `web-authenticated` branch) -- see Phase 8 |
| `backend/rsv-portfolios.php` | WordPress plugin for server-side portfolio storage (Phase 8) |
| `build_widget.py` | Python script that generates the HTML from extracted data |
| `extract_data.py` | Extracts index data from `Return_Stacking_Visualizer.xlsx` |
| `gen_ticker_info.py` | Generates `data/ticker_info.json` from the in-script Bloomberg ticker mapping |
| `build_ticker_map.py` | Builds an Excel reference mapping widget names <-> source index <-> Bloomberg ticker |
| `export_all_data.py` | Exports all embedded series + name mapping + calendar-year returns to Excel for review |
| `qc_stacked_portfolio.py` | QC workbook that replicates `computePortfolio()` for 100% ACWI core + 100% MFT stack with all formulas exposed (used to validate widget math against Excel) |
| `data/` | Extracted JSON data files, base64 logos/fonts, and the disclosures bundle |
| `Branding_for_widget_design.md` | Detailed brand/design reference used during the `ui-polish` redesign |
| `Simple widget.html` | Reference: simpler version with PDF export (used as design reference) |
| `return-stacking-report.pdf` | Reference: example PDF output for Phase 6 |
| `Return_Stacking_Visualizer.xlsx` | Source Excel workbook with all index time series |
| `Futures yield.html` | Source for Futures Yield (Carry) data series |

## Architecture

**Build process:** `py -3.11 build_widget.py` generates the output HTML (filename set by `OUTPUT_FILE` at the top of the script — differs per branch, see Branches table) from:
- `data/indices_compact.json` -- 55+ index time series (compressed, sparse format)
- `data/index_map.json` -- asset name to index column mapping with metadata
- `data/disclosures.json` -- legal text + 70+ index definitions
- `data/custom_assets.json` -- placeholder for custom asset data (legacy/vestigial; live custom assets come from the intake flow)
- `data/intake_engine.js` -- flexible custom-data parsing engine (csv/tsv/xlsx/paste, flexible dates, price/return detection); injected raw into the build
- `data/ticker_info.json` -- widget name -> Bloomberg ticker / provider lookup (consumed by the asset-info tooltips)
- `data/logo_ps_white_uri.txt` / `logo_ps_black_uri.txt` -- Return Stacked Portfolio Solutions logos (base64 data URI)
- `data/dmRegular.txt` / `dmBold.txt` / `dmItalic.txt` / `dmBoldItalic.txt` -- DM Sans font faces embedded as base64 (used in PDF export so jsPDF doesn't depend on a network font)

**CRITICAL:** `build_widget.py` uses Python f-strings for the entire HTML. All JS curly braces must be doubled (`{{` and `}}`). Watch for duplicate `let`/`const` declarations in the same method scope -- this caused a full widget blank-out once.

**Divi CSS Defense (ui-polish branch):** The widget uses `:where()` selectors for bare element resets (e.g., `.rsv-widget :where(button)`) so Divi's global styles don't bleed in. The `:where()` pseudo-class zeros out specificity, ensuring any `.rsv-*` component class always wins. Do NOT change these to plain `.rsv-widget button` -- that caused buttons to disappear because the reset's specificity (class + element) beat the component class (class only).

**Stats engine:** Single top-level `computeStats(returns, dates, rangeStart, rangeEnd)` function handles all 17 metrics with consistent Treasury Bill risk-free rate lookup and short-sample guards. All callers (initial compute, date filtering, comparison panels) use this one function.

**Libraries (CDN):**
- Chart.js v4 -- all interactive charts
- jsPDF v2 -- PDF export

**Data:** 55+ index monthly time series embedded inline as a compact JSON object. Dates array shared across all series. Each series stores `{start: index, values: [...]}` to skip leading nulls.

**Asset dropdown "Popular" groups** (defined in `renderAssetSelect`, assets moved out of original categories):
- Equities (Popular): U.S. Large Cap Equities, International Equities, Global Equities
- Fixed Income (Popular): U.S. Treasury Ladder, U.S. Core Fixed Income, Intermediate-Term U.S. Treasuries, Long-Term U.S. Treasuries
- Alternatives (Popular): Managed Futures CTA, Managed Futures Trend, Futures Yield (Carry), Gold, Merger Arbitrage, Systematic Global Macro, Risk-Weighted Gold/Bitcoin

---

## Brand Assets

Shared brand assets at `../../references/brand-assets/return-stacked/`

**Colors (CSS custom properties on `.rsv-widget`):**
- `--teal: #14cfa6` -- primary accent
- `--navy: #323a46` -- dark text, chart color 1
- `--blue: #3a6a9c` -- secondary accent
- `--text-primary: #2c3641`
- `--text-secondary: #625c6d`
- `--cover-dark: #172c3a` -- header background
- `--section-gray: #f0f1f1`

**Chart color progression (per-asset):** `#323A46`, `#3A6A9C`, `#7DA5CE`, `#14CFA6`, `#0C7C64`, `#EBE96A`, `#FFE885`, `#366390`, ...

**Font:** DM Sans from Google Fonts CDN (400, 500, 700)

**Logo:** Return Stacked Portfolio Solutions white logo embedded as base64 in header

---

## Features

### Portfolio Input (5 tabs)
- Editable names, enable/disable checkboxes
- Core allocation (must sum to 100%) + Stack/Overlay allocation
- **Excess return mode:** core can be empty (0%) when stack overlays exist -- analyzes overlay excess returns without a core portfolio. Core series hidden from all charts/tables; column labeled "Excess Return". Scaled Stack Blend and outperformance charts hidden in this mode.
- Asset class dropdown with "Popular" groups at top (Equities, Fixed Income, Alternatives) followed by full categories
- Already-selected assets greyed out (disabled) in dropdown to prevent duplicates
- Vertical stacked allocation bar with 100% dashed line
- Reset Portfolio button: clears name, allocations, and fees to default
- Saved Portfolios dropdown (localStorage) with 3 non-deletable defaults; saves core, stack (with feeBp/financingBp), and advisory fee

### Fee Configuration
- Portfolio-level "Annualized Advisor Fee" in basis points
- Per-overlay-asset Fee (bp) + Financing (bp) in collapsible "Advanced Fee Configuration" (located below Calendar Year Returns table in results section)
- Advanced fee config (feeBp, financingBp) is persisted when saving portfolios
- Most Alternative assets greyed out as "net of fees" (exceptions: Risk Parity 10/12/15%, Global Stock/Bond Momentum, Risk-Weighted Gold/Bitcoin)
- Financing = spread above T-bills (base T-bill deduction is automatic)
- Fee display: `(p.fee / 100).toFixed(2)` converts basis points to percent (50bp shows as "0.50%")

### Auto-Compute
- Debounced 500ms auto-compute on any input change
- Preset portfolios auto-computed on page load

### Date Range Controls
- Per-portfolio date range bar below Summary Statistics title
- Comparison date range bar (shared) below each Portfolio Comparison panel title
- Controls: Year dropdown, From/To date pickers (auto-apply on change), Reset button, quick buttons (3M, 6M, YTD, 1Y, 3Y, 5Y, 10Y, 20Y, All)
- Changing date range recomputes all 17 stats metrics + charts for that range
- Chart tab selection preserved when date range changes (doesn't reset to Return & Risk)
- `computeStats()` -- unified full 17-metric computation for any date range
- `_getFilteredView()` -- creates a filtered result object for chart rendering

### Per-Portfolio Charts (5 tabs)
1. **Return & Risk** -- dual scatter (return vs vol + return vs max DD), benchmark frontier, 10% grace padding
2. **Growth & Drawdowns** -- growth of $1 (log/linear) + drawdown with stats text
3. **Rolling Returns** -- debounced 150ms period slider, outperformance %, difference chart (blue/red shading)
4. **Calendar Year** -- returns + max DD bars, outperformance streaks; Calendar Year Returns table sorted most recent year first
5. **Scaled Stack Blend** -- decomposed streams, correlation, rolling correlation with debounced lookback slider

### Action Buttons (step 4 row)
- **Save Portfolio** -- saves to localStorage AND downloads a JSON backup file. Tooltip: "Saves to your browser and downloads a backup file. Use Import to restore if browser data is cleared."
- **Import Portfolio** -- loads one or multiple `.json` portfolio files from disk into saved presets. Prompts on duplicate names. Tooltip: "Load portfolio files (.json) from your computer."
- **Custom Data** -- navigates to the Custom Data Upload panel

### Portfolio Comparison (dropdown menu, right side of tab bar)
- "Portfolio Comparison" label hidden when dropdown is open (only shows options)
- Each panel has a large 22px page title
- **Risk & Return** -- three tables (Core, Stacked, Difference) + scatter charts, all over COMMON date range
  - Core/Stacked tables: black font (no color coding)
  - Difference table: green for improvement (higher returns, lower risk), red for degradation; Tracking Error always black
  - All table values centered (metric labels left-aligned)
  - Includes: Cumulative Return, Annualized Return, Volatility, Max Drawdown, Sharpe, Sortino, Tracking Error
- **Advanced Statistics** -- 17 risk metrics across all portfolios
- **Tracking Error** -- NxN matrix for stacked portfolios, common date range
- Chart instances properly destroyed when switching between comparison panels

### Custom Data Upload (via "Custom Data" button)
- **Flexible intake** (rewritten 2026-07): accepts `.csv` / `.tsv` / `.txt` / `.xlsx` files (drag-drop or browse) and paste-from-spreadsheet. Up to 10 series per import.
- **Parsing engine** lives in `data/intake_engine.js`, injected verbatim into the build (raw JS, NOT inside the f-string — edit the `.js`, not `build_widget.py`). Ported from portfolio-x-ray-widget: `rsvParseDelimited` (delimiter sniffing, quoted fields), `rsvXlsxToRows` (native in-browser xlsx via `DecompressionStream` + `DOMParser`, zero deps), `rsvParseNumber` ($/comma/%/paren-negatives). Widget-specific additions: `rsvParseMonth` (ISO, US M/D/Y, month names, `YYYY-MM`, Excel serials), `rsvDetectKind` (price vs decimal-return vs percent-return heuristic), `rsvExtractTimeSeries` (auto-detects the date column + value columns + header).
- **Auto-detect + override:** each series is classified as price level / decimal returns / percent returns; a Review & Import table lets the user rename series and flip the interpretation before importing. Conversion to the engine's `{start, values}` index format is in `RSV._seriesToIndex` (price → month-over-month ratios; returns → compounded).
- **Monthly only:** data must be monthly; flexible on date *format*. Still requires consecutive months (the engine assumes a contiguous grid) and trims to the built-in date range (~1970 to 2026-03), reporting what was dropped.
- Removing a custom asset scrubs all portfolio references to it. No persistence (session-only).

---

## Compute Engine

**Flow:** User input -> state update -> `computePortfolio()` -> render charts & stats

**Key calculations:**
- Monthly rebalancing: weighted average of individual asset returns
- Stacked returns = core + (overlay return - T-bill financing - per-asset fee/bp - financing spread/bp) * weight
- Portfolio fee deducted monthly: `fee_bp / 10000 / 12`
- All statistics computed via unified `computeStats()`: annualized return, vol, max DD, Sharpe, Sortino, Calmar, skewness, kurtosis, VaR, CVaR, tail ratio, etc.
- Sharpe ratio always uses Treasury Bill data for risk-free rate (including core-only portfolios)
- Short-sample guards: skewness requires n>=3, kurtosis requires n>3 and std>0
- Benchmark frontier: 6 mixes of Global Equities (MSCI ACWI) + US Core FI (Bloomberg US Agg)
- Portfolio comparison uses common date range to ensure identical cores show identical stats
- Date range filtering: `_getFilteredView()` creates a result-shaped object with filtered dates/returns/growth for charts (net of fee); `computeStats()` with range params recomputes full stats
- Comparison panels share `state.comparisonDateRange`; per-portfolio uses `state.portfolios[i].dateRange`
- Missing asset data aborts computation (no silent skipping)
- Invalid weight edits clear stale results immediately

**Validated against Excel:** exact match on cumulative returns, annualized returns, volatility, max drawdown

---

## Default Portfolios

| # | Name | Core | Stack |
|---|------|------|-------|
| 1 | Global Balanced | 60% Global Equities / 40% US Core FI | None |
| 2 | Global Balanced + 20% Diversified Stack | 60% Global Equities / 40% US Core FI | 5% each: MF CTA, FY, Gold, MA |
| 3 | Global Balanced + 40% Diversified Stack | 60% Global Equities / 40% US Core FI | 10% each: MF CTA, FY, Gold, MA |

---

## Net-of-Fees Assets

All Alternative category assets EXCEPT: Risk Parity (10%), Risk Parity (12%), Risk Parity (15%), Global Stock/Bond Momentum, Risk-Weighted Gold/Bitcoin. The fee input field is greyed out for net-of-fees assets.

---

## Branches

| Branch | Output file | Purpose | Status |
|--------|------------|---------|--------|
| `master` | `RS_advanced_visualizer_widget.html` | Production baseline -- original CSS, all features including PDF export | Stable |
| `ui-polish` | `RS_advanced_visualizer_widget.html` | Divi CSS defense + UI/UX improvements | In progress |
| `web-authenticated` | `RS_advanced_visualizer_widget_web.html` | WordPress authenticated version with server-side portfolio storage | In progress |

**Repo:** `https://github.com/resolve-lab/rs_tool_advanced_visualizer`

To build: `git checkout <branch>` then `py -3.11 build_widget.py`

---

## Remaining Work

### Phase 6: PDF Export (DONE)
- jsPDF v2 integrated, single-portfolio and comparison PDF export working
- Branded cover page, charts rendered to offscreen canvas, disclosures included

### Phase 7: Divi Integration + Responsive (IN PROGRESS on `ui-polish`)
**Completed:**
- Divi CSS defense: scoped reset using `:where()` for all bare HTML elements -- prevents Divi theme styles from overriding widget styles while keeping low specificity so component classes win
- `isolation: isolate` on `.rsv-widget` creates a stacking context boundary
- `font-variant-numeric: tabular-nums` for aligned numbers in stats tables
- Button press feedback: `:active` scale on all interactive buttons
- Tab indicator animation: smooth `scaleX` entrance using `cubic-bezier(0.23, 1, 0.32, 1)`
- Custom easing on all transitions (replaced `transition: all` antipattern)
- Subtle depth shadows on panels, summary bar, chart area
- Tooltip scale + translate entrance animation
- Button variant CSS classes (`--secondary`, `--tertiary`, `--compact`, `--filled`) replace inline `style=` overrides
- `:focus-visible` keyboard navigation rings (accessibility)
- `prefers-reduced-motion` media query guard (accessibility)
- Results table row hover states
- Chart height increased from 360px to 420px
- Results fade-in animation (`rsv-fade-in` keyframe)
- Date range quick buttons visual separator
- Border-radius CSS custom properties (`--radius-sm/md/lg/xl`)

**Still needed:**
- Divi shortcode wrapper for WordPress embedding
- Mobile/responsive testing on returnstacked.com
- Test inside actual Divi Code module on staging
- Final visual QA pass

---

## Debugging

**Blank page (header + disclosures only, no tabs):** JS syntax error preventing the `RSV` object from being defined. Create a test file:
```html
<script>
try { new Function(js_code); } catch(e) { document.body.innerHTML = e.message; }
</script>
```
Common causes: duplicate `let`/`const` in same method, unmatched braces from Python f-string escaping.

## Updating Data

To re-extract from Excel: `py -3.11 extract_data.py`
To add a new asset: add to `data/indices_compact.json` (series), `data/index_map.json` (metadata), `data/disclosures.json` (definition), then rebuild.
To rebuild: `py -3.11 build_widget.py`
To regenerate the ticker info JSON after editing the mapping in `gen_ticker_info.py`: `py -3.11 gen_ticker_info.py`

## QC / Validation Workflow

Widget math is validated by Python scripts that re-implement the JS compute path against the same JSON inputs:

- `py -3.11 qc_stacked_portfolio.py` -- emits an Excel workbook of monthly core, stacked, and per-asset return components (with all intermediate formulas as cell refs) for a fixed 100% ACWI / 100% MFT test case. Use this when changing anything in the stacked-return formula (`core + (overlay - tbill - feeBp - financingBp) * weight`), the T-Bill financing logic, or the monthly fee deduction.
- `py -3.11 export_all_data.py` -- dumps every embedded series + the widget-name <-> source-index mapping + calendar-year returns to Excel; useful when adding/renaming an asset to confirm the mapping in `index_map.json` round-trips correctly.
- `py -3.11 build_ticker_map.py` -- regenerates the Bloomberg ticker reference workbook used by sales/marketing.

When changing compute logic, run `qc_stacked_portfolio.py` first and diff the Excel output against the prior run before touching the HTML.

---

## Phase 8: WordPress Authenticated Version (IN PROGRESS on `web-authenticated`)

The widget will be deployed on returnstacked.com behind a WordPress login wall. No public/logged-out access. This version saves portfolios server-side per user account rather than to localStorage.

**Developer handoff doc:** https://claude.ai/code/artifact/44464600-7e6e-4dc2-ba26-e6a94db450b0

### Architecture decisions

- **Storage:** Custom DB table `wp_rsv_portfolios` (not user meta) -- users are expected to save many portfolios
- **Auth:** WordPress REST API with nonce-based auth (`X-WP-Nonce` header); all routes check `is_user_logged_in()` and enforce row-level ownership
- **Identity injection:** WordPress injects `window.RSV_CONFIG` with `userEmail` only (email from WP user record). First/last name are NOT collected from WordPress. The `[rsv_widget]` shortcode (or equivalent page-level script) must output this before the widget loads:
  ```html
  <script>
  window.RSV_CONFIG = {
    userEmail: '<?php echo esc_js( wp_get_current_user()->user_email ); ?>'
  };
  </script>
  ```
- **Intake gate:** Removed entirely (2026-06-25). The widget now loads immediately without asking for any user information. `activateWidget()` is called unconditionally on init. The intake overlay is hidden by default.
- **Consultant CTA:** Ungated (2026-06-25). The "Talk to a Consultant" strip now renders for all users. Previously it was gated on `storedInvestorType` matching a financial pro list -- that check has been removed since all users behind the login wall are pre-approved advisors. The consultant modal still asks for AUM + state and uses that to route to the correct rep.
- **HubSpot submissions:** `storedEmail` comes from `RSV_CONFIG.userEmail` injected by WordPress. Share-link and PDF form submissions carry this email. The user info header strip shows `· email@example.com` only (no name prefix) since firstName/lastName are not collected.
- **Share links:** Existing `?rs_p=` URL-encoded share mechanism is unchanged. When the widget detects it loaded from a share param, a "Save to your account?" prompt is shown on top. No new endpoints needed.
- **Saved Comparisons:** Same DB approach as portfolios (separate table/endpoints). `loadSavedComparison` needs async refactor since it resolves portfolio names from the API cache.
- **Import Portfolio:** Kept as a migration tool only -- for users bringing old localStorage JSON backups into the web version. Relabel to "Import from file".
- **Import Comparison:** Remove entirely -- comparisons aren't independently shareable artifacts.
- **JSON auto-download on save:** Removed -- server is the source of truth.

### What's already implemented (`web-authenticated` branch)

- `build_widget.py` outputs `RS_advanced_visualizer_widget_web.html`
- Pre-hydrate block bypasses intake gate using `RSV_CONFIG.userEmail` (Change 8)
- `backend/rsv-portfolios.php` -- full WP plugin: table creation, 5 REST routes, `[rsv_widget]` shortcode with user identity injection

### Pending widget-side changes (apply to `build_widget.py` before next rebuild)

Two changes were made directly to `RS_advanced_visualizer_widget.html` on 2026-06-25 that have NOT yet been applied to `build_widget.py`. A rebuild will overwrite them. Before running `py -3.11 build_widget.py` again, apply these to the Python source:

1. **Remove intake gate** -- in `_initHubSpot()`, change `if (storedEmail) { activateWidget(); }` to `activateWidget();` and change `showUserInfo()` inside `activateWidget()` to `if (storedEmail) showUserInfo();`
2. **Ungate consultant CTA** -- in `renderConsultantCTA()`, remove the line `if (!financialProTypes.includes(storedInvestorType)) return '';`

### Pending (developer tasks -- Changes 1--7 in handoff doc)

- `RSV_API` fetch wrapper + `_portfoliosCache` variable
- `getSavedPortfolios` / `setSavedPortfolios` simplified to read/write cache
- Init: populate cache from `GET /rsv/v1/portfolios` on page load
- `savePortfolio` -- async, POST to API, remove JSON file download
- `loadSavedPortfolio` -- async, fetch full data on demand by id
- `deleteSavedPortfolioPrompt` -- async, call DELETE endpoint
- `_handleImportFile` -- async, POST each imported file to API
- Saved Comparisons: new DB table + endpoints + async load refactor
- Share link: add "Save to account?" prompt when `?rs_p=` param detected on load
