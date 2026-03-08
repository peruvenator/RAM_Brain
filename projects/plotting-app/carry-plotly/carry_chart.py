"""
Carry Scatter Plot — Risk-Adjusted Carry Score vs. Risk-Adjusted Target Weight
Reproduces the branded scatter chart from the reference image using Plotly.
"""

import openpyxl
import plotly.graph_objects as go

# ── Brand colors ──────────────────────────────────────────────────────────────
TEXT_PRIMARY = "#2c3641"
TEXT_SECONDARY = "#625c6d"
TEAL_PRIMARY = "#14cfa6"
BLUE_SECONDARY = "#3a6a9c"
BLUE_LIGHT = "#7da5ce"
YELLOW = "#ebe96a"

# Asset-class color mapping (matching the reference image)
CLASS_COLORS = {
    "Bonds": TEAL_PRIMARY,
    "Equities": TEXT_PRIMARY,
    "Energies": "#8bc34a",       # bright green from image
    "Metals": YELLOW,
    "Currencies": BLUE_LIGHT,
}

# ── Load data ─────────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook("Sample Carry Data.xlsx", data_only=True)
ws = wb["Sheet1"]

rows = list(ws.iter_rows(min_row=2, values_only=True))  # skip header

records = []
for row in rows:
    name = row[0]
    carry = row[1]          # Risk-Adjusted Carry Score (col B)
    # Target weight is in the asset-class-specific column (C–G)
    bond_w, eq_w, energy_w, metal_w, ccy_w = row[2], row[3], row[4], row[5], row[6]

    if bond_w is not None:
        cls = "Bonds"
        weight = bond_w
    elif eq_w is not None:
        cls = "Equities"
        weight = eq_w
    elif energy_w is not None:
        cls = "Energies"
        weight = energy_w
    elif metal_w is not None:
        cls = "Metals"
        weight = metal_w
    elif ccy_w is not None:
        cls = "Currencies"
        weight = ccy_w
    else:
        continue

    records.append({"name": name, "carry": carry, "weight": weight, "class": cls})

# ── Build traces (one per asset class for legend) ────────────────────────────
fig = go.Figure()

for cls in ["Bonds", "Equities", "Energies", "Metals", "Currencies"]:
    subset = [r for r in records if r["class"] == cls]
    fig.add_trace(go.Scatter(
        x=[r["carry"] for r in subset],
        y=[r["weight"] for r in subset],
        mode="markers",
        name=cls,
        marker=dict(
            color=CLASS_COLORS[cls],
            size=10,
            line=dict(width=0.5, color="rgba(0,0,0,0.15)"),
        ),
        text=[r["name"] for r in subset],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Carry Score: %{x:.2f}<br>"
            "Target Weight: %{y:.2%}<extra></extra>"
        ),
    ))

# ── Layout ────────────────────────────────────────────────────────────────────
fig.update_layout(
    width=900,
    height=530,
    margin=dict(l=80, r=100, t=60, b=80),
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="DM Sans, sans-serif", color=TEXT_SECONDARY, size=12),

    # X axis
    xaxis=dict(
        title=dict(
            text="Risk-Adjusted Carry Score",
            font=dict(size=13, color=TEXT_SECONDARY),
            standoff=15,
        ),
        range=[-0.65, 0.65],
        dtick=0.2,
        tickformat=".1f",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor=TEXT_PRIMARY,
        gridcolor="rgba(0,0,0,0.06)",
        tickfont=dict(size=11, color=TEXT_SECONDARY),
    ),

    # Y axis
    yaxis=dict(
        title=dict(
            text="Risk-Adjusted Target Weight",
            font=dict(size=13, color=TEXT_SECONDARY),
            standoff=10,
        ),
        range=[-0.04, 0.03],
        dtick=0.01,
        tickformat=".0%",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor=TEXT_PRIMARY,
        gridcolor="rgba(0,0,0,0.06)",
        tickfont=dict(size=11, color=TEXT_SECONDARY),
    ),

    # Legend
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="center",
        x=0.45,
        font=dict(size=11, color=TEXT_SECONDARY),
        itemsizing="constant",
    ),
)

