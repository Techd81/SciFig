# GridSpec 多面板配方 (Grid Recipes)

Layout blueprints harvested from the 94-case template corpus. Each recipe has **at least one anchor case** and the actual GridSpec/subplots invocation copied from the corpus.

## When to use this file

- Phase 2 needs to choose a panel count + arrangement
- Phase 3 needs the actual GridSpec / subplots / `add_axes` invocation
- A user asks "how do I lay out my N panels?"

**Do NOT** use this file for chart-content decisions; that's `02-zorder-recipes.md` and `07-techniques/`.

## Corpus distribution (n=94)

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

19/94 use `GridSpec` explicitly and 23/94 use `subplots`; these are the cases that need irregular column widths, nested subplots, or compact repeated panels.

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
| 3D PDP surface | `(10, 8)` | landscape-ish 3D axes plus right colorbar |

**Case-066 environmental radar variant:** when the evidence is one condition
comparison on shared environmental/model metrics, keep the source-like R0 polar
axis instead of inflating it to empty panels:

```python
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
```

Use `R3_two_by_three_grid` only when the data supplies real facets such as
multiple basins, seasons, models, or ablation groups; every polar panel must
share the same spoke order and `[0, 1]` radial scale.

**Case-072 Nature radar canonical variant:** use one square `figsize=(8, 8)`
polar axis, north-up clockwise theta orientation, hidden circular spine, and
hand-drawn polygon grid. Do not use a 2D subplot grid for the canonical
semiconductor-fibre radar unless the data supplies separate radar panels.

**Case-077 Cell marker bar-scatter variant:** keep a single axes with
`figsize=(9, 7)` and create the group structure through explicit x positions,
not subplots:

```python
x_pos = [0, 1, 2, 3, 4.5, 5.5, 6.5, 7.5, 8.5]
```

The gap between `3` and `4.5` is semantic dorsal/ventral whitespace.  Use top
horizontal rules for group labels and keep the y-limit expanded from the maximum
upper error bound.

**Case-087 3D PDP surface variant:** keep the PDP interaction as one
`projection="3d"` axes plus a right colorbar, not a 2D-PDP subplot matrix:

```python
fig = plt.figure(figsize=(10, 8), dpi=300)
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(X_mesh, Y_mesh, Z_pred, cmap="viridis",
                       edgecolor="none", alpha=0.85)
ax.contourf(X_mesh, Y_mesh, Z_pred, zdir="z", offset=z_min,
            cmap="viridis", alpha=0.5)
fig.colorbar(surf, ax=ax, shrink=0.5, pad=0.1, aspect=15)
```

Use this R0 variant when the requested evidence is a single two-feature PDP
surface with bottom contour projection and transparent 3D panes. Use the
2D-PDP contour matrix only when the data supplies multiple feature-pair panels
or explicitly asks for flat response-boundary comparison.

---

## R1 — Two-panel horizontal (8 cases)

Use when: one hero panel + one diagnostic, OR two parallel comparisons. Case-008
uses this as a relationship/residual diagnostic pair.

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

**When to choose asymmetric:** the hero panel carries the headline (scatter+regression); the right panel carries supporting metric/distribution.

**Nature GAM diagnostic variant:** `GridSpec(1, 2, width_ratios=[1,1], wspace=0.25)`
with the left panel as log-log smooth relationship and the right panel as residual
outlier diagnosis.

**Urban gradient flux boxplot variant:** Case-049 uses
`plt.subplots(nrows=1, ncols=2, figsize=(10, 4.5), gridspec_kw={"wspace": 0.25})`
for parallel CH4 and CO2 flux panels. Keep urbanization categories on each
x-axis, nest season hue inside every category, set a log y-axis on both panels,
and allow independent gas-specific y scales. Use one shared season legend only
when both panels reuse the same Cool-dry / Warm-wet palette.
Case-061 is the raincloud form of the same environmental flux comparison:
`plt.subplots(nrows=1, ncols=2, figsize=(12, 5), dpi=300)` plus
`subplots_adjust(wspace=0.25, bottom=0.15, left=0.08, right=0.95)`. Use it when
the story depends on distribution shape and raw observations rather than only
box summaries; keep CH4 and CO2 on independent y-scales.

