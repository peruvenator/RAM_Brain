# Literature Page — Developer Handoff
Branch: master | Revision: 2026-06-30

Redesign of the Literature page on returnstackedetfs.com. Self-contained HTML for embedding into a WordPress + Divi Code module.

## What's new in this revision (2026-06-30)

If you have already embedded an earlier version of this widget, the two changes below are all you need to redeploy:

- **Search is smarter.** Multi-word queries and plurals now work. Previously, "product brief" matched but "product briefs" did not; "quarterly commentary" and "advisor guides" returned nothing. Now all of those work, plus typing a tile name (e.g. "advisor guides") surfaces every doc inside that tile AND any matching Start Here featured card. Implementation: the `<script>` block now includes a light stemmer (`rsLitStem`), a tokenizer (`rsLitTokens`), and a search-text builder (`rsLitSearchText`) that pulls in `textContent`, `data-keywords`, `data-tags`, and (for rows inside a tile) the tile name and description. The matcher signature changed from `rsLitElementMatches(el, query, activeTags)` to `rsLitElementMatches(el, queryStems, activeTags)`. **Copy the entire updated `<script>` block — partial patches won't work.**
- **"Guide: Top Return Stacking Case Studies" link fixed.** Both occurrences (Start Here featured card and the Advisor Guides row) previously had `href="#"`. They now point to `https://investresolve.com/inc/uploads/pdf/The-Return-Stacking-How-To-Guide.pdf` and open in a new tab.
- **New Advisor Guide added.** "The Case for NOT Making Room for Alternatives" was added to Manager Research → Advisor Guides as the **first item** in that tile (tile count is now 8, up from 7). Links to `https://www.returnstacked.com/wp-content/uploads/2026/06/The-Case-For-Not-Making-Room.pdf`.
- **Start Here grid is now 4 cards.** The same doc was added as the second Start Here featured card (immediately to the right of the Primer Presentation). Grid layout changed from `2fr 1fr 1fr` to `2fr 1fr 1fr 1fr` — the Primer remains the visual hero, and the three smaller cards (new doc, Case Studies, Leverage) share the remaining width. Card description: "A shareable primer on return stacking, portable alpha, and the core use cases, written in plain English." Stripe is a navy-to-blue gradient to differentiate it from the existing teal-blue, blue-light, and teal-dark stripes.
- **Divi hardening.** Added `isolation: isolate` to the `#rs-literature` root rule. Renamed two interior section IDs (`section-product` → `rs-section-product`, `section-research` → `rs-section-research`) to avoid potential collisions with Divi page-level IDs. No CSS or JS hooks referenced the old IDs, so this is invisible at runtime.

For a fresh deployment, ignore the above and follow the full instructions below.

## What's in this folder

- `literature-option-d.html` — **the deliverable.** Open in any browser to preview the working widget (search, tag filters, both sections).
- `HANDOFF.md` — this file.
- `literature-option-a.html`, `-b.html`, `-c.html` — earlier design explorations, reference only. Do not embed.

## How to embed in Divi

1. **Build the page banner natively in Divi** (using the site's standard page title pattern). Suggested content:
   - Eyebrow: `Return Stacked® ETFs`
   - Title: `Literature`
   - Tagline: `Our ETFs are designed to stack diversifying strategies on top of core stock and bond exposure, not in place of it.`

2. **Add a regular Divi section below the banner.**

3. **Drop in a single Code module** (fullwidth row recommended).

4. **From `literature-option-d.html`, copy three blocks into that Code module:**
   - The `<style>...</style>` block (everything in the `<head>`)
   - The `<div id="rs-literature">...</div>` block (the entire widget container — everything inside `<body>`)
   - The `<script>...</script>` block (immediately after the widget div)

5. Save and preview. No build step, no dev server, no external dependencies.

## What the widget does

- **Two compliance-driven sections** on a single page (no tabs):
  - **Product Literature** — ETF-specific materials (presentations, briefs, quarterly commentaries, foundational guides)
  - **Manager Research** — educational content from the investment team (one pagers, white papers, advisor guides)
- **"Start Here" featured cards** at the top highlight the three foundational pieces.
- **Search bar** filters all rows in real time by title, keywords, ETF ticker, or topic.
- **Tag chips** (Strategy + ETFs) narrow further. Single-select — only one chip can be active at a time; clicking another swaps the selection, clicking the active chip clears it. Selecting any ETF chip will hide the Manager Research section entirely, by design — that's the compliance separation.
- **Auto-hide cascade:** empty tiles disappear, then empty sections, then a "no results" message shows if nothing matches.

## Design notes (please preserve)

- **CSS is scoped under `#rs-literature`** to prevent collisions with Divi theme styles. Please do not strip or rename this scope.
- **Font:** DM Sans is already loaded by the Return Stacked theme. The Google Fonts `<link>` in the file's `<head>` is for standalone preview only — you can omit it in the Divi paste.
- **Color tokens** (CSS variables at the top of the style block) match the site palette: teal `#14cfa6`, navy `#283742`, blue `#3f73ab`. Don't introduce new colors.
- **External links:** all PDF/HubSpot links open in a new tab (`target="_blank" rel="noopener"`).
- **JS functions are namespaced** with the `rsLit` prefix (`rsLitFilter`, `rsLitToggleTag`, `rsLitClearSearch`, `rsLitClearTags`) so they won't conflict with anything else on the site.

## Open items — please confirm with marketing before launch

One link currently points to `href="#"` because the PDF does not exist yet:

- **"Keeping What Works, Adding What's Missing"** (appears in Product Literature → Foundational Guides)

Please ask marketing for the final URL and swap it in when available.

One link likely needs verification:

- **"Guide to Client Conversations: Gold & Bitcoin"** currently points to the same HubSpot doc ID (`1606656861`) as "Leverage For the Long Run". This was inherited from the source PDF and is most likely a live-site error. Please verify with marketing and swap to the correct doc ID.

One placeholder filter chip:

- **RSIT** appears in the ETF filter chip set as a placeholder for an upcoming product. No docs currently match it (selecting it will show the empty state). Leave it in unless marketing says otherwise.

## Adding new content later

When new docs are published, a row needs:

- A title and a working URL
- A `data-tags` attribute listing relevant strategy slugs (`trend`, `carry`, `mergarb`, `bonds`, `us-equity`, `intl-equity`, `gold`, `bitcoin`) and — if and only if the doc is in the Product Literature section — relevant ETF slugs (`rsst`, `rsit`, `rssy`, `rssx`, `rsbt`, `rsby`, `rsba`, `rssb`)
- A `data-keywords` attribute with synonyms and topics a user might search for that aren't in the title

The strategy/ETF tag slugs are case-sensitive and must match the chip definitions in the filter bar.

**Compliance rule:** Manager Research rows must never carry ETF slugs in `data-tags` or ETF tickers in `data-keywords`. The ETF chip filter is what enforces the product/research separation on the page.

## Contact

Questions: Rodrigo Gordillo, rodrigo.gordillo@investresolve.com
