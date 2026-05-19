# ML Model Diagnostics Technique

Use this deep-dive whenever `templateCasePlan.families` contains `ml_model_diagnostics`, or when the selected bundle key is one of `rf_model_performance_report`, `model_accuracy_stability_board`, `multimetric_model_boxplot`, `hyperparameter_stability_bubble_heatmap`, `h_statistic_contour_dependence_board`, `pdp_ice_threshold_grid`, `pdp_3d_surface_panel`, `neural_architecture_metric_storyboard`, `neural_architecture_topology`, `neural_training_dynamics`, `incremental_feature_selection_curve`, `feature_selection_weight_performance_board`, `prediction_experiment_external_stats`, `rf_feature_importance_shap`, `feature_importance_bar_board`, `spearman_ml_evaluation_board`, `pso_shap_optimization_framework`, or `classifier_validation_board`.

## Anchor Cases

- `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱_1777456409.md`
- `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md`
- `期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化_1777456510.md`
- `期刊复现：基于梯度提升树(GBDT)的多面板预测误差评估图_1777456338.md`
- `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图_1777454599.md`
- `期刊配图复现 _ Python绘制机器学习“预测-实验”对比图_1777452713.md`
- `期刊配图：基于机器学习的Spearman相关性热力图与模型预测效果组合分析_1777456565.md`
- `期刊配图：基于组合多面板条形图对比多条件下的机器学习特征重要性_1777453942.md`
- `期刊配图：多面板预测散点与SHAP局部依赖特征解释组合图_1777456052.md`
- `期刊配图：基于集成模型的3D部分依赖图(PDP)非线性交互效应可视化（附代码）_1778681006.md`
- `机制解释图复刻：基于Random Forest与局部依赖图(PDP)揭示特征关键阈值（附完整代码）_1778682927.md`

## RF Performance Triptych

When columns include `model` / `algorithm` plus `Training` / `Testing` / `R2` / `AUC` / `RMSE` / `MAE`, clone the RF triptych before falling back to generic grouped bars:

1. Top panel: horizontal grouped bar benchmark. Sort algorithms by test metric; highlight RF/RFR if present; keep train/test colors stable (`Testing #9BCBEB`, `Training #F6CFA3`).
2. Bottom-left: predicted-vs-actual parity scatter. Use train/test marker encoding (`Train` open square, `Test` open triangle), black 1:1 dashed line, and a compact metric table.
3. Bottom-right: residual-vs-predicted scatter. Use zero reference line in deep red (`#B00000`), light grid, and a short in-plot bias note.

Layout intent: `ml_model_performance_triptych` uses a 2x2 grid where the benchmark bar spans the top row and parity/residual diagnostics occupy the bottom row.
Executable fallback: `grouped_bar` renders the sorted RF-highlighted benchmark, accepts both long `metric/value` rows and wide aggregate metric columns (`AUC`, `F1`, `precision`, `recall`, etc.), folds very long model names into y-axis labels, adds a compact right-side metric table for the top model when wide metrics are present, expands left/bottom margins for dense model lists, and moves 5+ train/test/validation/external split legends to a bottom-centered figure legend. Standalone `scatter_regression` renders the train/test parity lane as a density-colored marginal joint diagnostic with 1:1 reference and R2/RMSE/MAE box, embedded `scatter_regression` keeps the compact parity lane, and `residual_vs_fitted` renders the residual lane with red zero reference plus bias/SD note.

## Model Accuracy + Stability Board

Use this when multiple models need both single-run prediction accuracy and
repeated-run stability evidence, such as Monte Carlo `R2`, `RMSE`, and `STD`.
This is more specific than a standalone `marginal_joint` diagnostic: every model
column must pair an upper nested prediction panel with a lower stability cloud.

Required composition:

- Use a `2 x n_models` grid, typically `GridSpec(2, 3)` for RF, LightGBM, and
  GBDT.
- Top row: each model cell uses a 2x2 `subgridspec` with a main true-vs-predicted
  scatter, top x-distribution KDE, and right y-distribution KDE.
- Top-row markers encode train/test with stable colors, black edges, and a
  dashed one-to-one line below the points.
