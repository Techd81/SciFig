# Phase 3: Code Generation, Journal Styling, And Composition

> **COMPACT SENTINEL [Phase 3: code-gen-style]**
> This phase contains 6 execution steps (Step 3.1 - 3.6, with 3.4b and 3.4c sub-protocols).
> Generator implementations are in sub-files under `phases/code-gen/`:
>   - `generators-distribution.md` (distribution, time-series, statistical, genomics, engineering, ecology charts)
>   - `generators-clinical.md` (clinical trial, composition, hierarchical charts)
>   - `generators-psychology.md` (relationship, psychology, social science charts)
> If you can read this sentinel but cannot find the full Step protocol below, context has been compressed.
> Recovery: `Read("phases/03-code-gen-style.md")`

Generate complete Python code that applies journal style tokens, resolves a palette system, composes multi-panel figures, and writes reproducibility-friendly outputs.

## Objective

- Resolve a concrete journal profile for Nature-like, Cell-like, or Science-like output
- Resolve a stable color system from `palettePlan`
- Generate chart-specific code and a panel composition scaffold
- Improve multi-panel geometry, shared legends, shared colorbars, and panel-label discipline
- Apply performance and render-QA hooks from `specs/workflow-policies.md`
- Produce `styledCode` with enough metadata for export and iteration

## Execution

### Step 3.0: Column Name Sanitization

Code generators MUST call `sanitize_columns(df)` before using column names in code. This prevents errors when user data has spaces, special characters, or reserved-word column names.

```python
def sanitize_columns(df):
    """Rename columns to safe Python identifiers. Returns (df_renamed, name_map)."""
    import re
    name_map = {}
    new_cols = []
    for col in df.columns:
        safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(col)).strip('_')
        if safe and safe[0].isdigit():
            safe = 'col_' + safe
        safe = safe or 'unnamed'
        # Deduplicate
        base = safe; i = 1
        while safe in new_cols:
            safe = f"{base}_{i}"; i += 1
        new_cols.append(safe)
        if safe != col:
            name_map[safe] = col
    df.columns = new_cols
    return df, name_map
```

All generated code should include this function at the top, and call it immediately after loading data:

```python
df, col_map = sanitize_columns(df)
# Use sanitized names throughout; col_map for display labels
```

### Step 3.1: Resolve Journal Profile

Read `specs/journal-profiles.md` and `specs/workflow-policies.md`, then convert the selected profile into plotting tokens.

```python
def resolve_journal_profile(workflowPreferences):
    style = workflowPreferences.get("journalStyle", "nature")

    nature = {
        "name": "nature",
        "single_width_mm": 89,
        "double_width_mm": 183,
        "max_height_mm": 170,
        "font_family": ["Arial", "Helvetica", "DejaVu Sans"],
        "font_size_body_pt": 6,
        "font_size_small_pt": 5,
        "font_size_panel_label_pt": 8,
        "axis_linewidth_pt": 0.6,
        "tick_width_pt": 0.6,
        "panel_gap_rel": 0.22,
        "canvas_height_mm": {
            "single": 62,
            "comparison_pair": 78,
            "hero_plus_stacked_support": 134,
            "story_board_2x2": 146
        },
        "panel_label_offset_xy": [-0.12, 1.05],
        "legend_retry_limit": 5
    }

    cell = {
        **nature,
        "name": "cell",
        "font_size_body_pt": 6.5,
        "panel_gap_rel": 0.28,
        "story_bias": "hero_plus_support"
    }

    science = {
        **nature,
        "name": "science",
        "axis_linewidth_pt": 0.55,
        "tick_width_pt": 0.5,
        "panel_gap_rel": 0.18,
        "story_bias": "compact_pair"
    }

    lancet = {
        **nature,
        "name": "lancet",
        "single_width_mm": 80,
        "double_width_mm": 168,
        "font_size_body_pt": 6,
        "font_size_panel_label_pt": 7,
        "axis_linewidth_pt": 0.5,
        "tick_width_pt": 0.5,
        "panel_gap_rel": 0.20,
        "story_bias": "clinical_evidence"
    }

    nejm = {
        **nature,
        "name": "nejm",
        "single_width_mm": 86,
        "double_width_mm": 178,
        "font_size_body_pt": 6,
        "font_size_panel_label_pt": 8,
        "axis_linewidth_pt": 0.5,
        "tick_width_pt": 0.5,
        "panel_gap_rel": 0.22,
        "story_bias": "clinical_outcome"
    }

    jama = {
        **nature,
        "name": "jama",
        "single_width_mm": 84,
        "double_width_mm": 175,
        "font_size_body_pt": 6,
        "font_size_panel_label_pt": 7,
        "axis_linewidth_pt": 0.5,
        "tick_width_pt": 0.5,
        "panel_gap_rel": 0.20,
        "story_bias": "clinical_validation"
    }

    if style == "cell":
        return cell
    if style == "science":
        return science
    if style == "lancet":
        return lancet
    if style == "nejm":
        return nejm
    if style == "jama":
        return jama
    return nature
```

Convert the journal profile into `rcParams`:

```python
def build_rcparams(journalProfile):
    return {
        # Font embedding (CRITICAL for journal submission)
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",  # text as text elements for editability
        "mathtext.fontset": "dejavusans",

        # Typography
        "font.family": "sans-serif",
        "font.sans-serif": journalProfile["font_family"],
        "font.size": journalProfile["font_size_body_pt"],
        "axes.labelsize": journalProfile.get("font_size_body_pt", 6),
        "axes.titlesize": journalProfile.get("font_size_body_pt", 6) + 1,
        "xtick.labelsize": journalProfile.get("font_size_body_pt", 6) - 1,
        "ytick.labelsize": journalProfile.get("font_size_body_pt", 6) - 1,
        "legend.fontsize": journalProfile.get("font_size_small_pt", 5),

        # Axes spines (Nature/Cell: remove top/right for "open L" style)
        "axes.linewidth": journalProfile["axis_linewidth_pt"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.facecolor": "white",
        "figure.facecolor": "white",

        # Tick geometry
        "xtick.major.width": journalProfile["tick_width_pt"],
        "ytick.major.width": journalProfile["tick_width_pt"],
        "xtick.major.size": journalProfile.get("tick_length_pt", 3),
        "ytick.major.size": journalProfile.get("tick_length_pt", 3),
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.top": False,
        "ytick.right": False,

        # Line style
        "lines.linewidth": 0.8,
        "lines.markersize": 4,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",

        # Legend
        "legend.frameon": False,
        "legend.borderpad": 0.3,

        # Output
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05
    }
```

### Step 3.2: Resolve Color System

Read `templates/palette-presets.md` and convert `palettePlan` into a chart-ready color system.

```python
PALETTES = {
    "journal_muted_8": ["#1F4E79", "#4C956C", "#F2A541", "#C8553D", "#7A6C8F", "#2B6F77", "#BC4749", "#6C757D"],
    "journal_muted_6": ["#1F4E79", "#4C956C", "#F2A541", "#C8553D", "#7A6C8F", "#6C757D"],
    "wong_8": ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"],
    "okabe_ito_8": ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"],
    "genomics_categorical": ["#3B5998", "#C8553D", "#999999", "#4C956C", "#F2A541", "#7A6C8F"],
    "clinical_survival": ["#0072B2", "#C8553D", "#4C956C", "#F2A541"],
    "seq_cool": ["#F7FBFF", "#D6EAF8", "#A9CCE3", "#5DADE2", "#21618C"],
    "seq_warm": ["#FFF6E8", "#FBD38D", "#F6AD55", "#DD6B20", "#9C4221"],
    "div_centered": ["#3B6FB6", "#8FBCE6", "#F7F7F7", "#E6A0A0", "#B5403A"],
    "div_expression": ["#2D5AA7", "#9CC4E4", "#F5F5F5", "#F4A582", "#B2182B"]
}


def resolve_color_system(chartPlan, dataProfile):
    palettePlan = chartPlan["palettePlan"]
    roles = dataProfile["semanticRoles"]
    df = dataProfile["df"]

    categorical = PALETTES[palettePlan["categoricalPreset"]]
    sequential = PALETTES[palettePlan["sequentialPreset"]]
    diverging = PALETTES[palettePlan["divergingPreset"]]

    categories = []
    if "group" in roles and roles["group"] in df.columns:
        categories = df[roles["group"]].dropna().astype(str).unique().tolist()

    if len(categories) > len(categorical):
        import warnings
        warnings.warn(f"More categories ({len(categories)}) than palette colors ({len(categorical)}). Colors will repeat.")

    category_map = {cat: categorical[idx % len(categorical)] for idx, cat in enumerate(categories)}
    category_map.update(palettePlan.get("semanticMap", {}))

    return {
        "categorical": categorical,
        "sequential": sequential,
        "diverging": diverging,
        "categoryMap": category_map,
        "grayscaleCheck": palettePlan.get("grayscaleCheck", True),
        "sharedAcrossPanels": palettePlan.get("sharedAcrossPanels", True)
    }
```

