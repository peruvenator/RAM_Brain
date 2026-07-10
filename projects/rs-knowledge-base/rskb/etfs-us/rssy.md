# RSSY — Return Stacked® U.S. Stocks & Futures Yield ETF

## At a glance

| Field | Value |
|---|---|
| Ticker | RSSY |
| CUSIP | 88636J345 |
| Primary Exchange | CBOE |
| Wrapper | ETF |
| Jurisdiction | USA |
| Inception | May 28, 2024 |
| Expense Ratio | 0.98% |
| Net Assets | ~$102M (04/17/2026) |
| 30-Day SEC Yield | 0.03% (as of 03/31/2026) |
| Distribution Frequency | Annual (December) |
| Cayman Subsidiary | Yes |

## Investment case

For every $1 invested, RSSY is designed to provide **$1 of large-cap U.S. equity exposure** and **$1 of a futures yield (carry) strategy**.

Three pillars:

1. **Capital Efficiency** — simultaneous $1 + $1 exposure to stocks and carry.
2. **Diversification** — futures yield has historically exhibited low average correlations to both stocks and bonds.
3. **Inflation Hedging / Directional Alternative** — with long/short ability across global futures, carry has the potential to dynamically respond to changing market regimes and complement other directional alternative strategies like trend-following.

## Mechanics

### U.S. Equity sleeve ($1)
Holds U.S. equities, U.S. equity ETFs (typically IVV — iShares Core S&P 500 ETF), and/or S&P 500 E-Mini futures.

**Example construction:** 50% IVV + 50% S&P 500 E-Mini futures.

### Futures Yield (Carry) sleeve ($1)
Invests long and short across commodities, currencies, bonds, and equities via futures contracts. Uses a systematic and quantitative process that seeks to harvest **roll yield (carry)** in futures contracts.

See `/concepts/carry-yield.md` for full detail on the strategy. In brief:
- Each market is scored on its **risk-adjusted carry**
- Highest-scoring markets are gone long; lowest-scoring are shorted
- Position sizes are scaled by recent volatility for risk balance
- Strategy is **directionally agnostic** — long or short any market depending on the carry signal

### Operational details
- **Rebalances:** daily
- **Cayman Subsidiary** used for commodity futures
- **Why pair with RSST?** RSSY (carry) and RSST (trend) target different characteristics of the same futures markets and have low correlation to each other — pairing them gives advisors three uncorrelated return streams (equity beta + trend + carry) per dollar invested

## FAQs (from product page)

### How does RSSY get its exposure to U.S. equities?
Holdings can include U.S. equities, U.S. equity ETFs, and U.S. equity index futures. Example: 50% large-cap equity ETF + 50% S&P 500 E-Mini futures. The Futures Yield strategy will also have long or short positions in U.S. equity index futures.

### What is Futures Yield?
The returns of an asset can largely be decomposed into two sources: (1) price appreciation and (2) yield (sometimes called "carry"). The second component is the expected return assuming no change in price — the economic benefit of simply holding an asset minus the costs associated with holding it. Futures yield strategies seek to maximize exposure to this second component.

### Is RSSY tax efficient?
Daily gains and losses in futures contracts may be calculated as realized for tax purposes, which may affect ordinary income or capital gains depending on the contract.

### How often does RSSY make distributions?
Annually at calendar year-end, if any.

## Performance (as of 03/31/2026, NAV)

| Period | RSSY NAV | S&P 500 TR |
|---|---|---|
| 1 Month | +7.15% | -4.98% |
| 3 Month | +15.51% | -4.33% |
| 6 Month | +13.22% | -1.79% |
| YTD | +15.51% | -4.33% |
| 1 Year | +27.39% | +17.80% |
| Since Inception (cumulative) | +13.89% | +26.02% |
| Since Inception (annualized) | +7.32% | +13.38% |

## Recent positioning (snapshot 04/17/2026 — illustrative; rotates frequently)

**Carry stack representative positions** (% of NAV, approximate):
- **Longs:** AUD/USD, GBP/USD, US 5Y/10Y/30Y futures, UK Long Gilt, energies (RBOB, gasoil, heating oil, Brent, WTI), Nikkei 225, NASDAQ 100, DAX
- **Shorts:** S&P 500, FTSE 100, S&P/TSX 60, Eurostoxx, JPY/USD, EUR/USD, CAD/USD, gold, copper, natural gas

## Pitch language (verbatim)

> "For every $1 invested, RSSY is designed to provide $1 of large-cap U.S. equity exposure and $1 of a futures yield strategy."

> "Futures yield (carry) has the potential to dynamically respond to changing market regimes and complement other directional alternative strategies like trend following."

## Compliance / risk notes

Same risk family as RSST plus:
- **High Portfolio Turnover Risk** — carry signals shift, so positions rotate frequently
- **Illiquid Investments Risk** — at times the fund may hold illiquid investments

## Management

**Investment Adviser**
Tidal Investments LLC serves as investment adviser to the Fund and the Subsidiary.

**Investment Sub-Advisers**
Newfound Research LLC serves as investment sub-adviser to the Fund.
ReSolve Asset Management Inc. serves as a non-discretionary investment sub-adviser to the Fund and the Subsidiary.

**Futures Advisor**
ReSolve Asset Management SEZC (Cayman) serves as futures advisor to the Fund and the Subsidiary.

**Distributor**
Foreside Fund Services, LLC

## Resources
- Presentation, Factsheet, Product Brief, Quarterly Commentary on returnstackedetfs.com
- Advisor Guide: "Managed Futures Yield (Carry) Advisor Guide" (HubSpot)
