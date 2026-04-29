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
        "dumbbell", "line", "line_ci", "spaghetti", "heatmap_cluster",
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
        "ci_plot", "dotplot", "adjacency_matrix", "heatmap_annotated", "heatmap_triangular",
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

    def _safe(chart):
        """Return chart if implemented, else closest fallback."""
        key = str(chart or "").replace("+", "_")
        if chart in IMPLEMENTED_CHARTS or key in IMPLEMENTED_CHARTS:
            return chart
        FALLBACKS = {
            # Keep only non-registry aliases here; registered keys should not be downgraded.
            "ridgeline": "ridge",
            "dot+box": "box+strip"
        }
        return FALLBACKS.get(key, "box+strip")

    # Direct pattern matches
    if "genomic_association" in patterns:
        return _safe("manhattan"), [_safe("qq"), "forest"]
    if "survival" in patterns:
        return "km", ["forest", "roc", "calibration"]
    if "dose_response" in patterns:
        return "dose_response", ["waterfall", "paired_lines"]
    if "embedding" in patterns:
        primary = "umap" if any(c.startswith("umap") for c in cols) else _safe("tsne")
        return primary, [_safe("composition_dotplot"), "violin+strip", "heatmap_pure"]
    if "differential" in patterns:
        if any("basemean" in c or "mean" in c for c in cols):
            return _safe("ma_plot"), ["volcano", "enrichment_dotplot", "heatmap+cluster"]
        return "volcano", ["heatmap+cluster", "enrichment_dotplot", "pca"]

    # Domain-aware defaults
    if "dose" in roles and "response" in roles:
        return "dose_response", ["waterfall", "violin+strip"]
    if "effect" in roles and "ci_low" in roles and "ci_high" in roles:
        return "forest", ["km" if "event" in roles else "box+strip"]
    if "score" in roles and "label" in roles:
        label_col = dataProfile["df"][roles["label"]]
        if pd.api.types.is_numeric_dtype(label_col):
            pos_rate = label_col.mean()
            return "pr_curve" if n_obs > 0 and pos_rate < DATA_SCALE_POLICY["rare_positive_rate"] else "roc", ["calibration", "box+strip"]
        return "roc", ["calibration", "box+strip"]
    if "subject_id" in roles and "time" in roles:
        return "spaghetti", ["line_ci", "paired_lines"]
    if "subject_id" in roles and n_groups == 2 and "value" in roles:
        return "paired_lines", ["dumbbell", "beeswarm"]
    if "time" in roles and "value" in roles:
        return "line_ci" if any("ci" in c or "conf" in c for c in cols) else "line_ci", ["beeswarm", "box+strip"]
    if dataProfile["structure"] == "matrix":
        return "heatmap+cluster" if n_obs <= 500 else "heatmap_pure", ["pca", "correlation"]

    # Publication-quality grouped defaults
    if "group" in roles and "value" in roles:
        if n_obs <= 80:
            primary = "raincloud" if domain in ("immunology_cell_biology", "general_biomedical") else "violin+strip"
        elif n_obs <= 250:
            primary = "violin+strip"
        else:
            primary = "box+strip"
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

    if primaryChart in ("volcano", "ma_plot", "heatmap+cluster", "heatmap_pure", "umap", "tsne", "pca", "spatial_feature"):
        return {"method": "none", "correction": None, "notes": ["exploratory_primary_chart"]}

    if primaryChart in ("roc", "pr_curve", "calibration"):
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
        "showIndividualPoints": primaryChart not in ("heatmap+cluster", "heatmap_pure", "volcano", "umap", "tsne", "pca", "manhattan", "qq"),
        "showSignificance": statPlan["method"] not in ("none", "effect_estimate_only"),
        "significanceDisplay": "exact_p",
        "showN": True,
        "showCI": primaryChart in ("line_ci", "forest", "roc", "pr_curve", "calibration"),
        "showAtRiskTable": primaryChart == "km",
        "showThresholdLines": primaryChart in ("volcano", "manhattan", "qq", "dose_response")
    }

    if not dataProfile["replicateInfo"]["has_bio_rep"] and "subject_id" not in dataProfile["semanticRoles"] and primaryChart not in ("km", "roc", "pr_curve", "forest"):
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


