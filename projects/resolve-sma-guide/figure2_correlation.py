"""
Figure 2 from "Why Bonds Still Belong" blog post.
Rolling 12-Month Correlation between U.S. Stocks and U.S. Bonds.
Data extracted via extract-chart-data skill.
Return Stacked brand guidelines.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import textwrap
from matplotlib.ticker import FuncFormatter
from pathlib import Path

# ── Brand setup ──────────────────────────────────────────────────────────
REPO = Path(r"c:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\references\brand-assets")
BRAND_DIR = REPO / "return-stacked"

for ttf in (BRAND_DIR / "Font_Family").glob("*.ttf"):
    fm.fontManager.addfont(str(ttf))

plt.style.use(str(BRAND_DIR / "matplotlib" / "return_stacked.mplstyle"))

BLUE_SEC = "#3a6a9c"
RED_NEG = "#C00000"

# ── Load extracted data ──────────────────────────────────────────────────
DATA_PATH = Path(r"c:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\resolve-sma-guide\extracted_chart_data.json")
with open(DATA_PATH) as f:
    charts = json.load(f)

chart = charts[1]  # Figure 2
title = chart["title"]
disclaimer = chart["disclaimer"]
rows = chart["data"]["rows"]

df = pd.DataFrame(rows, columns=["Date", "Correlation"])
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

# ── Plot ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 5))

# Main line
ax.plot(df["Date"], df["Correlation"], color=BLUE_SEC, linewidth=1.5)

# Fill above/below zero
ax.fill_between(df["Date"], df["Correlation"], 0,
                where=(df["Correlation"] >= 0),
                color=BLUE_SEC, alpha=0.08, interpolate=True)
ax.fill_between(df["Date"], df["Correlation"], 0,
                where=(df["Correlation"] < 0),
                color=RED_NEG, alpha=0.08, interpolate=True)

# Zero reference line
ax.axhline(0, color="#333333", linewidth=0.75, linestyle="-", zorder=1)

# Y-grid only
ax.yaxis.grid(True, color="#A7A7A7", linewidth=0.225)
ax.xaxis.grid(False)

# Axis formatting
ax.set_ylabel("Correlation", fontsize=13, fontweight="medium", labelpad=10)
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.1f}"))

# Rotated x-ticks
ax.tick_params(axis="x", rotation=45)
for label in ax.get_xticklabels():
    label.set_ha("right")
    label.set_rotation_mode("anchor")

# Y limits with padding
ax.set_ylim(-1.0, 1.0)

# Title (strip "Figure N: " prefix)
import re
clean_title = re.sub(r"^Figure\s+\d+\s*:\s*", "", title)
ax.set_title(clean_title, fontsize=14, fontweight="bold", color="#323a46", pad=12)

# Disclaimer: left-justified, one size smaller than body text (11pt -> 10pt)
fig.text(0.02, -0.02, disclaimer,
         ha="left", fontsize=10, color="#888888", style="italic",
         wrap=True, transform=fig.transFigure)

fig.tight_layout(rect=[0, 0.06, 1, 1])

# ── Save ─────────────────────────────────────────────────────────────────
output_dir = Path(r"c:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\resolve-sma-guide")
fig.savefig(output_dir / "figure2_correlation.png", dpi=300, facecolor="white")
fig.savefig(output_dir / "figure2_correlation.pdf", facecolor="white")
print(f"Saved to {output_dir / 'figure2_correlation.png'}")
plt.close(fig)