**TTOP raster map variant:** Case-090 uses a two-panel horizontal map board:
left continuous TTOP magnitude, right binary permafrost distribution. Keep the
continuous colorbar bound to the left panel and the discrete class legend bound
to the right panel.

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
axes[0].imshow(ttop, cmap="RdBu_r", norm=TwoSlopeNorm(vcenter=0))
axes[1].imshow(class_map, cmap=discrete_cmap, norm=discrete_norm)
```

**Freeze-thaw raster parameter variant:** Case-091 uses a compact 2x2 map atlas
for four derived rasters: freeze start day, last frozen/melt day, freeze
duration, and actual frozen days. Keep a local colorbar per parameter because
DOY and duration units are not interchangeable.

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 8.6))
for ax, (arr, title, label) in zip(axes.flat, parameter_panels):
    im = ax.imshow(arr, interpolation="nearest")
    fig.colorbar(im, ax=ax, label=label)
```

**NSGA-II 3D Pareto variant:** Case-064 uses `fig = plt.figure(figsize=(12, 5))`
with two side-by-side 3D axes: `fig.add_subplot(121, projection='3d')` and
`fig.add_subplot(122, projection='3d')`. Keep `subplots_adjust(wspace=0.25,
left=0.05, right=0.95, bottom=0.10)` and apply the same `view_init(elev=25,
azim=-45)` plus identical x/y/z limits in both panels before comparing strength
grades or optimization groups.

**SHAP bar+beeswarm variant:** Case-010 uses `GridSpec(1, 4,
width_ratios=[1.15, 0.05, 1.20, 0.05], wspace=0.10)`: left importance-bar
panel, spacer, right beeswarm panel, and a dedicated feature-value colorbar
slot. The bar panel may contain an inset pie, so treat this as R1 content with
R9 overlay, not as a loose outside legend.
Case-047 is the compact two-axis form: `GridSpec(1, 2, width_ratios=[1, 1.2],
wspace=0.15)` plus `fig.add_axes([0.25, 0.2, 0.15, 0.25])` for the inset
category pie. Use it when the feature-value colorbar can attach to the beeswarm
axis and a separate colorbar slot is unnecessary.
Case-059 is the pure global/local form: `GridSpec(1, 3,
width_ratios=[0.8, 1.2, 0.05], wspace=0.05)` with left mean `|SHAP|` bars,
right same-order beeswarm, and one narrow colorbar column. Use it when there is
no pie/donut side summary and the feature-value legend needs to stay outside the
dense beeswarm rows.
Case-063 is the GS-XGBoost grouped-bracket form: `fig.add_gridspec(1, 2,
width_ratios=[1, 1.3], wspace=0.35)` with `figsize=(16, 6)`. Use it when the
left mean `|SHAP|` lane needs dashed physical-group brackets and the feature
value colorbar can be attached as an inset outside the right beeswarm axis
instead of consuming a full GridSpec slot.

**Inset raincloud prediction variant:** `fig.add_gridspec(1, 2, wspace=0.25)`
with each panel as a true-vs-predicted trajectory and a white residual raincloud
inset at `[0.55, 0.35, 0.40, 0.35]`.

**RF EFI + SHAP donut variant:** Case-052 uses
`fig.add_gridspec(1, 2, width_ratios=[1.2, 1.6], wspace=0.25)` with
`figsize=(15, 6)`. The left lane is a horizontal RF EFI importance bar chart;
the right lane is wider because hollow SHAP donut labels and grey leader lines
need outside breathing room.

**PCA score decomposition variant:** Case-053 uses a 1x2 horizontal board where
the left panel is signed PC1-PC3 stacked decomposition and the right panel is
total-score ranking. Both panels need a visible zero baseline; keep enough
horizontal room for rotated bar labels.

**Spacing:** `wspace=0.25` for separated panels, `wspace=0.10` when sharing y-axis.

---

## R1c — Asymmetric polar + waffle board

Use when a feature-importance table must show both feature-level contributions
and grouped contribution shares in one explainability board.

```python
fig = plt.figure(figsize=(16.5, 7.6), facecolor="white")
gs = GridSpec(
    2, 2,
    width_ratios=[1.18, 1.00],
    height_ratios=[1.00, 0.16],
    wspace=0.18,
    hspace=0.02,
)
ax_polar = fig.add_subplot(gs[:, 0], polar=True)
ax_waffle = fig.add_subplot(gs[0, 1])
ax_legend = fig.add_subplot(gs[1, 1])
```

Case-086 `polar_waffle_feature_importance` uses the left polar axis for
feature-level mean absolute SHAP bars and the right 10x10 waffle grid for
group-level contribution percentages. Do not collapse it to a plain radar or
pie chart; the two panels carry different aggregation levels.