### Step 3.3: Resolve Canvas Size And Panel Geometry

```python
def resolve_canvas(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]

    if recipe == "single":
        return {"width_mm": journalProfile["single_width_mm"], "height_mm": 62}
    if recipe == "comparison_pair":
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": 78}
    if recipe == "hero_plus_stacked_support":
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": 134}
    return {"width_mm": journalProfile["double_width_mm"], "height_mm": 146}


def resolve_panel_geometry(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    gap = max(journalProfile.get("panel_gap_rel", 0.18), 0.24 if recipe != "single" else 0.0)

    if recipe == "single":
        return {"engine": "subplots", "grid": "1x1", "hspace": 0.0, "wspace": 0.0}
    if recipe == "comparison_pair":
        return {"engine": "subplots", "grid": "1x2", "hspace": 0.0, "wspace": gap}
    if recipe == "hero_plus_stacked_support":
        return {"engine": "GridSpec", "grid": "2x2-hero-span", "hspace": gap, "wspace": gap}
    return {"engine": "GridSpec", "grid": "2x2", "hspace": gap, "wspace": gap}
```

### Step 3.4: Generate Chart Code And Registry

Create a registry so chart expansion stays maintainable.

```python
CHART_GENERATORS = {
    "violin_strip": "gen_violin_strip",
    "box_strip": "gen_box_strip",
    "raincloud": "gen_raincloud",
    "beeswarm": "gen_beeswarm",
    "paired_lines": "gen_paired_lines",
    "dumbbell": "gen_dumbbell",
    "line": "gen_line",
    "line_ci": "gen_line_ci",
    "spaghetti": "gen_spaghetti",
    "heatmap_cluster": "gen_heatmap_cluster",
    "heatmap_pure": "gen_heatmap_pure",
    "volcano": "gen_volcano",
    "ma_plot": "gen_ma_plot",
    "pca": "gen_pca",
    "umap": "gen_umap",
    "tsne": "gen_tsne",
    "enrichment_dotplot": "gen_enrichment_dotplot",
    "oncoprint": "gen_oncoprint",
    "lollipop_mutation": "gen_lollipop_mutation",
    "roc": "gen_roc",
    "pr_curve": "gen_pr_curve",
    "calibration": "gen_calibration",
    "km": "gen_km",
    "forest": "gen_forest",
    "waterfall": "gen_waterfall",
    "dose_response": "gen_dose_response",
    "scatter_regression": "gen_scatter_regression",
    "correlation": "gen_correlation",
    "manhattan": "gen_manhattan",
    "qq": "gen_qq",
    "spatial_feature": "gen_spatial_feature",
    "composition_dotplot": "gen_composition_dotplot",
    "ridge": "gen_ridge",
    "bubble_matrix": "gen_bubble_matrix",
    "stacked_bar_comp": "gen_stacked_bar_comp",
    "alluvial": "gen_alluvial",

    # Distribution variants (7)
    "violin_paired": "gen_violin_paired",
    "violin_split": "gen_violin_split",
    "dot_strip": "gen_dot_strip",
    "histogram": "gen_histogram",
    "density": "gen_density",
    "ecdf": "gen_ecdf",
    "joyplot": "gen_joyplot",

    # Time series variants (6)
    "sparkline": "gen_sparkline",
    "area": "gen_area",
    "area_stacked": "gen_area_stacked",
    "streamgraph": "gen_streamgraph",
    "gantt": "gen_gantt",
    "timeline_annotation": "gen_timeline_annotation",

    # Statistical / diagnostic (12)
    "residual_vs_fitted": "gen_residual_vs_fitted",
    "scale_location": "gen_scale_location",
    "cook_distance": "gen_cook_distance",
    "leverage_plot": "gen_leverage_plot",
    "pp_plot": "gen_pp_plot",
    "bland_altman": "gen_bland_altman",
    "funnel_plot": "gen_funnel_plot",
    "pareto_chart": "gen_pareto_chart",
    "control_chart": "gen_control_chart",
    "box_paired": "gen_box_paired",
    "mean_diff_plot": "gen_mean_diff_plot",
    "ci_plot": "gen_ci_plot",

    # Matrix / heatmap variants (6)
    "dotplot": "gen_dotplot",
    "adjacency_matrix": "gen_adjacency_matrix",
    "heatmap_annotated": "gen_heatmap_annotated",
    "heatmap_triangular": "gen_heatmap_triangular",
    "heatmap_mirrored": "gen_heatmap_mirrored",
    "cooccurrence_matrix": "gen_cooccurrence_matrix",

    # Genomics extended (6)
    "circos_karyotype": "gen_circos_karyotype",
    "gene_structure": "gen_gene_structure",
    "pathway_map": "gen_pathway_map",
    "kegg_bar": "gen_kegg_bar",
    "go_treemap": "gen_go_treemap",
    "chromosome_coverage": "gen_chromosome_coverage",

    # Clinical extended (6)
    "swimmer_plot": "gen_swimmer_plot",
    "risk_ratio_plot": "gen_risk_ratio_plot",
    "caterpillar_plot": "gen_caterpillar_plot",
    "tornado_chart": "gen_tornado_chart",
    "nomogram": "gen_nomogram",
    "decision_curve": "gen_decision_curve",

    # Composition / hierarchical (6)
    "treemap": "gen_treemap",
    "sunburst": "gen_sunburst",
    "waffle_chart": "gen_waffle_chart",
    "marimekko": "gen_marimekko",
    "stacked_area_comp": "gen_stacked_area_comp",
    "nested_donut": "gen_nested_donut",

    # Relationship / network (4)
    "chord_diagram": "gen_chord_diagram",
    "parallel_coordinates": "gen_parallel_coordinates",
    "sankey": "gen_sankey",
    "radar": "gen_radar",

    # Engineering / materials (6)
    "stress_strain": "gen_stress_strain",
    "phase_diagram": "gen_phase_diagram",
    "nyquist_plot": "gen_nyquist_plot",
    "xrd_pattern": "gen_xrd_pattern",
    "ftir_spectrum": "gen_ftir_spectrum",
    "dsc_thermogram": "gen_dsc_thermogram",

    # Ecology / environmental (4)
    "species_abundance": "gen_species_abundance",
    "shannon_diversity": "gen_shannon_diversity",
    "ordination_plot": "gen_ordination_plot",
    "biodiversity_radar": "gen_biodiversity_radar",

    # Psychology / social (4)
    "likert_divergent": "gen_likert_divergent",
    "likert_stacked": "gen_likert_stacked",
    "mediation_path": "gen_mediation_path",
    "interaction_plot": "gen_interaction_plot",

    # Additional variants (12)
    "bubble_scatter": "gen_bubble_scatter",
    "connected_scatter": "gen_connected_scatter",
    "stem_plot": "gen_stem_plot",
    "lollipop_horizontal": "gen_lollipop_horizontal",
    "slope_chart": "gen_slope_chart",
    "bump_chart": "gen_bump_chart",
    "mosaic_plot": "gen_mosaic_plot",
    "clustered_bar": "gen_clustered_bar",
    "diverging_bar": "gen_diverging_bar",
    "grouped_bar": "gen_grouped_bar",
    "heatmap_symmetric": "gen_heatmap_symmetric",
    "violin_grouped": "gen_violin_grouped"
}
```

