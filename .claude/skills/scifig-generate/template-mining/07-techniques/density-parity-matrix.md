# Density Parity Matrix

Source anchor: Case 015, `template/articles/期刊图表复现：叠加二维核密度的渗透汽化膜性能预测对比图_1777455816.md`.

Duplicate audit note: a later queue pass over the same Markdown was treated as
`duplicate_markdown_covered_by_case_015`; no new chart key or renderer is
required beyond this Case-015 `density_parity_matrix` contract. The closure
evidence lives in
`.workflow/case_studies/case_080_density_parity_matrix_audit/comparison_report.json`.

## Visual Grammar

- Use `scatter_regression` as the chart key; do not add a new registry key.
- Trigger `density_parity_matrix` when actual/predicted values are grouped by `panel` / `property` / `target` and the prompt or data indicates density, KDE, flux, separation, or parity diagnostics.
- Render a 1 x N board, usually N=2, with one property per panel.
- Compute 2D KDE via `gaussian_kde(np.vstack([x, y]))(xy)` and sort points by ascending density before plotting so dense red/yellow points sit above sparse blue points.
- Use `jet` by default for this source case; `viridis` is an acceptable safer alternative when requested.
- Draw a red solid 1:1 reference line above the density cloud.
- Put R2 and RMSE in a white, rounded `transAxes` metric box at top-left.
- Attach a vertical colorbar to each panel and label it `Density`.
- Keep equal x/y limits and equal aspect per panel.

## Variant: Model-by-region density scatter matrix

Use this when the matrix crosses model rows against region/target columns, such
as 3 models x 5 regions. This is still parity evidence, but the layout is a
larger comparison matrix rather than a 1 x N property board.

Rendering contract:

- Layout is `GridSpec(3, 6)` with five equal data columns and a final
  `0.08`-width colorbar column.
- Each data cell draws KDE-colored predicted-vs-observed scatter points sorted
  by ascending density before plotting.
- Every panel keeps equal x/y limits and `ax.set_aspect("equal",
  adjustable="box")`.
- Draw the 1:1 reference as a red dashed line, then a blue regression line with
  a translucent 95% confidence band.
- Put bold `R2`, `MAE`, and `RMSE` text at the top-left of each panel.
- Use one row-local density colorbar per model row and one bottom-center global
  legend for the reference and regression lines.

Anchor: `期刊配图复现：如何用Python绘制多模型评估密度散点图矩阵`.

Case-060 evidence lives in
`.workflow/case_studies/case_060_density_scatter_model_region_matrix/comparison_report.json`.

## Variant: Hydrology 3x3 density parity matrix

Anchor: `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能_1777453582`.

Use this when basin/region rows are crossed with hydrology model or coupling
mechanism columns, and each cell compares simulated values against MODIS or
observed ET.

Rendering contract:

- Layout is `subplots(3, 3, sharex=True, sharey=True)` with a global y-axis
  label placed by `fig.text`.
- Every cell computes Gaussian KDE density, sorts points by ascending density,
  and renders a density-colored scatter using `RdBu_r`.
- Every panel draws a red dashed 1:1 line and a black fitted regression line.
- Every panel places `NSE` and `r` text in axes coordinates, usually bottom
  right, using math italic variable names.
- Attach one local colorbar to every panel with `make_axes_locatable(...).
  append_axes("right", size="5%", pad=0.1)`.
- Keep x/y limits shared across the matrix so row/column comparisons remain
  fair.

QA signals: `densityParityPanelCount == 9`, `densitySortedPoints == true`,
`referenceLineCount == 9`, `fitLineCount == 9`, `metricTextCount == 9`,
`localColorbarCount == 9`, `sharedAxisLimits` is present, and `cmap == "RdBu_r"`.

Case-069 evidence lives in
`.workflow/case_studies/case_069_hydrology_density_parity_matrix/comparison_report.json`.

## Phase-3 Binding

`gen_scatter_regression` calls `draw_density_parity_matrix` when:

- the generator is standalone;
- `panel` / `facet` / `task` / `target` / `property` resolves to a column;
- actual and predicted numeric columns resolve; and
- `templateMotifs` / `specialPatterns` includes `density_parity_matrix` or `kde_parity_matrix`, or the detected text includes parity plus density/KDE cues.

The branch returns the first axis to preserve the existing generator contract.

## QA Counters

Runtime metadata must record:

- `templateMotifsApplied` contains `density_parity_matrix`.
- `densityParityPanelCount` equals the number of rendered panels.
- `densityParityScatterCount` equals the number of density point layers.
- `densityParityColorbarCount` equals the number of panel colorbars.
- `densityColorEncodingCount`, `referenceLineCount`, `metricBoxCount`, and `colorbarSlotCount` are at least the panel count.
- `densitySortedPoints` is true.
- For model-by-region matrices: `densityParityPanelCount == model_count * region_count`, `rowColorbarCount == model_count`, and every panel reports equal aspect.
- For hydrology 3x3 matrices: `localColorbarCount == densityParityPanelCount` when every panel owns its own density scale.

## Variant: Single-Panel Density Linear Regression Fit

Anchor: `python绘制分布密度线性回归拟合图_1778682475`.

Use this when the source is a single true-vs-predicted or observed-vs-estimated
scatter rather than a panel matrix, but the visual contract still depends on
KDE density coloring.

Rendering contract:

- Use `scatter_regression` as the chart key; do not add a separate public
  registry key.
- Compute local density with `gaussian_kde(np.vstack([x, y]))(xy)` and sort
  points by ascending density before drawing.
- Use `seismic_r` for the source-like diverging density palette when the prompt
  explicitly asks for this article style; otherwise safer perceptual palettes
  remain acceptable.
- Draw the fitted OLS line as a neutral gray line and the 1:1 agreement line as
  a blue dashed line so they cannot be confused.
- Put `Number`, fitted equation, `R^2`, `RMSE`, and `MAE` together in one
  upper-left `transAxes` text block.
- Add a narrow right colorbar with `make_axes_locatable(...).append_axes("right",
  size="2%", pad=0.03)` and qualitative `H` / `M` / `L` labels instead of raw
  density ticks when density magnitude is only a visual guide.
- Use inward major/minor ticks on all four sides and keep the black frame
  around the plot.

Case-092 evidence lives in
`.workflow/case_studies/case_092_density_linear_regression_fit/comparison_report.json`.
QA signals: `density_scatter_count == 1`, `point_count >= 300`,
`density_sorted_points` is true, `fit_line_count == 1`,
`one_to_one_line_count == 1`, `metric_text_count == 1`, `colorbar_count == 1`,
`hml_label_count == 3`, and `four_side_ticks` is true.
