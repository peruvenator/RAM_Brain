"""
Lazy Money Flyer -- HTML Build Script
Generates a self-contained 2-page US Letter HTML flyer
with all ReSolve AM brand assets embedded.

Usage:
    python build_flyer.py
"""

import base64
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BRAND = REPO / "references" / "brand-assets" / "resolve-am"
FONTS = BRAND / "Fonts" / "Helvetica Neue LT Std"
CHARTS = HERE / "chart_exports"
OUTPUT = HERE / "lazy-money-flyer.html"

# ---------------------------------------------------------------------------
# Brand colors
# ---------------------------------------------------------------------------
PRIMARY_BLUE = "#00478D"
DEEP_NAVY = "#032F69"
COVER_NAVY = "#04367B"
AMBER = "#FBBA00"
SKY_BLUE = "#89D2FF"
TEXT_BLUE = "#294A85"
DARK_GRAY = "#333333"
BORDER_GRAY = "#B5C4CE"
LIGHT_GRAY = "#F2F2F2"


def b64(path: Path) -> str:
    """Base64-encode a binary file."""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def svg_data_uri(path: Path) -> str:
    """Create a base64 data URI for an SVG file."""
    raw = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{raw}"


def png_data_uri(path_or_b64: Path | str) -> str:
    """Create a data URI for a PNG (from file path or pre-encoded base64 string)."""
    if isinstance(path_or_b64, Path):
        return f"data:image/png;base64,{b64(path_or_b64)}"
    return f"data:image/png;base64,{path_or_b64}"


def build():
    print("Loading assets...")

    # Logos (as data URIs to avoid SVG ID collisions)
    logo_black_uri = svg_data_uri(BRAND / "Logo" / "ReSolve-AM-logo-Black.svg")
    logo_white_uri = svg_data_uri(BRAND / "Logo" / "ReSolve-AM-logo-White.svg")

    # Geometric banner
    banner_uri = svg_data_uri(BRAND / "Backdrops" / "basic Banner.svg")

    # Corner decoration
    corner_b64 = (BRAND / "cover-template" / "corner-decoration_b64.txt").read_text().strip()
    corner_uri = png_data_uri(corner_b64)

    # Fonts
    font_lt_b64 = b64(FONTS / "HelveticaNeueLTStd-Lt.otf")
    font_bd_b64 = b64(FONTS / "HelveticaNeueLTStd-Bd.otf")
    font_md_b64 = b64(FONTS / "HelveticaNeueLTStd-Md.otf")

    # Charts & diagrams
    slide4_uri = png_data_uri(CHARTS / "slide4.png")
    annual_uri = png_data_uri(CHARTS / "annual_returns.png")
    corr_uri = png_data_uri(CHARTS / "correlation_heatmap.png")

    print("Building HTML...")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ReSolve Asset Management — Lazy Money SMA</title>