- Bottom row: each model gets an `R2`-vs-`RMSE` Monte Carlo scatter cloud, colored
  by `STD` or another supplied stability/spread metric.
- Mean `R2` and mean `RMSE` crosshair lines are allowed only when those values
  are computed from the repeated-run table.
- Put compact metric/stat boxes in `transAxes` with a translucent white bbox so
  the labels remain legible over dense points.

### Prediction-Experiment External Stats Panel

Use this when the evaluation table is indexed by sample/run order and contains
paired actual/experimental and predicted/fitted values. This is not parity
geometry: preserve the sample index on x so train/test regime changes and local
tracking errors remain visible.

Required contract:

- Overlay Actual and Predicted on one sample-index axis; use square actual
  markers and circle predicted markers with thin white edges.
- Split Training and Testing with a dashed vertical divider at the sample
  boundary.
- Use `Line2D` proxy artists for Actual/Predicted legends when the legend layout
  is part of the composition.
- Place R2/RMSE metrics in a red external `transAxes` rectangle with
  `clip_on=False` and reserved right margin.
- Runtime boundary: `scatter_regression` still validates only
  actual-vs-predicted parity; record a gap until a registered generator creates
  the external stats panel and dual proxy legends.

### GBDT Prediction-Error Triptych

Use this when model evidence combines material/category response levels,
sample-wise observed-vs-predicted comparison, and global relative-error
distribution:

- Layout is a horizontal three-panel chain, not the RF top-wide 2x2 triptych.
- Left panel: grouped bars compare material or condition responses across
  analytes/classes.
- Middle panel: observed and predicted values are adjacent bars on the primary
  axis; relative error is a line on a secondary y-axis because it has different
  units and scale.
- Right panel: boxplots summarize baseline vs optimized model errors, with
  jittered hollow-square raw points overlaid so the distribution is auditable.
- Custom legend entries for IQR box, mean line, and raw data glyph are part of
  the evidence contract; do not replace them with a generic boxplot legend.
- Runtime status: current `residual_vs_fitted` validates only a single
  residual diagnostic panel. No public generator yet composes the full GBDT
  material/prediction/error triptych.

### Multi-Metric Model Boxplot Board

Use when model evaluation data include repeated fold, bootstrap, or resampling
values for several metrics such as MAE, RMSE, and R2, with a stable
Training/Testing split:

- Layout is a horizontal `1x3` metric board with `sharey=False`; MAE/RMSE error
  magnitudes and R2 scores must keep independent y-axis scales.
- Each panel uses the same model order on the x-axis so readers compare
  distribution stability, not only mean performance.
- Draw Training and Testing as grouped boxes with a fixed split palette:
  Training `#4A90E2`, Testing `#F5A623`.
- Box semantics are the evidence: median is central performance, IQR is
  stability, whiskers/outliers expose fold-level extremes. Do not collapse this
  board into mean bars when repeated values are available.
- Remove per-axis legends and use one top-center figure legend only when every
  panel uses the identical split mapping.
- Runtime status: current `box_strip` validates only one metric distribution
  panel. No public generator yet composes the full independent-y MAE/RMSE/R2
  grouped boxplot board.

## Neural Architecture Topology

When columns include `layer`, `module`, `component`, `block`, `source`, `target`, `params`, `units`, `channels`, `heads`, `attention`, `transformer`, `encoder`, or `decoder`, clone an architecture-topology board before falling back to generic flow diagrams:

- Use rounded module blocks rather than plain nodes. Put the layer or module name on the first line and compact type/unit/parameter tags below it.
- Group modules by stage or block with pale stage bands. Keep all labels inside the axes so the figure survives layout QA.
- Use directed arrows for source-target edges or sequential layer order. Encode supplied edge weights with line width and keep legends out unless a real categorical mapping is needed outside the plotting area.
- If edge/module metrics such as latency, FLOPs, memory, throughput, cost, parameters, or edge weights exist, prefer `model_architecture_board`: topology spans the top row, metric profile occupies panel B, and edge signal occupies panel C.
- If the same AI/ML profile also includes epoch/step training history, keep `training_curve` as the first support recommendation for the architecture board. Do not degrade architecture-plus-training requests into generic grouped bars or plain line charts.
- Use the compact in-panel metric dashboard only for plain `model_architecture` single-panel fallback.
- Pair the architecture hero with `training_curve` or `lollipop_horizontal` support panels only when training or explainability fields are also available.
- Executable fallback: `model_architecture_board` creates a three-axis architecture metric storyboard from one edge table; `model_architecture` detects node tables or edge tables, derives a compact DAG/sequential layout, draws stage bands, directed arrows, module blocks, edge-weight strokes, a module/edge/parameter summary box, and an edge/module metric dashboard when metric columns exist.

## Incremental Feature Selection

When columns include `n_features`, `top_k`, `feature_count`, `ablation`, `AUC`, `F1`, or `accuracy`, clone the incremental feature-selection curve:

- Use a multi-model line plot with distinct marker shapes and the `ml_model_performance_10` palette.
- Sort legend order by final score.
- Mark the elbow/decision point with vertical and horizontal dashed references.
- Highlight RF when present, but keep other model trajectories visible for benchmark credibility.
- Executable fallback: `line` detects `n_features` / `top_k` / `feature_count` / `ablation` tables, sorts model trajectories by final score, gives RF the strongest stroke, and marks the decision elbow with dashed guides plus an in-panel callout.

Case-013 executable contract:

- `visualContentPlan.templateMotifs` should include `incremental_feature_selection_curve`.
- Default decision point is `featureSelectionDecisionX=6` when the prompt/data does not supply a different elbow.
- Use `featureSelectionPalette` from the article (`#E64B35`, `#4DBBD5`, `#00A087`, `#3C5488`, `#F39B7F`, `#8491B4`, `#91D1C2`, `#DC0000`, `#7E6148`) and marker cycle `o/v/^/s/D/p/*/h/X`.
- Keep zig-zag variation; do not smooth the trajectories.
- Put the legend outside-right in standalone mode with `bbox_to_anchor=(1.02, 0.5)`.
- Runtime QA should record `featureSelectionModelCount`, `featureSelectionDecisionX`, `referenceLineCount`, `externalLegend`, and `rfHighlighted`.

Legacy duplicate-audit note (older queue numbering):

- `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272`
  reappears later in the markdown-learning order, but it is the same source
  already learned in Case-013. Keep the existing
  `incremental_feature_selection_curve` motif and ML model diagnostics routing
  rather than minting another multi-model performance template.
  It verifies that Case-013 already captured four reference screenshots, the
  replica, comparison report, runtime probe, and runtime QA for nine model
  curves, the `n=6` decision guide, RF highlighting, zig-zag preservation, and
  the external legend.

## Feature Selection Weight + Performance Board

Use this when recursive feature selection or feature-subset search provides
both ranked feature weights and a validation score at each selection step:

- Layout is vertical `2x1` with a shared x/order axis.
- Top panel shows contiguous selected/removed feature-weight bars. Use a
  stable red/blue split so the cutoff is visible before reading the score
  curve.
- Bottom panel shows model-performance evolution across the same feature order.
  Mark the actual optimum with a red star, not the last feature by default.
- Use an arrow/callout for the chosen feature subset only when the optimum or
  selected combination is supplied by the data or explicitly inferred from the
  score maximum.
- Runtime status: current `grouped_bar` validates the upper importance-bar
  layer only. No public generator yet composes the lower performance curve,
  optimum marker, and feature-subset annotation.

## Neural Training Dynamics

When columns include `epoch`, `step`, `iteration`, `train_loss`, `training_loss`, `val_loss`, `validation_loss`, `accuracy`, `val_accuracy`, `learning_rate`, or early-stopping markers, clone the training-history board before generic time-series plotting:

- Use convergence curves rather than bare line charts. Plot train and validation metrics together, and visually distinguish validation traces.
- Add validation-gap shading when train and validation loss are both present.
- Mark the best epoch using validation loss when available, otherwise validation accuracy / AUC / F1.
- Report compact final/best metrics in-panel so a standalone training curve reads like a model diagnostic, not a logging artifact.
- Executable fallback: `training_curve` detects wide or long training-history tables, plots up to six loss/score traces, shades the generalization gap, marks the best epoch, and keeps legends outside the plotting area for final render QA.

