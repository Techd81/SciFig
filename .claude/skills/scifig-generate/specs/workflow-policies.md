# Workflow Policies

Shared policy tokens for `scifig-generate`. Use this file when Phase 1-4 need thresholds, visual-density defaults, performance budgets, agent delegation, or rendered quality gates. Keep code snippets in phase files aligned with these names instead of introducing new inline constants.

## Data Scale Policy

```python
DATA_SCALE_POLICY = {
    "high_missing_rate_pct": 10,
    "overplotting_rows": 400,
    "point_density_full_max": 400,
    "point_density_alpha_max": 1000,
    "large_matrix_rows": 2000,
    "clusterable_matrix_rows": 500,
    "rare_positive_rate": 0.20,
    "legend_bottom_group_max": 8,
}
```

## Visual Impact Policy

```python
VISUAL_IMPACT_POLICY = {
    "default_mode": "nature_cell_dense",
    "default_density": "high",
    "impact_level": "editorial_science",
    "max_callouts_single": 8,
    "max_callouts_support": 4,
    "max_inline_stats": 4,
    "min_enhancements_per_panel": 2,
    "min_total_enhancements": 4,
    "reference_motifs_required": True,
    "min_reference_motifs_per_figure": 2,
    "require_inplot_explanatory_labels": True,
    "min_inplot_labels_per_figure": 1,
    "semantic_callout_mode": "data_derived",
    "use_inset_axes": True,
    "use_metric_tables": True,
    "use_density_halos": True,
    "use_density_color_encoding": True,
    "use_marginal_axes": True,
    "use_perfect_fit_reference": True,
    "use_sample_shape_encoding": True,
    "use_significance_star_layer": True,
    "use_dual_axis_error_bars": True,
    "use_template_motifs": True,
    "min_template_motifs_per_figure": 1,
    "require_stat_provenance": True,
    "no_invented_stats": True,
    "outside_layout_elements": True,
}
```

Visual impact must stay data-derived. Permitted enhancements include sample-size labels, observed quantiles, reference lines, confidence bands from supplied or computed values, inset distributions, rank callouts, model diagnostics, and semantic highlights already justified by `dataProfile` or `statPlan`. Every rendered figure should contain in-plot explanatory labels such as best group, endpoint delta, trend direction, threshold hit count, peak window, or matrix/value summaries; outside metric boxes alone do not satisfy visual impact.

Reference visual grammar is mandatory when data support it. Use the reference motifs seen in high-density ML and experimental figures: correlation/value matrices with cell labels and significance stars only when p-values are supplied; prediction scatter panels with dashed perfect-fit lines, R2/RMSE/MAE metric tables, density halos, density-colored points, marginal distributions, and optional sample-shape overlays; feature-importance or SHAP-like bars with clustering/cutoff sidecars when grouping or linkage data exist; validation/new-point panels with predicted/experimental markers plus dual-axis percent-error or RMSE bars when those columns exist. Do not invent p-values, SHAP values, clustering trees, or error columns for visual impact.

Template-derived motifs are governed by `specs/template-visual-motifs.md`. Phase 2 must store them in `visualContentPlan.templateMotifs` with explicit provenance requirements, and Phase 4 must verify `templateMotifCount` when motifs were planned. Motifs are not chart registry entries; they are overlays or layout intents that enrich implemented charts.

## Template Matching Policy

