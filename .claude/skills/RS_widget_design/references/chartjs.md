# Chart.js Conventions

Chart.js v4 configuration defaults and per-chart-type recipes for RS widgets. All charts inherit these settings unless a specific section overrides them.

---

## Setup

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
```

Chart container: relatively positioned div with explicit height (420px desktop, 280px mobile):
```html
<div class="rsw-chart-area">
  <div class="rsw-chart-container">
    <canvas id="my-chart"></canvas>
  </div>
</div>
```

```css
.rsw-chart-container {
  padding: 16px;
  position: relative;
  height: 420px;
}
```

Chart init options:
```javascript
responsive: true,
maintainAspectRatio: false,
```

---

## Global Defaults

Set once per widget, after Chart.js loads:

```javascript
if (window.Chart) {
  Chart.defaults.font.family = '"DM Sans", sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.color = '#555';
  Chart.defaults.animation = { duration: 300, easing: 'easeOutCubic' };
}
```

---

## Dataset Defaults (line charts)

```javascript
{
  borderColor: '#2a3f5b',                          // full-strength line color
  backgroundColor: 'rgba(42, 63, 91, 0.25)',       // ~25% alpha of the line color
  borderWidth: 2.5,
  fill: false,
  tension: 0.1,
  pointRadius: 0,
  pointHitRadius: 8,
  pointBorderColor: '#2a3f5b',                     // matches borderColor
  pointBackgroundColor: 'rgba(42, 63, 91, 0.25)',  // matches backgroundColor
}
```

**Legend icon convention — dark ring, light interior.** With `pointStyle: 'circle'` and `usePointStyle: true`, Chart.js renders the legend swatch using `borderColor` for the outline and `backgroundColor` for the fill. The 0.25 alpha on `backgroundColor` gives a visible ring-and-fill look in the legend without muddying the plot (since the line itself uses `fill: false`).

If `fill: true` for an area fill, drop alpha to ~0.12 — but the legend swatch interior will be faint.

For **bar** and **scatter** datasets, `backgroundColor` fills both the bars/points and the legend circle, so use full-strength color for both.

---

## Plugin Defaults

```javascript
plugins: {
  legend: {
    labels: {
      font: { family: 'DM Sans', size: 13, weight: 600 },
      usePointStyle: true,
      pointStyle: 'circle',
      boxWidth: 10,
      boxHeight: 10,
      padding: 20,
    }
  },
  tooltip: {
    mode: 'index',
    intersect: false,
    backgroundColor: 'rgba(42,63,91,0.95)',
    titleFont: { family: 'DM Sans', size: 13 },
    bodyFont: { family: 'DM Sans', size: 13 },
    padding: 12,
    cornerRadius: 8,
  }
}
```

---

## Axis Defaults

```javascript
scales: {
  x: {
    type: 'category',
    ticks: {
      font: { family: 'DM Sans', size: 11 },
      color: '#555',
      maxTicksLimit: 12,
    },
    grid: { display: false },
    border: { color: '#000', width: 1.5 },
  },
  y: {
    ticks: { font: { family: 'DM Sans', size: 11 }, color: '#555' },
    grid: { color: '#f0f0f0' },
    border: { color: '#000', width: 1.5 },
    title: {
      font: { family: 'DM Sans', size: 12, weight: 600 },
      color: '#555',
    },
  },
}

layout: { padding: { left: 10 } }
```

**Bold x and y axis border lines** (`#000`, 1.5px) give charts a strong editorial frame. Gridlines stay subtle (`#f0f0f0` horizontal only).

---

## Time-Series X-Axis Formatting

When labels are ISO dates (e.g. `2024-03-31`), reformat to `MM/YYYY` and force 35° rotation so label density doesn't toggle:

```javascript
x: {
  type: 'category',
  ticks: {
    maxRotation: 35,
    minRotation: 35,
    autoSkip: true,
    maxTicksLimit: 12,
    callback: function(v) {
      const l = this.getLabelForValue(v);
      if (!l) return '';
      const parts = l.split('-');
      return parts.length >= 2 ? parts[1] + '/' + parts[0] : l.substring(0, 4);
    },
  },
  grid: { display: false },
}
```

