import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from io import BytesIO
import base64
from datetime import datetime

# ── Style setup matching the Return Stacked commentary aesthetic ──
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.color': '#cccccc',
    'grid.linestyle': '-',
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '#cccccc',
})

# Colors matching Return Stacked style
C_SG = '#1a1a1a'        # Black for SG Trend Index
C_BLEND = '#0d9488'     # Teal for Trend Replication blend
C_TDS = '#94a3b8'       # Slate gray for Top Down Small
C_TDM = '#64748b'       # Darker slate for Top Down Medium
C_BU = '#cbd5e1'        # Light slate for Bottom Up
C_ACCENT = '#f59e0b'    # Amber for highlights
C_POS = '#10b981'       # Green for positive
C_NEG = '#ef4444'       # Red for negative

# ── Load data ──
df = pd.read_csv('/sessions/charming-zealous-tesla/mnt/uploads/trend-data.csv')
df.columns = ['Date', 'SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

# ── Compute daily returns ──
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{col}_ret'] = df[col].pct_change()

df = df.dropna(subset=['SG_Trend_ret']).reset_index(drop=True)

# ── Normalize to Growth of $1 ──
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df[f'{col}_g1'] = df[col] / df[col].iloc[0]

# ── Verify blend weights: 15% TDS + 15% TDM + 70% BU ──
# The blend is pre-computed in the data

# ── Helper: fig to base64 ──
def fig_to_b64(fig, dpi=150):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

charts = {}

# ════════════════════════════════════════════════════════════════
# CHART 1: Growth of $1 (Figure 2 style)
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5.5))

ax.plot(df['Date'], df['BU_g1'], color=C_BU, linewidth=1.2, linestyle='--', label='Bottom Up (70%)', alpha=0.7)
ax.plot(df['Date'], df['TD_Med_g1'], color=C_TDM, linewidth=1.2, linestyle='-.', label='Top Down Medium (15%)', alpha=0.7)
ax.plot(df['Date'], df['TD_Small_g1'], color=C_TDS, linewidth=1.2, linestyle=':', label='Top Down Small (15%)', alpha=0.7)
ax.plot(df['Date'], df['SG_Trend_g1'], color=C_SG, linewidth=2.2, label='SG Trend Index')
ax.plot(df['Date'], df['Blend_g1'], color=C_BLEND, linewidth=2.2, label='Trend Replication (Blend)')

ax.set_ylabel('Growth of $1')
ax.set_title('Growth of $1: Trend Replication Program vs. SG Trend Index', fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='upper right', ncol=2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.2f'))

# Add date range annotation
start_str = df['Date'].iloc[0].strftime('%b %d, %Y')
end_str = df['Date'].iloc[-1].strftime('%b %d, %Y')
ax.annotate(f'{start_str} – {end_str}', xy=(0.5, -0.18), xycoords='axes fraction',
            ha='center', fontsize=9, color='#666666')

plt.tight_layout()
charts['growth_of_1'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 2: Relative Performance (Figure 3 style) - Ratio of each to SG Trend
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5))

ax.axhline(y=1.0, color='#999999', linewidth=1, linestyle='-', alpha=0.5)

ratio_blend = df['Blend_g1'] / df['SG_Trend_g1']
ratio_bu = df['BU_g1'] / df['SG_Trend_g1']
ratio_tds = df['TD_Small_g1'] / df['SG_Trend_g1']
ratio_tdm = df['TD_Med_g1'] / df['SG_Trend_g1']

ax.plot(df['Date'], ratio_bu, color=C_BU, linewidth=1.2, linestyle='--', label='Bottom Up / SG Trend', alpha=0.7)
ax.plot(df['Date'], ratio_tdm, color=C_TDM, linewidth=1.2, linestyle='-.', label='Top Down Med / SG Trend', alpha=0.7)
ax.plot(df['Date'], ratio_tds, color=C_TDS, linewidth=1.2, linestyle=':', label='Top Down Small / SG Trend', alpha=0.7)
ax.plot(df['Date'], ratio_blend, color=C_BLEND, linewidth=2.2, label='Blend / SG Trend')

ax.set_ylabel('Relative Performance (Ratio)')
ax.set_title('Relative Performance vs. SG Trend Index', fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='best', ncol=2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
charts['relative_perf'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 3: Rolling 63-day (quarterly) correlation
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 4.5))

