# 三明治图层法 (zorder Recipes)

The dominant rendering pattern across the 77 reference cases. **61/77** explicitly use `zorder=` to stack chart layers in a deliberate order. This file documents the family-specific recipes — what goes on the bottom, what goes in the middle, what sits on top.

> "复杂图表的绘制核心在于对 `zorder` 的精准控制。"
> — *顶刊审美 _ 用 Python 绘制带"垂直渐变特效"的组合箱线图*

## The Universal Rule

**zorder ascends with semantic priority.** Lowest layers carry context (grids, fills, bands); top layers carry the points the reader is meant to focus on (highlights, error bars, callouts).

Standard tier:

| Tier   | zorder | Purpose | Examples |
|--------|--------|---------|----------|
| **L0** | 0      | grid, ticks, panel background | `ax.grid(zorder=0)`, `set_facecolor` |
| **L1** | 1–2    | density / uncertainty fills, base bars, faint context points | `fill_between` PI band, `bar` background, gray scatter |
| **L2** | 3–4    | primary marks, scatter, fit lines, regression bands | `scatter`, `plot` curve, `ax.bar` foreground |
| **L3** | 5–6    | reference lines / dividers / panel splits | `axvline`, `axhline`, perfect-fit dashed |
| **L4** | 7–9    | error bars, whiskers, IQR overlays, confidence whiskers | `errorbar`, `boxplot` lines |
| **L5** | 10+    | highlight markers, callouts, annotations, p-value brackets | `text`, highlighted scatter, panel-label letters |

A single chart rarely uses every tier; pick the tiers that map to your data semantics.

## Per-family Recipes

### scatter-regression (predicted vs actual / x-y diagnostic)

Source cases: GAM scatter+residual (Nature), CEJ density+marginal, R² scatter (basic), distance-decay scatter (community), prediction-experiment scatter.

```python
# L0: grid (optional, light dashed)
ax.grid(linestyle='--', color='#E0E0E0', alpha=0.6, zorder=0)

# L1: low-context gray points (background population)
ax.scatter(x_gray, y_gray, c='#B0B0B0', s=40, alpha=0.3, zorder=1)

# L1.5: density / confidence fill
ax.fill_between(curve_x, lower, upper, color='k', alpha=0.15, linewidth=0, zorder=2)

# L2: highlight points (the population you actually care about)
ax.scatter(x_color, y_color, c=palette['hero'], s=40, alpha=0.6, zorder=4)

# L3: fit line and reference (perfect-fit / y=x)
ax.plot(curve_x, curve_y, color='black', linewidth=2.5, zorder=5)
lim = max(x.max(), y.max()) * 1.1
ax.plot([0, lim], [0, lim], 'k--', linewidth=1.0, alpha=0.5, zorder=6)

# L5: in-axes annotation (R², N=, RMSE)
ax.text(0.05, 0.95, '$R^2=0.61$', transform=ax.transAxes, fontweight='bold',
        bbox=dict(boxstyle='square,pad=0.3', fc='white', ec='black', lw=0.8), zorder=20)
```

### forest-plot (effect estimates with CI)

Source cases: HR multi-panel forest (Nature Comms), risk-ratio caterpillar.

```python
# L0: panel background
# (forest plots typically skip grid; rely on x ticks)

# L3: reference line at null effect (HR=1, OR=1, RR=1, β=0)
ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1.0, zorder=0)

# L4: confidence whiskers + point estimate (single call)
xerr = [[hr - lower], [upper - hr]]
ax.errorbar(x=hr, y=y_pos, xerr=xerr, fmt='o',
            color=color_map[model], ecolor=color_map[model],
            elinewidth=2, capsize=4, markersize=8, zorder=10)

# L5: optional p-value or asterisk to the right of the whisker
ax.text(upper * 1.05, y_pos, '*' if p < 0.05 else '', va='center', zorder=15)
```

### dual-axis-combo (two y-axes sharing x)

Source cases: Materials Today porosity+strength, Nature Comms double-Y, JECE 双Y轴 grouped bars+lines.

