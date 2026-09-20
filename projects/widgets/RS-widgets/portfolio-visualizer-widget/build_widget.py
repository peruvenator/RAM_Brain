"""
Build the RS_advanced_visualizer_widget.html file with embedded data.
Reads extracted JSON data and generates the complete single-file widget.
"""
import json
import os

OUTPUT_FILE = "RS_advanced_visualizer_widget_web.html"

# Load data
with open("data/indices_compact.json") as f:
    indices_data = f.read()
with open("data/index_map.json") as f:
    index_map_data = f.read()
with open("data/disclosures.json") as f:
    disclosures = json.load(f)

# Default fee / financing cost assumptions for overlay (stack) strategies.
# Injected into the general disclosures so it appears in BOTH the on-screen
# disclaimer and the PDF export (PDF_DISCLOSURES is built from this same dict).
# Keep these values in sync with STACK_FEE_DEFAULTS in the widget JS below.
_cost_assumptions_disclosure = (
    "Default Cost Assumptions. Overlay (stacked) strategies in this tool carry default cost "
    "assumptions that are applied automatically unless adjusted by the user in the Advanced Fee "
    "Configuration. A financing spread of 0.50% per annum above the U.S. Treasury Bill rate is "
    "applied to Managed Futures (CTA), Managed Futures (Trend), Futures Yield (Carry), Systematic "
    "Global Macro, Merger Arbitrage, Merger Arbitrage (AB), Risk-Weighted Gold/Bitcoin, and Gold. "
    "This spread is in addition to the automatic Treasury Bill financing cost applied to all "
    "stacked exposures. Default annual management fees are also applied to certain overlays: "
    "Gold 0.40%, Risk-Weighted Gold/Bitcoin 0.50%, and Merger Arbitrage (AB) 0.95%. Indices that "
    "are already reported net of fees do not carry an additional management fee. These assumptions "
    "are estimates for illustrative purposes only, are user-adjustable, and may not reflect the "
    "actual fees and financing costs of any specific investment product."
)
if _cost_assumptions_disclosure not in disclosures["general"]:
    disclosures["general"].insert(3, _cost_assumptions_disclosure)
with open("data/custom_assets.json") as f:
    custom_assets_data = f.read()
with open("data/ticker_info.json") as f:
    ticker_info_data = f.read()
with open("data/intake_engine.js") as f:
    intake_engine_js = f.read()

# PDF assets pre-extracted in data/ for Phase 6:
with open("data/logo_ps_white_uri.txt") as f:
    logo_white_uri = f.read().strip()
with open("data/logo_white_uri.txt") as f:
    logo_icon_white_uri = f.read().strip()
with open("data/logo_black_uri.txt") as f:
    logo_black_uri = f.read().strip()
with open("data/logo_ps_black_uri.txt") as f:
    logo_ps_black_uri = f.read().strip()
with open("data/bg_image_uri.txt") as f:
    bg_image_uri = f.read().strip()
with open("data/dmRegular.txt") as f:
    dm_regular_b64 = f.read().strip()
with open("data/dmBold.txt") as f:
    dm_bold_b64 = f.read().strip()
with open("data/dmItalic.txt") as f:
    dm_italic_b64 = f.read().strip()
with open("data/dmBoldItalic.txt") as f:
    dm_bolditalic_b64 = f.read().strip()

# Build disclosures HTML
def _disc_esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace("\n", "<br>"))

def _render_definition(text):
    """Render one entry from indexDefinitions. Three shapes are handled:
       1. Section header (short, no delimiter)  e.g. "Statistics Definitions" -> <h3>
       2. Index definition "Name (Source). Desc" -> bold the "Name (Source)" head
       3. Term definition "Term: Desc"           -> bold the term
       Anything else renders as a plain paragraph."""
    s = text.strip()
    # 1. Section subheading
    if "). " not in s and ": " not in s and len(s) < 40:
        return f"<h3>{_disc_esc(s)}</h3>\n"
    # 2. Index definition: split on the FIRST "). " (avoids the "U.S." period trap)
    i = s.find("). ")
    if i != -1:
        head = s[:i + 1]          # include the closing ')'
        desc = s[i + 3:]          # text after "). "
        return f"<p><strong>{_disc_esc(head)}</strong>. {_disc_esc(desc)}</p>\n"
    # 3. Term/statistic definition: "Term: Desc" (guard against long sentences)
    j = s.find(": ")
    if j != -1:
        term = s[:j]
        desc = s[j + 2:]
        if len(term) < 60 and ". " not in term:
            return f"<p><strong>{_disc_esc(term)}:</strong> {_disc_esc(desc)}</p>\n"
    # 4. Plain paragraph
    return f"<p>{_disc_esc(s)}</p>\n"

disclosures_html = '<div class="rsv-disclosures-content">\n'
disclosures_html += '<h3>Important Disclosures</h3>\n'
for para in disclosures["general"]:
    disclosures_html += f'<p>{_disc_esc(para)}</p>\n'
disclosures_html += '<h3>Index Definitions</h3>\n'
for defn in disclosures["indexDefinitions"]:
    disclosures_html += _render_definition(defn)
disclosures_html += '</div>'


html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Return Stacked&reg; Visualizer - Return Stacked&reg; Portfolio Solutions</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
<script src="https://cdn.jsdelivr.net/npm/jspdf@2/dist/jspdf.umd.min.js"></script>
<style>
/* ── Reset & Base ── */
.rsv-widget * {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}
.rsv-widget {{
  font-family: "DM Sans", sans-serif;
  color: #2c3641;
  background: #ffffff;
  max-width: 1264px;
  margin: 0 auto;
  padding: var(--card-pad);
  line-height: 1.5;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  isolation: isolate;
  /* Card look (matches the simple visualizer): rounded white panel on a
     light backdrop with a soft drop shadow. */
  border-radius: var(--card-radius);
  box-shadow: 0 2px 16px rgba(23, 44, 58, 0.07);
}}

/* ── Divi Defense: bare element resets ── */
/* :where() zeroes specificity so component classes always win */
.rsv-widget :where(h1, h2, h3, h4, h5, h6) {{
  font-family: "DM Sans", sans-serif;
  color: inherit;
  margin: 0;
  padding: 0;
  line-height: 1.3;
  letter-spacing: normal;
  word-spacing: normal;
  -webkit-font-smoothing: antialiased;
}}
.rsv-widget :where(p) {{
  font-family: "DM Sans", sans-serif;
  color: inherit;
  margin: 0;
  padding: 0;
  line-height: 1.5;
  font-size: inherit;
}}
.rsv-widget :where(a) {{
  color: inherit;
  text-decoration: none;
}}
.rsv-widget :where(table) {{
  border-collapse: collapse;
  border-spacing: 0;
  border: none;
  width: auto;
  table-layout: auto;
}}
.rsv-widget :where(th, td) {{
  border: none;
  padding: 0;
  text-align: left;
  font-weight: inherit;
  vertical-align: middle;
}}
.rsv-widget :where(input, select, textarea) {{
  font-family: "DM Sans", sans-serif;
  font-size: 13px;
  color: var(--text-primary);
  background: var(--white);
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  padding: 6px 10px;
  margin: 0;
  appearance: auto;
  -webkit-appearance: auto;
  line-height: normal;
  outline: none;
}}
.rsv-widget :where(button) {{
  font-family: "DM Sans", sans-serif;
  font-size: inherit;
  color: inherit;
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  cursor: pointer;
  line-height: normal;
  -webkit-appearance: none;
  appearance: none;
}}
.rsv-widget :where(label) {{
  font-weight: inherit;
  display: inline;
  margin: 0;
  padding: 0;
}}
.rsv-widget :where(img) {{
  max-width: 100%;
  height: auto;
  border: none;
}}
.rsv-widget canvas {{
  display: block;
}}

/* ── Brand Colors ── */
.rsv-widget {{
  --teal: #14cfa6;
  --teal-dark: #0c7c64;
  --teal-light: #a1d7c6;
  --accent-green: #60cca8;
  --navy: #2a3f5b;
  --blue: #3a6a9c;
  --blue-light: #7da5ce;
  --text-primary: #2c3641;
  --text-secondary: #625c6d;
  --cover-dark: #172c3a;
  --section-gray: #f5f6fa;
  --border-gray: #bfbfbf;
  --yellow: #ebe96a;
  --white: #ffffff;
  --danger: #e74c3c;
  --success: #60cca8;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --card-radius: 20px;
  --card-pad: 32px;
}}

/* ── Header ── */
.rsv-header {{
  background: var(--cover-dark);
  color: var(--white);
  padding: 24px 32px;
  /* Full-bleed to the card edges: cancel the card's padding so the black
     header sits flush with the top, with the white content floating below.
     Corner radius matches the card so the top corners line up cleanly. */
  margin: calc(-1 * var(--card-pad)) calc(-1 * var(--card-pad)) 0;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
}}
.rsv-header h1 {{
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}}
.rsv-header p {{
  font-size: 13px;
  color: var(--teal-light);
  font-weight: 400;
}}

/* ── Portfolio Tabs ── */
.rsv-tabs {{
  display: flex;
  gap: 0;
  background: var(--section-gray);
  border-bottom: 2px solid var(--border-gray);
  /* Full-bleed to the card edges (no white space L/R), like the header.
     Internal padding keeps the tab labels aligned with the content below. */
  margin: 0 calc(-1 * var(--card-pad));
  padding: 0 var(--card-pad);
}}
.rsv-tab {{
  padding: 10px 16px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  border: none;
  background: transparent;
  font-family: inherit;
  position: relative;
  transition: color 0.2s cubic-bezier(0.23, 1, 0.32, 1);
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}}
.rsv-tab:hover {{
  color: var(--text-primary);
}}
.rsv-tab.active {{
  color: var(--teal);
  font-weight: 700;
}}
.rsv-tab::after {{
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--teal);
  border-radius: 2px 2px 0 0;
  transform: scaleX(0);
  transition: transform 0.25s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-tab.active::after {{
  transform: scaleX(1);
}}
.rsv-tab.disabled {{
  color: var(--border-gray);
  cursor: default;
}}
.rsv-tab .rsv-tab-toggle {{
  width: 14px;
  height: 14px;
  margin-left: 6px;
  vertical-align: middle;
  accent-color: var(--teal);
  cursor: pointer;
}}
/* Plain-text label — renaming happens in the Portfolio Name field, not the tab */
.rsv-tab .rsv-tab-name {{
  display: inline-block;
  font-family: inherit;
  font-size: 13px;
  font-weight: inherit;
  color: inherit;
  padding: 3px 6px;
  min-width: 80px;
  max-width: 160px;
  cursor: pointer;
  white-space: normal;
  word-break: break-word;
  line-height: 1.25;
  text-align: center;
  vertical-align: middle;
}}

/* ── Portfolio Name field (above step 1) ── */
.rsv-name-row {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}}
.rsv-name-row label {{
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}}
.rsv-name-row input {{
  font-family: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  width: 240px;
  color: var(--text-primary);
}}
.rsv-name-row input:focus {{
  outline: none;
  border-color: var(--teal);
  box-shadow: 0 0 0 2px rgba(20, 207, 166, 0.15);
}}

/* ── Custom Data dropzone ── */
.rsv-dropzone {{
  border: 2px dashed var(--border-gray);
  border-radius: 8px;
  padding: 28px 20px;
  text-align: center;
  background: var(--section-gray);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}}
.rsv-dropzone:hover {{
  border-color: var(--text-secondary);
}}
.rsv-dropzone.rsv-dragover {{
  border-color: var(--teal);
  background: rgba(20, 207, 166, 0.06);
}}
.rsv-dropzone .rsv-linklike {{
  color: var(--blue);
  text-decoration: underline;
}}

/* ── Card / Panel ── */
/* No border: the outer .rsv-widget card shadow now defines the edge, so the
   gray content frame ("wireframe") is removed. The tab bar's bottom border
   still separates the tabs from the panel content. */
.rsv-panel {{
  background: var(--white);
  border: none;
  padding: 24px;
}}
.rsv-section-title {{
  font-size: 15px;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--teal);
  display: inline-block;
}}
/* Plain variant: no teal underline, extra breathing room above/below and indented from the left */
.rsv-section-title--plain {{
  border-bottom: none;
  padding-bottom: 0;
  margin-top: 20px;
  margin-bottom: 16px;
  margin-left: 16px;
}}
.rsv-page-title {{
  font-size: 22px;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 20px;
}}

/* ── Numbered Section Headers ── */
.rsv-step-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}}
.rsv-step-num {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--teal);
  color: var(--white);
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}}
.rsv-step-label {{
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--navy);
  line-height: 1.3;
}}

/* ── Tooltips ── */
.rsv-tooltip {{
  position: relative;
  display: inline-block;
  color: var(--border-gray);
  cursor: help;
  font-size: 12px;
  font-weight: 700;
  margin-left: 4px;
}}
.rsv-tooltip .rsv-tooltip-text,
.rsv-btn-tooltip .rsv-tooltip-text {{
  visibility: hidden;
  width: 240px;
  background: var(--navy);
  color: #fff;
  text-align: left;
  border-radius: 4px;
  padding: 8px 10px;
  position: absolute;
  z-index: 10;
  bottom: 125%;
  left: 50%;
  margin-left: -120px;
  font-size: 11px;
  font-weight: 400;
  line-height: 1.4;
  opacity: 0;
  transform: translateY(4px) scale(0.98);
  transition: opacity 0.2s cubic-bezier(0.23, 1, 0.32, 1), transform 0.2s cubic-bezier(0.23, 1, 0.32, 1);
  pointer-events: none;
}}
.rsv-tooltip:hover .rsv-tooltip-text,
.rsv-btn-tooltip:hover .rsv-tooltip-text {{
  visibility: visible;
  transform: translateY(0) scale(1);
  opacity: 1;
}}
.rsv-btn-tooltip {{
  position: relative;
  display: inline-block;
}}

/* ── Saved Portfolios ── */
.rsv-saved-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}}
.rsv-saved-row select {{
  font-family: inherit;
  font-size: 12px;
  padding: 5px 8px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  color: var(--text-primary);
  flex: 1;
  max-width: 280px;
}}
.rsv-saved-row select:focus {{
  outline: none;
  border-color: var(--teal);
}}
.rsv-saved-row button {{
  font-family: inherit;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid var(--border-gray);
  background: var(--white);
  color: var(--text-secondary);
}}
.rsv-saved-row button:hover {{
  border-color: var(--teal);
  color: var(--teal-dark);
}}
.rsv-saved-row button:active {{
  transform: scale(0.97);
}}

/* ── Asset Allocation Table ── */
.rsv-alloc-table {{
  width: 100%;
  table-layout: fixed; /* column widths are hard caps — content can never widen a column */
  border-collapse: collapse;
  margin-bottom: 12px;
}}
.rsv-alloc-table th {{
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--border-gray);
}}
.rsv-alloc-table td {{
  padding: 6px 8px;
  border-bottom: 1px solid var(--section-gray);
  vertical-align: middle;
}}
.rsv-alloc-table tr:hover {{
  background: #f8f9fb;
}}
.rsv-alloc-table select {{
  font-family: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  background: var(--white);
  color: var(--text-primary);
  width: 100%;
  cursor: pointer;
}}
.rsv-alloc-table select:focus {{
  outline: none;
  border-color: var(--teal);
  box-shadow: 0 0 0 2px rgba(20, 207, 166, 0.15);
}}
.rsv-alloc-table select option:disabled {{
  color: #b0b0b0;
}}
.rsv-alloc-table input[type="number"] {{
  font-family: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  width: 80px;
  max-width: 100%; /* never wider than the fixed-layout column */
  text-align: center;
  color: var(--text-primary);
}}
/* Hide the native up/down spinner arrows on all numeric inputs */
.rsv-alloc-table input[type="number"]::-webkit-outer-spin-button,
.rsv-alloc-table input[type="number"]::-webkit-inner-spin-button,
.rsv-fee-row input[type="number"]::-webkit-outer-spin-button,
.rsv-fee-row input[type="number"]::-webkit-inner-spin-button {{
  -webkit-appearance: none;
  margin: 0;
}}
.rsv-alloc-table input[type="number"],
.rsv-fee-row input[type="number"] {{
  -moz-appearance: textfield;
  appearance: textfield;
}}
.rsv-alloc-table input[type="number"]:focus {{
  outline: none;
  border-color: var(--teal);
  box-shadow: 0 0 0 2px rgba(20, 207, 166, 0.15);
}}

/* ── Searchable Asset Combobox ── */
.rsv-combo {{
  position: relative;
  width: 100%;
}}
.rsv-combo-trigger {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  width: 100%;
  font-family: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  background: var(--white);
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}}
.rsv-combo-trigger:focus-visible {{
  outline: none;
  border-color: var(--teal);
  box-shadow: 0 0 0 2px rgba(20, 207, 166, 0.15);
}}
.rsv-combo-trigger.is-placeholder .rsv-combo-value {{
  color: #888;
}}
.rsv-combo-value {{
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.rsv-combo-arrow {{
  flex: 0 0 auto;
  font-size: 10px;
  color: var(--text-secondary);
  transition: transform 150ms ease;
}}
.rsv-combo.is-open .rsv-combo-arrow {{
  transform: rotate(180deg);
}}
.rsv-combo-panel {{
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 1000;
  min-width: 100%;
  max-width: 100%;
  background: var(--white);
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
}}
.rsv-combo-panel[hidden] {{
  display: none;
}}
.rsv-combo-search-wrap {{
  padding: 8px;
  border-bottom: 1px solid var(--border-gray);
}}
.rsv-combo-search {{
  width: 100%;
  font-family: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  color: var(--text-primary);
  box-sizing: border-box;
}}
.rsv-combo-search:focus {{
  outline: none;
  border-color: var(--teal);
  box-shadow: 0 0 0 2px rgba(20, 207, 166, 0.15);
}}
.rsv-combo-list {{
  max-height: 320px;
  overflow-y: auto;
  padding: 4px 0;
}}
.rsv-combo-group {{
  padding: 8px 12px 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  background: transparent;
}}
.rsv-combo-option {{
  display: block;
  width: 100%;
  font-family: inherit;
  font-size: 13px;
  /* Indent options so they sit visually below their group header */
  padding: 6px 12px 6px 24px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}}
.rsv-combo-option:hover:not(.is-disabled),
.rsv-combo-option.is-active:not(.is-disabled) {{
  background: var(--section-gray);
}}
.rsv-combo-option.is-selected {{
  color: var(--teal);
  font-weight: 600;
}}
.rsv-combo-option.is-disabled {{
  color: #b0b0b0;
  cursor: not-allowed;
}}
.rsv-combo-clear {{
  /* The clear/placeholder option isn't under a group, so don't indent it */
  padding-left: 12px;
  font-style: italic;
  color: var(--text-secondary);
}}
.rsv-combo-empty {{
  padding: 12px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-style: italic;
}}
/* Inline variant: trigger styled like a tab-bar item (used for global Saved Portfolios) */
.rsv-combo--inline {{
  width: auto;
}}
.rsv-combo--inline .rsv-combo-trigger {{
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: var(--navy);
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}}
.rsv-combo--inline .rsv-combo-trigger:hover {{
  color: var(--text-primary);
}}
.rsv-combo--inline .rsv-combo-panel {{
  min-width: 240px;
}}
.rsv-combo-footer {{
  padding: 8px 12px;
  border-top: 1px solid var(--border-gray);
  text-align: right;
}}
.rsv-combo-footer button {{
  font-family: inherit;
  font-size: 12px;
  padding: 4px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  background: var(--white);
  color: var(--text-secondary);
  cursor: pointer;
}}
.rsv-combo-footer button:hover {{
  color: var(--text-primary);
  border-color: var(--text-secondary);
}}

/* ── Add Row Button ── */
.rsv-add-btn {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  color: var(--blue);
  background: transparent;
  border: 1px dashed var(--blue);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s cubic-bezier(0.23, 1, 0.32, 1), border-color 0.2s cubic-bezier(0.23, 1, 0.32, 1), color 0.2s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-add-btn:hover {{
  background: rgba(58, 106, 156, 0.06);
  border-color: var(--teal);
  color: var(--teal-dark);
}}
.rsv-add-btn:active {{
  transform: scale(0.97);
}}

/* ── Remove Row Button ── */
.rsv-remove-btn {{
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  font-size: 16px;
  padding: 2px 6px;
  border-radius: 3px;
  line-height: 1;
}}
.rsv-remove-btn:hover {{
  background: rgba(217, 83, 79, 0.1);
}}
.rsv-remove-btn:active {{
  transform: scale(0.95);
}}

/* ── Totals Row ── */
.rsv-total-row {{
  font-weight: 700;
}}
.rsv-total-row td {{
  border-top: 2px solid var(--navy);
  padding-top: 10px;
}}
.rsv-total-valid {{
  color: var(--success);
}}
.rsv-total-invalid {{
  color: var(--danger);
}}

/* ── Summary Bar ── */
.rsv-summary-bar {{
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  padding: 16px 20px;
  background: var(--section-gray);
  border-radius: 6px;
  margin-top: 16px;
  margin-bottom: 16px;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.04);
}}
.rsv-summary-item {{
  display: flex;
  flex-direction: column;
}}
.rsv-summary-label {{
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}}
.rsv-summary-value {{
  font-size: 18px;
  font-weight: 700;
  color: var(--navy);
}}
.rsv-summary-value.warning {{
  color: var(--danger);
}}

/* ── Fee Input ── */
.rsv-fee-row {{
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}}
.rsv-fee-row label {{
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}}
.rsv-fee-row input {{
  font-family: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  width: 80px;
  text-align: center;
}}
.rsv-fee-row input:focus {{
  outline: none;
  border-color: var(--teal);
  box-shadow: 0 0 0 2px rgba(20, 207, 166, 0.15);
}}

/* ── Validation Messages ── */
.rsv-validation {{
  padding: 10px 16px;
  border-radius: 0 6px 6px 0;
  font-size: 12px;
  font-weight: 500;
  margin-top: 8px;
  background: #f8f9fc;
  border-left: 4px solid var(--border-gray);
  line-height: 1.5;
}}
/* State classes namespaced (rsv-error/rsv-success/rsv-info) so they don't
   collide with Divi/WordPress's own bare .error / .success form-state classes,
   which could otherwise bleed background/color into validation messages. */
.rsv-validation.rsv-error {{
  border-left-color: var(--danger);
  color: var(--danger);
}}
.rsv-validation.rsv-success {{
  border-left-color: var(--accent-green);
  color: var(--teal-dark);
}}
.rsv-validation.rsv-info {{
  border-left-color: var(--blue);
  color: var(--blue);
}}

/* ── Callout boxes (reusable) ── */
.rsv-callout {{
  background: #f8f9fc;
  border-left: 4px solid var(--border-gray);
  padding: 14px 20px;
  margin: 16px 0;
  border-radius: 0 8px 8px 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
}}
.rsv-callout.rsv-error {{ border-left-color: var(--danger); }}
.rsv-callout.rsv-success {{ border-left-color: var(--accent-green); }}
.rsv-callout.rsv-info {{ border-left-color: var(--blue); }}
.rsv-callout.rsv-warning {{ border-left-color: var(--yellow); }}

/* ── Chart Area ── */
.rsv-chart-area {{
  margin-top: 24px;
  background: var(--white);
  border: 1px solid var(--section-gray);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}}
.rsv-chart-tabs {{
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-gray);
  background: var(--section-gray);
}}
/* Comparison view: chart panes — only the active pane shows. Use :not() so hide rule's specificity (0,2,0)
   beats .rsv-chart-panel--side-by-side (0,1,0); active panes keep their natural block/grid display. */
[id^="rsv-comp-chart-"] {{
  margin-top: 24px;
}}
[id^="rsv-comp-chart-"]:not(.rsv-comp-chart-active) {{
  display: none;
}}
[id^="rsv-comp-chart-"] > .rsv-chart-controls {{
  margin-bottom: 16px;
}}
.rsv-chart-tab {{
  padding: 8px 18px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  position: relative;
  transition: color 0.15s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-chart-tab:hover {{
  color: var(--text-primary);
}}
.rsv-chart-tab.active {{
  color: var(--navy);
  font-weight: 700;
  background: var(--white);
}}
.rsv-chart-tab::after {{
  content: "";
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--teal);
  transform: scaleX(0);
  transition: transform 0.2s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-chart-tab.active::after {{
  transform: scaleX(1);
}}
.rsv-chart-controls {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px;
  border-bottom: 1px solid var(--section-gray);
  font-size: 12px;
  color: var(--text-secondary);
}}
.rsv-chart-controls label {{
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-weight: 500;
}}
.rsv-chart-controls input[type="checkbox"] {{
  accent-color: var(--teal);
}}
.rsv-chart-container {{
  padding: 16px;
  position: relative;
  height: 420px;
}}
/* Side-by-side variant: labels on row 1, charts on row 2, two columns */
.rsv-chart-panel--side-by-side {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto 1fr;
  grid-auto-flow: column;
  column-gap: 16px;
}}
@media (max-width: 720px) {{
  .rsv-chart-panel--side-by-side {{
    grid-template-columns: 1fr;
    grid-auto-flow: row;
  }}
}}
/* Download icon button -- appears over charts and next to table section titles */
.rsv-dl-btn {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--navy);
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--border-color, #d8d8d8);
  border-radius: 4px;
  cursor: pointer;
  transition: background 140ms cubic-bezier(0.23, 1, 0.32, 1), color 140ms, border-color 140ms;
  line-height: 1.2;
}}
.rsv-dl-btn:hover {{
  background: var(--navy);
  color: #fff;
  border-color: var(--navy);
}}
.rsv-dl-btn:active {{
  transform: scale(0.97);
}}
.rsv-dl-btn--chart {{
  position: absolute;
  top: 8px;
  right: 12px;
  z-index: 2;
  opacity: 0.55;
}}
.rsv-dl-btn--chart:hover {{
  opacity: 1;
}}
.rsv-dl-section > .rsv-section-title {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-left: 16px;
  padding-right: 16px;
}}
.rsv-chart-label {{
  font-size: 13px;
  font-weight: 700;
  color: var(--navy);
  padding: 8px 16px 0;
}}
.rsv-chart-stats {{
  font-size: 13px;
  font-weight: 600;
  color: #555;
  padding: 6px 16px 10px;
  line-height: 1.7;
}}
.rsv-chart-stats .hl {{
  color: var(--accent-green);
  font-weight: 700;
}}
.rsv-chart-stats .neg {{
  color: var(--danger);
  font-weight: 700;
}}
.rsv-chart-slider {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  margin: 6px 16px;
  font-size: 13px;
  color: #555;
  font-weight: 500;
}}
.rsv-chart-slider input[type="range"],
.rsv-chart-controls input[type="range"] {{
  -webkit-appearance: none;
  appearance: none;
  width: 160px;
  height: 6px;
  background: #dde2eb;
  border-radius: 3px;
  outline: none;
  padding: 0;
  margin: 0;
  cursor: pointer;
}}
.rsv-chart-slider input[type="range"]::-webkit-slider-runnable-track,
.rsv-chart-controls input[type="range"]::-webkit-slider-runnable-track {{
  height: 6px;
  border-radius: 3px;
  background: #dde2eb;
}}
.rsv-chart-slider input[type="range"]::-webkit-slider-thumb,
.rsv-chart-controls input[type="range"]::-webkit-slider-thumb {{
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--navy);
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.25);
  cursor: pointer;
  margin-top: -7px;
  transition: transform 0.15s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-chart-slider input[type="range"]::-webkit-slider-thumb:hover,
.rsv-chart-controls input[type="range"]::-webkit-slider-thumb:hover {{
  transform: scale(1.1);
}}
.rsv-chart-slider input[type="range"]::-moz-range-track,
.rsv-chart-controls input[type="range"]::-moz-range-track {{
  height: 6px;
  background: #dde2eb;
  border-radius: 3px;
  border: none;
}}
.rsv-chart-slider input[type="range"]::-moz-range-thumb,
.rsv-chart-controls input[type="range"]::-moz-range-thumb {{
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--navy);
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.25);
  cursor: pointer;
  transition: transform 0.15s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-chart-slider input[type="range"]::-moz-range-thumb:hover,
.rsv-chart-controls input[type="range"]::-moz-range-thumb:hover {{
  transform: scale(1.1);
}}
.rsv-chart-slider .slider-val,
.rsv-chart-controls .slider-val {{
  font-weight: 700;
  color: #fff;
  background: var(--navy);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  min-width: 80px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}}

/* ── Date Range Bar ── */
.rsv-date-range-bar {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--section-gray);
  border-radius: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--text-primary);
}}
.rsv-date-range-bar label {{
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 12px;
}}
.rsv-date-range-bar select,
.rsv-date-range-bar input[type="date"] {{
  font-family: inherit;
  font-size: 13px;
  padding: 5px 8px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  background: var(--white);
  color: var(--text-primary);
  cursor: pointer;
}}
.rsv-date-range-bar input[type="date"] {{
  width: 140px;
}}
.rsv-date-btn {{
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 14px;
  border: 1px solid var(--navy);
  border-radius: 4px;
  cursor: pointer;
  background: var(--white);
  color: var(--navy);
  transition: background-color 0.15s cubic-bezier(0.23, 1, 0.32, 1), color 0.15s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-date-btn:hover {{
  background: var(--navy);
  color: var(--white);
}}
.rsv-date-btn:active {{
  transform: scale(0.97);
}}
.rsv-date-quick-btns {{
  display: flex;
  gap: 4px;
  margin-left: 6px;
  padding-left: 10px;
  border-left: 1px solid var(--border-gray);
}}
.rsv-date-quick-btns button {{
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border: 1px solid var(--border-gray);
  border-radius: 4px;
  background: var(--white);
  color: var(--navy);
  cursor: pointer;
  transition: background-color 0.15s cubic-bezier(0.23, 1, 0.32, 1), color 0.15s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-date-quick-btns button:hover,
.rsv-date-quick-btns button.active {{
  background: var(--navy);
  color: var(--white);
  border-color: var(--navy);
}}
.rsv-date-quick-btns button:active {{
  transform: scale(0.97);
}}

/* ── Compute Button ── */
.rsv-compute-btn {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 22px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  color: var(--white);
  background: var(--teal);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s cubic-bezier(0.23, 1, 0.32, 1), transform 0.1s cubic-bezier(0.23, 1, 0.32, 1);
  margin-top: 20px;
}}
.rsv-compute-btn:hover {{
  background: var(--teal-dark);
}}
.rsv-compute-btn:active {{
  transform: scale(0.97);
}}
.rsv-compute-btn:disabled {{
  background: var(--border-gray);
  cursor: not-allowed;
}}

/* ── Button Variants ── */
.rsv-compute-btn--no-mt {{
  margin-top: 0;
}}
.rsv-compute-btn--secondary {{
  margin-top: 0;
  background: var(--blue);
}}
.rsv-compute-btn--secondary:hover {{
  background: #2d5580;
}}
.rsv-compute-btn--tertiary {{
  margin-top: 0;
  background: var(--text-secondary);
}}
.rsv-compute-btn--tertiary:hover {{
  background: #4a4557;
}}
.rsv-compute-btn--compact {{
  margin-top: 0;
  font-size: 12px;
  padding: 6px 14px;
  background: var(--navy);
}}
.rsv-compute-btn--compact:hover {{
  background: #232a34;
}}
.rsv-add-btn--filled {{
  margin-top: 0;
  background: var(--teal);
  color: var(--white);
  border-style: solid;
  border-color: var(--teal);
}}
.rsv-add-btn--filled:hover {{
  background: var(--teal-dark);
  border-color: var(--teal-dark);
  color: var(--white);
}}

/* Saved Comparisons controls box (top right of comparison panels) */
.rsv-comparison-controls {{
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 12px;
  width: fit-content;
  background: var(--white);
  border: 1px solid var(--border-gray);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}}
.rsv-comparison-controls .rsv-btn-tooltip {{
  display: block;
}}
.rsv-comparison-controls__btn {{
  width: 100%;
  justify-content: center;
  white-space: nowrap;
}}

/* Portfolio Comparison wrapper — sits in the tab bar, carries the active indicator */
.rsv-comparison-wrap {{
  margin-left: auto;
  display: flex;
  align-items: center;
  padding: 0 8px;
  position: relative;
}}
.rsv-comparison-wrap::after {{
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--teal);
  border-radius: 2px 2px 0 0;
  transform: scaleX(0);
  transition: transform 0.25s cubic-bezier(0.23, 1, 0.32, 1);
}}
.rsv-comparison-wrap.active::after {{
  transform: scaleX(1);
}}

/* Portfolio Comparison nav button (right-aligned, teal pill) */
.rsv-comparison-btn {{
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  color: var(--white);
  background: var(--teal);
  border: 1px solid var(--teal);
  border-radius: 999px;
  cursor: pointer;
  padding: 6px 16px;
  outline: none;
  transition: background 0.15s cubic-bezier(0.23, 1, 0.32, 1), border-color 0.15s, box-shadow 0.15s;
  white-space: nowrap;
}}
.rsv-comparison-btn:hover {{
  background: var(--teal-dark);
  border-color: var(--teal-dark);
}}
.rsv-comparison-btn:active {{
  transform: scale(0.97);
}}
.rsv-comparison-btn.active {{
  background: var(--teal-dark);
  border-color: var(--teal-dark);
  box-shadow: 0 0 0 3px rgba(20, 207, 166, 0.2);
}}

/* ── Results Table ── */
.rsv-results-table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
  font-size: 13px;
}}
.rsv-results-table th {{
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  padding: 8px 10px;
  border-bottom: 2px solid var(--navy);
}}
.rsv-results-table td {{
  padding: 8px 10px;
  border-bottom: 1px solid var(--section-gray);
}}
.rsv-results-table .positive {{
  color: var(--accent-green);
  font-weight: 700;
}}
.rsv-results-table .negative {{
  color: var(--danger);
  font-weight: 700;
}}
.rsv-results-table tbody tr:nth-child(even) td {{
  background: #f9fafb;
}}
.rsv-results-table tbody tr:hover td {{
  background: #eef1f6;
}}
.rsv-results-table.rsv-matrix th,
.rsv-results-table.rsv-matrix td {{
  text-align: center;
}}
.rsv-results-table.rsv-matrix td:first-child {{
  text-align: left;
}}

/* ── Disclosures ── */
.rsv-disclosures {{
  margin-top: 32px;
}}
.rsv-disclosures-toggle {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  border: none;
  background: none;
  font-family: inherit;
  width: 100%;
  text-align: left;
  border-top: 1px solid var(--border-gray);
}}
.rsv-disclosures-toggle:hover {{
  color: var(--text-primary);
}}
.rsv-disclosures-toggle:active {{
  opacity: 0.85;
}}
.rsv-disclosures-toggle .rsv-arrow {{
  display: inline-block;
  transition: transform 0.2s;
  font-size: 10px;
  /* DM Sans lacks U+25B6 (the triangle glyph); force a font that has it so it
     never renders as a '?'. Class is namespaced (rsv-arrow, not the generic
     .arrow) to avoid colliding with Divi's own .arrow class. */
  font-family: Arial, "Segoe UI Symbol", "Apple Symbols", sans-serif;
  font-style: normal;
}}
.rsv-disclosures-toggle.open .rsv-arrow {{
  transform: rotate(90deg);
}}
.rsv-disclosures-content {{
  display: none;
  padding: 16px 0;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.6;
}}
.rsv-disclosures-content.open {{
  display: block;
}}
.rsv-disclosures-content h3 {{
  font-size: 13px;
  font-weight: 700;
  color: var(--navy);
  margin: 16px 0 8px 0;
}}
.rsv-disclosures-content h3:first-child {{
  margin-top: 0;
}}
.rsv-disclosures-content p {{
  margin-bottom: 10px;
}}

/* ── Two-Column Layout ── */
.rsv-two-col {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}}

/* ── Three-Column Layout (inputs + alloc bar) ── */
.rsv-three-col {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 280px;
  gap: 24px 36px;
}}
.rsv-alloc-bar-wrap {{
  display: flex;
  flex-direction: column;
}}
.rsv-alloc-vis {{
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: stretch;
  min-height: 200px;
}}
.rsv-alloc-bar-outer {{
  width: 100px;
  height: 100%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}}
.rsv-alloc-bar-top {{
  height: 20px;
  position: relative;
  flex-shrink: 0;
  padding-left: 40px;
}}
.rsv-alloc-bar-body {{
  flex: 1;
  position: relative;
  padding-left: 40px;
}}
.rsv-alloc-bar {{
  width: 60px;
  height: 100%;
  display: flex;
  flex-direction: column-reverse;
  border-radius: 8px;
  overflow: hidden;
}}
.rsv-alloc-100-line {{
  position: absolute;
  left: 36px;
  right: -4px;
  border-top: 2px dashed var(--border-gray);
  z-index: 2;
  pointer-events: none;
}}
.rsv-alloc-pct-label {{
  font-size: 10px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
  position: absolute;
  left: 0;
}}
.rsv-alloc-segment {{
  transition: flex 0.25s ease;
  min-height: 0;
}}
.rsv-alloc-labels {{
  display: flex;
  flex-direction: column-reverse;
  justify-content: flex-start;
  flex: 1;
  height: 100%;
  gap: 0;
}}
.rsv-alloc-label {{
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-primary);
  line-height: 1.2;
  transition: flex 0.25s ease;
  min-height: 0;
  overflow: hidden;
}}
.rsv-alloc-label-dot {{
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}}
.rsv-alloc-label-text {{
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.rsv-alloc-label-pct {{
  font-weight: 700;
  margin-left: auto;
  flex-shrink: 0;
}}
.rsv-alloc-empty {{
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  padding: 12px;
}}

/* ── Fade-In Animation ── */
@keyframes rsv-fade-in {{
  from {{
    opacity: 0;
    transform: translateY(6px);
  }}
  to {{
    opacity: 1;
    transform: translateY(0);
  }}
}}
.rsv-animate-in {{
  animation: rsv-fade-in 0.35s cubic-bezier(0.23, 1, 0.32, 1) both;
}}

/* ── Responsive ── */
@media (max-width: 768px) {{
  .rsv-widget {{
    --card-pad: 10px;
    font-size: 13px;
  }}
  .rsv-header {{
    padding: 16px 20px;
  }}
  .rsv-header h1 {{
    font-size: 18px;
  }}
  .rsv-tabs {{
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }}
  .rsv-tab {{
    padding: 8px 12px;
    font-size: 12px;
    white-space: nowrap;
  }}
  .rsv-panel {{
    padding: 16px;
  }}
  .rsv-two-col, .rsv-three-col {{
    grid-template-columns: 1fr;
  }}
  .rsv-summary-bar {{
    gap: 16px;
  }}
  .rsv-alloc-table input[type="number"] {{
    width: 60px;
  }}
}}

/* ── Focus-Visible Accessibility ── */
.rsv-compute-btn:focus-visible,
.rsv-add-btn:focus-visible,
.rsv-date-btn:focus-visible,
.rsv-date-quick-btns button:focus-visible,
.rsv-tab:focus-visible,
.rsv-chart-tab:focus-visible,
.rsv-disclosures-toggle:focus-visible,
.rsv-saved-row button:focus-visible,
.rsv-remove-btn:focus-visible {{
  outline: 2px solid var(--teal);
  outline-offset: 2px;
}}
.rsv-alloc-table select:focus-visible,
.rsv-alloc-table input[type="number"]:focus-visible,
.rsv-fee-row input:focus-visible,
.rsv-date-range-bar select:focus-visible,
.rsv-date-range-bar input[type="date"]:focus-visible,
.rsv-saved-row select:focus-visible {{
  outline: 2px solid var(--teal);
  outline-offset: 1px;
}}

/* ── Reduced Motion ── */
@media (prefers-reduced-motion: reduce) {{
  .rsv-widget *,
  .rsv-widget *::before,
  .rsv-widget *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }}
}}

/* ── Intake Gate ── */
.rsv-intake-overlay {{
  position: fixed;
  inset: 0;
  background: rgba(23, 44, 58, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}}
.rsv-intake-overlay.hidden {{
  display: none;
}}
.rsv-intake-card {{
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 40px;
  max-width: 440px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}}
.rsv-intake-card h2 {{
  color: var(--navy);
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 6px;
}}
.rsv-intake-card > p {{
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 24px;
}}
.rsv-intake-field {{
  margin-bottom: 14px;
}}
.rsv-intake-field label {{
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}
.rsv-intake-field input,
.rsv-intake-field select {{
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid #ddd;
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-family: 'DM Sans', sans-serif;
  color: var(--text-primary);
  transition: border-color 0.15s;
  box-sizing: border-box;
}}
.rsv-intake-field input:focus,
.rsv-intake-field select:focus {{
  outline: none;
  border-color: var(--teal);
}}
.rsv-intake-name-row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}}
.rsv-intake-submit {{
  width: 100%;
  padding: 12px;
  background: var(--teal);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 600;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  margin-top: 8px;
  transition: opacity 0.15s, transform 0.1s;
}}
.rsv-intake-submit:hover {{ opacity: 0.88; }}
.rsv-intake-submit:active {{ transform: scale(0.98); }}

/* ── User Info Bar (header) ── */
.rsv-user-info {{
  background: rgba(255,255,255,0.12);
  border-radius: var(--radius-sm);
  padding: 5px 14px;
  font-size: 0.8rem;
  color: rgba(255,255,255,0.85);
  display: none;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}}
.rsv-not-you-btn {{
  background: none;
  border: none;
  color: var(--teal);
  font-size: 0.8rem;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}}

/* ── Consultant CTA Strip ── */
.rsv-cta-strip {{
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 24px;
  background: linear-gradient(120deg, var(--navy) 0%, #2a4a6e 100%);
  border-radius: var(--radius-md);
  padding: 14px 24px;
  margin-top: 12px;
  margin-bottom: 12px;
}}
.rsv-cta-strip-text strong {{
  display: block;
  font-size: 1rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}}
.rsv-cta-strip-text span {{
  font-size: 0.875rem;
  color: rgba(255,255,255,0.7);
}}
.rsv-cta-strip-btn {{
  background: var(--teal);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  padding: 11px 28px;
  font-size: 0.9375rem;
  font-weight: 600;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.15s, transform 0.1s;
}}
.rsv-cta-strip-btn:hover {{ opacity: 0.88; }}
.rsv-cta-strip-btn:active {{ transform: scale(0.97); }}

/* ── Consultant Modal ── */
.rsv-modal-overlay {{
  position: fixed;
  inset: 0;
  background: rgba(23, 44, 58, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9998;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
  backdrop-filter: blur(3px);
}}
.rsv-modal-overlay.active {{
  opacity: 1;
  pointer-events: all;
}}
.rsv-modal-card {{
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 36px;
  max-width: 460px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.28);
  position: relative;
  max-height: 90vh;
  overflow-y: auto;
}}
.rsv-modal-close {{
  position: absolute;
  top: 14px;
  right: 16px;
  background: none;
  border: none;
  font-size: 1.375rem;
  cursor: pointer;
  color: var(--text-secondary);
  line-height: 1;
  padding: 2px 6px;
}}
.rsv-modal-close:hover {{ color: var(--navy); }}
.rsv-modal-step {{ display: none; }}
.rsv-modal-step.active {{ display: block; }}
.rsv-modal-step h3 {{
  color: var(--navy);
  font-size: 1.125rem;
  font-weight: 700;
  margin-bottom: 6px;
}}
.rsv-modal-step > p {{
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 20px;
}}
.rsv-modal-field {{
  margin-bottom: 14px;
}}
.rsv-modal-field label {{
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}}
.rsv-modal-field select {{
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid #ddd;
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-family: 'DM Sans', sans-serif;
  color: var(--text-primary);
  box-sizing: border-box;
  transition: border-color 0.15s;
}}
.rsv-modal-field select:focus {{
  outline: none;
  border-color: var(--teal);
}}
.rsv-modal-find-btn {{
  width: 100%;
  padding: 12px;
  background: var(--navy);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 600;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  margin-top: 4px;
  transition: opacity 0.15s, transform 0.1s;
}}
.rsv-modal-find-btn:hover {{ opacity: 0.88; }}
.rsv-modal-find-btn:active {{ transform: scale(0.98); }}
.rsv-consultant-result {{
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--section-gray);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}}
.rsv-consultant-photo {{
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}}
.rsv-consultant-info strong {{
  display: block;
  color: var(--navy);
  font-weight: 700;
  font-size: 0.9375rem;
  margin-bottom: 2px;
}}
.rsv-consultant-info a {{
  font-size: 0.8125rem;
  color: var(--blue);
}}
.rsv-portfolio-summary {{
  border: 1.5px solid #e4e6e9;
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 18px;
  font-size: 0.875rem;
  color: var(--text-primary);
  line-height: 1.6;
}}
.rsv-portfolio-summary .portfolio-label {{
  font-weight: 700;
  color: var(--navy);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}}
.rsv-book-btn {{
  width: 100%;
  padding: 12px;
  background: var(--teal);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 600;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}}
.rsv-book-btn:hover {{ opacity: 0.9; }}
.rsv-book-btn:active {{ transform: scale(0.98); }}
</style>
</head>
<body>
<div class="rsv-widget" id="rsv-app">

  <!-- Header -->
  <div class="rsv-header" style="display:flex;align-items:center;justify-content:space-between;gap:16px;">
    <div>
      <h1>Return Stacked&reg; Advanced Visualizer</h1>
      <p>Build and analyze up to 5 portfolios with return stacking overlays</p>
    </div>
    <div id="rsv-user-info" class="rsv-user-info">
      <span id="rsv-user-info-text"></span>
      <button class="rsv-not-you-btn" id="rsv-not-you">Not you?</button>
    </div>
    <img src="{logo_white_uri}" alt="Return Stacked" style="height:40px;opacity:0.9;flex-shrink:0;">
  </div>

  <!-- Intake Gate Overlay -->
  <div class="rsv-intake-overlay" id="rsv-intake-overlay">
    <div class="rsv-intake-card">
      <h2>Welcome to the Return Stacked&reg; Advanced Visualizer</h2>
      <p>Tell us a bit about yourself to get started.</p>
      <div class="rsv-intake-name-row">
        <div class="rsv-intake-field">
          <label>First Name</label>
          <input type="text" id="rsv-intake-first" placeholder="Jane">
        </div>
        <div class="rsv-intake-field">
          <label>Last Name</label>
          <input type="text" id="rsv-intake-last" placeholder="Smith">
        </div>
      </div>
      <div class="rsv-intake-field">
        <label>Email Address</label>
        <input type="email" id="rsv-intake-email" placeholder="jane@example.com">
      </div>
      <div class="rsv-intake-field">
        <label>I am a...</label>
        <select id="rsv-intake-type">
          <option value="" disabled selected>Select your investor type</option>
          <option>Financial Advisor</option>
          <option>Single Family Office</option>
          <option>Institution</option>
          <option>OCIO</option>
          <option>Consultant</option>
          <option>Asset Manager</option>
          <option>Individual Investor</option>
          <option>Other</option>
        </select>
      </div>
      <button class="rsv-intake-submit" id="rsv-intake-submit">Get Started</button>
    </div>
  </div>

  <!-- Consultant Modal -->
  <div class="rsv-modal-overlay" id="rsv-consultant-modal">
    <div class="rsv-modal-card">
      <button class="rsv-modal-close" id="rsv-consultant-close">&times;</button>

      <!-- Step 1: AUM + State -->
      <div class="rsv-modal-step active" id="rsv-consultant-step1">
        <h3>Discuss Your Stack with a Consultant</h3>
        <p>We'll match you with the right person based on your region and AUM.</p>
        <div class="rsv-modal-field">
          <label>Assets Under Management</label>
          <select id="rsv-aum-select">
            <option value="" disabled selected>Select AUM range</option>
            <option>Under $5M</option>
            <option>$5M &ndash; $25M</option>
            <option>$25M &ndash; $50M</option>
            <option>$50M &ndash; $100M</option>
            <option>$100M &ndash; $500M</option>
            <option>$500M &ndash; $1B</option>
            <option>$1B &ndash; $3B</option>
            <option>$3B &ndash; $5B</option>
            <option>$5B+</option>
          </select>
        </div>
        <div class="rsv-modal-field">
          <label>State / Region</label>
          <select id="rsv-state-select">
            <option value="" disabled selected>Select your state</option>
            <option>Alabama</option>
            <option>Alaska</option>
            <option>Arizona</option>
            <option>Arkansas</option>
            <option>California</option>
            <option>Colorado</option>
            <option>Connecticut</option>
            <option>Delaware</option>
            <option>District of Columbia</option>
            <option>Florida</option>
            <option>Georgia</option>
            <option>Hawaii</option>
            <option>Idaho</option>
            <option>Illinois</option>
            <option>Indiana</option>
            <option>Iowa</option>
            <option>Kansas</option>
            <option>Kentucky</option>
            <option>Louisiana</option>
            <option>Maine</option>
            <option>Maryland</option>
            <option>Massachusetts</option>
            <option>Michigan</option>
            <option>Minnesota</option>
            <option>Mississippi</option>
            <option>Missouri</option>
            <option>Montana</option>
            <option>Nebraska</option>
            <option>Nevada</option>
            <option>New Hampshire</option>
            <option>New Jersey</option>
            <option>New Mexico</option>
            <option>New York</option>
            <option>North Carolina</option>
            <option>North Dakota</option>
            <option>Ohio</option>
            <option>Oklahoma</option>
            <option>Oregon</option>
            <option>Pennsylvania</option>
            <option>Rhode Island</option>
            <option>South Carolina</option>
            <option>South Dakota</option>
            <option>Tennessee</option>
            <option>Texas</option>
            <option>Utah</option>
            <option>Vermont</option>
            <option>Virginia</option>
            <option>Washington</option>
            <option>West Virginia</option>
            <option>Wisconsin</option>
            <option>Wyoming</option>
            <option>International / Ex-US</option>
          </select>
        </div>
        <button class="rsv-modal-find-btn" id="rsv-consultant-find">Find My Consultant</button>
      </div>

      <!-- Step 2: Result + Booking -->
      <div class="rsv-modal-step" id="rsv-consultant-step2">
        <h3>Your Dedicated Consultant</h3>
        <p>Based on your region, we've matched you with:</p>
        <div class="rsv-consultant-result">
          <img class="rsv-consultant-photo" id="rsv-consultant-photo" src="" alt="">
          <div class="rsv-consultant-info">
            <strong id="rsv-consultant-name"></strong>
            <a id="rsv-consultant-email" href=""></a>
          </div>
        </div>
        <div class="rsv-portfolio-summary" id="rsv-portfolio-summary"></div>
        <button class="rsv-book-btn" id="rsv-consultant-book">Schedule a Meeting</button>
      </div>
    </div>
  </div>

  <!-- Portfolio Tabs -->
  <div class="rsv-tabs" id="rsv-tabs">
    <!-- Generated by JS -->
  </div>

  <!-- Portfolio Panels (one per portfolio) -->
  <div id="rsv-panels">
    <!-- Generated by JS -->
  </div>

  <!-- Disclosures -->
  <div class="rsv-disclosures">
    <button class="rsv-disclosures-toggle" onclick="RSV.toggleDisclosures(this)">
      <span class="rsv-arrow">&#9654;</span> Important Disclosures &amp; Index Definitions
    </button>
    {disclosures_html}
  </div>

</div>

<script>
// ── Embedded Data ──
const INDEX_DATA = {indices_data};
const INDEX_MAP = {index_map_data};
const CUSTOM_ASSETS = {custom_assets_data};
const TICKER_INFO = {ticker_info_data};

// ── PDF Assets ──
const PDF_LOGO_WHITE = "{logo_icon_white_uri}";
const PDF_LOGO_BLACK = "{logo_ps_black_uri}";
const PDF_BG_IMAGE = "{bg_image_uri}";
const PDF_FONT_REGULAR = "{dm_regular_b64}";
const PDF_FONT_BOLD = "{dm_bold_b64}";
const PDF_FONT_ITALIC = "{dm_italic_b64}";
const PDF_FONT_BOLDITALIC = "{dm_bolditalic_b64}";
const PDF_DISCLOSURES = {json.dumps(disclosures)};

// ── Asset Categories ──
const ASSET_CATEGORIES = {{}};
INDEX_MAP.forEach(a => {{
  // Skip legacy Custom Asset # entries -- custom assets are added via CSV upload
  if (a.shortName.startsWith("Custom Asset #")) return;
  const cat = a.assetClass;
  if (!ASSET_CATEGORIES[cat]) ASSET_CATEGORIES[cat] = [];
  ASSET_CATEGORIES[cat].push(a);
}});

// Category display order
const CATEGORY_ORDER = ["Equity", "Fixed Income", "Real Assets", "Alternative", "Cash", "Custom"];

// ── Chart Colors (brand) ──
const CHART_COLORS = [
  "#323A46", "#14CFA6", "#3A6A9C", "#7DA5CE", "#FFE885", "#EBE96A",
  "#0A0A0B", "#0C7C64", "#23405E", "#366390", "#3BB823", "#B4B218"
];

// ── State ──
const NUM_PORTFOLIOS = 5;

// ── Default embedded fees / financing for overlay (stack) asset classes ──
// feeBp        = annual management fee, basis points. Only economically meaningful
//                where the index is NOT already net of fees (see NET_OF_FEES_ASSETS);
//                for net-of-fees assets it is left at 0 and the fee field shows N/A.
// financingBp  = annual financing spread above the T-Bill rate, basis points. The
//                base T-Bill deduction is automatic; this is the additional spread.
// Applied automatically when a stack asset is selected (updateAsset) and baked into
// the preset portfolios below.
const STACK_FEE_DEFAULTS = {{
  "Managed Futures CTA":        {{ feeBp: 0,  financingBp: 50 }},
  "Managed Futures Trend":      {{ feeBp: 0,  financingBp: 50 }},
  "Futures Yield (Carry)":      {{ feeBp: 0,  financingBp: 50 }},
  "Systematic Global Macro":    {{ feeBp: 0,  financingBp: 50 }},
  "Merger Arbitrage":           {{ feeBp: 0,  financingBp: 50 }},
  "Merger Arbitrage (AB)":      {{ feeBp: 95, financingBp: 50 }},
  "Risk-Weighted Gold/Bitcoin": {{ feeBp: 50, financingBp: 50 }},
  "Gold":                       {{ feeBp: 40, financingBp: 50 }},
}};
function getStackFeeDefaults(asset) {{
  return STACK_FEE_DEFAULTS[asset] || {{ feeBp: 0, financingBp: 0 }};
}}

const PRESET_PORTFOLIOS = [
  {{
    name: "Global Balanced",
    core: [
      {{ asset: "Global Equities", weight: 60 }},
      {{ asset: "U.S. Core Fixed Income", weight: 40 }},
    ],
    stack: [],
  }},
  {{
    name: "Global Balanced + 20% Diversified Stack",
    core: [
      {{ asset: "Global Equities", weight: 60 }},
      {{ asset: "U.S. Core Fixed Income", weight: 40 }},
    ],
    stack: [
      {{ asset: "Managed Futures CTA", weight: 5 }},
      {{ asset: "Futures Yield (Carry)", weight: 5 }},
      {{ asset: "Gold", weight: 5 }},
      {{ asset: "Merger Arbitrage", weight: 5 }},
    ],
  }},
  {{
    name: "Global Balanced + 40% Diversified Stack",
    core: [
      {{ asset: "Global Equities", weight: 60 }},
      {{ asset: "U.S. Core Fixed Income", weight: 40 }},
    ],
    stack: [
      {{ asset: "Managed Futures CTA", weight: 10 }},
      {{ asset: "Futures Yield (Carry)", weight: 10 }},
      {{ asset: "Gold", weight: 10 }},
      {{ asset: "Merger Arbitrage", weight: 10 }},
    ],
  }},
  {{
    name: "U.S. Equities & Trend",
    core: [{{ asset: "U.S. Large Cap Equities", weight: 100 }}],
    stack: [{{ asset: "Managed Futures Trend", weight: 100 }}],
  }},
  {{
    name: "U.S. Equities & Futures Yield",
    core: [{{ asset: "U.S. Large Cap Equities", weight: 100 }}],
    stack: [{{ asset: "Futures Yield (Carry)", weight: 100 }}],
  }},
  {{
    name: "U.S. Equities & Gold/Bitcoin",
    core: [{{ asset: "U.S. Large Cap Equities", weight: 100 }}],
    stack: [{{ asset: "Risk-Weighted Gold/Bitcoin", weight: 100 }}],
  }},
  {{
    name: "Intl Equities & Trend",
    core: [{{ asset: "International Equities", weight: 100 }}],
    stack: [{{ asset: "Managed Futures Trend", weight: 100 }}],
  }},
  {{
    name: "Bonds & Merger Arbitrage",
    core: [{{ asset: "U.S. Treasury Ladder", weight: 100 }}],
    stack: [{{ asset: "Merger Arbitrage (AB)", weight: 100 }}],
  }},
  {{
    name: "Bonds & Trend",
    core: [
      {{ asset: "U.S. Core Fixed Income", weight: 50 }},
      {{ asset: "U.S. Treasury Ladder", weight: 50 }},
    ],
    stack: [{{ asset: "Managed Futures Trend", weight: 100 }}],
  }},
  {{
    name: "Bonds & Futures Yield",
    core: [
      {{ asset: "U.S. Core Fixed Income", weight: 50 }},
      {{ asset: "U.S. Treasury Ladder", weight: 50 }},
    ],
    stack: [{{ asset: "Futures Yield (Carry)", weight: 100 }}],
  }},
  {{
    name: "Global Equities & Bonds",
    core: [{{ asset: "Global Equities", weight: 100 }}],
    stack: [{{ asset: "U.S. Treasury Ladder", weight: 100 }}],
  }},
];

// Bake the embedded fee/financing defaults into every preset stack row so the
// showcase portfolios reflect realistic net-of-cost returns.
PRESET_PORTFOLIOS.forEach(p => {{
  (p.stack || []).forEach(r => {{
    if (!r.asset) return;
    const d = getStackFeeDefaults(r.asset);
    if (r.feeBp == null) r.feeBp = d.feeBp;
    if (r.financingBp == null) r.financingBp = d.financingBp;
  }});
}});

// ── Saved Portfolios (localStorage) ──
const SAVED_PORTFOLIOS_KEY = "rsv_saved_portfolios";
function getSavedPortfolios() {{
  try {{ return JSON.parse(localStorage.getItem(SAVED_PORTFOLIOS_KEY)) || []; }}
  catch(e) {{ return []; }}
}}
function setSavedPortfolios(arr) {{
  localStorage.setItem(SAVED_PORTFOLIOS_KEY, JSON.stringify(arr));
}}

// ── Saved Comparisons (localStorage) ──
// A saved comparison stores per-slot {{ enabled, portfolioName }} entries; on load it
// looks up each portfolioName in the Saved Portfolios list and re-hydrates that slot.
const SAVED_COMPARISONS_KEY = "rsv_saved_comparisons";
function getSavedComparisons() {{
  try {{ return JSON.parse(localStorage.getItem(SAVED_COMPARISONS_KEY)) || []; }}
  catch(e) {{ return []; }}
}}
function setSavedComparisons(arr) {{
  localStorage.setItem(SAVED_COMPARISONS_KEY, JSON.stringify(arr));
}}

// Alternative assets that are already net of fees (fee field greyed out)
const NET_OF_FEES_ASSETS = new Set();
INDEX_MAP.forEach(a => {{
  if (a.assetClass === "Alternative" &&
      !["Risk Parity (10%)", "Risk Parity (12%)", "Risk Parity (15%)",
        "Global Stock / Bond Momentum", "Risk-Weighted Gold/Bitcoin",
        "Merger Arbitrage (AB)"].includes(a.shortName)) {{
    NET_OF_FEES_ASSETS.add(a.shortName);
  }}
}});

function createEmptyPortfolio(idx) {{
  return {{
    enabled: idx === 0,
    name: `Portfolio ${{idx + 1}}`,
    core: [{{ asset: "", weight: 0 }}],
    stack: [{{ asset: "", weight: 0, feeBp: 0, financingBp: 0 }}],
    fee: 0,
    result: null,
    dateRange: null,
  }};
}}

const state = {{
  portfolios: Array.from({{ length: NUM_PORTFOLIOS }}, (_, i) => createEmptyPortfolio(i)),
  activeTab: 0,
  comparisonDateRange: null,
}};

// ── Helpers ──

function getAssetData(shortName) {{
  // Look up the bloomberg name from index map
  const mapping = INDEX_MAP.find(a => a.shortName === shortName);
  if (!mapping) return null;
  const bbgName = mapping.bloombergName;
  const seriesInfo = INDEX_DATA.series[bbgName];
  if (!seriesInfo) return null;
  return {{
    dates: INDEX_DATA.dates,
    startIndex: seriesInfo.start,
    values: seriesInfo.values,
    startDate: mapping.startDate,
    assetClass: mapping.assetClass,
  }};
}}

function getMonthlyReturns(shortName) {{
  const data = getAssetData(shortName);
  if (!data) return null;
  const returns = [];
  const dates = [];
  for (let i = 1; i < data.values.length; i++) {{
    const prev = data.values[i - 1];
    const curr = data.values[i];
    if (prev != null && curr != null && prev !== 0) {{
      returns.push(curr / prev - 1);
      dates.push(data.dates[data.startIndex + i]);
    }} else {{
      returns.push(null);
      dates.push(data.dates[data.startIndex + i]);
    }}
  }}
  return {{ returns, dates, startDate: data.dates[data.startIndex] }};
}}

function findCommonDateRange(assetNames) {{
  // Find the latest start date and earliest end date across all assets
  let latestStart = null;
  let earliestEnd = null;
  for (const name of assetNames) {{
    const data = getAssetData(name);
    if (!data) return {{ start: null, end: null }};
    const startDate = data.dates[data.startIndex];
    const endIdx = data.startIndex + data.values.length - 1;
    const endDate = data.dates[endIdx];
    if (!latestStart || startDate > latestStart) latestStart = startDate;
    if (!earliestEnd || endDate < earliestEnd) earliestEnd = endDate;
  }}
  return {{ start: latestStart, end: earliestEnd }};
}}

// ── Stats Engine ──

// Unified stats computation. All callers use this single function.
// returns: array of monthly returns
// dates: array of date strings (dates[0] = period start, returns[i] corresponds to dates[i+1])
// rangeStart/rangeEnd: optional date strings to filter to a sub-range
function computeStats(returns, dates, rangeStart, rangeEnd, excessMode) {{
  // Filter to range if provided
  let arr, filteredDates;
  if (rangeStart && rangeEnd) {{
    arr = [];
    filteredDates = [rangeStart];
    for (let m = 0; m < returns.length; m++) {{
      const date = dates[m + 1];
      if (date && date > rangeStart && date <= rangeEnd) {{
        arr.push(returns[m]);
        filteredDates.push(date);
      }}
    }}
  }} else {{
    arr = returns;
    filteredDates = dates;
  }}

  if (arr.length < 2) return null;

  const n = arr.length;
  const cumReturn = arr.reduce((p, r) => p * (1 + r), 1);
  const years = n / 12;
  const annReturn = Math.pow(cumReturn, 1 / years) - 1;
  const mean = arr.reduce((s, r) => s + r, 0) / n;
  const variance = arr.reduce((s, r) => s + Math.pow(r - mean, 2), 0) / (n - 1);
  const vol = Math.sqrt(variance) * Math.sqrt(12);
  const std = Math.sqrt(variance);

  // Max drawdown and average drawdown
  let peak = 1, maxDD = 0, g = 1;
  let ddSum = 0, ddCount = 0;
  const drawdowns = [];
  for (const r of arr) {{
    g *= (1 + r);
    if (g > peak) peak = g;
    const dd = (peak - g) / peak;
    if (dd > maxDD) maxDD = dd;
    drawdowns.push(dd);
    if (dd > 0) {{ ddSum += dd; ddCount++; }}
  }}
  const avgDrawdown = ddCount > 0 ? ddSum / ddCount : 0;

  // Risk-free rate from Treasury Bill data.
  // Skip in excess-return mode (zero core + stack only): the stacked series is
  // already net of T-bill financing, so it is an excess return over cash and a
  // second risk-free deduction in Sharpe would double-count.
  let rfAnn = 0;
  const tbInfo = INDEX_DATA.series["Treasury Bill"];
  if (!excessMode && tbInfo) {{
    // Determine the actual date range used
    const rfStart = filteredDates[0];
    const rfEnd = filteredDates[filteredDates.length - 1];
    const gDates = INDEX_DATA.dates;
    const si = gDates.indexOf(rfStart);
    const ei = gDates.indexOf(rfEnd);
    if (si >= 0 && ei >= 0) {{
      let cSum = 0, cCount = 0;
      for (let i = si + 1; i <= ei; i++) {{
        const di = i - tbInfo.start;
        if (di > 0 && di < tbInfo.values.length && tbInfo.values[di - 1]) {{
          cSum += tbInfo.values[di] / tbInfo.values[di - 1] - 1;
          cCount++;
        }}
      }}
      if (cCount > 0) rfAnn = (cSum / cCount) * 12;
    }}
  }}

  const sharpe = vol > 0 ? (annReturn - rfAnn) / vol : 0;

  // Skewness (sample, adjusted) -- requires n >= 3 and std > 0
  const skewness = (n >= 3 && std > 0) ? (n / ((n-1)*(n-2))) * arr.reduce((s, r) => s + Math.pow((r - mean) / std, 3), 0) : 0;

  // Kurtosis (excess, sample adjusted) -- requires n >= 4 and std > 0
  const kurtosis = (n > 3 && std > 0) ? ((n*(n+1)) / ((n-1)*(n-2)*(n-3))) * arr.reduce((s, r) => s + Math.pow((r - mean) / std, 4), 0) - (3*(n-1)*(n-1)) / ((n-2)*(n-3)) : 0;

  // Sortino ratio (downside deviation, target = 0)
  const downsideSq = arr.map(r => r < 0 ? r * r : 0);
  const downsideDev = Math.sqrt(downsideSq.reduce((s, v) => s + v, 0) / n) * Math.sqrt(12);
  const sortino = downsideDev > 0 ? annReturn / downsideDev : 0;

  // Calmar ratio
  const calmar = maxDD > 0 ? annReturn / maxDD : 0;

  // Tail ratio (95th percentile / 5th percentile, absolute)
  const sorted = [...arr].sort((a, b) => a - b);
  const p5 = sorted[Math.floor(n * 0.05)];
  const p95 = sorted[Math.floor(n * 0.95)];
  const tailRatio = p5 !== 0 ? Math.abs(p95 / p5) : 0;

  // 1-Year 95% VaR (parametric)
  const var95 = mean * 12 - 1.645 * vol;

  // 1-Year 95% CVaR (parametric)
  const cvar95 = mean * 12 - (2.063 * vol);

  // Best/worst month
  const bestMonth = Math.max(...arr);
  const worstMonth = Math.min(...arr);

  // Calendar year returns
  const calYearReturns = {{}};
  if (filteredDates && filteredDates.length > 1) {{
    for (let m = 0; m < arr.length; m++) {{
      const yr = parseInt(filteredDates[m + 1].substring(0, 4));
      if (!calYearReturns[yr]) calYearReturns[yr] = 1;
      calYearReturns[yr] *= (1 + arr[m]);
    }}
  }}
  let bestYear = -Infinity, worstYear = Infinity;
  for (const yr in calYearReturns) {{
    const ret = calYearReturns[yr] - 1;
    if (ret > bestYear) bestYear = ret;
    if (ret < worstYear) worstYear = ret;
  }}

  // Rolling 12-month returns
  let bestRolling12 = -Infinity, worstRolling12 = Infinity;
  for (let i = 0; i <= arr.length - 12; i++) {{
    let rolling = 1;
    for (let j = i; j < i + 12; j++) rolling *= (1 + arr[j]);
    const r12 = rolling - 1;
    if (r12 > bestRolling12) bestRolling12 = r12;
    if (r12 < worstRolling12) worstRolling12 = r12;
  }}

  return {{
    cumulativeReturn: cumReturn - 1,
    annualizedReturn: annReturn,
    volatility: vol,
    maxDrawdown: maxDD,
    avgDrawdown: avgDrawdown,
    sharpe: sharpe,
    skewness: skewness,
    kurtosis: kurtosis,
    sortino: sortino,
    calmar: calmar,
    tailRatio: tailRatio,
    var95: var95,
    cvar95: cvar95,
    bestMonth: bestMonth,
    worstMonth: worstMonth,
    bestCalendarYear: bestYear === -Infinity ? 0 : bestYear,
    worstCalendarYear: worstYear === Infinity ? 0 : worstYear,
    bestRolling12: bestRolling12 === -Infinity ? 0 : bestRolling12,
    worstRolling12: worstRolling12 === Infinity ? 0 : worstRolling12,
    calendarYearReturns: calYearReturns,
  }};
}}

// ── Portfolio Computation ──

function computePortfolio(portfolio) {{
  // Gather all asset names from core and stack
  const coreAssets = portfolio.core.filter(r => r.asset && r.weight > 0);
  const stackAssets = portfolio.stack.filter(r => r.asset && r.weight > 0);

  const hasCore = coreAssets.length > 0;
  const hasStack = stackAssets.length > 0;

  // Must have either a valid core (100%) or stack-only (excess return mode)
  if (!hasCore && !hasStack) return null;

  const coreTotal = coreAssets.reduce((s, r) => s + r.weight, 0);
  const stackTotal = stackAssets.reduce((s, r) => s + r.weight, 0);

  // Validate: core must be 100% if present, or 0% if stack-only
  if (hasCore && Math.abs(coreTotal - 100) > 0.01) return null;
  if (!hasCore && !hasStack) return null;

  // Get all unique asset names
  const allAssets = [...coreAssets, ...stackAssets].map(r => r.asset);
  const allAssetNames = [...new Set(allAssets)];

  // Add Cash for financing cost if we have stack overlays
  if (stackAssets.length > 0 && !allAssetNames.includes("Cash")) {{
    allAssetNames.push("Cash");
  }}

  // Find common date range
  const range = findCommonDateRange(allAssetNames);
  if (!range.start || !range.end) return null;

  // Get monthly returns for each asset aligned to common dates
  const assetReturns = {{}};
  const allDates = INDEX_DATA.dates;
  const startIdx = allDates.indexOf(range.start);
  const endIdx = allDates.indexOf(range.end);
  if (startIdx < 0 || endIdx < 0 || endIdx <= startIdx) return null;

  for (const name of allAssetNames) {{
    const data = getAssetData(name);
    if (!data) {{
      console.warn("Asset data not found: " + name);
      return null;
    }}
    const returns = [];
    for (let i = startIdx + 1; i <= endIdx; i++) {{
      const dataI = i - data.startIndex;
      const dataPrev = dataI - 1;
      if (dataI >= 0 && dataI < data.values.length && dataPrev >= 0 && dataPrev < data.values.length) {{
        const prev = data.values[dataPrev];
        const curr = data.values[dataI];
        if (prev != null && curr != null && prev !== 0) {{
          returns.push(curr / prev - 1);
        }} else {{
          returns.push(0);
        }}
      }} else {{
        returns.push(0);
      }}
    }}
    assetReturns[name] = returns;
  }}

  const numMonths = endIdx - startIdx;
  const dates = allDates.slice(startIdx, endIdx + 1);

  // Compute core portfolio monthly returns
  const coreReturns = new Array(numMonths).fill(0);
  for (const {{ asset, weight }} of coreAssets) {{
    const w = weight / 100;
    const r = assetReturns[asset];
    for (let i = 0; i < numMonths; i++) {{
      coreReturns[i] += w * (r[i] || 0);
    }}
  }}

  // Compute stacked portfolio monthly returns
  // Stacked = core + overlay returns - T-bill financing - per-asset fee - per-asset financing spread
  const stackedReturns = [...coreReturns];
  const cashReturns = assetReturns["Cash"] || new Array(numMonths).fill(0);

  for (const {{ asset, weight, feeBp, financingBp }} of stackAssets) {{
    const w = weight / 100;
    const r = assetReturns[asset];
    const monthlyAssetFee = (feeBp || 0) / 10000 / 12;
    const monthlyFinSpread = (financingBp || 0) / 10000 / 12;
    for (let i = 0; i < numMonths; i++) {{
      // Add overlay return
      stackedReturns[i] += w * (r[i] || 0);
      // Subtract T-bill financing cost (base rate on overlay notional)
      stackedReturns[i] -= w * (cashReturns[i] || 0);
      // Subtract per-asset fee and financing spread
      stackedReturns[i] -= w * (monthlyAssetFee + monthlyFinSpread);
    }}
  }}

  // Deduct portfolio-level advisory fee (input in basis points)
  const monthlyFee = portfolio.fee / 10000 / 12;

  // Build growth series
  const coreGrowth = [1];
  const stackedGrowth = [1];
  for (let i = 0; i < numMonths; i++) {{
    coreGrowth.push(coreGrowth[i] * (1 + coreReturns[i] - monthlyFee));
    stackedGrowth.push(stackedGrowth[i] * (1 + stackedReturns[i] - monthlyFee));
  }}

  // Compute summary statistics using unified stats engine
  const coreStats = computeStats(coreReturns.map((r) => r - monthlyFee), dates);
  const stackedStats = computeStats(stackedReturns.map((r) => r - monthlyFee), dates, undefined, undefined, !hasCore);

  // Tracking error between core and stacked
  const diffReturns = [];
  for (let i = 0; i < numMonths; i++) {{
    diffReturns.push(stackedReturns[i] - coreReturns[i]);
  }}
  const diffMean = diffReturns.reduce((s, r) => s + r, 0) / diffReturns.length;
  const diffVar = diffReturns.reduce((s, r) => s + Math.pow(r - diffMean, 2), 0) / (diffReturns.length - 1);
  const trackingError = Math.sqrt(diffVar) * Math.sqrt(12);

  return {{
    dates,
    coreGrowth,
    stackedGrowth,
    coreReturns,
    stackedReturns,
    coreStats,
    stackedStats,
    trackingError,
    hasCore,
    period: {{ start: dates[0], end: dates[dates.length - 1] }},
  }};
}}

// ── Flexible custom-data intake engine (parsers + interpretation) ──
{intake_engine_js}

// ── UI Rendering ──

const RSV = {{

  _autoComputeTimer: null,
  _advancedFeeOpen: {{}},  // track toggle state per portfolio

  scheduleAutoCompute(portfolioIdx) {{
    clearTimeout(this._autoComputeTimer);
    this._autoComputeTimer = setTimeout(() => {{
      const p = state.portfolios[portfolioIdx];
      const coreTotal = p.core.reduce((s, r) => s + (r.weight || 0), 0);
      const coreAssets = p.core.filter(r => r.asset && r.weight > 0);
      const stackAssets = p.stack.filter(r => r.asset && r.weight > 0);
      // Auto-compute if core is valid (100%) or stack-only (excess return mode)
      const coreValid = coreAssets.length > 0 && Math.abs(coreTotal - 100) < 0.01;
      const stackOnly = coreAssets.length === 0 && stackAssets.length > 0;
      if (coreValid || stackOnly) {{
        this.computeSingle(portfolioIdx);
      }}
    }}, 500);
  }},

  init() {{
    // chartjs-plugin-annotation auto-registers when loaded via script tag.

    // Chart.js global defaults (brand-aligned)
    if (typeof Chart !== "undefined" && Chart.defaults) {{
      Chart.defaults.font.family = "'DM Sans', sans-serif";
      Chart.defaults.font.size = 11;
      Chart.defaults.color = "#555";
      Chart.defaults.elements.line.tension = 0.1;
      Chart.defaults.elements.line.borderWidth = 2.5;
      Chart.defaults.elements.point.radius = 0;
      Chart.defaults.elements.point.hitRadius = 8;
      Chart.defaults.animation.duration = 300;
      Chart.defaults.animation.easing = "easeOutCubic";
      // Solid black axis lines
      if (Chart.defaults.scale) {{
        if (Chart.defaults.scale.border) {{
          Chart.defaults.scale.border.color = "#000";
          Chart.defaults.scale.border.width = 1.5;
        }}
        if (Chart.defaults.scale.grid) {{
          Chart.defaults.scale.grid.color = "#f0f0f0";
        }}
      }}
      // Tooltip
      Chart.defaults.plugins.tooltip.backgroundColor = "rgba(42,63,91,0.95)";
      Chart.defaults.plugins.tooltip.titleFont = {{ family: "'DM Sans', sans-serif", size: 13, weight: "600" }};
      Chart.defaults.plugins.tooltip.bodyFont = {{ family: "'DM Sans', sans-serif", size: 13 }};
      Chart.defaults.plugins.tooltip.padding = 12;
      Chart.defaults.plugins.tooltip.cornerRadius = 8;
      Chart.defaults.plugins.tooltip.mode = "index";
      Chart.defaults.plugins.tooltip.intersect = false;
      // Legend: circle icons with dark ring + dataset-fill interior
      Chart.defaults.plugins.legend.labels.font = {{ family: "'DM Sans', sans-serif", size: 13, weight: "600" }};
      Chart.defaults.plugins.legend.labels.usePointStyle = true;
      Chart.defaults.plugins.legend.labels.pointStyle = "circle";
      Chart.defaults.plugins.legend.labels.padding = 20;
      Chart.defaults.plugins.legend.labels.boxWidth = 10;
      Chart.defaults.plugins.legend.labels.boxHeight = 10;
    }}

    // Auto-compute all preset portfolios on launch
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      try {{
        const p = state.portfolios[i];
        if (p.enabled && p.core.some(r => r.asset && r.weight > 0)) {{
          p.result = computePortfolio(p);
        }}
      }} catch(e) {{ console.error("Init compute error for portfolio " + i, e); }}
    }}
    // ── URL Share Param Restore ──
    try {{
      const _rsp = new URLSearchParams(window.location.search).get('rs_p');
      if (_rsp) {{
        const _s = JSON.parse(atob(_rsp));
        const _p = state.portfolios[0];
        _p.enabled = true;
        _p.result = null;
        if (_s.name) _p.name = _s.name;
        if (_s.fee != null) _p.fee = Number(_s.fee);
        _p.core = (_s.core || []).map(r => ({{ asset: r.asset, weight: Number(r.weight) }}));
        if (!_p.core.length) _p.core = [{{ asset: '', weight: 0 }}];
        _p.stack = (_s.stack || []).map(r => ({{ asset: r.asset, weight: Number(r.weight), feeBp: Number(r.feeBp || 0), financingBp: Number(r.financingBp || 0) }}));
        if (!_p.stack.length) _p.stack = [{{ asset: '', weight: 0, feeBp: 0, financingBp: 0 }}];
        if (_p.core.some(r => r.asset && r.weight > 0)) {{
          try {{ _p.result = computePortfolio(_p); }} catch(_ce) {{}}
        }}
        state.activeTab = 0;
      }}
    }} catch(_e) {{}}
    // ── URL Comparison Share Param Restore ──
    try {{
      const _rsc = new URLSearchParams(window.location.search).get('rs_c');
      if (_rsc) {{
        const _cs = JSON.parse(atob(_rsc));
        if (_cs.portfolios && Array.isArray(_cs.portfolios)) {{
          _cs.portfolios.forEach((sp, i) => {{
            if (i >= NUM_PORTFOLIOS) return;
            const _p = state.portfolios[i];
            _p.enabled = !!sp.enabled;
            _p.result = null;
            if (sp.name) _p.name = sp.name;
            if (sp.fee != null) _p.fee = Number(sp.fee);
            _p.core = (sp.core || []).map(r => ({{ asset: r.asset, weight: Number(r.weight) }}));
            if (!_p.core.length) _p.core = [{{ asset: '', weight: 0 }}];
            _p.stack = (sp.stack || []).map(r => ({{ asset: r.asset, weight: Number(r.weight), feeBp: Number(r.feeBp || 0), financingBp: Number(r.financingBp || 0) }}));
            if (!_p.stack.length) _p.stack = [{{ asset: '', weight: 0, feeBp: 0, financingBp: 0 }}];
            if (_p.enabled && _p.core.some(r => r.asset && r.weight > 0)) {{
              try {{ _p.result = computePortfolio(_p); }} catch(_ce) {{}}
            }}
          }});
          state.activeTab = 'summary';
          this._trackHubSpotBehavioralEvent('pe46343589_viewed_shared_link_comparison___adv_visualizer', {{
            shared_by: _cs.sharedBy || ''
          }});
        }}
      }}
    }} catch(_e) {{}}
    this._initComboGlobalListeners();
    this.renderTabs();
    this.renderPanel(state.activeTab);
    this._initHubSpot();
  }},

  // Called from the Portfolio Name input (live, on every keystroke).
  // Updates state + mirrors the text into the tab label WITHOUT re-rendering,
  // so the input keeps focus while typing.
  updatePortfolioName(portfolioIdx, value) {{
    const name = value.trim() || `Portfolio ${{portfolioIdx + 1}}`;
    state.portfolios[portfolioIdx].name = name;
    const tabName = document.querySelectorAll("#rsv-tabs .rsv-tab-name")[portfolioIdx];
    if (tabName) tabName.textContent = name;
  }},

  // On blur/Enter: refresh the panel so results titles pick up the new name.
  commitPortfolioName(portfolioIdx) {{
    this.renderPanel(portfolioIdx);
  }},

  renderTabs() {{
    const container = document.getElementById("rsv-tabs");
    container.innerHTML = "";
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      const isActive = i === state.activeTab;
      const tab = document.createElement("div");
      tab.className = "rsv-tab" + (isActive ? " active" : "") + (!p.enabled ? " disabled" : "");
      tab.innerHTML = `<span class="rsv-tab-name">${{p.name}}</span> <input type="checkbox" class="rsv-tab-toggle" ${{p.enabled ? "checked" : ""}} title="Enable/disable this portfolio">`;

      // Checkbox toggle
      tab.querySelector(".rsv-tab-toggle").addEventListener("change", (e) => {{
        e.stopPropagation();
        state.portfolios[i].enabled = e.target.checked;
        if (e.target.checked) {{
          // Enabling a portfolio: jump straight to its tab so the user can edit it.
          state.activeTab = i;
          this.renderTabs();
          this.renderPanel(i);
        }} else {{
          this.renderTabs();
          if (i === state.activeTab) {{
            const first = state.portfolios.findIndex(p => p.enabled);
            if (first >= 0) {{
              state.activeTab = first;
              this.renderTabs();
              this.renderPanel(first);
            }}
          }}
        }}
      }});

      // Click anywhere on the tab (except the checkbox): switch tab
      tab.addEventListener("click", (e) => {{
        if (e.target.classList.contains("rsv-tab-toggle")) return;
        if (!p.enabled) return;
        state.activeTab = i;
        this.renderTabs();
        this.renderPanel(i);
      }});

      container.appendChild(tab);
    }}

    // Global Saved Portfolios picker — sits next to the last portfolio tab
    const savedWrap = document.createElement("div");
    savedWrap.className = "rsv-tab";
    savedWrap.style.padding = "0";
    savedWrap.innerHTML = this.renderSavedDropdownGlobal();
    container.appendChild(savedWrap);

    // Portfolio Comparison button (right-aligned, teal pill). Always navigates to
    // the default "Risk & Return Statistics" sub-tab; sub-tabs inside the panel
    // handle the rest.
    const isComparisonActive = ["summary", "riskDiv"].includes(state.activeTab);
    const compWrap = document.createElement("div");
    compWrap.className = "rsv-comparison-wrap" + (isComparisonActive ? " active" : "");
    compWrap.innerHTML = `<button class="rsv-comparison-btn${{isComparisonActive ? ' active' : ''}}">Portfolio Comparison</button>`;
    compWrap.querySelector("button").addEventListener("click", () => {{
      const wasOnPortfolio = typeof state.activeTab === "number";
      state.activeTab = "summary";
      if (wasOnPortfolio) this.renderTabs();
      this.renderPanel("summary");
    }});
    container.appendChild(compWrap);
  }},

  // Sub-tab nav (with a Saved Comparisons controls box above it) rendered at the
  // top of every comparison panel.
  renderComparisonSubTabs(activeId) {{
    const tabs = [
      {{ id: "summary", label: "Risk & Return Statistics" }},
      {{ id: "riskDiv", label: "Advanced Statistics" }},
    ];
    const _cls = (id) => id === activeId ? "rsv-chart-tab active" : "rsv-chart-tab";
    let h = `<div style="display:flex;justify-content:flex-start;margin-bottom:12px;">
      ${{this.renderComparisonControlsBox()}}
    </div>`;
    h += '<div class="rsv-chart-tabs" style="margin-bottom:16px;">';
    for (const t of tabs) {{
      h += `<button class="${{_cls(t.id)}}" onclick="RSV.switchComparisonPage('${{t.id}}')">${{t.label}}</button>`;
    }}
    h += '</div>';
    return h;
  }},

  // Comparison controls: dropdown + Save/Share/PDF buttons, no container frame.
  renderComparisonControlsBox() {{
    return `<div style="display:flex;align-items:center;gap:8px;">
      ${{this.renderSavedComparisonsDropdown()}}
      <span class="rsv-btn-tooltip">
        <button class="rsv-compute-btn rsv-compute-btn--no-mt" onclick="RSV.saveComparison()">Save Comparison</button>
        <span class="rsv-tooltip-text">Save the current set of enabled portfolios as a named comparison setup.</span>
      </span>
      <span class="rsv-btn-tooltip">
        <button class="rsv-compute-btn rsv-compute-btn--secondary" onclick="RSV.shareComparison(this)">&#x2197; Share Comparison</button>
        <span class="rsv-tooltip-text">Copy a link that pre-loads all portfolios and opens this comparison view for the recipient.</span>
      </span>
      <span class="rsv-btn-tooltip">
        <button class="rsv-compute-btn rsv-compute-btn--secondary" onclick="RSV.exportComparisonPDF()">&#x2193; Comparison PDF</button>
        <span class="rsv-tooltip-text">Export all comparison data (Risk & Return Statistics, Advanced Statistics, Tracking Error) as a PDF.</span>
      </span>
    </div>`;
  }},

  // Boxed-style Saved Comparisons dropdown (default combo trigger styling, no --inline).
  renderSavedComparisonsDropdown() {{
    const saved = getSavedComparisons();
    let html = `<div class="rsv-combo" data-saved-comparisons="1" style="width:200px;">
      <button type="button" class="rsv-combo-trigger" onclick="RSV.toggleCombo(this)" aria-haspopup="listbox" aria-expanded="false">
        <span class="rsv-combo-value">Saved Comparisons</span>
        <span class="rsv-combo-arrow" aria-hidden="true">&#x25BE;</span>
      </button>
      <div class="rsv-combo-panel" hidden role="listbox">`;
    if (saved.length === 0) {{
      html += `<div class="rsv-combo-empty">No saved comparisons yet. Use "Save Comparison" to capture the current setup.</div>`;
    }} else {{
      html += `<div class="rsv-combo-list">
        <div class="rsv-combo-group">My Saved Comparisons</div>`;
      saved.forEach((c, i) => {{
        html += `<button type="button" class="rsv-combo-option" onclick="RSV.loadSavedComparison(${{i}})">${{c.name}}</button>`;
      }});
      html += `</div>
        <div class="rsv-combo-footer"><button type="button" onclick="RSV.closeAllCombos();RSV.deleteSavedComparisonPrompt();">Delete a Save</button></div>`;
    }}
    html += `</div></div>`;
    return html;
  }},

  switchComparisonPage(id) {{
    if (state.activeTab === id) return;
    state.activeTab = id;
    this.renderTabs();
    this.renderPanel(id);
  }},

  renderPanel(portfolioIdx) {{
    if (portfolioIdx === "summary") {{
      this.renderSummaryPanel();
      return;
    }}
    if (portfolioIdx === "riskDiv") {{
      this.renderRiskDivPanel();
      return;
    }}
    if (portfolioIdx === "trackingError") {{
      // Tracking Error is now a chart sub-tab inside the Risk & Return Statistics panel.
      state.activeTab = "summary";
      this._activeComparisonChartTab = "trackingError";
      this.renderSummaryPanel();
      return;
    }}
    if (portfolioIdx === "customUpload") {{
      this.renderCustomUploadPanel();
      return;
    }}
    const container = document.getElementById("rsv-panels");
    const p = state.portfolios[portfolioIdx];
    if (!p.enabled) {{
      container.innerHTML = '<div class="rsv-panel" style="text-align:center;color:var(--text-secondary);padding:40px;">This portfolio is disabled. Enable it using the checkbox above.</div>';
      return;
    }}

    container.innerHTML = `
      <div class="rsv-panel">
        <div class="rsv-three-col">
          <div>
            <div class="rsv-step-header">
              <span class="rsv-step-num">1</span>
              <span class="rsv-step-label">Choose Your Base Portfolio</span>
            </div>
            <div class="rsv-name-row">
              <label for="rsv-name-input-${{portfolioIdx}}">Portfolio Name</label>
              <input type="text" id="rsv-name-input-${{portfolioIdx}}" maxlength="60"
                     value="${{p.name.replace(/"/g, "&quot;")}}"
                     oninput="RSV.updatePortfolioName(${{portfolioIdx}}, this.value)"
                     onchange="RSV.commitPortfolioName(${{portfolioIdx}})">
            </div>
            ${{this.renderAllocTable(portfolioIdx, "core")}}
            <div style="display:flex;gap:8px;align-items:center;margin-top:8px;">
              <button class="rsv-add-btn rsv-compute-btn--no-mt" onclick="RSV.addRow(${{portfolioIdx}}, 'core')">+ Add Asset Class</button>
              <span class="rsv-btn-tooltip">
                <button class="rsv-add-btn rsv-add-btn--filled" onclick="RSV.resetPortfolio(${{portfolioIdx}})">Clear Portfolio</button>
                <span class="rsv-tooltip-text">Clear name, allocations, and fees to default.</span>
              </span>
            </div>
          </div>
          <div>
            <div class="rsv-step-header">
              <span class="rsv-step-num">2</span>
              <span class="rsv-step-label">Choose What You Want to Stack on Top</span>
            </div>
            <div class="rsv-name-row" style="visibility:hidden;" aria-hidden="true">
              <label>&nbsp;</label>
              <input type="text" tabindex="-1">
            </div>
            ${{this.renderAllocTable(portfolioIdx, "stack")}}
            <button class="rsv-add-btn" onclick="RSV.addRow(${{portfolioIdx}}, 'stack')">+ Add Overlay</button>
          </div>
          <div class="rsv-alloc-bar-wrap">
            <div class="rsv-step-header">
              <span class="rsv-step-num">3</span>
              <span class="rsv-step-label">Your Return Stacked&reg; Portfolio Allocation</span>
            </div>
            <div id="rsv-alloc-vis-${{portfolioIdx}}" class="rsv-alloc-vis">
              <div class="rsv-alloc-empty">Add assets to see allocation</div>
            </div>
          </div>
        </div>
        ${{this.renderSummaryBar(portfolioIdx)}}
        <div class="rsv-fee-row">
          <label>Annualized Advisor Fee (%)
            <span class="rsv-tooltip">(?)<span class="rsv-tooltip-text">Annualized advisor fee that applies across the whole portfolio, as a percentage (e.g. 1 for 1%, 0.50 for half a percent)</span></span>
          </label>
          <input type="number" step="0.01" min="0" max="5" value="${{p.fee / 100}}"
                 onchange="RSV.updateFee(${{portfolioIdx}}, this.value)"
                 oninput="RSV.updateFee(${{portfolioIdx}}, this.value)"
                 onfocus="this.select()">
          <div style="margin-left:auto;display:flex;align-items:center;gap:12px;">
            <div class="rsv-step-header" style="margin-bottom:0;">
              <span class="rsv-step-num">4</span>
              <span class="rsv-step-label">Save, Share &amp; Upload Custom Data</span>
            </div>
            <span class="rsv-btn-tooltip">
              <button class="rsv-compute-btn rsv-compute-btn--secondary" onclick="RSV.savePortfolio(${{portfolioIdx}})">Save Portfolio</button>
              <span class="rsv-tooltip-text">Saves to your browser and downloads a backup file. Use Import to restore if browser data is cleared.</span>
            </span>
            <span class="rsv-btn-tooltip">
              <button class="rsv-compute-btn rsv-compute-btn--secondary" onclick="RSV.sharePortfolio(${{portfolioIdx}}, this)">&#x2197; Share</button>
              <span class="rsv-tooltip-text">Copy a shareable link to this portfolio configuration.</span>
            </span>
            <span class="rsv-btn-tooltip">
              <button class="rsv-compute-btn rsv-compute-btn--secondary" onclick="RSV.exportPortfolioPDF(${{portfolioIdx}})">&#x2193; PDF</button>
              <span class="rsv-tooltip-text">Export this portfolio analysis as a branded PDF report.</span>
            </span>
            <button class="rsv-compute-btn rsv-compute-btn--no-mt" onclick="state.activeTab='customUpload';RSV.renderTabs();RSV.renderPanel('customUpload');">
              Custom Data
            </button>
          </div>
        </div>
        ${{this.renderValidation(portfolioIdx)}}
        ${{this.renderConsultantCTA()}}
        ${{this.renderPortfolioStats(portfolioIdx)}}
      </div>
    `;
    this.initCharts(portfolioIdx);
    this.renderAllocBar(portfolioIdx);
  }},

  renderAllocTable(portfolioIdx, section) {{
    const rows = state.portfolios[portfolioIdx][section];
    let html = `<table class="rsv-alloc-table">
      <thead><tr>
        <th style="width:52%">Asset Class</th>
        <th style="width:24%">Weight (%)</th>
        <th style="width:19%">Volatility</th>
        <th style="width:5%"></th>
      </tr></thead><tbody>`;

    for (let i = 0; i < rows.length; i++) {{
      const row = rows[i];
      const vol = this.getAssetVol(row.asset);
      html += `<tr>
        <td>${{this.renderAssetSelect(portfolioIdx, section, i, row.asset)}}</td>
        <td><input type="number" step="1" min="0" max="200" value="${{row.weight || ""}}"
             onchange="RSV.updateWeight(${{portfolioIdx}}, '${{section}}', ${{i}}, this.value)"
             oninput="RSV.updateWeight(${{portfolioIdx}}, '${{section}}', ${{i}}, this.value)"
             onfocus="this.select()"
             placeholder="0"></td>
        <td style="font-size:12px;color:var(--text-secondary)">${{vol ? (vol * 100).toFixed(1) + "%" : "-"}}</td>
        <td>${{rows.length > 1 ? `<button class="rsv-remove-btn" onclick="RSV.removeRow(${{portfolioIdx}}, '${{section}}', ${{i}})" title="Remove">&times;</button>` : ""}}</td>
      </tr>`;
    }}

    // Total row
    const total = rows.reduce((s, r) => s + (r.weight || 0), 0);
    const isCore = section === "core";
    const coreInvalid = isCore && total > 0.01 && Math.abs(total - 100) > 0.01;
    const validClass = isCore ? (coreInvalid ? "rsv-total-invalid" : "rsv-total-valid") : "";
    html += `<tr class="rsv-total-row">
      <td style="text-align:right">Total:</td>
      <td class="${{validClass}}">${{total.toFixed(1)}}%${{coreInvalid ? " (must = 100%)" : ""}}</td>
      <td></td><td></td>
    </tr>`;

    html += "</tbody></table>";
    return html;
  }},

  renderAssetSelect(portfolioIdx, section, rowIdx, selectedAsset) {{
    // Collect assets already used in other rows of this section
    const usedAssets = new Set();
    const rows = state.portfolios[portfolioIdx][section];
    for (let r = 0; r < rows.length; r++) {{
      if (r !== rowIdx && rows[r].asset) usedAssets.add(rows[r].asset);
    }}

    // Popular assets shown at top of dropdown (removed from their original categories)
    const popularGroups = [
      {{ label: "Equities (Popular)", names: ["U.S. Large Cap Equities", "International Equities", "Global Equities"] }},
      {{ label: "Fixed Income (Popular)", names: ["U.S. Treasury Ladder", "U.S. Core Fixed Income", "Intermediate-Term U.S. Treasuries", "Long-Term U.S. Treasuries"] }},
      {{ label: "Alternatives (Popular)", names: ["Managed Futures Trend", "Futures Yield (Carry)", "Gold", "Merger Arbitrage", "Merger Arbitrage (AB)", "Systematic Global Macro", "Risk-Weighted Gold/Bitcoin"] }},
    ];
    const popularSet = new Set();
    for (const g of popularGroups) for (const n of g.names) popularSet.add(n);

    const optionHtml = (a) => {{
      const isSel = a.shortName === selectedAsset;
      const isDis = usedAssets.has(a.shortName);
      const cls = "rsv-combo-option" + (isSel ? " is-selected" : "") + (isDis ? " is-disabled" : "");
      const disAttr = isDis ? " disabled" : "";
      return `<button type="button" class="${{cls}}" data-value="${{a.shortName}}" onclick="RSV.selectComboOption(this)"${{disAttr}}>${{a.shortName}}</button>`;
    }};

    const triggerLabel = selectedAsset || "-- Select Asset Class --";
    const isPlaceholder = !selectedAsset;
    let html = `<div class="rsv-combo" data-portfolio="${{portfolioIdx}}" data-section="${{section}}" data-row="${{rowIdx}}">
      <button type="button" class="rsv-combo-trigger${{isPlaceholder ? " is-placeholder" : ""}}" onclick="RSV.toggleCombo(this)" aria-haspopup="listbox" aria-expanded="false" title="${{triggerLabel}}">
        <span class="rsv-combo-value">${{triggerLabel}}</span>
        <span class="rsv-combo-arrow" aria-hidden="true">&#x25BE;</span>
      </button>
      <div class="rsv-combo-panel" hidden role="listbox">
        <div class="rsv-combo-search-wrap">
          <input type="text" class="rsv-combo-search" placeholder="Search assets..." oninput="RSV.filterCombo(this)" onkeydown="RSV.handleComboKeydown(event, this)" autocomplete="off">
        </div>
        <div class="rsv-combo-list">
          <button type="button" class="rsv-combo-option rsv-combo-clear${{isPlaceholder ? " is-selected" : ""}}" data-value="" onclick="RSV.selectComboOption(this)">-- Select Asset Class --</button>`;

    // Popular groups first
    for (const g of popularGroups) {{
      html += `<div class="rsv-combo-group">${{g.label}}</div>`;
      for (const name of g.names) {{
        // Find the asset object across all categories
        let found = null;
        for (const cat of CATEGORY_ORDER) {{
          const assets = ASSET_CATEGORIES[cat];
          if (assets) {{
            const match = assets.find(a => a.shortName === name);
            if (match) {{ found = match; break; }}
          }}
        }}
        if (found) html += optionHtml(found);
      }}
    }}

    // Remaining categories (excluding popular assets)
    for (const cat of CATEGORY_ORDER) {{
      const assets = ASSET_CATEGORIES[cat];
      if (!assets || assets.length === 0) continue;
      const filtered = assets.filter(a => !popularSet.has(a.shortName));
      if (filtered.length === 0) continue;
      html += `<div class="rsv-combo-group">${{cat}}</div>`;
      for (const a of filtered) {{
        html += optionHtml(a);
      }}
    }}
    html += `</div></div></div>`;
    return html;
  }},

  toggleCombo(triggerEl) {{
    const combo = triggerEl.closest(".rsv-combo");
    if (!combo) return;
    const isOpen = combo.classList.contains("is-open");
    this.closeAllCombos();
    if (isOpen) return;
    combo.classList.add("is-open");
    triggerEl.setAttribute("aria-expanded", "true");
    const panel = combo.querySelector(".rsv-combo-panel");
    if (panel) panel.hidden = false;
    const search = combo.querySelector(".rsv-combo-search");
    if (search) {{
      search.value = "";
      this.filterCombo(search);
      requestAnimationFrame(() => search.focus());
    }}
    // Auto-scroll to selected option
    const selected = combo.querySelector(".rsv-combo-option.is-selected:not(.rsv-combo-clear)");
    if (selected && panel) {{
      const list = panel.querySelector(".rsv-combo-list");
      if (list) list.scrollTop = Math.max(0, selected.offsetTop - 60);
    }}
  }},

  closeAllCombos() {{
    document.querySelectorAll(".rsv-combo.is-open").forEach(combo => {{
      combo.classList.remove("is-open");
      const trigger = combo.querySelector(".rsv-combo-trigger");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
      const panel = combo.querySelector(".rsv-combo-panel");
      if (panel) panel.hidden = true;
      // Clear active highlight
      combo.querySelectorAll(".rsv-combo-option.is-active").forEach(o => o.classList.remove("is-active"));
    }});
  }},

  filterCombo(searchEl) {{
    const combo = searchEl.closest(".rsv-combo");
    if (!combo) return;
    const q = searchEl.value.trim().toLowerCase();
    const list = combo.querySelector(".rsv-combo-list");
    if (!list) return;

    // Remove any previous "no results" element
    const prevEmpty = list.querySelector(".rsv-combo-empty");
    if (prevEmpty) prevEmpty.remove();

    let visibleCount = 0;
    const groups = list.querySelectorAll(".rsv-combo-group");
    // Walk siblings: each group is followed by options until the next group
    groups.forEach((groupEl) => {{
      let groupHasMatch = false;
      let sib = groupEl.nextElementSibling;
      while (sib && !sib.classList.contains("rsv-combo-group")) {{
        if (sib.classList.contains("rsv-combo-option")) {{
          const label = (sib.textContent || "").toLowerCase();
          const match = !q || label.includes(q);
          sib.style.display = match ? "" : "none";
          if (match) {{ groupHasMatch = true; visibleCount++; }}
        }}
        sib = sib.nextElementSibling;
      }}
      groupEl.style.display = groupHasMatch ? "" : "none";
    }});

    // The "-- Select Asset Class --" clear option only shows when there's no search query
    const clearOpt = list.querySelector(".rsv-combo-clear");
    if (clearOpt) clearOpt.style.display = q ? "none" : "";

    // Reset active highlight to first visible match
    list.querySelectorAll(".rsv-combo-option.is-active").forEach(o => o.classList.remove("is-active"));
    if (q && visibleCount > 0) {{
      const firstVisible = Array.from(list.querySelectorAll(".rsv-combo-option:not(.rsv-combo-clear):not(.is-disabled)")).find(o => o.style.display !== "none");
      if (firstVisible) firstVisible.classList.add("is-active");
    }}

    if (visibleCount === 0 && q) {{
      const empty = document.createElement("div");
      empty.className = "rsv-combo-empty";
      empty.textContent = "No matching assets";
      list.appendChild(empty);
    }}
  }},

  selectComboOption(optionEl) {{
    if (optionEl.classList.contains("is-disabled") || optionEl.disabled) return;
    const combo = optionEl.closest(".rsv-combo");
    if (!combo) return;
    const value = optionEl.dataset.value || "";
    this.closeAllCombos();
    if (combo.dataset.saved) {{
      // Global Saved Portfolios picker — load into the active portfolio tab
      if (!value) return;
      const target = typeof state.activeTab === "number" ? state.activeTab : 0;
      this.loadSavedPortfolio(target, value);
      return;
    }}
    const portfolioIdx = parseInt(combo.dataset.portfolio, 10);
    const section = combo.dataset.section;
    const rowIdx = parseInt(combo.dataset.row, 10);
    this.updateAsset(portfolioIdx, section, rowIdx, value);
  }},

  handleComboKeydown(ev, searchEl) {{
    const combo = searchEl.closest(".rsv-combo");
    if (!combo) return;
    const list = combo.querySelector(".rsv-combo-list");
    if (!list) return;
    const visibleOptions = Array.from(list.querySelectorAll(".rsv-combo-option:not(.rsv-combo-clear):not(.is-disabled)")).filter(o => o.style.display !== "none");

    if (ev.key === "Escape") {{
      ev.preventDefault();
      this.closeAllCombos();
      const trigger = combo.querySelector(".rsv-combo-trigger");
      if (trigger) trigger.focus();
      return;
    }}
    if (ev.key === "Enter") {{
      ev.preventDefault();
      const active = list.querySelector(".rsv-combo-option.is-active") || visibleOptions[0];
      if (active) this.selectComboOption(active);
      return;
    }}
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {{
      ev.preventDefault();
      if (visibleOptions.length === 0) return;
      const currentIdx = visibleOptions.findIndex(o => o.classList.contains("is-active"));
      let nextIdx;
      if (ev.key === "ArrowDown") nextIdx = currentIdx < 0 ? 0 : Math.min(currentIdx + 1, visibleOptions.length - 1);
      else nextIdx = currentIdx <= 0 ? 0 : currentIdx - 1;
      visibleOptions.forEach(o => o.classList.remove("is-active"));
      const next = visibleOptions[nextIdx];
      next.classList.add("is-active");
      // Scroll into view if needed
      const listRect = list.getBoundingClientRect();
      const optRect = next.getBoundingClientRect();
      if (optRect.bottom > listRect.bottom) list.scrollTop += (optRect.bottom - listRect.bottom);
      else if (optRect.top < listRect.top) list.scrollTop -= (listRect.top - optRect.top);
    }}
  }},

  _initComboGlobalListeners() {{
    if (this._comboListenersInstalled) return;
    this._comboListenersInstalled = true;
    document.addEventListener("mousedown", (ev) => {{
      if (ev.target.closest(".rsv-combo")) return;
      this.closeAllCombos();
    }});
    document.addEventListener("keydown", (ev) => {{
      if (ev.key === "Escape" && document.querySelector(".rsv-combo.is-open")) {{
        this.closeAllCombos();
      }}
    }});
  }},

  getAssetVol(shortName) {{
    if (!shortName) return null;
    const data = getAssetData(shortName);
    if (!data || !data.values) return null;
    // Calculate historical volatility from monthly returns
    const returns = [];
    for (let i = 1; i < data.values.length; i++) {{
      if (data.values[i] != null && data.values[i - 1] != null && data.values[i - 1] !== 0) {{
        returns.push(data.values[i] / data.values[i - 1] - 1);
      }}
    }}
    if (returns.length < 12) return null;
    const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
    const variance = returns.reduce((s, r) => s + Math.pow(r - mean, 2), 0) / (returns.length - 1);
    return Math.sqrt(variance) * Math.sqrt(12);  // Annualized
  }},

  renderSummaryBar(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const coreTotal = p.core.reduce((s, r) => s + (r.weight || 0), 0);
    const stackTotal = p.stack.reduce((s, r) => s + (r.weight || 0), 0);
    const notional = coreTotal + stackTotal;

    // Find effective start date
    const allAssets = [...p.core, ...p.stack].filter(r => r.asset).map(r => r.asset);
    const range = allAssets.length > 0 ? findCommonDateRange(allAssets) : {{ start: null, end: null }};

    return `<div class="rsv-summary-bar">
      <div class="rsv-summary-item">
        <span class="rsv-summary-label">Core Allocation</span>
        <span class="rsv-summary-value ${{Math.abs(coreTotal - 100) > 0.01 && !(coreTotal === 0 && stackTotal > 0) ? 'warning' : ''}}">${{coreTotal.toFixed(1)}}%</span>
      </div>
      <div class="rsv-summary-item">
        <span class="rsv-summary-label">Stack Overlay</span>
        <span class="rsv-summary-value">${{stackTotal.toFixed(1)}}%</span>
      </div>
      <div class="rsv-summary-item">
        <span class="rsv-summary-label">Notional Exposure</span>
        <span class="rsv-summary-value">${{notional.toFixed(1)}}%</span>
      </div>
      <div class="rsv-summary-item">
        <span class="rsv-summary-label">Asset Class Start Date</span>
        <span class="rsv-summary-value">${{range.start || "N/A"}}</span>
      </div>
    </div>`;
  }},

  renderValidation(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const coreTotal = p.core.reduce((s, r) => s + (r.weight || 0), 0);
    const coreAssets = p.core.filter(r => r.asset && r.weight > 0);

    const messages = [];
    const stackAssets = p.stack.filter(r => r.asset && r.weight > 0);

    if (coreAssets.length === 0 && stackAssets.length > 0) {{
      messages.push({{ type: "success", text: "Excess return mode: stack overlays will be analyzed without a core portfolio." }});
    }} else if (coreAssets.length === 0) {{
      messages.push({{ type: "info", text: "Select asset classes and set weights to build your core portfolio, or add stack overlays for excess return analysis." }});
    }} else if (Math.abs(coreTotal - 100) > 0.01) {{
      messages.push({{ type: "error", text: `Core portfolio weights must sum to 100%. Currently: ${{coreTotal.toFixed(1)}}%` }});
    }} else {{
      messages.push({{ type: "success", text: "Core portfolio is valid. Add stack overlays to create a return-stacked portfolio." }});
    }}

    // Check for duplicate assets
    const allAssets = [...p.core, ...p.stack].filter(r => r.asset).map(r => r.asset);
    const dupes = allAssets.filter((a, i) => allAssets.indexOf(a) !== i);
    if (dupes.length > 0) {{
      messages.push({{ type: "error", text: `Duplicate asset class: ${{[...new Set(dupes)].join(", ")}}` }});
    }}

    return messages.map(m => `<div class="rsv-validation rsv-${{m.type}}">${{m.text}}</div>`).join("");
  }},

  // ── Actions ──

  updateAsset(portfolioIdx, section, rowIdx, value) {{
    const row = state.portfolios[portfolioIdx][section][rowIdx];
    row.asset = value;
    // Load the asset's embedded fee/financing defaults into the stack row.
    // Selecting a new asset resets these to that asset's defaults; clearing the
    // asset resets them to 0.
    if (section === "stack") {{
      const d = getStackFeeDefaults(value);
      row.feeBp = d.feeBp;
      row.financingBp = d.financingBp;
    }}
    this.renderPanel(state.activeTab);
    this.scheduleAutoCompute(portfolioIdx);
  }},

  updateWeight(portfolioIdx, section, rowIdx, value) {{
    state.portfolios[portfolioIdx][section][rowIdx].weight = parseFloat(value) || 0;
    // Don't re-render full panel on weight change (would lose focus)
    // Just update the summary bar and validation
    const panel = document.querySelector(".rsv-panel");
    if (panel) {{
      const summaryBar = panel.querySelector(".rsv-summary-bar");
      if (summaryBar) summaryBar.outerHTML = this.renderSummaryBar(portfolioIdx);
      const validations = panel.querySelectorAll(".rsv-validation");
      const newValidation = this.renderValidation(portfolioIdx);
      validations.forEach(v => v.remove());
      const feeRow = panel.querySelector(".rsv-fee-row");
      if (feeRow) {{
        feeRow.insertAdjacentHTML("afterend", newValidation);
      }}
      ["core", "stack"].forEach(sec => {{
        const rows = state.portfolios[portfolioIdx][sec];
        const total = rows.reduce((s, r) => s + (r.weight || 0), 0);
        const tables = panel.querySelectorAll(".rsv-alloc-table");
        const tableIdx = sec === "core" ? 0 : 1;
        if (tables[tableIdx]) {{
          const totalCell = tables[tableIdx].querySelector(".rsv-total-row td:nth-child(2)");
          if (totalCell) {{
            const isCore = sec === "core";
            const coreInvalid = isCore && total > 0.01 && Math.abs(total - 100) > 0.01;
            const valid = !isCore || !coreInvalid;
            totalCell.className = isCore ? (valid ? "rsv-total-valid" : "rsv-total-invalid") : "";
            totalCell.textContent = total.toFixed(1) + "%" + (coreInvalid ? " (must = 100%)" : "");
          }}
        }}
      }});
    }}
    this.renderAllocBar(portfolioIdx);
    // If portfolio is now invalid, clear stale results so old charts/stats don't persist
    const p = state.portfolios[portfolioIdx];
    const coreTotal = p.core.reduce((s, r) => s + (r.weight || 0), 0);
    const coreHasAssets = p.core.some(r => r.asset && r.weight > 0);
    const stackHasAssets = p.stack.some(r => r.asset && r.weight > 0);
    const coreValid = coreHasAssets && Math.abs(coreTotal - 100) < 0.01;
    const stackOnly = !coreHasAssets && stackHasAssets;
    if (!coreValid && !stackOnly && p.result) {{
      p.result = null;
      this.destroyCharts(portfolioIdx);
      const statsEl = document.getElementById(`rsv-portfolio-stats-${{portfolioIdx}}`);
      if (statsEl) statsEl.innerHTML = "";
    }}
    this.scheduleAutoCompute(portfolioIdx);
  }},

  updateFee(portfolioIdx, value) {{
    // The input is a percentage (e.g. 0.50 for 0.50%); fee is stored internally
    // in basis points (50), which is what the compute/display/save paths expect.
    state.portfolios[portfolioIdx].fee = Math.round((parseFloat(value) || 0) * 100);
    this.scheduleAutoCompute(portfolioIdx);
  }},

  addRow(portfolioIdx, section) {{
    const row = {{ asset: "", weight: 0 }};
    if (section === "stack") {{ row.feeBp = 0; row.financingBp = 0; }}
    state.portfolios[portfolioIdx][section].push(row);
    this.renderPanel(state.activeTab);
  }},

  removeRow(portfolioIdx, section, rowIdx) {{
    state.portfolios[portfolioIdx][section].splice(rowIdx, 1);
    this.renderPanel(state.activeTab);
  }},

  computeSingle(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const result = computePortfolio(p);
    if (!result) {{
      alert("Cannot analyze this portfolio. Ensure core weights sum to 100% and at least one asset is selected.");
      return;
    }}
    p.result = result;
    this.renderPanel(portfolioIdx);
  }},

  compute() {{
    // Analyze all enabled portfolios and show Summary
    let anyValid = false;
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      if (!p.enabled) continue;
      const result = computePortfolio(p);
      p.result = result;
      if (result) anyValid = true;
    }}
    if (!anyValid) {{
      alert("No valid portfolios to analyze. Ensure core weights sum to 100% and at least one asset is selected.");
      return;
    }}
    state.activeTab = "summary";
    this.renderTabs();
    this.renderPanel("summary");
  }},

  // ── Comparison Date Range ──

  _getComparisonCommonRange(active) {{
    let commonStart = null, commonEnd = null;
    for (const i of active) {{
      const r = state.portfolios[i].result;
      const s = r.dates[0], e = r.dates[r.dates.length - 1];
      if (!commonStart || s > commonStart) commonStart = s;
      if (!commonEnd || e < commonEnd) commonEnd = e;
    }}
    return {{ start: commonStart, end: commonEnd }};
  }},

  _applyComparisonDateRange(naturalRange) {{
    const dr = state.comparisonDateRange;
    if (!dr) return naturalRange;
    return {{
      start: dr.start > naturalRange.start ? dr.start : naturalRange.start,
      end: dr.end < naturalRange.end ? dr.end : naturalRange.end,
    }};
  }},

  renderComparisonDateRangeBar(naturalRange) {{
    const dr = state.comparisonDateRange;
    const fromVal = dr ? dr.start : naturalRange.start;
    const toVal = dr ? dr.end : naturalRange.end;

    const startYear = parseInt(naturalRange.start.substring(0, 4));
    const endYear = parseInt(naturalRange.end.substring(0, 4));
    let yearOpts = '<option value="">--</option>';
    for (let y = endYear; y >= startYear; y--) {{
      yearOpts += `<option value="${{y}}">${{y}}</option>`;
    }}

    return `<div class="rsv-date-range-bar">
      <label>Year</label>
      <select id="rsv-comp-year" onchange="RSV.selectComparisonYear(this.value)">
        ${{yearOpts}}
      </select>
      <label>From</label>
      <input type="date" id="rsv-comp-date-from" value="${{fromVal}}"
             min="${{naturalRange.start}}" max="${{naturalRange.end}}"
             onchange="RSV.applyComparisonDateRange()">
      <label>To</label>
      <input type="date" id="rsv-comp-date-to" value="${{toVal}}"
             min="${{naturalRange.start}}" max="${{naturalRange.end}}"
             onchange="RSV.applyComparisonDateRange()">
      <button class="rsv-date-btn" onclick="RSV.resetComparisonDateRange()">Reset</button>
      <div class="rsv-date-quick-btns">
        <button onclick="RSV.quickComparisonDateRange('3M')">3M</button>
        <button onclick="RSV.quickComparisonDateRange('6M')">6M</button>
        <button onclick="RSV.quickComparisonDateRange('YTD')">YTD</button>
        <button onclick="RSV.quickComparisonDateRange('1Y')">1Y</button>
        <button onclick="RSV.quickComparisonDateRange('3Y')">3Y</button>
        <button onclick="RSV.quickComparisonDateRange('5Y')">5Y</button>
        <button onclick="RSV.quickComparisonDateRange('10Y')">10Y</button>
        <button onclick="RSV.quickComparisonDateRange('20Y')">20Y</button>
        <button onclick="RSV.quickComparisonDateRange('All')">All</button>
      </div>
    </div>`;
  }},

  applyComparisonDateRange() {{
    const fromEl = document.getElementById("rsv-comp-date-from");
    const toEl = document.getElementById("rsv-comp-date-to");
    if (!fromEl || !toEl || fromEl.value >= toEl.value) return;
    // Snap to nearest available dates in INDEX_DATA
    const allDates = INDEX_DATA.dates;
    const snap = (target) => {{
      let best = allDates[0];
      for (const d of allDates) {{
        if (d <= target) best = d;
      }}
      return best;
    }};
    state.comparisonDateRange = {{ start: snap(fromEl.value), end: snap(toEl.value) }};
    this.renderPanel(state.activeTab);
  }},

  resetComparisonDateRange() {{
    state.comparisonDateRange = null;
    this.renderPanel(state.activeTab);
  }},

  selectComparisonYear(yearStr) {{
    if (!yearStr) return;
    const year = parseInt(yearStr);
    const fromEl = document.getElementById("rsv-comp-date-from");
    const toEl = document.getElementById("rsv-comp-date-to");
    if (!fromEl || !toEl) return;
    const allDates = INDEX_DATA.dates;
    let firstInYear = null, lastInYear = null;
    for (const d of allDates) {{
      const y = parseInt(d.substring(0, 4));
      if (y === year) {{
        if (!firstInYear) firstInYear = d;
        lastInYear = d;
      }}
    }}
    if (firstInYear && lastInYear) {{
      const idx = allDates.indexOf(firstInYear);
      fromEl.value = idx > 0 ? allDates[idx - 1] : firstInYear;
      toEl.value = lastInYear;
      this.applyComparisonDateRange();
    }}
  }},

  quickComparisonDateRange(period) {{
    if (period === "All") {{
      this.resetComparisonDateRange();
      return;
    }}
    // Get the natural common range from active portfolios
    const active = [];
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      if (p.enabled && p.result) active.push(i);
    }}
    if (active.length === 0) return;
    const natural = this._getComparisonCommonRange(active);
    const fullEnd = natural.end;
    const endParts = fullEnd.split("-");
    let ey = parseInt(endParts[0]), em = parseInt(endParts[1]);

    let startDate;
    if (period === "YTD") {{
      startDate = `${{ey - 1}}-12-31`;
    }} else {{
      const months = {{ "3M": 3, "6M": 6, "1Y": 12, "3Y": 36, "5Y": 60, "10Y": 120, "20Y": 240 }}[period] || 12;
      let sm = em - months;
      let sy = ey;
      while (sm <= 0) {{ sm += 12; sy--; }}
      const smStr = sm < 10 ? "0" + sm : "" + sm;
      startDate = `${{sy}}-${{smStr}}-01`;
    }}
    const allDates = INDEX_DATA.dates;
    let snappedStart = natural.start;
    for (const d of allDates) {{
      if (d <= startDate) snappedStart = d;
    }}
    if (snappedStart >= fullEnd) return;
    state.comparisonDateRange = {{ start: snappedStart, end: fullEnd }};
    this.renderPanel(state.activeTab);
  }},

  // ── Summary Panel ──

  renderSummaryPanel() {{
    this.destroyComparisonCharts();
    const container = document.getElementById("rsv-panels");

    // Compute all enabled portfolios that haven't been computed yet
    const active = [];
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      if (!p.enabled) continue;
      if (!p.result) {{
        p.result = computePortfolio(p);
      }}
      if (p.result) active.push(i);
    }}

    if (active.length === 0) {{
      container.innerHTML = `<div class="rsv-panel">
        ${{this.renderComparisonSubTabs("summary")}}
        <div style="text-align:center;color:var(--text-secondary);padding:40px;">No analyzed portfolios. Set up and analyze at least one portfolio first, or load a saved comparison.</div>
      </div>`;
      return;
    }}

    // Find common date range across all active portfolios, then apply user filter
    const naturalRange = this._getComparisonCommonRange(active);
    const effectiveRange = this._applyComparisonDateRange(naturalRange);
    const commonStart = effectiveRange.start;
    const commonEnd = effectiveRange.end;
    const commonPeriod = effectiveRange;

    // Recompute stats over common period for each portfolio
    const commonCoreStats = {{}};
    const commonStackedStats = {{}};
    for (const i of active) {{
      const r = state.portfolios[i].result;
      commonCoreStats[i] = computeStats(r.coreReturns, r.dates, commonStart, commonEnd) || r.coreStats;
      commonStackedStats[i] = computeStats(r.stackedReturns, r.dates, commonStart, commonEnd, !r.hasCore) || r.stackedStats;
    }}

    const firstResult = state.portfolios[active[0]].result;
    const benchmarks = this.getBenchmarkFrontier(commonPeriod);

    const fmt = (v, isPct) => isPct ? (v * 100).toFixed(2) + "%" : v.toFixed(4);
    // No coloring for core/stacked tables
    const clsNone = () => "";
    // Difference table: green when improvement, red when degradation, tracking error always black
    const clsDiff = (v, key) => {{
      if (key === "trackingError") return "";
      // For risk metrics, lower is better so positive diff is bad
      if (key === "maxDrawdown" || key === "volatility") return v > 0 ? "negative" : v < 0 ? "positive" : "";
      // For return/ratio metrics, higher is better
      return v > 0 ? "positive" : v < 0 ? "negative" : "";
    }};

    const metrics = [
      ["Cumulative Return", "cumulativeReturn", true],
      ["Annualized Return", "annualizedReturn", true],
      ["Volatility", "volatility", true],
      ["Max Drawdown", "maxDrawdown", true],
      ["Sharpe Ratio", "sharpe", false],
      ["Sortino Ratio", "sortino", false],
      ["Tracking Error", "trackingError", true],
    ];

    // ── Build the three tables: Core, Stacked, Difference ──
    const buildTable = (title, getData, cls, csvName) => {{
      const csvFile = csvName || "Portfolio-Comparison_" + title.replace(/[^\\w]+/g, "-");
      let html = `<div class="rsv-dl-section" style="margin-bottom:24px;">
        <div class="rsv-section-title rsv-section-title--plain"><span>${{title}}</span>
          <button class="rsv-dl-btn" onclick="RSV.downloadSectionCsv(this, '${{csvFile}}')" title="Download table as CSV">&#x2193; CSV</button>
        </div>
        <div style="overflow-x:auto;">
        <table class="rsv-results-table rsv-rr-table">
          <thead><tr><th style="text-align:left;">Metric</th>`;
      for (const i of active) {{
        html += `<th style="text-align:center;">${{state.portfolios[i].name}}</th>`;
      }}
      // Benchmarks
      if (benchmarks) {{
        for (const b of benchmarks) {{
          html += `<th style="text-align:center;color:var(--text-secondary);font-weight:500;">${{b.label}}</th>`;
        }}
      }}
      html += "</tr></thead><tbody>";

      for (const [label, key, isPct] of metrics) {{
        html += `<tr><td style="text-align:left;">${{label}}</td>`;
        for (const i of active) {{
          const val = getData(i, key);
          if (val === null || val === undefined) {{
            html += '<td style="text-align:center;">-</td>';
          }} else {{
            html += `<td style="text-align:center;" class="${{cls(val, key)}}">${{fmt(val, isPct)}}</td>`;
          }}
        }}
        // Benchmark columns
        if (benchmarks && key !== "trackingError") {{
          for (const b of benchmarks) {{
            let bVal = null;
            if (key === "cumulativeReturn") bVal = null; // benchmarks don't have cumulative in frontier
            else if (key === "annualizedReturn") bVal = b.annReturn / 100;
            else if (key === "volatility") bVal = b.vol / 100;
            else if (key === "maxDrawdown") bVal = b.maxDD / 100;
            else if (key === "sharpe") bVal = b.annReturn && b.vol ? (b.annReturn / 100 - benchmarkRf) / (b.vol / 100) : null;
            if (bVal !== null) {{
              html += `<td style="text-align:center;color:var(--text-secondary);" class="${{cls(bVal, key)}}">${{fmt(bVal, isPct)}}</td>`;
            }} else {{
              html += '<td style="text-align:center;color:var(--text-secondary);">-</td>';
            }}
          }}
        }} else if (benchmarks) {{
          for (const b of benchmarks) html += '<td style="text-align:center;color:var(--text-secondary);">-</td>';
        }}
        html += "</tr>";
      }}
      html += "</tbody></table></div></div>";
      return html;
    }};

    // Compute risk-free rate for Sharpe on benchmark frontier points (over common period)
    let benchmarkRf = 0;
    const cashInfo = INDEX_DATA.series["Treasury Bill"];
    if (cashInfo) {{
      const allDates = INDEX_DATA.dates;
      const si = allDates.indexOf(commonStart);
      const ei = allDates.indexOf(commonEnd);
      let sum = 0, count = 0;
      for (let i = si + 1; i <= ei; i++) {{
        const di = i - cashInfo.start;
        if (di > 0 && di < cashInfo.values.length && cashInfo.values[di-1]) {{
          sum += cashInfo.values[di] / cashInfo.values[di-1] - 1;
          count++;
        }}
      }}
      if (count > 0) benchmarkRf = (sum / count) * 12;
    }}

    // Compute tracking error over common period
    const commonTE = {{}};
    for (const i of active) {{
      const r = state.portfolios[i].result;
      const coreAligned = [], stackAligned = [];
      for (let m = 0; m < r.coreReturns.length; m++) {{
        const date = r.dates[m + 1];
        if (date > commonStart && date <= commonEnd) {{
          coreAligned.push(r.coreReturns[m]);
          stackAligned.push(r.stackedReturns[m]);
        }}
      }}
      commonTE[i] = this.computeTrackingErrorBetween(coreAligned, stackAligned);
    }}

    let html = '<div class="rsv-panel">';
    html += this.renderComparisonSubTabs("summary");
    html += `<div class="rsv-page-title">Risk &amp; Return Statistics</div>`;
    html += this.renderComparisonDateRangeBar(naturalRange);
    html += `<div style="font-size:12px;color:var(--text-secondary);margin-bottom:16px;">
      Common Period: ${{commonStart}} to ${{commonEnd}} &middot;
      Benchmarks: Global Equities / U.S. Core Fixed Income
    </div>`;

    // ── Tabbed tables: Stacked / Core / Difference ──
    const anyHasCore = active.some(i => state.portfolios[i].result.hasCore !== false);
    const tableTabs = [{{ key: "stacked", label: "Stacked" }}];
    if (anyHasCore) {{
      tableTabs.push({{ key: "core", label: "Core" }});
      tableTabs.push({{ key: "difference", label: "Difference" }});
    }}
    let activeTableTab = this._activeComparisonTableTab || "stacked";
    if (!tableTabs.some(t => t.key === activeTableTab)) activeTableTab = "stacked";
    this._activeComparisonTableTab = activeTableTab;

    const stackedTableHtml = buildTable("Stacked Portfolio", (i, key) => {{
      if (key === "trackingError") return commonTE[i];
      return commonStackedStats[i][key];
    }}, clsNone, "Risk-and-Return_Stacked-Portfolio");
    const coreTableHtml = anyHasCore ? buildTable("Core Portfolio", (i, key) => {{
      if (key === "trackingError") return 0;
      return commonCoreStats[i][key];
    }}, clsNone, "Risk-and-Return_Core-Portfolio") : "";
    const diffTableHtml = anyHasCore ? buildTable("Difference (Stacked - Core)", (i, key) => {{
      if (key === "trackingError") return commonTE[i];
      return commonStackedStats[i][key] - commonCoreStats[i][key];
    }}, clsDiff, "Risk-and-Return_Difference") : "";

    const _ttCls = (k) => k === activeTableTab ? "rsv-chart-tab active" : "rsv-chart-tab";
    html += `<div class="rsv-chart-area" style="margin-top:8px;">
      <div class="rsv-chart-tabs">`;
    for (const t of tableTabs) {{
      html += `<button class="${{_ttCls(t.key)}}" onclick="RSV.switchComparisonTableTab('${{t.key}}', this)">${{t.label}}</button>`;
    }}
    html += `</div>
      <div id="rsv-comp-table-stacked" style="display:${{activeTableTab === 'stacked' ? 'block' : 'none'}};">${{stackedTableHtml}}</div>
      <div id="rsv-comp-table-core" style="display:${{activeTableTab === 'core' ? 'block' : 'none'}};">${{coreTableHtml}}</div>
      <div id="rsv-comp-table-difference" style="display:${{activeTableTab === 'difference' ? 'block' : 'none'}};">${{diffTableHtml}}</div>
    </div>`;

    // ── Tabbed charts: Growth & Drawdowns / Rolling Returns / Calendar Year / Return & Risk / Tracking Error ──
    const chartTabs = [
      {{ key: "growthDD", label: "Growth & Drawdowns" }},
      {{ key: "rollingReturns", label: "Rolling Returns" }},
      {{ key: "calendarYear", label: "Calendar Year" }},
      {{ key: "returnRisk", label: "Return & Risk" }},
      {{ key: "trackingError", label: "Tracking Error" }},
    ];
    let activeChartTab = this._activeComparisonChartTab || "growthDD";
    if (!chartTabs.some(t => t.key === activeChartTab)) activeChartTab = "growthDD";
    this._activeComparisonChartTab = activeChartTab;
    const _ctCls = (k) => k === activeChartTab ? "rsv-chart-tab active" : "rsv-chart-tab";
    const useLinear = !!this._comparisonGrowthLinear;
    const rollingMonths = this._comparisonRollingMonths || 36;

    html += `<div class="rsv-chart-area" style="margin-top:24px;">
      <div class="rsv-chart-tabs">`;
    for (const t of chartTabs) {{
      html += `<button class="${{_ctCls(t.key)}}" onclick="RSV.switchComparisonChartTab('${{t.key}}', this)">${{t.label}}</button>`;
    }}
    html += `</div>
      <div id="rsv-comp-chart-growthDD" class="${{activeChartTab === 'growthDD' ? 'rsv-comp-chart-active' : ''}}">
        <div class="rsv-chart-controls" style="display:flex;">
          <label><input type="checkbox" ${{useLinear ? "checked" : ""}} onchange="RSV._comparisonGrowthLinear=this.checked;RSV._renderComparisonChartTab('growthDD');"> Linear Scale</label>
        </div>
        <div class="rsv-chart-label">Growth of $1 (Stacked Portfolios)</div>
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadComparisonChart('rsv-summary-growth', 'Growth-of-$1')" title="Download chart as PNG">&#x2193; PNG</button>
          <canvas id="rsv-summary-growth"></canvas>
        </div>
        <div class="rsv-chart-label">Maximum Drawdown and Recovery (Stacked Portfolios)</div>
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadComparisonChart('rsv-summary-drawdown', 'Drawdown')" title="Download chart as PNG">&#x2193; PNG</button>
          <canvas id="rsv-summary-drawdown"></canvas>
        </div>
        <div class="rsv-chart-stats" id="rsv-comp-stats-growthDD" style="display:none;"></div>
      </div>
      <div id="rsv-comp-chart-rollingReturns" class="${{activeChartTab === 'rollingReturns' ? 'rsv-comp-chart-active' : ''}}">
        <div class="rsv-chart-controls" style="display:flex;">
          <span>Period:</span>
          <input type="range" min="12" max="120" value="${{rollingMonths}}" step="3"
            oninput="this.nextElementSibling.textContent=this.value+' Months';clearTimeout(RSV._sliderTimer);RSV._sliderTimer=setTimeout(()=>{{RSV._comparisonRollingMonths=parseInt(this.value);RSV._renderComparisonChartTab('rollingReturns');}},150)">
          <span class="slider-val">${{rollingMonths}} Months</span>
        </div>
        <div class="rsv-chart-label">Rolling Annualized Returns (Stacked Portfolios)</div>
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadComparisonChart('rsv-summary-rolling', 'Rolling-Returns')" title="Download chart as PNG">&#x2193; PNG</button>
          <canvas id="rsv-summary-rolling"></canvas>
        </div>
        <div class="rsv-chart-stats" id="rsv-comp-stats-rolling" style="display:none;"></div>
      </div>
      <div id="rsv-comp-chart-calendarYear" class="${{activeChartTab === 'calendarYear' ? 'rsv-comp-chart-active' : ''}}">
        <div class="rsv-chart-label">Calendar Year Returns (Stacked Portfolios)</div>
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadComparisonChart('rsv-summary-calendar', 'Calendar-Year-Returns')" title="Download chart as PNG">&#x2193; PNG</button>
          <canvas id="rsv-summary-calendar"></canvas>
        </div>
        <div class="rsv-chart-label">Intra-year Maximum Drawdown (Stacked Portfolios)</div>
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadComparisonChart('rsv-summary-calendar-dd', 'Calendar-Year-Max-Drawdown')" title="Download chart as PNG">&#x2193; PNG</button>
          <canvas id="rsv-summary-calendar-dd"></canvas>
        </div>
      </div>
      <div id="rsv-comp-chart-returnRisk" class="rsv-chart-panel--side-by-side${{activeChartTab === 'returnRisk' ? ' rsv-comp-chart-active' : ''}}">
        <div class="rsv-chart-label">Return vs Risk</div>
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadComparisonChart('rsv-summary-risk', 'Return-vs-Risk')" title="Download chart as PNG">&#x2193; PNG</button>
          <canvas id="rsv-summary-risk"></canvas>
        </div>
        <div class="rsv-chart-label">Return vs Max Drawdown</div>
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadComparisonChart('rsv-summary-dd', 'Return-vs-Max-Drawdown')" title="Download chart as PNG">&#x2193; PNG</button>
          <canvas id="rsv-summary-dd"></canvas>
        </div>
      </div>
      <div id="rsv-comp-chart-trackingError" class="${{activeChartTab === 'trackingError' ? 'rsv-comp-chart-active' : ''}}">
        ${{this._buildTrackingErrorMatrixHtml(active, commonStart, commonEnd)}}
      </div>
    </div>`;

    // Dynamic merged disclaimer for all active portfolios
    html += this.renderMergedDisclaimer(active, commonStart, commonEnd);

    html += '</div>';
    container.innerHTML = html;

    // Cache data needed to lazily render chart tabs on switch
    const commonBenchmarks = this.getBenchmarkFrontier(commonPeriod);
    const portfolioColors = ["#14CFA6", "#323A46", "#3A6A9C", "#0C7C64", "#7DA5CE", "#3BB823"];
    this._comparisonChartCtx = {{ active, commonBenchmarks, commonPeriod, portfolioColors }};

    // Render only the active chart tab on initial load
    requestAnimationFrame(() => {{
      this._renderComparisonChartTab(activeChartTab);
    }});
  }},

  _renderComparisonChartTab(tabKey) {{
    const ctx = this._comparisonChartCtx;
    if (!ctx) return;
    const {{ active, commonBenchmarks, commonPeriod, portfolioColors }} = ctx;
    if (tabKey === "returnRisk") {{
      this.renderSummaryScatter("rsv-summary-risk", "volatility", "Annualized Volatility (%)", active, commonBenchmarks, commonPeriod);
      this.renderSummaryScatter("rsv-summary-dd", "maxDrawdown", "Maximum Drawdown (%)", active, commonBenchmarks, commonPeriod);
    }} else if (tabKey === "growthDD") {{
      this.renderSummaryGrowth(active, portfolioColors, commonPeriod, !!this._comparisonGrowthLinear);
      this.renderSummaryDrawdown(active, portfolioColors, commonPeriod);
    }} else if (tabKey === "rollingReturns") {{
      this.renderSummaryRolling(active, portfolioColors, commonPeriod, this._comparisonRollingMonths || 36);
    }} else if (tabKey === "calendarYear") {{
      this.renderSummaryCalendar(active, portfolioColors, commonPeriod);
      this.renderSummaryCalendarDD(active, portfolioColors, commonPeriod);
    }}
  }},

  renderSummaryGrowth(activePortfolios, colors, commonPeriod, useLinear) {{
    const canvas = document.getElementById("rsv-summary-growth");
    if (!canvas) return;
    if (this._charts["rsv-summary-growth"]) this._charts["rsv-summary-growth"].destroy();

    const commonStart = commonPeriod.start;
    const commonEnd = commonPeriod.end;

    // Build aligned growth series for each portfolio
    const allDates = INDEX_DATA.dates;
    const startIdx = allDates.indexOf(commonStart);
    const endIdx = allDates.indexOf(commonEnd);
    const labels = allDates.slice(startIdx, endIdx + 1);

    const datasets = [];
    for (let idx = 0; idx < activePortfolios.length; idx++) {{
      const i = activePortfolios[idx];
      const p = state.portfolios[i];
      const r = p.result;
      const color = colors[idx % colors.length];

      // Find where commonStart falls in this portfolio's dates
      const pStartIdx = r.dates.indexOf(commonStart);
      const pEndIdx = r.dates.indexOf(commonEnd);
      if (pStartIdx < 0 || pEndIdx < 0) continue;

      // Re-base growth to 1 at commonStart
      const baseVal = r.stackedGrowth[pStartIdx];
      const rebasedGrowth = [];
      for (let j = pStartIdx; j <= pEndIdx; j++) {{
        rebasedGrowth.push(r.stackedGrowth[j] / baseVal);
      }}

      datasets.push({{
        label: p.name,
        data: rebasedGrowth,
        borderColor: color,
        backgroundColor: "transparent",
        fill: false,
        borderWidth: 2,
        pointRadius: 0,
        pointHitRadius: 6,
      }});
    }}

    this._charts["rsv-summary-growth"] = new Chart(canvas.getContext("2d"), {{
      type: "line",
      data: {{ labels, datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: "index", intersect: false }},
        plugins: {{
          legend: {{ display: true, position: "top" }},
          tooltip: {{
            callbacks: {{ title: (items) => items[0].label, label: (item) => `${{item.dataset.label}}: $${{item.parsed.y.toFixed(2)}}` }},
          }},
        }},
        scales: {{
          x: {{
            type: "category",
            ticks: {{
              color: "#555",
              maxTicksLimit: 12,
              maxRotation: 35,
              minRotation: 35,
              autoSkip: true,
              callback: function(v) {{
                const l = this.getLabelForValue(v);
                if (!l) return "";
                const parts = l.split("-");
                return parts.length >= 2 ? parts[1] + "/" + parts[0] : l.substring(0,4);
              }},
            }},
            grid: {{ display: false }},
          }},
          y: {{ type: useLinear ? "linear" : "logarithmic", title: {{ display: true, text: useLinear ? "Growth of $1" : "Growth of $1 (log)", font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => "$" + v.toFixed(1) }} }},
        }},
      }},
    }});
  }},

  renderSummaryCalendar(activePortfolios, colors, commonPeriod) {{
    const canvas = document.getElementById("rsv-summary-calendar");
    if (!canvas) return;
    if (this._charts["rsv-summary-calendar"]) this._charts["rsv-summary-calendar"].destroy();

    const commonStart = commonPeriod.start;
    const commonEnd = commonPeriod.end;

    // Compute calendar year returns only from common date range
    const portfolioYearData = [];
    let latestStartYear = 0;
    let earliestEndYear = 9999;

    for (const i of activePortfolios) {{
      const r = state.portfolios[i].result;
      const yearReturns = {{}};
      let curYear = null;
      let ytd = 1;
      let firstYear = null;
      let lastYear = null;

      for (let m = 0; m < r.stackedReturns.length; m++) {{
        const date = r.dates[m + 1];
        // Only include months within common range
        if (date <= commonStart || date > commonEnd) continue;
        const year = parseInt(date.substring(0, 4));
        if (curYear !== null && year !== curYear) {{
          yearReturns[curYear] = (ytd - 1) * 100;
          if (!firstYear) firstYear = curYear;
          lastYear = curYear;
          ytd = 1;
        }}
        curYear = year;
        ytd *= (1 + r.stackedReturns[m]);
      }}
      if (curYear !== null) {{
        yearReturns[curYear] = (ytd - 1) * 100;
        if (!firstYear) firstYear = curYear;
        lastYear = curYear;
      }}
      portfolioYearData.push(yearReturns);
      if (firstYear > latestStartYear) latestStartYear = firstYear;
      if (lastYear < earliestEndYear) earliestEndYear = lastYear;
    }}

    const years = [];
    for (let y = latestStartYear; y <= earliestEndYear; y++) years.push(y);
    const datasets = [];
    for (let idx = 0; idx < activePortfolios.length; idx++) {{
      const i = activePortfolios[idx];
      const color = colors[idx % colors.length];
      datasets.push({{
        label: state.portfolios[i].name,
        data: years.map(y => portfolioYearData[idx][y] || 0),
        backgroundColor: color,
        borderRadius: 2,
      }});
    }}

    this._charts["rsv-summary-calendar"] = new Chart(canvas.getContext("2d"), {{
      type: "bar",
      data: {{ labels: years.map(String), datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: true, position: "top" }},
          tooltip: {{
            callbacks: {{ label: (item) => `${{item.dataset.label}}: ${{item.parsed.y >= 0 ? "+" : ""}}${{item.parsed.y.toFixed(2)}}%` }},
          }},
        }},
        scales: {{
          x: {{ ticks: {{ color: "#555", maxRotation: 45 }}, grid: {{ display: false }} }},
          y: {{ ticks: {{ color: "#555", callback: (v) => v.toFixed(0) + "%" }} }},
        }},
      }},
    }});
  }},

  // Drawdown line chart per portfolio (stacked returns) over the common period
  renderSummaryDrawdown(activePortfolios, colors, commonPeriod) {{
    const canvas = document.getElementById("rsv-summary-drawdown");
    if (!canvas) return;
    if (this._charts["rsv-summary-drawdown"]) this._charts["rsv-summary-drawdown"].destroy();

    const commonStart = commonPeriod.start;
    const commonEnd = commonPeriod.end;
    const allDates = INDEX_DATA.dates;
    const startIdx = allDates.indexOf(commonStart);
    const endIdx = allDates.indexOf(commonEnd);
    const labels = allDates.slice(startIdx, endIdx + 1);

    const longestDD = (ddArr) => {{
      let maxLen = 0, curLen = 0, bestStart = 0, bestEnd = 0, curStart = 0;
      for (let i = 0; i < ddArr.length; i++) {{
        if (ddArr[i] < 0) {{
          if (curLen === 0) curStart = i;
          curLen++;
          if (curLen > maxLen) {{ maxLen = curLen; bestStart = curStart; bestEnd = i; }}
        }} else {{ curLen = 0; }}
      }}
      return {{ months: maxLen, startIdx: bestStart, endIdx: bestEnd }};
    }};

    const datasets = [];
    const statsRows = [];
    for (let idx = 0; idx < activePortfolios.length; idx++) {{
      const i = activePortfolios[idx];
      const p = state.portfolios[i];
      const r = p.result;
      const color = colors[idx % colors.length];

      const pStartIdx = r.dates.indexOf(commonStart);
      const pEndIdx = r.dates.indexOf(commonEnd);
      if (pStartIdx < 0 || pEndIdx < 0) continue;

      // Re-base growth to 1 at commonStart and compute drawdown %
      const baseVal = r.stackedGrowth[pStartIdx];
      const dd = [];
      let peak = 1;
      for (let j = pStartIdx; j <= pEndIdx; j++) {{
        const g = r.stackedGrowth[j] / baseVal;
        if (g > peak) peak = g;
        dd.push(((g - peak) / peak) * 100);
      }}

      datasets.push({{
        label: p.name,
        data: dd,
        borderColor: color,
        backgroundColor: this._hexToRgba(color, 0.12),
        fill: true,
        borderWidth: 1.5,
        pointRadius: 0,
        pointHitRadius: 6,
      }});

      const maxDD = Math.min(...dd);
      const longest = longestDD(dd);
      const labelsAligned = labels.slice(0, dd.length);
      const startLbl = labelsAligned[longest.startIdx] || "";
      const endLbl = labelsAligned[longest.endIdx] || "";
      statsRows.push(`<span style="color:${{color}};font-weight:600;">${{p.name}}</span> &mdash; Max DD: <span class="neg">${{maxDD.toFixed(2)}}%</span> &middot; Longest DD: <span class="neg">${{longest.months}} months</span> (${{startLbl}} &ndash; ${{endLbl}})`);
    }}

    this._charts["rsv-summary-drawdown"] = new Chart(canvas.getContext("2d"), {{
      type: "line",
      data: {{ labels, datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: "index", intersect: false }},
        plugins: {{
          legend: {{ display: true, position: "top" }},
          tooltip: {{
            callbacks: {{ title: (items) => items[0].label, label: (item) => `${{item.dataset.label}}: ${{item.parsed.y.toFixed(2)}}%` }},
          }},
        }},
        scales: {{
          x: {{
            type: "category",
            ticks: {{
              color: "#555", maxTicksLimit: 12, maxRotation: 35, minRotation: 35, autoSkip: true,
              callback: function(v) {{ const l = this.getLabelForValue(v); if (!l) return ""; const parts = l.split("-"); return parts.length >= 2 ? parts[1] + "/" + parts[0] : l.substring(0,4); }},
            }},
            grid: {{ display: false }},
          }},
          y: {{ title: {{ display: true, text: "Drawdown (%)", font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(0) + "%" }} }},
        }},
      }},
    }});

    const statsEl = document.getElementById("rsv-comp-stats-growthDD");
    if (statsEl && statsRows.length) {{
      statsEl.style.display = "block";
      statsEl.innerHTML = statsRows.join("<br>");
    }}
  }},

  // Rolling annualized returns per portfolio (stacked returns) over the common period
  renderSummaryRolling(activePortfolios, colors, commonPeriod, months) {{
    const canvas = document.getElementById("rsv-summary-rolling");
    if (!canvas) return;
    if (this._charts["rsv-summary-rolling"]) this._charts["rsv-summary-rolling"].destroy();

    const commonStart = commonPeriod.start;
    const commonEnd = commonPeriod.end;
    const allDates = INDEX_DATA.dates;
    const startIdx = allDates.indexOf(commonStart);
    const endIdx = allDates.indexOf(commonEnd);
    const labels = allDates.slice(startIdx, endIdx + 1);

    const datasets = [];
    const statsRows = [];
    let rollingLabels = labels;
    for (let idx = 0; idx < activePortfolios.length; idx++) {{
      const i = activePortfolios[idx];
      const p = state.portfolios[i];
      const r = p.result;
      const color = colors[idx % colors.length];

      const pStartIdx = r.dates.indexOf(commonStart);
      const pEndIdx = r.dates.indexOf(commonEnd);
      if (pStartIdx < 0 || pEndIdx < 0) continue;

      // Re-base growth to 1 at commonStart
      const baseVal = r.stackedGrowth[pStartIdx];
      const rebased = [];
      for (let j = pStartIdx; j <= pEndIdx; j++) rebased.push(r.stackedGrowth[j] / baseVal);

      if (rebased.length <= months) continue;
      const rolling = [];
      for (let j = months; j < rebased.length; j++) {{
        rolling.push((Math.pow(rebased[j] / rebased[j - months], 12 / months) - 1) * 100);
      }}

      datasets.push({{
        label: p.name,
        data: rolling,
        borderColor: color,
        backgroundColor: "transparent",
        fill: false,
        borderWidth: 2,
        pointRadius: 0,
        pointHitRadius: 6,
      }});

      const positiveCount = rolling.filter(v => v > 0).length;
      const positivePct = rolling.length ? (positiveCount / rolling.length * 100).toFixed(1) : "0.0";
      const minR = rolling.length ? Math.min(...rolling).toFixed(2) : "-";
      const maxR = rolling.length ? Math.max(...rolling).toFixed(2) : "-";
      statsRows.push(`<span style="color:${{color}};font-weight:600;">${{p.name}}</span> &mdash; Positive in <span class="hl">${{positivePct}}%</span> of ${{months}}-month windows &middot; Range: <span>${{minR}}% to ${{maxR}}%</span>`);
      rollingLabels = labels.slice(months);
    }}

    this._charts["rsv-summary-rolling"] = new Chart(canvas.getContext("2d"), {{
      type: "line",
      data: {{ labels: rollingLabels, datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: "index", intersect: false }},
        plugins: {{
          legend: {{ display: true, position: "top" }},
          tooltip: {{
            callbacks: {{ title: (items) => items[0].label, label: (item) => `${{item.dataset.label}}: ${{item.parsed.y.toFixed(2)}}%` }},
          }},
          annotation: {{
            annotations: {{
              zeroLine: {{ type: "line", yMin: 0, yMax: 0, borderColor: "#323A46", borderWidth: 2 }},
            }},
          }},
        }},
        scales: {{
          x: {{
            type: "category",
            ticks: {{
              color: "#555", maxTicksLimit: 12, maxRotation: 35, minRotation: 35, autoSkip: true,
              callback: function(v) {{ const l = this.getLabelForValue(v); if (!l) return ""; const parts = l.split("-"); return parts.length >= 2 ? parts[1] + "/" + parts[0] : l.substring(0,4); }},
            }},
            grid: {{ display: false }},
          }},
          y: {{ title: {{ display: true, text: months + "-Month Rolling Annualized Return (%)", font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(0) + "%" }} }},
        }},
      }},
    }});

    const statsEl = document.getElementById("rsv-comp-stats-rolling");
    if (statsEl && statsRows.length) {{
      statsEl.style.display = "block";
      statsEl.innerHTML = statsRows.join("<br>");
    }}
  }},

  // Intra-year max drawdown bar chart per portfolio (stacked returns) over the common period
  renderSummaryCalendarDD(activePortfolios, colors, commonPeriod) {{
    const canvas = document.getElementById("rsv-summary-calendar-dd");
    if (!canvas) return;
    if (this._charts["rsv-summary-calendar-dd"]) this._charts["rsv-summary-calendar-dd"].destroy();

    const commonStart = commonPeriod.start;
    const commonEnd = commonPeriod.end;

    const portfolioYearDD = [];
    let latestStartYear = 0;
    let earliestEndYear = 9999;

    for (const i of activePortfolios) {{
      const r = state.portfolios[i].result;
      const yearDD = {{}};
      let curYear = null;
      let g = 1, peak = 1, maxDD = 0;
      let firstYear = null, lastYear = null;

      for (let m = 0; m < r.stackedReturns.length; m++) {{
        const date = r.dates[m + 1];
        if (date <= commonStart || date > commonEnd) continue;
        const year = parseInt(date.substring(0, 4));
        if (curYear !== null && year !== curYear) {{
          yearDD[curYear] = -maxDD * 100;
          if (!firstYear) firstYear = curYear;
          lastYear = curYear;
          peak = g;
          maxDD = 0;
        }}
        curYear = year;
        g *= (1 + r.stackedReturns[m]);
        if (g > peak) peak = g;
        const dd = (peak - g) / peak;
        if (dd > maxDD) maxDD = dd;
      }}
      if (curYear !== null) {{
        yearDD[curYear] = -maxDD * 100;
        if (!firstYear) firstYear = curYear;
        lastYear = curYear;
      }}
      portfolioYearDD.push(yearDD);
      if (firstYear > latestStartYear) latestStartYear = firstYear;
      if (lastYear < earliestEndYear) earliestEndYear = lastYear;
    }}

    const years = [];
    for (let y = latestStartYear; y <= earliestEndYear; y++) years.push(y);
    const datasets = [];
    for (let idx = 0; idx < activePortfolios.length; idx++) {{
      const i = activePortfolios[idx];
      const color = colors[idx % colors.length];
      datasets.push({{
        label: state.portfolios[i].name,
        data: years.map(y => portfolioYearDD[idx][y] || 0),
        backgroundColor: color,
        borderRadius: 2,
      }});
    }}

    this._charts["rsv-summary-calendar-dd"] = new Chart(canvas.getContext("2d"), {{
      type: "bar",
      data: {{ labels: years.map(String), datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: true, position: "top" }},
          tooltip: {{
            callbacks: {{ label: (item) => `${{item.dataset.label}}: ${{item.parsed.y.toFixed(2)}}%` }},
          }},
        }},
        scales: {{
          x: {{ ticks: {{ color: "#555", maxRotation: 45 }}, grid: {{ display: false }} }},
          y: {{ title: {{ display: true, text: "Calendar Year Max Drawdown (%)", font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(0) + "%" }} }},
        }},
      }},
    }});
  }},

  _hexToRgba(hex, alpha) {{
    const h = hex.replace("#", "");
    const full = h.length === 3 ? h.split("").map(c => c + c).join("") : h;
    const r = parseInt(full.substring(0, 2), 16);
    const g = parseInt(full.substring(2, 4), 16);
    const b = parseInt(full.substring(4, 6), 16);
    return `rgba(${{r}}, ${{g}}, ${{b}}, ${{alpha}})`;
  }},

  _hexToRgbArr(hex) {{
    const h = hex.replace("#", "");
    const full = h.length === 3 ? h.split("").map(c => c + c).join("") : h;
    return [parseInt(full.substring(0, 2), 16), parseInt(full.substring(2, 4), 16), parseInt(full.substring(4, 6), 16)];
  }},

  // ── Risk & Diversification Panel ──

  renderRiskDivPanel() {{
    this.destroyComparisonCharts();
    const container = document.getElementById("rsv-panels");

    // Compute all enabled portfolios
    const active = [];
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      if (!p.enabled) continue;
      if (!p.result) p.result = computePortfolio(p);
      if (p.result) active.push(i);
    }}

    if (active.length === 0) {{
      container.innerHTML = `<div class="rsv-panel">
        ${{this.renderComparisonSubTabs("riskDiv")}}
        <div style="text-align:center;color:var(--text-secondary);padding:40px;">No analyzed portfolios. Set up and analyze at least one portfolio first, or load a saved comparison.</div>
      </div>`;
      return;
    }}

    // Find common date range, then apply user filter
    const naturalRange = this._getComparisonCommonRange(active);
    const effectiveRange = this._applyComparisonDateRange(naturalRange);
    const commonStart = effectiveRange.start;
    const commonEnd = effectiveRange.end;

    // Recompute full stats over common period for each portfolio
    const commonCoreStats = {{}};
    const commonStackedStats = {{}};

    for (const i of active) {{
      const r = state.portfolios[i].result;
      commonCoreStats[i] = computeStats(r.coreReturns, r.dates, commonStart, commonEnd) || {{}};
      commonStackedStats[i] = computeStats(r.stackedReturns, r.dates, commonStart, commonEnd, !r.hasCore) || {{}};
    }}

    const fmt = (v, isPct) => isPct ? (v * 100).toFixed(2) + "%" : v.toFixed(4);
    const cls = (v, key) => {{
      if (["maxDrawdown","avgDrawdown","var95","cvar95","worstMonth","worstCalendarYear","worstRolling12"].includes(key)) return "negative";
      if (["volatility","skewness","kurtosis"].includes(key)) return "";
      return v >= 0 ? "positive" : "negative";
    }};

    const riskMetrics = [
      ["Volatility", "volatility", true],
      ["Skewness", "skewness", false],
      ["Kurtosis", "kurtosis", false],
      ["Sharpe Ratio", "sharpe", false],
      ["Sortino Ratio", "sortino", false],
      ["Calmar Ratio", "calmar", false],
      ["Tail Ratio", "tailRatio", false],
      ["Max Drawdown", "maxDrawdown", true],
      ["Average Drawdown", "avgDrawdown", true],
      ["1-Year 95% VaR", "var95", true],
      ["1-Year 95% CVaR", "cvar95", true],
      ["Worst Month", "worstMonth", true],
      ["Best Month", "bestMonth", true],
      ["Worst Calendar Year", "worstCalendarYear", true],
      ["Best Calendar Year", "bestCalendarYear", true],
      ["Worst 12 Months", "worstRolling12", true],
      ["Best 12 Months", "bestRolling12", true],
    ];

    const buildRiskTable = (title, getStats, csvName) => {{
      const csvFile = csvName || "Advanced-Statistics_" + title.replace(/[^\\w]+/g, "-");
      let h = `<div class="rsv-dl-section" style="margin-bottom:24px;padding-top:16px;">
        <div class="rsv-section-title"><span>${{title}}</span>
          <button class="rsv-dl-btn" onclick="RSV.downloadSectionCsv(this, '${{csvFile}}')" title="Download table as CSV">&#x2193; CSV</button>
        </div>
        <div style="overflow-x:auto;">
        <table class="rsv-results-table">
          <thead><tr><th style="text-align:left;">Metric</th>`;
      for (const i of active) {{
        h += `<th style="text-align:center;">${{state.portfolios[i].name}}</th>`;
      }}
      h += "</tr></thead><tbody>";
      for (const [label, key, isPct] of riskMetrics) {{
        h += `<tr><td style="text-align:left;">${{label}}</td>`;
        for (const i of active) {{
          const val = getStats(i)[key];
          if (val === undefined || val === null) {{
            h += '<td style="text-align:center;">-</td>';
          }} else {{
            h += `<td style="text-align:center;" class="${{cls(val, key)}}">${{fmt(val, isPct)}}</td>`;
          }}
        }}
        h += "</tr>";
      }}
      h += "</tbody></table></div></div>";
      return h;
    }};

    let html = '<div class="rsv-panel">';
    html += this.renderComparisonSubTabs("riskDiv");
    html += `<div class="rsv-page-title">Advanced Statistics</div>`;
    html += this.renderComparisonDateRangeBar(naturalRange);
    html += `<div style="font-size:12px;color:var(--text-secondary);margin-bottom:16px;">
      * Common Period: ${{commonStart}} to ${{commonEnd}}. For definitions, please see the Disclosures section below.
    </div>`;

    const stackedTableHtml = buildRiskTable("Stacked Portfolio", (i) => commonStackedStats[i], "Advanced-Statistics_Stacked-Portfolio");
    const coreTableHtml = buildRiskTable("Core Portfolio", (i) => commonCoreStats[i], "Advanced-Statistics_Core-Portfolio");

    const buildDiffTable = () => {{
      let h = `<div class="rsv-dl-section" style="margin-bottom:24px;padding-top:16px;">
        <div class="rsv-section-title"><span>Difference (Stacked - Core)</span>
          <button class="rsv-dl-btn" onclick="RSV.downloadSectionCsv(this, 'Advanced-Statistics_Difference')" title="Download table as CSV">&#x2193; CSV</button>
        </div>
        <div style="overflow-x:auto;">
        <table class="rsv-results-table">
          <thead><tr><th style="text-align:left;">Metric</th>`;
      for (const i of active) h += `<th style="text-align:center;">${{state.portfolios[i].name}}</th>`;
      h += "</tr></thead><tbody>";
      for (const [label, key, isPct] of riskMetrics) {{
        h += `<tr><td style="text-align:left;">${{label}}</td>`;
        for (const i of active) {{
          const diff = (commonStackedStats[i][key] || 0) - (commonCoreStats[i][key] || 0);
          const dCls = ["maxDrawdown","avgDrawdown","var95","cvar95","worstMonth","worstCalendarYear","worstRolling12","volatility"].includes(key)
            ? (diff < 0 ? "positive" : diff > 0 ? "negative" : "")
            : (diff > 0 ? "positive" : diff < 0 ? "negative" : "");
          h += `<td style="text-align:center;" class="${{dCls}}">${{diff >= 0 ? "+" : ""}}${{fmt(diff, isPct)}}</td>`;
        }}
        h += "</tr>";
      }}
      h += "</tbody></table></div></div>";
      return h;
    }};
    const diffTableHtml = buildDiffTable();

    // Tabbed tables: Stacked / Core / Difference
    const advTabs = [
      {{ key: "stacked", label: "Stacked Portfolio" }},
      {{ key: "core", label: "Core Portfolio" }},
      {{ key: "difference", label: "Difference" }},
    ];
    let activeAdvTab = this._activeAdvancedStatsTab || "stacked";
    if (!advTabs.some(t => t.key === activeAdvTab)) activeAdvTab = "stacked";
    this._activeAdvancedStatsTab = activeAdvTab;
    const _avCls = (k) => k === activeAdvTab ? "rsv-chart-tab active" : "rsv-chart-tab";

    html += `<div class="rsv-chart-area" style="margin-top:8px;">
      <div class="rsv-chart-tabs">`;
    for (const t of advTabs) {{
      html += `<button class="${{_avCls(t.key)}}" onclick="RSV.switchAdvancedStatsTab('${{t.key}}', this)">${{t.label}}</button>`;
    }}
    html += `</div>
      <div id="rsv-adv-stacked" style="display:${{activeAdvTab === 'stacked' ? 'block' : 'none'}};">${{stackedTableHtml}}</div>
      <div id="rsv-adv-core" style="display:${{activeAdvTab === 'core' ? 'block' : 'none'}};">${{coreTableHtml}}</div>
      <div id="rsv-adv-difference" style="display:${{activeAdvTab === 'difference' ? 'block' : 'none'}};">${{diffTableHtml}}</div>
    </div>`;

    // Dynamic merged disclaimer
    html += this.renderMergedDisclaimer(active, commonStart, commonEnd);

    html += '</div>';
    container.innerHTML = html;
  }},

  // ── Tracking Error Panel ──

  computeTrackingErrorBetween(returnsA, returnsB) {{
    // Annualized tracking error between two monthly return arrays
    const n = Math.min(returnsA.length, returnsB.length);
    if (n < 2) return 0;
    const diffs = [];
    for (let i = 0; i < n; i++) {{
      diffs.push((returnsA[i] || 0) - (returnsB[i] || 0));
    }}
    const mean = diffs.reduce((s, d) => s + d, 0) / n;
    const variance = diffs.reduce((s, d) => s + Math.pow(d - mean, 2), 0) / (n - 1);
    return Math.sqrt(variance) * Math.sqrt(12);
  }},

  _buildTrackingErrorMatrixHtml(active, commonStart, commonEnd) {{
    if (active.length < 2) {{
      return '<div style="text-align:center;color:var(--text-secondary);padding:40px;">At least two analyzed portfolios are needed to compute tracking error.</div>';
    }}
    const fmt = (v) => (v * 100).toFixed(2) + "%";
    const getAlignedStacked = (portfolioIdx) => {{
      const r = state.portfolios[portfolioIdx].result;
      const aligned = [];
      for (let m = 0; m < r.stackedReturns.length; m++) {{
        const date = r.dates[m + 1];
        if (date > commonStart && date <= commonEnd) aligned.push(r.stackedReturns[m]);
      }}
      return aligned;
    }};
    let h = `<div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px;">
      * For the Common Period: ${{commonStart}} to ${{commonEnd}}
    </div>
    <div class="rsv-dl-section" style="margin-bottom:24px;">
      <div class="rsv-section-title"><span>Stacked Portfolios -- Tracking Error Matrix</span>
        <button class="rsv-dl-btn" onclick="RSV.downloadSectionCsv(this, 'Tracking-Error-Matrix')" title="Download matrix as CSV">&#x2193; CSV</button>
      </div>
      <div style="overflow-x:auto;">
      <table class="rsv-results-table rsv-matrix">
        <thead><tr><th></th>`;
    for (const i of active) h += `<th>${{state.portfolios[i].name}}</th>`;
    h += "</tr></thead><tbody>";
    for (const i of active) {{
      h += `<tr><td style="font-weight:700;">${{state.portfolios[i].name}}</td>`;
      for (const j of active) {{
        if (i === j) {{
          h += '<td style="background:var(--section-gray);text-align:center;">-</td>';
        }} else {{
          const te = this.computeTrackingErrorBetween(getAlignedStacked(i), getAlignedStacked(j));
          h += `<td>${{fmt(te)}}</td>`;
        }}
      }}
      h += "</tr>";
    }}
    h += "</tbody></table></div></div>";
    return h;
  }},

  renderTrackingErrorPanel() {{
    this.destroyComparisonCharts();
    const container = document.getElementById("rsv-panels");

    const active = [];
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      if (!p.enabled) continue;
      if (!p.result) p.result = computePortfolio(p);
      if (p.result) active.push(i);
    }}

    if (active.length < 2) {{
      container.innerHTML = '<div class="rsv-panel" style="text-align:center;color:var(--text-secondary);padding:40px;">At least two analyzed portfolios are needed to compute tracking error. Set up and analyze your portfolios first.</div>';
      return;
    }}

    // Find common date range, then apply user filter
    const naturalRange = this._getComparisonCommonRange(active);
    const effectiveRange = this._applyComparisonDateRange(naturalRange);
    const commonStart = effectiveRange.start;
    const commonEnd = effectiveRange.end;

    const fmt = (v) => (v * 100).toFixed(2) + "%";

    // Extract aligned returns for a portfolio over the common date range
    const getAlignedReturns = (portfolioIdx, useStacked) => {{
      const r = state.portfolios[portfolioIdx].result;
      const returns = useStacked ? r.stackedReturns : r.coreReturns;
      const aligned = [];
      for (let m = 0; m < returns.length; m++) {{
        const date = r.dates[m + 1];
        if (date > commonStart && date <= commonEnd) {{
          aligned.push(returns[m]);
        }}
      }}
      return aligned;
    }};

    let html = '<div class="rsv-panel">';
    html += this.renderComparisonSubTabs("trackingError");
    html += `<div class="rsv-page-title">Tracking Error</div>`;
    html += this.renderComparisonDateRangeBar(naturalRange);
    html += `<div style="font-size:12px;color:var(--text-secondary);margin-bottom:16px;">
      * For the Common Period: ${{commonStart}} to ${{commonEnd}}
    </div>`;

    // Stacked Portfolios matrix only
    html += `<div class="rsv-dl-section" style="margin-bottom:24px;">
      <div class="rsv-section-title"><span>Stacked Portfolios -- Tracking Error Matrix</span>
        <button class="rsv-dl-btn" onclick="RSV.downloadSectionCsv(this, 'Tracking-Error-Matrix')" title="Download matrix as CSV">&#x2193; CSV</button>
      </div>
      <div style="overflow-x:auto;">
      <table class="rsv-results-table rsv-matrix">
        <thead><tr><th></th>`;
    for (const i of active) html += `<th>${{state.portfolios[i].name}}</th>`;
    html += "</tr></thead><tbody>";

    for (const i of active) {{
      html += `<tr><td style="font-weight:700;">${{state.portfolios[i].name}}</td>`;
      for (const j of active) {{
        if (i === j) {{
          html += '<td style="background:var(--section-gray);text-align:center;">-</td>';
        }} else {{
          const rA = getAlignedReturns(i, true);
          const rB = getAlignedReturns(j, true);
          const te = this.computeTrackingErrorBetween(rA, rB);
          html += `<td>${{fmt(te)}}</td>`;
        }}
      }}
      html += "</tr>";
    }}
    html += "</tbody></table></div></div>";

    // Dynamic merged disclaimer
    html += this.renderMergedDisclaimer(active, commonStart, commonEnd);

    html += '</div>';
    container.innerHTML = html;
  }},

  // ── Custom Data Upload Panel ──

  renderCustomUploadPanel() {{
    const container = document.getElementById("rsv-panels");

    let html = '<div class="rsv-panel">';
    html += `<div class="rsv-section-title">Custom Data Upload</div>
      <p style="font-size:13px;color:var(--text-secondary);margin-bottom:16px;max-width:840px;">
        Add your own monthly series as custom asset classes. Upload a <strong>CSV or Excel (.xlsx)</strong> file, or
        paste rows straight from a spreadsheet. We auto-detect the date column and whether each series is a
        <strong>price level</strong> or <strong>returns</strong> &mdash; you can adjust before importing. Imported
        assets appear under the "Custom" category in the asset dropdown.
      </p>

      <div class="rsv-two-col" style="align-items:stretch;">
        <div class="rsv-dropzone" id="rsv-dropzone" style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
          <input type="file" id="rsv-file" accept=".csv,.tsv,.txt,.xlsx" style="display:none;">
          <div style="font-size:14px;color:var(--text-primary);"><strong>Drop a CSV or Excel file here</strong>, or <span class="rsv-linklike">browse</span></div>
          <div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">.csv &middot; .tsv &middot; .txt &middot; .xlsx &middot; up to 10 series</div>
        </div>
        <div style="display:flex;flex-direction:column;">
          <div style="font-size:12px;color:var(--text-secondary);margin-bottom:4px;">Or paste rows straight from Excel / Google Sheets:</div>
          <textarea id="rsv-paste" placeholder="Date&#9;My Strategy&#10;2020-01-31&#9;0.021&#10;2020-02-29&#9;-0.014&#10;..." style="flex:1;min-height:120px;width:100%;font-family:inherit;font-size:12px;padding:8px 10px;border:1px solid var(--border-gray);border-radius:4px;box-sizing:border-box;resize:vertical;"></textarea>
        </div>
      </div>

      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:16px;">
        <button class="rsv-compute-btn rsv-compute-btn--no-mt" onclick="RSV.readPastedData()">Upload Data</button>
        <button class="rsv-add-btn" onclick="RSV.downloadTemplate()">Download Template CSV</button>
        <span style="font-size:12px;color:var(--text-secondary);">Dates: 2020-01-31, Jan 2020, or 1/31/2020. Values: prices or returns (decimal or %).</span>
      </div>

      <div id="rsv-upload-status" style="margin-top:12px;"></div>
      <div id="rsv-import-review" style="margin-top:16px;"></div>`;

    // Show currently loaded custom assets
    const customAssets = (ASSET_CATEGORIES["Custom"] || []);
    if (customAssets.length > 0) {{
      html += `<div style="margin-top:24px;">
        <div class="rsv-section-title">Loaded Custom Assets</div>
        <table class="rsv-results-table">
          <thead><tr><th>Asset Name</th><th>Start Date</th><th>Action</th></tr></thead><tbody>`;
      for (const a of customAssets) {{
        html += `<tr><td>${{a.shortName}}</td><td>${{a.startDate || "N/A"}}</td>
          <td><button class="rsv-remove-btn" onclick="RSV.removeCustomAsset('${{a.shortName.replace(/'/g, "\\\\'")}}')">Remove</button></td></tr>`;
      }}
      html += "</tbody></table></div>";
    }}

    html += '</div>';
    container.innerHTML = html;

    // Wire dropzone (click anywhere to browse, plus drag-and-drop)
    const dz = document.getElementById("rsv-dropzone");
    const fileInput = document.getElementById("rsv-file");
    dz.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {{ if (e.target.files[0]) this.handleCustomFile(e.target.files[0]); }});
    dz.addEventListener("dragover", (e) => {{ e.preventDefault(); dz.classList.add("rsv-dragover"); }});
    dz.addEventListener("dragleave", () => dz.classList.remove("rsv-dragover"));
    dz.addEventListener("drop", (e) => {{
      e.preventDefault();
      dz.classList.remove("rsv-dragover");
      if (e.dataTransfer.files[0]) this.handleCustomFile(e.dataTransfer.files[0]);
    }});

    // Restore any in-progress review after a re-render
    if (this._pendingImport) this._renderImportReview();
  }},

  downloadTemplate() {{
    const csv = "Date,My Strategy (returns),My Index (price)\\n2000-01-31,0.0125,100.00\\n2000-02-29,0.0210,102.10\\n2000-03-31,-0.0180,100.26\\n2000-04-30,0.0095,101.21\\n2000-05-31,0.0315,104.40\\n2000-06-30,-0.0025,104.14\\n2000-07-31,0.0150,105.70\\n2000-08-31,0.0080,106.55\\n2000-09-30,-0.0230,104.10\\n2000-10-31,0.0110,105.24\\n2000-11-30,-0.0060,104.61\\n2000-12-31,0.0275,107.49\\n2001-01-31,0.0130,108.89";
    const blob = new Blob([csv], {{ type: "text/csv" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "custom_data_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  }},

  // Dispatch an uploaded file (xlsx via native reader, else delimited text)
  handleCustomFile(file) {{
    const statusEl = document.getElementById("rsv-upload-status");
    if (statusEl) statusEl.innerHTML = '';
    const fail = (msg) => {{ if (statusEl) statusEl.innerHTML = '<div class="rsv-validation rsv-error">' + msg + '</div>'; }};
    if (/\\.xlsx$/i.test(file.name)) {{
      file.arrayBuffer().then(rsvXlsxToRows).then((rows) => this._ingestRows(rows)).catch((e) => fail(String(e.message || e)));
    }} else {{
      file.text().then((txt) => this._ingestRows(rsvParseDelimited(txt))).catch(() => fail('Could not read that file.'));
    }}
  }},

  readPastedData() {{
    const statusEl = document.getElementById("rsv-upload-status");
    const txt = document.getElementById("rsv-paste").value;
    if (!txt.trim()) {{
      statusEl.innerHTML = '<div class="rsv-validation rsv-error">Paste some rows first, or use the file upload above.</div>';
      return;
    }}
    this._ingestRows(rsvParseDelimited(txt));
  }},

  _ingestRows(rows) {{
    const statusEl = document.getElementById("rsv-upload-status");
    const res = rsvExtractTimeSeries(rows);
    if (res.error) {{
      this._pendingImport = null;
      statusEl.innerHTML = '<div class="rsv-validation rsv-error">' + res.error + '</div>';
      this._renderImportReview();
      return;
    }}
    if (res.series.length > 10) {{
      res.series = res.series.slice(0, 10);
      res.warnings.push('Only the first 10 series were kept.');
    }}
    this._pendingImport = res;
    statusEl.innerHTML = '';
    this._renderImportReview();
  }},

  _renderImportReview() {{
    const el = document.getElementById("rsv-import-review");
    if (!el) return;
    const imp = this._pendingImport;
    if (!imp) {{ el.innerHTML = ''; return; }}
    const first = imp.months[0], last = imp.months[imp.months.length - 1];
    const kindOpts = (sel) => {{
      const opts = [["ret_dec", "Returns (decimal, e.g. 0.02)"], ["ret_pct", "Returns (percent, e.g. 2%)"], ["price", "Price / index level"]];
      return opts.map(o => `<option value="${{o[0]}}"${{o[0] === sel ? " selected" : ""}}>${{o[1]}}</option>`).join("");
    }};
    let h = `<div style="border:1px solid var(--border-gray);border-radius:6px;padding:16px;">
      <div style="font-weight:700;color:var(--navy);margin-bottom:6px;">Review &amp; Import</div>
      <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">
        Date column: <strong>${{imp.dateColName}}</strong> &middot; ${{imp.months.length}} monthly rows &middot; ${{first}} to ${{last}}
      </div>`;
    imp.warnings.forEach(w => {{ h += `<div class="rsv-validation rsv-info" style="margin-bottom:8px;">${{w}}</div>`; }});
    h += `<table class="rsv-results-table"><thead><tr><th>Series Name</th><th>Interpret As</th><th style="text-align:center;">Points</th><th style="text-align:center;">First Value</th></tr></thead><tbody>`;
    imp.series.forEach((s, i) => {{
      const nonNull = s.values.filter(v => v !== null);
      const sample = nonNull.length ? nonNull[0] : "&mdash;";
      h += `<tr>
        <td><input type="text" value="${{String(s.name).replace(/"/g, "&quot;")}}" onchange="RSV._setSeriesName(${{i}}, this.value)" style="font-family:inherit;font-size:13px;padding:4px 8px;border:1px solid var(--border-gray);border-radius:4px;width:100%;box-sizing:border-box;"></td>
        <td><select onchange="RSV._setSeriesKind(${{i}}, this.value)" style="font-family:inherit;font-size:13px;padding:4px 8px;border:1px solid var(--border-gray);border-radius:4px;">${{kindOpts(s.kind)}}</select></td>
        <td style="text-align:center;">${{nonNull.length}}</td>
        <td style="text-align:center;">${{sample}}</td>
      </tr>`;
    }});
    h += `</tbody></table>
      <div style="display:flex;gap:8px;margin-top:14px;">
        <button class="rsv-compute-btn rsv-compute-btn--no-mt" onclick="RSV.importReviewedSeries()">Import ${{imp.series.length}} Series</button>
        <button class="rsv-add-btn" onclick="RSV.cancelImport()">Cancel</button>
      </div></div>`;
    el.innerHTML = h;
  }},

  _setSeriesName(i, val) {{ if (this._pendingImport) this._pendingImport.series[i].name = val; }},
  _setSeriesKind(i, val) {{ if (this._pendingImport) this._pendingImport.series[i].kind = val; }},
  cancelImport() {{
    this._pendingImport = null;
    const el = document.getElementById("rsv-import-review");
    if (el) el.innerHTML = '';
  }},

  // Convert one values array (per its kind) to the engine's {{start, values}} index format.
  _seriesToIndex(vals, kind, firstIdx) {{
    let returns, startIdx;
    if (kind === "price") {{
      // forward-fill gaps, derive month-over-month ratios; first obs is the anchor (no return)
      const filled = []; let last = null;
      for (const v of vals) {{ if (v !== null && !isNaN(v) && v > 0) last = v; filled.push(last); }}
      let f = filled.findIndex(v => v !== null);
      if (f < 0) return null;
      returns = [];
      for (let i = f + 1; i < filled.length; i++) {{
        returns.push((filled[i] && filled[i - 1]) ? (filled[i] / filled[i - 1] - 1) : 0);
      }}
      startIdx = firstIdx + f;  // anchor sits at the first price month
    }} else {{
      const scale = kind === "ret_pct" ? 0.01 : 1;
      let f = vals.findIndex(v => v !== null);
      if (f < 0) return null;
      returns = [];
      for (let i = f; i < vals.length; i++) returns.push(vals[i] === null ? 0 : vals[i] * scale);
      startIdx = firstIdx + f - 1;  // anchor sits one month before the first return
      if (startIdx < 0) {{ startIdx = 0; returns = returns.slice(1); }}  // series begins at grid month 0
    }}
    const values = [100];
    for (const r of returns) values.push(values[values.length - 1] * (1 + (r || 0)));
    return {{ start: startIdx, values: values }};
  }},

  importReviewedSeries() {{
    const imp = this._pendingImport;
    const statusEl = document.getElementById("rsv-upload-status");
    if (!imp) return;

    const allDates = INDEX_DATA.dates;
    const gridFirst = allDates[0].substring(0, 7);
    const gridLast = allDates[allDates.length - 1].substring(0, 7);

    // Trim months to the widget's grid range
    const keep = [];
    for (let i = 0; i < imp.months.length; i++) {{
      if (imp.months[i] >= gridFirst && imp.months[i] <= gridLast) keep.push(i);
    }}
    const droppedOut = imp.months.length - keep.length;
    if (keep.length < 12) {{
      statusEl.innerHTML = '<div class="rsv-validation rsv-error">After trimming to the widget\\'s range (' + gridFirst + ' to ' + gridLast + '), only ' + keep.length + ' month(s) remain. Need at least 12.</div>';
      return;
    }}
    const months = keep.map(i => imp.months[i]);

    // Require consecutive months (the engine assumes a contiguous monthly grid)
    for (let d = 1; d < months.length; d++) {{
      const py = parseInt(months[d - 1].substring(0, 4)), pm = parseInt(months[d - 1].substring(5, 7));
      const cy = parseInt(months[d].substring(0, 4)), cm = parseInt(months[d].substring(5, 7));
      if ((cy - py) * 12 + (cm - pm) !== 1) {{
        statusEl.innerHTML = '<div class="rsv-validation rsv-error">Data must be consecutive months. Gap between ' + months[d - 1] + ' and ' + months[d] + '. Fill the gap or upload a contiguous range.</div>';
        return;
      }}
    }}

    // Grid index of the first kept month
    let firstIdx = -1;
    for (let i = 0; i < allDates.length; i++) {{
      if (allDates[i].substring(0, 7) === months[0]) {{ firstIdx = i; break; }}
    }}
    if (firstIdx < 0) {{
      statusEl.innerHTML = '<div class="rsv-validation rsv-error">Could not align the first month to the widget grid.</div>';
      return;
    }}

    const added = [], skipped = [];
    imp.series.forEach(s => {{
      const name = String(s.name).trim();
      if (!name) {{ skipped.push("(unnamed)"); return; }}
      if (INDEX_MAP.some(a => a.shortName === name)) {{ skipped.push(name + " (name exists)"); return; }}
      const vals = keep.map(i => s.values[i]);
      if (vals.every(v => v === null)) {{ skipped.push(name + " (no data)"); return; }}
      const conv = this._seriesToIndex(vals, s.kind, firstIdx);
      if (!conv) {{ skipped.push(name + " (no data)"); return; }}
      const startDate = allDates[conv.start];
      INDEX_DATA.series[name] = {{ start: conv.start, values: conv.values }};
      INDEX_MAP.push({{ shortName: name, bloombergName: name, startDate: startDate, assetClass: "Custom" }});
      if (!ASSET_CATEGORIES["Custom"]) ASSET_CATEGORIES["Custom"] = [];
      ASSET_CATEGORIES["Custom"].push({{ shortName: name, bloombergName: name, startDate: startDate, assetClass: "Custom" }});
      added.push(name);
    }});

    if (added.length) {{
      let msg = `Added ${{added.length}} custom asset(s): ${{added.join(", ")}}.`;
      if (droppedOut > 0) msg += ` Trimmed ${{droppedOut}} month(s) outside ${{gridFirst}}\\u2013${{gridLast}}.`;
      if (skipped.length) msg += ` Skipped: ${{skipped.join(", ")}}.`;
      this._pendingImport = null;
      statusEl.innerHTML = `<div class="rsv-validation rsv-success">${{msg}}</div>`;
      setTimeout(() => this.renderCustomUploadPanel(), 1800);
    }} else {{
      statusEl.innerHTML = `<div class="rsv-validation rsv-error">Nothing imported.${{skipped.length ? " Skipped: " + skipped.join(", ") + "." : ""}}</div>`;
    }}
  }},

  removeCustomAsset(name) {{
    // Remove from INDEX_DATA
    delete INDEX_DATA.series[name];
    // Remove from INDEX_MAP
    const mapIdx = INDEX_MAP.findIndex(a => a.shortName === name);
    if (mapIdx >= 0) INDEX_MAP.splice(mapIdx, 1);
    // Remove from ASSET_CATEGORIES
    if (ASSET_CATEGORIES["Custom"]) {{
      const catIdx = ASSET_CATEGORIES["Custom"].findIndex(a => a.shortName === name);
      if (catIdx >= 0) ASSET_CATEGORIES["Custom"].splice(catIdx, 1);
    }}
    // Clean up any portfolios referencing this asset
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      let changed = false;
      for (const section of ["core", "stack"]) {{
        for (const row of p[section]) {{
          if (row.asset === name) {{
            row.asset = "";
            row.weight = 0;
            changed = true;
          }}
        }}
      }}
      if (changed) p.result = null;
    }}
    this.renderCustomUploadPanel();
  }},

  renderSummaryScatter(canvasId, xKey, xLabel, activePortfolios, benchmarks, commonPeriod) {{
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (this._charts[canvasId]) this._charts[canvasId].destroy();

    const isRisk = xKey === "volatility";

    // Frontier line (already computed over common period)
    const frontierData = benchmarks ? benchmarks.map(b => ({{
      x: isRisk ? b.vol : b.maxDD,
      y: b.annReturn,
    }})) : [];

    const datasets = [
      {{ label: "Equity/Bond Frontier", data: frontierData, borderColor: "#bfbfbf", backgroundColor: "#bfbfbf", borderWidth: 2, pointRadius: 5, pointStyle: "circle", pointBackgroundColor: "#bfbfbf", pointBorderColor: "#fff", pointBorderWidth: 1, showLine: true, fill: false, order: 10 }},
    ];

    // Add each portfolio (stacked only, stats recomputed over common period)
    const portfolioColors = ["#14CFA6", "#323A46", "#3A6A9C", "#0C7C64", "#7DA5CE", "#3BB823"];

    for (let idx = 0; idx < activePortfolios.length; idx++) {{
      const i = activePortfolios[idx];
      const p = state.portfolios[i];
      const r = p.result;
      const color = portfolioColors[idx % portfolioColors.length];

      // Recompute stats over common period
      const commonStats = computeStats(r.stackedReturns, r.dates, commonPeriod.start, commonPeriod.end, !r.hasCore);
      if (!commonStats) continue;

      datasets.push({{
        label: p.name,
        data: [{{ x: commonStats[xKey] * 100, y: commonStats.annualizedReturn * 100 }}],
        borderColor: color, backgroundColor: color,
        pointRadius: 8, pointStyle: "circle", pointBorderColor: "#fff", pointBorderWidth: 2,
        showLine: false, order: idx,
      }});
    }}

    const frontierPlugin = benchmarks ? [{{ id: "summaryLabels_" + canvasId, afterDatasetsDraw: (ch) => {{
      const fCtx = ch.ctx; const meta = ch.getDatasetMeta(0);
      fCtx.save(); fCtx.font = "600 11px 'DM Sans'"; fCtx.fillStyle = "#555"; fCtx.textAlign = "center";
      meta.data.forEach((point, idx) => {{ if (benchmarks[idx]) fCtx.fillText(benchmarks[idx].label, point.x, point.y - 10); }});
      fCtx.restore();
    }} }}] : [];

    this._charts[canvasId] = new Chart(canvas.getContext("2d"), {{
      type: "scatter", data: {{ datasets }}, plugins: frontierPlugin,
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: true, position: "top" }},
          tooltip: {{
            callbacks: {{
              title: (items) => items[0].dataset.label,
              label: (item) => [`${{xLabel.split(" (")[0]}}: ${{item.parsed.x.toFixed(2)}}%`, `Ann. Return: ${{item.parsed.y.toFixed(2)}}%`],
            }},
          }},
        }},
        scales: {{
          x: {{ grace: "10%", title: {{ display: true, text: xLabel, font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(0) + "%" }} }},
          y: {{ grace: "10%", title: {{ display: true, text: "Annualized Return (%)", font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(1) + "%" }} }},
        }},
      }},
    }});
  }},

  // ── Date Range Controls ──

  renderDateRangeBar(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const r = p.result;
    if (!r) return "";
    const fullStart = r.dates[0];
    const fullEnd = r.dates[r.dates.length - 1];
    const dr = p.dateRange;
    const fromVal = dr ? dr.start : fullStart;
    const toVal = dr ? dr.end : fullEnd;

    // Build year options from data range
    const startYear = parseInt(fullStart.substring(0, 4));
    const endYear = parseInt(fullEnd.substring(0, 4));
    let yearOpts = '<option value="">--</option>';
    for (let y = endYear; y >= startYear; y--) {{
      yearOpts += `<option value="${{y}}">${{y}}</option>`;
    }}

    return `<div class="rsv-date-range-bar">
      <label>Year</label>
      <select id="rsv-year-${{portfolioIdx}}" onchange="RSV.selectYear(${{portfolioIdx}}, this.value)">
        ${{yearOpts}}
      </select>
      <label>From</label>
      <input type="date" id="rsv-date-from-${{portfolioIdx}}" value="${{fromVal}}"
             min="${{fullStart}}" max="${{fullEnd}}"
             onchange="RSV.applyDateRange(${{portfolioIdx}})">
      <label>To</label>
      <input type="date" id="rsv-date-to-${{portfolioIdx}}" value="${{toVal}}"
             min="${{fullStart}}" max="${{fullEnd}}"
             onchange="RSV.applyDateRange(${{portfolioIdx}})">
      <button class="rsv-date-btn" onclick="RSV.resetDateRange(${{portfolioIdx}})">Reset</button>
      <div class="rsv-date-quick-btns">
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, '3M')">3M</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, '6M')">6M</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, 'YTD')">YTD</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, '1Y')">1Y</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, '3Y')">3Y</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, '5Y')">5Y</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, '10Y')">10Y</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, '20Y')">20Y</button>
        <button onclick="RSV.quickDateRange(${{portfolioIdx}}, 'All')">All</button>
      </div>
    </div>`;
  }},

  applyDateRange(portfolioIdx) {{
    const fromEl = document.getElementById(`rsv-date-from-${{portfolioIdx}}`);
    const toEl = document.getElementById(`rsv-date-to-${{portfolioIdx}}`);
    if (!fromEl || !toEl) return;
    const r = state.portfolios[portfolioIdx].result;
    if (!r) return;
    // Snap to nearest available date in the portfolio's dates array
    const snapDate = (target, dates) => {{
      let best = dates[0];
      for (const d of dates) {{
        if (d <= target) best = d;
      }}
      return best;
    }};
    const start = snapDate(fromEl.value, r.dates);
    const end = snapDate(toEl.value, r.dates);
    if (start >= end) return;
    state.portfolios[portfolioIdx].dateRange = {{ start, end }};
    this._refreshStatsContent(portfolioIdx);
  }},

  resetDateRange(portfolioIdx) {{
    state.portfolios[portfolioIdx].dateRange = null;
    this._refreshStatsContent(portfolioIdx);
  }},

  selectYear(portfolioIdx, yearStr) {{
    if (!yearStr) return;
    const year = parseInt(yearStr);
    const r = state.portfolios[portfolioIdx].result;
    if (!r) return;
    const fromEl = document.getElementById(`rsv-date-from-${{portfolioIdx}}`);
    const toEl = document.getElementById(`rsv-date-to-${{portfolioIdx}}`);
    if (!fromEl || !toEl) return;
    // Find first and last date in that year from the portfolio's dates
    let firstInYear = null, lastInYear = null;
    for (const d of r.dates) {{
      const y = parseInt(d.substring(0, 4));
      if (y === year) {{
        if (!firstInYear) firstInYear = d;
        lastInYear = d;
      }}
    }}
    if (firstInYear && lastInYear) {{
      // Set from to the date before the first month of the year (so that month is included)
      const idx = r.dates.indexOf(firstInYear);
      fromEl.value = idx > 0 ? r.dates[idx - 1] : firstInYear;
      toEl.value = lastInYear;
      this.applyDateRange(portfolioIdx);
    }}
  }},

  quickDateRange(portfolioIdx, period) {{
    const r = state.portfolios[portfolioIdx].result;
    if (!r) return;
    const fullEnd = r.dates[r.dates.length - 1];
    const fullStart = r.dates[0];

    if (period === "All") {{
      this.resetDateRange(portfolioIdx);
      return;
    }}

    // Parse end date
    const endParts = fullEnd.split("-");
    let ey = parseInt(endParts[0]), em = parseInt(endParts[1]);

    let startDate;
    if (period === "YTD") {{
      // From Dec of previous year
      startDate = `${{ey - 1}}-12-31`;
    }} else {{
      const months = {{ "3M": 3, "6M": 6, "1Y": 12, "3Y": 36, "5Y": 60, "10Y": 120, "20Y": 240 }}[period] || 12;
      let sm = em - months;
      let sy = ey;
      while (sm <= 0) {{ sm += 12; sy--; }}
      const smStr = sm < 10 ? "0" + sm : "" + sm;
      startDate = `${{sy}}-${{smStr}}-01`;
    }}

    // Snap to nearest available date
    let snappedStart = fullStart;
    for (const d of r.dates) {{
      if (d <= startDate) snappedStart = d;
    }}
    if (snappedStart >= fullEnd) return;
    state.portfolios[portfolioIdx].dateRange = {{ start: snappedStart, end: fullEnd }};
    this._refreshStatsContent(portfolioIdx);
  }},

  _refreshStatsContent(portfolioIdx) {{
    this.destroyCharts(portfolioIdx);
    const statsEl = document.getElementById(`rsv-portfolio-stats-${{portfolioIdx}}`);
    if (statsEl) {{
      statsEl.innerHTML = this.renderPortfolioStatsContent(portfolioIdx);
      this.initCharts(portfolioIdx);
    }}
  }},

  renderPortfolioStats(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const r = p.result;
    if (!r) return "";
    let html = this.renderDateRangeBar(portfolioIdx);
    html += `<div id="rsv-portfolio-stats-${{portfolioIdx}}" class="rsv-animate-in">`;
    html += this.renderPortfolioStatsContent(portfolioIdx);
    html += `</div>`;
    return html;
  }},

  renderPortfolioStatsContent(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const r = p.result;
    if (!r) return "";

    const hasStack = p.stack.some(s => s.asset && s.weight > 0);
    const hasCore = r.hasCore !== false;
    const monthlyFee = (p.fee || 0) / 10000 / 12;

    // Determine stats to use: filtered or full
    let coreStats, stackedStats, periodStart, periodEnd, trackingErr;
    if (p.dateRange) {{
      const cs = computeStats(
        r.coreReturns.map(v => v - monthlyFee), r.dates, p.dateRange.start, p.dateRange.end);
      const ss = computeStats(
        r.stackedReturns.map(v => v - monthlyFee), r.dates, p.dateRange.start, p.dateRange.end, !hasCore);
      if (!cs || !ss) {{
        return '<div style="padding:16px;color:var(--text-secondary);">Not enough data in the selected date range. Try a wider range.</div>';
      }}
      coreStats = cs;
      stackedStats = ss;
      periodStart = p.dateRange.start;
      periodEnd = p.dateRange.end;
      // Recompute tracking error for this range
      const coreF = [], stackF = [];
      for (let m = 0; m < r.coreReturns.length; m++) {{
        const date = r.dates[m + 1];
        if (date > p.dateRange.start && date <= p.dateRange.end) {{
          coreF.push(r.coreReturns[m]);
          stackF.push(r.stackedReturns[m]);
        }}
      }}
      const diffR = coreF.map((c, i) => stackF[i] - c);
      const dMean = diffR.reduce((s, v) => s + v, 0) / diffR.length;
      const dVar = diffR.reduce((s, v) => s + Math.pow(v - dMean, 2), 0) / (diffR.length - 1);
      trackingErr = Math.sqrt(dVar) * Math.sqrt(12);
    }} else {{
      coreStats = r.coreStats;
      stackedStats = r.stackedStats;
      periodStart = r.period.start;
      periodEnd = r.period.end;
      trackingErr = r.trackingError;
    }}

    // Upside/Downside capture of the Stacked portfolio vs the Core (benchmark).
    // Morningstar method: over months where the benchmark (Core) is up (down),
    // compute each series' compound ANNUALIZED (geometric average) return, then
    // take the ratio stacked/core. Using annualized geometric means (not total
    // cumulative returns) keeps the ratio stable over long samples -- cumulative
    // ratios explode on the upside and saturate toward 100% on the downside.
    // Net of fee to match the stats shown above. Core-vs-itself is 1.00 (100%).
    let upsideCap = null, downsideCap = null;
    if (hasCore && hasStack) {{
      let capCore, capStack;
      if (p.dateRange) {{
        capCore = []; capStack = [];
        for (let m = 0; m < r.coreReturns.length; m++) {{
          const date = r.dates[m + 1];
          if (date > p.dateRange.start && date <= p.dateRange.end) {{
            capCore.push(r.coreReturns[m] - monthlyFee);
            capStack.push(r.stackedReturns[m] - monthlyFee);
          }}
        }}
      }} else {{
        capCore = r.coreReturns.map(v => v - monthlyFee);
        capStack = r.stackedReturns.map(v => v - monthlyFee);
      }}
      const capture = (up) => {{
        let coreProd = 1, stackProd = 1, count = 0;
        for (let i = 0; i < capCore.length; i++) {{
          if (up ? capCore[i] > 0 : capCore[i] < 0) {{
            coreProd *= (1 + capCore[i]);
            stackProd *= (1 + capStack[i]);
            count++;
          }}
        }}
        if (count === 0) return null;
        const coreAnn = Math.pow(coreProd, 12 / count) - 1;
        const stackAnn = Math.pow(stackProd, 12 / count) - 1;
        if (coreAnn === 0) return null;
        return stackAnn / coreAnn;
      }};
      upsideCap = capture(true);
      downsideCap = capture(false);
    }}

    const fmt = (v, isPct) => isPct ? (v * 100).toFixed(2) + "%" : v.toFixed(4);
    const cls = (v, key) => {{
      if (["maxDrawdown","avgDrawdown","var95","cvar95","worstMonth","worstCalendarYear","worstRolling12"].includes(key)) return "negative";
      if (["volatility","skewness","kurtosis"].includes(key)) return "";
      return v >= 0 ? "positive" : "negative";
    }};
    const diffCls = (v, key) => {{
      if (["maxDrawdown","avgDrawdown","var95","cvar95","worstMonth","worstCalendarYear","worstRolling12","volatility"].includes(key))
        return v < 0 ? "positive" : v > 0 ? "negative" : "";
      return v > 0 ? "positive" : v < 0 ? "negative" : "";
    }};

    const buildStatsTable = (title, metrics) => {{
      let h = `<div style="margin-top:24px;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div class="rsv-section-title" style="margin-bottom:0;">${{title}}</div>
        </div>
        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">
          ${{periodStart}} to ${{periodEnd}} &middot; Net of ${{(p.fee / 100).toFixed(2)}}% Fee
        </div>
        <table class="rsv-results-table">
          <thead><tr><th style="text-align:left;">Metric</th>`;
      if (hasCore) h += `<th style="text-align:center;">Core Portfolio</th>`;
      if (hasStack || !hasCore) h += `<th style="text-align:center;">${{!hasCore ? "Excess Return" : "Stacked Portfolio"}}</th>`;
      if (hasCore && hasStack) h += `<th style="text-align:center;">Difference</th>`;
      h += `</tr></thead><tbody>`;
      for (const [label, key, isPct] of metrics) {{
        const coreVal = coreStats[key];
        const stackVal = stackedStats[key];
        const diff = stackVal - coreVal;
        h += `<tr><td style="text-align:left;">${{label}}</td>`;
        if (hasCore) h += `<td style="text-align:center;" class="${{cls(coreVal, key)}}">${{fmt(coreVal, isPct)}}</td>`;
        if (hasStack || !hasCore) h += `<td style="text-align:center;" class="${{cls(stackVal, key)}}">${{fmt(stackVal, isPct)}}</td>`;
        if (hasCore && hasStack) {{
          h += `<td style="text-align:center;" class="${{diffCls(diff, key)}}">${{diff >= 0 ? "+" : ""}}${{fmt(diff, isPct)}}</td>`;
        }}
        h += "</tr>";
      }}
      if (title.includes("Summary") && hasCore && hasStack) {{
        // Upside/Downside capture rows. Core column is 100% by definition;
        // Stacked column shows the capture ratio; Difference = deviation from 100%.
        // goodHigh=true -> higher capture is better (upside); false -> lower is better (downside).
        const captureRow = (label, val, goodHigh) => {{
          if (val == null) {{
            return `<tr><td style="text-align:left;">${{label}}</td><td style="text-align:center;">100.00%</td><td style="text-align:center;">-</td><td style="text-align:center;">-</td></tr>`;
          }}
          const stackCls = (goodHigh ? val > 1 : val < 1) ? "positive" : (goodHigh ? val < 1 : val > 1) ? "negative" : "";
          const diff = (val - 1) * 100;
          const diffCls2 = (goodHigh ? diff > 0 : diff < 0) ? "positive" : (goodHigh ? diff < 0 : diff > 0) ? "negative" : "";
          return `<tr><td style="text-align:left;">${{label}}</td>`
            + `<td style="text-align:center;">100.00%</td>`
            + `<td style="text-align:center;" class="${{stackCls}}">${{(val * 100).toFixed(2)}}%</td>`
            + `<td style="text-align:center;" class="${{diffCls2}}">${{diff >= 0 ? "+" : ""}}${{diff.toFixed(2)}}%</td></tr>`;
        }};
        h += captureRow("Upside Capture", upsideCap, true);
        h += captureRow("Downside Capture", downsideCap, false);
        h += `<tr><td style="text-align:left;">Tracking Error</td><td style="text-align:center;">-</td><td style="text-align:center;">-</td><td style="text-align:center;">${{(trackingErr * 100).toFixed(2)}}%</td></tr>`;
      }}
      h += "</tbody></table></div>";
      return h;
    }};

    let html = "";

    // Summary Statistics
    html += buildStatsTable(`${{p.name}} -- Summary Statistics`, [
      ["Cumulative Return", "cumulativeReturn", true],
      ["Annualized Return", "annualizedReturn", true],
      ["Volatility", "volatility", true],
      ["Max Drawdown", "maxDrawdown", true],
      ["Sharpe Ratio", "sharpe", false],
      ["Sortino Ratio", "sortino", false],
    ]);

    // Charts
    const _act = RSV._activeChartType[portfolioIdx] || "growthDD";
    const _acls = (t) => t === _act ? "rsv-chart-tab active" : "rsv-chart-tab";
    html += `<div class="rsv-chart-area" style="margin-top:16px;">
      <div class="rsv-chart-tabs">
        <button class="${{_acls("growthDD")}}" onclick="RSV.switchChart(${{portfolioIdx}}, 'growthDD', this)">Growth &amp; Drawdowns</button>
        <button class="${{_acls("rollingReturns")}}" onclick="RSV.switchChart(${{portfolioIdx}}, 'rollingReturns', this)">Rolling Returns</button>
        <button class="${{_acls("calendarYear")}}" onclick="RSV.switchChart(${{portfolioIdx}}, 'calendarYear', this)">Calendar Year</button>
        ${{hasStack && hasCore ? '<button class="' + _acls("scaledBlend") + '" onclick="RSV.switchChart(' + portfolioIdx + ', &quot;scaledBlend&quot;, this)">Scaled Stack Blend</button>' : ''}}
        <button class="${{_acls("returnRisk")}}" onclick="RSV.switchChart(${{portfolioIdx}}, 'returnRisk', this)">Return &amp; Risk</button>
      </div>
      <div class="rsv-chart-controls" id="rsv-chart-controls-${{portfolioIdx}}" style="display:none;"></div>
      <div id="rsv-chart-panel-${{portfolioIdx}}">
        <div class="rsv-chart-container">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadPortfolioChart(${{portfolioIdx}}, 'a')" title="Download chart as PNG (disclosures download once per session)">&#x2193; PNG</button>
          <canvas id="rsv-chart-${{portfolioIdx}}-a"></canvas>
        </div>
        <div class="rsv-chart-stats" id="rsv-chart-stats-${{portfolioIdx}}-a" style="display:none;"></div>
        <div class="rsv-chart-container" id="rsv-chart-${{portfolioIdx}}-b-wrap" style="display:none;">
          <button class="rsv-dl-btn rsv-dl-btn--chart" onclick="RSV.downloadPortfolioChart(${{portfolioIdx}}, 'b')" title="Download chart as PNG (disclosures download once per session)">&#x2193; PNG</button>
          <canvas id="rsv-chart-${{portfolioIdx}}-b"></canvas>
        </div>
        <div class="rsv-chart-stats" id="rsv-chart-stats-${{portfolioIdx}}-b" style="display:none;"></div>
      </div>
    </div>`;

    // Calendar Year Returns Table (collapsible toggle below charts)
    const coreYears = coreStats.calendarYearReturns || {{}};
    const stackYears = stackedStats.calendarYearReturns || {{}};
    const allYears = [...new Set([...Object.keys(coreYears), ...Object.keys(stackYears)])].sort().reverse();

    if (allYears.length > 0) {{
      const calCsvName = ((state.portfolios[portfolioIdx].name) || ("Portfolio-" + (portfolioIdx + 1))) + "_Calendar-Year-Returns";
      html += `<div class="rsv-disclosures rsv-dl-section" style="margin-top:16px;position:relative;">
        <button class="rsv-disclosures-toggle" onclick="RSV.toggleDisclosures(this)">
          <span class="rsv-arrow">&#9654;</span> Calendar Year Returns Table
        </button>
        <button class="rsv-dl-btn" style="position:absolute;top:8px;right:12px;z-index:2;" onclick="event.stopPropagation(); RSV.downloadSectionCsv(this, '${{calCsvName}}');" title="Download Calendar Year Returns as CSV">&#x2193; CSV</button>
        <div class="rsv-disclosures-content">
          <div style="overflow-x:auto;">
          <table class="rsv-results-table">
            <thead><tr><th style="text-align:center;">Year</th><th style="text-align:center;">Core Portfolio</th>
            ${{hasStack ? "<th style=\\"text-align:center;\\">Stacked Portfolio</th><th style=\\"text-align:center;\\">Difference</th>" : ""}}
          </tr></thead><tbody>`;
      for (const yr of allYears) {{
        const coreRet = coreYears[yr] ? (coreYears[yr] - 1) * 100 : 0;
        const stackRet = stackYears[yr] ? (stackYears[yr] - 1) * 100 : 0;
        const diff = stackRet - coreRet;
        const retCls = (v) => v >= 0 ? "positive" : "negative";
        html += `<tr><td style="text-align:center;">${{yr}}</td><td style="text-align:center;" class="${{retCls(coreRet)}}">${{coreRet >= 0 ? "+" : ""}}${{coreRet.toFixed(2)}}%</td>`;
        if (hasStack) {{
          html += `<td style="text-align:center;" class="${{retCls(stackRet)}}">${{stackRet >= 0 ? "+" : ""}}${{stackRet.toFixed(2)}}%</td>
            <td style="text-align:center;font-weight:700;color:${{diff >= 0 ? 'var(--accent-green)' : 'var(--danger)'}}">${{diff >= 0 ? "+" : ""}}${{diff.toFixed(2)}}%</td>`;
        }}
        html += "</tr>";
      }}
      html += "</tbody></table></div></div></div>";
    }}

    // Dynamic portfolio disclaimer (collapsible, between calendar year and advanced fee)
    html += this.renderPortfolioDisclaimer(portfolioIdx);

    // Advanced Fee Configuration (collapsible, below results)
    html += this.renderAdvancedFeeConfig(portfolioIdx);

    return html;
  }},

  // ── Chart Rendering ──

  _charts: {{}},
  _sliderTimer: null,

  destroyCharts(portfolioIdx) {{
    const a = `rsv-chart-${{portfolioIdx}}-a`;
    const b = `rsv-chart-${{portfolioIdx}}-b`;
    if (this._charts[a]) {{ this._charts[a].destroy(); this._charts[a] = null; }}
    if (this._charts[b]) {{ this._charts[b].destroy(); this._charts[b] = null; }}
  }},

  destroyComparisonCharts() {{
    for (const key of Object.keys(this._charts)) {{
      if (key.startsWith("rsv-summary-") || key.startsWith("rsv-comp-") || key.startsWith("rsv-tracking-")) {{
        const inst = this._charts[key];
        if (inst && typeof inst.destroy === "function") {{
          try {{ inst.destroy(); }} catch (e) {{ console.warn("chart destroy failed", key, e); }}
        }}
        delete this._charts[key];
      }}
    }}
  }},

  switchChart(portfolioIdx, chartType, btn) {{
    const tabs = btn.parentElement;
    tabs.querySelectorAll(".rsv-chart-tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
    this.drawChart(portfolioIdx, chartType);
  }},

  switchComparisonTableTab(tabKey, btn) {{
    const tabs = btn.parentElement;
    tabs.querySelectorAll(".rsv-chart-tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
    this._activeComparisonTableTab = tabKey;
    for (const k of ["stacked", "core", "difference"]) {{
      const el = document.getElementById("rsv-comp-table-" + k);
      if (el) el.style.display = (k === tabKey) ? "block" : "none";
    }}
  }},

  switchAdvancedStatsTab(tabKey, btn) {{
    const tabs = btn.parentElement;
    tabs.querySelectorAll(".rsv-chart-tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
    this._activeAdvancedStatsTab = tabKey;
    for (const k of ["stacked", "core", "difference"]) {{
      const el = document.getElementById("rsv-adv-" + k);
      if (el) el.style.display = (k === tabKey) ? "block" : "none";
    }}
  }},

  switchComparisonChartTab(tabKey, btn) {{
    const tabs = btn.parentElement;
    tabs.querySelectorAll(".rsv-chart-tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
    this._activeComparisonChartTab = tabKey;
    for (const k of ["returnRisk", "growthDD", "rollingReturns", "calendarYear", "trackingError"]) {{
      const el = document.getElementById("rsv-comp-chart-" + k);
      if (el) el.classList.toggle("rsv-comp-chart-active", k === tabKey);
    }}
    requestAnimationFrame(() => {{ this._renderComparisonChartTab(tabKey); }});
  }},

  _benchmarkCache: null,

  getBenchmarkFrontier(dateRange) {{
    // Compute benchmarks for the same date range as the portfolio
    const allDates = INDEX_DATA.dates;
    const startIdx = allDates.indexOf(dateRange.start);
    const endIdx = allDates.indexOf(dateRange.end);
    if (startIdx < 0 || endIdx < 0) return null;

    const acwiInfo = INDEX_DATA.series["MSCI ACWI"];
    const aggInfo = INDEX_DATA.series["Bloomberg US Aggregate Bond"];
    const cashInfo = INDEX_DATA.series["Treasury Bill"];
    if (!acwiInfo || !aggInfo || !cashInfo) return null;

    // Cash for risk-free rate
    const cashReturns = [];
    for (let i = startIdx + 1; i <= endIdx; i++) {{
      const di = i - cashInfo.start;
      if (di > 0 && di < cashInfo.values.length) {{
        const prev = cashInfo.values[di - 1];
        const curr = cashInfo.values[di];
        cashReturns.push(prev && curr ? curr / prev - 1 : 0);
      }} else {{
        cashReturns.push(0);
      }}
    }}
    const rfAnn = (cashReturns.reduce((s, r) => s + r, 0) / cashReturns.length) * 12;

    const mixes = [[0,100],[20,80],[40,60],[60,40],[80,20],[100,0]];
    const points = [];

    for (const [eqPct, fiPct] of mixes) {{
      const returns = [];
      for (let i = startIdx + 1; i <= endIdx; i++) {{
        const adi = i - acwiInfo.start;
        const bdi = i - aggInfo.start;
        const eqR = (adi > 0 && adi < acwiInfo.values.length && acwiInfo.values[adi-1])
          ? acwiInfo.values[adi] / acwiInfo.values[adi-1] - 1 : 0;
        const fiR = (bdi > 0 && bdi < aggInfo.values.length && aggInfo.values[bdi-1])
          ? aggInfo.values[bdi] / aggInfo.values[bdi-1] - 1 : 0;
        returns.push((eqPct/100) * eqR + (fiPct/100) * fiR);
      }}
      const n = returns.length;
      const cumReturn = returns.reduce((p, r) => p * (1 + r), 1);
      const years = n / 12;
      const annReturn = Math.pow(cumReturn, 1/years) - 1;
      const mean = returns.reduce((s, r) => s + r, 0) / n;
      const variance = returns.reduce((s, r) => s + Math.pow(r - mean, 2), 0) / (n - 1);
      const vol = Math.sqrt(variance) * Math.sqrt(12);
      let peak = 1, maxDD = 0, g = 1;
      for (const r of returns) {{
        g *= (1 + r);
        if (g > peak) peak = g;
        const dd = (peak - g) / peak;
        if (dd > maxDD) maxDD = dd;
      }}
      points.push({{
        label: `${{eqPct}}/${{fiPct}}`,
        annReturn: annReturn * 100,
        vol: vol * 100,
        maxDD: maxDD * 100,
      }});
    }}
    return points;
  }},

  _activeChartType: {{}},
  _activeComparisonTableTab: "stacked",
  _activeComparisonChartTab: "growthDD",
  _comparisonChartCtx: null,
  _comparisonGrowthLinear: false,
  _comparisonRollingMonths: 36,

  // Build a filtered copy of the result object when a dateRange is active
  _getFilteredView(p) {{
    const r = p.result;
    const dr = p.dateRange;
    if (!r || !dr) return r;

    const dates = [dr.start];
    const coreReturns = [];
    const stackedReturns = [];
    for (let m = 0; m < r.coreReturns.length; m++) {{
      const d = r.dates[m + 1];
      if (d > dr.start && d <= dr.end) {{
        dates.push(d);
        coreReturns.push(r.coreReturns[m]);
        stackedReturns.push(r.stackedReturns[m]);
      }}
    }}
    // Rebuild growth-of-$1 arrays (net of portfolio fee, matching computePortfolio)
    const monthlyFee = (p.fee || 0) / 10000 / 12;
    const coreGrowth = [1];
    const stackedGrowth = [1];
    for (let i = 0; i < coreReturns.length; i++) {{
      coreGrowth.push(coreGrowth[i] * (1 + coreReturns[i] - monthlyFee));
      stackedGrowth.push(stackedGrowth[i] * (1 + stackedReturns[i] - monthlyFee));
    }}
    // Recompute stats
    const coreStats = computeStats(
      r.coreReturns.map(v => v - monthlyFee), r.dates, dr.start, dr.end) || r.coreStats;
    const stackedStats = computeStats(
      r.stackedReturns.map(v => v - monthlyFee), r.dates, dr.start, dr.end, !r.hasCore) || r.stackedStats;
    // Recompute tracking error
    const diffR = coreReturns.map((c, i) => stackedReturns[i] - c);
    const dMean = diffR.length > 1 ? diffR.reduce((s, v) => s + v, 0) / diffR.length : 0;
    const dVar = diffR.length > 1 ? diffR.reduce((s, v) => s + Math.pow(v - dMean, 2), 0) / (diffR.length - 1) : 0;
    const trackingError = Math.sqrt(dVar) * Math.sqrt(12);

    return {{
      dates, coreGrowth, stackedGrowth, coreReturns, stackedReturns,
      coreStats, stackedStats, trackingError,
      period: {{ start: dr.start, end: dr.end }},
    }};
  }},

  drawChart(portfolioIdx, chartType, options) {{
    const p = state.portfolios[portfolioIdx];
    const r = p.dateRange ? this._getFilteredView(p) : p.result;
    if (!r) return;

    this.destroyCharts(portfolioIdx);
    this._activeChartType[portfolioIdx] = chartType;
    const hasStack = p.stack.some(s => s.asset && s.weight > 0);
    const hasCore = p.result && p.result.hasCore !== false;

    const canvasA = document.getElementById(`rsv-chart-${{portfolioIdx}}-a`);
    const canvasB = document.getElementById(`rsv-chart-${{portfolioIdx}}-b`);
    const wrapB = document.getElementById(`rsv-chart-${{portfolioIdx}}-b-wrap`);
    const controlsEl = document.getElementById(`rsv-chart-controls-${{portfolioIdx}}`);
    if (!canvasA) return;

    // Hide second canvas by default, reset labels and stats
    if (wrapB) wrapB.style.display = "none";
    if (controlsEl) {{ controlsEl.style.display = "none"; controlsEl.innerHTML = ""; }}
    const statsAEl = document.getElementById(`rsv-chart-stats-${{portfolioIdx}}-a`);
    const statsBEl = document.getElementById(`rsv-chart-stats-${{portfolioIdx}}-b`);
    if (statsAEl) {{ statsAEl.style.display = "none"; statsAEl.innerHTML = ""; }}
    if (statsBEl) {{ statsBEl.style.display = "none"; statsBEl.innerHTML = ""; }}

    // Remove old labels, add new ones
    const panel = document.getElementById(`rsv-chart-panel-${{portfolioIdx}}`);
    if (panel) {{
      panel.querySelectorAll(".rsv-chart-label").forEach(el => el.remove());
      panel.classList.toggle("rsv-chart-panel--side-by-side", chartType === "returnRisk");
    }}
    const addLabel = (text, beforeEl) => {{
      const lbl = document.createElement("div");
      lbl.className = "rsv-chart-label";
      lbl.textContent = text;
      if (beforeEl && beforeEl.parentNode) beforeEl.parentNode.insertBefore(lbl, beforeEl);
    }};

    // Shared helpers
    const lineOpts = (yTitle, fmt) => ({{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: "index", intersect: false }},
      plugins: {{
        legend: {{ display: true, position: "top" }},
        tooltip: {{
          callbacks: {{ title: (items) => items[0].label, label: (item) => fmt(item) }},
        }},
      }},
      scales: {{
        x: {{
          type: "category",
          ticks: {{
            color: "#555",
            maxTicksLimit: 12,
            maxRotation: 35,
            minRotation: 35,
            autoSkip: true,
            callback: function(v) {{
              const l = this.getLabelForValue(v);
              if (!l) return "";
              const parts = l.split("-");
              return parts.length >= 2 ? parts[1] + "/" + parts[0] : l.substring(0,4);
            }},
          }},
          grid: {{ display: false }},
        }},
        y: {{
          title: {{ display: true, text: yTitle, font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }},
          ticks: {{ color: "#555" }},
        }},
      }},
    }});

    const coreLineDS = (data, fill) => ({{ label: "Core Portfolio", data, borderColor: "#323A46", backgroundColor: fill ? "rgba(50,58,70,0.12)" : "rgba(50,58,70,0.25)", fill, borderWidth: 2, pointRadius: 0, pointHitRadius: 6, pointBorderColor: "#323A46", pointBackgroundColor: "rgba(50,58,70,0.25)" }});
    const stackLineDS = (data, fill) => ({{ label: "Stacked Portfolio", data, borderColor: "#14CFA6", backgroundColor: fill ? "rgba(20,207,166,0.12)" : "rgba(20,207,166,0.25)", fill, borderWidth: 2, pointRadius: 0, pointHitRadius: 6, pointBorderColor: "#14CFA6", pointBackgroundColor: "rgba(20,207,166,0.25)" }});

    const computeDD = (growthArr) => {{
      const dd = []; let peak = growthArr[0];
      for (let i = 0; i < growthArr.length; i++) {{
        if (growthArr[i] > peak) peak = growthArr[i];
        dd.push(((growthArr[i] - peak) / peak) * 100);
      }}
      return dd;
    }};

    // ── Return & Risk (dual scatter: Return vs Volatility on top, Return vs Max DD below) ──
    if (chartType === "returnRisk") {{
      if (wrapB) wrapB.style.display = "block";
      const frontier = this.getBenchmarkFrontier(r.period);

      const buildScatterDS = (xKey, statKey) => {{
        const frontierData = frontier ? frontier.map(pt => ({{ x: pt[xKey], y: pt.annReturn }})) : [];
        const ds = [
          {{ label: "Equity/Bond Frontier", data: frontierData, borderColor: "#bfbfbf", backgroundColor: "#bfbfbf", borderWidth: 2, pointRadius: 5, pointStyle: "circle", pointBackgroundColor: "#bfbfbf", pointBorderColor: "#fff", pointBorderWidth: 1, showLine: true, fill: false, order: 2 }},
        ];
        if (hasCore) {{
          ds.push({{ label: "Core Portfolio", data: [{{ x: r.coreStats[statKey] * 100, y: r.coreStats.annualizedReturn * 100 }}], borderColor: "#323A46", backgroundColor: "#323A46", pointRadius: 8, pointStyle: "circle", pointBorderColor: "#fff", pointBorderWidth: 2, showLine: false, order: 1 }});
        }}
        if (hasStack || !hasCore) {{
          const lbl = !hasCore ? "Excess Return" : "Stacked Portfolio";
          ds.push({{ label: lbl, data: [{{ x: r.stackedStats[statKey] * 100, y: r.stackedStats.annualizedReturn * 100 }}], borderColor: "#14CFA6", backgroundColor: "#14CFA6", pointRadius: 8, pointStyle: "circle", pointBorderColor: "#fff", pointBorderWidth: 2, showLine: false, order: 0 }});
        }}
        return ds;
      }};

      const scatterOpts = (xLabel) => ({{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: true, position: "top" }},
          tooltip: {{
            callbacks: {{
              title: (items) => items[0].dataset.label,
              label: (item) => [`${{xLabel}}: ${{item.parsed.x.toFixed(2)}}%`, `Ann. Return: ${{item.parsed.y.toFixed(2)}}%`],
            }},
          }},
        }},
        scales: {{
          x: {{ grace: "10%", title: {{ display: true, text: xLabel, font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(0) + "%" }} }},
          y: {{ grace: "10%", title: {{ display: true, text: "Annualized Return (%)", font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(1) + "%" }} }},
        }},
      }});

      const frontierPlugin = (chartId) => frontier ? [{{ id: "fl_" + chartId, afterDatasetsDraw: (ch) => {{
        const fCtx = ch.ctx; const meta = ch.getDatasetMeta(0);
        fCtx.save(); fCtx.font = "600 11px 'DM Sans'"; fCtx.fillStyle = "#555"; fCtx.textAlign = "center";
        meta.data.forEach((point, idx) => {{ if (frontier[idx]) fCtx.fillText(frontier[idx].label, point.x, point.y - 10); }});
        fCtx.restore();
      }} }}] : [];

      // Return vs Risk (canvas A)
      addLabel("Return vs Risk", canvasA.parentNode);
      this._charts[`rsv-chart-${{portfolioIdx}}-a`] = new Chart(canvasA.getContext("2d"), {{
        type: "scatter", data: {{ datasets: buildScatterDS("vol", "volatility") }},
        plugins: frontierPlugin("a" + portfolioIdx),
        options: scatterOpts("Annualized Volatility (%)"),
      }});

      // Return vs Max DD (canvas B)
      addLabel("Return vs Drawdown", wrapB);
      this._charts[`rsv-chart-${{portfolioIdx}}-b`] = new Chart(canvasB.getContext("2d"), {{
        type: "scatter", data: {{ datasets: buildScatterDS("maxDD", "maxDrawdown") }},
        plugins: frontierPlugin("b" + portfolioIdx),
        options: scatterOpts("Maximum Drawdown (%)"),
      }});
      return;
    }}

    // ── Growth & Drawdowns (dual chart) ──
    if (chartType === "growthDD") {{
      const useLinear = options && options.linear;
      if (controlsEl) {{
        controlsEl.style.display = "flex";
        controlsEl.innerHTML = `<label><input type="checkbox" ${{useLinear ? "checked" : ""}} onchange="RSV.drawChart(${{portfolioIdx}}, 'growthDD', {{linear: this.checked}})"> Linear Scale</label>`;
      }}
      if (wrapB) wrapB.style.display = "block";

      // Growth chart (canvas A)
      addLabel("Growth of $1", canvasA.parentNode);
      const growthDS = [];
      if (hasCore) growthDS.push(coreLineDS(r.coreGrowth, false));
      if (hasStack || !hasCore) growthDS.push(!hasCore ? {{ ...stackLineDS(r.stackedGrowth, false), label: "Excess Return" }} : stackLineDS(r.stackedGrowth, false));
      const growthOpts = lineOpts("Growth of $1", (item) => `${{item.dataset.label}}: $${{item.parsed.y.toFixed(2)}}`);
      growthOpts.scales.y.type = useLinear ? "linear" : "logarithmic";
      growthOpts.scales.y.ticks.callback = (v) => "$" + v.toFixed(1);
      this._charts[`rsv-chart-${{portfolioIdx}}-a`] = new Chart(canvasA.getContext("2d"), {{
        type: "line", data: {{ labels: r.dates, datasets: growthDS }}, options: growthOpts,
      }});

      // Drawdown chart (canvas B)
      addLabel("Maximum Drawdown and Recovery", wrapB);
      const coreDD = computeDD(r.coreGrowth);
      const ddDS = [];
      if (hasCore) ddDS.push({{ ...coreLineDS(coreDD, true), borderWidth: 1.5 }});
      if (hasStack || !hasCore) {{
        const stackDD = computeDD(r.stackedGrowth);
        const stackDDds = {{ ...stackLineDS(stackDD, true), borderWidth: 1.5 }};
        if (!hasCore) stackDDds.label = "Excess Return";
        ddDS.push(stackDDds);
      }}
      const ddOpts = lineOpts("Drawdown (%)", (item) => `${{item.dataset.label}}: ${{item.parsed.y.toFixed(2)}}%`);
      ddOpts.scales.y.ticks.callback = (v) => v.toFixed(0) + "%";
      this._charts[`rsv-chart-${{portfolioIdx}}-b`] = new Chart(canvasB.getContext("2d"), {{
        type: "line", data: {{ labels: r.dates, datasets: ddDS }}, options: ddOpts,
      }});

      // Drawdown stats text
      const longestDD = (ddArr, dates) => {{
        let maxLen = 0, curLen = 0, curStart = 0, bestStart = 0, bestEnd = 0;
        for (let i = 0; i < ddArr.length; i++) {{
          if (ddArr[i] < 0) {{
            if (curLen === 0) curStart = i;
            curLen++;
            if (curLen > maxLen) {{ maxLen = curLen; bestStart = curStart; bestEnd = i; }}
          }} else {{ curLen = 0; }}
        }}
        return {{ months: maxLen, start: dates[bestStart] || "", end: dates[bestEnd] || "" }};
      }};
      const statsB = document.getElementById(`rsv-chart-stats-${{portfolioIdx}}-b`);
      if (statsB) {{
        statsB.style.display = "block";
        let ddText = "";
        if (hasCore) {{
          const coreMaxDD = Math.min(...coreDD);
          const coreLongest = longestDD(coreDD, r.dates);
          ddText = `Core Portfolio &mdash; Max drawdown: <span class="neg">${{coreMaxDD.toFixed(2)}}%</span> &middot; Longest drawdown: <span class="neg">${{coreLongest.months}} months</span> (${{coreLongest.start}} &ndash; ${{coreLongest.end}})`;
          if (hasStack) {{
            const stackDD2 = computeDD(r.stackedGrowth);
            const stackMaxDD = Math.min(...stackDD2);
            const stackLongest = longestDD(stackDD2, r.dates);
            ddText += `<br>Stacked Portfolio &mdash; Max drawdown: <span class="${{stackMaxDD > coreMaxDD ? "hl" : "neg"}}">${{stackMaxDD.toFixed(2)}}%</span> &middot; Longest drawdown: <span class="${{stackLongest.months < coreLongest.months ? "hl" : "neg"}}">${{stackLongest.months}} months</span> (${{stackLongest.start}} &ndash; ${{stackLongest.end}})`;
          }}
        }} else {{
          const exDD = computeDD(r.stackedGrowth);
          const exMaxDD = Math.min(...exDD);
          const exLongest = longestDD(exDD, r.dates);
          ddText = `Excess Return &mdash; Max drawdown: <span class="neg">${{exMaxDD.toFixed(2)}}%</span> &middot; Longest drawdown: <span class="neg">${{exLongest.months}} months</span> (${{exLongest.start}} &ndash; ${{exLongest.end}})`;
        }}
        statsB.innerHTML = ddText;
      }}
      return;
    }}

    // ── Calendar Year (dual bar chart) ──
    if (chartType === "calendarYear") {{
      if (wrapB) wrapB.style.display = "block";

      // Compute calendar year returns and max drawdowns
      const years = [];
      const coreYearReturns = [];
      const stackYearReturns = [];
      const coreYearDD = [];
      const stackYearDD = [];

      let curYear = null;
      let coreYTD = 1, stackYTD = 1;
      let corePeak = 1, stackPeak = 1, coreMaxDD = 0, stackMaxDD = 0;
      let coreG = 1, stackG = 1;

      for (let i = 0; i < r.coreReturns.length; i++) {{
        const date = r.dates[i + 1]; // dates[0] is start, returns start at index 0
        const year = parseInt(date.substring(0, 4));

        if (curYear !== null && year !== curYear) {{
          years.push(curYear);
          coreYearReturns.push((coreYTD - 1) * 100);
          stackYearReturns.push((stackYTD - 1) * 100);
          coreYearDD.push(-coreMaxDD * 100);
          stackYearDD.push(-stackMaxDD * 100);
          coreYTD = 1; stackYTD = 1;
          corePeak = coreG; stackPeak = stackG;
          coreMaxDD = 0; stackMaxDD = 0;
        }}
        curYear = year;

        coreYTD *= (1 + r.coreReturns[i]);
        stackYTD *= (1 + r.stackedReturns[i]);
        coreG *= (1 + r.coreReturns[i]);
        stackG *= (1 + r.stackedReturns[i]);

        if (coreG > corePeak) corePeak = coreG;
        if (stackG > stackPeak) stackPeak = stackG;
        const cDD = (corePeak - coreG) / corePeak;
        const sDD = (stackPeak - stackG) / stackPeak;
        if (cDD > coreMaxDD) coreMaxDD = cDD;
        if (sDD > stackMaxDD) stackMaxDD = sDD;
      }}
      // Push final year
      if (curYear !== null) {{
        years.push(curYear);
        coreYearReturns.push((coreYTD - 1) * 100);
        stackYearReturns.push((stackYTD - 1) * 100);
        coreYearDD.push(-coreMaxDD * 100);
        stackYearDD.push(-stackMaxDD * 100);
      }}

      const barOpts = (yTitle, fmt) => ({{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: hasStack, position: "top" }},
          tooltip: {{
            callbacks: {{ label: (item) => `${{item.dataset.label}}: ${{item.parsed.y.toFixed(2)}}%` }},
          }},
        }},
        scales: {{
          x: {{ ticks: {{ color: "#555" }}, grid: {{ display: false }} }},
          y: {{ title: {{ display: true, text: yTitle, font: {{ family: "'DM Sans'", size: 12, weight: "600" }}, color: "#555" }}, ticks: {{ color: "#555", callback: (v) => v.toFixed(0) + "%" }} }},
        }},
      }});

      // Calendar year returns bar chart (canvas A)
      addLabel("Calendar Year Performance", canvasA.parentNode);
      const retDS = [];
      if (hasCore) retDS.push({{ label: "Core Portfolio", data: coreYearReturns, backgroundColor: "#323A46", borderRadius: 2 }});
      if (hasStack || !hasCore) retDS.push({{ label: !hasCore ? "Excess Return" : "Stacked Portfolio", data: stackYearReturns, backgroundColor: "#14CFA6", borderRadius: 2 }});
      this._charts[`rsv-chart-${{portfolioIdx}}-a`] = new Chart(canvasA.getContext("2d"), {{
        type: "bar", data: {{ labels: years.map(String), datasets: retDS }}, options: barOpts("Calendar Year Return (%)"),
      }});

      // Calendar year max drawdown bar chart (canvas B)
      addLabel("Intra-year Maximum Drawdown", wrapB);
      const ddDS = [];
      if (hasCore) ddDS.push({{ label: "Core Portfolio", data: coreYearDD, backgroundColor: "#323A46", borderRadius: 2 }});
      if (hasStack || !hasCore) ddDS.push({{ label: !hasCore ? "Excess Return" : "Stacked Portfolio", data: stackYearDD, backgroundColor: "#14CFA6", borderRadius: 2 }});
      this._charts[`rsv-chart-${{portfolioIdx}}-b`] = new Chart(canvasB.getContext("2d"), {{
        type: "bar", data: {{ labels: years.map(String), datasets: ddDS }}, options: barOpts("Calendar Year Max Drawdown (%)"),
      }});

      // Calendar year stats text
      if (hasStack) {{
        let outCount = 0;
        let overStreak = 0, maxOver = 0, overStart = 0, overRanges = [];
        let underStreak = 0, maxUnder = 0, underStart = 0, underRanges = [];
        for (let i = 0; i < years.length; i++) {{
          if (stackYearReturns[i] > coreYearReturns[i]) {{
            outCount++;
            if (overStreak === 0) overStart = i;
            overStreak++;
            if (overStreak > maxOver) {{ maxOver = overStreak; overRanges = [{{ s: years[overStart], e: years[i] }}]; }}
            else if (overStreak === maxOver && maxOver > 0) overRanges.push({{ s: years[overStart], e: years[i] }});
            underStreak = 0;
          }} else if (stackYearReturns[i] < coreYearReturns[i]) {{
            if (underStreak === 0) underStart = i;
            underStreak++;
            if (underStreak > maxUnder) {{ maxUnder = underStreak; underRanges = [{{ s: years[underStart], e: years[i] }}]; }}
            else if (underStreak === maxUnder && maxUnder > 0) underRanges.push({{ s: years[underStart], e: years[i] }});
            overStreak = 0;
          }} else {{ overStreak = 0; underStreak = 0; }}
        }}
        const fmtRanges = (ranges) => {{
          const parts = ranges.map(r => r.s === r.e ? String(r.s) : r.s + "\\u2013" + r.e);
          if (parts.length <= 2) return parts.join(" & ");
          return parts.slice(0,-1).join(", ") + " & " + parts[parts.length-1];
        }};
        const overYrs = maxOver === 1 ? "1 year" : maxOver + " years";
        const underYrs = maxUnder === 1 ? "1 year" : maxUnder + " years";
        const statsA = document.getElementById(`rsv-chart-stats-${{portfolioIdx}}-a`);
        if (statsA) {{
          statsA.style.display = "block";
          statsA.innerHTML = `Stacked portfolio outperformed the Core portfolio in <span class="hl">${{outCount}} of ${{years.length}}</span> calendar years`
            + `<br>Longest streak of annual outperformance: <span class="hl">${{overYrs}}</span>${{overRanges.length ? " (" + fmtRanges(overRanges) + ")" : ""}}`
            + `<br>Longest streak of annual underperformance: <span class="hl">${{underYrs}}</span>${{underRanges.length ? " (" + fmtRanges(underRanges) + ")" : ""}}`;
        }}
      }}
      return;
    }}

    // ── Rolling Returns ──
    if (chartType === "rollingReturns") {{
      const months = (options && options.months) || 36;
      if (wrapB) wrapB.style.display = "block";

      // Show slider in controls
      if (controlsEl) {{
        controlsEl.style.display = "flex";
        controlsEl.innerHTML = `<span>Period:</span>
          <input type="range" min="12" max="120" value="${{months}}" step="3"
            oninput="this.nextElementSibling.textContent=this.value+' Months';clearTimeout(RSV._sliderTimer);RSV._sliderTimer=setTimeout(()=>RSV.drawChart(${{portfolioIdx}},'rollingReturns',{{months:parseInt(this.value)}}),150)">
          <span class="slider-val">${{months}} Months</span>`;
      }}

      // Compute rolling annualized returns
      const computeRolling = (growth, n) => {{
        const rolling = [];
        for (let i = n; i < growth.length; i++) {{
          rolling.push((Math.pow(growth[i] / growth[i - n], 12 / n) - 1) * 100);
        }}
        return rolling;
      }};

      const coreRolling = hasCore ? computeRolling(r.coreGrowth, months) : null;
      const stackRolling = (hasStack || !hasCore) ? computeRolling(r.stackedGrowth, months) : null;
      const rollingLabels = r.dates.slice(months);

      // Chart A: Rolling Annualized Returns
      addLabel("Rolling Annualized Returns", canvasA.parentNode);
      const rollingDS = [];
      if (hasCore && coreRolling) rollingDS.push({{ label: "Core Portfolio", data: coreRolling, borderColor: "#323A46", borderWidth: 2, pointRadius: 0, pointHitRadius: 6, fill: false }});
      if (stackRolling) {{
        rollingDS.push({{ label: !hasCore ? "Excess Return" : "Stacked Portfolio", data: stackRolling, borderColor: "#14CFA6", borderWidth: 2, pointRadius: 0, pointHitRadius: 6, fill: false }});
      }}
      const rollingOpts = lineOpts(`${{months}}-Month Rolling Annualized Return (%)`, (item) => `${{item.dataset.label}}: ${{item.parsed.y.toFixed(2)}}%`);
      rollingOpts.scales.y.ticks.callback = (v) => v.toFixed(0) + "%";
      rollingOpts.plugins = rollingOpts.plugins || {{}};
      rollingOpts.plugins.annotation = {{
        annotations: {{
          zeroLine: {{ type: "line", yMin: 0, yMax: 0, borderColor: "#323A46", borderWidth: 2 }},
        }},
      }};
      this._charts[`rsv-chart-${{portfolioIdx}}-a`] = new Chart(canvasA.getContext("2d"), {{
        type: "line", data: {{ labels: rollingLabels, datasets: rollingDS }}, options: rollingOpts,
      }});

      // Outperformance text (only when both core and stack exist)
      if (hasCore && hasStack && coreRolling && stackRolling) {{
        let outCount = 0;
        for (let i = 0; i < coreRolling.length; i++) {{
          if (stackRolling[i] > coreRolling[i]) outCount++;
        }}
        const outPct = (outCount / coreRolling.length * 100).toFixed(1);
        const statsA = document.getElementById(`rsv-chart-stats-${{portfolioIdx}}-a`);
        if (statsA) {{
          statsA.style.display = "block";
          statsA.innerHTML = `Stacked portfolio outperformed the Core portfolio in <span class="hl">${{outPct}}%</span> of rolling ${{months}}-month periods`;
        }}

        // Chart B: Stacked Portfolio Outperformance
        addLabel("Stacked Portfolio Outperformance", wrapB);
        const diffData = coreRolling.map((v, i) => stackRolling[i] - v);
        // Segment coloring: blue above 0, red below 0
        const diffDS = [{{
          label: "Stacked - Core (pp)",
          data: diffData,
          borderColor: "#3A6A9C",
          backgroundColor: "rgba(58,106,156,0.15)",
          segment: {{
            borderColor: (ctx) => {{
              const y0 = ctx.p0.parsed.y;
              const y1 = ctx.p1.parsed.y;
              return (y0 < 0 && y1 < 0) ? "#d9534f" : "#3A6A9C";
            }},
            backgroundColor: (ctx) => {{
              const y0 = ctx.p0.parsed.y;
              const y1 = ctx.p1.parsed.y;
              return (y0 < 0 && y1 < 0) ? "rgba(217,83,79,0.15)" : "rgba(58,106,156,0.15)";
            }},
          }},
          borderWidth: 1.5,
          pointRadius: 0,
          fill: true,
        }}];
        const diffOpts = lineOpts("Rolling Return Difference (pp)", (item) => `Difference: ${{item.parsed.y >= 0 ? "+" : ""}}${{item.parsed.y.toFixed(2)}}pp`);
        diffOpts.scales.y.ticks.callback = (v) => (v >= 0 ? "+" : "") + v.toFixed(0) + "pp";
        diffOpts.plugins.legend.display = false;
        diffOpts.plugins.annotation = {{
          annotations: {{
            zeroLine: {{ type: "line", yMin: 0, yMax: 0, borderColor: "#323A46", borderWidth: 2 }},
          }},
        }};
        this._charts[`rsv-chart-${{portfolioIdx}}-b`] = new Chart(canvasB.getContext("2d"), {{
          type: "line", data: {{ labels: rollingLabels, datasets: diffDS }}, options: diffOpts,
        }});
      }}
      return;
    }}

    // ── Scaled Stack Blend ──
    if (chartType === "scaledBlend") {{
      const lookback = (options && options.lookback) || 36;
      const useLinear = options && options.linear;
      if (wrapB) wrapB.style.display = "block";

      if (controlsEl) {{
        controlsEl.style.display = "flex";
        controlsEl.innerHTML = `<label><input type="checkbox" ${{useLinear ? "checked" : ""}}
          onchange="RSV.drawChart(${{portfolioIdx}}, 'scaledBlend', {{linear: this.checked, lookback: ${{lookback}}}})"> Linear Scale</label>`;
      }}

      // Compute blend returns (just the overlay sleeve)
      const blendGrowth = [1];
      for (let i = 0; i < r.stackedReturns.length; i++) {{
        const blendR = r.stackedReturns[i] - r.coreReturns[i];
        blendGrowth.push(blendGrowth[i] * (1 + blendR));
      }}

      // Chart A: Decomposed Return Streams
      addLabel("Decomposed Return Streams", canvasA.parentNode);
      const blendDS = [
        {{ label: "Core Portfolio", data: r.coreGrowth, borderColor: "#323A46", backgroundColor: "transparent", fill: false, borderWidth: 2, pointRadius: 0, pointHitRadius: 6 }},
        {{ label: "Scaled Stack Blend", data: blendGrowth, borderColor: "#14CFA6", backgroundColor: "transparent", fill: false, borderWidth: 2, pointRadius: 0, pointHitRadius: 6 }},
        {{ label: "Stacked Portfolio", data: r.stackedGrowth, borderColor: "rgba(0,0,0,0.35)", borderWidth: 1.5, borderDash: [5, 3], pointRadius: 0, fill: false }},
      ];
      const blendOpts = lineOpts("Growth of $1", (item) => `${{item.dataset.label}}: $${{item.parsed.y.toFixed(2)}}`);
      blendOpts.scales.y.type = useLinear ? "linear" : "logarithmic";
      blendOpts.scales.y.ticks.callback = (v) => "$" + v.toFixed(1);
      this._charts[`rsv-chart-${{portfolioIdx}}-a`] = new Chart(canvasA.getContext("2d"), {{
        type: "line", data: {{ labels: r.dates, datasets: blendDS }}, options: blendOpts,
      }});

      // Correlation text
      const coreMonthly = r.coreReturns;
      const blendMonthly = r.stackedReturns.map((s, i) => s - r.coreReturns[i]);
      const computeCorr = (a, b) => {{
        const n = a.length;
        const mA = a.reduce((s, v) => s + v, 0) / n;
        const mB = b.reduce((s, v) => s + v, 0) / n;
        let cov = 0, vA = 0, vB = 0;
        for (let i = 0; i < n; i++) {{
          const dA = a[i] - mA, dB = b[i] - mB;
          cov += dA * dB; vA += dA * dA; vB += dB * dB;
        }}
        const denom = Math.sqrt(vA * vB);
        return denom === 0 ? 0 : cov / denom;
      }};
      const fullCorr = computeCorr(coreMonthly, blendMonthly);
      const statsA = document.getElementById(`rsv-chart-stats-${{portfolioIdx}}-a`);
      if (statsA) {{
        statsA.style.display = "block";
        statsA.innerHTML = `Monthly return correlation between Core and Scaled Stack Blend: <span class="hl">${{fullCorr.toFixed(2)}}</span>`;
      }}

      // Chart B: Rolling Correlations
      addLabel("Rolling Correlations", wrapB);
      const rollingCorr = [];
      const corrLabels = [];
      for (let i = lookback - 1; i < coreMonthly.length; i++) {{
        const wA = coreMonthly.slice(i - lookback + 1, i + 1);
        const wB = blendMonthly.slice(i - lookback + 1, i + 1);
        rollingCorr.push(computeCorr(wA, wB));
        corrLabels.push(r.dates[i + 1]);
      }}

      const corrDS = [{{ label: "Rolling Correlation", data: rollingCorr, borderColor: "#3A6A9C", borderWidth: 2, pointRadius: 0, fill: false }}];
      const corrOpts = lineOpts("Rolling Correlation: Core vs. Scaled Stack Blend", (item) => `Correlation: ${{item.parsed.y.toFixed(3)}}`);
      corrOpts.scales.y.ticks.callback = (v) => v.toFixed(1);
      corrOpts.scales.y.min = -1;
      corrOpts.scales.y.max = 1;
      corrOpts.plugins.legend.display = false;
      corrOpts.plugins.annotation = {{
        annotations: {{
          zeroLine: {{ type: "line", yMin: 0, yMax: 0, borderColor: "#323A46", borderWidth: 2 }},
        }},
      }};
      this._charts[`rsv-chart-${{portfolioIdx}}-b`] = new Chart(canvasB.getContext("2d"), {{
        type: "line", data: {{ labels: corrLabels, datasets: corrDS }}, options: corrOpts,
      }});

      // Lookback slider below chart B
      const statsB = document.getElementById(`rsv-chart-stats-${{portfolioIdx}}-b`);
      if (statsB) {{
        statsB.style.display = "block";
        statsB.innerHTML = `<div class="rsv-chart-slider">
          <span>Lookback:</span>
          <input type="range" min="12" max="120" value="${{lookback}}" step="3"
            oninput="this.nextElementSibling.textContent=this.value+' Months';clearTimeout(RSV._sliderTimer);RSV._sliderTimer=setTimeout(()=>RSV.drawChart(${{portfolioIdx}},'scaledBlend',{{lookback:parseInt(this.value),linear:${{useLinear ? 'true' : 'false'}}}}),150)">
          <span class="slider-val">${{lookback}} Months</span>
        </div>`;
      }}
      return;
    }}
  }},

  initCharts(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    if (p.result) {{
      const chartType = this._activeChartType[portfolioIdx] || "growthDD";
      requestAnimationFrame(() => this.drawChart(portfolioIdx, chartType));
    }}
  }},

  // ── Advanced Fee Configuration ──

  renderAdvancedFeeConfig(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const stackAssets = p.stack.filter(r => r.asset && r.weight > 0);
    if (stackAssets.length === 0) return "";

    let rows = "";
    for (let i = 0; i < p.stack.length; i++) {{
      const row = p.stack[i];
      if (!row.asset || row.weight <= 0) continue;
      const isNetOfFees = NET_OF_FEES_ASSETS.has(row.asset);
      const feeVal = row.feeBp || 0;
      const finVal = row.financingBp || 0;

      rows += `<tr>
        <td>${{row.asset}}</td>
        <td>${{isNetOfFees
          ? '<span class="rsv-tooltip" style="color:var(--border-gray);font-size:12px;">N/A<span class="rsv-tooltip-text">This index is already reported net of fees</span></span>'
          : '<input type="number" step="1" min="0" max="500" value="' + feeVal + '" style="width:70px;text-align:right;font-family:inherit;font-size:12px;padding:4px 6px;border:1px solid var(--border-gray);border-radius:3px;" onchange="RSV.updateAssetFee(' + portfolioIdx + ',' + i + ',\\'feeBp\\',this.value)" oninput="RSV.updateAssetFee(' + portfolioIdx + ',' + i + ',\\'feeBp\\',this.value)" onfocus="this.select()">'
        }}</td>
        <td><input type="number" step="1" min="0" max="500" value="${{finVal}}" style="width:70px;text-align:right;font-family:inherit;font-size:12px;padding:4px 6px;border:1px solid var(--border-gray);border-radius:3px;"
             onchange="RSV.updateAssetFee(${{portfolioIdx}},${{i}},'financingBp',this.value)"
             oninput="RSV.updateAssetFee(${{portfolioIdx}},${{i}},'financingBp',this.value)"
             onfocus="this.select()"></td>
      </tr>`;
    }}

    const isOpen = this._advancedFeeOpen[portfolioIdx];
    return `<div class="rsv-disclosures" style="margin-top:8px;margin-bottom:8px;">
      <button class="rsv-disclosures-toggle${{isOpen ? " open" : ""}}" onclick="RSV.toggleAdvancedFee(${{portfolioIdx}}, this)" style="border-top:none;font-size:12px;">
        <span class="rsv-arrow">&#9654;</span> Advanced Fee Configuration
      </button>
      <div class="rsv-disclosures-content${{isOpen ? " open" : ""}}" style="font-size:13px;color:var(--text-primary);">
        <table class="rsv-results-table" style="font-size:12px;">
          <thead><tr>
            <th style="text-align:left;">Overlay Asset</th>
            <th>Fee (bp)
              <span class="rsv-tooltip">(?)<span class="rsv-tooltip-text">Estimated annual cost of accessing each alternative strategy, in basis points (e.g. 100 for 1%)</span></span>
            </th>
            <th>Financing (bp)
              <span class="rsv-tooltip">(?)<span class="rsv-tooltip-text">Estimated financing spread above T-bills required to carry each leveraged exposure, in basis points</span></span>
            </th>
          </tr></thead>
          <tbody>${{rows}}</tbody>
        </table>
      </div>
    </div>`;
  }},

  updateAssetFee(portfolioIdx, stackIdx, field, value) {{
    state.portfolios[portfolioIdx].stack[stackIdx][field] = parseFloat(value) || 0;
    this.scheduleAutoCompute(portfolioIdx);
  }},

  toggleAdvancedFee(portfolioIdx, btn) {{
    btn.classList.toggle("open");
    const content = btn.nextElementSibling;
    content.classList.toggle("open");
    this._advancedFeeOpen[portfolioIdx] = content.classList.contains("open");
  }},

  // ── Dynamic Portfolio Disclaimer ──

  _fmtDisclaimerDate(isoDate) {{
    if (!isoDate) return "";
    const parts = isoDate.split("-");
    return parseInt(parts[1]) + "/" + parseInt(parts[2]) + "/" + parts[0];
  }},

  _collectPortfolioAssets(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const coreAssets = p.core.filter(a => a.asset && a.weight > 0);
    const stackAssets = p.stack.filter(a => a.asset && a.weight > 0);
    const names = [...new Set([...coreAssets.map(a => a.asset), ...stackAssets.map(a => a.asset)])];
    if (stackAssets.length > 0 && !names.includes("Cash")) names.push("Cash");
    return {{ coreAssets, stackAssets, allNames: names }};
  }},

  _buildSourceLine(assetNames) {{
    const providers = new Set();
    for (const name of assetNames) {{
      const info = TICKER_INFO[name];
      if (info && info.provider) {{
        info.provider.split("; ").forEach(p => providers.add(p));
      }}
    }}
    if (providers.has("ReSolve Asset Management")) {{
      providers.delete("ReSolve Asset Management");
      providers.add("ReSolve Asset Management (SEZC)");
    }}
    const sorted = [...providers].sort();
    return "Source: " + sorted.join("; ") + ".";
  }},

  _buildAssetDefinitions(assetNames) {{
    const lines = [];
    for (const name of assetNames) {{
      const info = TICKER_INFO[name];
      if (!info) continue;
      let line = name + " is the " + info.fullName;
      if (info.ticker && info.ticker !== "N/A") {{
        line += " (\u201C" + info.ticker + "\u201D)";
      }}
      if (info.specialNote) {{
        line += " (" + info.specialNote + ")";
      }}
      line += ".";
      lines.push(line);
    }}
    return lines.join(" ");
  }},

  _buildCompositionDescription(p, coreAssets, stackAssets) {{
    let desc = "The " + p.name + " portfolio is ";
    if (coreAssets.length > 0) {{
      desc += coreAssets.map(a => a.weight + "% " + a.asset).join(" / ");
    }} else {{
      desc += "an excess return portfolio";
    }}
    if (stackAssets.length > 0) {{
      const totalStack = stackAssets.reduce((s, a) => s + a.weight, 0);
      const stackDetail = stackAssets.map(a => {{
        const pct = ((a.weight / totalStack) * 100).toFixed(0);
        return pct + "% " + a.asset;
      }}).join(", ");
      desc += " / " + totalStack + "% Stack (" + stackDetail + ") / -" + totalStack + "% T-Bills";
    }}
    desc += ".";
    return desc;
  }},

  _buildCostsSection(p, stackAssets) {{
    const lines = [];
    if (p.fee > 0) {{
      lines.push("Advisory Fee: " + (p.fee / 100).toFixed(2) + "%");
    }}
    for (const a of stackAssets) {{
      const info = TICKER_INFO[a.asset];
      const isNet = NET_OF_FEES_ASSETS.has(a.asset);
      const feeBp = a.feeBp || 0;
      const finBp = a.financingBp || 0;
      if (feeBp === 0 && finBp === 0) continue;
      const parts = [];
      if (feeBp > 0) {{
        let fp = feeBp + " bp fee";
        if (isNet && info) fp += " (the " + info.fullName + " is reported net of fees)";
        parts.push(fp);
      }}
      if (finBp > 0) parts.push(finBp + " bp financing");
      lines.push(a.asset + ": " + parts.join(" / "));
    }}
    if (lines.length === 0) return "";
    return "Assumed annual costs: " + lines.join("; ") + ".";
  }},

  _buildLegalFooter(periodStart, periodEnd) {{
    let t = "See methodology below for an explicit explanation of how portfolio returns are calculated. ";
    t += "See glossary below for index definitions. ";
    t += "You cannot invest in an index. Portfolio returns are hypothetical. ";
    t += "Returns are gross of all fees, including management costs, transaction costs, and taxes, except where explicitly stated otherwise. ";
    t += "Returns assume the reinvestment of all distributions. ";
    t += "Period is " + this._fmtDisclaimerDate(periodStart) + " through " + this._fmtDisclaimerDate(periodEnd) + ". ";
    t += "The starting date is chosen based upon the earliest date data is available for the underlying indexes. ";
    t += "Past performance is not indicative of future results.";
    return t;
  }},

  generatePortfolioDisclaimer(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const r = p.result;
    if (!r) return "";

    const {{ coreAssets, stackAssets, allNames }} = this._collectPortfolioAssets(portfolioIdx);
    const periodStart = p.dateRange ? p.dateRange.start : r.period.start;
    const periodEnd = p.dateRange ? p.dateRange.end : r.period.end;

    const parts = [];
    parts.push(this._buildSourceLine(allNames));
    parts.push(this._buildAssetDefinitions(allNames));
    parts.push(this._buildCompositionDescription(p, coreAssets, stackAssets));
    const costs = this._buildCostsSection(p, stackAssets);
    if (costs) parts.push(costs);
    parts.push(this._buildLegalFooter(periodStart, periodEnd));
    return parts.join(" ");
  }},

  generateMergedDisclaimer(activeIndices, commonStart, commonEnd) {{
    const allNames = new Set();
    const portfolioDescs = [];

    for (const i of activeIndices) {{
      const p = state.portfolios[i];
      const {{ coreAssets, stackAssets, allNames: names }} = this._collectPortfolioAssets(i);
      names.forEach(n => allNames.add(n));
      portfolioDescs.push(this._buildCompositionDescription(p, coreAssets, stackAssets));
    }}

    const nameArr = [...allNames];
    const parts = [];
    parts.push(this._buildSourceLine(nameArr));
    parts.push(this._buildAssetDefinitions(nameArr));
    parts.push(portfolioDescs.join(" "));

    // Merge costs from all portfolios (deduplicate by asset name, skip zero fees)
    const seenAssets = new Set();
    const costLines = [];
    for (const i of activeIndices) {{
      const p = state.portfolios[i];
      const stackAssets = p.stack.filter(a => a.asset && a.weight > 0);
      if (p.fee > 0) costLines.push(p.name + " Advisory Fee: " + (p.fee / 100).toFixed(2) + "%");
      for (const a of stackAssets) {{
        if (seenAssets.has(a.asset)) continue;
        seenAssets.add(a.asset);
        const info = TICKER_INFO[a.asset];
        const isNet = NET_OF_FEES_ASSETS.has(a.asset);
        const feeBp = a.feeBp || 0;
        const finBp = a.financingBp || 0;
        if (feeBp === 0 && finBp === 0) continue;
        const cp = [];
        if (feeBp > 0) {{
          let fp = feeBp + " bp fee";
          if (isNet && info) fp += " (the " + info.fullName + " is reported net of fees)";
          cp.push(fp);
        }}
        if (finBp > 0) cp.push(finBp + " bp financing");
        costLines.push(a.asset + ": " + cp.join(" / "));
      }}
    }}
    if (costLines.length > 0) {{
      parts.push("Assumed annual costs: " + costLines.join("; ") + ".");
    }}

    parts.push(this._buildLegalFooter(commonStart, commonEnd));
    return parts.join(" ");
  }},

  renderPortfolioDisclaimer(portfolioIdx) {{
    const text = this.generatePortfolioDisclaimer(portfolioIdx);
    if (!text) return "";
    return `<div style="margin-top:12px;margin-bottom:8px;font-size:11px;font-style:italic;color:var(--text-secondary);line-height:1.5;">
      ${{text}}
      <span style="font-weight:700;font-style:italic;">NO REPRESENTATION IS BEING MADE THAT ANY PORTFOLIO WILL OR IS LIKELY TO ACHIEVE PROFIT OR LOSSES SIMILAR TO THOSE SHOWN.</span>
    </div>`;
  }},

  renderMergedDisclaimer(activeIndices, commonStart, commonEnd) {{
    if (activeIndices.length === 0) return "";
    const text = this.generateMergedDisclaimer(activeIndices, commonStart, commonEnd);
    return `<div style="margin-top:16px;margin-bottom:8px;font-size:11px;font-style:italic;color:var(--text-secondary);line-height:1.5;">
      ${{text}}
      <span style="font-weight:700;font-style:italic;">NO REPRESENTATION IS BEING MADE THAT ANY PORTFOLIO WILL OR IS LIKELY TO ACHIEVE PROFIT OR LOSSES SIMILAR TO THOSE SHOWN.</span>
    </div>`;
  }},

  // ── Saved Portfolios ──

  // Global searchable Saved Portfolios picker (rendered in the tab bar, applies to active portfolio).
  renderSavedDropdownGlobal() {{
    const saved = getSavedPortfolios();
    let html = `<div class="rsv-combo rsv-combo--inline" data-saved="1">
      <button type="button" class="rsv-combo-trigger" onclick="RSV.toggleCombo(this)" aria-haspopup="listbox" aria-expanded="false">
        <span class="rsv-combo-value">Saved Portfolios</span>
        <span class="rsv-combo-arrow" aria-hidden="true">&#x25BE;</span>
      </button>
      <div class="rsv-combo-panel" hidden role="listbox">
        <div class="rsv-combo-search-wrap">
          <input type="text" class="rsv-combo-search" placeholder="Search portfolios..." oninput="RSV.filterCombo(this)" onkeydown="RSV.handleComboKeydown(event, this)" autocomplete="off">
        </div>
        <div class="rsv-combo-list">
          <div class="rsv-combo-group">Defaults</div>`;
    PRESET_PORTFOLIOS.forEach((p, i) => {{
      html += `<button type="button" class="rsv-combo-option" data-value="default_${{i}}" onclick="RSV.selectComboOption(this)">${{p.name}}</button>`;
    }});
    if (saved.length > 0) {{
      html += `<div class="rsv-combo-group">My Saved Portfolios</div>`;
      saved.forEach((s, i) => {{
        html += `<button type="button" class="rsv-combo-option" data-value="saved_${{i}}" onclick="RSV.selectComboOption(this)">${{s.name}}</button>`;
      }});
    }}
    html += `</div>`;
    if (saved.length > 0) {{
      html += `<div class="rsv-combo-footer"><button type="button" onclick="RSV.closeAllCombos();RSV.deleteSavedPortfolioPrompt(typeof state.activeTab === 'number' ? state.activeTab : 0);">Delete a Save</button></div>`;
    }}
    html += `</div></div>`;
    return html;
  }},

  resetPortfolio(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    p.name = "Portfolio " + (portfolioIdx + 1);
    p.core = [{{ asset: "", weight: 0 }}];
    p.stack = [{{ asset: "", weight: 0, feeBp: 0, financingBp: 0 }}];
    p.fee = 0;
    p.result = null;
    p.dateRange = null;
    this.renderTabs();
    this.renderPanel(portfolioIdx);
  }},

  savePortfolio(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    const coreAssets = p.core.filter(r => r.asset && r.weight > 0);
    if (coreAssets.length === 0) {{
      alert("Add at least one asset to the core portfolio before saving.");
      return;
    }}
    const name = prompt("Save portfolio as:", p.name);
    if (!name) return;

    const saved = getSavedPortfolios();
    // Check for duplicate name
    const existing = saved.findIndex(s => s.name === name);
    if (existing >= 0) {{
      if (!confirm("A saved portfolio named '" + name + "' already exists. Overwrite?")) return;
      saved.splice(existing, 1);
    }}

    const portfolioData = {{
      name: name,
      core: p.core.filter(r => r.asset).map(r => ({{ asset: r.asset, weight: r.weight }})),
      stack: p.stack.filter(r => r.asset).map(r => ({{ asset: r.asset, weight: r.weight, feeBp: r.feeBp || 0, financingBp: r.financingBp || 0 }})),
      fee: p.fee,
      savedAt: new Date().toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', year: 'numeric' }}),
    }};
    saved.push(portfolioData);
    setSavedPortfolios(saved);
    _submitAllPortfoliosToHS();

    // Also download as JSON backup file
    const blob = new Blob([JSON.stringify(portfolioData, null, 2)], {{ type: "application/json" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name.replace(/[^a-zA-Z0-9]+/g, "_") + ".json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    this.renderPanel(state.activeTab);
  }},

  importPortfolio() {{
    const fileEl = document.getElementById("rsv-import-file");
    if (fileEl) fileEl.click();
  }},

  _handleImportFile(fileEl) {{
    if (!fileEl.files || fileEl.files.length === 0) return;
    const files = Array.from(fileEl.files);
    let imported = 0, skipped = 0;
    let remaining = files.length;

    const saved = getSavedPortfolios();

    const processFile = (file) => {{
      const reader = new FileReader();
      reader.onload = (e) => {{
        try {{
          const data = JSON.parse(e.target.result);
          if (!data.name || !Array.isArray(data.core) || !data.core.some(r => r.asset && r.weight > 0)) {{
            skipped++;
          }} else {{
            const existing = saved.findIndex(s => s.name === data.name);
            if (existing >= 0) {{
              if (!confirm("'" + data.name + "' already exists. Overwrite?")) {{
                skipped++;
                remaining--;
                if (remaining === 0) finalize();
                return;
              }}
              saved.splice(existing, 1);
            }}
            saved.push({{
              name: data.name,
              core: data.core,
              stack: data.stack || [{{ asset: "", weight: 0 }}],
              fee: data.fee || 0,
            }});
            imported++;
          }}
        }} catch (err) {{
          skipped++;
        }}
        remaining--;
        if (remaining === 0) finalize();
      }};
      reader.readAsText(file);
    }};

    const finalize = () => {{
      setSavedPortfolios(saved);
      if (imported > 0) {{
        alert("Imported " + imported + " portfolio(s)." + (skipped > 0 ? " Skipped " + skipped + "." : ""));
      }} else {{
        alert("No portfolios were imported." + (skipped > 0 ? " " + skipped + " file(s) skipped or invalid." : ""));
      }}
      this.renderPanel(state.activeTab);
    }};

    for (const file of files) processFile(file);
    fileEl.value = "";
  }},

  loadSavedPortfolio(portfolioIdx, value) {{
    if (!value) return;
    let config;
    if (value.startsWith("default_")) {{
      const idx = parseInt(value.split("_")[1]);
      config = PRESET_PORTFOLIOS[idx];
    }} else if (value.startsWith("saved_")) {{
      const idx = parseInt(value.split("_")[1]);
      config = getSavedPortfolios()[idx];
    }}
    if (!config) return;

    const p = state.portfolios[portfolioIdx];
    p.name = config.name;
    // Deep copy arrays to avoid sharing references with presets or other portfolios
    p.core = JSON.parse(JSON.stringify(config.core));
    p.stack = config.stack && config.stack.length > 0 ? JSON.parse(JSON.stringify(config.stack)) : [{{ asset: "", weight: 0 }}];
    if (p.core.length === 0) p.core = [{{ asset: "", weight: 0 }}];
    p.fee = config.fee || 0;
    // Recompute so charts/stats refresh with the newly loaded weights
    p.result = computePortfolio(p);
    state.activeTab = portfolioIdx;
    this.renderTabs();
    this.renderPanel(portfolioIdx);
  }},

  deleteSavedPortfolioPrompt(portfolioIdx) {{
    const saved = getSavedPortfolios();
    if (saved.length === 0) return;
    const names = saved.map((s, i) => (i + 1) + ". " + s.name).join("\\n");
    const choice = prompt("Enter the number of the portfolio to delete:\\n\\n" + names);
    if (!choice) return;
    const idx = parseInt(choice) - 1;
    if (idx >= 0 && idx < saved.length) {{
      saved.splice(idx, 1);
      setSavedPortfolios(saved);
      this.renderPanel(state.activeTab);
    }}
  }},

  // ── Saved Comparisons ──

  saveComparison() {{
    const anyEnabled = state.portfolios.some(p => p.enabled);
    if (!anyEnabled) {{
      alert("Enable at least one portfolio before saving a comparison.");
      return;
    }}
    const name = prompt("Save comparison as:");
    if (!name) return;
    const trimmed = name.trim();
    if (!trimmed) return;

    // Embed full portfolio data per slot so comparisons are self-contained.
    // portfolioName is kept for display and backwards-compat name lookup.
    const slots = state.portfolios.map(p => ({{
      enabled: !!p.enabled,
      portfolioName: p.name || "",
      core: p.core.filter(r => r.asset).map(r => ({{ asset: r.asset, weight: r.weight }})),
      stack: p.stack.filter(r => r.asset).map(r => ({{ asset: r.asset, weight: r.weight, feeBp: r.feeBp || 0, financingBp: r.financingBp || 0 }})),
      fee: p.fee || 0,
    }}));
    const compData = {{ name: trimmed, slots: slots, savedAt: new Date().toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', year: 'numeric' }}) }};

    const saved = getSavedComparisons();
    const existing = saved.findIndex(c => c.name === trimmed);
    if (existing >= 0) {{
      if (!confirm("A saved comparison named '" + trimmed + "' already exists. Overwrite?")) return;
      saved.splice(existing, 1);
    }}
    saved.push(compData);
    setSavedComparisons(saved);
    _submitComparisonToHS(compData);

    // Also download as JSON backup file
    const blob = new Blob([JSON.stringify(compData, null, 2)], {{ type: "application/json" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "comparison_" + trimmed.replace(/[^a-zA-Z0-9]+/g, "_") + ".json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    this.renderPanel(state.activeTab);
  }},

  loadSavedComparison(idx) {{
    this.closeAllCombos();
    const saved = getSavedComparisons();
    const comp = saved[idx];
    if (!comp || !Array.isArray(comp.slots)) return;

    const savedPortfolios = getSavedPortfolios();
    const presetByName = {{}};
    PRESET_PORTFOLIOS.forEach(p => {{ presetByName[p.name] = p; }});

    const missing = [];
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const slot = comp.slots[i] || {{ enabled: false, portfolioName: "" }};
      const p = state.portfolios[i];
      p.enabled = !!slot.enabled;
      if (slot.enabled && slot.portfolioName) {{
        // Prefer embedded portfolio data in the slot (self-contained format).
        // Fall back to name lookup for old-format files that only stored names.
        const src = (slot.core && slot.core.length > 0)
          ? slot
          : (savedPortfolios.find(s => s.name === slot.portfolioName) || presetByName[slot.portfolioName]);
        if (src) {{
          p.name = src.name || slot.portfolioName;
          p.core = JSON.parse(JSON.stringify(src.core || [{{ asset: "", weight: 0 }}]));
          p.stack = src.stack && src.stack.length > 0
            ? JSON.parse(JSON.stringify(src.stack))
            : [{{ asset: "", weight: 0 }}];
          if (p.core.length === 0) p.core = [{{ asset: "", weight: 0 }}];
          p.fee = src.fee || 0;
          p.dateRange = null;
          p.result = computePortfolio(p);
        }} else {{
          missing.push(slot.portfolioName);
        }}
      }}
    }}

    if (missing.length) {{
      alert("Heads up: these portfolios are referenced by the comparison but were not found in Saved Portfolios:\\n\\n  " + missing.join("\\n  ") + "\\n\\nThose slots have been left in their current state. Save them as portfolios with matching names to fully restore the comparison.");
    }}

    state.activeTab = "summary";
    this.renderTabs();
    this.renderPanel("summary");
  }},

  importComparison() {{
    const fileEl = document.getElementById("rsv-import-comparison-file");
    if (fileEl) fileEl.click();
  }},

  _handleImportComparisonFile(fileEl) {{
    if (!fileEl.files || fileEl.files.length === 0) return;
    const files = Array.from(fileEl.files);
    let imported = 0, skipped = 0;
    let remaining = files.length;

    const saved = getSavedComparisons();

    const processFile = (file) => {{
      const reader = new FileReader();
      reader.onload = (e) => {{
        try {{
          const data = JSON.parse(e.target.result);
          if (!data.name || !Array.isArray(data.slots)) {{
            skipped++;
          }} else {{
            const existing = saved.findIndex(c => c.name === data.name);
            if (existing >= 0) {{
              if (!confirm("'" + data.name + "' already exists. Overwrite?")) {{
                skipped++;
                remaining--;
                if (remaining === 0) finalize();
                return;
              }}
              saved.splice(existing, 1);
            }}
            saved.push({{ name: data.name, slots: data.slots }});
            imported++;
          }}
        }} catch (err) {{
          skipped++;
        }}
        remaining--;
        if (remaining === 0) finalize();
      }};
      reader.readAsText(file);
    }};

    const finalize = () => {{
      setSavedComparisons(saved);
      if (imported > 0) {{
        alert("Imported " + imported + " comparison(s)." + (skipped > 0 ? " Skipped " + skipped + "." : ""));
      }} else {{
        alert("No comparisons were imported." + (skipped > 0 ? " " + skipped + " file(s) skipped or invalid." : ""));
      }}
      this.renderPanel(state.activeTab);
    }};

    for (const file of files) processFile(file);
    fileEl.value = "";
  }},

  deleteSavedComparisonPrompt() {{
    const saved = getSavedComparisons();
    if (saved.length === 0) return;
    const names = saved.map((c, i) => (i + 1) + ". " + c.name).join("\\n");
    const choice = prompt("Enter the number of the comparison to delete:\\n\\n" + names);
    if (!choice) return;
    const idx = parseInt(choice) - 1;
    if (idx >= 0 && idx < saved.length) {{
      saved.splice(idx, 1);
      setSavedComparisons(saved);
      this.renderPanel(state.activeTab);
    }}
  }},

  // ── Allocation Bar (pure DOM, vertical stacked) ──

  // Brand chart color progression -- each asset gets its own color
  ALLOC_PALETTE: [
    "#323A46", "#3A6A9C", "#7DA5CE", "#14CFA6", "#0C7C64", "#EBE96A",
    "#FFE885", "#366390", "#23405E", "#3BB823", "#B4B218", "#10A685",
    "#5287BF", "#97B7D8", "#31EBC2", "#AAED9D", "#EFED88", "#3F3B47",
  ],

  renderAllocBar(portfolioIdx) {{
    const container = document.getElementById(`rsv-alloc-vis-${{portfolioIdx}}`);
    if (!container) return;

    const p = state.portfolios[portfolioIdx];
    const coreAssets = p.core.filter(r => r.asset && r.weight > 0);
    const stackAssets = p.stack.filter(r => r.asset && r.weight > 0);

    if (coreAssets.length === 0 && stackAssets.length === 0) {{
      container.innerHTML = '<div class="rsv-alloc-empty">Add assets to see allocation</div>';
      return;
    }}

    // Build segments: core first (bottom), then stack on top
    // Each asset gets a unique color from the palette
    const segments = [];
    let colorIdx = 0;
    for (const r of coreAssets) {{
      segments.push({{ name: r.asset, weight: r.weight, color: this.ALLOC_PALETTE[colorIdx % this.ALLOC_PALETTE.length], section: "core" }});
      colorIdx++;
    }}
    for (const r of stackAssets) {{
      segments.push({{ name: r.asset, weight: r.weight, color: this.ALLOC_PALETTE[colorIdx % this.ALLOC_PALETTE.length], section: "stack" }});
      colorIdx++;
    }}

    const totalWeight = segments.reduce((s, seg) => s + seg.weight, 0);
    if (totalWeight <= 0) {{
      container.innerHTML = '<div class="rsv-alloc-empty">Add assets to see allocation</div>';
      return;
    }}

    const coreTotal = coreAssets.reduce((s, r) => s + r.weight, 0);

    // Build bar segments (bottom to top) and labels
    let barHTML = '<div class="rsv-alloc-bar-outer">';

    // Total label area at top
    barHTML += `<div class="rsv-alloc-bar-top"><span class="rsv-alloc-pct-label" style="bottom:0;">${{totalWeight.toFixed(0)}}%</span></div>`;

    // Bar body (segments + 100% line)
    barHTML += '<div class="rsv-alloc-bar-body">';
    barHTML += '<div class="rsv-alloc-bar">';

    let labelsHTML = '<div class="rsv-alloc-labels" style="padding-top:20px;">';

    for (const seg of segments) {{
      const pct = seg.weight / totalWeight;
      barHTML += `<div class="rsv-alloc-segment" style="flex:${{pct}};background:${{seg.color}};"></div>`;
      labelsHTML += `<div class="rsv-alloc-label" style="flex:${{pct}};">
        <span class="rsv-alloc-label-dot" style="background:${{seg.color}};"></span>
        <span class="rsv-alloc-label-text">${{seg.name}}</span>
        <span class="rsv-alloc-label-pct">${{seg.weight.toFixed(0)}}%</span>
      </div>`;
    }}

    barHTML += '</div>'; // close .rsv-alloc-bar

    // Add 100% dashed line if there are stack overlays (total > core)
    if (stackAssets.length > 0 && totalWeight > coreTotal && coreTotal > 0) {{
      const corePct = (coreTotal / totalWeight) * 100;
      barHTML += `<div class="rsv-alloc-100-line" style="bottom:${{corePct}}%;"></div>`;
      barHTML += `<span class="rsv-alloc-pct-label" style="bottom:${{corePct}}%;transform:translateY(50%);">100%</span>`;
    }}

    barHTML += '</div>'; // close .rsv-alloc-bar-body
    barHTML += '</div>'; // close .rsv-alloc-bar-outer
    labelsHTML += '</div>';
    container.innerHTML = barHTML + labelsHTML;
  }},

  // ── PDF Generation (Phase 6) -- Advisor Guide Style ──
  // Portrait US Letter (8.5 x 11 in), DM Sans, advisor guide header/footer,
  // teal accent bars, two charts per page where possible.

  // ── Portfolio Configuration Block (Page 2 of single-portfolio PDF) ──
  _pdfRenderPortfolioConfig(doc, portfolioIdx, startY) {{
    const p = state.portfolios[portfolioIdx];
    const {{ pw, ml, mr, contentW, navy, teal, textDark, textSec, sectionGray, borderGray }} = this._pdfC();
    const coreAssets = p.core.filter(r => r.asset && r.weight > 0);
    const stackAssets = p.stack.filter(r => r.asset && r.weight > 0);
    const coreTotal = coreAssets.reduce((s, r) => s + r.weight, 0);
    const stackTotal = stackAssets.reduce((s, r) => s + r.weight, 0);
    const notional = coreTotal + stackTotal;
    const allNames = [...coreAssets, ...stackAssets].map(r => r.asset);
    const range = allNames.length > 0 ? findCommonDateRange(allNames) : {{ start: null, end: null }};

    const hexToRgb = (hex) => {{
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return [r, g, b];
    }};

    let y = startY;
    y = this._pdfSectionHeading(doc, "Portfolio Configuration", y);
    y += 1;

    // Summary stats row: Core | Stack | Notional | Start Date
    const summaryItems = [
      ["Core Allocation", coreTotal.toFixed(1) + "%"],
      ["Stack Overlay", stackTotal.toFixed(1) + "%"],
      ["Notional Exposure", notional.toFixed(1) + "%"],
      ["Asset Class Start Date", range.start || "N/A"],
    ];
    const itemW = contentW / summaryItems.length;
    doc.setFillColor(sectionGray[0], sectionGray[1], sectionGray[2]);
    doc.rect(ml, y, contentW, 12, "F");
    summaryItems.forEach((item, i) => {{
      const cx = ml + i * itemW + itemW / 2;
      doc.setFont("DMSans", "normal");
      doc.setFontSize(6.5);
      doc.setTextColor(textSec[0], textSec[1], textSec[2]);
      doc.text(item[0], cx, y + 4, {{ align: "center" }});
      doc.setFont("DMSans", "bold");
      doc.setFontSize(9);
      doc.setTextColor(textDark[0], textDark[1], textDark[2]);
      doc.text(item[1], cx, y + 10, {{ align: "center" }});
    }});
    y += 20;

    // Layout: [Core Table | gap | Stack Table | gap | pct labels | Bar]
    if (coreAssets.length > 0 || stackAssets.length > 0) {{
      const segments = [];
      let colorIdx = 0;
      for (const r of coreAssets) {{
        segments.push({{ name: r.asset, weight: r.weight, color: this.ALLOC_PALETTE[colorIdx % this.ALLOC_PALETTE.length], section: "core" }});
        colorIdx++;
      }}
      for (const r of stackAssets) {{
        segments.push({{ name: r.asset, weight: r.weight, color: this.ALLOC_PALETTE[colorIdx % this.ALLOC_PALETTE.length], section: "stack" }});
        colorIdx++;
      }}
      const totalWeight = segments.reduce((s, seg) => s + seg.weight, 0);
      const maxRows = Math.max(coreAssets.length, stackAssets.length);

      // Dimensions
      const barW = 24;          // wider bar
      const pctLabelW = 14;     // space for "100%" / "120%" labels
      const tableGap = 5;
      const barGap = 5;         // gap between tables and bar zone
      const rightPad = 10;      // white space to the right of bar
      const tablesW = contentW - barW - pctLabelW - barGap - rightPad;
      const coreTableW = (tablesW - tableGap) / 2;
      const stackTableW = (tablesW - tableGap) / 2;
      const rowH = 6.5;
      const headerH = 7;
      const barR = 3;           // rounded corner radius

      const coreX = ml;
      const stackX = ml + coreTableW + tableGap;
      const barZoneX = ml + tablesW + barGap; // start of pct labels + bar
      const barX = barZoneX + pctLabelW;

      // ── Core Portfolio table ──
      doc.setFillColor(navy[0], navy[1], navy[2]);
      doc.rect(coreX, y, coreTableW, headerH, "F");
      doc.setFont("DMSans", "bold"); doc.setFontSize(6.5); doc.setTextColor(255, 255, 255);
      doc.text("Core Portfolio", coreX + coreTableW / 2, y + 5, {{ align: "center" }});

      const subY = y + headerH;
      doc.setFillColor(sectionGray[0], sectionGray[1], sectionGray[2]);
      doc.rect(coreX, subY, coreTableW, rowH, "F");
      doc.setFont("DMSans", "bold"); doc.setFontSize(6); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
      doc.text("Asset Class", coreX + 3, subY + 4.5);
      doc.text("Weight", coreX + coreTableW - 3, subY + 4.5, {{ align: "right" }});

      const coreSegs = segments.filter(s => s.section === "core");
      for (let i = 0; i < coreSegs.length; i++) {{
        const ry = subY + rowH + i * rowH;
        if (i % 2 === 0) {{ doc.setFillColor(248, 248, 248); doc.rect(coreX, ry, coreTableW, rowH, "F"); }}
        const seg = coreSegs[i];
        const rgb = hexToRgb(seg.color);
        doc.setFillColor(rgb[0], rgb[1], rgb[2]);
        doc.roundedRect(coreX + 3, ry + 1.5, 2.4, 2.4, 0.5, 0.5, "F");
        doc.setFont("DMSans", "normal"); doc.setFontSize(6.5); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
        doc.text(seg.name, coreX + 7, ry + 4.5);
        doc.setFont("DMSans", "bold");
        doc.text(seg.weight.toFixed(0) + "%", coreX + coreTableW - 3, ry + 4.5, {{ align: "right" }});
        doc.setDrawColor(borderGray[0], borderGray[1], borderGray[2]); doc.setLineWidth(0.1);
        doc.line(coreX, ry + rowH, coreX + coreTableW, ry + rowH);
      }}
      const coreTotalY = subY + rowH + coreSegs.length * rowH;
      doc.setFillColor(sectionGray[0], sectionGray[1], sectionGray[2]);
      doc.rect(coreX, coreTotalY, coreTableW, rowH, "F");
      doc.setFont("DMSans", "bold"); doc.setFontSize(6.5); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
      doc.text("Total", coreX + 3, coreTotalY + 4.5);
      doc.text(coreTotal.toFixed(0) + "%", coreX + coreTableW - 3, coreTotalY + 4.5, {{ align: "right" }});

      // ── Stack Overlay table ──
      if (stackAssets.length > 0) {{
        doc.setFillColor(navy[0], navy[1], navy[2]);
        doc.rect(stackX, y, stackTableW, headerH, "F");
        doc.setFont("DMSans", "bold"); doc.setFontSize(6.5); doc.setTextColor(255, 255, 255);
        doc.text("Stack Overlay", stackX + stackTableW / 2, y + 5, {{ align: "center" }});

        const subYs = y + headerH;
        doc.setFillColor(sectionGray[0], sectionGray[1], sectionGray[2]);
        doc.rect(stackX, subYs, stackTableW, rowH, "F");
        doc.setFont("DMSans", "bold"); doc.setFontSize(6); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Asset Class", stackX + 3, subYs + 4.5);
        doc.text("Weight", stackX + stackTableW - 3, subYs + 4.5, {{ align: "right" }});

        const stackSegs = segments.filter(s => s.section === "stack");
        for (let i = 0; i < stackSegs.length; i++) {{
          const ry = subYs + rowH + i * rowH;
          if (i % 2 === 0) {{ doc.setFillColor(248, 248, 248); doc.rect(stackX, ry, stackTableW, rowH, "F"); }}
          const seg = stackSegs[i];
          const rgb = hexToRgb(seg.color);
          doc.setFillColor(rgb[0], rgb[1], rgb[2]);
          doc.roundedRect(stackX + 3, ry + 1.5, 2.4, 2.4, 0.5, 0.5, "F");
          doc.setFont("DMSans", "normal"); doc.setFontSize(6.5); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
          doc.text(seg.name, stackX + 7, ry + 4.5);
          doc.setFont("DMSans", "bold");
          doc.text(seg.weight.toFixed(0) + "%", stackX + stackTableW - 3, ry + 4.5, {{ align: "right" }});
          doc.setDrawColor(borderGray[0], borderGray[1], borderGray[2]); doc.setLineWidth(0.1);
          doc.line(stackX, ry + rowH, stackX + stackTableW, ry + rowH);
        }}
        const stackTotalY = subYs + rowH + stackSegs.length * rowH;
        doc.setFillColor(sectionGray[0], sectionGray[1], sectionGray[2]);
        doc.rect(stackX, stackTotalY, stackTableW, rowH, "F");
        doc.setFont("DMSans", "bold"); doc.setFontSize(6.5); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
        doc.text("Total", stackX + 3, stackTotalY + 4.5);
        doc.text(stackTotal.toFixed(0) + "%", stackX + stackTableW - 3, stackTotalY + 4.5, {{ align: "right" }});
      }}

      // ── Vertical allocation bar (right of tables, rounded) ──
      const barH = headerH + rowH + maxRows * rowH + rowH; // match table height
      const barTop = y;

      // Notional exposure label above bar
      doc.setFont("DMSans", "bold"); doc.setFontSize(8); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
      doc.text(totalWeight.toFixed(0) + "%", barX + barW / 2, barTop - 2, {{ align: "center" }});

      // Draw rounded bar using clip path
      doc.saveGraphicsState();
      doc.roundedRect(barX, barTop, barW, barH, barR, barR, null);
      doc.clip("nonzero");
      doc.discardPath();

      // Draw segments bottom-to-top (clipped to rounded rect)
      let segY = barTop + barH;
      for (const seg of segments) {{
        const segH = (seg.weight / totalWeight) * barH;
        segY -= segH;
        const rgb = hexToRgb(seg.color);
        doc.setFillColor(rgb[0], rgb[1], rgb[2]);
        doc.rect(barX, segY, barW, segH, "F");
      }}

      // 100% dashed line (inside clip so it stays within rounded edges)
      if (stackAssets.length > 0 && coreTotal > 0 && totalWeight > coreTotal) {{
        const lineY = barTop + barH - (coreTotal / totalWeight) * barH;
        doc.setDrawColor(255, 255, 255);
        doc.setLineWidth(0.6);
        // Dashed line across bar
        const dashLen = 1.8, gapLen = 1.4;
        let dx = barX;
        while (dx < barX + barW) {{
          const x2 = Math.min(dx + dashLen, barX + barW);
          doc.line(dx, lineY, x2, lineY);
          dx += dashLen + gapLen;
        }}
      }}

      doc.restoreGraphicsState();

      // 100% label to the left of the bar (outside clip)
      if (stackAssets.length > 0 && coreTotal > 0 && totalWeight > coreTotal) {{
        const lineY = barTop + barH - (coreTotal / totalWeight) * barH;
        doc.setFont("DMSans", "bold"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("100%", barX - 2, lineY + 1, {{ align: "right" }});
      }}

      y = barTop + barH + 6;
    }}

    return y;
  }},

  _pdfSetupFonts(doc) {{
    doc.addFileToVFS("DMSans-Regular.ttf", PDF_FONT_REGULAR);
    doc.addFileToVFS("DMSans-Bold.ttf", PDF_FONT_BOLD);
    doc.addFileToVFS("DMSans-Italic.ttf", PDF_FONT_ITALIC);
    doc.addFileToVFS("DMSans-BoldItalic.ttf", PDF_FONT_BOLDITALIC);
    doc.addFont("DMSans-Regular.ttf", "DMSans", "normal");
    doc.addFont("DMSans-Bold.ttf", "DMSans", "bold");
    doc.addFont("DMSans-Italic.ttf", "DMSans", "italic");
    doc.addFont("DMSans-BoldItalic.ttf", "DMSans", "bolditalic");
    doc.setFont("DMSans", "normal");
  }},

  // Portrait US Letter constants (mm)
  _pdfC() {{
    const pw = 215.9, ph = 279.4; // portrait letter
    const ml = 10, mr = 10, mt = 10, mb = 10; // margins
    const contentW = pw - ml - mr; // ~196mm
    const navy = [23, 44, 58];
    const teal = [20, 207, 166];
    const textDark = [44, 54, 65];
    const textSec = [98, 92, 109];
    const gray = [160, 160, 160];
    const coverDark = [23, 44, 58];
    const sectionGray = [240, 241, 241];
    const borderGray = [191, 191, 191];
    // Interior page zones (mm from top)
    const headerH = 20;       // header zone height
    const footerH = 10;       // footer zone height
    const contentTop = 25;    // content starts here
    const contentBottom = ph - 14; // content ends here (above footer)
    return {{ pw, ph, ml, mr, mt, mb, contentW, navy, teal, textDark, textSec, gray, coverDark, sectionGray, borderGray, headerH, footerH, contentTop, contentBottom }};
  }},

  // Advisor guide-style interior header: logo left, right-aligned title + teal accent bar
  _pdfHeader(doc, portfolioName) {{
    const {{ pw, ml, mr, navy, teal, textDark }} = this._pdfC();
    // Logo (black variant, left side)
    try {{ doc.addImage(PDF_LOGO_BLACK, "PNG", ml, 5, 39, 7, "LOGO_BLACK", "FAST"); }} catch(e) {{}}
    // Right side: series title + portfolio name
    doc.setFont("DMSans", "bold");
    doc.setFontSize(8);
    doc.setTextColor(teal[0], teal[1], teal[2]);
    doc.text("Return Stacked\u00AE Portfolio Visualizer", pw - mr - 3.5, 8, {{ align: "right" }});
    doc.setFont("DMSans", "normal");
    doc.setFontSize(7);
    doc.setTextColor(textDark[0], textDark[1], textDark[2]);
    doc.text(portfolioName, pw - mr - 3.5, 12, {{ align: "right" }});
    // Teal accent bar on far right edge
    doc.setFillColor(teal[0], teal[1], teal[2]);
    doc.rect(pw - 3.5, 0, 3.5, 20, "F");
  }},

  // Advisor guide-style footer: dark icon square | teal band | white URL area
  _pdfFooter(doc, pageNum, totalPages) {{
    const {{ pw, ph, navy, teal, textDark, coverDark }} = this._pdfC();
    const fh = 10; // footer height
    const fy = ph - fh;
    // Dark icon square (left)
    doc.setFillColor(coverDark[0], coverDark[1], coverDark[2]);
    doc.rect(0, fy, fh, fh, "F");
    try {{ doc.addImage(PDF_LOGO_WHITE, "PNG", 1.5, fy + 1.5, 7, 7, "LOGO_WHITE", "FAST"); }} catch(e) {{}}
    // Teal band (center)
    const urlAreaW = 55;
    doc.setFillColor(teal[0], teal[1], teal[2]);
    doc.rect(fh, fy, pw - fh - urlAreaW, fh, "F");
    // White URL area (right)
    doc.setFillColor(255, 255, 255);
    doc.rect(pw - urlAreaW, fy, urlAreaW, fh, "F");
    doc.setFont("DMSans", "bold");
    doc.setFontSize(7);
    doc.setTextColor(textDark[0], textDark[1], textDark[2]);
    doc.text("www.returnstacked.com", pw - 5, fy + 6, {{ align: "right" }});
    // Page number on teal band
    if (pageNum && totalPages) {{
      doc.setFont("DMSans", "normal");
      doc.setFontSize(6);
      doc.setTextColor(255, 255, 255);
      doc.text("Page " + pageNum + " of " + totalPages, pw - urlAreaW - 4, fy + 6, {{ align: "right" }});
    }}
  }},

  // Section heading with teal accent rectangle (advisor guide style)
  _pdfSectionHeading(doc, text, y) {{
    const {{ ml, teal, textDark }} = this._pdfC();
    // Teal accent rectangle
    doc.setFillColor(teal[0], teal[1], teal[2]);
    doc.rect(ml, y - 3.5, 2, 5, "F");
    // Heading text
    doc.setFont("DMSans", "bold");
    doc.setFontSize(12);
    doc.setTextColor(textDark[0], textDark[1], textDark[2]);
    doc.text(text, ml + 5, y);
    return y + 6;
  }},

  // Subsection heading (no accent bar)
  _pdfSubheading(doc, text, y) {{
    const {{ ml, textDark }} = this._pdfC();
    doc.setFont("DMSans", "bold");
    doc.setFontSize(10);
    doc.setTextColor(textDark[0], textDark[1], textDark[2]);
    doc.text(text, ml, y);
    return y + 5;
  }},

  // Draw a chart image preserving its exact canvas aspect ratio
  // chartObj = {{ data, width, height, alias }} from _captureChart
  _pdfDrawChart(doc, chartObj, x, y, maxW, maxH) {{
    if (!chartObj || !chartObj.data) return y;
    const aspect = chartObj.width / chartObj.height;
    let drawW = maxW;
    let drawH = drawW / aspect;
    if (drawH > maxH) {{
      drawH = maxH;
      drawW = drawH * aspect;
    }}
    const offX = x + (maxW - drawW) / 2;
    const fmt = chartObj.data.startsWith("data:image/jpeg") ? "JPEG" : "PNG";
    if (chartObj.alias) {{
      doc.addImage(chartObj.data, fmt, offX, y, drawW, drawH, chartObj.alias, "FAST");
    }} else {{
      doc.addImage(chartObj.data, fmt, offX, y, drawW, drawH, undefined, "FAST");
    }}
    return y + drawH;
  }},

  // Source note (matches stats table metric font size)
  _pdfSourceNote(doc, text, y) {{
    const {{ ml, contentW }} = this._pdfC();
    doc.setFont("DMSans", "normal");
    doc.setFontSize(6);
    doc.setTextColor(98, 92, 109);
    const lines = doc.splitTextToSize(text, contentW);
    doc.text(lines, ml, y);
    return y + lines.length * 2.6;
  }},

  _pdfBuildConfigLabel(p) {{
    const coreAssets = p.core.filter(r => r.asset && r.weight > 0);
    const stackAssets = p.stack.filter(r => r.asset && r.weight > 0);
    const parts = [];
    if (coreAssets.length > 0) {{
      parts.push(coreAssets.map(r => r.weight + "% " + r.asset).join(" / "));
    }}
    if (stackAssets.length > 0) {{
      const stackTotal = stackAssets.reduce((s, r) => s + r.weight, 0);
      parts.push("Stack: " + stackTotal + "% (" + stackAssets.map(r => r.weight + "% " + r.asset).join(", ") + ")");
    }}
    return parts.join("  |  ");
  }},

  _pdfBuildSourceText(portfolioIdx) {{
    // Use the same full disclaimer that appears under the calendar year returns table
    return this.generatePortfolioDisclaimer(portfolioIdx);
  }},

  _captureChart(chartKey) {{
    const chart = this._charts[chartKey];
    if (!chart) return null;
    const src = chart.canvas;
    // Draw onto a white-background temp canvas (JPEG has no transparency)
    const tmp = document.createElement("canvas");
    tmp.width = src.width;
    tmp.height = src.height;
    const ctx = tmp.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, tmp.width, tmp.height);
    ctx.drawImage(src, 0, 0);
    return {{
      data: tmp.toDataURL("image/jpeg", 0.95),
      width: src.width,
      height: src.height,
    }};
  }},

  // ── Chart PNG / Table CSV Export ──
  _disclaimerDownloadedForSession: false,
  _blackLogoImg: null,

  _chartLabelFor(portfolioIdx, slot) {{
    const map = {{
      returnRisk: {{ a: "Return vs Volatility", b: "Return vs Max Drawdown" }},
      growthDD:   {{ a: "Growth of $1", b: "Drawdown" }},
      rollingReturns: {{ a: "Rolling Returns", b: "Rolling Outperformance" }},
      calendarYear:   {{ a: "Calendar Year Returns", b: "" }},
      scaledBlend:    {{ a: "Scaled Stack Blend", b: "Rolling Correlation" }},
    }};
    const type = this._activeChartType[portfolioIdx] || "growthDD";
    return (map[type] && map[type][slot]) || "Chart";
  }},

  _safeFilename(s) {{
    return String(s || "chart")
      .replace(/[\\/\\\\?%*:|"<>]+/g, "")
      .replace(/\\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^[-.]+|[-.]+$/g, "")
      .slice(0, 120) || "chart";
  }},

  _triggerFileDownload(data, filename, mime) {{
    const blob = (data instanceof Blob) ? data : new Blob([data], {{ type: mime || "application/octet-stream" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }},

  _triggerDataUrlDownload(dataUrl, filename) {{
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }},

  _loadBlackLogo() {{
    if (this._blackLogoImg) return Promise.resolve(this._blackLogoImg);
    return new Promise((resolve) => {{
      const img = new Image();
      img.onload = () => {{ this._blackLogoImg = img; resolve(img); }};
      img.onerror = () => resolve(null);
      img.src = PDF_LOGO_BLACK;
    }});
  }},

  _downloadDisclaimerOnce(disclaimerText) {{
    if (this._disclaimerDownloadedForSession) return;
    if (!disclaimerText) return;
    this._disclaimerDownloadedForSession = true;
    const preface = "Return Stacked(R) Portfolio Visualizer -- Disclosures\\n"
                  + "-------------------------------------------------------\\n\\n";
    this._triggerFileDownload(preface + disclaimerText + "\\n", "Return-Stacked-Disclosures.txt", "text/plain;charset=utf-8");
  }},

  async exportChartPng(chartKey, filename, disclaimerText) {{
    const chart = this._charts[chartKey];
    if (!chart) return;
    const src = chart.canvas;
    const cssW = src.clientWidth || src.width;
    const cssH = src.clientHeight || src.height;

    // Bump Chart.js backing resolution for a native high-DPI render (2 frames for layout + draw)
    const savedDPR = chart.options.devicePixelRatio;
    const targetDPR = Math.max(3, 2400 / cssW);
    try {{ chart.options.devicePixelRatio = targetDPR; chart.resize(); }} catch (e) {{}}
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));

    const chartW = Math.round(cssW * targetDPR);
    const chartH = Math.round(cssH * targetDPR);
    // Dedicated header band keeps the logo from overlapping chart content
    const headerH = Math.max(Math.round(chartW * 0.055), 80);
    const outW = chartW;
    const outH = chartH + headerH;

    const tmp = document.createElement("canvas");
    tmp.width = outW;
    tmp.height = outH;
    const ctx = tmp.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, outW, outH);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    const logo = await this._loadBlackLogo();
    if (logo && logo.naturalWidth > 0) {{
      const logoH = headerH * 0.68;
      const aspect = logo.naturalWidth / logo.naturalHeight;
      const logoW = logoH * aspect;
      const padX = outW * 0.014;
      const padY = (headerH - logoH) / 2;
      ctx.drawImage(logo, outW - logoW - padX, padY, logoW, logoH);
    }}

    // Draw chart beneath the header band
    ctx.drawImage(src, 0, headerH, chartW, chartH);

    const dataUrl = tmp.toDataURL("image/png");

    // Restore original DPR before triggering download
    try {{ chart.options.devicePixelRatio = savedDPR; chart.resize(); }} catch (e) {{}}

    this._triggerDataUrlDownload(dataUrl, filename + ".png");
    this._downloadDisclaimerOnce(disclaimerText);
  }},

  downloadPortfolioChart(portfolioIdx, slot) {{
    const p = state.portfolios[portfolioIdx];
    if (!p) return;
    const chartName = this._chartLabelFor(portfolioIdx, slot);
    const filename = this._safeFilename((p.name || ("Portfolio " + (portfolioIdx + 1))) + "_" + chartName);
    const disclaimer = this.generatePortfolioDisclaimer(portfolioIdx);
    this.exportChartPng("rsv-chart-" + portfolioIdx + "-" + slot, filename, disclaimer);
  }},

  downloadComparisonChart(chartKey, chartName) {{
    const active = [];
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      if (state.portfolios[i].enabled && state.portfolios[i].result) active.push(i);
    }}
    let disclaimer = "";
    if (active.length > 0) {{
      const r0 = state.portfolios[active[0]].result;
      const cr = this._getComparisonCommonRange ? this._getComparisonCommonRange(active) : {{ start: r0.period.start, end: r0.period.end }};
      disclaimer = this.generateMergedDisclaimer(active, cr.start, cr.end);
    }}
    const filename = this._safeFilename("Portfolio-Comparison_" + chartName);
    this.exportChartPng(chartKey, filename, disclaimer);
  }},

  _extractTableRows(table) {{
    const rows = [];
    for (const tr of table.querySelectorAll("tr")) {{
      const cells = [];
      for (const cell of tr.querySelectorAll("th, td")) {{
        let txt = (cell.innerText || cell.textContent || "").trim().replace(/\\s+/g, " ");
        if (/["\\n,]/.test(txt)) txt = '"' + txt.replace(/"/g, '""') + '"';
        cells.push(txt);
      }}
      if (cells.length) rows.push(cells.join(","));
    }}
    return rows.join("\\n");
  }},

  downloadSectionCsv(btnEl, filename) {{
    const section = btnEl.closest(".rsv-dl-section");
    const table = section && section.querySelector("table");
    if (!table) return;
    const csv = this._extractTableRows(table);
    this._triggerFileDownload("\\ufeff" + csv, this._safeFilename(filename) + ".csv", "text/csv;charset=utf-8");
  }},

  // ── Cover Page (advisor guide style) ──
  _pdfRenderCover(doc, portfolioName, configLabel, period) {{
    const {{ pw, ph, ml, navy, teal, coverDark }} = this._pdfC();

    // White top bar with logo
    doc.setFillColor(255, 255, 255);
    doc.rect(0, 0, pw, 28, "F");
    try {{ doc.addImage(PDF_LOGO_BLACK, "PNG", ml + 4, 7, 55, 10, "LOGO_BLACK", "FAST"); }} catch(e) {{}}

    // Dark banner with backdrop
    const bannerTop = 28;
    const bannerH = 120;
    doc.setFillColor(coverDark[0], coverDark[1], coverDark[2]);
    doc.rect(0, bannerTop, pw, bannerH, "F");
    if (PDF_BG_IMAGE) {{
      try {{ doc.addImage(PDF_BG_IMAGE, "PNG", 0, bannerTop, pw, bannerH, "BG_IMAGE", "FAST"); }} catch(e) {{}}
    }}
    // Translucent overlay
    doc.setGState(new doc.GState({{ opacity: 0.5 }}));
    doc.setFillColor(0, 0, 0);
    doc.rect(0, bannerTop, pw, bannerH, "F");
    doc.setGState(new doc.GState({{ opacity: 1 }}));
    // Teal left accent bar on banner
    doc.setFillColor(teal[0], teal[1], teal[2]);
    doc.rect(0, bannerTop, 3.5, bannerH, "F");

    // Banner title text -- left edge at teal accent bar + padding
    const tx = ml + 8;
    const maxTitleW = pw - tx - ml - 10; // max width for wrapping
    let y = bannerTop + 20;
    doc.setFont("DMSans", "normal");
    doc.setFontSize(14);
    doc.setTextColor(255, 255, 255);
    doc.text("The", tx, y);
    doc.setFont("DMSans", "bold");
    doc.text(" Return Stacked\u00AE", tx + doc.getTextWidth("The "), y);
    y += 7;
    doc.setFont("DMSans", "normal");
    doc.setFontSize(14);
    doc.text("Portfolio Visualizer", tx, y);
    y += 14;
    // Portfolio name -- wrap to multiple lines if needed
    doc.setFont("DMSans", "bold");
    doc.setFontSize(26);
    doc.setTextColor(teal[0], teal[1], teal[2]);
    const nameLines = doc.splitTextToSize(portfolioName, maxTitleW);
    doc.text(nameLines, tx, y);

    // Intro zone below banner
    y = bannerTop + bannerH + 18;
    doc.setFont("DMSans", "bold");
    doc.setFontSize(20);
    doc.setTextColor(44, 54, 65);
    doc.text("Portfolio Analysis Report", pw / 2, y, {{ align: "center" }});
    y += 16;

    // Config details
    doc.setFont("DMSans", "bold");
    doc.setFontSize(11);
    doc.setTextColor(teal[0], teal[1], teal[2]);
    doc.text("PORTFOLIO CONFIGURATION", tx, y);
    y += 3;
    doc.setDrawColor(teal[0], teal[1], teal[2]);
    doc.setLineWidth(0.4);
    doc.line(tx, y, tx + 82, y);
    y += 7;
    doc.setFont("DMSans", "normal");
    doc.setFontSize(11);
    doc.setTextColor(44, 54, 65);
    const cfgLines = doc.splitTextToSize(configLabel, pw - tx - ml - 4);
    doc.text(cfgLines, tx, y);
    y += cfgLines.length * 5.5 + 6;

    if (period) {{
      doc.setFont("DMSans", "italic");
      doc.setFontSize(10);
      doc.setTextColor(98, 92, 109);
      doc.text("Data Period: " + period.start + " \u2013 " + period.end, tx, y);
    }}

    // Footer info
    doc.setFont("DMSans", "normal");
    doc.setFontSize(9);
    doc.setTextColor(130, 130, 130);
    doc.text("\u00A9 Return Stacked\u00AE Portfolio Solutions, " + new Date().getFullYear(), ml, ph - 12);
    const dateStr = new Date().toLocaleDateString("en-US", {{ year: "numeric", month: "long", day: "numeric" }});
    doc.text(dateStr, ml, ph - 7);
  }},

  // ── Stats Table ──
  _pdfRenderStatsTable(doc, p, startY) {{
    const {{ pw, ml, mr, contentW, navy, teal, textDark }} = this._pdfC();
    const r = p.result;
    if (!r) return startY;
    const isExcess = !r.hasCore;
    const coreLbl = isExcess ? "Excess Return" : "Core";

    let y = startY;
    y = this._pdfSectionHeading(doc, "Performance Statistics", y);
    doc.setFont("DMSans", "normal");
    doc.setFontSize(7);
    doc.setTextColor(98, 92, 109);
    doc.text("Full analysis period: " + r.period.start + " \u2013 " + r.period.end, ml + 5, y);
    y += 5;

    const fmt = (v, pct) => v == null ? "\u2014" : (pct ? (v * 100).toFixed(2) + "%" : v.toFixed(2));
    const fmtDiff = (a, b, pct, lower) => {{
      if (a == null || b == null) return {{ text: "\u2014", color: textDark }};
      const d = b - a;
      const text = (d >= 0 ? "+" : "") + (pct ? (d * 100).toFixed(2) + "%" : d.toFixed(2));
      const good = lower ? d < 0 : d > 0;
      return {{ text, color: good ? [20, 160, 100] : d === 0 ? textDark : [200, 60, 60] }};
    }};

    const rows = [
      ["Annualized Return", fmt(r.coreStats.annualizedReturn, true), fmt(r.stackedStats.annualizedReturn, true), fmtDiff(r.coreStats.annualizedReturn, r.stackedStats.annualizedReturn, true, false)],
      ["Annualized Volatility", fmt(r.coreStats.volatility, true), fmt(r.stackedStats.volatility, true), fmtDiff(r.coreStats.volatility, r.stackedStats.volatility, true, true)],
      ["Maximum Drawdown", fmt(r.coreStats.maxDrawdown, true), fmt(r.stackedStats.maxDrawdown, true), fmtDiff(r.coreStats.maxDrawdown, r.stackedStats.maxDrawdown, true, true)],
      ["Sharpe Ratio", fmt(r.coreStats.sharpe, false), fmt(r.stackedStats.sharpe, false), fmtDiff(r.coreStats.sharpe, r.stackedStats.sharpe, false, false)],
      ["Sortino Ratio", fmt(r.coreStats.sortino, false), fmt(r.stackedStats.sortino, false), fmtDiff(r.coreStats.sortino, r.stackedStats.sortino, false, false)],
      ["Tracking Error", "\u2014", fmt(r.trackingError, true), {{ text: "\u2014", color: textDark }}],
    ];
    const headers = ["Metric", coreLbl, "Stacked", "Difference"];
    const tableX = ml;
    const tableW = contentW;
    const colW = [tableW * 0.32, tableW * 0.22, tableW * 0.22, tableW * 0.24];
    const rowH = 8;

    // Header
    doc.setFillColor(navy[0], navy[1], navy[2]);
    doc.rect(tableX, y, tableW, rowH, "F");
    doc.setFont("DMSans", "bold");
    doc.setFontSize(7);
    doc.setTextColor(255, 255, 255);
    let cx = tableX;
    headers.forEach((h, i) => {{
      doc.text(h, i === 0 ? cx + 4 : cx + colW[i] - 4, y + 5.5, {{ align: i === 0 ? "left" : "right" }});
      cx += colW[i];
    }});
    y += rowH;

    rows.forEach((row, ri) => {{
      if (ri % 2 === 0) {{
        doc.setFillColor(240, 241, 241);
        doc.rect(tableX, y, tableW, rowH, "F");
      }}
      cx = tableX;
      row.forEach((cell, ci) => {{
        doc.setFont("DMSans", "normal");
        doc.setFontSize(7);
        if (ci === 0) {{
          doc.setTextColor(textDark[0], textDark[1], textDark[2]);
          doc.text(cell, cx + 4, y + 5.5);
        }} else if (ci === 3) {{
          const c = cell.color || textDark;
          doc.setTextColor(c[0], c[1], c[2]);
          doc.text(cell.text, cx + colW[ci] - 4, y + 5.5, {{ align: "right" }});
        }} else {{
          doc.setTextColor(textDark[0], textDark[1], textDark[2]);
          doc.text(cell, cx + colW[ci] - 4, y + 5.5, {{ align: "right" }});
        }}
        cx += colW[ci];
      }});
      doc.setDrawColor(191, 191, 191);
      doc.setLineWidth(0.1);
      doc.line(tableX, y + rowH, tableX + tableW, y + rowH);
      y += rowH;
    }});
    y += 3;
    doc.setFont("DMSans", "normal");
    doc.setFontSize(6);
    doc.setTextColor(98, 92, 109);
    doc.text("Green = improved outcome, Red = worsened outcome in the Difference column.", ml, y);
    return y + 4;
  }},

  // ── Disclosures text block ──
  _pdfRenderDisclosures(doc, startY) {{
    const {{ ml, contentW, textDark }} = this._pdfC();
    let y = this._pdfSectionHeading(doc, "Important Disclosures on Hypothetical Performance", startY);
    y += 2;
    doc.setFont("DMSans", "normal");
    doc.setFontSize(7);
    doc.setTextColor(textDark[0], textDark[1], textDark[2]);
    const paras = [
      "The portfolio returns set forth herein represent a series of differently weighted portfolios comprised of historical index returns; any such portfolio returns should be considered hypothetical and are for illustrative purposes. You are cautioned that hypothetical performance results have many inherent limitations, some of which are described herein.",
      "Indexes are unmanaged and you cannot invest in an index. No representation is being made that any account will or is likely to achieve profits similar to those shown or will not be able to avoid substantial losses.",
      "The hypothetical portfolio in this presentation assumes full investment, whereas an actual investor's portfolio would most likely have a positive cash position. Had the hypothetical portfolio included a cash position, the information would have been different and generally may have been lower.",
      "An additional limitation of hypothetical performance results is that they are generally prepared with the benefit of hindsight.",
      "Furthermore, the construction of a hypothetical portfolio of investments does not involve financial risk, and no hypothetical portfolio of investments can completely account for the impact of financial risk in actual trading. There are numerous other factors related to the markets in general or the implementation of a portfolio of investments which cannot be fully accounted for in the preparation of hypothetical performance results, all of which can adversely affect actual trading results.",
    ];
    for (const para of paras) {{
      const lines = doc.splitTextToSize(para, contentW);
      doc.text(lines, ml, y);
      y += lines.length * 3 + 2;
    }}
    return y;
  }},

  // ── Methodology block ──
  _pdfRenderMethodology(doc, portfolioIdx, startY) {{
    const p = state.portfolios[portfolioIdx];
    const {{ ml, contentW, navy, textDark }} = this._pdfC();
    let y = this._pdfSectionHeading(doc, "Methodology & Disclosures", startY);
    y += 2;
    doc.setFont("DMSans", "normal");
    doc.setFontSize(7);
    doc.setTextColor(textDark[0], textDark[1], textDark[2]);
    const methTexts = [
      "The Core portfolio allocates among selected asset classes according to user-specified weights. The portfolio is rebalanced monthly: each month's return is computed as the weighted average of the individual asset returns, and the portfolio value is compounded forward.",
      "The Stacked portfolio begins with the same Core base and layers on additional alternative exposure. The stacked exposure is financed by selling an equivalent notional amount of T-Bills short. Each alternative asset's contribution is reduced by a Fee and a Financing Cost (spread above T-Bills).",
      "All portfolios assume monthly rebalancing back to target weights with no transaction costs.",
    ];
    for (const para of methTexts) {{
      const lines = doc.splitTextToSize(para, contentW);
      doc.text(lines, ml, y);
      y += lines.length * 3 + 2;
    }}
    y += 2;
    const srcText = this._pdfBuildSourceText(portfolioIdx);
    const srcLines = doc.splitTextToSize(srcText, contentW);
    doc.text(srcLines, ml, y);
    y += srcLines.length * 3 + 4;
    return y;
  }},

  // ── Full Disclosures (general + filtered index definitions, multi-page) ──
  // usedAssets: Set of asset shortNames used in the portfolio(s). Only definitions
  // for used assets are included. PivotalPath section only appears if a PivotalPath
  // index is used. Statistics Definitions always appear (stats are always shown).
  _pdfRenderFullDisclosures(doc, portfolioName, usedAssets) {{
    const {{ pw, ph, ml, contentW, contentTop, contentBottom, textDark, navy, teal }} = this._pdfC();
    const lineH = 2.8;
    const fontSize = 6.5;
    let y = contentTop;

    const needPage = (needed) => {{
      if (y + needed > contentBottom) {{
        doc.addPage();
        this._pdfHeader(doc, portfolioName);
        y = contentTop;
      }}
    }};

    const renderPara = (text) => {{
      const clean = text.replace(/\\n/g, " ").trim();
      if (!clean) return;
      const lines = doc.splitTextToSize(clean, contentW);
      needPage(lines.length * lineH + 3);
      doc.setFont("DMSans", "normal");
      doc.setFontSize(fontSize);
      doc.setTextColor(textDark[0], textDark[1], textDark[2]);
      doc.text(lines, ml, y);
      y += lines.length * lineH + 3;
    }};

    const renderDef = (text) => {{
      const clean = text.replace(/\\n/g, " ").trim();
      if (!clean) return;
      const lines = doc.splitTextToSize(clean, contentW);
      needPage(lines.length * lineH + 2);
      doc.setFont("DMSans", "normal");
      doc.setFontSize(fontSize);
      doc.setTextColor(textDark[0], textDark[1], textDark[2]);
      doc.text(lines, ml, y);
      y += lines.length * lineH + 2;
    }};

    // Returns true if this definition matches any asset in usedAssets.
    // Definitions begin with "Asset Name (Source). description".
    const isUsedDef = (defn) => {{
      if (!usedAssets || usedAssets.size === 0) return true;
      const s = defn.trim();
      for (const name of usedAssets) {{
        if (s.startsWith(name + ' (') || s.startsWith(name + '.')) return true;
      }}
      return false;
    }};

    // ── Important Disclosures ──
    y = this._pdfSectionHeading(doc, "Important Disclosures", y);
    y += 2;
    for (const para of PDF_DISCLOSURES.general) {{
      const subParas = para.split("\\n\\n");
      for (const sp of subParas) {{ renderPara(sp); }}
    }}

    // ── Partition indexDefinitions into buckets ──
    const indexDefs   = [];    // used non-PivotalPath index definitions
    const ppIndexDefs = [];    // used PivotalPath index definitions
    const statsDefs   = [];    // statistics definitions (always shown)
    let ppDisclaimer  = null;  // long PivotalPath disclaimer block
    let inStats = false;

    for (const defn of PDF_DISCLOSURES.indexDefinitions) {{
      const s = defn.trim();
      if (!s) continue;
      if (s.startsWith("The PivotalPath index/indices")) {{ ppDisclaimer = s; continue; }}
      if (s === "Statistics Definitions") {{ inStats = true; continue; }}
      if (inStats) {{ statsDefs.push(s); continue; }}
      if (s.includes("PivotalPath")) {{
        if (isUsedDef(s)) ppIndexDefs.push(s);
        continue;
      }}
      if (isUsedDef(s)) indexDefs.push(s);
    }}

    // ── Index Definitions ──
    if (indexDefs.length > 0 || ppIndexDefs.length > 0) {{
      y += 4; needPage(12);
      y = this._pdfSectionHeading(doc, "Index Definitions", y);
      y += 2;
      for (const d of indexDefs) {{ renderDef(d); }}
      for (const d of ppIndexDefs) {{ renderDef(d); }}
    }}

    // ── PivotalPath Index Disclosures (only if a PivotalPath index is used) ──
    if (ppIndexDefs.length > 0 && ppDisclaimer) {{
      y += 4; needPage(12);
      y = this._pdfSectionHeading(doc, "PivotalPath Index Disclosures", y);
      y += 2;
      for (const pp of ppDisclaimer.split("\\n\\n")) {{ renderPara(pp); }}
    }}

    // ── Statistics Definitions ──
    if (statsDefs.length > 0) {{
      y += 4; needPage(12);
      y = this._pdfSectionHeading(doc, "Statistics Definitions", y);
      y += 2;
      for (const d of statsDefs) {{ renderDef(d); }}
    }}

    // Copyright
    y += 4; needPage(6);
    doc.setFont("DMSans", "normal");
    doc.setFontSize(fontSize);
    doc.setTextColor(textDark[0], textDark[1], textDark[2]);
    doc.text("© Return Stacked® Portfolio Solutions, " + new Date().getFullYear() + ". All rights reserved.", ml, y);
  }},

  // ── PDF stat-line helpers (drawdown + calendar outperformance) ──
  // Longest contiguous run of negative drawdown values; returns months + start/end date labels.
  _longestDDRange(ddArr, dates) {{
    let maxLen = 0, curLen = 0, curStart = 0, bestStart = 0, bestEnd = 0;
    for (let i = 0; i < ddArr.length; i++) {{
      if (ddArr[i] < 0) {{
        if (curLen === 0) curStart = i;
        curLen++;
        if (curLen > maxLen) {{ maxLen = curLen; bestStart = curStart; bestEnd = i; }}
      }} else {{ curLen = 0; }}
    }}
    return {{ months: maxLen, start: dates[bestStart] || "", end: dates[bestEnd] || "" }};
  }},

  // Calendar-year compounded returns for core and stacked streams of a result.
  _calendarYearReturns(r) {{
    const years = [], coreYearReturns = [], stackYearReturns = [];
    let curYear = null, coreYTD = 1, stackYTD = 1;
    for (let i = 0; i < r.coreReturns.length; i++) {{
      const date = r.dates[i + 1];
      if (!date) continue;
      const year = parseInt(date.substring(0, 4));
      if (curYear !== null && year !== curYear) {{
        years.push(curYear);
        coreYearReturns.push((coreYTD - 1) * 100);
        stackYearReturns.push((stackYTD - 1) * 100);
        coreYTD = 1; stackYTD = 1;
      }}
      curYear = year;
      coreYTD *= (1 + r.coreReturns[i]);
      stackYTD *= (1 + r.stackedReturns[i]);
    }}
    if (curYear !== null) {{
      years.push(curYear);
      coreYearReturns.push((coreYTD - 1) * 100);
      stackYearReturns.push((stackYTD - 1) * 100);
    }}
    return {{ years, coreYearReturns, stackYearReturns }};
  }},

  // Outperformance count + longest over/under streaks (mirrors the in-widget calendar stats text).
  _calendarOutperformance(years, coreYearReturns, stackYearReturns) {{
    let outCount = 0;
    let overStreak = 0, maxOver = 0, overStart = 0, overRanges = [];
    let underStreak = 0, maxUnder = 0, underStart = 0, underRanges = [];
    for (let i = 0; i < years.length; i++) {{
      if (stackYearReturns[i] > coreYearReturns[i]) {{
        outCount++;
        if (overStreak === 0) overStart = i;
        overStreak++;
        if (overStreak > maxOver) {{ maxOver = overStreak; overRanges = [{{ s: years[overStart], e: years[i] }}]; }}
        else if (overStreak === maxOver && maxOver > 0) overRanges.push({{ s: years[overStart], e: years[i] }});
        underStreak = 0;
      }} else if (stackYearReturns[i] < coreYearReturns[i]) {{
        if (underStreak === 0) underStart = i;
        underStreak++;
        if (underStreak > maxUnder) {{ maxUnder = underStreak; underRanges = [{{ s: years[underStart], e: years[i] }}]; }}
        else if (underStreak === maxUnder && maxUnder > 0) underRanges.push({{ s: years[underStart], e: years[i] }});
        overStreak = 0;
      }} else {{ overStreak = 0; underStreak = 0; }}
    }}
    const fmtRanges = (ranges) => {{
      const parts = ranges.map(rg => rg.s === rg.e ? String(rg.s) : rg.s + "\\u2013" + rg.e);
      if (parts.length <= 2) return parts.join(" & ");
      return parts.slice(0, -1).join(", ") + " & " + parts[parts.length - 1];
    }};
    return {{ outCount, total: years.length, maxOver, maxUnder, overRanges, underRanges, fmtRanges }};
  }},

  // Draws stat lines below a chart in the PDF. Each line is a string, or {{prefix, color, text}}
  // where prefix is rendered bold in `color` and text follows in the default dark color.
  _pdfStatLines(doc, lines, y) {{
    const {{ ml, teal, textDark }} = this._pdfC();
    const lineH = 4.2;
    doc.setFontSize(7.5);
    for (const ln of lines) {{
      let x = ml + 5;
      if (typeof ln === "string") {{
        doc.setFont("DMSans", "normal");
        doc.setTextColor(textDark[0], textDark[1], textDark[2]);
        doc.text(ln, x, y);
      }} else {{
        if (ln.prefix) {{
          const col = ln.color || teal;
          doc.setFont("DMSans", "bold");
          doc.setTextColor(col[0], col[1], col[2]);
          doc.text(ln.prefix, x, y);
          x += doc.getTextWidth(ln.prefix);
        }}
        doc.setFont("DMSans", "normal");
        doc.setTextColor(textDark[0], textDark[1], textDark[2]);
        doc.text(ln.text, x, y);
      }}
      y += lineH;
    }}
    return y;
  }},

  // Drawdown stat lines for a single portfolio (full period).
  _pdfDrawdownStatLines(r, hasStack) {{
    const navy = [50, 58, 70], teal = [20, 207, 166];
    const computeDD = (g) => {{ const dd = []; let peak = g[0]; for (let i = 0; i < g.length; i++) {{ if (g[i] > peak) peak = g[i]; dd.push(((g[i] - peak) / peak) * 100); }} return dd; }};
    const hasCore = r.hasCore !== false;
    const lines = [];
    if (hasCore) {{
      const coreDD = computeDD(r.coreGrowth);
      const coreL = this._longestDDRange(coreDD, r.dates);
      lines.push({{ prefix: "Core Portfolio ", color: navy, text: "— Max drawdown: " + Math.min(...coreDD).toFixed(2) + "%   ·   Longest drawdown: " + coreL.months + " months (" + coreL.start + " – " + coreL.end + ")" }});
      if (hasStack) {{
        const stackDD = computeDD(r.stackedGrowth);
        const stackL = this._longestDDRange(stackDD, r.dates);
        lines.push({{ prefix: "Stacked Portfolio ", color: teal, text: "— Max drawdown: " + Math.min(...stackDD).toFixed(2) + "%   ·   Longest drawdown: " + stackL.months + " months (" + stackL.start + " – " + stackL.end + ")" }});
      }}
    }} else {{
      const exDD = computeDD(r.stackedGrowth);
      const exL = this._longestDDRange(exDD, r.dates);
      lines.push({{ prefix: "Excess Return ", color: teal, text: "— Max drawdown: " + Math.min(...exDD).toFixed(2) + "%   ·   Longest drawdown: " + exL.months + " months (" + exL.start + " – " + exL.end + ")" }});
    }}
    return lines;
  }},

  // Calendar-year outperformance stat lines for a single portfolio (core vs stacked).
  _pdfCalendarStatLines(r, hasStack) {{
    if (!hasStack || r.hasCore === false) return [];
    const {{ years, coreYearReturns, stackYearReturns }} = this._calendarYearReturns(r);
    if (!years.length) return [];
    const o = this._calendarOutperformance(years, coreYearReturns, stackYearReturns);
    const overYrs = o.maxOver === 1 ? "1 year" : o.maxOver + " years";
    const underYrs = o.maxUnder === 1 ? "1 year" : o.maxUnder + " years";
    return [
      "Stacked portfolio outperformed the Core portfolio in " + o.outCount + " of " + o.total + " calendar years",
      "Longest streak of annual outperformance: " + overYrs + (o.overRanges.length ? " (" + o.fmtRanges(o.overRanges) + ")" : ""),
      "Longest streak of annual underperformance: " + underYrs + (o.underRanges.length ? " (" + o.fmtRanges(o.underRanges) + ")" : ""),
    ];
  }},

  // Comparison: per-portfolio drawdown stat lines over the common period (rebased at commonStart).
  _pdfCompDrawdownStatLines(active, colors, commonStart, commonEnd) {{
    const lines = [];
    active.forEach((i, idx) => {{
      const p = state.portfolios[i], r = p.result;
      const s = r.dates.indexOf(commonStart), e = r.dates.indexOf(commonEnd);
      if (s < 0 || e < 0) return;
      const base = r.stackedGrowth[s];
      const dd = []; let peak = 1;
      for (let j = s; j <= e; j++) {{ const g = r.stackedGrowth[j] / base; if (g > peak) peak = g; dd.push(((g - peak) / peak) * 100); }}
      const datesSlice = r.dates.slice(s, e + 1);
      const longest = this._longestDDRange(dd, datesSlice);
      lines.push({{ prefix: p.name + " ", color: this._hexToRgbArr(colors[idx % colors.length]), text: "— Max DD: " + Math.min(...dd).toFixed(2) + "%   ·   Longest DD: " + longest.months + " months (" + longest.start + " – " + longest.end + ")" }});
    }});
    return lines;
  }},

  // Comparison: per-portfolio calendar outperformance lines over the common period (core vs stacked).
  _pdfCompCalendarStatLines(active, colors, commonStart, commonEnd) {{
    const lines = [];
    active.forEach((i, idx) => {{
      const p = state.portfolios[i], r = p.result;
      if (r.hasCore === false) return;
      const hasStack = p.stack.some(st => st.asset && st.weight > 0);
      if (!hasStack) return;
      const s = r.dates.indexOf(commonStart), e = r.dates.indexOf(commonEnd);
      if (s < 0 || e < 0) return;
      // Slice returns to the common range (returns[m] spans dates[m] -> dates[m+1]).
      const sub = {{ dates: r.dates.slice(s, e + 1), coreReturns: r.coreReturns.slice(s, e), stackedReturns: r.stackedReturns.slice(s, e), hasCore: true }};
      const {{ years, coreYearReturns, stackYearReturns }} = this._calendarYearReturns(sub);
      if (!years.length) return;
      const o = this._calendarOutperformance(years, coreYearReturns, stackYearReturns);
      lines.push({{ prefix: p.name + " ", color: this._hexToRgbArr(colors[idx % colors.length]), text: "— Stacked beat Core in " + o.outCount + " of " + o.total + " years · longest over: " + (o.maxOver === 1 ? "1 yr" : o.maxOver + " yrs") + " · longest under: " + (o.maxUnder === 1 ? "1 yr" : o.maxUnder + " yrs") }});
    }});
    return lines;
  }},

  _trackHubSpotBehavioralEvent(eventName, properties) {{
    try {{
      const _email = (window.RSV_CONFIG && RSV_CONFIG.userEmail) || storedEmail;
      if (!_email || typeof _hsq === 'undefined') return;
      _hsq.push(['identify', {{ email: _email }}]);
      _hsq.push(['trackCustomBehavioralEvent', {{ name: eventName, properties: properties || {{}} }}]);
    }} catch(_e) {{}}
  }},

  shareComparison(btn) {{
    const sharedBy = (window.RSV_CONFIG && RSV_CONFIG.userEmail) || storedEmail || '';
    const portfolios = state.portfolios.map(p => ({{
      enabled: p.enabled,
      name: p.name,
      fee: p.fee,
      core: p.core.filter(r => r.asset && r.weight > 0).map(r => ({{ asset: r.asset, weight: r.weight }})),
      stack: p.stack.filter(r => r.asset && r.weight > 0).map(r => ({{ asset: r.asset, weight: r.weight, feeBp: r.feeBp || 0, financingBp: r.financingBp || 0 }}))
    }}));
    const shareState = {{ portfolios, sharedBy }};
    const encoded = btoa(JSON.stringify(shareState));
    const url = window.location.origin + window.location.pathname + '?rs_c=' + encoded;
    navigator.clipboard.writeText(url).then(() => {{
      if (btn) {{ btn.textContent = 'Copied!'; setTimeout(() => {{ btn.innerHTML = '&#x2197; Share Comparison'; }}, 2000); }}
    }});
    this._trackHubSpotBehavioralEvent('pe46343589_created_shared_link_comparison___adv_visualizer', {{}});
  }},

  // ── Single Portfolio Share ──
  sharePortfolio(portfolioIdx, btn) {{
    const p = state.portfolios[portfolioIdx];
    if (!p) return;
    const shareState = {{
      name: p.name,
      fee: p.fee,
      core: p.core.filter(r => r.asset && r.weight > 0).map(r => ({{ asset: r.asset, weight: r.weight }})),
      stack: p.stack.filter(r => r.asset && r.weight > 0).map(r => ({{ asset: r.asset, weight: r.weight, feeBp: r.feeBp || 0, financingBp: r.financingBp || 0 }}))
    }};
    const encoded = btoa(JSON.stringify(shareState));
    const url = window.location.origin + window.location.pathname + '?rs_p=' + encoded;
    navigator.clipboard.writeText(url).then(() => {{
      btn.textContent = 'Copied!';
      setTimeout(() => {{ btn.innerHTML = '↗ Share'; }}, 2000);
    }});
    submitHubSpotForm(HS_SHARE_FORM_ID, [
      {{ name: 'email', value: storedEmail }},
      {{ name: 'portfolio_widget_output', value: _formatPortfolioForHS(shareState) }}
    ]);
  }},

  async exportPortfolioPDF(portfolioIdx) {{
    const p = state.portfolios[portfolioIdx];
    if (!p || !p.result) {{
      alert("Please analyze this portfolio first before exporting to PDF.");
      return;
    }}
    const btn = event && event.target;
    if (btn) {{ btn.disabled = true; btn.textContent = "Generating..."; }}

    submitHubSpotForm(HS_PDF_FORM_ID, [
      {{ name: 'email', value: storedEmail }},
      {{ name: 'portfolio_widget_output', value: _formatPortfolioForHS(p) }}
    ]);

    try {{
      const r = p.result;
      const isExcess = !r.hasCore;
      const portfolioName = p.name;
      const sourceText = this._pdfBuildSourceText(portfolioIdx);

      // Capture all chart images by cycling through tabs
      const savedChartType = this._activeChartType[portfolioIdx] || "growthDD";
      const chartImages = {{}};
      const tabOrder = ["returnRisk", "growthDD", "rollingReturns", "calendarYear", "scaledBlend"];
      for (const tabName of tabOrder) {{
        if (tabName === "scaledBlend" && isExcess) continue;
        this.drawChart(portfolioIdx, tabName);
        await new Promise(resolve => setTimeout(resolve, 300));
        chartImages[tabName + "_a"] = this._captureChart(`rsv-chart-${{portfolioIdx}}-a`);
        chartImages[tabName + "_b"] = this._captureChart(`rsv-chart-${{portfolioIdx}}-b`);
      }}
      this.drawChart(portfolioIdx, savedChartType);

      const {{ jsPDF }} = window.jspdf;
      const doc = new jsPDF({{ orientation: "portrait", unit: "mm", format: "letter" }});
      const {{ pw, ph, ml, mr, contentW, contentTop, contentBottom }} = this._pdfC();
      this._pdfSetupFonts(doc);

      // Chart image dimensions for 2-per-page layout
      const chartW = contentW;
      const chartH = 80; // height per chart
      const chartGap = 6;

      // Page 1: Cover
      this._pdfRenderCover(doc, portfolioName, this._pdfBuildConfigLabel(p), r.period);

      // Page 2: Portfolio Config + Stats + Portfolio Disclaimer
      doc.addPage();
      this._pdfHeader(doc, portfolioName);
      let y = this._pdfRenderPortfolioConfig(doc, portfolioIdx, contentTop);
      y += 4;
      y = this._pdfRenderStatsTable(doc, p, y);
      y += 4;
      y = this._pdfSourceNote(doc, sourceText, y);

      // Helper: render a two-chart page (stats1/stats2 are optional stat-line arrays drawn under each chart)
      const twoChartPage = (title1, sub1, img1, title2, sub2, img2, stats1, stats2) => {{
        doc.addPage();
        this._pdfHeader(doc, portfolioName);
        y = contentTop;
        y = this._pdfSectionHeading(doc, title1, y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(98, 92, 109);
        doc.text(sub1, ml + 5, y); y += 4;
        y = this._pdfDrawChart(doc, img1, ml, y, chartW, chartH);
        if (stats1 && stats1.length) y = this._pdfStatLines(doc, stats1, y + 4);
        y += chartGap;
        if (img2) {{
          y = this._pdfSectionHeading(doc, title2, y);
          doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(98, 92, 109);
          doc.text(sub2, ml + 5, y); y += 4;
          y = this._pdfDrawChart(doc, img2, ml, y, chartW, chartH);
          if (stats2 && stats2.length) y = this._pdfStatLines(doc, stats2, y + 4);
        }}
        y += 8;
        this._pdfSourceNote(doc, sourceText, y);
      }};

      const hasStackP = p.stack.some(s => s.asset && s.weight > 0);
      const drawdownStats = this._pdfDrawdownStatLines(r, hasStackP);
      const calendarStats = this._pdfCalendarStatLines(r, hasStackP);

      // Page 3: Growth of $100 + Drawdowns
      twoChartPage(
        "Growth of $100", "Cumulative growth of a hypothetical $100 investment, rebalanced monthly.", chartImages.growthDD_a,
        "Drawdowns", "Peak-to-trough declines from the highest portfolio value to date.", chartImages.growthDD_b,
        null, drawdownStats
      );

      // Page 4: Rolling Returns + Rolling Return Difference
      twoChartPage(
        "Rolling Returns", "Annualized returns over rolling windows.", chartImages.rollingReturns_a,
        "Rolling Return Difference", "Difference in annualized rolling returns: Stacked minus Core.", chartImages.rollingReturns_b
      );

      // Page 5: Calendar Year Returns + Intra-year Maximum Drawdown
      twoChartPage(
        "Calendar Year Returns", "Total return for each calendar year of the analysis period.", chartImages.calendarYear_a,
        "Intra-year Maximum Drawdown", "Largest peak-to-trough decline within each calendar year of the analysis period.", chartImages.calendarYear_b,
        calendarStats, null
      );

      // Page 6: Return vs Risk + Return vs Max Drawdown (both scatter plots)
      twoChartPage(
        "Return vs. Volatility", "Annualized return vs. annualized volatility with benchmark frontier.", chartImages.returnRisk_a,
        "Return vs. Max Drawdown", "Annualized return vs. maximum drawdown with benchmark frontier.", chartImages.returnRisk_b
      );

      // Page 7-8: Scaled Stack Blend + Rolling Correlation (if applicable)
      if (!isExcess && chartImages.scaledBlend_a) {{
        twoChartPage(
          "Scaled Stack Blend", "Growth of $100: Core vs. the alternative sleeve scaled by the stack size.", chartImages.scaledBlend_a,
          "Rolling Correlation", "Rolling correlation between Core and Scaled Stack Blend monthly returns.", chartImages.scaledBlend_b
        );
      }}

      // Disclosures pages (general + index definitions, multi-page)
      const _usedAssets = new Set();
      p.core.filter(r => r.asset).forEach(r => _usedAssets.add(r.asset));
      p.stack.filter(r => r.asset).forEach(r => _usedAssets.add(r.asset));
      doc.addPage();
      this._pdfHeader(doc, portfolioName);
      this._pdfRenderFullDisclosures(doc, portfolioName, _usedAssets);

      // Add footers + page numbers to all pages
      const totalPages = doc.getNumberOfPages();
      for (let i = 2; i <= totalPages; i++) {{ // skip cover
        doc.setPage(i);
        this._pdfFooter(doc, i, totalPages);
      }}

      const safeName = portfolioName.replace(/[^a-zA-Z0-9]/g, "_");
      doc.save("RS_Portfolio_Report_" + safeName + ".pdf");

    }} catch(e) {{
      console.error("PDF generation error:", e);
      alert("Error generating PDF: " + e.message);
    }} finally {{
      if (btn) {{ btn.disabled = false; btn.textContent = "\u2193 PDF"; }}
    }}
  }},

  // ── Comparison PDF: reusable table renderer ──
  _pdfCompTable(doc, title, y, active, metrics, getVal, fmt) {{
    const {{ ml, contentW, navy, teal, textDark, textSec }} = this._pdfC();
    const tableX = ml;
    const tableW = contentW;
    const metricColW = 42;
    const dataColW = (tableW - metricColW) / active.length;
    const rowH = 7;

    y = this._pdfSubheading(doc, title, y);
    y += 1;

    // Header
    doc.setFillColor(navy[0], navy[1], navy[2]);
    doc.rect(tableX, y, tableW, rowH, "F");
    doc.setFont("DMSans", "bold"); doc.setFontSize(6.5); doc.setTextColor(255, 255, 255);
    doc.text("Metric", tableX + 4, y + 5);
    active.forEach((pidx, ci) => {{
      doc.text(state.portfolios[pidx].name, tableX + metricColW + ci * dataColW + dataColW / 2, y + 5, {{ align: "center" }});
    }});
    y += rowH;

    // Rows
    metrics.forEach((row, ri) => {{
      if (ri % 2 === 0) {{ doc.setFillColor(240, 241, 241); doc.rect(tableX, y, tableW, rowH, "F"); }}
      doc.setFont("DMSans", "normal"); doc.setFontSize(6.5); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
      doc.text(row.label, tableX + 4, y + 5);
      active.forEach((pidx, ci) => {{
        const val = getVal(pidx, row.key);
        const text = fmt(val, row.pct);
        // Color-code difference table
        if (row.colorFn && val != null) {{
          const c = row.colorFn(val, row.key);
          if (c) doc.setTextColor(c[0], c[1], c[2]);
        }}
        doc.text(text, tableX + metricColW + ci * dataColW + dataColW / 2, y + 5, {{ align: "center" }});
        doc.setTextColor(textDark[0], textDark[1], textDark[2]); // reset
      }});
      doc.setDrawColor(191, 191, 191); doc.setLineWidth(0.1);
      doc.line(tableX, y + rowH, tableX + tableW, y + rowH);
      y += rowH;
    }});
    return y;
  }},

  // ── Comparison PDF Export ──
  async exportComparisonPDF() {{
    const active = [];
    for (let i = 0; i < NUM_PORTFOLIOS; i++) {{
      const p = state.portfolios[i];
      if (p.enabled && p.result) active.push(i);
    }}
    if (active.length < 2) {{
      alert("At least two analyzed portfolios are needed for comparison PDF.");
      return;
    }}
    const btn = event && event.target;
    if (btn) {{ btn.disabled = true; btn.textContent = "Generating..."; }}

    const _compSummary = active.map(i => _formatPortfolioForHS(state.portfolios[i]))
      .join('\\n\\n' + '─'.repeat(20) + '\\n\\n');
    submitHubSpotForm(HS_PDF_FORM_ID, [
      {{ name: 'email', value: storedEmail }},
      {{ name: 'portfolio_widget_output', value: _compSummary }}
    ]);

    try {{
      // Capture comparison charts by rendering the summary panel and cycling through chart tabs
      const savedTab = state.activeTab;
      const savedChartTab = this._activeComparisonChartTab || "growthDD";
      this.renderSummaryPanel();
      await new Promise(resolve => setTimeout(resolve, 300));
      const chartImages = {{}};
      const allChartTabs = ["returnRisk", "growthDD", "rollingReturns", "calendarYear"];
      for (const tabKey of allChartTabs) {{
        for (const k of allChartTabs) {{
          const el = document.getElementById("rsv-comp-chart-" + k);
          if (el) el.classList.toggle("rsv-comp-chart-active", k === tabKey);
        }}
        this._renderComparisonChartTab(tabKey);
        await new Promise(resolve => setTimeout(resolve, 300));
        if (tabKey === "returnRisk") {{
          chartImages.risk = this._captureChart("rsv-summary-risk");
          chartImages.dd = this._captureChart("rsv-summary-dd");
        }} else if (tabKey === "growthDD") {{
          chartImages.growth = this._captureChart("rsv-summary-growth");
          chartImages.drawdown = this._captureChart("rsv-summary-drawdown");
        }} else if (tabKey === "rollingReturns") {{
          chartImages.rolling = this._captureChart("rsv-summary-rolling");
        }} else if (tabKey === "calendarYear") {{
          chartImages.calendar = this._captureChart("rsv-summary-calendar");
          chartImages.calendarDD = this._captureChart("rsv-summary-calendar-dd");
        }}
      }}
      this._activeComparisonChartTab = savedChartTab;
      // Restore previous panel
      state.activeTab = savedTab;
      this.renderPanel(savedTab);

      const {{ jsPDF }} = window.jspdf;
      const doc = new jsPDF({{ orientation: "portrait", unit: "mm", format: "letter" }});
      const {{ pw, ph, ml, mr, contentW, contentTop, contentBottom, navy, teal, textDark, textSec }} = this._pdfC();
      this._pdfSetupFonts(doc);

      // Chart layout constants
      const chartW = contentW;
      const chartH = 80;
      const chartGap = 6;
      // Portfolio colors (must match renderSummaryPanel ordering so stat-line prefixes match chart colors)
      const compColors = ["#14CFA6", "#323A46", "#3A6A9C", "#0C7C64", "#7DA5CE", "#3BB823"];

      // Common date range
      let commonStart = null, commonEnd = null;
      for (const i of active) {{
        const r = state.portfolios[i].result;
        if (!commonStart || r.period.start > commonStart) commonStart = r.period.start;
        if (!commonEnd || r.period.end < commonEnd) commonEnd = r.period.end;
      }}

      // Recompute stats for common range (core and stacked separately)
      const commonCoreStats = {{}}, commonStackedStats = {{}}, commonTE = {{}};
      for (const i of active) {{
        const r = state.portfolios[i].result;
        const coreAligned = [], stackAligned = [];
        for (let m = 0; m < r.coreReturns.length; m++) {{
          const date = r.dates[m + 1];
          if (date > commonStart && date <= commonEnd) {{
            coreAligned.push(r.coreReturns[m]);
            stackAligned.push(r.stackedReturns[m]);
          }}
        }}
        // Build dates array for the common range
        const commonDates = r.dates.filter(d => d >= commonStart && d <= commonEnd);
        const monthlyFee = (state.portfolios[i].fee || 0) / 10000 / 12;
        commonCoreStats[i] = computeStats(coreAligned.map(r => r - monthlyFee), commonDates);
        commonStackedStats[i] = computeStats(stackAligned.map(r => r - monthlyFee), commonDates, undefined, undefined, !r.hasCore);
        // Tracking error
        const diffs = [];
        for (let k = 0; k < Math.min(coreAligned.length, stackAligned.length); k++) diffs.push(stackAligned[k] - coreAligned[k]);
        const dm = diffs.length ? diffs.reduce((s, v) => s + v, 0) / diffs.length : 0;
        const dv = diffs.length > 1 ? diffs.reduce((s, v) => s + Math.pow(v - dm, 2), 0) / (diffs.length - 1) : 0;
        commonTE[i] = Math.sqrt(dv) * Math.sqrt(12);
      }}

      const fmt = (v, pct) => v == null ? "\u2014" : (pct ? (v * 100).toFixed(2) + "%" : v.toFixed(2));

      // Metrics for the Risk & Return tables
      const riskMetrics = [
        {{ label: "Cumulative Return", key: "cumulativeReturn", pct: true }},
        {{ label: "Annualized Return", key: "annualizedReturn", pct: true }},
        {{ label: "Annualized Volatility", key: "volatility", pct: true }},
        {{ label: "Maximum Drawdown", key: "maxDrawdown", pct: true }},
        {{ label: "Sharpe Ratio", key: "sharpe", pct: false }},
        {{ label: "Sortino Ratio", key: "sortino", pct: false }},
        {{ label: "Tracking Error", key: "trackingError", pct: true }},
      ];

      // Color function for difference table
      const lowerBetter = ["volatility", "maxDrawdown"];
      const diffColor = (val, key) => {{
        if (val === 0 || val == null) return null;
        const good = lowerBetter.includes(key) ? val < 0 : val > 0;
        return good ? [20, 160, 100] : [200, 60, 60];
      }};

      // Build merged disclaimer text
      const mergedDisclaimer = this.generateMergedDisclaimer(active, commonStart, commonEnd);

      // Cover
      this._pdfRenderCover(doc, "Portfolio Comparison", active.map(i => state.portfolios[i].name).join(" vs "), {{ start: commonStart, end: commonEnd }});

      // ── Page 2: Risk & Return -- Core table + Stacked table ──
      doc.addPage();
      this._pdfHeader(doc, "Portfolio Comparison");
      let y = contentTop;
      y = this._pdfSectionHeading(doc, "Risk & Return", y);
      doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
      doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 5;

      // Core Portfolio table
      y = this._pdfCompTable(doc, "Core Portfolio", y, active, riskMetrics, (pidx, key) => {{
        if (key === "trackingError") return 0;
        return commonCoreStats[pidx] ? commonCoreStats[pidx][key] : null;
      }}, fmt);
      y += 6;

      // Stacked Portfolio table
      y = this._pdfCompTable(doc, "Stacked Portfolio", y, active, riskMetrics, (pidx, key) => {{
        if (key === "trackingError") return commonTE[pidx] || 0;
        return commonStackedStats[pidx] ? commonStackedStats[pidx][key] : null;
      }}, fmt);
      y += 6;

      // Difference table (with color coding)
      const diffMetrics = riskMetrics.map(r => ({{ ...r, colorFn: diffColor }}));
      y = this._pdfCompTable(doc, "Difference (Stacked - Core)", y, active, diffMetrics, (pidx, key) => {{
        if (key === "trackingError") return commonTE[pidx] || 0;
        const cs = commonCoreStats[pidx], ss = commonStackedStats[pidx];
        if (!cs || !ss || cs[key] == null || ss[key] == null) return null;
        return ss[key] - cs[key];
      }}, fmt);
      y += 8;
      this._pdfSourceNote(doc, mergedDisclaimer, y);

      // ── Page 3: Advanced Statistics ──
      doc.addPage();
      this._pdfHeader(doc, "Portfolio Comparison");
      y = contentTop;
      y = this._pdfSectionHeading(doc, "Advanced Statistics", y);
      doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
      doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 5;

      const advRows = [
        {{ label: "Annualized Return", key: "annualizedReturn", pct: true }},
        {{ label: "Annualized Volatility", key: "volatility", pct: true }},
        {{ label: "Cumulative Return", key: "cumulativeReturn", pct: true }},
        {{ label: "Maximum Drawdown", key: "maxDrawdown", pct: true }},
        {{ label: "Sharpe Ratio", key: "sharpe", pct: false }},
        {{ label: "Sortino Ratio", key: "sortino", pct: false }},
        {{ label: "Calmar Ratio", key: "calmar", pct: false }},
        {{ label: "Skewness", key: "skewness", pct: false }},
        {{ label: "Kurtosis", key: "kurtosis", pct: false }},
        {{ label: "VaR (95%)", key: "var95", pct: true }},
        {{ label: "CVaR (95%)", key: "cvar95", pct: true }},
        {{ label: "Best Month", key: "bestMonth", pct: true }},
        {{ label: "Worst Month", key: "worstMonth", pct: true }},
      ];

      y = this._pdfCompTable(doc, "Stacked Portfolios", y, active, advRows, (pidx, key) => {{
        return commonStackedStats[pidx] ? commonStackedStats[pidx][key] : null;
      }}, fmt);
      y += 8;
      this._pdfSourceNote(doc, mergedDisclaimer, y);

      // ── Page 4: Tracking Error Matrix ──
      doc.addPage();
      this._pdfHeader(doc, "Portfolio Comparison");
      y = contentTop;
      y = this._pdfSectionHeading(doc, "Tracking Error Matrix", y);
      doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
      doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 5;

      const n = active.length;
      const tableX = ml;
      const tableW = contentW;
      const metricColW = 42;
      const matColW = Math.min(30, (tableW - metricColW) / n);
      const rowH = 7;

      // Header
      doc.setFillColor(navy[0], navy[1], navy[2]);
      doc.rect(tableX, y, metricColW + n * matColW, rowH, "F");
      doc.setFont("DMSans", "bold"); doc.setFontSize(6); doc.setTextColor(255, 255, 255);
      active.forEach((pidx, ci) => {{
        doc.text(state.portfolios[pidx].name, tableX + metricColW + ci * matColW + matColW / 2, y + 5, {{ align: "center" }});
      }});
      y += rowH;

      // Matrix rows
      active.forEach((pidxRow, ri) => {{
        if (ri % 2 === 0) {{ doc.setFillColor(240, 241, 241); doc.rect(tableX, y, metricColW + n * matColW, rowH, "F"); }}
        doc.setFont("DMSans", "bold"); doc.setFontSize(6); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
        doc.text(state.portfolios[pidxRow].name, tableX + 4, y + 5);
        const rRow = state.portfolios[pidxRow].result;
        active.forEach((pidxCol, ci) => {{
          const cx = tableX + metricColW + ci * matColW + matColW / 2;
          if (pidxRow === pidxCol) {{
            doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
            doc.text("\u2014", cx, y + 5, {{ align: "center" }});
          }} else {{
            const rCol = state.portfolios[pidxCol].result;
            const s1 = rRow.dates.indexOf(commonStart), e1 = rRow.dates.indexOf(commonEnd);
            const s2 = rCol.dates.indexOf(commonStart), e2 = rCol.dates.indexOf(commonEnd);
            if (s1 >= 0 && e1 > s1 && s2 >= 0 && e2 > s2) {{
              const r1 = rRow.stackedReturns.slice(s1, e1), r2 = rCol.stackedReturns.slice(s2, e2);
              const len = Math.min(r1.length, r2.length);
              const diffs = []; for (let k = 0; k < len; k++) diffs.push(r1[k] - r2[k]);
              const dm = diffs.reduce((s, v) => s + v, 0) / diffs.length;
              const dv = diffs.reduce((s, v) => s + Math.pow(v - dm, 2), 0) / (diffs.length - 1);
              doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textDark[0], textDark[1], textDark[2]);
              doc.text((Math.sqrt(dv) * Math.sqrt(12) * 100).toFixed(2) + "%", cx, y + 5, {{ align: "center" }});
            }}
          }}
        }});
        doc.setDrawColor(191, 191, 191); doc.setLineWidth(0.1);
        doc.line(tableX, y + rowH, tableX + metricColW + n * matColW, y + rowH);
        y += rowH;
      }});
      y += 8;
      this._pdfSourceNote(doc, mergedDisclaimer, y);

      // ── Chart Pages: Return vs Volatility + Return vs Max Drawdown ──
      if (chartImages.risk || chartImages.dd) {{
        doc.addPage();
        this._pdfHeader(doc, "Portfolio Comparison");
        y = contentTop;
        y = this._pdfSectionHeading(doc, "Return vs. Volatility", y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 4;
        if (chartImages.risk) {{
          y = this._pdfDrawChart(doc, chartImages.risk, ml, y, chartW, chartH);
        }}
        y += chartGap;
        y = this._pdfSectionHeading(doc, "Return vs. Max Drawdown", y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 4;
        if (chartImages.dd) {{
          y = this._pdfDrawChart(doc, chartImages.dd, ml, y, chartW, chartH);
        }}
        y += 8;
        this._pdfSourceNote(doc, mergedDisclaimer, y);
      }}

      // ── Chart Pages: Growth of $1 + Drawdown ──
      if (chartImages.growth || chartImages.drawdown) {{
        doc.addPage();
        this._pdfHeader(doc, "Portfolio Comparison");
        y = contentTop;
        y = this._pdfSectionHeading(doc, "Growth of $1 (Stacked Portfolios)", y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 4;
        if (chartImages.growth) {{
          y = this._pdfDrawChart(doc, chartImages.growth, ml, y, chartW, chartH);
        }}
        y += chartGap;
        y = this._pdfSectionHeading(doc, "Maximum Drawdown and Recovery (Stacked Portfolios)", y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 4;
        if (chartImages.drawdown) {{
          y = this._pdfDrawChart(doc, chartImages.drawdown, ml, y, chartW, chartH);
          const ddLines = this._pdfCompDrawdownStatLines(active, compColors, commonStart, commonEnd);
          if (ddLines.length) y = this._pdfStatLines(doc, ddLines, y + 4);
        }}
        y += 8;
        this._pdfSourceNote(doc, mergedDisclaimer, y);
      }}

      // ── Chart Page: Rolling Returns ──
      if (chartImages.rolling) {{
        doc.addPage();
        this._pdfHeader(doc, "Portfolio Comparison");
        y = contentTop;
        const rollMonths = this._comparisonRollingMonths || 36;
        y = this._pdfSectionHeading(doc, rollMonths + "-Month Rolling Annualized Returns (Stacked Portfolios)", y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 4;
        y = this._pdfDrawChart(doc, chartImages.rolling, ml, y, chartW, chartH);
        y += 8;
        this._pdfSourceNote(doc, mergedDisclaimer, y);
      }}

      // ── Chart Pages: Calendar Year Returns + Intra-year DD ──
      if (chartImages.calendar || chartImages.calendarDD) {{
        doc.addPage();
        this._pdfHeader(doc, "Portfolio Comparison");
        y = contentTop;
        y = this._pdfSectionHeading(doc, "Calendar Year Returns (Stacked Portfolios)", y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 4;
        if (chartImages.calendar) {{
          y = this._pdfDrawChart(doc, chartImages.calendar, ml, y, chartW, chartH);
          const calLines = this._pdfCompCalendarStatLines(active, compColors, commonStart, commonEnd);
          if (calLines.length) y = this._pdfStatLines(doc, calLines, y + 4);
        }}
        y += chartGap;
        y = this._pdfSectionHeading(doc, "Intra-year Maximum Drawdown (Stacked Portfolios)", y);
        doc.setFont("DMSans", "normal"); doc.setFontSize(7); doc.setTextColor(textSec[0], textSec[1], textSec[2]);
        doc.text("Common Period: " + commonStart + " to " + commonEnd, ml + 5, y); y += 4;
        if (chartImages.calendarDD) {{
          y = this._pdfDrawChart(doc, chartImages.calendarDD, ml, y, chartW, chartH);
        }}
        y += 8;
        this._pdfSourceNote(doc, mergedDisclaimer, y);
      }}

      // ── Disclosures pages ──
      const _compUsedAssets = new Set();
      active.forEach(i => {{
        const _ap = state.portfolios[i];
        _ap.core.filter(r => r.asset).forEach(r => _compUsedAssets.add(r.asset));
        _ap.stack.filter(r => r.asset).forEach(r => _compUsedAssets.add(r.asset));
      }});
      doc.addPage();
      this._pdfHeader(doc, "Portfolio Comparison");
      this._pdfRenderFullDisclosures(doc, "Portfolio Comparison", _compUsedAssets);

      // Footers on all pages
      const totalPages = doc.getNumberOfPages();
      for (let i = 2; i <= totalPages; i++) {{
        doc.setPage(i);
        this._pdfFooter(doc, i, totalPages);
      }}

      doc.save("RS_Portfolio_Comparison.pdf");
    }} catch(e) {{
      console.error("Comparison PDF error:", e);
      alert("Error generating comparison PDF: " + e.message);
    }} finally {{
      if (btn) {{ btn.disabled = false; btn.textContent = "\u2193 Comparison PDF"; }}
    }}
  }},

  renderConsultantCTA() {{
    return `<div class="rsv-cta-strip">
      <div class="rsv-cta-strip-text">
        <strong>Discuss your stack with a consultant</strong>
        <span>Get matched with a Return Stacked&reg; specialist in your region</span>
      </div>
      <button class="rsv-cta-strip-btn" onclick="RSV._openConsultantModal()">Talk to a Consultant</button>
    </div>`;
  }},

  _openConsultantModal() {{
    const modal = document.getElementById('rsv-consultant-modal');
    const step1 = document.getElementById('rsv-consultant-step1');
    const step2 = document.getElementById('rsv-consultant-step2');
    try {{
      const saved = JSON.parse(localStorage.getItem(INTAKE_STORAGE_KEY)) || {{}};
      if (saved.aum && saved.state) {{
        step1.classList.remove('active');
        step2.classList.add('active');
        this._showConsultantResult(saved.aum, saved.state);
      }} else {{
        step1.classList.add('active');
        step2.classList.remove('active');
      }}
    }} catch(e) {{
      step1.classList.add('active');
      step2.classList.remove('active');
    }}
    modal.classList.add('active');
  }},

  _showConsultantResult(selectedAum, selectedState) {{
    const resolved = resolveConsultant(selectedAum, selectedState);
    const consultant = resolved.name;
    const details = resolved.details;
    const firstName = consultant.split(' ')[0];
    document.getElementById('rsv-consultant-name').textContent = consultant;
    const photo = document.getElementById('rsv-consultant-photo');
    photo.src = details.photo;
    photo.alt = consultant;
    const emailEl = document.getElementById('rsv-consultant-email');
    emailEl.textContent = details.email;
    emailEl.href = 'mailto:' + details.email;
    const p = state.portfolios[typeof state.activeTab === 'number' ? state.activeTab : 0];
    const coreTotal = p ? p.core.reduce((s, r) => s + (r.weight || 0), 0) : 0;
    const stackTotal = p ? p.stack.reduce((s, r) => s + (r.weight || 0), 0) : 0;
    const stackAssets = p ? p.stack.filter(r => r.asset && r.weight > 0)
      .map(r => r.weight + '% ' + r.asset).join(' / ') : '';
    document.getElementById('rsv-portfolio-summary').innerHTML =
      '<div class="portfolio-label">Proposed Portfolio</div>' +
      '<div><strong>Core Allocation:</strong> ' + coreTotal.toFixed(1) + '%</div>' +
      '<div><strong>Stack Overlay:</strong> ' + stackTotal.toFixed(1) + '%</div>' +
      (stackAssets ? '<div><strong>Stack Blend:</strong> ' + stackAssets + '</div>' : '');
    document.getElementById('rsv-consultant-book').textContent = 'Schedule with ' + firstName;
    this._selectedConsultantUrl = details.url;
    document.getElementById('rsv-consultant-step1').classList.remove('active');
    document.getElementById('rsv-consultant-step2').classList.add('active');
  }},

  _initHubSpot() {{
    const intakeOverlay = document.getElementById('rsv-intake-overlay');
    const userInfoEl = document.getElementById('rsv-user-info');
    const userInfoTextEl = document.getElementById('rsv-user-info-text');

    const showUserInfo = () => {{
      userInfoTextEl.textContent = storedFirstName + ' ' + storedLastName + ' · ' + storedEmail;
      userInfoEl.style.display = 'flex';
    }};

    const activateWidget = () => {{
      intakeOverlay.classList.add('hidden');
      if (storedEmail) showUserInfo();
      this.renderPanel(state.activeTab);
    }};

    activateWidget();

    document.getElementById('rsv-intake-submit').addEventListener('click', () => {{
      const first = document.getElementById('rsv-intake-first').value.trim();
      const last = document.getElementById('rsv-intake-last').value.trim();
      const email = document.getElementById('rsv-intake-email').value.trim();
      const type = document.getElementById('rsv-intake-type').value;
      if (!first || !last || !email || !type) {{
        alert('Please fill in all fields.');
        return;
      }}
      storedFirstName = first;
      storedLastName = last;
      storedEmail = email;
      storedInvestorType = type;
      try {{
        localStorage.setItem(INTAKE_STORAGE_KEY, JSON.stringify({{
          firstName: first, lastName: last, email: email, investorType: type
        }}));
      }} catch(e) {{}}
      submitHubSpotForm(HS_INTAKE_FORM_ID, [
        {{ objectTypeId: '0-1', name: 'email', value: email }},
        {{ objectTypeId: '0-1', name: 'firstname', value: first }},
        {{ objectTypeId: '0-1', name: 'lastname', value: last }},
        {{ objectTypeId: '0-1', name: 'contact_type', value: type }}
      ]);
      activateWidget();
    }});

    document.getElementById('rsv-not-you').addEventListener('click', () => {{
      storedFirstName = ''; storedLastName = ''; storedEmail = ''; storedInvestorType = '';
      try {{ localStorage.removeItem(INTAKE_STORAGE_KEY); }} catch(e) {{}}
      userInfoEl.style.display = 'none';
      ['rsv-intake-first','rsv-intake-last','rsv-intake-email','rsv-intake-type']
        .forEach(id => {{ document.getElementById(id).value = ''; }});
      intakeOverlay.classList.remove('hidden');
      this.renderPanel(state.activeTab);
    }});

    const modalOverlay = document.getElementById('rsv-consultant-modal');
    const closeModal = () => modalOverlay.classList.remove('active');
    document.getElementById('rsv-consultant-close').addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', e => {{ if (e.target === modalOverlay) closeModal(); }});
    document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

    const aumToHubSpotValue = {{
      'Under $5M': 'Under $25M',
      '$5M – $25M': '$5M - $25M',
      '$25M – $50M': '$25M - $50M',
      '$50M – $100M': '$25M - $100M',
      '$100M – $500M': '$250M - $500M',
      '$500M – $1B': '$500M - $1B',
      '$1B – $3B': '$1B - $2.5B',
      '$3B – $5B': '$2.5B -$5B',
      '$5B+': '$5B+'
    }};

    document.getElementById('rsv-consultant-find').addEventListener('click', () => {{
      const selectedAum = document.getElementById('rsv-aum-select').value;
      const selectedState = document.getElementById('rsv-state-select').value;
      if (!selectedAum || !selectedState) return;
      submitHubSpotForm(HS_CONSULTANT_FORM_ID, [
        {{ objectTypeId: '0-1', name: 'email', value: storedEmail }},
        {{ objectTypeId: '0-1', name: 'investable_assets', value: aumToHubSpotValue[selectedAum] || selectedAum }},
        {{ objectTypeId: '0-1', name: 'state_province_dropdown', value: selectedState }}
      ]);
      try {{
        const saved = JSON.parse(localStorage.getItem(INTAKE_STORAGE_KEY)) || {{}};
        saved.aum = selectedAum;
        saved.state = selectedState;
        localStorage.setItem(INTAKE_STORAGE_KEY, JSON.stringify(saved));
      }} catch(e) {{}}
      this._showConsultantResult(selectedAum, selectedState);
    }});

    document.getElementById('rsv-consultant-book').addEventListener('click', () => {{
      const p = state.portfolios[typeof state.activeTab === 'number' ? state.activeTab : 0];
      const coreAssets = p ? p.core.filter(r => r.asset && r.weight > 0)
        .map(r => r.weight + '% ' + r.asset).join(' / ') : '';
      const stackAssets = p ? p.stack.filter(r => r.asset && r.weight > 0)
        .map(r => r.weight + '% ' + r.asset).join(' / ') : '';
      const summary = 'Core: ' + (coreAssets || 'None') + '\\nStack: ' + (stackAssets || 'None');
      const params = new URLSearchParams({{
        firstName: storedFirstName,
        lastName: storedLastName,
        email: storedEmail,
        investor_type: storedInvestorType,
        portfolio_widget_output: summary
      }});
      window.open(this._selectedConsultantUrl + '?' + params.toString(), '_blank');
    }});
  }},

  toggleDisclosures(btn) {{
    btn.classList.toggle("open");
    const parent = btn.closest(".rsv-disclosures");
    const content = parent && parent.querySelector(".rsv-disclosures-content");
    if (content) content.classList.toggle("open");
  }},
}};

// ── HubSpot Integration ──
var HS_PORTAL_ID = '46343589';
var HS_INTAKE_FORM_ID = '6b9c8e0b-cb6b-4825-a746-c71582a2a399';
var HS_CONSULTANT_FORM_ID = 'bcf7ac41-efe8-4232-bfc7-4f83d7a9df87';
var HS_SHARE_FORM_ID = '2da1dbd2-93c6-4b6e-a7df-dcbb1929f346';
var HS_PDF_FORM_ID = 'b90d1e6b-0dd3-474b-aa5c-414a66849e1c';
var HS_SAVE_PORTFOLIO_FORM_ID = '4f3dcb5a-53f7-4ea6-a48e-fca42e32e89c';
var HS_SAVE_COMPARISON_FORM_ID = 'd6bc3ec3-21f7-489c-b295-eaf834cc6835';
var INTAKE_STORAGE_KEY = 'rsWidgetIntake';
var financialProTypes = ['Financial Advisor', 'Single Family Office', 'Institution', 'OCIO', 'Consultant', 'Asset Manager'];

var storedFirstName = '';
var storedLastName = '';
var storedEmail = '';
var storedInvestorType = '';

// Pre-hydrate from localStorage so renderPanel() has storedInvestorType before init renders
(function() {{
  if (window.RSV_CONFIG && RSV_CONFIG.userEmail) {{
    storedEmail     = RSV_CONFIG.userEmail;
    storedFirstName = RSV_CONFIG.firstName || '';
    storedLastName  = RSV_CONFIG.lastName  || '';
    return;
  }}
  try {{
    const saved = JSON.parse(localStorage.getItem('rsWidgetIntake'));
    if (saved && saved.email) {{
      storedFirstName = saved.firstName || '';
      storedLastName  = saved.lastName  || '';
      storedEmail     = saved.email     || '';
      storedInvestorType = saved.investorType || '';
    }}
  }} catch(e) {{}}
}})();

function submitHubSpotForm(formId, fields) {{
  fetch('https://api.hsforms.com/submissions/v3/integration/submit/' + HS_PORTAL_ID + '/' + formId, {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ fields: fields }})
  }}).catch(function() {{}});
}}

function _formatPortfolioForHS(p) {{
  const feeStr = p.fee > 0 ? ' (Fee: ' + (p.fee / 100).toFixed(2) + '%)' : '';
  const coreAssets = (p.core || []).filter(r => r.asset && r.weight > 0);
  const stackAssets = (p.stack || []).filter(r => r.asset && r.weight > 0);
  const lines = ['Name:  ' + (p.name || 'Unnamed') + feeStr];
  lines.push('Core:  ' + (coreAssets.map(r => r.weight + '% ' + r.asset).join(' · ') || 'None'));
  if (stackAssets.length > 0) {{
    lines.push('Stack: ' + stackAssets.map(r => r.weight + '% ' + r.asset).join(' · '));
  }}
  if (p.savedAt) lines.push('Saved: ' + p.savedAt);
  return lines.join('\\n');
}}

function _submitAllPortfoliosToHS() {{
  const saved = getSavedPortfolios();
  const email = (window.RSV_CONFIG && RSV_CONFIG.userEmail) || storedEmail;
  if (!email || !saved.length) return;
  const sep = '\\n\\n' + '─'.repeat(20) + '\\n\\n';
  const text = [...saved].reverse().map(_formatPortfolioForHS).join(sep);
  submitHubSpotForm(HS_SAVE_PORTFOLIO_FORM_ID, [
    {{ name: 'email', value: email }},
    {{ name: 'saved_portfolio_visualizer', value: text }}
  ]);
}}

function _submitComparisonToHS(comp) {{
  const email = (window.RSV_CONFIG && RSV_CONFIG.userEmail) || storedEmail;
  if (!email || !comp) return;
  const enabledSlots = (comp.slots || []).filter(s => s.enabled);
  const slotLines = enabledSlots.map((s, i) => {{
    const coreStr = (s.core || []).filter(r => r.asset && r.weight > 0)
      .map(r => r.weight + '% ' + r.asset).join(' · ') || 'None';
    const stackAssets = (s.stack || []).filter(r => r.asset && r.weight > 0);
    let out = '  ' + (i + 1) + '. ' + (s.portfolioName || 'Portfolio ' + (i + 1));
    if (s.fee > 0) out += ' (Fee: ' + (s.fee / 100).toFixed(2) + '%)';
    out += '\\n     Core:  ' + coreStr;
    if (stackAssets.length > 0) {{
      out += '\\n     Stack: ' + stackAssets.map(r => r.weight + '% ' + r.asset).join(' · ');
    }}
    return out;
  }}).join('\\n');
  const savedAt = comp.savedAt ? ' — Saved: ' + comp.savedAt : '';
  const text = comp.name + savedAt + '\\n' + slotLines;
  submitHubSpotForm(HS_SAVE_COMPARISON_FORM_ID, [
    {{ name: 'email', value: email }},
    {{ name: 'saved_comparison_visualizer', value: text }}
  ]);
}}

var consultantDetails = {{
  'Dillon Pierce': {{
    url: 'https://meetings.hubspot.com/dillon-pierce/return-stacked-portfolio-visualizer-meeting-djp',
    photo: 'https://www.returnstacked.com/wp-content/uploads/2024/11/dillon-pierce-return-stacked-portfolio-solutions.png',
    email: 'dpierce@thinknewfound.com'
  }},
  'Brady Stibi': {{
    url: 'https://meetings.hubspot.com/brady-stibi/return-stacked-portfolio-visualizer-meeting-bsp',
    photo: 'https://www.returnstacked.com/wp-content/uploads/2024/11/brady-return-stacked-portfolio-solutions.png',
    email: 'bstibi@thinknewfound.com'
  }},
  'Spencer Booth': {{
    url: 'https://meetings.hubspot.com/spencer-booth/portfolio-visualizer-meeting',
    photo: 'https://www.returnstacked.com/wp-content/uploads/2024/11/spencer-booth-return-stacked.png',
    email: 'sbooth@thinknewfound.com'
  }},
  'Richard Laterman': {{
    url: 'https://meetings.hubspot.com/richard-laterman/return-stacked-portfolio-visualizer-meeting-rl',
    photo: 'https://www.returnstacked.com/wp-content/uploads/2024/11/richard-laterman-return-stacked-portfolio-solutions-480x480.png',
    email: 'richard.laterman@investresolve.com'
  }}
}};

var stateToConsultant = {{
  'Texas': 'Dillon Pierce', 'Kansas': 'Dillon Pierce', 'Oklahoma': 'Dillon Pierce',
  'Nebraska': 'Dillon Pierce', 'South Dakota': 'Dillon Pierce', 'North Dakota': 'Dillon Pierce',
  'Minnesota': 'Dillon Pierce', 'Iowa': 'Dillon Pierce', 'Missouri': 'Dillon Pierce',
  'Wisconsin': 'Dillon Pierce', 'Michigan': 'Dillon Pierce', 'Illinois': 'Dillon Pierce',
  'Indiana': 'Dillon Pierce', 'Tennessee': 'Dillon Pierce', 'Arkansas': 'Dillon Pierce',
  'Louisiana': 'Dillon Pierce', 'Colorado': 'Dillon Pierce',
  'Washington': 'Brady Stibi', 'Oregon': 'Brady Stibi', 'California': 'Brady Stibi',
  'Nevada': 'Brady Stibi', 'Idaho': 'Brady Stibi', 'Montana': 'Brady Stibi',
  'Wyoming': 'Brady Stibi', 'Utah': 'Brady Stibi', 'Arizona': 'Brady Stibi',
  'New Mexico': 'Brady Stibi', 'Alaska': 'Brady Stibi', 'Hawaii': 'Brady Stibi',
  'Maine': 'Spencer Booth', 'New Hampshire': 'Spencer Booth', 'Vermont': 'Spencer Booth',
  'Massachusetts': 'Spencer Booth', 'Rhode Island': 'Spencer Booth', 'Connecticut': 'Spencer Booth',
  'New York': 'Spencer Booth', 'Pennsylvania': 'Spencer Booth', 'New Jersey': 'Spencer Booth',
  'Delaware': 'Spencer Booth', 'Maryland': 'Spencer Booth', 'District of Columbia': 'Spencer Booth',
  'Virginia': 'Spencer Booth', 'West Virginia': 'Spencer Booth', 'North Carolina': 'Spencer Booth',
  'South Carolina': 'Spencer Booth', 'Georgia': 'Spencer Booth', 'Florida': 'Spencer Booth',
  'Alabama': 'Spencer Booth', 'Mississippi': 'Spencer Booth', 'Kentucky': 'Spencer Booth',
  'International / Ex-US': 'Richard Laterman'
}};

var dillonStates = new Set(Object.keys(stateToConsultant).filter(function(s) {{ return stateToConsultant[s] === 'Dillon Pierce'; }}));
var underHundredM = new Set(['Under $5M', '$5M – $25M', '$25M – $50M', '$50M – $100M']);

function resolveConsultant(aum, region) {{
  var consultant = stateToConsultant[region] || 'Richard Laterman';
  if (dillonStates.has(region) && underHundredM.has(aum)) {{
    consultant = 'Richard Laterman';
  }}
  return {{ name: consultant, details: consultantDetails[consultant] }};
}}

// ── Initialize ──
document.addEventListener("DOMContentLoaded", () => RSV.init());
</script>
</body>
</html>'''

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Generated {OUTPUT_FILE}: {os.path.getsize(OUTPUT_FILE) / 1024:.0f} KB")

# ── Generate WordPress/Divi embed outputs ──
# Produces rsv_widget.js (upload to server) and rsv_widget_embed.html (paste into Divi Code module)

# Extract CSS block (the single <style> block in the <head>)
style_start = html.index('<style>') + len('<style>')
style_end   = html.index('</style>')
css_block   = html[style_start:style_end]

# Extract body HTML (between <body> and the inline <script> block)
body_start  = html.index('<body>') + len('<body>')
script_open = html.rindex('<script>')          # last <script> = the inline block
body_html   = html[body_start:script_open].strip()

# Extract the JS block (between last <script> and its </script>)
script_close = html.rindex('</script>')
js_block     = html[script_open + len('<script>'):script_close].strip()

# Divi compatibility overrides – defeat theme styles that bleed into the widget.
# Uses #rsv-widget-root prefix + !important on properties known to be clobbered by Divi.
DIVI_OVERRIDES = """
/* ── Divi Compatibility Overrides ──────────────────────────────────────────
   These rules use #rsv-widget-root + !important to win against Divi theme
   selectors that bleed through the :where() specificity shield.
   ───────────────────────────────────────────────────────────────────────── */

/* Box model + base font
   Setting font-family here fixes Divi's Georgia bleeding into table cells,
   spans, and other elements not covered by the input/select rule below.
   The light-gray background + padding form the backdrop that makes the
   white .rsv-widget read as a floating card (matches the simple visualizer). */
#rsv-widget-root {
  box-sizing:  border-box !important;
  font-family: "DM Sans", sans-serif !important;
  background:  #f5f6fa !important;
  padding:     24px !important;
}
#rsv-widget-root * {
  box-sizing: border-box !important;
}

/* Divi adds padding-bottom:1em to every <p> */
#rsv-widget-root p {
  padding-bottom: 0 !important;
  margin-bottom:  0 !important;
  line-height:    inherit !important;
}

/* Divi adds padding-bottom:10px and fixed color to headings */
#rsv-widget-root h1, #rsv-widget-root h2, #rsv-widget-root h3,
#rsv-widget-root h4, #rsv-widget-root h5, #rsv-widget-root h6 {
  padding-bottom: 0 !important;
  margin-bottom:  0 !important;
  line-height:    inherit !important;
  color:          inherit !important;
}

/* ── Inputs & selects ──
   Divi + plugins set width:100%, gray backgrounds, fixed heights, and
   wrong fonts. The width:auto here is the critical fix – without it every
   input stretches to full row width and stacks.
   font-size is pinned to 12px (matching the Volatility cell) so Divi's
   14px can't bleed in. Do NOT use `inherit` here — it makes each input
   take its parent <td>/body size, which balloons them inconsistently.
   NOTE: button is intentionally excluded — see separate rule below. */
#rsv-widget-root input,
#rsv-widget-root select,
#rsv-widget-root textarea {
  font-family:      "DM Sans", sans-serif !important;
  font-size:        12px !important;
  letter-spacing:   normal !important;
  text-transform:   none !important;
  line-height:      normal !important;
  width:            auto !important;
  height:           auto !important;
  min-height:       0 !important;
  background-color: #ffffff !important;
  color:            #2c3641 !important;
  border:           1px solid #bfbfbf !important;
  border-radius:    4px !important;
  box-shadow:       none !important;
}

/* ── Buttons ──
   Only reset what Divi adds (casing, spacing, sizing box). Do NOT override
   background-color, border, color, OR font-size — the widget's own classes
   (.rsv-compute-btn 14px, --compact 12px, .rsv-cta-strip-btn, etc.) set
   those and beat Divi's bare `button` rule on specificity. Forcing a single
   font-size here (or `inherit`) flattens the button hierarchy / balloons text. */
#rsv-widget-root button {
  font-family:    "DM Sans", sans-serif !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  line-height:    normal !important;
  width:          auto !important;
  height:         auto !important;
  min-height:     0 !important;
  box-shadow:     none !important;
  cursor:         pointer !important;
}

/* Restore the combobox trigger width — the button width:auto reset above
   makes it size to its content, so a long asset name spills over the
   Weight column. 100% pins it to its fixed-layout table cell; the name
   truncates with ellipsis inside. */
#rsv-widget-root .rsv-combo-trigger {
  width:     100% !important;
  max-width: 100% !important;
}

/* Restore specific input widths the widget intentionally sets.
   text-align:center + appearance:textfield match the widget design:
   values are centered and the native up/down spinners are hidden. */
#rsv-widget-root .rsv-name-row input {
  width: 240px !important;
}
#rsv-widget-root .rsv-alloc-table input[type="number"] {
  width:      60px !important;
  padding:    4px 6px !important;
  text-align: center !important;
  -webkit-appearance: textfield !important;
  appearance:         textfield !important;
}
#rsv-widget-root .rsv-fee-row input[type="number"] {
  width:      80px !important;
  text-align: center !important;
  -webkit-appearance: textfield !important;
  appearance:         textfield !important;
}
/* Kill the spinner buttons even if Divi/WebKit tries to show them */
#rsv-widget-root input[type="number"]::-webkit-outer-spin-button,
#rsv-widget-root input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none !important;
  margin: 0 !important;
}
#rsv-widget-root .rsv-date-range-bar input[type="date"] {
  width: 140px !important;
}

/* Fee row must stay as a flex row so the input doesn't crowd the buttons */
#rsv-widget-root .rsv-fee-row {
  display:     flex !important;
  align-items: center !important;
  flex-wrap:   nowrap !important;
  gap:         12px !important;
}

/* Date range bar is a flex row – inputs must not expand to full width */
#rsv-widget-root .rsv-date-range-bar {
  display:     flex !important;
  flex-wrap:   wrap !important;
  align-items: center !important;
  gap:         6px !important;
}

/* Divi link colour overrides */
#rsv-widget-root a {
  color:           inherit !important;
  text-decoration: none !important;
}

/* Lists – Divi adds margins/padding */
#rsv-widget-root ul,
#rsv-widget-root ol {
  margin:     0 !important;
  padding:    0 !important;
  list-style: none !important;
}

/* ── Disclosures spacing ──
   The generic `#rsv-widget-root p { margin-bottom: 0 }` rule above (needed to
   stop Divi's 1em paragraph padding everywhere else) also flattens the
   disclosures list. Restore breathing room between definitions and headings. */
#rsv-widget-root .rsv-disclosures-content p {
  margin-bottom: 10px !important;
}
#rsv-widget-root .rsv-disclosures-content h3 {
  margin: 16px 0 8px 0 !important;
}
#rsv-widget-root .rsv-disclosures-content h3:first-child {
  margin-top: 0 !important;
}

/* ── Disclosures arrow glyph ──
   DM Sans doesn't include U+25B6 (▶). Force a font that does so the triangle
   renders instead of a replacement '?'. Namespaced class (.rsv-arrow) so it
   doesn't collide with Divi's own global .arrow class, which was overriding
   the static disclosures toggle and rendering it as a '?'. */
#rsv-widget-root .rsv-arrow {
  font-family: Arial, "Segoe UI Symbol", "Apple Symbols", sans-serif !important;
  font-style:  normal !important;
}

/* ── Intake overlay ──
   In the WordPress version all users are pre-authenticated via WP login.
   activateWidget() hides this on init, but this rule prevents the flash
   that occurs between page paint and JS execution. */
#rsv-widget-root .rsv-intake-overlay {
  display: none !important;
}

/* ── Allocation table headers ──
   Divi's global table/th typography (size, weight, letter-spacing) widens
   the fixed-layout columns until the VOLATILITY header overlaps the panel
   edge. Pin the widget's own header metrics and clip any residue. */
#rsv-widget-root .rsv-alloc-table th {
  font-size:      11px !important;
  font-weight:    700 !important;
  letter-spacing: 0.5px !important;
  line-height:    normal !important;
  padding:        6px 8px !important;
  overflow:       hidden !important;
}

/* ── Allocation bar chart ──
   The bar chart and its labels can exceed the panel width. Clip to container. */
#rsv-widget-root .rsv-alloc-bar-wrap {
  overflow: hidden !important;
  min-width: 0 !important;
}
#rsv-widget-root .rsv-alloc-vis {
  max-width: 100% !important;
  overflow:  hidden !important;
}

/* ── Z-index: Divi stacking contexts clip widget overlays ── */
/* Divi DiviArea uses z-index:1000000; our dropdowns must exceed that */
#rsv-widget-root .rsv-combo-panel {
  z-index: 9999999 !important;
}
#rsv-widget-root .rsv-modal-overlay {
  z-index: 99999998 !important;
}
#rsv-widget-root .rsv-tooltip .rsv-tooltip-text,
#rsv-widget-root .rsv-btn-tooltip .rsv-tooltip-text {
  z-index: 9999997 !important;
}
"""

# Write rsv_widget.js
JS_FILE = "rsv_widget.js"
with open(JS_FILE, "w", encoding="utf-8") as f:
    f.write(js_block)
print(f"Generated {JS_FILE}: {os.path.getsize(JS_FILE) / 1024:.0f} KB")

# Write rsv_widget_embed.html
# This file goes into the Divi Code module as-is.
# Before deploying: update the <script src> path to wherever rsv_widget.js is hosted.
# The PHP plugin injects window.RSV_CONFIG immediately before the <script src> line.
EMBED_FILE = "rsv_widget_embed.html"
embed_html = (
    '<div id="rsv-widget-root">\n'
    '<style>\n'
    + css_block
    + DIVI_OVERRIDES
    + '</style>\n\n'
    + body_html
    + '\n\n'
    + '<!-- DEPLOY: upload rsv_widget.js to your server and update this path -->\n'
    + '<!-- The PHP plugin injects window.RSV_CONFIG as a <script> block above this line -->\n'
    + '<script src="/wp-content/uploads/rsv-widget/rsv_widget.js"></script>\n'
    + '</div>\n'
)
with open(EMBED_FILE, "w", encoding="utf-8") as f:
    f.write(embed_html)
print(f"Generated {EMBED_FILE}: {os.path.getsize(EMBED_FILE) / 1024:.0f} KB")