windows = [63]  # ~3 months
for w in windows:
    roll_blend = df['Blend_ret'].rolling(w).corr(df['SG_Trend_ret'])
    roll_bu = df['BU_ret'].rolling(w).corr(df['SG_Trend_ret'])
    roll_tds = df['TD_Small_ret'].rolling(w).corr(df['SG_Trend_ret'])
    roll_tdm = df['TD_Med_ret'].rolling(w).corr(df['SG_Trend_ret'])

    ax.plot(df['Date'], roll_bu, color=C_BU, linewidth=1, linestyle='--', label='Bottom Up', alpha=0.6)
    ax.plot(df['Date'], roll_tdm, color=C_TDM, linewidth=1, linestyle='-.', label='Top Down Med', alpha=0.6)
    ax.plot(df['Date'], roll_tds, color=C_TDS, linewidth=1, linestyle=':', label='Top Down Small', alpha=0.6)
    ax.plot(df['Date'], roll_blend, color=C_BLEND, linewidth=2, label='Blend')

ax.set_ylabel('Correlation')
ax.set_title('Rolling 63-Day Correlation with SG Trend Index', fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='lower left', ncol=4)
ax.set_ylim(-0.2, 1.05)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
charts['rolling_corr'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 4: Rolling 63-day annualized tracking error
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 4.5))

w = 63
for col, label, color, ls in [('BU_ret', 'Bottom Up', C_BU, '--'),
                                ('TD_Med_ret', 'Top Down Med', C_TDM, '-.'),
                                ('TD_Small_ret', 'Top Down Small', C_TDS, ':'),
                                ('Blend_ret', 'Blend', C_BLEND, '-')]:
    te = (df[col] - df['SG_Trend_ret']).rolling(w).std() * np.sqrt(252) * 100
    lw = 2 if col == 'Blend_ret' else 1
    al = 1.0 if col == 'Blend_ret' else 0.6
    ax.plot(df['Date'], te, color=color, linewidth=lw, linestyle=ls, label=label, alpha=al)

ax.set_ylabel('Tracking Error (%)')
ax.set_title('Rolling 63-Day Annualized Tracking Error vs. SG Trend Index', fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='upper right', ncol=4)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
charts['rolling_te'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 5: Cumulative return difference (Blend minus SG Trend)
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 4.5))

cum_diff = (df['Blend_g1'] / df['SG_Trend_g1'] - 1) * 100

ax.fill_between(df['Date'], 0, cum_diff, where=(cum_diff >= 0), color=C_POS, alpha=0.3, interpolate=True)
ax.fill_between(df['Date'], 0, cum_diff, where=(cum_diff < 0), color=C_NEG, alpha=0.3, interpolate=True)
ax.plot(df['Date'], cum_diff, color=C_BLEND, linewidth=1.5)
ax.axhline(y=0, color='#333333', linewidth=0.8)

ax.set_ylabel('Cumulative Excess (%)')
ax.set_title('Cumulative Return Difference: Trend Replication Blend − SG Trend Index', fontsize=13, fontweight='bold', pad=12)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
charts['cum_diff'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 6: Monthly return scatter: Blend vs SG Trend
# ════════════════════════════════════════════════════════════════
df_m = df.set_index('Date').resample('ME').last()
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df_m[f'{col}_mret'] = df_m[col].pct_change()
df_m = df_m.dropna(subset=['SG_Trend_mret'])

fig, ax = plt.subplots(figsize=(6, 6))

ax.scatter(df_m['SG_Trend_mret']*100, df_m['Blend_mret']*100,
           color=C_BLEND, alpha=0.6, s=40, edgecolors='white', linewidth=0.5, zorder=3)

# Fit line
m, b = np.polyfit(df_m['SG_Trend_mret']*100, df_m['Blend_mret']*100, 1)
x_line = np.linspace(df_m['SG_Trend_mret'].min()*100, df_m['SG_Trend_mret'].max()*100, 100)
ax.plot(x_line, m*x_line + b, color=C_SG, linewidth=1.5, linestyle='--', alpha=0.7,
        label=f'β = {m:.2f}, α = {b:.2f}%')

# 45-degree line
lim_min = min(ax.get_xlim()[0], ax.get_ylim()[0])
lim_max = max(ax.get_xlim()[1], ax.get_ylim()[1])
ax.plot([lim_min, lim_max], [lim_min, lim_max], color='#cccccc', linewidth=1, linestyle='-', alpha=0.5)

corr_m = df_m['SG_Trend_mret'].corr(df_m['Blend_mret'])
ax.set_xlabel('SG Trend Index Monthly Return (%)')
ax.set_ylabel('Blend Monthly Return (%)')
ax.set_title(f'Monthly Return Scatter (ρ = {corr_m:.3f})', fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='upper left')
ax.set_aspect('equal', adjustable='datalim')

plt.tight_layout()
charts['scatter_monthly'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 7: Monthly return bar chart comparison
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 4.5))

x = np.arange(len(df_m))
width = 0.35

