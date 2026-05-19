# 三明治图层法 (zorder Recipes)

The dominant rendering pattern across the 94-case template corpus. **61/94** explicitly use `zorder=` to stack chart layers in a deliberate order. This file documents the family-specific recipes — what goes on the bottom, what goes in the middle, what sits on top.

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

Case-008 `gam_log_residual_diagnostic` specialization:

- L1: `Non` background points in gray `#B0B0B0`, alpha 0.30.
- L2: black smooth confidence band, alpha 0.15, no edge.
- L3: black GAM/spline smooth line, linewidth 2.5.
- L4: semantic highlights in `Adj=#5FA896` and `In=#FBC15E`, reused in residual panel.
- L5: bold italic `R^2` transAxes text without bbox; panel labels above axes.

Case-067 `distance_decay_grouped_regression` specialization:

- L1: dense pairwise-distance scatter uses group color at low alpha around
  `0.15`, `s≈15`, and `edgecolor='none'`; points are evidence context, not the
  dominant layer.
- L2: each period/treatment gets its own translucent `fill_between` error band
  (`alpha≈0.20`) underneath the matching fit line.
- L3: draw one linear trend per group with the same color as the band; slope
  contrast is the scientific claim, so do not collapse groups into one OLS line.
- L5: group-colored `R^2` and `p` formula text sits in `transAxes` coordinates
  away from the dense scatter cloud; prune the legend to fit lines only.

Case-004 `parity_ci_matrix` specialization:

- L2: maroon 45-degree bisect line.
- L3: split-specific 95% CI shadow band.
- L4: split-specific regression line.
- L5: Training/Testing hollow markers.
- L10+: R2/RMSE metric box and panel letters anchored in `transAxes`.

Case-042 `target_aligned_descriptor_scatter_matrix` specialization:

- L0: light dashed grid in every descriptor panel, alpha about 0.3.
- L2: semi-transparent blue scatter points, alpha about 0.6.
- L3: white marker edge (`linewidths=0.5`) so dense descriptor clouds remain legible.
- Layout rule: share only the target y-axis; keep descriptor x-axes independent because their units are incompatible.

Case-064 `nsga2_3d_pareto_front` specialization:

- L1/L2: dense Pareto solution points are the front surface; keep them
  semi-transparent (`alpha≈0.6`), small, and edge-free so the 3D cloud remains
  readable.
- L5: selected engineering optima use red star markers with black edges,
  `s≈120`, and higher zorder than the Pareto cloud.
- Layout layer: the legend belongs above the 3D axes (`loc='upper center'`,
  `bbox_to_anchor=(0.5, 1.10)`) because in-axes legends occlude perspective
  points.
- Cross-panel rule: zorder alone does not make 3D panels comparable; enforce
  shared `view_init` and shared x/y/z limits before interpreting group
  differences.

Case-058 `prediction_experiment_external_stats` specialization:

- L0/L1: light grid stays behind sample-index scatter (`zorder=1` in source).
- L2: Training/Testing divider is a structural split cue at `zorder=2`; it separates sample regimes, not y=x parity.
- L3: Actual square markers and Predicted circle markers sit above the grid/divider at `zorder=3`; use thin white edges.
- L5: external red R2/RMSE rectangle and text live outside the axes in `transAxes` with `clip_on=False`, so they should not occlude points.
- Legend rule: use Line2D proxy artists when Actual/Predicted legends must be anchored independently at opposite upper corners.

Case-060 `model_region_density_parity_matrix` specialization:

- L0/L1: panel grid and CI band stay behind marks; the CI band supports the fit,
  not the density story.
- L2: red dashed 1:1 reference line anchors parity in every cell.
- L3: KDE-colored scatter points are density-sorted ascending so dense cores are
  drawn last and remain visible.
- L4: blue regression fit sits above the point cloud; it is the model-bias cue
  and should not be hidden by dense points.
- L5: bold R2/MAE/RMSE text sits in `transAxes`; row colorbars and the
  bottom-center legend are layout layers outside the data cells.

Case-069 `hydrology_density_parity_matrix` specialization:

- L0/L1: shared axis grid, common x/y limits, and the figure-level y-label are
  board structure; keep them consistent across the basin-by-model matrix.
