#!/usr/bin/env python3
"""reformat_html.py -- Transform trend report from dashboard to paged PDF layout.

Reads the current HTML, extracts sections, and re-templates into explicit
US Letter page divs with headers, footers, and page numbers using the shared
white paper template.

Usage:
    python reformat_html.py

Output overwrites trend-replication-analysis.html in place.
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent  # RAM_Brain root

# Import shared white paper template
sys.path.insert(0, str(
    ROOT / "references" / "brand-assets" / "resolve-am" / "white-paper-template"
))
from white_paper_template import (
    WhitePaperBuilder,
    extract_cover,
    extract_doc_footer,
    extract_sections,
    split_section_at,
)

# --- Paths ----------------------------------------------------------------
HTML_PATH = HERE / "trend-replication-analysis.html"


# --- Disclaimer consolidation --------------------------------------------

# Unique substrings that identify each boilerplate block
_BLOCK_A_ID = "hypothetical model returns of ReSolve"
_BLOCK_C_ID = "composite results are extracted from actual trading"

FOOTNOTE = (
    '<p class="disclaimer">See Methodology &amp; Important Information on '
    "page 2. Past performance is not indicative of future results.</p>"
)

METHODOLOGY_HTML = """\
<div class="section">
  <h2>Methodology &amp; Important Information</h2>

  <h3>Series Definitions</h3>
  <table>
    <thead>
      <tr><th style="width:35%; text-align:left">Series</th><th style="text-align:left">Description</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><span style="color:#000000; font-size:14px">&#9632;</span> SG Trend Index (Excess)</td>
        <td style="text-align:left">Soci&eacute;t&eacute; G&eacute;n&eacute;rale Trend Index (NEIXCTAT) minus Bloomberg Short Treasury Total Return Index (LD12TRUU). Returns are net of underlying fees.</td>
      </tr>
      <tr>
        <td><span style="color:#00478D; font-size:14px">&#9632;</span> Blend (Net)</td>
        <td style="text-align:left">15% Top Down Small (Gross) / 15% Top Down Medium (Gross) / 70% Bottom Up (Gross), rebalanced daily. Net of estimated trading costs and 0.95% annual expense ratio.</td>
      </tr>
      <tr>
        <td><span style="color:#FBBA00; font-size:14px">&#9632;</span> Bottom Up (Net) &ndash; 70%</td>
        <td style="text-align:left">Hypothetical model returns of ReSolve's bottom-up trend replication sub-strategy. Net of estimated trading costs and 0.95% annual expense ratio.</td>
      </tr>
      <tr>
        <td><span style="color:#89D2FF; font-size:14px">&#9632;</span> Top Down Medium (Net) &ndash; 15%</td>
        <td style="text-align:left">Hypothetical model returns of ReSolve's medium-lookback trend replication sub-strategy. Net of estimated trading costs and 0.95% annual expense ratio.</td>
      </tr>
      <tr>
        <td><span style="color:#6F4596; font-size:14px">&#9632;</span> Top Down Small (Net) &ndash; 15%</td>
        <td style="text-align:left">Hypothetical model returns of ReSolve's short-lookback trend replication sub-strategy. Net of estimated trading costs and 0.95% annual expense ratio.</td>
      </tr>
    </tbody>
  </table>

  <p style="margin-top:10px; font-size:11px; color:#1a1a1a;">
    <strong>Source:</strong> Bloomberg, Soci&eacute;t&eacute; G&eacute;n&eacute;rale.
    <strong>Calculations:</strong> ReSolve Asset Management SEZC (Cayman).
    Returns assume the reinvestment of all distributions.
    Analysis period: Feb 08, 2023 &ndash; Feb 06, 2026.
  </p>

  <h3>Hypothetical Model Returns</h3>
  <p class="disclaimer" style="border-top:none; padding-top:0;">Top Down #1 (Net), Top Down #2 (Net), Bottom Up (Net), and Blend (Net) are the hypothetical model returns of ReSolve&rsquo;s trend replication sub strategies. Top Down #1 (Net), Top Down #2 (Net), and Bottom Up (Net) are net of estimated trading costs and a 0.95% annual expense ratio. Blend (Net) is a 15% Top Down #1 (Gross) / 15% Top Down #2 (Gross) / 70% Bottom Up (Gross) portfolio rebalanced daily, net of estimated trading costs and a 0.95% annual expense ratio. SocGen Trend Index (Excess) is the Soci&eacute;t&eacute; G&eacute;n&eacute;rale Trend Index (NEIXCTAT) minus the Bloomberg Short Treasury Total Return Index Value Unhedged Index (LD12TRUU). Returns assume the reinvestment of all distributions. Returns of NEIXCTAT are net of underlying fees. Index returns are hypothetical. You cannot invest in an index. Past performance is not indicative of future returns. Please see Important Notices and Disclaimers at the end of this document for additional important information. This material is for illustrative purposes only and is not meant to reflect the actual investment of the Trend Replication Program.</p>

  <h3>Composite Trading Results</h3>
  <p class="disclaimer" style="border-top:none; padding-top:0;">Certain sections of this report present composite results extracted from actual trading returns for the Program ReSolve Global operates within third party multi-strategy funds and as such are considered SIMULATED performance. The results are excess returns (calculated prior to any yield on posted collateral) and less a 0.95% annual fee. Please see Important Notices and Disclaimers at the end of this document for additional important information regarding hypothetical performance. These materials do not constitute an offer or solicitation of an offer to make an investment in any of the funds or separately managed accounts ReSolve Global manages. Past performance is not indicative of future results. The risk of loss in trading commodity interests is substantial.</p>
