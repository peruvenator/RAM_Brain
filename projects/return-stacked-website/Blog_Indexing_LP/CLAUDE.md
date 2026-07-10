# Blog Indexing Landing Page

Sub-project of the Return Stacked website redesign. Catalog all blog posts on returnstacked.com and build a landing page for categorizing and discovering content.

## Goals

- **Catalog:** Index every blog post on returnstacked.com with metadata (title, date, author, category, tags, URL)
- **Categorize:** Assign each post to meaningful categories/tags (e.g., by strategy, by audience, by topic)
- **Landing page:** Build an HTML landing page that lets users browse, filter, and search the blog content library

## Workflow

1. Scrape/catalog all blog posts from returnstacked.com
2. Organize into a structured index (CSV or JSON)
3. Build a filterable landing page using the index data
4. Iterate on design and categorization with Rodrigo

## Canonical File

- **`blog-landing-page_divi.html` is the source of truth. Make ALL future updates here.**
- This is the developer-hardened version that runs on the live Divi site. The web developer fixed device-distortion bugs in it (see Divi Hardening below).
- `blog-landing-page.html` is the original Claude build, kept for reference only. Do NOT edit it.
- The HTML is self-contained: 71 posts inlined into the `POSTS` array in the `<script>` block, CSS scoped under `#rs-blog`, JS namespaced `rsBlog*`. No fetch, no build step. See `HANDOFF.md` for the Divi embed steps and the `POSTS` schema.

## Divi Hardening (learnings from the developer's revision)

These patterns fixed real rendering bugs on the live WordPress + Divi site. Preserve them and apply the same approach to any new components.

1. **Count badges / "circles" -- center with flex, never with padding alone.** The `.cat-tile-count` pills were built from `padding` + `border-radius` only, with no fixed sizing. The text reflowed and the shape distorted across device sizes. Fix: `display: inline-flex; align-items: center; justify-content: center; min-width: 28px; line-height: 1.4`. Any pill, badge, or circular element must size from flex centering + `min-width`, not from padding.

2. **Icons inside inputs -- use a separate positioned inner wrapper, not a background-image with padding.** The search icon was a CSS `background` SVG offset by `padding-left`, which shifted unpredictably. Fix: wrap the input in `.rsb-search-inner { position: relative }` and place a real `<svg>` as an absolutely-positioned sibling (`.rsb-search-icon`), with the input padded to clear it. Inline structure beats padding hacks for alignment stability.

3. **Responsive typography via media queries, not single fixed sizes.** Headings (`.featured-card-title`, `.cat-tile-name`) get explicit sizes at the `980/981px` breakpoint instead of one fixed `font-size`. Set type per breakpoint so it does not crowd on tablet/mobile.

4. **Use `!important` defensively against Divi theme bleed.** The Divi theme leaks styles into the widget. Key properties on the count badge and search input are forced with `!important` to win the cascade. Expect to do this on any element whose box model or color the theme overrides.

5. **Layout numbers that ship:** container `max-width: 1264px`; desktop horizontal padding `24px` (was 48); mobile padding `12px` (was 20). Base font sizes nudged up one step (11->12, 13->14) for readability. Tight headings use `letter-spacing: -0.0325em`.

6. **Class prefixing:** developer-revised search components use an `rsb-` prefix on top of the `#rs-blog` scope for extra collision safety. Follow the `rsb-` convention for new sub-components.

## Brand

- Follow Return Stacked brand guidelines from `references/brand-assets/`
- Match the visual language of the main website redesign

## Parent Project

- `projects/return-stacked-website/` -- Return Stacked website redesign
- Sibling: `lp-widget/` -- Landing page visualizer component