- L2: red dashed 1:1 parity line repeats in every cell before the bias fit.
- L3: density-sorted `RdBu_r` scatter draws low-density points first so the
  high-density hydrology core remains visible.
- L4: black fitted regression line sits above the density cloud as the
  systematic-bias cue.
- L5: bottom-right NSE/r metric text stays in `transAxes`; local colorbars are
  panel sidecars created with `make_axes_locatable`.
- Colorbar rule: unlike Case-060 row colorbars, Case-069 uses one small local
  colorbar per panel because each basin-model cell owns its KDE density scale.

Case-092 `density_linear_regression_fit` specialization:

- L0: dashed grid, inward major/minor ticks on all four sides, and the thick
  black frame are reading aids; keep them below data and statistical layers.
- L2: density-sorted KDE scatter is the primary evidence. Draw lower-density
  points first and keep thin black marker edges so the dense red core remains
  legible.
- L3: the neutral gray OLS fit line and blue dashed 1:1 line sit above the
  point cloud; use distinct colors and line styles because they answer
  different questions.
- L5: the upper-left `Number` / equation / `R^2` / RMSE / MAE text block and
  qualitative `H` / `M` / `L` colorbar labels are explanatory overlays.
- Colorbar rule: the narrow right `make_axes_locatable` sidecar is a density
  legend, not a second data axis; it should not expand the main scatter limits.

### adsorption-isotherm multipanel (CEJ 2x3 condition storyboard)

```python
# L0: light dashed grid in every panel
ax.grid(linestyle='--', color='#D8D8D8', alpha=0.7, zorder=0)

# L2/L3: model curves below observations
ax.plot(pressure, q_or, color='#00CED1', marker='^', zorder=3, label='OR model')
ax.plot(pressure, q_il, color='#FF0000', marker='o', zorder=4, label='IL model')

# L5: observed and simulation points as hollow markers
ax.plot(pressure_obs, q_exp, linestyle='None', marker='o',
        mfc='white', mec='#1E90FF', mew=1.0, zorder=7, label='Experiment')
ax.plot(pressure_obs, q_gcmc, linestyle='None', marker='o',
        mfc='white', mec='black', mew=1.0, zorder=6, label='GCMC simulation')
```

The source article places a small legend in each lower-right panel. SciFig
translates that into a single bottom-center figure legend so markers never hide
low-pressure adsorption points.

### forest-plot (effect estimates with CI)

Source cases: HR multi-panel forest (Nature Comms), risk-ratio caterpillar.
Case-003 adds the `faceted_hr_forest` variant: four outcome panels share the
same Model 1-3 y rows, use a repeated HR=1 reference spine, and keep the model
legend at figure level above the panels.

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

Case-079 biodegradation validation variant:

- Panel A: left-axis influent scatter is the top raw-condition layer; right-axis
  removal lines sit below it but share the same day axis.
- Panels B/C: kinetic errorbar lines are the focal mechanism evidence; do not
  smooth away the SMX versus SMX+ATU inhibitor contrast.
- Panel D: boxplots and raw replicate overlays summarize zones/stages and should
  not share the dual-axis legend.

Case-054 `triple_y_mechanical_grid` specialization:

- L0: light panel grid and the asymmetric 2x6 layout; axis-color linking is a
  frame cue, not a plotted data layer.
- L1: grey CS bars on the main left axis, `zorder=2`, with black-edged error
  caps above the bar fill.
- L2: CS error bars, `zorder=3`, so uncertainty remains visible over the grey
  bars.
- L3: FS orange and STS green marker/errorbar layers, `zorder=4`, drawn on two
  separate right axes.
- Multi-axis rule: create two `twinx()` axes per panel and move the second
  right spine outward by 45 points before tinting the right spines/ticks to the
  orange and green series.

### signed PCA score bars

- L0: light y-grid behind both the PCA decomposition and total-score panels.
- L2/L3: PC component bars and total-score bars sit above the grid; signed
  stacked PC bars must use separate positive and negative bottoms.
- L4: zero baseline must be above bars in both panels so positive/negative
  interpretation remains visible.
- L5: polarity-aware rotated labels sit above the zero line and bars. Positive
  values offset upward with `va='bottom'`; negative values offset downward with
  `va='top'`.
