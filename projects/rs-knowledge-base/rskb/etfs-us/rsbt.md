# RSBT — Return Stacked® Bonds & Managed Futures ETF

## At a glance

| Field | Value |
|---|---|
| Ticker | RSBT |
| CUSIP | 88636J105 |
| Primary Exchange | CBOE |
| Wrapper | ETF |
| Jurisdiction | USA |
| Inception | February 7, 2023 (the original product in the suite) |
| Expense Ratio | 1.02% (gross = net) |
| Net Assets | ~$127M (04/17/2026) |
| 30-Day SEC Yield | 2.32% (as of 03/31/2026) |
| Distribution Frequency | Annual (December) |
| Cayman Subsidiary | Yes |

## Investment case

For every $1 invested, RSBT is designed to provide **$1 of broad U.S. bond exposure** and **$1 of a managed futures (trend) strategy**.

Three pillars:
1. **Capital Efficiency** — simultaneous $1 + $1 exposure to bonds and trend.
2. **Diversification** — managed futures has historically exhibited low correlation to both stocks and bonds.
3. **Inflation Hedging** — long/short across global futures markets.

## Mechanics

### Bond sleeve ($1)
Holds U.S. Treasuries, broad-based bond ETFs (typically SPAB — SPDR Portfolio Aggregate Bond ETF), and/or U.S. Treasury futures across the curve.

**Example construction:**
- 75% SPDR Portfolio Aggregate Bond ETF (SPAB)
- 6.25% U.S. 2-Year Treasury futures
- 6.25% U.S. 5-Year Treasury futures
- 6.25% U.S. 10-Year Treasury futures
- 6.25% U.S. Long Bond futures

**Effective duration:** approximately tracks the Bloomberg U.S. Aggregate Bond Index.

### Managed Futures sleeve ($1)
Identical methodology to RSST: 30% top-down + 70% bottom-up trend replication across ~27 global futures markets. See `/concepts/trend-replication.md`.

### Active duration management
The trend stack will go long or short bond futures as bond trends evolve. By design:
- **Bond trends down** → trend stack shorts bonds → reduces total portfolio duration (hedging duration risk)
- **Bond trends up** → trend stack goes long bonds → increases duration

This means the fund's effective bond exposure adjusts dynamically with market conditions.

### Operational details
- **Rebalances:** daily
- **Cayman Subsidiary:** futures positions held inside a Cayman CFC for RIC tax compliance

## FAQs (from product page)

### How does RSBT get its exposure to bonds?
The bond strategy can hold U.S. Treasuries, bond ETFs, and U.S. Treasury futures, or any combination. Example: 75% broad U.S. bond ETF + 25% Treasury futures ladder. The trend stack will also have long/short positions in U.S. Treasury futures.

### What is the effective duration of the Bond strategy?
Approximately tracks the Bloomberg U.S. Aggregate Bond Index.

### What proportion is given to each replication approach?
30% top-down + 70% bottom-up.

### What is the expected risk profile?
Joint inception 12/31/1999 – 3/31/2023:
- Bloomberg US Aggregate Bond Index realized vol: ~4.0%
- SocGen Trend Index realized vol: ~13.6%
- Equal-weight 200%-levered combo: realized vol of **14.3%**

## Performance (as of 03/31/2026, NAV)

| Period | RSBT NAV | Bloomberg US Agg |
|---|---|---|
| 1 Month | -4.53% | -1.76% |
| 3 Month | +4.91% | -0.05% |
| 6 Month | +11.74% | +1.05% |
| YTD | +4.91% | -0.05% |
| 1 Year | +15.96% | +4.35% |
| 3 Year (annualized) | +2.99% | +3.63% |
| Since Inception (cumulative) | -0.48% | +12.15% |
| Since Inception (annualized) | -0.15% | +3.72% |

## Pitch language (verbatim)

> "For every $1 invested, RSBT is designed to provide $1 of broad U.S. bond exposure and $1 of a managed futures strategy."

> "By design [the active bond exposure via the trend stack] should be considered as an attempt to use trend signals to hedge against duration risk in bond portfolios when trends are down (by shorting) and at times increase duration exposure when trends are positive (by going long)."

## Compliance / risk notes

Same risk family as RSST: Leverage Risk, Cayman Subsidiary Risk, Bond Risks, Commodity Risk, Commodity-Linked Derivatives Tax Risk, Commodity Pool Regulatory Risk, Credit Risk, Currency Risk, Foreign and Emerging Markets Risk, Non-Diversification Risk, Underlying ETFs Risk, New Fund Risk.

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
- Advisor Guide: "Managed Futures Advisor Guide" (HubSpot)
- Whitepaper: "Filling the Gap: Enhancing Traditional Stock and Bond Portfolios with a Managed Futures Stack"
