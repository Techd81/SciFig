# Phase 2: Chart Recommendation, Statistics, And Panel Blueprint

> **COMPACT SENTINEL [Phase 2: recommend-stats]**
> This phase contains 9 execution steps (Step 2.1 - 2.9).
> If you can read this sentinel but cannot find the full Step protocol below, context has been compressed.
> Recovery: `Read("phases/02-recommend-stats.md")`

Resolve the domain playbook, expand chart coverage, choose inferential or descriptive statistics, and convert the story request into a concrete panel and palette blueprint.

## Objective

- Map the `dataProfile` onto the chart catalog and domain playbooks
- Recommend a primary chart plus domain-appropriate secondary charts
- Select a conservative statistical plan that matches the data design
- Build a reusable `panelBlueprint` for multi-panel assembly
- Build a `visualContentPlan` for Nature/Cell-style information density
- Build a stable `palettePlan` aligned with journal and domain semantics

## Execution

### Step 2.1: Load Domain And Chart References

Use these files as on-demand references during decision making:

- `specs/chart-catalog.md`
- `specs/domain-playbooks.md`
- `specs/workflow-policies.md`
- `specs/template-visual-motifs.md`
- `templates/panel-layout-recipes.md`
- `templates/palette-presets.md`

Resolve the working domain with:

```python
def resolve_domain(dataProfile, workflowPreferences):
    user_domain = workflowPreferences.get("domainFamily")
    custom_domain_text = workflowPreferences.get("customDomainText") or workflowPreferences.get("syntheticDomainText")
    detected = dataProfile["domainHints"]["primary"]

    if user_domain == "custom_user_domain" and custom_domain_text:
        return {
            "selected": custom_domain_text,
            "selectedFamily": detected,
            "detected": detected,
            "overridden": True,
            "custom": True
        }

    if user_domain and user_domain != "general_biomedical":
        return {
            "selected": user_domain,
            "selectedFamily": user_domain,
            "detected": detected,
            "overridden": user_domain != detected,
            "custom": False
        }

    return {
        "selected": detected,
        "selectedFamily": detected,
        "detected": detected,
        "overridden": False,
        "custom": False
    }
```

### Step 2.2: Recommend Primary And Secondary Charts

Use structure, semantic roles, and domain cues together. Prefer field-standard figures where the schema strongly implies them.

