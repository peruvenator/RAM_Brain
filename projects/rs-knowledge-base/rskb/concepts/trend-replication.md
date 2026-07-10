# Trend Replication Methodology

Used in: **RSST** (U.S. Stocks & Managed Futures), **RSBT** (Bonds & Managed Futures).

## The problem

Single-manager managed futures funds are concentrated bets on one team's process. To get a diversified, "average" exposure to the trend-following category, you'd need to allocate to many managers — operationally infeasible for most retail and even most advisor portfolios.

## The solution: replicate the basket

The Managed Futures sleeve in RSST/RSBT seeks to replicate **a basket of leading trend-following funds** using two complementary techniques: top-down and bottom-up. The blend is **30% top-down + 70% bottom-up**.

## Top-Down Replication (30% weight)

**Analogy:** trying to replicate an active long-term stock-picker's returns by figuring out which portfolio of stocks (with which weights) best tracks their published track record. Use regression on the universe of stocks against the manager's returns; whatever weights minimize tracking error become your replicating portfolio.

**Applied to trend funds:** unlike a long-term stock picker, trend-following funds change positions rapidly. So the replicating portfolio must be re-fit at each daily time-step using the basket's recent returns and returns of the explanatory markets over the preceding days/weeks. Each model fit yields weights for a portfolio of representative markets that, if held over the regression window, minimize tracking error against the benchmark basket.

**Pros:**
- Agnostic of how individual managers run their portfolios
- Adapts naturally to model innovation among managers

**Cons:**
- Can only use most recent data to estimate current positioning
- May miss sudden manager position changes (regression lags)

## Bottom-Up Replication (70% weight)

**Analogy:** if top-down asks "which stocks does this manager own?", bottom-up asks "what *characteristics* does this manager use to pick stocks?" Once you've identified the strategy, you implement it yourself directly.

**Applied to trend funds:** uncovers the underlying strategies the basket uses to form portfolios. Common trend-identification systems include:
- Time-series momentum (asset return relative to its own past)
- Price vs. moving average
- Multiple moving average crossovers
- Breakout systems (price exceeds a recent range)

A blended implementation of these signals across the universe of liquid futures markets gives a "trend-following portfolio" that tracks the basket's behavior on a *strategy* basis rather than a *position* basis.

**Pros:**
- Can use much more historical data → more stable estimates
- Captures sudden weight changes well (signals respond directly to price)

**Cons:**
- Will not necessarily capture genuine model *innovation* among managers (if the basket discovers a new signal, bottom-up won't pick it up until that signal is added to the system)

## Why blend the two?

The two approaches have complementary failure modes:
- Top-down captures manager *innovation* but lags on sudden moves
- Bottom-up captures sudden moves but misses innovation
- A 30/70 blend leans on the more responsive bottom-up engine while keeping a top-down "innovation tracker" running underneath

## Universe traded

Approximately 27 global futures markets across four asset classes:
- **Equities:** S&P 500, NASDAQ 100, S&P/TSX 60, Nikkei 225, FTSE 100, Eurostoxx, DAX
- **Bonds:** US 2Y/5Y/10Y/Long Bond, Euro Bund, UK Long Gilt
- **Currencies:** USD vs. EUR, GBP, JPY, AUD, CAD
- **Energies:** WTI Crude, Brent Crude, Heating Oil, Gasoil, RBOB Gasoline, Natural Gas
- **Metals:** Gold, Silver, Copper

Positions can be long or short. The portfolio is risk-balanced across asset classes and markets, with position sizes scaled by recent volatility (so a single market's daily P&L impact is roughly equal regardless of how volatile it is).

## Expected risk profile

**RSST historical context (12/31/1999 – 7/31/2023):**
- S&P 500 TR realized vol: ~15.5%
- SocGen Trend Index realized vol: ~13.5%
- Equal-weight 200%-levered combo (financed at Bloomberg Short-Term Treasury TR): realized vol of **19.2%** over the period

**RSBT historical context (12/31/1999 – 3/31/2023):**
- Bloomberg US Aggregate realized vol: ~4.0%
- SocGen Trend Index realized vol: ~13.6%
- Equal-weight 200%-levered combo: realized vol of **14.3%** over the period

## Active duration management (RSBT-specific)

In RSBT, the trend stack will go long or short bond futures as bond trends evolve. By design this means: when bond trends are *down*, the trend stack shorts bonds → reducing total portfolio duration. When bond trends are *up*, the trend stack goes long bonds → increasing duration. This lets the product use trend signals to **hedge against duration risk** during rate rises and **lean into duration** during rate falls.
