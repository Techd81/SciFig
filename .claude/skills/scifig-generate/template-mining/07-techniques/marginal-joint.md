# Technique: Marginal Joint (center scatter + top/right marginals)

6/94 corpus cases. Density scatter or predicted-vs-actual diagnostic with side distributions.

**Anchor cases:**
- `复现 CEJ 顶刊神图_Python 绘制"密度散点+边缘直方图"多面板组合图_1777452838`
- `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图_1777453032`
- `期刊复现：联合等高线热图与边缘分布图_1777454914`
- `期刊复现：通过带边缘密度的联合残差图_1777454731`

## Hallmark elements

1. **Center panel** = density-colored scatter or contour KDE, density-sorted
2. **Top panel** = histogram of x; height-only, no scaffolding
3. **Right panel** = histogram of y rotated 90°; same color
4. **Perfect-fit diagonal** in center if predicted-vs-actual
5. **Marginal axes off** (`axis('off')`)
6. **Equal aspect ratio** in center panel
7. **Colorbar** on the side, labeled "Density"

## Case 007: CEJ density scatter + attached histograms

Source: `template/articles/复现 CEJ 顶刊神图 _ Python 绘制“密度散点+边缘直方图”多面板组合图_1777452838.md`.

The article's executable trick is not just "scatter with histograms"; it is a
tight nested marginal system:

- `GridSpecFromSubplotSpec(4, 4, width_ratios=[1,1,1,0.3], height_ratios=[0.3,1,1,1], wspace=0.0, hspace=0.0)` creates an attached top/right sidecar system.
- Center points are colored by `gaussian_kde(np.vstack([x, y]))(xy)` and sorted by ascending density before plotting, so bright dense points remain visible.
- Center density uses `GnBu_r`; both marginals use Teal `#69b3a2`.
- The 1:1 line is black dashed, semi-transparent, and above the point cloud.
- The metric/title plaque is a square white `transAxes` box with a black edge and high z-order.
- Top/right marginal axes call `axis('off')`; hidden ticks alone are not enough.

Case-072 duplicate-audit note:

- `复现 CEJ 顶刊神图 _ Python 绘制“密度散点+边缘直方图”多面板组合图_1777452838`
  reappears later in the markdown-learning order, but it is the same source
  already learned in Case-007. Keep the existing `marginal_joint` /
  `joint_marginal_grid` routing rather than minting another density-scatter
  template.
- The closure evidence lives in
  `.workflow/case_studies/case_072_cej_density_marginal_audit/comparison_report.json`.
  It verifies that Case-007 already captured five reference screenshots, the
  replica, comparison report, runtime probe, and runtime QA for attached
  marginal axes plus density encoding.

## Reference (CEJ-style)

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde

plt.rcParams.update({
    'font.family':      ['Times New Roman', 'Arial'],
    'mathtext.fontset': 'stix',
    'font.size':        6.5,
    'axes.linewidth':   1.5,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

# Data: predicted vs actual
np.random.seed(0)
N = 1500
y_actual = np.random.uniform(0, 100, N)
y_pred   = y_actual + np.random.normal(0, 8, N)

# === Density-sort ===
xy = np.vstack([y_actual, y_pred])
z  = gaussian_kde(xy)(xy)
idx = z.argsort()
y_actual_s = y_actual[idx]; y_pred_s = y_pred[idx]; z_s = z[idx]

# === Layout ===
fig = plt.figure(figsize=(8, 8))
gs  = GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
               hspace=0.05, wspace=0.05)
ax_top   = fig.add_subplot(gs[0, 0])
ax_main  = fig.add_subplot(gs[1, 0])
ax_right = fig.add_subplot(gs[1, 1])
ax_corner = fig.add_subplot(gs[0, 1]); ax_corner.axis('off')

# === Center: density scatter ===
sc = ax_main.scatter(y_actual_s, y_pred_s, c=z_s, cmap='GnBu_r',
                     s=8, alpha=0.85, edgecolor='white',
                     linewidth=0.2, rasterized=True, zorder=4)
# Perfect-fit diagonal
lo, hi = min(y_actual.min(), y_pred.min()), max(y_actual.max(), y_pred.max())
pad = (hi - lo) * 0.05
ax_main.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
             'k--', linewidth=1.2, alpha=0.6, zorder=6)
ax_main.set_xlim(lo - pad, hi + pad); ax_main.set_ylim(lo - pad, hi + pad)
ax_main.set_aspect('equal')
ax_main.set_xlabel('Actual')
ax_main.set_ylabel('Predicted')
ax_main.spines['top'].set_visible(False)
ax_main.spines['right'].set_visible(False)