- Required order for this case family: grid `0`, bars `3`, zero line `4`, text
  `5`.

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

Case-072 `nature_radar_canonical` specialization:

- L0: hide the default circular polar spine/grid and draw dashed polygon rings
  plus radial spokes first.
- L1: draw normalized condition fills at low alpha around `0.15`; fills are
  context, not the dominant evidence.
- L3: draw the thick condition outlines above fills, with navy Ge and crimson
  Si kept as the canonical bipolar palette.
- L5: draw vertex error bars last (`zorder=10`) so uncertainty remains visible
  at every physical-property spoke.
- Label rule: axis labels and physical max-limit annotations sit outside the
  unit radius; keep enough margin for the square polar canvas.

Case-066 `environment_radar_comparison` specialization:

- L0/L1: keep the radial scale fixed at `[0, 1]` and draw tick rings/grid behind
  every condition so polygon area comparisons are not rescaled per group.
- L2: draw semi-transparent season/condition fills at `alpha=0.20-0.25` below
  outlines; do not let one condition fully occlude the other.
- L3: draw closed condition outlines above fills, using style as a semantic
  channel (`Wet Season` solid blue, `Dry Season` dashed orange in the source).
- L5: place the legend outside the polar data area (`upper right`,
  `bbox_to_anchor` near `(1.3, 1.1)`) so dense spoke labels remain readable.
- Cross-panel extension: if expanded to multiple radar panels, lock spoke order,
  theta offset/direction, and radial scale before comparing shapes.

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

Case-057 `multipanel_shap_beeswarm_matrix` specialization:

- L0: `twiny` mean `|SHAP|` bars are background evidence, not a separate y
  ordering; keep them purple, alpha about 0.15, and behind all signed points.
- L2: the black SHAP zero reference line sits between background bars and
  points, `zorder=5`, and must repeat in every region panel.
- L4/L5: density-aware beeswarm points are the focal layer, `zorder=10`, with
  white marker edges and feature-value color encoding.
- Layout layer: one manual Feature value colorbar belongs to the board, not to
  individual panels; repeated per-panel colorbars break the matrix comparison.

Case-059 `shap_global_local_bar_beeswarm` specialization:

- L0: x-grid in the left mean `|SHAP|` bar panel and dotted row separators in
  the beeswarm panel remain low-salience guides.
- L2: the SHAP x=0 vertical reference line separates positive and negative local
  effects; keep it below dense points but above row separators.
- L3: left horizontal bars and right jittered beeswarm points are parallel
  evidence layers that must share one feature y-order.
- Colorbar layer: reserve a narrow GridSpec column for Feature value Low/High
  semantics; do not draw the colorbar inside either data panel.

Case-063 `gs_xgboost_shap_grouped_bar_beeswarm` specialization:

- L0: the left-lane x-grid and group bracket guide lines are explanatory
  scaffolding; keep bracket strokes dashed and below labels but above the bar
  background.
- L2: the gray SHAP x=0 line in the beeswarm lane separates local positive and
  negative contribution; it should sit below dense points.
- L3: mean `|SHAP|` bars and beeswarm points share one feature order after any
  merged structure-descriptor row is computed.
- L5: physical group labels and the inset Low/High colorbar are layout/text
  layers outside the data marks; they must not occlude beeswarm rows.

Case-065 `spearman_ml_evaluation_board` specialization:

- L0/L1: Spearman heatmap cells and SHAP bar baselines are structural evidence;
  keep grids, dendrogram/cluster brackets, and cell boundaries low-salience.
- L3: numeric `r` labels, supplied significance stars, parity y=x reference,
  and external RMSE/percent-error bars are interpretation layers above primary
  marks.
- L5: train/test hollow parity markers, SHAP value labels, and the inset
  RMSE/MAE/time table are focal audit layers.
- Multi-axis rule: the external validation panel may use `twinx()` for error
  bars, but the primary experimental/predicted marks must remain readable and
  the two y-axis labels should be color-linked.

Case-070 `prediction_shap_pdp_board` specialization:

- L0/L1: residual histogram bins, SHAP bar baselines, and PDP grid lines are
  support layers; keep them behind the evidence marks.