---

## R1b — Two-panel vertical stack

Use when one sample/time axis must align a larger evidence panel with a smaller
diagnostic panel below it.

```python
fig = plt.figure(figsize=(10, 6))
gs = gridspec.GridSpec(2, 1, height_ratios=[2.5, 1], hspace=0.10)
ax_main = fig.add_subplot(gs[0])
ax_residual = fig.add_subplot(gs[1], sharex=ax_main)
plt.setp(ax_main.get_xticklabels(), visible=False)
```

Prediction/residual variant: Case-044 uses the top panel for observed vs
predicted line-marker series and the lower panel for residual scatter. Repeat
the train/test split line in both panels and keep residual y-scale separate
from the target magnitude scale.

**Stacked violin metric-board variant:** Case-074 uses
`plt.subplots(3, 1, figsize=(7, 11), sharex=True,
gridspec_kw={"hspace": 0.0})`. Use this when the same models are compared
across metric rows such as R2, MAE, and RMSE. Share the model x-axis, keep
independent y-scales per metric, hide upper-row x labels, and use dashed bottom
spines as panel separators.

---

## R2 — 2×2 Story Board (6 cases)

Use when: discovery + mechanism + validation + cohort/context (4 distinct claims),
or four parity tasks with identical actual/predicted grammar.

```python
fig, axes = plt.subplots(2, 2, figsize=(11, 9))
(ax_a, ax_b), (ax_c, ax_d) = axes
```

`Python科研绘图：一行代码实现 R² + 95% 置信区间的高级散点图`.

**Panel naming convention** (corpus-consistent):
- A = hero (top-left)
- B = orthogonal support (top-right)
- C = validation (bottom-left)
- D = context / cohort / summary (bottom-right)

**Spacing:** `hspace=0.3, wspace=0.3`. Tighten to `0.2/0.2` only when all four panels share x-axis.
Case-004 parity matrix uses `GridSpec(2, 2, wspace=0.25, hspace=0.25)` with
equal x/y limits per panel so the 45-degree line is not visually distorted.
Case-062 2D-PDP interaction contour matrix uses
`plt.subplots(2, 2, figsize=(12, 10))` plus
`subplots_adjust(wspace=0.30, hspace=0.30, right=0.88)`. The four panels are
parallel feature-pair response surfaces, and the right margin belongs to one
shared `Predicted Target` colorbar when contour levels are shared.
Case-078 XGBoost PDP contour variant uses the same response-surface grammar but
only three feature pairs, so prefer:

```python
fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2))
fig.subplots_adjust(left=0.07, right=0.88, bottom=0.18, top=0.88, wspace=0.32)
cax = fig.add_axes([0.905, 0.20, 0.018, 0.62])
```

The panel count follows the supplied `pdp_features` list; do not create empty
PDP axes.
Case-065 Spearman ML evaluation board uses `GridSpec(2, 2)` as an evidence
loop: top-left correlation structure, top-right SHAP/feature importance,
bottom-left train/test parity with an inset metric table, and bottom-right
external validation with a twin error axis. Keep all four panels active; do not
collapse the request to a standalone heatmap when model-fit and external
validation fields are present.
Case-079 biodegradation kinetics validation board also uses a 2x2 layout, but
the panels are an experimental evidence chain: long-term dual-axis operation,
two short-term kinetic errorbar panels, and one stage/zone boxplot summary.
Keep panel-specific time scales; do not share x-axes across days, hours, and
zone categories.
Case-070 prediction + SHAP/PDP board uses
`GridSpec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1.2])` with
`figsize=(14, 10)` and `subplots_adjust(wspace=0.3, hspace=0.3)`. Top row is
model validation (parity scatter plus residual distribution); bottom row is
explanation (global SHAP importance plus one local PDP/dependence panel).
Case-076 gradient-box metric dashboard also uses a 2x2 grid, but only three
cells are data panels.  Reserve the lower-right cell for a custom legend when
R2, MAE, and RMSE already consume the other cells:

```python
fig, axes = plt.subplots(2, 2, figsize=(9, 7))
metric_axes = [axes[0, 0], axes[0, 1], axes[1, 0]]
legend_ax = axes[1, 1]
```