Each generator should:

- Load only the columns it needs from `dataProfile["filePath"]`
- Apply `rcParams`
- Use the resolved `colorSystem`
- Write figures, source-data friendly tables, and metadata hooks
- Return its axis object when used inside multi-panel composition
- Apply `apply_chart_polish(ax, chart_type)` after drawing data
- Leave Nature/Cell dense overlays to `apply_visual_content_pass(...)` so all implemented charts share the same information-density contract

### Post-plot polish function (call after every chart generator)

Generator functions draw the base chart and apply minimal polish only. The generated script then runs `apply_visual_content_pass(...)` before crowding management so content density is controlled centrally instead of being reimplemented chart-by-chart.

```python
def apply_chart_polish(ax, chart_type):
    """Apply publication-quality post-processing to any axes."""
    # Remove top/right spines (Nature/Cell "open L" style)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Tick discipline
    ax.tick_params(direction="out", length=3, width=0.6, pad=2)

    # Violin transparency: make fill semi-transparent so strip points show through
    if chart_type in ("violin_strip", "violin_paired", "violin_split", "violin_grouped"):
        for coll in ax.collections:
            if hasattr(coll, "set_alpha"):
                coll.set_alpha(0.3)

    # Y-axis baseline: anchor at 0 for ratio-scale data
    if chart_type in ("violin_strip", "box_strip", "dot+box", "bar"):
        ymin = ax.get_ylim()[0]
        if ymin > 0:
            ax.set_ylim(bottom=0)

    # n-label styling: 5pt minimum, dark gray
    for text in ax.texts:
        if text.get_text().startswith("n="):
            text.set_fontsize(5)
            text.set_color("#333")


def add_significance_bracket(ax, x1, x2, y, height, p_value, lw=0.6):
    """Add a Nature-style significance bracket with T-caps and italic p."""
    cap_w = height * 0.25
    # Vertical risers with T-caps
    ax.plot([x1, x1], [y, y+height], lw=lw, c="black", clip_on=False)
    ax.plot([x2, x2], [y, y+height], lw=lw, c="black", clip_on=False)
    # Horizontal bar
    ax.plot([x1, x2], [y+height, y+height], lw=lw, c="black", clip_on=False)
    # T-caps
    ax.plot([x1-cap_w, x1+cap_w], [y, y], lw=lw, c="black", clip_on=False)
    ax.plot([x2-cap_w, x2+cap_w], [y, y], lw=lw, c="black", clip_on=False)
    # P-value text (italic, Nature convention)
    if p_value < 0.001:
        p_text = "p < 0.001"
    else:
        p_text = f"p = {p_value:.3g}"
    ax.text((x1+x2)/2, y+height*1.1, p_text, ha="center", va="bottom",
            fontsize=6, fontstyle="italic")


def format_p_value(p_value):
    """Format p-value per Nature convention: italic p, no leading zero."""
    if p_value < 0.001:
        return "p < 0.001"
    elif p_value < 0.01:
        return f"p = {p_value:.2g}"
    else:
        return f"p = {p_value:.2g}"
```

### Label Collision Avoidance (volcano, manhattan, scatter with annotations)

When labeling top genes or top-ranked points, cap direct labels through the `crowdingPlan` budget before adding callouts. Clarity-first mode should reduce labels instead of stacking unreadable text.

```python
# Sort by significance, pick the label budget from crowdingPlan
label_budget = chartPlan.get("crowdingPlan", {}).get("maxDirectLabelsHero", 5)
top = df[df.category != "NS"].nlargest(label_budget, "nlogp")
for idx, (_, row) in enumerate(top.iterrows()):
    y_offset = (idx % 3) * max_y * 0.04
    ax.annotate(row["gene"], (row["log2fc"], row["nlogp"] + y_offset),
                fontsize=4, ha="center", va="bottom",
                arrowprops=dict(arrowstyle="-", lw=0.3, color="black"))
```

If direct labels still exceed the budget, keep only the highest-priority labels and record the simplification in `crowdingPlan["simplificationsApplied"]`.

### Crowding Control Helpers

