# GridSpec 多面板配方 (Grid Recipes)

Layout blueprints harvested from the 77 reference cases. Each recipe has **at least one anchor case** and the actual GridSpec/subplots invocation copied from the corpus.

## When to use this file

- Phase 2 needs to choose a panel count + arrangement
- Phase 3 needs the actual GridSpec / subplots / `add_axes` invocation
- A user asks "how do I lay out my N panels?"

**Do NOT** use this file for chart-content decisions; that's `02-zorder-recipes.md` and `07-techniques/`.

## Corpus distribution (n=77)

| Shape | Cases | Recipe key |
|---|---|---|
| `1×2` | 8 (6 subplots + 2 gridspec) | `R1_two_panel_horizontal` |
| `2×2` | 6 (4 + 2) | `R2_two_by_two_storyboard` |
| `2×3` | 6 (3 + 3) | `R3_two_by_three_grid` |
| `1×3` | 4 (3 + 1) | `R4_three_panel_horizontal` |
| `3×3` | 3 (2 + 1) | `R5_n_by_n_pairwise` |
| `1×4` | 2 (1 + 1) | `R6_four_panel_band` |
| `2×6` | 2 (gridspec only) | `R7_dense_2x6_lineup` |
| `3×2` | 2 (1 + 1) | `R2` rotated |
| `2×1` | 2 | `R1` rotated |
| `1×5` | 1 | exotic — one-off in `期刊配图：基于线性拟合与误差带的距离衰减散点图` |
| `4×8` | 1 | exotic — `Python 科研绘图：模型精度+稳定性` |
| `3×6` | 1 | exotic — `期刊配图复现 _ Python 绘制多面板分层热力图` |
| (no grid; single panel) | 36 | `R0_single_panel` |
| (irregular `add_axes`/`inset_axes`) | varies | `R8_main_with_marginal`, `R9_inset_overlay` |

23/77 use `GridSpec` explicitly (vs `subplots`); these are the cases that need irregular column widths or nested subplots.

---

## R0 — Single panel (36 cases)

Default for: hero radar, single forest, single SHAP beeswarm, dual-axis combo, single density scatter.

```python
fig, ax = plt.subplots(figsize=(6.5, 6.0))
```

**Figsize discipline (corpus-derived medians):**

| Family | Common figsize | Notes |
|---|---|---|
| Hero radar | `(8, 8)` | square; polar projection |
| Hero forest 4-cohort | `(8, 6)` | slightly landscape for label space |
| Single dual-axis combo | `(7, 5)` | wide for x-axis category labels |
| Single SHAP beeswarm | `(7, 7)` | square; many y-rows |
| Density scatter w/ colorbar | `(6.5, 6.0)` | square; colorbar steals 0.5 width |

---

## R1 — Two-panel horizontal (8 cases)

Use when: one hero panel + one diagnostic, OR two parallel comparisons.

```python
# Equal width
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ax_left, ax_right = axes

# Asymmetric width via GridSpec (≈70/30)
import matplotlib.gridspec as gridspec
fig = plt.figure(figsize=(13, 5))
gs = gridspec.GridSpec(1, 2, width_ratios=[7, 3], wspace=0.25)
ax_left  = fig.add_subplot(gs[0, 0])
ax_right = fig.add_subplot(gs[0, 1])
```

**When to choose asymmetric:** the hero panel carries the headline (scatter+regression); the right panel carries supporting metric/distribution. Anchor: `期刊配图：基于线性拟合与误差带的距离衰减散点图`.

**Spacing:** `wspace=0.25` for separated panels, `wspace=0.10` when sharing y-axis.

---

## R2 — 2×2 Story Board (6 cases)

Use when: discovery + mechanism + validation + cohort/context (4 distinct claims).

```python
fig, axes = plt.subplots(2, 2, figsize=(11, 9))
(ax_a, ax_b), (ax_c, ax_d) = axes
```

