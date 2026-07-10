---
name: extract-chart-data
description: Extract embedded chart/visualization data from web pages (Google Charts, Chart.js, Highcharts, wpDataCharts, inline data arrays). Extracts figure titles and disclaimers too. Handles JavaScript-heavy pages that WebFetch cannot fully render.
---

# Extract Chart Data from Web Pages

Extract embedded visualization data, figure titles, and disclaimers from web pages where WebFetch fails due to JavaScript rendering or content truncation.

## Quick Start

```bash
python .claude/skills/extract-chart-data/extract.py "<URL>" --output output.json
```

Output JSON per chart:
```json
{
  "title": "Figure 1: Rolling 5-Year Annualized Returns of U.S. Bonds",
  "disclaimer": "Source: Bloomberg. U.S. Bonds are the Bloomberg U.S. Aggregate Bond Index...",
  "data": {
    "columns": [{"type": "string", "label": "Year"}, {"type": "number", "label": "(%)"}],
    "rows": [["12/31/2004", 7.71], ["1/31/2005", 7.92], ...]
  }
}
```

## What It Extracts

1. **Chart data** from inline `<script>` tags:
   - wpDataCharts (WordPress DataTables plugin) -- `render_data` objects with columns + rows
   - Google Charts -- `arrayToDataTable`, `addRows`, `DataTable` constructors
   - Chart.js -- `datasets`, `labels` arrays
   - Highcharts -- `series` data
   - Generic -- large numeric arrays, JSON script blocks

2. **Figure titles** -- scans for "Figure N: ..." in `<strong>`, `<b>`, `<h2>`-`<h4>` tags

3. **Disclaimers** -- scans for "Source: ..." text in `<em>`, `<p>` tags near each figure, walking up to `<p>` level to capture full text across split tags

Charts, titles, and disclaimers are matched by page order (figure 1 maps to chart 1, etc.).

## Using Extracted Data for Branded Plots

After extracting, use the data directly in matplotlib with Return Stacked or ReSolve brand styles:

```python
import json
import pandas as pd

with open("extracted_chart_data.json") as f:
    charts = json.load(f)

chart = charts[0]  # Figure 1
title = chart["title"]          # "Figure 1: Rolling 5-Year Annualized Returns..."
disclaimer = chart["disclaimer"] # "Source: Bloomberg..."
rows = chart["data"]["rows"]     # [["12/31/2004", 7.71], ...]

df = pd.DataFrame(rows, columns=["Date", "Value"])
df["Date"] = pd.to_datetime(df["Date"])
```

Then plot with these conventions:

- **Title**: Strip the "Figure N: " prefix -- use only the descriptive text after the colon
- **Disclaimer**: Left-justified, font size one step smaller than chart body text (mplstyle sets 11pt for ticks, so use 10pt for disclaimer)

```python
import re, textwrap

# Strip "Figure N: " prefix from title
clean_title = re.sub(r"^Figure\s+\d+\s*:\s*", "", title)
ax.set_title(clean_title, fontsize=14, fontweight="bold", color="#323a46", pad=12)

# Disclaimer: left-justified, one size smaller than body text
wrapped = textwrap.fill(disclaimer, width=130)
fig.text(0.02, -0.02, wrapped,
         ha="left", fontsize=10, color="#888888", style="italic",
         transform=fig.transFigure)
fig.tight_layout(rect=[0, 0.06, 1, 1])
```

## Strategy (if the script doesn't find data)

### 1. Debug with --raw-scripts

```bash
python .claude/skills/extract-chart-data/extract.py "<URL>" --raw-scripts
```

Shows all inline script contents so you can identify the data format.

### 2. Chrome CDP fallback (for AJAX-loaded data)

If data is loaded dynamically via AJAX (not in the initial HTML), use chrome-cdp:

```bash
# List targets and find the tab
node .claude/skills/chrome-cdp/scripts/cdp.mjs list

# Extract chart data from rendered DOM
node .claude/skills/chrome-cdp/scripts/cdp.mjs eval <target> "
  JSON.stringify(
    Array.from(document.querySelectorAll('script'))
      .map(s => s.textContent)
      .filter(t => /wpDataCharts|google\.visualization|arrayToDataTable|new Chart|Highcharts/.test(t))
  )
"
```

### 3. Network inspection

```bash
node .claude/skills/chrome-cdp/scripts/cdp.mjs net <target>
```

Look for `.json`, `.csv`, or API calls returning chart data.

## Known Patterns by Site

| Site Type | Chart Library | Data Location |
|-----------|--------------|---------------|
| returnstacked.com | wpDataCharts (Google Charts) | Inline `<script>`, `wpDataCharts[N].render_data` |
| WordPress + Divi | Google Charts / wpDataCharts | Inline `<script>` in page body |
| WordPress + Elementor | Chart.js | Inline `<script>` or separate `.js` |
| Custom React/Vue | Various | Often AJAX/API (use CDP) |
| Static HTML | Any | Inline `<script>` |

## Dependencies

```bash
pip install requests beautifulsoup4
```
