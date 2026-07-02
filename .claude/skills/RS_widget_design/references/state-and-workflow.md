# State, Integration, and Workflow

State management patterns, article integration, and the build workflow for RS widgets.

---

## State Management

### Plain JS, no framework
State lives in a single `state` object inside the widget's IIFE:
```javascript
var state = {
  stockPct: 60,
  period: 5,
  tab: 'growth',
  dateRange: { from: null, to: null }
};
```

No Redux, no MobX, no React. Updating state requires a manual `render()` or `recompute()` call — which is fine because every state change already has an explicit trigger (slider input, button click).

### localStorage persistence
Use for user identity, saved portfolios, intake-gate bypass. Keyed by a single constant:
```javascript
var STORAGE_KEY = 'rsw-visualizer-v1';
localStorage.setItem(STORAGE_KEY, JSON.stringify({ savedPortfolios, userProfile }));
var saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
```

### URL query parameters (shareable state)
Encode widget configuration into search params so a link reproduces the exact view. Parse URL params on load before rendering.
```javascript
var params = new URLSearchParams(window.location.search);
if (params.has('stock')) state.stockPct = parseInt(params.get('stock'), 10);
if (params.has('period')) state.period = parseInt(params.get('period'), 10);
```
For complex state (full portfolio configs), base64-encode a JSON snapshot into one param (the visualizer uses `?rs_p=` + `btoa(JSON.stringify(shareState))`).

---

## WordPress Identity Injection (`window.RSV_CONFIG`)

For widgets behind a WordPress login wall, the PHP shortcode injects the logged-in user's identity as a global **immediately before** the widget `<script src>` (order matters — the widget reads it at parse time):

```html
<script>
window.RSV_CONFIG = {
  userEmail: '<?php echo esc_js( wp_get_current_user()->user_email ); ?>'
};
</script>
```

The widget hydrates identity with a priority chain — config global first, localStorage fallback:

```javascript
var storedEmail = '';
(function () {
  if (window.RSV_CONFIG && RSV_CONFIG.userEmail) {
    storedEmail = RSV_CONFIG.userEmail;
    return;
  }
  try {
    var saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && saved.email) storedEmail = saved.email;
  } catch (e) {}
})();
```

Every downstream submission (HubSpot forms, booking links) reads `storedEmail` — no intake form needed when WordPress supplies the identity.

## Server-Side Persistence (WordPress REST + nonce)

When saved items should follow the user's account instead of the browser (production pattern from the authenticated visualizer):

- Custom DB table (e.g. `wp_rsv_portfolios`), not user meta, when users save many items
- REST routes registered by a small PHP plugin; every route checks `is_user_logged_in()` and enforces row-level ownership
- Auth via the `X-WP-Nonce` header — the shortcode passes `wp_create_nonce('wp_rest')` through the config global
- Widget side: a small fetch wrapper + an in-memory cache populated from `GET` on init; save/load/delete become async API calls
- Server becomes the source of truth — drop JSON-file auto-downloads; keep file import only as a migration path for old localStorage backups

---

## Intake Gate Pattern

Used on the LP widget to capture a lead before revealing the tool.

1. Widget renders behind a blurred overlay (`filter: blur(6px); pointer-events: none`)
2. Modal intake form sits on top, captures name/email/firm
3. On submit: save to localStorage, remove the blur, fire HubSpot form submission
4. Returning visitors (detected via localStorage) skip the gate
5. "Not you?" link clears localStorage and re-shows the gate

### Form validation
Disable submit button until required fields are filled. Wire via input listeners:
```javascript
function checkReady() {
  var ready = emailInput.value && nameInput.value && firmInput.value;
  submitBtn.disabled = !ready;
}
[emailInput, nameInput, firmInput].forEach(function (el) {
  el.addEventListener('input', checkReady);
});
```

---

## HubSpot Integration

Define one shared helper plus one form-ID constant per event (production pattern — the visualizer has separate forms for intake, consultant, share-link, and PDF-download events):

```javascript
var HS_PORTAL_ID = '46343589';
var HS_SHARE_FORM_ID = '...';   // one GUID per HubSpot form / event type
var HS_PDF_FORM_ID = '...';

function submitHubSpotForm(formId, fields) {
  fetch('https://api.hsforms.com/submissions/v3/integration/submit/' + HS_PORTAL_ID + '/' + formId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields: fields })
  }).catch(function () {});   // fire-and-forget — never block the UX
}
```

Each field is `{ objectTypeId: '0-1', name: '<contact property>', value: ... }`. The Forms API v3 is public — no API key.

**Attach usage context to submissions.** The visualizer sends the active portfolio composition with every share/PDF event so the CRM record shows what the user was building:
```javascript
var coreStr = core.map(function (r) { return r.weight + '% ' + r.asset; }).join(' / ') || 'None';
submitHubSpotForm(HS_SHARE_FORM_ID, [
  { objectTypeId: '0-1', name: 'email', value: storedEmail },
  { objectTypeId: '0-1', name: 'portfolio_widget_output', value: 'Core: ' + coreStr + '\nStack: ' + stackStr }
]);
```

**Picklist values must match HubSpot exactly.** If widget labels differ from the HubSpot property's picklist options (e.g. AUM ranges), keep an explicit label→value mapping object — don't send the display label raw.

---

## PDF Generation (jsPDF)

```html
<script src="https://cdn.jsdelivr.net/npm/jspdf@2/dist/jspdf.umd.min.js"></script>
```

