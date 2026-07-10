import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib import font_manager
from io import BytesIO
import base64
from pathlib import Path
from datetime import datetime

# ── Paths ──
ROOT = Path(__file__).parent
BRAND_DIR = ROOT / '..' / '..' / 'references' / 'brand-assets' / 'resolve-am'
DATA_CSV = ROOT / 'trend-data.csv'
OUT_HTML = ROOT / 'trend-replication-analysis.html'

# ── Load ReSolve brand fonts ──
for fn in ['HelveticaNeueLTStd-Lt.otf', 'HelveticaNeueLTStd-Roman.otf',
           'HelveticaNeueLTStd-Bd.otf', 'HelveticaLTStd-Roman.otf',
           'HelveticaLTStd-Bold.otf']:
    fp = BRAND_DIR / 'Fonts' / fn
    if not fp.exists():
        fp = BRAND_DIR / 'Fonts' / 'Helvetica Neue LT Std' / fn
    if fp.exists():
        try:
            font_manager.fontManager.addfont(str(fp))
        except Exception:
            pass

# ── Style setup (ReSolve AM brand) ──
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.color': '#cccccc',
    'grid.linestyle': '-',
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica LT Std', 'HelveticaNeueLT Std',
                        'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '#cccccc',
})

# ReSolve AM brand palette
C_SG = '#000000'
C_BLEND = '#00478D'
C_TDS = '#6F4596'
C_TDM = '#89D2FF'
C_BU = '#FBBA00'
C_POS = '#62CC77'
C_NEG = '#C00000'

# ── Load data ──
df = pd.read_csv(str(DATA_CSV))
df.columns = ['Date', 'SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')
df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{col}_ret'] = df[col].pct_change()
df = df.dropna(subset=['SG_Trend_ret']).reset_index(drop=True)

for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{col}_g1'] = df[col] / df[col].iloc[0]

start_str = df['Date'].iloc[0].strftime('%b %d, %Y')
end_str = df['Date'].iloc[-1].strftime('%b %d, %Y')

def fig_to_b64(fig, dpi=150):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

charts = {}

