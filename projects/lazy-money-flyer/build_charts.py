"""
Lazy Money Flyer -- Chart Generation
Recreates annual returns bar chart and correlation heatmap
using ReSolve AM brand style.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

# ---------------------------------------------------------------------------
# Brand setup
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent.parent
BRAND_DIR = REPO / "references" / "brand-assets" / "resolve-am"
OUT_DIR = Path(__file__).resolve().parent / "chart_exports"
OUT_DIR.mkdir(exist_ok=True)

# Load fonts
for otf in (BRAND_DIR / "Fonts").glob("*.otf"):
    fm.fontManager.addfont(str(otf))
for otf in (BRAND_DIR / "Fonts" / "Helvetica Neue LT Std").glob("*.otf"):
    fm.fontManager.addfont(str(otf))

plt.style.use(str(BRAND_DIR / "matplotlib" / "resolve.mplstyle"))

# RAM brand colors
BLUE = "#00478D"
AMBER = "#FBBA00"
BLACK = "#000000"
NAVY = "#032F69"
SKY = "#89D2FF"
WHITE = "#FFFFFF"
DARK_GRAY = "#333333"

# ---------------------------------------------------------------------------
# Chart A: Annual Returns Grouped Bar Chart
# ---------------------------------------------------------------------------
def build_annual_returns():
    periods = ["2021", "2022", "2023", "2024", "2025", "2026", "Annualized\nReturn"]
    carry =   [3.1,   8.5,   6.7,   22.5,  -3.2,  15.5,  11.1]
    bonds =   [-1.0, -13.0,  5.7,    1.3,   7.2,  -2.2,  -0.3]
    equities = [2.5, -18.4, 22.3,   17.5,  22.4,   0.0,   8.1]

    x = np.arange(len(periods))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 5.5))

    bars_carry = ax.bar(x - width, carry, width, color=BLUE, label="ReSolve Carry (Excess Returns)", zorder=3)
    bars_bonds = ax.bar(x, bonds, width, color=AMBER, label="Bonds", zorder=3)
    bars_eq = ax.bar(x + width, equities, width, color=BLACK, label="Global Equities", zorder=3)

    # Zero line
    ax.axhline(y=0, color=DARK_GRAY, linewidth=0.8, zorder=2)

    # Data labels
    def add_labels(bars, values):
        for bar, val in zip(bars, values):
            y = bar.get_height()
            offset = 0.8 if val >= 0 else -0.8
            va = "bottom" if val >= 0 else "top"
            # Determine text color based on contrast
            text_color = DARK_GRAY
            label = f"{val:.1f}%"
            # Drop the leading zero for -0.3%
            ax.annotate(label, xy=(bar.get_x() + bar.get_width() / 2, y),
                        xytext=(0, 3 if val >= 0 else -3), textcoords="offset points",
                        ha="center", va=va, fontsize=8, fontweight="medium",
                        color=text_color)

    add_labels(bars_carry, carry)
    add_labels(bars_bonds, bonds)
    add_labels(bars_eq, equities)

    # Axes
    ax.set_xticks(x)
    ax.set_xticklabels(periods, fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.set_ylabel("")

    # Legend -- horizontal across the top
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=3,
              fontsize=10, frameon=False)

    # Add visual separator before "Annualized Return"
    ax.axvline(x=5.5, color="#E0E0E0", linewidth=1, linestyle="--", zorder=1)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "annual_returns.png", dpi=150)
    fig.savefig(OUT_DIR / "annual_returns.pdf")
    plt.close(fig)
    print(f"Saved annual_returns.png and .pdf to {OUT_DIR}")


# ---------------------------------------------------------------------------
# Chart B: Correlation Heatmap (Reimagined)
# ---------------------------------------------------------------------------
def build_correlation_heatmap():
    labels = ["ReSolve Carry\n(Excess Returns)", "Bonds", "Global Equities"]
    data = np.array([
        [1.00, -0.22, -0.14],
        [-0.22, 1.00,  0.94],
        [-0.14, 0.94,  1.00],
    ])

    # Custom diverging colormap from RAM blues
    # Light (low correlation) -> Deep navy (high correlation)
    cmap = LinearSegmentedColormap.from_list("ram_corr", [
        "#FFFFFF",   # white (0 / no correlation)
        SKY,         # sky blue (mid)
        BLUE,        # brand blue (strong)
        NAVY,        # deep navy (perfect)
    ])

    fig, ax = plt.subplots(figsize=(6, 5))

    # Use absolute values for color mapping (symmetric diverging)
    im = ax.imshow(np.abs(data), cmap=cmap, vmin=0, vmax=1, aspect="equal")

    # Annotations
    for i in range(3):
        for j in range(3):
            val = data[i, j]
            # White text on dark cells, dark on light
            abs_val = abs(val)
            text_color = WHITE if abs_val > 0.5 else DARK_GRAY
            fontweight = "bold" if i == j else "medium"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=14, fontweight=fontweight, color=text_color)

    # Axes
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(labels, fontsize=10, ha="center")
    ax.set_yticklabels(labels, fontsize=10)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Remove ticks
    ax.tick_params(top=False, bottom=False, left=False, right=False)

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.08)
    cbar.set_label("Pearson Correlation (absolute)", fontsize=9)
    cbar.ax.tick_params(labelsize=9)

    # Title
    ax.set_title("Correlation Matrix", fontsize=14, fontweight="bold",
                 color=BLUE, pad=15)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "correlation_heatmap.png", dpi=150)
    fig.savefig(OUT_DIR / "correlation_heatmap.pdf")
    plt.close(fig)
    print(f"Saved correlation_heatmap.png and .pdf to {OUT_DIR}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    build_annual_returns()
    build_correlation_heatmap()
    print("Done.")