```python
ax1, ax2 = ax, ax.twinx()

# L1: bottom-axis bars (the "bread" of the sandwich)
ax1.bar(x, df['Porosity'], width=0.6, yerr=df['Por_Err'], capsize=5,
        color='#CFE2F3', edgecolor='#9BC2E6', linewidth=1.5, zorder=2)

# L2.5: vertical group dividers (dashed light gray)
for idx in split_indices:
    ax1.axvline(x=idx, color='gray', linestyle='--', linewidth=1.5, alpha=0.6, zorder=1)

# L3: top-axis spline-smoothed line (the "meat")
ax2.plot(x_smooth, y_smooth, color='#F48E66', linewidth=3, zorder=3)

# L4: error bars and markers on top axis
ax2.errorbar(x, df['Strength'], yerr=df['Str_Err'], fmt='o',
             color='#F48E66', markersize=10, capsize=5, elinewidth=2, zorder=4)

# Optional: tint the spines to match each axis's data color
ax1.spines['left'].set_color('#9BC2E6'); ax1.spines['left'].set_linewidth(2)
ax2.spines['right'].set_color('#F48E66'); ax2.spines['right'].set_linewidth(2)
```

### radar / polar-comparison

Source cases: Nature semiconductor fibre radar, biodiversity radar, mirror radial.

```python
# L0: replace default circular grid with explicit polygon dashed grid
ax.spines['polar'].set_visible(False)
ax.grid(False)
for level in [0.25, 0.5, 0.75, 1.0]:
    ax.plot(angles, [level] * len(angles), color='black', linestyle='--', alpha=0.6, zorder=0)

# L1: translucent fill (the "cushion")
ax.fill(angles, values, color=color, alpha=0.15, zorder=1)

# L2: solid outline (the "wrapper")
ax.plot(angles, values, color=color, linewidth=2.5, label=label, zorder=5)

# L4: error-bar marker points at the vertices
ax.errorbar(angles[:-1], values[:-1], yerr=errors[:-1], fmt='o',
            color=color, capsize=4, zorder=10)
```

For mirror radial (two-condition bipolar): give upper-half bars `zorder=5`, slim foreground bars `zorder=10`.

### shap-composite (importance + beeswarm)

Source cases: SHAP 上三下二 multi-panel, SHAP+条形组合, SHAP+饼图.

```python
ax_top = ax_bottom.twiny()

# L0: dashed gray vertical zero line
ax_bottom.axvline(x=0, color='black', linewidth=1.2, zorder=5)

# L1: background importance bars (purple, 15% alpha)
ax_top.barh(range(len(top_idx)), mean_abs_shap[top_idx],
            color='purple', alpha=0.15, zorder=0)

# L2: beeswarm scatter, colored by feature value
for i, idx in enumerate(top_idx):
    y_jit = calculate_jitter(shap_vals[:, idx])
    ax_bottom.scatter(shap_vals[:, idx], np.full(len(y_jit), i) + y_jit,
                      c=norm_f, cmap='viridis', s=20, alpha=0.8,
                      edgecolor='white', zorder=10)
```

### heatmap-pairwise (n×n diagonal+upper+lower)

Source cases: Nature Pearson n×n, 上三角填充饼相关性矩阵.

```python
# Diagonal (i == j): histogram + KDE
if i == j:
    ax.hist(x, bins=15, density=True, color='white', edgecolor='black', zorder=1)
    ax.plot(x_grid, kde(x_grid), color=PRIMARY_COLOR, lw=2, zorder=3)

# Upper-triangle (i < j): correlation number on tinted background
elif i < j:
    ax.set_facecolor(BG_COLOR_CORR)            # zorder=0
    ax.text(0.5, 0.5, f'{corr:.2f}', ha='center', va='center',
            transform=ax.transAxes, zorder=10)
    for spine in ax.spines.values():
        spine.set_visible(False)

# Lower-triangle (i > j): hollow scatter
else:
    ax.scatter(x, y, s=15, facecolor='none',
               edgecolor=PRIMARY_COLOR, alpha=0.6, zorder=2)
```

### marginal-joint (main scatter + top/right histograms)

Source cases: CEJ density+marginal, joint residual+kde, joint contour heatmap.