Apply to: growth-of-$1, drawdown, rolling returns, rolling correlation charts.

**Do NOT apply to calendar-year bar charts** — labels are already `YYYY` strings. Use 45° rotation without the callback.

---

## Color Assignments (multi-line charts)

Order consistently:

1. `#2a3f5b` navy — benchmark / primary reference
2. `#60cca8` accent-green — secondary / alternative strategy
3. `#3a6a9c` / `#7da5ce` steel blue — stacking / lump-sum variant
4. `#8896ab` slate — funding / tranche variant
5. Muted supplementary palette: `#14cfa6`, `#f5a623`, `#e06d5e`, `#d4af37`

**Bar chart segments** (portfolio allocation visuals):
- Stocks: `#456998` muted steel blue
- Bonds: `#7da5ce` lighter complement
- Alt segments: `#14cfa6` (teal), `#f5a623` (amber), `#e06d5e` (coral), `#d4af37` (gold)

---

## Line Chart Recipes

### Growth of $1
- Primary line: navy, `fill: false`
- Secondary/accent line: accent-green, optional gradient fill from `rgba(96,204,168,0.25)` to `rgba(96,204,168,0.02)`
- $100 reference line (or $1 baseline):
  ```javascript
  annotation: {
    annotations: {
      base: { type: 'line', yMin: 1, yMax: 1, borderColor: '#000', borderWidth: 1 }
    }
  }
  ```
- Log scale toggle: swap y-axis `type: 'linear'` ↔ `type: 'logarithmic'`

### Drawdown
- Navy primary, red fill below zero
- Y-axis formatted as percent
- Zero baseline annotation

### Rolling Returns
- Blue/red shaded difference chart (outperformance vs underperformance)
- Debounced 150ms slider for period length
- Summary text below chart: "Stacked portfolio outperformed the Core portfolio in 68% of rolling 36-month periods"

### Rolling Correlation
- Debounced lookback slider
- Y-axis clamped `-1` to `1`

### Calendar Year Returns
- Grouped bars (Core vs Stacked)
- Outperformance streak highlights
- 45° rotation on x-axis (no callback)

### Scatter (Return vs Risk)
- `pointRadius: 6`, `pointHoverRadius: 8`
- 10% padding on axes (compute `min`/`max` with `* 0.9` / `* 1.1`)
- Benchmark frontier line underlying the points

---

## Annotations

| Type | Style |
|---|---|
| Zero/baseline reference | `borderColor: '#000'`, `borderWidth: 1`, solid |
| Event marker (vertical) | `borderColor: '#999'`, `borderDash: [6, 4]`, label `position: 'start'` or `'end'` |
| Alternative scenario line | `borderDash: [8, 4]` on the dataset itself |

---

## Null / Partial Lines

To start a line partway through a chart: fill leading values with `null`:
```javascript
data: [null, null, null, 100, 102, 105, ...]
```
Chart.js will render the line starting at the first non-null index.

---

## Destroying and Rebuilding

When date range changes, tab changes, or slider drags trigger a rebuild, destroy the existing instance first:

```javascript
if (chart) chart.destroy();
chart = new Chart(ctx, { ... });
```

Otherwise memory leaks and phantom tooltips accumulate.

---

## Debouncing Interactive Inputs

Wrap chart-rebuild calls in a debounce for slider drags:

```javascript
function debounce(fn, ms) {
  var t;
  return function () {
    var args = arguments, ctx = this;
    clearTimeout(t);
    t = setTimeout(function () { fn.apply(ctx, args); }, ms);
  };
}

var recompute = debounce(renderChart, 150);
slider.addEventListener('input', recompute);
```

Standard debounce times:
- 150ms for chart re-renders (rolling window, lookback)
- 500ms for full portfolio recomputes
- 0ms for pill toggles, tab switches (instant)