## Hyperparameter Stability Bubble Heatmap

Use when model-tuning data include repeated scores across one or more
hyperparameters and a joint grid-search table:

- Layout is a 2x2 board. Panels A-C show single-parameter sensitivity with
  replicate boxplots plus an overlaid mean trend line.
- Panel D shows the joint tuning grid as a bubble heatmap: x/y are two
  hyperparameters, color is the model score, and bubble size is a third cost,
  runtime, variance, or stability metric.
- Keep panel D as discrete evidence. Do not smooth or interpolate it into a
  continuous surface unless the user supplies dense response-surface data.
- Runtime status: the public `bubble_matrix` generator verifies panel D only.
  There is not yet a complete packaged 2x2 hyperparameter-stability board, so
  generated reports should disclose that gap when they use this case as a
  planning reference.

## RF Feature Importance + SHAP

When columns include `feature`, `importance`, `gain`, `permutation`, `shap`, or `mean_abs_shap`, clone the RF EFI + SHAP board:

Case-052 exact contract (`rf_efi_shap_donut`):

- Layout is `fig.add_gridspec(1, 2, width_ratios=[1.2, 1.6], wspace=0.25)`
  with `figsize=(15, 6)`.
- Left lane: RF EFI horizontal bars sorted ascending, colored by a sequential
  blue gradient from `#D6EAF8` to `#5A9BBF`, with red numeric labels at bar
  ends.
- Right lane: hollow SHAP donut built from mean `|SHAP|`, sorted separately
  from EFI, with external labels and grey elbow leader lines.
- Add a visible interpretation boundary: EFI scores and mean `|SHAP|` values
  are different statistical units, so the board supports rank agreement rather
  than absolute cross-panel numeric comparison.
- If donut is unsupported for the data, use `lollipop_horizontal` plus
  `dotplot`, but preserve the left/right asymmetric composition and feature
  ordering.
- Runtime status: `lollipop_horizontal` validates only the ranked importance
  fallback lane. No public generator currently composes the exact EFI gradient
  bar plus SHAP hollow-donut callout board in one call.

## Feature Importance Bar Board

Use this when feature-importance evidence is split between absolute ranked
importance values and condition-wise percentage composition, especially in
materials informatics or environmental model-sensitivity settings.

Required composition:

- Layout is a 2x2 board: horizontal MDA/importance rankings in the left column,
  stacked percentage bars in the right column.
- The horizontal bars show absolute importance and should be sorted within each
  feature family.
- The stacked bars show within-condition composition; do not imply direct
  absolute comparison across stacked panels.
- Use explicit x-position gaps such as `[0, 1, 2, 4, 5, 6]` when one axis groups
  multiple physical environments.
- Draw bottom bracket annotations outside the axis with `clip_on=False` to label
  environment groups such as `0 deg C` and `25 deg C`.
- Keep stacked group colors stable for P/PT/CC-style feature groups; the article
  palette is deep purple `#2B0E68`, orange `#D26E17`, and gray-green `#466B6C`.

Case-068 acceptance signals: `panelCount == 4`, `horizontalBarCount > 0`,
`stackedPanelCount == 2`, `stackedBarSegmentCount > 0`,
`bottomBracketCount >= 4`, `xGapPositions` includes a center gap, and
`exportDpi == 600`.

Current executable boundary: `stacked_bar_comp` validates one part-whole stacked
panel only. Until a full-board generator exists, compose the 2x2 board manually
and record the gap instead of reducing the request to a single grouped bar.

## Spearman ML Evaluation Board

Use this when the prompt combines Spearman/correlation screening with ML explanation, parity accuracy, and external validation. Treat it as a manuscript evidence board, not as four unrelated chart requests.

Required composition:

- Panel A/C: Spearman correlation heatmap with all cells annotated by `r` and significance stars when p-values are supplied.
- Panel B/D: SHAP or mean absolute SHAP importance bars, preserving feature order and optional cluster/dendrogram brackets when group membership is supplied.
- Panel C/E: train/test predicted-vs-observed parity scatter with hollow markers, 1:1 reference, and a compact inset table for RMSE, MAE, R2, or runtime metrics.
- Panel D/F: external validation panel combining experimental/predicted points on the primary axis with RMSE, percent error, or residual bars on a twin axis.

Case-065 acceptance signals: `panelCount == 4`, `spearmanHeatmapCells > 0`, `significanceStarCount > 0` only when p-values exist, `shapBarCount > 0`, `parityPointCount > 0`, `insetTableCount == 1`, `externalTwinAxis == true`, and `externalBarCount > 0`.

Current executable boundary: `heatmap_symmetric` can validate only the correlation panel. Until a registered full-board generator exists, compose the board with `GridSpec(2, 2)` and record the gap rather than degrading the request to a standalone heatmap.

## PSO / Pareto Optimization + SHAP

When columns include `objective_1`, `objective_2`, `obj1`, `obj2`, `cost`, `latency`, `complexity`, `rank`, `pareto_flag`, `optimal_flag`, `iteration`, or explicit PSO/NSGA/Pareto wording, clone the optimization + explainability framework instead of treating Pareto as category frequency:

- Use `radar` for model/solution metric signatures, `lollipop_horizontal` or `dotplot` for SHAP-style explanation, `heatmap_triangular` for objective/feature correlation context, and `pareto_chart` for the tradeoff front.
- Highlight Pareto / optimal points only when a flag or rank column exists; otherwise show the tradeoff cloud and state that no Pareto flag was supplied.
- Use a red diamond + connecting line for the supplied Pareto/top-rank front, a rank or candidate-index colorbar, and an in-panel best-candidate callout.
- Executable fallback: `pareto_chart` detects `pso_shap_optimization_framework` / optimization patterns plus two numeric objective columns, switches from categorical bars to a multi-objective tradeoff scatter, uses supplied Pareto/optimal flags or ranks for front highlighting, and keeps embedded labels compact for render QA.

Case-006 composition discipline:

- Treat this as a framework bundle, not a single chart. The visual story is
  prediction -> optimization -> explanation -> decision.
- Use a workflow strip only when the user requests framework/process context;
  otherwise spend the canvas on evidence panels.
- Minimum evidence trio: model/solution metric signature (`radar`), objective
  tradeoff front (`pareto_chart`), and global explanation (`lollipop_horizontal`
  or SHAP-compatible `dotplot`).
- Do not claim a Pareto front unless `pareto_flag`, `optimal_flag`, rank, or a
  supplied non-dominated set exists. Without that evidence, show only the
  tradeoff cloud and label it as candidates.

Case-071 duplicate-audit note:

- `机器学习：集PSO多目标优化与SHAP的回归预测模型_ 从数据清洗 → 多模型对比 → 贝叶斯寻优 _1777458801`
  reappears later in the markdown-learning order as the same framework family
  already learned in Case-006. Keep the existing
  `pso_shap_optimization_framework` routing rather than minting a second
  bundle.
  It verifies that Case-006 already captured the three reference screenshots,
  replica/comparison images, and runtime nonblank four-panel framework.

## 2D-PDP Interaction Contour Matrix

Use when the model diagnostic task asks for two-feature partial dependence,
interaction surfaces, response boundaries, or control regimes.

Required rendering contract:

- Layout is usually `subplots(2, 2, figsize=(12, 10))` with `wspace=0.30` and
  `hspace=0.30`.
- Every panel draws a filled response surface with `contourf(..., cmap="viridis",
  alpha=0.85)`.
- Color levels are shared across panels; do not normalize each PDP panel
  independently when the prompt asks for cross-feature comparison.
- Overlay three percentile contours per panel: Q1 blue dash-dot, median green
  solid, and Q3 red dashed.
- Use one outside colorbar labeled `Predicted Target` for the matrix when a
  shared scale is used.

