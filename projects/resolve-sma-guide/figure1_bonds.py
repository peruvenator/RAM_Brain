"""
Recreate Figure 1 from "Why Bonds Still Belong" blog post.
Rolling 5-Year Annualized Returns of U.S. Bonds
Data source: Rolling_5-Year_Annualized_Returns.xlsx (Bloomberg US Agg)
Using Return Stacked brand guidelines.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter
from pathlib import Path

# ── Brand setup ──────────────────────────────────────────────────────────
REPO = Path(r"c:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\references\brand-assets")
BRAND_DIR = REPO / "return-stacked"

for ttf in (BRAND_DIR / "Font_Family").glob("*.ttf"):
    fm.fontManager.addfont(str(ttf))

plt.style.use(str(BRAND_DIR / "matplotlib" / "return_stacked.mplstyle"))

# ── Brand colors ─────────────────────────────────────────────────────────
BLUE_SEC = "#3a6a9c"
RED_NEG = "#C00000"

# ── Load data ────────────────────────────────────────────────────────────
DATA_PATH = Path(r"C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\Downloads RG\Rolling_5-Year_Annualized_Returns.xlsx")
raw = pd.read_excel(DATA_PATH)

# Columns 2-3 have the rolling 5-year return series (dates + decimals)
df = raw[["Unnamed: 2", "Unnamed: 3"]].dropna().copy()
df.columns = ["Date", "Return"]
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

# Convert to percentage for display
df["Return_pct"] = df["Return"] * 100

# ── Plot ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 5))

# Main line
ax.plot(df["Date"], df["Return_pct"], color=BLUE_SEC, linewidth=2.0)

# Fill above/below zero
ax.fill_between(df["Date"], df["Return_pct"], 0,
                where=(df["Return_pct"] >= 0),
                color=BLUE_SEC, alpha=0.08, interpolate=True)
ax.fill_between(df["Date"], df["Return_pct"], 0,
                where=(df["Return_pct"] < 0),
                color=RED_NEG, alpha=0.08, interpolate=True)

# Zero reference line
ax.axhline(0, color="#333333", linewidth=0.75, linestyle="-", zorder=1)

# Y-grid only
ax.yaxis.grid(True, color="#A7A7A7", linewidth=0.225)
ax.xaxis.grid(False)

# Axis formatting
ax.set_ylabel("Annualized Return (%)", fontsize=13, fontweight="medium", labelpad=10)
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0f}%"))

# Rotated x-ticks
ax.tick_params(axis="x", rotation=45)
for label in ax.get_xticklabels():
    label.set_ha("right")
    label.set_rotation_mode("anchor")

# Y limits with padding
ax.set_ylim(-2.5, 9.5)

# Title (descriptive text only, no "Figure N:" prefix)
ax.set_title(
    "Rolling 5-Year Annualized Returns of U.S. Bonds",
    fontsize=14, fontweight="bold", color="#323a46", pad=12,
)

# Disclaimer: left-justified, one size smaller than body text (11pt -> 10pt)
disclaimer = (
    "Source: Bloomberg. U.S. Bonds are the Bloomberg U.S. Aggregate Bond Index (LBUSTRUU). "
    "Index returns are gross of all fees, taxes, and transaction costs. "
    "You cannot invest in an index. Past performance is not indicative of future results."
)
fig.text(0.02, -0.02, disclaimer,
         ha="left", fontsize=10, color="#888888", style="italic",
         wrap=True, transform=fig.transFigure)

fig.tight_layout(rect=[0, 0.06, 1, 1])

# ── Save ─────────────────────────────────────────────────────────────────
output_dir = Path(r"c:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\resolve-sma-guide")
fig.savefig(output_dir / "figure1_rolling_5yr_bond_returns.png", dpi=300, facecolor="white")
fig.savefig(output_dir / "figure1_rolling_5yr_bond_returns.pdf", facecolor="white")
print(f"Saved to {output_dir / 'figure1_rolling_5yr_bond_returns.png'}")
plt.close(fig)
