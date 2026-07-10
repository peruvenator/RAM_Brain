# Futures Yield / Carry Strategy

Used in: **RSSY** (U.S. Stocks & Futures Yield), **RSBY** (Bonds & Futures Yield).

## The intuition

Asset returns can be decomposed into two sources:

1. **Price appreciation** — what most investors focus on (the asset's price goes up or down).
2. **Yield (a.k.a. carry)** — the expected return assuming the asset's price *doesn't change*. It captures the economic benefit of simply holding the asset minus the costs of holding it.

A bond's yield, a stock's dividend, gold's storage cost (negative carry), the front-month-to-back-month spread on a commodity futures contract — all are expressions of carry.

Futures yield strategies seek to **maximize exposure to this second component of returns** by going long markets where carry is positive and large, and short markets where carry is negative.

## Why carry deserves a strategy

Across asset classes and decades of data, carry has been one of the most robust documented risk premia. It works in a similar way to value investing: instead of picking *cheap* assets, you pick assets where you get *paid* to hold them. The size and direction of carry varies dynamically across markets and over time.

Crucially, carry is **directionally agnostic** — at any given moment, the strategy might be long energies and short metals, or long equities and short bonds. Because it doesn't trade off price trend, it has historically had **low average correlation to both stocks and bonds *and* to trend-following**. That makes it a genuine third-leg diversifier alongside trend.

## How the strategy is built

The futures yield strategy in RSSY and RSBY invests long and short across:
- **Commodities** (energies, metals)
- **Currencies** (G10 vs. USD)
- **Bonds** (developed-market sovereigns)
- **Equities** (developed-market index futures)

Position sizing reflects risk-adjusted carry scores. The strategy ranks each market's carry (after adjusting for the market's recent volatility) and goes long the highest-ranked markets, short the lowest-ranked markets, sizing positions so that each asset class contributes roughly equal risk to the portfolio.

## Recent positioning examples (snapshot — illustrative only)

These shift continuously as carry across markets changes:

**Common longs in current environments:** AUD, GBP (often have positive yield differentials vs. USD); long-dated bonds when curves are positively sloped; energies in backwardation; cross-listed equity indices when their dividend yield exceeds local rates.

**Common shorts:** JPY (when negative-rate-policy regime persists); CAD (during commodity rolls); short-dated bonds when curves are inverted; commodities in contango (typical for natural gas, sometimes industrial metals).

## Why pair carry with trend?

Trend (RSST/RSBT) and carry (RSSY/RSBY) target *different* characteristics of the same futures markets:
- Trend asks "which way is this market moving?"
- Carry asks "what return do I get if nothing moves?"

These two signals are largely uncorrelated to each other, so combining them improves the diversification of an alternatives sleeve. An advisor running a 50/50 RSST/RSSY pair (or RSBT/RSBY) gets two distinct alternative return streams in addition to the doubled-up base exposure — three sources of return per dollar invested.

## Carry's regime sensitivity

Carry can outperform in low-volatility, slow-moving environments where trend struggles. Trend can outperform in fast-moving directional environments where carry signals are noisy. The two together help smooth the alternative sleeve's experience across regimes.

## Risks specific to carry

- **High portfolio turnover** — carry signals shift, so positions rotate frequently.
- **Illiquid investments at times** — depending on which markets are being traded.
- **Carry trades can crash** — historically, popular currency carry trades have unwound violently during global risk-off events. Position sizing and risk management aim to mitigate this, but it's a known strategy-level risk.