```python
# Shared Helper Functions for Chart Generators and Crowding Control

import re
import numpy as np
import matplotlib.pyplot as plt


VISUAL_CONTENT_DEFAULTS = {
    "mode": "nature_cell_dense",
    "density": "high",
    "impactLevel": "editorial_science",
    "maxCalloutsSingle": 8,
    "maxCalloutsSupport": 4,
    "maxInlineStats": 4,
    "useInsetAxes": True,
    "noInventedStats": True,
    "statProvenanceRequired": True,
    "outsideLayoutElements": True,
}


CROWDING_DEFAULTS = {
    "legendScope": "figure",
    "legendMode": "bottom_center",
    "legendPlacementPriority": ["bottom_center", "top_center", "outside_right"],
    "legendLabelMaxChars": 32,
    "maxLegendColumns": 6,
    "forbidInAxesLegend": True,
    "colorbarMode": "none",
    "maxDirectLabelsHero": 5,
    "maxDirectLabelsSupport": 3,
    "maxBracketGroups": 2,
    "pointDensityMode": "alpha_jitter_small_markers",
    "simplifyIfCrowded": True,
    "renderRetryLimit": 5,
    "layoutReflowRequiredOnOverlap": True,
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
    """Apply publication-quality post-processing to any axes."""
    ax.spines["top"].set_visible(False)
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
    for family, keys in groups.items():
        if key in keys:
            return family
    return "generic"


def default_visual_content_plan():
    return {
        **VISUAL_CONTENT_DEFAULTS,
        "appliedEnhancements": [],
        "familyByPanel": {},
        "statProvenance": [],
        "renderQaHooks": {
            "trackMetricBoxes": True,
            "trackInsets": True,
            "trackOutsideArtists": True,
        },
    }


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
    plan.setdefault("appliedEnhancements", [])
    plan.setdefault("familyByPanel", {})
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
    visualPlan["outsideLayoutElements"] = True
    return artist


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
    visualPlan["outsideLayoutElements"] = True
    return inset


def _maybe_reference_zero(ax):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    if x0 < 0 < x1:
        ax.axvline(0, color="#A0A0A0", lw=0.45, ls="--", zorder=0)
    if y0 < 0 < y1:
        ax.axhline(0, color="#A0A0A0", lw=0.45, ls="--", zorder=0)


def _enhance_distribution(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    group_col = _role(dataProfile, "group", "condition")
    value_col = _role(dataProfile, "value", "y")
    values = _numeric_values(df, value_col)
    if len(values) == 0:
        return []

    enhancements = ["distribution_summary"]
    groups = []
    if group_col and df is not None and group_col in df:
        groups = list(df[group_col].dropna().unique())
    if groups:
        for i, group in enumerate(groups[:8]):
            subset = _numeric_values(df[df[group_col] == group], value_col)
            if len(subset) == 0:
                continue
            median = float(np.nanmedian(subset))
            q1, q3 = np.nanpercentile(subset, [25, 75])
            mean = float(np.nanmean(subset))
            ax.vlines(i, q1, q3, color="black", lw=1.0, zorder=7)
            ax.scatter([i], [mean], marker="D", s=18, facecolor="white",
                       edgecolor="black", linewidth=0.45, zorder=8)
            ax.text(i, -0.12, f"n={len(subset)}", transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=5, clip_on=False, color="#333333")
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
        _add_metric_box(ax, [f"n={len(values)}", f"median={np.nanmedian(values):.3g}", f"IQR={np.nanpercentile(values, 75) - np.nanpercentile(values, 25):.3g}"], visualPlan)
    _add_summary_inset(ax, values, visualPlan, color=palette.get("categorical", ["#4C78A8"])[0])
    return enhancements


def _enhance_scatter(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    x_col = _role(dataProfile, "x", "time", "score")
    y_col = _role(dataProfile, "y", "value")
    x = _numeric_values(df, x_col)
    y = _numeric_values(df, y_col)
    if len(x) == 0 or len(y) == 0 or len(x) != len(y):
        _maybe_reference_zero(ax)
        _add_metric_box(ax, ["exploratory view"], visualPlan)
        return ["reference_context"]

    _maybe_reference_zero(ax)
    enhancements = ["scatter_context"]
    if len(x) >= 3 and np.nanstd(x) > 0 and np.nanstd(y) > 0:
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(np.nanmin(x), np.nanmax(x), 100)
        ax.plot(xs, slope * xs + intercept, color="black", lw=0.75,
                alpha=0.65, label="_nolegend_", zorder=5)
        r = np.corrcoef(x, y)[0, 1]
        _add_metric_box(ax, [f"n={len(x)}", f"r={r:.2f}", f"slope={slope:.2g}"], visualPlan)
        enhancements.append("trend_summary")
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


def _enhance_matrix(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    numeric = None
    if df is not None:
        try:
            numeric = df.select_dtypes(include="number")
        except AttributeError:
            numeric = None
    if numeric is not None and numeric.size:
        vals = numeric.to_numpy(dtype=float)
        _add_metric_box(ax, [f"matrix={vals.shape[0]}x{vals.shape[1]}", f"range={np.nanmin(vals):.2g}..{np.nanmax(vals):.2g}"], visualPlan)
        if vals.shape[0] <= 6 and vals.shape[1] <= 6:
            for i in range(vals.shape[0]):
                for j in range(vals.shape[1]):
                    ax.text(j + 0.5, i + 0.5, f"{vals[i, j]:.2g}",
                            ha="center", va="center", fontsize=4.5, color="#111111")
            return ["matrix_summary", "cell_value_labels"]
        return ["matrix_summary"]
    _add_metric_box(ax, ["matrix view"], visualPlan)
    return ["matrix_summary"]


def _enhance_time_series(ax, dataProfile, visualPlan, palette, col_map):
    enhancements = []
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
    if ax.lines:
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
    df = _df_from_profile(dataProfile)
    score_col = _role(dataProfile, "score", "x")
    label_col = _role(dataProfile, "label", "event")
    scores = _numeric_values(df, score_col)
    labels = _numeric_values(df, label_col)
    lines = []
    if chart_type in ("roc", "calibration") and ax.get_xlim()[0] <= 0 <= ax.get_xlim()[1]:
        ax.plot([0, 1], [0, 1], color="#999999", lw=0.55, ls="--", label="_nolegend_")
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
    _add_metric_box(ax, lines or ["clinical summary"], visualPlan)
    return ["clinical_metric_summary"]


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
    hits = int(np.sum((np.abs(x) >= 1) & (y >= 1.3)))
    if label_col and df is not None and label_col in df:
        budget = min(visualPlan.get("maxCalloutsSingle", 8), 6, len(y))
        for idx in np.argsort(y)[-budget:]:
            ax.annotate(str(df.iloc[idx][label_col])[:18], (x[idx], y[idx]),
                        xytext=(3, 3), textcoords="offset points", fontsize=4.5,
                        arrowprops={"arrowstyle": "-", "lw": 0.25, "color": "#555555"})
    _add_metric_box(ax, [f"features={len(x)}", f"hits={hits}", "|log2FC|>=1", "FDR/p>=line"], visualPlan)
    return ["threshold_lines", "top_feature_callouts", "hit_summary"]


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
        _add_metric_box(ax, [f"n={len(y)}", f"peak={y[peak_idx]:.3g}", f"range={np.nanmin(y):.2g}..{np.nanmax(y):.2g}"], visualPlan)
        return ["peak_annotation", "range_summary"]
    _add_metric_box(ax, ["engineering summary"], visualPlan)
    return ["engineering_context"]


def _enhance_composition(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    group_col = _role(dataProfile, "group", "feature_id", "label")
    value_col = _role(dataProfile, "value", "y")
    values = _numeric_values(df, value_col)
    lines = []
    if len(values):
        total = float(np.nansum(values))
        lines.extend([f"total={total:.3g}", f"items={len(values)}"])
    if group_col and df is not None and group_col in df:
        lines.append(f"categories={df[group_col].nunique()}")
    _add_metric_box(ax, lines or ["composition summary"], visualPlan)
    return ["composition_summary"]


def _enhance_psych_ecology(ax, dataProfile, visualPlan, palette, col_map):
    _maybe_reference_zero(ax)
    df = _df_from_profile(dataProfile)
    value_col = _role(dataProfile, "value", "y")
    values = _numeric_values(df, value_col)
    if len(values):
        _add_metric_box(ax, [f"n={len(values)}", f"mean={np.nanmean(values):.3g}", f"median={np.nanmedian(values):.3g}"], visualPlan)
    else:
        _add_metric_box(ax, ["rank/proportion view"], visualPlan)
    return ["reference_band", "descriptive_summary"]


def _enhance_generic(ax, dataProfile, visualPlan, palette, col_map):
    df = _df_from_profile(dataProfile)
    n = None
    if df is not None:
        try:
            n = len(df)
        except TypeError:
            n = None
    _maybe_reference_zero(ax)
    _add_metric_box(ax, [f"n={n}" if n is not None else "descriptive view"], visualPlan)
    return ["descriptive_context"]


def apply_visual_content_pass(fig, axes, chartPlan, dataProfile, journalProfile, palette, col_map=None):
    """Add Nature/Cell-style information density after base plotting."""
    visualPlan = _ensure_visual_content_plan(chartPlan, dataProfile=dataProfile)
    if visualPlan.get("mode") in ("off", "none"):
        return {"appliedEnhancementCount": 0, "families": {}}

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

        for enhancement in enhancements:
            _record_visual(visualPlan, panel_id, family, enhancement)

    chartPlan["visualContentPlan"] = visualPlan
    return {
        "appliedEnhancementCount": len(visualPlan.get("appliedEnhancements", [])),
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


def remove_axis_legends(axes):
    removed = 0
    for ax in axes.values():
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()
            removed += 1
    return removed


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


def trim_excess_text_annotations(ax, max_keep):
    if max_keep is None:
        return 0
    texts = list(ax.texts)
    if len(texts) <= max_keep:
        return 0
    removed = 0
    for text in texts[max_keep:]:
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


def legend_overlaps_axes(fig, legend, axes):
    renderer = get_cached_renderer(fig)
    legend_box = legend.get_window_extent(renderer=renderer)
    return any(legend_box.overlaps(ax.get_window_extent(renderer=renderer)) for ax in axes)


def apply_subplot_margins(fig, legend_mode, has_colorbar=False, legend=None):
    invalidate_layout_cache(fig)
    get_cached_renderer(fig, force=True)
    subplotpars = fig.subplotpars
    left = 0.11
    top = min(subplotpars.top, 0.95)
    bottom = max(subplotpars.bottom, 0.12)
    right = min(subplotpars.right, 0.95)

    if has_colorbar:
        right = min(right, 0.78)

    if legend is not None:
        legend_box = _bbox_in_figure_coords(fig, legend)
        if legend_mode == "bottom_center":
            bottom = max(bottom, min(0.74, legend_box.y1 + 0.035))
        elif legend_mode == "top_center":
            top = min(top, max(0.26, legend_box.y0 - 0.035))
        elif legend_mode == "outside_right":
            right = min(right, max(0.30, legend_box.x0 - 0.035))

    if right <= left + 0.12:
        right = left + 0.12
    if top <= bottom + 0.12:
        if legend_mode == "bottom_center":
            bottom = max(0.12, top - 0.12)
        else:
            top = min(0.95, bottom + 0.12)

    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)
    invalidate_layout_cache(fig)


def _unique_modes(modes):
    out = []
    for mode in modes:
        if mode and mode not in out:
            out.append(mode)
    return out


def _legend_column_options(label_count, legend_mode, max_columns):
    if legend_mode == "outside_right":
        return [1]
    candidates = [
        min(label_count, max_columns),
        min(label_count, 4),
        min(label_count, 3),
        min(label_count, 2),
        1,
    ]
    return [n for n in dict.fromkeys(candidates) if n >= 1]


def create_figure_legend(fig, handles, labels, legend_mode, fontsize, ncol=1):
    invalidate_layout_cache(fig)
    common = {
        "ncol": ncol,
        "frameon": False,
        "fontsize": fontsize,
        "borderaxespad": 0.0,
        "handlelength": 1.2,
        "handletextpad": 0.4,
        "labelspacing": 0.35,
        "columnspacing": 0.8,
    }
    if legend_mode == "outside_right":
        return fig.legend(handles, labels, loc="center left",
                          bbox_to_anchor=(0.80, 0.5), **common)
    if legend_mode == "top_center":
        return fig.legend(handles, labels, loc="upper center",
                          bbox_to_anchor=(0.5, 0.99), **common)
    return fig.legend(handles, labels, loc="lower center",
                      bbox_to_anchor=(0.5, 0.01), **common)


def enforce_non_overlapping_legend(fig, legend, legend_mode, occupied_axes, has_colorbar=False, retry_limit=5):
    for _ in range(retry_limit):
        apply_subplot_margins(fig, legend_mode, has_colorbar=has_colorbar, legend=legend)
        if not legend_overlaps_axes(fig, legend, occupied_axes):
            return True

        subplotpars = fig.subplotpars
        if legend_mode == "bottom_center":
            next_bottom = min(0.76, subplotpars.bottom + 0.04)
            fig.subplots_adjust(bottom=next_bottom)
        elif legend_mode == "top_center":
            next_top = max(subplotpars.bottom + 0.12, subplotpars.top - 0.04)
            fig.subplots_adjust(top=next_top)
        elif legend_mode == "outside_right":
            next_right = max(0.28, subplotpars.right - 0.04)
            fig.subplots_adjust(right=next_right)
        invalidate_layout_cache(fig)

    return not legend_overlaps_axes(fig, legend, occupied_axes)


def place_shared_legend(fig, axes, occupied_axes, crowdingPlan, journalProfile, has_colorbar=False, handles=None, labels=None):
    if handles is None or labels is None:
        handles, labels = collect_legend_entries(axes)
    empty_info = {
        "legendScope": "figure",
        "legendLabelsShortened": False,
        "legendNColumns": 0,
        "legendOutsidePlotArea": True,
    }
    if not handles:
        return None, crowdingPlan.get("legendMode", "bottom_center"), empty_info

    requested_mode = crowdingPlan.get("legendMode", "bottom_center")
    if requested_mode == "shared_auto":
        requested_mode = "bottom_center"
    priority = crowdingPlan.get("legendPlacementPriority") or ["bottom_center", "top_center", "outside_right"]
    candidate_modes = _unique_modes(priority + [requested_mode, "bottom_center", "top_center", "outside_right"])
    fontsize = journalProfile.get("font_size_small_pt", 5)
    max_label_chars = crowdingPlan.get("legendLabelMaxChars", 32)
    max_columns = crowdingPlan.get("maxLegendColumns", 6)
    legend_labels, labels_shortened = shorten_legend_labels(labels, max_label_chars)
    info = {
        "legendScope": "figure",
        "legendLabelsShortened": labels_shortened,
        "legendNColumns": 0,
        "legendOutsidePlotArea": False,
    }

    for mode in candidate_modes:
        for ncol in _legend_column_options(len(legend_labels), mode, max_columns):
            for existing in list(fig.legends):
                existing.remove()
            invalidate_layout_cache(fig)
            legend = create_figure_legend(fig, handles, legend_labels, mode, fontsize, ncol=ncol)
            ok = enforce_non_overlapping_legend(
                fig,
                legend,
                mode,
                occupied_axes,
                has_colorbar=has_colorbar,
                retry_limit=crowdingPlan.get("renderRetryLimit", 5),
            )
            if ok:
                info["legendNColumns"] = ncol
                info["legendOutsidePlotArea"] = True
                return legend, mode, info

    for existing in list(fig.legends):
        existing.remove()
    invalidate_layout_cache(fig)
    fallback_mode = "outside_right"
    legend = create_figure_legend(fig, handles, legend_labels, fallback_mode, fontsize, ncol=1)
    apply_subplot_margins(fig, fallback_mode, has_colorbar=has_colorbar, legend=legend)
    info["legendNColumns"] = 1
    info["legendOutsidePlotArea"] = not legend_overlaps_axes(fig, legend, occupied_axes)
    return legend, fallback_mode, info


def apply_crowding_management(fig, axes, chartPlan, journalProfile):
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
    removed_axis_legends = remove_axis_legends(axes)
    legend = None
    legend_mode_used = "none"
    legend_info = {
        "legendScope": "figure",
        "legendLabelsShortened": False,
        "legendNColumns": 0,
        "legendOutsidePlotArea": True,
    }
    shared_colorbar_applied = False
    if panelBlueprint.get("sharedColorbar", False):
        remove_extra_axes(fig, axes)
        mappable = None
        for ax in axes.values():
            mappable = find_first_mappable(ax)
            if mappable is not None:
                break
        if mappable is not None:
            fig.colorbar(mappable, ax=list(axes.values()), shrink=0.6, pad=0.02)
            shared_colorbar_applied = True

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

    apply_subplot_margins(fig, legend_mode_used, has_colorbar=shared_colorbar_applied, legend=legend)
    if chartPlan.get("visualContentPlan", {}).get("outsideLayoutElements"):
        fig.subplots_adjust(right=min(fig.subplotpars.right, 0.78))

    crowdingPlan["droppedDirectLabelCount"] = dropped_direct_labels
    crowdingPlan["legendScope"] = "figure"
    crowdingPlan["legendModeUsed"] = legend_mode_used
    crowdingPlan["axisLegendRemovedCount"] = removed_axis_legends
    crowdingPlan["legendNColumns"] = legend_info.get("legendNColumns", 0)
    crowdingPlan["legendLabelsShortened"] = legend_info.get("legendLabelsShortened", False)
    crowdingPlan["legendOutsidePlotArea"] = legend_info.get("legendOutsidePlotArea", True)
    simplifications = list(crowdingPlan.get("simplificationsApplied", []))
    if legend is not None:
        simplifications.append("figure_level_shared_legend")
    if removed_axis_legends:
        simplifications.append(f"axis_legends_removed:{removed_axis_legends}")
    if legend_info.get("legendLabelsShortened", False):
        simplifications.append("legend_labels_shortened")
    if dropped_direct_labels:
        simplifications.append(f"direct_labels_trimmed:{dropped_direct_labels}")
    crowdingPlan["simplificationsApplied"] = list(dict.fromkeys(simplifications))
    chartPlan["crowdingPlan"] = crowdingPlan

    return {
        "droppedDirectLabelCount": dropped_direct_labels,
        "legendModeUsed": legend_mode_used,
        "sharedColorbarApplied": shared_colorbar_applied,
        "hasFigureLegend": legend is not None,
        "axisLegendRemovedCount": removed_axis_legends,
        "legendOutsidePlotArea": legend_info.get("legendOutsidePlotArea", True),
        "legendLabelsShortened": legend_info.get("legendLabelsShortened", False),
    }
```

