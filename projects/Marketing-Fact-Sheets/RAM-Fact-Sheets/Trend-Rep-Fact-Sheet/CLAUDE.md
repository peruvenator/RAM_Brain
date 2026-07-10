# Trend Rep Fact Sheet

HTML fact sheet for the ReSolve Asset Management trend replication strategy. Designed to match the visual language of existing RAM fact sheets (All Terrain, Futures Yield Program) while adding new interactive/visual elements.

Brand: ReSolve Asset Management.

## Folder Layout

- `data/` -- Input time series (Excel). Primary file: `trend-rep-live-performance.xlsx`
- `references/` -- Existing RAM fact sheets used as design/layout references + current copy:
  - `All-Terrain-Factsheet-US-March2026.pdf` -- layout/design reference
  - `ReSolve-Futures-Yield-Program-Factsheet-Expanded-Universe-US.pdf` -- layout/design reference
  - `current-website-copy.md` -- captured copy from https://investresolve.com/strategies/resolve-trend-replication-program/ (2026-04-20). Baseline wording for the fact sheet; improve on it, don't reproduce verbatim
- `build/` -- Python / build scripts (data loaders, chart generators, HTML assembler)
- `output/` -- Final `trend-rep-factsheet.html` + any generated chart assets

## External Data Sources

Additional time series pulled from the local S3 mirror (nightly sync):

- `C:\Users\RodrigoGordillo\S3_Data\trading_data\` -- ETFs, futures, indices, FX, rates (diff-adjusted, ratio-adjusted, term structure)
- `C:\Users\RodrigoGordillo\S3_Data\signal_gen_data\` -- Feature data + portfolio manager outputs (contract table, risk/trade weights, blotter, reports)
- `C:\Users\RodrigoGordillo\S3_Data\backtest-sims\` -- Backtest sim outputs (portfolio_returns/trend_rep sub-strategy returns)
- Schema reference: `C:\Users\RodrigoGordillo\S3_Data\DATA_SYNC_AND_SCHEMAS.md`

Read from these locations directly; do not copy the raw data into the project repo.

## Workflow

1. Load time series from `data/trend-rep-live-performance.xlsx` + any S3_Data series needed
2. Compute fact sheet statistics (returns, vol, drawdown, rolling metrics, correlations, etc.)
3. Generate charts (prefer inline SVG or PNG embedded as base64 for a self-contained HTML)
4. Assemble the HTML fact sheet in `output/trend-rep-factsheet.html`
5. Print-to-PDF from Chrome for the distribution-ready artifact

## Design Notes

- Match the layout grammar of the two reference PDFs (header/footer, typography hierarchy, disclosure block placement)
- Use RAM brand assets from `references/brand-assets/` (fonts, colors, logos) -- do not re-invent styling
- New elements beyond the existing fact sheet template will be added iteratively; leave the HTML structured for easy section swapping

## Writing / Compliance

- Follow `rs-writing-style` skill conventions where applicable (em-dash ban, we/our, hedged performance language)
- Fact sheets are compliance-reviewed artifacts. All performance claims must be sourced and footnoted.

## Source Copy

The strategy's public page -- https://investresolve.com/strategies/resolve-trend-replication-program/ -- is the baseline for written content. A local snapshot lives at `references/current-website-copy.md`. Use it as the starting point for the fact sheet's narrative, disclaimers, and mandate highlights, then tighten and improve the wording.

## Status

Scaffolded 2026-04-20. Excel, reference PDFs, and website copy staged. No build scripts yet -- waiting on design direction.