</div>"""


def strip_boilerplate(section_html: str) -> str:
    """Replace repeated boilerplate disclaimers with a short footnote."""
    added_footnote = False

    def _replace(m):
        nonlocal added_footnote
        text = m.group(0)
        if _BLOCK_A_ID in text or _BLOCK_C_ID in text:
            if not added_footnote:
                added_footnote = True
                return FOOTNOTE
            return ""  # drop duplicate boilerplate in same section
        return text  # keep unique disclaimers (e.g. Important Notices)

    return re.sub(
        r'<p class="disclaimer"[^>]*>.*?</p>',
        _replace,
        section_html,
        flags=re.DOTALL,
    )


# ---------------------------------------------------------------------------
# Page map: each entry is a list of section indices to place on that page.
# Page numbering starts at 2 (cover is unnumbered).
# ---------------------------------------------------------------------------

# After splitting, sections are re-indexed:
#  0: Executive Summary           9:  Monthly Return Analysis (scatter)  18: Thought Experiment (part B)
#  1: Growth of $1               10:  Monthly Return Analysis (bars)     19: Sub-Program Assessment
#  2: Relative Performance       11:  Annual Performance                 20: Quarterly Tracking Detail
#  3: Full-Period Statistics      12:  Drawdown Analysis                 21: Conclusions
#  4: Rolling Correlation (pt A) 13:  Thought Experiment (part A)       22: Technical Glossary
#  5: Rolling Correlation (pt B) 14:  (unused slot)                     23: Index Definitions
#  6: Tracking Error (part A)    15:  (unused slot)                     24: Important Disclosures
#  7: Tracking Error (part B)    16:  (unused slot)
#  8: Cumulative Return Diff     17:  (unused slot)

PAGE_MAP = [
    [0],             # p2:  Executive Summary
    [1],             # p3:  Growth of $1
    [2],             # p4:  Relative Performance
    [3],             # p5:  Full-Period Statistics
    [4],             # p6:  Rolling Correlation (Fig 3, 63-day)
    [5],             # p7:  Rolling Correlation cont'd (Fig 4, 126-day)
    [6],             # p8:  Tracking Error (chart + Lo explanation)
    [7],             # p9:  Tracking Error cont'd (rolling 1yr + callout)
    [8],             # p10: Cumulative Return Difference
    [9],             # p11: Monthly Return Analysis (scatter + interpretation)
    [10],            # p12: Monthly Return Analysis cont'd (bar chart)
    [11],            # p13: Annual Performance
    [12],            # p14: Drawdown Analysis
    [13],            # p15: Thought Experiment (intro + TE frontier)
    [14],            # p16: Thought Experiment cont'd (weights + analysis)
    [15],            # p17: Sub-Program Assessment
    [16],            # p18: Quarterly Tracking Detail
    [17],            # p19: Conclusions
    [18],            # p20: Technical Glossary
    [19],            # p21: Index Definitions
    [20],            # p22: Important Disclosures
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Reading HTML...")
    html = HTML_PATH.read_text(encoding="utf-8")

    print("Extracting cover page...")
    cover = extract_cover(html)
    print(f"  {'Cover page found' if cover else 'No cover page -- will generate one'}")

    print("Extracting sections...")
    raw_sections = extract_sections(html)
    print(f"  Found {len(raw_sections)} raw sections")

    if len(raw_sections) == 21:
        # Already split (from a previous reformat run) -- use as-is
        sections = raw_sections
        print("  Sections already split -- using as-is")
    else:
        # Raw HTML from build_report.py (17 sections) -- split long sections
        rc_a, rc_b = split_section_at(
            raw_sections[4], '<h3>Longer-Window Perspective</h3>')
        te_a, te_b = split_section_at(
            raw_sections[5], '<h3>Rolling One-Year Return Differences</h3>')
        mra_a, mra_b = split_section_at(
            raw_sections[7], '<h3>Month-by-Month Returns</h3>')
        te_exp_a, te_exp_b = split_section_at(
            raw_sections[10], '<p>The frontier reveals a notably flat')

        sections = list(raw_sections[:4])           # 0-3: Exec Summary, Growth, Relative, Stats
        sections.append(rc_a)                        # 4: Rolling Correlation (Fig 3)
        sections.append(rc_b)                        # 5: Rolling Correlation cont'd (Fig 4)
        sections.append(te_a)                        # 6: Tracking Error (chart + Lo explanation)
        sections.append(te_b)                        # 7: Tracking Error cont'd (rolling 1yr + callout)
        sections.append(raw_sections[6])             # 8: Cumulative Return Difference
        sections.append(mra_a)                       # 9: Monthly Return Analysis (scatter)
        sections.append(mra_b)                       # 10: Monthly Return Analysis cont'd (bars)
        sections.extend(raw_sections[8:10])          # 11-12: Annual Performance, Drawdown Analysis
        sections.append(te_exp_a)                    # 13: Thought Experiment (intro + TE frontier)
        sections.append(te_exp_b)                    # 14: Thought Experiment cont'd (weights + analysis)
        sections.extend(raw_sections[11:])           # 15-20: Sub-Program, Quarterly, Conclusions, Glossary, Index Defs, Disclosures
        print(f"  After splitting: {len(sections)} sections")

    doc_footer = extract_doc_footer(html)

    # Build using shared template
    builder = WhitePaperBuilder(
        header_line1="Trend Replication Program",
        header_line2="3-Year Analysis",
        document_title="Trend Replication Program - 3-Year Analysis",
    )

    # Cover: use existing if present, otherwise generate
    cover_kwargs = {}
    if not cover:
        cover_kwargs = dict(
            title="Trend Replication Program",
            subtitle="3-Year Hypothetical Performance Analysis",
            doc_type="For use with sophisticated investors and financial professionals only. Not for distribution to the general public.",
            date_line="Feb 08, 2023 - Feb 06, 2026",
        )

    print("Building output...")
    output = builder.build_from_page_map(
        sections=sections,
        page_map=PAGE_MAP,
        cover_html=cover,
        doc_footer=doc_footer,
        **cover_kwargs,
    )

    print(f"Writing {len(output):,} chars to {HTML_PATH.name}...")
    HTML_PATH.write_text(output, encoding="utf-8")
    print(f"Done.")


if __name__ == "__main__":
    main()
