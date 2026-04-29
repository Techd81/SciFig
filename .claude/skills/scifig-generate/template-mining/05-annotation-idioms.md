# In-axes Annotation Idioms

The annotation patterns used **inside** plot axes across the 77 cases. These are the "顶刊感" multipliers that turn a base chart into an evidence layer. Phase 3 should apply at least 2-3 of these per chart family.

## Frequency table (regex-verified, n=77)

| Idiom | Cases | Phase 3 priority |
|---|---|---|
| `alpha_layered_scatter` (alpha + zorder ≥ 2 layers) | 24 | universal — always |
| `group_divider_axvline` (dashed gray group splits) | 14 | bar/dual-axis with category groups |
| `density_color_scatter` (KDE-derived c=) | 14 | scatter with > 12 points |
| `raincloud_combo` (jitter + box + half-violin) | 13 | distribution comparison |
| `metric_text_box` (R²/RMSE in transAxes box) | 9 | predicted-vs-actual scatter |
| `axes_inset_overlay` | 8 | hero panel needs zoom/distribution |
| `dotted_zero_axhline` (zero ref for ALE/diff) | 8 | ALE / SHAP / differential |
| `pvalue_stars_overlay` | 7 | comparison with supplied p-values |
| `colored_marker_edge` (`edgecolor='white'`) | 7 | scatter with color encoding |
| `twin_axes_color_spines` | 6 | dual-axis combo |
| `error_band_fill_between` (alpha 0.15–0.4) | 5 | regression / time-series PI |
| `marginal_axes_grid` (top/right marginals) | 5 | density scatter + diagnostic |
| `category_split_dashed` | 4 | grouped bars |
| `dual_y_bar_line` (bar on left axis, line on right) | 4 | dual-axis combo |
| `imshow_gradient_box` (gradient fill via imshow) | 4 | gradient box plot |
| `ridgeline_offset_kde` | 2 | distribution stack |
| `upper_triangle_split` | 2 | n×n pairwise matrix |
| `perfect_fit_diagonal` (`y=x` dashed ref) | 2 (regex narrow; visual ≥ 20) | predicted-vs-actual |
| `polygon_polar_grid` (replace circular polar grid) | 2 | hero radar |

> The `perfect_fit_diagonal` regex narrowly matches one form; visual inspection of the corpus shows ~20 cases use this pattern with various syntaxes (`np.linspace(min, max)`, `[0, lim]`, `xlim`, etc.). When implementing, always include the diagonal for predicted-vs-actual scatter.

---

## I1 — Metric text box (`metric_text_box`)

In-plot text annotation showing R²/RMSE/N inside a white square with thin black border, top-left or top-right of the panel.

```python
metric_lines = f"$R^2 = {r2:.2f}$\nRMSE = {rmse:.2f}\nN = {n}"
ax.text(0.05, 0.95, metric_lines,
        transform=ax.transAxes, va='top', ha='left',
        fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='square,pad=0.4',
                  fc='white', ec='black', lw=0.8),
        zorder=20)
```

**Position decision:**
- Top-left `(0.05, 0.95)` is corpus default (regression scatter)
- Top-right `(0.95, 0.95)` when left is taken by data
- Bottom-right `(0.95, 0.05)` when both top corners are busy

**Multi-line discipline:** at most 4 lines; use `\n`. Math via `$...$`. Never put the legend inside this box.

Anchor: `Python科研绘图：一行代码实现 R² + 95% 置信区间的高级散点图`, `复现 Nature_Python 绘制广义相加模型(GAM)`.

---

## I2 — Perfect-fit diagonal (`perfect_fit_diagonal`)

Dashed black diagonal line at `y=x` for predicted-vs-actual diagnostic. Always present, always behind the points.

```python
lo, hi = min(x.min(), y.min()), max(x.max(), y.max())
pad = (hi - lo) * 0.05
ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
        'k--', linewidth=1.0, alpha=0.6, zorder=6)
ax.set_xlim(lo - pad, hi + pad)
ax.set_ylim(lo - pad, hi + pad)
ax.set_aspect('equal')
```