- L2: parity `y=x` and PDP zero/effect baselines are reference layers and must
  sit below scatter points but above the grid.
- L3: parity scatter, SHAP bars, and PDP scatter/trend are the focal evidence
  layers; the parity panel should keep equal aspect so the reference line is
  interpretable.
- L5: the in-axes `R^2`/metric box and panel labels are interpretation layers;
  reserve enough whitespace so they do not cover the densest prediction points.
- Story rule: read the board from prediction validity to residual bias to
  global SHAP importance to local PDP/dependence, not as four unrelated plots.

Case-068 `feature_importance_bar_board` specialization:

- L1/L2: left-column horizontal MDA/importance bars are absolute-rank evidence;
  keep their x scales local to the feature set and do not compare them directly
  to the right-column percentages.
- L2/L3: right-column stacked percentage bars use cumulative `bottom` arrays;
  each feature-group color must stay stable across both stacked panels.
- L4: x-position gaps such as `[0, 1, 2, 4, 5, 6]` are structural separators for
  physical environments, not missing data; keep tick labels aligned to the
  actual bar positions.
- L5: bottom brackets and temperature labels use data-axis coordinates with
  `clip_on=False`; reserve bottom margin so brackets survive tight export.
- Legend rule: use fit-for-purpose P/PT/CC legend ordering and avoid repeated
  legends in every panel when the same feature-group mapping applies.

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

Case-080 `spearman_kde_pairplot_matrix` specialization:

- L0: upper-triangle correlation tile facecolor is a background layer with one
  signed Spearman normalization across the matrix.
- L1: optional raw data points in the lower triangle are faint context only;
  keep them under the density field.
- L2: filled 2D KDE contours are the primary distribution layer for each
  variable pair.
- L3: thin white contour strokes can sit above the filled KDE to preserve the
  closed-density topology.
- L5: diagonal variable labels, upper-triangle `r` labels, and the outside
  Spearman colorbar are interpretation/layout layers, not data marks.

Case-073 `triangular_correlation_heatmap` specialization:

- L0: the upper-triangle mask is structural whitespace; keep it empty so group
  brackets and oblique colorbar have room.
- L1: lower-triangle heatmap cells use one zero-centered diverging norm across
  the whole matrix.
- L2: thin white cell separators keep dense 16-variable matrices readable.
- L3: coefficient annotations and significance stars sit centered in each
  rendered cell; text color flips by `abs(r)` for contrast.
- L5: group brackets and diagonal colorbar labels are outside-axis layout
  layers with `clip_on=False`; reserve margins for them before tight export.

Case-055 `layered_heatmap_matrix` specialization:

- L0: one `GridSpec(n_groups, 3)` frame with equal heatmap columns and a
  0.05-width row colorbar column; the layout carries the row-paired comparison.
- L1: heatmap cell color blocks use one board-level symmetric diverging norm
  (`TwoSlopeNorm(vcenter=0)`) so every row interprets neutral zero identically.
- L2: white cell separators (`linewidths=1.5`, `linecolor='white'`) sit above
  the colored cells and make dense matrices auditable.
- L3: centered numeric annotations are bold and compact; text color may flip
  for contrast, but values must remain supplied data, not inferred labels.
- L4: visible black panel spines and row-local vertical colorbars frame each
  site/cohort without adding extra data marks inside the heatmaps.

### 2D-PDP interaction contour matrix

- L1: filled `contourf` response surface is the base evidence layer; keep shared
  levels across panels before comparing high-response regions.
- L3: Q1 / median / Q3 contour lines sit above the fill as control-boundary
  cues. Use fixed semantics: Q1 blue dash-dot, median green solid, Q3 red
  dashed.
- L5: panel labels, axis labels, and the single outside colorbar are layout/text
  layers; they should not compete with local contour lines inside the data
  cells.
- Colorbar rule: use one outside `Predicted Target` colorbar when all panels
  share contour levels; repeated local colorbars weaken cross-panel comparison.
- Case-078 XGBoost variant: the same layer order applies to `subplots(1,3)` when
  the article supplies three feature pairs from `partial_dependence`.  Keep the
  shared levels/colorbar and exportable PDP grid table; do not add a blank fourth
  panel only to mimic the Case-062 2x2 shape.

