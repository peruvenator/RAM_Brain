# RSST — Return Stacked® U.S. Stocks & Managed Futures ETF

## At a glance

| Field | Value |
|---|---|
| Ticker | RSST |
| CUSIP | 88636J816 |
| Primary Exchange | CBOE |
| Wrapper | ETF |
| Jurisdiction | USA |
| Inception | September 5, 2023 |
| Expense Ratio | 0.99% (gross = net) |
| Net Assets | ~$407M (04/27/2026) |
| 30-Day SEC Yield | 0.38% (as of 03/31/2026) |
| Distribution Frequency | Annual (December) |
| Cayman Subsidiary | Yes |

## Investment case

For every $1 invested, RSST is designed to provide **$1 of large-cap U.S. equity exposure** and **$1 of a managed futures (trend) strategy**.

Three pillars (verbatim positioning from product page):

1. **Capital Efficiency** — simultaneous $1 + $1 exposure in a single ticker.
2. **Diversification** — managed futures has historically exhibited low correlation to both stocks and bonds.
3. **Inflation Hedging** — with the ability to go long and short global futures markets (equities, bonds, commodities, currencies), trend has historically exhibited inflation-hedging characteristics.

## Mechanics

### U.S. Equity sleeve ($1)
Can hold U.S. equities, U.S. equity ETFs (typically SPYM — SPDR Portfolio S&P 500 ETF), and U.S. equity index futures (S&P 500 E-Mini), or any combination thereof.

**Example construction:** 75% SPYM + 25% S&P 500 E-Mini futures.

### Managed Futures sleeve ($1)
Implements the trend-replication framework (see `/concepts/trend-replication.md`):
- **30%** allocated to top-down replication
- **70%** allocated to bottom-up replication
- Trades ~27 global futures markets across equities, fixed income, commodities, and currencies
- Long and short positions, sized by recent volatility for risk balance

### Operational details
- **Rebalances:** daily
- **Cayman Subsidiary:** futures positions held inside a Cayman CFC for RIC tax-qualifying-income compliance
- **Bond exposure inside the trend stack** can adjust the fund's net duration profile (long bond futures = added duration; short bond futures = reduced duration)

## FAQs (from product page)

### How does RSST get its exposure to U.S. equities?
Holdings can include U.S. equities, U.S. equity ETFs, and U.S. equity index futures. Example: 75% large-cap U.S. equity ETF + 25% S&P 500 E-Mini. The Managed Futures strategy will *also* have long or short positions in U.S. equity index futures, increasing or decreasing net equity exposure dynamically.

### What proportion is given to each replication approach?
30% top-down + 70% bottom-up.

### What is the expected risk profile?
Joint inception 12/31/1999 – 7/31/2023:
- S&P 500 TR realized vol: ~15.5%
- SocGen Trend Index realized vol: ~13.5%
- Equal-weight 200%-levered combo (financed at Bloomberg Short-Term Treasury TR): realized vol of **19.2%**

### Is RSST tax efficient?
Daily gains and losses in futures contracts may be calculated as realized for tax purposes, which may affect ordinary income or capital gains depending on the contract. Consult a tax advisor.

### How often does RSST make distributions?
Annually at calendar year-end, if any.

## Performance (as of 03/31/2026, NAV)

| Period | RSST NAV | S&P 500 TR |
|---|---|---|
| 1 Month | -7.65% | -4.98% |
| 3 Month | +0.09% | -4.33% |
| 6 Month | +8.12% | -1.79% |
| YTD | +0.09% | -4.33% |
| 1 Year | +29.63% | +17.80% |
| Since Inception (cumulative) | +44.57% | +50.31% |
| Since Inception (annualized) | +15.42% | +17.18% |

## Recent positioning (snapshot 04/27/2026 — illustrative; changes daily)

**Equity sleeve:** ~75% SPYM + ~30% S&P 500 E-Mini futures.

**Trend stack — representative long/short positions** (% of NAV, approximate):
- **Long:** S&P/TSX 60, FTSE 100, NASDAQ 100, AUD/USD, EUR/USD, copper, gold, energies (WTI, Brent, gasoline, gasoil, heating oil, natural gas)
- **Short:** US 2Y/5Y/10Y futures, Euro Bund, UK Long Gilt, JPY/USD, CAD/USD

## Pitch language (verbatim, for reuse)

> "For every $1 invested, RSST is designed to provide $1 of large-cap U.S. equity exposure and $1 of a managed futures strategy."

> "RSST seeks to provide exposure to a managed futures strategy that has historically exhibited low correlation to both stocks and bonds."

> "With the ability to go both long and short global futures markets (including equities, bonds, commodities, and currencies), managed futures has historically exhibited inflation-hedging characteristics."

## Compliance / risk notes

**Material risks** (from prospectus):
- **Leverage Risk** — investors could lose all or substantially all of their investment if trading positions suddenly turn unprofitable. NAV more volatile and sensitive to market moves.
- **Cayman Subsidiary Risk** — subsidiary not registered under the 1940 Act.
- **Commodity-Linked Derivatives Tax Risk** — RIC qualifying-income concerns.
- **Commodity Pool Regulatory Risk** — fund deemed a commodity pool, subject to CFTC rules.
- **Non-Diversification Risk** — fund may invest a larger percentage of assets in fewer issuers.
- **Foreign and Emerging Markets Risk, Currency Risk, Underlying ETFs Risk, New Fund Risk.**

## Management

**Investment Adviser**
Tidal Investments LLC serves as investment adviser to the Fund and the Subsidiary.

**Investment Sub-Advisers**
Newfound Research LLC serves as investment sub-adviser to the Fund.
ReSolve Asset Management Inc. serves as investment sub-adviser to the Fund and the Subsidiary.

**Futures Advisor**
ReSolve Asset Management SEZC (Cayman) serves as futures advisor to the Fund and the Subsidiary.

**Distributor**
Foreside Fund Services, LLC

> Note: per the current prospectus, RAM is listed as "investment sub-adviser" (not "non-discretionary investment sub-adviser") for RSST — different from the other Return Stacked® US ETFs. Verify with compliance before relying on this distinction in client-facing copy.

## Resources
- Presentation, Factsheet, Product Brief, Quarterly Commentary on returnstackedetfs.com
- Advisor Guide: "Managed Futures Advisor Guide" (HubSpot documents)
- Whitepaper: "Filling the Gap: Enhancing Traditional Stock and Bond Portfolios with a Managed Futures Stack" (returnstacked.com)
