---
name: rs-etfs-knowledge-base
description: Knowledge base for the Return Stacked® ETF lineup, RDMIX mutual fund, Canadian ETFs (RGBM, RGBM.U), and Quantify partner funds. Use whenever the user references any of these tickers (RSST, RSBT, RSSB, RSSY, RSBY, RSBA, RSSX, RGBM, RGBM.U, RDMIX, RDMAX, RDMCX, BTGD, ISBG, ISSB) or asks about return stacking, capital efficiency, managed futures replication, futures yield (carry), merger arbitrage, or systematic macro. Also triggers on sponsor names (Tidal, Newfound, ReSolve, LongPoint, Rational, Quantify) and product-page URLs (returnstackedetfs.com, returnstackedetfs.ca, returnstackedfunds.com, quantifyfunds.com). Use for writing product briefs, FAQs, advisor explainers, social copy; fact-checking tickers/CUSIPs/inception/expense ratios; comparing funds; or explaining how a Stack is constructed. Provides compliance-approved pitch language and the RDMIX predecessor-fund disclosure.
---

# Return Stacked® Knowledge Base — Skill Instructions

## What this skill provides

A structured, team-maintained reference covering every product in the Return Stacked® lineup plus the closely-affiliated Quantify partner funds. This is the canonical source of truth for product positioning, mechanics, fees, sponsor structure, and compliance-approved language.

## How to navigate the KB

When this skill is invoked, follow this flow:

1. **For lineup-wide questions** ("what's in the Return Stacked lineup?", "compare RSST and RSBT", "which Stack pairs with bonds?"): start with `overview.md`.

2. **For a specific product** (any ticker mentioned): open the matching file:
   - U.S. ETFs → `etfs-us/{ticker}.md`
   - Canadian ETFs → `etfs-canada/rgbm.md` or `etfs-canada/rgbm-u.md`
   - Mutual fund → `mutual-funds/rdmix.md` (covers all three share classes RDMIX/RDMAX/RDMCX)
   - Partner funds → `partner-funds/{ticker}.md`

3. **For concept-level explainers** (what *is* return stacking, how does trend replication work, what is carry, what is merger arb): open the matching file in `concepts/`.

4. **For sponsor / adviser structure**: end of `overview.md`.

5. **For refresh cadence and update workflow**: `update-process.md`.

6. **For canonical URLs of every product page**: `urls.yaml` (used by the live-data refresh protocol below).

## Live Data Refresh Protocol

Time-sensitive figures (AUM/net assets, NAV, 30-Day SEC Yield, current holdings, performance, premium/discount, median spread) **must be fetched live before being quoted in any client-facing or published content.** The KB stores dated snapshots, not live values.

### The provenance constraint

The `web_fetch` tool only accepts URLs that have either:
- Been provided directly by the user in the conversation, OR
- Appeared in the results of a prior `web_search` or `web_fetch` call.

URLs read from `urls.yaml` via the `view` tool **do not** establish provenance. Attempting `web_fetch` on a URL that hasn't been "introduced" returns a `PERMISSIONS_ERROR`.

### Standard refresh path (use this first)

For any U.S. ETF, Canadian ETF, or RDMIX:

1. **Look up the canonical URL** in `urls.yaml` (or use the table at the bottom of this section).
2. **Establish provenance** with a targeted search. Use the ticker plus a `site:` operator if needed:
   - `web_search` with query like `RSBY returnstackedetfs.com` or `RSBY site:returnstackedetfs.com`
   - The first result will be the product page, surfacing the URL into provenance.
3. **Fetch the page** with `web_fetch` on the URL from `urls.yaml` (now permitted).
4. **Extract the field(s) needed** (Net Assets, NAV, expense ratios, 30-Day SEC Yield, etc.) directly from the rendered page text.
5. **Cite "as of" date** from the page in any user-facing output.

This works for all four ReSolve-affiliated domains (`returnstackedetfs.com`, `returnstackedetfs.ca`, `returnstackedfunds.com`) and for Quantify (`quantifyfunds.com`).

### Alternate path: user-provided URL

If the user pastes a URL into chat, that URL has direct provenance — go straight to `web_fetch`. No search step needed.

### Alternate path: bash helper for Quantify pages

For partner funds (BTGD, ISBG, ISSB) **only**, a Python helper at `scripts/fetch_live_data.py` provides structured extraction via direct HTTP:

```bash
python scripts/fetch_live_data.py BTGD --raw
```

This returns JSON with extracted fields plus cleaned page text. **Does not work for ReSolve domains** — those pages are behind SiteGround's bot-challenge layer, which `requests` cannot bypass. Use the Standard Refresh Path instead.

The helper is also useful in Claude Code sessions on the Mac mini / desktop, where `requests` may have access through a configured browser-spoofing path that this sandbox lacks.

### When NOT to refresh

Skip the live refresh and use KB values for: CUSIPs, inception dates, gross/net expense ratios (only re-check at prospectus updates — typically May 1 annually), sponsor structure, pitch language, fund mechanics descriptions, ticker symbols, naming conventions.

### Quick URL reference (mirror of urls.yaml)

