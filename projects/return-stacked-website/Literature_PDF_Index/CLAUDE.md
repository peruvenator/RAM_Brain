# Literature PDF Index — Claude Workflow

Redesign of the Literature page on returnstackedetfs.com. Standalone HTML mockups for handoff to the web designer (WordPress + Divi site).

## Active File

- `literature-option-d.html` is the deliverable. Iterate on this one.
- A/B/C are reference-only earlier mockups; do not edit them.

## How to Preview

- Open `literature-option-d.html` directly in a browser. No build step, no dev server.
- All CSS is inline and scoped under `#rs-literature` to avoid Divi conflicts.
- JS is a single `rsLitSwitchTab()` function.

## Architecture

- Container: single `<div id="rs-literature">` block. Everything CSS/JS-namespaced under it.
- Search bar at top (`#rs-lit-search`) and tag chips (`#rs-lit-filters`) filter all content in real time. Chips are single-select — clicking an active chip deactivates it; clicking another chip swaps the selection.
- Page is split into two compliance-driven sections (no tabs):
  - **Product Literature** (`#rs-section-product`) — Presentations, Product Briefs, Quarterly Commentaries, Foundational Guides
  - **Manager Research** (`#rs-section-research`) — One Pagers, White Papers, Advisor Guides
- A "Start Here" featured row sits above both sections and cross-cuts the compliance split (Primer + Case Studies Guide + Leverage). Featured cards also respond to filters.
- Page banner is NOT in this file — handled by Divi page title natively. The header comment block has the embedding instructions for the designer.
- Font: DM Sans, loaded via Google Fonts link. In Divi embed the theme already loads it.

## Section Allocation Rule (Compliance)

Compliance requires bifurcation between product-specific materials and manager research content.

**Product Literature** = any of:
- Presentations (including the Return Stacked Primer Presentation)
- Product Briefs
- Quarterly Commentaries
- "Guide: Leverage For the Long Run"
- "Keeping What Works, Adding What's Missing"

**Manager Research** = everything else:
- "Why We Stack" one-pagers (the series)
- "Guide to Client Conversations" series
- White papers
- "Managed Futures Carry: A Practitioner's Guide"
- "Bulls Vs Bears" (reclassified as White Paper for the type taxonomy)
- "Stacking 101: Your Mortgage"
- "Return Stacked All-Terrain Portfolio Primer"
- "Guide: Top Return Stacking Case Studies"

When adding a new doc, place it on the right side of this split FIRST, then decide which tile within that section.

## Row Metadata

Every row carries two hidden attributes used by the filter:

- `data-tags="..."` — space-separated slugs from the controlled taxonomy below. Filter chips match against these.
- `data-keywords="..."` — free-text search terms (synonyms, themes, related concepts not in the title). Search input matches against `textContent + data-keywords`.

Featured "Start Here" cards carry the same attributes on the `<a class="featured-card">` element. Doc-list and product-list rows carry them on the `<li>`.

## Tag Taxonomy

Slugs are stable; display labels can change without breaking the filter.

| Group | Slug | Display |
|---|---|---|
| Strategy | `trend` | Trend |
| Strategy | `carry` | Futures Yield (Carry) |
| Strategy | `mergarb` | Merger Arbitrage |
| Strategy | `bonds` | Bonds |
| Strategy | `us-equity` | U.S. Equity |
| Strategy | `intl-equity` | International Equity |
| Strategy | `gold` | Gold |
| Strategy | `bitcoin` | Bitcoin |
| ETF | `rsst` `rsit` `rssy` `rssx` `rsbt` `rsby` `rsba` `rssb` | (ticker) |

There is no Type chip group — content type is communicated by which tile a row lives in. Type slugs (`presentation`, `advisor-guide`, `whitepaper`, `onepager`, `commentary`) are still maintained on rows as metadata in case the filter is reintroduced, but they are not currently surfaced as chips.

### Tagging Rules (Compliance-Driven)

These rules keep the Product Literature / Manager Research compliance split clean when users filter:

1. **Strategy slugs** apply to any row, in either section.
2. **ETF slugs** apply ONLY to rows in the Product Literature section. They must never appear on a Manager Research row, even if that row is conceptually related to an ETF. Selecting an ETF chip should never surface manager research content.
3. **Quarterly Commentaries** carry all 8 ETF slugs (commentaries cover every ETF) so an ETF chip still surfaces them.
4. **Foundational Guides** (Leverage, Keeping What Works) and the Primer Presentation carry no ETF slugs — they're conceptually all-ETF but are not ETF-specific docs, so an ETF chip should not surface them. (The strategy chip will still surface them if their strategy matches.)
5. `data-keywords` should include synonyms and themes a user might text-search for. Do not include ETF tickers in the keywords of Manager Research rows — that would let an "RSST" text search surface manager research, defeating the compliance separation.