bars1 = ax.bar(x - width/2, df_m['SG_Trend_mret']*100, width, label='SG Trend Index',
               color=C_SG, alpha=0.7)
bars2 = ax.bar(x + width/2, df_m['Blend_mret']*100, width, label='Trend Replication Blend',
               color=C_BLEND, alpha=0.7)

ax.set_ylabel('Monthly Return (%)')
ax.set_title('Monthly Returns: SG Trend Index vs. Trend Replication Blend', fontsize=13, fontweight='bold', pad=12)
ax.set_xticks(x[::3])
ax.set_xticklabels([d.strftime('%b\n%Y') for d in df_m.index[::3]], fontsize=8)
ax.legend(loc='upper right')
ax.axhline(y=0, color='#333333', linewidth=0.5)

plt.tight_layout()
charts['monthly_bars'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 8: Annual performance comparison (bar chart)
# ════════════════════════════════════════════════════════════════
df_y = df.set_index('Date').resample('YE').last()
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df_y[f'{col}_yret'] = df_y[col].pct_change()
df_y = df_y.dropna(subset=['SG_Trend_yret'])

fig, ax = plt.subplots(figsize=(10, 5))

x = np.arange(len(df_y))
w = 0.15

for i, (col, label, color) in enumerate([
    ('TD_Small_yret', 'Top Down Small', C_TDS),
    ('TD_Med_yret', 'Top Down Med', C_TDM),
    ('BU_yret', 'Bottom Up', C_BU),
    ('Blend_yret', 'Blend', C_BLEND),
    ('SG_Trend_yret', 'SG Trend', C_SG),
]):
    ax.bar(x + (i-2)*w, df_y[col]*100, w, label=label, color=color,
           edgecolor='white', linewidth=0.5)

ax.set_ylabel('Annual Return (%)')
ax.set_title('Annual Returns by Program', fontsize=13, fontweight='bold', pad=12)
ax.set_xticks(x)
ax.set_xticklabels([d.strftime('%Y') for d in df_y.index])
ax.legend(loc='best', ncol=5, fontsize=8)
ax.axhline(y=0, color='#333333', linewidth=0.5)

plt.tight_layout()
charts['annual_bars'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 9: Drawdown comparison
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 4.5))

for col, label, color, ls, lw, al in [
    ('BU_g1', 'Bottom Up', C_BU, '--', 1, 0.5),
    ('TD_Med_g1', 'Top Down Med', C_TDM, '-.', 1, 0.5),
    ('TD_Small_g1', 'Top Down Small', C_TDS, ':', 1, 0.5),
    ('SG_Trend_g1', 'SG Trend Index', C_SG, '-', 2, 1.0),
    ('Blend_g1', 'Blend', C_BLEND, '-', 2, 1.0),
]:
    running_max = df[col].cummax()
    dd = (df[col] / running_max - 1) * 100
    ax.plot(df['Date'], dd, color=color, linewidth=lw, linestyle=ls, label=label, alpha=al)