Keep each metric panel on an independent y-scale and reuse the exact algorithm
color map across all panels.  Do not force the legend into a data axis for this
motif.
Case-068 feature-importance bar board uses
`plt.subplots(2, 2, figsize=(14, 11))` plus
`subplots_adjust(wspace=0.30, hspace=0.55, bottom=0.15)`. The left column is
absolute horizontal MDA/importance ranking; the right column is stacked
percentage composition with an x-position gap between physical environments.
Do not compare the right-column percentages as absolute importance values.

**Target-by-feature SHAP dependence variant:** Case-050 uses
`plt.subplots(2, 2, figsize=(15, 10))` plus
`fig.subplots_adjust(wspace=0.35, hspace=0.45)`. Use rows for prediction
targets such as CH4 and CO2 conversion, and columns for main features such as
surface area and reaction temperature. Each cell keeps its own secondary-feature
colorbar; do not normalize color across panels when the secondary feature
changes.

**Rotated 3x2 SHAP-dependence variant:** Case-039 uses
`plt.subplots(nrows=3, ncols=2, figsize=(12, 14))` with
`fig.subplots_adjust(wspace=0.3, hspace=0.4)` and a reserved right-side
`fig.add_axes([0.92, 0.15, 0.02, 0.7])` slot for one global interaction
colorbar. Use this when six feature-vs-SHAP panels are vertically stacked for
label space and all panels share one interaction-value color scale.

---

## R3 — 2×3 grid (6 cases)

Use when: 6 SHAP dependence panels, 6-feature ALE/PDP grid, 6-condition box, or CEJ-style adsorption isotherm condition storyboard.

```python
fig = plt.figure(figsize=(15, 9))
gs = gridspec.GridSpec(2, 3, hspace=0.35, wspace=0.25)
axes = [[fig.add_subplot(gs[r, c]) for c in range(3)] for r in range(2)]
```

Anchors: `期刊图表复现：多面板SHAP依赖图展示分子特征对自由基反应速率的非线性影响` (2,3 SHAP),
`期刊配图：基于极坐标系的多面板雷达图`,
`Python复现顶刊CEJ _ 拒绝手绘！如何用代码"量产"高颜值多面板吸附等温线图`.

**Case-089 PDP + ICE threshold variant:** use plain
`plt.subplots(2, 3, figsize=(16, 9))` for the six-panel RF/RFR mechanism grid:
the top row carries broad feature responses and the lower row carries local
zoom-in views for sensitive intervals such as low-concentration inputs.

```python
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes = axes.flatten()
for ax, conf in zip(axes, panels_config):
    draw_ice_background(ax, conf)
    draw_pdp_curve(ax, conf)
    draw_threshold_segment(ax, conf)
    draw_bottom_rug(ax, conf)
plt.tight_layout(pad=2.0, w_pad=1.5, h_pad=2.0)
```

Do not replace the lower zoom row with empty panels; if no zoom intervals are
supplied, reduce the grid to the number of real PDP/ICE panels.

**Tuning:**
- For SHAP/ALE bands: tighten hspace to `0.30` so dependence curves visually align
- For radar polar: keep hspace `0.40` because polar panels need vertical breathing room
- For adsorption isotherms: use `wspace=0.30`, `hspace=0.30-0.34`, shared x/y labels by outer panels, and one bottom-center legend for all methods
- Case-082 CEJ adsorption isotherm uses `fig = plt.figure(figsize=(15, 10))`
  with `GridSpec(2, 3, figure=fig, wspace=0.3, hspace=0.3)`. Panel ids are
  semantic letters `d` through `i`; keep them in `transAxes` outside the
  upper-left corner so they survive data-range changes.
- For target-aligned descriptor scatter matrices: use
  `plt.subplots(2, 3, figsize=(14, 8), sharey=True)` with `wspace=0.10`,
  `hspace=0.30`. Keep every descriptor on its native x-scale and label the
  shared target y-axis only on the left column.
- For multi-model parity grids: use `plt.subplots(2, 3, figsize=(12, 8),
  sharex=True, sharey=True)` with `wspace=0.10`, `hspace=0.15`; add
  figure-level Experimental / Predicted labels, not repeated axis labels in
  every panel. Every panel must keep equal aspect and identical limits.
- For model accuracy + stability boards: Case-081 uses
  `GridSpec(2, 3, figure=fig, wspace=0.35, hspace=0.45)` where each top-row
  cell owns a nested `subgridspec(2, 2, width_ratios=[6, 1],
  height_ratios=[1, 6], wspace=0.0, hspace=0.0)` for the marginal-joint
  prediction panel. The bottom row stays as ordinary axes for `R2`-`RMSE`
  Monte Carlo stability clouds.