```python
TEMPLATE_MATCH_POLICY = {
    "clone_known_family_first": True,
    "computer_ai_ml_strong_signals": [
        "model", "algorithm", "estimator", "random forest", "rf", "rfr",
        "xgboost", "lightgbm", "gbdt", "svm", "knn", "probability", "proba", "threshold", "train", "test",
        "validation", "cv", "auc", "accuracy", "f1", "precision", "recall",
        "r2", "rmse", "mae", "residual", "shap", "feature_importance", "rf_classifier_report_board",
        "confusion", "confusion_matrix", "classification_error",
        "true_label", "actual_label", "predicted_label", "prediction_label", "y_pred",
        "epoch", "learning_curve", "training_curve", "training_history",
        "train_loss", "training_loss", "val_loss", "validation_loss", "val_accuracy",
        "model_architecture", "model_architecture_board", "neural_architecture", "architecture_diagram",
        "pipeline_topology", "dag_pipeline", "layer", "module", "component",
        "block", "node", "source", "target", "params", "parameters", "units",
        "channels", "heads", "attention", "transformer", "encoder", "decoder",
        "latency", "flops", "memory", "throughput", "edge_weight"
    ],
    "preferred_ml_bundle_order": [
        "rf_model_performance_report",
        "rf_classifier_validation_report",
        "neural_architecture_metric_storyboard",
        "neural_architecture_topology",
        "neural_training_dynamics",
        "incremental_feature_selection_curve",
        "rf_feature_importance_shap",
        "pso_shap_optimization_framework",
        "classifier_validation_board"
    ],
    "rf_anchor_required_when_compatible": True,
}
```

If a user-selected or inferred domain contains AI/ML/computer-science signals, Phase 2 must route to `computer_ai_ml` before generic biomedical or engineering defaults. If layer/module/component or source-target topology fields are present with latency, FLOPs, memory, throughput, cost, edge_weight, or parameter metrics, prefer `model_architecture_board` and the `neural_architecture_metric_storyboard` bundle over a plain topology diagram. If RF/Random Forest data contain probability/score, label, and feature-importance/SHAP/gain fields, prefer `rf_classifier_report_board`; this includes stacked long tables where prediction rows and feature-importance rows are separated by `table_type`, `record_type`, or `row_type`, and multi-model classifier tables where RF competes with XGBoost/SVM/other estimators and must be highlighted without mixing probability rows. If probability/score plus label or threshold fields exist without explainability fields, prefer `classifier_validation_board` over separate ROC/PR/calibration singles; if a model/algorithm column contains multiple classifiers, the board must choose an explicit selected/focus model or RF anchor before computing curves. If the user supplies only aggregate classifier metrics by model/split/metric, prefer `grouped_bar` and do not invoke `classifier_validation_board` unless row-level probability/label or threshold fields are present; wide metric columns such as AUC/F1/precision/recall are accepted directly. If Random Forest/RF/RFR is present and the schema supports model metrics, actual/predicted, residuals, or feature importance, the RF anchor cases are preferred over generic prediction diagnostics.

## Autonomous Distillation Policy

```python
AUTONOMOUS_DISTILLATION_POLICY = {
    "cycle_minutes": 5,
    "smoke_output_root": "output/autonomous_distill",
    "smoke_domains": [
        "computer_ai_ml",
        "genomics_transcriptomics",
        "clinical_diagnostics_survival",
        "materials_engineering",
        "ecology_environmental",
    ],
    "single_figures_per_domain": 3,
    "composite_figures_per_domain": 2,
    "generated_artifacts_must_be_ignored": True,
    "commit_tracked_skill_changes_only": True,
    "carry_forward_previous_cycle_lessons": True,
    "prefer_code_promotion_over_prompt_growth": True,
}
```

Every autonomous maintenance cycle must run Phase 5 once, inspect the previous cycle's smoke outputs and failures, promote one reusable template-derived improvement, generate the smoke bundle under the ignored output root, run render/test validation, and commit only tracked skill/package changes. Generated PNG/SVG/PDF, scratch reports, and temporary datasets remain ignored artifacts.

## Crowding And Layout Policy