```python
DATA_SCALE_POLICY = {
    "point_density_full_max": 400,
    "point_density_alpha_max": 1000,
    "clusterable_matrix_rows": 500,
    "rare_positive_rate": 0.20,
    "legend_bottom_group_max": 8,
}


def recommend_chart_bundle(dataProfile, workflowPreferences):
    roles = dataProfile["semanticRoles"]
    cols = [c.lower() for c in dataProfile["columnNames"]]
    patterns = set(dataProfile["specialPatterns"])
    n_groups = dataProfile["nGroups"] or 0
    n_obs = dataProfile["nObservations"]
    domain = dataProfile["domainHints"]["primary"]

    # Implemented-only filter: every registered chart key has a real gen_ function.
    IMPLEMENTED_CHARTS = {
        # Mirrors phases/code-gen/registry.py; every registered key has a gen_ implementation.
        "violin_strip", "box_strip", "raincloud", "beeswarm", "paired_lines",
        "dumbbell", "line", "training_curve", "model_architecture", "model_architecture_board", "rf_classifier_report_board", "classifier_validation_board", "line_ci", "spaghetti", "heatmap_cluster",
        "heatmap_pure", "volcano", "ma_plot", "pca", "umap",
        "tsne", "enrichment_dotplot", "oncoprint", "lollipop_mutation", "roc",
        "pr_curve", "calibration", "km", "forest", "waterfall",
        "dose_response", "scatter_regression", "correlation", "manhattan", "qq",
        "spatial_feature", "composition_dotplot", "ridge", "bubble_matrix", "stacked_bar_comp",
        "alluvial", "violin_paired", "violin_split", "dot_strip", "histogram",
        "density", "ecdf", "joyplot", "sparkline", "area",
        "area_stacked", "streamgraph", "gantt", "timeline_annotation", "residual_vs_fitted",
        "scale_location", "cook_distance", "leverage_plot", "pp_plot", "bland_altman",
        "funnel_plot", "pareto_chart", "control_chart", "box_paired", "mean_diff_plot",
        "ci_plot", "dotplot", "adjacency_matrix", "heatmap_annotated", "confusion_matrix", "heatmap_triangular",
        "heatmap_mirrored", "cooccurrence_matrix", "circos_karyotype", "gene_structure", "pathway_map",
        "kegg_bar", "go_treemap", "chromosome_coverage", "swimmer_plot", "risk_ratio_plot",
        "caterpillar_plot", "tornado_chart", "nomogram", "decision_curve", "treemap",
        "sunburst", "waffle_chart", "marimekko", "stacked_area_comp", "nested_donut",
        "chord_diagram", "parallel_coordinates", "sankey", "radar", "stress_strain",
        "phase_diagram", "nyquist_plot", "xrd_pattern", "ftir_spectrum", "dsc_thermogram",
        "species_abundance", "shannon_diversity", "ordination_plot", "biodiversity_radar", "likert_divergent",
        "likert_stacked", "mediation_path", "interaction_plot", "bubble_scatter", "connected_scatter",
        "stem_plot", "lollipop_horizontal", "slope_chart", "bump_chart", "mosaic_plot",
        "clustered_bar", "diverging_bar", "grouped_bar", "heatmap_symmetric", "violin_grouped",
        "violin+strip", "box+strip", "heatmap+cluster"
    }

    CHART_KEY_ALIASES = {
        "violin+strip": "violin_strip",
        "box+strip": "box_strip",
        "heatmap+cluster": "heatmap_cluster",
        "dot+box": "box_strip",
    }

    def _canonical_chart_key(chart):
        raw = str(chart or "")
        return CHART_KEY_ALIASES.get(raw, CHART_KEY_ALIASES.get(raw.replace("+", "_"), raw.replace("+", "_")))

    def _safe(chart):
        """Return chart if implemented, else closest fallback."""
        key = _canonical_chart_key(chart)
        if key in IMPLEMENTED_CHARTS:
            return key
        FALLBACKS = {
            # Keep only non-registry aliases here; registered keys should not be downgraded.
            "ridgeline": "ridge",
            "dot+box": "box_strip",
            "dot_box": "box_strip",
        }
        return FALLBACKS.get(key, "box_strip")

    selected_bundle = workflowPreferences.get("selectedChartBundle") or {}
    if isinstance(selected_bundle, dict) and selected_bundle.get("primaryChart"):
        primary = _safe(selected_bundle.get("primaryChart"))
        secondary = []
        for chart in selected_bundle.get("secondaryCharts", []):
            safe_chart = _safe(chart)
            if safe_chart and safe_chart != primary and safe_chart not in secondary:
                secondary.append(safe_chart)
        return primary, secondary

    has_prediction_fit = "prediction_diagnostic" in patterns or ("actual" in roles and "predicted" in roles)
    has_model_performance = (
        "model_performance_benchmark" in patterns
        or "ml_model_family" in patterns
        or ("model" in roles and any(role in roles for role in ("metric", "score", "rmse", "mae", "residual")))
        or (
            "model" in roles
            and any(token in cols for token in ("auc", "roc_auc", "accuracy", "f1", "precision", "recall", "r2", "rmse", "mae"))
            and (
                domain == "computer_ai_ml"
                or "ml_model_family" in patterns
                or any(token in cols for token in ("algorithm", "estimator", "split", "train", "test", "validation"))
            )
        )
    )
    has_feature_selection_curve = (
        "incremental_feature_selection" in patterns
        or "feature_selection" in patterns
        or "ablation_curve" in patterns
        or any(token in cols for token in ("n_features", "top_k", "feature_count", "ablation"))
    ) and (
        domain == "computer_ai_ml"
        or has_model_performance
        or any(token in cols for token in ("auc", "accuracy", "f1", "r2", "rmse", "mae"))
    )
    profile_tokens = set(cols) | {str(k).lower() for k in roles} | {str(v).lower() for v in roles.values()} | patterns
    architecture_tokens = {
        "model_architecture", "neural_architecture", "architecture_diagram",
        "pipeline_topology", "dag_pipeline", "layer", "module", "component",
        "block", "node", "source", "target", "from", "to", "params",
        "parameters", "units", "channels", "heads", "attention", "transformer",
        "encoder", "decoder", "embedding", "classifier",
    }
    has_source_target_schema = bool(profile_tokens & {"source", "from", "input"}) and bool(profile_tokens & {"target", "to", "output"})
    has_architecture_hint = bool(profile_tokens & (architecture_tokens - {"source", "target", "from", "to"}))
    has_model_architecture = (
        bool(patterns & {"model_architecture", "neural_architecture", "architecture_diagram", "pipeline_topology", "dag_pipeline"})
        or (has_source_target_schema and (domain == "computer_ai_ml" or has_architecture_hint))
        or (
            bool(profile_tokens & {"layer", "module", "component", "block", "node"})
            and (
                domain == "computer_ai_ml"
                or "ml_model_family" in patterns
                or bool(profile_tokens & architecture_tokens)
            )
        )
    )
    architecture_metric_tokens = {"latency", "flops", "memory", "throughput", "edge_weight", "weight", "cost", "params", "parameters"}
    has_architecture_metrics = has_model_architecture and bool(profile_tokens & architecture_metric_tokens)
    has_training_curve = (
        "training_curve" in patterns
        or "learning_curve" in patterns
        or "training_history" in patterns
        or "neural_training" in patterns
        or (
            any(role in roles for role in ("epoch", "step", "iteration", "time"))
            and any(role in roles for role in ("loss", "train_loss", "val_loss", "accuracy", "val_accuracy", "metric", "value"))
            and (
                domain == "computer_ai_ml"
                or "ml_model_family" in patterns
                or any(token in cols for token in ("epoch", "train_loss", "training_loss", "val_loss", "validation_loss", "accuracy", "val_accuracy", "learning_rate"))
            )
        )
        or (
            any(token in cols for token in ("epoch", "step", "iteration"))
            and any(token in cols for token in ("loss", "train_loss", "training_loss", "val_loss", "validation_loss", "accuracy", "val_accuracy", "auc", "f1"))
        )
    )
    has_classifier_validation_board = (
        "classifier_validation" in patterns
        or "threshold_tuning" in patterns
        or "probability_calibration" in patterns
        or (
            "score" in roles and "label" in roles
            and (
                domain == "computer_ai_ml"
                or "ml_model_family" in patterns
                or any(token in cols for token in ("probability", "proba", "auc", "f1", "precision", "recall", "threshold"))
            )
        )
    )
    classifier_metric_tokens = {
        "auc", "roc_auc", "f1", "accuracy", "balanced_accuracy",
        "precision", "recall", "specificity", "sensitivity",
    }
    row_level_classifier_tokens = {
        "probability", "proba", "prediction_score", "y_score",
        "threshold", "true_label", "actual_label", "y_true",
        "predicted_label", "prediction_label", "predicted_class", "y_pred",
    }
    cols_set = set(cols)
    has_aggregate_classifier_metrics = (
        has_model_performance
        and (
            "metric" in roles
            or bool(cols_set & classifier_metric_tokens)
            or bool(profile_tokens & classifier_metric_tokens)
        )
        and not bool(cols_set & row_level_classifier_tokens)
        and not bool(profile_tokens & {"probability", "proba", "prediction_score", "y_score", "threshold"})
    )
    has_confusion_matrix_labels = (
        "confusion_matrix" in patterns
        or "classification_error" in patterns
        or (
            any(role in roles for role in ("label", "true_label", "actual_label", "y_true"))
            and any(role in roles for role in ("predicted_label", "prediction_label", "predicted_class", "y_pred"))
        )
        or (
            "score" in roles
            and any(role in roles for role in ("label", "true_label", "actual_label", "y_true"))
        )
        or any(token in cols for token in (
            "confusion", "true_label", "actual_label", "y_true",
            "predicted_label", "prediction_label", "predicted_class", "y_pred"
        ))
    )
    has_classifier_validation_board = has_classifier_validation_board or has_confusion_matrix_labels
    if has_aggregate_classifier_metrics:
        has_classifier_validation_board = False
        has_confusion_matrix_labels = False
    df_for_role_values = dataProfile.get("df")
    model_cols = [
        roles.get(role)
        for role in ("model", "algorithm", "estimator")
        if df_for_role_values is not None and roles.get(role) in getattr(df_for_role_values, "columns", [])
    ]
    model_values = " ".join(
        str(value).lower()
        for col in model_cols
        for value in df_for_role_values[col].dropna().unique().tolist()[:12]
    )
    rf_tokens = {"random forest", "random_forest", "randomforest", "rf", "rfr"}
    has_rf_signal = (
        any(token in profile_tokens for token in rf_tokens)
        or any(token in model_values for token in ("random forest", "random_forest", "randomforest"))
        or any(value.strip() in {"rf", "rfr"} for value in model_values.split())
    )
    has_feature_importance = (
        "feature_importance" in patterns
        or "ml_explainability" in patterns
        or ("feature_id" in roles and any(role in roles for role in ("importance", "feature_importance", "shap_value", "value")))
        or any(token in cols for token in ("importance", "feature_importance", "mean_abs_shap", "shap_value", "gain", "permutation"))
    )
    has_rf_classifier_report = has_rf_signal and has_classifier_validation_board and has_feature_importance
    has_shap_dependence = (
        "shap_dependence" in patterns
        or (
            ("feature_value" in roles or "x" in roles or any(token in cols for token in ("feature_value", "feature_val")))
            and ("shap_value" in roles or any(token in cols for token in ("shap_value", "shap")))
        )
    )

    # Direct pattern matches
    if has_architecture_metrics:
        secondary = ["model_architecture", "parallel_coordinates"]
        if has_training_curve:
            secondary = ["training_curve", "model_architecture", "parallel_coordinates"]
        return "model_architecture_board", secondary
    if has_model_architecture:
        return "model_architecture", ["training_curve", "confusion_matrix", "lollipop_horizontal"]
    if has_training_curve:
        secondary = ["line", "grouped_bar", "lollipop_horizontal"]
        if has_confusion_matrix_labels:
            secondary = ["confusion_matrix", "line", "grouped_bar"]
        return "training_curve", secondary
    if has_feature_selection_curve:
        return "line", ["grouped_bar", "lollipop_horizontal"]
    if has_aggregate_classifier_metrics:
        return "grouped_bar", ["line", "lollipop_horizontal"]
    if has_rf_classifier_report and has_classifier_validation_board:
        return "rf_classifier_report_board", ["classifier_validation_board", "lollipop_horizontal", "dotplot"]
    if has_classifier_validation_board and "score" in roles and "label" in roles:
        return "classifier_validation_board", ["roc", "pr_curve", "calibration", "confusion_matrix"]
    if has_confusion_matrix_labels:
        return "confusion_matrix", ["grouped_bar", "heatmap_annotated"]
    if has_model_performance and has_prediction_fit:
        return "grouped_bar", ["scatter_regression", "residual_vs_fitted"]
    if has_model_performance:
        return "grouped_bar", ["line", "lollipop_horizontal"]
    if "genomic_association" in patterns:
        return _safe("manhattan"), [_safe("qq"), "forest"]
    if "survival" in patterns:
        return "km", ["forest", "roc", "calibration"]
    if "dose_response" in patterns:
        return "dose_response", ["waterfall", "paired_lines"]
    if has_shap_dependence:
        return "scatter_regression", ["lollipop_horizontal", "dotplot", "heatmap_annotated"]
    if "prediction_diagnostic" in patterns or ("actual" in roles and "predicted" in roles):
        return "scatter_regression", ["residual_vs_fitted", "bland_altman", "histogram"]
    if "ml_explainability" in patterns or "feature_importance" in patterns or ("feature_id" in roles and ("importance" in roles or "shap_value" in roles)):
        return "lollipop_horizontal", ["dotplot", "scatter_regression", "heatmap_annotated", "correlation"]
    if "optimization_tradeoff" in patterns or "pareto_flag" in roles or "objective" in roles:
        return "pareto_chart", ["scatter_regression", "parallel_coordinates"]
    if "embedding" in patterns:
        primary = "umap" if any(c.startswith("umap") for c in cols) else _safe("tsne")
        return primary, [_safe("composition_dotplot"), "violin_strip", "heatmap_pure"]
    if "differential" in patterns:
        if any("basemean" in c or "mean" in c for c in cols):
            return _safe("ma_plot"), ["volcano", "enrichment_dotplot", "heatmap_cluster"]
        return "volcano", ["heatmap_cluster", "enrichment_dotplot", "pca"]

    # Domain-aware defaults
    if "dose" in roles and "response" in roles:
        return "dose_response", ["waterfall", "violin_strip"]
    if "effect" in roles and "ci_low" in roles and "ci_high" in roles:
        return "forest", ["km" if "event" in roles else "box_strip"]
    if "score" in roles and "label" in roles:
        label_col = dataProfile["df"][roles["label"]]
        if pd.api.types.is_numeric_dtype(label_col):
            pos_rate = label_col.mean()
            return "pr_curve" if n_obs > 0 and pos_rate < DATA_SCALE_POLICY["rare_positive_rate"] else "roc", ["calibration", "box_strip"]
        return "roc", ["calibration", "box_strip"]
    if "subject_id" in roles and "time" in roles:
        return "spaghetti", ["line_ci", "paired_lines"]
    if "subject_id" in roles and n_groups == 2 and "value" in roles:
        return "paired_lines", ["dumbbell", "beeswarm"]
    if "time" in roles and "value" in roles:
        return "line_ci" if any("ci" in c or "conf" in c for c in cols) else "line_ci", ["beeswarm", "box_strip"]
    if dataProfile["structure"] == "matrix":
        return "heatmap_cluster" if n_obs <= 500 else "heatmap_pure", ["pca", "correlation"]

    # Publication-quality grouped defaults
    if "group" in roles and "value" in roles:
        if n_obs <= 80:
            primary = "raincloud" if domain in ("immunology_cell_biology", "general_biomedical") else "violin_strip"
        elif n_obs <= 250:
            primary = "violin_strip"
        else:
            primary = "box_strip"
        secondary = ["beeswarm", "paired_lines" if "subject_id" in roles else "line_ci"]
        return primary, secondary

    return "scatter_regression", ["correlation"]
```

### Step 2.3: Select Statistical Plan

Broaden the decision tree so domain-specific charts still get defensible defaults.