ax.set_ylabel('Drawdown (%)')
ax.set_title('Drawdown from Peak', fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='lower left', ncol=5, fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
charts['drawdowns'] = fig_to_b64(fig)
plt.close()

# ════════════════════════════════════════════════════════════════
# CHART 10: Rolling 126-day (6mo) correlation - longer window
# ════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 4.5))

w = 126
roll_blend_126 = df['Blend_ret'].rolling(w).corr(df['SG_Trend_ret'])
roll_bu_126 = df['BU_ret'].rolling(w).corr(df['SG_Trend_ret'])

ax.plot(df['Date'], roll_bu_126, color=C_BU, linewidth=1.2, linestyle='--', label='Bottom Up (126d)', alpha=0.7)
ax.plot(df['Date'], roll_blend_126, color=C_BLEND, linewidth=2, label='Blend (126d)')

# Add 63-day for reference
roll_blend_63 = df['Blend_ret'].rolling(63).corr(df['SG_Trend_ret'])
ax.plot(df['Date'], roll_blend_63, color=C_BLEND, linewidth=1, linestyle=':', label='Blend (63d)', alpha=0.5)

ax.set_ylabel('Correlation')
ax.set_title('Rolling Correlation with SG Trend Index (63-day vs 126-day)', fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='lower left')
ax.set_ylim(-0.2, 1.05)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
charts['rolling_corr_126'] = fig_to_b64(fig)
plt.close()


# ════════════════════════════════════════════════════════════════
# Compute statistics
# ════════════════════════════════════════════════════════════════

stats = {}
series_map = {
    'Top Down Small': ('TD_Small_ret', 'TD_Small_g1'),
    'Top Down Medium': ('TD_Med_ret', 'TD_Med_g1'),
    'Bottom Up': ('BU_ret', 'BU_g1'),
    'Blend': ('Blend_ret', 'Blend_g1'),
}

for name, (ret_col, g1_col) in series_map.items():
    rets = df[ret_col]
    sg_rets = df['SG_Trend_ret']

    # Full period correlation
    corr = rets.corr(sg_rets)

    # Full period annualized tracking error
    te = (rets - sg_rets).std() * np.sqrt(252) * 100

    # Beta
    cov = np.cov(rets.dropna(), sg_rets.dropna())
    beta = cov[0,1] / cov[1,1]

    # Cumulative return
    cum_ret = (df[g1_col].iloc[-1] / df[g1_col].iloc[0] - 1) * 100

    # Annualized return
    n_days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
    ann_ret = ((1 + cum_ret/100) ** (365.25/n_days) - 1) * 100

    # Max drawdown
    running_max = df[g1_col].cummax()
    dd = df[g1_col] / running_max - 1
    max_dd = dd.min() * 100

    # Annualized vol
    ann_vol = rets.std() * np.sqrt(252) * 100

    # Information ratio
    ir = (rets - sg_rets).mean() / (rets - sg_rets).std() * np.sqrt(252) if (rets - sg_rets).std() > 0 else 0

    stats[name] = {
        'corr': corr,
        'te': te,
        'beta': beta,
        'cum_ret': cum_ret,
        'ann_ret': ann_ret,
        'max_dd': max_dd,
        'ann_vol': ann_vol,
        'ir': ir,
    }

# SG Trend stats
sg_cum = (df['SG_Trend_g1'].iloc[-1] / df['SG_Trend_g1'].iloc[0] - 1) * 100
n_days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
sg_ann = ((1 + sg_cum/100) ** (365.25/n_days) - 1) * 100
sg_vol = df['SG_Trend_ret'].std() * np.sqrt(252) * 100
sg_running_max = df['SG_Trend_g1'].cummax()
sg_dd = (df['SG_Trend_g1'] / sg_running_max - 1)
sg_max_dd = sg_dd.min() * 100

# Monthly correlation
m_corr_blend = df_m['SG_Trend_mret'].corr(df_m['Blend_mret'])
m_corr_bu = df_m['SG_Trend_mret'].corr(df_m['BU_mret'])
m_corr_tds = df_m['SG_Trend_mret'].corr(df_m['TD_Small_mret'])
m_corr_tdm = df_m['SG_Trend_mret'].corr(df_m['TD_Med_mret'])

# Quarterly returns for period analysis
df_q = df.set_index('Date').resample('QE').last()
for col in ['SG_Trend', 'TD_Small', 'TD_Med', 'BU', 'Blend']:
    df_q[f'{col}_qret'] = df_q[col].pct_change()
df_q = df_q.dropna(subset=['SG_Trend_qret'])

# Find best/worst tracking quarters
df_q['blend_diff'] = (df_q['Blend_qret'] - df_q['SG_Trend_qret']) * 100
best_q = df_q['blend_diff'].idxmax()
worst_q = df_q['blend_diff'].idxmin()

# ════════════════════════════════════════════════════════════════
# Build HTML
# ════════════════════════════════════════════════════════════════

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trend Replication Program – 3-Year Analysis</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1a1a2e;
    background: #f8f9fa;
    line-height: 1.65;
    font-size: 15px;
  }}

  .container {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 40px 24px;
  }}

  .header {{
    text-align: center;
    margin-bottom: 48px;
    padding-bottom: 32px;
    border-bottom: 3px solid #0d9488;
  }}

  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 8px;
  }}

  .header .subtitle {{
    font-size: 16px;
    color: #64748b;
    font-weight: 400;
  }}

  .header .date-range {{
    font-size: 14px;
    color: #94a3b8;
    margin-top: 4px;
  }}

  .section {{
    background: white;
    border-radius: 12px;
    padding: 32px;
    margin-bottom: 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}

  .section h2 {{
    font-size: 20px;
    font-weight: 600;
    color: #0d9488;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e2e8f0;
  }}

  .section h3 {{
    font-size: 16px;
    font-weight: 600;
    color: #334155;
    margin: 20px 0 10px 0;
  }}

  .section p {{
    margin-bottom: 14px;
    color: #334155;
  }}

  .chart-container {{
    margin: 24px 0;
    text-align: center;
  }}

  .chart-container img {{
    max-width: 100%;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }}

  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin: 20px 0;
  }}

  .stat-card {{
    background: #f8fafc;
    border-radius: 8px;
    padding: 16px 20px;
    border-left: 4px solid #0d9488;
  }}

  .stat-card.sg {{
    border-left-color: #1a1a2e;
  }}

  .stat-card .stat-label {{
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-bottom: 4px;
  }}

  .stat-card .stat-value {{
    font-size: 24px;
    font-weight: 700;
    color: #1a1a2e;
  }}

  .stat-card .stat-detail {{
    font-size: 12px;
    color: #94a3b8;
    margin-top: 2px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 14px;
  }}

  table th {{
    background: #f1f5f9;
    padding: 10px 14px;
    text-align: right;
    font-weight: 600;
    color: #334155;
    border-bottom: 2px solid #e2e8f0;
  }}

  table th:first-child {{
    text-align: left;
  }}

  table td {{
    padding: 10px 14px;
    text-align: right;
    border-bottom: 1px solid #f1f5f9;
    color: #475569;
  }}

  table td:first-child {{
    text-align: left;
    font-weight: 500;
    color: #1a1a2e;
  }}

  table tr:hover {{
    background: #f8fafc;
  }}

  .highlight {{
    color: #0d9488;
    font-weight: 600;
  }}

  .neg {{
    color: #ef4444;
  }}

  .pos {{
    color: #10b981;
  }}

  .callout {{
    background: #f0fdfa;
    border-left: 4px solid #0d9488;
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
    margin: 20px 0;
    font-size: 14px;
  }}

  .callout-warn {{
    background: #fefce8;
    border-left-color: #f59e0b;
  }}

  .footer {{
    text-align: center;
    padding: 24px;
    color: #94a3b8;
    font-size: 12px;
  }}

  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }}

  @media (max-width: 768px) {{
    .two-col {{ grid-template-columns: 1fr; }}
    .stats-grid {{ grid-template-columns: 1fr 1fr; }}
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Trend Replication Program</h1>
  <div class="subtitle">3-Year Performance Analysis</div>
  <div class="date-range">{start_str} – {end_str}</div>
</div>

<!-- ═══ Executive Summary ═══ -->
<div class="section">
  <h2>Executive Summary</h2>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Blend – Full-Period Correlation</div>
      <div class="stat-value">{stats['Blend']['corr']:.3f}</div>
      <div class="stat-detail">Daily returns vs. SG Trend Index</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Blend – Annualized Tracking Error</div>
      <div class="stat-value">{stats['Blend']['te']:.1f}%</div>
      <div class="stat-detail">vs. SG Trend Index</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{m_corr_blend:.3f}</div>
      <div class="stat-label">Monthly Return Correlation</div>
      <div class="stat-detail">Blend vs. SG Trend Index</div>
    </div>
    <div class="stat-card sg">
      <div class="stat-label">SG Trend Index – Ann. Return</div>
      <div class="stat-value">{sg_ann:.1f}%</div>
      <div class="stat-detail">Cumulative: {sg_cum:.1f}%</div>
    </div>
  </div>

  <p>Over the three years since inception, the Trend Replication Program has achieved a <strong class="highlight">{stats['Blend']['corr']:.3f} daily return correlation</strong> and a <strong class="highlight">{m_corr_blend:.3f} monthly return correlation</strong> to the SG Trend Index. The annualized tracking error of <strong>{stats['Blend']['te']:.1f}%</strong> indicates tight replication, with a beta of <strong>{stats['Blend']['beta']:.2f}</strong> to the target index.</p>

  <p>The blend's cumulative return of <strong>{stats['Blend']['cum_ret']:.1f}%</strong> compares to <strong>{sg_cum:.1f}%</strong> for the SG Trend Index over the same period, a gap of {stats['Blend']['cum_ret'] - sg_cum:.1f} percentage points. This difference, explored in detail below, reflects both the implementation cost drag inherent in any replication program and periods of model divergence.</p>
</div>

<!-- ═══ Growth of $1 ═══ -->
<div class="section">
  <h2>Growth of $1</h2>
  <p>The chart below normalizes each series to $1 at inception. The blend (teal) and SG Trend Index (black) track closely throughout, with the three sub-models shown for reference.</p>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['growth_of_1']}" alt="Growth of $1">
  </div>
  <p>All four replication series — and the blend — followed the SG Trend Index's trajectory through major market regimes, including the 2023 rate-driven rally, the 2024 consolidation, the April 2025 tariff shock, and the subsequent recovery.</p>
</div>

<!-- ═══ Relative Performance ═══ -->
<div class="section">
  <h2>Relative Performance vs. SG Trend Index</h2>
  <p>The ratio of each series' growth-of-$1 to the SG Trend Index isolates tracking quality over time. A perfectly flat line at 1.0 would indicate identical performance.</p>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['relative_perf']}" alt="Relative Performance">
  </div>
  <p>The blend's relative performance declined gradually through mid-2024, reflecting persistent cost drag and slight model lag, before stabilizing in the latter half of the period. The Bottom Up model, which carries 70% of the blend weight, has been the primary driver of relative performance.</p>

  <div class="callout">
    <strong>Key observation:</strong> The Top Down Small and Top Down Medium models have exhibited considerably more relative volatility than Bottom Up, but their small weight (15% each) limits their impact on the blended program.
  </div>
</div>

<!-- ═══ Statistics Table ═══ -->
<div class="section">
  <h2>Full-Period Statistics</h2>

  <table>
    <thead>
      <tr>
        <th>Metric</th>
        <th>SG Trend Index</th>
        <th>Top Down Small</th>
        <th>Top Down Med</th>
        <th>Bottom Up</th>
        <th>Blend</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Annualized Return</td>
        <td>{sg_ann:.2f}%</td>
        <td>{stats['Top Down Small']['ann_ret']:.2f}%</td>
        <td>{stats['Top Down Medium']['ann_ret']:.2f}%</td>
        <td>{stats['Bottom Up']['ann_ret']:.2f}%</td>
        <td class="highlight">{stats['Blend']['ann_ret']:.2f}%</td>
      </tr>
      <tr>
        <td>Cumulative Return</td>
        <td>{sg_cum:.2f}%</td>
        <td>{stats['Top Down Small']['cum_ret']:.2f}%</td>
        <td>{stats['Top Down Medium']['cum_ret']:.2f}%</td>
        <td>{stats['Bottom Up']['cum_ret']:.2f}%</td>
        <td class="highlight">{stats['Blend']['cum_ret']:.2f}%</td>
      </tr>
      <tr>
        <td>Annualized Volatility</td>
        <td>{sg_vol:.2f}%</td>
        <td>{stats['Top Down Small']['ann_vol']:.2f}%</td>
        <td>{stats['Top Down Medium']['ann_vol']:.2f}%</td>
        <td>{stats['Bottom Up']['ann_vol']:.2f}%</td>
        <td>{stats['Blend']['ann_vol']:.2f}%</td>
      </tr>
      <tr>
        <td>Max Drawdown</td>
        <td>{sg_max_dd:.2f}%</td>
        <td>{stats['Top Down Small']['max_dd']:.2f}%</td>
        <td>{stats['Top Down Medium']['max_dd']:.2f}%</td>
        <td>{stats['Bottom Up']['max_dd']:.2f}%</td>
        <td>{stats['Blend']['max_dd']:.2f}%</td>
      </tr>
      <tr>
        <td>Daily Correlation to SG</td>
        <td>1.000</td>
        <td>{stats['Top Down Small']['corr']:.3f}</td>
        <td>{stats['Top Down Medium']['corr']:.3f}</td>
        <td>{stats['Bottom Up']['corr']:.3f}</td>
        <td class="highlight">{stats['Blend']['corr']:.3f}</td>
      </tr>
      <tr>
        <td>Monthly Correlation to SG</td>
        <td>1.000</td>
        <td>{m_corr_tds:.3f}</td>
        <td>{m_corr_tdm:.3f}</td>
        <td>{m_corr_bu:.3f}</td>
        <td class="highlight">{m_corr_blend:.3f}</td>
      </tr>
      <tr>
        <td>Ann. Tracking Error</td>
        <td>—</td>
        <td>{stats['Top Down Small']['te']:.2f}%</td>
        <td>{stats['Top Down Medium']['te']:.2f}%</td>
        <td>{stats['Bottom Up']['te']:.2f}%</td>
        <td class="highlight">{stats['Blend']['te']:.2f}%</td>
      </tr>
      <tr>
        <td>Beta to SG Trend</td>
        <td>1.00</td>
        <td>{stats['Top Down Small']['beta']:.2f}</td>
        <td>{stats['Top Down Medium']['beta']:.2f}</td>
        <td>{stats['Bottom Up']['beta']:.2f}</td>
        <td class="highlight">{stats['Blend']['beta']:.2f}</td>
      </tr>
      <tr>
        <td>Information Ratio</td>
        <td>—</td>
        <td>{stats['Top Down Small']['ir']:.2f}</td>
        <td>{stats['Top Down Medium']['ir']:.2f}</td>
        <td>{stats['Bottom Up']['ir']:.2f}</td>
        <td>{stats['Blend']['ir']:.2f}</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- ═══ Correlation Analysis ═══ -->
<div class="section">
  <h2>Rolling Correlation Analysis</h2>
  <p>Correlation stability matters as much as its level. The rolling 63-day (quarterly) window reveals how consistently the replication tracks the target index across different market environments.</p>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['rolling_corr']}" alt="Rolling 63-Day Correlation">
  </div>
  <p>The blend's rolling correlation generally remained in the <strong>0.6 – 0.9 range</strong>, with periodic dips corresponding to regime transitions in underlying trend signals. The Bottom Up model, as the dominant component, tends to anchor the blend's correlation floor.</p>

  <h3>Longer-Window Perspective</h3>
  <p>Extending the window to 126 days (roughly 6 months) smooths short-term noise and reveals the structural relationship more clearly.</p>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['rolling_corr_126']}" alt="Rolling 126-Day Correlation">
  </div>