```python
CROWDING_POLICY = {
    "legend_scope": "figure",
    "legend_priority": ["bottom_center"],
    "legend_allowed_modes": ["bottom_center"],
    "legend_label_max_chars": 32,
    "max_legend_columns": 6,
    "legend_frame": True,
    "legend_frame_style": {
        "facecolor": "#FFFFFF",
        "edgecolor": "#222222",
        "linewidth": 0.55,
        "alpha": 0.96,
        "pad": 0.28,
        "boxstyle": "round",
    },
    "legend_center_placement_only": True,
    "forbid_outside_right_legend": True,
    "forbid_in_axes_legend": True,
    "max_direct_labels_hero": 5,
    "max_direct_labels_support": 3,
    "max_bracket_groups": 2,
    "render_retry_limit": 5,
    "layout_reflow_required_on_overlap": True,
    "legend_external_hard_limit": True,
    "axis_legend_hard_fail": True,
    "legend_contract_finalizer_required": True,
    "savefig_requires_legend_contract": True,
    "legend_contract_failure_is_hard_fail": True,
    "layout_contract_required": True,
    "layout_contract_failure_is_hard_fail": True,
    "max_text_font_size_pt": 12,
    "max_panel_label_font_size_pt": 12,
    "forbid_negative_axes_text": True,
    "legend_reflow_strategy": ["margin_adjust", "height_increase", "entry_reduction"],
    "legend_max_height_multiplier": 1.3,
}

LAYOUT_SCORE_WEIGHTS = {
    "panel_count": 2,
    "legend_burden": 3,
    "long_label_burden": 2,
    "colorbar_burden": 2,
    "aspect_ratio_mismatch": 2,
    "story_fit": 4,
}
```

Before Phase 3 locks the plan, score each candidate layout for group count, label length, legend burden, colorbar need, panel count, and chart aspect ratio. Prefer a lower-scoring layout even when it has fewer panels. In composite figures, every panel-level legend is only a temporary handle source: the final output must have one framed figure-level legend centered at the bottom, below every plotting panel, so it cannot collide with the figure title. `outside_right`, top-center, `loc="best"`, and any in-axes legend are forbidden in final publication output. Every saved figure must pass through the skill helper `enforce_figure_legend_contract(...)` immediately before `savefig`; missing embedded helper source, custom replacement helpers, missing `legendContractEnforced`, remaining axis legend, unframed final legend, or final legend overlap is a hard failure. Risk tables, footnotes, and outside summaries require a reserved GridSpec/subfigure/table slot; negative `ax.transAxes` text coordinates such as `y=-0.18` are forbidden because they can collide with lower panels. Print-scale typography is mandatory: body 5-7 pt, axis labels 6-8 pt, panel labels 8-10 pt, titles 7-9 pt, and any generated `font.size >= 12`, `fontsize >= 13`, or panel label >12 pt is a hard failure. If a rendered legend, colorbar, title, table, risk table, or direct label overlaps another panel's layout box, reflow before export.

## Performance Policy

```python
PERFORMANCE_POLICY = {
    "renderer_cache": True,
    "max_render_retries": 5,
    "adaptive_kde_grid_min": 96,
    "adaptive_kde_grid_max": 300,
    "adaptive_heatmap_cluster_rows": 500,
    "sample_points_preview_max": 5000,
}
```

Generators should precompute grouped subsets once, use adaptive KDE/grid resolution, and avoid repeated `fig.canvas.draw()` calls inside nested layout searches. Expensive rendered checks should share a cached renderer and invalidate it only after layout changes.

## Agent Delegation Policy

Use `Agent` only after the data-status, file-path, and mode gates are complete. Agents must be read-only unless the coordinator explicitly asks for a rewritten artifact. Each agent returns JSON findings that the coordinator merges into phase state.