**Discipline:**
- Always equal aspect ratio (`set_aspect('equal')`)
- Always `linewidth=1.0` and `alpha=0.5–0.6` so points dominate
- `zorder=6` so it sits below points (`zorder=4`) and above grid (`zorder=0`)

---

## I3 — Group divider (`group_divider_axvline`)

Dashed gray vertical lines that split a categorical axis into named groups (e.g. "Material A" vs "Material B" within a single bar chart).

```python
group_split_indices = [3.5, 7.5]              # midpoints between groups
for x_split in group_split_indices:
    ax.axvline(x=x_split, color='gray', linestyle='--',
               linewidth=1.5, alpha=0.6, zorder=1)

# Group labels above the dividers
for x_center, label in [(1.5, 'Family A'), (5.5, 'Family B'), (9.0, 'Family C')]:
    ax.text(x_center, ax.get_ylim()[1] * 1.02, label,
            ha='center', va='bottom', fontsize=11,
            fontweight='bold', color='#444')
```

Anchor: `如何用Python绘制教科书级的双Y轴组合图`, `期刊复现：双Y轴分组柱状与折线组合图`.

---

## I4 — Zero reference line (`dotted_zero_axhline`)

For ALE, SHAP, residuals, log-fold-change — any signed quantity. Almost always horizontal, dashed, gray.

```python
ax.axhline(0, color='#222222', linestyle='--', linewidth=1.0, zorder=5)

# Vertical variant for forest plots (HR=1, OR=1):
ax.axvline(1, color='#888888', linestyle='--', linewidth=1.0, zorder=0)
```

**Discipline:** `zorder=0` (forest plots) when whiskers should sit above; `zorder=5` (ALE/SHAP) when zero must visually divide signed regions.

---

## I5 — P-value stars (`pvalue_stars_overlay`)

Significance stars added **only** when p-values are supplied in data.

```python
def stars(p):
    return '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'

# For boxplot/bar comparison brackets:
def add_bracket(ax, x1, x2, y, p, line_h=0.02, fontsize=11):
    h = (ax.get_ylim()[1] - ax.get_ylim()[0]) * line_h
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=0.8, c='black')
    ax.text((x1 + x2) / 2, y + h, stars(p),
            ha='center', va='bottom', fontsize=fontsize)
```

**Discipline:**
- Never invent p-values. If absent → no stars.
- Bracket height ~2% of y-range; line width 0.8.
- Use `ns` (italic) when p ≥ 0.05 to make non-significance explicit.

Anchor: `进阶绘图：解决"多变量拥挤"痛点——Python 绘制带显著性星号与斜向色条的三角热图`.

---

## I6 — Density-colored scatter (`density_color_scatter`)

Color points by local 2D density to make crowded regions readable.

```python
from scipy.stats import gaussian_kde
import numpy as np

def density_sort(x, y, bw=None):
    xy = np.vstack([x, y])
    z = gaussian_kde(xy, bw_method=bw)(xy)
    idx = z.argsort()
    return x[idx], y[idx], z[idx]

x_s, y_s, z_s = density_sort(x, y)
sc = ax.scatter(x_s, y_s, c=z_s, cmap='GnBu_r', s=18,
                edgecolor='white', linewidth=0.4, zorder=4, rasterized=True)
fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.04, label='Density')
```

**Discipline:**
- Density-sort so the brightest points draw last
- `rasterized=True` so PDF stays under 5MB
- Always pair with a **colorbar labeled "Density"** — otherwise readers misinterpret the color as a third variable
- `edgecolor='white'` for crispness

Anchor: `复现 CEJ 顶刊神图：密度散点+边缘直方图`, `期刊配图：基于高斯核密度的3x3多面板散点图`.

---

## I7 — White-edge marker (`colored_marker_edge`)

The cheapest readability multiplier in the corpus. Apply by default whenever a scatter has color encoding or sits on a colored background.

```python
ax.scatter(x, y, c=values, cmap='viridis', s=20,
           edgecolor='white', linewidth=0.4, zorder=4)
```