# === Top marginal ===
ax_top.hist(y_actual, bins=60, density=True,
            color='#69b3a2', alpha=0.7, edgecolor='none', zorder=1)
ax_top.axis('off')

# === Right marginal ===
ax_right.hist(y_pred, bins=60, density=True, orientation='horizontal',
              color='#69b3a2', alpha=0.7, edgecolor='none', zorder=1)
ax_right.axis('off')

# === Colorbar ===
cax = fig.add_axes([0.93, 0.18, 0.012, 0.50])
cbar = fig.colorbar(sc, cax=cax)
cbar.set_label('Density', fontsize=11)

# === Metric box on center ===
r2  = 1 - np.sum((y_actual - y_pred)**2) / np.sum((y_actual - y_actual.mean())**2)
rmse = np.sqrt(np.mean((y_actual - y_pred)**2))
ax_main.text(0.05, 0.95, f"$R^2 = {r2:.3f}$\nRMSE = {rmse:.2f}",
             transform=ax_main.transAxes, va='top', ha='left',
             fontsize=12, fontweight='bold',
             bbox=dict(boxstyle='square,pad=0.4', fc='white', ec='black', lw=0.8),
             zorder=20)

plt.savefig('marginal_joint.pdf', dpi=600, bbox_inches='tight')
```

## Variant: Joint contour heatmap

Replace center scatter with `contourf` of 2D KDE for smooth bivariate density.

```python
xx, yy = np.meshgrid(np.linspace(lo, hi, 100), np.linspace(lo, hi, 100))
positions = np.vstack([xx.ravel(), yy.ravel()])
zz = gaussian_kde(np.vstack([y_actual, y_pred]))(positions).reshape(xx.shape)
cf = ax_main.contourf(xx, yy, zz, levels=12, cmap='GnBu_r', zorder=3)
ax_main.contour(xx, yy, zz, levels=12, colors='white', linewidths=0.4, zorder=4)
```

Anchor: `期刊复现：联合等高线热图与边缘分布图`.

## Variant: Contour-search + marginal validation

Anchor: `期刊复现：联合等高线热图与边缘分布图验证模型预测精度与参数寻优_1777454914`.

Use this when a model-validation figure must show both search-space behavior and
final prediction accuracy:

- Layout is `GridSpec(4,8)`: left panel spans `gs[:, 0:3]` for
  hyperparameter RMSE contour; right panel nests `gs[1:, 4:7]` scatter,
  `gs[0, 4:7]` top marginal, and `gs[1:, 7]` right marginal.
- Left panel uses `tricontourf` / `contourf` over the searched parameter grid,
  adds an optimum marker, and owns the RMSE colorbar.
- Right panel uses observed-vs-predicted scatter, a red `y=x` reference, and a
  compact R2/RMSE metric box.
- Top/right histograms must share x/y with the scatter. They are evidence about
  where validation is dense or sparse, especially at extremes.
- Keep the search-space conclusion bounded by the plotted hyperparameter
  ranges; the contour does not prove a global optimum outside that domain.
- Runtime status: current `scatter_regression` validates only the central parity
  relation. No public generator yet composes the contour-search plus
  marginal-validation board.

Case-048 evidence lives in
`.workflow/case_studies/case_048_contour_marginal_validation/comparison_report.json`.

## Variant: Joint residual marginal performance

Anchor:
`期刊复现：通过带边缘密度的联合残差图全面评估预测模型性能_1777454731`.

Use this when a single regression-performance figure must verify accuracy,
split distribution overlap, and residual bias at the same time:

- Layout is an asymmetric `GridSpec(3, 2)` with `width_ratios=[4, 1]`,
  `height_ratios=[1, 4, 1.5]`, and tight `wspace=hspace=0.05`.
- The main axes shows actual-vs-predicted parity scatter with a dashed `y=x`
  line below the points. Train points use `#1F77B4` at lower zorder/alpha;
  test points use `#FF7F0E` at higher zorder/alpha.
- The top KDE axis shares x with the main axes and summarizes actual values;
  the right KDE axis shares y with the main axes and summarizes predicted
  values. Overlay train/test densities rather than separating scales.
- The bottom residual axes shares x with the main axes and plots residual
  versus actual value with a dashed `y=0` baseline. Do not allow independent
  x-limits because that changes the bias/heteroscedasticity reading.
- Place R2/RMSE in a compact white `transAxes` metric plaque inside the main
  axes so the metrics stay attached to the split being shown.

Runtime status: current `scatter_regression` validates only the central parity
behavior. No public generator currently composes the full four-axis
marginal-residual diagnostic in one call.