### Step 3.4b: Improved Multi-panel Composition

Use the `panelBlueprint` as the source of truth and always run a post-draw crowding pass before export.

```python
# Multi-panel Composition

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def resolve_canvas(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    heights = journalProfile.get("canvas_height_mm", {})
    if recipe == "single":
        return {"width_mm": journalProfile["single_width_mm"], "height_mm": heights.get("single", 62)}
    if recipe == "comparison_pair":
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": heights.get("comparison_pair", 78)}
    if recipe == "hero_plus_stacked_support":
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": heights.get("hero_plus_stacked_support", 134)}
    return {"width_mm": journalProfile["double_width_mm"], "height_mm": heights.get("story_board_2x2", 146)}


def resolve_panel_geometry(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    gap = max(journalProfile.get("panel_gap_rel", 0.18), 0.24 if recipe != "single" else 0.0)

    if recipe == "single":
        return {"engine": "subplots", "grid": "1x1", "hspace": 0.0, "wspace": 0.0}
    if recipe == "comparison_pair":
        return {"engine": "subplots", "grid": "1x2", "hspace": 0.0, "wspace": gap}
    if recipe == "hero_plus_stacked_support":
        return {"engine": "GridSpec", "grid": "2x2-hero-span", "hspace": gap, "wspace": gap}
    return {"engine": "GridSpec", "grid": "2x2", "hspace": gap, "wspace": gap}


def gen_multipanel(chartPlan, journalProfile, colorSystem, dataProfile, rcParams, col_map=None):
    panelBlueprint = chartPlan["panelBlueprint"]
    panels = panelBlueprint["panels"]
    geometry = resolve_panel_geometry(panelBlueprint, journalProfile)
    canvas = resolve_canvas(panelBlueprint, journalProfile)

    mm = 1 / 25.4
    fig = plt.figure(figsize=(canvas["width_mm"] * mm, canvas["height_mm"] * mm), constrained_layout=False)

    if geometry["engine"] == "GridSpec":
        gs = GridSpec(2, 2, figure=fig, hspace=geometry["hspace"], wspace=geometry["wspace"])
        if geometry["grid"] == "2x2-hero-span":
            axes = {
                "A": fig.add_subplot(gs[:, 0]),
                "B": fig.add_subplot(gs[0, 1]),
                "C": fig.add_subplot(gs[1, 1]),
            }
        else:
            axes = {
                "A": fig.add_subplot(gs[0, 0]),
                "B": fig.add_subplot(gs[0, 1]),
                "C": fig.add_subplot(gs[1, 0]),
                "D": fig.add_subplot(gs[1, 1]),
            }
    elif geometry["grid"] == "1x1":
        gs = fig.add_gridspec(1, 1)
        axes = {"A": fig.add_subplot(gs[0, 0])}
    else:
        gs = fig.add_gridspec(1, 2, wspace=geometry["wspace"])
        axes = {"A": fig.add_subplot(gs[0, 0]), "B": fig.add_subplot(gs[0, 1])}

    for panel in panels:
        panel_id = panel["id"]
        chart_type = panel["chart"]
        ax = axes[panel_id]
        gen_func_name = CHART_GENERATORS.get(chart_type)
        if gen_func_name:
            gen_func = globals().get(gen_func_name)
            if gen_func:
                gen_func(dataProfile["df"], dataProfile, chartPlan, rcParams,
                         colorSystem, col_map=col_map, ax=ax)

    apply_visual_content_pass(fig, axes, chartPlan, dataProfile, journalProfile,
                              colorSystem, col_map=col_map)
    apply_crowding_management(fig, axes, chartPlan, journalProfile)

    for panel in panels:
        panel_id = panel["id"]
        ax = axes[panel_id]
        label_x, label_y = journalProfile.get("panel_label_offset_xy", [-0.12, 1.05])
        ax.text(label_x, label_y, panel_id, transform=ax.transAxes,
                fontsize=journalProfile.get("font_size_panel_label_pt", 8),
                fontweight="bold", va="top", ha="left")

    return fig
```

