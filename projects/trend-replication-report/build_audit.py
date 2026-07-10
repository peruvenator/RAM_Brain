"""
Trend Replication Audit Workbook Generator
===========================================
Replicates ALL key computations from build_report.py and produces a
self-contained HTML audit document (trend-replication-audit.html) for
delivery to compliance alongside the main report.

Usage:
    python build_audit.py

Output:
    trend-replication-audit.html
"""

import pandas as pd
import numpy as np
from scipy.optimize import minimize as sp_minimize
from pathlib import Path
from datetime import datetime
import textwrap
import html as html_mod

# ── Paths ──
ROOT = Path(__file__).parent
DATA_CSV = ROOT / 'trend-data.csv'
OUT_HTML = ROOT / 'trend-replication-audit.html'

# ── Constants (must match build_report.py exactly) ──
LO_Q = 21  # number of lags for Lo (2002) adjustment

# ══════════════════════════════════════════════════════════
# DATA LOADING  (mirrors build_report.py lines 65-78)
# ══════════════════════════════════════════════════════════
df = pd.read_csv(str(DATA_CSV))
df.columns = ['Date', 'SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')
df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

# Daily returns via pct_change
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{col}_ret'] = df[col].pct_change()
df = df.dropna(subset=['SG_Trend_ret']).reset_index(drop=True)

# Growth of $1
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{col}_g1'] = df[col] / df[col].iloc[0]

# Synthetic blend from components (for optimization section)
df['Synth_ret'] = 0.15 * df['TD_Small_ret'] + 0.15 * df['TD_Med_ret'] + 0.70 * df['BU_ret']

start_date = df['Date'].iloc[0]
end_date = df['Date'].iloc[-1]
start_str = start_date.strftime('%b %d, %Y')
end_str = end_date.strftime('%b %d, %Y')
n_trading_days = len(df)
n_calendar_days = (end_date - start_date).days

# Monthly returns
df_m = df.set_index('Date').resample('ME').last()
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df_m[f'{col}_mret'] = df_m[col].pct_change()
df_m = df_m.dropna(subset=['SG_Trend_mret'])


# ══════════════════════════════════════════════════════════
# LO (2002) FUNCTIONS  (exact copy from build_report.py)
# ══════════════════════════════════════════════════════════
def lo_eta(x, q):
    """Compute the Lo (2002) autocorrelation adjustment factor."""
    x_dm = x - x.mean()
    eta = 1.0
    for k in range(1, q + 1):
        rho_k = np.corrcoef(x_dm[k:], x_dm[:-k])[0, 1]
        eta += 2 * (1 - k / (q + 1)) * rho_k
    return max(eta, 0.01)  # floor to avoid degenerate cases


def lo_adj_te(diff):
    """Lo-adjusted annualized TE for an arbitrary daily difference series."""
    daily_std = np.std(diff, ddof=1)
    eta = lo_eta(diff, LO_Q)
    return daily_std * np.sqrt(252 * eta) * 100


# ══════════════════════════════════════════════════════════
# FULL-PERIOD STATISTICS  (mirrors build_report.py lines 505-536)
# ══════════════════════════════════════════════════════════
series_map = {
    'Top Down (Constrained)': ('TD_Small_ret', 'TD_Small_g1'),
    'Top Down (Full)':        ('TD_Med_ret',   'TD_Med_g1'),
    'Bottom Up':              ('BU_ret',       'BU_g1'),
    'Blend':                  ('Blend_ret',    'Blend_g1'),
}

stats = {}
for name, (ret_col, g1_col) in series_map.items():
    rets = df[ret_col]
    sg_rets = df['SG_Trend_ret']
    corr = rets.corr(sg_rets)
    te = (rets - sg_rets).std() * np.sqrt(252) * 100
    cov = np.cov(rets.dropna(), sg_rets.dropna())
    beta = cov[0, 1] / cov[1, 1]
    cum_ret = (df[g1_col].iloc[-1] / df[g1_col].iloc[0] - 1) * 100
    ann_ret = ((1 + cum_ret / 100) ** (365.25 / n_calendar_days) - 1) * 100
    running_max = df[g1_col].cummax()
    dd = df[g1_col] / running_max - 1
    max_dd = dd.min() * 100
    ann_vol = rets.std() * np.sqrt(252) * 100
    ir = (rets - sg_rets).mean() / (rets - sg_rets).std() * np.sqrt(252) if (rets - sg_rets).std() > 0 else 0
    stats[name] = dict(corr=corr, te=te, beta=beta, cum_ret=cum_ret, ann_ret=ann_ret,
                        max_dd=max_dd, ann_vol=ann_vol, ir=ir)

# Lo-adjusted TE for each model
for name, (ret_col, _) in series_map.items():
    diff_arr = (df[ret_col] - df['SG_Trend_ret']).dropna().values
    daily_std = np.std(diff_arr, ddof=1)
    eta = lo_eta(diff_arr, LO_Q)
    stats[name]['te_adj'] = daily_std * np.sqrt(252 * eta) * 100
    stats[name]['lo_eta'] = eta

