"""Build the Trend Replication Program fact sheet (HTML, 2 pages, Carry-style)."""
import os
import re
import base64

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = os.path.abspath(os.path.join(PROJECT, "..", "..", "..", "..", "references", "brand-assets", "resolve-am"))
LOGO_B64 = os.path.join(BRAND, "cover-template", "logo-black_b64.txt")
FONTS_DIR = os.path.join(BRAND, "Fonts")
FONTS_SUBDIR = os.path.join(FONTS_DIR, "Helvetica Neue LT Std")
SVG_CHART = os.path.join(PROJECT, "Trend Rep Line chart.svg")
OUT_HTML = os.path.join(PROJECT, "output", "trend-rep-factsheet.html")


def b64file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


with open(LOGO_B64) as f:
    logo = f.read().strip()
with open(SVG_CHART, encoding="utf-8") as f:
    svg = f.read()
svg = re.sub(r"<\?xml[^?]*\?>", "", svg).strip()
# Inject viewBox so the SVG scales responsively inside the chart container.
m = re.match(r'(<svg\b)([^>]*)>', svg)
if m and 'viewBox' not in m.group(2):
    attrs = m.group(2)
    wm = re.search(r'width="(\d+)"', attrs)
    hm = re.search(r'height="(\d+)"', attrs)
    if wm and hm:
        w, h = wm.group(1), hm.group(1)
        attrs_new = re.sub(r'\s*width="\d+"', '', attrs)
        attrs_new = re.sub(r'\s*height="\d+"', '', attrs_new)
        attrs_new = f' viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid meet"' + attrs_new
        svg = m.group(1) + attrs_new + '>' + svg[m.end():]

fonts = {
    "HNLt":    os.path.join(FONTS_DIR, "HelveticaNeueLTStd-Lt.otf"),
    "HNRm":    os.path.join(FONTS_DIR, "HelveticaNeueLTStd-Roman.otf"),
    "HNBd":    os.path.join(FONTS_DIR, "HelveticaNeueLTStd-Bd.otf"),
    "HNIt":    os.path.join(FONTS_SUBDIR, "HelveticaNeueLTStd-It.otf"),
    "HLtLt":   os.path.join(FONTS_SUBDIR, "HelveticaLTStd-Light.otf"),
    "HLtRm":   os.path.join(FONTS_DIR, "HelveticaLTStd-Roman.otf"),
}
fonts_b64 = {k: b64file(v) for k, v in fonts.items()}

# Monthly returns from data/trend-rep-live-performance.xlsx.
monthly = {
    2023: [None, None, -0.10643, 0.00295, -0.01022, 0.03903,
           -0.00614, -0.03495, 0.04546, -0.00555, -0.06040, -0.00345],
    2024: [-0.02186, 0.04257, 0.03371, 0.02423, -0.01419, -0.00365,
           -0.03826, -0.01872, 0.00162, -0.06488, 0.00696, 0.01543],
    2025: [0.01850, -0.02693, -0.02040, -0.05220, -0.00447, 0.01801,
           -0.03348, 0.02657, 0.05549, 0.03503, 0.00016, 0.01829],
    2026: [0.03051, 0.04583, -0.02654, None, None, None,
           None, None, None, None, None, None],
}


def ytd(vals):
    c = 1.0
    any_v = False
    for v in vals:
        if v is None:
            continue
        c *= (1 + v)
        any_v = True
    return (c - 1) if any_v else None


def cell(v):
    if v is None:
        return "<td></td>"
    return f"<td>{v*100:.2f}%</td>"


def ytd_cell(v):
    if v is None:
        return '<td class="ytd"></td>'
    return f'<td class="ytd">{v*100:.2f}%</td>'


rows = []
for y in sorted(monthly.keys(), reverse=True):
    vals = monthly[y]
    cells = "".join(cell(v) for v in vals)
    rows.append(f'<tr><td class="year">{y}</td>{cells}{ytd_cell(ytd(vals))}</tr>')
monthly_rows = "\n          ".join(rows)

FONT_FACE = """
@font-face {{ font-family:'HN'; font-weight: 300; font-style: normal;
  src: url(data:font/otf;base64,{HNLt}) format('opentype'); }}
@font-face {{ font-family:'HN'; font-weight: 400; font-style: normal;
  src: url(data:font/otf;base64,{HNRm}) format('opentype'); }}
@font-face {{ font-family:'HN'; font-weight: 700; font-style: normal;
  src: url(data:font/otf;base64,{HNBd}) format('opentype'); }}
@font-face {{ font-family:'HN'; font-weight: 400; font-style: italic;
  src: url(data:font/otf;base64,{HNIt}) format('opentype'); }}
@font-face {{ font-family:'HLt'; font-weight: 300; font-style: normal;
  src: url(data:font/otf;base64,{HLtLt}) format('opentype'); }}
@font-face {{ font-family:'HLt'; font-weight: 400; font-style: normal;
  src: url(data:font/otf;base64,{HLtRm}) format('opentype'); }}
""".format(**fonts_b64)


