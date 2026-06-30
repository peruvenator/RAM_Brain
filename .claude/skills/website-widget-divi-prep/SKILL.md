# Skill: website-widget-divi-prep

Audit an HTML widget for Divi/WordPress compatibility before deployment. Produces a pass/fail report with specific fixes.

## When to Use

Run this skill proactively — without waiting for the user to ask — whenever:
- The user says they are building a widget "for the website," "for returnstacked.com," "for the Divi site," or "to embed on WordPress"
- The user asks to prepare or finalize a widget for deployment
- The user runs `/widget-handoff` — this skill should be confirmed as passing first

Also invoke directly with `/website-widget-divi-prep`.

---

## Background: Why Divi Breaks Widgets

Divi applies aggressive global CSS resets to bare HTML elements (`button`, `input`, `select`, `a`, `p`, etc.) and loads them at high specificity. Without proper scoping, Divi's styles bleed into the widget and override its styling silently. This has caused real breakage: buttons disappearing, gray inputs, broken arrow glyphs, and intake overlay flash.

The fix pattern established for this project:
- All widget CSS scoped under a single root wrapper class (e.g., `.rsv-widget`)
- Bare element resets inside the widget use `:where()` to zero out specificity, so component classes always win
- `isolation: isolate` on the root wrapper creates a stacking context boundary
- JS extracted to a separate file loaded via WordPress enqueue (not inline in the HTML)

---

## Audit Steps

### 1. Identify the widget file(s)

Find the main widget HTML file. If there's a build script, check whether the build has been run recently (compare source files vs output timestamps or ask the user). If the build is stale, prompt the user to run it before continuing.

### 2. CSS Scoping Audit

Read the widget's `<style>` block(s) and check:

**A. Root wrapper class**
- Confirm there is a single root wrapper element with a unique class (e.g., `.rsv-widget`, `.my-widget`)
- Every CSS rule must be prefixed with this class
- Flag any rule that targets bare elements without the wrapper prefix (e.g., `button { }` instead of `.rsv-widget button { }`)

**B. `:where()` on bare element resets**
- Any rule that resets a bare HTML element (`button`, `input`, `select`, `textarea`, `a`, `ul`, `li`, `p`, `h1`-`h6`, `table`, etc.) inside the widget MUST use `:where()`:
  - Correct: `.rsv-widget :where(button) { }`
  - Wrong: `.rsv-widget button { }` — this has class+element specificity and will lose to component class overrides
- Flag any bare element reset that does NOT use `:where()`

**C. No `!important`**
- Flag every `!important` declaration. These fight Divi and each other unpredictably.
- Exception: one or two may be unavoidable for Divi overrides — note these explicitly rather than treating them as automatic failures

**D. No global scope pollution**
- Flag any rule targeting `body`, `html`, `:root`, or `*` without the widget wrapper prefix
- CSS custom properties should be defined on the root wrapper class, not `:root`

**E. `isolation: isolate`**
- Confirm the root wrapper element has `isolation: isolate` in its CSS
- This creates a stacking context so z-index inside the widget doesn't interfere with Divi's modal/overlay z-index

### 3. JavaScript Audit

Read the widget's `<script>` block(s) and check:

**A. No `document.write()`**
- Flag any usage — it breaks async loading in WordPress

**B. Global namespace**
- Widget JS should be wrapped in an IIFE or use a single top-level namespace object
- Flag any `var`/`let`/`const` declared at the top level that could collide with Divi's globals (jQuery, `$`, common names)

**C. jQuery compatibility**
- Divi loads jQuery. If the widget uses `$`, confirm it's either using the widget's own bundled library or wrapping in `jQuery(function($) { })` to avoid conflicts
- Flag bare `$(...)` calls if jQuery is not bundled in the widget

**D. JS/HTML separation**
- If the widget is going into WordPress via a PHP plugin or shortcode, the JS should be in a separate `.js` file enqueued by WordPress — not inline in the HTML
- Flag if JS is only available inline and there's no extracted JS file

### 4. HTML Structure Audit

**A. Single root wrapper**
- Confirm the widget has exactly one root element with the wrapper class
- No stray elements outside the wrapper that could affect the page layout

**B. No conflicting IDs**
- Flag any `id` attributes that are generic enough to clash with Divi page elements (e.g., `#header`, `#content`, `#main`, `#sidebar`)

**C. Font loading**
- If fonts are loaded from a CDN (`@import` or `<link>`), note that Divi may already load the same font — double-loading causes flash. Recommend checking whether the font is already available in the Divi theme before adding a second load.

---

## Output Format

Produce a structured report directly in the chat:

