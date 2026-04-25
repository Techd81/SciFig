# Phase 2: Chart Recommendation, Statistics, And Panel Blueprint

> **COMPACT SENTINEL [Phase 2: recommend-stats]**
> This phase contains 7 execution steps (Step 2.1 - 2.7).
> If you can read this sentinel but cannot find the full Step protocol below, context has been compressed.
> Recovery: `Read("phases/02-recommend-stats.md")`

Resolve the domain playbook, expand chart coverage, choose inferential or descriptive statistics, and convert the story request into a concrete panel and palette blueprint.

## Objective

- Map the `dataProfile` onto the chart catalog and domain playbooks
- Recommend a primary chart plus domain-appropriate secondary charts
- Select a conservative statistical plan that matches the data design
- Build a reusable `panelBlueprint` for multi-panel assembly
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
    detected = dataProfile["domainHints"]["primary"]

    if user_domain and user_domain != "general_biomedical":
        return {
            "selected": user_domain,
            "detected": detected,
            "overridden": user_domain != detected
        }

    return {
        "selected": detected,
        "detected": detected,
        "overridden": False
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

    # Direct pattern matches
    if "genomic_association" in patterns:
        return "manhattan", ["qq", "forest"]
    if "survival" in patterns:
        return "km", ["forest", "roc", "calibration"]
    if "dose_response" in patterns:
        return "dose_response", ["waterfall", "paired_lines"]
    if "embedding" in patterns:
        primary = "umap" if any(c.startswith("umap") for c in cols) else "tsne"
        return primary, ["composition_dotplot", "violin+strip", "heatmap_pure"]
    if "differential" in patterns:
        if any("basemean" in c or "mean" in c for c in cols):
            return "ma_plot", ["volcano", "enrichment_dotplot", "heatmap+cluster"]
        return "volcano", ["heatmap+cluster", "enrichment_dotplot", "pca"]

    # Domain-aware defaults
    if "dose" in roles and "response" in roles:
        return "dose_response", ["waterfall", "violin+strip"]
    if "effect" in roles and "ci_low" in roles and "ci_high" in roles:
        return "forest", ["km" if "event" in roles else "box+strip"]
    if "score" in roles and "label" in roles:
        return "pr_curve" if n_obs > 0 and (dataProfile["df"][roles["label"]].mean() < 0.2) else "roc", ["calibration", "box+strip"]
    if "subject_id" in roles and "time" in roles:
        return "spaghetti", ["line_ci", "paired_lines"]
    if "subject_id" in roles and n_groups == 2 and "value" in roles:
        return "paired_lines", ["dumbbell", "beeswarm"]
    if "time" in roles and "value" in roles:
        return "line_ci" if any("ci" in c or "conf" in c for c in cols) else "line", ["beeswarm", "box+strip"]
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
def build_panel_blueprint(primaryChart, secondaryCharts, dataProfile, workflowPreferences):
    story = workflowPreferences.get("storyMode", "comparison_pair")
    panel_candidates = dataProfile["panelCandidates"]

    if story == "single":
        panels = [{"id": "A", "role": "hero", "chart": primaryChart, "source": "primary"}]
        layout = {"recipe": "single", "grid": "1x1"}
    elif story == "hero_plus_stacked_support":
        panels = [
            {"id": "A", "role": "hero", "chart": primaryChart, "source": "primary"},
            {"id": "B", "role": "support", "chart": secondaryCharts[0], "source": "secondary"},
            {"id": "C", "role": "validation", "chart": secondaryCharts[1], "source": "secondary"}
        ]
        layout = {"recipe": "hero_plus_stacked_support", "grid": "2x2-hero-span"}
    elif story == "story_board_2x2":
        fallback = [c["chart"] for c in panel_candidates if c["chart"] not in secondaryCharts]
        charts = [primaryChart] + secondaryCharts[:2] + fallback[:1]
        panels = [
            {"id": "A", "role": "hero", "chart": charts[0], "source": "primary"},
            {"id": "B", "role": "support", "chart": charts[1], "source": "secondary"},
            {"id": "C", "role": "validation", "chart": charts[2], "source": "secondary"},
            {"id": "D", "role": "context", "chart": charts[3] if len(charts) > 3 else charts[1], "source": "candidate"}
        ]
        layout = {"recipe": "story_board_2x2", "grid": "2x2"}
    else:
        panels = [
            {"id": "A", "role": "hero", "chart": primaryChart, "source": "primary"},
            {"id": "B", "role": "support", "chart": secondaryCharts[0], "source": "secondary"}
        ]
        layout = {"recipe": "comparison_pair", "grid": "1x2"}

    return {
        "layout": layout,
        "panels": panels,
        "sharedLegend": True,
        "sharedColorbar": primaryChart in ("heatmap+cluster", "heatmap_pure", "spatial_feature"),
        "axisLinkGroups": [["A", "B"]] if len(panels) >= 2 else [],
        "notes": ["keep_semantic_colors_consistent", "hero_panel_priority"]
    }
```

### Step 2.6: Build `palettePlan`

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

### Step 2.7: Assemble `chartPlan` And Confirm With User

```python
domainProfile = resolve_domain(dataProfile, workflowPreferences)
primaryChart, secondaryCharts = recommend_chart_bundle(dataProfile, workflowPreferences)
statPlan = select_statistical_plan(dataProfile, primaryChart, workflowPreferences)
annotations = configure_annotations(dataProfile, primaryChart, statPlan)
panelBlueprint = build_panel_blueprint(primaryChart, secondaryCharts, dataProfile, workflowPreferences)
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
    "palettePlan": palettePlan,
    "journalOverrides": {},
    "rationale": "Selected using semantic roles, special patterns, domain hints, and requested story mode."
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