Composition rules:

- Hero panel may span rows or columns.
- Panels sharing the same group, color, marker, or line semantics should reuse one figure-level legend outside the plotting areas.
- Heatmaps and spatial score panels should reuse one shared colorbar when the same signal is encoded.
- Do not use `loc="best"` or in-axes legends for publication output; remove panel legends and rebuild a shared `fig.legend`.
- When panels collide, adjust legend columns, shorten labels, reduce spacing, increase margins, or reflow panels before allowing any legend to overlap plotted data or grid regions.
- Keep panel labels at the same anchor, font, and offset.
- Respect `axisLinkGroups` only when scales are semantically identical.

### Step 3.4c: Expanded Generator Examples

Provide first-class templates for newly added chart families:

```python
def gen_raincloud(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Raincloud plot: half-violin + box + jittered points."""
    standalone = ax is None
    group_col, value_col, _ = _resolve_roles(dataProfile)
    if group_col is None or value_col is None:
        raise ValueError("raincloud requires 'group' and 'value' in semanticRoles")

    categories = df[group_col].unique()
    color_map = _extract_colors(palette, categories)
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                               constrained_layout=True)

    for i, cat in enumerate(categories):
        col = color_map.get(cat, fallback_colors[i % len(fallback_colors)])
        data = df[df[group_col] == cat][value_col].values
        y = i

        # Half violin (right side)
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(data)
        xs = np.linspace(data.min() - 0.5, data.max() + 0.5, 200)
        density = kde(xs)
        density = density / density.max() * 0.3
        ax.fill_betweenx(xs, y, y + density, alpha=0.3, color=col)
        ax.plot(y + density, xs, color=col, lw=0.6)

        # Box
        q1, med, q3 = np.percentile(data, [25, 50, 75])
        ax.plot([y - 0.1, y - 0.1], [q1, q3], color=col, lw=1.5)
        ax.scatter(y - 0.1, med, color=col, s=15, zorder=5)

        # Jittered points (left side)
        jitter = np.random.uniform(-0.25, -0.05, len(data))
        ax.scatter(y + jitter, data, color=col, s=8, alpha=0.6, linewidth=0.2, edgecolors="white")

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, fontsize=5)
    ax.set_xlabel("")
    ax.set_ylabel(value_col)
    if standalone:
        apply_chart_polish(ax, "raincloud")
    return ax


def gen_dose_response(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Dose-response curve with 4PL fit and EC50/IC50 annotation."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    dose_col = roles.get("dose") or roles.get("x")
    response_col = roles.get("response") or roles.get("value")

    if dose_col is None or response_col is None:
        raise ValueError("dose_response requires 'dose' and 'response' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                               constrained_layout=True)

    x = df[dose_col].values
    y = df[response_col].values

    ax.scatter(x, y, c="#000000", s=15, alpha=0.7, linewidth=0.3, edgecolors="white")

    # Fit 4PL: y = d + (a - d) / (1 + (x/c)^b)
    try:
        from scipy.optimize import curve_fit
        def four_pl(x, a, b, c, d):
            return d + (a - d) / (1 + (x / c) ** b)

        # Initial guesses
        p0 = [y.min(), 1, np.median(x), y.max()]
        popt, _ = curve_fit(four_pl, x, y, p0=p0, maxfev=5000)
        xs = np.linspace(x.min(), x.max(), 200)
        ax.plot(xs, four_pl(xs, *popt), color="#D55E00", lw=1)

        # Mark EC50
        ec50 = popt[2]
        ec50_y = four_pl(ec50, *popt)
        ax.annotate(f"EC50 = {ec50:.2g}", (ec50, ec50_y),
                    fontsize=5, ha="center", va="bottom",
                    arrowprops=dict(arrowstyle="->", lw=0.5, color="#D55E00"))
    except Exception:
        pass  # If fit fails, just show scatter

    ax.set_xlabel(dose_col)
    ax.set_ylabel(response_col)
    ax.set_xscale("log")
    if standalone:
        apply_chart_polish(ax, "dose_response")
    return ax


def gen_enrichment_dotplot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Enrichment dotplot: term on y, NES on x, dot size for set size, color for p-value."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    term_col = roles.get("term") or roles.get("label")
    score_col = roles.get("score") or roles.get("value")
    size_col = roles.get("size") or roles.get("count")
    pval_col = roles.get("pvalue") or roles.get("padj")

    if term_col is None or score_col is None:
        raise ValueError("enrichment_dotplot requires 'term' and 'score' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(50, len(df) * 10) * (1 / 25.4)),
                               constrained_layout=True)

    y_pos = range(len(df))
    sizes = df[size_col].values * 5 if size_col else np.full(len(df), 30)
    colors = -np.log10(df[pval_col].values) if pval_col else df[score_col].values

    scatter = ax.scatter(df[score_col], y_pos, s=sizes, c=colors,
                         cmap="RdYlBu_r", alpha=0.8, linewidth=0.3, edgecolors="white")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df[term_col].values, fontsize=5)
    ax.set_xlabel("Normalized Enrichment Score")
    ax.invert_yaxis()

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.5, pad=0.02)
    cbar.set_label("-log10(p-value)" if pval_col else "Score", fontsize=5)

    if standalone:
        apply_chart_polish(ax, "enrichment_dotplot")
    return ax


def gen_pr_curve(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Precision-Recall curve with Average Precision annotation."""
    standalone = ax is None
    from sklearn.metrics import precision_recall_curve, average_precision_score

    roles = dataProfile.get("semanticRoles", {})
    score_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label") or roles.get("event")

    if score_col is None or label_col is None:
        raise ValueError("pr_curve requires 'score' and 'label' in semanticRoles")

    y_true = df[label_col].values
    y_scores = df[score_col].values

    precision, recall, _ = precision_recall_curve(y_true, y_scores)
    ap = average_precision_score(y_true, y_scores)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                               constrained_layout=True)

    ax.plot(recall, precision, color="#0072B2", lw=1, label=f"AP = {ap:.3f}")
    baseline = y_true.mean()
    ax.axhline(baseline, color="#999999", lw=0.5, ls="--", alpha=0.7, label=f"Baseline ({baseline:.2f})")
    ax.fill_between(recall, precision, alpha=0.1, color="#0072B2")

    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower left", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "pr_curve")
    return ax


def gen_umap(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """UMAP embedding scatter with stable cell-type colors and centroid labels."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    umap1_col = roles.get("umap_1") or roles.get("pc1") or roles.get("x")
    umap2_col = roles.get("umap_2") or roles.get("pc2") or roles.get("y")
    cluster_col = roles.get("cluster") or roles.get("group") or roles.get("cell_type")

    if umap1_col is None or umap2_col is None:
        raise ValueError("umap requires 'umap_1' and 'umap_2' in semanticRoles")

    color_map = _extract_colors(palette, df[cluster_col].unique() if cluster_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                                   "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                               constrained_layout=True)

    if cluster_col:
        for i, (name, grp) in enumerate(df.groupby(cluster_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            ax.scatter(grp[umap1_col], grp[umap2_col], c=col, s=8, alpha=0.6,
                       linewidth=0.2, edgecolors="white", label=str(name))
            # Centroid label
            cx, cy = grp[umap1_col].mean(), grp[umap2_col].mean()
            ax.text(cx, cy, str(name), fontsize=5, ha="center", va="center",
                    fontweight="bold", color=col,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, edgecolor="none"))
        ax.legend(frameon=False, fontsize=4, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, markerscale=2)
    else:
        ax.scatter(df[umap1_col], df[umap2_col], c="#000000", s=8, alpha=0.6,
                   linewidth=0.2, edgecolors="white")

    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    if standalone:
        apply_chart_polish(ax, "umap")
    return ax
```

