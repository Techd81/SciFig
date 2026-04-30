# ML Model Diagnostics Technique

Use this deep-dive whenever `templateCasePlan.families` contains `ml_model_diagnostics`, or when the selected bundle key is one of `rf_model_performance_report`, `neural_architecture_metric_storyboard`, `neural_architecture_topology`, `neural_training_dynamics`, `incremental_feature_selection_curve`, `rf_feature_importance_shap`, `pso_shap_optimization_framework`, or `classifier_validation_board`.

## Anchor Cases

- `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱_1777456409.md`
- `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md`
- `期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化_1777456510.md`
- `期刊复现：基于梯度提升树(GBDT)的多面板预测误差评估图_1777456338.md`
- `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图_1777454599.md`

## RF Performance Triptych

When columns include `model` / `algorithm` plus `Training` / `Testing` / `R2` / `AUC` / `RMSE` / `MAE`, clone the RF triptych before falling back to generic grouped bars:

1. Top panel: horizontal grouped bar benchmark. Sort algorithms by test metric; highlight RF/RFR if present; keep train/test colors stable (`Testing #9BCBEB`, `Training #F6CFA3`).
2. Bottom-left: predicted-vs-actual parity scatter. Use train/test marker encoding (`Train` open square, `Test` open triangle), black 1:1 dashed line, and a compact metric table.
3. Bottom-right: residual-vs-predicted scatter. Use zero reference line in deep red (`#B00000`), light grid, and a short in-plot bias note.

Layout intent: `ml_model_performance_triptych` uses a 2x2 grid where the benchmark bar spans the top row and parity/residual diagnostics occupy the bottom row.
Executable fallback: `grouped_bar` renders the sorted RF-highlighted benchmark, standalone `scatter_regression` renders the train/test parity lane as a density-colored marginal joint diagnostic with 1:1 reference and R2/RMSE/MAE box, embedded `scatter_regression` keeps the compact parity lane, and `residual_vs_fitted` renders the residual lane with red zero reference plus bias/SD note.

## Neural Architecture Topology

When columns include `layer`, `module`, `component`, `block`, `source`, `target`, `params`, `units`, `channels`, `heads`, `attention`, `transformer`, `encoder`, or `decoder`, clone an architecture-topology board before falling back to generic flow diagrams:

- Use rounded module blocks rather than plain nodes. Put the layer or module name on the first line and compact type/unit/parameter tags below it.
- Group modules by stage or block with pale stage bands. Keep all labels inside the axes so the figure survives layout QA.
- Use directed arrows for source-target edges or sequential layer order. Encode supplied edge weights with line width and keep legends out unless a real categorical mapping is needed outside the plotting area.
- If edge/module metrics such as latency, FLOPs, memory, throughput, cost, parameters, or edge weights exist, prefer `model_architecture_board`: topology spans the top row, metric profile occupies panel B, and edge signal occupies panel C.
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

## Neural Training Dynamics

When columns include `epoch`, `step`, `iteration`, `train_loss`, `training_loss`, `val_loss`, `validation_loss`, `accuracy`, `val_accuracy`, `learning_rate`, or early-stopping markers, clone the training-history board before generic time-series plotting:

- Use convergence curves rather than bare line charts. Plot train and validation metrics together, and visually distinguish validation traces.
- Add validation-gap shading when train and validation loss are both present.
- Mark the best epoch using validation loss when available, otherwise validation accuracy / AUC / F1.
- Report compact final/best metrics in-panel so a standalone training curve reads like a model diagnostic, not a logging artifact.
- Executable fallback: `training_curve` detects wide or long training-history tables, plots up to six loss/score traces, shades the generalization gap, marks the best epoch, and keeps legends outside the plotting area for final render QA.

## RF Feature Importance + SHAP

When columns include `feature`, `importance`, `gain`, `permutation`, `shap`, or `mean_abs_shap`, clone the RF EFI + SHAP board:

- Left lane: horizontal importance bars with sequential blue gradient and red value labels at bar ends.
- Right lane: SHAP donut or compact contribution summary with callout leaders outside the ring.
- If donut is unsupported for the data, use `lollipop_horizontal` plus `dotplot`, but preserve the left/right asymmetric composition and feature ordering.
- Executable fallback: `lollipop_horizontal` renders the top-15 importance lane and `dotplot` renders the SHAP beeswarm lane with shared feature ordering, zero reference, and feature-value color encoding.

## PSO / Pareto Optimization + SHAP

When columns include `objective_1`, `objective_2`, `obj1`, `obj2`, `cost`, `latency`, `complexity`, `rank`, `pareto_flag`, `optimal_flag`, `iteration`, or explicit PSO/NSGA/Pareto wording, clone the optimization + explainability framework instead of treating Pareto as category frequency:

- Use `radar` for model/solution metric signatures, `lollipop_horizontal` or `dotplot` for SHAP-style explanation, `heatmap_triangular` for objective/feature correlation context, and `pareto_chart` for the tradeoff front.
- Highlight Pareto / optimal points only when a flag or rank column exists; otherwise show the tradeoff cloud and state that no Pareto flag was supplied.
- Use a red diamond + connecting line for the supplied Pareto/top-rank front, a rank or candidate-index colorbar, and an in-panel best-candidate callout.
- Executable fallback: `pareto_chart` detects `pso_shap_optimization_framework` / optimization patterns plus two numeric objective columns, switches from categorical bars to a multi-objective tradeoff scatter, uses supplied Pareto/optimal flags or ranks for front highlighting, and keeps embedded labels compact for render QA.

## Classifier Validation Board

When columns include `score`, `probability`, `label`, `true_label`, `predicted_label`, `threshold`, `AUC`, `F1`, `precision`, or `recall`, clone the classifier validation board before falling back to generic ROC:

- Prefer the registered `classifier_validation_board` generator for the whole ROC + PR + calibration + threshold/confusion set, not a single ROC alone.
- Add data-derived metric boxes for AUC, AP, best threshold, F1, ECE, bin count, and sample count.
- Mark the selected threshold with a red point and reference guides.
- Use calibration bin marker size for sample count so imbalanced bins remain visible.
- Executable fallback: `classifier_validation_board` creates a single self-contained four-panel board with ROC AUC, AP/F1, ECE, best threshold, and TP/FP/FN/TN sidecar. `roc` and `pr_curve` still detect `classifier_validation_board`, mark the Youden / best-F1 threshold with red points plus dashed guides, and move standalone legends to bottom center. `calibration` computes ECE, scales bin markers by sample count, shades the +/-0.05 calibration band, marks the worst bin, and reports ECE / bins / n in a compact metric box. `confusion_matrix` uses true/predicted labels or thresholded score data, annotates count plus row percentage per cell, outlines the diagonal, and reports accuracy / balanced accuracy / largest off-diagonal error.

## Routing Rules

- Prefer `rf_model_performance_report` when both model benchmark metrics and actual/predicted or residual fields exist.
- Prefer `neural_architecture_metric_storyboard` / `model_architecture_board` when architecture fields include latency/FLOPs/memory/throughput/cost/edge metrics.
- Prefer `neural_architecture_topology` when layer/module/component or source-target architecture fields exist without metric columns.
- Prefer `neural_training_dynamics` when epoch/step training histories include loss, validation loss, accuracy, or learning-rate fields.
- Prefer `incremental_feature_selection_curve` when feature-count or ablation fields exist.
- Prefer `rf_feature_importance_shap` when explainability fields exist.
- Prefer `pso_shap_optimization_framework` when optimization / Pareto / objective columns exist alongside explainability or model-metric fields.
- Prefer `classifier_validation_board` when labels/probabilities and AUC/F1/precision/recall fields exist.
- If a user explicitly mentions Random Forest/RF/RFR and the data is compatible, keep the RF anchor even if another generic prediction template also matches.