QA signals: `pdpContourPanelCount == 4`, `contourfCount == 4`,
`quartileContourLineCount == 12`, `sharedColorbarCount == 1`, and
`sharedContourLevels` is true.

Case-078 (`期刊复现：XGBoost的双变量偏依赖(PDP)等高线可视化图`) is the
XGBoost / `sklearn.inspection.partial_dependence` data-flow variant.  It keeps
the same contour semantics but uses the supplied feature-pair count:

- Three feature pairs render as `subplots(1, 3)`; do not pad an empty fourth
  panel just to satisfy the Case-062 2x2 shape.
- The upstream contract includes exporting or retaining long-form PDP grid
  evidence (`feature_x`, `feature_y`, `PDP_Predicted_Value`) before plotting.
- Shared color levels and one `PDP Predicted Value` colorbar remain mandatory
  when panels are compared side by side.
- Q1 / median / Q3 contour lines remain the control-boundary overlay, even when
  the model implementation changes from Random Forest to XGBoost.

Case-088 empty-source audit note:

- `机制解释图复刻：基于Random Forest与局部依赖图(PDP)揭示特征关键阈值（附完整代码）_1778680013`
  is present in the local corpus as a 0-byte Markdown file: no image links, code
  fences, palettes, or layout signals can be learned from it.
- Keep routing title-only RF/PDP threshold requests to the existing
  `shap_pdp_threshold_panel_array` / `threshold_annotation` motif from
  Case-036; do not mint a new template from an empty source file.

## PDP + ICE Threshold Grid

Use this when a Random Forest / RFR mechanism-explanation task supplies
feature-wise PDP or ICE curves plus threshold values and source-data
distributions. This is not a SHAP dependence grid: the primary evidence is the
model response curve family for each feature.

Required rendering contract:

- Layout is a `2 x 3` matrix (`plt.subplots(2, 3, figsize=(16, 9))`) when the
  article or data contains four or more mechanism features and local zoom-ins.
- Each panel draws many thin gray ICE curves first (`alpha≈0.45`,
  `linewidth≈0.5`) to expose sample-level heterogeneity.
- Draw the PDP average as a thick blue dashed line (`#0033CC`, `linewidth≈3.5`)
  above the ICE layer.
- Mark the mechanism threshold with a red dotted vertical segment from the low
  y-baseline to the PDP value, then place a bold red threshold label near that
  point. Do not draw the threshold as a full-height gridline when the source
  uses a local segment.
- Add source-data support as bottom rug ticks using `ax.get_xaxis_transform()`
  so the distribution cue does not consume a separate subplot row.
- Reserve the lower row for zoom-in panels only when the sensitive intervals are
  real subsets of the same PDP/ICE mechanism; otherwise keep all panels at the
  same scale.

QA signals: `panel_count == 6`, `ice_line_count >= 240`,
`pdp_line_count == 6`, `threshold_line_count == 6`,
`threshold_label_count == 6`, `rug_tick_count >= 60`, and
`zoom_panel_count == 2`.

## 3D PDP Surface Panel

Use this when the model-diagnostic task asks for a two-feature PDP interaction
as a perspective 3D response surface, not a flat 2D contour matrix. The data
must provide or allow computing an x-grid, y-grid, and predicted response matrix
from `partial_dependence`, model predictions, or an equivalent upstream table.

Required rendering contract:

- Layout is a single `fig.add_subplot(111, projection="3d")` axes, typically
  `figsize=(10, 8)`, with the colorbar reserved on the right.
- Render the focal PDP response with `plot_surface(..., cmap="viridis",
  edgecolor="none", alpha=0.85, rstride=1, cstride=1)`.
- Add a bottom contour projection using `contourf(..., zdir="z",
  offset=z_min, cmap="viridis", alpha=0.5)` so the threshold footprint remains
  readable despite perspective distortion.
- Use transparent 3D panes via `set_pane_color((1, 1, 1, 0))`, a light dashed
  grid, `view_init(elev=30, azim=-60)`, and `set_box_aspect((1.05, 1.0, 0.78))`
  unless the source figure supplies a different camera.