```python
# Inner GridSpec is built first (see 04-grid-recipes.md § marginal-grid)
ax_main, ax_top, ax_right = build_marginal_axes(fig, gs_outer)

# Main: density-colored scatter (sort by density to put bright points on top)
x_sorted, y_sorted, z_sorted = density_sort(x, y)
ax_main.scatter(x_sorted, y_sorted, c=z_sorted, cmap='GnBu_r',
                s=2, rasterized=True, zorder=2)

# Diagonal reference line (perfect fit)
lim = max(x.max(), y.max()) * 1.1
ax_main.plot([0, lim], [0, lim], 'k--', lw=1.0, alpha=0.5, zorder=10)

# Marginal histograms — context only; transparent fills, no scaffolding
ax_top.hist(x, bins=50, density=True, color='#69b3a2', alpha=0.7, zorder=1)
ax_right.hist(y, bins=50, density=True, orientation='horizontal',
              color='#69b3a2', alpha=0.7, zorder=1)
ax_top.axis('off'); ax_right.axis('off')
```

### gradient-box (vertical-gradient box plot)

Source cases: JBE 渐变箱线图.

```python
# L0: dashed horizontal grid (very light)
ax.yaxis.grid(True, linestyle='--', color='#E0E0E0', zorder=0)

# L1: jitter scatter (hollow, behind the box)
ax.scatter(jitter_x, subset, s=25, facecolors='none', edgecolors=color,
           alpha=0.8, zorder=1)

# L2: gradient-fill rectangle via imshow trick
draw_gradient_box(ax, i - 0.25, q1, 0.5, q3 - q1, color, zorder=2)

# L2: whiskers (drawn as plain lines)
ax.plot([i, i], [high_whisker, q3], color=color, lw=1.2, zorder=2)
ax.plot([i, i], [low_whisker, q1], color=color, lw=1.2, zorder=2)

# L3: median line (slightly thicker)
ax.plot([i - 0.25, i + 0.25], [median, median], color=color, lw=2, zorder=3)

# L4: mean marker (square, contrasting color)
ax.plot(i, mean_val, marker='s', mfc='#F06292', mec='#C2185B',
        markersize=6, zorder=4)
```

The `draw_gradient_box` trick uses `ax.imshow` of a 1-pixel-wide RGBA matrix to fake a gradient — see `07-techniques/gradient-box.md`.

### time-series with prediction interval

Source cases: SOC 90% PI fitting, 双 Y轴 时序+分布.

```python
# L1: 90% PI band (sky blue, alpha=0.4)
ax.fill_between(x, y_lower, y_upper, color='skyblue', alpha=0.4,
                label='90% Prediction Interval', zorder=1)

# L2: ground-truth observations (small black dots)
ax.scatter(x, y_true, color='black', s=15, alpha=0.7,
           label='Actual Observations', zorder=2)

# L3: prediction line (red, thin)
ax.plot(x, y_pred, color='red', linewidth=1.5,
        label='Model Prediction', zorder=3)

# L3: train/test divider
ax.axvline(x=split_index, color='gray', linestyle='--', linewidth=1.5, zorder=4)
```

### lollipop / dumbbell

Source cases: 双侧棒棒糖 PFI+ALE, 双侧棒棒糖 importance.

```python
# L1: stems (line segments)
ax.hlines(y=y_pos, xmin=0, xmax=values, color=stem_color,
          linewidth=2.5, zorder=1)

# L2: end-point markers
ax.scatter(values, y_pos, color=marker_color, s=80, zorder=2)

# L3: zero / reference line (esp. for ALE bipolar)
ax.axvline(0, color='gray', linestyle='--', linewidth=1.2, zorder=0)
```

For bipolar ALE: build `colors = ['#C0504D' if v > 0 else '#4F81BD' for v in values]` and pass per-segment.

### inset-axes (raincloud / mini distribution)

Source cases: Materials inset 雨云图, Nature Nanotechnology 画中画.

```python
# Outer plot: trend line first (zorder=2-4 for true vs predicted)
ax.plot(d['x'], d['y_true'], color='#FFA500', marker='s', label='True', zorder=3)
ax.plot(d['x'], d['y_pred'], color='#008000', marker='o', label='Pred', zorder=4)

# Inner: inset_axes with high zorder so it sits above main
rect = [0.55, 0.35, 0.40, 0.35]                  # x, y, w, h in axes fraction
ax_ins = ax.inset_axes(rect, zorder=10)
ax_ins.set_facecolor('white')                    # opaque white background
# ... draw distribution inside ax_ins ...
```

