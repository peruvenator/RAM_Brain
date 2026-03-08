# RS Portfolio Widget — Return Stacking Explorer

## Project Overview

An interactive single-file web application that lets users visualize how return stacking works. Users adjust a stock/bond mix, choose alternative strategy overlays (trend following, gold, merger arbitrage), set a stack size, and compare the "stacked" portfolio against the traditional allocation across multiple chart types. Includes client-side PDF report generation.

---

## Key Files

| File | Purpose |
|------|---------|
| `RS_portfolio_widget.html` | **The entire app** — single 2,276-line HTML file with inline CSS, JS, and embedded data |
| `Return Stacking Widget.pdf` | Reference/example PDF output |

## Architecture

Everything is in one file:
- **Lines ~10–525**: CSS styles (inline `<style>`)
- **Lines ~529–718**: HTML structure
- **Lines ~719–2276**: JavaScript (inline `<script>`) — 33 named functions, embedded base64 fonts and logo for PDF

**Libraries (CDN):**
- Chart.js v4 — interactive charts
- jsPDF v2 — client-side PDF generation

**Data**: 313 monthly data points (12/1999–2/2025) embedded inline as a `DATA` array with fields: `date`, `stocks`, `bonds`, `gold`, `trend`, `mergerArb`, `tbills`.

---

## Brand Assets

Shared brand assets are at `../Brand_elements/` (see root `CLAUDE.md` for full reference).

**Colors** — hardcoded throughout (not CSS custom properties):
- `#2A3F5B` — primary navy (close to Cover Dark `#172c3a` but not exact)
- `#456998` — fixed portfolio chart color (Blue Secondary range)
- `#60CCA8` — stacked portfolio chart color (Teal Primary range)
- `#f5f6fa` — light background (close to Section Gray `#f0f1f1`)
- `#625c6d` — secondary text (matches Text Secondary)

**Font**: DM Sans from Google Fonts CDN (weights 400, 500, 700). Not loaded from local `../Brand_elements/Font_Family/` files.

**Logo**: White RS logo embedded as base64 in JavaScript for PDF header. No external logo file referenced.

---

## How It Works

**State** — a single `state` object holds all user inputs:
```
stockPct, bondPct, trendPct, goldPct, marbPct, stackSize,
trendFee, goldFee, marbFee, trendFinancing, goldFinancing, marbFinancing
```

**Flow**: User input → state update → `compute()` → render charts & stats

**4 Chart Types** (tab-switched):
1. Growth of $100
2. Rolling returns (configurable window)
3. Drawdowns
4. Calendar year returns

**PDF Generation** (7 pages):
1. Title page with settings summary
2. Summary metrics + disclaimer
3. Growth chart
4. Rolling returns + outperformance stat
5. Drawdowns chart
6. Calendar year returns + streak stats
7. Methodology & disclosures (dynamic based on active strategies)

---

## Key Conventions

- **Alt blend validation**: Trend + Gold + MergerArb must sum to 100%. Shows warning and disables charts if invalid.
- **Fee inputs**: Decimals allowed. Trend fee is read-only (net of fees by design).
- **Chart colors**: `FIXED_COLOR = '#456998'`, `STACKED_COLOR = '#60CCA8'` — constants used consistently.
- **Disclosures**: Dynamically generated based on which alternatives are active in the portfolio.
- **Section comments**: Code uses `// ── Data ──`, `// ── State ──`, `// ── DOM refs ──` markers.

## Build / Deploy

No build process. Single HTML file served directly. All libraries loaded from CDN. Works offline after initial load (except CDN resources). PDF generation is entirely client-side.

## Updating Data

To update the embedded monthly data, modify the `DATA` array in the `<script>` section. Each entry has the format:
```javascript
{ date: "YYYY-MM-DD", stocks: X.XXXX, bonds: X.XXXX, gold: X.XXXX, trend: X.XXXX, mergerArb: X.XXXX, tbills: X.XXXX }
```
Values are cumulative return index levels (starting at 1.0 on 12/31/1999).