- Preserve the PDP grid orientation; when `partial_dependence` returns a
  `(len(x), len(y))` matrix, transpose it before `plot_surface` if `meshgrid`
  was built from `np.meshgrid(x, y)`.
- Add one colorbar labeled `Prediction Response`; do not repeat a separate
  colorbar for the bottom projection.

QA signals: `surface_count == 1`, `contour_projection_count == 1`,
`colorbar_count == 1`, `transparent_panes` is true, `view_elev == 30`,
`view_azim == -60`, and `pdp_grid_shape == [50, 50]`.

## H-Statistic Ranking + Contour Dependence Board

Use when interaction-ranking data and 2D response surfaces are both available:

- Layout is an asymmetric 3x2 GridSpec: left H-statistic bar ranking spans all
  rows, while the right column holds the top interaction-pair contour panels.
- The H-statistic panel answers which pairs matter; the contour panels answer
  where in feature space the interaction changes prediction.
- Draw each response surface with `contourf` and overlay observed samples as
  white points with black edges so unsupported high-response regions are not
  overread.
- Use independent colorbars per contour panel unless a shared model-response
  scale is explicitly supplied.
- Runtime status: current `heatmap_pure` validates only a color-mapped matrix
  layer. There is no public generator yet for the H-statistic ranking plus
  top-pair contour composition.

## NSGA-II 3D Pareto Front

Use this when three competing objectives need to be shown as a 3D Pareto front
and the prompt asks for group/strength-grade comparison.

Required rendering contract:

- Compose side-by-side 3D axes with `fig.add_subplot(..., projection="3d")`.
- Use the same `view_init(elev=25, azim=-45)` and the same x/y/z limits in
  every panel.
- Plot Pareto solutions as semi-transparent points colored by one objective,
  typically strength, with `viridis`.
- Plot selected engineering optima as red star markers with black edges and
  higher z-order.
- Keep the legend above the axes (`loc="upper center"`,
  `bbox_to_anchor=(0.5, 1.10)`) so it does not hide 3D points.

QA signals: `pareto3dPanelCount >= 2`, `shared3DView=True`,
`shared3DAxisLimits=True`, `optimalStarCount > 0`, and `threeDimensional=True`.

Runtime status: current `scatter_regression` validates only a 2D objective
tradeoff fallback; it does not create 3D axes, selected-optimum stars, or the
two-panel shared-view NSGA-II board.

## Classifier Validation Board

When columns include `score`, `probability`, `label`, `true_label`, `predicted_label`, `threshold`, `AUC`, `F1`, `precision`, or `recall`, clone the classifier validation board before falling back to generic ROC:

- Prefer the registered `classifier_validation_board` generator for the whole ROC + PR + calibration + threshold/confusion set, not a single ROC alone.
- Add data-derived metric boxes for AUC, AP, best threshold, F1, ECE, bin count, and sample count.
- Mark the selected threshold with a red point and reference guides.
- When a probability table contains multiple classifier models but no feature-importance fields, select the explicit `selected_model` / `is_selected` model when supplied, otherwise prefer RF, and keep competing model colors in a bottom-centered figure legend rather than mixing score rows.
- In narrow embedded slots, compress the threshold sidecar to TP/FP and FN/TN shorthand so it does not collide with neighboring panels.
- Use calibration bin marker size for sample count so imbalanced bins remain visible.
- Executable fallback: `classifier_validation_board` creates a single self-contained four-panel board with ROC AUC, AP/F1, ECE, best threshold, and TP/FP/FN/TN sidecar; multi-model probability tables are filtered to the selected/RF model before metrics are computed. `roc` and `pr_curve` still detect `classifier_validation_board`, mark the Youden / best-F1 threshold with red points plus dashed guides, and move standalone legends to bottom center. `calibration` computes ECE, scales bin markers by sample count, shades the +/-0.05 calibration band, marks the worst bin, and reports ECE / bins / n in a compact metric box. `confusion_matrix` uses true/predicted labels or thresholded score data, annotates count plus row percentage per cell, outlines the diagonal, and reports accuracy / balanced accuracy / largest off-diagonal error.

## RF Classifier Validation + Importance Board