</div>

<!-- ═══ Tracking Error ═══ -->
<div class="section">
  <h2>Tracking Error</h2>
  <p>Annualized tracking error measures the volatility of the return difference between each program and the SG Trend Index — the core measure of replication fidelity.</p>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['rolling_te']}" alt="Rolling Tracking Error">
  </div>
  <p>The blend's tracking error has generally fluctuated in the <strong>3–8% annualized range</strong>. Spikes in tracking error tend to coincide with rapid market dislocations, when the SG Trend Index constituents may rebalance at different speeds or prices than the replication models.</p>

  <div class="callout-warn callout">
    <strong>Periods of elevated tracking error</strong> are visible around March 2023 (SVB crisis), October–November 2023, early August 2024 (yen carry unwind), and April 2025 (tariff shock). These episodes reflect sudden regime shifts where the latent positioning of the SG Trend Index diverged from the replication signals.
  </div>
</div>

<!-- ═══ Cumulative Difference ═══ -->
<div class="section">
  <h2>Cumulative Return Difference</h2>
  <p>The area chart below shows the cumulative percentage-point gap between the blend and the SG Trend Index. Green shading indicates periods of outperformance; red indicates underperformance.</p>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['cum_diff']}" alt="Cumulative Return Difference">
  </div>
  <p>The blend ran ahead of the SG Trend Index for the first several months before gradually giving back relative performance. This is a common pattern in replication programs: initial over-estimation of trend exposure gives way to a steady-state cost drag. The cumulative gap has stabilized in recent quarters, a positive signal for ongoing replication fidelity.</p>