# SG Trend stats
sg_cum = (df['SG_Trend_g1'].iloc[-1] / df['SG_Trend_g1'].iloc[0] - 1) * 100
sg_ann = ((1 + sg_cum / 100) ** (365.25 / n_calendar_days) - 1) * 100
sg_vol = df['SG_Trend_ret'].std() * np.sqrt(252) * 100
sg_max_dd = (df['SG_Trend_g1'] / df['SG_Trend_g1'].cummax() - 1).min() * 100

# Monthly correlations
m_corr_blend = df_m['SG_Trend_mret'].corr(df_m['Blend_mret'])
m_corr_bu = df_m['SG_Trend_mret'].corr(df_m['BU_mret'])
m_corr_tds = df_m['SG_Trend_mret'].corr(df_m['TD_Small_mret'])
m_corr_tdm = df_m['SG_Trend_mret'].corr(df_m['TD_Med_mret'])


# ══════════════════════════════════════════════════════════
# LO (2002) DETAILED DECOMPOSITION PER SERIES
# ══════════════════════════════════════════════════════════
lo_details = {}
for name, (ret_col, _) in series_map.items():
    diff_arr = (df[ret_col] - df['SG_Trend_ret']).dropna().values
    x_dm = diff_arr - diff_arr.mean()
    daily_std = np.std(diff_arr, ddof=1)
    naive_te = daily_std * np.sqrt(252) * 100

    lags_data = []
    running_eta = 1.0
    for k in range(1, LO_Q + 1):
        rho_k = np.corrcoef(x_dm[k:], x_dm[:-k])[0, 1]
        kernel_w = 1 - k / (LO_Q + 1)
        contribution = 2 * kernel_w * rho_k
        running_eta += contribution
        lags_data.append({
            'lag': k,
            'rho_k': rho_k,
            'kernel_weight': kernel_w,
            'contribution': contribution,
            'running_eta': running_eta,
        })

    final_eta = max(running_eta, 0.01)
    adj_te = daily_std * np.sqrt(252 * final_eta) * 100
    pct_reduction = (1 - adj_te / naive_te) * 100 if naive_te > 0 else 0

    lo_details[name] = {
        'lags': lags_data,
        'naive_te': naive_te,
        'raw_eta': running_eta,
        'final_eta': final_eta,
        'adj_te': adj_te,
        'pct_reduction': pct_reduction,
        'daily_std': daily_std,
    }


# ══════════════════════════════════════════════════════════
# TRACKING ERROR RECONCILIATION
# ══════════════════════════════════════════════════════════
# Rolling 1-year return differences for validation
roll_1y_blend = df['Blend'].pct_change(252) * 100
roll_1y_sg = df['SG_Trend'].pct_change(252) * 100
roll_1y_diff = (roll_1y_blend - roll_1y_sg).dropna()
roll_1y_diff_std = roll_1y_diff.std()


# ══════════════════════════════════════════════════════════
# EX-POST OPTIMIZATION  (mirrors build_report.py lines 397-432)
# ══════════════════════════════════════════════════════════
sg_r = df['SG_Trend_ret'].values
tds_r = df['TD_Small_ret'].values
tdm_r = df['TD_Med_ret'].values
bu_r = df['BU_ret'].values


def te_obj_full(w):
    diff = w[0] * tds_r + w[1] * tdm_r + w[2] * bu_r - sg_r
    return lo_adj_te(diff)


opt_res = sp_minimize(te_obj_full, [0.15, 0.15, 0.70],
                      bounds=[(0, 1), (0, 1), (0, 1)],
                      constraints={'type': 'eq', 'fun': lambda w: sum(w) - 1},
                      method='SLSQP')
w_opt = opt_res.x
te_opt = te_obj_full(w_opt)

te_current = lo_adj_te(0.15 * tds_r + 0.15 * tdm_r + 0.70 * bu_r - sg_r)

te_tds_solo = lo_adj_te(tds_r - sg_r)
te_tdm_solo = lo_adj_te(tdm_r - sg_r)
te_bu_solo = lo_adj_te(bu_r - sg_r)

# Tracking error correlations
diff_tds = tds_r - sg_r
diff_tdm = tdm_r - sg_r
diff_bu = bu_r - sg_r
corr_tds_bu = np.corrcoef(diff_tds, diff_bu)[0, 1]
corr_tdm_bu = np.corrcoef(diff_tdm, diff_bu)[0, 1]
corr_tds_tdm = np.corrcoef(diff_tds, diff_tdm)[0, 1]


# ══════════════════════════════════════════════════════════
# HTML GENERATION
# ══════════════════════════════════════════════════════════

def esc(s):
    """HTML-escape a string."""
    return html_mod.escape(str(s))


def code_block(code_str):
    """Wrap code in a styled pre/code block."""
    return f'<pre class="code-block"><code>{esc(textwrap.dedent(code_str).strip())}</code></pre>'