---

## R4 — Three-panel horizontal (4 cases)

Use when: train→validate→test, or condition-by-condition triple.

```python
fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
```

`sharey=True` is the default in this layout because the 3 panels usually compare the **same** y-quantity across conditions.

---

## R4c — Independent-scale metric board

Use when: the figure compares the same models across incompatible performance
metrics such as MAE, RMSE, and R2, where each metric needs its own y-axis scale.

```python
fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 5), sharey=False)
metrics = ["MAE", "RMSE", "R2"]
plt.subplots_adjust(wspace=0.30)
```

Case-045 `multimetric_model_boxplot` variant:

- Each panel is one metric; do not share y because error magnitudes and R2 are
  not comparable on one numeric scale.
- X positions are identical model names in every panel so stability can be read
  metric-by-metric.
- Training/Testing grouped boxes keep one fixed hue mapping across all panels.
- Remove per-axis legends and use a single top-center figure legend when the
  split semantics are identical.

---

## R4d — Target-wise SHAP importance triptych

Use when: three targets/tasks each need a separate ranked horizontal mean
`|SHAP|` feature-importance panel.

```python
fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 6), sharex=False)
plt.subplots_adjust(wspace=0.40, left=0.08, right=0.98, bottom=0.15)
panel_labels = ["(a) SSA", "(b) Vt", "(c) NC"]
```

Case-046 `shap_mean_importance_triptych` variant:

- Keep x scales independent because target-specific mean `|SHAP|` magnitudes
  can differ by orders of magnitude.
- Use the same horizontal-bar grammar in every panel, but allow feature order
  to differ per target.
- Normalize the warm-to-cool color ramp locally within each panel; color is a
  within-target emphasis cue, not a globally comparable magnitude scale.
- Numeric labels on every bar are mandatory when close-ranked features need
  exact mean `|SHAP|` values.

---

## R4b — RF / ML diagnostic triptych

Use when: Random Forest / ML model benchmark requires one wide algorithm-comparison panel plus two diagnostic panels.

```python
fig = plt.figure(figsize=(14, 10.6))
gs = fig.add_gridspec(2, 2, height_ratios=[0.92, 1.00], wspace=0.22, hspace=0.23)

ax_benchmark = fig.add_subplot(gs[0, :])  # A: grouped train/test model metrics
ax_parity = fig.add_subplot(gs[1, 0])     # B: actual vs predicted
ax_residual = fig.add_subplot(gs[1, 1])   # C: predicted vs residual
```

Anchors: `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱`, `期刊复现：基于梯度提升树(GBDT)的多面板预测误差评估图`.

Rules:
- Top panel spans both columns and carries the algorithm-selection argument.
- Bottom panels must share diagnostic scale semantics where possible.
- Use `ml_model_performance_10`; RF/RFR should remain visually prominent when present.
- Keep figure legend bottom-center after the final legend contract pass, not inside any panel.

**GBDT horizontal variant:** Case-040 uses `plt.subplots(1, 3)` for a left-to-right
evidence chain rather than the RF top-wide 2x2 layout: material grouped bars,
observed/predicted grouped bars with a relative-error twin axis, and error
boxplots with jittered hollow-square raw points. Keep the custom IQR / mean /
data legend above the boxplot panel so the distribution summary is readable.

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
            ax.hist(..); ax.plot(kde(..), zorder=3)
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

**Single-axes bubble-correlation variant:** Case-011 keeps the n×n evidence
logic but renders it on one equal-aspect axes: center-aligned ticks, minor grid
cell boundaries, one bubble and one numeric `r` label per finite cell, plus an
outside colorbar. Use `draw_bubble_correlation_matrix` rather than building
subplots when the source style is the Materials Today red-blue bubble matrix.

**Single-axes lower-triangle heatmap variant:** Case-073 keeps the pairwise
correlation evidence in one large square axes, usually `figsize=(16, 16)`, with
the upper triangle masked out. Use this instead of an n x n subplot matrix when
the source emphasizes a triangular heatmap, grouped feature brackets, or an
oblique colorbar parallel to the matrix diagonal.

**Spearman + KDE pairplot variant:** Case-080 uses
`plt.subplots(nrows=n_vars, ncols=n_vars, figsize=(8, 8), dpi=100)` plus
`subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.05,
hspace=0.05)`. Keep the matrix square, place variable-name labels on the
diagonal, put Spearman tiles in the upper triangle, and reserve the lower
triangle for filled 2D KDE contours rather than scatter/regression cells.