The inset itself is a tier 5 (`zorder=10`) layer because it visually sits on top of the main plot. Inside the inset, restart from L0.

## Despine: the silent partner of zorder

Despine (top + right spine off) is applied in **64/77 cases**. It's not strictly a zorder concern, but it's part of the same "remove distractions, foreground the data" discipline.

```python
def despine(ax, sides=('top', 'right')):
    for side in sides:
        ax.spines[side].set_visible(False)
```

Family-specific:
- Polar: `ax.spines['polar'].set_visible(False)` then re-add a polygon grid (see radar).
- Pairwise upper-triangle: hide ALL spines, keep only the text.
- Forest plot panels: keep all four spines; remove only top in some variants.
- Inset: keep all four spines (the rectangle is the inset's identity).

## Helpers Contract

`phases/code-gen/helpers.py` exposes the recipes as callable applicators that rewrite zorder-naive generator output:

```python
def apply_zorder_recipe(family: str, ax, layers: dict) -> None:
    """Apply the family's zorder recipe to existing artists.
    family: one of 'scatter_regression', 'forest', 'dual_axis', 'radar',
            'shap_composite', 'heatmap_pairwise', 'marginal_joint',
            'gradient_box', 'time_series_pi', 'lollipop', 'inset_distribution'.
    layers: dict mapping role names ('grid', 'background', 'primary',
            'reference', 'error', 'highlight') to the artists or
            artist-lists to be re-tagged.
    """
```

Generator authors don't have to memorize zorder numbers — they tag artists semantically and the helper sets the right values. This is the path to retroactively making old generators consistent.

## QA Hooks

`render-qa` (Phase 4) checks:

- `zorderRecipeApplied`: at least one `apply_zorder_recipe()` call per chart family that has a recipe defined here.
- `referenceLineCount` ≥ 1 for chart families that mandate a reference (forest, ALE, predicted-vs-actual).
- `noZorderInversion`: no artist has zorder lower than its declared semantic tier (e.g. error bars below background fill).
- For polar plots: `polarGridReplaced` must be True (default circular grid was hidden + custom polygon grid added).

Failures route back to Phase 3 with the specific layer that's misplaced.

## Source Anchors

| Family | Reference cases |
|--------|-----------------|
| scatter-regression | `复现 Nature _ Python 绘制广义相加模型 (GAM)`, `Python科研绘图：一行代码实现 R² + 95% 置信区间的高级散点图`, `期刊配图：基于线性拟合与误差带的距离衰减散点图` |
| forest | `Python科研绘图复现_绘制多面板分组森林图展示生存分析风险比(HR)` |
| dual-axis | `如何用Python绘制教科书级的双Y轴组合图`, `期刊复现：Nature Comms 双Y轴组合图`, `期刊复现：双Y轴分组柱状与折线组合图评估多模型预测性能` |
| radar | `绝美！Nature 这张雷达图`, `顶刊复刻 _ "中心挖空"+"立体高光"的雷达图`, `期刊配图：基于极坐标系的多面板雷达图` |
| shap-composite | `期刊配图复现 _ Python绘制多面板SHAP蜂群图`, `复现顶刊 _ 拒绝千篇一律的SHAP图`, `期刊复现：组合重要性条形图与SHAP蜂群图` |
| heatmap-pairwise | `期刊复现：Nature同款皮尔逊热力图`, `期刊复现：基于上三角局部填充饼图的相关性矩阵` |
| marginal-joint | `复现 CEJ 顶刊神图 _ Python 绘制"密度散点+边缘直方图"多面板组合图`, `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图`, `期刊复现：联合等高线热图与边缘分布图` |
| gradient-box | `顶刊审美 _ 用 Python 绘制带"垂直渐变特效"的组合箱线图` |
| time-series-pi | `期刊图表复现：基于预测区间与训练_测试划分的时序拟合效果对比`, `期刊配图复现 _ Python绘制"趋势+分布"时序混合图` |
| lollipop | `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向`, `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图` |
| inset-distribution | `复现顶刊 _ Python绘制"主图+嵌入雨云图"组合`, `期刊复现：Nature Nanotechnology 经典"画中画"组合图` |
