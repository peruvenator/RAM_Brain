# RGBM.U — Return Stacked® Global Balanced & Macro ETF USD Shares

## At a glance

| Field | Value |
|---|---|
| Ticker | RGBM.U (USD-denominated) |
| CUSIP | 54315B789 |
| ISIN | CA54315B7896 |
| Primary Exchange | Toronto Stock Exchange |
| Wrapper | **Alternative Mutual Fund** structured as ETF |
| Jurisdiction | Canada |
| Inception | April 28, 2025 |
| Management Fee | 0.85% (plus applicable sales tax) |
| Performance Fee | 10% of outperformance over global balanced benchmark |
| MER / TER | N/A (new ETF) |
| Currency | **USD** |
| Currency Hedging | **CAD bond exposure hedged back to USD; equity exposure not hedged** |
| Net Assets | ~US$35.8M (04/24/2026) |
| NAV | US$24.93 (04/24/2026) |
| Distributions | None expected |

## What's different from RGBM

RGBM.U is the **USD share class** of the same underlying strategy as RGBM. They are structurally near-identical with one key difference:

**RGBM.U hedges the Canadian-dollar exposure on the bond sleeve back to USD.** The global equity sleeve is *not* hedged (it has natural multi-currency exposure as designed).

The USD share class lets U.S. investors (or Canadians in U.S. dollar accounts) access the strategy in USD without taking on Canadian-dollar FX risk on the bond component. RGBM.U trades in USD on the Toronto Stock Exchange.

## Investment case

For every $1 invested, RGBM.U aims to provide **$1 of exposure to a global balanced allocation strategy** and **$1 of exposure to a systematic macro strategy** — same as RGBM.

Five pillars (RGBM.U has the additional "Currency Hedging" pillar that RGBM doesn't):

1. **Capital Efficiency**
2. **Diversification**
3. **Inflation Hedging**
4. **Tax Efficiency** — corporate-class structure means no expected taxable distributions
5. **Currency Hedging** — RGBM.U hedges any Canadian-dollar exposure back to USD on the bond sleeve, and trades in USD

## Mechanics — currency hedge implementation

Example construction for $1 of balanced allocation:
- 50% Vanguard Total World Stock ETF (VT) — *not currency-hedged*, naturally USD-based via multi-currency holdings
- 25% Vanguard Canadian Aggregate Bond ETF (VAB.TO) — Canadian dollar denominated
- 25% Canadian 10Y Government Bond futures (CGB)
- 50% USD/CAD forward contract to hedge the Canadian currency exposure on the bond allocation back to USD

Systematic macro sleeve operates identically to RGBM.

## Why a Canadian-bond-hedged-to-USD sleeve?

This is the key design question. Per the product page FAQ:

> "Historically the total return of a core Canadian government bond portfolio e.g. iShares Core Canadian Government Bond Index ETF (XGB.TO) hedged back to USD versus a core U.S. treasury bond portfolio e.g. iShares U.S. Treasury Bond Index ETF (GOVT) have broadly traded within very similar bands and with similar risk/return profiles."

**Translation:** the hedged Canadian bond sleeve gives USD-share holders functionally similar fixed-income exposure to U.S. Treasuries. The Canadian bond infrastructure is used because the Investment Fund Manager (LongPoint) and Portfolio Manager (ReSolve Canada) are Canadian-domiciled and the fund is TSX-listed.

## FAQs (from product page)

### How often does RGBM.U rebalance?
RGBM.U rebalances daily.

### How does RGBM.U get its exposure to a Balanced Allocation strategy and hedge out Canadian currency risk?
Global equity portion: holds global equities, global equity ETFs, and/or global equity index futures (not currency-hedged). Bond portion: Canadian bonds, Canadian bond ETFs, and/or CGB futures, with USD/CAD forward contracts to hedge CAD exposure on the bond allocation back to USD. The systematic macro stack will also hold long or short positions in global equity index futures and CGB futures.

### How has a broad Canadian bond portfolio compared to U.S. Treasury bonds with similar duration historically?
See above — Canadian bonds hedged back to USD have broadly traded within similar bands as U.S. Treasuries with similar risk/return profiles.

### Is RGBM.U tax efficient?
Expected to be tax-efficient as part of a corporate-class structure.

### How often does RGBM.U make distributions?
**RGBM.U is not expected to make any distributions.**

## Performance

> "Investment fund regulations restrict the presentation of performance figures until a fund reaches its one-year anniversary."

RGBM.U hit its one-year mark on April 28, 2026, so performance disclosure is just becoming permissible at this snapshot date. Verify the latest factsheet.

## Recent positioning (snapshot 04/24/2026)

Same underlying strategy positioning as RGBM. See `rgbm.md` for the holdings table.

## Pitch language (verbatim)

> "For every $1 invested, RGBM.U aims to provide $1 of exposure to a global balanced allocation and $1 of exposure to a systematic macro strategy."

> "RGBM.U hedges any Canadian dollar exposure back to USD and trades in USD."

## Compliance / risk notes

Same risks as RGBM. Alternative mutual fund using leverage and derivatives. Past performance not a guarantee. Read ETF Facts and prospectus before investing.

## Sponsor structure

Same as RGBM:
- **Investment Fund Manager:** LongPoint Asset Management Inc.
- **Portfolio Manager:** ReSolve Asset Management Inc. ("ReSolve Canada")
- **Portfolio Sub-Advisor:** ReSolve Asset Management SEZC (Cayman) ("ReSolve Global")
- **Co-Promoter:** Newfound Research LLC

## Resources
- Factsheet, Quarterly Commentary, RGBM.U Presentation, Product Brief, RGBM.U KYP, Prospectus (EN/FR), Fund Facts (EN/FR) on returnstackedetfs.ca