CSS = r"""
@page { size: Letter; margin: 0; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; font-family:'HN','Helvetica Neue','Helvetica LT Std',Helvetica,Arial,sans-serif; color:#000; background:#DDD; }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; font-weight:300; }

.page {
  width: 8.5in; height: 11in; position: relative;
  background:#fff; margin: 0.25in auto;
  box-shadow: 0 0 8pt rgba(0,0,0,0.15);
  page-break-after: always; overflow: hidden;
  display: grid;
  grid-template-columns: 2.2in 1fr;
  grid-template-rows: 1fr;
}
.page:last-child { page-break-after: auto; }
@media print { html, body { background:#fff; } .page { margin:0; box-shadow:none; } }

/* Sidebar (L shape: full height pale-blue column) */
.side {
  background:#E9F5FF;
  padding: 0.45in 0.22in 0.25in 0.35in;
  display:flex; flex-direction: column;
  color:#3E3D40;
  font-size: 6.5pt;
  line-height: 1.35;
}
.side .logo { width: 1.35in; display:block; margin-bottom: 0.5in; }
.side h3 { color:#003A6D; font-family:'HN'; font-weight:700; font-size:7pt; margin:0 0 6pt 0; padding:0; }
.side .fields { flex: 0 0 auto; }
.side .kv { display: grid; grid-template-columns: 1fr 1fr; gap: 4pt; padding: 4.5pt 0; border-bottom: 0.5pt solid #C3DAEC; }
.side .kv .k { font-weight:700; color:#48494B; font-size:6pt; }
.side .kv .v { color:#3E3D40; font-weight:400; font-size:6pt; }
.side .spacer { flex: 1 1 auto; }
.side .contact { margin-top: 0.3in; }
.side .contact .line { font-size:6pt; color:#3E3D40; line-height:1.55; }
.side .contact a { color:#187CBC; text-decoration: none; }
.side .pagenum { background:#FFFFFF; color:#48494B; display:inline-block; padding: 2pt 6pt; font-size: 7pt; margin-top: 6pt; border: 0.5pt solid #C3DAEC; }

/* Main content column */
.main {
  padding: 0.45in 0.4in 0.35in 0.35in;
  position: relative;
  font-size: 7pt;
  line-height: 1.4;
  color:#000;
  font-family:'HN'; font-weight:300;
}

/* Header: title (left) + date badge (right) */
.hdr {
  display:grid; grid-template-columns: 1fr auto; align-items:start;
  margin-bottom: 0.2in;
  min-height: 0.55in;
}
.hdr .title {
  font-family:'HN'; font-weight:700; color:#007FBF;
  font-size: 14pt; line-height: 1.15; letter-spacing: 0;
}
.hdr .title .sub { display:block; font-weight:700; }
.hdr .date {
  font-family:'HLt'; font-weight:400; color:#FFFFFF;
  font-size: 9pt;
  padding: 6pt 18pt 6pt 18pt;
  background: linear-gradient(to right, #006CA4 0%, #003A6D 100%);
  white-space: nowrap;
  align-self: start;
  margin-top: 2pt;
}
.hdr .date sup { font-size: 5.5pt; vertical-align: super; }

/* Section headings in main column */
h2.sec { color:#003A6D; font-family:'HN'; font-weight:700; font-size: 8pt; margin: 8pt 0 4pt 0; line-height:1.2; }
h2.sec:first-child { margin-top: 0; }
h2.sec .muted { color:#003A6D; font-family:'HN'; font-weight:400; font-style:italic; font-size: 7pt; }

/* Body paragraphs */
.main p { margin: 0 0 6pt 0; font-family:'HN'; font-weight:300; font-size: 7pt; color:#000; line-height:1.45; }

/* Monthly performance table */
table.perf { border-collapse: collapse; width: 100%; margin: 2pt 0 2pt 0; table-layout: fixed; }
table.perf th, table.perf td { padding: 3pt 2pt; text-align: right; font-size: 6pt; vertical-align: middle; font-family:'HN'; }
table.perf thead th {
  background: linear-gradient(to right, #008CD0 0%, #004779 100%);
  color:#FFFFFF; font-weight:700; text-align:center; font-size:6pt;
  padding: 4.5pt 2pt;
}
table.perf tbody td { border-bottom: 0.25pt solid #FFFFFF; }
table.perf tbody tr:nth-child(odd) td { background:#F1F2F2; }
table.perf tbody tr:nth-child(even) td { background:#E7E9E8; }
table.perf tbody td.year { color:#003A6D; font-family:'HN'; font-weight:400; text-align:center; background:#DCDFE0; font-size:6pt; }
table.perf tbody tr:nth-child(even) td.year { background:#D1D4D5; }
table.perf tbody td.ytd { font-family:'HN'; font-weight:700; color:#000; }

/* Stats table (inception row) */
table.stats { border-collapse: collapse; width: 100%; margin: 2pt 0 2pt 0; }
table.stats thead th {
  background: linear-gradient(to right, #008CD0 0%, #004779 100%);
  color:#FFFFFF; font-family:'HN'; font-weight:700; text-align:center;
  padding: 5pt 2pt; font-size: 6pt; line-height:1.15;
}
table.stats tbody td {
  background:#F1F2F2; text-align:center;
  font-family:'HN'; font-weight:400; color:#000;
  padding: 6pt 2pt; font-size: 6.5pt;
}

.main .foot-small {
  font-family:'HN'; font-weight:300; font-size: 6pt; color:#000;
  margin: 4pt 0 0 0; line-height: 1.4;
}
.main .foot-small strong { font-weight:700; text-transform: uppercase; letter-spacing: 0.2pt; }

/* Chart */
.chart-wrap { margin: 6pt 0 2pt 0; }
.chart-wrap svg { width: 100%; height: auto; display:block; }
.chart-caption { font-family:'HN'; font-style: italic; font-weight: 300; font-size: 5.5pt; color:#444; padding: 2pt 0 0 0; line-height:1.35; }

/* Bulleted lists (website copy) */
.bullets { margin: 0; padding: 0 0 0 14pt; }
.bullets li { font-family:'HLt'; font-weight:300; font-size: 7pt; line-height:1.45; margin-bottom: 3pt; color:#000; }

/* Disclosures */
.disclosure { font-family:'HN'; font-weight:300; font-size: 5.5pt; color:#000; line-height:1.45; margin: 4pt 0 0 0; }
.disclosure p { margin: 0 0 4pt 0; font-size: 5.5pt; }
.disclosure strong { font-weight:700; }

/* Pull quote / tagline */
.tagline { font-family:'HN'; font-weight:400; font-style: italic; font-size: 8pt; color:#003A6D; border-left: 2pt solid #FBBA00; padding: 4pt 0 4pt 10pt; margin: 6pt 0; line-height:1.4; }
"""

