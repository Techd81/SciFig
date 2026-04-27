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
            return "pr_curve" if n_obs > 0 and pos_rate < 0.2 else "roc", ["calibration", "box+strip"]
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


def build_panel_blueprint(primaryChart, secondaryCharts, dataProfile, workflowPreferences):
    story = workflowPreferences.get("storyMode", "comparison_pair")
    crowding_policy = workflowPreferences.get("crowdingPolicy", "auto_simplify")
    panel_candidates = dataProfile["panelCandidates"]
    candidate_pool = _dedupe_charts(
        [c["chart"] for c in panel_candidates if c["chart"] != primaryChart]
    )
    support_pool = _dedupe_charts(
        [chart for chart in list(secondaryCharts) + candidate_pool if chart != primaryChart]
    )
    requested_story = story

    if story == "story_board_2x2" and len(support_pool) < 3:
        story = "hero_plus_stacked_support" if len(support_pool) >= 2 else "comparison_pair" if len(support_pool) >= 1 else "single"
    elif story == "hero_plus_stacked_support" and len(support_pool) < 2:
        story = "comparison_pair" if len(support_pool) >= 1 else "single"
    elif story == "comparison_pair" and len(support_pool) < 1:
        story = "single"

    if story == "single":
        panels = [{"id": "A", "role": "hero", "chart": primaryChart, "source": "primary"}]
        layout = {"recipe": "single", "grid": "1x1"}
    elif story == "hero_plus_stacked_support":
        panels = [
            {"id": "A", "role": "hero", "chart": primaryChart, "source": "primary"},
            {"id": "B", "role": "support", "chart": support_pool[0], "source": "secondary"},
            {"id": "C", "role": "validation", "chart": support_pool[1], "source": "secondary"}
        ]
        layout = {"recipe": "hero_plus_stacked_support", "grid": "2x2-hero-span"}
    elif story == "story_board_2x2":
        charts = [primaryChart] + support_pool[:3]
        panels = [
            {"id": "A", "role": "hero", "chart": charts[0], "source": "primary"},
            {"id": "B", "role": "support", "chart": charts[1], "source": "secondary"},
            {"id": "C", "role": "validation", "chart": charts[2], "source": "secondary"},
            {"id": "D", "role": "context", "chart": charts[3], "source": "candidate"}
        ]
        layout = {"recipe": "story_board_2x2", "grid": "2x2"}
    else:
        panels = [
            {"id": "A", "role": "hero", "chart": primaryChart, "source": "primary"},
            {"id": "B", "role": "support", "chart": support_pool[0], "source": "secondary"}
        ]
        layout = {"recipe": "comparison_pair", "grid": "1x2"}

    continuous_scale_charts = {
        "heatmap_cluster", "heatmap_pure", "heatmap_annotated", "heatmap_triangular",
        "heatmap_mirrored", "heatmap_symmetric", "spatial_feature", "correlation"
    }
    n_groups = dataProfile.get("nGroups") or 1
    notes = ["keep_semantic_colors_consistent", "hero_panel_priority", "deduplicate_support_panels"]
    if story != requested_story:
        notes.append(f"degraded_from_{requested_story}_to_{story}")
    if crowding_policy == "auto_simplify":
        notes.append("clarity_first_crowding_policy")

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
        "notes": notes
    }
```

### Step 2.6: Build `crowdingPlan`

```python
def build_crowding_plan(primaryChart, secondaryCharts, dataProfile, workflowPreferences, panelBlueprint):
    policy = workflowPreferences.get("crowdingPolicy", "auto_simplify")
    n_obs = dataProfile.get("nObservations") or 0
    n_groups = dataProfile.get("nGroups") or 1
    final_layout = panelBlueprint.get("finalLayout", panelBlueprint["layout"]["recipe"])
    panel_count = len(panelBlueprint.get("panels", []))

    if n_obs <= 400:
        point_density_mode = "full_points"
    elif n_obs <= 1000:
        point_density_mode = "alpha_jitter_small_markers"
    else:
        point_density_mode = "summary_or_thin_points"

    if panelBlueprint.get("sharedLegend", False):
        if panelBlueprint.get("sharedColorbar", False):
            legend_mode = "bottom_center"
        elif n_groups <= 8:
            legend_mode = "bottom_center"
        else:
            legend_mode = "outside_right"
    else:
        legend_mode = "bottom_center"

    layout_fallbacks = {
        "story_board_2x2": ["hero_plus_stacked_support", "comparison_pair", "single"],
        "hero_plus_stacked_support": ["comparison_pair", "single"],
        "comparison_pair": ["single"],
        "single": []
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
        "annotationMode": "compact" if policy == "auto_simplify" else "full",
        "simplifyIfCrowded": policy != "preserve_information",
        "simplificationsApplied": simplifications,
        "droppedDirectLabelCount": 0
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
    charts = [primaryChart] + list(secondaryCharts or [])
    mode = workflowPreferences.get("visualContentMode", "nature_cell_dense")
    density = workflowPreferences.get("visualDensity", "high")

    return {
        "mode": mode,
        "density": density,
        "maxCalloutsSingle": 8,
        "maxInlineStats": 4,
        "useInsetAxes": True,
        "noInventedStats": True,
        "familyByChart": {chart: infer_visual_chart_family(chart) for chart in charts if chart},
        "appliedEnhancements": [],
        "familyByPanel": {},
        "outsideLayoutElements": False,
        "notes": [
            "do_not_add_new_chart_types",
            "statistics_must_be_data_derived",
            "nature_cell_information_density"
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
            "rescue": "#4C956C"
        },
        "grayscaleCheck": True,
        "sharedAcrossPanels": True
    }

    if color_mode == "domain_semantic":
        if domain == "clinical_diagnostics_survival":
            plan["sequentialPreset"] = "seq_warm"
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
    "journalOverrides": {},
    "rationale": "Selected using semantic roles, special patterns, domain hints, requested story mode, clarity-first crowding control, and Nature/Cell dense visual content."
}
```

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