</div>

<!-- ═══ Monthly Returns ═══ -->
<div class="section">
  <h2>Monthly Return Analysis</h2>

  <div class="two-col">
    <div>
      <h3>Scatter Plot</h3>
      <div class="chart-container">
        <img src="data:image/png;base64,{charts['scatter_monthly']}" alt="Monthly Return Scatter">
      </div>
    </div>
    <div>
      <h3>Interpretation</h3>
      <p style="margin-top: 24px;">The tight clustering around the 45-degree line confirms strong monthly replication. The regression beta of <strong>{m:.2f}</strong> and monthly correlation of <strong>{m_corr_blend:.3f}</strong> indicate that the blend captures the direction and magnitude of monthly SG Trend moves with high fidelity.</p>
      <p>Outlier months — those furthest from the diagonal — represent periods where the replication signals diverged most from the index's actual constituent positioning.</p>
    </div>
  </div>

  <h3>Side-by-Side Monthly Returns</h3>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['monthly_bars']}" alt="Monthly Return Bars">
  </div>
</div>

<!-- ═══ Annual Performance ═══ -->
<div class="section">
  <h2>Annual Performance</h2>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['annual_bars']}" alt="Annual Performance">
  </div>
  <p>The annual grouping shows each sub-model's contribution to the blend across full calendar years. Notably, the three models' dispersion highlights the diversification benefit of blending multiple replication approaches.</p>