```python
def select_statistical_plan(dataProfile, primaryChart, workflowPreferences):
    roles = dataProfile["semanticRoles"]
    df = dataProfile["df"]
    rigor = workflowPreferences.get("statsRigor", "strict")

    if rigor == "descriptive":
        return {"method": "none", "correction": None, "notes": ["descriptive_only"]}

    if primaryChart in ("volcano", "ma_plot", "heatmap_cluster", "heatmap_pure", "umap", "tsne", "pca", "spatial_feature", "training_curve", "model_architecture", "model_architecture_board"):
        return {"method": "none", "correction": None, "notes": ["exploratory_primary_chart"]}

    if primaryChart in ("rf_classifier_report_board", "classifier_validation_board", "roc", "pr_curve", "calibration"):
        return {"method": "auc_ci", "correction": None, "notes": ["bootstrap_ci_if_available"]}

    if primaryChart == "km":
        return {"method": "logrank", "correction": None, "notes": ["use_coxph_for_effect_panel_if_covariates_exist"]}

    if primaryChart == "forest":
        return {"method": "effect_estimate_only", "correction": None, "notes": ["estimates_supplied_by_upstream_model"]}

    if primaryChart == "dose_response":
        return {"method": "four_parameter_logistic", "correction": None, "notes": ["report_ec50_or_ic50"]}

    if "subject_id" in roles and "group" in roles and "value" in roles:
        return {"method": "paired_t_or_wilcoxon", "correction": None, "notes": ["choose_wilcoxon_if_non_normal"]}

    if "group" in roles and "value" in roles and (dataProfile["nGroups"] or 0) == 2:
        return {"method": "welch_t_or_mann_whitney", "correction": None, "notes": ["test_normality", "prefer_welch_if_normal"]}

    if "group" in roles and "value" in roles and (dataProfile["nGroups"] or 0) >= 3:
        correction = "fdr_bh" if rigor == "strict" else "bonferroni"
        return {"method": "anova_or_kruskal", "correction": correction, "notes": ["post_hoc_required"]}

    if primaryChart == "scatter_regression":
        return {"method": "pearson_or_spearman", "correction": None, "notes": ["report_effect_and_ci_when_possible"]}

    return {"method": "none", "correction": None, "notes": ["insufficient_design_information"]}
```

### Step 2.4: Configure Annotation Behavior

```python
def configure_annotations(dataProfile, primaryChart, statPlan):
    annotations = {
        "showIndividualPoints": primaryChart not in ("heatmap_cluster", "heatmap_pure", "volcano", "umap", "tsne", "pca", "manhattan", "qq"),
        "showSignificance": statPlan["method"] not in ("none", "effect_estimate_only"),
        "significanceDisplay": "exact_p",
        "showN": True,
        "showCI": primaryChart in ("line_ci", "forest", "classifier_validation_board", "roc", "pr_curve", "calibration"),
        "showAtRiskTable": primaryChart == "km",
        "showThresholdLines": primaryChart in ("volcano", "manhattan", "qq", "dose_response")
    }

    if not dataProfile["replicateInfo"]["has_bio_rep"] and "subject_id" not in dataProfile["semanticRoles"] and primaryChart not in ("km", "classifier_validation_board", "roc", "pr_curve", "forest"):
        annotations["showSignificance"] = False

    if dataProfile["nObservations"] > 500:
        annotations["showIndividualPoints"] = False

    return annotations
```

### Step 2.5: Build `panelBlueprint`

Map the story mode to one of the reusable layout recipes.

```python
def _dedupe_charts(charts):
    seen = set()
    ordered = []
    for chart in charts:
        if chart and chart not in seen:
            ordered.append(chart)
            seen.add(chart)
    return ordered


def _layout_label_burden(dataProfile):
    df = dataProfile.get("df")
    roles = dataProfile.get("semanticRoles", {})
    if df is None:
        return 0
    burden = 0
    for role in ("group", "condition", "label", "category"):
        col = roles.get(role)
        if col and col in df:
            labels = [str(v) for v in df[col].dropna().unique()]
            burden += sum(1 for label in labels if len(label) > 24)
    return min(burden, 6)


def _layout_legend_burden(n_groups, label_burden):
    if n_groups >= 12:
        return 6 + label_burden
    if n_groups >= 8:
        return 4 + label_burden
    if n_groups >= 6:
        return 2 + label_burden
    return label_burden


def infer_template_layout_intents(dataProfile, primaryChart, secondaryCharts):
    roles = dataProfile.get("semanticRoles", {})
    patterns = set(dataProfile.get("specialPatterns", []))
    charts = [primaryChart] + list(secondaryCharts or [])
    columns = [str(c).lower() for c in dataProfile.get("columnNames", [])]
    profile_tokens = set(columns) | {str(k).lower() for k in roles} | {str(v).lower() for v in roles.values()} | patterns
    architecture_metric_tokens = {"latency", "flops", "memory", "throughput", "edge_weight", "weight", "cost", "params", "parameters"}
    intents = []

    def add(intent):
        if intent not in intents:
            intents.append(intent)

    if "prediction_diagnostic" in patterns or ("actual" in roles and "predicted" in roles):
        add("prediction_diagnostic_matrix")
        add("joint_marginal_grid")
    if (
        "model_performance_benchmark" in patterns
        or "ml_model_family" in patterns
        or ("model" in roles and any(role in roles for role in ("metric", "score", "rmse", "mae", "residual")))
    ):
        add("ml_model_performance_triptych")
    if (
        "classifier_validation_board" in charts
        or "rf_classifier_report_board" in charts
        or "classifier_validation" in patterns
        or "threshold_tuning" in patterns
        or "probability_calibration" in patterns
        or (
            any(chart in ("roc", "pr_curve", "calibration", "confusion_matrix") for chart in charts)
            and ("score" in roles or any(token in profile_tokens for token in ("probability", "proba", "threshold")))
            and ("label" in roles or any(token in profile_tokens for token in ("true_label", "actual_label", "y_true")))
        )
    ):
        add("classifier_validation_board")
    if (
        "rf_classifier_report_board" in charts
        or "rf_classifier_validation_report" in patterns
        or (
            "classifier_validation_board" in charts
            and ("feature_importance" in patterns or "importance" in roles or "feature_id" in roles)
        )
    ):
        add("rf_classifier_report_board")
    if (
        "model_architecture_board" in charts
        or "model_architecture_board" in patterns
        or (
            any(chart in ("model_architecture", "model_architecture_board") for chart in charts)
            and bool(profile_tokens & architecture_metric_tokens)
        )
        or (
            bool(patterns & {"model_architecture", "neural_architecture", "architecture_diagram", "pipeline_topology", "dag_pipeline"})
            and bool(profile_tokens & architecture_metric_tokens)
        )
    ):
        add("architecture_metric_storyboard")
    if "ml_explainability" in patterns or "feature_importance" in patterns or "shap_value" in roles:
        add("ml_explainability_board")
    if "optimization_tradeoff" in patterns or "pareto_chart" in charts or "pareto_flag" in roles:
        add("pareto_tradeoff_board")
    if "prediction_interval" in patterns or ("pi_low" in roles and "pi_high" in roles):
        add("interval_uncertainty_band")
    if any(chart in ("heatmap_annotated", "heatmap_triangular", "correlation", "bubble_matrix") for chart in charts):
        add("correlation_evidence_matrix")
    return intents


def build_panel_blueprint(primaryChart, secondaryCharts, dataProfile, workflowPreferences):
    scale_policy = globals().get("DATA_SCALE_POLICY", {
        "legend_bottom_group_max": 8,
    })
    story_was_default = "storyMode" not in workflowPreferences
    story = workflowPreferences.get("storyMode", "comparison_pair")
    template_layout_intents = infer_template_layout_intents(dataProfile, primaryChart, secondaryCharts)
    if (story == "auto" or story_was_default) and "architecture_metric_storyboard" in template_layout_intents and primaryChart == "model_architecture_board":
        story = "single"
    elif (story == "auto" or story_was_default) and "rf_classifier_report_board" in template_layout_intents and primaryChart == "rf_classifier_report_board":
        story = "single"
    elif (story == "auto" or story_was_default) and "classifier_validation_board" in template_layout_intents and primaryChart == "classifier_validation_board":
        story = "single"
    elif (story == "auto" or story_was_default) and "architecture_metric_storyboard" in template_layout_intents:
        story = "architecture_metric_storyboard"
    elif (story == "auto" or story_was_default) and "ml_model_performance_triptych" in template_layout_intents:
        story = "ml_model_performance_triptych"
    elif (story == "auto" or story_was_default) and "prediction_diagnostic_matrix" in template_layout_intents:
        story = "prediction_diagnostic_matrix"
    elif (story == "auto" or story_was_default) and "ml_explainability_board" in template_layout_intents:
        story = "ml_explainability_board"
    elif (story == "auto" or story_was_default) and "pareto_tradeoff_board" in template_layout_intents:
        story = "asymmetric_L"
    elif workflowPreferences.get("journalStyle") == "cell" and story == "auto":
        story = "hero_plus_stacked_support"
    crowding_policy = workflowPreferences.get("crowdingPolicy", "auto_simplify")
    panel_candidates = dataProfile["panelCandidates"]
    candidate_pool = _dedupe_charts(
        [c["chart"] for c in panel_candidates if c["chart"] != primaryChart]
    )
    support_pool = _dedupe_charts(
        [chart for chart in list(secondaryCharts) + candidate_pool if chart != primaryChart]
    )
    requested_story = story

    PANEL_IDS = list("ABCDEFGHI")
    story_panel_map = {
        "single": 1,
        "comparison_pair": 2,
        "hero_plus_stacked_support": 3,
        "story_board_2x2": 4,
        "triple_horizontal": 3,
        "triple_vertical": 3,
        "stacked_pair": 2,
        "hero_plus_triple_support": 4,
        "asymmetric_L": 3,
        "ml_model_performance_triptych": 3,
        "architecture_metric_storyboard": 3,
        "board_2x3": 6,
        "board_3x3": 9,
        "prediction_diagnostic_matrix": 4,
        "ml_explainability_board": 4,
    }

    needed = story_panel_map.get(story, 2)
    available = 1 + len(support_pool)

    if needed > available:
        for fallback in ["story_board_2x2", "hero_plus_stacked_support", "comparison_pair", "single"]:
            if story_panel_map.get(fallback, 99) <= available:
                story = fallback
                needed = story_panel_map[story]
                break

    charts = [primaryChart] + support_pool[:needed - 1]
    roles = ["hero"] + ["support"] * (needed - 2) + (["context"] if needed > 2 else [])
    if len(roles) < needed:
        roles = ["hero"] + ["support"] * (needed - 1)

    panels = []
    for i in range(min(needed, len(charts))):
        panels.append({
            "id": PANEL_IDS[i],
            "role": roles[i] if i < len(roles) else "support",
            "chart": charts[i],
            "source": "primary" if i == 0 else "secondary",
        })

    layout_grid_map = {
        "ml_model_performance_triptych": "2x2-rf-diagnostic",
        "architecture_metric_storyboard": "2x2-architecture-metric",
        "prediction_diagnostic_matrix": "2x2-diagnostic",
        "ml_explainability_board": "2x2-explainability",
    }
    layout = {
        "recipe": story,
        "grid": layout_grid_map.get(story, f"{story_panel_map.get(story, 2)}"),
        "templateLayoutIntents": template_layout_intents,
    }

    continuous_scale_charts = {
        "heatmap_cluster", "heatmap_pure", "heatmap_annotated", "heatmap_triangular",
        "heatmap_mirrored", "heatmap_symmetric", "spatial_feature", "correlation"
    }
    n_groups = dataProfile.get("nGroups") or 1
    label_burden = _layout_label_burden(dataProfile)
    legend_burden = _layout_legend_burden(n_groups, label_burden)
    colorbar_burden = 2 if any(panel["chart"] in continuous_scale_charts for panel in panels) else 0
    layout_score = len(panels) * 2 + legend_burden + label_burden + colorbar_burden
    notes = ["keep_semantic_colors_consistent", "hero_panel_priority", "deduplicate_support_panels"]
    reflow_reasons = []
    if story != requested_story:
        notes.append(f"degraded_from_{requested_story}_to_{story}")
        reflow_reasons.append("insufficient_support_panels")
    if crowding_policy == "auto_simplify":
        notes.append("clarity_first_crowding_policy")
    if n_groups > scale_policy["legend_bottom_group_max"]:
        notes.append("high_legend_burden")
        reflow_reasons.append("many_groups")
    if label_burden:
        notes.append("long_label_burden")
        reflow_reasons.append("long_labels")

    return {
        "layout": layout,
        "panels": panels,
        "requestedLayout": requested_story,
        "finalLayout": story,
        "sharedLegend": n_groups > 1,
        "sharedColorbar": any(panel["chart"] in continuous_scale_charts for panel in panels),
        "axisLinkGroups": [["A", "B"]] if len(panels) >= 2 else [],
        "layoutIntents": template_layout_intents,
        "subAxesRequired": "joint_marginal_grid" in template_layout_intents,
        "colorbarSlotRequired": any(intent in template_layout_intents for intent in ("correlation_evidence_matrix", "ml_explainability_board")),
        "legendMode": "shared_auto",
        "colorbarMode": "shared_single" if any(panel["chart"] in continuous_scale_charts for panel in panels) else "none",
        "layoutScore": layout_score,
        "legendBurden": legend_burden,
        "labelBurden": label_burden,
        "reflowReasons": reflow_reasons,
        "notes": notes
    }
```