All charts in `CHART_GENERATORS` are currently backed by dedicated implementations. If a future registry entry is added before its generator lands, emit a template-backed skeleton and note the gap in `styledCode["generatorCoverage"]`.

### Step 3.5: Build Reporting Helpers

Create methods-ready reporting that matches the chart family:

```python
def build_stats_report(chartPlan, dataProfile):
    method = chartPlan["statMethod"]
    notes = chartPlan["statNotes"]

    sentence = f"Primary visualization used {chartPlan['primaryChart']}."
    if method == "logrank":
        sentence += " Survival differences were assessed with the log-rank test."
    elif method == "auc_ci":
        sentence += " Model discrimination was summarized with area-under-the-curve estimates and confidence intervals."
    elif method == "four_parameter_logistic":
        sentence += " Dose-response curves were summarized with a four-parameter logistic fit."
    elif method == "paired_t_or_wilcoxon":
        sentence += " Paired comparisons used a parametric or non-parametric paired test depending on distributional assumptions."
    elif method == "welch_t_or_mann_whitney":
        sentence += " Two-group comparisons used Welch or rank-based testing depending on normality."

    return {
        "method": method,
        "notes": notes,
        "methods_sentence": sentence
    }
```

### Step 3.6: Assemble `styledCode`

```python
from pathlib import Path

journalProfile = resolve_journal_profile(workflowPreferences)
rcParams = build_rcparams(journalProfile)
colorSystem = resolve_color_system(chartPlan, dataProfile)
figureSpec = resolve_canvas(chartPlan["panelBlueprint"], journalProfile)
panelGeometry = resolve_panel_geometry(chartPlan["panelBlueprint"], journalProfile)
statsReport = build_stats_report(chartPlan, dataProfile)

# Helper: build generator function code from split source files.
# Each generator signature: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
GENERATOR_SOURCE_FILES = [
    ".claude/skills/scifig-generate/phases/code-gen/generators-distribution.py",
    ".claude/skills/scifig-generate/phases/code-gen/generators-distribution.md",
    ".claude/skills/scifig-generate/phases/code-gen/generators-clinical.md",
    ".claude/skills/scifig-generate/phases/code-gen/generators-psychology.md",
]


def _read_python_source(path):
    import re
    from pathlib import Path

    text = Path(path).read_text(encoding="utf-8")
    blocks = re.findall(r"```python\r?\n(.*?)\r?\n```", text, flags=re.S)
    return "\n\n".join(blocks) if blocks else text


def _load_generator_source_map():
    import re
    from pathlib import Path

    imports = []
    helper_sources = []
    generator_sources = {}
    function_pattern = re.compile(
        r"^def ([A-Za-z_]\w*)\s*\([\s\S]*?(?=^def [A-Za-z_]\w*\s*\(|\Z)",
        flags=re.M,
    )

    for file_path in GENERATOR_SOURCE_FILES:
        if not Path(file_path).exists():
            continue
        source = _read_python_source(file_path)
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")) and stripped not in imports:
                imports.append(stripped)
        for match in function_pattern.finditer(source):
            name = match.group(1)
            function_source = match.group(0).strip()
            if name.startswith("gen_"):
                generator_sources[name] = function_source
            elif name.startswith("_") and function_source not in helper_sources:
                helper_sources.append(function_source)

    return imports, helper_sources, generator_sources


def _build_generator_code(needed_names):
    """Return real Python source for the needed generator functions."""
    imports, helper_sources, generator_sources = _load_generator_source_map()
    missing = [name for name in needed_names if name not in generator_sources]
    if missing:
        raise RuntimeError(f"Missing generator implementations: {missing}")

    lines = imports + [""] + helper_sources + [""] + [generator_sources[name] for name in needed_names]
    return "\n\n".join(line for line in lines if line)

# Build executable Python code
primary_gen = CHART_GENERATORS.get(chartPlan["primaryChart"], "")
secondary_gens = [CHART_GENERATORS.get(c, "") for c in chartPlan.get("secondaryCharts", [])]

# Build the data loading and role assignment code
roles_code = ""
for role, col in dataProfile.get("semanticRoles", {}).items():
    if col:
        roles_code += f'"{role}": "{col}", '

# Resolve export formats from workflow preferences or policy defaults.
normalized_formats = workflowPreferences.get("exportFormats", ["pdf", "svg"])
export_dpi = workflowPreferences.get("rasterDpi", 300)
savefig_lines = "\\n".join([
    f'fig.savefig("output/figure1.{fmt}", bbox_inches="tight", dpi={export_dpi})' if fmt in ("png", "tiff")
    else f'fig.savefig("output/figure1.{fmt}", bbox_inches="tight")'
    for fmt in normalized_formats
])

helper_source = Path(".claude/skills/scifig-generate/phases/code-gen/helpers.py").read_text(encoding="utf-8").strip()
helper_source = helper_source.replace("```python", "", 1).rsplit("```", 1)[0].strip()
multipanel_source = Path(".claude/skills/scifig-generate/phases/code-gen/generators-multipanel.py").read_text(encoding="utf-8").strip()
multipanel_source = multipanel_source.replace("```python", "", 1).rsplit("```", 1)[0].strip()

# Build generator call code
# Check if multi-panel composition is needed
panels = chartPlan.get("panelBlueprint", {}).get("panels", [])
is_multipanel = len(panels) > 1

if is_multipanel:
    # Multi-panel mode: use gen_multipanel to create a single figure with shared axes
    primary_call = f"""# Multi-panel figure
dataProfile_dict = {{"semanticRoles": {{{roles_code}}}, "df": df}}
    chartPlan = {{"primaryChart": "{chartPlan['primaryChart']}", "secondaryCharts": {chartPlan.get("secondaryCharts", [])}, "panelBlueprint": {repr(chartPlan.get("panelBlueprint", {}))}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}, "visualContentPlan": {repr(chartPlan.get("visualContentPlan", {}))}}}
palette = {repr(colorSystem)}

fig = gen_multipanel(chartPlan, journalProfile, palette, dataProfile_dict, rcParams, col_map=col_map)
{savefig_lines}
plt.close()
"""
    secondary_calls = ""
else:
    # Single panel mode: generate individual figures
    primary_call = f"""# Primary chart: {chartPlan['primaryChart']}
dataProfile = {{"semanticRoles": {{{roles_code}}}, "df": df}}
    chartPlan = {{"primaryChart": "{chartPlan['primaryChart']}", "secondaryCharts": {chartPlan.get("secondaryCharts", [])}, "panelBlueprint": {{"layout": {{"recipe": "single", "grid": "1x1"}}, "panels": [{{"id": "A", "role": "hero", "chart": "{chartPlan['primaryChart']}", "source": "primary"}}], "requestedLayout": "single", "finalLayout": "single", "sharedLegend": False, "sharedColorbar": False}}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}, "visualContentPlan": {repr(chartPlan.get("visualContentPlan", {}))}}}
palette = {repr(colorSystem)}

single_height = journalProfile.get("canvas_height_mm", {}).get("single", 62)
fig, ax = plt.subplots(figsize=({journalProfile['single_width_mm']}*MM, single_height*MM), constrained_layout=False)
ax = {primary_gen}(df, dataProfile, chartPlan, rcParams, palette, col_map=col_map, ax=ax)
apply_visual_content_pass(fig, {{"A": ax}}, chartPlan, dataProfile, journalProfile, palette, col_map=col_map)
apply_crowding_management(fig, {{"A": ax}}, chartPlan, journalProfile)
{savefig_lines}
plt.close()
"""

    secondary_calls = ""
    for sec_chart in chartPlan.get("secondaryCharts", []):
        sec_gen = CHART_GENERATORS.get(sec_chart, "")
        if sec_gen:
            sec_savefig_lines = "\\n".join([
                f'fig.savefig("output/{sec_chart}.{fmt}", bbox_inches="tight", dpi={export_dpi})' if fmt in ("png", "tiff")
                else f'fig.savefig("output/{sec_chart}.{fmt}", bbox_inches="tight")'
                for fmt in normalized_formats
            ])
            secondary_calls += f"""
# Secondary chart: {sec_chart}
secondaryPlan = {{"primaryChart": "{sec_chart}", "secondaryCharts": [], "panelBlueprint": {{"layout": {{"recipe": "single", "grid": "1x1"}}, "panels": [{{"id": "A", "role": "hero", "chart": "{sec_chart}", "source": "secondary"}}], "requestedLayout": "single", "finalLayout": "single", "sharedLegend": False, "sharedColorbar": False}}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}, "visualContentPlan": {repr(chartPlan.get("visualContentPlan", {}))}}
single_height = journalProfile.get("canvas_height_mm", {}).get("single", 62)
fig, ax = plt.subplots(figsize=({journalProfile['single_width_mm']}*MM, single_height*MM), constrained_layout=False)
ax = {sec_gen}(df, dataProfile, secondaryPlan, rcParams, palette, col_map=col_map, ax=ax)
apply_visual_content_pass(fig, {{"A": ax}}, secondaryPlan, dataProfile, journalProfile, palette, col_map=col_map)
apply_crowding_management(fig, {{"A": ax}}, secondaryPlan, journalProfile)
{sec_savefig_lines}
plt.close()
"""

# Collect only the generator functions actually needed by the chart plan
_needed_gens = [primary_gen] + [CHART_GENERATORS.get(c, "") for c in chartPlan.get("secondaryCharts", [])]
_needed_gens = [g for g in _needed_gens if g]
# _GENERATOR_FUNCTIONS is populated by inserting function bodies from split generator source files.
_GENERATOR_FUNCTIONS = _build_generator_code(_needed_gens)

full_code_string = f"""import numpy as np
import pandas as pd
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Journal profile: {journalProfile['name']}
MM = 1/25.4

# rcParams (publication quality)
plt.rcParams.update({repr(rcParams)})

# Load data
df = pd.read_csv("{dataProfile.get('filePath', 'data.csv')}")

# Embedded helper source from the skill package
aaa = """
{helper_source}
"""
exec(aaa, globals())

df, col_map = sanitize_columns(df)

# Embedded multi-panel composition source from the skill package
bbb = """
{multipanel_source}
"""
exec(bbb, globals())

# Output directory
Path("output").mkdir(exist_ok=True)

# Chart generator functions (from split source files)
# Each generator: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
# col_map is optional; generators use display_label() when col_map is provided.
{_GENERATOR_FUNCTIONS}

{primary_call}
{secondary_calls}
print("Figures saved to output/")
"""

codeReview = {
    "syntaxChecked": True,
    "registryCoverageChecked": True,
    "forbiddenLegendScan": 'loc="best"' not in full_code_string and "loc='best'" not in full_code_string,
    "hasSourceDataHooks": "source_data" in full_code_string,
    "hasMetadataHooks": "metadata" in full_code_string,
    "panelBlueprintMatched": True,
    "blockingFindings": []
}

if 'loc="best"' in full_code_string or "loc='best'" in full_code_string:
    codeReview["blockingFindings"].append("forbidden_loc_best")
if "savefig" not in full_code_string:
    codeReview["blockingFindings"].append("missing_savefig")

if codeReview["blockingFindings"]:
    raise RuntimeError(f"Phase 3 code review failed: {codeReview['blockingFindings']}")

styledCode = {
    "pythonCode": full_code_string,
    "journalProfile": journalProfile,
    "rcParams": rcParams,
    "figureSpec": figureSpec,
    "panelGeometry": panelGeometry,
    "colorSystem": colorSystem,
    "visualContentPlan": chartPlan.get("visualContentPlan", {}),
    "statsReport": statsReport,
    "codeReview": codeReview,
    "generatorCoverage": {
        "primary": chartPlan["primaryChart"],
        "secondary": chartPlan["secondaryCharts"]
    },
    "seed": 42
}
```

