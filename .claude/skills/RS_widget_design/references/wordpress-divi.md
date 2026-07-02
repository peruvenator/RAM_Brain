# WordPress / Divi Integration

How to keep a single-file widget from being mangled by Divi's aggressive global styles, and how to embed it cleanly.

---

## Architecture: Single-File HTML

- The widget is one self-contained HTML file — all CSS in `<style>`, all JS inline
- External deps via CDN `<link>` / `<script>` tags (Google Fonts, Chart.js, jsPDF if needed)
- No build step at runtime — the file runs as-is
- All data embedded inline (no fetch calls, no CORS issues). Base64-encode + decode for moderate datasets.

> **Scale caveat (learned on the Advanced Visualizer):** the all-inline single-file model
> works for small/medium widgets. For a LARGE widget (hundreds of KB of JS, many charts),
> Divi mangles the inline `<script>` and the `:where()` resets lose to Divi's real selectors.
> See **"Scaling Up: When the Single-File Model Breaks"** below for the production-proven
> alternative (external JS file + PHP plugin + ID-scoped `!important` overrides).

---

## Embedding in Divi

- Use a Divi **Code Module** to paste the HTML
- When embedding inline inside a page, strip `<html>`, `<head>`, `<body>` wrappers. Keep only `<style>`, `<script>`, and the widget `<div>`
- Google Fonts `<link>` goes above the `<style>` block, **outside** the namespaced container. If Divi strips it, inject via the theme's header settings
- The WP visual editor may strip or mangle `<style>` and `<script>`. Always use Code/Text editor or a Code Module
- Wrap everything in a single container `<div>` to prevent WP from wrapping raw HTML in `<p>` / `<br>`

---

## CSS Namespacing (Critical)

Divi injects global styles targeting bare selectors (`input`, `label`, `button`, `h2`, `p`, `table`, etc.) with high specificity. Without namespacing, the widget inherits Divi's look and breaks.

### Rules
1. **Root namespace:** wrap the widget in a single root element with a unique class (e.g. `.rsw-widget`) or ID
2. **Class prefix:** all internal classes and IDs use a consistent prefix (`rsw-`, `rsv-`, `rst-` — pick one per widget)
3. **Box-sizing reset inside the namespace:**
   ```css
   .rsw-widget * { margin: 0; padding: 0; box-sizing: border-box; }
   ```
4. **Every CSS rule scoped to the namespace** — no bare element selectors, no bare class selectors anywhere
5. **Keyframe names namespaced** too (`@keyframes rsw-fade-in`, not `@keyframes fade-in`)
6. **EVERY class token must carry the prefix — including modifiers and children in compound selectors.** This is the rule most easily violated: `class="rsv-tab active"`, `<span class="arrow">`, `class="rsv-validation error"`. The `rsv-` element is namespaced, but `active`, `arrow`, `error` are NOT.

### The bare-modifier-class trap (learned twice on the Portfolio Visualizer)

Divi ships global rules for many common class names. If your markup uses a bare
class with the same name, Divi's rule applies to your element for any property
your own (scoped) rule doesn't explicitly set.

- **`.arrow`** — the disclosures toggle used `<span class="arrow">▶</span>`. Divi
  styles `.arrow` with its **icon font** (ETmodules). Our scoped rule
  `.rsv-disclosures-toggle .arrow` set `transform`/`font-size` but NOT
  `font-family`, so Divi's icon font won through and the ▶ rendered as `?`.
  Fix: rename to `.rsv-arrow` (+ keep a symbol-font fallback on it).
- **`.error` / `.success` / `.info` / `.warning`** — WordPress and Divi define
  these for form/notice states. A validation message `class="rsv-validation error"`
  can inherit Divi's background/color for `.error`. Fix: `.rsv-error`, `.rsv-success`, …
- Other Divi-defined names to never use bare: `.active`, `.open`, `.close`,
  `.hidden`, `.button`, `.title`, `.label`, `.container`, `.row`, `.column`,
  `.grid`, `.tab`, `.tabs`, `.icon`, `.slider`, `.arrow`, `.toggle`.

**Why compound-scoping is not a full defense.** `.rsv-tab.active` (specificity
0,2,0) beats Divi's `.active` (0,1,0) for properties *you set* — but any property
Divi sets that you don't still bleeds in. Compound-scoping protects the visible
result only if your rule sets every property that matters. Namespacing the class
outright is the reliable fix.