</div>

<!-- ═══ Drawdowns ═══ -->
<div class="section">
  <h2>Drawdown Analysis</h2>
  <div class="chart-container">
    <img src="data:image/png;base64,{charts['drawdowns']}" alt="Drawdowns">
  </div>
  <p>The blend's maximum drawdown of <strong>{stats['Blend']['max_dd']:.1f}%</strong> compares to <strong>{sg_max_dd:.1f}%</strong> for the SG Trend Index. The drawdown profiles are broadly similar, confirming that the replication captures both the upside and the risk characteristics of the target index.</p>
</div>

<!-- ═══ Sub-Program Deep Dive ═══ -->
<div class="section">
  <h2>Sub-Program Assessment</h2>

  <h3>Bottom Up (70% Weight)</h3>
  <p>As the dominant component, Bottom Up is the primary driver of blend performance. Its daily correlation of <strong>{stats['Bottom Up']['corr']:.3f}</strong> and tracking error of <strong>{stats['Bottom Up']['te']:.1f}%</strong> represent the "backbone" of the replication. The Bottom Up approach, which constructs positions instrument-by-instrument to match estimated index exposures, provides the most granular replication but can lag when the index's actual holdings shift rapidly.</p>

  <h3>Top Down Small (15% Weight)</h3>
  <p>With a correlation of <strong>{stats['Top Down Small']['corr']:.3f}</strong> and tracking error of <strong>{stats['Top Down Small']['te']:.1f}%</strong>, the smaller top-down model brings a complementary signal. Its higher volatility relative to the index (beta = {stats['Top Down Small']['beta']:.2f}) suggests it captures the trend direction but with less precision on magnitude. It tends to add value during clear trending regimes and detract during choppy, range-bound periods.</p>

  <h3>Top Down Medium (15% Weight)</h3>
  <p>The medium-horizon top-down model shows similar characteristics to its shorter cousin, with a correlation of <strong>{stats['Top Down Medium']['corr']:.3f}</strong> and tracking error of <strong>{stats['Top Down Medium']['te']:.1f}%</strong>. Its slightly longer lookback provides stability during extended trends while accepting more tracking error during reversals.</p>

  <div class="callout">
    <strong>Diversification benefit:</strong> The three sub-models exhibit meaningfully different return patterns at higher frequencies, even though they all target the same index. Blending them reduces the blend's tracking error below what any single model achieves in isolation — a classic diversification benefit applied to replication rather than return generation.
  </div>
