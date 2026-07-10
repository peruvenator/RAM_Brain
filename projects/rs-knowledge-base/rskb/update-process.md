# Update Process & Skill Deployment

## Refresh cadence

### What changes daily / monthly (DO NOT hard-code in the KB)
- NAV, AUM, premium/discount, top holdings, risk allocations
- Performance figures (1M / 3M / YTD / 1Y / 3Y / Since Inception)
- 30-Day SEC Yield, distribution amounts
- Carry scores and trend positioning

**Recommendation:** these should be fetched **live** at content-creation time. Claude can pull them directly from `returnstackedetfs.com`, `returnstackedetfs.ca`, `returnstackedfunds.com`, or `quantifyfunds.com` when generating client-facing content. The KB stores the *structure* and *narrative*; the live sites store the *current numbers*.

### What changes occasionally (quarterly)
- New product launches (e.g., RSSX in May 2025; ISBG/ISSB in January 2026)
- Fee waiver expirations / renewals (RSSB has a waiver through May 30, 2026)
- Quarterly commentary publication
- Holdings concentration shifts
- Inception of new share classes

**Recommendation:** quarterly KB refresh. Verify the lineup table, fee waiver dates, AUM rank order, and any new product additions. Add a `CHANGELOG.md` entry per refresh.

### What rarely changes (annual or less)
- Investment strategy / sleeve construction
- Sub-adviser arrangements
- CUSIPs, tickers, exchange listings (unless corporate action)
- Inception dates
- Predecessor fund disclosures (RDMIX — only changes if there's a new strategy revision)

**Recommendation:** annual full rebuild against live product pages. Trigger immediately on any of: new product launch, sub-adviser change, fee structure change, regulatory filing change.

## Suggested refresh workflow (semi-automated)

A fit for the existing RAM_Brain automation patterns:

1. **Scheduled scrape** — Python script (similar to the chart-extraction skill) fetches each product page on a quarterly cadence
2. **Diff against KB** — compare extracted facts (expense ratios, inception, sponsor names, FAQ text) against the canonical KB files
3. **Generate refresh PR** — script emits a Markdown diff or Notion page with proposed changes
4. **Human review:**
   - **Marissa Ciancio** for compliance-language changes (especially RDMIX predecessor fund disclosure)
   - **Rodrigo / Mike / Adam / Corey** for strategic positioning changes
5. **Merge** to canonical KB (whether that lives in Notion, Dropbox, or directly in the skill folder)

## Deployment options

### Option 1 (recommended) — Make this a Claude Skill

**Pros:**
- Any teammate can invoke it from chat, Claude Code, or Cowork without navigating to a Project
- Consistent across surfaces (web, mobile, desktop, terminal)
- Trigger phrase like "look up RSST" or "summarize the Return Stacked lineup" auto-loads the relevant section
- Fits naturally with the existing `RAM_Brain/.claude/skills` setup
- Same sharing mechanism as the weekly RS scorecard skill

**Skill structure:**
```
.claude/skills/rs-etfs-knowledge-base/
├── SKILL.md              ← description with triggers
├── README.md
├── overview.md
├── update-process.md
├── concepts/
│   ├── return-stacking-101.md
│   ├── trend-replication.md
│   ├── carry-yield.md
│   ├── merger-arbitrage.md
│   └── glossary.md
├── etfs-us/
│   ├── rsst.md
│   ├── rsbt.md
│   ├── rssb.md
│   ├── rssy.md
│   ├── rsby.md
│   ├── rsba.md
│   └── rssx.md
├── etfs-canada/
│   ├── rgbm.md
│   └── rgbm-u.md
├── mutual-funds/
│   └── rdmix.md
└── partner-funds/
    ├── btgd.md
    ├── isbg.md
    └── issb.md
```

**SKILL.md description should trigger on:**
- Any ticker symbol: RSST, RSBT, RSBY, RSSY, RSBA, RSSB, RSSX, RGBM, RGBM.U, RDMIX, RDMAX, RDMCX, BTGD, ISBG, ISSB
- Product names: "Return Stacked", "ReturnStacked", "stacked ETF"
- Concepts: "return stacking", "managed futures replication", "futures yield", "carry strategy", "merger arbitrage" (in fund context)
- Sponsor names: "Tidal Investments", "Newfound Research", "ReSolve", "LongPoint", "Rational Advisors", "Quantify"
- Common content tasks: "write a product brief about", "FAQ for", "explain RSSB to an advisor", "compare RSST and RSSY"

### Option 2 — Notion-hosted reference + Claude Project knowledge

**Pros:**
- Human-readable, easy to edit collaboratively
- Fits with existing Notion-centric workflow (RAM_Brain)
- Non-technical team members can update directly in Notion

**Cons:**
- Claude has to fetch it on every use (less reliable trigger)
- Not surface-portable (can't easily use in Claude Code or Cowork)

### Option 3 (recommended for the team) — Hybrid

- **Master content lives in Notion** (so non-technical team members can edit)
- **Sync script** (similar to existing Notion source-file sync) pushes the latest Notion version into the skill folder weekly or on-edit
- **The skill is what Claude actually uses for retrieval** at chat time

This gives the team:
- Easy editing in a familiar tool (Notion)
- Reliable retrieval via the skill mechanism (works in chat, Claude Code, Cowork)
- A single source of truth that stays in sync

## Permissions / sharing model

For the small power-user team currently on Max plans (the same group that uses the weekly RS scorecard skill):
- Distribute the skill via the same mechanism as your existing skills (you've already navigated this with Anthropic regarding skill sharing on Max plans)
- Consider whether some sections (e.g., the Marissa-reviewed RDMIX predecessor disclosure) should be flagged as "approved-language only" vs. "internal reference"

## Open design questions for the skill version

1. **Live data fetching:** should the skill auto-fetch live NAV/AUM/performance from product pages when invoked, or just return the static narrative and prompt the user to confirm with current data? (The cleaner architecture is static narrative + always re-fetch live numbers.)

2. **Compliance modes:** should there be:
   - A "client-facing" mode that returns only compliance-approved language and includes mandatory disclosure blocks?
   - An "internal" mode that includes commentary, positioning context, and competitive notes?

3. **Voice / persona file:** worth adding a `personas.md` that gives Claude voice guidance for each principal (Adam Butler, Mike Philbrick, Corey Hoffstein, Rodrigo Gordillo) so generated content matches the right house style depending on who's publishing.

4. **Refresh trigger:** should the skill self-flag stale data (e.g., "this snapshot is from April 2026; please verify current figures before publishing")?

## Changelog

### 2026-04-28 — Initial knowledge base
- Built from returnstackedetfs.com, returnstackedetfs.ca, returnstackedfunds.com, quantifyfunds.com product pages
- Snapshot data current as of late April 2026
- Includes: 7 U.S. ETFs (RSST, RSBT, RSSB, RSSY, RSBY, RSBA, RSSX), 2 Canadian ETFs (RGBM, RGBM.U), 1 mutual fund (RDMIX/RDMAX/RDMCX), 3 partner funds (BTGD, ISBG, ISSB)
- 5 concept files: return stacking 101, trend replication, carry/yield, merger arbitrage, glossary
- RDMIX predecessor-fund compliance language captured