Anchor: `期刊复现：双面板组合图展示特征重要性权重与模型性能演变`, `期刊复现：双Y轴分组柱状与折线组合图`.

**Panel naming convention** (corpus-consistent):
- A = hero (top-left)
- B = orthogonal support (top-right)
- C = validation (bottom-left)
- D = context / cohort / summary (bottom-right)

**Spacing:** `hspace=0.3, wspace=0.3`. Tighten to `0.2/0.2` only when all four panels share x-axis.

---

## R3 — 2×3 grid (6 cases)

Use when: 6 SHAP dependence panels, 6-feature ALE/PDP grid, 6-condition box.

```python
fig = plt.figure(figsize=(15, 9))
gs = gridspec.GridSpec(2, 3, hspace=0.35, wspace=0.25)
axes = [[fig.add_subplot(gs[r, c]) for c in range(3)] for r in range(2)]
```

Anchors: `期刊图表复现：多面板SHAP依赖图展示分子特征对自由基反应速率的非线性影响` (2,3 SHAP),
`期刊配图：基于极坐标系的多面板雷达图`.

**Tuning:**
- For SHAP/ALE bands: tighten hspace to `0.30` so dependence curves visually align
- For radar polar: keep hspace `0.40` because polar panels need vertical breathing room

---

## R4 — Three-panel horizontal (4 cases)

Use when: train→validate→test, or condition-by-condition triple.

```python
fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
```

`sharey=True` is the default in this layout because the 3 panels usually compare the **same** y-quantity across conditions.

Anchor: `期刊复现：通过多子图布局对比城市化梯度对气体排放量的非线性影响`.

---

## R5 — n×n pairwise (3 cases at 3×3, plus pairwise variants)

Use when: pearson/spearman correlation matrix, scatter matrix.

```python
n = 5
fig = plt.figure(figsize=(2.4*n, 2.4*n))
gs = gridspec.GridSpec(n, n, hspace=0.05, wspace=0.05)
axes = [[fig.add_subplot(gs[i, j]) for j in range(n)] for i in range(n)]

for i in range(n):
    for j in range(n):
        ax = axes[i][j]
        if i == j:        # diagonal: hist + KDE
            ax.hist(...); ax.plot(kde(...), zorder=3)
        elif i < j:       # upper triangle: correlation number on tinted bg
            ax.set_facecolor(BG_FROM_CORR(corr[i,j]))
            ax.text(0.5, 0.5, f"{corr[i,j]:.2f}", ha='center', va='center', transform=ax.transAxes)
            for s in ax.spines.values(): s.set_visible(False)
            ax.set_xticks([]); ax.set_yticks([])
        else:             # lower triangle: hollow scatter
            ax.scatter(x[j], x[i], s=15, facecolor='none', edgecolor=PRIMARY, alpha=0.6)
        # only show labels on outer panels
        if j == 0: ax.set_ylabel(features[i])
        if i == n-1: ax.set_xlabel(features[j])
```

Anchors: `期刊复现：Nature同款皮尔逊热力图`, `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能`.

**Spacing:** `hspace=wspace=0.05` — must be tight or n×n looks loose.

---

## R6 — 1×4 narrow band (2 cases)

Use when: forest plot with 4 cohorts, multi-cohort survival comparison.

```python
fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
```

Anchors: `Python科研绘图复现_绘制多面板分组森林图展示生存分析风险比(HR)`.

---

## R7 — Dense 2×6 lineup (2 cases)

Use when: 12-panel mass comparison (12 features × 1 method, or 6 metrics × 2 methods).

```python
fig = plt.figure(figsize=(20, 7))
gs = gridspec.GridSpec(2, 6, hspace=0.40, wspace=0.30)
```

Anchors: SHAP large-feature multi-panel, dependence plots with many features. Keep figsize wide (≥18 inches) to avoid label crash.

---

## R8 — Main + marginal (5 cases)

Use when: density scatter + top/right histograms; predicted-vs-actual + residual KDE.