**Sweep for these before shipping.** Extract every class token from `class="…"`
attributes and flag any that don't start with your prefix:
```bash
grep -oE 'class="[a-zA-Z0-9_ -]+"' widget.* | sed 's/class="//;s/"//' \
  | tr ' ' '\n' | grep -vE '^rsv-|^$' | sort -u
```
Rename decorative/state classes Divi is known to define. Pure-custom value
classes Divi never defines (`neg`, `hl`, `positive`) are lower risk, but
namespacing them anyway keeps the sweep clean.

---

## The `:where()` Pattern (preferred over `!important`)

Divi styles bare HTML elements (`h1`, `p`, `button`, `input`, `table`, etc.) with high specificity. Rather than fight with `!important` on every property, use `:where()` to zero specificity on the resets so component classes always win.

```css
.rsw-widget :where(h1, h2, h3, h4, h5, h6) {
  font-family: "DM Sans", sans-serif;
  color: inherit;
  margin: 0;
  padding: 0;
  line-height: 1.3;
  letter-spacing: normal;
  text-transform: none;
}
.rsw-widget :where(p) {
  font-family: "DM Sans", sans-serif;
  color: inherit;
  margin: 0;
  line-height: 1.5;
}
.rsw-widget :where(button) {
  font-family: "DM Sans", sans-serif;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}
.rsw-widget :where(input, select, textarea) {
  font-family: "DM Sans", sans-serif;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 6px 10px;
}
.rsw-widget :where(table) {
  border-collapse: collapse;
  border-spacing: 0;
  border: none;
}
.rsw-widget :where(th, td) {
  border: none;
  padding: 0;
  font-weight: inherit;
}
```

**How it works:** `:where(h1, h2, ...)` has specificity `(0,0,0)` from the pseudo-class itself, plus `(0,1,0)` from the parent `.rsw-widget`. Your component class (e.g. `.rsw-title`) has specificity `(0,1,0)` too but wins on source order. A plain `.rsw-widget h1` reset would be `(0,1,1)` and *beat* `.rsw-title`, which is why the component class would then disappear.

**Critical gotcha (learned the hard way on the portfolio visualizer):**
> Do NOT change `.rsw-widget :where(button)` to plain `.rsw-widget button`. That caused buttons to disappear because the reset's specificity (class + element = 0,1,1) beat the component class (class only = 0,1,0).

### When `!important` is still needed
The `:where()` pattern handles most cases, but a few stubborn Divi selectors still punch through:
- `tbody tr:nth-child(even) td` — Divi's alternating row striping. Override with an equally-specific selector set on `td`, not `tr`
- Divi sometimes applies uppercase + letter-spacing to headings inside specific modules. Add `text-transform: none` to the reset
- For form elements in certain Divi themes, you may need `!important` on `font-family` and `color` specifically — use sparingly, only after confirming `:where()` doesn't cut it

---

## `isolation: isolate`

Add to the widget root:
```css
.rsw-widget { isolation: isolate; }
```

Creates a stacking context boundary so `z-index` values inside the widget don't compete with Divi's sticky headers, mobile menus, or modal overlays.

---

## Font Loading Order

The Google Fonts `<link>` must load before the `<style>` block. Put it in the `<head>` above `<style>`, or as the first element in the Divi Code Module.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

If the page already loads DM Sans elsewhere, the `<link>` is safe to include again — browsers deduplicate.

---

## JavaScript Isolation

Wrap all JS in an IIFE:
```javascript
(function () {
  'use strict';
  // ...
})();
```

- Scope all DOM queries to the root: `document.querySelector('.rsw-widget').querySelector('...')` or cache a `root` reference
- Avoid generic selectors (`document.querySelectorAll('button')`) — they'll catch Divi's chrome
- If using Web Workers, create from inline Blob URLs, not external `.js` files — external paths don't always resolve inside WP

---

## Performance