`_layout_label_burden` should count labels over 24 characters in semantic role columns; `_layout_legend_burden` should increase when groups exceed 6, 8, or 12. A lower layout score wins even if it drops a support panel. Never keep a four-panel plan only because four panels were requested.

### Step 2.6: Build `crowdingPlan`

```python
def build_crowding_plan(primaryChart, secondaryCharts, dataProfile, workflowPreferences, panelBlueprint):
    scale_policy = globals().get("DATA_SCALE_POLICY", {
        "point_density_full_max": 400,
        "point_density_alpha_max": 1000,
        "legend_bottom_group_max": 8,
    })
    policy = workflowPreferences.get("crowdingPolicy", "auto_simplify")
    n_obs = dataProfile.get("nObservations") or 0
    n_groups = dataProfile.get("nGroups") or 1
    final_layout = panelBlueprint.get("finalLayout", panelBlueprint["layout"]["recipe"])
    panel_count = len(panelBlueprint.get("panels", []))

    if n_obs <= scale_policy["point_density_full_max"]:
        point_density_mode = "full_points"
    elif n_obs <= scale_policy["point_density_alpha_max"]:
        point_density_mode = "alpha_jitter_small_markers"
    else:
        point_density_mode = "summary_or_thin_points"

    legend_mode = "bottom_center"

    layout_fallbacks = {
        "story_board_2x2": ["hero_plus_stacked_support", "comparison_pair", "single"],
        "hero_plus_stacked_support": ["comparison_pair", "single"],
        "comparison_pair": ["single"],
        "single": [],
        "triple_horizontal": ["comparison_pair", "single"],
        "triple_vertical": ["stacked_pair", "single"],
        "stacked_pair": ["single"],
        "board_2x3": ["story_board_2x2", "hero_plus_stacked_support", "comparison_pair", "single"],
        "board_3x3": ["board_2x3", "story_board_2x2", "hero_plus_stacked_support", "comparison_pair", "single"],
        "hero_plus_triple_support": ["hero_plus_stacked_support", "comparison_pair", "single"],
        "asymmetric_L": ["triple_horizontal", "comparison_pair", "single"],
        "architecture_metric_storyboard": ["ml_model_performance_triptych", "hero_plus_stacked_support", "comparison_pair", "single"],
        "prediction_diagnostic_matrix": ["story_board_2x2", "comparison_pair", "single"],
        "ml_explainability_board": ["story_board_2x2", "hero_plus_stacked_support", "comparison_pair", "single"],
    }.get(final_layout, ["comparison_pair", "single"])

    simplifications = []
    if panelBlueprint.get("finalLayout") != panelBlueprint.get("requestedLayout"):
        simplifications.append(f"layout_fallback:{panelBlueprint.get('requestedLayout')}->{panelBlueprint.get('finalLayout')}")
    if panelBlueprint.get("sharedLegend", False):
        simplifications.append("figure_level_shared_legend")
        simplifications.append("framed_shared_legend")
        simplifications.append("no_in_axes_legend")
    if panelBlueprint.get("sharedColorbar", False):
        simplifications.append("shared_colorbar")
    if point_density_mode != "full_points":
        simplifications.append(f"point_density:{point_density_mode}")
    if policy == "auto_simplify":
        simplifications.append("direct_labels_capped")

    return {
        "policy": policy,
        "overlapPriority": workflowPreferences.get("overlapPriority", "clarity_first"),
        "panelBudget": panel_count,
        "layoutFallbacks": layout_fallbacks,
        "legendScope": "figure",
        "legendMode": legend_mode,
        "legendPlacementPriority": ["bottom_center"],
        "legendAllowedModes": ["bottom_center"],
        "legendLabelMaxChars": 32,
        "maxLegendColumns": 6,
        "legendFrame": True,
        "legendFrameStyle": {
            "facecolor": "#FFFFFF",
            "edgecolor": "#222222",
            "linewidth": 0.55,
            "alpha": 0.96,
            "pad": 0.28,
            "boxstyle": "round",
        },
        "legendCenterPlacementOnly": True,
        "forbidOutsideRightLegend": True,
        "forbidInAxesLegend": True,
        "colorbarMode": panelBlueprint.get("colorbarMode", "none"),
        "maxDirectLabelsHero": 8 if policy == "preserve_information" else 5,
        "maxDirectLabelsSupport": 4 if policy == "preserve_information" else 3,
        "maxBracketGroups": 3 if policy == "preserve_information" else 2,
        "pointDensityMode": point_density_mode,
        "renderRetryLimit": 5,
        "layoutReflowRequiredOnOverlap": True,
        "legendExternalHardLimit": True,
        "axisLegendHardFail": True,
        "annotationMode": "compact" if policy == "auto_simplify" else "full",
        "simplifyIfCrowded": policy != "preserve_information",
        "simplificationsApplied": simplifications,
        "droppedDirectLabelCount": 0,
        "axisLegendRemainingCount": 0
    }
```

### Step 2.7: Build `visualContentPlan`