| Agent | Trigger | Output | Blocking Gates |
|-------|---------|--------|----------------|
| `data-profile-auditor` | Matrix/large data, high missingness, weak replicates, ambiguous roles/domain, survival or dose-response incompleteness | `dataProfile.audit` | unresolved role conflicts, low schema confidence, required clarification |
| `chart-stats-planner` | Multi-panel, custom domain, high-stakes statistics, or requested inferential claims | `chartPlan.delegationReports.stats` | unregistered chart, unsupported statistical assumption, missing replicate/cohort meaning |
| `panel-layout-auditor` | More than two panels, shared legend/colorbar, long labels, many groups | `chartPlan.delegationReports.layout` | overpacked layout, missing legend/colorbar plan, invalid axis linking |
| `palette-journal-auditor` | Domain palette, many categories, grayscale-safe request, journal submission | `chartPlan.delegationReports.palette` | category collisions, poor grayscale contrast, semantic map drift |
| `scientific-color-harmony` | After build_palette_plan in Phase 2 | `chartPlan.delegationReports.color_harmony` | advisory only — perceptual harmony, color-wheel relationships, domain aesthetics |
| `layout-aesthetics` | After build_panel_blueprint in Phase 2 | `chartPlan.delegationReports.aesthetics` | advisory only — whitespace balance, visual weight distribution, panel proportions |
| `content-richness` | After build_visual_content_plan in Phase 2 | `chartPlan.delegationReports.content_richness` | advisory only — annotation density, label informativeness, marker diversity |
| `code-reviewer` | Before Phase 3 completion | `styledCode.codeReview` | syntax/import failures, generator drift, forbidden `loc="best"`, missing metadata/source hooks |
| `rendered-qa` | After script execution and before final outputBundle | `outputBundle.renderQa` | blank/tiny output, overlap, in-axes legend, missing format, non-editable SVG/PDF text |
| `visual-impact-scorer` | After rendered-qa, before outputBundle packaging | `outputBundle.renderQa.impactScore` | impactScore < 40 → warning, impactScore < 20 → hardFail |

Blocking findings route back to the owning phase rather than being buried in the final report.

## Render QA Policy

Phase 4 must produce `render_qa.json` with:

- `legendOutsidePlotArea`
- `legendContractEnforced`
- `legendContractFailures`
- `layoutContractEnforced`
- `layoutContractFailures`
- `crossPanelOverlapIssues`
- `negativeAxesTextCount`
- `oversizedTextCount`
- `figureWhitespaceFraction`
- `legendModeUsed`
- `legendAllowedModes`
- `legendCenterPlacementOnly`
- `legendFrameApplied`
- `legendFrameStyle`
- `forbidOutsideRightLegend`
- `axisLegendRemovedCount`
- `axisLegendRemainingCount`
- `figureLegendCount`
- `sharedColorbarApplied`
- `overlapFailures`
- `contentDensityFailures`
- `blankOrTinyOutputs`
- `editableTextCheck`
- `paletteContrastCheck`
- `visualEnhancementCount`
- `inPlotExplanatoryLabelCount`
- `referenceMotifCount`
- `minReferenceMotifCount`
- `templateMotifCount`
- `minTemplateMotifCount`
- `templateMotifs`
- `templateMotifsApplied`
- `marginalAxesCount`
- `densityColorEncodingCount`
- `subAxesCount`
- `colorbarSlotCount`
- `multiAxisEncodingCount`
- `visualGrammarMotifs`
- `visualGrammarMotifsApplied`
- `metricTableCount`
- `referenceLineCount`
- `densityHaloCount`
- `sampleEncodingCount`
- `significanceStarLayerCount`
- `dualAxisEncodingCount`
- `statProvenanceWarnings`
- `impactScore` (0-100 from visual-impact-scorer agent)

Any hard failure returns to Phase 3 for styling/layout/code or Phase 2 for an overpacked plan. `legendContractEnforced != true`, non-empty `legendContractFailures`, `layoutContractEnforced != true`, non-empty `layoutContractFailures`, `axisLegendRemainingCount > 0`, `legendOutsidePlotArea == false`, `figureLegendCount != 1` when a legend exists, `legendModeUsed != "bottom_center"` when a legend exists, `legendFrameApplied == false` when a legend exists, negative axes text without a reserved slot, poster-scale font sizes, cross-panel table/title/text overlap, missing in-plot explanatory labels, missing required reference motifs, or `visualEnhancementCount < visualContentPlan.minTotalEnhancements` are hard failures. `impactScore < 20` is a hard fail; `impactScore < 40` is a warning.