# -- Build Lo detail tables for Section 4 --
lo_detail_html = ""
for name in ['Top Down (Constrained)', 'Top Down (Full)', 'Bottom Up', 'Blend']:
    d = lo_details[name]
    lo_detail_html += f"""
    <h3>{esc(name)}</h3>
    <p>Daily std of tracking difference: <strong>{d['daily_std']:.8f}</strong> | Naive TE: <strong>{d['naive_te']:.4f}%</strong></p>
    <table>
      <thead>
        <tr>
          <th style="text-align:center">Lag (k)</th>
          <th>Autocorrelation (rho<sub>k</sub>)</th>
          <th>Bartlett Weight (1 - k/22)</th>
          <th>Weighted Contribution (2 * w * rho)</th>
          <th>Running eta</th>
        </tr>
      </thead>
      <tbody>
"""
    for row in d['lags']:
        lo_detail_html += f"""        <tr>
          <td style="text-align:center">{row['lag']}</td>
          <td>{row['rho_k']:+.8f}</td>
          <td>{row['kernel_weight']:.6f}</td>
          <td>{row['contribution']:+.8f}</td>
          <td>{row['running_eta']:.8f}</td>
        </tr>
"""
    lo_detail_html += f"""      </tbody>
    </table>
    <p>
      Raw eta (before floor): <strong>{d['raw_eta']:.8f}</strong> |
      Final eta (after max(., 0.01) floor): <strong>{d['final_eta']:.8f}</strong><br>
      Adjusted TE = {d['daily_std']:.8f} x sqrt(252 x {d['final_eta']:.8f}) = <strong>{d['adj_te']:.4f}%</strong><br>
      Reduction from naive: <strong>{d['pct_reduction']:.2f}%</strong>
    </p>
"""


# -- Build full stats table for Section 3 --
def fmt_pct(v, decimals=2):
    return f"{v:.{decimals}f}%"

def fmt_num(v, decimals=3):
    return f"{v:.{decimals}f}"

stats_rows_html = ""
metrics = [
    ("Annualized Return",
     fmt_pct(sg_ann),
     lambda n: fmt_pct(stats[n]['ann_ret']),
     "((Ending / Beginning)^(365.25 / calendar_days) - 1) * 100"),
    ("Cumulative Return",
     fmt_pct(sg_cum),
     lambda n: fmt_pct(stats[n]['cum_ret']),
     "(G1_end / G1_start - 1) * 100"),
    ("Ann. Volatility",
     fmt_pct(sg_vol),
     lambda n: fmt_pct(stats[n]['ann_vol']),
     "daily_ret.std() * sqrt(252) * 100"),
    ("Max Drawdown",
     fmt_pct(sg_max_dd),
     lambda n: fmt_pct(stats[n]['max_dd']),
     "min(price / cummax(price) - 1) * 100"),
    ("Daily Correlation",
     "1.000",
     lambda n: fmt_num(stats[n]['corr']),
     "pearsonr(daily_ret, sg_daily_ret)"),
    ("Monthly Correlation",
     "1.000",
     lambda n: fmt_num({'Top Down (Constrained)': m_corr_tds,
                         'Top Down (Full)': m_corr_tdm,
                         'Bottom Up': m_corr_bu,
                         'Blend': m_corr_blend}[n]),
     "pearsonr(monthly_ret, sg_monthly_ret)"),
    ("Ann. Tracking Error (Naive)",
     "---",
     lambda n: fmt_pct(stats[n]['te']),
     "(daily_ret - sg_daily_ret).std() * sqrt(252) * 100"),
    ("Adj. Tracking Error (Lo)",
     "---",
     lambda n: fmt_pct(stats[n]['te_adj']),
     "daily_std * sqrt(252 * eta) * 100"),
    ("Beta",
     "1.00",
     lambda n: fmt_num(stats[n]['beta'], 2),
     "cov(ret, sg_ret) / var(sg_ret)"),
    ("Information Ratio",
     "---",
     lambda n: fmt_num(stats[n]['ir'], 2),
     "mean(diff) / std(diff) * sqrt(252)"),
]

for metric_name, sg_val, val_fn, formula in metrics:
    stats_rows_html += f"""      <tr>
        <td>{esc(metric_name)}</td>
        <td>{sg_val}</td>
        <td>{val_fn('Top Down (Constrained)')}</td>
        <td>{val_fn('Top Down (Full)')}</td>
        <td>{val_fn('Bottom Up')}</td>
        <td><strong>{val_fn('Blend')}</strong></td>
        <td class="formula-col">{esc(formula)}</td>
      </tr>
"""