```
## Divi Prep Report — [Widget Name]

### Result: PASS / FAIL / PASS WITH WARNINGS

### CSS
- [PASS] All rules scoped under .rsv-widget
- [PASS] Bare element resets use :where()
- [FAIL] Line 412: `!important` on `.rsv-widget .btn` — review whether this is needed
- [PASS] isolation: isolate present on root wrapper

### JavaScript
- [PASS] No document.write()
- [PASS] JS wrapped in IIFE
- [WARN] jQuery `$` used — confirm Divi jQuery compatibility or bundle a local copy

### HTML
- [PASS] Single root wrapper
- [PASS] No conflicting IDs

### Action Required Before Handoff
1. Line 412: Remove or justify the !important on .rsv-widget .btn
2. Confirm $ / jQuery strategy

### Ready for handoff: YES / NO (resolve items above first)
```

If the result is PASS or PASS WITH WARNINGS (no blocking issues), tell the user: "Widget passes Divi prep. You can now run `/widget-handoff` to package for the developer."

If FAIL, list the blocking items and stop. Do not proceed to handoff until resolved.

---

### 5. Divi Harness Test

Before handing off to the developer, generate (or verify) a `test_divi_harness.html` file in the project root. This simulates Divi's CSS bleed and the WordPress script-loading order locally — far faster than deploying to a staging server.

**When to generate:** If no harness exists for this widget, or if the embed/JS filenames have changed.

**The harness does four things:**
1. Applies known Divi global CSS overrides as a `<style>` block (buttons, inputs, fonts, paragraphs, headings, `.DiviArea` z-index)
2. Enqueues the same CDN dependencies the PHP plugin would load in WordPress `<head>`
3. Fetches the embed HTML, extracts its `<style>` into `<head>`, injects any window config object, then loads the `.js` file dynamically in the right order
4. Calls the widget's init function manually (DOMContentLoaded has already fired at fetch time)

**To run:** `python -m http.server 8080` from the project root, then open `http://localhost:8080/test_divi_harness.html`. Do NOT open via `file://` — `fetch()` will be blocked by CORS.