**Hydrology 3x3 density-parity variant:** Case-069 uses
`fig, axes = plt.subplots(3, 3, figsize=(14, 10), sharex=True, sharey=True)`,
a figure-level vertical y-label via `fig.text(..)`, and
`subplots_adjust(left=0.08, right=0.96, top=0.96, bottom=0.08, wspace=0.35,
hspace=0.15)`. Rows are basin/region groups, columns are hydrology
model/mechanism variants, every cell keeps a common observed/simulated axis
scale, and the local density colorbar is attached to the right of its own cell
with `axes_grid1.make_axes_locatable`.

**Spacing:** `hspace=wspace=0.05` — must be tight or n×n looks loose.

---

## R6 — 1×4 narrow band (2 cases)

Use when: forest plot with 4 cohorts, multi-cohort survival comparison.

```python
fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
```

Anchors: `Python科研绘图复现_绘制多面板分组森林图展示生存分析风险比(HR)`.
Keep y tick labels only on the first axis; all other panels hide left labels
but retain aligned Model 1-3 y positions. Reserve top space for a shared
figure legend rather than repeating per-panel legends.

---

## R7 — Dense 2×6 lineup (2 cases)

Use when: 12-panel mass comparison (12 features × 1 method, or 6 metrics × 2 methods).

```python
fig = plt.figure(figsize=(20, 7))
gs = gridspec.GridSpec(2, 6, hspace=0.40, wspace=0.30)
```

Anchors: SHAP large-feature multi-panel, dependence plots with many features. Keep figsize wide (≥18 inches) to avoid label crash.

**Five-panel triple-y mechanical variant:** Case-054 uses
`GridSpec(2, 6, hspace=0.45, wspace=1.5)` with figsize `(10, 8)`. Top-row
axes span `[0:2]`, `[2:4]`, and `[4:6]`; bottom-row axes span `[0:3]` and
`[3:6]`, creating a balanced 3-over-2 board. Reserve the large `wspace`
because every panel owns two right-side y axes.

```python
fig = plt.figure(figsize=(10, 8))
gs = gridspec.GridSpec(2, 6, figure=fig, hspace=0.45, wspace=1.5)
axes = [
    fig.add_subplot(gs[0, 0:2]),
    fig.add_subplot(gs[0, 2:4]),
    fig.add_subplot(gs[0, 4:6]),
    fig.add_subplot(gs[1, 0:3]),
    fig.add_subplot(gs[1, 3:6]),
]
```

**Five-panel SHAP beeswarm matrix variant:** Case-057 uses
`GridSpec(2, 6, figure=fig, wspace=1.2, hspace=0.4)` with figsize `(24, 12)`.
The top row spans `[0:2]`, `[2:4]`, and `[4:6]`; the bottom row spans `[1:3]`
and `[3:5]` so the two lower SHAP panels are centered under the three upper
panels. Reserve wide `wspace` because long feature labels and `twiny` SHAP bar
axes need horizontal breathing room.

```python
fig = plt.figure(figsize=(24, 12))
gs = gridspec.GridSpec(2, 6, figure=fig, wspace=1.2, hspace=0.4)
regions_map = {
    "West": (0, slice(0, 2), "a"),
    "Northeast": (0, slice(2, 4), "b"),
    "National": (0, slice(4, 6), "c"),
    "Central": (1, slice(1, 3), "d"),
    "East": (1, slice(3, 5), "e"),
}
```

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

### Variant C — CEJ 4x4 attached sidecars

Use inside an outer multi-panel cell when the marginal strips must visually
grow out of the main axis with no internal gutter.

```python
inner = GridSpecFromSubplotSpec(
    4, 4, subplot_spec=outer_cell,
    width_ratios=[1, 1, 1, 0.3],
    height_ratios=[0.3, 1, 1, 1],
    wspace=0.0, hspace=0.0,
)
ax_top = fig.add_subplot(inner[0, :-1])
ax_main = fig.add_subplot(inner[1:, :-1], sharex=ax_top)
ax_right = fig.add_subplot(inner[1:, -1], sharey=ax_main)
ax_top.axis("off"); ax_right.axis("off")
```

### Variant D — nested 2x3 model matrix

Use when: six model/algorithm prediction diagnostics each need their own
main+top/right marginal system.