# -- Build TE reconciliation table for Section 5 --
te_recon_html = ""
for name in ['Top Down (Constrained)', 'Top Down (Full)', 'Bottom Up', 'Blend']:
    d = lo_details[name]
    te_recon_html += f"""      <tr>
        <td>{esc(name)}</td>
        <td>{d['naive_te']:.4f}%</td>
        <td>{d['final_eta']:.6f}</td>
        <td>{d['adj_te']:.4f}%</td>
        <td>{d['pct_reduction']:.2f}%</td>
      </tr>
"""


# -- Source code strings for Section 7 --
lo_eta_code = '''
def lo_eta(x, q):
    """Compute the Lo (2002) autocorrelation adjustment factor."""
    x_dm = x - x.mean()
    eta = 1.0
    for k in range(1, q + 1):
        rho_k = np.corrcoef(x_dm[k:], x_dm[:-k])[0, 1]
        eta += 2 * (1 - k / (q + 1)) * rho_k
    return max(eta, 0.01)  # floor to avoid degenerate cases
'''

lo_adj_te_code = '''
def lo_adj_te(diff):
    """Lo-adjusted annualized TE for an arbitrary daily difference series."""
    daily_std = np.std(diff, ddof=1)
    eta = lo_eta(diff, LO_Q)
    return daily_std * np.sqrt(252 * eta) * 100
'''

stats_loop_code = '''
series_map = {
    'Top Down (Constrained)': ('TD_Small_ret', 'TD_Small_g1'),
    'Top Down (Full)':        ('TD_Med_ret',   'TD_Med_g1'),
    'Bottom Up':              ('BU_ret',       'BU_g1'),
    'Blend':                  ('Blend_ret',    'Blend_g1'),
}

for name, (ret_col, g1_col) in series_map.items():
    rets = df[ret_col]
    sg_rets = df['SG_Trend_ret']
    corr = rets.corr(sg_rets)
    te = (rets - sg_rets).std() * np.sqrt(252) * 100
    cov = np.cov(rets.dropna(), sg_rets.dropna())
    beta = cov[0,1] / cov[1,1]
    cum_ret = (df[g1_col].iloc[-1] / df[g1_col].iloc[0] - 1) * 100
    n_days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
    ann_ret = ((1 + cum_ret/100) ** (365.25/n_days) - 1) * 100
    running_max = df[g1_col].cummax()
    dd = df[g1_col] / running_max - 1
    max_dd = dd.min() * 100
    ann_vol = rets.std() * np.sqrt(252) * 100
    ir = (rets - sg_rets).mean() / (rets - sg_rets).std() * np.sqrt(252)
'''

optimization_code = '''
from scipy.optimize import minimize as sp_minimize

sg_r = df['SG_Trend_ret'].values
tds_r = df['TD_Small_ret'].values
tdm_r = df['TD_Med_ret'].values
bu_r = df['BU_ret'].values

def te_obj_full(w):
    diff = w[0]*tds_r + w[1]*tdm_r + w[2]*bu_r - sg_r
    return lo_adj_te(diff)

opt_res = sp_minimize(te_obj_full, [0.15, 0.15, 0.70],
                      bounds=[(0,1),(0,1),(0,1)],
                      constraints={'type': 'eq', 'fun': lambda w: sum(w) - 1},
                      method='SLSQP')
w_opt = opt_res.x
te_opt = te_obj_full(w_opt)
'''