## Variant: `make_axes_locatable` (cleaner code)

```python
from mpl_toolkits.axes_grid1 import make_axes_locatable

fig, ax_main = plt.subplots(figsize=(7, 7))
divider = make_axes_locatable(ax_main)
ax_top   = divider.append_axes("top",   size="20%", pad=0.05, sharex=ax_main)
ax_right = divider.append_axes("right", size="20%", pad=0.05, sharey=ax_main)
ax_top.tick_params(labelbottom=False)
ax_right.tick_params(labelleft=False)
```

Cleaner but less control over corner panel. Use for pure marginal-joint without colorbar inside.

Executable mapping: `scatter_regression` enters marginal-joint mode for standalone prediction/accuracy-vs-stability scatters when `visualContentPlan.useMarginalAxes`, the `joint_marginal_grid` motif, or the `marginal_joint` family is present. It calls the shared density-color and marginal-axis helpers, keeps split markers as hollow overlays when supplied, uses the CEJ defaults (`GnBu_r`, density-sorted paint order, `#69b3a2` marginals, tight top/right gaps), reserves top/right sidecar axes, and adds a slim density colorbar outside those sidecars when density color encoding is active.

## Variant: nested model matrix

Anchor: `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图`.

Case-084 evidence lives in
`.workflow/case_studies/case_084_nested_marginal_joint_matrix/comparison_report.json`.

`gen_scatter_regression` enters `nested_marginal_joint_matrix` mode when model /
algorithm, split, actual, and predicted roles are present and the motif is
planned. It builds a 2x3 outer model matrix; each model cell uses
`GridSpecFromSubplotSpec(2, 2, width_ratios=[4,1], height_ratios=[1,4])`.
Train and test colors must be shared between the main scatter and both marginal
KDE sidecars.

QA cues: `modelPanelCount == n_models`, `marginalAxesCount == n_models * 2`,
`metricBoxCount == n_models`, `referenceLineCount == n_models`, and one shared
train/test legend should replace repeated per-panel legends.

## Variant: train/validation OLS CI with marginal histograms

Anchor: `【Python绘图！用Matplotlib+Statsmodels打造带边缘直方图的炫酷散点回归分析`.

Case-096 evidence lives in
`.workflow/case_studies/case_096_train_val_marginal_ols_ci/comparison_report.json`.

Use this when the prediction diagnostic has one true-vs-predicted main scatter,
separate train and validation point clouds, split-specific OLS fits, and
marginal histograms rather than density sidecars.

Rendering contract:

- Layout is a 2x2 `GridSpec` with `[main, right histogram]` on the bottom row,
  `[top histogram, blank corner]` on the top row.
- Top histogram shares the main x-axis and shows true/observed value
  distributions for train and validation with the same split colors as the main
  scatter.
- Right histogram shares the main y-axis and shows predicted/fitted value
  distributions for the same splits.
- Fit train and validation separately; draw two OLS fit lines and two
  translucent 95% mean-confidence bands.
- Keep the dotted 1:1 line as the agreement reference, separate from the two
  statistical fit lines.
- Put sample counts, equations, `R^2`, RMSE, and MAE for both splits in one
  upper-left text box.
- Hide duplicate tick labels on the sidecar axes while preserving their
  frequency labels.

QA signals: `main_scatter_count == split_count`, `top_histogram_count == 1`,
`right_histogram_count == 1`, `blank_corner_axis == true`,
`ols_fit_line_count == split_count`, `ols_ci_band_count == split_count`,
`one_to_one_line_count == 1`, `metric_text_box_count == 1`, and
`shared_axis_sidecar_count == 2`.

## Discipline rules

| Rule | Reason |
|---|---|
| Density-sort the center scatter | Bright dense regions paint last |
| `rasterized=True` on dense scatter | Keep PDF under 5MB |
| Marginal axes `axis('off')` | They're decoration, not data |
| Same color for both marginals | They show the same population |
| Center `set_aspect('equal')` when predicted-vs-actual | Diagonal is meaningful |
| Colorbar separate `add_axes` outside the grid | Don't steal width from main |
| `wspace/hspace` or sidecar gaps near zero | Marginals must look attached to the main panel |
| Square white metric box with high z-order | Keeps model evidence readable over dense points |

## QA contract

- `marginalAxesCount`: 2
- `densityColorEncodingCount`: ≥1 in center
- `marginalAxesOff`: True (`axis('off')` applied)
- `centerAspectEqual`: True for predicted-vs-actual
- `perfectFitCount`: ≥1 for predicted-vs-actual