HTML_TMPL = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ReSolve Trend Replication Program — Fact Sheet</title>
<style>{font_face}</style>
<style>{css}</style>
</head>
<body>

<!-- PAGE 1 -->
<section class="page">
  <aside class="side">
    <img class="logo" src="data:image/png;base64,{logo}" alt="ReSolve Asset Management" />
    <div class="fields">
      <h3>General Information</h3>
      <div class="kv"><span class="k">Program</span><span class="v">Managed Futures Trend Following</span></div>
      <div class="kv"><span class="k">Region</span><span class="v">Global</span></div>
      <div class="kv"><span class="k">Structure:</span><span class="v">Separately Managed Account</span></div>
      <div class="kv"><span class="k">Management Fee:</span><span class="v">0.95%</span></div>
      <div class="kv"><span class="k">Account Minimum:</span><span class="v">$10,000,000 USD</span></div>
      <div class="kv"><span class="k">Investment Adviser:</span><span class="v">ReSolve Asset Management SEZC (Cayman)</span></div>
    </div>
    <div class="spacer"></div>
    <div class="contact">
      <h3>Contact us</h3>
      <div class="line">TF: 1-855-446-4170</div>
      <div class="line"><a href="mailto:info@investresolve.com">info@investresolve.com</a></div>
      <div class="line"><a href="https://www.investresolve.com">www.investresolve.com</a></div>
      <div class="line" style="margin-top:8pt;">ReSolve Asset Management SEZC (Cayman)</div>
      <div class="line">90 North Church Street</div>
      <div class="line">Strathvale House, 5<sup>th</sup> Floor</div>
      <div class="line">Georgetown, Grand Cayman</div>
      <div class="line">Cayman Islands, KY1-9012</div>
      <div class="pagenum">1</div>
    </div>
  </aside>

  <main class="main">
    <div class="hdr">
      <div class="title">ReSolve Trend Replication Program<span class="sub">Fact Sheet</span></div>
      <div class="date">March 31<sup>st</sup>, 2026</div>
    </div>

    <h2 class="sec">Strategy Description</h2>
    <p>The ReSolve Trend Replication Program seeks to deliver the return profile of leading trend-following managed-futures managers through a systematic, machine-learning-based replication of the SG Trend Index. The program blends top-down and bottom-up replication models across a globally diversified universe of equity, fixed income, currency and commodity futures, targeting medium- to long-term trends of 90+ days.</p>
    <p>The approach is designed to offer cost-efficient, transparent access to trend-following exposure with historically low correlation to traditional assets, and potential to deliver positive returns during equity drawdowns.</p>

    <h2 class="sec">Monthly Performance Returns Since Inception <span class="muted">(Using Excess Returns, net of 0.95% annual fee)</span></h2>
    <table class="perf">
      <thead>
        <tr>
          <th class="year">&nbsp;</th>
          <th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th><th>May</th><th>Jun</th>
          <th>Jul</th><th>Aug</th><th>Sep</th><th>Oct</th><th>Nov</th><th>Dec</th>
          <th>YTD</th>
        </tr>
      </thead>
      <tbody>
        {monthly_rows}
      </tbody>
    </table>

    <h2 class="sec">Performance Statistics Since Inception <span class="muted">(Using Excess Returns, net of 0.95% annual fee)</span></h2>
    <table class="stats">
      <thead>
        <tr>
          <th>1 Mo</th><th>3 Mo</th><th>6 Mo</th><th>YTD</th>
          <th>1 Yr</th><th>3 Yr</th><th>5 Yr</th>
          <th>Annualized<br>Program Return<br>(Inception)</th>
          <th>Program<br>Total Return<br>(Inception)</th>
          <th>Standard<br>Deviation</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>-2.65%</td><td>4.91%</td><td>10.59%</td><td>4.91%</td>
          <td>11.25%</td><td>-0.30%</td><td>&mdash;</td>
          <td>-3.68%</td><td>-10.91%</td><td>12.25%</td>
        </tr>
      </tbody>
    </table>
    <p class="foot-small"><strong>Past performance is not a guarantee of future results.</strong> The risk of loss in trading commodity interests is substantial. Indicated returns of one year or more are annualized. Inception: March 2023. See important disclosures on page 2.</p>

    <h2 class="sec">Growth of 100 Since Inception</h2>
    <div class="chart-wrap">
      {svg}
    </div>
    <p class="chart-caption">Source: ReSolve Asset Management SEZC (Cayman); Société Générale. The Trend Replication blend is constructed from 15% Top Down (Constrained), 15% Top Down (Full) and 70% Bottom Up sub-models, net of estimated transaction costs and the 0.95% management fee. SG Trend Index shown on an excess-return basis. Hypothetical performance; past performance is not indicative of future results.</p>
  </main>