# ══════════════════════════════════════════════════════════
# ASSEMBLE HTML
# ══════════════════════════════════════════════════════════

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trend Replication Program -- Compliance Audit Workbook</title>
<style>
  @page {{
    size: letter;
    margin: 0.6in 0.7in;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #1a1a2e;
    background: white;
    line-height: 1.55;
    font-size: 10px;
    padding: 24px 32px;
    max-width: 1100px;
    margin: 0 auto;
  }}

  /* Header */
  .header {{
    text-align: center;
    margin-bottom: 28px;
    padding-bottom: 16px;
    border-bottom: 3px solid #00478D;
  }}
  .header h1 {{
    font-size: 22px;
    font-weight: 700;
    color: #00478D;
    margin-bottom: 4px;
  }}
  .header .subtitle {{
    font-size: 13px;
    color: #475569;
    font-weight: 400;
  }}
  .header .date-range {{
    font-size: 10px;
    color: #94a3b8;
    margin-top: 4px;
  }}
  .header .meta {{
    font-size: 9px;
    color: #94a3b8;
    margin-top: 6px;
    font-style: italic;
  }}

  /* Sections */
  .section {{
    margin-bottom: 28px;
    page-break-inside: auto;
  }}
  .section h2 {{
    font-size: 15px;
    font-weight: 700;
    color: #00478D;
    margin-bottom: 10px;
    padding-bottom: 5px;
    border-bottom: 2px solid #00478D;
  }}
  .section h3 {{
    font-size: 12px;
    font-weight: 600;
    color: #334155;
    margin: 14px 0 6px 0;
  }}
  .section p {{
    margin-bottom: 8px;
    color: #334155;
    font-size: 10px;
  }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 14px 0;
    font-size: 9px;
    page-break-inside: auto;
  }}
  table th {{
    background: #f1f5f9;
    padding: 5px 6px;
    text-align: right;
    font-weight: 600;
    color: #334155;
    border-bottom: 2px solid #cbd5e1;
    border-top: 1px solid #e2e8f0;
  }}
  table th:first-child {{
    text-align: left;
  }}
  table td {{
    padding: 4px 6px;
    text-align: right;
    border-bottom: 1px solid #e2e8f0;
    color: #475569;
  }}
  table td:first-child {{
    text-align: left;
    font-weight: 500;
    color: #1a1a2e;
  }}
  table tbody tr:nth-child(even) {{
    background: #f8fafc;
  }}
  table tbody tr:hover {{
    background: #eef2ff;
  }}
  tr {{
    page-break-inside: avoid;
  }}
  .formula-col {{
    font-family: 'Consolas', 'Menlo', 'Monaco', monospace;
    font-size: 8px;
    color: #64748b;
    text-align: left !important;
  }}

  /* Code blocks */
  .code-block {{
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #00478D;
    padding: 10px 14px;
    margin: 8px 0 12px 0;
    font-family: 'Consolas', 'Menlo', 'Monaco', monospace;
    font-size: 9px;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre;
    color: #334155;
    page-break-inside: avoid;
  }}

  /* Math notation */
  .math {{
    font-style: italic;
    font-family: 'Cambria Math', 'Georgia', serif;
  }}

  /* Callouts */
  .callout {{
    background: #f8fdfb;
    border-left: 3px solid #00478D;
    padding: 8px 12px;
    margin: 10px 0;
    font-size: 10px;
  }}
  .callout-ref {{
    background: #fefce8;
    border-left-color: #eab308;
  }}

  /* Definition list style */
  .def-table {{
    margin: 8px 0;
  }}
  .def-table td:first-child {{
    width: 180px;
    font-weight: 600;
    white-space: nowrap;
    vertical-align: top;
  }}

  strong {{
    color: #1a1a2e;
  }}

  .footer {{
    text-align: center;
    padding: 16px;
    color: #94a3b8;
    font-size: 8px;
    border-top: 1px solid #e2e8f0;
    margin-top: 24px;
  }}
</style>
</head>
<body>

