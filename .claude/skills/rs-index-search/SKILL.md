# Skill: rs-index-search

One search engine for every Return Stacked index widget (Research Articles, Product Articles, Literature, and any future "browse a library" section on the website). The skill owns the canonical search code and the shared synonym list; each widget carries a rendered copy between two marker comments.

## When to Use

- Building a new index / library widget for returnstacked.com or returnstackedetfs.com that needs a search box
- Someone reports a search miss on any index widget ("taxation finds nothing", "cta should find managed futures")
- The team edits the synonym list and every widget needs the update
- Changing the search behaviour itself (stemmer, typo tolerance, fallback rules) so all widgets move together

## What the engine does (2026-09-14 spec, born in the Research Articles widget)

- Porter stemmer on both the query and the item text, so tax / taxes / taxation agree.
- Two-way prefix rule between query stems and text stems (stack finds stacking, stacking finds stack), with guards so "the" does not find "theory".
- Typo tolerance: a query word of 5+ letters matches one edit away (levrage finds leverage, protfolio finds portfolio).
- Multi-word queries require every word. If that finds nothing, the widget re-runs in any-word mode and shows a note under the search box.
- Synonym concept groups (`assets/search-synonyms.json`): when an item's text contains any phrase in a group, every word of the group is added to that item's search terms at runtime (cta finds an item that only says managed futures).
- Stems are computed once per element (WeakMap cache) so typing stays cheap.
- The code contains no `&`, `<` or `>` characters (Divi Code Module / WP editor rule shared by all the widgets).

## Files

| File | Role |
|---|---|
| `assets/search-core.js` | The canonical core. `__NS__` is the widget's JS prefix; `__SYNONYM_GROUPS__` is filled from the JSON. Edit search behaviour HERE, then re-sync every widget. |
| `assets/search-synonyms.json` | Shared concept groups (38 as of 2026-09-15). Team-editable; see its `_readme`. Never add ETF tickers as trigger phrases (Literature compliance: a ticker must not surface Manager Research rows). |
| `scripts/sync_search_core.py` | `python sync_search_core.py <widget-source> --ns rsArt` replaces the block between `// RS-SEARCH-CORE-START` and `// RS-SEARCH-CORE-END` in the widget with the rendered core. `--check` only reports (exit 1 when stale); the Research Articles build runs this check and refuses to build on a stale copy. |
| `scripts/test_search.js` | `node test_search.js <search-tests.json>` extracts the core from a built widget file, rebuilds each item's search text from the markup, and checks query hit counts from the config. Stemmer guard rails run for every widget. |
| `scripts/make_synonyms.py` | One-off seed script (record only). |

## Widgets on the shared core (2026-09-15)

| Widget | Source file | Namespace | Test config | Notes |
|---|---|---|---|---|
| Research Articles | `projects/return-stacked-website/Blog_Indexing_LP/research-articles.template.html` | `rsRes` | `Blog_Indexing_LP/search-tests.json` (`node test_search.js` shim) | Built widget. `build_research_widget.py` also applies the synonym groups at build time (it sees each post's key sentences, which the widget does not ship). |
| Product Articles | `projects/return-stacked-website/Product_Blog_Index/product-articles.html` | `rsArt` | `Product_Blog_Index/search-tests.json` | Hand-maintained. Regenerate the embed with the sed one-liner in its CLAUDE.md after a sync. |
| Literature | `projects/return-stacked-website/Literature_PDF_Index/literature-option-d.html` | `rsLit` | `Literature_PDF_Index/search-tests.json` | Hand-maintained, single file. Items inside a tile also search the tile name and description. |

## Procedure A: add the engine to a new widget

1. Pick the widget's JS prefix (`rsXxx`, matching its CSS prefix convention) and make sure it is not `rsRes`, `rsArt` or `rsLit`.
2. In the widget script, where the search functions go, add the two marker lines on their own:
   ```
   // RS-SEARCH-CORE-START
   // RS-SEARCH-CORE-END
   ```
3. Run `python .claude/skills/rs-index-search/scripts/sync_search_core.py <file> --ns rsXxx`.
4. Wire the DOM side (copy from the Product Articles widget, it is the smallest):
   - `rsXxxSearchText(el)`: visible `textContent` plus the `data-*` attributes that hold keywords, tags, topics, or an excerpt.
   - A WeakMap stem cache calling `rsXxxTextStems(rsXxxSearchText(el))` once per element.
   - Match with `rsXxxMatchText(stems, queryStems, mode)`, then AND with whatever chip / pill / tag is active.
   - Query from the input with `rsXxxQuery(raw)`.
   - Apply in mode `'all'`; when nothing is visible and `rsXxxLE(2, queryStems.length)`, apply again in `'any'` and show the note ("No articles match all of "q". Showing articles that match any of the words.").
5. Markup and CSS for the note: an `aria-live="polite"` div right under the search bar, hidden by default, 12.5px, sub-text colour (see `.rs-res-search-note` / `.rs-art-search-note`).
6. Every item needs `data-tags` (the runner keys on it) and a `data-keywords` attribute for search-only synonyms not in the visible text.
7. Write `search-tests.json` next to the widget (copy a sibling's and adjust `file`, `itemTags`, `itemClass`, `dedupeAttr`, `titleRe`, `minItems`, `checks`). Run the runner; it must print ALL PASS.
8. Keep the widget script free of `&`, `<`, `>`: use `!==`, `Math.min` helpers (`rsXxxLE`, `rsXxxLT`) and nested ifs.
9. Add the widget to the table above and note the namespace in the widget's CLAUDE.md.

## Procedure B: change search behaviour or synonyms

1. Edit `assets/search-core.js` or `assets/search-synonyms.json` (phrases lowercase; no `& < > " '`).
2. Re-sync every widget in the table (three commands today). For Research Articles run `python build_research_widget.py` afterwards; for Product Articles regenerate the embed.
3. Run every widget's `search-tests.json` through the runner. Add a check for the query that motivated the change.
4. Log the behaviour change in `decisions/log.md` if it changes what users find.

## Procedure C: a reported search miss

1. Reproduce with the runner: add `{ "q": "<their query>", "atLeast": N, "list": true }` to the widget's config and read the printed titles.
2. Decide: missing synonym (add a phrase to an existing group or a new group), missing `data-keywords` on the item (fix the item), or an engine rule (edit the core; rare).
3. Follow Procedure B. Keep the new check in the config as a regression guard.

## Do Not

- Edit the code between the markers inside a widget. The next sync overwrites it and the Research Articles build refuses to run on a stale copy.
- Keep a per-widget copy of the synonyms. One file, in this skill.
- Add ETF tickers as synonym trigger phrases (compliance, see above).
- Introduce `&`, `<` or `>` into the core or any widget script.