</section>

<!-- PAGE 2 -->
<section class="page">
  <aside class="side">
    <img class="logo" src="data:image/png;base64,{logo}" alt="ReSolve Asset Management" />
    <div class="fields">
      <h3>General Information</h3>
      <div class="kv"><span class="k">Program</span><span class="v">Managed Futures Trend Following</span></div>
      <div class="kv"><span class="k">Region</span><span class="v">Global</span></div>
      <div class="kv"><span class="k">Structure:</span><span class="v">Separately Managed Account</span></div>
      <div class="kv"><span class="k">Management Fee:</span><span class="v">0.95%</span></div>
      <div class="kv"><span class="k">Account Minimum:</span><span class="v">$10,000,000 USD</span></div>
      <div class="kv"><span class="k">Investment Adviser:</span><span class="v">ReSolve Asset Management SEZC (Cayman)</span></div>
    </div>
    <div class="spacer"></div>
    <div class="contact">
      <h3>Contact us</h3>
      <div class="line">TF: 1-855-446-4170</div>
      <div class="line"><a href="mailto:info@investresolve.com">info@investresolve.com</a></div>
      <div class="line"><a href="https://www.investresolve.com">www.investresolve.com</a></div>
      <div class="line" style="margin-top:8pt;">ReSolve Asset Management SEZC (Cayman)</div>
      <div class="line">90 North Church Street</div>
      <div class="line">Strathvale House, 5<sup>th</sup> Floor</div>
      <div class="line">Georgetown, Grand Cayman</div>
      <div class="line">Cayman Islands, KY1-9012</div>
      <div class="pagenum">2</div>
    </div>
  </aside>

  <main class="main">
    <div class="hdr">
      <div class="title">ReSolve Trend Replication Program<span class="sub">Fact Sheet</span></div>
      <div class="date">March 31<sup>st</sup>, 2026</div>
    </div>

    <p class="tagline">"It's not the strongest of species that thrives, nor the most intelligent. It is the one that is most adaptable to change."</p>

    <h2 class="sec">Key Benefits</h2>
    <ul class="bullets">
      <li>Sophisticated replication of leading trend-following strategies using machine-learning techniques.</li>
      <li>Highly diversified exposure across global markets and asset classes to pursue returns in both up and down markets.</li>
      <li>Two complementary approaches combining top-down portfolio construction with bottom-up strategy selection.</li>
      <li>Potential to reduce overall portfolio volatility and provide downside protection during equity market drawdowns.</li>
      <li>Systematic, rules-based approach removing emotion and behavioral biases.</li>
    </ul>

    <h2 class="sec">Strategy Highlights</h2>
    <ul class="bullets">
      <li>Aims to replicate leading trend-following strategies in the managed-futures space using advanced modelling.</li>
      <li>Provides diversified exposure across global markets including equities, fixed income, currencies, and commodities.</li>
      <li>Combines top-down portfolio construction with bottom-up strategy selection.</li>
      <li>Trend models focus on medium- to long-term trends of 90+ days.</li>
      <li>Targets long-term returns competitive with stocks and bonds with lower correlation to both.</li>
      <li>Systematic, rules-based approach removes discretionary decision-making.</li>
    </ul>

    <h2 class="sec">Important Disclosures</h2>
    <div class="disclosure">
      <p><strong>Confidential and proprietary information.</strong> The contents hereof may not be reproduced or disseminated without the express written permission of ReSolve Asset Management SEZC (Cayman) ("ReSolve Global"). ReSolve Global is registered with the Commodity Futures Trading Commission as a Commodity Trading Advisor and Commodity Pool Operator. This registration is administered through the National Futures Association ("NFA"). Further, ReSolve Global is a registered person with the Cayman Islands Monetary Authority. ReSolve Global has claimed an exemption under CFTC Rule 4.7 which exempts ReSolve Global from certain part 4 requirements with respect to offerings to qualified eligible persons in the U.S.</p>
      <p><strong>Simulated / Hypothetical Performance.</strong> The composite results shown are extracted from actual trading returns for the Program ReSolve Global operates within third-party multi-strategy funds and are considered SIMULATED performance. Results are excess returns (calculated prior to any yield on posted collateral) and less a 0.95% annual fee. Results represent composite portions of broader strategies provided to third-party funds, and include estimates and assumptions regarding portfolio allocations, expenses and cash return on balances. They should not be taken as an indication of actual or future performance, and no representation is made that any account will achieve similar profits or losses. Detailed assumptions and estimates are available upon request.</p>
      <p><strong>Past performance is not indicative of future results.</strong> The risk of loss in trading commodity interests is substantial. Futures trading is speculative and can result in significant loss. Indicated returns of one year or more are annualized.</p>
      <p><strong>Intended Audience.</strong> This presentation is intended exclusively for Qualified Eligible Persons and Qualified Purchasers only and is being delivered to prospective investors on a confidential basis. These materials do not purport to be exhaustive or to contain all the information a prospective investor may desire. Prospective investors should review the Program's Offering Memoranda and rely on their own independent investigation of the Program. In the event of any inconsistency between this presentation and the Offering Memoranda or account opening documents, the latter shall prevail.</p>
      <p><strong>No Offer or Solicitation.</strong> Neither the Securities and Exchange Commission, the National Futures Association, nor any other securities regulatory authority has passed on the accuracy or adequacy of this presentation, and any representation to the contrary is unlawful. This material does not constitute an offer to sell or a solicitation of interest to purchase any securities or investment advisory services in any jurisdiction in which such offer or solicitation is not authorized.</p>
      <p><strong>Index Data.</strong> SG Trend Index data sourced from Société Générale and is used for replication and comparison purposes only. You cannot invest directly in an index.</p>
      <p>&copy; 2026 ReSolve Asset Management SEZC (Cayman). All rights reserved.</p>
    </div>
  </main>
</section>

</body>
</html>
"""

html = HTML_TMPL.format(
    font_face=FONT_FACE,
    css=CSS,
    logo=logo,
    svg=svg,
    monthly_rows=monthly_rows,
)

os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"wrote {OUT_HTML}  ({len(html):,} bytes)")
