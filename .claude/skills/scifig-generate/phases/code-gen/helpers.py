```python
# Shared Helper Functions for Chart Generators and Crowding Control

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse


VISUAL_CONTENT_DEFAULTS = {
    "mode": "nature_cell_dense",
    "density": "high",
    "impactLevel": "editorial_science",
    "maxCalloutsSingle": 8,
    "maxCalloutsSupport": 4,
    "maxInlineStats": 4,
    "minEnhancementsPerPanel": 2,
    "minTotalEnhancements": 4,
    "requireInPlotExplanatoryLabels": True,
    "minInPlotLabelsPerFigure": 1,
    "semanticCalloutMode": "data_derived",
    "useInsetAxes": True,
    "referenceMotifsRequired": True,
    "minReferenceMotifsPerFigure": 2,
    "useMetricTables": True,
    "useMetricTableFallbackBox": True,
    "useDensityHalos": True,
    "useDensityColorEncoding": True,
    "useMarginalAxes": True,
    "usePerfectFitReference": True,
    "useSampleShapeEncoding": True,
    "useSignificanceStarLayer": True,
    "useDualAxisErrorBars": True,
    "templateMotifsRequired": False,
    "minTemplateMotifsPerFigure": 0,
    "exactMotifCoverageRequired": True,
    "useTemplateMotifs": True,
    "noInventedStats": True,
    "statProvenanceRequired": True,
    "outsideLayoutElements": True,
}


CROWDING_DEFAULTS = {
    "legendScope": "figure",
    "legendMode": "bottom_center",
    "legendPlacementPriority": ["bottom_center"],
    "legendAllowedModes": ["bottom_center"],
    "legendLabelMaxChars": 32,
    "legendFontSizePt": 7,
    "legendBottomAnchorY": 0.015,
    "legendBottomMarginNoLegend": 0.05,
    "legendBottomMarginMin": 0.06,
    "legendBottomMarginMax": 0.16,
    "maxLegendColumns": 6,
    "legendFrame": True,
    "legendFrameStyle": {
        "facecolor": "#FFFFFF",
        "edgecolor": "#cccccc",
        "linewidth": 0.55,
        "alpha": 1.0,
        "pad": 0.4,
        "boxstyle": "round",
    },
    "legendCenterPlacementOnly": True,
    "forbidOutsideRightLegend": True,
    "forbidInAxesLegend": True,
    "colorbarMode": "none",
    "colorbarReflowRequiredOnOverlap": True,
    "colorbarReservedRight": 0.78,
    "colorbarReflowPad": 0.04,
    "colorbarReflowWidth": 0.025,
    "colorbarReflowMinHeight": 0.20,
    "maxDirectLabelsHero": 5,
    "maxDirectLabelsSupport": 3,
    "maxBracketGroups": 2,
    "pointDensityMode": "alpha_jitter_small_markers",
    "simplifyIfCrowded": True,
    "renderRetryLimit": 5,
    "layoutReflowRequiredOnOverlap": True,
    "legendExternalHardLimit": True,
    "axisLegendHardFail": True,
    "layoutContractRequired": True,
    "maxTextFontSizePt": 12,
    "maxPanelLabelFontSizePt": 12,
    "forbidNegativeAxesText": True,
    "maxFigureWhitespaceFraction": 0.82,
    "minFigureInkFraction": 0.04,
    "legendReflowStrategy": ["margin_adjust", "height_increase", "entry_reduction"],
    "legendMaxHeightMultiplier": 1.3,
    "simplificationsApplied": [],
    "droppedDirectLabelCount": 0,
}


def sanitize_columns(df):
    """Rename columns to safe Python identifiers. Returns (df_renamed, name_map)."""
    name_map = {}
    new_cols = []
    for col in df.columns:
        safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(col)).strip('_')
        if safe and safe[0].isdigit():
            safe = 'col_' + safe
        safe = safe or 'unnamed'
        base = safe
        i = 1
        while safe in new_cols:
            safe = f"{base}_{i}"
            i += 1
        new_cols.append(safe)
        if safe != col:
            name_map[safe] = col
    df.columns = new_cols
    return df, name_map


def apply_chart_polish(ax, chart_type):
    """Apply publication-quality post-processing to any axes.

    Polar-safe: matplotlib's polar Axes only owns a 'polar' spine, not
    'top'/'right'. Guard the cartesian spine hiding so radar / polar charts
    can call this generically without KeyError.
    """
    spines = getattr(ax, "spines", None)
    is_polar = getattr(ax, "name", "") == "polar" or (
        hasattr(spines, "__contains__") and "polar" in spines and "top" not in spines
    )
    if not is_polar and spines is not None:
        if "top" in spines:
            ax.spines["top"].set_visible(False)
        if "right" in spines:
            ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.6, pad=2)

    if chart_type in ("violin_strip", "violin_paired", "violin_split", "violin_grouped"):
        for coll in ax.collections:
            if hasattr(coll, "set_alpha"):
                coll.set_alpha(0.3)

    if chart_type in ("violin_strip", "box_strip", "dot+box", "bar"):
        ymin = ax.get_ylim()[0]
        if ymin > 0:
            ax.set_ylim(bottom=0)

    for text in ax.texts:
        if text.get_text().startswith("n="):
            text.set_fontsize(5)
            text.set_color("#333")


def add_significance_bracket(ax, x1, x2, y, height, p_value, lw=0.6):
    """Add a Nature-style significance bracket with T-caps and italic p."""
    cap_w = height * 0.25
    ax.plot([x1, x1], [y, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x2, x2], [y, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x1, x2], [y + height, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x1 - cap_w, x1 + cap_w], [y, y], lw=lw, c="black", clip_on=False)
    ax.plot([x2 - cap_w, x2 + cap_w], [y, y], lw=lw, c="black", clip_on=False)
    if p_value < 0.001:
        p_text = "p < 0.001"
    else:
        p_text = f"p = {p_value:.3g}"
    ax.text((x1 + x2) / 2, y + height * 1.1, p_text, ha="center", va="bottom",
            fontsize=6, fontstyle="italic")


def format_p_value(p_value):
    if p_value < 0.001:
        return "p < 0.001"
    return f"p = {p_value:.2g}"


def _resolve_roles(dataProfile):
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")
    x_col = roles.get("x") or roles.get("condition")
    return group_col, value_col, x_col


def _extract_colors(palette, categories):
    cat_colors = palette.get("categoryMap", {})
    fallback = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                            "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])
    color_map = {}
    for i, cat in enumerate(categories):
        if cat in cat_colors:
            color_map[cat] = cat_colors[cat]
        else:
            color_map[cat] = fallback[i % len(fallback)]
    return color_map


def display_label(sanitized_name, col_map):
    if not col_map:
        return sanitized_name
    return col_map.get(sanitized_name, sanitized_name)


def infer_chart_family(chart_type):
    """Map chart keys to reusable visual-content recipes."""
    key = str(chart_type or "").replace("+", "_").lower()
    groups = {
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
    for family, keys in groups.items():
        if key in keys:
            return family
    return "generic"


def default_visual_content_plan():
    return {
        **VISUAL_CONTENT_DEFAULTS,
        "appliedEnhancements": [],
        "familyByPanel": {},
        "visualGrammarMotifs": [],
        "visualGrammarMotifsApplied": [],
        "templateMotifs": [],
        "templateMotifsApplied": [],
        "statProvenance": [],
        "metricBoxCount": 0,
        "metricTableCount": 0,
        "metricTableRelocatedCount": 0,
        "metricTableSuppressedCount": 0,
        "metricTableFallbackBoxCount": 0,
        "insetCount": 0,
        "referenceLineCount": 0,
        "densityHaloCount": 0,
        "sampleEncodingCount": 0,
        "significanceStarLayerCount": 0,
        "dualAxisEncodingCount": 0,
        "referenceMotifCount": 0,
        "templateMotifCount": 0,
        "marginalAxesCount": 0,
        "densityColorEncodingCount": 0,
        "subAxesCount": 0,
        "colorbarSlotCount": 0,
        "multiAxisEncodingCount": 0,
        "inPlotExplanatoryLabelCount": 0,
        "renderQaHooks": {
            "trackMetricBoxes": True,
            "trackMetricTables": True,
            "trackInsets": True,
            "trackReferenceLines": True,
            "trackDensityHalos": True,
            "trackDensityColorEncoding": True,
            "trackMarginalAxes": True,
            "trackSampleEncodings": True,
            "trackOutsideArtists": True,
            "trackInPlotLabels": True,
        },
    }


def infer_reference_motifs(charts, dataProfile=None):
    """Plan reusable evidence-layer motifs from chart families and semantic roles."""
    dataProfile = dataProfile or {}
    roles = dataProfile.get("semanticRoles", {}) if isinstance(dataProfile, dict) else {}
    cols = [str(c).lower() for c in dataProfile.get("columnNames", [])] if isinstance(dataProfile, dict) else []
    role_values = [str(v).lower() for v in roles.values()]
    families = [infer_chart_family(chart) for chart in charts if chart]
    tokens = " ".join(cols + role_values)
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
    if "clinical_diagnostic" in families:
        if any(str(chart).lower() in ("rf_classifier_report_board", "classifier_validation_board", "roc", "pr_curve", "calibration") for chart in charts if chart):
            add("diagnostic_reference_line")
        add("diagnostic_metric_box")
    if "genomics_enrichment" in families:
        add("threshold_reference_lines")
        if any(token in tokens for token in ("gene", "feature", "label", "id")):
            add("top_feature_callouts")
    if "distribution" in families:
        add("sample_size_labels")
        add("median_iqr_summary")
    if "time_series" in families:
        add("endpoint_peak_labels")
        add("trajectory_delta_label")
    if "engineering_spectra" in families:
        add("peak_window_callout")
        add("range_summary_box")
    if "composition_flow" in families:
        add("composition_summary")
    if "psych_ecology" in families:
        add("response_summary")
    if any(token in tokens for token in ("rmse", "mae", "percent_error", "percentage_error", "error_pct")):
        add("dual_axis_error_bars")
    if not motifs:
        add("descriptive_summary_box")
    return motifs


def infer_template_motifs(charts, dataProfile=None):
    """Infer template-derived evidence motifs without adding unsupported chart keys."""
    dataProfile = dataProfile or {}
    roles = dataProfile.get("semanticRoles", {}) if isinstance(dataProfile, dict) else {}
    cols = [str(c).lower() for c in dataProfile.get("columnNames", [])] if isinstance(dataProfile, dict) else []
    patterns = set(dataProfile.get("specialPatterns", [])) if isinstance(dataProfile, dict) else set()
    role_values = [str(v).lower() for v in roles.values()]
    tokens = " ".join(cols + role_values)
    chart_keys = {str(chart or "").replace("+", "_").lower() for chart in charts if chart}
    motifs = []

    def add(name):
        if name not in motifs:
            motifs.append(name)

    if "prediction_diagnostic" in patterns or ("actual" in roles and "predicted" in roles):
        add("prediction_diagnostic_matrix")
        add("joint_marginal_grid")
        add("density_encoded_scatter")
        add("metric_table_in_panel")
    if (
        "model_performance_benchmark" in patterns
        or "ml_model_family" in patterns
        or ("model" in roles and any(role in roles for role in ("metric", "score", "rmse", "mae", "residual")))
    ):
        add("ml_model_performance_triptych")
    if (
        "model_architecture_board" in chart_keys
        or "model_architecture" in chart_keys
        or "model_architecture" in patterns
        or "neural_architecture" in patterns
        or "pipeline_topology" in patterns
        or any(token in tokens for token in ("layer", "module", "component", "transformer", "attention", "encoder", "decoder"))
        or (("source" in roles or "from" in roles) and ("target" in roles or "to" in roles))
    ):
        add("neural_architecture_topology")
        add("metric_table_in_panel")
        if "model_architecture_board" in chart_keys or any(token in tokens for token in ("latency", "flops", "memory", "throughput", "cost", "edge_weight", "params", "parameters")):
            add("architecture_metric_dashboard")
            add("architecture_metric_storyboard")
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
        add("classifier_validation_board")
        add("classification_error_matrix")
        add("metric_table_in_panel")
        if "rf_classifier_report_board" in chart_keys or "feature_importance" in patterns or "importance" in roles or "feature_id" in roles:
            add("rf_classifier_report_board")
            add("explainability_importance_stack")
    if (
        "confusion_matrix" in chart_keys
        or "confusion_matrix" in patterns
        or "classification_error" in patterns
        or any(token in tokens for token in ("true_label", "actual_label", "predicted_label", "prediction_label", "y_pred"))
    ):
        add("classification_error_matrix")
        add("metric_table_in_panel")
    if (
        "training_curve" in chart_keys
        or "training_curve" in patterns
        or "learning_curve" in patterns
        or "training_history" in patterns
        or any(token in tokens for token in ("epoch", "train_loss", "training_loss", "val_loss", "validation_loss", "val_accuracy"))
    ):
        add("neural_training_dynamics")
        add("metric_table_in_panel")
    if "model_error_diagnostic" in patterns or any(token in tokens for token in ("rmse", "mae", "percent_error", "percentage_error", "error_pct")):
        add("dual_axis_error_sidecar")
    if "ml_explainability" in patterns or "feature_importance" in patterns or "shap_value" in roles or "importance" in roles:
        add("explainability_importance_stack")
        add("signed_effect_axis")
    if "prediction_interval" in patterns or ("pi_low" in roles and "pi_high" in roles):
        add("interval_uncertainty_band")
    if ("ci_low" in roles and "ci_high" in roles) or "effect_interval" in patterns:
        add("forest_interval_board")
    if any(token in tokens for token in ("pvalue", "p_value", "padj", "fdr", "qvalue")) and any(
        chart in chart_keys for chart in ("heatmap_annotated", "heatmap_triangular", "heatmap_symmetric", "correlation", "bubble_matrix")
    ):
        add("correlation_evidence_matrix")
    if "optimization_tradeoff" in patterns or "pareto_flag" in roles or "pareto_chart" in chart_keys:
        add("pareto_tradeoff_board")
    if "radar" in chart_keys or "biodiversity_radar" in chart_keys:
        add("polar_comparison_signature")
    return motifs


def build_visual_content_plan(primaryChart, secondaryCharts=None, dataProfile=None,
                              workflowPreferences=None, existing=None):
    """Create the default Nature/Cell dense visual-content contract."""
    workflowPreferences = workflowPreferences or {}
    plan = default_visual_content_plan()
    if existing:
        plan.update(existing)
    if workflowPreferences.get("visualContentMode"):
        plan["mode"] = workflowPreferences["visualContentMode"]
    if workflowPreferences.get("visualDensity"):
        plan["density"] = workflowPreferences["visualDensity"]
    if workflowPreferences.get("visualImpactLevel"):
        plan["impactLevel"] = workflowPreferences["visualImpactLevel"]

    n_obs = (dataProfile or {}).get("nObservations") or 0
    n_groups = (dataProfile or {}).get("nGroups") or 0
    if plan.get("density") == "high" and n_obs > 1000:
        plan["maxCalloutsSingle"] = min(plan.get("maxCalloutsSingle", 8), 6)
        plan["pointAnnotationMode"] = "summary_plus_extremes"
    elif n_groups and n_groups > 8:
        plan["maxCalloutsSingle"] = min(plan.get("maxCalloutsSingle", 8), 5)
        plan["pointAnnotationMode"] = "group_summary"
    else:
        plan.setdefault("pointAnnotationMode", "direct_when_legible")

    charts = [primaryChart] + list(secondaryCharts or [])
    plan["familyByChart"] = {chart: infer_chart_family(chart) for chart in charts if chart}
    planned_motifs = infer_reference_motifs(charts, dataProfile=dataProfile)
    template_motifs = infer_template_motifs(charts, dataProfile=dataProfile)
    existing_motifs = list(plan.get("visualGrammarMotifs", []))
    for motif in planned_motifs:
        if motif not in existing_motifs:
            existing_motifs.append(motif)
    plan["visualGrammarMotifs"] = existing_motifs
    existing_template_motifs = list(plan.get("templateMotifs", []))
    for motif in template_motifs:
        if motif not in existing_template_motifs:
            existing_template_motifs.append(motif)
    plan["templateMotifs"] = existing_template_motifs
    plan["templateMotifsRequired"] = bool(existing_template_motifs)
    plan["minTemplateMotifsPerFigure"] = min(2, len(existing_template_motifs)) if existing_template_motifs else 0
    if "joint_marginal_grid" in existing_template_motifs:
        plan["useMarginalAxes"] = True
    if "density_encoded_scatter" in existing_template_motifs:
        plan["useDensityColorEncoding"] = True
    if "dual_axis_error_sidecar" in existing_template_motifs:
        plan["requiresMultiAxisEncoding"] = True
    panel_count = max(1, len(charts))
    template_density_bonus = min(2, len(existing_template_motifs))
    plan["minTotalEnhancements"] = max(
        plan.get("minTotalEnhancements", 4),
        panel_count * plan.get("minEnhancementsPerPanel", 2) + template_density_bonus,
    )
    plan["minReferenceMotifsPerFigure"] = min(
        max(1, len(plan.get("visualGrammarMotifs", []))),
        max(2, min(3, panel_count + 1)),
    )
    if plan.get("requireInPlotExplanatoryLabels", True):
        plan["minInPlotLabelsPerFigure"] = max(
            plan.get("minInPlotLabelsPerFigure", 1),
            min(panel_count, plan.get("maxCalloutsSingle", 8)),
        )
    plan.setdefault("appliedEnhancements", [])
    plan.setdefault("familyByPanel", {})
    plan.setdefault("visualGrammarMotifsApplied", [])
    plan.setdefault("templateMotifsApplied", [])
    plan.setdefault("metricBoxCount", 0)
    plan.setdefault("metricTableCount", 0)
    plan.setdefault("insetCount", 0)
    plan.setdefault("referenceLineCount", 0)
    plan.setdefault("densityHaloCount", 0)
    plan.setdefault("sampleEncodingCount", 0)
    plan.setdefault("significanceStarLayerCount", 0)
    plan.setdefault("dualAxisEncodingCount", 0)
    plan.setdefault("referenceMotifCount", 0)
    plan.setdefault("templateMotifCount", 0)
    plan.setdefault("marginalAxesCount", 0)
    plan.setdefault("densityColorEncodingCount", 0)
    plan.setdefault("subAxesCount", 0)
    plan.setdefault("colorbarSlotCount", 0)
    plan.setdefault("multiAxisEncodingCount", 0)
    plan.setdefault("inPlotExplanatoryLabelCount", 0)
    return plan


def _ensure_visual_content_plan(chartPlan, dataProfile=None, workflowPreferences=None):
    existing = chartPlan.get("visualContentPlan", {})
    primary = chartPlan.get("primaryChart")
    secondary = chartPlan.get("secondaryCharts", [])
    visual = build_visual_content_plan(
        primary,
        secondary,
        dataProfile=dataProfile,
        workflowPreferences=workflowPreferences,
        existing=existing,
    )
    chartPlan["visualContentPlan"] = visual
    return visual


def _df_from_profile(dataProfile):
    if isinstance(dataProfile, dict):
        return dataProfile.get("df")
    return None


def _role(dataProfile, *names):
    roles = dataProfile.get("semanticRoles", {}) if isinstance(dataProfile, dict) else {}
    for name in names:
        if roles.get(name):
            return roles[name]
    return None


def _numeric_values(df, col):
    if df is None or col is None or col not in df:
        return np.array([])
    values = np.asarray(df[col].dropna(), dtype=float)
    return values[np.isfinite(values)]


def _display_col(col, col_map):
    return display_label(col, col_map) if col_map else str(col)


def _record_visual(plan, panel_id, family, enhancement):
    entry = f"{panel_id}:{family}:{enhancement}"
    if entry not in plan["appliedEnhancements"]:
        plan["appliedEnhancements"].append(entry)
    plan["familyByPanel"][panel_id] = family


def _visual_count(plan, key):
    plan[key] = int(plan.get(key, 0)) + 1


def _record_motif(plan, motif):
    applied = plan.setdefault("visualGrammarMotifsApplied", [])
    if motif not in applied:
        applied.append(motif)
        _visual_count(plan, "referenceMotifCount")


def _record_template_motif(plan, motif):
    applied = plan.setdefault("templateMotifsApplied", [])
    if motif not in applied:
        applied.append(motif)
        _visual_count(plan, "templateMotifCount")


def _template_motif_planned(plan, motif):
    return motif in plan.get("templateMotifs", [])


def _add_ml_model_triptych_marker(ax, dataProfile, visualPlan):
    if not _template_motif_planned(visualPlan, "ml_model_performance_triptych"):
        return []
    df = _df_from_profile(dataProfile)
    model_col = _role(dataProfile, "model", "algorithm")
    model_count = None
    if df is not None and model_col in getattr(df, "columns", []):
        try:
            model_count = int(df[model_col].dropna().astype(str).nunique())
        except Exception:
            model_count = None
    label = "ML model diagnostic\nRF template route"
    if model_count:
        label += f"\nmodels={model_count}"
    _add_inplot_label(ax, label, visualPlan, loc="upper_right")
    _record_template_motif(visualPlan, "ml_model_performance_triptych")
    return ["ml_model_performance_triptych"]


def _add_interval_template_summary(ax, dataProfile, visualPlan):
    df = _df_from_profile(dataProfile)
    if df is None:
        return None
    interval_specs = [
        ("ci_low", "ci_high", "forest_interval_board", "CI"),
        ("pi_low", "pi_high", "interval_uncertainty_band", "PI"),
    ]
    for low_role, high_role, motif, label in interval_specs:
        low_col = _role(dataProfile, low_role)
        high_col = _role(dataProfile, high_role)
        if low_col not in df or high_col not in df:
            continue
        low = _numeric_values(df, low_col)
        high = _numeric_values(df, high_col)
        if len(low) == 0 or len(high) == 0:
            continue
        count = min(len(low), len(high))
        width = float(np.nanmedian(high[:count] - low[:count])) if count else np.nan
        _add_inplot_label(ax, f"{label} intervals\nn={count}, width={width:.2g}", visualPlan, loc="lower_right")
        _record_template_motif(visualPlan, motif)
        return motif
    return None


def _density_color_values(x, y, bins=32):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 6:
        return np.array([])
    x_valid = x[mask]
    y_valid = y[mask]
    hist, x_edges, y_edges = np.histogram2d(x_valid, y_valid, bins=bins)
    x_idx = np.clip(np.searchsorted(x_edges, x_valid, side="right") - 1, 0, hist.shape[0] - 1)
    y_idx = np.clip(np.searchsorted(y_edges, y_valid, side="right") - 1, 0, hist.shape[1] - 1)
    density = hist[x_idx, y_idx].astype(float)
    if density.size and np.nanmax(density) > np.nanmin(density):
        density = (density - np.nanmin(density)) / (np.nanmax(density) - np.nanmin(density))
    return density


def _safe_kde_curve(values, grid):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    grid = np.asarray(grid, dtype=float)
    if len(values) < 4 or np.nanstd(values) <= 0:
        return None
    try:
        from scipy.stats import gaussian_kde
        density = gaussian_kde(values)(grid)
    except Exception:
        return None
    if not np.isfinite(density).any() or np.nanmax(density) <= 0:
        return None
    return density / np.nanmax(density)


def _style_template_marginal_axis(axis):
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_gid("scifig_marginal_axis")
    axis.patch.set_alpha(0.0)
    for spine in axis.spines.values():
        spine.set_linewidth(0.35)
        spine.set_edgecolor("#A8A8A8")


def _draw_template_marginal_distribution(axis, values, *, orientation, color, bins):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return
    axis.hist(
        values,
        bins=bins,
        density=True,
        orientation=orientation,
        color=color,
        alpha=0.26,
        edgecolor="white",
        linewidth=0.25,
        zorder=1,
    )
    grid = np.linspace(np.nanmin(values), np.nanmax(values), 160)
    density = _safe_kde_curve(values, grid)
    if density is None:
        return
    if orientation == "vertical":
        ymax = axis.get_ylim()[1] or 1.0
        axis.fill_between(grid, density * ymax * 0.82, color=color, alpha=0.28, linewidth=0, zorder=2)
        axis.plot(grid, density * ymax * 0.82, color=color, lw=0.65, zorder=3)
    else:
        xmax = axis.get_xlim()[1] or 1.0
        axis.fill_betweenx(grid, 0, density * xmax * 0.82, color=color, alpha=0.28, linewidth=0, zorder=2)
        axis.plot(density * xmax * 0.82, grid, color=color, lw=0.65, zorder=3)


def _overlay_density_colored_points(ax, x, y, visualPlan):
    if not visualPlan.get("useDensityColorEncoding", False):
        return None
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 12:
        return None
    x_valid = x[mask]
    y_valid = y[mask]
    density = _density_color_values(x_valid, y_valid, bins=min(40, max(12, int(np.sqrt(mask.sum())))))
    if density.size != len(x_valid):
        return None
    scatter = ax.scatter(
        x_valid,
        y_valid,
        c=density,
        cmap="viridis",
        s=18,
        edgecolors="white",
        linewidths=0.18,
        alpha=0.86,
        label="_nolegend_",
        zorder=6,
    )
    scatter.set_gid("scifig_density_color_points")
    _visual_count(visualPlan, "densityColorEncodingCount")
    _record_template_motif(visualPlan, "density_encoded_scatter")
    return scatter


def _add_marginal_distribution_axes(ax, x, y, visualPlan, color="#4C78A8"):
    if not visualPlan.get("useMarginalAxes", False):
        return None
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 12:
        return None
    x_valid = x[mask]
    y_valid = y[mask]
    fig = ax.figure
    fig.canvas.draw_idle()
    pos = ax.get_position()
    top_h = min(0.115, max(0.075, pos.height * 0.24))
    right_w = min(0.105, max(0.07, pos.width * 0.22))
    side_gap = 0.008
    top_gap = 0.085 if visualPlan.get("reserveMarginalTitleGap", True) else 0.008
    if pos.y1 + top_gap + top_h >= 0.985 or pos.x1 + side_gap + right_w >= 0.985:
        new_pos = [
            pos.x0,
            pos.y0,
            max(pos.width - right_w - side_gap, pos.width * 0.72),
            max(pos.height - top_h - top_gap, pos.height * 0.72),
        ]
        ax.set_position(new_pos)
        pos = ax.get_position()
    top = fig.add_axes([pos.x0, pos.y1 + top_gap, pos.width, top_h], sharex=ax)
    right = fig.add_axes([pos.x1 + side_gap, pos.y0, right_w, pos.height], sharey=ax)
    bins = min(22, max(8, int(np.sqrt(mask.sum()))))
    _draw_template_marginal_distribution(top, x_valid, orientation="vertical", color=color, bins=bins)
    _draw_template_marginal_distribution(right, y_valid, orientation="horizontal", color=color, bins=bins)
    for marginal in (top, right):
        _style_template_marginal_axis(marginal)
    # Each marginal panel produces TWO Axes (top + right), so count both
    # subAxesCount and marginalAxesCount twice per call. This matches the
    # QA contract in template-mining/07-techniques/marginal-joint.md
    # ("marginalAxesCount: 2") and is asserted by
    # tests/test_crowding_controls.py::test_prediction_scatter_adds_reference_grammar_motifs.
    _visual_count(visualPlan, "marginalAxesCount")
    _visual_count(visualPlan, "marginalAxesCount")
    _visual_count(visualPlan, "subAxesCount")
    _visual_count(visualPlan, "subAxesCount")
    visualPlan["outsideLayoutElements"] = True
    visualPlan["templateSidecarAxesReserved"] = True
    _record_template_motif(visualPlan, "joint_marginal_grid")
    return top, right


def apply_template_radar_signature(ax, angles, value_rows=None, colors=None, visualPlan=None, *, draw_grid=True):
    """Legacy radar polish: polygon grid plus glass markers.

    DEPRECATED MIGRATION TARGET: New radar code (gen_radar in
    generators-distribution.md, post-Phase C1) calls
    template_mining_helpers.add_polygon_polar_grid + apply_zorder_recipe('radar')
    directly. This shim remains for:
      1. Backward compatibility with legacy code paths still importing it
      2. visualPlan motif counter wiring (polar_comparison_signature, sample
         encoding count) which downstream gates depend on

    When add_polygon_polar_grid is reachable in globals (Phase A1 embedded
    template_mining_helpers), this shim delegates the grid replacement to that
    canonical implementation and only owns the glass-marker overlay + motif
    counter updates. Otherwise it falls back to the inline grid-drawing logic
    preserved below.

    draw_grid: pass False from gen_radar (which already drew the polygon grid
               via add_polygon_polar_grid) to avoid duplicate dashed grid lines.
               Default True keeps backward-compat for legacy callers.
    """
    angles = np.asarray(list(angles), dtype=float)
    if len(angles) < 3 or not hasattr(ax, "set_theta_offset"):
        return {"polygonGrid": False, "glassMarkers": 0}

    grid_drawn = False
    if draw_grid:
        # ─── Prefer template_mining_helpers when reachable (Phase A1) ─────────
        canonical_grid = globals().get("add_polygon_polar_grid")
        if canonical_grid is not None:
            try:
                closed_angles = np.r_[angles, angles[0]]
                r0, r1 = ax.get_ylim()
                if not np.isfinite(r0) or not np.isfinite(r1) or r1 <= r0:
                    r0, r1 = 0.0, 1.0
                    ax.set_ylim(r0, r1)
                # Use the canonical 4-level polygon grid (matches radar.md spec)
                canonical_grid(ax, closed_angles, levels=(0.25, 0.5, 0.75, 1.0))
                grid_drawn = True
            except Exception:
                grid_drawn = False

        if not grid_drawn:
            # Inline fallback (legacy path, used when template_mining_helpers not embedded)
            ax.grid(False)
            try:
                ax.spines["polar"].set_visible(False)
            except Exception:
                pass
            r0, r1 = ax.get_ylim()
            if not np.isfinite(r0) or not np.isfinite(r1) or r1 <= r0:
                r0, r1 = 0.0, 1.0
                ax.set_ylim(r0, r1)
            closed_angles = np.r_[angles, angles[0]]
            for frac in np.linspace(0.2, 1.0, 5):
                radius = r0 + (r1 - r0) * frac
                ax.plot(
                    closed_angles,
                    np.full_like(closed_angles, radius),
                    color="#C8CED6",
                    lw=0.45,
                    ls=(0, (2.0, 2.0)),
                    zorder=0,
                )
            for theta in angles:
                ax.plot([theta, theta], [r0, r1], color="#D5D9DF", lw=0.35, zorder=0)
            grid_drawn = True
    marker_count = 0
    if value_rows is not None:
        colors = list(colors or ["#1F4E79"] * len(value_rows))
        for row, color in zip(value_rows, colors):
            values = np.asarray(row, dtype=float)
            if values.size != angles.size:
                continue
            ax.scatter(angles, values, s=28, color=color, alpha=0.55, edgecolor="white", linewidth=0.55, zorder=8)
            ax.scatter(angles, values, s=9, color="white", alpha=0.75, edgecolor="none", zorder=9)
            marker_count += len(values)
    if visualPlan is not None:
        _record_template_motif(visualPlan, "polar_comparison_signature")
        if marker_count:
            _visual_count(visualPlan, "sampleEncodingCount")
    return {"polygonGrid": grid_drawn, "glassMarkers": marker_count}


def _pvalue_to_stars(p_value):
    try:
        p = float(p_value)
    except (TypeError, ValueError):
        return ""
    if not np.isfinite(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def apply_template_triangular_heatmap_signature(ax, row_labels=None, col_labels=None, pvalue_lookup=None, visualPlan=None):
    """Apply template/articles triangular heatmap polish and real p-value stars."""
    row_labels = list(row_labels or [])
    col_labels = list(col_labels or [])
    n_rows = len(row_labels)
    n_cols = len(col_labels)
    symmetric_labels = n_rows and n_cols and n_rows == n_cols and set(map(str, row_labels)) == set(map(str, col_labels))
    if symmetric_labels:
        ax.plot([0, n_cols], [0, n_rows], color="#F7F7F7", lw=1.0, zorder=8, solid_capstyle="butt")
        ax.plot([0, n_cols], [0, n_rows], color="#6F6F6F", lw=0.35, zorder=9, alpha=0.55)
    star_count = 0
    pvalue_lookup = pvalue_lookup or {}
    for i, row in enumerate(row_labels):
        for j, col in enumerate(col_labels):
            if symmetric_labels and j >= i:
                continue
            stars = _pvalue_to_stars(pvalue_lookup.get((row, col), pvalue_lookup.get((col, row))))
            if not stars:
                continue
            ax.text(
                j + 0.5,
                i + 0.5,
                stars,
                ha="center",
                va="center",
                fontsize=5.5,
                color="#111111",
                fontweight="bold",
                zorder=10,
            )
            star_count += 1
    ax.tick_params(axis="x", labelrotation=45, labelsize=5, pad=1)
    ax.tick_params(axis="y", labelsize=5, pad=1)
    if visualPlan is not None:
        _record_template_motif(visualPlan, "correlation_evidence_matrix")
        if star_count:
            _visual_count(visualPlan, "significanceStarLayerCount")
    return {"diagonalGuide": bool(symmetric_labels), "starCount": star_count}


def _resolve_numeric_column(dataProfile, df, *names):
    col = _role(dataProfile, *names)
    if df is not None and col in df:
        return col
    if df is None:
        return None
    tokens = [str(name).lower().replace("_", "") for name in names if name]
    for candidate in getattr(df, "columns", []):
        candidate_key = str(candidate).lower().replace("_", "").replace(" ", "")
        if any(token and token in candidate_key for token in tokens):
            return candidate
    return None


def _numeric_pair(df, x_col, y_col):
    if df is None or x_col is None or y_col is None or x_col not in df or y_col not in df:
        return np.array([]), np.array([])
    pair = df[[x_col, y_col]].dropna()
    try:
        x = np.asarray(pair[x_col], dtype=float)
        y = np.asarray(pair[y_col], dtype=float)
    except (TypeError, ValueError):
        return np.array([]), np.array([])
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]


def _is_prediction_pair(x_col, y_col):
    x_name = str(x_col or "").lower()
    y_name = str(y_col or "").lower()
    actual_tokens = ("actual", "observed", "measured", "experimental", "truth", "y_true")
    predicted_tokens = ("pred", "predict", "fitted", "estimate", "y_pred")
    return (
        any(token in x_name for token in actual_tokens)
        and any(token in y_name for token in predicted_tokens)
    )


def _add_inplot_label(ax, text, visualPlan, xy=None, loc="upper_left", color="#222222"):
    clean = str(text).strip()
    if not clean:
        return None
    anchors = {
        "upper_left": (0.04, 0.94, "left", "top"),
        "upper_right": (0.96, 0.94, "right", "top"),
        "lower_left": (0.04, 0.08, "left", "bottom"),
        "lower_right": (0.96, 0.08, "right", "bottom"),
        "center_right": (0.96, 0.52, "right", "center"),
    }
    if xy is None:
        x, y, ha, va = anchors.get(loc, anchors["upper_left"])
        artist = ax.text(
            x, y, clean,
            transform=ax.transAxes,
            ha=ha,
            va=va,
            fontsize=4.8,
            color=color,
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "#D0D0D0",
                "linewidth": 0.3,
                "alpha": 0.82,
            },
            zorder=9,
        )
    else:
        artist = ax.annotate(
            clean,
            xy=xy,
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=4.8,
            color=color,
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "white",
                "edgecolor": "#D0D0D0",
                "linewidth": 0.3,
                "alpha": 0.84,
            },
            arrowprops={"arrowstyle": "-", "lw": 0.28, "color": "#555555"},
            zorder=9,
        )
    artist.set_gid("scifig_inplot_label")
    _visual_count(visualPlan, "inPlotExplanatoryLabelCount")
    return artist


def _has_inplot_label(ax):
    for text in ax.texts:
        gid = getattr(text, "get_gid", lambda: None)()
        if gid == "scifig_inplot_label":
            return True
    return False


def _ensure_panel_explanatory_label(ax, visualPlan, family):
    if not visualPlan.get("requireInPlotExplanatoryLabels", True) or _has_inplot_label(ax):
        return None
    labels = {
        "distribution": "median and spread encoded",
        "scatter_embedding": "trend context",
        "matrix_heatmap": "value pattern",
        "time_series": "trajectory summary",
        "clinical_diagnostic": "diagnostic summary",
        "genomics_enrichment": "threshold context",
        "engineering_spectra": "performance window",
        "composition_flow": "composition summary",
        "psych_ecology": "response pattern",
        "generic": "data-derived summary",
    }
    return _add_inplot_label(ax, labels.get(family, "data-derived summary"), visualPlan, loc="lower_left")


def _add_metric_box(ax, lines, visualPlan):
    clean = [str(line) for line in lines if line is not None and str(line).strip()]
    if not clean:
        return None
    text = "\n".join(clean[:visualPlan.get("maxInlineStats", 4)])
    artist = ax.text(
        1.015, 1.0, text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=5,
        color="#222222",
        clip_on=False,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#B8B8B8",
            "linewidth": 0.35,
            "alpha": 0.94,
        },
    )
    artist.set_gid("scifig_metric_box")
    _visual_count(visualPlan, "metricBoxCount")
    visualPlan["outsideLayoutElements"] = True
    return artist


def _metric_table_data_patch_bboxes(ax, renderer):
    data_patches = []
    for patch in getattr(ax, "patches", []):
        if not getattr(patch, "get_visible", lambda: True)():
            continue
        if getattr(patch, "get_gid", lambda: None)() in {"scifig_density_halo", "scifig_table_cell"}:
            continue
        if patch is getattr(ax, "patch", None):
            continue
        if patch.__class__.__name__ != "Rectangle":
            continue
        try:
            if abs(float(patch.get_width())) <= 0 or abs(float(patch.get_height())) <= 0:
                continue
            patch_box = patch.get_window_extent(renderer=renderer)
        except Exception:
            continue
        if _bbox_area(patch_box) <= 9:
            continue
        data_patches.append(patch_box)
    return data_patches


def _metric_table_overlaps_data_marks(ax, table):
    fig = getattr(ax, "figure", None)
    if fig is None:
        return False
    try:
        fig.canvas.draw()
        renderer = get_cached_renderer(fig, force=True)
    except Exception:
        try:
            renderer = fig.canvas.get_renderer()
        except Exception:
            return False
    try:
        table_box = table.get_window_extent(renderer=renderer)
    except Exception:
        return False
    return any(table_box.overlaps(patch_box) for patch_box in _metric_table_data_patch_bboxes(ax, renderer))


def _add_metric_table_fallback_box(ax, clean_rows, visualPlan):
    if not visualPlan.get("useMetricTableFallbackBox", True):
        return None
    lines = [f"{label}: {value}" for label, value in clean_rows[:visualPlan.get("maxInlineStats", 4)]]
    artist = _add_metric_box(ax, lines, visualPlan)
    if artist is None:
        return None
    _visual_count(visualPlan, "metricTableFallbackBoxCount")
    visualPlan.setdefault("metricTableFallbackEvents", []).append({
        "reason": "all_table_locations_overlap_data",
        "rows": len(lines),
    })
    _record_motif(visualPlan, "prediction_metric_table_fallback_box")
    return artist


def _add_metric_table(ax, rows, visualPlan, loc="lower_right"):
    if not visualPlan.get("useMetricTables", True):
        return None
    clean = [(str(label), str(value)) for label, value in rows if str(label).strip() and str(value).strip()]
    if not clean:
        return None
    boxes = {
        "lower_right": [0.58, 0.05, 0.38, 0.20],
        "lower_left": [0.04, 0.05, 0.38, 0.20],
        "upper_right": [0.58, 0.74, 0.38, 0.20],
        "upper_left": [0.04, 0.74, 0.38, 0.20],
        "mid_right": [0.68, 0.39, 0.29, 0.22],
        "upper_center": [0.31, 0.74, 0.38, 0.20],
        "lower_center": [0.31, 0.05, 0.38, 0.20],
        "sidecar_right": [0.70, 0.06, 0.27, 0.22],
    }
    requested = loc if loc in boxes else "lower_right"
    fallback_locations = ["upper_right", "lower_right", "upper_left", "lower_left", "upper_center", "lower_center"]
    if requested == "sidecar_right":
        fallback_locations = ["sidecar_right", "mid_right"] + fallback_locations
    location_priority = visualPlan.get("metricTableLocationPriority") or [requested] + fallback_locations
    location_priority = [name for i, name in enumerate(location_priority) if name in boxes and name not in location_priority[:i]]

    def _make_table(location):
        table = ax.table(
            cellText=[[label, value] for label, value in clean[:4]],
            cellLoc="center",
            bbox=boxes.get(location, boxes["lower_right"]),
        )
        table.auto_set_font_size(False)
        table.set_fontsize(4.6)
        table.set_zorder(10)
        table.set_gid("scifig_metric_table")
        for (row, col), cell in table.get_celld().items():
            cell.set_linewidth(0.25)
            cell.set_edgecolor("#B8B8B8")
            cell.set_facecolor("#FFFFFF" if row % 2 else "#F7F7F7")
            if col == 0:
                cell.get_text().set_fontweight("bold")
        return table

    selected_table = None
    selected_location = requested
    attempts = []
    for location in location_priority:
        table = _make_table(location)
        overlaps_data = _metric_table_overlaps_data_marks(ax, table)
        attempts.append({"location": location, "overlapsData": bool(overlaps_data)})
        if not overlaps_data:
            selected_table = table
            selected_location = location
            break
        try:
            table.remove()
        except Exception:
            pass
    visualPlan.setdefault("metricTablePlacementAttempts", []).append(attempts)
    if selected_table is None:
        _visual_count(visualPlan, "metricTableSuppressedCount")
        return _add_metric_table_fallback_box(ax, clean, visualPlan)
    if selected_location != requested:
        _visual_count(visualPlan, "metricTableRelocatedCount")
        visualPlan.setdefault("metricTableRelocationEvents", []).append({
            "from": requested,
            "to": selected_location,
            "reason": "avoid_data_bar_overlap",
        })
    _visual_count(visualPlan, "metricTableCount")
    _record_motif(visualPlan, "prediction_metric_table")
    _record_template_motif(visualPlan, "metric_table_in_panel")
    return selected_table


def _r2_from_actual_pred(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if len(actual) < 2:
        return None
    ss_res = float(np.nansum((predicted - actual) ** 2))
    ss_tot = float(np.nansum((actual - np.nanmean(actual)) ** 2))
    if ss_tot <= 0:
        return None
    return 1.0 - ss_res / ss_tot


def _add_perfect_fit_line(ax, x, y, visualPlan):
    if not visualPlan.get("usePerfectFitReference", True):
        return None
    if len(x) < 2 or len(y) < 2:
        return None
    lo = float(np.nanmin([np.nanmin(x), np.nanmin(y)]))
    hi = float(np.nanmax([np.nanmax(x), np.nanmax(y)]))
    if not np.isfinite(lo) or not np.isfinite(hi) or lo == hi:
        return None
    ax.plot([lo, hi], [lo, hi], color="#222222", lw=0.7, ls="--",
            label="_nolegend_", zorder=4)
    _visual_count(visualPlan, "referenceLineCount")
    _record_motif(visualPlan, "perfect_fit_reference")
    return True


def _add_density_halos(ax, x, y, visualPlan, color="#4C78A8"):
    if not visualPlan.get("useDensityHalos", True):
        return None
    if len(x) < 6 or len(y) < 6:
        return None
    values = np.column_stack([np.asarray(x, dtype=float), np.asarray(y, dtype=float)])
    values = values[np.isfinite(values).all(axis=1)]
    if len(values) < 6:
        return None
    cov = np.cov(values, rowvar=False)
    if cov.shape != (2, 2) or not np.isfinite(cov).all():
        return None
    vals, vecs = np.linalg.eigh(cov)
    vals = np.clip(vals, 1e-12, None)
    order = vals.argsort()[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    angle = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
    center = values.mean(axis=0)
    for scale, alpha in ((2.4, 0.08), (1.5, 0.12)):
        ellipse = Ellipse(
            xy=center,
            width=2 * scale * np.sqrt(vals[0]),
            height=2 * scale * np.sqrt(vals[1]),
            angle=angle,
            facecolor=color,
            edgecolor="none",
            alpha=alpha,
            zorder=1,
        )
        ellipse.set_gid("scifig_density_halo")
        ax.add_patch(ellipse)
    _visual_count(visualPlan, "densityHaloCount")
    _record_motif(visualPlan, "density_halo")
    return True


def _add_sample_shape_encoding(ax, df, x_col, y_col, visualPlan, dataProfile=None):
    if not visualPlan.get("useSampleShapeEncoding", True):
        return None
    sample_col = None
    if df is None:
        return None
    roles = ("sample", "source", "reference", "ref", "cohort", "batch")
    sample_col = _role(dataProfile or {}, *roles)
    for candidate in getattr(df, "columns", []):
        if sample_col is not None and sample_col in df:
            break
        key = str(candidate).lower().replace("_", "").replace(" ", "")
        if any(token in key for token in roles):
            sample_col = candidate
            break
    if sample_col is None or sample_col not in df or x_col not in df or y_col not in df:
        return None
    groups = list(df[sample_col].dropna().unique())
    if len(groups) < 2 or len(groups) > 8:
        return None
    markers = ["o", "s", "^", "v", "D", "P", "X", "<"]
    for idx, group in enumerate(groups[:8]):
        subset = df[df[sample_col] == group]
        x, y = _numeric_pair(subset, x_col, y_col)
        if len(x) == 0:
            continue
        ax.scatter(
            x,
            y,
            marker=markers[idx % len(markers)],
            s=22,
            facecolors="none",
            edgecolors="#2B2B2B",
            linewidths=0.45,
            alpha=0.75,
            label="_nolegend_",
            zorder=6,
        )
    _visual_count(visualPlan, "sampleEncodingCount")
    _record_motif(visualPlan, "sample_shape_encoding")
    return True


def _add_dual_axis_error_bars(ax, df, x_col, visualPlan):
    if not visualPlan.get("useDualAxisErrorBars", True) or df is None:
        return None
    error_col = None
    error_tokens = ("percenterror", "percentageerror", "errorpct", "rmse")
    for candidate in getattr(df, "columns", []):
        key = str(candidate).lower().replace("_", "").replace(" ", "")
        if any(token in key for token in error_tokens):
            error_col = candidate
            break
    if error_col is None or error_col not in df:
        return None
    try:
        errors = np.asarray(df[error_col], dtype=float)
    except (TypeError, ValueError):
        return None
    mask = np.isfinite(errors)
    if not mask.any():
        return None
    if x_col is not None and x_col in df:
        try:
            xpos = np.asarray(df[x_col], dtype=float)
        except (TypeError, ValueError):
            xpos = np.arange(len(errors), dtype=float)
    else:
        xpos = np.arange(len(errors), dtype=float)
    xpos = xpos[mask]
    errors = errors[mask]
    if len(errors) == 0:
        return None
    ax2 = ax.twinx()
    width = 0.65
    if len(xpos) > 1:
        diffs = np.diff(np.sort(np.unique(xpos)))
        if len(diffs):
            width = max(float(np.nanmedian(diffs)) * 0.55, 0.08)
    ax2.bar(
        xpos,
        errors,
        width=width,
        facecolor="none",
        edgecolor="#8F91FF",
        linewidth=0.55,
        hatch="////",
        alpha=0.55,
        label="_nolegend_",
        zorder=0,
    )
    ax2.set_ylabel(str(error_col)[:22], fontsize=5, color="#7376D6")
    ax2.tick_params(axis="y", colors="#7376D6", labelsize=5, width=0.5, length=2)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_linewidth(0.5)
    ax2.set_gid("scifig_dual_axis_error")
    _visual_count(visualPlan, "dualAxisEncodingCount")
    _visual_count(visualPlan, "multiAxisEncodingCount")
    _record_motif(visualPlan, "dual_axis_error_bars")
    _record_template_motif(visualPlan, "dual_axis_error_sidecar")
    return True


def _add_summary_inset(ax, values, visualPlan, color="#4C78A8"):
    if not visualPlan.get("useInsetAxes", True):
        return None
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 5:
        return None
    inset = ax.inset_axes([1.015, 0.06, 0.28, 0.24], transform=ax.transAxes)
    inset.hist(values, bins=min(12, max(5, int(np.sqrt(len(values))))),
               color=color, alpha=0.82, edgecolor="white", linewidth=0.25)
    inset.axvline(np.nanmedian(values), color="black", lw=0.6)
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_linewidth(0.35)
        spine.set_edgecolor("#777777")
    inset.set_title("dist.", fontsize=4, pad=1)
    inset.set_gid("scifig_inset")
    _visual_count(visualPlan, "insetCount")
    visualPlan["outsideLayoutElements"] = True
    return inset


def _maybe_reference_zero(ax, visualPlan=None):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    drawn = False
    if x0 < 0 < x1:
        ax.axvline(0, color="#A0A0A0", lw=0.45, ls="--", zorder=0)
        drawn = True
    if y0 < 0 < y1:
        ax.axhline(0, color="#A0A0A0", lw=0.45, ls="--", zorder=0)
        drawn = True
    if visualPlan is not None and drawn:
        _visual_count(visualPlan, "referenceLineCount")
        _record_motif(visualPlan, "trend_or_fit_reference")


def _enhance_distribution(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    group_col = _role(dataProfile, "group", "condition")
    value_col = _role(dataProfile, "value", "y")
    values = _numeric_values(df, value_col)
    ml_enhancements = _add_ml_model_triptych_marker(ax, dataProfile, visualPlan)
    if len(values) == 0:
        return ml_enhancements

    enhancements = ["distribution_summary"] + ml_enhancements
    groups = []
    if group_col and df is not None and group_col in df:
        groups = list(df[group_col].dropna().unique())
    if groups:
        group_summaries = []
        for i, group in enumerate(groups[:8]):
            subset = _numeric_values(df[df[group_col] == group], value_col)
            if len(subset) == 0:
                continue
            median = float(np.nanmedian(subset))
            q1, q3 = np.nanpercentile(subset, [25, 75])
            mean = float(np.nanmean(subset))
            group_summaries.append((i, str(group), median, mean, len(subset)))
            ax.vlines(i, q1, q3, color="black", lw=1.0, zorder=7)
            ax.scatter([i], [mean], marker="D", s=18, facecolor="white",
                       edgecolor="black", linewidth=0.45, zorder=8)
            ax.text(i, -0.12, f"n={len(subset)}", transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=5, clip_on=False, color="#333333")
        _record_motif(visualPlan, "sample_size_labels")
        if group_summaries:
            best = max(group_summaries, key=lambda item: item[2])
            baseline = group_summaries[0]
            delta = best[2] - baseline[2]
            _add_inplot_label(
                ax,
                f"best: {best[1][:14]}\nmedian {best[2]:.3g}\ndelta={delta:+.2g}",
                visualPlan,
                xy=(best[0], best[2]),
                color="#111111",
            )
            enhancements.append("best_group_callout")
        if len(groups) == 2:
            a = _numeric_values(df[df[group_col] == groups[0]], value_col)
            b = _numeric_values(df[df[group_col] == groups[1]], value_col)
            pooled = np.sqrt((np.nanvar(a) + np.nanvar(b)) / 2) if len(a) and len(b) else 0
            if pooled > 0:
                effect = (np.nanmean(b) - np.nanmean(a)) / pooled
                _add_metric_box(ax, [f"n={len(values)}", f"median={np.nanmedian(values):.3g}", f"d={effect:.2f}"], visualPlan)
            else:
                _add_metric_box(ax, [f"n={len(values)}", f"median={np.nanmedian(values):.3g}"], visualPlan)
        else:
            _add_metric_box(ax, [f"groups={len(groups)}", f"n={len(values)}", f"median={np.nanmedian(values):.3g}"], visualPlan)
    else:
        ax.axvline(np.nanmedian(values), color="black", lw=0.7, ls="--")
        _add_inplot_label(ax, f"median={np.nanmedian(values):.3g}", visualPlan, loc="upper_left")
        _add_metric_box(ax, [f"n={len(values)}", f"median={np.nanmedian(values):.3g}", f"IQR={np.nanpercentile(values, 75) - np.nanpercentile(values, 25):.3g}"], visualPlan)
        _record_motif(visualPlan, "sample_size_labels")
    _record_motif(visualPlan, "median_iqr_summary")
    _add_summary_inset(ax, values, visualPlan, color=palette.get("categorical", ["#4C78A8"])[0])
    return enhancements


def _enhance_scatter(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    actual_col = _resolve_numeric_column(dataProfile, df, "actual", "observed", "measured", "experimental", "truth", "y_true")
    predicted_col = _resolve_numeric_column(dataProfile, df, "predicted", "prediction", "pred", "fitted", "estimated", "estimate", "y_pred")
    is_prediction = actual_col is not None and predicted_col is not None
    if is_prediction:
        x_col, y_col = actual_col, predicted_col
    else:
        x_col = _resolve_numeric_column(dataProfile, df, "x", "time", "score", "actual", "observed")
        y_col = _resolve_numeric_column(dataProfile, df, "y", "value", "predicted", "prediction", "response")
        is_prediction = _is_prediction_pair(x_col, y_col)
    x, y = _numeric_pair(df, x_col, y_col)
    if len(x) == 0 or len(y) == 0 or len(x) != len(y):
        _maybe_reference_zero(ax, visualPlan)
        _add_metric_box(ax, ["exploratory view"], visualPlan)
        return ["reference_context"]

    _maybe_reference_zero(ax, visualPlan)
    enhancements = ["scatter_context"]
    halo_color = palette.get("categorical", ["#4C78A8"])[0]

    if is_prediction:
        _add_perfect_fit_line(ax, x, y, visualPlan)
        _add_density_halos(ax, x, y, visualPlan, color=halo_color)
        density_encoded = _overlay_density_colored_points(ax, x, y, visualPlan)
        marginal_axes = _add_marginal_distribution_axes(ax, x, y, visualPlan, color=halo_color)
        sample_encoded = _add_sample_shape_encoding(ax, df, x_col, y_col, visualPlan, dataProfile=dataProfile)
        error_sidecar = _add_dual_axis_error_bars(ax, df, x_col, visualPlan)
        rmse = float(np.sqrt(np.nanmean((y - x) ** 2)))
        mae = float(np.nanmean(np.abs(y - x)))
        r2 = _r2_from_actual_pred(x, y)
        r2_text = f"{r2:.2f}" if r2 is not None else "n/a"
        _add_metric_table(
            ax,
            [("R2", r2_text), ("RMSE", f"{rmse:.3g}"), ("MAE", f"{mae:.3g}"), ("n", str(len(x)))],
            visualPlan,
        )
        _add_inplot_label(ax, f"perfect-fit diagnostic\nR2={r2_text}", visualPlan, loc="upper_left")
        _add_metric_box(ax, [f"n={len(x)}", f"RMSE={rmse:.3g}", f"MAE={mae:.3g}"], visualPlan)
        enhancements = ["perfect_fit_reference", "prediction_metric_table", "density_halo", "inplot_prediction_label"]
        _record_template_motif(visualPlan, "prediction_diagnostic_matrix")
        if _template_motif_planned(visualPlan, "ml_model_performance_triptych"):
            _record_template_motif(visualPlan, "ml_model_performance_triptych")
            enhancements.append("ml_model_performance_triptych")
        if density_encoded is not None:
            enhancements.append("density_encoded_scatter")
        if marginal_axes is not None:
            enhancements.append("joint_marginal_grid")
        if error_sidecar:
            enhancements.append("dual_axis_error_sidecar")
        if sample_encoded:
            enhancements.append("sample_shape_encoding")
        return enhancements

    _add_density_halos(ax, x, y, visualPlan, color=halo_color)
    density_encoded = _overlay_density_colored_points(ax, x, y, visualPlan)
    if density_encoded is not None:
        enhancements.append("density_encoded_scatter")
    if len(x) >= 3 and np.nanstd(x) > 0 and np.nanstd(y) > 0:
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(np.nanmin(x), np.nanmax(x), 100)
        ax.plot(xs, slope * xs + intercept, color="black", lw=0.75,
                alpha=0.65, label="_nolegend_", zorder=5)
        _visual_count(visualPlan, "referenceLineCount")
        _record_motif(visualPlan, "trend_or_fit_reference")
        r = np.corrcoef(x, y)[0, 1]
        direction = "positive" if slope >= 0 else "negative"
        _add_inplot_label(ax, f"{direction} trend\nr={r:.2f}", visualPlan, loc="upper_left")
        _add_metric_box(ax, [f"n={len(x)}", f"r={r:.2f}", f"slope={slope:.2g}"], visualPlan)
        enhancements.extend(["trend_summary", "inplot_trend_label", "density_halo"])
    label_col = _role(dataProfile, "feature_id", "label", "gene")
    if label_col and df is not None and label_col in df and len(y) > 0:
        budget = min(visualPlan.get("maxCalloutsSingle", 8), 5, len(y))
        top_idx = np.argsort(np.abs(y - np.nanmedian(y)))[-budget:]
        for idx in top_idx:
            label = str(df.iloc[idx][label_col])[:18]
            ax.annotate(label, (x[idx], y[idx]), xytext=(4, 4),
                        textcoords="offset points", fontsize=4.5,
                        arrowprops={"arrowstyle": "-", "lw": 0.25, "color": "#555555"})
        enhancements.append("top_point_callouts")
    return enhancements


def _add_matrix_significance_stars(ax, numeric, dataProfile, visualPlan):
    if not visualPlan.get("useSignificanceStarLayer", True):
        return None
    roles = dataProfile.get("semanticRoles", {}) if isinstance(dataProfile, dict) else {}
    role_text = " ".join(str(v).lower() for v in roles.values())
    col_text = " ".join(str(col).lower() for col in getattr(numeric, "columns", []))
    if not any(token in f"{role_text} {col_text}" for token in ("pvalue", "p_value", "padj", "fdr", "qvalue")):
        return None
    vals = numeric.to_numpy(dtype=float)
    if vals.shape[0] > 12 or vals.shape[1] > 12:
        return None
    star_count = 0
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            value = vals[i, j]
            if not np.isfinite(value) or value > 0.05:
                continue
            stars = "***" if value <= 0.001 else "**" if value <= 0.01 else "*"
            ax.text(j + 0.5, i + 0.25, stars, ha="center", va="center",
                    fontsize=4.2, color="#111111", fontweight="bold")
            star_count += 1
    if star_count:
        _visual_count(visualPlan, "significanceStarLayerCount")
        _record_motif(visualPlan, "significance_star_layer")
        _record_template_motif(visualPlan, "correlation_evidence_matrix")
        return True
    return None


def _enhance_matrix(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    template_enhancements = []
    if _template_motif_planned(visualPlan, "classification_error_matrix"):
        _add_inplot_label(ax, "classification error\nrow-normalized", visualPlan, loc="upper_right")
        _record_template_motif(visualPlan, "classification_error_matrix")
        template_enhancements.append("classification_error_matrix")
    numeric = None
    if df is not None:
        try:
            numeric = df.select_dtypes(include="number")
        except AttributeError:
            numeric = None
    if numeric is not None and numeric.size:
        vals = numeric.to_numpy(dtype=float)
        _add_metric_box(ax, [f"matrix={vals.shape[0]}x{vals.shape[1]}", f"range={np.nanmin(vals):.2g}..{np.nanmax(vals):.2g}"], visualPlan)
        _record_motif(visualPlan, "diverging_colorbar")
        if vals.shape[0] <= 6 and vals.shape[1] <= 6:
            for i in range(vals.shape[0]):
                for j in range(vals.shape[1]):
                    ax.text(j + 0.5, i + 0.5, f"{vals[i, j]:.2g}",
                            ha="center", va="center", fontsize=4.5, color="#111111")
            _record_motif(visualPlan, "cell_value_labels")
            _add_matrix_significance_stars(ax, numeric, dataProfile, visualPlan)
            return template_enhancements + ["matrix_summary", "cell_value_labels"]
        _add_matrix_significance_stars(ax, numeric, dataProfile, visualPlan)
        return template_enhancements + ["matrix_summary"]
    _add_metric_box(ax, ["matrix view"], visualPlan)
    return template_enhancements + ["matrix_summary"]


def _enhance_time_series(ax, dataProfile, visualPlan, palette, col_map):
    enhancements = []
    df = _df_from_profile(dataProfile)
    x_col = _resolve_numeric_column(dataProfile, df, "x", "time", "index", "point")
    if _template_motif_planned(visualPlan, "neural_training_dynamics"):
        _add_inplot_label(ax, "training dynamics\nbest epoch marked", visualPlan, loc="upper_left")
        _record_template_motif(visualPlan, "neural_training_dynamics")
        enhancements.append("neural_training_dynamics")
    if _add_dual_axis_error_bars(ax, df, x_col, visualPlan):
        enhancements.append("dual_axis_error_bars")
    for line in ax.lines[:visualPlan.get("maxInlineStats", 4)]:
        x = np.asarray(line.get_xdata(), dtype=float)
        y = np.asarray(line.get_ydata(), dtype=float)
        if len(x) < 2 or len(y) < 2:
            continue
        label = line.get_label()
        if not label or label.startswith("_"):
            label = "series"
        ax.text(x[-1], y[-1], str(label)[:16], fontsize=5, ha="left",
                va="center", color=line.get_color(), clip_on=False)
        peak_idx = int(np.nanargmax(y))
        ax.scatter([x[peak_idx]], [y[peak_idx]], s=14, facecolor="white",
                   edgecolor=line.get_color(), linewidth=0.6, zorder=7)
        enhancements.append("endpoint_and_peak_labels")
        _record_motif(visualPlan, "endpoint_peak_labels")
    if ax.lines:
        main_line = ax.lines[0]
        x0 = np.asarray(main_line.get_xdata(), dtype=float)
        y0 = np.asarray(main_line.get_ydata(), dtype=float)
        if len(x0) >= 2 and len(y0) >= 2:
            change = y0[-1] - y0[0]
            _add_inplot_label(ax, f"endpoint delta={change:+.2g}", visualPlan, loc="upper_right")
            enhancements.append("endpoint_delta_label")
            _record_motif(visualPlan, "trajectory_delta_label")
        _add_metric_box(ax, [f"series={len(ax.lines)}", "endpoints labeled"], visualPlan)
    return enhancements or ["time_context"]


def _auc_from_scores(labels, scores):
    labels = np.asarray(labels, dtype=float)
    scores = np.asarray(scores, dtype=float)
    mask = np.isfinite(labels) & np.isfinite(scores)
    labels = labels[mask]
    scores = scores[mask]
    pos = labels == 1
    neg = labels == 0
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(scores)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    return (ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def _enhance_clinical(ax, dataProfile, visualPlan, palette, col_map, chart_type):
    if chart_type in ("rf_classifier_report_board", "classifier_validation_board"):
        if chart_type == "rf_classifier_report_board":
            _record_template_motif(visualPlan, "rf_classifier_report_board")
            _record_template_motif(visualPlan, "explainability_importance_stack")
        _record_template_motif(visualPlan, "classifier_validation_board")
        _record_template_motif(visualPlan, "classification_error_matrix")
        return [f"{chart_type}_native"]
    df = _df_from_profile(dataProfile)
    score_col = _role(dataProfile, "score", "x")
    label_col = _role(dataProfile, "label", "event")
    scores = _numeric_values(df, score_col)
    labels = _numeric_values(df, label_col)
    lines = []
    if chart_type in ("roc", "pr_curve", "calibration") and ax.get_xlim()[0] <= 0 <= ax.get_xlim()[1]:
        ax.plot([0, 1], [0, 1], color="#999999", lw=0.55, ls="--", label="_nolegend_")
        _visual_count(visualPlan, "referenceLineCount")
        _record_motif(visualPlan, "diagnostic_reference_line")
    if len(scores) == len(labels) and len(scores):
        auc = _auc_from_scores(labels, scores)
        if auc is not None:
            lines.append(f"AUC={auc:.2f}")
        lines.append(f"n={len(scores)}")
    elif df is not None:
        try:
            lines.append(f"n={len(df)}")
        except TypeError:
            pass
    if lines:
        _add_inplot_label(ax, "\n".join(lines[:2]), visualPlan, loc="upper_left")
    _add_metric_box(ax, lines or ["clinical summary"], visualPlan)
    _record_motif(visualPlan, "diagnostic_metric_box")
    enhancements = ["clinical_metric_summary", "inplot_clinical_label"]
    interval_motif = _add_interval_template_summary(ax, dataProfile, visualPlan)
    if interval_motif:
        enhancements.append(interval_motif)
    return enhancements


def _enhance_genomics(ax, dataProfile, visualPlan, palette, col_map, chart_type):
    df = _df_from_profile(dataProfile)
    fc_col = _role(dataProfile, "log2fc", "effect", "x")
    p_col = _role(dataProfile, "nlogp", "padj", "pvalue", "y")
    label_col = _role(dataProfile, "gene", "feature_id", "label")
    x = _numeric_values(df, fc_col)
    y_raw = _numeric_values(df, p_col)
    if len(x) == 0 or len(y_raw) == 0 or len(x) != len(y_raw):
        _add_metric_box(ax, ["genomics context"], visualPlan)
        return ["genomics_context"]
    y = y_raw
    p_name = str(p_col).lower() if p_col else ""
    if "padj" in p_name or "pvalue" in p_name:
        y = -np.log10(np.clip(y_raw, 1e-300, 1.0))
    ax.axvline(-1, color="#888888", lw=0.5, ls="--")
    ax.axvline(1, color="#888888", lw=0.5, ls="--")
    ax.axhline(1.3, color="#888888", lw=0.5, ls="--")
    _visual_count(visualPlan, "referenceLineCount")
    _record_motif(visualPlan, "threshold_reference_lines")
    hits = int(np.sum((np.abs(x) >= 1) & (y >= 1.3)))
    _add_inplot_label(ax, f"hits={hits}\nthresholded", visualPlan, loc="upper_right")
    if label_col and df is not None and label_col in df:
        budget = min(visualPlan.get("maxCalloutsSingle", 8), 6, len(y))
        for idx in np.argsort(y)[-budget:]:
            ax.annotate(str(df.iloc[idx][label_col])[:18], (x[idx], y[idx]),
                        xytext=(3, 3), textcoords="offset points", fontsize=4.5,
                        arrowprops={"arrowstyle": "-", "lw": 0.25, "color": "#555555"})
        _record_motif(visualPlan, "top_feature_callouts")
    _add_metric_box(ax, [f"features={len(x)}", f"hits={hits}", "|log2FC|>=1", "FDR/p>=line"], visualPlan)
    return ["threshold_lines", "top_feature_callouts", "hit_summary", "inplot_hit_label"]


def _enhance_engineering(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    x_col = _role(dataProfile, "x", "dose", "time")
    y_col = _role(dataProfile, "y", "response", "value")
    x = _numeric_values(df, x_col)
    y = _numeric_values(df, y_col)
    if len(x) and len(y) and len(x) == len(y):
        peak_idx = int(np.nanargmax(y))
        ax.scatter([x[peak_idx]], [y[peak_idx]], s=20, facecolor="white",
                   edgecolor="black", linewidth=0.6, zorder=8)
        ax.annotate(f"peak {y[peak_idx]:.2g}", (x[peak_idx], y[peak_idx]),
                    xytext=(5, 5), textcoords="offset points", fontsize=4.8,
                    arrowprops={"arrowstyle": "-", "lw": 0.3, "color": "#555555"})
        _add_inplot_label(ax, f"peak window\n{x[peak_idx]:.3g}, {y[peak_idx]:.3g}", visualPlan, loc="upper_left")
        _add_metric_box(ax, [f"n={len(y)}", f"peak={y[peak_idx]:.3g}", f"range={np.nanmin(y):.2g}..{np.nanmax(y):.2g}"], visualPlan)
        _record_motif(visualPlan, "peak_window_callout")
        _record_motif(visualPlan, "range_summary_box")
        return ["peak_annotation", "range_summary", "inplot_peak_label"]
    _add_metric_box(ax, ["engineering summary"], visualPlan)
    return ["engineering_context"]


def _enhance_composition(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    group_col = _role(dataProfile, "group", "feature_id", "label")
    value_col = _role(dataProfile, "value", "y")
    values = _numeric_values(df, value_col)
    lines = []
    enhancements = ["composition_summary", "inplot_composition_label"]
    if len(values):
        total = float(np.nansum(values))
        lines.extend([f"total={total:.3g}", f"items={len(values)}"])
    if group_col and df is not None and group_col in df:
        lines.append(f"categories={df[group_col].nunique()}")
    if _template_motif_planned(visualPlan, "neural_architecture_topology"):
        source_col = _role(dataProfile, "source", "from")
        target_col = _role(dataProfile, "target", "to")
        node_col = _role(dataProfile, "layer", "module", "node", "component", "block", "label")
        params_col = _role(dataProfile, "params", "parameters")
        module_count = None
        edge_count = None
        params_total = None
        if df is not None:
            if source_col in getattr(df, "columns", []) and target_col in getattr(df, "columns", []):
                endpoints = list(df[source_col].dropna().astype(str)) + list(df[target_col].dropna().astype(str))
                module_count = len(set(endpoints))
                edge_count = int(df[[source_col, target_col]].dropna().shape[0])
            elif node_col in getattr(df, "columns", []):
                module_count = int(df[node_col].dropna().astype(str).nunique())
                edge_count = max(0, module_count - 1)
            if params_col in getattr(df, "columns", []):
                params = pd.to_numeric(df[params_col], errors="coerce")
                if params.notna().any():
                    params_total = float(params.sum())
        label = "architecture topology"
        if module_count is not None:
            label += f"\nmodules={module_count}"
            lines.append(f"modules={module_count}")
        if edge_count is not None:
            lines.append(f"edges={edge_count}")
        if params_total is not None:
            lines.append(f"params={params_total:.3g}")
        _add_inplot_label(ax, label, visualPlan, loc="upper_right")
        _record_template_motif(visualPlan, "neural_architecture_topology")
        enhancements.append("neural_architecture_topology")
        if _template_motif_planned(visualPlan, "architecture_metric_dashboard"):
            _record_template_motif(visualPlan, "architecture_metric_dashboard")
            enhancements.append("architecture_metric_dashboard")
        if _template_motif_planned(visualPlan, "architecture_metric_storyboard"):
            _record_template_motif(visualPlan, "architecture_metric_storyboard")
            enhancements.append("architecture_metric_storyboard")
    if _template_motif_planned(visualPlan, "explainability_importance_stack"):
        feature_col = _role(dataProfile, "feature_id", "label", "feature")
        importance_col = _role(dataProfile, "importance", "shap_value", "effect", "value")
        feature_count = df[feature_col].nunique() if df is not None and feature_col in df else len(values)
        _maybe_reference_zero(ax, visualPlan)
        _add_inplot_label(ax, f"ranked feature evidence\nfeatures={feature_count}", visualPlan, loc="upper_left")
        _record_template_motif(visualPlan, "explainability_importance_stack")
        if importance_col:
            _record_template_motif(visualPlan, "signed_effect_axis")
        enhancements.append("explainability_importance_stack")
    if _template_motif_planned(visualPlan, "pareto_tradeoff_board"):
        pareto_col = _role(dataProfile, "pareto_flag", "optimal_flag")
        objective_cols = [
            col for col in getattr(df, "columns", [])
            if any(token in str(col).lower() for token in ("objective", "loss", "cost", "utility", "score"))
        ] if df is not None else []
        pareto_count = None
        if pareto_col and df is not None and pareto_col in df:
            try:
                pareto_count = int(np.asarray(df[pareto_col], dtype=float).sum())
            except (TypeError, ValueError):
                pareto_count = int(df[pareto_col].astype(bool).sum())
        label = f"tradeoff board\nobjectives={len(objective_cols)}"
        if pareto_count is not None:
            label += f"\npareto={pareto_count}"
        _add_inplot_label(ax, label, visualPlan, loc="upper_right")
        _record_template_motif(visualPlan, "pareto_tradeoff_board")
        enhancements.append("pareto_tradeoff_board")
    if _template_motif_planned(visualPlan, "polar_comparison_signature"):
        _record_template_motif(visualPlan, "polar_comparison_signature")
        enhancements.append("polar_comparison_signature")
    summary_loc = "lower_left" if len(enhancements) > 2 else "upper_left"
    _add_inplot_label(ax, "\n".join(lines[:2]) if lines else "composition", visualPlan, loc=summary_loc)
    _add_metric_box(ax, lines or ["composition summary"], visualPlan)
    _record_motif(visualPlan, "composition_summary")
    return enhancements


def _enhance_psych_ecology(ax, dataProfile, visualPlan, palette, col_map):
    _maybe_reference_zero(ax)
    df = _df_from_profile(dataProfile)
    value_col = _role(dataProfile, "value", "y")
    values = _numeric_values(df, value_col)
    if len(values):
        _add_inplot_label(ax, f"mean={np.nanmean(values):.3g}\nmedian={np.nanmedian(values):.3g}", visualPlan, loc="upper_left")
        _add_metric_box(ax, [f"n={len(values)}", f"mean={np.nanmean(values):.3g}", f"median={np.nanmedian(values):.3g}"], visualPlan)
    else:
        _add_inplot_label(ax, "rank/proportion view", visualPlan, loc="upper_left")
        _add_metric_box(ax, ["rank/proportion view"], visualPlan)
    _record_motif(visualPlan, "response_summary")
    return ["reference_band", "descriptive_summary", "inplot_response_label"]


def _enhance_generic(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    n = None
    if df is not None:
        try:
            n = len(df)
        except TypeError:
            n = None
    _maybe_reference_zero(ax)
    _add_inplot_label(ax, f"n={n}" if n is not None else "descriptive view", visualPlan, loc="upper_left")
    _add_metric_box(ax, [f"n={n}" if n is not None else "descriptive view"], visualPlan)
    _record_motif(visualPlan, "descriptive_summary_box")
    interval_motif = _add_interval_template_summary(ax, dataProfile, visualPlan)
    if interval_motif:
        return ["descriptive_context", interval_motif]
    return ["descriptive_context", "inplot_context_label"]


def apply_visual_content_pass(fig, axes, chartPlan, dataProfile, journalProfile, palette, col_map=None):
    """Add Nature/Cell-style information density after base plotting."""
    visualPlan = _ensure_visual_content_plan(chartPlan, dataProfile=dataProfile)
    if visualPlan.get("mode") in ("off", "none"):
        return {"appliedEnhancementCount": 0, "families": {}}

    actual_panel_count = max(1, len(axes))
    template_density_bonus = min(2, len(visualPlan.get("templateMotifs", [])))
    visualPlan["minTotalEnhancements"] = max(
        visualPlan.get("minTotalEnhancements", 0),
        actual_panel_count * visualPlan.get("minEnhancementsPerPanel", 2) + template_density_bonus,
    )
    if visualPlan.get("requireInPlotExplanatoryLabels", True):
        visualPlan["minInPlotLabelsPerFigure"] = max(
            1,
            min(actual_panel_count, visualPlan.get("maxCalloutsSingle", 8)),
        )

    panel_lookup = {
        panel.get("id"): panel.get("chart")
        for panel in chartPlan.get("panelBlueprint", {}).get("panels", [])
        if isinstance(panel, dict)
    }
    families = {}
    for panel_id, ax in axes.items():
        chart_type = panel_lookup.get(panel_id) or chartPlan.get("primaryChart")
        family = infer_chart_family(chart_type)
        families[panel_id] = family
        try:
            if family == "distribution":
                enhancements = _enhance_distribution(ax, dataProfile, visualPlan, palette, col_map)
            elif family == "scatter_embedding":
                enhancements = _enhance_scatter(ax, dataProfile, visualPlan, palette, col_map)
            elif family == "matrix_heatmap":
                enhancements = _enhance_matrix(ax, dataProfile, visualPlan, palette, col_map)
            elif family == "time_series":
                enhancements = _enhance_time_series(ax, dataProfile, visualPlan, palette, col_map)
            elif family == "clinical_diagnostic":
                enhancements = _enhance_clinical(ax, dataProfile, visualPlan, palette, col_map, str(chart_type or ""))
            elif family == "genomics_enrichment":
                enhancements = _enhance_genomics(ax, dataProfile, visualPlan, palette, col_map, str(chart_type or ""))
            elif family == "engineering_spectra":
                enhancements = _enhance_engineering(ax, dataProfile, visualPlan, palette, col_map)
            elif family == "composition_flow":
                enhancements = _enhance_composition(ax, dataProfile, visualPlan, palette, col_map)
            elif family == "psych_ecology":
                enhancements = _enhance_psych_ecology(ax, dataProfile, visualPlan, palette, col_map)
            else:
                enhancements = _enhance_generic(ax, dataProfile, visualPlan, palette, col_map)
        except Exception as exc:
            visualPlan.setdefault("enhancementWarnings", []).append({
                "panel": panel_id,
                "family": family,
                "error": f"{type(exc).__name__}: {str(exc)[:120]}",
            })
            try:
                enhancements = _enhance_generic(ax, dataProfile, visualPlan, palette, col_map)
            except Exception:
                enhancements = []

        fallback_label = _ensure_panel_explanatory_label(ax, visualPlan, family)
        if fallback_label is not None:
            enhancements.append("fallback_inplot_explanatory_label")
        for enhancement in enhancements:
            _record_visual(visualPlan, panel_id, family, enhancement)

    chartPlan["visualContentPlan"] = visualPlan
    return {
        "appliedEnhancementCount": len(visualPlan.get("appliedEnhancements", [])),
        "inPlotExplanatoryLabelCount": visualPlan.get("inPlotExplanatoryLabelCount", 0),
        "metricBoxCount": visualPlan.get("metricBoxCount", 0),
        "metricTableCount": visualPlan.get("metricTableCount", 0),
        "metricTableRelocatedCount": visualPlan.get("metricTableRelocatedCount", 0),
        "metricTableSuppressedCount": visualPlan.get("metricTableSuppressedCount", 0),
        "metricTableFallbackBoxCount": visualPlan.get("metricTableFallbackBoxCount", 0),
        "insetCount": visualPlan.get("insetCount", 0),
        "referenceLineCount": visualPlan.get("referenceLineCount", 0),
        "densityHaloCount": visualPlan.get("densityHaloCount", 0),
        "sampleEncodingCount": visualPlan.get("sampleEncodingCount", 0),
        "significanceStarLayerCount": visualPlan.get("significanceStarLayerCount", 0),
        "dualAxisEncodingCount": visualPlan.get("dualAxisEncodingCount", 0),
        "referenceMotifCount": visualPlan.get("referenceMotifCount", 0),
        "templateMotifCount": visualPlan.get("templateMotifCount", 0),
        "minTemplateMotifsPerFigure": visualPlan.get("minTemplateMotifsPerFigure", 0),
        "templateMotifs": visualPlan.get("templateMotifs", []),
        "templateMotifsApplied": visualPlan.get("templateMotifsApplied", []),
        "marginalAxesCount": visualPlan.get("marginalAxesCount", 0),
        "densityColorEncodingCount": visualPlan.get("densityColorEncodingCount", 0),
        "subAxesCount": visualPlan.get("subAxesCount", 0),
        "colorbarSlotCount": visualPlan.get("colorbarSlotCount", 0),
        "multiAxisEncodingCount": visualPlan.get("multiAxisEncodingCount", 0),
        "minReferenceMotifsPerFigure": visualPlan.get("minReferenceMotifsPerFigure", 0),
        "visualGrammarMotifs": visualPlan.get("visualGrammarMotifs", []),
        "visualGrammarMotifsApplied": visualPlan.get("visualGrammarMotifsApplied", []),
        "minTotalEnhancements": visualPlan.get("minTotalEnhancements", 0),
        "minInPlotLabelsPerFigure": visualPlan.get("minInPlotLabelsPerFigure", 0),
        "families": families,
        "outsideLayoutElements": visualPlan.get("outsideLayoutElements", False),
    }


def default_crowding_plan():
    return {**CROWDING_DEFAULTS, "simplificationsApplied": []}


def dedupe_handles_labels(handles, labels):
    seen = set()
    out_handles = []
    out_labels = []
    for handle, label in zip(handles, labels):
        clean = str(label).strip()
        if not clean or clean == "_nolegend_" or clean in seen:
            continue
        seen.add(clean)
        out_handles.append(handle)
        out_labels.append(clean)
    return out_handles, out_labels


def collect_legend_entries(axes):
    handles = []
    labels = []
    for ax in axes.values():
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
        legend = ax.get_legend()
        if legend is not None:
            legend_handles = getattr(legend, "legend_handles", None)
            if legend_handles is None:
                legend_handles = getattr(legend, "legendHandles", [])
            legend_labels = [text.get_text() for text in legend.get_texts()]
            handles.extend(legend_handles)
            labels.extend(legend_labels)
    return dedupe_handles_labels(handles, labels)


def collect_figure_legend_entries(fig):
    handles = []
    labels = []
    for legend in list(getattr(fig, "legends", [])):
        legend_handles = getattr(legend, "legend_handles", None)
        if legend_handles is None:
            legend_handles = getattr(legend, "legendHandles", [])
        legend_labels = [text.get_text() for text in legend.get_texts()]
        handles.extend(legend_handles)
        labels.extend(legend_labels)
    return dedupe_handles_labels(handles, labels)


def _panel_id_from_index(index):
    if index < 26:
        return chr(65 + index)
    return f"P{index + 1}"


def normalize_axes_map(fig, axes=None):
    """Return panel-id -> Axes, adding unnamed non-colorbar fig.axes.

    Cycle-24: single-axis path now audits all fig.axes including inset axes
    (fix B01). The caller's explicit panel keys stay stable; extra child axes
    are appended as A1, A2, ... by Axes identity rather than label.
    """
    def _is_colorbar_axes(ax):
        label = str(getattr(ax, "get_label", lambda: "")())
        if label == "<colorbar>":
            return True
        if getattr(ax, "_colorbar", None) is not None:
            return True
        return False

    if isinstance(axes, dict):
        axes_map = {key: ax for key, ax in axes.items() if ax is not None}
    else:
        if axes is None:
            raw_axes = [ax for ax in fig.axes if ax.get_visible()]
        elif hasattr(axes, "ravel"):
            raw_axes = list(axes.ravel())
        elif isinstance(axes, (list, tuple, set)):
            raw_axes = list(axes)
        else:
            raw_axes = [axes]

        axes_map = {}
        for ax in raw_axes:
            if ax is None:
                continue
            if _is_colorbar_axes(ax) and ax.get_legend() is None:
                continue
            axes_map[_panel_id_from_index(len(axes_map))] = ax

    seen_ids = {id(ax) for ax in axes_map.values() if ax is not None}
    child_index = 1
    candidate_axes = list(getattr(fig, "axes", []))
    for parent_ax in list(candidate_axes):
        for child_ax in getattr(parent_ax, "child_axes", []):
            if id(child_ax) not in {id(candidate) for candidate in candidate_axes}:
                candidate_axes.append(child_ax)
    for ax in candidate_axes:
        if ax is None or id(ax) in seen_ids:
            continue
        if not getattr(ax, "get_visible", lambda: True)():
            continue
        if _is_colorbar_axes(ax) and ax.get_legend() is None:
            continue
        key = f"A{child_index}"
        while key in axes_map:
            child_index += 1
            key = f"A{child_index}"
        axes_map[key] = ax
        seen_ids.add(id(ax))
        child_index += 1
    return axes_map


def remove_axis_legends(axes):
    """Robust removal of every Legend artist on each Axes.

    matplotlib's ``ax.get_legend()`` only returns the *most recent* legend
    attached as ``ax._legend``. When a generator calls ``ax.legend(...)``
    multiple times — or when a Legend was attached via ``ax.add_artist(...)``
    — the older Legend artists remain in ``ax.get_children()`` even though
    ``get_legend()`` no longer sees them. They still render, producing the
    "ghost legend" occlusion users observe in multi-panel figures.

    This sweep enumerates every child of each Axes and removes any
    matplotlib.legend.Legend instance, then also removes the canonical
    ``ax._legend`` to leave a clean slate.

    Returns the total number of Legend artists removed.
    """
    from matplotlib.legend import Legend
    removed = 0
    for ax in axes.values():
        # Strategy 1: clean stale legends hidden in the children list first
        for child in list(ax.get_children()):
            if isinstance(child, Legend):
                try:
                    child.remove()
                    removed += 1
                except Exception:  # noqa: BLE001 — keep sweeping
                    pass
        # Strategy 2: clean canonical ax._legend if anything still lingers
        primary = ax.get_legend()
        if primary is not None:
            try:
                primary.remove()
                removed += 1
            except Exception:
                pass
    return removed


def count_axis_legends(axes):
    """Count every Legend artist on each Axes (not just ax._legend).

    Mirrors :func:`remove_axis_legends` so the contract verifier sees the
    same Legend instances the renderer actually paints.
    """
    from matplotlib.legend import Legend
    count = 0
    for ax in axes.values():
        for child in ax.get_children():
            if isinstance(child, Legend):
                count += 1
    return count


def shorten_legend_labels(labels, max_chars=32):
    shortened = False
    output = []
    for label in labels:
        clean = str(label).strip()
        if max_chars and len(clean) > max_chars:
            output.append(clean[:max_chars - 3].rstrip() + "...")
            shortened = True
        else:
            output.append(clean)
    return output, shortened


ASCII_TEXT_REPLACEMENTS = (
    ("R⊕", "Earth radii"),
    ("M⊕", "Earth masses"),
    ("R_⊕", "Earth radii"),
    ("M_⊕", "Earth masses"),
    ("log₁₀", "log10"),
    ("₀", "0"),
    ("₁", "1"),
    ("₂", "2"),
    ("₃", "3"),
    ("₄", "4"),
    ("₅", "5"),
    ("₆", "6"),
    ("₇", "7"),
    ("₈", "8"),
    ("₉", "9"),
    ("—", "-"),
    ("–", "-"),
    ("−", "-"),
    ("×", "x"),
    ("±", "+/-"),
    ("≤", "<="),
    ("≥", ">="),
    ("⊕", "Earth"),
)


def ascii_safe_text(value):
    text = str(value)
    for old, new in ASCII_TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def sanitize_figure_text(fig):
    """Replace fragile label glyphs that render as boxes on minimal systems."""
    from matplotlib.text import Text

    changed = 0
    for text_artist in fig.findobj(match=Text):
        try:
            current = text_artist.get_text()
        except Exception:
            continue
        safe = ascii_safe_text(current)
        if safe != current:
            text_artist.set_text(safe)
            changed += 1
    if changed:
        invalidate_layout_cache(fig)
    return {"asciiTextReplacementCount": changed}


def center_figure_titles(fig, axes):
    """Normalize suptitle and Axes titles to centered alignment before QA."""
    centered = 0
    moved_side_titles = 0

    suptitle = getattr(fig, "_suptitle", None)
    if suptitle is not None and str(suptitle.get_text()).strip():
        suptitle.set_x(0.5)
        suptitle.set_ha("center")
        centered += 1

    for ax in axes.values():
        center_title = getattr(ax, "title", None)
        side_titles = [
            getattr(ax, "_left_title", None),
            getattr(ax, "_right_title", None),
        ]
        if center_title is not None and str(center_title.get_text()).strip():
            try:
                _, y_pos = center_title.get_position()
            except Exception:
                y_pos = 1.0
            center_title.set_position((0.5, y_pos))
            center_title.set_ha("center")
            centered += 1

        for side_title in side_titles:
            if side_title is None:
                continue
            text = str(side_title.get_text()).strip()
            if not text:
                continue
            if center_title is not None and not str(center_title.get_text()).strip():
                ax.set_title(
                    text,
                    loc="center",
                    fontsize=side_title.get_fontsize(),
                    fontweight=side_title.get_fontweight(),
                    fontstyle=side_title.get_fontstyle(),
                    color=side_title.get_color(),
                    pad=4,
                )
                centered += 1
            side_title.set_text("")
            moved_side_titles += 1

    if centered or moved_side_titles:
        invalidate_layout_cache(fig)
    return {
        "centeredTitleCount": centered,
        "sideTitleMovedCount": moved_side_titles,
    }


def trim_excess_text_annotations(ax, max_keep):
    if max_keep is None:
        return 0
    # Heatmap bypass: an Axes hosting a QuadMesh (sns.heatmap / pcolormesh)
    # has one Text per cell — N×N can easily reach hundreds. Trimming those
    # would destroy the heatmap's quantitative annotations. The
    # post-finalizer ``_shrink_heatmap_cell_labels`` is the right reformer
    # for that case; this trim only applies to free-standing direct labels.
    from matplotlib.collections import QuadMesh
    if any(isinstance(c, QuadMesh) for c in ax.collections):
        return 0
    protected_gids = {"scifig_metric_box", "scifig_inplot_label"}
    trim_candidates = []
    for text in list(ax.texts):
        gid = getattr(text, "get_gid", lambda: None)()
        raw = str(text.get_text())
        if gid in protected_gids or raw.startswith("n="):
            continue
        trim_candidates.append(text)
    if len(trim_candidates) <= max_keep:
        return 0
    removed = 0
    for text in trim_candidates[max_keep:]:
        text.remove()
        removed += 1
    return removed


def trim_pvalue_annotations(ax, max_keep=2):
    p_texts = [text for text in list(ax.texts) if str(text.get_text()).startswith("p")]
    removed = 0
    for text in p_texts[max_keep:]:
        text.remove()
        removed += 1
    return removed


def find_first_mappable(ax):
    for artist in list(ax.images) + list(ax.collections):
        if hasattr(artist, "get_array"):
            data = artist.get_array()
            if data is not None:
                return artist
    return None


def remove_extra_axes(fig, axes):
    panel_axes = set(axes.values())
    for extra_ax in [ax for ax in list(fig.axes) if ax not in panel_axes]:
        extra_ax.remove()


def get_non_panel_axes(fig, axes):
    panel_axes = set(axes.values())
    return [ax for ax in list(fig.axes) if ax not in panel_axes]


def get_cached_renderer(fig, force=False):
    if force or not hasattr(fig, "_scifig_renderer_cache"):
        fig.canvas.draw()
        fig._scifig_renderer_cache = fig.canvas.get_renderer()
    return fig._scifig_renderer_cache


def invalidate_layout_cache(fig):
    if hasattr(fig, "_scifig_renderer_cache"):
        delattr(fig, "_scifig_renderer_cache")


def _bbox_in_figure_coords(fig, artist):
    renderer = get_cached_renderer(fig)
    return artist.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())


def _axis_layout_bbox(ax, renderer):
    try:
        tight = ax.get_tightbbox(renderer)
        if tight is not None:
            return tight
    except Exception:
        pass
    return ax.get_window_extent(renderer=renderer)


def legend_overlaps_axes(fig, legend, axes):
    renderer = get_cached_renderer(fig)
    legend_box = legend.get_window_extent(renderer=renderer)
    return any(legend_box.overlaps(ax.get_window_extent(renderer=renderer)) for ax in axes)


def elements_overlap_axes(fig, axes):
    renderer = get_cached_renderer(fig)
    axes_boxes = {pid: _axis_layout_bbox(ax, renderer) for pid, ax in axes.items()}
    issues = []
    for ax_pid, ax in axes.items():
        for child in ax.get_children():
            gid = getattr(child, "get_gid", lambda: None)()
            if gid in ("scifig_metric_box", "scifig_inset"):
                try:
                    child_box = child.get_window_extent(renderer=renderer)
                    for other_pid, other_box in axes_boxes.items():
                        if other_pid != ax_pid and child_box.overlaps(other_box):
                            issues.append({"element": gid, "host_panel": ax_pid, "conflict_panel": other_pid})
                except Exception:
                    pass
    return issues


def _iter_layout_artists(axes):
    for panel_id, ax in axes.items():
        seen = set()
        candidates = list(getattr(ax, "texts", []))
        candidates.extend([ax.title, ax.xaxis.label, ax.yaxis.label])
        candidates.extend(list(getattr(ax, "tables", [])))
        for artist in candidates:
            if artist is None or id(artist) in seen:
                continue
            seen.add(id(artist))
            if hasattr(artist, "get_visible") and not artist.get_visible():
                continue
            if hasattr(artist, "get_text") and not str(artist.get_text()).strip():
                continue
            yield panel_id, artist


def _bbox_outside(inner, outer, tol=2.0):
    return (
        inner.x0 < outer.x0 - tol or
        inner.y0 < outer.y0 - tol or
        inner.x1 > outer.x1 + tol or
        inner.y1 > outer.y1 + tol
    )


def _bbox_union(boxes):
    if not boxes:
        return None
    x0 = min(box.x0 for box in boxes)
    y0 = min(box.y0 for box in boxes)
    x1 = max(box.x1 for box in boxes)
    y1 = max(box.y1 for box in boxes)
    return x0, y0, x1, y1


def _bbox_area(box):
    if box is None:
        return 0.0
    if isinstance(box, tuple):
        return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])
    return max(0.0, box.width) * max(0.0, box.height)


def _bbox_overlap_area(first, second):
    if first is None or second is None:
        return 0.0
    x0 = max(first.x0, second.x0)
    x1 = min(first.x1, second.x1)
    y0 = max(first.y0, second.y0)
    y1 = min(first.y1, second.y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def _axes_share_visual_panel(first_box, second_box, threshold=0.85):
    """Return true for overlaid axes such as twinx/twiny panels."""
    smaller_area = min(_bbox_area(first_box), _bbox_area(second_box))
    if smaller_area <= 0:
        return False
    return (_bbox_overlap_area(first_box, second_box) / smaller_area) >= threshold


def _metric_table_data_overlap_issues(fig, axes, renderer):
    issues = []
    for panel_id, ax in axes.items():
        tables = [
            table for table in getattr(ax, "tables", [])
            if getattr(table, "get_gid", lambda: None)() == "scifig_metric_table"
            and getattr(table, "get_visible", lambda: True)()
        ]
        if not tables:
            continue
        data_patches = _metric_table_data_patch_bboxes(ax, renderer)
        for table_index, table in enumerate(tables):
            try:
                table_box = table.get_window_extent(renderer=renderer)
            except Exception:
                continue
            for patch_index, patch_box in enumerate(data_patches):
                if table_box.overlaps(patch_box):
                    issues.append({
                        "panel": panel_id,
                        "tableIndex": table_index,
                        "dataPatchIndex": patch_index,
                        "element": "scifig_metric_table",
                        "conflict": "data_bar",
                    })
                    break
    return issues


def _text_data_overlap_issues(fig, axes, renderer, threshold=0.30, report=None):
    """Detect annotations that are visually buried under data artists.

    For each Axes, intersect every Text artist's display-coord bbox with
    the bboxes of every Line2D / Collection / Patch on the same Axes.
    When the overlap area exceeds ``threshold`` * text bbox area, the
    text is being painted on top of a data layer with significant
    coverage — readers cannot resolve the label cleanly.

    Excludes:
      * Panel labels (single uppercase letters A-Z) — they live in axis-coord
        margin slots and are intended to be free-floating.
      * Texts whose ``gid`` marks them as already-managed metric-box content.
      * Texts that already carry an opaque-enough bbox patch (i.e., the
        ``_promote_inaxes_text_safety`` retrofit applied a white bbox).
        Such labels have visual occlusion already resolved by the bbox
        — the geometric bbox-vs-line overlap is not a usability problem.

    Returns a list of issue dicts compatible with the
    ``layoutContractFailures`` aggregation.
    """
    from matplotlib.text import Text as _Text

    # Cycle-24: text-vs-text + bbox coverage audits added (B09 + B10).
    issues = []
    if report is None:
        report = {}
    report.setdefault("bboxDataCoverageOverflowCount", 0)
    panel_label_set = {chr(code) for code in range(65, 91)}
    managed_gids = {"scifig_metric_box", "scifig_metric_table"}

    def _has_opaque_bbox(text_artist):
        """True if the Text artist has a bbox patch with white-ish opaque fill.

        Visual occlusion is only "resolved" when the bbox is both:
          * White-ish (R, G, B all > 0.85) — a coloured bbox would still
            blend with the underlying line and require contrast checking.
          * Sufficiently opaque (alpha >= 0.5).

        Anything else (transparent box, coloured semantic-encoding bbox,
        decorative tinted background) is treated as NOT occlusion-safe so
        the audit still flags the geometric overlap.
        """
        patch = text_artist.get_bbox_patch()
        if patch is None:
            return False
        try:
            face = patch.get_facecolor()
            if not face or len(face) < 3:
                return False
            r, g, b = float(face[0]), float(face[1]), float(face[2])
            alpha = float(face[3]) if len(face) >= 4 else 1.0
            if alpha < 0.5:
                return False
            # Whitish heuristic: each channel above 0.85 (corpus default
            # is pure white 1.0, so this allows minor off-white tints).
            return r > 0.85 and g > 0.85 and b > 0.85
        except Exception:
            return False

    for panel_id, ax in axes.items():
        # Collect text artists worth checking
        text_artists = []
        for child in ax.get_children():
            if not isinstance(child, _Text):
                continue
            raw = str(child.get_text()).strip()
            if not raw:
                continue
            if raw in panel_label_set:
                continue
            gid = getattr(child, "get_gid", lambda: None)()
            if gid in managed_gids:
                continue
            # Skip artists that already have an opaque bbox — visual
            # occlusion resolved by the bbox itself.
            has_opaque_bbox = _has_opaque_bbox(child)
            try:
                tbox = child.get_window_extent(renderer=renderer)
                if tbox.width <= 0 or tbox.height <= 0:
                    continue
            except Exception:
                continue
            text_artists.append((child, tbox, raw, has_opaque_bbox))

        if not text_artists:
            continue

        # Collect data artist bboxes (lines / collections / patches)
        data_bboxes = []
        for artist in list(ax.lines) + list(ax.collections) + list(ax.patches):
            try:
                if not artist.get_visible():
                    continue
                bbox = artist.get_window_extent(renderer=renderer)
                if bbox is None or bbox.width <= 0 or bbox.height <= 0:
                    continue
                data_bboxes.append((artist, bbox))
            except Exception:
                continue

        if not data_bboxes:
            continue

        axes_box = ax.get_window_extent(renderer=renderer)
        axes_area = max(_bbox_area(axes_box), 1.0)

        for text_artist, tbox, raw, has_opaque_bbox in text_artists:
            tbox_area = max(tbox.width * tbox.height, 1.0)
            if has_opaque_bbox:
                coverage_ratio = tbox_area / axes_area
                if coverage_ratio <= 0.40:
                    continue
                for artist, dbox in data_bboxes:
                    if tbox.overlaps(dbox):
                        report["bboxDataCoverageOverflowCount"] = report.get("bboxDataCoverageOverflowCount", 0) + 1
                        issues.append({
                            "panel": panel_id,
                            "element": "annotation_text_bbox",
                            "conflict": "bbox_oversized_data_coverage",
                            "text": raw[:32],
                            "bbox_data_coverage_ratio": round(coverage_ratio, 3),
                        })
                        break
                continue
            for artist, dbox in data_bboxes:
                if not tbox.overlaps(dbox):
                    continue
                # Compute intersection area
                x0 = max(tbox.x0, dbox.x0); x1 = min(tbox.x1, dbox.x1)
                y0 = max(tbox.y0, dbox.y0); y1 = min(tbox.y1, dbox.y1)
                if x1 <= x0 or y1 <= y0:
                    continue
                overlap_area = (x1 - x0) * (y1 - y0)
                ratio = overlap_area / tbox_area
                if ratio < threshold:
                    continue
                issues.append({
                    "panel": panel_id,
                    "element": "annotation_text",
                    "conflict": type(artist).__name__.lower(),
                    "text": raw[:32],
                    "overlap_ratio": round(ratio, 3),
                })
                break  # one overlap per text is enough to flag
    return issues


def _text_text_overlap_issues(axes, report, renderer=None, iou_threshold=0.15):
    """Detect label-on-label collisions inside each audited Axes.

    Cycle-24: text-vs-text + bbox coverage audits added (B09 + B10).
    """
    from matplotlib.text import Annotation as _Annotation
    from matplotlib.text import Text as _Text

    issues = []
    report.setdefault("textTextOverlapCount", 0)
    panel_label_set = {chr(code) for code in range(65, 91)}
    managed_gids = {"scifig_metric_box", "scifig_metric_table", "scifig_panel_label"}

    def _overlap_area(a, b):
        x0 = max(a.x0, b.x0); x1 = min(a.x1, b.x1)
        y0 = max(a.y0, b.y0); y1 = min(a.y1, b.y1)
        if x1 <= x0 or y1 <= y0:
            return 0.0
        return (x1 - x0) * (y1 - y0)

    for panel_id, ax in axes.items():
        texts = []
        seen = set()
        candidates = list(ax.texts) + [obj for obj in ax.findobj(_Annotation)]
        for child in candidates:
            if id(child) in seen or not isinstance(child, _Text):
                continue
            seen.add(id(child))
            raw = str(child.get_text()).strip()
            if not raw or raw in panel_label_set:
                continue
            gid = getattr(child, "get_gid", lambda: None)()
            if gid in managed_gids:
                continue
            try:
                box = child.get_window_extent(renderer=renderer)
            except Exception:
                continue
            if box is None or box.width <= 0 or box.height <= 0:
                continue
            texts.append((child, box, raw))

        for idx, (_, box_a, text_a) in enumerate(texts):
            for _, box_b, text_b in texts[idx + 1:]:
                overlap = _overlap_area(box_a, box_b)
                if overlap <= 0:
                    continue
                union = max(_bbox_area(box_a) + _bbox_area(box_b) - overlap, 1.0)
                iou = overlap / union
                if iou <= iou_threshold:
                    continue
                report["textTextOverlapCount"] = report.get("textTextOverlapCount", 0) + 1
                issues.append({
                    "panel": panel_id,
                    "element": "annotation_text",
                    "conflict": "text_text_overlap",
                    "text": text_a[:32],
                    "other_text": text_b[:32],
                    "iou": round(iou, 3),
                })
                break
    return issues


def _promote_inaxes_text_safety(axes, *, target_zorder=20, alpha=0.85, pad=0.25):
    """Zero-touch retrofit: enforce occlusion-safe state on every in-axes Text.

    Generators historically call ``ax.text(...)`` / ``ax.annotate(...)`` with
    matplotlib defaults (zorder=3, no bbox), which leaves the label silently
    buried under any line drawn afterward (default zorder=2 but cumulative
    fills/scatter often raise the data layer above 3).

    Rather than rewriting 100+ scattered call sites in
    ``generators-*.md / .py``, this function — invoked once near the end of
    ``enforce_figure_legend_contract`` — sweeps every Axes and:

      * Promotes the Text artist's zorder to ``target_zorder`` (default 20)
        if it is currently lower.
      * Adds a rounded white bbox (alpha=0.85) if the artist has no bbox.

    Excludes infrastructure text that should NOT carry a white bbox:
      * Panel labels (single uppercase A-Z),
      * Axis title, axis x/y labels,
      * Tick labels,
      * Anything carrying a managed gid (metric box, inplot label, panel label),
      * **Heatmap cell labels** (text inside an Axes hosting a QuadMesh) —
        a white bbox would obliterate the cell colour and defeat the heatmap.

    Returns a counter dict for diagnostics::

        {"promoted_zorder": int, "promoted_bbox": int}
    """
    from matplotlib.text import Text as _Text
    from matplotlib.collections import QuadMesh

    panel_label_set = {chr(c) for c in range(65, 91)}
    managed_gids = {
        "scifig_metric_box",
        "scifig_metric_table",
        "scifig_inplot_label",
        "scifig_panel_label",
        "scifig_no_safety_bbox",   # M2: explicit opt-out for generators that need
                                    # raw text (LaTeX equations, arrow callouts,
                                    # decorative labels with custom backgrounds)
    }
    promoted_zorder = 0
    promoted_bbox = 0

    for ax in axes.values():
        # Detect heatmap-style Axes (skip bbox addition for cell labels)
        is_heatmap = any(isinstance(c, QuadMesh) for c in ax.collections)

        # Build a "do not touch" set of Text artist ids belonging to axis chrome
        protected_ids = set()
        try:
            protected_ids.add(id(ax.title))
        except Exception:
            pass
        try:
            protected_ids.add(id(ax.xaxis.label))
        except Exception:
            pass
        try:
            protected_ids.add(id(ax.yaxis.label))
        except Exception:
            pass
        try:
            for tick_label in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
                protected_ids.add(id(tick_label))
        except Exception:
            pass

        for child in ax.get_children():
            if not isinstance(child, _Text):
                continue
            if id(child) in protected_ids:
                continue
            raw = str(child.get_text()).strip()
            if not raw:
                continue
            if raw in panel_label_set:
                continue
            gid = getattr(child, "get_gid", lambda: None)()
            if gid in managed_gids:
                continue

            current_z = child.get_zorder() or 0
            if current_z < target_zorder:
                child.set_zorder(target_zorder)
                promoted_zorder += 1

            # Skip bbox addition on heatmap cell labels — the cell's
            # face colour is the visual signal; a white bbox would erase it.
            if is_heatmap:
                continue

            if child.get_bbox_patch() is None:
                child.set_bbox(dict(
                    boxstyle=f"round,pad={pad}",
                    facecolor="white",
                    alpha=alpha,
                    edgecolor="none",
                    linewidth=0,
                ))
                promoted_bbox += 1

    return {"promoted_zorder": promoted_zorder, "promoted_bbox": promoted_bbox}


def _shrink_heatmap_cell_labels(axes, fig, *, font_size_pt=5.0, char_width_factor=0.55):
    """Re-format heatmap cell label text strings to fit cell physical width.

    For each Axes hosting a QuadMesh (i.e., a heatmap), compute the cell
    physical width from ``ax.get_position()`` and ``fig.get_size_inches()``
    divided by the mesh column count, then call ``choose_heatmap_fmt`` to
    pick the longest format string that fits. Existing numeric-text artists
    in ``ax.texts`` are reformatted in place (e.g., "−0.873" → "−0.9");
    when the cell is too tiny for any digit fmt, every numeric label is
    removed (the heatmap colour itself remains the only signal).

    This is a zero-touch retrofit — generators continue to call
    ``sns.heatmap(annot=True, fmt=".2f")`` as today; the corrective pass
    here adapts to the final layout once the figure size is known.

    Returns a counter dict::

        {"reformatted": int, "removed": int, "skipped_axes": int}
    """
    from matplotlib.collections import QuadMesh

    reformatted = 0
    removed = 0
    skipped_axes = 0

    fig_w_in, _ = fig.get_size_inches()

    for ax in axes.values():
        meshes = [c for c in ax.collections if isinstance(c, QuadMesh)]
        if not meshes:
            continue
        qm = meshes[0]
        # Detect column count.
        # M3: prefer the public API (Path count) before falling back to the
        # internal `_meshWidth` / `_coordinates` attributes which may be
        # renamed in future matplotlib versions.
        n_cols = None
        try:
            n_paths = len(qm.get_paths())
            if n_paths > 0:
                root = int(round(n_paths ** 0.5))
                if root * root == n_paths:
                    n_cols = root  # square mesh
        except Exception:
            pass
        if n_cols is None:
            for attr in ("_meshWidth", "_coordinates"):
                val = getattr(qm, attr, None)
                if val is None:
                    continue
                if attr == "_meshWidth" and isinstance(val, (int, float)):
                    n_cols = int(val)
                    break
                if attr == "_coordinates":
                    try:
                        n_cols = val.shape[1] - 1
                        break
                    except Exception:
                        continue
        if n_cols is None:
            try:
                arr = qm.get_array()
                if arr.ndim == 2:
                    n_cols = arr.shape[1]
                elif arr.ndim == 1:
                    n_cols = int(np.sqrt(arr.size))
            except Exception:
                pass
        if n_cols is None or n_cols <= 0:
            skipped_axes += 1
            continue

        try:
            position = ax.get_position()
            cell_width_in = position.width * fig_w_in / n_cols
        except Exception:
            skipped_axes += 1
            continue

        try:
            arr = qm.get_array()
            vmin = float(np.nanmin(arr)); vmax = float(np.nanmax(arr))
        except Exception:
            vmin, vmax = -1.0, 1.0

        # Use the function from template_mining_helpers if available; otherwise
        # reproduce the calculation locally so this works even when not embedded.
        try:
            tmh_choose = globals().get("choose_heatmap_fmt")
            if tmh_choose is None:
                # Inline duplicate of choose_heatmap_fmt
                int_digits = max(
                    len(str(int(abs(vmin)))) + (1 if vmin < 0 else 0),
                    len(str(int(abs(vmax)))) + (1 if vmax < 0 else 0),
                    1,
                )
                char_width_in = (font_size_pt * char_width_factor) / 72.0
                available_in = cell_width_in * 0.85
                fmt = ""
                for decimals in (3, 2, 1, 0):
                    text_chars = int_digits if decimals == 0 else int_digits + 1 + decimals
                    if text_chars * char_width_in <= available_in:
                        fmt = f".{decimals}f"
                        break
            else:
                fmt = tmh_choose(cell_width_in, font_size_pt=font_size_pt,
                                  value_range=(vmin, vmax))
        except Exception:
            skipped_axes += 1
            continue

        # P2 — graceful integer fallback (cycle-23 fix for Finding-1)
        # When fmt == "" the strict-fit pass rejected every decimal width.
        # For integer / count-style heatmaps (e.g. weekday-by-hour trip counts)
        # this is too aggressive: removing 100% of labels destroys all
        # information density. Detect "values are effectively integers" and
        # accept .0f with mild overflow tolerance so the user still sees
        # the magnitudes, even if neighbouring labels touch by a hair.
        # Zero cells are still suppressed in graceful_threshold path below.
        force_integer_fallback = False
        if fmt == "":
            try:
                arr = qm.get_array()
                arr_finite = np.asarray(arr).astype(float)
                arr_finite = arr_finite[np.isfinite(arr_finite)]
                if arr_finite.size > 0:
                    is_integer = np.all(arr_finite == np.round(arr_finite))
                    char_width_in = (font_size_pt * char_width_factor) / 72.0
                    available_in = cell_width_in * 0.85
                    int_digits_local = max(
                        len(str(int(abs(vmin)))) + (1 if vmin < 0 else 0),
                        len(str(int(abs(vmax)))) + (1 if vmax < 0 else 0),
                        1,
                    )
                    needed_in = int_digits_local * char_width_in
                    # Allow up to 1.4x overflow for integer data so 5-digit
                    # counts (e.g. up to 99999) still annotate even when the
                    # cell is borderline-tight.
                    if is_integer and needed_in <= available_in * 1.4:
                        fmt = ".0f"
                        force_integer_fallback = True
            except Exception:
                pass

        # Reformat / remove text artists.
        # M1: skip texts that contain scientific notation ('e'/'E') or significance
        # markers ('*' / '†' / '‡' / '§') — generators may have intentional formats.
        # P1: when fmt == '.0f' (heavy density), apply graceful degradation —
        # remove non-diagonal cells with |value| < 0.5 so the remaining numbers
        # carry real information rather than a forest of "0" / "-0".
        # P2 (cycle-23): when force_integer_fallback is on, suppress zero-value
        # cells so a sparse-zero heatmap stays readable; do not impose the
        # diagonal-only rule (count heatmaps have no semantic diagonal).
        graceful_threshold = 0.5
        for txt in list(ax.texts):
            raw = str(txt.get_text()).strip()
            if not raw:
                continue
            # M1 — preserve generator-supplied special formats
            lowered = raw.lower()
            if "e" in lowered and any(ch.isdigit() for ch in lowered):
                # could be scientific notation like '1.2e-3'
                if any(marker in raw for marker in ("e+", "e-", "E+", "E-")):
                    continue
            if any(marker in raw for marker in ("*", "†", "‡", "§", "ns", "n.s.")):
                continue
            try:
                val = float(raw.replace("−", "-"))
            except ValueError:
                continue
            if fmt == "":
                txt.remove()
                removed += 1
                continue
            # P2 (cycle-23) — integer fallback: drop zero-value cells only
            if force_integer_fallback:
                if val == 0:
                    txt.remove()
                    removed += 1
                    continue
                new_text = format(val, fmt)
                if new_text != raw:
                    txt.set_text(new_text)
                    reformatted += 1
                continue
            # P1 — graceful degradation when fmt forced to '.0f'
            if fmt == ".0f":
                try:
                    x_pos, y_pos = txt.get_position()
                    col = int(round(x_pos - 0.5))
                    row = int(round(y_pos - 0.5))
                    is_diagonal = (col == row)
                except Exception:
                    is_diagonal = False
                if not is_diagonal and abs(val) < graceful_threshold:
                    txt.remove()
                    removed += 1
                    continue
            new_text = format(val, fmt)
            if new_text != raw:
                txt.set_text(new_text)
                reformatted += 1

    return {"reformatted": reformatted, "removed": removed,
            "skipped_axes": skipped_axes}


def _colorbar_axes(fig, axes):
    return [
        colorbar_ax
        for colorbar_ax in get_non_panel_axes(fig, axes)
        if hasattr(colorbar_ax, "_colorbar")
        and getattr(colorbar_ax, "get_visible", lambda: True)()
    ]


def _colorbar_panel_overlap_issues(fig, axes, renderer):
    panel_boxes = {pid: _axis_layout_bbox(ax, renderer) for pid, ax in axes.items()}
    issues = []
    for colorbar_index, colorbar_ax in enumerate(_colorbar_axes(fig, axes)):
        try:
            colorbar_box = _axis_layout_bbox(colorbar_ax, renderer)
        except Exception:
            continue
        for panel_id, panel_box in panel_boxes.items():
            if colorbar_box.overlaps(panel_box):
                issues.append({
                    "element": "colorbar",
                    "colorbarIndex": colorbar_index,
                    "conflict_panel": panel_id,
                })
    return issues


def _axes_position_bounds(axes):
    positions = []
    for ax in axes:
        try:
            positions.append(ax.get_position())
        except Exception:
            continue
    if not positions:
        return None
    return {
        "x0": min(pos.x0 for pos in positions),
        "y0": min(pos.y0 for pos in positions),
        "x1": max(pos.x1 for pos in positions),
        "y1": max(pos.y1 for pos in positions),
    }


def _compress_panel_axes_right(fig, axes, target_right):
    bounds = _axes_position_bounds(axes.values())
    if not bounds:
        return
    span = max(bounds["x1"] - bounds["x0"], 1e-6)
    target_right = max(bounds["x0"] + 0.18, min(target_right, bounds["x1"]))
    scale = (target_right - bounds["x0"]) / span
    for ax in axes.values():
        pos = ax.get_position()
        new_x0 = bounds["x0"] + (pos.x0 - bounds["x0"]) * scale
        ax.set_position([new_x0, pos.y0, pos.width * scale, pos.height])
    invalidate_layout_cache(fig)


def reflow_colorbars_outside_panels(fig, axes=None, crowdingPlan=None):
    """Move overlapping colorbar axes into reserved non-panel slots before final QA."""
    axes_map = normalize_axes_map(fig, axes)
    plan = {**default_crowding_plan(), **(crowdingPlan or {})}
    if not axes_map or not plan.get("colorbarReflowRequiredOnOverlap", True):
        return 0

    renderer = get_cached_renderer(fig, force=True)
    overlap_issues = _colorbar_panel_overlap_issues(fig, axes_map, renderer)
    if not overlap_issues:
        return 0

    colorbars = _colorbar_axes(fig, axes_map)
    overlap_indices = {
        issue.get("colorbarIndex")
        for issue in overlap_issues
        if issue.get("colorbarIndex") is not None
    }
    if not overlap_indices:
        return 0

    _disable_layout_engine_for_manual_margins(fig)
    try:
        fig.subplots_adjust(right=min(fig.subplotpars.right, float(plan.get("colorbarReservedRight", 0.78))))
    except Exception:
        pass
    invalidate_layout_cache(fig)
    get_cached_renderer(fig, force=True)

    bounds = _axes_position_bounds(axes_map.values())
    if not bounds:
        return 0
    pad = float(plan.get("colorbarReflowPad", 0.04))
    width = float(plan.get("colorbarReflowWidth", 0.025))
    min_height = float(plan.get("colorbarReflowMinHeight", 0.20))
    target_right = min(float(plan.get("colorbarReservedRight", 0.78)), 0.98 - width - pad)
    if bounds["x1"] + pad + width > 0.98:
        _compress_panel_axes_right(fig, axes_map, target_right)
        bounds = _axes_position_bounds(axes_map.values())
        if not bounds:
            return 0

    y0 = max(0.12, bounds["y0"])
    y1 = min(0.92, bounds["y1"])
    height = max(min_height, y1 - y0)
    if y0 + height > 0.94:
        y0 = max(0.08, 0.94 - height)

    moved = 0
    for slot, colorbar_ax in enumerate(colorbars):
        if slot not in overlap_indices:
            continue
        x0 = min(0.98 - width, bounds["x1"] + pad + moved * (width + pad * 0.5))
        if x0 <= bounds["x1"]:
            continue
        try:
            colorbar_ax.set_position([x0, y0, width, height])
            colorbar_ax.set_in_layout(False)
            colorbar_ax.yaxis.set_ticks_position("right")
            colorbar_ax.yaxis.set_label_position("right")
            moved += 1
        except Exception:
            continue

    if moved:
        invalidate_layout_cache(fig)
        get_cached_renderer(fig, force=True)
    return moved


def audit_figure_layout_contract(fig, axes=None, chartPlan=None, journalProfile=None, strict=False):
    """Check final multi-panel layout for cross-panel text, off-canvas text, and poster-scale typography."""
    axes_map = normalize_axes_map(fig, axes)
    plan = chartPlan if isinstance(chartPlan, dict) else {}
    crowdingPlan = {**default_crowding_plan(), **plan.get("crowdingPlan", {})}
    profile = journalProfile or {}
    max_text_size = crowdingPlan.get(
        "maxTextFontSizePt",
        profile.get("max_text_font_size_pt", max(12, profile.get("font_size_panel_label_pt", 8) + 4)),
    )
    max_panel_label_size = crowdingPlan.get(
        "maxPanelLabelFontSizePt",
        profile.get("max_panel_label_font_size_pt", max_text_size),
    )

    renderer = get_cached_renderer(fig, force=True)
    fig_box = fig.bbox
    axes_boxes = {pid: _axis_layout_bbox(ax, renderer) for pid, ax in axes_map.items()}
    cross_panel_overlaps = []
    off_canvas_artists = []
    oversized_text = []
    negative_axes_text = []
    metric_table_data_overlaps = _metric_table_data_overlap_issues(fig, axes_map, renderer)
    colorbar_panel_overlaps = _colorbar_panel_overlap_issues(fig, axes_map, renderer)
    audit_counters = {
        "bboxDataCoverageOverflowCount": 0,
        "textTextOverlapCount": 0,
    }
    text_data_overlaps = _text_data_overlap_issues(
        fig, axes_map, renderer,
        threshold=float(crowdingPlan.get("textDataOverlapThreshold", 0.30)),
        report=audit_counters,
    )
    text_text_overlaps = _text_text_overlap_issues(axes_map, audit_counters, renderer=renderer)

    for panel_id, artist in _iter_layout_artists(axes_map):
        try:
            artist_box = artist.get_window_extent(renderer=renderer)
        except Exception:
            continue
        raw_text = str(getattr(artist, "get_text", lambda: type(artist).__name__)()).strip()
        font_size = float(getattr(artist, "get_fontsize", lambda: 0.0)() or 0.0)
        is_panel_label = raw_text in [chr(code) for code in range(65, 91)] and font_size >= max_text_size
        if is_panel_label and font_size > max_panel_label_size:
            oversized_text.append({"panel": panel_id, "text": raw_text, "fontsize": font_size, "limit": max_panel_label_size})
        elif font_size > max_text_size:
            oversized_text.append({"panel": panel_id, "text": raw_text[:32], "fontsize": font_size, "limit": max_text_size})

        if _bbox_outside(artist_box, fig_box):
            off_canvas_artists.append({"panel": panel_id, "text": raw_text[:32]})

        if crowdingPlan.get("forbidNegativeAxesText", True) and hasattr(artist, "get_position"):
            transform = getattr(artist, "get_transform", lambda: None)()
            try:
                x_pos, y_pos = artist.get_position()
            except Exception:
                x_pos, y_pos = None, None
            if transform is axes_map[panel_id].transAxes and y_pos is not None and (y_pos < -0.02 or y_pos > 1.08):
                negative_axes_text.append({"panel": panel_id, "text": raw_text[:32], "position": [float(x_pos), float(y_pos)]})

        for other_id, other_box in axes_boxes.items():
            if other_id != panel_id and artist_box.overlaps(other_box):
                if _axes_share_visual_panel(axes_boxes.get(panel_id), other_box):
                    continue
                cross_panel_overlaps.append({
                    "element": "text_or_table",
                    "host_panel": panel_id,
                    "conflict_panel": other_id,
                    "text": raw_text[:32],
                })

    axes_union = _bbox_union(list(axes_boxes.values()))
    whitespace_fraction = 1.0
    if axes_union is not None and _bbox_area(fig_box):
        whitespace_fraction = 1.0 - min(1.0, _bbox_area(axes_union) / _bbox_area(fig_box))
    ink_fraction = 0.0
    try:
        get_cached_renderer(fig, force=True)
        rgba = np.asarray(fig.canvas.buffer_rgba())
        if rgba.size:
            visible = rgba[..., 3] > 8 if rgba.shape[-1] == 4 else np.ones(rgba.shape[:2], dtype=bool)
            ink = np.any(rgba[..., :3] < 245, axis=-1) & visible
            ink_fraction = float(np.mean(ink))
    except Exception:
        ink_fraction = 0.0

    failures = []
    if cross_panel_overlaps:
        failures.append("cross_panel_text_or_table_overlap")
    if off_canvas_artists:
        failures.append("off_canvas_text_or_table")
    if oversized_text:
        failures.append("poster_scale_fontsize")
    if negative_axes_text:
        failures.append("negative_axes_text_without_reserved_slot")
    if metric_table_data_overlaps:
        failures.append("metric_table_data_overlap")
    if colorbar_panel_overlaps:
        failures.append("colorbar_panel_overlap")
    if text_data_overlaps:
        failures.append("annotation_text_buried_under_data")
    if text_text_overlaps:
        failures.append("text_text_overlap")
    if audit_counters.get("bboxDataCoverageOverflowCount", 0) > 0:
        failures.append("bbox_oversized_coverage")
    if whitespace_fraction > crowdingPlan.get("maxFigureWhitespaceFraction", 0.82):
        failures.append("figure_whitespace_fraction_above_maximum")
    if ink_fraction < crowdingPlan.get("minFigureInkFraction", 0.04):
        failures.append("figure_ink_fraction_below_minimum")

    report = {
        "layoutContractEnforced": True,
        "layoutContractFailures": failures,
        "audited_axes_count": len(axes_map),
        "crossPanelOverlapIssues": cross_panel_overlaps,
        "metricTableDataOverlapIssues": metric_table_data_overlaps,
        "metricTableDataOverlapCount": len(metric_table_data_overlaps),
        "colorbarPanelOverlapIssues": colorbar_panel_overlaps,
        "colorbarPanelOverlapCount": len(colorbar_panel_overlaps),
        "textDataOverlapIssues": text_data_overlaps,
        "textDataOverlapCount": len(text_data_overlaps),
        "textTextOverlapIssues": text_text_overlaps,
        "textTextOverlapCount": audit_counters.get("textTextOverlapCount", 0),
        "bboxDataCoverageOverflowCount": audit_counters.get("bboxDataCoverageOverflowCount", 0),
        "offCanvasArtistCount": len(off_canvas_artists),
        "offCanvasArtists": off_canvas_artists,
        "oversizedTextCount": len(oversized_text),
        "oversizedText": oversized_text,
        "negativeAxesTextCount": len(negative_axes_text),
        "negativeAxesText": negative_axes_text,
        "figureWhitespaceFraction": whitespace_fraction,
        "figureInkFraction": ink_fraction,
        "maxFigureWhitespaceFraction": crowdingPlan.get("maxFigureWhitespaceFraction", 0.82),
        "minFigureInkFraction": crowdingPlan.get("minFigureInkFraction", 0.04),
    }
    plan.setdefault("crowdingPlan", {}).update(report)
    if strict and failures:
        raise RuntimeError("Figure layout contract failed: " + ", ".join(failures))
    return report


def audit_visual_density_contract(chartPlan, strict=True):
    """Require the planned template/reference motifs to appear in runtime metadata."""
    plan = chartPlan if isinstance(chartPlan, dict) else {}
    visual = plan.setdefault("visualContentPlan", {})
    template_case = plan.get("templateCasePlan", {}) or {}
    applied_enhancements = list(visual.get("appliedEnhancements", []))
    planned_template = {str(m) for m in visual.get("templateMotifs", []) if m}
    applied_template = {str(m) for m in visual.get("templateMotifsApplied", []) if m}
    planned_reference = {str(m) for m in visual.get("visualGrammarMotifs", []) if m}
    applied_reference = {str(m) for m in visual.get("visualGrammarMotifsApplied", []) if m}

    failures = []
    if len(applied_enhancements) < visual.get("minTotalEnhancements", 0):
        failures.append("visual_enhancement_count_below_minimum")
    if visual.get("inPlotExplanatoryLabelCount", 0) < visual.get("minInPlotLabelsPerFigure", 0):
        failures.append("inplot_explanatory_labels_below_minimum")
    if visual.get("referenceMotifsRequired", True):
        if visual.get("referenceMotifCount", 0) < visual.get("minReferenceMotifsPerFigure", 0):
            failures.append("reference_visual_motif_count_below_minimum")
        if visual.get("exactMotifCoverageRequired", True) and planned_reference - applied_reference:
            failures.append("missing_required_visual_grammar_motifs")
    template_required = (
        visual.get("templateMotifsRequired", False)
        or visual.get("exactTemplateReplicationRequired", False)
        or template_case.get("exactTemplateReplicationRequired", False)
        or template_case.get("templateMatchMode") == "clone_when_known"
    )
    if template_required:
        if visual.get("templateMotifCount", 0) < visual.get("minTemplateMotifsPerFigure", 0):
            failures.append("template_visual_motif_count_below_minimum")
        if visual.get("exactMotifCoverageRequired", True) and planned_template - applied_template:
            failures.append("missing_required_template_motifs")

    report = {
        "visualDensityContractEnforced": True,
        "contentDensityFailures": failures,
        "missingTemplateMotifs": sorted(planned_template - applied_template),
        "missingVisualGrammarMotifs": sorted(planned_reference - applied_reference),
        "visualEnhancementCount": len(applied_enhancements),
        "templateMotifCount": visual.get("templateMotifCount", 0),
        "referenceMotifCount": visual.get("referenceMotifCount", 0),
    }
    visual.update(report)
    if strict and failures:
        raise RuntimeError("Visual density contract failed: " + ", ".join(failures))
    return report


def _reflow_legend_with_height_increase(fig, handles, labels, legend_labels, occupied_axes,
                                        crowdingPlan, journalProfile, fontsize):
    max_mult = crowdingPlan.get("legendMaxHeightMultiplier", 1.3)
    base_height = fig.get_figheight()
    for mult in [1.1, 1.2, 1.3]:
        if mult > max_mult:
            break
        fig.set_figheight(base_height * mult)
        invalidate_layout_cache(fig)
        get_cached_renderer(fig, force=True)
        for mode in _center_legend_modes(crowdingPlan.get("legendPlacementPriority")):
            for existing in list(fig.legends):
                existing.remove()
            legend = create_figure_legend(
                fig,
                handles,
                legend_labels,
                mode,
                fontsize,
                ncol=1,
                frame_style=crowdingPlan.get("legendFrameStyle"),
                anchor_y=crowdingPlan.get("legendBottomAnchorY", CROWDING_DEFAULTS["legendBottomAnchorY"]),
            )
            ok = enforce_non_overlapping_legend(
                fig,
                legend,
                mode,
                occupied_axes,
                retry_limit=3,
                crowdingPlan=crowdingPlan,
            )
            if ok:
                return legend, mode
    for existing in list(fig.legends):
        existing.remove()
    fig.set_figheight(base_height)
    return None, None


def _disable_layout_engine_for_manual_margins(fig):
    """Matplotlib ignores subplots_adjust while constrained layout owns the figure."""
    try:
        if hasattr(fig, "set_layout_engine"):
            fig.set_layout_engine(None)
    except Exception:
        pass
    try:
        fig.set_constrained_layout(False)
    except Exception:
        pass


def _legend_font_size(crowdingPlan=None, journalProfile=None):
    plan = crowdingPlan if isinstance(crowdingPlan, dict) else {}
    profile = journalProfile if isinstance(journalProfile, dict) else {}
    return float(plan.get("legendFontSizePt", profile.get("legend_font_size_pt", 7)))


def _bottom_margin_for_legend(fig, legend=None, crowdingPlan=None):
    plan = {**CROWDING_DEFAULTS, **(crowdingPlan or {})}
    if legend is None:
        return float(plan.get("legendBottomMarginNoLegend", 0.05))
    legend_box = _bbox_in_figure_coords(fig, legend)
    target = float(legend_box.y1) + 0.018
    lower = float(plan.get("legendBottomMarginMin", 0.06))
    upper = float(plan.get("legendBottomMarginMax", CROWDING_DEFAULTS["legendBottomMarginMax"]))
    return min(upper, max(lower, target))


def apply_subplot_margins(fig, legend_mode, has_colorbar=False, legend=None, crowdingPlan=None):
    legend_mode = _normalize_legend_mode(legend_mode)
    _disable_layout_engine_for_manual_margins(fig)
    invalidate_layout_cache(fig)
    get_cached_renderer(fig, force=True)
    subplotpars = fig.subplotpars
    left = max(subplotpars.left, 0.16)
    top = min(subplotpars.top, 0.95)
    bottom = _bottom_margin_for_legend(fig, legend, crowdingPlan)
    right = min(subplotpars.right, 0.95)

    if has_colorbar:
        right = min(right, 0.78)

    if legend is not None:
        legend_box = _bbox_in_figure_coords(fig, legend)
        if legend_mode == "bottom_center":
            bottom = _bottom_margin_for_legend(fig, legend, crowdingPlan)
        else:
            top = min(top, max(0.26, legend_box.y0 - 0.055))

    if right <= left + 0.12:
        right = left + 0.12
    if top <= bottom + 0.12:
        top = min(0.95, bottom + 0.12)

    if legend is not None:
        renderer = get_cached_renderer(fig)
        legend_box = legend.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
        if legend_mode == "bottom_center":
            bottom = _bottom_margin_for_legend(fig, legend, crowdingPlan)
        else:
            top = min(top, max(0.26, legend_box.y0 - 0.055))

    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)
    invalidate_layout_cache(fig)


def _unique_modes(modes):
    out = []
    for mode in modes:
        if mode and mode not in out:
            out.append(mode)
    return out


def _normalize_legend_mode(mode):
    return "bottom_center"


def _center_legend_modes(modes=None):
    return ["bottom_center"]


def _legend_column_options(label_count, legend_mode, max_columns):
    candidates = [
        min(label_count, max_columns),
        min(label_count, 4),
        min(label_count, 3),
        min(label_count, 2),
        1,
    ]
    return [n for n in dict.fromkeys(candidates) if n >= 1]


def _apply_legend_frame_style(legend, frame_style=None):
    style = {
        "facecolor": "#FFFFFF",
        "edgecolor": "#cccccc",
        "linewidth": 0.55,
        "alpha": 1.0,
        "pad": 0.4,
        "boxstyle": "round",
    }
    style.update(frame_style or {})
    frame = legend.get_frame()
    frame.set_visible(True)
    frame.set_facecolor(style["facecolor"])
    frame.set_edgecolor(style["edgecolor"])
    frame.set_linewidth(style["linewidth"])
    frame.set_alpha(style["alpha"])
    if hasattr(frame, "set_boxstyle"):
        try:
            frame.set_boxstyle(f"{style.get('boxstyle', 'round')},pad={style['pad']}")
        except Exception:
            frame.set_boxstyle(f"round,pad={style['pad']}")
    legend.set_gid("scifig_shared_legend")
    legend.set_zorder(1000)
    return True


def create_figure_legend(fig, handles, labels, legend_mode, fontsize, ncol=1, frame_style=None, anchor_y=None):
    invalidate_layout_cache(fig)
    legend_mode = _normalize_legend_mode(legend_mode)
    common = {
        "ncol": ncol,
        "frameon": True,
        "fancybox": False,
        "fontsize": fontsize,
        "borderaxespad": 0.0,
        "borderpad": 0.4,
        "handlelength": 1.2,
        "handletextpad": 0.4,
        "labelspacing": 0.35,
        "columnspacing": 0.8,
    }
    anchor_y = CROWDING_DEFAULTS["legendBottomAnchorY"] if anchor_y is None else float(anchor_y)
    legend = fig.legend(handles, labels, loc="lower center",
                        bbox_to_anchor=(0.5, anchor_y), **common)
    _apply_legend_frame_style(legend, frame_style)
    return legend


def enforce_non_overlapping_legend(fig, legend, legend_mode, occupied_axes, has_colorbar=False, retry_limit=5, crowdingPlan=None):
    plan = {**CROWDING_DEFAULTS, **(crowdingPlan or {})}
    for _ in range(retry_limit):
        apply_subplot_margins(fig, legend_mode, has_colorbar=has_colorbar, legend=legend, crowdingPlan=plan)
        if not legend_overlaps_axes(fig, legend, occupied_axes):
            return True

        subplotpars = fig.subplotpars
        if _normalize_legend_mode(legend_mode) == "bottom_center":
            next_bottom = min(
                float(plan.get("legendBottomMarginMax", CROWDING_DEFAULTS["legendBottomMarginMax"])),
                subplotpars.top - 0.12,
                subplotpars.bottom + 0.04,
            )
            if next_bottom <= subplotpars.bottom + 1e-6:
                break
            plan["legendBottomMarginMin"] = max(
                float(plan.get("legendBottomMarginMin", CROWDING_DEFAULTS["legendBottomMarginMin"])),
                next_bottom,
            )
            fig.subplots_adjust(bottom=max(subplotpars.bottom, next_bottom))
        else:
            next_top = max(subplotpars.bottom + 0.12, subplotpars.top - 0.04)
            fig.subplots_adjust(top=next_top)
        invalidate_layout_cache(fig)

    if not legend_overlaps_axes(fig, legend, occupied_axes):
        return True

    invalidate_layout_cache(fig)
    apply_subplot_margins(fig, legend_mode, has_colorbar=has_colorbar, legend=legend, crowdingPlan=plan)
    return not legend_overlaps_axes(fig, legend, occupied_axes)


def place_shared_legend(fig, axes, occupied_axes, crowdingPlan, journalProfile, has_colorbar=False, handles=None, labels=None):
    if handles is None or labels is None:
        handles, labels = collect_legend_entries(axes)
    empty_info = {
        "legendScope": "figure",
        "legendLabelsShortened": False,
        "legendNColumns": 0,
        "legendOutsidePlotArea": True,
        "legendAllowedModes": ["bottom_center"],
        "legendCenterPlacementOnly": True,
        "legendFrameApplied": False,
        "forbidOutsideRightLegend": True,
    }
    if not handles:
        return None, _normalize_legend_mode(crowdingPlan.get("legendMode", "bottom_center")), empty_info

    requested_mode = _normalize_legend_mode(crowdingPlan.get("legendMode", "bottom_center"))
    priority = crowdingPlan.get("legendPlacementPriority") or ["bottom_center"]
    allowed_modes = _center_legend_modes(crowdingPlan.get("legendAllowedModes"))
    candidate_modes = _center_legend_modes(priority + [requested_mode] + allowed_modes)
    fontsize = _legend_font_size(crowdingPlan, journalProfile)
    max_label_chars = crowdingPlan.get("legendLabelMaxChars", 32)
    max_columns = crowdingPlan.get("maxLegendColumns", 6)
    frame_style = crowdingPlan.get("legendFrameStyle")
    legend_labels, labels_shortened = shorten_legend_labels(labels, max_label_chars)
    info = {
        "legendScope": "figure",
        "legendLabelsShortened": labels_shortened,
        "legendNColumns": 0,
        "legendOutsidePlotArea": False,
        "legendAllowedModes": allowed_modes,
        "legendCenterPlacementOnly": True,
        "legendFrameApplied": False,
        "legendFrameStyle": frame_style or CROWDING_DEFAULTS["legendFrameStyle"],
        "forbidOutsideRightLegend": True,
    }

    for mode in candidate_modes:
        for ncol in _legend_column_options(len(legend_labels), mode, max_columns):
            for existing in list(fig.legends):
                existing.remove()
            invalidate_layout_cache(fig)
            legend = create_figure_legend(
                fig,
                handles,
                legend_labels,
                mode,
                fontsize,
                ncol=ncol,
                frame_style=frame_style,
                anchor_y=crowdingPlan.get("legendBottomAnchorY", CROWDING_DEFAULTS["legendBottomAnchorY"]),
            )
            ok = enforce_non_overlapping_legend(
                fig,
                legend,
                mode,
                occupied_axes,
                has_colorbar=has_colorbar,
                retry_limit=crowdingPlan.get("renderRetryLimit", 5),
                crowdingPlan=crowdingPlan,
            )
            if ok:
                info["legendNColumns"] = ncol
                info["legendOutsidePlotArea"] = True
                info["legendFrameApplied"] = legend.get_frame().get_visible()
                return legend, mode, info

    for existing in list(fig.legends):
        existing.remove()
    invalidate_layout_cache(fig)
    info["legendOutsidePlotArea"] = False
    info["layoutReflowNeeded"] = True
    return None, requested_mode, info


def apply_crowding_management(fig, axes, chartPlan, journalProfile):
    axes = normalize_axes_map(fig, axes)
    crowdingPlan = {**default_crowding_plan(), **chartPlan.get("crowdingPlan", {})}
    panelBlueprint = chartPlan.get("panelBlueprint", {})

    dropped_direct_labels = 0
    for panel_id, ax in axes.items():
        if panel_id == "A":
            dropped_direct_labels += trim_excess_text_annotations(ax, crowdingPlan.get("maxDirectLabelsHero"))
        else:
            dropped_direct_labels += trim_excess_text_annotations(ax, crowdingPlan.get("maxDirectLabelsSupport"))
        trim_pvalue_annotations(ax, crowdingPlan.get("maxBracketGroups", 2))

    handles, labels = collect_legend_entries(axes)
    figure_handles, figure_labels = collect_figure_legend_entries(fig)
    handles, labels = dedupe_handles_labels(handles + figure_handles, labels + figure_labels)
    legend_input_entry_count = len(labels)
    for existing in list(fig.legends):
        existing.remove()
    removed_axis_legends = remove_axis_legends(axes)
    remaining_axis_legends = count_axis_legends(axes)
    legend = None
    legend_mode_used = "none"
    legend_info = {
        "legendScope": "figure",
        "legendLabelsShortened": False,
        "legendNColumns": 0,
        "legendOutsidePlotArea": True,
        "legendAllowedModes": ["bottom_center"],
        "legendCenterPlacementOnly": True,
        "legendFrameApplied": False,
        "legendFrameStyle": crowdingPlan.get("legendFrameStyle", CROWDING_DEFAULTS["legendFrameStyle"]),
        "forbidOutsideRightLegend": True,
    }
    shared_colorbar_applied = False
    shared_colorbar_mappable = None
    if panelBlueprint.get("sharedColorbar", False):
        remove_extra_axes(fig, axes)
        for ax in axes.values():
            shared_colorbar_mappable = find_first_mappable(ax)
            if shared_colorbar_mappable is not None:
                break
        if shared_colorbar_mappable is not None:
            shared_colorbar_applied = True
            visual_plan = chartPlan.setdefault("visualContentPlan", {})
            _visual_count(visual_plan, "colorbarSlotCount")
            if "correlation_evidence_matrix" in visual_plan.get("templateMotifs", []):
                _record_template_motif(visual_plan, "correlation_evidence_matrix")

    occupied_axes = list(axes.values()) + get_non_panel_axes(fig, axes)
    if handles:
        legend, legend_mode_used, legend_info = place_shared_legend(
            fig,
            axes,
            occupied_axes,
            crowdingPlan,
            journalProfile,
            has_colorbar=shared_colorbar_applied,
            handles=handles,
            labels=labels,
        )

    if legend_info.get("layoutReflowNeeded") and crowdingPlan.get("legendExternalHardLimit", True):
        fontsize = _legend_font_size(crowdingPlan, journalProfile)
        max_label_chars = crowdingPlan.get("legendLabelMaxChars", 32)
        legend_labels, _ = shorten_legend_labels(labels, max_label_chars)
        reflow_legend, reflow_mode = _reflow_legend_with_height_increase(
            fig, handles, labels, legend_labels, occupied_axes, crowdingPlan, journalProfile, fontsize)
        if reflow_legend is not None:
            legend = reflow_legend
            legend_mode_used = reflow_mode
            legend_info["legendOutsidePlotArea"] = True
            legend_info["layoutReflowNeeded"] = False
            legend_info["heightIncreased"] = True
            legend_info["legendFrameApplied"] = legend.get_frame().get_visible()
        else:
            legend_info["legendOutsidePlotArea"] = False

    apply_subplot_margins(
        fig,
        legend_mode_used,
        has_colorbar=shared_colorbar_applied,
        legend=legend,
        crowdingPlan=crowdingPlan,
    )
    if chartPlan.get("visualContentPlan", {}).get("outsideLayoutElements"):
        fig.subplots_adjust(right=min(fig.subplotpars.right, 0.78))
    if shared_colorbar_applied and shared_colorbar_mappable is not None:
        fig.colorbar(shared_colorbar_mappable, ax=list(axes.values()), shrink=0.6, pad=0.06)

    final_legend_overlap = False
    if legend is not None:
        occupied_axes = list(axes.values()) + get_non_panel_axes(fig, axes)
        invalidate_layout_cache(fig)
        if legend_overlaps_axes(fig, legend, occupied_axes):
            ok = enforce_non_overlapping_legend(
                fig,
                legend,
                legend_mode_used,
                occupied_axes,
                has_colorbar=shared_colorbar_applied,
                retry_limit=crowdingPlan.get("renderRetryLimit", 5),
                crowdingPlan=crowdingPlan,
            )
            final_legend_overlap = not ok
            legend_info["legendOutsidePlotArea"] = ok

    if remaining_axis_legends:
        removed_axis_legends += remove_axis_legends(axes)
    remaining_axis_legends = count_axis_legends(axes)
    get_cached_renderer(fig, force=True)
    overlap_issues = elements_overlap_axes(fig, axes)
    if final_legend_overlap:
        overlap_issues.append({"element": "scifig_shared_legend", "host_panel": "figure", "conflict_panel": "plot_area"})
    if overlap_issues:
        for issue in overlap_issues:
            if issue.get("host_panel") not in axes:
                continue
            for child in list(axes[issue["host_panel"]].get_children()):
                gid = getattr(child, "get_gid", lambda: None)()
                if gid == issue["element"]:
                    if gid == "scifig_metric_box":
                        if hasattr(child, "set_position"):
                            child.set_position((0.98, 0.98))
                        if hasattr(child, "set_ha"):
                            child.set_ha("right")
                        if hasattr(child, "set_va"):
                            child.set_va("top")
                        if hasattr(child, "set_clip_on"):
                            child.set_clip_on(True)
                        continue
                    current_x = getattr(child, '_x', None) or 1.015
                    if hasattr(child, 'set_position'):
                        child.set_position((current_x + 0.05, getattr(child, '_y', 1.0)))
                    elif hasattr(child, 'set_x'):
                        child.set_x(current_x + 0.05)
        invalidate_layout_cache(fig)

    crowdingPlan["droppedDirectLabelCount"] = dropped_direct_labels
    crowdingPlan["legendScope"] = "figure"
    crowdingPlan["legendMode"] = "bottom_center"
    crowdingPlan["legendModeUsed"] = legend_mode_used
    crowdingPlan["legendAllowedModes"] = ["bottom_center"]
    crowdingPlan["legendPlacementPriority"] = _center_legend_modes(crowdingPlan.get("legendPlacementPriority"))
    crowdingPlan["legendCenterPlacementOnly"] = True
    crowdingPlan["forbidOutsideRightLegend"] = True
    crowdingPlan["legendFrame"] = True
    crowdingPlan["legendFrameApplied"] = legend_info.get("legendFrameApplied", False)
    crowdingPlan["legendFrameStyle"] = legend_info.get("legendFrameStyle", CROWDING_DEFAULTS["legendFrameStyle"])
    crowdingPlan["axisLegendRemovedCount"] = removed_axis_legends
    crowdingPlan["axisLegendRemainingCount"] = remaining_axis_legends
    crowdingPlan["legendInputEntryCount"] = legend_input_entry_count
    crowdingPlan["figureLegendCount"] = len(fig.legends)
    crowdingPlan["legendNColumns"] = legend_info.get("legendNColumns", 0)
    crowdingPlan["legendLabelsShortened"] = legend_info.get("legendLabelsShortened", False)
    crowdingPlan["legendOutsidePlotArea"] = legend_info.get("legendOutsidePlotArea", True)
    simplifications = list(crowdingPlan.get("simplificationsApplied", []))
    if legend is not None:
        simplifications.append("figure_level_shared_legend")
        simplifications.append("framed_shared_legend")
    if removed_axis_legends:
        simplifications.append(f"axis_legends_removed:{removed_axis_legends}")
    if remaining_axis_legends:
        simplifications.append(f"axis_legends_remaining:{remaining_axis_legends}")
    if legend_info.get("legendLabelsShortened", False):
        simplifications.append("legend_labels_shortened")
    if dropped_direct_labels:
        simplifications.append(f"direct_labels_trimmed:{dropped_direct_labels}")
    crowdingPlan["simplificationsApplied"] = list(dict.fromkeys(simplifications))
    if overlap_issues:
        crowdingPlan["overlapIssues"] = overlap_issues
    chartPlan["crowdingPlan"] = crowdingPlan

    return {
        "droppedDirectLabelCount": dropped_direct_labels,
        "legendModeUsed": legend_mode_used,
        "sharedColorbarApplied": shared_colorbar_applied,
        "hasFigureLegend": legend is not None,
        "axisLegendRemovedCount": removed_axis_legends,
        "axisLegendRemainingCount": remaining_axis_legends,
        "legendInputEntryCount": legend_input_entry_count,
        "figureLegendCount": len(fig.legends),
        "legendOutsidePlotArea": legend_info.get("legendOutsidePlotArea", True),
        "legendLabelsShortened": legend_info.get("legendLabelsShortened", False),
        "legendAllowedModes": crowdingPlan["legendAllowedModes"],
        "legendCenterPlacementOnly": crowdingPlan["legendCenterPlacementOnly"],
        "legendFrameApplied": crowdingPlan["legendFrameApplied"],
        "forbidOutsideRightLegend": crowdingPlan["forbidOutsideRightLegend"],
        "layoutReflowApplied": legend_info.get("layoutReflowNeeded", False) is False and legend_info.get("heightIncreased", False),
        "overlapIssues": overlap_issues,
    }


def _sanitize_svg_component_id(value):
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", ".", str(value or "component")).strip(".")
    if not safe:
        safe = "component"
    if safe[0].isdigit():
        safe = "id." + safe
    return safe


def _set_gid_if_missing(artist, gid):
    if artist is None:
        return None
    gid = _sanitize_svg_component_id(gid)
    try:
        current = artist.get_gid()
        if not current:
            artist.set_gid(gid)
            return gid
        return str(current)
    except Exception:
        return None


def assign_editable_svg_ids(fig, axes=None, figure_id="figure1"):
    """Assign stable SVG IDs to movable figure components before SVG export."""
    axes_map = normalize_axes_map(fig, axes)
    assigned = []
    fig_gid = _set_gid_if_missing(fig, f"scifig.figure.{figure_id}")
    if fig_gid:
        assigned.append(fig_gid)

    suptitle = getattr(fig, "_suptitle", None)
    if suptitle is not None and suptitle.get_text():
        gid = _set_gid_if_missing(suptitle, "scifig.title.main")
        if gid:
            assigned.append(gid)

    for panel_id, ax in axes_map.items():
        panel_key = _sanitize_svg_component_id(panel_id)
        gid = _set_gid_if_missing(ax, f"scifig.panel.{panel_key}.axes")
        if gid:
            assigned.append(gid)
        title_specs = [
            ("title.center", getattr(ax, "title", None)),
            ("title.left", getattr(ax, "_left_title", None)),
            ("title.right", getattr(ax, "_right_title", None)),
        ]
        for role, title in title_specs:
            if title is not None and title.get_text():
                gid = _set_gid_if_missing(title, f"scifig.panel.{panel_key}.{role}")
                if gid:
                    assigned.append(gid)
        label_specs = [
            ("xlabel", getattr(ax.xaxis, "label", None)),
            ("ylabel", getattr(ax.yaxis, "label", None)),
        ]
        for role, label in label_specs:
            if label is not None and label.get_text():
                gid = _set_gid_if_missing(label, f"scifig.panel.{panel_key}.{role}")
                if gid:
                    assigned.append(gid)
        for index, text in enumerate(getattr(ax, "texts", []), start=1):
            if not text.get_text():
                continue
            current = text.get_gid()
            if current:
                gid = str(current)
            else:
                gid = _set_gid_if_missing(text, f"scifig.panel.{panel_key}.annotation.{index:03d}")
            if gid:
                assigned.append(gid)
        legend = ax.get_legend()
        if legend is not None:
            gid = _set_gid_if_missing(legend, f"scifig.panel.{panel_key}.legend")
            if gid:
                assigned.append(gid)

    for index, legend in enumerate(getattr(fig, "legends", []), start=1):
        gid = _set_gid_if_missing(legend, "scifig.legend.bottom" if index == 1 else f"scifig.legend.figure.{index:03d}")
        if gid:
            assigned.append(gid)
        for text_index, text in enumerate(legend.get_texts(), start=1):
            text_gid = _set_gid_if_missing(text, f"{gid}.text.{text_index:03d}" if gid else f"scifig.legend.text.{text_index:03d}")
            if text_gid:
                assigned.append(text_gid)

    return {"assignedSvgIdCount": len(set(assigned)), "assignedSvgIds": sorted(set(assigned))}


def _artist_bbox_record(fig, renderer, artist, component_id, role, panel_id=None, editable=True):
    try:
        if artist is None or not artist.get_visible():
            return None
        bbox = artist.get_window_extent(renderer=renderer)
    except Exception:
        return None
    if bbox is None or bbox.width <= 0 or bbox.height <= 0:
        return None
    fig_bbox = fig.bbox
    width = float(fig_bbox.width) or 1.0
    height = float(fig_bbox.height) or 1.0
    return {
        "id": str(component_id),
        "role": role,
        "panelId": panel_id,
        "manualMoveAllowed": bool(editable),
        "bboxPixels": {
            "x0": float(bbox.x0),
            "y0": float(bbox.y0),
            "x1": float(bbox.x1),
            "y1": float(bbox.y1),
            "width": float(bbox.width),
            "height": float(bbox.height),
        },
        "bboxFigureFraction": {
            "x0": float((bbox.x0 - fig_bbox.x0) / width),
            "y0": float((bbox.y0 - fig_bbox.y0) / height),
            "x1": float((bbox.x1 - fig_bbox.x0) / width),
            "y1": float((bbox.y1 - fig_bbox.y0) / height),
            "centerX": float(((bbox.x0 + bbox.x1) * 0.5 - fig_bbox.x0) / width),
            "centerY": float(((bbox.y0 + bbox.y1) * 0.5 - fig_bbox.y0) / height),
        },
    }


def _manifest_component_centered(components, roles, tolerance=0.035):
    if isinstance(roles, str):
        roles = {roles}
    else:
        roles = set(roles)
    matches = [item for item in components if item.get("role") in roles]
    if not matches:
        return None
    return all(abs(item.get("bboxFigureFraction", {}).get("centerX", 0.5) - 0.5) <= tolerance for item in matches)


def build_editable_svg_manifest(fig, axes=None, figure_id="figure1", chartPlan=None):
    """Build a component manifest for user-editable SVG post-processing."""
    axes_map = normalize_axes_map(fig, axes)
    id_report = assign_editable_svg_ids(fig, axes_map, figure_id=figure_id)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    components = []

    suptitle = getattr(fig, "_suptitle", None)
    if suptitle is not None and suptitle.get_text():
        component_id = suptitle.get_gid() or "scifig.title.main"
        record = _artist_bbox_record(fig, renderer, suptitle, component_id, "main_title", editable=True)
        if record:
            components.append(record)

    for panel_id, ax in axes_map.items():
        ax_gid = ax.get_gid() or f"scifig.panel.{panel_id}.axes"
        record = _artist_bbox_record(fig, renderer, ax, ax_gid, "panel_axes", panel_id=panel_id, editable=False)
        if record:
            components.append(record)
        title_specs = [
            ("panel_title", getattr(ax, "title", None)),
            ("panel_title_left", getattr(ax, "_left_title", None)),
            ("panel_title_right", getattr(ax, "_right_title", None)),
        ]
        for role, title in title_specs:
            if title is not None and title.get_text():
                record = _artist_bbox_record(fig, renderer, title, title.get_gid() or role, role, panel_id=panel_id, editable=True)
                if record:
                    components.append(record)
        for role, label in (("x_axis_label", getattr(ax.xaxis, "label", None)), ("y_axis_label", getattr(ax.yaxis, "label", None))):
            if label is not None and label.get_text():
                record = _artist_bbox_record(fig, renderer, label, label.get_gid() or role, role, panel_id=panel_id, editable=True)
                if record:
                    components.append(record)
        for text in getattr(ax, "texts", []):
            if not text.get_text():
                continue
            gid = text.get_gid() or "scifig.annotation"
            role = "panel_label" if gid in ("scifig_panel_label", "scifig.panel_label") or "panel.label" in gid else "annotation"
            record = _artist_bbox_record(fig, renderer, text, gid, role, panel_id=panel_id, editable=True)
            if record:
                components.append(record)
        legend = ax.get_legend()
        if legend is not None:
            record = _artist_bbox_record(fig, renderer, legend, legend.get_gid() or f"scifig.panel.{panel_id}.legend", "axis_legend", panel_id=panel_id, editable=True)
            if record:
                components.append(record)

    for legend in getattr(fig, "legends", []):
        legend_id = legend.get_gid() or "scifig.legend.bottom"
        record = _artist_bbox_record(fig, renderer, legend, legend_id, "bottom_legend", editable=True)
        if record:
            components.append(record)

    figure_width_px = float(fig.bbox.width)
    figure_height_px = float(fig.bbox.height)
    manifest = {
        "figureId": figure_id,
        "editableSvgContractVersion": 1,
        "canonicalSource": "editable_svg",
        "figureSizePixels": {"width": figure_width_px, "height": figure_height_px},
        "manualEditPolicy": {
            "allowedRoles": ["main_title", "panel_title", "panel_label", "annotation", "bottom_legend", "axis_label"],
            "lockedRoles": ["panel_axes", "data_layer"],
        },
        "componentCount": len(components),
        "components": components,
        "titleCentered": _manifest_component_centered(components, "main_title"),
        "bottomLegendCentered": _manifest_component_centered(components, "bottom_legend", tolerance=0.08),
        "assignedSvgIdCount": id_report["assignedSvgIdCount"],
        "chartPlanSummary": {
            "primaryChart": (chartPlan or {}).get("primaryChart") if isinstance(chartPlan, dict) else None,
            "secondaryCharts": (chartPlan or {}).get("secondaryCharts", []) if isinstance(chartPlan, dict) else [],
        },
    }
    return manifest


def _read_json_report(path, default):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _upsert_figure_record(path, record, collection_key):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _read_json_report(path, {collection_key: []})
    if isinstance(payload, list):
        payload = {collection_key: payload}
    if not isinstance(payload, dict):
        payload = {collection_key: []}
    records = [item for item in payload.get(collection_key, []) if item.get("figureId") != record.get("figureId")]
    records.append(record)
    payload[collection_key] = records
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return payload


def _svg_text_is_editable(svg_path):
    try:
        root = ET.parse(svg_path).getroot()
    except Exception:
        text = Path(svg_path).read_text(encoding="utf-8", errors="ignore")
        return "<text" in text
    return any(str(element.tag).endswith("text") for element in root.iter())


def _svg_id_set(svg_path):
    ids = set()
    try:
        root = ET.parse(svg_path).getroot()
        for element in root.iter():
            value = element.attrib.get("id")
            if value:
                ids.add(value)
    except Exception:
        text = Path(svg_path).read_text(encoding="utf-8", errors="ignore")
        ids.update(re.findall(r'\bid="([^"]+)"', text))
    return ids


def find_svg_renderer():
    """Find a renderer that can rasterize SVG into PNG and optionally PDF."""
    for name in ("inkscape", "resvg", "rsvg-convert"):
        exe = shutil.which(name)
        if exe:
            return {"name": name, "executable": exe}
    try:
        import cairosvg  # noqa: F401
        return {"name": "cairosvg", "executable": "python-module"}
    except Exception:
        return None


def _run_svg_renderer(svg_path, out_path, fmt, dpi):
    renderer = find_svg_renderer()
    if not renderer:
        raise RuntimeError("No SVG renderer found; install Inkscape, resvg, rsvg-convert, or cairosvg.")
    svg_path = Path(svg_path)
    out_path = Path(out_path)
    fmt = fmt.lower()
    name = renderer["name"]
    if name == "inkscape":
        command = [
            renderer["executable"],
            str(svg_path),
            f"--export-type={fmt}",
            f"--export-filename={out_path}",
        ]
        if fmt in ("png", "tiff"):
            command.append(f"--export-dpi={dpi}")
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "Inkscape export failed").strip())
    elif name == "resvg":
        if fmt != "png":
            raise RuntimeError("resvg fallback supports PNG only; install Inkscape or cairosvg for PDF.")
        command = [renderer["executable"], "--dpi", str(int(dpi)), str(svg_path), str(out_path)]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "resvg export failed").strip())
    elif name == "rsvg-convert":
        command = [renderer["executable"], "-f", fmt, "-o", str(out_path), str(svg_path)]
        if fmt in ("png", "tiff"):
            command[1:1] = ["-d", str(int(dpi)), "-p", str(int(dpi))]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "rsvg-convert export failed").strip())
    elif name == "cairosvg":
        import cairosvg
        if fmt == "png":
            cairosvg.svg2png(url=str(svg_path), write_to=str(out_path), dpi=float(dpi))
        elif fmt == "pdf":
            cairosvg.svg2pdf(url=str(svg_path), write_to=str(out_path), dpi=float(dpi))
        else:
            raise RuntimeError(f"cairosvg fallback does not support {fmt!r}.")
    if not out_path.exists() or out_path.stat().st_size < 512:
        raise RuntimeError(f"SVG renderer did not create a usable {fmt.upper()} file: {out_path}")
    return renderer


def _build_svg_render_qa(figure_id, svg_path, manifest, requested_formats, renderer=None, outputs=None,
                         error=None, source_label="editable_svg", derivative_sources=None, warnings=None):
    svg_path = Path(svg_path)
    ids = _svg_id_set(svg_path) if svg_path.exists() else set()
    expected_ids = {
        component.get("id")
        for component in manifest.get("components", [])
        if component.get("id") and component.get("manualMoveAllowed", True)
    }
    missing_ids = sorted(expected_ids - ids)
    editable_text = _svg_text_is_editable(svg_path) if svg_path.exists() else False
    outputs = outputs or {}
    derivative_sources = derivative_sources or {}
    warnings = list(warnings or [])
    qa = {
        "figureId": figure_id,
        "editableSvgPath": str(svg_path),
        "canonicalSource": source_label,
        "requestedFormats": list(requested_formats),
        "renderer": renderer,
        "outputs": outputs,
        "editableTextCheck": "passed" if editable_text else "failed",
        "componentIdsPresent": not missing_ids,
        "missingComponentIds": missing_ids,
        "titleCentered": manifest.get("titleCentered"),
        "bottomLegendCentered": manifest.get("bottomLegendCentered"),
        "pngSource": derivative_sources.get("png") if "png" in outputs else None,
        "pdfSource": derivative_sources.get("pdf") if "pdf" in outputs else None,
        "editableSvgWarnings": warnings,
        "hardFail": False,
        "failures": [],
    }
    if not svg_path.exists() or svg_path.stat().st_size < 1024:
        qa["failures"].append("editable_svg_missing_or_tiny")
    if not editable_text:
        qa["failures"].append("svg_text_not_editable")
    if missing_ids:
        qa["failures"].append("manifest_component_ids_missing_from_svg")
    for fmt, path in outputs.items():
        if not path:
            continue
        artifact = Path(path)
        if artifact.suffix and (not artifact.exists() or artifact.stat().st_size < 512):
            qa["failures"].append(f"{fmt}_missing_or_tiny")
    if error:
        qa["failures"].append(str(error))
    qa["hardFail"] = bool(qa["failures"])
    return qa


def export_editable_svg_bundle(fig, figure_id="figure1", output_dir="output", axes=None, chartPlan=None,
                               raster_dpi=300, normalized_formats=None, strict=True):
    """Export editable SVG as the canonical source and derive strict PNG from it."""
    requested = list(normalized_formats or ["pdf", "svg"])
    requested = [str(fmt).lower().lstrip(".") for fmt in requested]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"svg.fonttype": "none"})

    manifest = build_editable_svg_manifest(fig, axes=axes, figure_id=figure_id, chartPlan=chartPlan)
    editable_svg = output_dir / f"{figure_id}.editable.svg"
    canonical_svg = output_dir / f"{figure_id}.svg"
    fig.savefig(editable_svg, format="svg", facecolor="white", edgecolor="none", bbox_inches=None)
    shutil.copyfile(editable_svg, canonical_svg)

    outputs = {"editable_svg": str(editable_svg), "svg": str(canonical_svg)}
    derivative_sources = {"svg": "editable_svg", "editable_svg": "editable_svg"}
    render_warnings = []
    renderer_info = None
    render_error = None
    for fmt in requested:
        if fmt == "svg":
            continue
        if fmt in ("png", "pdf", "tiff"):
            out_path = output_dir / f"{figure_id}.{fmt}"
            try:
                renderer_info = _run_svg_renderer(editable_svg, out_path, fmt, raster_dpi)
                outputs[fmt] = str(out_path)
                derivative_sources[fmt] = "editable_svg"
            except Exception as exc:
                if fmt == "pdf":
                    fig.savefig(out_path, format="pdf", facecolor="white", edgecolor="none", bbox_inches=None)
                    outputs[fmt] = str(out_path)
                    derivative_sources[fmt] = "matplotlib_pdf_fallback"
                    render_warnings.append(f"pdf_from_svg_renderer_unavailable: {exc}")
                    continue
                render_error = f"{fmt}_from_svg_failed: {exc}"
                if strict:
                    _upsert_figure_record(reports_dir / "editable_svg_manifest.json", manifest, "figures")
                    qa = _build_svg_render_qa(
                        figure_id,
                        editable_svg,
                        manifest,
                        requested,
                        renderer=renderer_info,
                        outputs=outputs,
                        error=render_error,
                        derivative_sources=derivative_sources,
                        warnings=render_warnings,
                    )
                    _upsert_figure_record(reports_dir / "svg_render_qa.json", qa, "figures")
                    raise RuntimeError(render_error) from exc
        else:
            outputs[fmt] = None

    manifest["paths"] = outputs
    _upsert_figure_record(reports_dir / "editable_svg_manifest.json", manifest, "figures")
    qa = _build_svg_render_qa(
        figure_id,
        editable_svg,
        manifest,
        requested,
        renderer=renderer_info,
        outputs=outputs,
        error=render_error,
        derivative_sources=derivative_sources,
        warnings=render_warnings,
    )
    _upsert_figure_record(reports_dir / "svg_render_qa.json", qa, "figures")
    if strict and qa["hardFail"]:
        raise RuntimeError("Editable SVG QA failed: " + ", ".join(qa["failures"]))
    return {"manifest": manifest, "svgRenderQa": qa, "paths": outputs}


def revalidate_edited_svg_bundle(edited_svg_path, figure_id="figure1", output_dir="output",
                                 raster_dpi=300, normalized_formats=None, strict=True):
    """Use a hand-edited SVG as the final source and regenerate derivative assets."""
    requested = list(normalized_formats or ["svg", "png", "pdf"])
    requested = [str(fmt).lower().lstrip(".") for fmt in requested]
    edited_svg_path = Path(edited_svg_path)
    if not edited_svg_path.exists():
        raise FileNotFoundError(f"Edited SVG not found: {edited_svg_path}")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    final_svg = output_dir / f"{figure_id}.final.svg"
    canonical_svg = output_dir / f"{figure_id}.svg"
    shutil.copyfile(edited_svg_path, final_svg)
    shutil.copyfile(final_svg, canonical_svg)

    manifest_payload = _read_json_report(reports_dir / "editable_svg_manifest.json", {"figures": []})
    manifest_records = manifest_payload.get("figures", []) if isinstance(manifest_payload, dict) else []
    manifest = next((item for item in manifest_records if item.get("figureId") == figure_id), {"figureId": figure_id, "components": []})
    outputs = {"final_svg": str(final_svg), "svg": str(canonical_svg)}
    derivative_sources = {"svg": "edited_svg", "final_svg": "edited_svg"}
    render_warnings = []
    renderer_info = None
    render_error = None
    for fmt in requested:
        if fmt == "svg":
            continue
        if fmt in ("png", "pdf", "tiff"):
            out_path = output_dir / f"{figure_id}.{fmt}"
            try:
                renderer_info = _run_svg_renderer(final_svg, out_path, fmt, raster_dpi)
                outputs[fmt] = str(out_path)
                derivative_sources[fmt] = "edited_svg"
            except Exception as exc:
                if fmt == "pdf":
                    render_warnings.append(f"pdf_from_edited_svg_renderer_unavailable: {exc}")
                    continue
                render_error = f"{fmt}_from_edited_svg_failed: {exc}"
                if strict:
                    break
    qa = _build_svg_render_qa(
        figure_id,
        final_svg,
        manifest,
        requested,
        renderer=renderer_info,
        outputs=outputs,
        error=render_error,
        source_label="edited_svg",
        derivative_sources=derivative_sources,
        warnings=render_warnings,
    )
    _upsert_figure_record(reports_dir / "svg_render_qa.json", qa, "figures")
    if strict and qa["hardFail"]:
        raise RuntimeError("Edited SVG QA failed: " + ", ".join(qa["failures"]))
    return {"svgRenderQa": qa, "paths": outputs}


def _default_panel_blueprint_for_axes(axes):
    panel_ids = list(axes.keys()) or ["A"]
    recipe = "single" if len(panel_ids) == 1 else f"auto_{len(panel_ids)}_panel"
    return {
        "layout": {"recipe": recipe, "grid": recipe},
        "panels": [{"id": panel_id, "role": "panel", "chart": "auto"} for panel_id in panel_ids],
        "requestedLayout": recipe,
        "finalLayout": recipe,
        "sharedLegend": True,
        "sharedColorbar": False,
    }


def enforce_figure_legend_contract(fig, axes=None, chartPlan=None, journalProfile=None, crowdingPlan=None, strict=True):
    """Promote all axis/figure legends into one framed external legend before saving."""
    axes_map = normalize_axes_map(fig, axes)
    plan = chartPlan if isinstance(chartPlan, dict) else {}
    plan.setdefault("panelBlueprint", _default_panel_blueprint_for_axes(axes_map))
    plan.setdefault("crowdingPlan", {})
    if crowdingPlan:
        plan["crowdingPlan"].update(crowdingPlan)
    plan["crowdingPlan"]["legendContractRequired"] = True
    plan["crowdingPlan"]["legendMode"] = "bottom_center"
    plan["crowdingPlan"]["legendPlacementPriority"] = ["bottom_center"]
    plan["crowdingPlan"]["legendAllowedModes"] = ["bottom_center"]
    plan["crowdingPlan"]["legendFrame"] = True
    plan["crowdingPlan"].setdefault("legendFrameStyle", dict(CROWDING_DEFAULTS["legendFrameStyle"]))
    plan["crowdingPlan"].setdefault("legendFontSizePt", 7)
    plan["crowdingPlan"].setdefault("legendBottomAnchorY", CROWDING_DEFAULTS["legendBottomAnchorY"])
    plan["crowdingPlan"].setdefault("legendBottomMarginMin", 0.06)
    plan["crowdingPlan"].setdefault("legendBottomMarginMax", CROWDING_DEFAULTS["legendBottomMarginMax"])
    plan["crowdingPlan"]["forbidOutsideRightLegend"] = True
    plan["crowdingPlan"]["forbidInAxesLegend"] = True

    profile = journalProfile or {"font_size_small_pt": 7}
    report = apply_crowding_management(fig, axes_map, plan, profile)
    failures = []
    legend_exists = bool(report.get("hasFigureLegend")) or len(fig.legends) > 0
    legend_input_entry_count = report.get("legendInputEntryCount", 0)
    if report.get("axisLegendRemainingCount", 0) > 0:
        failures.append("axis_legend_remaining")
    if legend_input_entry_count > 0 and not legend_exists:
        failures.append("figure_legend_missing_for_handles")
    if legend_exists and len(fig.legends) != 1:
        failures.append("figure_legend_count_not_one")
    if legend_exists and report.get("legendModeUsed") != "bottom_center":
        failures.append("legend_not_bottom_center")
    if legend_exists and not report.get("legendFrameApplied"):
        failures.append("legend_frame_missing")
    if legend_exists and not report.get("legendOutsidePlotArea", False):
        failures.append("legend_overlaps_plot_area")
    if report.get("overlapIssues"):
        if any(issue.get("element") == "scifig_shared_legend" for issue in report["overlapIssues"]):
            failures.append("legend_overlap_issue_recorded")

    colorbar_reflow_count = reflow_colorbars_outside_panels(fig, axes_map, plan["crowdingPlan"])
    plan["crowdingPlan"]["colorbarReflowCount"] = colorbar_reflow_count
    report["colorbarReflowCount"] = colorbar_reflow_count

    title_alignment = center_figure_titles(fig, axes_map)
    plan["crowdingPlan"].update(title_alignment)
    report.update(title_alignment)

    text_sanitize = sanitize_figure_text(fig)
    plan["crowdingPlan"].update(text_sanitize)
    report.update(text_sanitize)

    # Zero-touch retrofit: every in-axes annotation gets zorder>=20 + white bbox
    # (cycle-22 anti-occlusion) BEFORE layout audit so the audit sees the
    # post-promotion state and reports buried-text overlaps accurately.
    text_safety = _promote_inaxes_text_safety(axes_map)
    plan["crowdingPlan"]["textSafetyPromotedZorder"] = text_safety["promoted_zorder"]
    plan["crowdingPlan"]["textSafetyPromotedBbox"] = text_safety["promoted_bbox"]
    report["textSafetyPromotedZorder"] = text_safety["promoted_zorder"]
    report["textSafetyPromotedBbox"] = text_safety["promoted_bbox"]

    # Zero-touch heatmap fmt adaptation: cell labels are reformatted to fit
    # actual cell physical width (cycle-22). Generators continue to use
    # sns.heatmap(annot=True, fmt=".2f"); this pass overrides the literal
    # fmt at finalize time so high-density matrices switch to ".1f" / ".0f"
    # / no-annot automatically.
    heatmap_shrink = _shrink_heatmap_cell_labels(axes_map, fig)
    plan["crowdingPlan"]["heatmapCellLabelsReformatted"] = heatmap_shrink["reformatted"]
    plan["crowdingPlan"]["heatmapCellLabelsRemoved"] = heatmap_shrink["removed"]
    report["heatmapCellLabelsReformatted"] = heatmap_shrink["reformatted"]
    report["heatmapCellLabelsRemoved"] = heatmap_shrink["removed"]

    layout_report = audit_figure_layout_contract(fig, axes_map, plan, profile, strict=False)
    if layout_report.get("layoutContractFailures"):
        failures.extend(layout_report["layoutContractFailures"])

    plan["crowdingPlan"]["legendContractEnforced"] = True
    plan["crowdingPlan"]["legendContractFailures"] = failures
    report["legendContractEnforced"] = True
    report["legendContractFailures"] = failures
    report.update(layout_report)
    report["colorbarReflowCount"] = colorbar_reflow_count
    if strict and failures:
        raise RuntimeError("Figure contract failed: " + ", ".join(failures))
    return report
```