```python
outer = fig.add_gridspec(2, 3, wspace=0.32, hspace=0.36)
inner = GridSpecFromSubplotSpec(
    2, 2, subplot_spec=outer[i // 3, i % 3],
    width_ratios=[4, 1], height_ratios=[1, 4],
    wspace=0.05, hspace=0.05,
)
```

### Variant E — joint residual marginal performance

Use when: one prediction-performance diagnostic must combine parity, train/test
marginal density, and a residual panel with strictly shared actual-value x-scale.

```python
fig = plt.figure(figsize=(7, 8))
gs = gridspec.GridSpec(
    3, 2,
    width_ratios=[4, 1],
    height_ratios=[1, 4, 1.5],
    wspace=0.05,
    hspace=0.05,
)
ax_joint = fig.add_subplot(gs[1, 0])
ax_marg_x = fig.add_subplot(gs[0, 0], sharex=ax_joint)
ax_marg_y = fig.add_subplot(gs[1, 1], sharey=ax_joint)
ax_resid = fig.add_subplot(gs[2, 0], sharex=ax_joint)
```

The bottom residual axis must share x with the main parity axis; independent
x-limits can hide or invent heteroscedasticity. Top/right KDE sidecars are split
distribution context, not extra model-performance panels.

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

---

## R12 — Layered heatmap matrix (row-paired heatmaps + row colorbar)

```python
fig = plt.figure(figsize=(14, 10))
gs = fig.add_gridspec(
    4, 3,
    width_ratios=[1, 1, 0.05],
    wspace=0.10,
    hspace=0.30,
)
for row in range(4):
    ax_left = fig.add_subplot(gs[row, 0])
    ax_right = fig.add_subplot(gs[row, 1])
    ax_cbar = fig.add_subplot(gs[row, 2])
```

Use when: each row represents one station/cohort/condition, with two directly
comparable heatmaps and a narrow row-local colorbar. Use a shared symmetric
limit across all rows when the values are increments or deltas, so the zero
point stays visually comparable across the board.

---

## R13 — Seven-panel top-four bottom-three board

```python
fig = plt.figure(figsize=(14, 8))
gs = gridspec.GridSpec(2, 4, width_ratios=[1, 1, 1, 1], height_ratios=[1, 1])
gs.update(wspace=0.35, hspace=0.45)
subplots_config = [
    ("(a)AQI", 0, 0), ("(b)PM2.5", 0, 1), ("(c)O3", 0, 2), ("(d)PM10", 0, 3),
    ("(e)SO2", 1, 0), ("(f)NO2", 1, 1), ("(g)CO", 1, 2),
]
for label, row, col in subplots_config:
    ax = fig.add_subplot(gs[row, col])
```

Use when: seven small multiples need even panel sizes without forcing a blank
eighth panel to carry data. Keep the bottom-right GridSpec cell inactive and
avoid spanning the bottom row unless the final panel is meant to be a summary.

---

## R14 — Model-by-region density parity matrix

```python
fig = plt.figure(figsize=(20, 12))
gs = gridspec.GridSpec(
    3, 6,
    width_ratios=[1, 1, 1, 1, 1, 0.08],
    wspace=0.25,
    hspace=0.35,
)
for row_idx, model in enumerate(models):
    for col_idx, region in enumerate(regions):
        ax = fig.add_subplot(gs[row_idx, col_idx])
    cax = fig.add_subplot(gs[row_idx, 5])
```

Use when: model rows cross region/target columns and every cell is an
observed-vs-predicted density parity panel. The sixth column is a narrow
per-row colorbar slot, not a data panel. Keep equal x/y limits and equal aspect
inside every data cell so model comparisons are not visually distorted.

---

## R15 — Contour-search plus marginal-validation board

```python
fig = plt.figure(figsize=(14, 6))
gs = gridspec.GridSpec(4, 8, figure=fig, wspace=0.60, hspace=0.40)

ax_contour = fig.add_subplot(gs[:, 0:3])
ax_scatter = fig.add_subplot(gs[1:, 4:7])
ax_hist_x = fig.add_subplot(gs[0, 4:7], sharex=ax_scatter)
ax_hist_y = fig.add_subplot(gs[1:, 7], sharey=ax_scatter)
```

Use when: a figure must connect hyperparameter search evidence to final
observed-vs-predicted validation. The left panel owns the searched
hyperparameter space; the right nested marginal system owns prediction
accuracy and sample-density diagnostics.

Case-048 `contour_marginal_validation` rules:

- The contour optimum is bounded by the sampled search grid; do not call it a
  global optimum outside the plotted ranges.