def build_panel_blueprint(primaryChart, secondaryCharts, dataProfile, workflowPreferences):
    scale_policy = globals().get("DATA_SCALE_POLICY", {
        "legend_bottom_group_max": 8,
    })
    story = workflowPreferences.get("storyMode", "comparison_pair")
    if workflowPreferences.get("journalStyle") == "cell" and story == "auto":
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
        "board_2x3": 6,
        "board_3x3": 9,
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

    layout = {"recipe": story, "grid": f"{story_panel_map.get(story, 2)}"}

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

    if panelBlueprint.get("sharedLegend", False):
        if panelBlueprint.get("sharedColorbar", False):
            legend_mode = "bottom_center"
        elif n_groups <= scale_policy["legend_bottom_group_max"]:
            legend_mode = "bottom_center"
        else:
            legend_mode = "outside_right"
    else:
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
    }.get(final_layout, ["comparison_pair", "single"])

    simplifications = []
    if panelBlueprint.get("finalLayout") != panelBlueprint.get("requestedLayout"):
        simplifications.append(f"layout_fallback:{panelBlueprint.get('requestedLayout')}->{panelBlueprint.get('finalLayout')}")
    if panelBlueprint.get("sharedLegend", False):
        simplifications.append("figure_level_shared_legend")
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
        "legendPlacementPriority": ["bottom_center", "top_center", "outside_right"],
        "legendLabelMaxChars": 32,
        "maxLegendColumns": 6,
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
            "dotplot", "composition_dotplot",
        },
        "time_series": {
            "line", "line_ci", "spaghetti", "sparkline", "area", "area_stacked",
            "streamgraph", "gantt", "timeline_annotation", "control_chart",
            "slope_chart", "bump_chart",
        },
        "clinical_diagnostic": {
            "roc", "pr_curve", "calibration", "km", "forest", "waterfall",
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
            "stem_plot", "mosaic_plot", "diverging_bar",
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

    return {
        "mode": mode,
        "density": density,
        "impactLevel": workflowPreferences.get("visualImpactLevel", "editorial_science"),
        "maxCalloutsSingle": max_callouts,
        "maxCalloutsSupport": 4,
        "maxInlineStats": 4,
        "minEnhancementsPerPanel": 2,
        "minTotalEnhancements": max(4, len(charts) * 2),
        "requireInPlotExplanatoryLabels": True,
        "minInPlotLabelsPerFigure": min(max(1, len(charts)), max_callouts),
        "semanticCalloutMode": "data_derived",
        "useInsetAxes": True,
        "noInventedStats": True,
        "statProvenanceRequired": True,
        "pointAnnotationMode": point_annotation_mode,
        "familyByChart": {chart: infer_visual_chart_family(chart) for chart in charts if chart},
        "appliedEnhancements": [],
        "familyByPanel": {},
        "metricBoxCount": 0,
        "insetCount": 0,
        "inPlotExplanatoryLabelCount": 0,
        "outsideLayoutElements": True,
        "statProvenance": [],
        "notes": [
            "do_not_add_new_chart_types",
            "statistics_must_be_data_derived",
            "nature_cell_information_density",
            "minimum_inplot_explanatory_labels_required",
            "minimum_visual_enhancement_count_required"
        ]
    }
```

### Step 2.8: Build `palettePlan`

```python
def build_palette_plan(primaryChart, dataProfile, workflowPreferences):
    domain = dataProfile["domainHints"]["primary"]
    color_mode = workflowPreferences.get("colorMode", "journal_safe_muted")

    plan = {
        "mode": color_mode,
        "categoricalPreset": "journal_muted_8",
        "sequentialPreset": "seq_cool",
        "divergingPreset": "div_expression" if primaryChart in ("volcano", "heatmap+cluster", "heatmap_pure", "correlation") else "div_centered",
        "semanticMap": {
            "control": "#1F4E79",
            "treatment": "#C8553D",
            "treated": "#C8553D",
            "drug": "#C8553D",
            "rescue": "#4C956C"
        },
        "grayscaleCheck": True,
        "sharedAcrossPanels": True,
        "deterministicCategoryOrder": True,
        "overflowEncoding": "marker_or_linestyle",
        "minGrayscaleDelta": 0.18,
        "contrastAuditRequired": True
    }

    if color_mode == "domain_semantic":
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
    "palettePlan": palettePlan,
    "delegationReports": delegationReports,
    "journalOverrides": {},
    "rationale": "Selected using semantic roles, special patterns, domain hints, requested story mode, layout scoring, clarity-first crowding control, palette contrast policy, and Nature/Cell dense visual content."
}
```

Before locking `chartPlan`, optionally use read-only agents when the plan is complex:

- `chart-stats-planner`: validate chart/stat fit, replicate meaning, and no invented inferential claims.
- `panel-layout-auditor`: validate support-panel dedupe, layout score, legend burden, axis linking, and reflow fallbacks.
- `palette-journal-auditor`: validate semantic color mapping, grayscale contrast, journal profile fit, and overflow marker/linestyle fallback.

Additionally, these advisory agents run after their respective plan steps:

- `scientific-color-harmony`: after `palettePlan` is built, evaluates perceptual harmony, color-wheel relationships, and domain aesthetics. Writes to `chartPlan.delegationReports.color_harmony`.
- `layout-aesthetics`: after `panelBlueprint` is built, evaluates whitespace balance, visual weight distribution, panel proportions, and grid harmony. Writes to `chartPlan.delegationReports.aesthetics`.
- `content-richness`: after `visualContentPlan` is built, evaluates annotation density, label informativeness, marker diversity, and directional elements. Writes to `chartPlan.delegationReports.content_richness`.

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
           f"Assess: annotation density, label informativeness, marker diversity, directional elements. "
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