```python
import json
from pathlib import Path


def infer_visual_chart_family(chart_type):
    key = str(chart_type or "").replace("+", "_").lower()
    family_map = {
        "distribution": {
            "violin_strip", "box_strip", "raincloud", "beeswarm", "paired_lines",
            "dumbbell", "violin_paired", "violin_split", "dot_strip", "histogram",
            "density", "ecdf", "ridge", "joyplot", "box_paired", "mean_diff_plot",
            "ci_plot", "clustered_bar", "grouped_bar", "violin_grouped",
        },
        "scatter_embedding": {
            "scatter_regression", "correlation", "pca", "umap", "tsne",
            "ordination_plot", "bubble_scatter", "connected_scatter",
            "residual_vs_fitted", "scale_location", "pp_plot", "leverage_plot",
            "cook_distance", "bland_altman", "funnel_plot",
        },
        "matrix_heatmap": {
            "heatmap_cluster", "heatmap_pure", "heatmap_annotated",
            "heatmap_triangular", "heatmap_mirrored", "heatmap_symmetric",
            "adjacency_matrix", "cooccurrence_matrix", "bubble_matrix",
            "dotplot", "composition_dotplot", "confusion_matrix",
        },
        "time_series": {
            "line", "training_curve", "line_ci", "spaghetti", "sparkline", "area", "area_stacked",
            "streamgraph", "gantt", "timeline_annotation", "control_chart",
            "slope_chart", "bump_chart",
        },
        "clinical_diagnostic": {
            "rf_classifier_report_board", "classifier_validation_board", "roc", "pr_curve", "calibration", "km", "forest", "waterfall",
            "swimmer_plot", "risk_ratio_plot", "caterpillar_plot",
            "tornado_chart", "nomogram", "decision_curve",
        },
        "genomics_enrichment": {
            "volcano", "ma_plot", "manhattan", "qq", "enrichment_dotplot",
            "oncoprint", "lollipop_mutation", "circos_karyotype",
            "gene_structure", "pathway_map", "kegg_bar", "go_treemap",
            "chromosome_coverage",
        },
        "engineering_spectra": {
            "dose_response", "stress_strain", "phase_diagram", "nyquist_plot",
            "xrd_pattern", "ftir_spectrum", "dsc_thermogram",
        },
        "composition_flow": {
            "stacked_bar_comp", "alluvial", "treemap", "sunburst",
            "waffle_chart", "marimekko", "stacked_area_comp",
            "nested_donut", "chord_diagram", "parallel_coordinates",
            "sankey", "radar", "pareto_chart", "lollipop_horizontal",
            "stem_plot", "mosaic_plot", "diverging_bar", "model_architecture", "model_architecture_board",
        },
        "psych_ecology": {
            "species_abundance", "shannon_diversity", "biodiversity_radar",
            "likert_divergent", "likert_stacked", "mediation_path",
            "interaction_plot",
        },
    }
    for family, charts in family_map.items():
        if key in charts:
            return family
    return "generic"


def infer_reference_visual_motifs(charts, dataProfile):
    roles = dataProfile.get("semanticRoles", {})
    columns = [str(c).lower() for c in dataProfile.get("columnNames", [])]
    role_values = [str(v).lower() for v in roles.values()]
    families = [infer_visual_chart_family(chart) for chart in charts if chart]
    tokens = " ".join(columns + role_values)
    try:
        n_obs = dataProfile.get("nObservations") or len(dataProfile.get("df"))
    except TypeError:
        n_obs = dataProfile.get("nObservations") or 0
    motifs = []

    def add(name):
        if name not in motifs:
            motifs.append(name)

    if "matrix_heatmap" in families:
        add("diverging_colorbar")
        if n_obs <= 36:
            add("cell_value_labels")
        if any(token in tokens for token in ("pvalue", "p_value", "padj", "fdr", "qvalue")):
            add("significance_star_layer")
    if "scatter_embedding" in families:
        add("trend_or_fit_reference")
        if n_obs >= 6:
            add("density_halo")
        if any(token in tokens for token in ("actual", "observed", "measured", "experimental")) and any(
            token in tokens for token in ("pred", "predict", "fitted", "estimate")
        ):
            add("perfect_fit_reference")
            add("prediction_metric_table")
        if any(token in tokens for token in ("sample", "source", "reference", "cohort", "batch")):
            add("sample_shape_encoding")
    if "distribution" in families:
        add("sample_size_labels")
        add("median_iqr_summary")
    if "time_series" in families:
        add("endpoint_peak_labels")
        add("trajectory_delta_label")
    if "engineering_spectra" in families:
        add("peak_window_callout")
        add("range_summary_box")
    if "clinical_diagnostic" in families:
        if any(str(chart).lower() in ("rf_classifier_report_board", "classifier_validation_board", "roc", "pr_curve", "calibration") for chart in charts if chart):
            add("diagnostic_reference_line")
        add("diagnostic_metric_box")
    if "genomics_enrichment" in families:
        add("threshold_reference_lines")
        if any(token in tokens for token in ("gene", "feature", "label", "id")):
            add("top_feature_callouts")
    if "composition_flow" in families:
        add("composition_summary")
    if "psych_ecology" in families:
        add("response_summary")
    if any(token in tokens for token in ("rmse", "mae", "percent_error", "percentage_error", "error_pct")):
        add("dual_axis_error_bars")
    if not motifs:
        add("descriptive_summary_box")
    return motifs


def infer_template_visual_motifs(charts, dataProfile):
    roles = dataProfile.get("semanticRoles", {})
    columns = [str(c).lower() for c in dataProfile.get("columnNames", [])]
    patterns = set(dataProfile.get("specialPatterns", []))
    tokens = " ".join(columns + [str(v).lower() for v in roles.values()])
    chart_keys = {str(chart or "").replace("+", "_").lower() for chart in charts if chart}
    motifs = []
    provenance = []

    def add(name, requirement):
        if name not in motifs:
            motifs.append(name)
        if requirement not in provenance:
            provenance.append(requirement)

    if "prediction_diagnostic" in patterns or ("actual" in roles and "predicted" in roles):
        add("prediction_diagnostic_matrix", "actual_and_predicted_columns")
        add("joint_marginal_grid", "numeric_actual_predicted_pair")
        add("density_encoded_scatter", "numeric_xy_pair")
        add("metric_table_in_panel", "metrics_computed_from_actual_predicted")
    if (
        "classifier_validation_board" in chart_keys
        or "rf_classifier_report_board" in chart_keys
        or "classifier_validation" in patterns
        or "threshold_tuning" in patterns
        or "probability_calibration" in patterns
        or (
            {"roc", "pr_curve", "calibration", "confusion_matrix"} & chart_keys
            and ("score" in roles or "label" in roles or any(token in tokens for token in ("probability", "threshold", "auc", "f1", "precision", "recall")))
        )
    ):
        add("classifier_validation_board", "score_probability_label_or_threshold_columns")
        add("classification_error_matrix", "threshold_sweep_or_true_predicted_columns")
        add("metric_table_in_panel", "auc_ap_f1_ece_threshold_summary")
        if "rf_classifier_report_board" in chart_keys or "feature_importance" in patterns or "importance" in roles or "feature_id" in roles:
            add("rf_classifier_report_board", "rf_classifier_scores_plus_feature_importance")
            add("explainability_importance_stack", "feature_importance_or_shap_columns")
    if (
        "model_performance_benchmark" in patterns
        or "ml_model_family" in patterns
        or ("model" in roles and any(role in roles for role in ("metric", "score", "rmse", "mae", "residual")))
    ):
        add("ml_model_performance_triptych", "model_algorithm_metric_or_split_columns")
    if (
        "model_architecture_board" in chart_keys
        or "model_architecture" in chart_keys
        or "model_architecture" in patterns
        or "neural_architecture" in patterns
        or "pipeline_topology" in patterns
        or any(token in tokens for token in ("layer", "module", "component", "transformer", "attention", "encoder", "decoder"))
        or (("source" in roles or "from" in roles) and ("target" in roles or "to" in roles))
    ):
        add("neural_architecture_topology", "layer_module_or_source_target_topology_columns")
        add("metric_table_in_panel", "module_count_edge_count_or_parameter_summary")
        if "model_architecture_board" in chart_keys or any(token in tokens for token in ("latency", "flops", "memory", "throughput", "cost", "edge_weight", "params", "parameters")):
            add("architecture_metric_dashboard", "edge_or_module_metric_columns")
            add("architecture_metric_storyboard", "architecture_plus_metric_support_axes")
    if "model_error_diagnostic" in patterns or any(token in tokens for token in ("rmse", "mae", "percent_error", "percentage_error", "error_pct")):
        add("dual_axis_error_sidecar", "error_metric_column_or_computable_residuals")
    if "ml_explainability" in patterns or "feature_importance" in patterns or "shap_value" in roles or "importance" in roles:
        add("explainability_importance_stack", "feature_importance_or_shap_columns")
        add("signed_effect_axis", "signed_importance_or_effect_values")
    if "prediction_interval" in patterns or ("pi_low" in roles and "pi_high" in roles):
        add("interval_uncertainty_band", "provided_interval_columns")
    if ("ci_low" in roles and "ci_high" in roles) or "effect_interval" in patterns:
        add("forest_interval_board", "provided_effect_interval_columns")
    if any(token in tokens for token in ("pvalue", "p_value", "padj", "fdr", "qvalue")) and any(
        chart in chart_keys for chart in ("heatmap_annotated", "heatmap_triangular", "heatmap_symmetric", "correlation", "bubble_matrix")
    ):
        add("correlation_evidence_matrix", "matrix_or_correlation_values_plus_pvalues")
    if "optimization_tradeoff" in patterns or "pareto_flag" in roles or "pareto_chart" in chart_keys:
        add("pareto_tradeoff_board", "objective_columns_or_pareto_flags")
    if "radar" in chart_keys or "biodiversity_radar" in chart_keys:
        add("polar_comparison_signature", "radar_or_cyclic_comparison_columns")

    return {
        "motifs": motifs,
        "provenanceRequirements": provenance,
        "requiresMarginalAxes": "joint_marginal_grid" in motifs,
        "requiresDensityColor": "density_encoded_scatter" in motifs,
        "requiresColorbarSlot": "correlation_evidence_matrix" in motifs,
        "requiresMultiAxis": "dual_axis_error_sidecar" in motifs,
    }


_TEMPLATE_CASE_INDEX_CACHE = None
_TEMPLATE_CASE_INDEX_PATH = Path(".claude/skills/scifig-generate/template-mining/case-index.json")


def _normalize_template_token(value):
    return str(value or "").replace("+", "_").replace("-", "_").lower().strip()


def load_template_case_index(path=None):
    """Load mined template cases as UTF-8 data for recommendation routing."""
    global _TEMPLATE_CASE_INDEX_CACHE
    if _TEMPLATE_CASE_INDEX_CACHE is not None and path is None:
        return _TEMPLATE_CASE_INDEX_CACHE
    index_path = Path(path or _TEMPLATE_CASE_INDEX_PATH)
    try:
        cases = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        cases = []
    if path is None:
        _TEMPLATE_CASE_INDEX_CACHE = cases
    return cases


def _case_search_text(case):
    parts = [
        case.get("id", ""),
        case.get("file", ""),
        case.get("title", ""),
        case.get("narrative_arc", ""),
        case.get("preamble", ""),
        " ".join(case.get("chart_families", []) or []),
        " ".join(case.get("signature_tricks", []) or []),
    ]
    return _normalize_template_token(" ".join(str(part) for part in parts))


def _family_query_terms(family):
    terms_by_family = {
        "ml_model_diagnostics": {
            "machine", "learning", "model", "random", "forest", "rf", "training",
            "testing", "prediction", "residual", "rmse", "mae", "auc", "feature",
            "shap", "scatter_regression", "forest", "shap_composite",
        },
        "marginal_joint": {"marginal", "density", "kde", "scatter_regression", "subgrid", "parity"},
        "shap_composite": {"shap", "feature", "importance", "beeswarm", "waterfall", "shap_composite"},
        "heatmap_pairwise": {"heatmap", "correlation", "matrix", "pairwise"},
        "radar": {"radar", "spider", "polar"},
        "dual_axis": {"dual", "axis", "twin", "secondary", "spectrum", "dose"},
        "time_series_pi": {"time", "series", "prediction", "interval", "training", "testing"},
        "forest": {"forest", "hazard", "odds", "confidence", "interval"},
        "pareto": {"pareto", "optimization", "front", "tradeoff"},
    }
    return terms_by_family.get(family, {_normalize_template_token(family)})


def rank_template_cases_for_family(family, profile_tokens=None, limit=3):
    """Return case-index-backed anchors before static-anchor fallback."""
    terms = {_normalize_template_token(term) for term in _family_query_terms(family)}
    profile_terms = {_normalize_template_token(term) for term in (profile_tokens or set()) if term}
    scored = []
    for case in load_template_case_index():
        text = _case_search_text(case)
        families = {_normalize_template_token(item) for item in case.get("chart_families", []) or []}
        score = 0
        score += 4 * len(terms & families)
        score += sum(1 for term in terms if term and term in text)
        score += min(4, sum(1 for token in profile_terms if token and token in text))
        if family == "ml_model_diagnostics" and {"forest", "scatter_regression", "shap_composite"} & families:
            score += 3
        if score > 0:
            scored.append((score, case))
    scored.sort(key=lambda item: (-item[0], item[1].get("file", "")))
    return [
        {
            "file": case.get("file"),
            "id": case.get("id"),
            "chartFamilies": case.get("chart_families", []),
            "score": score,
        }
        for score, case in scored[:limit]
        if case.get("file")
    ]


def resolve_template_case_plan(primaryChart, secondaryCharts, workflowPreferences, dataProfile=None):
    """Bind selected or detected chart families to template-mining cases and technique refs."""
    selected_bundle = workflowPreferences.get("selectedChartBundle") or {}
    charts = [primaryChart] + list(secondaryCharts or [])
    normalized = {str(chart or "").replace("+", "_").lower() for chart in charts if chart}
    profile = dataProfile or {}
    roles = profile.get("semanticRoles", {}) or {}
    cols = {str(c).lower() for c in profile.get("columnNames", [])}
    patterns = {str(p).lower() for p in profile.get("specialPatterns", [])}
    domain_hint = str((profile.get("domainHints") or {}).get("primary", "")).lower()
    profile_tokens = set(cols) | {str(k).lower() for k in roles} | {str(v).lower() for v in roles.values()} | patterns
    ml_tokens = {
        "model", "algorithm", "estimator", "random forest", "rf", "rfr",
        "xgboost", "lightgbm", "gbdt", "svm", "knn", "train", "training",
        "test", "testing", "validation", "cv", "auc", "accuracy", "f1",
        "precision", "recall", "r2", "rmse", "mae", "residual", "shap",
        "feature_importance", "rf_classifier_report_board", "rf_classifier_validation_report", "confusion", "confusion_matrix", "classification_error",
        "true_label", "actual_label", "predicted_label", "prediction_label", "y_pred",
        "epoch", "learning_curve", "training_curve", "training_history",
        "train_loss", "training_loss", "val_loss", "validation_loss", "val_accuracy",
        "model_architecture", "model_architecture_board", "classifier_validation_board", "neural_architecture", "architecture_diagram",
        "pipeline_topology", "dag_pipeline", "layer", "module", "component",
        "block", "node", "source", "target", "params", "parameters", "units",
        "channels", "heads", "attention", "transformer", "encoder", "decoder",
        "latency", "flops", "memory", "throughput", "edge_weight",
    }
    feature_selection_tokens = {"n_features", "top_k", "feature_count", "ablation", "feature_selection", "incremental_feature_selection"}
    training_curve_tokens = {"epoch", "learning_curve", "training_curve", "training_history", "train_loss", "training_loss", "val_loss", "validation_loss", "val_accuracy"}
    architecture_tokens = {"model_architecture", "model_architecture_board", "neural_architecture", "architecture_diagram", "pipeline_topology", "dag_pipeline", "layer", "module", "component", "block", "node", "source", "target", "params", "parameters", "units", "channels", "heads", "attention", "transformer", "encoder", "decoder"}
    has_ml_signal = domain_hint == "computer_ai_ml" or bool(profile_tokens & ml_tokens)
    has_feature_selection_signal = bool(profile_tokens & feature_selection_tokens)
    has_training_curve_signal = bool(profile_tokens & training_curve_tokens)
    has_architecture_signal = bool(profile_tokens & architecture_tokens)
    family_map = {
        "scatter_regression": "marginal_joint",
        "residual_vs_fitted": "marginal_joint",
        "bland_altman": "marginal_joint",
        "histogram": "marginal_joint",
        "model_architecture": "ml_model_diagnostics",
        "model_architecture_board": "ml_model_diagnostics",
        "rf_classifier_report_board": "ml_model_diagnostics",
        "classifier_validation_board": "ml_model_diagnostics",
        "grouped_bar": "ml_model_diagnostics",
        "line": "ml_model_diagnostics",
        "training_curve": "ml_model_diagnostics",
        "lollipop_horizontal": "shap_composite",
        "dotplot": "shap_composite",
        "nested_donut": "shap_composite",
        "heatmap_annotated": "shap_composite",
        "confusion_matrix": "ml_model_diagnostics",
        "heatmap_triangular": "heatmap_pairwise",
        "heatmap_symmetric": "heatmap_pairwise",
        "correlation": "heatmap_pairwise",
        "bubble_matrix": "heatmap_pairwise",
        "radar": "radar",
        "biodiversity_radar": "radar",
        "forest": "forest",
        "km": "forest",
        "roc": "forest",
        "pr_curve": "forest",
        "calibration": "forest",
        "pareto_chart": "pareto",
        "dose_response": "dual_axis",
        "line_ci": "time_series_pi",
        "xrd_pattern": "dual_axis",
        "ftir_spectrum": "dual_axis",
        "dsc_thermogram": "dual_axis",
        "stress_strain": "dual_axis",
    }
    technique_by_family = {
        "marginal_joint": "template-mining/07-techniques/marginal-joint.md",
        "density_scatter": "template-mining/07-techniques/marginal-joint.md",
        "ml_model_diagnostics": "template-mining/07-techniques/ml-model-diagnostics.md",
        "shap_composite": "template-mining/07-techniques/shap-composite.md",
        "heatmap_pairwise": "template-mining/07-techniques/heatmap-pairwise.md",
        "radar": "template-mining/07-techniques/radar.md",
        "dual_axis": "template-mining/07-techniques/dual-axis.md",
        "time_series_pi": "template-mining/07-techniques/time-series-pi.md",
        "gradient_box": "template-mining/07-techniques/gradient-box.md",
        "inset_distribution": "template-mining/07-techniques/inset-distribution.md",
    }
    anchor_by_family = {
        "ml_model_diagnostics": [
            "期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱_1777456409.md",
            "拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md",
            "期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化_1777456510.md",
        ],
        "shap_composite": [
            "复现顶刊 _ 拒绝千篇一律的SHAP图，用Matplotlib手绘一张“蜂群+条形”组合图_1777452577.md",
        ],
        "marginal_joint": [
            "Python 科研绘图：如何优雅地展示“模型精度+稳定性”？顶刊可视化复盘_1777452458.md",
        ],
    }

    families = list(selected_bundle.get("templateFamilies") or [])
    for chart in sorted(normalized):
        family = family_map.get(chart)
        if family == "ml_model_diagnostics" and chart in {"line", "grouped_bar"} and not (selected_bundle or has_ml_signal or has_feature_selection_signal or has_training_curve_signal or has_architecture_signal):
            continue
        if family and family not in families:
            families.append(family)
        if chart in {"rf_classifier_report_board", "classifier_validation_board", "roc", "pr_curve", "calibration", "confusion_matrix"} and has_ml_signal and "ml_model_diagnostics" not in families:
            families.append("ml_model_diagnostics")
        if chart == "rf_classifier_report_board" and "shap_composite" not in families:
            families.append("shap_composite")

    technique_refs = list(selected_bundle.get("techniqueRefs") or [])
    for family in families:
        ref = technique_by_family.get(family)
        if ref and ref not in technique_refs:
            technique_refs.append(ref)

    anchors = list(selected_bundle.get("templateAnchors") or [])
    case_index_matches = {}
    for family in families:
        matches = rank_template_cases_for_family(family, profile_tokens=profile_tokens, limit=3)
        if matches:
            case_index_matches[family] = matches
        for match in matches:
            anchor = match.get("file")
            if anchor and anchor not in anchors:
                anchors.append(anchor)
    for family in families:
        for anchor in anchor_by_family.get(family, []):
            if anchor not in anchors:
                anchors.append(anchor)
    inferred_bundle_key = selected_bundle.get("bundleKey")
    if not inferred_bundle_key:
        chart_set = set(normalized)
        if "ml_model_diagnostics" in families and "model_architecture_board" in chart_set:
            inferred_bundle_key = "neural_architecture_metric_storyboard"
        elif "ml_model_diagnostics" in families and "rf_classifier_report_board" in chart_set:
            inferred_bundle_key = "rf_classifier_validation_report"
        elif "ml_model_diagnostics" in families and "model_architecture" in chart_set:
            inferred_bundle_key = "neural_architecture_topology"
        elif "ml_model_diagnostics" in families and "training_curve" in chart_set:
            inferred_bundle_key = "neural_training_dynamics"
        elif "ml_model_diagnostics" in families and "line" in chart_set and has_feature_selection_signal:
            inferred_bundle_key = "incremental_feature_selection_curve"
        elif "ml_model_diagnostics" in families and {"grouped_bar", "scatter_regression", "residual_vs_fitted"} & chart_set:
            inferred_bundle_key = "rf_model_performance_report"
        elif "shap_composite" in families and {"lollipop_horizontal", "dotplot", "scatter_regression", "heatmap_annotated"} & chart_set:
            inferred_bundle_key = "rf_feature_importance_shap"
        elif "classifier_validation_board" in chart_set or {"roc", "pr_curve", "calibration", "confusion_matrix"} & chart_set:
            inferred_bundle_key = "classifier_validation_board"
    template_match_mode = selected_bundle.get("templateMatchMode") or ("clone_when_known" if families else "best_effort")
    if inferred_bundle_key and families:
        template_match_mode = "clone_when_known"
    return {
        "selectedByUser": bool(selected_bundle),
        "bundleKey": inferred_bundle_key,
        "inferredBundleKey": inferred_bundle_key if not selected_bundle.get("bundleKey") else None,
        "label": selected_bundle.get("label"),
        "templateMatchMode": template_match_mode,
        "exactTemplateReplicationRequired": bool(families),
        "caseIndexResolverUsed": bool(case_index_matches),
        "caseIndexMatches": case_index_matches,
        "primaryChart": primaryChart,
        "secondaryCharts": list(secondaryCharts or []),
        "families": families,
        "techniqueRefs": technique_refs,
        "anchors": anchors,
        "instructions": [
            "if_chart_type_matches_template_family_clone_template_structure_first",
            "preserve_template_chart_composition_before_data_specific_adaptation",
            "use_template_palette_layering_annotation_idioms_when_supported",
            "when_bundleKey_is_inferred_follow_the_same_template_case_as_user_selected_bundle",
            "when_feature_count_or_ablation_columns_exist_clone_incremental_feature_selection_curve",
            "when_probability_label_or_threshold_columns_exist_clone_classifier_validation_board",
            "when_architecture_metric_columns_exist_clone_architecture_metric_storyboard",
            "when_layer_module_or_source_target_columns_exist_clone_neural_architecture_topology",
        ],
    }


def build_visual_content_plan(primaryChart, secondaryCharts, dataProfile, workflowPreferences):
    scale_policy = globals().get("DATA_SCALE_POLICY", {
        "point_density_alpha_max": 1000,
        "legend_bottom_group_max": 8,
    })
    charts = [primaryChart] + list(secondaryCharts or [])
    mode = workflowPreferences.get("visualContentMode", "nature_cell_dense")
    density = workflowPreferences.get("visualDensity", "high")
    n_obs = dataProfile.get("nObservations") or 0
    n_groups = dataProfile.get("nGroups") or 0
    max_callouts = 8
    if n_obs > scale_policy["point_density_alpha_max"]:
        max_callouts = 6
        point_annotation_mode = "summary_plus_extremes"
    elif n_groups > scale_policy["legend_bottom_group_max"]:
        max_callouts = 5
        point_annotation_mode = "group_summary"
    else:
        point_annotation_mode = "direct_when_legible"
    reference_motifs = infer_reference_visual_motifs(charts, dataProfile)
    template_motif_plan = infer_template_visual_motifs(charts, dataProfile)
    template_case_plan = resolve_template_case_plan(primaryChart, secondaryCharts, workflowPreferences, dataProfile)
    template_motifs = template_motif_plan["motifs"]
    template_density_bonus = min(2, len(template_motifs))

    return {
        "mode": mode,
        "density": density,
        "impactLevel": workflowPreferences.get("visualImpactLevel", "editorial_science"),
        "maxCalloutsSingle": max_callouts,
        "maxCalloutsSupport": 4,
        "maxInlineStats": 4,
        "minEnhancementsPerPanel": 2,
        "minTotalEnhancements": max(4, len(charts) * 2 + template_density_bonus),
        "referenceMotifsRequired": True,
        "minReferenceMotifsPerFigure": min(max(1, len(reference_motifs)), max(2, min(3, len(charts) + 1))),
        "visualGrammarMotifs": reference_motifs,
        "visualGrammarMotifsApplied": [],
        "templateMotifsRequired": bool(template_motifs),
        "templateMotifs": template_motifs,
        "templateMotifsApplied": [],
        "templateMotifCount": 0,
        "minTemplateMotifsPerFigure": template_density_bonus,
        "templateCasePlan": template_case_plan,
        "templateCaseAnchors": template_case_plan["anchors"],
        "templateTechniqueRefs": template_case_plan["techniqueRefs"],
        "templateMatchMode": template_case_plan["templateMatchMode"],
        "exactTemplateReplicationRequired": template_case_plan["exactTemplateReplicationRequired"],
        "layoutIntents": template_motifs,
        "provenanceRequirements": template_motif_plan["provenanceRequirements"],
        "requireInPlotExplanatoryLabels": True,
        "minInPlotLabelsPerFigure": min(max(1, len(charts)), max_callouts),
        "semanticCalloutMode": "data_derived",
        "useInsetAxes": True,
        "useMarginalAxes": template_motif_plan["requiresMarginalAxes"],
        "useMetricTables": True,
        "useDensityHalos": True,
        "useDensityColorEncoding": template_motif_plan["requiresDensityColor"],
        "usePerfectFitReference": True,
        "useSampleShapeEncoding": True,
        "useSignificanceStarLayer": True,
        "useDualAxisErrorBars": True,
        "requiresColorbarSlot": template_motif_plan["requiresColorbarSlot"],
        "requiresMultiAxisEncoding": template_motif_plan["requiresMultiAxis"],
        "noInventedStats": True,
        "statProvenanceRequired": True,
        "pointAnnotationMode": point_annotation_mode,
        "familyByChart": {chart: infer_visual_chart_family(chart) for chart in charts if chart},
        "appliedEnhancements": [],
        "familyByPanel": {},
        "metricBoxCount": 0,
        "metricTableCount": 0,
        "insetCount": 0,
        "referenceLineCount": 0,
        "densityHaloCount": 0,
        "sampleEncodingCount": 0,
        "significanceStarLayerCount": 0,
        "dualAxisEncodingCount": 0,
        "marginalAxesCount": 0,
        "densityColorEncodingCount": 0,
        "subAxesCount": 0,
        "colorbarSlotCount": 0,
        "multiAxisEncodingCount": 0,
        "referenceMotifCount": 0,
        "inPlotExplanatoryLabelCount": 0,
        "outsideLayoutElements": True,
        "statProvenance": [],
        "notes": [
            "do_not_add_new_chart_types",
            "statistics_must_be_data_derived",
            "nature_cell_information_density",
            "reference_visual_grammar_required",
            "template_visual_motifs_required_when_data_supports_them",
            "clone_known_template_family_before_style_generalization",
            "minimum_inplot_explanatory_labels_required",
            "minimum_visual_enhancement_count_required"
        ]
    }
```