Notes:
- `RSIT` is in the chip set but no rows currently carry it — placeholder for upcoming product. Selecting it shows the empty state.

## JS Functions (namespaced)

- `rsLitFilter()` — combined search + tag filter over the whole page. Tokenizes `#rs-lit-search` value via `rsLitTokens`, reads the (at most one) `.chip.active` tag, then hides any row/featured-card that fails (query tokens not all present in row search text) OR (the active tag missing from row's data-tags). Cascades up: hides tiles when no rows remain, hides whole `.section-block` when no tiles remain, shows `.no-results` when nothing matches anywhere.
- `rsLitElementMatches(el, queryStems, activeTags)` — predicate used by rsLitFilter. AND across every query stem and every active tag. Each query stem must prefix-match some text stem; tag membership must match exactly.
- `rsLitStem(word)` / `rsLitTokens(text)` — light stemmer + tokenizer used on both query and searchable text. Stemmer drops trailing `s` (except `ss`/`us`) and converts `ies` → `y`. Keeps "briefs"≈"brief", "guides"≈"guide", "commentaries"≈"commentary" matching.
- `rsLitSearchText(el)` — assembles searchable text for a row: `textContent + data-keywords + data-tags + parent .cat-tile-name + parent .cat-tile-desc`. `data-tags` inclusion is what lets featured "Start Here" cards match searches like "advisor guide" (those cards live outside any `.cat-tile`, so tile-name fallback doesn't apply to them). Tile name/desc inclusion is what lets a search for "advisor guides" surface every row inside the Advisor Guides tile.
- `rsLitToggleTag(chip)` — single-select toggle. Clicking an inactive chip deactivates any currently active chip and activates this one; clicking the active chip deactivates it.
- `rsLitClearSearch()` — resets search input.
- `rsLitClearTags()` — deselects all chips.

(No `rsLitSwitchTab` — the tabs were removed in the compliance restructure.)

## Design Decisions (locked in unless requested otherwise)

- Subsection dividers: inline floating chip on a hairline rule (`.doc-divider` / `.doc-divider-chip`). Do not switch to gray section backgrounds.
- Equal-weight typography across all doc rows. No grayed-out commentary/case study rows.
- Type badges (`.doc-badge`) on every row in By Stack view.
- Strategy tags (`.strat-tag`) on every row in By Content Type view (replace type badges).
- Product tiles use ticker-first layout (`.product-row` / `.product-ticker`).
- All external links: `target="_blank" rel="noopener"`.

## Brand Tokens (inline in CSS variables)

- Teal `#14cfa6` (primary accent), Navy `#283742` (tile headers, text), Blue `#3f73ab` (secondary).
- Light BG `#f7f6f6`, Border `#d9d9d9`.
- Match site palette exactly — do not introduce new colors without checking the returnstacked.com brand.

## Open Items (as of 2026-06-30)

- One link kept as `href="#"` because no PDF exists yet:
  - "Keeping What Works, Adding What's Missing"
- "Guide: Top Return Stacking Case Studies" (in both Advisor Guides and the featured Case Studies card) points to `https://investresolve.com/inc/uploads/pdf/The-Return-Stacking-How-To-Guide.pdf` as of 2026-06-30.
- Gold/Bitcoin "Guide to Client Conversations" currently points to the same HubSpot doc ID as the Leverage guide (`1606656861`). This is likely a live-site error inherited from the PDF source. Verify with marketing before fixing.
- Product Briefs and Product Presentations both point to the ETF product page URL. If discrete brief/deck URLs become available, swap them in.

## URL Source of Truth

Confirmed URL mapping for every link is in the memory file `project_rs_literature_page.md`. If a link looks wrong, check that first before assuming the HTML is the source of truth.

## Handoff

Final destination is the live Literature page on returnstackedetfs.com (WordPress + Divi). The web designer pastes the contents of `<div id="rs-literature">` plus the `<style>` and `<script>` blocks into a Divi Code module inside a regular section. Page banner is built natively in Divi.

## Do Not

- Add a build pipeline. This is a single self-contained HTML file by design.
- Add external JS dependencies. Vanilla JS only.
- Rename CSS variables or break the `#rs-literature` scoping (would conflict with Divi).
- Touch A/B/C files unless explicitly asked.