### Variant A — `axes_grid1.make_axes_locatable` (cleanest)

```python
from mpl_toolkits.axes_grid1 import make_axes_locatable

fig, ax_main = plt.subplots(figsize=(7, 7))
divider = make_axes_locatable(ax_main)
ax_top   = divider.append_axes("top",   size="20%", pad=0.05, sharex=ax_main)
ax_right = divider.append_axes("right", size="20%", pad=0.05, sharey=ax_main)

ax_top.tick_params(labelbottom=False)
ax_right.tick_params(labelleft=False)
ax_top.axis('off'); ax_right.axis('off')
```

### Variant B — explicit GridSpec (full control)

```python
fig = plt.figure(figsize=(8, 8))
gs = gridspec.GridSpec(2, 2,
                       width_ratios=[4, 1],
                       height_ratios=[1, 4],
                       hspace=0.05, wspace=0.05)
ax_top   = fig.add_subplot(gs[0, 0])
ax_main  = fig.add_subplot(gs[1, 0])
ax_right = fig.add_subplot(gs[1, 1])
gs_corner = fig.add_subplot(gs[0, 1]); gs_corner.axis('off')
```

Anchors: `复现 CEJ 顶刊神图_Python 绘制"密度散点+边缘直方图"多面板组合图`, `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图`, `期刊复现：联合等高线热图与边缘分布图`, `期刊复现：通过带边缘密度的联合残差图`.

**Marginal-axis discipline** (corpus-consistent):
- Marginals are **context only**: `axis('off')`, fill alpha=0.7, no ticks
- Their color matches the main scatter palette anchor
- Density-sort the main scatter so dense regions paint last

---

## R9 — Inset overlay (8 cases — `inset_axes`)

Use when: main trend + small distribution panel (e.g. raincloud) inside the same axes.

```python
ax.plot(d['x'], d['y_true'], color='#FFA500', marker='s', label='True',  zorder=3)
ax.plot(d['x'], d['y_pred'], color='#008000', marker='o', label='Pred', zorder=4)

rect = [0.55, 0.35, 0.40, 0.35]                    # x, y, w, h in axes fraction
ax_ins = ax.inset_axes(rect, zorder=10)
ax_ins.set_facecolor('white')
ax_ins.patch.set_alpha(0.95)
for spine in ax_ins.spines.values():
    spine.set_linewidth(0.8); spine.set_color('#222')
# inside ax_ins: draw raincloud / mini distribution / detail zoom
```

Anchors: `复现顶刊_Python绘制"主图+嵌入雨云图"组合`, `期刊复现：Nature Nanotechnology 经典"画中画"组合图`.

**Position discipline:**
- Inset rect `[0.55, 0.35, 0.40, 0.35]` is the corpus default (right-center)
- `[0.05, 0.55, 0.35, 0.40]` for top-left inset (rare; only when right side is busy)
- Always `zorder=10+` and opaque white background

---

## R10 — Asymmetric three-panel (top-wide + 2 below) — SHAP上三下二

```python
# 1 wide top + 2 narrow below
fig = plt.figure(figsize=(11, 9))
gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.25)
ax_top    = fig.add_subplot(gs[0, :])             # spans full top row
ax_bl     = fig.add_subplot(gs[1, 0])
ax_br     = fig.add_subplot(gs[1, 1])
```

Use when: hero overview on top, two comparison panels below.

Anchor: SHAP composite cases — top = global importance bar, bottom-left = beeswarm, bottom-right = local force/dependence.

---

## R11 — Triple Y-axis (rare; single panel with 3 axes)