### 3D-PDP surface panel

- L0/L1: transparent 3D panes and the dashed grid are spatial scaffolding; set
  pane alpha to zero before adding the surface so the back walls do not visually
  flatten the PDP response.
- L2: the bottom `contourf(..., zdir="z", offset=z_min)` projection is the
  footprint layer. Keep it below the lowest surface value and below any contour
  strokes.
- L3/L4: the `plot_surface` body is the focal evidence layer. Use edge-free
  `viridis` with `alpha≈0.85`; mesh edges usually add false ridges to PDP
  response surfaces.
- L5: a single `Prediction Response` colorbar and axis labels are layout/text
  layers. Do not add a second colorbar for the projection.
- Camera rule: use `view_init(elev=30, azim=-60)` and
  `set_box_aspect((1.05, 1.0, 0.78))` as the source-like default so the surface
  ridge and bottom projection are both readable.

### PDP + ICE threshold grid

- L1: ICE curves are the heterogeneity background. Use many thin gray lines with
  low alpha so they read as uncertainty/individual-response texture rather than
  separate highlighted series.
- L3: the PDP curve is the average mechanism evidence. Draw it as a thick
  `#0033CC` dashed line above every ICE curve.
- L4: red threshold vlines are interpretation guides, but keep them as local
  segments from the y-baseline to the PDP value; a full-height line overstates
  the threshold certainty.
- L5: bold red threshold labels, panel letters, and the one PDP legend are text
  layers. Place labels near the threshold point and avoid covering the steepest
  PDP slope.
- Rug layer: source-data rug ticks use x-axis transform coordinates and
  `clip_on=False`; they sit at the bottom edge as distribution support, not as
  a separate data series.

### TTOP permafrost raster map

- L1/L2: raster cells are the base evidence layer. Use a continuous diverging
  map for TTOP magnitude and a discrete class map for permafrost extent; do not
  mix them in one axes.
- L3: the zero-degree/threshold contour is the decision boundary and should sit
  above the continuous TTOP raster.
- L4: NoData or unmapped land-cover pixels stay visible as their own class in
  the binary map; they are not background decoration.
- L5: legends, colorbars, north arrows, and scale bars are map-layout layers.
  Keep the continuous panel's colorbar separate from the binary panel's class
  legend.

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

Case-081 `model_accuracy_stability_board` specialization:

- Top-row L1: one-to-one reference line stays below train/test points.
- Top-row L2: top/right marginal KDE fills are distribution context; keep them
  behind KDE outlines and outside the main data region.
- Top-row L3: train/test prediction points sit above the reference line with
  black edges for dense overlap.
- Bottom-row L2: mean `R2` and `RMSE` crosshair lines sit below the Monte Carlo
  stability cloud.
- L5: `R2`/RMSE and repeated-run summary boxes use translucent white `bbox`
  in `transAxes` above all points.

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

Case-076 dashboard boundary: repeat this same sandwich in each R2/MAE/RMSE
panel, but reserve the fourth 2x2 cell for a hand-drawn legend.  The legend cell
is a composition element, not a data panel, so do not count it as a fourth
metric axis.

### grouped-box median regression

- L0: alternating `axvspan` interval bands sit behind all distribution marks and
  replace the grid for bin readability.
- L2: paired box bodies, whiskers, and caps are the distribution layer; keep
  left/right offsets stable within every interval.
- L3: black median lines stay above the boxes because they are the regression
  input statistic.
- L4: series-colored dashed regression lines fit the per-interval medians and
  span the full categorical range.
- L5: the combined box-plus-line legend and color-matched `k` / `R` annotation
  text sit above the marks in axes coordinates.

### grouped environmental flux boxplot

- L0: omit or keep only a very faint y-grid; in this motif the log y-axis is
  the structural scale cue, not decoration.
- L2/L4: draw grouped `seaborn.boxplot` boxes, whiskers, medians, and fliers
  for each season nested inside each urbanization category.
- L5: keep the season legend above data marks, but render it once at figure or
  surviving-panel level when every gas panel uses the same hue mapping.