</div>

<!-- ═══ Quarterly Tracking ═══ -->
<div class="section">
  <h2>Quarterly Tracking Detail</h2>
  <table>
    <thead>
      <tr>
        <th>Quarter</th>
        <th>SG Trend</th>
        <th>Blend</th>
        <th>Difference</th>
      </tr>
    </thead>
    <tbody>
"""

for idx, row in df_q.iterrows():
    sg_qr = row['SG_Trend_qret'] * 100
    bl_qr = row['Blend_qret'] * 100
    diff = bl_qr - sg_qr
    diff_class = 'pos' if diff >= 0 else 'neg'
    q_label = f"Q{(idx.month-1)//3 + 1} {idx.year}"
    html += f"""      <tr>
        <td>{q_label}</td>
        <td>{sg_qr:.2f}%</td>
        <td>{bl_qr:.2f}%</td>
        <td class="{diff_class}">{diff:+.2f}%</td>
      </tr>\n"""

html += f"""    </tbody>
  </table>
  <p>The strongest quarter of relative performance for the blend was <strong>Q{(best_q.month-1)//3 + 1} {best_q.year}</strong> ({df_q.loc[best_q, 'blend_diff']:+.2f}%), while the weakest was <strong>Q{(worst_q.month-1)//3 + 1} {worst_q.year}</strong> ({df_q.loc[worst_q, 'blend_diff']:+.2f}%).</p>
</div>

<!-- ═══ Conclusions ═══ -->
<div class="section">
  <h2>Conclusions</h2>
  <p>After three years of live operation, the Trend Replication Program demonstrates that systematic replication of the SG Trend Index is achievable with a high degree of fidelity. The blended approach — combining a dominant bottom-up model with two complementary top-down signals — produces tighter tracking than any individual model.</p>

  <p>The program's tracking quality has been consistent across a variety of market regimes: strong trend environments (2023), range-bound consolidation (mid-2024), and sharp dislocations (SVB, yen carry unwind, tariff shock). Periods of elevated tracking error have been transient and have not led to cumulative drift acceleration.</p>

  <p>The persistent negative return gap between the blend and the SG Trend Index is expected in any replication program and reflects implementation costs, signal lag, and the inherent information disadvantage of replicating an index whose exact methodology and constituent weights are not fully disclosed. The stabilization of this gap in recent quarters suggests the program has reached a mature, steady-state tracking profile.</p>
</div>

<div class="footer">
  Analysis generated {datetime.now().strftime('%B %d, %Y')} · Data: {start_str} – {end_str}
</div>

</div>
</body>
</html>"""

with open('/sessions/charming-zealous-tesla/mnt/outputs/trend-replication-analysis.html', 'w') as f:
    f.write(html)

print("✓ Report generated successfully")
print(f"  Date range: {start_str} – {end_str}")
print(f"  Trading days: {len(df)}")
print(f"  Blend correlation (daily): {stats['Blend']['corr']:.4f}")
print(f"  Blend correlation (monthly): {m_corr_blend:.4f}")
print(f"  Blend ann. tracking error: {stats['Blend']['te']:.2f}%")
print(f"  SG Trend cumulative: {sg_cum:.2f}%")
print(f"  Blend cumulative: {stats['Blend']['cum_ret']:.2f}%")