# ── Annotations ───────────────────────────────────────────────────────────────

# Top banner: "Negative Carry" ← → "Positive Carry"
fig.add_annotation(
    x=0.25, y=1.08, xref="paper", yref="paper",
    text="<b>Negative Carry</b>",
    showarrow=False,
    font=dict(size=12, color=TEXT_SECONDARY),
)
fig.add_annotation(
    x=0.75, y=1.08, xref="paper", yref="paper",
    text="<b>Positive Carry</b>",
    showarrow=False,
    font=dict(size=12, color=TEXT_SECONDARY),
)
# Arrow lines (using shapes since Plotly v6 doesn't support axref="paper")
fig.add_shape(
    type="line",
    x0=0.05, y0=1.08, x1=0.20, y1=1.08,
    xref="paper", yref="paper",
    line=dict(color=TEXT_SECONDARY, width=1.5),
)
fig.add_annotation(
    x=0.05, y=1.08, xref="paper", yref="paper",
    text="\u25C0", showarrow=False,
    font=dict(size=8, color=TEXT_SECONDARY),
)
fig.add_shape(
    type="line",
    x0=0.80, y0=1.08, x1=0.95, y1=1.08,
    xref="paper", yref="paper",
    line=dict(color=TEXT_SECONDARY, width=1.5),
)
fig.add_annotation(
    x=0.95, y=1.08, xref="paper", yref="paper",
    text="\u25B6", showarrow=False,
    font=dict(size=8, color=TEXT_SECONDARY),
)

# Right-side vertical labels: "Positive Weight" / "Negative Weight"
fig.add_annotation(
    x=1.07, y=0.75, xref="paper", yref="paper",
    text="<b>Positive Weight</b>",
    showarrow=False,
    textangle=90,
    font=dict(size=11, color=TEAL_PRIMARY),
)
fig.add_annotation(
    x=1.07, y=0.25, xref="paper", yref="paper",
    text="<b>Negative Weight</b>",
    showarrow=False,
    textangle=90,
    font=dict(size=11, color=TEXT_SECONDARY),
)

# Callout: upper-left quadrant
fig.add_annotation(
    x=-0.35, y=0.025,
    text=(
        "Some positions with negative<br>"
        "carry are held long to hedge<br>"
        "portfolio risks."
    ),
    showarrow=False,
    font=dict(size=10, color=TEXT_SECONDARY),
    align="left",
    bgcolor="rgba(255,255,255,0.7)",
)

# Callout: right side — energies
fig.add_annotation(
    x=0.42, y=-0.010,
    text=(
        "Strong carry in energies<br>"
        "leads to a net long in the<br>"
        "sector"
    ),
    showarrow=False,
    font=dict(size=10, color=TEXT_SECONDARY),
    align="left",
    bgcolor="rgba(255,255,255,0.7)",
)

# Callout: bottom center
fig.add_annotation(
    x=-0.05, y=-0.032,
    text=(
        "With most assets<br>"
        "exhibiting negative carry,<br>"
        "the portfolio is net short."
    ),
    showarrow=False,
    font=dict(size=10, color=TEXT_SECONDARY),
    align="left",
    bgcolor="rgba(255,255,255,0.7)",
)

# Disclaimer
fig.add_annotation(
    x=1.0, y=-0.25, xref="paper", yref="paper",
    text="<i>For illustrative purposes only.</i>",
    showarrow=False,
    font=dict(size=10, color=TEXT_SECONDARY),
    xanchor="right",
)

# ── Export ────────────────────────────────────────────────────────────────────
fig.write_image("carry_scatter.png", scale=2)
fig.write_html("carry_scatter.html")
print("Saved carry_scatter.png and carry_scatter.html")