---

## I8 — Twin-axis tinted spine (`twin_axes_color_spines`)

For dual-axis combo charts, tint each spine to its data color so readers immediately see which axis owns which mark.

```python
ax1, ax2 = ax, ax.twinx()
BAR_COLOR = "#9BC2E6"
LINE_COLOR = "#F48E66"

ax1.bar(x, y_left, color=BAR_COLOR, edgecolor=BAR_COLOR, zorder=2)
ax2.plot(x, y_right, color=LINE_COLOR, lw=2.5, marker='o', zorder=3)

ax1.spines['left'].set_color(BAR_COLOR); ax1.spines['left'].set_linewidth(2)
ax1.tick_params(axis='y', colors=BAR_COLOR)
ax1.set_ylabel('Porosity (%)', color=BAR_COLOR)

ax2.spines['right'].set_color(LINE_COLOR); ax2.spines['right'].set_linewidth(2)
ax2.tick_params(axis='y', colors=LINE_COLOR)
ax2.set_ylabel('Strength (MPa)', color=LINE_COLOR)
```

Anchor: `如何用Python绘制教科书级的双Y轴组合图`, `期刊复现：Nature Comms 双Y轴组合图`.

---

## I9 — Confidence/prediction band (`error_band_fill_between`)

Translucent fill behind a primary line to convey uncertainty.

```python
# 95% CI
ax.fill_between(x, lower, upper, color='#888888', alpha=0.15,
                linewidth=0, zorder=2, label='95% CI')

# Prediction interval (sky blue)
ax.fill_between(x, pi_lower, pi_upper, color='skyblue', alpha=0.4,
                label='90% Prediction Interval', zorder=1)

# Regression band (k tinted)
ax.fill_between(curve_x, curve_y - 1.96*se, curve_y + 1.96*se,
                color='black', alpha=0.18, linewidth=0, zorder=2)
```

**Discipline:**
- Alpha 0.15-0.20 for CI/regression band
- Alpha 0.35-0.45 for prediction interval (more visible)
- Always `linewidth=0` so the fill has no border
- Always lower zorder than the primary line/scatter

Anchor: `期刊图表复现：基于预测区间与训练_测试划分的时序拟合效果对比`, `复现 Nature_Python 绘制广义相加模型(GAM)`.

---

## I10 — Marginal axes grid (`marginal_axes_grid`)

Top + right histograms attached to a main scatter. See `04-grid-recipes.md § R8` for the layout; the annotation idiom here is the **styling**.

```python
ax_top.hist(x, bins=40, density=True, color='#69b3a2',
            alpha=0.7, edgecolor='none', zorder=1)
ax_right.hist(y, bins=40, density=True, orientation='horizontal',
              color='#69b3a2', alpha=0.7, edgecolor='none', zorder=1)
ax_top.axis('off'); ax_right.axis('off')
```

**Color:** match the main scatter's anchor color (cool side if predicted-vs-actual, warm if highlight).

**Discipline:** marginal axes are decoration — turn off ticks, no axis labels, no title.

---

## I11 — Polygon polar grid (`polygon_polar_grid`)

Replace matplotlib's circular default polar grid with explicit polygon dashed rings — the Nature radar trick.

```python
ax.spines['polar'].set_visible(False)
ax.grid(False)
n_axes = len(angles) - 1                      # angles closed, drop last
for level in [0.25, 0.5, 0.75, 1.0]:
    ax.plot(angles, [level] * len(angles),
            color='black', linestyle='--', linewidth=0.8,
            alpha=0.6, zorder=0)
# radial spokes
for ang in angles[:-1]:
    ax.plot([ang, ang], [0, 1.0], color='black', linewidth=0.6, alpha=0.4, zorder=0)
```

Anchor: `绝美！Nature 这张雷达图`, `顶刊复刻 _ 这种"中心挖空"+"立体高光"的雷达图`.

---

## I12 — Imshow gradient box (`imshow_gradient_box`)

Vertical gradient inside a box-plot rectangle, faked via `imshow`.