### Step 2.8: Build `palettePlan`

```python
def build_palette_plan(primaryChart, dataProfile, workflowPreferences):
    domain = dataProfile["domainHints"]["primary"]
    patterns = set(dataProfile.get("specialPatterns", []))
    color_mode = workflowPreferences.get("colorMode", "journal_safe_muted")

    plan = {
        "mode": color_mode,
        "categoricalPreset": "journal_muted_8",
        "sequentialPreset": "seq_cool",
        "divergingPreset": "div_expression" if primaryChart in ("volcano", "heatmap_cluster", "heatmap_pure", "correlation") else "div_centered",
        "semanticMap": {
            "control": "#1F4E79",
            "treatment": "#C8553D",
            "treated": "#C8553D",
            "drug": "#C8553D",
            "rescue": "#4C956C",
            "train": "#4C78A8",
            "test": "#E45756",
            "actual": "#1F4E79",
            "observed": "#1F4E79",
            "predicted": "#C8553D",
            "feature_low": "#3B6FB6",
            "feature_high": "#B5403A",
            "positive_correlation": "#B5403A",
            "negative_correlation": "#3B6FB6",
            "optimal": "#00A087"
        },
        "grayscaleCheck": True,
        "sharedAcrossPanels": True,
        "deterministicCategoryOrder": True,
        "overflowEncoding": "marker_or_linestyle",
        "minGrayscaleDelta": 0.18,
        "contrastAuditRequired": True
    }

    if color_mode == "domain_semantic":
        if domain == "computer_ai_ml" or any(p in patterns for p in ("model_performance_benchmark", "ml_model_family", "ml_explainability", "feature_importance")):
            plan["categoricalPreset"] = "ml_model_performance_10"
            plan["sequentialPreset"] = "seq_cool"
            plan["semanticMap"].update({
                "rf": "#4DBBD5",
                "random forest": "#4DBBD5",
                "rfr": "#4DBBD5",
                "xgboost": "#E64B35",
                "lightgbm": "#00A087",
                "gbdt": "#3C5488",
                "svm": "#F39B7F",
                "knn": "#8491B4",
                "training": "#F6CFA3",
                "testing": "#9BCBEB",
                "residual_zero": "#B00000"
            })
        if domain == "clinical_diagnostics_survival":
            plan["categoricalPreset"] = "clinical_survival"
            plan["sequentialPreset"] = "seq_warm"
        if domain == "genomics_transcriptomics":
            plan["categoricalPreset"] = "genomics_categorical"
        if domain == "single_cell_spatial":
            plan["categoricalPreset"] = "journal_muted_8"
    if color_mode == "strict_grayscale_safe":
        plan["categoricalPreset"] = "journal_muted_6"

    return plan
```