- WP pages are heavy. Minimize DOM manipulation and avoid layout thrashing
- For computationally expensive work, use Web Workers to keep the UI responsive
- Lazy-init expensive resources (don't spin up workers until the user interacts)
- Destroy Chart.js instances on rebuild (otherwise memory leaks)

---

## Testing

- **Always test in the actual WP/Divi environment**, not just standalone — Divi injects styles that don't reproduce locally
- Check desktop and mobile in Divi preview and on real devices
- Verify slider interactions and chart rendering after embedding — Divi's JS can occasionally interfere
- Confirm the visual builder doesn't strip or reformat the HTML (Code Modules are generally safe but verify)

---

## Scaling Up: When the Single-File Model Breaks (Advanced Visualizer lessons)

The single-file/all-inline/`:where()` model is the default, but a large, complex widget
(the Advanced Portfolio Visualizer: ~1.8MB JS, 5 portfolios, many charts, PDF export)
broke in Divi in ways the default model doesn't cover. The production-proven architecture
for a heavy widget is different:

### 1. Host the JS as a separate file — do NOT inline it
Divi's Code Module mangles large inline `<script>` blocks (they may not execute at all).
- Extract all JS to a standalone file (e.g. `rsv_widget.js`), upload to the server
  (`/wp-content/uploads/<widget>/rsv_widget.js`), reference with `<script src="...">`.
- The embed HTML then contains only the namespaced `<div>`, the `<style>`, and the
  `<script src>` line — no inline JS.
- Confirmed by the partner who deployed the simple visualizer: "a lot of the issues came
  from not hosting the .js file independently and trying to put the JavaScript into Divi."

### 2. Load CDN dependencies via `wp_enqueue_script`, not in the Code Module
Chart.js / annotation plugin / jsPDF / Google Fonts must be enqueued from a small PHP
plugin, loaded in `<head>` (pass `false` for the in-footer arg), so they're ready before
the widget parses. CDN `<script>` tags pasted into a Code Module don't reliably execute.
- `has_shortcode( $post->post_content, '<tag>' )` can return false on Divi pages because
  Divi stores layout as serialized JSON. If Chart.js fails to load, drop the `has_shortcode`
  guard and enqueue sitewide.

### 3. PHP shortcode returns embed-ready HTML and injects config BEFORE the script
- The shortcode returns the embed file's contents — **no** `<!DOCTYPE>`, `<html>`, `<head>`,
  or `<body>`. A full document returned from a shortcode gets mangled.
- If the JS needs server values (API base, nonce, user email), inject a `<script>` defining
  the global (e.g. `window.RSV_CONFIG = {...}`) **immediately before** the `<script src>`
  line — not after `</body>`. The external file reads the global at parse time, so order matters.

### 4. Add an ID-scoped `!important` override block — `:where()` alone loses at scale
`:where()` resets have zero specificity and lose to Divi's actual element/class selectors
(`input { width:100% }`, button styling, etc.). Keep `:where()` as the first layer, but add a
dedicated override block scoped to the root **ID** (higher specificity than any class) with
`!important` on the properties Divi clobbers. Known offenders and fixes:

| Divi global bleed | Symptom | Fix (`#root … !important`) |
|---|---|---|
| `input, select { width: 100% }` | inputs stretch full-width and stack vertically | `width: auto !important` + restore intentional widths per component |
| gray input bg + fixed min-height | gray, oversized input boxes | `background-color`, `height: auto`, `min-height: 0` |
| `button { text-transform: uppercase; letter-spacing; background }` | wrong button look | reset casing/spacing only; do NOT override bg/border/color (let component classes win) |
| `p { padding-bottom: 1em }`, heading margins | extra space everywhere | reset to 0 globally, then **restore** intended spacing with a higher-specificity rule (e.g. `#root .disclosures p`) |
| bare `a`, `ul/ol` list styling | underlines, bullets, indents | reset color/decoration/list-style/margins |

**The `font-size: inherit` trap:** never put `font-size: inherit !important` on a catch-all
`input/select/button` override. Each field then inherits its *parent's* size, so the same
control renders at different sizes in different rows. Pin an explicit px value instead
(match the design — e.g. 12px to match a reference cell).

**Buttons need their own rule:** don't fold `button` into the input override (which sets
bg/border). Give buttons a separate rule that only neutralizes Divi's additions (font,
casing, spacing, box) and leaves bg/border/color to the widget's own button classes — and
do NOT force a single `font-size` on it, or you flatten the button hierarchy.

