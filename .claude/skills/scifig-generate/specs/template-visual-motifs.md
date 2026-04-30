# Template Visual Motifs

Distilled from the `template/articles` reference cases. These are visual grammar motifs, not new chart keys. Phase 2 infers them from data roles and existing chart families; Phase 3 renders them through helper overlays; Phase 4 verifies that required motif counters were actually applied.

## Core Motifs

| Motif | Data cues | Rendering pattern | QA counters |
|-------|-----------|-------------------|-------------|
| `joint_marginal_grid` | actual/predicted pairs, dense x/y diagnostics, residual diagnostics | Main scatter plus reserved top/right sidecar axes with histogram + KDE density strips outside the data marks | `marginalAxesCount`, `subAxesCount`, `templateMotifCount` |
| `density_encoded_scatter` | point count >= 12 and numeric x/y | Points colored by local 2D-bin density, optionally with translucent covariance halos | `densityColorEncodingCount`, `densityHaloCount` |
| `prediction_diagnostic_matrix` | `actual` + `predicted`, optional split/model/sample columns | Perfect-fit line, R2/RMSE/MAE table, residual/error sidecar when available, sample marker shapes | `metricTableCount`, `referenceLineCount`, `sampleEncodingCount` |
| `ml_model_performance_triptych` | `model` / `algorithm` plus train/test, validation, R2/RMSE/MAE/AUC/F1, actual/predicted, or residual fields | RF-template triptych: top-row model benchmark, bottom-left parity scatter, bottom-right residual diagnostic; degrade honestly when a lane is missing | `templateMotifCount`, `metricTableCount`, `referenceLineCount` |
| `correlation_evidence_matrix` | correlation/covariance matrix or p-value columns | Diverging matrix, cell labels when small, p-value stars only from supplied p-values, shared colorbar outside axes | `significanceStarLayerCount`, `colorbarSlotCount` |
| `explainability_importance_stack` | feature + importance, SHAP, ALE/PDP, H-statistic, model explanation columns | Ranked bars/lollipops, signed zero line, low-to-high feature-value color semantics, optional dependence support panel | `referenceLineCount`, `inPlotExplanatoryLabelCount` |
| `interval_uncertainty_band` | CI/PI lower and upper columns, SEM/STD columns, survival/effect intervals | Shaded interval band or forest-style whiskers; never synthesize intervals | `referenceLineCount`, `templateMotifCount` |
| `dual_axis_error_sidecar` | RMSE, MAE, percent-error, new-data-point error columns | Secondary y-axis hatched error bars paired with primary predicted/experimental marks | `dualAxisEncodingCount`, `multiAxisEncodingCount` |
| `pareto_tradeoff_board` | objective columns, rank, pareto/optimal flags | Tradeoff scatter, highlighted non-dominated or optimal points only when flags or ranks exist | `inPlotExplanatoryLabelCount`, `sampleEncodingCount` |
| `polar_comparison_signature` | cyclic angle, radar score, category-by-metric wide tables | Radar/polar comparison with hand-drawn polygon grid, muted fills, strong outline hierarchy, and layered glass markers | `templateMotifCount`, `sampleEncodingCount` |

## Selection Rules

1. Treat motifs as evidence layers attached to implemented charts. Do not add registry keys such as `shap_beeswarm` unless a real generator exists.
2. A motif must be data-driven. SHAP, PDP, ALE, H-statistic, p-value stars, clustering trees, percent-error bars, and Pareto flags can only be rendered when columns or upstream outputs exist.
3. If the user asks for a top-journal style figure but the detected data only support a simple chart, add dense but honest overlays: direct labels, sample-size labels, summary tables, marginal distributions, reference lines, and source-data exports.
4. Legends, colorbars, metric boxes, and marginal axes are layout elements. Keep them outside plotted data regions and let render QA fail if they overlap.
5. Prefer one strong motif plus one support motif over many weak decorations. The goal is visual evidence density, not ornament.

## Phase Contracts

- Phase 1 adds semantic roles and `specialPatterns` that expose motif opportunities.
- Phase 2 writes `visualContentPlan.templateMotifs`, `layoutIntents`, `provenanceRequirements`, and minimum motif counters.
- Phase 3 uses `phases/code-gen/helpers.py` to apply motif overlays after base chart drawing and before crowding management.
- Phase 4 records motif counters in `render_qa.json` and hard-fails when a required template motif was planned but not applied.