### Step 2.9: Assemble `chartPlan` And Confirm With User

```python
domainProfile = resolve_domain(dataProfile, workflowPreferences)
primaryChart, secondaryCharts = recommend_chart_bundle(dataProfile, workflowPreferences)
statPlan = select_statistical_plan(dataProfile, primaryChart, workflowPreferences)
annotations = configure_annotations(dataProfile, primaryChart, statPlan)
panelBlueprint = build_panel_blueprint(primaryChart, secondaryCharts, dataProfile, workflowPreferences)
crowdingPlan = build_crowding_plan(primaryChart, secondaryCharts, dataProfile, workflowPreferences, panelBlueprint)
visualContentPlan = build_visual_content_plan(primaryChart, secondaryCharts, dataProfile, workflowPreferences)
templateCasePlan = visualContentPlan.get("templateCasePlan", resolve_template_case_plan(primaryChart, secondaryCharts, workflowPreferences, dataProfile))
palettePlan = build_palette_plan(primaryChart, dataProfile, workflowPreferences)

delegationReports = {
    "stats": chartPlanReview.get("stats") if "chartPlanReview" in globals() else None,
    "layout": chartPlanReview.get("layout") if "chartPlanReview" in globals() else None,
    "palette": chartPlanReview.get("palette") if "chartPlanReview" in globals() else None,
}

chartPlan = {
    "domainProfile": domainProfile,
    "primaryChart": primaryChart,
    "secondaryCharts": secondaryCharts,
    "fallbackChart": secondaryCharts[0] if secondaryCharts else None,
    "statMethod": statPlan["method"],
    "multipleComparison": statPlan["correction"],
    "statNotes": statPlan["notes"],
    "annotations": annotations,
    "panelBlueprint": panelBlueprint,
    "crowdingPlan": crowdingPlan,
    "visualContentPlan": visualContentPlan,
    "templateMotifs": visualContentPlan.get("templateMotifs", []),
    "templateCasePlan": templateCasePlan,
    "palettePlan": palettePlan,
    "delegationReports": delegationReports,
    "journalOverrides": {},
    "rationale": "Selected using semantic roles, special patterns, domain hints, requested story mode, template-case chart bundle constraints, layout scoring, clarity-first crowding control, palette contrast policy, and Nature/Cell dense visual content."
}
```