| Ticker | Canonical URL |
|---|---|
| RSST | https://www.returnstackedetfs.com/rsst-return-stacked-us-stocks-managed-futures/ |
| RSBT | https://www.returnstackedetfs.com/rsbt-return-stacked-bonds-managed-futures/ |
| RSSB | https://www.returnstackedetfs.com/rssb-return-stacked-global-stocks-bonds/ |
| RSSY | https://www.returnstackedetfs.com/rssy-return-stacked-u-s-stocks-futures-yield-etf/ |
| RSBY | https://www.returnstackedetfs.com/rsby-return-stacked-bonds-futures-yield/ |
| RSBA | https://www.returnstackedetfs.com/rsba-return-stacked-bonds-merger-arbitrage/ |
| RSSX | https://www.returnstackedetfs.com/rssx-return-stacked-us-stocks-gold-bitcoin/ |
| RGBM | https://www.returnstackedetfs.ca/rgbm/ |
| RGBM.U | https://www.returnstackedetfs.ca/rgbm-u/ |
| RDMIX | https://www.returnstackedfunds.com/rdmix/ |
| BTGD | https://www.quantifyfunds.com/funds/btgd/ |
| ISBG | https://www.quantifyfunds.com/funds/isbg/ |
| ISSB | https://www.quantifyfunds.com/funds/issb/ |

If a slug changes, update `urls.yaml` and this table together.

## Critical rules when generating content

### Always verify time-sensitive numbers

Performance, NAV, AUM, holdings, risk allocations, and 30-Day SEC Yield change frequently. The KB includes dated snapshots. **Before publishing any content that quotes these figures, follow the Live Data Refresh Protocol above.**

### RDMIX predecessor fund disclosure is mandatory

When generating any content for RDMIX that uses long-dated track record, the predecessor fund disclosure block (in `mutual-funds/rdmix.md`) **must be included verbatim**. The fund changed strategy on 2/27/2018 *and* again on 1/1/2025. Compliance officer Marissa Ciancio has reviewed the canonical language — do not paraphrase it.

### Pitch language sections are compliance-approved verbatim copy

Every product file has a "Pitch language (verbatim)" section. These quotes are lifted directly from the public product pages and represent compliance-approved phrasing. They can be reused or remixed in marketing copy without re-deriving language.

### Branding rules

- "Return Stacked®" — registered trademark; use the ® on first reference in formal copy
- "STKd" — derivative brand licensed to Quantify; use on Quantify product references (BTGD, ISBG, ISSB)
- Naming hierarchy: umbrella ("Return Stacked® ETFs") → formal ("Return Stacked® U.S. Stocks & Managed Futures ETF") → ticker ("RSST")
- The Quantify partner funds are *not* Return Stacked® ETFs — they are partner funds that use the STKd derivative brand under license. Do not refer to them as "Return Stacked® ETFs."

### Wrapper distinctions matter

- **RSSB** is the only Return Stacked® ETF *without* a Cayman Subsidiary (no commodity futures held); also the only one with a fee waiver in effect.
- **RGBM / RGBM.U** are technically *alternative mutual funds* in Canada, not pure ETFs. They use a corporate-class structure for tax efficiency.
- **RDMIX** is a *mutual fund*, not an ETF — has share classes (I/A/C), sales loads on A, CDSC on C.
- **RGBM.U** hedges Canadian-dollar bond exposure to USD; RGBM does not hedge.

## Common content tasks and where to start

| Task | Start here |
|---|---|
| "Explain what Return Stacking is" | `concepts/return-stacking-101.md` |
| "Write a product brief for RSBT" | `etfs-us/rsbt.md` + `concepts/trend-replication.md` |
| "Compare RSST vs RSSY" | `etfs-us/rsst.md` + `etfs-us/rssy.md` + `concepts/trend-replication.md` + `concepts/carry-yield.md` |
| "FAQ about RSSB for advisors" | `etfs-us/rssb.md` |
| "Why merger arb in a bond ETF?" | `concepts/merger-arbitrage.md` + `etfs-us/rsba.md` |
| "Talk about gold/bitcoin in a stack" | `etfs-us/rssx.md` (note: NOT BTGD — RSSX is the Return Stacked® product) |
| "RDMIX track record content" | `mutual-funds/rdmix.md` (read the predecessor fund section first!) |
| "What's RGBM and who's it for?" | `etfs-canada/rgbm.md` |
| "USD-denominated Canadian product" | `etfs-canada/rgbm-u.md` |
| "Current AUM / NAV / yield for {ticker}" | Live Data Refresh Protocol above |

## Cross-suite themes (useful for content writing)

When discussing the lineup as a whole, these recurring threads work well:
1. **Capital efficiency** — every dollar does double duty
2. **Diversification without sacrifice** — diversifiers added *on top of* core, not in place of it
3. **Institutional technique, retail wrapper** — concepts going back to the 1980s, packaged in daily-liquid products
4. **Built to diversify, not to displace** — frames each Stack as additive to a traditional 60/40
5. **Refuse to choose** — reject the false dichotomy of "core vs. alternatives"

## What this skill does NOT do

- Does not generate live performance numbers from memory — those must be fetched via the Live Data Refresh Protocol
- Does not replace compliance review for client-facing material — flag work touching RDMIX predecessor disclosures or new product launches for human review
- Does not cover the broader research blog (returnstacked.com/insights) — that's a separate content surface
- Does not include presentations or factsheet PDFs — those should be linked rather than recreated