```python
fig, ax1 = plt.subplots(figsize=(8, 5))
ax2 = ax1.twinx()
ax3 = ax1.twinx()
ax3.spines['right'].set_position(('outward', 60))      # offset 3rd axis
ax1.bar(x, y1, color="#CFE2F3", zorder=2)
ax2.plot(x, y2, color="#F48E66", lw=2, zorder=3)
ax3.plot(x, y3, color="#4C956C", lw=2, linestyle='--', zorder=4)
# tint each spine to its data color
ax1.spines['left'].set_color("#9BC2E6"); ax1.spines['left'].set_linewidth(2)
ax2.spines['right'].set_color("#F48E66"); ax2.spines['right'].set_linewidth(2)
ax3.spines['right'].set_color("#4C956C"); ax3.spines['right'].set_linewidth(2)
```

Anchor: `期刊配图复现 _ Matplotlib 挑战"多面板+三Y轴"组合图`.

---

## Universal layout discipline (consolidated)

| Rule | Frequency | Notes |
|---|---|---|
| Panel labels A/B/C/D bold, 8-10 pt, at `(-0.12, 1.05)` axes fraction | most multi-panel cases | `ax.text(-0.12, 1.05, 'a', transform=ax.transAxes, fontweight='bold', fontsize=8)` |
| Outer-only tick labels in shared-axis grids | n×n, 1×N | use `sharex/sharey` or hide via `tick_params(labelbottom/left=False)` |
| Colorbar `shrink=0.6`, `pad=0.04`, beside heatmap panels | all heatmap cases | never inside the data rectangle |
| Legend outside the data rectangle (bottom-center or top-center only) | all multi-condition cases | `bbox_to_anchor=(0.5, 0.01), loc='lower center'` with reserved bottom margin; outside-right is forbidden in final output |
| `hspace=0.30`, `wspace=0.25` defaults for 2×N grids | majority | tighten to 0.10 when sharing axis, loosen to 0.40 when polar |

## Helpers contract

```python
def build_grid(recipe: str, fig=None, **opts) -> tuple[Figure, list[Axes]]:
    """Build a multi-panel figure from a recipe key.
    recipe: 'R0_single_panel' | 'R1_two_panel_horizontal' | 'R2_two_by_two_storyboard'
            | 'R3_two_by_three_grid' | 'R4_three_panel_horizontal' | 'R5_n_by_n_pairwise'
            | 'R6_four_panel_band' | 'R7_dense_2x6_lineup' | 'R8_main_with_marginal'
            | 'R9_inset_overlay' | 'R10_asymmetric_top_wide' | 'R11_triple_y_axis'
    opts:   recipe-specific tuning (figsize, n for R5, ratios, spacing).
    Returns the figure and a flat list of axes in reading order.
    """
```

Phase 3 should not call `plt.subplots`/`GridSpec` directly when a recipe applies — it should call `build_grid()`. Generators authored before this file may stay as-is until refactored.

## Source anchors

| Recipe | Reference cases |
|---|---|
| R0 | `绝美！Nature 这张雷达图`, `如何用Python绘制教科书级的双Y轴组合图` |
| R1 | `期刊配图：基于线性拟合与误差带的距离衰减散点图`, `期刊复现：双面板NMDS散点图` |
| R2 | `期刊复现：双面板组合图展示特征重要性权重与模型性能演变` |
| R3 | `期刊图表复现：多面板SHAP依赖图`, `期刊配图：基于极坐标系的多面板雷达图` |
| R4 | `期刊复现：通过多子图布局对比城市化梯度` |
| R5 | `期刊复现：Nature同款皮尔逊热力图`, `期刊配图：基于高斯核密度的3x3多面板散点图` |
| R6 | `Python科研绘图复现_绘制多面板分组森林图(HR)` |
| R7 | SHAP large-feature multi-panel cases |
| R8 | `复现 CEJ 顶刊神图：密度散点+边缘直方图`, `期刊复现：联合等高线热图与边缘分布图` |
| R9 | `复现顶刊：主图+嵌入雨云图`, `期刊复现：Nature Nanotechnology 经典画中画` |
| R10 | SHAP composite multi-panel cases |
| R11 | `期刊配图复现：Matplotlib 挑战多面板+三Y轴组合图` |