Before locking `chartPlan`, optionally use read-only agents when the plan is complex:

- `chart-stats-planner`: validate chart/stat fit, replicate meaning, and no invented inferential claims.
- `panel-layout-auditor`: validate support-panel dedupe, layout score, legend burden, axis linking, and reflow fallbacks.
- `palette-journal-auditor`: validate semantic color mapping, grayscale contrast, journal profile fit, and overflow marker/linestyle fallback.

Additionally, these advisory agents run after their respective plan steps:

- `scientific-color-harmony`: after `palettePlan` is built, evaluates perceptual harmony, color-wheel relationships, and domain aesthetics. Writes to `chartPlan.delegationReports.color_harmony`.
- `layout-aesthetics`: after `panelBlueprint` is built, evaluates whitespace balance, visual weight distribution, panel proportions, and grid harmony. Writes to `chartPlan.delegationReports.aesthetics`.
- `content-richness`: after `visualContentPlan` is built, evaluates annotation density, label informativeness, reference visual grammar motifs, marker diversity, and directional elements. Writes to `chartPlan.delegationReports.content_richness`.

These three advisory agents are non-blocking — findings are logged but do not block Phase 3 entry.

Advisory agent dispatch protocol:

```python
# After palettePlan is built
color_harmony = Agent(
    subagent_type="general-purpose",
    prompt=f"Evaluate the perceptual harmony of this palette plan for a {domain} domain figure. "
           f"Palette: {palettePlan}. Journal profile: {journalProfile}. "
           f"Assess: color-wheel relationships, perceptual uniformity, domain aesthetic fit. "
           f"Return JSON: {{\"harmony_score\": 0-100, \"findings\": [...], \"suggestions\": [...]}}"
)
chartPlan["delegationReports"]["color_harmony"] = color_harmony

# After panelBlueprint is built
aesthetics = Agent(
    subagent_type="general-purpose",
    prompt=f"Evaluate the layout aesthetics of this {len(panels)}-panel {recipe} figure. "
           f"Panel blueprint: {panelBlueprint}. Journal profile: {journalProfile}. "
           f"Assess: whitespace balance, visual weight distribution, panel proportions, grid harmony. "
           f"Return JSON: {{\"aesthetics_score\": 0-100, \"findings\": [...], \"suggestions\": [...]}}"
)
chartPlan["delegationReports"]["aesthetics"] = aesthetics

# After visualContentPlan is built
richness = Agent(
    subagent_type="general-purpose",
    prompt=f"Evaluate the content richness of this figure's visual content plan. "
           f"Plan: {visualContentPlan}. Chart types: {[p['chart'] for p in panels]}. "
           f"Assess: annotation density, label informativeness, reference visual grammar motifs "
           f"(metric tables, perfect-fit lines, density halos, significance stars when p-values exist, "
           f"dual-axis error bars when error columns exist), marker diversity, directional elements. "
           f"Return JSON: {{\"richness_score\": 0-100, \"findings\": [...], \"suggestions\": [...]}}"
)
chartPlan["delegationReports"]["content_richness"] = richness
```

Any blocking finding must be resolved in Phase 2 before Phase 3 starts.

Present the summary:

```text
Recommended figure plan:
  Domain: genomics_transcriptomics
  Primary chart: volcano
  Support charts: heatmap+cluster, enrichment_dotplot, pca
  Story recipe: story_board_2x2
  Statistical mode: none on hero panel, FDR-aware support panels where applicable
  Palette: journal_muted_8 + div_expression

Rationale:
  Differential-analysis columns strongly imply a genomics workflow.
  Volcano is the best hero panel for effect size + significance.
  Heatmap and enrichment dotplot support mechanism and pathway context.
```

Allow the user to adjust chart family, layout recipe, stats mode, or palette mode before Phase 3.

## Output

- **Variable**: `chartPlan`
- **TodoWrite**: Mark Phase 2 completed, Phase 3 in_progress

## Next Phase

Return to orchestrator, then continue to [Phase 3: Code Generation, Journal Styling, And Composition](03-code-gen-style.md).