- Scale discipline: all flux values must be positive before `ax.set_yscale("log")`.
  CH4 and CO2 panels keep independent y limits because units and magnitude
  ranges differ.
- Palette discipline: keep Cool-dry `#4C72B0` and Warm-wet `#DD8452` stable
  across both gas panels so the single legend remains truthful.

### cell marker bar-scatter

```python
# L1: mean bar as background summary
ax.bar(x_pos[i], mean_val, 0.6, color=color, edgecolor='black',
       alpha=0.7, zorder=1)

# L2: uncertainty
ax.errorbar(x_pos[i], mean_val, yerr=std_val, fmt='none',
            ecolor='black', capsize=5, zorder=2)

# L3: raw samples must remain visible above summaries
ax.scatter(x_pos[i] + jitter, data_series, s=100, color=color,
           edgecolor='black', zorder=3)

# L4: group navigation rule above data, with y derived from max upper bound
ax.hlines(line_y, x_start, x_end, colors='black', linewidth=3, zorder=4)
```

Do not treat the top horizontal rules as p-value brackets unless p-values are
supplied.  Their role in Case-077 is to separate dorsal and ventral marker
blocks created by a non-uniform x-axis gap.

### polar waffle feature importance

- Polar L0: hide the default polar spine/grid and redraw structural concentric
  rings plus radial guide lines by hand.
- Polar L3: radial bars encode feature-level mean `|SHAP|`; white bar edges
  separate adjacent features.
- Polar L5: feature labels and numeric values sit outside the bar tips and
  rotate with the angular position.
- Waffle L1: 100 rectangles are the primary group-share marks; draw them on a
  Cartesian axis with equal aspect and no ticks.
- Waffle L5: group legend and percentages belong in the reserved lower-right
  GridSpec row, not over the waffle squares.

### greenhouse flux raincloud

- L1: half-violin KDE cloud is the distribution-shape layer; keep it behind all
  raw observations.
- L2: jittered raw observations are the audit layer, with white marker edges and
  alpha about 0.70 so dense clusters remain readable.
- L3/L4: the narrow transparent boxplot sits above cloud and rain points; black
  median and whisker strokes carry the statistical summary.
- Layout rule: use two independent-y flux panels for CH4 and CO2; remove
  redundant legends when color only repeats the urbanization categories.

### stacked violin metric board

- L1: full violin bodies are the distribution-shape layer; keep black outlines
  but do not let them overpower the summaries.
- L2/L3: narrow white boxplots sit above each violin and carry IQR stability;
  hide caps/median strokes when the red median point owns the median cue.
- L4: red median points with white edges sit above the boxplot layer.
- L5: color-matched numeric median labels sit beside each violin and should not
  overlap the violin body.
- Layout rule: zero vertical spacing and dashed separator spines are structural
  cues, not data marks; preserve them across all metric rows.

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

Case-056 `trend_distribution_hybrid` specialization:

- L0: the `GridSpec(2, 4)` board activates seven equal panels and leaves the
  bottom-right cell inactive; panel labels sit in transAxes coordinates.
- L1: scenario uncertainty bands use `fill_between(..., alpha=0.25, zorder=1)`.
- L2: scenario trend lines and markers share the same scenario color and use
  `zorder=2` so the mean stays readable over the band.
- L3/L4: terminal boxplots sit at artificial x positions beyond the forecast
  horizon, for example 2064/2066/2068, and must remain above the line/band
  layers. Reuse the scenario color for `boxprops.facecolor`.
- Legend rule: keep one scenario legend in a low-salience panel only; repeated
  legends are not data layers and will crowd the seven small multiples.

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

Despine (top + right spine off) is applied in **13/94 cases**. It's not strictly a zorder concern, and it is family-dependent rather than universal.

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
| grouped-box median regression | `Python绘制箱型图与回归线，一眼看穿数据趋势！` |
| time-series-pi | `期刊图表复现：基于预测区间与训练_测试划分的时序拟合效果对比`, `期刊配图复现 _ Python绘制"趋势+分布"时序混合图` |
| lollipop | `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向`, `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图` |
| inset-distribution | `复现顶刊 _ Python绘制"主图+嵌入雨云图"组合`, `期刊复现：Nature Nanotechnology 经典"画中画"组合图` |