```python
def draw_gradient_box(ax, x, q1, width, height, color, alpha=0.85, zorder=2):
    """Fill a box rectangle with a vertical gradient from translucent to opaque color."""
    import matplotlib.colors as mc
    rgba = mc.to_rgba(color)
    grad = np.linspace(0.15, 0.95, 256).reshape(-1, 1)
    cmap = mc.LinearSegmentedColormap.from_list('g', [(rgba[0], rgba[1], rgba[2], a) for a in grad.flatten()])
    ax.imshow(grad, extent=(x, x + width, q1, q1 + height),
              aspect='auto', origin='lower', cmap=cmap, zorder=zorder)
    rect = plt.Rectangle((x, q1), width, height, fill=False,
                         edgecolor=color, linewidth=1.2, zorder=zorder + 1)
    ax.add_patch(rect)
```

Anchor: `顶刊审美 _ 用 Python 绘制带"垂直渐变特效"的组合箱线图`.

---

## I13 — Panel labels (a/b/c)

Bold lowercase letter at the top-left **outside** the data rectangle. Universal across all multi-panel cases in the corpus.

```python
def add_panel_label(ax, label, *, x=-0.12, y=1.05, fontsize=14):
    ax.text(x, y, label, transform=ax.transAxes,
            fontweight='bold', fontsize=fontsize, va='top', ha='right')
```

**Style:**
- Lowercase letters (`a`, `b`, `c`...) — Nature/Cell/Science convention
- Times New Roman bold, 14pt
- Position `(-0.12, 1.05)` axes fraction; `(-0.18, 1.08)` for cramped panels

---

## I14 — Sample-shape encoding

When color is reserved for a continuous variable, use **marker shape** for discrete groups.

```python
shapes = {'train': 'o', 'val': 's', 'test': 'D'}
for split, df_s in df.groupby('split'):
    ax.scatter(df_s.x, df_s.y, marker=shapes[split],
               c=df_s.value, cmap='viridis', s=30,
               edgecolor='white', linewidth=0.4,
               label=split, zorder=4)
```

Anchor: split overlay in predicted-vs-actual cases.

---

## Helpers contract

```python
def add_metric_box(ax, metrics: dict, *, loc='top_left', fontsize=11,
                   pad=0.4, lw=0.8) -> None: ...

def add_perfect_fit_diagonal(ax, x, y, *, color='black', lw=1.0, alpha=0.6) -> None: ...

def add_group_dividers(ax, split_indices: list[float], *, group_labels: list[str] | None = None) -> None: ...

def add_zero_reference(ax, *, axis='y', color='#222', lw=1.0, ls='--') -> None: ...

def add_significance_brackets(ax, comparisons: list[tuple[float, float, float]], *, fontsize=11) -> None: ...

def density_color_scatter(ax, x, y, *, cmap='GnBu_r', s=18, with_colorbar=True) -> Axes: ...

def add_polygon_polar_grid(ax, angles, levels=(0.25, 0.5, 0.75, 1.0)) -> None: ...

def draw_gradient_box(ax, x: float, q1: float, width: float, height: float,
                      color: str, *, alpha=0.85, zorder=2) -> None: ...

def add_panel_label(ax, label: str, *, x=-0.12, y=1.05, fontsize=14) -> None: ...
```

All annotation idioms must be applied through these helpers so QA can count motif applications via the helper signature.

## QA contract

`render-qa` (Phase 4) checks:

- `metricBoxCount`: predicted-vs-actual scatter must have ≥1 metric box if R²/RMSE were planned
- `perfectFitCount`: predicted-vs-actual scatter must have a diagonal
- `zeroReferenceCount`: ALE / SHAP / signed-effect plots must include zero ref
- `panelLabelCount`: multi-panel figures must have a/b/c labels on every plotted panel
- `pvalueStarsOnlyWhenSupplied`: stars present iff p-value column present in data
- `polarGridReplaced`: polar plots must hide default grid + add polygon grid

Failures route back to Phase 3 with the specific idiom that's missing.
