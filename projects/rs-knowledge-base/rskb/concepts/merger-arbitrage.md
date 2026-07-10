# Merger Arbitrage

Used in: **RSBA** (Bonds & Merger Arbitrage). Tracks the **AlphaBeta Merger Arbitrage Index**.

## The strategy in one sentence

Merger arbitrage involves investing in companies engaged in **announced** M&A deals and capturing the spread between the trading price and the deal price.

## The mechanics

1. After a deal is **announced**, the target company's stock typically trades *below* the announced deal price — a discount that reflects the risk that the deal may not close (regulatory, financing, shareholder vote, antitrust, etc.) plus a time-value adjustment for the wait until close.
2. The arbitrageur **buys the target's stock** at this discount.
3. If the deal is a **stock-for-stock** transaction, the arbitrageur **shorts the acquirer's stock** in the agreed exchange ratio. This locks in the spread regardless of where the acquirer's stock moves post-announcement.
4. If the deal is **all cash**, no acquirer hedge is needed — the arbitrageur just collects the cash payment at deal close.
5. If the deal closes successfully, the spread is captured. If it breaks, the target stock typically falls back toward its pre-announcement price — that's the deal-break risk being compensated.

## Why it's a distinct risk premium

Merger arbitrage returns are driven by:
- **Deal-break risk** (the deal fails) — which is uncorrelated with broad market direction
- **Deal-completion timing** (the deal takes longer than expected) — also uncorrelated
- **Spread compression** (the discount narrows as time-to-close approaches)

Because the dominant risk factor is *deal-specific*, merger arb has historically exhibited:
- **Low average correlation to stocks and bonds**
- **Only moderate correlation to credit risk**
- **Lower drawdowns than equities during corrections**

This is what makes it a credible *fixed-income diversifier* — not because it behaves like a bond (it doesn't), but because its return drivers are different from credit and duration.

## Why pair it with bonds (RSBA)?

For investors holding fixed-income sleeves looking for yield enhancement, the typical move is to take *more credit risk* — go down in quality, longer in duration, or into less liquid sub-segments. The problem is that all of those introduce equity-correlated downside during stress.

Merger arbitrage is positioned as an **alternative to credit risk**: it offers an additional return stream with low correlation to credit, lower drawdowns during equity corrections, and a strong theoretical foundation (it's compensating real economic risk, not just term premium).

## How RSBA implements the sleeve

- The merger arbitrage sleeve seeks to **track the AlphaBeta Merger Arbitrage Index** rather than running fully discretionary stock-picking. This gives systematic, rules-based exposure to the strategy.
- The Index rebalances on an **event-driven basis** (when new deals are announced or existing deals close).
- RSBA holdings include long positions in target companies in active deals (recent examples: Webster Financial, Penumbra, Chart Industries, Masimo) and short positions in acquirers when deals are stock-for-stock.

## Key risks

- **Deal-break risk** — the central risk of the strategy. If a deal fails, the target's stock typically drops sharply.
- **Regulatory risk** — antitrust review, especially for large deals or in concentrated industries.
- **Concentration in active deal flow** — when M&A activity is high, the strategy has more opportunities; when low, opportunity set narrows and spreads compress.
- **Deal-spread compression** — when many arbitrageurs are crowding in, spreads can be tight.

## Compliance language

> "Merger-arbitrage investing involves the risk that the outcome of a proposed event, whether it be a merger, reorganization, or other event, will prove incorrect and that the Fund's return on the investment will be negative, or that the expected event may be delayed or completed on terms other than those originally proposed, which may cause the Fund to lose money or fail to achieve a desired rate of return."

## Resources

- **Whitepaper:** "Boosting Bonds: Stacking Merger Arbitrage to Enhance Fixed Income Portfolios" (returnstacked.com)
- **Advisor guide:** "Merger Arbitrage Advisor Guide" (HubSpot documents)