<style>
  /* --- Fonts --- */
  @font-face {{
    font-family: 'HelveticaNeue';
    src: url('data:font/opentype;base64,{font_lt_b64}') format('opentype');
    font-weight: 300;
    font-style: normal;
  }}
  @font-face {{
    font-family: 'HelveticaNeue';
    src: url('data:font/opentype;base64,{font_md_b64}') format('opentype');
    font-weight: 500;
    font-style: normal;
  }}
  @font-face {{
    font-family: 'HelveticaNeue';
    src: url('data:font/opentype;base64,{font_bd_b64}') format('opentype');
    font-weight: 700;
    font-style: normal;
  }}

  /* --- Reset --- */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'HelveticaNeue', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-weight: 300;
    color: {DARK_GRAY};
    background: #e8e8e8;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 40px;
    padding: 40px 20px;
  }}

  /* --- Page frame --- */
  .page {{
    width: 8.5in;
    height: 11in;
    background: #fff;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  }}

  /* --- Print --- */
  @page {{ size: letter; margin: 0; }}
  @media print {{
    body {{ background: #fff; padding: 0; gap: 0; }}
    .page {{
      box-shadow: none;
      page-break-after: always;
      width: 100%;
      height: 100vh;
    }}
    .page:last-child {{ page-break-after: auto; }}
  }}

  /* --- Banner strip --- */
  .banner-strip {{
    width: 100%;
    height: 42px;
    overflow: hidden;
    flex-shrink: 0;
  }}
  .banner-strip img {{
    width: 100%;
    display: block;
    transform: translateY(-2px);
  }}

  /* --- Corner decoration --- */
  .corner-deco {{
    position: absolute;
    bottom: 0;
    right: 0;
    width: 38%;
    opacity: 0.08;
  }}
  .corner-deco img {{
    width: 100%;
    display: block;
  }}

  /* --- Page 1 layout --- */
  .p1-content {{
    padding: 28px 48px 20px 48px;
  }}
  .p1-logo {{
    width: 200px;
    margin-bottom: 24px;
  }}
  .p1-headline {{
    font-size: 38px;
    font-weight: 700;
    color: {DEEP_NAVY};
    line-height: 1.15;
    margin-bottom: 6px;
    letter-spacing: -0.5px;
  }}
  .p1-subtitle {{
    font-size: 15px;
    font-weight: 500;
    color: {PRIMARY_BLUE};
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 20px;
  }}
  .p1-divider {{
    width: 100%;
    height: 1.5px;
    background: {BORDER_GRAY};
    margin-bottom: 20px;
  }}
  .p1-diagram {{
    width: 100%;
    margin-bottom: 18px;
    border: 1px solid {BORDER_GRAY};
    border-radius: 2px;
    overflow: hidden;
  }}
  .p1-diagram img {{
    width: 100%;
    display: block;
  }}
  .p1-two-col {{
    display: flex;
    gap: 32px;
    margin-bottom: 16px;
  }}
  .p1-col-left {{
    flex: 1;
  }}
  .p1-col-right {{
    flex: 1;
  }}
  .section-heading {{
    font-size: 13px;
    font-weight: 700;
    color: {PRIMARY_BLUE};
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
  }}
  .body-text {{
    font-size: 9.5px;
    line-height: 1.55;
    color: {DARK_GRAY};
  }}
  .bullet-list {{
    font-size: 9.5px;
    line-height: 1.7;
    color: {DARK_GRAY};
    list-style: none;
    padding: 0;
  }}
  .bullet-list li {{
    padding-left: 14px;
    position: relative;
    margin-bottom: 3px;
  }}
  .bullet-list li::before {{
    content: '';
    position: absolute;
    left: 0;
    top: 6px;
    width: 5px;
    height: 5px;
    background: {PRIMARY_BLUE};
    border-radius: 50%;
  }}
  .pull-quote {{
    border-left: 3px solid {AMBER};
    padding: 10px 16px;
    margin-top: 10px;
    background: {LIGHT_GRAY};
  }}
  .pull-quote .quote-text {{
    font-size: 10.5px;
    font-weight: 300;
    font-style: italic;
    color: {TEXT_BLUE};
    line-height: 1.5;
    margin-bottom: 4px;
  }}
  .pull-quote .quote-attr {{
    font-size: 8.5px;
    font-weight: 500;
    color: {DARK_GRAY};
  }}

  /* --- Page 2 layout --- */
  .p2-header {{
    background: {DEEP_NAVY};
    padding: 22px 48px 18px 48px;
  }}
  .p2-header-title {{
    font-size: 24px;
    font-weight: 700;
    color: #fff;
    line-height: 1.2;
    margin-bottom: 4px;
  }}
  .p2-header-sub {{
    font-size: 12px;
    font-weight: 300;
    color: {SKY_BLUE};
    letter-spacing: 0.5px;
  }}
  .p2-content {{
    padding: 20px 48px 16px 48px;
  }}
  .chart-section {{
    margin-bottom: 14px;
  }}
  .chart-section img {{
    width: 100%;
    display: block;
  }}
  .p2-two-col {{
    display: flex;
    gap: 24px;
    margin-bottom: 14px;
  }}
  .p2-col-chart {{
    flex: 0 0 45%;
  }}
  .p2-col-chart img {{
    width: 100%;
    display: block;
  }}
  .p2-col-table {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .stats-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9px;
  }}
  .stats-table th {{
    background: {PRIMARY_BLUE};
    color: #fff;
    font-weight: 700;
    padding: 6px 8px;
    text-align: center;
    font-size: 8px;
    letter-spacing: 0.3px;
  }}
  .stats-table th:first-child {{
    text-align: left;
  }}
  .stats-table td {{
    padding: 5px 8px;
    text-align: center;
    border-bottom: 1px solid {BORDER_GRAY};
    font-size: 9px;
  }}
  .stats-table td:first-child {{
    text-align: left;
    font-weight: 500;
    color: {TEXT_BLUE};
  }}
  .stats-table tr:last-child td {{
    border-bottom: 2px solid {PRIMARY_BLUE};
  }}
  .stats-table .highlight {{
    font-weight: 700;
    color: {PRIMARY_BLUE};
  }}
  .credibility-row {{
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 14px;
  }}
  .cred-item {{
    flex: 1;
    min-width: 140px;
    background: {LIGHT_GRAY};
    padding: 8px 12px;
    border-left: 3px solid {PRIMARY_BLUE};
    font-size: 9px;
    font-weight: 500;
    color: {TEXT_BLUE};
  }}
  .cta-box {{
    background: {DEEP_NAVY};
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    border-radius: 2px;
  }}
  .cta-box .cta-label {{
    font-size: 14px;
    font-weight: 700;
    color: #fff;
  }}
  .cta-box .cta-contact {{
    font-size: 10px;
    font-weight: 300;
    color: {SKY_BLUE};
  }}
  .cta-box .cta-contact a {{
    color: {AMBER};
    text-decoration: none;
  }}
  .cta-logo {{
    width: 160px;
    margin-left: 20px;
  }}
  .disclosures {{
    font-size: 6px;
    line-height: 1.45;
    color: #999;
    margin-top: 8px;
  }}
  .source-note {{
    font-size: 6.5px;
    line-height: 1.4;
    color: #888;
    margin-bottom: 6px;
  }}
</style>
</head>
<body>

<!-- ============================================================ -->
<!-- PAGE 1 — Strategy & Benefits                                  -->
<!-- ============================================================ -->
<div class="page">
  <div class="banner-strip">
    <img src="{banner_uri}" alt="">
  </div>

  <div class="p1-content">
    <img class="p1-logo" src="{logo_black_uri}" alt="ReSolve Asset Management">

    <div class="p1-headline">Put Your Lazy Money<br>to Work</div>
    <div class="p1-subtitle">Portable Alpha for the Mid-Market</div>
    <div class="p1-divider"></div>

    <!-- Portfolio Enhancement Diagram -->
    <div class="p1-diagram">
      <img src="{slide4_uri}" alt="Your Portfolio Enhanced — Example of 100% Investor Portfolio + 100% ReSolve Mandate">
    </div>

    <!-- Two-column: Return Stacking explanation + Why ReSolve -->
    <div class="p1-two-col">
      <div class="p1-col-left">
        <div class="section-heading">What is Return Stacking?</div>
        <p class="body-text">
          Return stacking is a capital-efficient investment approach that allows
          investors to maintain their existing portfolio while adding uncorrelated
          return streams on top. By using futures-based strategies funded with
          T-Bill collateral, investors can achieve more than 100% economic exposure
          without additional leverage on the underlying portfolio.
        </p>
      </div>
      <div class="p1-col-right">
        <div class="section-heading">Why ReSolve?</div>
        <ul class="bullet-list">
          <li>20+ years of quantitative research heritage</li>
          <li>Systematic carry, trend, and volatility strategies across 50+ global futures markets</li>
          <li>True portable alpha: uncorrelated to stocks and bonds</li>
          <li>Institutional infrastructure, mid-market accessibility</li>
          <li>Separately managed accounts with full transparency</li>
        </ul>
      </div>
    </div>

    <!-- Pull Quote -->
    <div class="pull-quote">
      <div class="quote-text">
        "ReSolve has delivered institutional-grade alpha that has genuinely
        enhanced our portfolio construction."
      </div>
      <div class="quote-attr">
        — Jonathan Glidden, Former CIO, Delta Air Lines
      </div>
    </div>
  </div>

  <div class="corner-deco">
    <img src="{corner_uri}" alt="">
  </div>
</div>

<!-- ============================================================ -->
<!-- PAGE 2 — Proof & Call to Action                               -->
<!-- ============================================================ -->
<div class="page">
  <div class="banner-strip">
    <img src="{banner_uri}" alt="">
  </div>

  <div class="p2-header">
    <div class="p2-header-title">Building Blocks for a<br>Robust Stacked Portfolio</div>
    <div class="p2-header-sub">Case Study on a Live ReSolve Carry Mandate</div>
  </div>

  <div class="p2-content">
    <!-- Annual Returns Chart -->
    <div class="chart-section">
      <img src="{annual_uri}" alt="Annual Returns — ReSolve Carry vs. Bonds vs. Global Equities">
    </div>

    <!-- Correlation Heatmap + Stats Table side by side -->
    <div class="p2-two-col">
      <div class="p2-col-chart">
        <img src="{corr_uri}" alt="Correlation Matrix">
      </div>
      <div class="p2-col-table">
        <table class="stats-table">
          <thead>
            <tr>
              <th>Statistics</th>
              <th>Balanced<br>Portfolio</th>
              <th>Carry<br>(Excess Returns)</th>
              <th class="highlight">100% Balanced<br>+ 100% Carry</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Annualized Return</td>
              <td>4.92%</td>
              <td>11.34%</td>
              <td class="highlight">17.90%</td>
            </tr>
            <tr>
              <td>Annualized Volatility</td>
              <td>11.14%</td>
              <td>22.08%</td>
              <td class="highlight">20.43%</td>
            </tr>
            <tr>
              <td>Max Drawdown</td>
              <td>-21.23%</td>
              <td>-23.98%</td>
              <td class="highlight">-14.71%</td>
            </tr>
            <tr>
              <td>Sharpe Ratio</td>
              <td>0.44</td>
              <td>0.51</td>
              <td class="highlight">0.88</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Institutional Credibility -->
    <div class="credibility-row">
      <div class="cred-item">$2B+ in AUM across strategies</div>
      <div class="cred-item">Sub-advised for major ETF platforms</div>
      <div class="cred-item">CFTC-registered CTA</div>
      <div class="cred-item">SEC-registered RIA</div>
    </div>

    <!-- CTA -->
    <div class="cta-box">
      <div>
        <div class="cta-label">Ready to put your lazy money to work?</div>
        <div class="cta-contact">
          info@investresolve.com &nbsp;|&nbsp;
          <a href="https://www.investresolve.com">www.investresolve.com</a>
        </div>
      </div>
      <img class="cta-logo" src="{logo_white_uri}" alt="ReSolve Asset Management">
    </div>

    <!-- Source -->
    <div class="source-note">
      Source: Tiingo. Analysis by ReSolve Asset Management SEZC (Cayman).
      ReSolve Carry is ReSolve Futures Yield (Carry) 20% Volatility Program (Excess Returns).
      Bonds is the iShares Core U.S. Aggregate Bond ETF (AGG).
      Global Equities is the iShares MSCI ACWI ETF (ACWI).
      Period is from September 1, 2021 through March 31, 2026.
      Indicated returns of one year or more are annualized.
      These results are a carveout of returns for the Program.
      All performance data is provided by the third party fund admin less a 0.85% annual fee.
    </div>

    <!-- Disclosures -->
    <div class="disclosures">
      PAST PERFORMANCE IS NOT A GUARANTEE OF FUTURE RESULTS. THE RISK OF LOSS IN
      TRADING COMMODITY INTERESTS IS SUBSTANTIAL. These materials do not constitute
      an offer or solicitation of an offer to make an investment in any of the funds
      or separately managed accounts ReSolve Global manages. ReSolve Global operates
      within a fund of funds and as excess returns (calculated prior to any yield on
      posted collateral). Confidential — Qualified Eligible Purchasers Only.
    </div>
  </div>

  <div class="corner-deco">
    <img src="{corner_uri}" alt="">
  </div>
</div>

</body>
</html>"""

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Written {OUTPUT.name} ({len(html):,} bytes)")
    print(f"Open in Chrome: {OUTPUT}")


if __name__ == "__main__":
    build()
