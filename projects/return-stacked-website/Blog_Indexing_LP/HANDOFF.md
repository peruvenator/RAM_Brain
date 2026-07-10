# Blog Library — Developer Handoff

A filterable, searchable index of every Return Stacked blog post, built as self-contained HTML for embedding into a WordPress + Divi Code module.

## What's in this folder

- `blog-landing-page_divi.html` — **the deliverable and source of truth.** Open in any browser to preview the working widget (search, category + strategy filters, By Topic / By Strategy views). This is the device-hardened version; make all future edits here.
- `HANDOFF.md` — this file.
- `blog-landing-page.html` — the original build, kept for reference only. Do not embed or edit it.
- The `.py` scripts and `.json` files are the content pipeline Rodrigo uses to regenerate the index. The developer does not need them. The finished HTML already has all 71 posts baked in.

## How to embed in Divi

1. **Build the page banner natively in Divi** (the site's standard page title pattern). Suggested content:
   - Eyebrow: `Return Stacked® ETFs`
   - Title: `Blog Library`
   - Tagline: `Explore our complete collection of articles on return stacking, portfolio construction, and capital-efficient investing.`

2. **Add a regular Divi section below the banner.**

3. **Drop in a single Code module** (fullwidth row recommended).

4. **From `blog-landing-page_divi.html`, copy three blocks into that Code module:**
   - The `<style>...</style>` block (lines 46 to 453, everything in the `<head>`)
   - The `<div id="rs-blog">...</div>` block (lines 457 to 534, the entire widget container)
   - The `<script>...</script>` block (lines 536 to 761, immediately after the widget div)

5. Save and preview. No build step, no dev server, no external dependencies, no data files to upload. The post data is inlined directly into the script.

## What the widget does

- **Search bar** filters all posts in real time by title, topic, strategy, or keyword.
- **Two filter chip rows:**
  - **Category** (Foundations, Strategy Spotlights, Portfolio Construction, Leverage Explained, Mechanics & Operations, Practice Management, Research & Case Studies)
  - **Strategy** (Trend, Carry, Gold, Bitcoin, Merger Arb, Bonds, Equities)
  - Each row is single-select. Clicking the active chip clears it.
- **Two views via tabs:**
  - **By Topic** groups posts into category tiles, with a "Latest Posts" row and a "Start Here" row featured at the top.
  - **By Strategy** groups posts into strategy tiles, plus a "General" tile for posts with no strategy tag.
- **Latest Posts** and **Start Here** featured rows show the top 3 posts flagged for each. They hide automatically when a search is active.
- **Auto-hide cascade:** empty tiles disappear, then a "No articles found" message shows if nothing matches.

## Design notes (please preserve)

- **CSS is scoped under `#rs-blog`** to prevent collisions with Divi theme styles. Please do not strip or rename this scope.
- **Font:** DM Sans is already loaded by the Return Stacked theme. The Google Fonts `<link>` in the file's `<head>` is for standalone preview only. You can omit it in the Divi paste.
- **Color tokens** (CSS variables at the top of the style block) match the site palette: teal `#14cfa6`, navy `#283742`, blue `#3f73ab`, light bg `#f7f6f6`, border `#d9d9d9`. Please do not introduce new colors.
- **External links:** all post links open in a new tab (`target="_blank" rel="noopener"`).
- **JS is fully namespaced** under an IIFE with the `rsBlog` prefix (`rsBlogFilter`, `rsBlogCatFilter`, `rsBlogStratFilter`, `rsBlogSwitchTab`) so it will not conflict with anything else on the site.

## Adding or editing content later

All posts live in the `POSTS` array near the top of the `<script>` block. Each post is one object:

| Field | Meaning |
|---|---|
| `t` | Title |
| `u` | Full post URL |
| `d` | Publish date `YYYY-MM-DD` (used for ordering; can be empty) |
| `c` | Array of category labels (must match a Category chip) |
| `s` | Array of strategy labels (must match a Strategy chip; empty array = General) |
| `e` | One-line excerpt shown on the card |
| `k` | Space-separated search keywords (synonyms and themes not in the title) |
| `f` | `true` puts the post in the **Latest Posts** featured row (top 3 shown) |
| `sh` | `true` puts the post in the **Start Here** featured row (top 3 shown) |

To add a post, copy an existing object, edit the fields, and place it in the array. Category and strategy labels are case-sensitive and must match the chip definitions exactly. Rodrigo can also regenerate the whole array from the content pipeline scripts in this folder.

## Contact

Questions: Rodrigo Gordillo, rodrigo.gordillo@investresolve.com