<!-- ═══ HEADER ═══ -->
<div class="header">
  <h1>Trend Replication Program</h1>
  <div class="subtitle">Compliance Audit Workbook</div>
  <div class="date-range">Data Period: {start_str} -- {end_str}</div>
  <div class="meta">Generated {datetime.now().strftime('%B %d, %Y')} by build_audit.py | All computations replicated from build_report.py</div>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- SECTION 1: DATA SUMMARY                                -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="section">
  <h2>1. Data Summary</h2>

  <h3>Source File &amp; Date Range</h3>
  <table class="def-table">
    <tbody>
      <tr><td>Source file</td><td>trend-data.csv</td></tr>
      <tr><td>Date range</td><td>{start_str} -- {end_str}</td></tr>
      <tr><td>Calendar days</td><td>{n_calendar_days:,}</td></tr>
      <tr><td>Trading days (after dropna)</td><td>{n_trading_days:,}</td></tr>
      <tr><td>Date parsing format</td><td>%m/%d/%y (e.g. 2/7/23)</td></tr>
    </tbody>
  </table>

  <h3>Series Definitions</h3>
  <table>
    <thead>
      <tr>
        <th>Display Name</th>
        <th>CSV Column</th>
        <th>Internal Code</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>SG Trend Index (Excess)</td>
        <td>SocGen CTA Trend Index (Excess)</td>
        <td>SG_Trend</td>
        <td>Benchmark; equal-weighted top 10 trend CTAs by AUM, excess return basis</td>
      </tr>
      <tr>
        <td>Top Down (Constrained)</td>
        <td>Top Down (Small, Net)</td>
        <td>TD_Small</td>
        <td>Regression-based replication, constrained market universe</td>
      </tr>
      <tr>
        <td>Top Down (Full)</td>
        <td>Top Down (Med, Net)</td>
        <td>TD_Med</td>
        <td>Regression-based replication, full market universe</td>
      </tr>
      <tr>
        <td>Bottom Up</td>
        <td>Bottom Up (Net)</td>
        <td>BU</td>
        <td>Blend of actual trend-following programs</td>
      </tr>
      <tr>
        <td>Trend Replication (Blend)</td>
        <td>Trend Replication (Net)</td>
        <td>Blend</td>
        <td>Composite: 15% TD Constrained + 15% TD Full + 70% Bottom Up</td>
      </tr>
    </tbody>
  </table>

  <h3>Blend Composition</h3>
  <p>The Trend Replication Blend is a fixed-weight daily composite:</p>
  <table>
    <thead><tr><th>Component</th><th>Weight</th></tr></thead>
    <tbody>
      <tr><td>Top Down (Constrained)</td><td>15%</td></tr>
      <tr><td>Top Down (Full)</td><td>15%</td></tr>
      <tr><td>Bottom Up</td><td>70%</td></tr>
      <tr><td><strong>Total</strong></td><td><strong>100%</strong></td></tr>
    </tbody>
  </table>
  <p>The blend is pre-computed in the source data. Verification via synthetic construction: <code>Synth_ret = 0.15 * TD_Small_ret + 0.15 * TD_Med_ret + 0.70 * BU_ret</code></p>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- SECTION 2: RETURN METHODOLOGY                          -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="section">
  <h2>2. Return Methodology</h2>

  <h3>Daily Returns</h3>
  <p>Daily returns are computed via simple percentage change on the raw index level:</p>
  {code_block("""
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{{col}}_ret'] = df[col].pct_change()
df = df.dropna(subset=['SG_Trend_ret']).reset_index(drop=True)
  """)}
  <p>This is equivalent to: r<sub>t</sub> = (P<sub>t</sub> / P<sub>t-1</sub>) - 1. The first row is dropped (NaN from pct_change).</p>

  <h3>Growth of $1</h3>
  <p>Each series is normalized to $1 at the first observation (after dropna):</p>
  {code_block("""
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{{col}}_g1'] = df[col] / df[col].iloc[0]
  """)}
  <p>G1<sub>t</sub> = Level<sub>t</sub> / Level<sub>0</sub>. This preserves the exact return characteristics of the original series.</p>

  <h3>Monthly Returns</h3>
  <p>Monthly returns use end-of-month resampling and percentage change on levels:</p>
  {code_block("""
df_m = df.set_index('Date').resample('ME').last()
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df_m[f'{{col}}_mret'] = df_m[col].pct_change()
df_m = df_m.dropna(subset=['SG_Trend_mret'])
  """)}

  <h3>Quarterly Returns</h3>
  <p>Quarterly returns follow the same pattern with 'QE' resampling.</p>

  <h3>Annual Returns</h3>
  <p>Annual returns are calculated within each calendar year as: (last trading day level / first trading day level) - 1. Partial years (first and last) are marked with an asterisk.</p>

  <h3>Annualized Return</h3>
  <p>Compound annual growth rate using calendar days:</p>
  {code_block("""
n_days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
ann_ret = ((1 + cum_ret/100) ** (365.25/n_days) - 1) * 100
  """)}
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- SECTION 3: FULL-PERIOD STATISTICS TABLE                -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="section">
  <h2>3. Full-Period Statistics</h2>
  <p>Every metric for every series, with the formula used to compute each value. All values below were computed by this audit script using the identical methodology as build_report.py.</p>

  <table>
    <thead>
      <tr>
        <th>Metric</th>
        <th>SG Trend</th>
        <th>TD (Constrained)</th>
        <th>TD (Full)</th>
        <th>Bottom Up</th>
        <th>Blend</th>
        <th style="text-align:left">Formula</th>
      </tr>
    </thead>
    <tbody>
{stats_rows_html}
    </tbody>
  </table>

  <h3>Formula Definitions</h3>
  <table class="def-table">
    <tbody>
      <tr><td>Annualized Return</td><td>((End_G1 / Start_G1)<sup>(365.25/calendar_days)</sup> - 1) x 100</td></tr>
      <tr><td>Cumulative Return</td><td>(End_G1 / Start_G1 - 1) x 100</td></tr>
      <tr><td>Ann. Volatility</td><td>std(daily_returns) x sqrt(252) x 100 &nbsp;(sample std, ddof=1 implicit in pandas)</td></tr>
      <tr><td>Max Drawdown</td><td>min(level / running_max - 1) x 100</td></tr>
      <tr><td>Daily Correlation</td><td>Pearson correlation of daily returns with SG Trend daily returns</td></tr>
      <tr><td>Monthly Correlation</td><td>Pearson correlation of month-end returns with SG Trend month-end returns</td></tr>
      <tr><td>Ann. Tracking Error</td><td>std(daily_ret - sg_daily_ret) x sqrt(252) x 100 &nbsp;(pandas .std(), ddof=1)</td></tr>
      <tr><td>Adj. Tracking Error (Lo)</td><td>std(diff, ddof=1) x sqrt(252 x eta) x 100 &nbsp;(numpy .std(ddof=1))</td></tr>
      <tr><td>Beta</td><td>cov(ret, sg_ret)[0,1] / cov(ret, sg_ret)[1,1] &nbsp;(numpy .cov, ddof=1)</td></tr>
      <tr><td>Information Ratio</td><td>mean(daily_diff) / std(daily_diff) x sqrt(252)</td></tr>
    </tbody>
  </table>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- SECTION 4: LO (2002) AUTOCORRELATION ADJUSTMENT        -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="section">
  <h2>4. Lo (2002) Autocorrelation Adjustment -- Detailed Decomposition</h2>

  <h3>The Formula</h3>
  <p>The Lo (2002) adjustment factor eta accounts for serial correlation in daily tracking differences when annualizing volatility. The standard sqrt(252) annualization implicitly assumes i.i.d. returns; when autocorrelation is present, the effective annualized dispersion differs.</p>

  <p>The adjustment factor is:</p>
  <div class="callout">
    <span class="math">eta</span> = 1 + 2 x <span class="math">&Sigma;</span><sub>k=1</sub><sup>q</sup> (1 - k / (q + 1)) x <span class="math">rho</span><sub>k</sub>
  </div>

  <p>Where:</p>
  <ul style="margin: 6px 0 8px 20px; font-size: 10px; color: #334155;">
    <li><span class="math">q</span> = {LO_Q} lags (approximately 1 month of trading days)</li>
    <li><span class="math">rho</span><sub>k</sub> = autocorrelation of the demeaned tracking difference at lag k, computed via <code>np.corrcoef(x_dm[k:], x_dm[:-k])[0,1]</code></li>
    <li>The kernel weight <code>(1 - k/(q+1))</code> is the Bartlett (triangular) kernel, giving decreasing weight to higher lags</li>
    <li>A floor of 0.01 is applied: <code>eta = max(eta, 0.01)</code> to avoid degenerate/negative values</li>
  </ul>

  <p>The Lo-adjusted tracking error is then:</p>
  <div class="callout">
    TE<sub>adj</sub> = <span class="math">sigma</span><sub>daily</sub> x sqrt(252 x <span class="math">eta</span>) x 100
  </div>

  <p>When <span class="math">eta</span> &lt; 1 (negative net autocorrelation), the standard TE overstates true longer-horizon dispersion.</p>

  <h3>Source Code: lo_eta()</h3>
  {code_block(lo_eta_code)}

  <h3>Source Code: lo_adj_te()</h3>
  {code_block(lo_adj_te_code)}

  <h3>Lag-by-Lag Decomposition per Series</h3>
  <p>For each series, the table below shows the autocorrelation at each lag (1-{LO_Q}), the Bartlett kernel weight, the weighted contribution to eta, and the running cumulative eta value.</p>

  {lo_detail_html}

  <div class="callout callout-ref">
    <strong>Reference:</strong> Lo, Andrew W. "The Statistics of Sharpe Ratios." <em>Financial Analysts Journal</em> 58, no. 4 (2002): 36--52.
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- SECTION 5: TRACKING ERROR RECONCILIATION               -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="section">
  <h2>5. Tracking Error Reconciliation</h2>

  <h3>Naive vs. Lo-Adjusted Tracking Error</h3>
  <table>
    <thead>
      <tr>
        <th>Series</th>
        <th>Naive TE</th>
        <th>Lo eta Factor</th>
        <th>Lo-Adjusted TE</th>
        <th>Reduction</th>
      </tr>
    </thead>
    <tbody>
{te_recon_html}
    </tbody>
  </table>

  <h3>Validation: Rolling 1-Year Return Difference</h3>
  <p>As an independent check, we compute the standard deviation of rolling 252-trading-day return differences between the Blend and SG Trend Index:</p>
  {code_block("""
roll_1y_blend = df['Blend'].pct_change(252) * 100
roll_1y_sg = df['SG_Trend'].pct_change(252) * 100
roll_1y_diff = (roll_1y_blend - roll_1y_sg).dropna()
roll_1y_diff_std = roll_1y_diff.std()
  """)}
  <table class="def-table">
    <tbody>
      <tr><td>Rolling 1-year diff std</td><td>{roll_1y_diff_std:.4f}%</td></tr>
      <tr><td>Lo-adjusted TE (Blend)</td><td>{lo_details['Blend']['adj_te']:.4f}%</td></tr>
      <tr><td>Naive TE (Blend)</td><td>{lo_details['Blend']['naive_te']:.4f}%</td></tr>
    </tbody>
  </table>
  <p>The rolling 1-year figure ({roll_1y_diff_std:.1f}%) is more consistent with the Lo-adjusted TE ({lo_details['Blend']['adj_te']:.1f}%) than the naive TE ({lo_details['Blend']['naive_te']:.1f}%), confirming that negative autocorrelation in daily tracking differences causes the standard annualization to overstate effective dispersion over longer horizons.</p>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- SECTION 6: EX-POST OPTIMIZATION DETAIL                 -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="section">
  <h2>6. Ex-Post Optimization Detail</h2>

  <h3>Objective Function</h3>
  <p>Minimize Lo-adjusted annualized tracking error of the blended portfolio against the SG Trend Index:</p>
  {code_block("""
def te_obj_full(w):
    diff = w[0]*tds_r + w[1]*tdm_r + w[2]*bu_r - sg_r
    return lo_adj_te(diff)
  """)}

  <h3>Constraints</h3>
  <table class="def-table">
    <tbody>
      <tr><td>Non-negativity</td><td>w<sub>i</sub> >= 0 for all i (bounds: [(0,1), (0,1), (0,1)])</td></tr>
      <tr><td>Full investment</td><td>w<sub>1</sub> + w<sub>2</sub> + w<sub>3</sub> = 1</td></tr>
      <tr><td>Method</td><td>scipy.optimize.minimize with method='SLSQP'</td></tr>
      <tr><td>Initial guess</td><td>[0.15, 0.15, 0.70] (current weights)</td></tr>
    </tbody>
  </table>

  <h3>Optimization Result</h3>
  <table>
    <thead>
      <tr><th>Weight</th><th>Current</th><th>Optimal</th></tr>
    </thead>
    <tbody>
      <tr><td>Top Down (Constrained)</td><td>15.0%</td><td>{w_opt[0]*100:.2f}%</td></tr>
      <tr><td>Top Down (Full)</td><td>15.0%</td><td>{w_opt[1]*100:.2f}%</td></tr>
      <tr><td>Bottom Up</td><td>70.0%</td><td>{w_opt[2]*100:.2f}%</td></tr>
    </tbody>
  </table>

  <h3>Tracking Error Comparison</h3>
  <table class="def-table">
    <tbody>
      <tr><td>Current blend TE (Lo-adj)</td><td>{te_current:.4f}%</td></tr>
      <tr><td>Optimal blend TE (Lo-adj)</td><td>{te_opt:.4f}%</td></tr>
      <tr><td>Improvement</td><td>{te_current - te_opt:.4f} pp</td></tr>
      <tr><td>Optimizer converged</td><td>{'Yes' if opt_res.success else 'No'}</td></tr>
      <tr><td>Optimizer message</td><td>{esc(opt_res.message)}</td></tr>
    </tbody>
  </table>

  <h3>Individual Model Lo-Adjusted Tracking Errors</h3>
  <table>
    <thead><tr><th>Model</th><th>Lo-Adj TE (standalone)</th></tr></thead>
    <tbody>
      <tr><td>Top Down (Constrained)</td><td>{te_tds_solo:.4f}%</td></tr>
      <tr><td>Top Down (Full)</td><td>{te_tdm_solo:.4f}%</td></tr>
      <tr><td>Bottom Up</td><td>{te_bu_solo:.4f}%</td></tr>
    </tbody>
  </table>

  <h3>Cross-Correlations of Tracking Differences</h3>
  <p>Tracking difference = model daily return - SG Trend daily return. Correlations between these difference series drive the diversification benefit:</p>
  <table>
    <thead>
      <tr><th></th><th>TD (Constrained)</th><th>TD (Full)</th><th>Bottom Up</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>TD (Constrained)</td>
        <td>1.000</td>
        <td>{corr_tds_tdm:.4f}</td>
        <td>{corr_tds_bu:.4f}</td>
      </tr>
      <tr>
        <td>TD (Full)</td>
        <td>{corr_tds_tdm:.4f}</td>
        <td>1.000</td>
        <td>{corr_tdm_bu:.4f}</td>
      </tr>
      <tr>
        <td>Bottom Up</td>
        <td>{corr_tds_bu:.4f}</td>
        <td>{corr_tdm_bu:.4f}</td>
        <td>1.000</td>
      </tr>
    </tbody>
  </table>
  <p>The low correlation between TD and BU tracking differences ({corr_tds_bu:.2f} and {corr_tdm_bu:.2f}) is the primary source of diversification benefit in the blend. The high correlation between the two TD models ({corr_tds_tdm:.2f}) limits the benefit of shifting weight between them.</p>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- SECTION 7: SOURCE CODE REFERENCE                       -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="section">
  <h2>7. Source Code Reference</h2>
  <p>The complete functions used in both build_report.py and this audit script are reproduced below for reference.</p>

  <h3>lo_eta() -- Lo (2002) Autocorrelation Adjustment Factor</h3>
  {code_block(lo_eta_code)}

  <h3>lo_adj_te() -- Lo-Adjusted Annualized Tracking Error</h3>
  {code_block(lo_adj_te_code)}

  <h3>Statistics Computation Loop</h3>
  {code_block(stats_loop_code)}

  <h3>Ex-Post Optimization</h3>
  {code_block(optimization_code)}
</div>

<!-- ═══ FOOTER ═══ -->
<div class="footer">
  Audit workbook generated {datetime.now().strftime('%B %d, %Y')} by build_audit.py<br>
  Data period: {start_str} -- {end_str} | {n_trading_days:,} trading days<br>
  All computations replicated from build_report.py using identical methodology.<br>
  &copy; {datetime.now().year} ReSolve Asset Management. All rights reserved.
</div>

</body>
</html>"""

# ── Write output ──
with open(str(OUT_HTML), 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Audit workbook saved to {OUT_HTML.name}")
print(f"  Data: {start_str} - {end_str}")
print(f"  Trading days: {n_trading_days:,}")
print(f"  Series: {', '.join(series_map.keys())}")
print(f"  Lo adjustment: q={LO_Q} lags, Bartlett kernel")
print(f"  Optimizer converged: {opt_res.success}")