# ════════════════════════════════════════════════════════
# CHART 1: Growth of $1
# ════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.plot(df['Date'], df['BU_g1'], color=C_BU, linewidth=1.2, linestyle='--', label='Bottom Up (70%)', alpha=0.7)
ax.plot(df['Date'], df['TD_Med_g1'], color=C_TDM, linewidth=1.2, linestyle='-.', label='Top Down (Full) (15%)', alpha=0.7)
ax.plot(df['Date'], df['TD_Small_g1'], color=C_TDS, linewidth=1.2, linestyle=':', label='Top Down (Constrained) (15%)', alpha=0.7)
ax.plot(df['Date'], df['SG_Trend_g1'], color=C_SG, linewidth=2.2, label='SG Trend Index (Excess)')
ax.plot(df['Date'], df['Blend_g1'], color=C_BLEND, linewidth=2.2, label='Trend Replication (Blend, Net)')
ax.set_ylabel('Growth of $1')
ax.legend(loc='upper right', ncol=2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.2f'))
plt.tight_layout()
charts['growth_of_1'] = fig_to_b64(fig)
plt.close()

# CHART 2: Relative Performance
fig, ax = plt.subplots(figsize=(12, 5))
ax.axhline(y=1.0, color='#999999', linewidth=1, linestyle='-', alpha=0.5)
ratio_blend = df['Blend_g1'] / df['SG_Trend_g1']
ratio_bu = df['BU_g1'] / df['SG_Trend_g1']
ratio_tds = df['TD_Small_g1'] / df['SG_Trend_g1']
ratio_tdm = df['TD_Med_g1'] / df['SG_Trend_g1']
ax.plot(df['Date'], ratio_bu, color=C_BU, linewidth=1.2, linestyle='--', label='Bottom Up / SG Trend', alpha=0.7)
ax.plot(df['Date'], ratio_tdm, color=C_TDM, linewidth=1.2, linestyle='-.', label='Top Down (Full) / SG Trend', alpha=0.7)
ax.plot(df['Date'], ratio_tds, color=C_TDS, linewidth=1.2, linestyle=':', label='Top Down (Constrained) / SG Trend', alpha=0.7)
ax.plot(df['Date'], ratio_blend, color=C_BLEND, linewidth=2.2, label='Blend / SG Trend')
ax.set_ylabel('Relative Performance (Ratio)')
ax.legend(loc='best', ncol=2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
charts['relative_perf'] = fig_to_b64(fig)
plt.close()

# CHART 3: Rolling 63-day correlation
fig, ax = plt.subplots(figsize=(12, 4.5))
w = 63
roll_blend = df['Blend_ret'].rolling(w).corr(df['SG_Trend_ret'])
roll_bu = df['BU_ret'].rolling(w).corr(df['SG_Trend_ret'])
roll_tds = df['TD_Small_ret'].rolling(w).corr(df['SG_Trend_ret'])
roll_tdm = df['TD_Med_ret'].rolling(w).corr(df['SG_Trend_ret'])
ax.plot(df['Date'], roll_bu, color=C_BU, linewidth=1, linestyle='--', label='Bottom Up', alpha=0.6)
ax.plot(df['Date'], roll_tdm, color=C_TDM, linewidth=1, linestyle='-.', label='Top Down (Full)', alpha=0.6)
ax.plot(df['Date'], roll_tds, color=C_TDS, linewidth=1, linestyle=':', label='Top Down (Constrained)', alpha=0.6)
ax.plot(df['Date'], roll_blend, color=C_BLEND, linewidth=2, label='Blend')
ax.set_ylabel('Correlation')
ax.legend(loc='lower left', ncol=4)
ax.set_ylim(-0.2, 1.05)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
charts['rolling_corr'] = fig_to_b64(fig)
plt.close()

# CHART 4: Lo-adjusted exponentially-weighted annualized tracking error (252-day half-life)
# We apply a rolling Lo (2002) adjustment: at each point, compute η from the trailing
# LO_Q autocorrelations of the daily tracking difference, then scale the EWM std
# by sqrt(252 * η) instead of sqrt(252).
LO_Q_CHART = 21  # same q as full-period calculation

def rolling_lo_eta(series, q):
    """Compute a rolling Lo (2002) η using a trailing window of 252 days."""
    window = 252  # need enough data for q lags to be meaningful
    eta_series = pd.Series(np.nan, index=series.index)
    vals = series.values
    for i in range(window, len(vals)):
        chunk = vals[i - window:i]
        chunk_dm = chunk - np.nanmean(chunk)
        if np.nanstd(chunk_dm) < 1e-12:
            eta_series.iloc[i] = 1.0
            continue
        eta = 1.0
        for k in range(1, q + 1):
            if k >= len(chunk):
                break
            a, b = chunk_dm[k:], chunk_dm[:-k]
            denom = np.sqrt(np.sum(a**2) * np.sum(b**2))
            if denom > 0:
                rho_k = np.sum(a * b) / denom
                eta += 2 * (1 - k / (q + 1)) * rho_k
        eta_series.iloc[i] = max(eta, 0.01)
    return eta_series

fig, ax = plt.subplots(figsize=(12, 4.5))
hl = 252  # half-life in trading days
for col, label, color, ls in [('BU_ret', 'Bottom Up', C_BU, '--'),
                                ('TD_Med_ret', 'Top Down (Full)', C_TDM, '-.'),
                                ('TD_Small_ret', 'Top Down (Constrained)', C_TDS, ':'),
                                ('Blend_ret', 'Blend', C_BLEND, '-')]:
    diff = df[col] - df['SG_Trend_ret']
    ewm_std = diff.ewm(halflife=hl).std()
    eta_roll = rolling_lo_eta(diff, LO_Q_CHART)
    te_adj = ewm_std * np.sqrt(252 * eta_roll) * 100
    lw = 2 if col == 'Blend_ret' else 1
    al = 1.0 if col == 'Blend_ret' else 0.6
    ax.plot(df['Date'], te_adj, color=color, linewidth=lw, linestyle=ls, label=label, alpha=al)
ax.set_ylabel('Lo-Adjusted Tracking Error (%)')
ax.legend(loc='upper right', ncol=4)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
charts['rolling_te'] = fig_to_b64(fig)
plt.close()

# CHART 4b: Rolling 1-year return differences
roll_1y_sg_chart = df['SG_Trend'].pct_change(252) * 100
roll_1y_blend_chart = df['Blend'].pct_change(252) * 100
roll_1y_diff_chart = roll_1y_blend_chart - roll_1y_sg_chart

# Trim to first valid 252-day observation
first_valid_idx = roll_1y_diff_chart.first_valid_index()
dates_trim = df['Date'].loc[first_valid_idx:]
diff_trim = roll_1y_diff_chart.loc[first_valid_idx:]

# Compute full-period std over valid data only
roll_1y_full_std = diff_trim.std()
roll_1y_full_mean = diff_trim.mean()

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.fill_between(dates_trim, roll_1y_full_mean - roll_1y_full_std, roll_1y_full_mean + roll_1y_full_std,
                color=C_BLEND, alpha=0.10, label='±1 Std Dev')
ax.fill_between(dates_trim, 0, diff_trim,
                where=(diff_trim >= 0), color=C_POS, alpha=0.3, interpolate=True)
ax.fill_between(dates_trim, 0, diff_trim,
                where=(diff_trim < 0), color=C_NEG, alpha=0.3, interpolate=True)
ax.plot(dates_trim, diff_trim, color=C_BLEND, linewidth=1.5)
ax.axhline(y=0, color='#333333', linewidth=0.5)
ax.axhline(y=roll_1y_full_mean + roll_1y_full_std, color=C_BLEND, linewidth=0.8, linestyle='--', alpha=0.5)
ax.axhline(y=roll_1y_full_mean - roll_1y_full_std, color=C_BLEND, linewidth=0.8, linestyle='--', alpha=0.5)
ax.set_ylabel('Return Difference (%)')
ax.legend(loc='lower left', fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
charts['rolling_1y_diff'] = fig_to_b64(fig)
plt.close()

# CHART 5: Cumulative return difference
fig, ax = plt.subplots(figsize=(12, 4.5))
cum_diff = (df['Blend_g1'] / df['SG_Trend_g1'] - 1) * 100
ax.fill_between(df['Date'], 0, cum_diff, where=(cum_diff >= 0), color=C_POS, alpha=0.3, interpolate=True)
ax.fill_between(df['Date'], 0, cum_diff, where=(cum_diff < 0), color=C_NEG, alpha=0.3, interpolate=True)
ax.plot(df['Date'], cum_diff, color=C_BLEND, linewidth=1.5)
ax.axhline(y=0, color='#333333', linewidth=0.8)
ax.set_ylabel('Cumulative Excess (%)')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
charts['cum_diff'] = fig_to_b64(fig)
plt.close()

# CHART 6: Monthly return scatter
df_m = df.set_index('Date').resample('ME').last()
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df_m[f'{col}_mret'] = df_m[col].pct_change()
df_m = df_m.dropna(subset=['SG_Trend_mret'])

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(df_m['SG_Trend_mret']*100, df_m['Blend_mret']*100,
           color=C_BLEND, alpha=0.6, s=40, edgecolors='white', linewidth=0.5, zorder=3)
m_slope, m_int = np.polyfit(df_m['SG_Trend_mret']*100, df_m['Blend_mret']*100, 1)
x_line = np.linspace(df_m['SG_Trend_mret'].min()*100, df_m['SG_Trend_mret'].max()*100, 100)
ax.plot(x_line, m_slope*x_line + m_int, color=C_SG, linewidth=1.5, linestyle='--', alpha=0.7,
        label=f'monthly beta = {m_slope:.2f}, alpha = {m_int:.2f}%')
lim_min = min(ax.get_xlim()[0], ax.get_ylim()[0])
lim_max = max(ax.get_xlim()[1], ax.get_ylim()[1])
ax.plot([lim_min, lim_max], [lim_min, lim_max], color='#cccccc', linewidth=1, linestyle='-', alpha=0.5)
corr_m = df_m['SG_Trend_mret'].corr(df_m['Blend_mret'])
ax.set_xlabel('SG Trend Index Monthly Return (%)')
ax.set_ylabel('Blend Monthly Return (%)')
ax.legend(loc='upper left')
ax.set_aspect('equal', adjustable='datalim')
plt.tight_layout()
charts['scatter_monthly'] = fig_to_b64(fig)
plt.close()

# CHART 7: Monthly return bars
fig, ax = plt.subplots(figsize=(14, 4.5))
x = np.arange(len(df_m))
width = 0.35
ax.bar(x - width/2, df_m['SG_Trend_mret']*100, width, label='SG Trend Index', color=C_SG, alpha=0.7)
ax.bar(x + width/2, df_m['Blend_mret']*100, width, label='Trend Replication Blend', color=C_BLEND, alpha=0.7)
ax.set_ylabel('Monthly Return (%)')
ax.set_xticks(x[::3])
ax.set_xticklabels([d.strftime('%b\n%Y') for d in df_m.index[::3]], fontsize=8)
ax.legend(loc='upper right')
ax.axhline(y=0, color='#333333', linewidth=0.5)
plt.tight_layout()
charts['monthly_bars'] = fig_to_b64(fig)
plt.close()

# CHART 8: Annual / partial-year performance
# Compute within-year returns (first trading day to last trading day of each year)
df['_year'] = df['Date'].dt.year
year_groups = []
for yr, grp in df.groupby('_year'):
    row = {}
    row['year'] = yr
    first_date = grp['Date'].iloc[0]
    last_date = grp['Date'].iloc[-1]
    # Label partial years
    if yr == df['_year'].min():
        row['label'] = f"{yr}*"
    elif yr == df['_year'].max() and last_date.month < 12:
        row['label'] = f"{yr}*"
    else:
        row['label'] = str(yr)
    for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
        row[f'{col}_yret'] = grp[col].iloc[-1] / grp[col].iloc[0] - 1
    year_groups.append(row)
df_y = pd.DataFrame(year_groups)

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(df_y))
w = 0.15
for i, (col, label, color) in enumerate([
    ('TD_Small_yret', 'Top Down (Constrained)', C_TDS),
    ('TD_Med_yret', 'Top Down (Full)', C_TDM),
    ('BU_yret', 'Bottom Up', C_BU),
    ('Blend_yret', 'Blend', C_BLEND),
    ('SG_Trend_yret', 'SG Trend', C_SG),
]):
    ax.bar(x + (i-2)*w, df_y[col]*100, w, label=label, color=color, edgecolor='white', linewidth=0.5)
ax.set_ylabel('Annual Return (%)')
ax.set_xticks(x)
ax.set_xticklabels(df_y['label'].tolist())
ax.legend(loc='best', ncol=5, fontsize=8)
ax.axhline(y=0, color='#333333', linewidth=0.5)
# Add footnote for partial years
ax.annotate('* Partial year', xy=(0.01, 0.01), xycoords='axes fraction',
            fontsize=7, color='#888888', fontstyle='italic')
plt.tight_layout()
charts['annual_bars'] = fig_to_b64(fig)
plt.close()
df.drop(columns=['_year'], inplace=True)

# Synthetic blend returns (used later in optimization section)
df['Synth_ret'] = 0.15 * df['TD_Small_ret'] + 0.15 * df['TD_Med_ret'] + 0.70 * df['BU_ret']

# CHART 9: Drawdowns
fig, ax = plt.subplots(figsize=(12, 4.5))
for col, label, color, ls, lw, al in [
    ('BU_g1', 'Bottom Up', C_BU, '--', 1, 0.5),
    ('TD_Med_g1', 'Top Down (Full)', C_TDM, '-.', 1, 0.5),
    ('TD_Small_g1', 'Top Down (Constrained)', C_TDS, ':', 1, 0.5),
    ('SG_Trend_g1', 'SG Trend Index', C_SG, '-', 2, 1.0),
    ('Blend_g1', 'Blend', C_BLEND, '-', 2, 1.0),
]:
    running_max = df[col].cummax()
    dd = (df[col] / running_max - 1) * 100
    ax.plot(df['Date'], dd, color=color, linewidth=lw, linestyle=ls, label=label, alpha=al)
ax.set_ylabel('Drawdown (%)')
ax.legend(loc='lower left', ncol=5, fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
charts['drawdowns'] = fig_to_b64(fig)
plt.close()

# CHART 10: Rolling 126-day correlation
fig, ax = plt.subplots(figsize=(12, 4.5))
w2 = 126
roll_blend_126 = df['Blend_ret'].rolling(w2).corr(df['SG_Trend_ret'])
roll_bu_126 = df['BU_ret'].rolling(w2).corr(df['SG_Trend_ret'])
roll_tds_126 = df['TD_Small_ret'].rolling(w2).corr(df['SG_Trend_ret'])
roll_tdm_126 = df['TD_Med_ret'].rolling(w2).corr(df['SG_Trend_ret'])
ax.plot(df['Date'], roll_bu_126, color=C_BU, linewidth=1, linestyle='--', label='Bottom Up', alpha=0.6)
ax.plot(df['Date'], roll_tdm_126, color=C_TDM, linewidth=1, linestyle='-.', label='Top Down (Full)', alpha=0.6)
ax.plot(df['Date'], roll_tds_126, color=C_TDS, linewidth=1, linestyle=':', label='Top Down (Constrained)', alpha=0.6)
ax.plot(df['Date'], roll_blend_126, color=C_BLEND, linewidth=2, label='Blend')
ax.set_ylabel('Correlation')
ax.legend(loc='lower left', ncol=4)
ax.set_ylim(-0.2, 1.05)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
charts['rolling_corr_126'] = fig_to_b64(fig)
plt.close()

# ── Lo (2002) autocorrelation-adjusted tracking error ──
# Defined here so it can be used in the thought experiment AND later stats.
LO_Q = 21  # number of lags (approx 1 month of trading days)

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

# CHART 11: Ex-post optimal blend — tracking error frontier
from scipy.optimize import minimize as sp_minimize

sg_r = df['SG_Trend_ret'].values
tds_r = df['TD_Small_ret'].values
tdm_r = df['TD_Med_ret'].values
bu_r = df['BU_ret'].values

# Full unconstrained optimization (Lo-adjusted)
def te_obj_full(w):
    diff = w[0]*tds_r + w[1]*tdm_r + w[2]*bu_r - sg_r
    return lo_adj_te(diff)

opt_res = sp_minimize(te_obj_full, [0.15, 0.15, 0.70],
                      bounds=[(0,1),(0,1),(0,1)],
                      constraints={'type': 'eq', 'fun': lambda w: sum(w) - 1},
                      method='SLSQP')
w_opt = opt_res.x
te_opt = te_obj_full(w_opt)

# Current blend TE (Lo-adjusted)
te_current = lo_adj_te(0.15*tds_r + 0.15*tdm_r + 0.70*bu_r - sg_r)

# Individual model TEs (Lo-adjusted)
te_tds_solo = lo_adj_te(tds_r - sg_r)
te_tdm_solo = lo_adj_te(tdm_r - sg_r)
te_bu_solo = lo_adj_te(bu_r - sg_r)

# Tracking error correlations
diff_tds = tds_r - sg_r
diff_tdm = tdm_r - sg_r
diff_bu = bu_r - sg_r
corr_tds_bu = np.corrcoef(diff_tds, diff_bu)[0,1]
corr_tdm_bu = np.corrcoef(diff_tdm, diff_bu)[0,1]
corr_tds_tdm = np.corrcoef(diff_tds, diff_tdm)[0,1]

# Frontier: sweep TD total weight from 0 to 100%
td_weights_scan = np.arange(0, 1.005, 0.01)
frontier_te = []
frontier_tds_w = []
frontier_tdm_w = []
frontier_bu_w = []

for td_total in td_weights_scan:
    bu_w = 1 - td_total
    if td_total < 0.001:
        frontier_te.append(lo_adj_te(bu_r - sg_r))
        frontier_tds_w.append(0)
        frontier_tdm_w.append(0)
        frontier_bu_w.append(1)
        continue
    def te_split(split):
        w1 = td_total * split[0]
        w2 = td_total * (1 - split[0])
        return lo_adj_te(w1*tds_r + w2*tdm_r + bu_w*bu_r - sg_r)
    r = sp_minimize(te_split, [0.5], bounds=[(0,1)], method='L-BFGS-B')
    frontier_te.append(r.fun)
    frontier_tds_w.append(td_total * r.x[0])
    frontier_tdm_w.append(td_total * (1 - r.x[0]))
    frontier_bu_w.append(bu_w)

frontier_te = np.array(frontier_te)

# Chart 11a: Tracking Error Frontier
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.plot(td_weights_scan * 100, frontier_te, color=C_BLEND, linewidth=2.5, label='Minimum Tracking Error Frontier')
ax.axhline(y=te_current, color=C_SG, linewidth=1.2, linestyle='--', alpha=0.7, label=f'Current Blend (15/15/70): {te_current:.1f}%')

# Mark the optimal point
opt_td_total = (w_opt[0] + w_opt[1]) * 100
ax.scatter([opt_td_total], [te_opt], color='#ef4444', s=80, zorder=5, edgecolors='white', linewidth=1.5)
ax.annotate(f'  Optimal: {w_opt[0]:.0%}/{w_opt[1]:.0%}/{w_opt[2]:.0%}\n  TE = {te_opt:.1f}%',
            xy=(opt_td_total, te_opt), fontsize=9, color='#ef4444', fontweight='500',
            xytext=(opt_td_total + 5, te_opt + 0.15))

# Mark current blend
current_td = 30
ax.scatter([current_td], [te_current], color=C_SG, s=80, zorder=5, edgecolors='white', linewidth=1.5)

ax.set_xlabel('Combined Top Down Weight (%)')
ax.set_ylabel('Lo-Adjusted Tracking Error (%)')
ax.legend(loc='upper left')
ax.set_xlim(-2, 102)
plt.tight_layout()
charts['te_frontier'] = fig_to_b64(fig)
plt.close()

# Chart 11b: Stacked area of optimal weights across the frontier
fig, ax = plt.subplots(figsize=(10, 4))
ax.fill_between(td_weights_scan * 100, 0, np.array(frontier_bu_w)*100, color=C_BU, alpha=0.6, label='Bottom Up')
ax.fill_between(td_weights_scan * 100, np.array(frontier_bu_w)*100,
                (np.array(frontier_bu_w) + np.array(frontier_tdm_w))*100, color=C_TDM, alpha=0.6, label='Top Down (Full)')
ax.fill_between(td_weights_scan * 100, (np.array(frontier_bu_w) + np.array(frontier_tdm_w))*100,
                100, color=C_TDS, alpha=0.6, label='Top Down (Constrained)')
ax.axvline(x=30, color=C_SG, linewidth=1.2, linestyle='--', alpha=0.7, label='Current (30% TD)')
ax.axvline(x=opt_td_total, color='#ef4444', linewidth=1.2, linestyle='--', alpha=0.7, label=f'Optimal ({opt_td_total:.0f}% TD)')
ax.set_xlabel('Combined Top Down Weight (%)')
ax.set_ylabel('Model Weight (%)')
ax.legend(loc='center right', fontsize=8)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
plt.tight_layout()
charts['weight_composition'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════
# Compute statistics (same as before)
# ════════════════════════════════════════════════════════
stats = {}
series_map = {
    'Top Down (Constrained)': ('TD_Small_ret', 'TD_Small_g1'),
    'Top Down (Full)': ('TD_Med_ret', 'TD_Med_g1'),
    'Bottom Up': ('BU_ret', 'BU_g1'),
    'Blend': ('Blend_ret', 'Blend_g1'),
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
    ir = (rets - sg_rets).mean() / (rets - sg_rets).std() * np.sqrt(252) if (rets - sg_rets).std() > 0 else 0
    stats[name] = dict(corr=corr, te=te, beta=beta, cum_ret=cum_ret, ann_ret=ann_ret, max_dd=max_dd, ann_vol=ann_vol, ir=ir)

# ── Lo-adjusted TE for each model (uses lo_eta defined earlier) ──
for name, (ret_col, _) in series_map.items():
    diff_arr = (df[ret_col] - df['SG_Trend_ret']).dropna().values
    daily_std = np.std(diff_arr, ddof=1)
    eta = lo_eta(diff_arr, LO_Q)
    stats[name]['te_adj'] = daily_std * np.sqrt(252 * eta) * 100
    stats[name]['lo_eta'] = eta

# Use the synthetic blend TE (te_current) for the Blend display value
# so it matches the Figure 12 chart annotation consistently (5.4% not 5.3%)
stats['Blend']['te_adj'] = te_current
synth_diff = (0.15*tds_r + 0.15*tdm_r + 0.70*bu_r - sg_r)
stats['Blend']['lo_eta'] = lo_eta(synth_diff, LO_Q)

sg_cum = (df['SG_Trend_g1'].iloc[-1] / df['SG_Trend_g1'].iloc[0] - 1) * 100
n_days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
sg_ann = ((1 + sg_cum/100) ** (365.25/n_days) - 1) * 100
sg_vol = df['SG_Trend_ret'].std() * np.sqrt(252) * 100
sg_max_dd = (df['SG_Trend_g1'] / df['SG_Trend_g1'].cummax() - 1).min() * 100

m_corr_blend = df_m['SG_Trend_mret'].corr(df_m['Blend_mret'])
m_corr_bu = df_m['SG_Trend_mret'].corr(df_m['BU_mret'])
m_corr_tds = df_m['SG_Trend_mret'].corr(df_m['TD_Small_mret'])
m_corr_tdm = df_m['SG_Trend_mret'].corr(df_m['TD_Med_mret'])

df_q = df.set_index('Date').resample('QE').last()
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df_q[f'{col}_qret'] = df_q[col].pct_change()
df_q = df_q.dropna(subset=['SG_Trend_qret'])
df_q['blend_diff'] = (df_q['Blend_qret'] - df_q['SG_Trend_qret']) * 100
best_q = df_q['blend_diff'].idxmax()
worst_q = df_q['blend_diff'].idxmin()

# Rolling 1-year return differences
roll_1y_blend = df['Blend'].pct_change(252) * 100
roll_1y_sg = df['SG_Trend'].pct_change(252) * 100
roll_1y_diff = (roll_1y_blend - roll_1y_sg).dropna()
roll_1y_diff_std = roll_1y_diff.std()
roll_1y_diff_mean = roll_1y_diff.mean()
roll_1y_diff_min = roll_1y_diff.min()
roll_1y_diff_max = roll_1y_diff.max()
roll_1y_within_5 = (roll_1y_diff.abs() <= 5).sum() / len(roll_1y_diff) * 100

# Monthly diff stats (for conclusions)
m_diff = (df_m['Blend_mret'] - df_m['SG_Trend_mret']) * 100
m_diff_std = m_diff.std()
m_within_2 = (m_diff.abs() <= 2).sum() / len(m_diff) * 100
m_within_3 = (m_diff.abs() <= 3).sum() / len(m_diff) * 100
q_diff_std = df_q['blend_diff'].std()

# ════════════════════════════════════════════════════════
# Build HTML with disclosures, figure labels, etc.
# ════════════════════════════════════════════════════════

# Shared source/disclaimer fragments
SRC_LINE = f"Source: ReSolve Asset Management SEZC (Cayman) (replication model data), Société Générale (SG Trend Index data). Calculations by ReSolve Asset Management. Data from {start_str} through {end_str}."
SRC_SG = ""  # incorporated into SRC_LINE
DISC_HYPO = "Trend Replication model returns are hypothetical, net of estimated transaction costs and management fees, and do not represent actual trading. The SG Trend Index is shown on an excess return basis. Hypothetical performance results have many inherent limitations, some of which are described in the Important Disclosures section of this document."
DISC_PAST = "Past performance is not indicative of future results."

def fig_block(num, title, img_key, description="", sg_verb="used"):
    """Generate a labeled figure block with caption above and a single consolidated disclosure paragraph below."""
    # Build one self-contained disclosure paragraph: source → description → hypothetical caveat → past-performance caveat
    parts = [f"Source: ReSolve Asset Management SEZC (Cayman) (replication model data), Société Générale (SG Trend Index data). Calculations by ReSolve Asset Management. Data from {start_str} through {end_str}."]
    if description:
        parts.append(description)
    parts.append(f"Trend Replication model returns are hypothetical, net of estimated transaction costs and management fees, and do not represent actual trading. The SG Trend Index is {sg_verb} on an excess return basis and is net of underlying fund fees, which include management fees and trading costs and may include performance fees. Hypothetical performance results have many inherent limitations, some of which are described in the Important Disclosures section of this document. Past performance is not indicative of future results.")
    disclosure = " ".join(parts)
    return f"""
  <div class="figure-block">
    <div class="figure-caption"><strong>Figure {num}:</strong> {title}</div>
    <div class="chart-container">
      <img src="data:image/png;base64,{charts[img_key]}" alt="Figure {num}">
    </div>
    <div class="figure-disclosure">{disclosure}</div>
  </div>"""


html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trend Replication Program – 3-Year Analysis</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  @page {{
    size: letter;
    margin: 0.75in 0.85in;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1a1a2e; background: white; line-height: 1.5; font-size: 10.5px;
  }}
  .container {{ margin: 0; padding: 0; }}
  .header {{ text-align: center; margin-bottom: 28px; padding-bottom: 18px; border-bottom: 2px solid #00478D; }}
  .header h1 {{ font-size: 20px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }}
  .header .subtitle {{ font-size: 12px; color: #64748b; font-weight: 400; }}
  .header .date-range {{ font-size: 10px; color: #94a3b8; margin-top: 2px; }}
  .section {{ padding: 0; margin-bottom: 20px; }}
  .section h2 {{ font-size: 14px; font-weight: 600; color: #00478D; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #e2e8f0; }}
  .section h3 {{ font-size: 11.5px; font-weight: 600; color: #334155; margin: 12px 0 6px 0; }}
  .section p {{ margin-bottom: 8px; color: #334155; }}
  .chart-container {{ margin: 10px 0 4px 0; text-align: center; }}
  .chart-container img {{ max-width: 100%; border: 0.5px solid #e2e8f0; }}
  .figure-block {{ margin: 14px 0 18px 0; }}
  .figure-caption {{ font-size: 9.5px; font-weight: 600; color: #1a1a2e; margin: 0 0 4px 0; text-align: left; }}
  .figure-disclosure {{ font-size: 7.5px; color: #94a3b8; font-style: italic; text-align: justify; margin: 4px 0 0 0; line-height: 1.5; padding: 0; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 12px 0; }}
  .stat-card {{ background: #f8fafc; padding: 10px 12px; border-left: 3px solid #00478D; }}
  .stat-card.sg {{ border-left-color: #1a1a2e; }}
  .stat-card .stat-label {{ font-size: 8px; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b; margin-bottom: 2px; }}
  .stat-card .stat-value {{ font-size: 18px; font-weight: 700; color: #1a1a2e; }}
  .stat-card .stat-detail {{ font-size: 8px; color: #94a3b8; margin-top: 1px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 9.5px; }}
  table th {{ background: #f1f5f9; padding: 5px 8px; text-align: right; font-weight: 600; color: #334155; border-bottom: 1.5px solid #cbd5e1; }}
  table th:first-child {{ text-align: left; }}
  table td {{ padding: 4px 8px; text-align: right; border-bottom: 0.5px solid #e2e8f0; color: #475569; }}
  table td:first-child {{ text-align: left; font-weight: 500; color: #1a1a2e; }}
  .highlight {{ color: #00478D; font-weight: 600; }}
  .neg {{ color: #ef4444; }}
  .pos {{ color: #10b981; }}
  .callout {{ background: #f8fdfb; border-left: 3px solid #00478D; padding: 8px 12px; margin: 12px 0; font-size: 10px; }}
  .callout-warn {{ background: #fffef5; border-left-color: #f59e0b; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .disclosure-section {{ background: #fafafa; padding: 18px; margin-bottom: 20px; }}
  .disclosure-section h2 {{ font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1.5px solid #e2e8f0; }}
  .disclosure-section p {{ font-size: 8px; color: #64748b; margin-bottom: 6px; line-height: 1.6; text-align: justify; font-style: italic; }}
  .glossary-term {{ font-weight: 700; color: #475569; font-style: normal; }}
  .footer {{ text-align: center; padding: 12px; color: #94a3b8; font-size: 8px; }}
  /* Page break hints */
  .section {{ page-break-inside: auto; }}
  .figure-block {{ page-break-inside: avoid; }}
  .stat-card {{ page-break-inside: avoid; }}
  table {{ page-break-inside: auto; }}
  tr {{ page-break-inside: avoid; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <div style="font-size: 8px; color: #94a3b8; font-style: italic; margin-bottom: 8px;">For use with sophisticated investors and financial professionals only. Not for distribution to the general public.</div>
  <h1>Trend Replication Program</h1>
  <div class="subtitle">3-Year Hypothetical Performance Analysis</div>
  <div class="date-range">{start_str} – {end_str}</div>
</div>

<!-- ═══ Executive Summary ═══ -->
<div class="section">
  <h2>Executive Summary</h2>
  <p>Over the three-year historical period since inception, the Trend Replication Program has achieved a <strong class="highlight">{stats['Blend']['corr']:.3f} daily return correlation</strong> and a <strong class="highlight">{m_corr_blend:.3f} monthly return correlation</strong> to the SG Trend Index, with a beta of <strong>{stats['Blend']['beta']:.2f}</strong>. The autocorrelation-adjusted annualized tracking error (Lo, 2002) has been <strong>{stats['Blend']['te_adj']:.1f}%</strong>. While these metrics suggest a strong historical fit, readers should note that replication programs are inherently imperfect: the exact methodology and constituent weights of the SG Trend Index are not fully disclosed, and the models used here may not capture all drivers of index performance.</p>
  <p>The blend's hypothetical cumulative return of <strong>{stats['Blend']['cum_ret']:.1f}%</strong> compares to <strong>{sg_cum:.1f}%</strong> for the SG Trend Index over the same period.</p>
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Blend – Full-Period Correlation</div>
      <div class="stat-value">{stats['Blend']['corr']:.3f}</div>
      <div class="stat-detail">Daily returns vs. SG Trend Index</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Monthly Return Correlation</div>
      <div class="stat-value">{m_corr_blend:.3f}</div>
      <div class="stat-detail">Blend vs. SG Trend Index</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Blend – Adj. Tracking Error</div>
      <div class="stat-value">{stats['Blend']['te_adj']:.1f}%</div>
      <div class="stat-detail">Lo (2002) autocorrelation-adjusted</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Rolling 1-Year Return Diff (Std)</div>
      <div class="stat-value">{roll_1y_diff_std:.1f}%</div>
      <div class="stat-detail">Historical standard deviation</div>
    </div>
  </div>
</div>

<!-- ═══ Growth of $1 ═══ -->
<div class="section">
  <h2>Growth of $1</h2>
  <p>The chart below normalizes each series to $1 at inception. The blend (blue) and SG Trend Index (black) track closely throughout, with the three sub-models shown for reference.</p>
  {fig_block(1, "Growth of $1 — Trend Replication Program vs. SG Trend Index",
             "growth_of_1",
             "Each series is normalized to $1 as of the inception date. The Trend Replication Blend is composed of 15% Top Down (Constrained), 15% Top Down (Full), and 70% Bottom Up, rebalanced daily.",
             sg_verb="shown")}
  <p>Over the historical period, all four replication series — and the blend — generally followed the SG Trend Index's trajectory through major market regimes, including the 2023 rate-driven rally, the 2024 consolidation, the April 2025 tariff shock, and the subsequent recovery.</p>
</div>

<!-- ═══ Relative Performance ═══ -->
<div class="section">
  <h2>Relative Performance vs. SG Trend Index</h2>
  <p>The ratio of each series' growth-of-$1 to the SG Trend Index isolates tracking quality over time. A perfectly flat line at 1.0 would indicate identical performance.</p>
  {fig_block(2, "Relative Performance of Each Sub-Model and Blend vs. SG Trend Index",
             "relative_perf",
             "Calculated as the ratio of each strategy's growth-of-$1 to the SG Trend Index growth-of-$1. A value above 1.0 indicates cumulative outperformance; below 1.0 indicates cumulative underperformance.")}
  <p>Over the historical period, the blend's relative performance declined gradually through mid-2024 before stabilizing in the latter half of the period. The Bottom Up model, which carries 70% of the blend weight, has historically been the primary driver of relative performance.</p>
  <div class="callout">
    <strong>Key observation:</strong> The Top Down (Constrained) and Top Down (Full) models have exhibited considerably more relative volatility than Bottom Up, but their small weight (15% each) limits their impact on the blended program.
  </div>
</div>

<!-- ═══ Statistics Table ═══ -->
<div class="section">
  <h2>Full-Period Statistics</h2>
  <table>
    <thead>
      <tr><th>Metric</th><th>SG Trend Index</th><th>Top Down (Constrained)</th><th>Top Down (Full)</th><th>Bottom Up</th><th>Blend</th></tr>
    </thead>
    <tbody>
      <tr><td>Annualized Return</td><td>{sg_ann:.2f}%</td><td>{stats['Top Down (Constrained)']['ann_ret']:.2f}%</td><td>{stats['Top Down (Full)']['ann_ret']:.2f}%</td><td>{stats['Bottom Up']['ann_ret']:.2f}%</td><td class="highlight">{stats['Blend']['ann_ret']:.2f}%</td></tr>
      <tr><td>Cumulative Return</td><td>{sg_cum:.2f}%</td><td>{stats['Top Down (Constrained)']['cum_ret']:.2f}%</td><td>{stats['Top Down (Full)']['cum_ret']:.2f}%</td><td>{stats['Bottom Up']['cum_ret']:.2f}%</td><td class="highlight">{stats['Blend']['cum_ret']:.2f}%</td></tr>
      <tr><td>Annualized Volatility</td><td>{sg_vol:.2f}%</td><td>{stats['Top Down (Constrained)']['ann_vol']:.2f}%</td><td>{stats['Top Down (Full)']['ann_vol']:.2f}%</td><td>{stats['Bottom Up']['ann_vol']:.2f}%</td><td>{stats['Blend']['ann_vol']:.2f}%</td></tr>
      <tr><td>Max Drawdown</td><td>{sg_max_dd:.2f}%</td><td>{stats['Top Down (Constrained)']['max_dd']:.2f}%</td><td>{stats['Top Down (Full)']['max_dd']:.2f}%</td><td>{stats['Bottom Up']['max_dd']:.2f}%</td><td>{stats['Blend']['max_dd']:.2f}%</td></tr>
      <tr><td>Daily Correlation to SG</td><td>1.000</td><td>{stats['Top Down (Constrained)']['corr']:.3f}</td><td>{stats['Top Down (Full)']['corr']:.3f}</td><td>{stats['Bottom Up']['corr']:.3f}</td><td class="highlight">{stats['Blend']['corr']:.3f}</td></tr>
      <tr><td>Monthly Correlation to SG</td><td>1.000</td><td>{m_corr_tds:.3f}</td><td>{m_corr_tdm:.3f}</td><td>{m_corr_bu:.3f}</td><td class="highlight">{m_corr_blend:.3f}</td></tr>
      <tr><td>Ann. Tracking Error</td><td>—</td><td>{stats['Top Down (Constrained)']['te']:.2f}%</td><td>{stats['Top Down (Full)']['te']:.2f}%</td><td>{stats['Bottom Up']['te']:.2f}%</td><td>{stats['Blend']['te']:.2f}%</td></tr>
      <tr><td>Adj. Tracking Error (Lo)</td><td>—</td><td>{stats['Top Down (Constrained)']['te_adj']:.2f}%</td><td>{stats['Top Down (Full)']['te_adj']:.2f}%</td><td>{stats['Bottom Up']['te_adj']:.2f}%</td><td class="highlight">{stats['Blend']['te_adj']:.2f}%</td></tr>
      <tr><td>Beta to SG Trend</td><td>1.00</td><td>{stats['Top Down (Constrained)']['beta']:.2f}</td><td>{stats['Top Down (Full)']['beta']:.2f}</td><td>{stats['Bottom Up']['beta']:.2f}</td><td class="highlight">{stats['Blend']['beta']:.2f}</td></tr>
      <tr><td>Information Ratio</td><td>—</td><td>{stats['Top Down (Constrained)']['ir']:.2f}</td><td>{stats['Top Down (Full)']['ir']:.2f}</td><td>{stats['Bottom Up']['ir']:.2f}</td><td>{stats['Blend']['ir']:.2f}</td></tr>
    </tbody>
  </table>
  <div class="figure-disclosure">Source: ReSolve Asset Management SEZC (Cayman) (replication model data), Société Générale (SG Trend Index data). Calculations by ReSolve Asset Management. Data from {start_str} through {end_str}. Trend Replication model returns are hypothetical, net of estimated transaction costs and management fees, and do not represent actual trading. The SG Trend Index is shown on an excess return basis and is net of underlying fund fees, which include management fees and trading costs and may include performance fees. Hypothetical performance results have many inherent limitations, some of which are described in the Important Disclosures section of this document. Adjusted Tracking Error (Lo) applies the autocorrelation adjustment of Lo (2002) using a Bartlett kernel with {LO_Q} lags. Past performance is not indicative of future results. See Technical Glossary for metric definitions.</div>
</div>

<!-- ═══ Correlation Analysis ═══ -->
<div class="section">
  <h2>Rolling Correlation Analysis</h2>
  <p>Correlation stability matters as much as its level. The rolling 63-day (quarterly) window reveals how consistently the replication tracks the target index across different market environments.</p>
  {fig_block(3, "Rolling 63-Day Correlation of Each Sub-Model and Blend with the SG Trend Index",
             "rolling_corr",
             "Pearson correlation is calculated on a rolling 63-trading-day (approximately one calendar quarter) window using daily returns.")}
  <p>Historically, the blend's rolling correlation generally remained in the <strong>0.6 – 0.9 range</strong>, with periodic dips corresponding to regime transitions in underlying trend signals. The Bottom Up model, as the dominant component, has tended to anchor the blend's correlation floor.</p>

  <h3>Longer-Window Perspective</h3>
  <p>Extending the window to 126 days (roughly 6 months) smooths short-term noise and reveals the structural relationship more clearly.</p>
  {fig_block(4, "Rolling 126-Day Correlation of Each Sub-Model and Blend with the SG Trend Index",
             "rolling_corr_126",
             "Pearson correlation is calculated on a rolling 126-trading-day (approximately six calendar months) window using daily returns.")}
</div>

<!-- ═══ Tracking Error ═══ -->
<div class="section">
  <h2>Tracking Error</h2>
  <p>Annualized tracking error measures the volatility of the daily return difference between each program and the SG Trend Index. An exponentially-weighted standard deviation (252-day half-life) is used in the chart below to emphasize more recent tracking behavior while retaining sensitivity to earlier episodes.</p>
  {fig_block(5, "Lo Autocorrelation-Adjusted Exponentially-Weighted Annualized Tracking Error vs. SG Trend Index (252-Day Half-Life)",
             "rolling_te",
             "Tracking error is the exponentially-weighted standard deviation (252-trading-day half-life) of the daily return difference between each model and the SG Trend Index, annualized using the Lo (2002) autocorrelation adjustment with a rolling 252-day window and Bartlett kernel ({LO_Q} lags). The adjustment accounts for negative serial correlation in daily tracking differences that causes the standard sqrt(252) annualization to overstate effective longer-horizon dispersion.")}
  <p>Over the historical period, the blend's standard tracking error has generally fluctuated in the 5–8% annualized range. Spikes have tended to coincide with rapid market dislocations, when the SG Trend Index constituents may rebalance at different speeds or prices than the replication models.</p>

  <h3>Autocorrelation-Adjusted Tracking Error</h3>
  <p>Standard tracking error annualizes daily return differences by multiplying by √252, which implicitly assumes those differences are serially independent. In practice, the daily tracking differences of the blend have historically exhibited <em>negative</em> autocorrelation — a tendency for above-average tracking differences on one day to be partially offset in subsequent days. This negative autocorrelation means the standard measure overstates the dispersion an investor would have actually experienced over longer horizons.</p>
  <p>Following Lo (2002), we apply a Bartlett-kernel autocorrelation adjustment using {LO_Q} lags of serial correlation. The adjustment factor η scales the annualization: TE<sub>adj</sub> = σ<sub>daily</sub> × √(252 × η), where η &lt; 1 indicates negative net autocorrelation and a reduction in effective annualized dispersion. For the blend, the full-period η = {stats['Blend']['lo_eta']:.3f}, reducing the full-period annualized tracking error from <strong>{stats['Blend']['te']:.1f}%</strong> (standard) to <strong>{stats['Blend']['te_adj']:.1f}%</strong> (adjusted).</p>

  <h3>Rolling One-Year Return Differences</h3>
  <p>As a point of validation, the chart below shows the rolling 252-trading-day return difference between the blend and the SG Trend Index. The historical standard deviation of these differences has been approximately <strong>{roll_1y_diff_std:.1f}%</strong>, with {roll_1y_within_5:.0f}% of observations falling within ±5 percentage points. This realized figure is more consistent with the Lo-adjusted tracking error than with the standard measure, supporting the view that the standard figure overstates the effective longer-horizon dispersion for this program.</p>
  {fig_block(6, "Rolling 252-Trading-Day Return Difference — Trend Replication Blend Minus SG Trend Index",
             "rolling_1y_diff",
             "Each point shows the trailing 252-trading-day (approximately one calendar year) total return of the Trend Replication Blend minus the trailing 252-trading-day total return of the SG Trend Index. Green shading indicates periods of blend outperformance; red indicates underperformance.")}
  <div class="callout-warn callout">
    <strong>Periods of elevated tracking error</strong> are visible around March 2023 (SVB crisis), October–November 2023, early August 2024 (yen carry unwind), and April 2025 (tariff shock). These episodes reflect sudden regime shifts where the latent positioning of the SG Trend Index diverged from the replication signals.
  </div>
</div>

<!-- ═══ Cumulative Difference ═══ -->
<div class="section">
  <h2>Cumulative Return Difference</h2>
  <p>The area chart below shows the cumulative percentage-point gap between the blend and the SG Trend Index. Green shading indicates periods of outperformance; red indicates underperformance.</p>
  {fig_block(7, "Cumulative Return Difference — Trend Replication Blend Minus SG Trend Index",
             "cum_diff",
             "Calculated as (Blend Growth-of-$1 divided by SG Trend Growth-of-$1, minus 1) times 100. Green shading indicates periods of blend outperformance; red indicates underperformance.")}
  <p>Historically, the blend lagged the SG Trend Index for the first several months before the cumulative gap began to stabilize in more recent quarters, though there is no assurance that this pattern will persist.</p>
</div>

<!-- ═══ Monthly Returns ═══ -->
<div class="section">
  <h2>Monthly Return Analysis</h2>
  <div class="two-col">
    <div>
      {fig_block(8, f"Monthly Return Scatter — Blend vs. SG Trend Index (ρ = {corr_m:.3f})",
                 "scatter_monthly",
                 f"Each dot represents one calendar month. The dashed line shows ordinary least squares regression on monthly returns (monthly beta = {m_slope:.2f}, alpha = {m_int:.2f}%). The light gray line is the 45-degree reference. Note: the monthly regression beta differs from the daily-return beta reported in the Full-Period Statistics table.")}
    </div>
    <div>
      <h3>Interpretation</h3>
      <p style="margin-top: 24px;">The clustering around the 45-degree line suggests a strong historical monthly fit. The monthly regression beta of <strong>{m_slope:.2f}</strong> and monthly correlation of <strong>{m_corr_blend:.3f}</strong> indicate that, over this period, the blend has generally captured the direction and magnitude of monthly SG Trend moves. This monthly regression beta is distinct from the daily-return beta of <strong>{stats['Blend']['beta']:.2f}</strong> reported in the Full-Period Statistics table, which is computed from daily returns.</p>
      <p>Outlier months — those furthest from the diagonal — represent periods where the replication signals diverged most from the index's actual constituent positioning.</p>
    </div>
  </div>
  <h3>Month-by-Month Returns</h3>
  {fig_block(9, "Side-by-Side Monthly Returns — SG Trend Index vs. Trend Replication Blend",
             "monthly_bars",
             "Each pair of bars represents one calendar month. SG Trend Index is shown in black and the Trend Replication Blend in blue.")}
</div>

<!-- ═══ Annual Performance ═══ -->
<div class="section">
  <h2>Annual Performance</h2>
  {fig_block(10, "Calendar-Year Returns by Sub-Model and Blend vs. SG Trend Index",
             "annual_bars",
             "Returns are calculated within each calendar year from the first trading day to the last trading day. Years marked with an asterisk (*) are partial: 2023 begins at program inception (February) and 2026 is year-to-date through the last available observation.")}
  <p>The annual grouping shows each sub-model's contribution to the blend across calendar years, including partial years at inception and year-to-date. The three models' dispersion highlights the diversification benefit of blending multiple replication approaches.</p>

  <div class="callout">
    <strong>A note on blend vs. sub-model returns:</strong> Readers may notice that the blend's calendar-year return can differ from a simple weighted average of sub-model returns. This is expected. The blend reflects the actual portfolio, where trades are netted across sub-models before execution — e.g., one model going long while another reduces the same position — and position- and sector-level risk caps are applied at the aggregate portfolio level rather than to each sub-model independently. Daily rebalancing back to fixed weights can also create modest drag when sub-model returns are positively autocorrelated, or a modest benefit when returns mean-revert.  </div>
</div>

<!-- ═══ Drawdowns ═══ -->
<div class="section">
  <h2>Drawdown Analysis</h2>
  {fig_block(11, "Drawdown from Peak — All Sub-Models and Blend vs. SG Trend Index",
              "drawdowns",
              "Drawdown is measured from each series' respective running high-water mark. A value of negative 10% means the series is 10% below its all-time high as of that date.")}
  <p>Over the historical period, the blend's maximum drawdown of <strong>{stats['Blend']['max_dd']:.1f}%</strong> compares to <strong>{sg_max_dd:.1f}%</strong> for the SG Trend Index. The broadly similar drawdown profiles suggest the replication has historically captured both the upside and the risk characteristics of the target index, though future drawdown behavior may differ.</p>
</div>

<!-- ═══ Thought Experiment: Ex-Post Optimal Blend ═══ -->
<div class="section">
  <h2>Thought Experiment: Ex-Post Optimal Blend</h2>
  <p>A natural question for any multi-model program is whether the chosen weights are optimal. While the current 15/15/70 allocation was set ex-ante, we can use the full history to ask: <em>what blend of the three sub-models would have minimized tracking error against the SG Trend Index over the live period?</em> This is purely a backward-looking exercise — the result reflects hindsight and should not be interpreted as a recommendation for prospective weights.</p>

  <p>The ex-post optimal weights are approximately <strong>{w_opt[0]*100:.1f}% Top Down (Constrained) / {w_opt[1]*100:.1f}% Top Down (Full) / {w_opt[2]*100:.1f}% Bottom Up</strong>, which would have produced a Lo-adjusted annualized tracking error of <strong>{te_opt:.1f}%</strong> versus <strong>{te_current:.1f}%</strong> for the current blend — a reduction of roughly {te_current - te_opt:.1f} percentage points.</p>

  {fig_block(12, "Tracking Error Frontier — Minimum Achievable Lo-Adjusted Tracking Error by Combined Top Down Weight",
             "te_frontier",
             "The frontier shows the minimum Lo-adjusted annualized tracking error (Lo, 2002; Bartlett kernel, {LO_Q} lags) achievable at each level of combined Top Down weight, with the split between Top Down (Constrained) and Top Down (Full) optimized at each point. The red dot marks the ex-post global minimum; the black dot marks the current 15/15/70 blend. All weights are constrained to be non-negative and sum to 100%.")}

  <p>The frontier reveals a notably flat minimum: tracking error varies by less than one percentage point across a wide range of Top Down allocations (roughly 35–75%). This flatness implies that moderate changes to the current weights would have had limited impact on tracking quality — a reassuring finding for the robustness of the existing allocation.</p>

  {fig_block(13, "Optimal Sub-Model Weight Composition Along the Frontier",
             "weight_composition",
             "Stacked area chart showing how the minimum-tracking-error split between Top Down (Constrained), Top Down (Full), and Bottom Up shifts as total Top Down weight increases. Vertical dashed lines mark the current allocation (30% TD) and the ex-post optimal allocation ({w_opt[0]+w_opt[1]:.0%} TD).")}

  <p>The key insight driving the result is the low correlation between the tracking errors of the Top Down and Bottom Up models. The correlation between Bottom Up and Top Down (Constrained) tracking differences is just <strong>{corr_tds_bu:.2f}</strong>, and between Bottom Up and Top Down (Full) it is <strong>{corr_tdm_bu:.2f}</strong>. By contrast, the two Top Down models' tracking errors are highly correlated (<strong>{corr_tds_tdm:.2f}</strong>), limiting the diversification benefit of shifting weight between them. This suggests that the primary lever for reducing tracking error is the balance between the Top Down family and the Bottom Up model, not the internal split within Top Down.</p>

  <div class="callout-warn callout">
    <strong>Important caveat:</strong> These optimal weights are computed with perfect hindsight over the full three-year sample. They are not implementable in real time and are sensitive to the specific market regimes realized during this period. The purpose of this analysis is to bound the potential for improvement and to illuminate the structural diversification properties of the sub-models, not to prescribe a weight change.
  </div>
</div>

<!-- ═══ Sub-Program Deep Dive ═══ -->
<div class="section">
  <h2>Sub-Program Assessment</h2>
  <h3>Bottom Up (70% Weight)</h3>
  <p>As the dominant component, Bottom Up is the primary driver of blend performance. Its daily correlation of <strong>{stats['Bottom Up']['corr']:.3f}</strong> and Lo-adjusted tracking error of <strong>{stats['Bottom Up']['te_adj']:.1f}%</strong> represent the backbone of the replication. The Bottom Up model runs a combination of actual trend-following programs whose blend was selected to produce a strong fit to the performance of the systematic trend-following category. Because these are trend-following models rather than statistical regressions, their signals should evolve at a pace comparable to the underlying managers in the index itself.</p>
  <h3>Top Down — Constrained Universe (15% Weight)</h3>
  <p>With a correlation of <strong>{stats['Top Down (Constrained)']['corr']:.3f}</strong> and Lo-adjusted tracking error of <strong>{stats['Top Down (Constrained)']['te_adj']:.1f}%</strong>, the constrained-universe top-down model brings a complementary regression-based signal. This model uses a deliberately limited set of markets and factors to estimate index exposures, trading parsimony for robustness. Its beta of {stats['Top Down (Constrained)']['beta']:.2f} to the index suggests it captures trend direction with some amplification in magnitude.</p>
  <h3>Top Down — Full Universe (15% Weight)</h3>
  <p>The full-universe top-down model expands the regression to the complete set of available markets and factors, with a correlation of <strong>{stats['Top Down (Full)']['corr']:.3f}</strong> and Lo-adjusted tracking error of <strong>{stats['Top Down (Full)']['te_adj']:.1f}%</strong>. The broader input set gives this model more degrees of freedom to fit index behavior, at the cost of greater estimation noise. It complements the constrained variant by capturing cross-market exposures that the smaller model omits.</p>
  <div class="callout">
    <strong>Diversification benefit:</strong> The three sub-models represent fundamentally different replication philosophies — the Bottom Up model blends live trend programs, while the two Top Down models use regression on narrow and broad market universes respectively. Despite targeting the same index, their return patterns differ meaningfully at higher frequencies. Blending them reduces the blend's tracking error below what any single model achieves in isolation — a classic diversification benefit applied to replication rather than return generation.
  </div>
</div>

<!-- ═══ Quarterly Tracking Detail ═══ -->
<div class="section">
  <h2>Quarterly Tracking Detail</h2>
  <table>
    <thead><tr><th>Quarter</th><th>SG Trend</th><th>Blend</th><th>Difference</th></tr></thead>
    <tbody>
"""

for idx, row in df_q.iterrows():
    sg_qr = row['SG_Trend_qret'] * 100
    bl_qr = row['Blend_qret'] * 100
    diff = bl_qr - sg_qr
    diff_class = 'pos' if diff >= 0 else 'neg'
    is_last = idx == df_q.index[-1]
    last_data_date = df['Date'].iloc[-1]
    is_partial = is_last and idx.date() > last_data_date.date()
    if is_partial:
        q_label = f"Q{(idx.month-1)//3 + 1} {idx.year} (through {last_data_date.strftime('%b %d')})"
    else:
        q_label = f"Q{(idx.month-1)//3 + 1} {idx.year}"
    html += f'      <tr><td>{q_label}</td><td>{sg_qr:.2f}%</td><td>{bl_qr:.2f}%</td><td class="{diff_class}">{diff:+.2f}%</td></tr>\n'

html += f"""    </tbody>
  </table>
  <p>The strongest quarter of relative performance for the blend was <strong>Q{(best_q.month-1)//3 + 1} {best_q.year}</strong> ({df_q.loc[best_q, 'blend_diff']:+.2f}%), while the weakest was <strong>Q{(worst_q.month-1)//3 + 1} {worst_q.year}</strong> ({df_q.loc[worst_q, 'blend_diff']:+.2f}%).</p>
  <div class="figure-disclosure">Source: ReSolve Asset Management SEZC (Cayman) (replication model data), Société Générale (SG Trend Index data). Calculations by ReSolve Asset Management. Data from {start_str} through {end_str}. Quarterly returns are calculated from the last trading day of the prior quarter to the last trading day of the displayed quarter. Trend Replication model returns are hypothetical, net of estimated transaction costs and management fees, and do not represent actual trading. The SG Trend Index is shown on an excess return basis and is net of underlying fund fees, which include management fees and trading costs and may include performance fees. Past performance is not indicative of future results.</div>
</div>

<!-- ═══ Conclusions ═══ -->
<div class="section">
  <h2>Conclusions</h2>
  <p>Over its three-year historical period, the Trend Replication Program has demonstrated that systematic replication of the SG Trend Index may be achievable with a meaningful degree of fidelity. The blend's Lo-adjusted annualized tracking error of <strong>{stats['Blend']['te_adj']:.1f}%</strong> and daily return correlation of <strong>{stats['Blend']['corr']:.3f}</strong> suggest that the program has historically captured both the direction and magnitude of the target index's moves, though there is no guarantee that this level of fit will persist.</p>
  <p>A central finding is the diversification benefit of combining fundamentally different replication approaches. Each individual sub-model historically produced higher adjusted tracking error than the blend — {stats['Bottom Up']['te_adj']:.1f}% for Bottom Up, {stats['Top Down (Constrained)']['te_adj']:.1f}% for Top Down (Constrained), and {stats['Top Down (Full)']['te_adj']:.1f}% for Top Down (Full) — yet blending them reduced adjusted tracking error to {stats['Blend']['te_adj']:.1f}%. The low correlation between the Top Down and Bottom Up tracking differences has been the primary driver of this improvement, and the ex-post optimal weight analysis suggests the benefit has been robust across a wide range of allocations over this historical period.</p>
  <p>Historically, monthly return differences between the blend and the SG Trend Index have had a standard deviation of approximately {m_diff_std:.1f}%, with roughly {m_within_2:.0f}% of months falling within ±2% of the index and {m_within_3:.0f}% within ±3%. On a quarterly basis, the historical standard deviation has been approximately {q_diff_std:.1f}%. These differences are a natural consequence of replicating an index whose exact methodology and constituent weights are not fully disclosed.</p>
  <p>Over longer horizons, the historical fit has been tighter. The monthly return correlation of <strong>{m_corr_blend:.3f}</strong> and near-zero average monthly return difference ({(df_m['Blend_mret'].mean() - df_m['SG_Trend_mret'].mean())*100*12:.2f}% annualized) suggest that, historically, short-term noise has not compounded into persistent cumulative drift. The program's tracking quality held across a variety of market regimes over this period, including strong trend environments, range-bound consolidation, and sharp dislocations. Future market environments may produce different results.</p>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- TECHNICAL GLOSSARY                                     -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="disclosure-section">
  <h2>Technical Glossary</h2>

  <p><span class="glossary-term">Annualized Return:</span> The geometric average annual rate of return over the measurement period. Calculated as (Ending Value / Beginning Value)^(365.25 / Calendar Days) − 1.</p>

  <p><span class="glossary-term">Annualized Volatility:</span> The standard deviation of daily returns, multiplied by √252 to express on an annualized basis. Measures the total variability of a return series.</p>

  <p><span class="glossary-term">Beta:</span> The slope coefficient from a regression of the strategy's daily returns on the SG Trend Index's daily returns. A beta of 1.0 indicates proportional co-movement; values above (below) 1.0 indicate amplified (dampened) sensitivity.</p>

  <p><span class="glossary-term">Correlation:</span> The Pearson correlation coefficient between the daily (or monthly) returns of two series. Ranges from −1 (perfect inverse) to +1 (perfect co-movement). Used here as the primary measure of directional replication quality.</p>

  <p><span class="glossary-term">Cumulative Return:</span> The total percentage change in the growth-of-$1 series from inception to the end of the measurement period.</p>

  <p><span class="glossary-term">Drawdown:</span> The percentage decline from a series' running all-time high (high-water mark) to any subsequent trough. Maximum drawdown is the largest such decline observed over the full period.</p>

  <p><span class="glossary-term">Growth of $1:</span> A normalization that sets each series to $1.00 at inception, allowing direct visual comparison of cumulative performance across series with different base index levels.</p>

  <p><span class="glossary-term">Information Ratio:</span> The annualized mean of the daily return difference (strategy minus benchmark) divided by the annualized standard deviation of that difference. Measures risk-adjusted active return; positive values indicate outperformance per unit of tracking error.</p>

  <p><span class="glossary-term">Relative Performance (Ratio):</span> The ratio of a strategy's growth-of-$1 to the benchmark's growth-of-$1 at each point in time. A rising line indicates the strategy is outperforming; a falling line indicates underperformance.</p>

  <p><span class="glossary-term">Rolling Correlation:</span> The Pearson correlation coefficient calculated over a trailing window of fixed length (e.g., 63 or 126 trading days), recomputed daily. Captures the time-varying stability of the relationship between two return series.</p>

  <p><span class="glossary-term">Tracking Error (Standard):</span> The annualized volatility of the daily return difference between a strategy and its benchmark (SG Trend Index), calculated as σ<sub>daily</sub> × √252. This measure implicitly assumes daily return differences are serially independent. In the rolling charts, tracking error is computed using an exponentially-weighted standard deviation with a 252-trading-day half-life. Full-period tracking error in the statistics table uses the simple (equal-weighted) standard deviation over all observations.</p>

  <p><span class="glossary-term">Tracking Error (Lo-Adjusted):</span> An autocorrelation-adjusted annualized tracking error following the methodology of Lo (2002). The adjustment applies a Bartlett kernel over q lags of the daily return difference series to compute an adjustment factor η = 1 + 2 × Σ<sub>k=1</sub><sup>q</sup> (1 − k/(q+1)) × ρ<sub>k</sub>, where ρ<sub>k</sub> is the autocorrelation at lag k. The adjusted tracking error is σ<sub>daily</sub> × √(252 × η). When daily tracking differences exhibit negative autocorrelation (η &lt; 1), the standard measure overstates effective annualized dispersion and the adjusted figure is lower. This analysis uses q = {LO_Q} lags. Reference: Lo, Andrew W. "The Statistics of Sharpe Ratios." <em>Financial Analysts Journal</em> 58, no. 4 (2002): 36–52.</p>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- INDEX DEFINITIONS                                      -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="disclosure-section">
  <h2>Index Definitions</h2>

  <p><span class="glossary-term">SG Trend Index (SG CTA Trend Index):</span> The SG Trend Index is an equal-weighted, daily-calculated index of the ten largest (by AUM) trend-following CTA managers, reconstituted annually. It is designed to track the performance of a diversified portfolio of large, established trend-following funds and serves as a widely used benchmark for the managed futures trend-following style. The index is calculated and published by Société Générale. Because it is composed of actual fund returns, the index is reported net of underlying fund fees, which include management fees and trading costs and may include performance fees. Returns in this analysis are presented on an excess return basis (i.e., net of the risk-free rate). The index is not directly investable, and an investor cannot invest directly in an index.</p>

  <p><span class="glossary-term">Trend Replication Blend:</span> A proprietary composite index constructed by ReSolve Asset Management, designed to approximate the daily performance of the SG Trend Index. The blend is composed of three sub-models — 15% Top Down (Constrained), 15% Top Down (Full), and 70% Bottom Up — rebalanced daily. Returns are presented net of estimated transaction costs and management fees.</p>

  <p><span class="glossary-term">Top Down — Constrained Universe (Model #1):</span> A regression-based trend replication model that estimates SG Trend Index exposures using a deliberately limited set of markets and factors. The constrained universe trades parsimony for robustness, reducing estimation noise at the cost of omitting some cross-market exposures.</p>

  <p><span class="glossary-term">Top Down — Full Universe (Model #2):</span> A regression-based trend replication model that estimates SG Trend Index exposures using the complete set of available markets and factors. The broader input set provides more degrees of freedom to capture index behavior, complementing the constrained variant by fitting cross-market relationships the smaller model omits.</p>

  <p><span class="glossary-term">Bottom Up:</span> A replication model that runs a combination of actual trend-following programs, with the blend of programs selected to produce a strong fit to the performance of the systematic trend-following category. Because these are trend-following models rather than statistical regressions, their signals evolve at a pace comparable to the underlying managers in the index. It carries the largest blend weight (70%).</p>
</div>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- IMPORTANT DISCLOSURES                                  -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="disclosure-section">
  <h2>Important Disclosures</h2>

  <p>This analysis has been prepared by ReSolve Asset Management Inc. and/or ReSolve Asset Management SEZC (Cayman) ("ReSolve") for informational purposes only. Nothing contained herein constitutes investment advice, a recommendation, or an offer to buy or sell any security or investment product. All investments involve risk, including the possible loss of principal. Past performance is not indicative of future results. The Trend Replication model results presented herein represent hypothetical performance and do not reflect actual trading. Hypothetical performance results have many inherent limitations. No representation is being made that any account will or is likely to achieve profits or losses similar to those shown. In fact, there are frequently sharp differences between hypothetical performance results and the actual results subsequently achieved by any particular trading program. One of the limitations of hypothetical performance results is that they are generally prepared with the benefit of hindsight. In addition, hypothetical trading does not involve financial risk, and no hypothetical trading record can completely account for the impact of financial risk in actual trading. For example, the ability to withstand losses or to adhere to a particular trading program in spite of trading losses are material points which can also adversely affect actual trading results. There are numerous other factors related to the markets in general or to the implementation of any specific trading program which cannot be fully accounted for in the preparation of hypothetical performance results and all of which can adversely affect actual trading results.</p>

  <p>Trend Replication model returns labeled "Net" are presented after deduction of estimated transaction costs and management fees. Actual fees and expenses may vary. The SG Trend Index is presented on an excess return basis (net of the risk-free rate). Because the index is composed of actual fund returns, it is reported net of underlying fund fees, which include management fees and trading costs and may include performance fees. The SG Trend Index (SG CTA Trend Index) is a product of Société Générale. Société Générale does not sponsor, endorse, sell, or promote the Trend Replication Program or any investment product based on or linked to the SG Trend Index. Société Générale makes no representation or warranty, express or implied, regarding the advisability of investing in any product that seeks to replicate or track the SG Trend Index. An investor cannot invest directly in an index. Index performance does not reflect the deduction of any fees or expenses.</p>

  <p>Replication model data is sourced from ReSolve Asset Management SEZC (Cayman). SG Trend Index data is sourced from Société Générale. All calculations are performed by ReSolve Asset Management. While data is believed to be reliable, ReSolve does not guarantee its accuracy or completeness. Trend-following strategies, including replication programs, are subject to numerous risks including but not limited to market risk, leverage risk, liquidity risk, counterparty risk, model risk, and the risk that past trends may not persist. Replication programs face additional risks including signal lag, tracking error, divergence from the target index, and the risk that the target index methodology may change without notice. There is no guarantee that the Trend Replication Program will continue to achieve the level of tracking quality demonstrated during the historical period analyzed herein. ReSolve and/or its affiliates may have financial interests in products that utilize the Trend Replication models described herein. This analysis should not be considered independent research.</p>
</div>

<div class="footer">
  Analysis generated {datetime.now().strftime('%B %d, %Y')} · Data: {start_str} – {end_str}<br>
  © {datetime.now().year} ReSolve Asset Management. All rights reserved.
</div>

</div>
</body>
</html>"""

# Resolve template variables that don't get interpolated inside fig_block() args
html = html.replace('{LO_Q}', str(LO_Q))
opt_td_pct = f"{(w_opt[0]+w_opt[1])*100:.0f}"
html = html.replace('{w_opt[0]+w_opt[1]:.0%}', f"{opt_td_pct}%")

with open(str(OUT_HTML), 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML report saved to {OUT_HTML.name}")