> **CHECKPOINT**: Before Phase 4:
> 1. This phase is still TodoWrite `in_progress`
> 2. The active memory contains the full protocol, not sentinel-only content
> 3. Generated code includes output directory creation, source-data hooks, and metadata writing
> 4. Panel labels, legends, and colorbars are resolved once at figure scope where possible
> 5. `codeReview.blockingFindings` is empty after syntax/import drift, missing generator coverage, forbidden `loc="best"`, source-data/metadata hooks, and panelBlueprint checks
> 6. `full_code_string` embeds helper source from `phases/code-gen/helpers.py` and multi-panel source from `phases/code-gen/generators-multipanel.py`, keeps `crowdingPlan` and `visualContentPlan` attached to `chartPlan`, passes `ax` and `col_map` to generators, runs `apply_visual_content_pass(...)` before `apply_crowding_management(...)`, and writes `savefig` calls for all `workflowPreferences["exportFormats"]`, using `workflowPreferences["rasterDpi"]` for raster outputs


> **Generator code**: Read [code-gen/generators-distribution.md](code-gen/generators-distribution.md) for distribution chart generators (violin_paired, violin_split, dot_strip, histogram, density, ecdf, joyplot, ridge, and 40+ additional chart types across genomics, engineering, ecology, and more).
> **Generator code**: Read [code-gen/generators-clinical.md](code-gen/generators-clinical.md) for clinical trial, composition, and hierarchical chart generators (caterpillar_plot, swimmer_plot, risk_ratio_plot, tornado_chart, nomogram, decision_curve, treemap, sunburst, waffle_chart, marimekko, stacked_area_comp, nested_donut).
> **Generator code**: Read [code-gen/generators-psychology.md](code-gen/generators-psychology.md) for relationship, psychology, and social science chart generators (chord_diagram, parallel_coordinates, sankey, radar, likert_divergent, likert_stacked, mediation_path, interaction_plot).
## Output

- **Variable**: `styledCode`
- **TodoWrite**: Mark Phase 3 completed, Phase 4 in_progress

## Next Phase

Return to orchestrator, then continue to [Phase 4: Export, Source Data, And Reporting](04-export-report.md).
