# Trend Replication Report

3-year trend replication analysis for the SocGen CTA and related trend indices.
Brand: ReSolve Asset Management.

## Key Files

- `trend-data.csv` -- Daily time series data (Feb 2023 - Feb 2026, 754 trading days)
- `build_report.py` -- Generates the raw HTML report with 13 PNG charts (Corey Hoffstein's v2 script, rebranded for ReSolve)
- `reformat_html.py` -- Transforms the raw HTML into a paged PDF-style layout with ReSolve branded cover, headers, footers, and embedded Helvetica Neue fonts
- `build_audit.py` -- Generates a standalone HTML audit workbook with Lo(2002) lag-by-lag detail
- `package_for_compliance.py` -- Runs all three scripts and zips the deliverables for compliance review
- `trend-replication-analysis.html` -- The final generated HTML report (self-contained, print to PDF from Chrome)
- `trend-replication-audit.html` -- The audit workbook
- `charts/` -- 10 SVG chart files (legacy, from old build script)
- `ReSolve_report_exapmples/` -- Reference PDFs for design matching
- `Reference files/` -- Corey's original session files

## Usage

```bash
cd projects/trend-replication-report
python build_report.py        # generates raw HTML with charts
python reformat_html.py       # applies paged layout + ReSolve branding
python build_audit.py         # generates audit workbook
python package_for_compliance.py  # runs all three + zips for compliance
```

To print to PDF: open `trend-replication-analysis.html` in Chrome, print with "Save as PDF", Letter size, no margins, background graphics enabled.

## Build Pipeline

1. `build_report.py` reads `trend-data.csv`, computes all statistics (including Lo(2002) autocorrelation-adjusted tracking error), generates 13 inline PNG charts, and outputs a flat HTML file
2. `reformat_html.py` reads that HTML, extracts sections, splits large sections (Tracking Error and Thought Experiment) across pages, generates a branded cover page, wraps everything in explicit page divs with headers/footers/page numbers, embeds Helvetica Neue fonts from brand assets, and overwrites the HTML
3. `build_audit.py` independently replicates all computations and outputs an audit trail

## Lo (2002) Tracking Error

The key methodological feature. Uses autocorrelation-adjusted annualization instead of naive sqrt(252).

- **Parameters**: q=21 lags (Bartlett kernel), floor eta=0.01
- **Implementation**: `lo_eta()` and `lo_adj_te()` functions in build_report.py (lines ~358-371)
- **Source**: Corey Hoffstein's build_report_v2.py (identical computation, verified line-by-line)
- **Result**: Blend TE drops from ~7.0% (naive) to ~5.3% (adjusted), eta ~0.569
- **Validation**: Rolling 1-year return difference std (~3.4%) is more consistent with Lo-adjusted figure

## Report Structure (17 sections + 2 split = 19 pages + cover)

| Page | Content | Charts |
|------|---------|--------|
| Cover | Logo, title, subtitle, date | - |
| 2 | Executive Summary | - |
| 3 | Growth of $1 | Fig 1 |
| 4 | Relative Performance | Fig 2 |
| 5 | Full-Period Statistics | - |
| 6 | Rolling Correlation | Fig 3, 4 |
| 7 | Tracking Error (chart + Lo explanation) | Fig 5 |
| 8 | Tracking Error cont'd (rolling 1yr + callout) | Fig 6 |
| 9 | Cumulative Return Difference | Fig 7 |
| 10 | Monthly Return Analysis | Fig 8, 9 |
| 11 | Annual Performance | Fig 10 |
| 12 | Drawdown Analysis | Fig 11 |
| 13 | Thought Experiment (intro + TE frontier) | Fig 12 |
| 14 | Thought Experiment cont'd (weights + analysis) | Fig 13 |
| 15 | Sub-Program Assessment | - |
| 16 | Quarterly Tracking Detail | - |
| 17 | Conclusions | - |
| 18 | Technical Glossary | - |
| 19 | Index Definitions | - |
| 20 | Important Disclosures | - |

## Sub-Model Naming

| CSV Column | Report Name | Description |
|------------|-------------|-------------|
| TD_Small | Top Down (Constrained) | Limited-universe regression model |
| TD_Med | Top Down (Full) | Full-universe regression model |
| BU | Bottom Up | Blend of live trend-following programs |
| Blend | Trend Replication Blend | 15/15/70 daily-rebalanced |

## Series Color Mapping (RAM Brand)

| Series | Hex | Role |
|--------|-----|------|
| SG Trend Index | `#000000` | Benchmark (black) |
| Trend Replication (Blend) | `#00478D` | Hero series (brand blue) |
| Bottom Up (70%) | `#FBBA00` | Sub-model (amber) |
| Top Down Full (15%) | `#89D2FF` | Sub-model (sky blue) |
| Top Down Constrained (15%) | `#6F4596` | Sub-model (purple) |

## Dependencies

```
pip install matplotlib pandas numpy scipy    # build_report.py
```

## Origin

- Original computation and text by Corey Hoffstein (Newfound Research), via Claude session
- Corey's `build_report_v2.py` adopted as the build script with ReSolve branding applied
- All entity references changed from "Newfound Research" to "ReSolve Asset Management"
- Computations verified identical line-by-line (2026-03-18)
- Adam Butler reviewed and made two text edits (2026-03-18): shortened exec summary cumulative return paragraph, expanded Figure 5 caption to "Lo Autocorrelation-Adjusted"