**Harness template** (adapt the five config variables at the top):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[WIDGET_NAME] — Divi CSS Simulation Harness</title>

  <!--
    === CONFIG — change these five values for each widget ===
    EMBED_FILE:    the embed HTML filename (no HTML wrapper, just widget div+CSS+<script src>)
    JS_FILE:       the extracted JS filename
    WIDGET_CONFIG: JS to inject before the widget script (simulate PHP shortcode injection)
                   Set to empty string '' if the widget needs no config object.
    ROOT_ID:       the widget's root element id (used to extract from parsed embed HTML)
    INIT_CALL:     JS expression to initialize the widget after the script loads.
                   Set to '' if the widget self-initializes on DOMContentLoaded.
  -->
  <script>
    var HARNESS_CONFIG = {
      EMBED_FILE:    'widget_embed.html',
      JS_FILE:       'widget.js',
      WIDGET_CONFIG: '',   // e.g. 'window.MY_CONFIG = { apiBase: "..." };'
      ROOT_ID:       'my-widget-root',
      INIT_CALL:     '',   // e.g. 'MyWidget.init()'
      WIDGET_NAME:   '[Widget Name]'
    };
  </script>

  <!--
    CDN dependencies — add/remove to match what the PHP plugin enqueues in <head>.
    Chart.js, annotation plugin, jsPDF, and DM Sans are common for RS widgets.
  -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script> -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script> -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/jspdf@2/dist/jspdf.umd.min.js"></script> -->
  <!-- <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet"> -->

  <style>
    /* === SIMULATED DIVI GLOBAL CSS ===
       These mirror the known Divi theme rules that bleed into widgets.
       If the widget renders correctly below, its scoping is winning. */

    body { font-family: Georgia, "Times New Roman", serif; font-size: 14px; color: #666666; line-height: 1.7em; }

    input, input[type="text"], input[type="email"], input[type="number"],
    input[type="date"], input[type="search"], select, textarea {
      width: 100%; box-sizing: border-box; min-height: 38px;
      background-color: #f5f5f5; border: 1px solid #d9d9d9; border-radius: 0;
      color: #666666; font-size: 14px; font-family: Georgia, serif;
      letter-spacing: 0; line-height: 1.7em; padding: 8px 12px;
    }
    p { padding-bottom: 1em; line-height: 1.7em; }
    h1, h2, h3, h4, h5, h6 { font-family: Georgia, serif; font-weight: 500; line-height: 1em; padding-bottom: 10px; color: #333333; }
    button {
      background-color: #2ea3f2; color: #ffffff; border: none; border-radius: 3px;
      padding: 0.3em 1em; font-size: 14px; font-family: Georgia, serif;
      letter-spacing: 2px; text-transform: uppercase; cursor: pointer; min-height: 38px; width: auto;
    }
    a { color: #2ea3f2; text-decoration: none; }
    a:hover { text-decoration: underline; }
    ul, ol { padding-left: 1.5em; padding-bottom: 1em; list-style: disc outside; }
    li { line-height: 1.7em; }
    .DiviArea { z-index: 1000000; position: relative; }

    #harness-banner {
      background: #172c3a; color: #e0e0e0; padding: 10px 20px;
      font-family: Arial, sans-serif; font-size: 12px;
      display: flex; align-items: center; gap: 12px;
    }
    #harness-banner strong { color: #14cfa6; font-size: 13px; }
    #harness-banner code { background: rgba(255,255,255,0.12); padding: 2px 6px; border-radius: 3px; }
    #harness-error {
      display: none; margin: 30px; padding: 24px;
      background: #fff5f5; border: 1px solid #ffcccc; border-radius: 6px;
      font-family: Arial, sans-serif; font-size: 13px; line-height: 1.6;
    }
    #harness-error strong { color: #cc0000; }
    #harness-error code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
  </style>
</head>
<body>

  <div id="harness-banner">
    <strong id="harness-title">Divi CSS Simulation Harness</strong>
    <span id="harness-status">Loading embed file...</span>
  </div>

  <div class="DiviArea" style="position:relative;">
    <div id="widget-container"></div>
  </div>

  <div id="harness-error">
    <strong>Could not load widget</strong><br><br>
    <span id="harness-error-msg"></span><br><br>
    Fix steps:<br>
    1. Build the widget (run the project's build script)<br>
    2. Start a local server from the project root: <code>python -m http.server 8080</code><br>
    3. Open <code>http://localhost:8080/test_divi_harness.html</code>
  </div>

  <script>
    var cfg = HARNESS_CONFIG;
    document.getElementById('harness-title').textContent = cfg.WIDGET_NAME + ' — Divi CSS Simulation Harness';
    document.getElementById('harness-status').textContent = 'Loading ' + cfg.EMBED_FILE + '...';

    fetch(cfg.EMBED_FILE)
      .then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status + ' loading ' + cfg.EMBED_FILE + '. Run the build script first.');
        return r.text();
      })
      .then(function(html) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');

        // Move the widget's <style> block to <head> so it applies reliably
        var styleEl = doc.querySelector('style');
        if (styleEl) { styleEl.parentNode.removeChild(styleEl); document.head.appendChild(styleEl); }

        // Strip <script> tags — scripts from innerHTML don't execute; re-added below
        Array.from(doc.querySelectorAll('script')).forEach(function(s) { s.parentNode.removeChild(s); });

        // Inject the widget HTML
        var root = cfg.ROOT_ID ? doc.getElementById(cfg.ROOT_ID) : null;
        document.getElementById('widget-container').appendChild(root || doc.body);

        // Inject window config (simulates PHP shortcode injection)
        if (cfg.WIDGET_CONFIG) {
          var cfgScript = document.createElement('script');
          cfgScript.textContent = cfg.WIDGET_CONFIG;
          document.head.appendChild(cfgScript);
        }

        // Load widget JS
        document.getElementById('harness-status').textContent = cfg.EMBED_FILE + ' loaded. Loading ' + cfg.JS_FILE + '...';
        var widgetScript = document.createElement('script');
        widgetScript.src = cfg.JS_FILE;
        widgetScript.onload = function() {
          try {
            if (cfg.INIT_CALL) {
              document.getElementById('harness-status').textContent = cfg.JS_FILE + ' loaded. Calling ' + cfg.INIT_CALL + '...';
              eval(cfg.INIT_CALL);
            }
            document.getElementById('harness-status').textContent =
              'Divi global styles active. If layout looks correct, the widget scoping is winning.';
          } catch(e) {
            document.getElementById('harness-status').innerHTML =
              '<span style="color:#ff6b6b;">' + cfg.INIT_CALL + ' threw: ' + e.message + ' — check Console</span>';
          }
        };
        widgetScript.onerror = function() {
          document.getElementById('harness-status').innerHTML =
            '<span style="color:#ff6b6b;">Failed to load ' + cfg.JS_FILE + ' (404?) — is the file in the project folder?</span>';
        };
        document.head.appendChild(widgetScript);
      })
      .catch(function(err) {
        document.getElementById('harness-error-msg').textContent = err.message;
        document.getElementById('harness-error').style.display = 'block';
      });
  </script>
</body>
</html>
```

Add this file to the project root as `test_divi_harness.html` and fill in the five `HARNESS_CONFIG` values. The RSV Advanced Visualizer's harness (in `projects/portfolio-visualizer-widget/test_divi_harness.html`) is a working reference.

---

## Notes

- This skill audits the built output file, not the source. If there's a build step, the build must be current.
- `:where()` specificity behavior: `selector-weight = 0` for anything inside `:where()`. This means `.rsv-widget :where(button)` has specificity of one class (0,1,0), so `.rsv-widget .btn` (also 0,1,0 but more specific due to later declaration) wins correctly. Never replace `:where()` resets with plain element selectors inside the widget.
- The harness requires a local HTTP server (`python -m http.server 8080`). Opening via `file://` blocks `fetch()` due to CORS and will always fail.
