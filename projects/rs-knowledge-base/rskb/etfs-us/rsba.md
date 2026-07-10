# RSBA — Return Stacked® Bonds & Merger Arbitrage ETF

## At a glance

| Field | Value |
|---|---|
| Ticker | RSBA |
| CUSIP | 88636R586 |
| Primary Exchange | CBOE |
| Wrapper | ETF |
| Jurisdiction | USA |
| Inception | December 17, 2024 |
| Gross Expense Ratio | 0.96% |
| **Net Expense Ratio** | **0.68%** (waiver in effect) |
| Net Assets | ~$52M (04/15/2026) |
| 30-Day SEC Yield | -0.45% (as of 03/31/2026) |
| Distribution Frequency | Annual (December) |
| Cayman Subsidiary | Not required (no commodity futures) |

## Investment case

For every $1 invested, RSBA is designed to provide **$1 of U.S. Treasury exposure** and **$1 of a merger arbitrage strategy**.

Three pillars:

1. **Capital Efficiency** — simultaneous $1 + $1 exposure to Treasuries and merger arb.
2. **Diversification** — merger arbitrage has historically exhibited low average correlations to bonds.
3. **Alternative to Credit** — merger arb has a strong theoretical foundation as a risk premium, presenting a compelling diversifier to credit exposure with only moderate correlation to credit risk on average and lower drawdowns during equity market corrections.

## Mechanics

### Bond sleeve ($1)
**Predominantly implemented via a U.S. Treasury futures ladder** (rather than ETFs/cash bonds, unlike RSBT/RSBY):
- 25% U.S. 2-Year Treasury futures
- 25% U.S. 5-Year Treasury futures
- 25% U.S. 10-Year Treasury futures
- 25% U.S. Long Bond futures

**Effective duration:** approximately tracks the Bloomberg U.S. Treasury Total Return Index.

Why futures-heavy? Treasury futures are the most capital-efficient way to express duration exposure, freeing the entire underlying $1 of cash to fund the merger arb sleeve.

### Merger Arbitrage sleeve ($1)
Seeks to **track the AlphaBeta Merger Arbitrage Index**.

The strategy:
1. Buys target company stocks at a discount to their announced deal price
2. For stock-for-stock deals, hedges by shorting the acquirer in the agreed exchange ratio
3. For all-cash deals, holds long target only and waits for deal close
4. Captures the spread between trading price and deal price as the deal progresses to close

See `/concepts/merger-arbitrage.md` for full strategy detail.

**Rebalancing:** Index rebalances on an event-driven basis (when new deals are announced or existing deals close). The fund itself rebalances daily.

## FAQs (from product page)

### How often does RSBA rebalance?
RSBA rebalances daily. The AlphaBeta Merger Arbitrage Index, which the merger arbitrage strategy seeks to track, rebalances on an event-driven basis.

### How does RSBA get its exposure to U.S. Treasuries?
The Bond strategy can hold U.S. Treasuries, U.S. Treasury ETFs, and U.S. Treasury futures, or any combination. It is expected that RSBA will *predominantly* get its exposure through U.S. Treasury futures via a ladder of contracts.

### What is the effective duration of the Bond strategy?
Approximately tracks the Bloomberg U.S. Treasury Total Return Index.

### What is Merger Arbitrage?
Merger Arbitrage involves investing in companies involved in announced merger & acquisition deals. The strategy involves capturing the spread between the trading price and the deal price by:
1. Purchasing stock of the target at a discount
2. Hedging by shorting the acquirer (unless cash deal)

The strategy focuses on legally binding merger situations after they've been announced.

### How often does RSBA make distributions?
Annually at calendar year-end, if any.

## Performance (as of 03/31/2026, NAV)

| Period | RSBA NAV | Bloomberg US Treasury |
|---|---|---|
| 1 Month | -1.81% | -1.74% |
| 3 Month | -0.67% | -0.04% |
| 6 Month | +0.58% | +0.86% |
| YTD | -0.67% | -0.04% |
| 1 Year | +4.19% | +3.25% |
| Since Inception (cumulative) | +7.25% | +5.53% |
| Since Inception (annualized) | +5.60% | +4.28% |

## Recent positioning (snapshot 04/16/2026 — illustrative)

**Treasury sleeve:** 25% each in 2Y, 5Y, 10Y, Long Bond futures.

**Merger arb sleeve — representative active deal positions:**
- **Long targets:** Webster Financial (WBS), Penumbra (PEN), Chart Industries (GTLS), Masimo (MASI), Clear Channel Outdoor (CCO), DigitalBridge (DBRG), Brighthouse Financial (BHF), Talkspace (TALK), Cantaloupe (CTLP)
- **Short acquirers:** Boston Scientific (BSX), Banco Santander (SAN)

## Pitch language (verbatim)

> "For every $1 invested, RSBA is designed to provide $1 of exposure to U.S. Treasuries and $1 of exposure to a merger arbitrage strategy."

> "With a strong, theoretical foundation as a risk premium, merger arbitrage strategies can present a compelling diversifier to credit exposure, historically exhibiting only a moderate correlation to credit risk on average and lower drawdowns during equity market corrections."

## Compliance / risk notes

- **Merger-Arbitrage Risk** — proposed deals may fail, complete on different terms, or be delayed; can cause negative returns
- **Leverage Risk, Bond Risk, Credit Risk, Currency Risk, Foreign and Emerging Markets Risk, Non-Diversification, Underlying ETFs Risk, New Fund Risk**
- **High Portfolio Turnover Risk, Illiquid Investments Risk**

## Management

**Investment Adviser**
Tidal Investments LLC ("Tidal" or the "Adviser") serves as investment adviser to the Fund.

**Investment Sub-Advisers**
Newfound Research LLC ("Newfound") serves as investment sub-adviser to the Fund.
ReSolve Asset Management Inc. ("RAM") serves as a non-discretionary investment sub-adviser to the Fund.

**Distributor**
Foreside Fund Services, LLC

## Resources
- Presentation, Factsheet, Product Brief, Quarterly Commentary on returnstackedetfs.com
- Advisor Guide: "Merger Arbitrage Advisor Guide" (HubSpot)
- Whitepaper: "Boosting Bonds: Stacking Merger Arbitrage to Enhance Fixed Income Portfolios"