### 5. Beat DiviArea's z-index
Divi's "DiviArea" wrapper uses `z-index: 1000000`. `isolation: isolate` creates a stacking
context but is not enough on its own — give popovers/dropdowns/modals/tooltips a very high
z-index (e.g. `9999999`) so they aren't clipped.

### 6. Glyph fallbacks for icon characters
DM Sans (and many web fonts) lack symbol glyphs like ▶ (U+25B6), ▾, ↗. They render as "?".
Put a symbol-capable fallback on the glyph span: `font-family: Arial, "Segoe UI Symbol",
"Apple Symbols", sans-serif !important;`.

### 7. Prevent overlay flash
Any overlay that JS hides on init (intake gate, modal) will paint for a frame before the JS
runs. Hide it by default in CSS (`display: none !important`) and let JS reveal it instead.

### 8. The deploy artifact is three files, not one
Build output for a heavy widget: (a) `*_embed.html` (namespaced div + style + `<script src>`,
no wrapper) for the plugin dir, (b) `<widget>.js` for the server uploads dir, (c) the PHP
plugin. A standalone single-file build is still useful for local functional testing but is
NOT what gets deployed.

### 9. Syntax-validate generated JS before every handoff
If the widget is generated by a Python build script, ONE broken escape produces a JS parse
error and the entire widget dies silently (header renders, `RSV`-style app object never
defined). This shipped to a deploy zip once. After every build:
```bash
node --check <widget>.js
```
Node prints the exact line of the first syntax error. Do this before zipping or handing off —
it takes one second and catches the whole class of f-string escaping bugs (see
`state-and-workflow.md` → Python f-string Build Gotchas).

### Why a local "Divi simulation harness" misleads
Building a local HTML page that injects Divi's known-bad CSS, then fetches the embed HTML +
JS, is tempting but unreliable:
- It injects async (after page load), so `DOMContentLoaded` has already fired and the widget's
  init never runs — a false failure that doesn't happen in the real synchronous WP render.
- It won't show charts or the real font unless you manually load the **same** CDN deps and
  Google Fonts the PHP plugin enqueues — otherwise charts are blank and the font falls back
  to a system sans-serif (looks like a font bug that isn't real).
- Verdict: a harness is OK for a rough CSS sanity check, but the **real staging site is the
  only accurate test**. Don't chase "bugs" that are actually harness artifacts.

---

## Checklist before deploying

- [ ] Single root element with namespaced class
- [ ] All CSS rules prefixed with the namespace
- [ ] **Swept `class="…"` attributes for bare (non-prefixed) tokens** — no bare `arrow`, `active`, `error`, `success`, `open`, `icon`, etc. that Divi could hijack (see "bare-modifier-class trap")
- [ ] `:where()` resets for bare elements (h1-h6, p, a, button, input, label, table, th, td, img)
- [ ] `isolation: isolate` on the root
- [ ] Fonts loaded via `<link>` before `<style>`
- [ ] JS wrapped in IIFE
- [ ] DOM queries scoped to the widget root
- [ ] Tested in Divi Code Module on staging
- [ ] Mobile breakpoint verified on real device
- [ ] Chart instances destroyed before rebuild
- [ ] No keyframe name collisions (`@keyframes` all namespaced)

**For a LARGE widget, additionally:**
- [ ] JS hosted as a separate file (`<script src>`), not inlined in the Code Module
- [ ] CDN deps + fonts enqueued via `wp_enqueue_script`/`wp_enqueue_style` in `<head>` (PHP plugin)
- [ ] Shortcode returns embed HTML only (no `<!DOCTYPE>`/`<html>`/`<head>`/`<body>`)
- [ ] Server-value config global injected immediately before the `<script src>` line
- [ ] ID-scoped `!important` override block present for Divi's stubborn globals (input width, gray bg, button styling, `p`/heading spacing)
- [ ] No `font-size: inherit` on any catch-all input/button override (use explicit px)
- [ ] High z-index (`9999999`) on dropdowns/modals/tooltips to beat DiviArea
- [ ] Symbol-glyph fallback font on icon characters (▶ ▾ ↗)
- [ ] JS-hidden overlays also hidden in CSS by default (no flash)
- [ ] `node --check` passes on the generated JS (catches f-string escaping bugs)
- [ ] Verified on real staging — not a local simulation harness