- Orientation per report type: the visualizer uses portrait US Letter in mm (`pw = 215.9, ph = 279.4`); landscape pt is fine for chart-dominant reports
- Charts rendered to off-screen canvases, exported as JPEG (0.92 quality) or PNG, placed as images:
  ```javascript
  var imgData = chartInstance.toBase64Image('image/jpeg', 0.92);
  doc.addImage(imgData, 'JPEG', x, y, width, height);
  ```
- **Brand font embedding:** for branded reports, embed DM Sans as base64 (`data/dmRegular.txt`, `dmBold.txt`, `dmItalic.txt`, `dmBoldItalic.txt` in the visualizer project) and register via `doc.addFileToVFS(...)` + `doc.addFont(...)` — this removes the network-font dependency and keeps typography on-brand. It does grow the build (~MBs); fall back to jsPDF built-in fonts only for throwaway/unbranded exports
- **Branded cover/footer:** cover = white logo bar + `--cover-dark` banner with background image + teal accent bar; footer = dark logo square + teal page-number band + URL. RGB tuples mirror the CSS tokens (navy `[23,44,58]`, teal `[20,207,166]`, section gray `[240,241,241]`)
- Colors: `doc.setFillColor(r, g, b)` using decimal RGB
- Multi-page: `doc.addPage()`

---

## Article + Widget Integration

### Layout
- Article and widget live inside the **same namespaced root container**
- Article comes first; widget appears at the narrative moment where the reader is ready to explore
- Provide a "skip to tool" affordance early in the article — subtle horizontal bar (light background, centered text + button), not a garish banner
- Mid-article embeds: zero vertical margin between article bottom and widget top so they feel continuous

### Widget introduction
Briefly restate the parameters the reader will be adjusting and why those parameters matter (referencing the preceding analysis). The widget should feel like an extension of the argument, not a bolted-on appendix.

### Widget anatomy
1. Widget container (namespaced root)
2. Title — concise, descriptive
3. Description — 1-2 sentences explaining what to look for
4. Compliance disclaimer (short, in-line)
5. Controls (grouped)
6. Chart canvas (sized container)
7. Stat boxes (grid)
8. Source attribution
9. Collapsible full disclosures

---

## Build Workflow

### Iterative process
- Start with article prose + overall structure
- Build widgets one at a time, test each before moving on
- Embed data directly in JS (precompute as much as possible to keep runtime simple)
- After all widgets work, do a styling pass for cross-widget consistency
- Test at desktop/tablet/mobile viewport widths
- **Test in the actual Divi environment**, not just standalone — some issues only reproduce there

### Data pipeline
- Python analysis scripts generate figures and precomputed data
- A build script (e.g. `build_widget.py`) assembles the final HTML by injecting embedded data into a template
- **Analysis stays separate from widget code** — widget consumes precomputed outputs only, never runs analysis at runtime
- Raw CSVs processed offline; final HTML never fetches/parses them
- For financial time series: be explicit about returns vs levels, arithmetic vs geometric

### Reproducibility
- Master "run all" script regenerates all figures + data from source
- Pin random seeds or save simulation indices for reproducible results
- Shared utilities (data loading, stats) in a shared module, not duplicated

---

## Python f-string Build Gotchas

Widgets built with `build_widget.py` using Python f-strings for the whole HTML:
- All JS curly braces must be doubled (`{{` and `}}`)
- **Backslash escapes must be doubled too.** Python interprets `\n`, `\t`, `\r` inside a non-raw f-string, so JS like `text.replace(/\n/g, " ")` or `para.split("\n\n")` emits a **literal newline** into the generated file — splitting the regex/string across two lines and killing the entire script with a syntax error. Write `\\n` in the Python source. (Shipped broken once: widget loaded but the app object was never defined.) `\uXXXX` escapes are safe — they become actual characters, which are valid in JS strings.
- Watch for duplicate `let` / `const` declarations in the same method scope — caused a full widget blank-out on the visualizer once
- **Validate after every build:** `node --check <generated>.js` (or the generated HTML's extracted JS) prints the exact line of the first syntax error. Make this part of the build-then-handoff routine.
- Debug blank-page issues in-browser with a wrapper test:
  ```html
  <script>
    try { new Function(js_code); } catch(e) { document.body.innerHTML = e.message; }
  </script>
  ```
  Common causes: duplicate `let`/`const`, unmatched braces or single-backslash escapes from f-string escaping

---

## Common Pitfalls

- **Accidentally reverting widget logic** when editing surrounding prose (or vice versa). Keep edits surgical.
- **Formulas silently changing** during refactors. Always verify financial calculations after any code change.
- **Dead code accumulating** from removed widgets. Clean up associated JS, CSS, and data when removing a widget.
- **Stat box layouts overflowing** on mobile. Test grid layouts at narrow widths; split into multiple rows if needed.
- **Chart.js annotation plugin not loading** — make sure both `chart.js@4` AND `chartjs-plugin-annotation@3` CDN scripts are included.
- **Chart instance leaks** — always `chart.destroy()` before creating a new one in the same canvas.
- **Divi visual builder mangles inline styles** — use Code Modules, paste into Text/Code editor, not visual.

---

## Accessibility (don't skip)

- Semantic HTML where possible
- Sufficient color contrast — body text should never be pure black
- `title` attributes on interactive icon-only buttons
- `cursor: pointer` on interactives
- `:focus-visible` outlines on all focusable elements
- `prefers-reduced-motion` media query to zero out animations
- Animations: subtle, 0.15s for feedback, 0.3s for layout changes — never flashy