When RF/Random Forest classifier probability and label columns appear together with feature importance, SHAP, gain, or permutation columns, prefer `rf_classifier_report_board` before separate validation or feature-importance charts:

- Keep the classifier validation board as the visual hero, then add a ranked RF feature-importance lane.
- Use the feature importance values supplied by the data; do not fabricate importances from labels alone.
- Accept stacked long tables that separate prediction rows from feature-importance rows using `table_type`, `record_type`, `row_type`, or similar source columns.
- When multiple classifier models appear in the same table (RF, XGBoost, SVM, etc.), select the explicit `selected_model` / `is_selected` model when supplied, otherwise prefer RF as the report anchor; never mix probability rows from competing models in the validation sub-board.
- Never borrow competitor-only importance rows for the selected RF report. If RF is selected but only XGBoost/SVM/other importance rows are present, keep the validation board and model-competition strip, but render a compact "selected RF importance not supplied" lane instead of relabeling competitor explanations as RF evidence.
- Use a compact model-competition strip and bottom-centered figure legend to keep model colors/selection semantics outside the plotting area.
- Wrap long feature names into compact two-line labels before truncating so dense importance lanes remain legible.
- Add a compact model summary with n, positive count, best threshold, best F1, and number of ranked features.
- Generator-level acceptance fixture: a single long table may interleave RF, XGBoost, and SVM prediction rows with RF feature-importance rows, separated only by `table_type`, `record_type`, or `row_type`. With no `selected_model` / `is_selected` flag, the registered generator must still anchor RF, filter the embedded validation board to RF rows, retain competitor semantics in the model strip or bottom legend, and draw the ranked RF importance lane from supplied importance values.
- Executable fallback: `rf_classifier_report_board` splits validation rows from importance rows when a source/type column exists, filters the validation board to the selected/RF model in multi-model tables, embeds `classifier_validation_board`, draws a top-12 relative importance lane with wrapped feature labels, adds model-competition semantics, and records both classifier-validation and explainability motifs for render QA.

## Routing Rules

- Prefer `rf_model_performance_report` when both model benchmark metrics and actual/predicted or residual fields exist.
- Prefer `rf_classifier_validation_report` / `rf_classifier_report_board` when RF classifier score+label data also include feature importance or SHAP-style explanation fields, especially when RF is one competitor among XGBoost/SVM/other classifiers and needs a highlighted manuscript-ready report.
- Prefer `classifier_validation_board` for multi-model classifier probability tables without feature-importance columns; it must still pick one selected/RF anchor model for the validation curves.
- Prefer `grouped_bar` over `classifier_validation_board` when the table is already aggregated by model/split/metric with AUC, F1, precision, recall, or accuracy columns but lacks row-level probability/label or threshold fields; wide metric columns are valid and do not need to be reshaped by the user.
- Prefer `neural_architecture_metric_storyboard` / `model_architecture_board` when architecture fields include latency/FLOPs/memory/throughput/cost/edge metrics.
- Prefer `neural_architecture_topology` when layer/module/component or source-target architecture fields exist without metric columns.
- Prefer `neural_training_dynamics` when epoch/step training histories include loss, validation loss, accuracy, or learning-rate fields.
- Prefer `incremental_feature_selection_curve` when feature-count or ablation fields exist.
- Prefer `rf_feature_importance_shap` when explainability fields exist.
- Prefer `feature_importance_bar_board` when ranked importance values appear together with condition-wise stacked percentage contributions.
- Prefer `prediction_shap_pdp_board` when parity/residual prediction validation appears together with SHAP importance and PDP/local-dependence explanation panels.
- Prefer `spearman_ml_evaluation_board` when Spearman/correlation fields appear together with SHAP/importance fields, actual/predicted fit rows, and external validation or error-summary rows.
- Prefer `pso_shap_optimization_framework` when optimization / Pareto / objective columns exist alongside explainability or model-metric fields.
- Prefer `classifier_validation_board` when labels/probabilities and AUC/F1/precision/recall fields exist.
- If a user explicitly mentions Random Forest/RF/RFR and the data is compatible, keep the RF anchor even if another generic prediction template also matches.