- The marginal histograms must share the scatter axes so density/sparsity
  statements line up with the validation data.
- Keep the y=x parity reference and metric box in the scatter panel; the
  marginal panels qualify, but do not replace, the accuracy evidence.
- The RMSE colorbar belongs to the contour panel, not the parity scatter.

---

## Universal layout discipline (consolidated)

| Rule | Frequency | Notes |
|---|---|---|
| Panel labels A/B/C/D bold, 8-10 pt, at `(-0.12, 1.05)` axes fraction | most multi-panel cases | `ax.text(-0.12, 1.05, 'a', transform=ax.transAxes, fontweight='bold', fontsize=8)` |
| Outer-only tick labels in shared-axis grids | n×n, 1×N | use `sharex/sharey` or hide via `tick_params(labelbottom/left=False)` |
| Colorbar `shrink=0.6`, `pad=0.04`, beside heatmap panels | all heatmap cases | never inside the data rectangle |
| Row-paired heatmaps reserve a 0.05-width GridSpec column for per-row colorbars | layered heatmap matrix | use `width_ratios=[1,1,0.05]`; keep both heatmap columns equal width |
| Seven-panel boards use 2×4 GridSpec with the final bottom-right cell inactive | trend + distribution small multiples | avoids stretching the last row or shrinking the top row |
| Model-by-region density parity matrices reserve a 0.08-width final GridSpec column for row colorbars | dense regression matrix | use 5 equal data columns plus one narrow colorbar column |
| Contour-search plus marginal-validation boards use `GridSpec(4,8)` | tuning + validation composite | left contour spans all rows; right scatter spans lower rows with shared top/right marginals |
| Legend outside the data rectangle (bottom-center only) | all multi-condition cases | `bbox_to_anchor=(0.5, 0.01), loc='lower center'` with reserved bottom margin and a rounded frame; outside-right, top-center, and in-axes legends are forbidden in final output |
| `hspace=0.30`, `wspace=0.25` defaults for 2×N grids | majority | tighten to 0.10 when sharing axis, loosen to 0.40 when polar |

## Helpers contract

```python
def build_grid(recipe: str, fig=None, **opts) -> tuple[Figure, list[Axes]]:
    """Build a multi-panel figure from a recipe key.
    recipe: 'R0_single_panel' | 'R1_two_panel_horizontal' | 'R2_two_by_two_storyboard'
            | 'R3_two_by_three_grid' | 'R4_three_panel_horizontal'
            | 'R4b_rf_ml_diagnostic_triptych' | 'R4c_independent_scale_metric_board'
            | 'R4d_targetwise_shap_importance_triptych' | 'R5_n_by_n_pairwise'
            | 'R6_four_panel_band' | 'R7_dense_2x6_lineup' | 'R8_main_with_marginal'
            | 'R9_inset_overlay' | 'R10_asymmetric_top_wide' | 'R11_triple_y_axis'
            | 'R12_layered_heatmap_matrix' | 'R13_seven_panel_top_four_bottom_three'
            | 'R14_model_region_density_parity_matrix'
            | 'R15_contour_marginal_validation'
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
| R4c | `期刊复现：多面板箱线图对比多模型不同评估指标的误差分布` |
| R4d | `期刊复现：子图平铺展示比表面积与孔容的全局SHAP值与关键特征排行` |
| R5 | `期刊复现：Nature同款皮尔逊热力图`, `期刊配图：基于高斯核密度的3x3多面板散点图` |
| R6 | `Python科研绘图复现_绘制多面板分组森林图(HR)` |
| R7 | SHAP large-feature multi-panel cases |
| R8 | `复现 CEJ 顶刊神图：密度散点+边缘直方图`, `期刊复现：联合等高线热图与边缘分布图` |
| R9 | `复现顶刊：主图+嵌入雨云图`, `期刊复现：Nature Nanotechnology 经典画中画` |
| R10 | SHAP composite multi-panel cases |
| R11 | `期刊配图复现：Matplotlib 挑战多面板+三Y轴组合图` |
| R12 | `期刊配图复现：Python 绘制多面板分层热力图矩阵` |
| R13 | `期刊配图复现：Python 绘制"趋势+分布"时序混合图` |
| R14 | `期刊配图复现：如何用Python绘制多模型评估密度散点图矩阵` |
| R15 | `期刊复现：联合等高线热图与边缘分布图验证模型预测精度与参数寻优` |
