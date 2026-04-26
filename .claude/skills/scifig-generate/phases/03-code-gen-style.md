# Phase 3: Code Generation, Journal Styling, And Composition

> **COMPACT SENTINEL [Phase 3: code-gen-style]**
> This phase contains 6 execution steps (Step 3.1 - 3.6, with 3.4b and 3.4c sub-protocols).
> If you can read this sentinel but cannot find the full Step protocol below, context has been compressed.
> Recovery: `Read("phases/03-code-gen-style.md")`

Generate complete Python code that applies journal style tokens, resolves a palette system, composes multi-panel figures, and writes reproducibility-friendly outputs.

## Objective

- Resolve a concrete journal profile for Nature-like, Cell-like, or Science-like output
- Resolve a stable color system from `palettePlan`
- Generate chart-specific code and a panel composition scaffold
- Improve multi-panel geometry, shared legends, shared colorbars, and panel-label discipline
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

Read `specs/journal-profiles.md` and convert the selected profile into plotting tokens.

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
        "panel_gap_rel": 0.22
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

### Post-plot polish function (call after every chart generator)

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


def default_crowding_plan():
    return {
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
        "simplificationsApplied": [],
        "droppedDirectLabelCount": 0,
    }


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


def _bbox_in_figure_coords(fig, artist):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    return artist.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())


def legend_overlaps_axes(fig, legend, axes):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend_box = legend.get_window_extent(renderer=renderer)
    return any(legend_box.overlaps(ax.get_window_extent(renderer=renderer)) for ax in axes)


def apply_subplot_margins(fig, legend_mode, has_colorbar=False, legend=None):
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


def enforce_non_overlapping_legend(fig, legend, legend_mode, occupied_axes, has_colorbar=False):
    for _ in range(8):
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
            legend = create_figure_legend(fig, handles, legend_labels, mode, fontsize, ncol=ncol)
            ok = enforce_non_overlapping_legend(
                fig,
                legend,
                mode,
                occupied_axes,
                has_colorbar=has_colorbar,
            )
            if ok:
                info["legendNColumns"] = ncol
                info["legendOutsidePlotArea"] = True
                return legend, mode, info

    for existing in list(fig.legends):
        existing.remove()
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

    apply_crowding_management(fig, axes, chartPlan, journalProfile)

    for panel in panels:
        panel_id = panel["id"]
        ax = axes[panel_id]
        ax.text(-0.12, 1.05, panel_id, transform=ax.transAxes,
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

If a chart is in `CHART_GENERATORS` but not yet backed by a dedicated implementation, emit a template-backed skeleton and note the gap in `styledCode["generatorCoverage"]`.

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
journalProfile = resolve_journal_profile(workflowPreferences)
rcParams = build_rcparams(journalProfile)
colorSystem = resolve_color_system(chartPlan, dataProfile)
figureSpec = resolve_canvas(chartPlan["panelBlueprint"], journalProfile)
panelGeometry = resolve_panel_geometry(chartPlan["panelBlueprint"], journalProfile)
statsReport = build_stats_report(chartPlan, dataProfile)

# Helper: build generator function code from the registry of implemented generators
# Generator functions are defined in Step 3.4d and collected here for inclusion in full_code_string
def _build_generator_code(needed_names):
    """Return Python source for the needed generator functions.
    If a generator has a full implementation (from Step 3.4d), include it.
    Otherwise emit a stub that raises NotImplementedError."""
    # Map of generator name -> function body source (populated from Step 3.4d definitions)
    # Each generator signature: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
    generator_sources = {}  # Populated at runtime from the implemented generators
    lines = []
    for name in needed_names:
        if name in generator_sources:
            lines.append(generator_sources[name])
        else:
            lines.append(f"""def {name}(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    \"\"\"Stub for {name} - replace with full implementation from Step 3.4d.\"\"\"
    raise NotImplementedError("{name} generator not yet implemented")
""")
    return "\\n".join(lines)

# Build executable Python code
primary_gen = CHART_GENERATORS.get(chartPlan["primaryChart"], "")
secondary_gens = [CHART_GENERATORS.get(c, "") for c in chartPlan.get("secondaryCharts", [])]

# Build the data loading and role assignment code
roles_code = ""
for role, col in dataProfile.get("semanticRoles", {}).items():
    if col:
        roles_code += f'"{role}": "{col}", '

# Resolve export formats (default pdf + svg)
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
chartPlan = {{"primaryChart": "{chartPlan['primaryChart']}", "secondaryCharts": {chartPlan.get("secondaryCharts", [])}, "panelBlueprint": {repr(chartPlan.get("panelBlueprint", {}))}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}}}
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
chartPlan = {{"primaryChart": "{chartPlan['primaryChart']}", "secondaryCharts": {chartPlan.get("secondaryCharts", [])}, "panelBlueprint": {{"layout": {{"recipe": "single", "grid": "1x1"}}, "panels": [{{"id": "A", "role": "hero", "chart": "{chartPlan['primaryChart']}", "source": "primary"}}], "requestedLayout": "single", "finalLayout": "single", "sharedLegend": False, "sharedColorbar": False}}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}}}
palette = {repr(colorSystem)}

fig, ax = plt.subplots(figsize=({journalProfile['single_width_mm']}*MM, 60*MM), constrained_layout=False)
ax = {primary_gen}(df, dataProfile, chartPlan, rcParams, palette, col_map=col_map)
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
secondaryPlan = {{"primaryChart": "{sec_chart}", "secondaryCharts": [], "panelBlueprint": {{"layout": {{"recipe": "single", "grid": "1x1"}}, "panels": [{{"id": "A", "role": "hero", "chart": "{sec_chart}", "source": "secondary"}}], "requestedLayout": "single", "finalLayout": "single", "sharedLegend": False, "sharedColorbar": False}}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}}
fig, ax = plt.subplots(figsize=({journalProfile['single_width_mm']}*MM, 60*MM), constrained_layout=False)
ax = {sec_gen}(df, dataProfile, secondaryPlan, rcParams, palette, col_map=col_map)
apply_crowding_management(fig, {{"A": ax}}, secondaryPlan, journalProfile)
{sec_savefig_lines}
plt.close()
"""

# Collect only the generator functions actually needed by the chart plan
_needed_gens = [primary_gen] + [CHART_GENERATORS.get(c, "") for c in chartPlan.get("secondaryCharts", [])]
_needed_gens = [g for g in _needed_gens if g]
# _GENERATOR_FUNCTIONS will be populated by inserting the function bodies from Step 3.4d
# For now, use a stub that raises if a generator is missing
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

# Chart generator functions (from Step 3.4d definitions)
# Each generator: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
# col_map is optional; generators use display_label() when col_map is provided.
{_GENERATOR_FUNCTIONS}

{primary_call}
{secondary_calls}
print("Figures saved to output/")
"""

styledCode = {
    "pythonCode": full_code_string,
    "journalProfile": journalProfile,
    "rcParams": rcParams,
    "figureSpec": figureSpec,
    "panelGeometry": panelGeometry,
    "colorSystem": colorSystem,
    "statsReport": statsReport,
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
> 5. `full_code_string` embeds helper source from `phases/code-gen/helpers.py` and multi-panel source from `phases/code-gen/generators-multipanel.py`, keeps `crowdingPlan` attached to `chartPlan`, passes `col_map` to generators, and writes `savefig` calls for all `workflowPreferences["exportFormats"]`, using `workflowPreferences["rasterDpi"]` for raster outputs

### Step 3.4d: Distribution Chart Generators (Implemented)

The following 8 generators provide production-ready templates for distribution chart types registered in `CHART_GENERATORS`. Each follows the Nature/Cell style contract: open-L spines, no grid, round line caps, publication font sizes, and `apply_chart_polish` post-processing.

```python
# ──────────────────────────────────────────────────────────────
# Distribution Chart Generators
# Signature: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
# Each returns the matplotlib Axes for multi-panel composition.
# col_map: optional dict mapping sanitized column names -> original display labels.
# Use display_label(col, col_map) to get the human-readable label for axis/legend text.
# ──────────────────────────────────────────────────────────────

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.collections import PolyCollection


def _resolve_roles(dataProfile):
    """Extract semantic roles from dataProfile."""
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")
    x_col = roles.get("x") or roles.get("condition")
    return group_col, value_col, x_col


def _extract_colors(palette, categories):
    """Build a color map from palette for the given categories."""
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


def gen_histogram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Grouped histogram with overlaid KDE density curves.

    Supports 1-6 groups. Uses Freedman-Diaconis bin width with a floor of
    10 bins.  KDE overlay uses Gaussian kernel with Scott bandwidth.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("histogram requires a numeric value column in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                               constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)

        for cat in categories:
            subset = df[df[group_col] == cat][value_col].dropna()
            color = color_map[cat]
            # Freedman-Diaconis bin width
            iqr = subset.quantile(0.75) - subset.quantile(0.25)
            bin_width = 2 * iqr * len(subset) ** (-1 / 3) if iqr > 0 else 0.1
            n_bins = max(10, int(np.ceil((subset.max() - subset.min()) / bin_width))) if bin_width > 0 else 15

            ax.hist(subset, bins=n_bins, density=True, alpha=0.35,
                    color=color, edgecolor="white", linewidth=0.4, label=cat)
            # KDE overlay
            sns.kdeplot(subset, ax=ax, color=color, linewidth=0.8,
                        clip=(subset.min() - 0.5 * bin_width,
                              subset.max() + 0.5 * bin_width))
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    else:
        values = df[value_col].dropna()
        iqr = values.quantile(0.75) - values.quantile(0.25)
        bin_width = 2 * iqr * len(values) ** (-1 / 3) if iqr > 0 else 0.1
        n_bins = max(10, int(np.ceil((values.max() - values.min()) / bin_width))) if bin_width > 0 else 15
        color = palette.get("categorical", ["#000000"])[0]

        ax.hist(values, bins=n_bins, density=True, alpha=0.35,
                color=color, edgecolor="white", linewidth=0.4)
        sns.kdeplot(values, ax=ax, color=color, linewidth=0.8)

    ax.set_xlabel(display_label(value_col, col_map) if col_map else value_col)
    ax.set_ylabel("Density")
    if standalone:
        apply_chart_polish(ax, "histogram")
    return ax


def gen_density(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Kernel density estimation for multiple groups.

    Uses Gaussian kernel with Silverman bandwidth.  Each group gets a filled
    KDE with controlled opacity so overlapping distributions remain legible.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("density requires a numeric value column in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                               constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)

        for cat in categories:
            subset = df[df[group_col] == cat][value_col].dropna()
            color = color_map[cat]
            sns.kdeplot(subset, ax=ax, fill=True, alpha=0.3,
                        color=color, linewidth=0.8, label=cat)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    else:
        values = df[value_col].dropna()
        color = palette.get("categorical", ["#000000"])[0]
        sns.kdeplot(values, ax=ax, fill=True, alpha=0.3,
                    color=color, linewidth=0.8)

    ax.set_xlabel(value_col)
    ax.set_ylabel("Density")
    if standalone:
        apply_chart_polish(ax, "density")
    return ax


def gen_ecdf(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Empirical cumulative distribution function for comparing groups.

    Step-function CDF (no smoothing).  Each group drawn in its palette color
    with a thin line to preserve legibility when many groups overlap.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("ecdf requires a numeric value column in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                               constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)

        for cat in categories:
            subset = df[df[group_col] == cat][value_col].dropna()
            color = color_map[cat]
            sorted_vals = np.sort(subset)
            ecdf_y = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
            ax.step(sorted_vals, ecdf_y, where="post", color=color,
                    linewidth=0.8, label=cat)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    else:
        values = df[value_col].dropna()
        color = palette.get("categorical", ["#000000"])[0]
        sorted_vals = np.sort(values)
        ecdf_y = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        ax.step(sorted_vals, ecdf_y, where="post", color=color, linewidth=0.8)

    ax.set_xlabel(value_col)
    ax.set_ylabel("Cumulative proportion")
    ax.set_ylim(0, 1.05)
    if standalone:
        apply_chart_polish(ax, "ecdf")
    return ax


def gen_ridge(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Ridgeline / joy plot for many groups.

    Overlapping density ridges stacked vertically.  Uses Gaussian KDE with
    shared bandwidth across groups.  Groups ordered by median value.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("ridge requires a numeric value column in semanticRoles")
    if group_col is None:
        raise ValueError("ridge requires a group column in semanticRoles")

    categories = df[group_col].dropna().unique().tolist()
    # Sort by median value for visual ordering
    medians = df.groupby(group_col)[value_col].median()
    categories = sorted(categories, key=lambda c: medians.get(c, 0))
    color_map = _extract_colors(palette, categories)

    n_groups = len(categories)
    fig_height = max(60, 15 * n_groups) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                               constrained_layout=True)

    # Shared x range and bandwidth
    all_vals = df[value_col].dropna()
    x_min, x_max = all_vals.min(), all_vals.max()
    x_pad = (x_max - x_min) * 0.1
    x_grid = np.linspace(x_min - x_pad, x_max + x_pad, 300)

    overlap = 0.75  # fraction of ridge height that overlaps with neighbor
    heights = []

    for i, cat in enumerate(categories):
        subset = df[df[group_col] == cat][value_col].dropna()
        color = color_map[cat]

        # Gaussian KDE
        sigma = subset.std() * len(subset) ** (-1 / 5)  # Silverman bandwidth
        if sigma == 0:
            sigma = 0.1
        density = np.exp(-0.5 * ((x_grid - subset.mean()) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
        # Normalize density to unit max for consistent ridge height
        density = density / density.max() if density.max() > 0 else density

        ridge_height = 1.0
        baseline = i * (1 - overlap)
        heights.append(baseline + ridge_height)

        ax.fill_between(x_grid, baseline, baseline + density * ridge_height,
                        alpha=0.6, color=color, linewidth=0)
        ax.plot(x_grid, baseline + density * ridge_height, color=color,
                linewidth=0.6)
        ax.plot([x_min - x_pad, x_max + x_pad], [baseline, baseline],
                color="white", linewidth=0.6)

        # Group label
        ax.text(x_min - x_pad * 1.1, baseline + ridge_height * 0.3, cat,
                fontsize=5, ha="right", va="center")

    ax.set_yticks([])
    ax.set_xlabel(value_col)
    ax.spines["left"].set_visible(False)
    if standalone:
        apply_chart_polish(ax, "ridge")
    return ax


def gen_violin_paired(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Paired violin plots (before/after or time 1/time 2).

    Expects a group column with exactly 2 levels and a subject/pair ID column
    in semanticRoles["pair_id"].  Connects paired observations with thin gray
    lines.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)
    pair_col = dataProfile.get("semanticRoles", {}).get("pair_id") or \
               dataProfile.get("semanticRoles", {}).get("subject")

    if value_col is None:
        raise ValueError("violin_paired requires a numeric value column")
    if group_col is None:
        raise ValueError("violin_paired requires a group column with 2 levels")

    categories = df[group_col].dropna().unique().tolist()
    if len(categories) != 2:
        import warnings
        warnings.warn("violin_paired expects exactly 2 groups; using first 2")
        categories = categories[:2]

    color_map = _extract_colors(palette, categories)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                               constrained_layout=True)

    # Violin bodies
    parts = ax.violinplot(
        [df[df[group_col] == cat][value_col].dropna().values for cat in categories],
        positions=range(len(categories)),
        showmeans=False, showmedians=True, showextrema=False
    )
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(list(color_map.values())[i])
        pc.set_alpha(0.3)
        pc.set_linewidth(0.6)
    parts["cmedians"].set_color("black")
    parts["cmedians"].set_linewidth(0.6)

    # Paired connecting lines
    if pair_col and pair_col in df.columns:
        for pid in df[pair_col].dropna().unique():
            pair_df = df[df[pair_col] == pid].sort_values(group_col)
            if len(pair_df) == 2:
                vals = pair_df[value_col].values
                ax.plot(range(len(categories)), vals, color="#BBBBBB",
                        linewidth=0.3, alpha=0.5, zorder=1)

    # Jittered individual points
    for i, cat in enumerate(categories):
        subset = df[df[group_col] == cat][value_col].dropna()
        jitter = np.random.default_rng(42).uniform(-0.08, 0.08, len(subset))
        ax.scatter(np.full(len(subset), i) + jitter, subset,
                   color=color_map[cat], s=8, alpha=0.6,
                   linewidth=0.3, edgecolor="white", zorder=2)

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories)
    ax.set_xlabel("")
    ax.set_ylabel(value_col)
    if standalone:
        apply_chart_polish(ax, "violin_paired")
    return ax


def gen_violin_split(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Split violin (half/half comparison).

    Two groups shown as left and right halves of a violin at the same
    position.  Requires exactly 2 groups.  Each half is the KDE of one group,
    mirrored for visual comparison.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, x_col = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("violin_split requires a numeric value column")
    if group_col is None:
        raise ValueError("violin_split requires a group column with 2 levels")

    categories = df[group_col].dropna().unique().tolist()
    if len(categories) != 2:
        import warnings
        warnings.warn("violin_split expects exactly 2 groups; using first 2")
        categories = categories[:2]

    color_map = _extract_colors(palette, categories)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    # Determine x positions
    if x_col and x_col in df.columns:
        x_levels = df[x_col].dropna().unique().tolist()
    else:
        x_levels = ["All"]

    for xi, xl in enumerate(x_levels):
        if x_col and x_col in df.columns:
            subset = df[df[x_col] == xl]
        else:
            subset = df

        for side, cat in enumerate(categories):
            data = subset[subset[group_col] == cat][value_col].dropna()
            if len(data) < 3:
                continue

            # KDE computation
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(data, bw_method="silverman")
            y_grid = np.linspace(data.min() - 0.5 * data.std(),
                                 data.max() + 0.5 * data.std(), 200)
            density = kde(y_grid)
            density = density / density.max() * 0.35  # scale to half-width

            # Mirror: left group goes left (negative), right goes right
            direction = -1 if side == 0 else 1
            color = color_map[cat]

            ax.fill_betweenx(y_grid, xi, xi + direction * density,
                             alpha=0.5, color=color, linewidth=0)
            ax.plot(xi + direction * density, y_grid, color=color, linewidth=0.6)

    if x_col and x_col in df.columns:
        ax.set_xticks(range(len(x_levels)))
        ax.set_xticklabels(x_levels)
    else:
        ax.set_xticks([0])
        ax.set_xticklabels([""])

    ax.set_xlabel(x_col or "")
    ax.set_ylabel(value_col)

    # Legend
    legend_handles = [plt.Line2D([0], [0], color=color_map[c], linewidth=2,
                                  alpha=0.5, label=c) for c in categories]
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)

    if standalone:
        apply_chart_polish(ax, "violin_split")
    return ax


def gen_dot_strip(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pure dot plot (Cleveland-style, no box or violin).

    Each observation is a single dot.  Dots are stacked along the y-axis using
    a beeswarm-style jitter to prevent overplotting.  Preferred for small-to-
    medium sample sizes (n < 100 per group).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("dot_strip requires a numeric value column")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)

        for i, cat in enumerate(categories):
            subset = df[df[group_col] == cat][value_col].dropna()
            color = color_map[cat]

            # Beeswarm-style jitter: offset each dot to avoid overlap
            n = len(subset)
            if n == 0:
                continue
            sorted_idx = np.argsort(subset.values)
            sorted_vals = subset.values[sorted_idx]
            # Compute simple strip jitter
            jitter_offsets = np.zeros(n)
            bin_width = subset.std() * 0.15 if subset.std() > 0 else 0.05
            for j in range(n):
                # Count neighbors within bin_width and offset accordingly
                neighbors = np.abs(sorted_vals - sorted_vals[j]) < bin_width
                rank_in_bin = np.sum(neighbors[:j])
                jitter_offsets[j] = (rank_in_bin - np.sum(neighbors) / 2) * 0.08

            ax.scatter(np.full(n, i) + jitter_offsets, sorted_vals,
                       color=color, s=10, alpha=0.7,
                       linewidth=0.3, edgecolor="white", zorder=2)

            # Median line
            med = subset.median()
            ax.plot([i - 0.2, i + 0.2], [med, med], color="black",
                    linewidth=0.8, solid_capstyle="round", zorder=3)

        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories)
        ax.set_xlabel("")
    else:
        values = df[value_col].dropna()
        color = palette.get("categorical", ["#000000"])[0]
        n = len(values)
        jitter = np.random.default_rng(42).uniform(-0.15, 0.15, n)
        ax.scatter(jitter, values, color=color, s=10, alpha=0.7,
                   linewidth=0.3, edgecolor="white")
        ax.set_xticks([])

    ax.set_ylabel(value_col)
    if standalone:
        apply_chart_polish(ax, "dot_strip")
    return ax


def gen_joyplot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stacked density ridgeline (joyplot).

    Similar to gen_ridge but with more overlap and filled areas, producing the
    classic "joy division" aesthetic.  Groups are ordered by median and each
    ridge is a filled KDE with high overlap.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("joyplot requires a numeric value column")
    if group_col is None:
        raise ValueError("joyplot requires a group column in semanticRoles")

    categories = df[group_col].dropna().unique().tolist()
    medians = df.groupby(group_col)[value_col].median()
    categories = sorted(categories, key=lambda c: medians.get(c, 0))
    color_map = _extract_colors(palette, categories)

    n_groups = len(categories)
    fig_height = max(60, 18 * n_groups) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    all_vals = df[value_col].dropna()
    x_min, x_max = all_vals.min(), all_vals.max()
    x_pad = (x_max - x_min) * 0.1
    x_grid = np.linspace(x_min - x_pad, x_max + x_pad, 400)

    overlap = 0.85  # high overlap for joyplot aesthetic

    for i, cat in enumerate(reversed(categories)):  # bottom-up stacking
        subset = df[df[group_col] == cat][value_col].dropna()
        color = color_map[cat]

        # Gaussian KDE with Silverman bandwidth
        sigma = subset.std() * len(subset) ** (-1 / 5)
        if sigma == 0:
            sigma = 0.1
        density = np.exp(-0.5 * ((x_grid - subset.mean()) / sigma) ** 2) / \
                  (sigma * np.sqrt(2 * np.pi))
        density = density / density.max() if density.max() > 0 else density

        baseline = i * (1 - overlap)
        ax.fill_between(x_grid, baseline, baseline + density,
                        alpha=0.65, color=color, linewidth=0)
        ax.plot(x_grid, baseline + density, color=color, linewidth=0.5)
        # Clean baseline
        ax.plot([x_min - x_pad, x_max + x_pad], [baseline, baseline],
                color="white", linewidth=0.5)

    # Y-axis labels: map reversed index back to category name
    ax.set_yticks([i * (1 - overlap) for i in range(n_groups)])
    ax.set_yticklabels(list(reversed(categories)), fontsize=5)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    # Draw labels on the left margin instead
    for i, cat in enumerate(reversed(categories)):
        baseline = i * (1 - overlap)
        ax.text(x_min - x_pad * 1.1, baseline + 0.3, cat,
                fontsize=5, ha="right", va="center")

    ax.set_xlabel(value_col)
    if standalone:
        apply_chart_polish(ax, "joyplot")
    return ax


def gen_residual_vs_fitted(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Residuals vs fitted values scatter for regression diagnostics.

    Expects columns: fitted (predicted values) and residual in semanticRoles.
    Adds a horizontal reference line at y=0 and a LOWESS smoother to reveal
    non-linearity or heteroscedasticity patterns.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    fitted_col = roles.get("fitted") or roles.get("x")
    resid_col = roles.get("residual") or roles.get("value")

    if fitted_col is None or resid_col is None:
        raise ValueError("residual_vs_fitted requires 'fitted' and 'residual' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#0072B2"])[0]
    ax.scatter(df[fitted_col], df[resid_col], s=10, alpha=0.5, color=color,
               linewidth=0.3, edgecolor="white", zorder=2)

    # Reference line at zero
    ax.axhline(0, color="black", linewidth=0.6, linestyle="--", zorder=1)

    # LOWESS smoother
    from statsmodels.nonparametric.smoothers_lowess import lowess
    smoothed = lowess(df[resid_col].dropna(), df[fitted_col].dropna(), frac=0.3)
    ax.plot(smoothed[:, 0], smoothed[:, 1], color="#C8553D", linewidth=0.8,
            solid_capstyle="round", zorder=3)

    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residuals")
    if standalone:
        apply_chart_polish(ax, "residual_vs_fitted")
    return ax


def gen_scale_location(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Scale-location plot: sqrt(|standardized residuals|) vs fitted values.

    Used to assess homoscedasticity.  A flat LOWESS line suggests constant
    variance; an upward trend indicates increasing spread with fitted values.
    Expects columns: fitted and residual (or standardized_residual) in
    semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    fitted_col = roles.get("fitted") or roles.get("x")
    resid_col = roles.get("standardized_residual") or roles.get("residual") or roles.get("value")

    if fitted_col is None or resid_col is None:
        raise ValueError("scale_location requires 'fitted' and 'residual' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    fitted = df[fitted_col].dropna()
    resid = df[resid_col].dropna()
    common_idx = fitted.index.intersection(resid.index)
    fitted, resid = fitted.loc[common_idx], resid.loc[common_idx]

    # Standardize residuals if raw residuals provided
    std_resid = resid / resid.std() if resid.std() > 0 else resid
    sqrt_abs = np.sqrt(np.abs(std_resid))

    color = palette.get("categorical", ["#0072B2"])[0]
    ax.scatter(fitted, sqrt_abs, s=10, alpha=0.5, color=color,
               linewidth=0.3, edgecolor="white", zorder=2)

    # LOWESS smoother
    from statsmodels.nonparametric.smoothers_lowess import lowess
    smoothed = lowess(sqrt_abs.values, fitted.values, frac=0.3)
    ax.plot(smoothed[:, 0], smoothed[:, 1], color="#C8553D", linewidth=0.8,
            solid_capstyle="round", zorder=3)

    ax.set_xlabel("Fitted values")
    ax.set_ylabel(r"$\sqrt{|\mathrm{Standardized\ residuals}|}$")
    if standalone:
        apply_chart_polish(ax, "scale_location")
    return ax


def gen_pp_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """P-P plot: observed vs expected cumulative probabilities.

    Plots empirical CDF against a theoretical reference (normal by default)
    to assess distributional fit.  Points lying on the diagonal indicate
    good agreement; systematic deviations reveal skew, heavy tails, or
    other departures from the reference distribution.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    value_col = roles.get("value") or roles.get("y")

    if value_col is None:
        raise ValueError("pp_plot requires a numeric value column in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    values = df[value_col].dropna().values
    n = len(values)
    sorted_vals = np.sort(values)
    observed = np.arange(1, n + 1) / n

    # Expected quantiles under normal reference
    from scipy.stats import norm
    mean, std = sorted_vals.mean(), sorted_vals.std()
    expected = norm.cdf(sorted_vals, loc=mean, scale=std) if std > 0 else observed

    color = palette.get("categorical", ["#0072B2"])[0]
    ax.scatter(expected, observed, s=10, alpha=0.6, color=color,
               linewidth=0.3, edgecolor="white", zorder=2)

    # Diagonal reference line
    ax.plot([0, 1], [0, 1], color="black", linewidth=0.6, linestyle="--", zorder=1)

    ax.set_xlabel("Expected cumulative probability")
    ax.set_ylabel("Observed cumulative probability")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    if standalone:
        apply_chart_polish(ax, "pp_plot")
    return ax


def gen_bland_altman(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Bland-Altman agreement plot: mean vs difference of paired measurements.

    Each point represents one subject measured by two methods (or timepoints).
    The x-axis is the mean of the two measurements; the y-axis is their
    difference.  Horizontal lines mark the mean bias and 95 % limits of
    agreement (mean +/- 1.96 SD of differences).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    # Expect two measurement columns
    method_a = roles.get("method_a") or roles.get("x")
    method_b = roles.get("method_b") or roles.get("y") or roles.get("value")

    if method_a is None or method_b is None:
        raise ValueError("bland_altman requires 'method_a' and 'method_b' columns in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    a = df[method_a].dropna()
    b = df[method_b].dropna()
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]

    mean_vals = (a + b) / 2
    diff_vals = a - b

    bias = diff_vals.mean()
    loa_upper = bias + 1.96 * diff_vals.std()
    loa_lower = bias - 1.96 * diff_vals.std()

    color = palette.get("categorical", ["#0072B2"])[0]
    ax.scatter(mean_vals, diff_vals, s=10, alpha=0.6, color=color,
               linewidth=0.3, edgecolor="white", zorder=2)

    # Mean bias line
    ax.axhline(bias, color="black", linewidth=0.8, linestyle="-", zorder=1)
    # 95 % limits of agreement
    ax.axhline(loa_upper, color="black", linewidth=0.6, linestyle="--", zorder=1)
    ax.axhline(loa_lower, color="black", linewidth=0.6, linestyle="--", zorder=1)

    # Annotate bias and limits
    x_right = ax.get_xlim()[1]
    ax.text(x_right, bias, f"  bias = {bias:+.2g}", fontsize=5, va="center", ha="left")
    ax.text(x_right, loa_upper, f"  +1.96 SD = {loa_upper:+.2g}", fontsize=5, va="center", ha="left")
    ax.text(x_right, loa_lower, f"  -1.96 SD = {loa_lower:+.2g}", fontsize=5, va="center", ha="left")

    ax.set_xlabel("Mean of two measurements")
    ax.set_ylabel("Difference (A - B)")
    if standalone:
        apply_chart_polish(ax, "bland_altman")
    return ax


def gen_funnel_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Funnel plot for publication bias assessment.

    Plots effect size (or log odds ratio) against a precision measure
    (typically sample size or inverse standard error).  A pseudo-95%
    confidence funnel is drawn around the pooled estimate, and studies
    outside the funnel are highlighted as potential bias signals.

    Expects in semanticRoles: effect (effect size), precision (1/SE or
    sample size), and optionally label (study identifier).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    effect_col = roles.get("effect") or roles.get("y") or roles.get("value")
    precision_col = roles.get("precision") or roles.get("x")
    label_col = roles.get("label")

    if effect_col is None or precision_col is None:
        raise ValueError("funnel_plot requires 'effect' and 'precision' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    effect = df[effect_col].dropna()
    precision = df[precision_col].dropna()
    common = effect.index.intersection(precision.index)
    effect, precision = effect.loc[common], precision.loc[common]

    pooled = effect.mean()
    se_approx = 1.0 / precision  # precision ~ 1/SE
    se_min = se_approx.min()
    se_grid = np.linspace(se_min * 0.5, se_approx.max() * 1.2, 200)

    ax.scatter(effect, precision, s=14, alpha=0.6,
               color=palette.get("categorical", ["#0072B2"])[0],
               linewidth=0.3, edgecolor="white", zorder=2)

    # Pseudo-95% funnel boundary
    ax.plot(pooled + 1.96 * se_grid, 1.0 / se_grid, color="#C8553D",
            linewidth=0.6, linestyle="--", zorder=1)
    ax.plot(pooled - 1.96 * se_grid, 1.0 / se_grid, color="#C8553D",
            linewidth=0.6, linestyle="--", zorder=1)
    ax.axvline(pooled, color="black", linewidth=0.6, linestyle="-", zorder=1)

    if label_col and label_col in df.columns:
        outside = ((effect - pooled).abs() > 1.96 * se_approx)
        for idx in effect[outside].index:
            ax.annotate(df.loc[idx, label_col], (effect[idx], precision[idx]),
                        fontsize=4, ha="left", va="bottom",
                        arrowprops=dict(arrowstyle="-", lw=0.3, color="black"))

    ax.set_xlabel("Effect size")
    ax.set_ylabel("Precision (1 / SE)")
    if standalone:
        apply_chart_polish(ax, "funnel_plot")
    return ax


def gen_pareto_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pareto chart: bars sorted descending with cumulative percentage line.

    Bars represent category frequencies (descending order) and a secondary
    y-axis shows the cumulative percentage.  The 80% threshold line is
    drawn per the Pareto principle.

    Expects in semanticRoles: category (categorical column) and optionally
    value (pre-aggregated counts).  If value is absent, rows are counted
    per category.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    cat_col = roles.get("category") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")

    if cat_col is None:
        raise ValueError("pareto_chart requires a 'category' column in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if val_col and val_col in df.columns:
        counts = df.groupby(cat_col)[val_col].sum()
    else:
        counts = df[cat_col].value_counts()

    counts = counts.sort_values(ascending=False)
    cumulative = counts.cumsum() / counts.sum() * 100

    color = palette.get("categorical", ["#1F4E79"])[0]
    ax.bar(range(len(counts)), counts.values, color=color, edgecolor="white",
           linewidth=0.4, width=0.7, zorder=2)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index, rotation=45, ha="right", fontsize=5)

    ax2 = ax.twinx()
    ax2.plot(range(len(counts)), cumulative.values, color="#C8553D",
             linewidth=0.8, marker="o", markersize=3, zorder=3)
    ax2.axhline(80, color="gray", linewidth=0.5, linestyle=":", zorder=1)
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 105)
    ax2.spines["top"].set_visible(False)

    ax.set_ylabel("Count")
    if standalone:
        apply_chart_polish(ax, "pareto_chart")
    return ax


def gen_mean_diff_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mean-difference plot (Tukey-style alternative to Bland-Altman).

    Each point is one subject measured twice.  X-axis = mean of the two
    measurements; Y-axis = difference (method A minus method B).  A solid
    horizontal line marks the mean difference; dashed lines mark the 95 % CI
    of the mean and 95 % limits of agreement (mean +/- 1.96 SD).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    method_a = roles.get("method_a") or roles.get("x")
    method_b = roles.get("method_b") or roles.get("y") or roles.get("value")

    if method_a is None or method_b is None:
        raise ValueError("mean_diff_plot requires 'method_a' and 'method_b' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    a = df[method_a].dropna()
    b = df[method_b].dropna()
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]

    means = (a + b) / 2
    diffs = a - b
    n = len(diffs)
    mean_diff = diffs.mean()
    sd_diff = diffs.std()
    se = sd_diff / np.sqrt(n) if n > 0 else 0

    color = palette.get("categorical", ["#0072B2"])[0]
    ax.scatter(means, diffs, s=10, alpha=0.6, color=color,
               linewidth=0.3, edgecolor="white", zorder=2)

    # Mean difference and 95 % CI of the mean
    ax.axhline(mean_diff, color="black", linewidth=0.8, zorder=1)
    ax.axhline(mean_diff + 1.96 * se, color="black", linewidth=0.5,
               linestyle=":", zorder=1)
    ax.axhline(mean_diff - 1.96 * se, color="black", linewidth=0.5,
               linestyle=":", zorder=1)
    # 95 % limits of agreement
    ax.axhline(mean_diff + 1.96 * sd_diff, color="#C8553D",
               linewidth=0.6, linestyle="--", zorder=1)
    ax.axhline(mean_diff - 1.96 * sd_diff, color="#C8553D",
               linewidth=0.6, linestyle="--", zorder=1)

    # Annotation
    x_right = ax.get_xlim()[1]
    ax.text(x_right, mean_diff, f"  mean = {mean_diff:+.2g}",
            fontsize=5, va="center", ha="left")
    ax.text(x_right, mean_diff + 1.96 * sd_diff,
            f"  +1.96 SD = {mean_diff + 1.96 * sd_diff:+.2g}",
            fontsize=5, va="center", ha="left")
    ax.text(x_right, mean_diff - 1.96 * sd_diff,
            f"  -1.96 SD = {mean_diff - 1.96 * sd_diff:+.2g}",
            fontsize=5, va="center", ha="left")

    ax.set_xlabel("Mean of two measurements")
    ax.set_ylabel("Difference (A - B)")
    if standalone:
        apply_chart_polish(ax, "mean_diff_plot")
    return ax


def gen_ci_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Confidence interval plot for multiple estimates.

    Displays horizontal CI bars for each estimate row.  Expects columns for
    estimate (point value), lower CI bound, and upper CI bound.  Optionally
    accepts a label column for y-axis tick names.  A vertical reference line
    at x = 0 is drawn when the interval spans zero.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    est_col = roles.get("estimate") or roles.get("value") or roles.get("y")
    lower_col = roles.get("ci_lower") or roles.get("lower")
    upper_col = roles.get("ci_upper") or roles.get("upper")
    label_col = roles.get("label") or roles.get("group") or roles.get("x")

    if est_col is None or lower_col is None or upper_col is None:
        raise ValueError("ci_plot requires 'estimate', 'ci_lower', and 'ci_upper' in semanticRoles")

    n = len(df)
    fig_height = max(60, 12 * n + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    y_pos = np.arange(n)
    color = palette.get("categorical", ["#0072B2"])[0]

    for i, (_, row) in enumerate(df.iterrows()):
        est = row[est_col]
        lo = row[lower_col]
        hi = row[upper_col]
        ax.plot([lo, hi], [i, i], color=color, linewidth=0.8,
                solid_capstyle="round", zorder=2)
        ax.plot(est, i, "o", color=color, markersize=4, zorder=3)

    # Reference line at zero if interval spans it
    all_lo = df[lower_col].min()
    all_hi = df[upper_col].max()
    if all_lo < 0 < all_hi:
        ax.axvline(0, color="black", linewidth=0.5, linestyle="--", zorder=1)

    if label_col and label_col in df.columns:
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df[label_col].astype(str).tolist(), fontsize=5)
    else:
        ax.set_yticks(y_pos)
        ax.set_yticklabels([str(i + 1) for i in range(n)], fontsize=5)

    ax.set_xlabel("Estimate (95 % CI)")
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if standalone:
        apply_chart_polish(ax, "ci_plot")
    return ax


def gen_cook_distance(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Cook's distance bar chart for influential point detection.

    Fits OLS on observation index vs value column, computes Cook's D for each
    point, and highlights observations exceeding the 4/n threshold.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    _, value_col, _ = _resolve_roles(dataProfile)
    if value_col is None:
        raise ValueError("cook_distance requires a numeric value column")

    y = df[value_col].dropna().values
    n = len(y)
    X = np.column_stack([np.ones(n), np.arange(n)])

    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    residuals = y - X @ beta
    p = X.shape[1]
    mse = np.sum(residuals ** 2) / (n - p)
    hat = np.diag(X @ np.linalg.inv(X.T @ X) @ X.T)
    cook_d = (residuals ** 2 * hat) / (p * mse * (1 - hat) ** 2)

    threshold = 4.0 / n
    colors = [palette["categorical"][1] if d > threshold
              else palette["categorical"][0] for d in cook_d]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4),
                           constrained_layout=True)
    ax.bar(np.arange(n), cook_d, color=colors, edgecolor="white",
           linewidth=0.4, width=0.8)
    ax.axhline(threshold, color="gray", linestyle="--", linewidth=0.6,
               label=f"4/n = {threshold:.3f}")
    ax.legend(frameon=False, fontsize=5)
    ax.set_xlabel("Observation index")
    ax.set_ylabel("Cook's distance")
    if standalone:
        apply_chart_polish(ax, "cook_distance")
    return ax


def gen_leverage_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Leverage vs squared residual for regression diagnostics.

    Fits OLS on observation index vs value, plots leverage (hat values) against
    squared residuals.  A vertical line marks the 2p/n high-leverage threshold.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    _, value_col, _ = _resolve_roles(dataProfile)
    if value_col is None:
        raise ValueError("leverage_plot requires a numeric value column")

    y = df[value_col].dropna().values
    n = len(y)
    X = np.column_stack([np.ones(n), np.arange(n)])

    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    residuals = y - X @ beta
    p = X.shape[1]
    hat = np.diag(X @ np.linalg.inv(X.T @ X) @ X.T)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4),
                           constrained_layout=True)
    ax.scatter(hat, residuals ** 2, s=12, alpha=0.7,
               color=palette["categorical"][0],
               linewidth=0.3, edgecolor="white", zorder=2)
    ax.axvline(2 * p / n, color="gray", linestyle="--", linewidth=0.6,
               label=f"2p/n = {2 * p / n:.3f}")
    ax.legend(frameon=False, fontsize=5)
    ax.set_xlabel("Leverage")
    ax.set_ylabel("Squared residual")
    if standalone:
        apply_chart_polish(ax, "leverage_plot")
    return ax


def gen_circos_karyotype(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified circos-like karyotype plot (linear chromosomes with colored tracks).

    Expects columns: chromosome, start, end, and optionally track_value and
    track_color in semanticRoles.  Draws horizontal chromosome bands with
    colored overlay tracks simulating a circos layout in linear form.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    chr_col = roles.get("chromosome") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end")
    value_col = roles.get("track_value") or roles.get("value")
    color_col = roles.get("track_color")

    if chr_col is None or start_col is None or end_col is None:
        raise ValueError("circos_karyotype requires 'chromosome', 'start', 'end' in semanticRoles")

    chromosomes = df[chr_col].dropna().unique().tolist()
    n_chr = len(chromosomes)
    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(60, 12 * n_chr) * (1 / 25.4)),
                           constrained_layout=True)

    fallback = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                            "#C8553D", "#7A6C8F", "#2B6F77"])
    chr_colors = {c: fallback[i % len(fallback)] for i, c in enumerate(chromosomes)}

    for yi, chrom in enumerate(chromosomes):
        sub = df[df[chr_col] == chrom].sort_values(start_col)
        x_max = sub[end_col].max()
        # Chromosome backbone
        ax.barh(yi, x_max, left=0, height=0.5, color="#E0E0E0",
                edgecolor="black", linewidth=0.4)
        # Colored segments
        for _, row in sub.iterrows():
            seg_color = row[color_col] if color_col and color_col in df.columns \
                else chr_colors[chrom]
            seg_alpha = 0.7
            if value_col and value_col in df.columns:
                seg_alpha = max(0, min(1, 0.3 + 0.7 * min(row[value_col], 1.0)))
            ax.barh(yi, row[end_col] - row[start_col], left=row[start_col],
                    height=0.5, color=seg_color, alpha=seg_alpha, linewidth=0)

    ax.set_yticks(range(n_chr))
    ax.set_yticklabels(chromosomes, fontsize=5)
    ax.set_xlabel("Genomic position")
    ax.set_ylim(-0.5, n_chr - 0.5)
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    if standalone:
        apply_chart_polish(ax, "circos_karyotype")
    return ax


def gen_gene_structure(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Gene structure diagram (exons as boxes, introns as lines, UTRs colored).

    Expects columns: feature_type (exon/intron/5utr/3utr/cds), start, end,
    and optionally strand in semanticRoles.  Draws a horizontal gene model
    with exon boxes, intron lines, and colored UTR regions.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    type_col = roles.get("feature_type") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end")
    strand = roles.get("strand", "+")

    if type_col is None or start_col is None or end_col is None:
        raise ValueError("gene_structure requires 'feature_type', 'start', 'end' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 40 * (1 / 25.4)),
                           constrained_layout=True)

    feature_colors = {
        "exon": "#3B5998", "cds": "#1F4E79",
        "5utr": "#F2A541", "3utr": "#F2A541",
        "intron": "#999999",
    }

    gene_start = df[start_col].min()
    gene_end = df[end_col].max()
    # Intron line at y=0
    ax.plot([gene_start, gene_end], [0, 0], color="#666666", linewidth=0.8,
            solid_capstyle="round", zorder=1)

    for _, row in df.iterrows():
        ftype = str(row[type_col]).lower().strip()
        s, e = row[start_col], row[end_col]
        color = feature_colors.get(ftype, "#999999")
        height = 0.6 if ftype in ("exon", "cds") else 0.4
        box = plt.Rectangle((s, -height / 2), e - s, height,
                             facecolor=color, edgecolor="black",
                             linewidth=0.4, zorder=2)
        ax.add_patch(box)

    # Arrow indicating strand direction
    arrow_y = -0.8
    if strand == "+":
        ax.annotate("", xy=(gene_end, arrow_y), xytext=(gene_start, arrow_y),
                    arrowprops=dict(arrowstyle="->", lw=0.6, color="black"))
    else:
        ax.annotate("", xy=(gene_start, arrow_y), xytext=(gene_end, arrow_y),
                    arrowprops=dict(arrowstyle="->", lw=0.6, color="black"))

    ax.set_xlim(gene_start - (gene_end - gene_start) * 0.05,
                gene_end + (gene_end - gene_start) * 0.05)
    ax.set_ylim(-1.2, 0.8)
    ax.set_xlabel("Genomic position (bp)")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)

    # Legend for feature types
    present_types = df[type_col].dropna().unique()
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=feature_colors.get(t, "#999999"),
                              edgecolor="black", linewidth=0.4, label=t)
               for t in present_types]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=5, ncol=len(handles))

    if standalone:
        apply_chart_polish(ax, "gene_structure")
    return ax


def gen_pathway_map(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pathway enrichment bubble chart.

    x=enrichment score, y=pathway name, size=gene count, color=-log10(p).
    Expects columns: pathway, enrichment_score, gene_count, p_value in semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pathway_col = roles.get("pathway") or roles.get("group") or roles.get("y")
    score_col = roles.get("enrichment_score") or roles.get("x") or roles.get("value")
    count_col = roles.get("gene_count") or roles.get("size")
    pval_col = roles.get("p_value") or roles.get("color")

    if pathway_col is None or score_col is None:
        raise ValueError("pathway_map requires 'pathway' and 'enrichment_score' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(60, 12 * len(df) + 20) * (1 / 25.4)),
                           constrained_layout=True)

    nlogp = -np.log10(df[pval_col].clip(lower=1e-300)) if pval_col and pval_col in df.columns else np.ones(len(df))
    sizes = df[count_col] * 8 if count_col and count_col in df.columns else np.full(len(df), 40)
    cmap = plt.cm.YlOrRd

    scatter = ax.scatter(df[score_col], df[pathway_col], s=sizes, c=nlogp,
                         cmap=cmap, alpha=0.7, edgecolor="white", linewidth=0.4)
    cbar = ax.figure.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label(r"$-\log_{10}(p)$", fontsize=5)
    cbar.ax.tick_params(labelsize=4)

    ax.set_xlabel("Enrichment score")
    ax.set_ylabel("")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "pathway_map")
    return ax


def gen_kegg_bar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """KEGG pathway horizontal bar chart.

    Enrichment ratio bars with significance markers (* p<0.05, ** p<0.01, *** p<0.001).
    Expects columns: pathway, enrichment_ratio, p_value in semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pathway_col = roles.get("pathway") or roles.get("group") or roles.get("y")
    ratio_col = roles.get("enrichment_ratio") or roles.get("x") or roles.get("value")
    pval_col = roles.get("p_value")

    if pathway_col is None or ratio_col is None:
        raise ValueError("kegg_bar requires 'pathway' and 'enrichment_ratio' in semanticRoles")

    n = len(df)
    fig_height = max(60, 12 * n + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height), constrained_layout=True)

    colors = palette.get("categorical", ["#1F4E79"])[0]
    bars = ax.barh(df[pathway_col], df[ratio_col], color=colors, edgecolor="white",
                   linewidth=0.4, height=0.7, zorder=2)

    # Significance markers
    if pval_col and pval_col in df.columns:
        for i, (_, row) in enumerate(df.iterrows()):
            p = row[pval_col]
            if p < 0.001:
                marker = "***"
            elif p < 0.01:
                marker = "**"
            elif p < 0.05:
                marker = "*"
            else:
                continue
            ax.text(row[ratio_col] + ax.get_xlim()[1] * 0.01, i, marker,
                    fontsize=5, va="center", ha="left", color="#C8553D")

    ax.set_xlabel("Enrichment ratio")
    ax.set_ylabel("")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "kegg_bar")
    return ax


def gen_control_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Shewhart control chart with mean line and +/-3sigma limits.

    Expects a numeric value column in semanticRoles["value"].  Points beyond
    the control limits are highlighted in red.  Center line shows the process
    mean; upper/lower limits are mean +/- 3 * std.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    _, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("control_chart requires a numeric value column in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    values = df[value_col].dropna().values
    mean = np.mean(values)
    sigma = np.std(values, ddof=1)
    ucl, lcl = mean + 3 * sigma, mean - 3 * sigma

    x = np.arange(len(values))
    color_normal = palette.get("categorical", ["#0072B2"])[0]

    # In-control points
    in_ctrl = (values >= lcl) & (values <= ucl)
    ax.scatter(x[in_ctrl], values[in_ctrl], s=12, color=color_normal,
               linewidth=0.3, edgecolor="white", zorder=2)
    # Out-of-control points
    ooc = ~in_ctrl
    if ooc.any():
        ax.scatter(x[ooc], values[ooc], s=16, color="#C8553D",
                   linewidth=0.3, edgecolor="white", zorder=3)

    # Control limit lines
    ax.axhline(mean, color="black", linewidth=0.8, linestyle="-",
               solid_capstyle="round", label=f"Mean = {mean:.2f}")
    ax.axhline(ucl, color="#C8553D", linewidth=0.6, linestyle="--",
               label=f"+3σ = {ucl:.2f}")
    ax.axhline(lcl, color="#C8553D", linewidth=0.6, linestyle="--",
               label=f"−3σ = {lcl:.2f}")

    ax.set_xlabel("Observation")
    ax.set_ylabel(value_col)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "control_chart")
    return ax


def gen_box_paired(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Paired box plots with per-subject connecting lines.

    Expects a group column with exactly 2 levels and a subject/pair ID column
    in semanticRoles["pair_id"].  Boxes show before/after distributions; thin
    gray lines connect paired observations across conditions.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)
    pair_col = dataProfile.get("semanticRoles", {}).get("pair_id") or \
               dataProfile.get("semanticRoles", {}).get("subject")

    if value_col is None:
        raise ValueError("box_paired requires a numeric value column")
    if group_col is None:
        raise ValueError("box_paired requires a group column with 2 levels")

    categories = df[group_col].dropna().unique().tolist()
    if len(categories) != 2:
        import warnings
        warnings.warn("box_paired expects exactly 2 groups; using first 2")
        categories = categories[:2]

    color_map = _extract_colors(palette, categories)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    # Box plots
    positions = range(len(categories))
    box_data = [df[df[group_col] == cat][value_col].dropna().values
                for cat in categories]
    bp = ax.boxplot(box_data, positions=list(positions), widths=0.5,
                    patch_artist=True, showfliers=False,
                    medianprops=dict(color="black", linewidth=0.8),
                    whiskerprops=dict(linewidth=0.6),
                    capprops=dict(linewidth=0.6))
    for patch, cat in zip(bp["boxes"], categories):
        patch.set_facecolor(color_map[cat])
        patch.set_alpha(0.4)
        patch.set_linewidth(0.6)

    # Paired connecting lines
    if pair_col and pair_col in df.columns:
        for pid in df[pair_col].dropna().unique():
            pair_df = df[df[pair_col] == pid].sort_values(group_col)
            if len(pair_df) == 2:
                vals = pair_df[value_col].values
                ax.plot(list(positions), vals, color="#BBBBBB",
                        linewidth=0.3, alpha=0.5, zorder=1)

    ax.set_xticks(list(positions))
    ax.set_xticklabels(categories)
    ax.set_xlabel("")
    ax.set_ylabel(value_col)
    if standalone:
        apply_chart_polish(ax, "box_paired")
    return ax


def gen_stress_strain(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stress-strain curve for materials science.

    Plots strain (x) vs stress (y) with optional yield point annotation.
    Expects columns: strain (x-axis) and stress (y-axis) in semanticRoles.
    If a yield_strain/yield_stress column exists, annotates the yield point.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    strain_col = roles.get("strain") or roles.get("x")
    stress_col = roles.get("stress") or roles.get("y") or roles.get("value")

    if strain_col is None or stress_col is None:
        raise ValueError("stress_strain requires 'strain' and 'stress' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#0072B2"])[0]
    ax.plot(df[strain_col], df[stress_col], color=color, linewidth=0.8,
            solid_capstyle="round", zorder=2)

    # Yield point annotation if available
    yield_strain_col = roles.get("yield_strain")
    yield_stress_col = roles.get("yield_stress")
    if yield_strain_col and yield_stress_col and yield_strain_col in df.columns:
        ystrain = df[yield_strain_col].dropna().iloc[0]
        ystress = df[yield_stress_col].dropna().iloc[0]
        ax.plot(ystrain, ystress, "o", color="#C8553D", markersize=4, zorder=3)
        ax.annotate(f"Yield\n({ystrain:.2f}, {ystress:.1f})",
                    xy=(ystrain, ystress), xytext=(ystrain + 0.02, ystress * 0.9),
                    fontsize=5, arrowprops=dict(arrowstyle="->", lw=0.4, color="black"))

    ax.set_xlabel("Strain")
    ax.set_ylabel("Stress (MPa)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "stress_strain")
    return ax


def gen_xrd_pattern(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """X-ray diffraction (XRD) pattern with stick plot peaks.

    Plots 2-theta (x) vs intensity (y) as vertical sticks at peak positions.
    Expects columns: two_theta (x-axis) and intensity (y-axis) in semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    theta_col = roles.get("two_theta") or roles.get("x")
    intensity_col = roles.get("intensity") or roles.get("y") or roles.get("value")

    if theta_col is None or intensity_col is None:
        raise ValueError("xrd_pattern requires 'two_theta' and 'intensity' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#1F4E79"])[0]

    # Vertical stick plot
    theta = df[theta_col].dropna()
    intensity = df[intensity_col].dropna()
    common = theta.index.intersection(intensity.index)
    theta, intensity = theta.loc[common], intensity.loc[common]

    # Normalize intensity to [0, 1] for stick heights
    max_int = intensity.max()
    norm_int = intensity / max_int if max_int > 0 else intensity

    # Draw sticks
    for t, h in zip(theta, norm_int):
        ax.plot([t, t], [0, h], color=color, linewidth=0.6, solid_capstyle="round", zorder=2)

    ax.set_xlabel(r"2$\theta$ (degrees)")
    ax.set_ylabel("Relative intensity")
    ax.set_ylim(0, 1.1)
    if standalone:
        apply_chart_polish(ax, "xrd_pattern")
    return ax


def gen_treemap(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Treemap with squarified algorithm, hierarchical size encoding, labels inside rectangles.

    Expects in semanticRoles: category (labels) and value (numeric sizes).
    Optionally parent for two-level hierarchy.  Uses squarify library when
    available; falls back to a simple slice-and-dice layout with matplotlib
    patches.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    cat_col = roles.get("category") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")
    parent_col = roles.get("parent")

    if cat_col is None or val_col is None:
        raise ValueError("treemap requires 'category' and 'value' in semanticRoles")

    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if parent_col and parent_col in df.columns:
        grouped = df.groupby(parent_col)[val_col].sum().sort_values(ascending=False)
        labels = grouped.index.astype(str).tolist()
        sizes = grouped.values.tolist()
    else:
        sub = df[[cat_col, val_col]].dropna().sort_values(val_col, ascending=False)
        labels = sub[cat_col].astype(str).tolist()
        sizes = sub[val_col].tolist()

    try:
        import squarify
        rects = squarify.squarify(squarify.normalize_sizes(sizes, 1, 1), 0, 0, 1, 1)
        for i, (r, lbl, sz) in enumerate(zip(rects, labels, sizes)):
            color = colors[i % len(colors)]
            ax.add_patch(plt.Rectangle((r["x"], r["y"]), r["dx"], r["dy"],
                                       facecolor=color, edgecolor="white",
                                       linewidth=0.6, alpha=0.85))
            if r["dx"] > 0.05 and r["dy"] > 0.03:
                ax.text(r["x"] + r["dx"] / 2, r["y"] + r["dy"] / 2,
                        f"{lbl}\n{sz:.0f}" if sz == int(sz) else f"{lbl}\n{sz:.2g}",
                        ha="center", va="center", fontsize=5, color="white",
                        fontweight="bold")
    except ImportError:
        # Fallback: simple slice-and-dice
        total = sum(sizes)
        x, y, w, h = 0, 0, 1, 1
        horizontal = True
        for i, (lbl, sz) in enumerate(zip(labels, sizes)):
            frac = sz / total if total > 0 else 1 / len(sizes)
            color = colors[i % len(colors)]
            if horizontal:
                dx = w * frac
                ax.add_patch(plt.Rectangle((x, y), dx, h, facecolor=color,
                                           edgecolor="white", linewidth=0.6, alpha=0.85))
                if dx > 0.05 and h > 0.03:
                    ax.text(x + dx / 2, y + h / 2, f"{lbl}\n{sz:.0f}",
                            ha="center", va="center", fontsize=5, color="white",
                            fontweight="bold")
                x += dx
            else:
                dy = h * frac
                ax.add_patch(plt.Rectangle((x, y), w, dy, facecolor=color,
                                           edgecolor="white", linewidth=0.6, alpha=0.85))
                if w > 0.05 and dy > 0.03:
                    ax.text(x + w / 2, y + dy / 2, f"{lbl}\n{sz:.0f}",
                            ha="center", va="center", fontsize=5, color="white",
                            fontweight="bold")
                y += dy
            horizontal = not horizontal

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "treemap")
    return ax


def gen_sunburst(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Sunburst / hierarchical donut chart with rings from center outward.

    Expects in semanticRoles: category (inner ring labels), value (numeric
    sizes), and optionally subcategory (outer ring labels).  When only
    category is provided, renders a single-ring donut.  With subcategory,
    draws two concentric rings where the outer ring segments are proportional
    within each inner-ring wedge.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    cat_col = roles.get("category") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")
    sub_col = roles.get("subcategory") or roles.get("subgroup")

    if cat_col is None or val_col is None:
        raise ValueError("sunburst requires 'category' and 'value' in semanticRoles")

    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    inner = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False)
    inner_labels = inner.index.tolist()
    inner_sizes = inner.values.tolist()
    inner_total = sum(inner_sizes)

    inner_colors = [colors[i % len(colors)] for i in range(len(inner_sizes))]

    # Inner ring (donut)
    wedges, _ = ax.pie(inner_sizes, radius=0.6, colors=inner_colors,
                       startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.35, edgecolor="white", linewidth=0.6))

    # Labels on inner ring
    for i, (wedge, lbl, sz) in enumerate(zip(wedges, inner_labels, inner_sizes)):
        ang = (wedge.theta2 + wedge.theta1) / 2
        rad = np.deg2rad(ang)
        r = 0.6 - 0.175
        x, y = r * np.cos(rad), r * np.sin(rad)
        pct = sz / inner_total * 100 if inner_total > 0 else 0
        if pct > 4:
            ax.text(x, y, f"{lbl}\n{pct:.0f}%", ha="center", va="center",
                    fontsize=4, color="white", fontweight="bold")

    # Outer ring (subcategories)
    if sub_col and sub_col in df.columns:
        outer_starts = []
        outer_sizes = []
        outer_colors = []
        angle = 90
        for i, (cat, cat_sz) in enumerate(zip(inner_labels, inner_sizes)):
            sub_df = df[df[cat_col] == cat].groupby(sub_col)[val_col].sum()
            sub_df = sub_df.sort_values(ascending=False)
            wedge_angle = (cat_sz / inner_total) * 360 if inner_total > 0 else 0
            base_color = inner_colors[i]
            # Lighten sub-colors by blending with white
            sub_colors_list = []
            n_sub = len(sub_df)
            for j in range(n_sub):
                blend = 0.2 + 0.6 * j / max(n_sub - 1, 1)
                r_c, g_c, b_c = int(base_color[1:3], 16), int(base_color[3:5], 16), int(base_color[5:7], 16)
                r_c = int(r_c + (255 - r_c) * blend)
                g_c = int(g_c + (255 - g_c) * blend)
                b_c = int(b_c + (255 - b_c) * blend)
                sub_colors_list.append(f"#{r_c:02x}{g_c:02x}{b_c:02x}")

            for j, (sub_lbl, sub_sz) in enumerate(zip(sub_df.index, sub_df.values)):
                sub_angle = (sub_sz / cat_sz) * wedge_angle if cat_sz > 0 else 0
                outer_starts.append(angle)
                outer_sizes.append(sub_angle)
                outer_colors.append(sub_colors_list[j % len(sub_colors_list)])
                # Sub-label
                mid_rad = np.deg2rad(angle + sub_angle / 2)
                r_outer = 0.6 + 0.175
                sx, sy = r_outer * np.cos(mid_rad), r_outer * np.sin(mid_rad)
                if sub_angle > 6:
                    ax.text(sx, sy, str(sub_lbl), ha="center", va="center",
                            fontsize=3.5, rotation=0, color="#333333")
                angle += sub_angle

        outer_wedges, _ = ax.pie(
            [s if s > 0 else 0.001 for s in outer_sizes],
            radius=0.95, colors=outer_colors, startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.3, edgecolor="white", linewidth=0.4))

    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_aspect("equal")
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "sunburst")
    return ax


def gen_swimmer_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Swimmer plot: horizontal bars for treatment duration with event markers.

    Each row is a patient.  A horizontal bar spans from start to end (e.g.
    treatment start/stop).  Optional marker columns encode events such as
    response, progression, or adverse events with distinct shapes/colors.

    Expects in semanticRoles: id (patient label), start, end, and optionally
    group (arm/cohort).  Event markers are read from columns whose names are
    listed in chartPlan.get("eventColumns", []).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    id_col = roles.get("id") or roles.get("label") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end") or roles.get("y") or roles.get("value")
    arm_col = roles.get("arm") or roles.get("cohort")

    if id_col is None or start_col is None or end_col is None:
        raise ValueError("swimmer_plot requires 'id', 'start', and 'end' in semanticRoles")

    df = df.sort_values(start_col).reset_index(drop=True)
    n = len(df)
    fig_height = max(60, 10 * n + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    arms = df[arm_col].unique().tolist() if arm_col and arm_col in df.columns else [None]
    arm_colors = _extract_colors(palette, [a for a in arms if a is not None])

    for i, (_, row) in enumerate(df.iterrows()):
        arm = row[arm_col] if arm_col and arm_col in df.columns else None
        color = arm_colors.get(arm, palette["categorical"][0]) if arm else palette["categorical"][0]
        ax.barh(i, row[end_col] - row[start_col], left=row[start_col],
                height=0.6, color=color, edgecolor="white", linewidth=0.4, zorder=2)

    event_cols = chartPlan.get("eventColumns", [])
    event_markers = ["o", "s", "^", "D", "P", "X"]
    for j, ecol in enumerate(event_cols):
        if ecol not in df.columns:
            continue
        marker = event_markers[j % len(event_markers)]
        for i, (_, row) in enumerate(df.iterrows()):
            val = row[ecol]
            if pd.notna(val) and val != 0:
                xpos = val if isinstance(val, (int, float)) else row[end_col]
                ax.scatter(xpos, i, marker=marker, s=18,
                           color=palette["categorical"][(j + 1) % len(palette["categorical"])],
                           edgecolor="white", linewidth=0.3, zorder=3)

    ax.set_yticks(range(n))
    ax.set_yticklabels(df[id_col].astype(str).tolist(), fontsize=5)
    ax.set_xlabel("Time")
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    if event_cols:
        handles = []
        for j, ecol in enumerate(event_cols):
            marker = event_markers[j % len(event_markers)]
            handles.append(plt.Line2D([0], [0], marker=marker, color="w",
                           markerfacecolor=palette["categorical"][(j + 1) % len(palette["categorical"])],
                           markersize=4, label=ecol))
        ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "swimmer_plot")
    return ax


def gen_risk_ratio_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Risk ratio forest plot (HR / OR with 95 % CI).

    Horizontal forest plot showing hazard ratios or odds ratios with
    confidence intervals for each subgroup.  A vertical reference line at 1
    (no effect) is drawn.  Optionally annotates p-values on the right margin.

    Expects in semanticRoles: label (subgroup name), estimate (HR or OR),
    ci_lower, ci_upper, and optionally p_value.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group") or roles.get("x")
    est_col = roles.get("estimate") or roles.get("value") or roles.get("y")
    lo_col = roles.get("ci_lower") or roles.get("lower")
    hi_col = roles.get("ci_upper") or roles.get("upper")
    p_col = roles.get("p_value") or roles.get("pvalue")

    if est_col is None or lo_col is None or hi_col is None:
        raise ValueError("risk_ratio_plot requires 'estimate', 'ci_lower', 'ci_upper' in semanticRoles")

    n = len(df)
    fig_height = max(60, 12 * n + 24) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    y_pos = np.arange(n)
    color = palette.get("categorical", ["#0072B2"])[0]

    for i, (_, row) in enumerate(df.iterrows()):
        est = row[est_col]
        lo = row[lo_col]
        hi = row[hi_col]
        ax.plot([lo, hi], [i, i], color=color, linewidth=0.8,
                solid_capstyle="round", zorder=2)
        ax.plot(est, i, "D", color=color, markersize=4, zorder=3)

    ax.axvline(1, color="black", linewidth=0.6, linestyle="--", zorder=1)

    if label_col and label_col in df.columns:
        labels = df[label_col].astype(str).tolist()
    else:
        labels = [str(i + 1) for i in range(n)]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=5)

    # Annotate estimate [CI] on right margin
    x_max = ax.get_xlim()[1]
    for i, (_, row) in enumerate(df.iterrows()):
        ci_text = f"{row[est_col]:.2f} [{row[lo_col]:.2f}, {row[hi_col]:.2f}]"
        ax.text(x_max * 1.05, i, ci_text, fontsize=4, va="center", ha="left",
                color="#333", transform=ax.get_yaxis_transform())

    if p_col and p_col in df.columns:
        p_x = x_max * 1.45
        ax.text(p_x, n + 0.3, "p", fontsize=5, fontstyle="italic", fontweight="bold",
                va="bottom", ha="center", transform=ax.get_yaxis_transform())
        for i, (_, row) in enumerate(df.iterrows()):
            pval = row[p_col]
            p_text = "<0.001" if pval < 0.001 else f"{pval:.3g}"
            ax.text(p_x, i, p_text, fontsize=4, va="center", ha="center",
                    transform=ax.get_yaxis_transform())

    ratio_label = chartPlan.get("ratioLabel", "Risk ratio")
    ax.set_xlabel(f"{ratio_label} (95 % CI)")
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if standalone:
        apply_chart_polish(ax, "risk_ratio_plot")
    return ax


def gen_sankey(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified Sankey diagram showing flow between stages using matplotlib patches.

    Expects columns: source (origin stage), target (destination stage), and
    value (flow magnitude) in semanticRoles.  Draws horizontal node bars at
    left/right with filled bezier-like flow ribbons connecting them.
    Nature style: no grid, open-L spines, publication fonts.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    src_col = roles.get("source") or roles.get("group")
    tgt_col = roles.get("target") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")

    if src_col is None or tgt_col is None or val_col is None:
        raise ValueError("sankey requires 'source', 'target', and 'value' in semanticRoles")

    flows = df[[src_col, tgt_col, val_col]].dropna()
    sources = flows[src_col].unique().tolist()
    targets = flows[tgt_col].unique().tolist()

    fallback = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                            "#C8553D", "#7A6C8F", "#2B6F77"])
    all_nodes = list(dict.fromkeys(sources + targets))
    color_map = {n: fallback[i % len(fallback)] for i, n in enumerate(all_nodes)}

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 80 * (1 / 25.4)),
                           constrained_layout=True)

    # Node heights proportional to total flow through each node
    node_totals = {}
    for _, row in flows.iterrows():
        node_totals[row[src_col]] = node_totals.get(row[src_col], 0) + row[val_col]
        node_totals[row[tgt_col]] = node_totals.get(row[tgt_col], 0) + row[val_col]
    max_total = max(node_totals.values()) if node_totals else 1

    # Position source nodes on left, target nodes on right
    y_src, y_tgt = {}, {}
    src_gap, tgt_gap = 0.05, 0.05
    src_y = 0.0
    for s in sources:
        h = node_totals.get(s, 1) / max_total * 0.8
        y_src[s] = (src_y, src_y + h)
        src_y += h + src_gap
    tgt_y = 0.0
    for t in targets:
        h = node_totals.get(t, 1) / max_total * 0.8
        y_tgt[t] = (tgt_y, tgt_y + h)
        tgt_y += h + tgt_gap

    # Draw node bars
    for n, (y0, y1) in {**y_src, **y_tgt}.items():
        x = 0.0 if n in y_src else 1.0
        ax.barh((y0 + y1) / 2, 0.03, height=y1 - y0, left=x - 0.015,
                color=color_map[n], edgecolor="none", alpha=0.85, zorder=3)
        ax.text(x + (0.06 if n in y_src else -0.06), (y0 + y1) / 2, n,
                fontsize=5, ha="left" if n in y_src else "right", va="center")

    # Draw flow bands as filled bezier-like polygons
    src_offset = {s: y_src[s][0] for s in sources}
    tgt_offset = {t: y_tgt[t][0] for t in targets}
    for _, row in flows.iterrows():
        s, t, v = row[src_col], row[tgt_col], row[val_col]
        band_h = v / max_total * 0.8
        sy0, ty0 = src_offset[s], tgt_offset[t]
        src_offset[s] += band_h
        tgt_offset[t] += band_h
        xs = [0.0, 0.0, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0]
        ys = [sy0, sy0 + band_h, sy0 + band_h, ty0 + band_h,
              ty0 + band_h, ty0, ty0, sy0, sy0]
        ax.fill(xs, ys, color=color_map[s], alpha=0.3, linewidth=0)

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.05, max(src_y, tgt_y) + 0.05)
    ax.axis("off")
    ax.set_title(chartPlan.get("title", ""), fontsize=7, pad=8)
    if standalone:
        apply_chart_polish(ax, "sankey")
    return ax


def gen_radar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Radar / spider chart for multi-attribute comparison across groups.

    Expects columns: attribute (axis label), group (series), and value in
    semanticRoles.  One polygon per group, filled with semi-transparent color.
    Axes are radial with attribute labels at each spoke.  Nature style: thin
    lines, no grid fill, publication fonts.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    attr_col = roles.get("attribute") or roles.get("x")
    group_col = roles.get("group")
    val_col = roles.get("value") or roles.get("y")

    if attr_col is None or val_col is None:
        raise ValueError("radar requires 'attribute' and 'value' in semanticRoles")

    attributes = df[attr_col].dropna().unique().tolist()
    n_attrs = len(attributes)
    if n_attrs < 3:
        raise ValueError("radar requires at least 3 attributes")

    fallback = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                            "#C8553D", "#7A6C8F", "#2B6F77"])
    cat_map = palette.get("categoryMap", {})

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           subplot_kw=dict(polar=True),
                           constrained_layout=True)

    angles = np.linspace(0, 2 * np.pi, n_attrs, endpoint=False).tolist()
    angles += angles[:1]  # close polygon

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(attributes, fontsize=5)
    if hasattr(ax, 'set_rlabel_position'):
        ax.set_rlabel_position(30)
        ax.yaxis.set_tick_params(labelsize=4)
        ax.grid(linewidth=0.4, color="#CCCCCC")
        ax.spines["polar"].set_linewidth(0.4)

    if group_col and group_col in df.columns:
        groups = df[group_col].dropna().unique().tolist()
        for i, grp in enumerate(groups):
            subset = df[df[group_col] == grp]
            values = []
            for attr in attributes:
                match = subset[subset[attr_col] == attr][val_col]
                values.append(match.values[0] if len(match) > 0 else 0)
            values += values[:1]
            color = cat_map.get(grp, fallback[i % len(fallback)])
            ax.plot(angles, values, linewidth=0.8, color=color, label=grp)
            ax.fill(angles, values, alpha=0.15, color=color)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1),
                  frameon=False, fontsize=5)
    else:
        values = []
        for attr in attributes:
            match = df[df[attr_col] == attr][val_col]
            values.append(match.values[0] if len(match) > 0 else 0)
        values += values[:1]
        color = fallback[0]
        ax.plot(angles, values, linewidth=0.8, color=color)
        ax.fill(angles, values, alpha=0.15, color=color)

    if standalone:
        apply_chart_polish(ax, "radar")
    return ax


def gen_likert_divergent(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Diverging stacked bar chart for Likert scale responses.

    Bars extend left (negative) and right (positive) from a center line at
    neutral.  Expects one row per respondent and columns whose names match the
    Likert categories (e.g., 'Strongly Disagree', 'Disagree', 'Neutral',
    'Agree', 'Strongly Agree').  The question/item labels come from
    semanticRoles['group']; the Likert columns are auto-detected from a
    predefined ordered list.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    item_col = roles.get("group") or roles.get("label") or roles.get("x")

    if item_col is None:
        raise ValueError("likert_divergent requires a 'group' or 'label' column for items")

    likert_order = ["Strongly Disagree", "Disagree", "Neutral",
                    "Agree", "Strongly Agree"]
    cats = [c for c in likert_order if c in df.columns]
    if not cats:
        cats = [c for c in df.columns if c != item_col]

    n_cats = len(cats)
    neutral_idx = n_cats // 2
    likert_colors = ["#B2182B", "#D6604D", "#F7F7F7", "#4393C3", "#2166AF"]
    colors = [likert_colors[i % len(likert_colors)] for i in range(n_cats)]

    counts = df.groupby(item_col)[cats].sum()
    pct = counts.div(counts.sum(axis=1), axis=0) * 100
    items = pct.index.tolist()
    n_items = len(items)
    y_pos = np.arange(n_items)

    fig_height = max(60, 12 * n_items + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    for i, item in enumerate(items):
        left_neg = -pct.loc[item, cats[:neutral_idx]].sum()
        for j, cat in enumerate(cats):
            val = pct.loc[item, cat]
            if j < neutral_idx:
                ax.barh(i, val, left=left_neg, height=0.65,
                        color=colors[j], edgecolor="white", linewidth=0.3)
                left_neg += val
            elif j == neutral_idx:
                left_pos = 0
                ax.barh(i, val, left=left_pos, height=0.65,
                        color=colors[j], edgecolor="white", linewidth=0.3)
                left_pos += val
            else:
                ax.barh(i, val, left=left_pos, height=0.65,
                        color=colors[j], edgecolor="white", linewidth=0.3)
                left_pos += val

    ax.axvline(0, color="black", linewidth=0.6, linestyle="-", zorder=3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(items, fontsize=5)
    ax.set_xlabel("Percentage of responses")
    ax.set_xlim(-105, 105)
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=colors[j],
                              edgecolor="white", linewidth=0.3, label=cats[j])
               for j in range(n_cats)]
    ax.legend(handles=handles, loc="lower center", ncol=n_cats,
              frameon=False, fontsize=5, bbox_to_anchor=(0.5, -0.18))
    if standalone:
        apply_chart_polish(ax, "likert_divergent")
    return ax


def gen_likert_stacked(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Horizontal stacked bar chart for Likert responses.

    Each bar represents one item/question; segments show the percentage
    breakdown across ordered Likert categories with percentage labels inside
    each segment.  Expects one row per respondent, item labels in
    semanticRoles['group'], and Likert response columns auto-detected from a
    predefined ordered list.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    item_col = roles.get("group") or roles.get("label") or roles.get("x")

    if item_col is None:
        raise ValueError("likert_stacked requires a 'group' or 'label' column for items")

    likert_order = ["Strongly Disagree", "Disagree", "Neutral",
                    "Agree", "Strongly Agree"]
    cats = [c for c in likert_order if c in df.columns]
    if not cats:
        cats = [c for c in df.columns if c != item_col]

    n_cats = len(cats)
    likert_colors = ["#B2182B", "#D6604D", "#F7F7F7", "#4393C3", "#2166AF"]
    colors = [likert_colors[i % len(likert_colors)] for i in range(n_cats)]

    counts = df.groupby(item_col)[cats].sum()
    pct = counts.div(counts.sum(axis=1), axis=0) * 100
    items = pct.index.tolist()
    n_items = len(items)
    y_pos = np.arange(n_items)

    fig_height = max(60, 12 * n_items + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    left = np.zeros(n_items)
    for j, cat in enumerate(cats):
        vals = pct[cat].values
        bars = ax.barh(y_pos, vals, left=left, height=0.65,
                       color=colors[j], edgecolor="white", linewidth=0.3,
                       label=cat)
        # Percentage labels inside segments wider than 8%
        for k in range(n_items):
            if vals[k] >= 8:
                ax.text(left[k] + vals[k] / 2, y_pos[k], f"{vals[k]:.0f}%",
                        ha="center", va="center", fontsize=4, color="black")
        left += vals

    ax.set_yticks(y_pos)
    ax.set_yticklabels(items, fontsize=5)
    ax.set_xlabel("Percentage of responses")
    ax.set_xlim(0, 105)
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    ax.legend(loc="lower center", ncol=n_cats, frameon=False, fontsize=5,
              bbox_to_anchor=(0.5, -0.18))
    if standalone:
        apply_chart_polish(ax, "likert_stacked")
    return ax


def gen_clustered_bar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Clustered bar chart: multiple metrics per group, side-by-side bars.

    Each group gets one cluster of bars, one bar per metric column.
    Expects in semanticRoles: group (category axis) and a list of value
    columns encoded as semicolon-separated string in 'value' or 'y'.
    Falls back to all numeric columns when no explicit value list is given.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_spec = roles.get("value") or roles.get("y")

    if group_col is None:
        raise ValueError("clustered_bar requires a 'group' column in semanticRoles")

    if value_spec and ";" in str(value_spec):
        metric_cols = [c.strip() for c in str(value_spec).split(";")]
    elif value_spec and value_spec in df.columns:
        metric_cols = [value_spec]
    else:
        metric_cols = [c for c in df.select_dtypes(include="number").columns if c != group_col]

    categories = df[group_col].dropna().unique().tolist()
    n_metrics = len(metric_cols)
    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)
    bar_width = 0.8 / n_metrics
    x = np.arange(len(categories))

    for mi, mcol in enumerate(metric_cols):
        means = [df[df[group_col] == c][mcol].mean() for c in categories]
        ax.bar(x + mi * bar_width, means, width=bar_width,
               color=colors[mi % len(colors)], edgecolor="white",
               linewidth=0.4, label=mcol, zorder=2)

    ax.set_xticks(x + bar_width * (n_metrics - 1) / 2)
    ax.set_xticklabels(categories, fontsize=5)
    ax.set_xlabel(group_col)
    ax.set_ylabel("Value")
    ax.legend(frameon=False, fontsize=5, ncol=min(n_metrics, 4))
    if standalone:
        apply_chart_polish(ax, "clustered_bar")
    return ax


def gen_grouped_bar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Grouped bar chart with error bars: subgroups within categories.

    Each category on the x-axis contains one bar per subgroup, with SEM
    error bars.  Expects in semanticRoles: group (x-axis categories),
    subgroup (bar series within each group), and value (numeric y).
    Computes mean and SEM per cell for error bar display.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    subgroup_col = roles.get("subgroup") or roles.get("color") or roles.get("hue")
    value_col = roles.get("value") or roles.get("y")

    if group_col is None or subgroup_col is None or value_col is None:
        raise ValueError("grouped_bar requires 'group', 'subgroup', and 'value' in semanticRoles")

    categories = df[group_col].dropna().unique().tolist()
    subgroups = df[subgroup_col].dropna().unique().tolist()
    n_sub = len(subgroups)
    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)
    bar_width = 0.8 / n_sub
    x = np.arange(len(categories))

    for si, sub in enumerate(subgroups):
        means, sems = [], []
        for cat in categories:
            cell = df[(df[group_col] == cat) & (df[subgroup_col] == sub)][value_col].dropna()
            means.append(cell.mean() if len(cell) > 0 else 0)
            sems.append(cell.sem() if len(cell) > 1 else 0)
        ax.bar(x + si * bar_width, means, width=bar_width, yerr=sems,
               color=colors[si % len(colors)], edgecolor="white",
               linewidth=0.4, capsize=2, error_kw=dict(linewidth=0.5),
               label=sub, zorder=2)

    ax.set_xticks(x + bar_width * (n_sub - 1) / 2)
    ax.set_xticklabels(categories, fontsize=5)
    ax.set_xlabel(group_col)
    ax.set_ylabel(value_col)
    ax.legend(frameon=False, fontsize=5, ncol=min(n_sub, 4))
    if standalone:
        apply_chart_polish(ax, "grouped_bar")
    return ax


def gen_ordination_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Ordination plot (PCoA/NMDS) with group confidence ellipses.

    Expects in semanticRoles: x (axis 1 scores), y (axis 2 scores), and group
    (sample grouping).  Draws 95 % confidence ellipses per group using the
    chi-squared distribution.  Nature style: thin lines, no grid, publication
    fonts.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("axis1")
    y_col = roles.get("y") or roles.get("axis2")
    group_col = roles.get("group")

    if x_col is None or y_col is None:
        raise ValueError("ordination_plot requires 'x' and 'y' (axis scores) in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)
    color_map = _extract_colors(palette, df[group_col].dropna().unique()) if group_col else {}
    method = chartPlan.get("method", "PCoA")

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        for cat in categories:
            sub = df[df[group_col] == cat]
            color = color_map.get(cat, "#666666")
            ax.scatter(sub[x_col], sub[y_col], s=12, alpha=0.7, color=color,
                       linewidth=0.3, edgecolor="white", label=cat, zorder=2)
            # 95 % confidence ellipse via chi-squared (df=2, p=0.95 -> 5.991)
            if len(sub) >= 3:
                from matplotlib.patches import Ellipse
                cov = np.cov(sub[x_col], sub[y_col])
                vals, vecs = np.linalg.eigh(cov)
                angle = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
                chi2_val = 5.991  # chi2.ppf(0.95, 2)
                w, h = 2 * np.sqrt(vals * chi2_val)
                ell = Ellipse((sub[x_col].mean(), sub[y_col].mean()), w, h,
                              angle=angle, edgecolor=color, facecolor=color,
                              alpha=0.12, linewidth=0.6)
                ax.add_patch(ell)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    else:
        ax.scatter(df[x_col], df[y_col], s=12, alpha=0.7,
                   color=palette.get("categorical", ["#0072B2"])[0],
                   linewidth=0.3, edgecolor="white", zorder=2)

    ax.set_xlabel(f"{method} axis 1")
    ax.set_ylabel(f"{method} axis 2")
    if standalone:
        apply_chart_polish(ax, "ordination_plot")
    return ax


def gen_biodiversity_radar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Biodiversity radar: multiple diversity indices on polar axes.

    Expects in semanticRoles: attribute (diversity index name) and value
    (index value).  Optionally group for comparing communities.  Indices are
    plotted as radial spokes (e.g. Shannon, Simpson, Richness, Evenness,
    Chao1).  Values are min-max normalised to [0, 1] for visual comparison.
    Nature style: thin lines, no grid fill, publication fonts.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    attr_col = roles.get("attribute") or roles.get("x")
    group_col = roles.get("group")
    val_col = roles.get("value") or roles.get("y")

    if attr_col is None or val_col is None:
        raise ValueError("biodiversity_radar requires 'attribute' and 'value' in semanticRoles")

    indices = df[attr_col].dropna().unique().tolist()
    n_idx = len(indices)
    if n_idx < 3:
        raise ValueError("biodiversity_radar requires at least 3 diversity indices")

    fallback = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                            "#C8553D", "#7A6C8F", "#2B6F77"])
    cat_map = palette.get("categoryMap", {})

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           subplot_kw=dict(polar=True),
                           constrained_layout=True)

    angles = np.linspace(0, 2 * np.pi, n_idx, endpoint=False).tolist()
    angles += angles[:1]

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(indices, fontsize=5)
    if hasattr(ax, 'set_rlabel_position'):
        ax.set_rlabel_position(30)
        ax.yaxis.set_tick_params(labelsize=4)
        ax.grid(linewidth=0.4, color="#CCCCCC")
        ax.spines["polar"].set_linewidth(0.4)

    # Normalise values per index to [0, 1] for cross-index comparability
    if group_col and group_col in df.columns:
        groups = df[group_col].dropna().unique().tolist()
        for i, grp in enumerate(groups):
            subset = df[df[group_col] == grp]
            vals = []
            for idx_name in indices:
                match = subset[subset[attr_col] == idx_name][val_col]
                vals.append(match.values[0] if len(match) > 0 else 0)
            # Min-max normalise
            vmin, vmax = min(vals), max(vals)
            rng = vmax - vmin if vmax != vmin else 1.0
            vals = [(v - vmin) / rng for v in vals]
            vals += vals[:1]
            color = cat_map.get(grp, fallback[i % len(fallback)])
            ax.plot(angles, vals, linewidth=0.8, color=color, label=grp)
            ax.fill(angles, vals, alpha=0.15, color=color)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1),
                  frameon=False, fontsize=5)
    else:
        vals = []
        for idx_name in indices:
            match = df[df[attr_col] == idx_name][val_col]
            vals.append(match.values[0] if len(match) > 0 else 0)
        vmin, vmax = min(vals), max(vals)
        rng = vmax - vmin if vmax != vmin else 1.0
        vals = [(v - vmin) / rng for v in vals]
        vals += vals[:1]
        color = fallback[0]
        ax.plot(angles, vals, linewidth=0.8, color=color)
        ax.fill(angles, vals, alpha=0.15, color=color)

    if standalone:
        apply_chart_polish(ax, "biodiversity_radar")
    return ax


def gen_bubble_scatter(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Bubble scatter chart with size and color encoding.

    x and y are numeric axes; a third variable controls marker size and an
    optional fourth variable (or group column) controls marker color.  Uses
    Nature-style open-L spines, no grid, and publication font sizes.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x")
    y_col = roles.get("y") or roles.get("value")
    size_col = roles.get("size") or roles.get("z")
    color_col = roles.get("color") or roles.get("group")

    if x_col is None or y_col is None:
        raise ValueError("bubble_scatter requires 'x' and 'y' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    sizes = df[size_col] * 6 if size_col and size_col in df.columns else np.full(len(df), 30)

    if color_col and color_col in df.columns:
        categories = df[color_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            mask = df[color_col] == cat
            ax.scatter(df.loc[mask, x_col], df.loc[mask, y_col],
                       s=sizes[mask], color=color_map[cat], alpha=0.6,
                       edgecolor="white", linewidth=0.4, label=cat, zorder=2)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5, title_fontsize=5)
    else:
        color = palette.get("categorical", ["#0072B2"])[0]
        ax.scatter(df[x_col], df[y_col], s=sizes, color=color, alpha=0.6,
                   edgecolor="white", linewidth=0.4, zorder=2)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    if standalone:
        apply_chart_polish(ax, "bubble_scatter")
    return ax


def gen_connected_scatter(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Connected scatter plot showing trajectory in x-y space.

    Points are drawn in row order and connected by sequential lines to reveal
    temporal or ordinal trajectories.  Optional group column draws separate
    trajectories per category.  Nature-style open-L spines, no grid.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x")
    y_col = roles.get("y") or roles.get("value")
    group_col = roles.get("group")

    if x_col is None or y_col is None:
        raise ValueError("connected_scatter requires 'x' and 'y' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            sub = df[df[group_col] == cat].sort_values(x_col)
            color = color_map[cat]
            ax.plot(sub[x_col], sub[y_col], color=color, linewidth=0.8,
                    solid_capstyle="round", zorder=1)
            ax.scatter(sub[x_col], sub[y_col], s=14, color=color, alpha=0.7,
                       edgecolor="white", linewidth=0.3, zorder=2)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    else:
        ordered = df.sort_values(x_col)
        color = palette.get("categorical", ["#0072B2"])[0]
        ax.plot(ordered[x_col], ordered[y_col], color=color, linewidth=0.8,
                solid_capstyle="round", zorder=1)
        ax.scatter(ordered[x_col], ordered[y_col], s=14, color=color, alpha=0.7,
                   edgecolor="white", linewidth=0.3, zorder=2)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    if standalone:
        apply_chart_polish(ax, "connected_scatter")
    return ax


def gen_species_abundance(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Horizontal bar chart of species abundance, sorted descending.

    Ecology-style plot where each bar represents a species (or OTU/ASV) and
    its count or relative abundance.  Bars are sorted from most to least
    abundant and drawn horizontally for long species labels.  Uses Nature
    style: open-L spines, no grid, round line caps, 6 pt font.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    species_col = roles.get("species") or roles.get("group") or roles.get("label")
    abundance_col = roles.get("abundance") or roles.get("value") or roles.get("y")

    if species_col is None or abundance_col is None:
        raise ValueError("species_abundance requires 'species' and 'abundance' in semanticRoles")

    agg = df.groupby(species_col)[abundance_col].sum().sort_values(ascending=True)
    n = len(agg)

    fig_height = max(60, 5 * n + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    colors = palette.get("categorical", ["#1F4E79"])[0]
    ax.barh(range(n), agg.values, color=colors, edgecolor="white",
            linewidth=0.4, height=0.7, zorder=2)

    ax.set_yticks(range(n))
    ax.set_yticklabels(agg.index, fontsize=5)
    ax.set_xlabel("Abundance")
    ax.set_ylabel("")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "species_abundance")
    return ax


def gen_shannon_diversity(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Bar chart comparing Shannon diversity index across groups with error bars.

    Expects one row per sample with a group column and a Shannon index value.
    Computes mean and SEM per group, then draws vertical bars with error caps.
    Nature style: open-L spines, no grid, round line caps, 6 pt font.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value") or roles.get("y") or roles.get("shannon")

    if group_col is None or value_col is None:
        raise ValueError("shannon_diversity requires 'group' and 'value' in semanticRoles")

    stats = df.groupby(group_col)[value_col].agg(["mean", "sem"]).reset_index()
    categories = stats[group_col].tolist()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    bar_colors = [color_map[c] for c in categories]
    ax.bar(range(len(categories)), stats["mean"], yerr=stats["sem"],
           color=bar_colors, edgecolor="white", linewidth=0.4,
           width=0.6, capsize=3, error_kw=dict(linewidth=0.6, elinewidth=0.6),
           zorder=2)

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, fontsize=5)
    ax.set_xlabel("")
    ax.set_ylabel("Shannon diversity index")
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "shannon_diversity")
    return ax


# ──────────────────────────────────────────────────────────────
# Core Chart Generators (Phase 2 default recommendations)
# ──────────────────────────────────────────────────────────────

def gen_line_ci(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Line chart with confidence interval bands (mean ± CI or SE)."""
    standalone = ax is None
    group_col, value_col, x_col = _resolve_roles(dataProfile)
    if x_col is None or value_col is None:
        raise ValueError("line_ci requires 'x' and 'value' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            summary = grp.groupby(x_col)[value_col].agg(["mean", "sem"]).reset_index()
            ax.plot(summary[x_col], summary["mean"], color=col, lw=1, label=str(name))
            ax.fill_between(summary[x_col],
                            summary["mean"] - 1.96 * summary["sem"],
                            summary["mean"] + 1.96 * summary["sem"],
                            alpha=0.15, color=col)
    else:
        summary = df.groupby(x_col)[value_col].agg(["mean", "sem"]).reset_index()
        ax.plot(summary[x_col], summary["mean"], color="#000000", lw=1)
        ax.fill_between(summary[x_col],
                        summary["mean"] - 1.96 * summary["sem"],
                        summary["mean"] + 1.96 * summary["sem"],
                        alpha=0.15, color="#000000")

    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    if group_col:
        ax.legend(frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "line_ci")
    return ax


def gen_km(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Kaplan-Meier survival curve with optional at-risk table."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    time_col = roles.get("time") or roles.get("duration")
    event_col = roles.get("event") or roles.get("status")
    group_col = roles.get("group")

    if time_col is None or event_col is None:
        raise ValueError("km requires 'time' and 'event' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    def _km_curve(times, events):
        """Compute KM survival estimate."""
        unique_times = np.sort(times[events == 1].unique())
        n_at_risk = len(times)
        surv = [1.0]
        t_points = [0]
        for t in unique_times:
            d = ((times == t) & (events == 1)).sum()
            n = (times >= t).sum()
            if n > 0:
                surv.append(surv[-1] * (1 - d / n))
                t_points.append(t)
        return np.array(t_points), np.array(surv)

    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            t_km, s_km = _km_curve(grp[time_col], grp[event_col])
            ax.step(t_km, s_km, where="post", color=col, lw=1, label=str(name))
    else:
        t_km, s_km = _km_curve(df[time_col], df[event_col])
        ax.step(t_km, s_km, where="post", color="#000000", lw=1)

    ax.set_xlabel("Time")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(0, 1.05)
    if group_col:
        ax.legend(frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "km")
    return ax


def gen_forest(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Forest plot for effect sizes with confidence intervals."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    estimate_col = roles.get("estimate") or roles.get("value")
    ci_low_col = roles.get("ci_low")
    ci_high_col = roles.get("ci_high")

    if label_col is None or estimate_col is None:
        raise ValueError("forest requires 'label' and 'estimate' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = range(len(df))
    estimates = df[estimate_col].values

    if ci_low_col and ci_high_col:
        ci_low = df[ci_low_col].values
        ci_high = df[ci_high_col].values
    else:
        # Use SE-based approximate CI
        se = df[roles.get("se", estimate_col)].values if roles.get("se") else estimates * 0.1
        ci_low = estimates - 1.96 * se
        ci_high = estimates + 1.96 * se

    ax.errorbar(estimates, y_pos,
                xerr=[estimates - ci_low, ci_high - estimates],
                fmt="o", color="#000000", markersize=4, capsize=3,
                elinewidth=0.6, capthick=0.6, linewidth=0.6)

    ax.axvline(0, color="#999999", lw=0.5, ls="--", alpha=0.7)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df[label_col].values, fontsize=5)
    ax.set_xlabel("Effect size (95% CI)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "forest")
    return ax


def gen_spaghetti(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Spaghetti plot: individual subject trajectories over time."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    time_col = roles.get("time") or roles.get("x")
    value_col = roles.get("value") or roles.get("y")
    subject_col = roles.get("subject_id") or roles.get("id")
    group_col = roles.get("group")

    if time_col is None or value_col is None:
        raise ValueError("spaghetti requires 'time' and 'value' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if subject_col:
        for _, subj_df in df.groupby(subject_col):
            grp = subj_df[group_col].iloc[0] if group_col else None
            col = color_map.get(grp, "#999999")
            ax.plot(subj_df[time_col], subj_df[value_col],
                    color=col, lw=0.4, alpha=0.4)
    else:
        ax.plot(df[time_col], df[value_col], color="#999999", lw=0.4, alpha=0.4)

    # Overlay group means
    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            summary = grp.groupby(time_col)[value_col].mean()
            ax.plot(summary.index, summary.values, color=col, lw=2, label=str(name))
        ax.legend(frameon=False, fontsize=5)

    ax.set_xlabel(time_col)
    ax.set_ylabel(value_col)
    if standalone:
        apply_chart_polish(ax, "spaghetti")
    return ax


def gen_dumbbell(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Dumbbell plot: before/after or treatment delta per subject."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    before_col = roles.get("before") or roles.get("value_pre")
    after_col = roles.get("after") or roles.get("value_post")

    if label_col is None or before_col is None or after_col is None:
        raise ValueError("dumbbell requires 'label', 'before', and 'after' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = range(len(df))
    for i, (_, row) in enumerate(df.iterrows()):
        ax.plot([row[before_col], row[after_col]], [i, i],
                color="#999999", lw=1, zorder=1)
    ax.scatter(df[before_col], y_pos, c="#000000", s=20, zorder=2, label="Before")
    ax.scatter(df[after_col], y_pos, c="#E69F00", s=20, zorder=2, label="After")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df[label_col].values, fontsize=5)
    ax.set_xlabel("Value")
    ax.invert_yaxis()
    ax.legend(frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "dumbbell")
    return ax


# ──────────────────────────────────────────────────────────────
# Core Phase 2 Default Charts (highest priority)
# ──────────────────────────────────────────────────────────────

def gen_violin_strip(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Violin + strip plot: distribution-aware group comparison."""
    standalone = ax is None
    group_col, value_col, _ = _resolve_roles(dataProfile)
    if group_col is None or value_col is None:
        raise ValueError("violin_strip requires 'group' and 'value' in semanticRoles")

    categories = df[group_col].unique()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    sns.violinplot(data=df, x=group_col, y=value_col, hue=group_col,
                   palette=color_map, width=0.5, inner=None, linewidth=0.6,
                   legend=False, ax=ax, alpha=0.3)
    sns.stripplot(data=df, x=group_col, y=value_col, hue=group_col,
                  palette=color_map, size=3, jitter=0.15, alpha=0.7,
                  linewidth=0.4, edgecolor="white", legend=False, ax=ax)
    if ax.get_legend():
        ax.get_legend().remove()

    ax.set_xlabel("")
    ax.set_ylabel(value_col)
    apply_chart_polish(ax, "violin_strip")
    return ax


def gen_box_strip(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Box + strip plot: robust summary plus individual points."""
    standalone = ax is None
    group_col, value_col, _ = _resolve_roles(dataProfile)
    if group_col is None or value_col is None:
        raise ValueError("box_strip requires 'group' and 'value' in semanticRoles")

    categories = df[group_col].unique()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    sns.boxplot(data=df, x=group_col, y=value_col, hue=group_col,
                palette=color_map, width=0.4, fliersize=0, linewidth=0.6,
                legend=False, ax=ax)
    sns.stripplot(data=df, x=group_col, y=value_col, hue=group_col,
                  palette=color_map, size=2.5, jitter=0.15, alpha=0.5,
                  linewidth=0.3, edgecolor="white", legend=False, ax=ax)
    if ax.get_legend():
        ax.get_legend().remove()

    ax.set_xlabel("")
    ax.set_ylabel(value_col)
    apply_chart_polish(ax, "box_strip")
    return ax


def gen_paired_lines(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Paired lines: before/after or matched conditions connected by lines."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    before_col = roles.get("before") or roles.get("value_pre")
    after_col = roles.get("after") or roles.get("value_post")
    pair_col = roles.get("pair_id") or roles.get("subject_id")

    if before_col is None or after_col is None:
        raise ValueError("paired_lines requires 'before' and 'after' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    for i, (_, row) in enumerate(df.iterrows()):
        ax.plot([0, 1], [row[before_col], row[after_col]],
                color="#999999", lw=0.5, alpha=0.5)
    ax.scatter(np.zeros(len(df)), df[before_col], c="#000000", s=15, zorder=5)
    ax.scatter(np.ones(len(df)), df[after_col], c="#E69F00", s=15, zorder=5)
    ax.plot([0, 1], [df[before_col].mean(), df[after_col].mean()],
            c="#D55E00", lw=2, zorder=6)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Before", "After"])
    ax.set_ylabel("Value")
    if standalone:
        apply_chart_polish(ax, "paired_lines")
    return ax


def gen_volcano(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Volcano plot: fold-change vs significance with threshold lines."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    fc_col = roles.get("fold_change") or roles.get("x")
    pval_col = roles.get("p_value")
    label_col = roles.get("label_col") or roles.get("feature_id")

    if fc_col is None or pval_col is None:
        raise ValueError("volcano requires 'fold_change' and 'p_value' in semanticRoles")

    df = df.copy()
    df["nlogp"] = -np.log10(df[pval_col].clip(lower=1e-20))
    fc_thresh = 1
    pval_thresh = 0.05

    def _cat(row):
        if row[pval_col] < pval_thresh and row[fc_col] > fc_thresh:
            return "Up"
        elif row[pval_col] < pval_thresh and row[fc_col] < -fc_thresh:
            return "Down"
        return "NS"

    df["cat"] = df.apply(_cat, axis=1)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)

    colors = {"Up": "#D55E00", "Down": "#0072B2", "NS": "#999999"}
    for cat, col in colors.items():
        s = df[df.cat == cat]
        ax.scatter(s[fc_col], s["nlogp"], c=col, s=12, alpha=0.7,
                   linewidth=0.3, edgecolors="white", label=f"{cat} ({len(s)})")

    ax.axhline(-np.log10(pval_thresh), color="black", lw=0.5, ls="--", alpha=0.5)
    ax.axvline(fc_thresh, color="black", lw=0.5, ls="--", alpha=0.5)
    ax.axvline(-fc_thresh, color="black", lw=0.5, ls="--", alpha=0.5)

    if label_col:
        top = df[df.cat != "NS"].nlargest(5, "nlogp")
        for idx, (_, row) in enumerate(top.iterrows()):
            y_off = (idx % 3) * df["nlogp"].max() * 0.04
            ax.annotate(row[label_col], (row[fc_col], row["nlogp"] + y_off),
                        fontsize=4, ha="center", va="bottom",
                        arrowprops=dict(arrowstyle="-", lw=0.3, color="black"))

    ax.set_xlabel("log2(Fold Change)")
    ax.set_ylabel("-log10(adj. p-value)")
    ax.legend(loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "volcano")
    return ax


def gen_heatmap_cluster(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Heatmap with hierarchical clustering: Z-scored expression/abundance matrix."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    # If data is matrix-like, use directly; otherwise pivot
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) >= 3:
        Z = df[numeric_cols]
        # Z-score normalize
        Z = Z.sub(Z.mean(1), axis=0).div(Z.std(1).replace(0, 1), axis=0)
    else:
        roles = dataProfile.get("semanticRoles", {})
        group_col = roles.get("group")
        value_col = roles.get("value")
        feature_col = roles.get("feature_id")
        if group_col and value_col and feature_col:
            pivot = df.pivot_table(index=feature_col, columns=group_col, values=value_col)
            Z = pivot.sub(pivot.mean(1), axis=0).div(pivot.std(1).replace(0, 1), axis=0)
        else:
            Z = df.select_dtypes(include="number")

    sns.heatmap(Z, cmap="vlag", center=0, linewidths=0, ax=ax,
                cbar_kws={"shrink": 0.6, "label": "Z-score"})
    ax.set_xlabel("Samples")
    ax.set_ylabel("Features")
    ax.set_yticks([])
    apply_chart_polish(ax, "heatmap_cluster")
    return ax


def gen_heatmap_pure(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pure heatmap without clustering: ordered matrix with explicit annotation."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    numeric_cols = df.select_dtypes(include="number").columns
    Z = df[numeric_cols] if len(numeric_cols) >= 3 else df.select_dtypes(include="number")

    sns.heatmap(Z, cmap="vlag", center=0, linewidths=0, ax=ax,
                cbar_kws={"shrink": 0.6, "label": "Value"})
    ax.set_xlabel("Columns")
    ax.set_ylabel("Rows")
    if standalone:
        apply_chart_polish(ax, "heatmap_pure")
    return ax


def gen_pca(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """PCA scatter with 95% confidence ellipses per group."""
    standalone = ax is None
    from matplotlib.patches import Ellipse

    roles = dataProfile.get("semanticRoles", {})
    pc1_col = roles.get("x") or roles.get("umap_1")
    pc2_col = roles.get("y") or roles.get("umap_2")
    group_col = roles.get("group") or roles.get("cell_type")

    if pc1_col is None or pc2_col is None:
        raise ValueError("pca requires 'x'/'umap_1' and 'y'/'umap_2' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])
    markers = ["o", "s", "^", "D", "v", "P", "*", "X"]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            marker = markers[i % len(markers)]
            ax.scatter(grp[pc1_col], grp[pc2_col], c=col, marker=marker, s=25,
                       alpha=0.8, linewidth=0.3, edgecolors="white", label=str(name))
            cx, cy = grp[pc1_col].mean(), grp[pc2_col].mean()
            ax.add_patch(Ellipse((cx, cy), grp[pc1_col].std() * 2 * 1.96,
                                 grp[pc2_col].std() * 2 * 1.96,
                                 fill=False, color=col, linewidth=0.6,
                                 linestyle="--", alpha=0.5))
        ax.legend(frameon=False, fontsize=5)
    else:
        ax.scatter(df[pc1_col], df[pc2_col], c="#000000", s=25, alpha=0.8,
                   linewidth=0.3, edgecolors="white")

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    if standalone:
        apply_chart_polish(ax, "pca")
    return ax


def gen_roc(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """ROC curve with AUC annotation and confidence band."""
    standalone = ax is None
    from sklearn.metrics import roc_curve, auc

    roles = dataProfile.get("semanticRoles", {})
    score_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label") or roles.get("event")

    if score_col is None or label_col is None:
        raise ValueError("roc requires 'score' and 'label' in semanticRoles")

    y_true = df[label_col].values
    y_scores = df[score_col].values

    fpr, tpr, _ = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    ax.plot(fpr, tpr, color="#0072B2", lw=1, label=f"AUC = {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], color="#999999", lw=0.5, ls="--")
    ax.fill_between(fpr, 0, tpr, alpha=0.1, color="#0072B2")

    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "roc")
    return ax


def gen_calibration(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Calibration plot: predicted probability vs observed fraction."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    pred_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label") or roles.get("event")

    if pred_col is None or label_col is None:
        raise ValueError("calibration requires 'score' and 'label' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    # Bin predictions and compute observed fraction
    bins = np.linspace(0, 1, 11)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    observed = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (df[pred_col] >= lo) & (df[pred_col] < hi)
        if mask.sum() > 0:
            observed.append(df.loc[mask, label_col].mean())
        else:
            observed.append(np.nan)

    ax.plot(bin_centers, observed, "o-", color="#0072B2", lw=1, markersize=4)
    ax.plot([0, 1], [0, 1], "--", color="#999999", lw=0.5)

    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed fraction")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    if standalone:
        apply_chart_polish(ax, "calibration")
    return ax


def gen_waterfall(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Waterfall plot: ordered patient/response values."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    value_col = roles.get("value") or roles.get("response")
    label_col = roles.get("label") or roles.get("subject_id")

    if value_col is None:
        raise ValueError("waterfall requires 'value' in semanticRoles")

    values = np.sort(df[value_col].values)[::-1]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    colors = ["#0072B2" if v <= -30 else "#999999" if v <= 20 else "#D55E00" for v in values]
    ax.bar(range(len(values)), values, color=colors, width=0.7,
           linewidth=0.3, edgecolor="white")
    ax.axhline(0, color="black", lw=0.5)

    ax.set_xlabel("Patient")
    ax.set_ylabel("Response (%)")
    if standalone:
        apply_chart_polish(ax, "waterfall")
    return ax


def gen_correlation(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Correlation heatmap: lower triangle with annotations."""
    standalone = ax is None
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("correlation requires at least 2 numeric columns")

    corr = df[numeric_cols].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    cbar_kw = {"shrink": 0.6} if standalone else {"shrink": 0.4, "aspect": 20}
    sns.heatmap(corr, mask=mask, ax=ax, cmap="vlag", center=0,
                annot=True, fmt=".2f", linewidths=0.5,
                cbar_kws=cbar_kw, annot_kws={"size": 5},
                square=True)
    if standalone:
        apply_chart_polish(ax, "correlation")
    return ax


def gen_scatter_regression(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Scatter with regression line and r annotation."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("dose")
    y_col = roles.get("y") or roles.get("value")

    if x_col is None or y_col is None:
        raise ValueError("scatter_regression requires 'x' and 'y' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    ax.scatter(df[x_col], df[y_col], c="#000000", s=15, alpha=0.7,
               linewidth=0.3, edgecolors="white")

    z = np.polyfit(df[x_col], df[y_col], 1)
    p_line = np.poly1d(z)
    xs = np.linspace(df[x_col].min(), df[x_col].max(), 100)
    ax.plot(xs, p_line(xs), color="#D55E00", lw=1, ls="--")

    r = np.corrcoef(df[x_col], df[y_col])[0, 1]
    ax.text(0.05, 0.95, f"r = {r:.3f}", transform=ax.transAxes, fontsize=6, va="top")

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    if standalone:
        apply_chart_polish(ax, "scatter_regression")
    return ax


def gen_beeswarm(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Beeswarm plot: exact point placement for low/moderate n."""
    standalone = ax is None
    group_col, value_col, _ = _resolve_roles(dataProfile)
    if group_col is None or value_col is None:
        raise ValueError("beeswarm requires 'group' and 'value' in semanticRoles")

    categories = df[group_col].unique()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    sns.swarmplot(data=df, x=group_col, y=value_col, hue=group_col,
                  palette=color_map, size=3, linewidth=0.3, edgecolor="white",
                  legend=False, ax=ax)
    if ax.get_legend():
        ax.get_legend().remove()

    ax.set_xlabel("")
    ax.set_ylabel(value_col)
    if standalone:
        apply_chart_polish(ax, "beeswarm")
    return ax



def gen_dotplot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Dot matrix plot where dot size and color encode values.

    Rows are features, columns are groups.  Dot size is proportional to the
    value magnitude and dot color encodes direction or magnitude via a diverging
    palette.  Common in genomics enrichment analyses.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")

    if group_col is None or value_col is None:
        raise ValueError("dotplot requires 'group' and 'value' in semanticRoles")

    if feature_col and feature_col in df.columns:
        pivot = df.pivot_table(index=feature_col, columns=group_col, values=value_col, aggfunc="mean")
    else:
        pivot = df.pivot_table(index=df.columns[0], columns=group_col, values=value_col, aggfunc="mean")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    rows, cols = pivot.shape
    max_abs = pivot.abs().max().max() or 1.0
    for i, feat in enumerate(pivot.index):
        for j, grp in enumerate(pivot.columns):
            val = pivot.iloc[i, j]
            if pd.notna(val):
                size = (abs(val) / max_abs) * 80 + 4
                div_cmap = palette.get("diverging", "RdBu_r")
                if isinstance(div_cmap, list):
                    from matplotlib.colors import LinearSegmentedColormap
                    div_cmap = LinearSegmentedColormap.from_list("div_pal", div_cmap)
                ax.scatter(j, i, s=size, c=[val], cmap=div_cmap,
                           vmin=pivot.min().min(), vmax=pivot.max().max(),
                           edgecolor="white", linewidth=0.3, zorder=2)

    ax.set_xticks(range(cols))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=6)
    ax.set_yticks(range(rows))
    ax.set_yticklabels(pivot.index, fontsize=6)
    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(rows - 0.5, -0.5)
    ax.set_xlabel(group_col)
    ax.set_ylabel(feature_col or "Feature")
    sm = plt.cm.ScalarMappable(cmap=div_cmap,
                                norm=plt.Normalize(pivot.min().min(), pivot.max().max()))
    sm.set_array([])
    ax.figure.colorbar(sm, ax=ax, shrink=0.6, label=value_col)
    if standalone:
        apply_chart_polish(ax, "dotplot")
    return ax


def gen_adjacency_matrix(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Adjacency matrix visualization for network data.

    A symmetric binary or weighted adjacency matrix rendered as a heatmap.
    Rows and columns represent nodes; cell fill indicates edge presence or
    weight.  Diagonal is masked for clarity.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    source_col = roles.get("x") or roles.get("group")
    target_col = roles.get("y") or roles.get("feature_id")
    weight_col = roles.get("value")

    if source_col and target_col and weight_col:
        adj = df.pivot_table(index=source_col, columns=target_col,
                             values=weight_col, aggfunc="mean", fill_value=0)
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        adj = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    # Make symmetric if nearly symmetric
    if adj.shape[0] == adj.shape[1]:
        adj = (adj + adj.T) / 2

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    mask = np.eye(adj.shape[0], dtype=bool)
    sns.heatmap(adj, mask=mask, cmap="Blues", linewidths=0.3, linecolor="white",
                square=True, cbar_kws={"shrink": 0.6, "label": "Weight"}, ax=ax)
    ax.set_xlabel("Node")
    ax.set_ylabel("Node")
    if standalone:
        apply_chart_polish(ax, "adjacency_matrix")
    return ax


def gen_heatmap_annotated(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Heatmap with cell value annotations displayed inside each cell.

    Suitable for small-to-medium matrices where exact numeric values are
    important.  Font size auto-adjusts to cell count.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")

    if group_col and value_col and feature_col:
        pivot = df.pivot_table(index=feature_col, columns=group_col,
                               values=value_col, aggfunc="mean")
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        pivot = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    n_cells = pivot.shape[0] * pivot.shape[1]
    annot_size = max(4, min(8, int(120 / max(n_cells, 1))))

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(pivot, annot=True, fmt=".2f", annot_kws={"size": annot_size},
                cmap="YlOrRd", linewidths=0.3, linecolor="white",
                cbar_kws={"shrink": 0.6, "label": value_col or "Value"}, ax=ax)
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel(feature_col or "Row")
    if standalone:
        apply_chart_polish(ax, "heatmap_annotated")
    return ax


def gen_heatmap_triangular(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Lower or upper triangular heatmap.

    Masks the upper triangle to display only the lower half (or vice versa).
    Common for correlation or distance matrices to avoid redundancy.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")

    if group_col and value_col and feature_col:
        pivot = df.pivot_table(index=feature_col, columns=group_col,
                               values=value_col, aggfunc="mean")
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        pivot = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    # Ensure square for triangular masking
    if pivot.shape[0] == pivot.shape[1]:
        mask = np.triu(np.ones_like(pivot, dtype=bool), k=0)
    else:
        mask = np.zeros_like(pivot, dtype=bool)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(pivot, mask=mask, cmap="coolwarm", center=0,
                linewidths=0.3, linecolor="white", square=True,
                cbar_kws={"shrink": 0.6, "label": value_col or "Value"}, ax=ax)
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel(feature_col or "Row")
    if standalone:
        apply_chart_polish(ax, "heatmap_triangular")
    return ax


def gen_heatmap_mirrored(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mirrored symmetric heatmap.

    Displays the full matrix on one triangle and a transposed or secondary
    metric on the other triangle.  Useful for showing two related measures
    (e.g., correlation coefficient vs p-value) in a single figure.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")

    if group_col and value_col and feature_col:
        pivot = df.pivot_table(index=feature_col, columns=group_col,
                               values=value_col, aggfunc="mean")
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        pivot = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    if pivot.shape[0] != pivot.shape[1]:
        pivot = pivot.iloc[:min(pivot.shape), :min(pivot.shape)]
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                               constrained_layout=True)
        sns.heatmap(pivot, cmap="RdBu_r", center=0, linewidths=0.3,
                    cbar_kws={"shrink": 0.6, "label": value_col or "Value"}, ax=ax)
    if standalone:
        apply_chart_polish(ax, "heatmap_mirrored")
        return ax

    n = pivot.shape[0]
    mask_lower = np.tril(np.ones((n, n), dtype=bool), k=-1)
    mask_upper = np.triu(np.ones((n, n), dtype=bool), k=1)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(pivot, mask=mask_lower, cmap="RdBu_r", center=0,
                linewidths=0.3, linecolor="white", square=True,
                cbar_kws={"shrink": 0.6, "label": "Lower"}, ax=ax)
    sns.heatmap(pivot.T, mask=mask_upper, cmap="PiYG", center=0,
                linewidths=0.3, linecolor="white", square=True,
                cbar_kws={"shrink": 0.6, "label": "Upper"}, ax=ax)
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel(feature_col or "Row")
    if standalone:
        apply_chart_polish(ax, "heatmap_mirrored")
    return ax


def gen_cooccurrence_matrix(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Co-occurrence matrix with optional hierarchical clustering.

    Computes pairwise co-occurrence counts or similarity between categories,
    then displays as a clustered heatmap.  Rows and columns are reordered by
    dendrogram to reveal group structure.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")

    if group_col and feature_col:
        ct = pd.crosstab(df[feature_col], df[group_col])
    elif group_col and value_col:
        pivot = df.pivot_table(index=df.columns[0], columns=group_col,
                               values=value_col, aggfunc="count", fill_value=0)
        ct = pivot
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        ct = df[numeric_cols].corr() if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    # Attempt hierarchical clustering to reorder
    try:
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import pdist
        if ct.shape[0] > 2 and ct.shape[1] > 2:
            row_link = linkage(pdist(ct.values, metric="euclidean"), method="average")
            col_link = linkage(pdist(ct.values.T, metric="euclidean"), method="average")
            row_order = leaves_list(row_link)
            col_order = leaves_list(col_link)
            ct = ct.iloc[row_order, col_order]
    except Exception:
        pass

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(ct, cmap="YlGnBu", linewidths=0.3, linecolor="white",
                cbar_kws={"shrink": 0.6, "label": "Co-occurrence"}, ax=ax)
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel(feature_col or "Row")
    if standalone:
        apply_chart_polish(ax, "cooccurrence_matrix")
    return ax



# ──────────────────────────────────────────────────────────────
# Time Series Chart Generators
# ──────────────────────────────────────────────────────────────

def gen_sparkline(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Sparkline: minimal time series line chart with no axes labels.

    A compact, annotation-free line chart for embedding in tables or dashboards.
    Expects semanticRoles: x (time), value (numeric). Optional group for
    multiple sparklines.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, x_col = _resolve_roles(dataProfile)
    if x_col is None or value_col is None:
        raise ValueError("sparkline requires 'x' and 'value' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 30 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            grp_sorted = grp.sort_values(x_col)
            ax.plot(grp_sorted[x_col], grp_sorted[value_col],
                    color=col, lw=0.8, label=str(name))
        ax.legend(frameon=False, fontsize=5, loc="upper left")
    else:
        df_sorted = df.sort_values(x_col)
        ax.plot(df_sorted[x_col], df_sorted[value_col],
                color=palette.get("categorical", ["#000000"])[0], lw=0.8)

    ax.axis("off")
    ax.margins(x=0.02, y=0.1)
    if standalone:
        apply_chart_polish(ax, "sparkline")
    return ax


def gen_area(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Area chart: filled area under a line for time series volume.

    Uses fill_between to shade the region between the curve and zero.
    Expects semanticRoles: x (time), value (numeric). Optional group for
    overlapping semi-transparent areas.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, x_col = _resolve_roles(dataProfile)
    if x_col is None or value_col is None:
        raise ValueError("area requires 'x' and 'value' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            grp_sorted = grp.sort_values(x_col)
            ax.fill_between(grp_sorted[x_col], grp_sorted[value_col],
                            alpha=0.35, color=col, label=str(name))
            ax.plot(grp_sorted[x_col], grp_sorted[value_col],
                    color=col, lw=0.8)
        ax.legend(frameon=False, fontsize=5)
    else:
        df_sorted = df.sort_values(x_col)
        col = palette.get("categorical", ["#000000"])[0]
        ax.fill_between(df_sorted[x_col], df_sorted[value_col],
                        alpha=0.35, color=col)
        ax.plot(df_sorted[x_col], df_sorted[value_col], color=col, lw=0.8)

    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    if standalone:
        apply_chart_polish(ax, "area")
    return ax


def gen_area_stacked(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stacked area chart: compositional time series with layers summing to total.

    Each group is a layer stacked on top of the previous.  Useful for showing
    part-to-whole relationships over time.  Expects semanticRoles: x (time),
    value (numeric), group (categorical for layers).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, x_col = _resolve_roles(dataProfile)
    if x_col is None or value_col is None:
        raise ValueError("area_stacked requires 'x' and 'value' in semanticRoles")
    if group_col is None:
        raise ValueError("area_stacked requires 'group' in semanticRoles")

    categories = df[group_col].unique().tolist()
    color_map = _extract_colors(palette, categories)
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    pivot = df.pivot_table(index=x_col, columns=group_col,
                           values=value_col, aggfunc="mean").fillna(0)
    pivot = pivot.sort_index()

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    colors = [color_map.get(c, fallback_colors[i % len(fallback_colors)])
              for i, c in enumerate(pivot.columns)]
    stacked_data = [pivot[c].values for c in pivot.columns]
    ax.stackplot(pivot.index, *stacked_data,
                 labels=[str(c) for c in pivot.columns], colors=colors, alpha=0.8)

    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    stacked_totals = np.sum(stacked_data, axis=0)
    ax.set_ylim(0, float(np.max(stacked_totals)) * 1.05)
    ax.legend(frameon=False, fontsize=5, loc="upper left")
    if standalone:
        apply_chart_polish(ax, "area_stacked")
    return ax


def gen_streamgraph(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Streamgraph: centered stacked area for compositional time series.

    A baseline-centered stacked area chart that emphasizes changes in
    composition rather than absolute totals.  Uses matplotlib stackplot with
    baseline='wiggle'.  Expects semanticRoles: x (time), value (numeric),
    group (categorical for layers).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, value_col, x_col = _resolve_roles(dataProfile)
    if x_col is None or value_col is None:
        raise ValueError("streamgraph requires 'x' and 'value' in semanticRoles")
    if group_col is None:
        raise ValueError("streamgraph requires 'group' in semanticRoles")

    categories = df[group_col].unique().tolist()
    color_map = _extract_colors(palette, categories)
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    pivot = df.pivot_table(index=x_col, columns=group_col,
                           values=value_col, aggfunc="mean").fillna(0)
    pivot = pivot.sort_index()

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    colors = [color_map.get(c, fallback_colors[i % len(fallback_colors)])
              for i, c in enumerate(pivot.columns)]
    ax.stackplot(pivot.index, *[pivot[c] for c in pivot.columns],
                 labels=[str(c) for c in pivot.columns], colors=colors,
                 alpha=0.8, baseline="wiggle")

    ax.set_xlabel(x_col)
    ax.yaxis.set_visible(False)
    ax.legend(frameon=False, fontsize=5, loc="upper left")
    if standalone:
        apply_chart_polish(ax, "streamgraph")
    return ax


def gen_gantt(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Gantt chart: horizontal bars for project timelines or task schedules.

    Each row is a task with a start and duration (or start and end).
    Expects semanticRoles: label (task name), start, and either end or value
    (duration). Optional group for color-coded categories.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("id") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end")
    duration_col = roles.get("value") or roles.get("duration")
    group_col = roles.get("group") if roles.get("group") != label_col else roles.get("category")

    if label_col is None or start_col is None:
        raise ValueError("gantt requires 'label' and 'start' in semanticRoles")
    if end_col is None and duration_col is None:
        raise ValueError("gantt requires 'end' or 'value' (duration) in semanticRoles")

    n = len(df)
    fig_height = max(60, 10 * n + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    categories = df[group_col].unique().tolist() if group_col and group_col in df.columns else [None]
    color_map = _extract_colors(palette, [c for c in categories if c is not None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    for i, (_, row) in enumerate(df.iterrows()):
        start = row[start_col]
        width = (row[end_col] - start) if end_col and end_col in df.columns else row[duration_col]
        grp = row[group_col] if group_col and group_col in df.columns else None
        color = color_map.get(grp, fallback_colors[0]) if grp else fallback_colors[0]
        ax.barh(i, width, left=start, height=0.6, color=color,
                edgecolor="white", linewidth=0.4)

    ax.set_yticks(range(n))
    ax.set_yticklabels(df[label_col].astype(str).tolist(), fontsize=5)
    ax.set_xlabel("Time")
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if standalone:
        apply_chart_polish(ax, "gantt")
    return ax


def gen_timeline_annotation(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Timeline with annotated events: vertical markers with labels along a time axis.

    Useful for displaying discrete events, milestones, or annotations at
    specific time points.  Expects semanticRoles: x (time position), label
    (event description). Optional value for y-offset staggering, group for
    color coding.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("start") or roles.get("time")
    label_col = roles.get("label") or roles.get("id")
    group_col = roles.get("group")
    value_col = roles.get("value")

    if x_col is None or label_col is None:
        raise ValueError("timeline_annotation requires 'x' and 'label' in semanticRoles")

    categories = df[group_col].unique().tolist() if group_col and group_col in df.columns else [None]
    color_map = _extract_colors(palette, [c for c in categories if c is not None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 50 * (1 / 25.4)),
                           constrained_layout=True)

    # Draw baseline
    ax.axhline(y=0, color="#999999", lw=0.6, zorder=1)

    for i, (_, row) in enumerate(df.iterrows()):
        x_pos = row[x_col]
        grp = row[group_col] if group_col and group_col in df.columns else None
        color = color_map.get(grp, fallback_colors[i % len(fallback_colors)]) if grp else fallback_colors[i % len(fallback_colors)]

        # Alternate labels above/below to reduce overlap
        y_offset = 0.5 if i % 2 == 0 else -0.5
        if value_col and pd.notna(row.get(value_col)):
            y_offset = row[value_col]

        ax.scatter(x_pos, 0, color=color, s=25, zorder=3, edgecolor="white", lw=0.3)
        ax.vlines(x_pos, 0, y_offset, color=color, lw=0.5, zorder=2)
        ax.text(x_pos, y_offset, str(row[label_col]), fontsize=4.5,
                ha="center", va="bottom" if y_offset > 0 else "top", color=color)

    ax.set_xlabel(x_col)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.margins(x=0.05)
    if standalone:
        apply_chart_polish(ax, "timeline_annotation")
    return ax



### Step 3.4h: Clinical & Composition Chart Generators

The following 8 generators cover clinical trial, sensitivity analysis, and compositional chart types.

```python
# ──────────────────────────────────────────────────────────────
# Clinical & Composition Chart Generators
# Signature: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
# ──────────────────────────────────────────────────────────────


def gen_caterpillar_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Caterpillar plot: ranked effects with confidence intervals, sorted by effect size."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    estimate_col = roles.get("estimate") or roles.get("value")
    ci_low_col = roles.get("ci_low")
    ci_high_col = roles.get("ci_high")

    if label_col is None or estimate_col is None:
        raise ValueError("caterpillar_plot requires 'label' and 'estimate' in semanticRoles")

    sort_col = roles.get("sort") or estimate_col
    df_sorted = df.sort_values(sort_col).reset_index(drop=True)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df_sorted) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = np.arange(len(df_sorted))
    estimates = df_sorted[estimate_col].values

    if ci_low_col and ci_high_col:
        ci_low = df_sorted[ci_low_col].values
        ci_high = df_sorted[ci_high_col].values
    else:
        se = df_sorted[roles.get("se", estimate_col)].values if roles.get("se") else estimates * 0.1
        ci_low = estimates - 1.96 * se
        ci_high = estimates + 1.96 * se

    ax.errorbar(estimates, y_pos,
                xerr=[estimates - ci_low, ci_high - estimates],
                fmt="o", color="#0072B2", markersize=4, capsize=3,
                elinewidth=0.6, capthick=0.6, linewidth=0.6)

    ax.axvline(0, color="#999999", lw=0.5, ls="--", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[label_col].values, fontsize=5)
    ax.set_xlabel("Effect size (95% CI)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "caterpillar_plot")
    return ax


def gen_tornado_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Tornado diagram for sensitivity analysis: horizontal bars showing variable impact."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    low_col = roles.get("low") or roles.get("ci_low")
    high_col = roles.get("high") or roles.get("ci_high")
    base_col = roles.get("base") or roles.get("value")

    if label_col is None or low_col is None or high_col is None:
        raise ValueError("tornado_chart requires 'label', 'low', and 'high' in semanticRoles")

    # Sort by bar width (largest impact first)
    df_sorted = df.copy()
    df_sorted["_width"] = (df_sorted[high_col] - df_sorted[low_col]).abs()
    df_sorted = df_sorted.sort_values("_width", ascending=True).reset_index(drop=True)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df_sorted) * 10) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = np.arange(len(df_sorted))
    base = df_sorted[base_col].values if base_col else np.zeros(len(df_sorted))

    for i in range(len(df_sorted)):
        low = df_sorted[low_col].iloc[i]
        high = df_sorted[high_col].iloc[i]
        ax.barh(y_pos[i], high - base[i], left=base[i], height=0.6,
                color="#0072B2", alpha=0.7, edgecolor="none")
        ax.barh(y_pos[i], low - base[i], left=base[i], height=0.6,
                color="#D55E00", alpha=0.7, edgecolor="none")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[label_col].values, fontsize=5)
    ax.set_xlabel("Impact on outcome")
    if standalone:
        apply_chart_polish(ax, "tornado_chart")
    return ax


def gen_nomogram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified nomogram: linear scale with point markers for prediction models."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    score_col = roles.get("score") or roles.get("value")

    if label_col is None or score_col is None:
        raise ValueError("nomogram requires 'label' and 'score' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(40, len(df) * 14) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = np.arange(len(df))
    labels = df[label_col].values
    scores = df[score_col].values

    for i in range(len(df)):
        # Draw horizontal scale line with tick marks
        ax.plot([0, 100], [y_pos[i], y_pos[i]], color="#CCCCCC", lw=1)
        for tick in np.linspace(0, 100, 6):
            ax.plot([tick, tick], [y_pos[i] - 0.2, y_pos[i] + 0.2], color="#999999", lw=0.5)
        # Mark the score value on the scale
        if np.isscalar(scores[i]) and 0 <= scores[i] <= 100:
            ax.plot(scores[i], y_pos[i], "o", color="#D55E00", markersize=6, zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xlim(-5, 105)
    ax.set_xlabel("Points")
    ax.set_ylim(-0.5, len(df) - 0.5)
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "nomogram")
    return ax


def gen_decision_curve(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Decision curve analysis: net benefit vs threshold probability."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    threshold_col = roles.get("threshold") or roles.get("x")
    benefit_col = roles.get("benefit") or roles.get("y") or roles.get("value")
    model_col = roles.get("group") or roles.get("model")

    if threshold_col is None or benefit_col is None:
        raise ValueError("decision_curve requires 'threshold' and 'benefit' in semanticRoles")

    color_map = _extract_colors(palette, df[model_col].unique() if model_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if model_col:
        for i, (name, grp) in enumerate(df.groupby(model_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            grp_sorted = grp.sort_values(threshold_col)
            ax.plot(grp_sorted[threshold_col], grp_sorted[benefit_col],
                    color=col, lw=1, label=str(name))
        ax.legend(frameon=False, fontsize=5)
    else:
        df_sorted = df.sort_values(threshold_col)
        ax.plot(df_sorted[threshold_col], df_sorted[benefit_col],
                color="#0072B2", lw=1)

    # Reference lines: "treat all" and "treat none"
    thresholds = np.sort(df[threshold_col].unique())
    prevalence = df[benefit_col].mean()
    treat_all = prevalence - (1 - prevalence) * thresholds / (1 - thresholds + 1e-10)
    ax.plot(thresholds, treat_all, color="#999999", lw=0.5, ls="--", label="Treat all")
    ax.axhline(0, color="#999999", lw=0.5, ls=":", label="Treat none")

    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_ylim(-0.05, None)
    if standalone:
        apply_chart_polish(ax, "decision_curve")
    return ax


def gen_waffle_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Waffle chart: 10x10 grid of squares showing proportions."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("label")
    value_col = roles.get("value") or roles.get("count")

    if group_col is None or value_col is None:
        raise ValueError("waffle_chart requires 'group' and 'value' in semanticRoles")

    categories = df[group_col].values
    values = df[value_col].values.astype(float)
    total = values.sum()
    if total == 0:
        raise ValueError("waffle_chart: values must sum to a positive number")

    proportions = values / total
    counts = np.round(proportions * 100).astype(int)
    # Adjust rounding to exactly 100
    diff = 100 - counts.sum()
    counts[np.argmax(proportions)] += diff

    color_map = _extract_colors(palette, categories)
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                                    "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           constrained_layout=True)

    idx = 0
    for row in range(10):
        for col_idx in range(10):
            if idx >= 100:
                break
            # Determine which category this cell belongs to
            cumsum = 0
            cat = categories[0]
            for k, cnt in enumerate(counts):
                cumsum += cnt
                if idx < cumsum:
                    cat = categories[k]
                    break
            color = color_map.get(cat, fallback_colors[k % len(fallback_colors)])
            ax.add_patch(plt.Rectangle((col_idx, 9 - row), 1, 1, facecolor=color,
                                        edgecolor="white", linewidth=0.5))
            idx += 1

    # Legend
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=color_map.get(c, fallback_colors[i % len(fallback_colors)]))
               for i, c in enumerate(categories)]
    ax.legend(handles, [str(c) for c in categories], loc="upper left",
              bbox_to_anchor=(1.02, 1), frameon=False, fontsize=5)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "waffle_chart")
    return ax


def gen_marimekko(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Marimekko chart: variable-width stacked bar for market/composition data."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("group")
    stack_col = roles.get("stack") or roles.get("subgroup")
    value_col = roles.get("value") or roles.get("count")

    if x_col is None or stack_col is None or value_col is None:
        raise ValueError("marimekko requires 'x', 'stack', and 'value' in semanticRoles")

    pivot = df.pivot_table(index=x_col, columns=stack_col, values=value_col, aggfunc="sum", fill_value=0)
    categories = pivot.columns.tolist()
    color_map = _extract_colors(palette, categories)
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                                    "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    totals = pivot.sum(axis=1)
    widths = totals / totals.sum()
    x_left = 0

    for idx, (x_val, row) in enumerate(pivot.iterrows()):
        col_total = totals.iloc[idx]
        if col_total == 0:
            x_left += widths.iloc[idx]
            continue
        y_bottom = 0
        for k, cat in enumerate(categories):
            val = row[cat]
            height = val / col_total
            color = color_map.get(cat, fallback_colors[k % len(fallback_colors)])
            ax.bar(x_left + widths.iloc[idx] / 2, height, width=widths.iloc[idx],
                   bottom=y_bottom, color=color, edgecolor="white", linewidth=0.3)
            y_bottom += height
        x_left += widths.iloc[idx]

    ax.set_xticks(np.cumsum(widths) - widths / 2)
    ax.set_xticklabels(pivot.index, fontsize=5, rotation=45, ha="right")
    ax.set_ylabel("Proportion")
    ax.set_ylim(0, 1)

    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=color_map.get(c, fallback_colors[k % len(fallback_colors)]))
               for k, c in enumerate(categories)]
    ax.legend(handles, [str(c) for c in categories], loc="upper left",
              bbox_to_anchor=(1.02, 1), frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "marimekko")
    return ax


def gen_nested_donut(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Nested donut chart for hierarchical proportions (two concentric rings)."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    outer_col = roles.get("group") or roles.get("outer")
    inner_col = roles.get("subgroup") or roles.get("inner")
    value_col = roles.get("value") or roles.get("count")

    if outer_col is None or value_col is None:
        raise ValueError("nested_donut requires 'group' and 'value' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           constrained_layout=True)

    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                                    "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])

    # Outer ring: grouped by outer_col
    outer_grouped = df.groupby(outer_col)[value_col].sum()
    outer_labels = outer_grouped.index.tolist()
    outer_values = outer_grouped.values
    outer_color_map = _extract_colors(palette, outer_labels)

    outer_colors = [outer_color_map.get(l, fallback_colors[i % len(fallback_colors)])
                    for i, l in enumerate(outer_labels)]

    ax.pie(outer_values, radius=1.0, colors=outer_colors, labels=None,
           wedgeprops=dict(width=0.35, edgecolor="white", linewidth=0.5),
           startangle=90)

    # Inner ring: grouped by inner_col (if present)
    if inner_col and inner_col in df.columns:
        inner_grouped = df.groupby([outer_col, inner_col])[value_col].sum()
        inner_values = inner_grouped.values
        # Color by parent outer category
        parent_colors = []
        for o, s in inner_grouped.index:
            idx = outer_labels.index(o) if o in outer_labels else 0
            parent_colors.append(outer_colors[idx])
        ax.pie(inner_values, radius=0.65, colors=parent_colors, labels=None,
               wedgeprops=dict(width=0.3, edgecolor="white", linewidth=0.5),
               startangle=90)

    # Legend for outer ring
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=c) for c in outer_colors]
    ax.legend(handles, [str(l) for l in outer_labels], loc="upper left",
              bbox_to_anchor=(1.02, 1), frameon=False, fontsize=5)
    ax.set_aspect("equal")
    if standalone:
        apply_chart_polish(ax, "nested_donut")
    return ax


def gen_stacked_area_comp(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stacked area chart for compositional time series (e.g., microbiome, cell fractions)."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("time")
    stack_col = roles.get("stack") or roles.get("group")
    value_col = roles.get("value") or roles.get("proportion")

    if x_col is None or stack_col is None or value_col is None:
        raise ValueError("stacked_area_comp requires 'x', 'stack', and 'value' in semanticRoles")

    pivot = df.pivot_table(index=x_col, columns=stack_col, values=value_col, aggfunc="sum", fill_value=0)
    categories = pivot.columns.tolist()
    color_map = _extract_colors(palette, categories)
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                                    "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    x_vals = pivot.index.values
    y_stack = np.zeros(len(x_vals))
    for i, cat in enumerate(categories):
        col = color_map.get(cat, fallback_colors[i % len(fallback_colors)])
        y_vals = pivot[cat].values
        ax.fill_between(x_vals, y_stack, y_stack + y_vals, color=col,
                         label=str(cat), alpha=0.85, linewidth=0)
        y_stack += y_vals

    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    ax.set_ylim(0, None)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "stacked_area_comp")
    return ax
```

```python
def gen_go_treemap(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """GO enrichment treemap: hierarchical GO terms with p-value coloring.

    Expects columns: term (GO term name), pvalue (or padj), parent (GO category:
    BP/MF/CC), and optionally enrichment (NES or fold enrichment) in semanticRoles.
    Rectangle size encodes -log10(pvalue); color encodes GO category.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    term_col = roles.get("term") or roles.get("label") or roles.get("x")
    pval_col = roles.get("pvalue") or roles.get("padj") or roles.get("value")
    parent_col = roles.get("parent") or roles.get("group")
    enrich_col = roles.get("enrichment") or roles.get("nes")

    if term_col is None or pval_col is None:
        raise ValueError("go_treemap requires 'term' and 'pvalue' in semanticRoles")

    df = df.copy()
    df["_neglogp"] = -np.log10(df[pval_col].clip(lower=1e-300))
    categories = df[parent_col].unique() if parent_col else ["GO"]
    color_map = _extract_colors(palette, categories)
    fallback = palette.get("categorical", ["#4C956C", "#1F4E79", "#F2A541"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    try:
        import squarify
        sizes = df["_neglogp"].values.tolist()
        labels = [f"{row[term_col]}\n(p={row[pval_col]:.1e})" for _, row in df.iterrows()]
        rects = squarify.squarify(squarify.normalize_sizes(sizes, 1, 1), 0, 0, 1, 1)
        for i, (r, lbl) in enumerate(zip(rects, labels)):
            cat = df[parent_col].iloc[i] if parent_col else "GO"
            color = color_map.get(cat, fallback[i % len(fallback)])
            ax.add_patch(plt.Rectangle((r["x"], r["y"]), r["dx"], r["dy"],
                                       facecolor=color, edgecolor="white", linewidth=0.5))
            if r["dx"] > 0.08 and r["dy"] > 0.04:
                fs = min(5, max(3, r["dx"] * 40))
                ax.text(r["x"] + r["dx"] / 2, r["y"] + r["dy"] / 2, lbl,
                        ha="center", va="center", fontsize=fs, clip_on=True)
    except ImportError:
        ax.scatter(range(len(df)), df["_neglogp"],
                   c=[color_map.get(df[parent_col].iloc[i] if parent_col else "GO", fallback[0]) for i in range(len(df))],
                   s=df["_neglogp"] * 20, alpha=0.7, linewidth=0.3, edgecolors="white")
        ax.set_ylabel("-log10(p-value)")

    ax.set_axis_off()
    if standalone:
        apply_chart_polish(ax, "go_treemap")
    return ax


def gen_chromosome_coverage(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Chromosome-wide coverage/depth plot: line along chromosome position.

    Expects columns: position (genomic coordinate) and coverage (read depth) in
    semanticRoles. Optionally chromosome label for multi-chrom figure.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pos_col = roles.get("position") or roles.get("x")
    cov_col = roles.get("coverage") or roles.get("depth") or roles.get("value")
    chrom_col = roles.get("chromosome") or roles.get("group")

    if pos_col is None or cov_col is None:
        raise ValueError("chromosome_coverage requires 'position' and 'coverage' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 40 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#1F4E79"])[0]

    if chrom_col and chrom_col in df.columns:
        for i, (name, grp) in enumerate(df.groupby(chrom_col)):
            c = palette.get("categorical", ["#1F4E79", "#C8553D"])[i % 2]
            ax.fill_between(grp[pos_col], grp[cov_col], alpha=0.5, color=c, linewidth=0)
            ax.plot(grp[pos_col], grp[cov_col], color=c, lw=0.4, label=str(name))
        ax.legend(frameon=False, fontsize=5, loc="upper right")
    else:
        ax.fill_between(df[pos_col], df[cov_col], alpha=0.4, color=color, linewidth=0)
        ax.plot(df[pos_col], df[cov_col], color=color, lw=0.5)

    ax.set_xlabel("Genomic position (bp)")
    ax.set_ylabel("Coverage depth")
    ax.set_xlim(df[pos_col].min(), df[pos_col].max())
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "chromosome_coverage")
    return ax


def gen_phase_diagram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Phase diagram: composition vs temperature with phase regions.

    Expects columns: composition (mole fraction, 0-1), temperature, and optionally
    phase (categorical region label) in semanticRoles. Plots a scatter with
    optional convex-hull outlines per phase region.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    comp_col = roles.get("composition") or roles.get("x")
    temp_col = roles.get("temperature") or roles.get("y")
    phase_col = roles.get("phase") or roles.get("group")

    if comp_col is None or temp_col is None:
        raise ValueError("phase_diagram requires 'composition' and 'temperature' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if phase_col and phase_col in df.columns:
        categories = df[phase_col].unique()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            sub = df[df[phase_col] == cat]
            ax.scatter(sub[comp_col], sub[temp_col], c=color_map.get(cat, "#999999"),
                       s=15, alpha=0.7, linewidth=0.3, edgecolors="white", label=str(cat))
            # Convex hull outline
            try:
                from scipy.spatial import ConvexHull
                pts = sub[[comp_col, temp_col]].dropna().values
                if len(pts) >= 3:
                    hull = ConvexHull(pts)
                    for simplex in hull.simplices:
                        ax.plot(pts[simplex, 0], pts[simplex, 1],
                                color=color_map.get(cat, "#999999"), lw=0.8, alpha=0.6)
            except Exception:
                pass
        ax.legend(frameon=False, fontsize=5, title=phase_col, title_fontsize=5)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(df[comp_col], df[temp_col], c=color, s=15, alpha=0.7,
                   linewidth=0.3, edgecolors="white")

    ax.set_xlabel("Composition (mole fraction)")
    ax.set_ylabel("Temperature")
    ax.set_xlim(0, 1)
    if standalone:
        apply_chart_polish(ax, "phase_diagram")
    return ax


def gen_nyquist_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Nyquist plot: real vs imaginary impedance (Z' vs Z'').

    Expects columns: z_real and z_imaginary (or x/y) in semanticRoles.
    Optionally frequency column for color-coded annotation.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    real_col = roles.get("z_real") or roles.get("x")
    imag_col = roles.get("z_imaginary") or roles.get("y")
    freq_col = roles.get("frequency") or roles.get("value")

    if real_col is None or imag_col is None:
        raise ValueError("nyquist_plot requires 'z_real' and 'z_imaginary' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if freq_col and freq_col in df.columns:
        scatter = ax.scatter(df[real_col], df[imag_col], c=df[freq_col],
                             cmap="viridis", s=20, alpha=0.8, linewidth=0.3, edgecolors="white",
                             zorder=3)
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
        cbar.set_label("Frequency (Hz)", fontsize=5)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(df[real_col], df[imag_col], c=color, s=20, alpha=0.8,
                   linewidth=0.3, edgecolors="white", zorder=3)

    ax.plot(df[real_col], df[imag_col], color="#999999", lw=0.4, alpha=0.5, zorder=2)
    ax.set_xlabel(r"$Z'$ (Real, $\Omega$)")
    ax.set_ylabel(r"$Z''$ (Imaginary, $\Omega$)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "nyquist_plot")
    return ax


def gen_ftir_spectrum(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """FTIR spectrum: wavenumber vs absorbance with inverted x-axis.

    Expects columns: wavenumber (cm^-1) and absorbance (or transmittance) in
    semanticRoles. X-axis is inverted (high wavenumber on left) per FTIR convention.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    wn_col = roles.get("wavenumber") or roles.get("x")
    abs_col = roles.get("absorbance") or roles.get("transmittance") or roles.get("value")

    if wn_col is None or abs_col is None:
        raise ValueError("ftir_spectrum requires 'wavenumber' and 'absorbance' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#C8553D"])[0]
    ax.plot(df[wn_col], df[abs_col], color=color, lw=0.8, solid_capstyle="round")
    ax.fill_between(df[wn_col], df[abs_col], alpha=0.1, color=color)

    ax.set_xlabel(r"Wavenumber (cm$^{-1}$)")
    ax.set_ylabel("Absorbance")
    ax.invert_xaxis()
    if standalone:
        apply_chart_polish(ax, "ftir_spectrum")
    return ax


def gen_dsc_thermogram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """DSC thermogram: temperature vs heat flow (exo down convention).

    Expects columns: temperature and heat_flow in semanticRoles.
    Optionally marks onset/peak temperatures for thermal events.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    temp_col = roles.get("temperature") or roles.get("x")
    hf_col = roles.get("heat_flow") or roles.get("y") or roles.get("value")

    if temp_col is None or hf_col is None:
        raise ValueError("dsc_thermogram requires 'temperature' and 'heat_flow' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#D55E00"])[0]
    ax.plot(df[temp_col], df[hf_col], color=color, lw=0.8, solid_capstyle="round")
    ax.fill_between(df[temp_col], df[hf_col], alpha=0.1, color=color)

    # Annotate peak (most negative heat flow = strongest endotherm)
    peak_idx = df[hf_col].idxmin()
    peak_t = df.loc[peak_idx, temp_col]
    peak_hf = df.loc[peak_idx, hf_col]
    ax.annotate(f"Peak: {peak_t:.1f}", xy=(peak_t, peak_hf),
                xytext=(peak_t + 5, peak_hf * 0.85),
                fontsize=5, arrowprops=dict(arrowstyle="->", lw=0.4, color="black"))

    ax.set_xlabel("Temperature")
    ax.set_ylabel("Heat flow (exo down)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "dsc_thermogram")
    return ax


def gen_stem_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stem/lollipop plot for discrete signals.

    Expects columns: x (discrete positions) and y (signal amplitude) in
    semanticRoles. Optionally group for multi-series overlay.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("index")
    y_col = roles.get("y") or roles.get("value")
    group_col = roles.get("group")

    if x_col is None or y_col is None:
        raise ValueError("stem_plot requires 'x' and 'y' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].unique()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            sub = df[df[group_col] == cat]
            markerline, stemlines, baseline = ax.stem(sub[x_col], sub[y_col])
            c = color_map.get(cat, "#999999")
            plt.setp(stemlines, color=c, linewidth=0.6)
            plt.setp(markerline, color=c, markersize=4)
            plt.setp(baseline, linewidth=0)
        ax.legend(frameon=False, fontsize=5)
    else:
        color = palette.get("categorical", ["#0072B2"])[0]
        markerline, stemlines, baseline = ax.stem(df[x_col], df[y_col])
        plt.setp(stemlines, color=color, linewidth=0.6)
        plt.setp(markerline, color=color, markersize=4)
        plt.setp(baseline, linewidth=0)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    if standalone:
        apply_chart_polish(ax, "stem_plot")
    return ax


def gen_lollipop_horizontal(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Horizontal lollipop chart for ranked values.

    Expects columns: label (category names) and value (numeric) in semanticRoles.
    Sorted descending with highest values at top.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")

    if label_col is None or val_col is None:
        raise ValueError("lollipop_horizontal requires 'label' and 'value' in semanticRoles")

    df_sorted = df.sort_values(val_col, ascending=True).reset_index(drop=True)
    color = palette.get("categorical", ["#1F4E79"])[0]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4),
                                    max(50, len(df_sorted) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = range(len(df_sorted))
    ax.hlines(y_pos, 0, df_sorted[val_col], color=color, linewidth=0.8)
    ax.scatter(df_sorted[val_col], y_pos, color=color, s=25, zorder=3,
               linewidth=0.3, edgecolors="white")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df_sorted[label_col].values, fontsize=5)
    ax.set_xlabel(val_col)
    ax.set_ylim(-0.5, len(df_sorted) - 0.5)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if standalone:
        apply_chart_polish(ax, "lollipop_horizontal")
    return ax


def gen_slope_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Slope chart for before/after ranking changes.

    Expects columns: label, before (value_pre), and after (value_post) in
    semanticRoles. Each item is a line segment from its before-rank to after-rank.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    before_col = roles.get("before") or roles.get("value_pre") or roles.get("x")
    after_col = roles.get("after") or roles.get("value_post") or roles.get("y")

    if label_col is None or before_col is None or after_col is None:
        raise ValueError("slope_chart requires 'label', 'before', and 'after' in semanticRoles")

    fallback = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    for i, (_, row) in enumerate(df.iterrows()):
        c = fallback[i % len(fallback)]
        ax.plot([0, 1], [row[before_col], row[after_col]], color=c, lw=0.8, alpha=0.7)
        ax.scatter([0, 1], [row[before_col], row[after_col]], color=c, s=15, zorder=3)
        ax.text(-0.02, row[before_col], str(row[label_col]), ha="right", va="center", fontsize=4)
        ax.text(1.02, row[after_col], str(row[label_col]), ha="left", va="center", fontsize=4)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Before", "After"])
    ax.set_xlim(-0.15, 1.15)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    if standalone:
        apply_chart_polish(ax, "slope_chart")
    return ax


def gen_bump_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Bump chart for ranking changes over time.

    Expects columns: time (or x), rank (or value), and group in semanticRoles.
    Each group is a line showing its rank trajectory across time periods.
    Y-axis is inverted (rank 1 at top).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    time_col = roles.get("time") or roles.get("x")
    rank_col = roles.get("rank") or roles.get("value") or roles.get("y")
    group_col = roles.get("group") or roles.get("label")

    if time_col is None or rank_col is None or group_col is None:
        raise ValueError("bump_chart requires 'time', 'rank', and 'group' in semanticRoles")

    categories = df[group_col].unique()
    color_map = _extract_colors(palette, categories)
    fallback = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                            "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    for i, (name, grp) in enumerate(df.groupby(group_col)):
        grp_sorted = grp.sort_values(time_col)
        c = color_map.get(name, fallback[i % len(fallback)])
        ax.plot(grp_sorted[time_col], grp_sorted[rank_col], color=c, lw=1.2,
                marker="o", markersize=4, markeredgecolor="white", markeredgewidth=0.3)
        # Label at endpoints
        first_row = grp_sorted.iloc[0]
        last_row = grp_sorted.iloc[-1]
        ax.text(first_row[time_col] - 0.1, first_row[rank_col], str(name),
                ha="right", va="center", fontsize=4, color=c)
        ax.text(last_row[time_col] + 0.1, last_row[rank_col], str(name),
                ha="left", va="center", fontsize=4, color=c)

    ax.invert_yaxis()
    ax.set_xlabel(time_col)
    ax.set_ylabel("Rank")
    if standalone:
        apply_chart_polish(ax, "bump_chart")
    return ax

```



### Relationship / Psychology / Social chart generators

```python
def gen_chord_diagram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Chord diagram showing flows between categories using matplotlib arcs.

    Expects a square matrix or long-format flow table.  Semantic roles:
      - feature_id: source category column
      - group: target category column
      - value: flow magnitude column
    Falls back to the first NxN numeric block if roles are absent.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    src_col = roles.get("feature_id")
    tgt_col = roles.get("group")
    val_col = roles.get("value")

    # Build adjacency matrix
    if src_col and tgt_col and val_col:
        cats = sorted(set(df[src_col]) | set(df[tgt_col]))
        mat = df.pivot_table(index=src_col, columns=tgt_col,
                             values=val_col, aggfunc="sum").reindex(
                                 index=cats, columns=cats).fillna(0).values
    else:
        numeric = df.select_dtypes(include="number")
        mat = numeric.values[:len(numeric.columns), :len(numeric.columns)]
        cats = list(numeric.columns[:mat.shape[0]])

    n = len(cats)
    totals = mat.sum(axis=1) + mat.sum(axis=0)
    total = totals.sum()
    if total == 0:
        total = 1

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           subplot_kw={"aspect": "equal"},
                           constrained_layout=True)

    fallback = palette.get("categorical",
                            ["#0072B2", "#E69F00", "#56B4E9", "#009E73",
                             "#F0E442", "#D55E00", "#CC79A7", "#999999"])
    colors = [fallback[i % len(fallback)] for i in range(n)]

    angle_gap = 4  # degrees between arcs
    gap_total = n * angle_gap
    sweep = 360 - gap_total

    # Compute angular spans for each node
    spans = []
    start = 0
    for i in range(n):
        extent = (totals[i] / total) * sweep
        spans.append((start, extent))
        start += extent + angle_gap

    # Draw outer arcs
    for i, (s, e) in enumerate(spans):
        wedge = matplotlib.patches.Wedge(
            (0, 0), 1.0, s, s + e, width=0.15,
            facecolor=colors[i], edgecolor="white", linewidth=0.5)
        ax.add_patch(wedge)
        mid_angle = np.radians(s + e / 2)
        ax.text(1.18 * np.cos(mid_angle), 1.18 * np.sin(mid_angle),
                cats[i], ha="center", va="center", fontsize=5,
                rotation=np.degrees(mid_angle) - 90
                if 90 < np.degrees(mid_angle) < 270
                else np.degrees(mid_angle) + 90)

    # Draw chords
    out_pos = [0.0] * n  # track outgoing offset within each arc
    for i in range(n):
        for j in range(n):
            if mat[i, j] == 0:
                continue
            frac = mat[i, j] / total
            si, ei = spans[i]
            sj, ej = spans[j]

            a1 = si + out_pos[i] * sweep / totals[i] if totals[i] else 0
            out_pos[i] += mat[i, j]

            b1 = sj + out_pos[j] * sweep / totals[j] if totals[j] else 0
            out_pos[j] += mat[j, i]

            t = np.linspace(0, 1, 50)
            # Quadratic Bezier through center
            p0 = np.array([np.cos(np.radians(a1)), np.sin(np.radians(a1))])
            p2 = np.array([np.cos(np.radians(b1)), np.sin(np.radians(b1))])
            mid = (p0 + p2) / 2 * 0.3  # pull toward center
            chord_pts = ((1 - t)[:, None] ** 2 * p0
                         + 2 * (1 - t)[:, None] * t[:, None] * mid
                         + t[:, None] ** 2 * p2)
            ax.plot(chord_pts[:, 0], chord_pts[:, 1],
                    color=colors[i], alpha=0.25, lw=0.4)

    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "chord_diagram")
    return ax


def gen_parallel_coordinates(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Parallel coordinates plot for multivariate profiles.

    Each row becomes a polyline across numeric columns.  Semantic roles:
      - group: categorical column used for colouring lines
      - value / feature_id are optional; all numeric columns are used.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, _, _ = _resolve_roles(dataProfile)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("parallel_coordinates requires at least 2 numeric columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    # Normalize each column to [0, 1]
    normed = df[numeric_cols].copy()
    for c in numeric_cols:
        rng = normed[c].max() - normed[c].min()
        normed[c] = (normed[c] - normed[c].min()) / (rng if rng != 0 else 1)

    x = np.arange(len(numeric_cols))

    if group_col and group_col in df.columns:
        categories = df[group_col].unique()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            mask = df[group_col] == cat
            for _, row in normed.loc[mask].iterrows():
                ax.plot(x, row.values, color=color_map[cat], alpha=0.35, lw=0.5)
        # Legend proxy
        for cat in categories:
            ax.plot([], [], color=color_map[cat], label=str(cat), lw=1.5)
        ax.legend(fontsize=5, frameon=False, loc="upper right")
    else:
        for _, row in normed.iterrows():
            ax.plot(x, row.values, color="#999999", alpha=0.35, lw=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(numeric_cols, rotation=30, ha="right", fontsize=5)
    ax.set_ylabel("Normalized value")
    ax.set_xlim(x[0], x[-1])
    if standalone:
        apply_chart_polish(ax, "parallel_coordinates")
    return ax


def gen_mediation_path(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mediation path diagram: X -> M -> Y with path coefficients.

    Semantic roles:
      - x: independent variable (column name or computed summary key)
      - mediator: mediating variable column
      - y: dependent variable column
    Coefficients are computed as standardized betas via OLS.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    m_col = roles.get("mediator") or roles.get("feature_id")
    y_col = roles.get("y") or roles.get("value")

    if not all([x_col, m_col, y_col]):
        raise ValueError("mediation_path requires 'x', 'mediator', and 'y' in semanticRoles")

    # Standardize for comparable coefficients
    z = (df[[x_col, m_col, y_col]] - df[[x_col, m_col, y_col]].mean()) / \
        df[[x_col, m_col, y_col]].std().replace(0, 1)

    # Path coefficients
    a = np.polyfit(z[x_col], z[m_col], 1)[0]  # X -> M
    b = np.polyfit(z[m_col], z[y_col], 1)[0]  # M -> Y
    c_prime = np.polyfit(z[x_col], z[y_col], 1)[0]  # X -> Y (direct)
    ab = a * b  # indirect effect

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    # Node positions
    nodes = {x_col: (0.1, 0.5), m_col: (0.5, 0.5), y_col: (0.9, 0.5)}
    box_w, box_h = 0.12, 0.10

    color_accent = palette.get("categorical", ["#0072B2"])[0]

    for name, (cx, cy) in nodes.items():
        rect = plt.Rectangle((cx - box_w / 2, cy - box_h / 2), box_w, box_h,
                              facecolor="white", edgecolor=color_accent,
                              linewidth=1, transform=ax.transAxes, clip_on=False)
        ax.add_patch(rect)
        ax.text(cx, cy, name, ha="center", va="center", fontsize=6,
                fontweight="bold", transform=ax.transAxes)

    # Arrows with coefficients
    arrow_kw = dict(arrowstyle="-|>", color="#333333", lw=1,
                    connectionstyle="arc3,rad=0", transform=ax.transAxes)

    def _draw_arrow(src, dst, coeff, y_off=0.08):
        sx, sy = nodes[src]
        dx, dy = nodes[dst]
        ax.annotate("", xy=(dx - box_w / 2 - 0.01, dy),
                     xytext=(sx + box_w / 2 + 0.01, sy),
                     xycoords="axes fraction", textcoords="axes fraction",
                     arrowprops=arrow_kw)
        mx = (sx + dx) / 2
        ax.text(mx, sy + y_off, f"{coeff:.3f}", ha="center", va="bottom",
                fontsize=5.5, color="#333333", transform=ax.transAxes)

    _draw_arrow(x_col, m_col, a, y_off=0.06)
    _draw_arrow(m_col, y_col, b, y_off=0.06)
    # Direct path below
    sx, sy = nodes[x_col]
    dx, dy = nodes[y_col]
    ax.annotate("", xy=(dx - box_w / 2 - 0.01, dy - 0.18),
                 xytext=(sx + box_w / 2 + 0.01, sy - 0.18),
                 xycoords="axes fraction", textcoords="axes fraction",
                 arrowprops={**arrow_kw, "linestyle": "--"})
    mx = (sx + dx) / 2
    ax.text(mx, sy - 0.18 - 0.06, f"c'={c_prime:.3f}", ha="center",
            va="top", fontsize=5, color="#666666", transform=ax.transAxes)

    ax.text(0.5, 0.02, f"Indirect effect (a*b) = {ab:.3f}",
            ha="center", fontsize=5, transform=ax.transAxes, color="#333333")

    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "mediation_path")
    return ax


def gen_interaction_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Interaction plot for factorial designs: lines connecting cell means.

    Semantic roles:
      - x: primary factor (x-axis categories)
      - group: secondary factor (separate lines)
      - value: numeric outcome variable
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")

    if not all([x_col, group_col, value_col]):
        raise ValueError("interaction_plot requires 'x', 'group', and 'value' in semanticRoles")

    cell_means = df.groupby([x_col, group_col])[value_col].mean().unstack()
    cell_sems = df.groupby([x_col, group_col])[value_col].sem().unstack()

    categories = cell_means.columns.tolist()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    x_positions = np.arange(len(cell_means.index))
    for cat in categories:
        means = cell_means[cat].values
        sems = cell_sems[cat].values
        ax.errorbar(x_positions, means, yerr=sems,
                     marker="o", markersize=4, linewidth=1,
                     color=color_map[cat], label=str(cat),
                     capsize=2, capthick=0.5, elinewidth=0.5)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(cell_means.index, fontsize=5.5)
    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    ax.legend(title=group_col, fontsize=5, title_fontsize=5.5,
              frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "interaction_plot")
    return ax


def gen_mosaic_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mosaic plot for categorical associations: area-proportional stacked bars.

    Semantic roles:
      - x: primary categorical variable (columns)
      - group: secondary categorical variable (segments within columns)
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    group_col = roles.get("group")

    if not all([x_col, group_col]):
        raise ValueError("mosaic_plot requires 'x' and 'group' in semanticRoles")

    ct = pd.crosstab(df[x_col], df[group_col])
    row_totals = ct.sum(axis=1)
    grand_total = ct.values.sum()

    categories_g = ct.columns.tolist()
    color_map = _extract_colors(palette, categories_g)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    x_pos = 0.0
    bar_gap = 0.02
    bar_width_avail = 1.0 - (len(ct.index) - 1) * bar_gap

    for i, xcat in enumerate(ct.index):
        col_width = (row_totals[xcat] / grand_total) * bar_width_avail
        y_pos = 0.0
        for gcat in categories_g:
            seg_height = ct.loc[xcat, gcat] / row_totals[xcat]
            ax.bar(x_pos + col_width / 2, seg_height, width=col_width,
                   bottom=y_pos, color=color_map[gcat],
                   edgecolor="white", linewidth=0.5)
            if seg_height > 0.05:
                ax.text(x_pos + col_width / 2, y_pos + seg_height / 2,
                        str(ct.loc[xcat, gcat]), ha="center", va="center",
                        fontsize=4.5, color="white", fontweight="bold")
            y_pos += seg_height
        x_pos += col_width + bar_gap

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_ylabel(f"P({group_col})")
    ax.set_xticks([])
    # Legend
    for gcat in categories_g:
        ax.bar(0, 0, color=color_map[gcat], label=str(gcat))
    ax.legend(title=group_col, fontsize=5, title_fontsize=5.5,
              frameon=False, loc="upper right")
    if standalone:
        apply_chart_polish(ax, "mosaic_plot")
    return ax


def gen_diverging_bar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Diverging bar chart: bars extending left/right from a center zero line.

    Semantic roles:
      - group: category labels (y-axis)
      - value: numeric scores (positive = right, negative = left)
      - feature_id: optional second category for colouring
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")
    color_col = roles.get("feature_id")

    if group_col is None or value_col is None:
        raise ValueError("diverging_bar requires 'group' and 'value' in semanticRoles")

    df_sorted = df.sort_values(value_col, ascending=True).reset_index(drop=True)
    n = len(df_sorted)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(50, n * 4) * (1 / 25.4)),
                           constrained_layout=True)

    fallback = palette.get("categorical",
                            ["#0072B2", "#E69F00", "#56B4E9", "#009E73"])

    if color_col and color_col in df.columns:
        color_cats = df_sorted[color_col].unique()
        color_map = _extract_colors(palette, color_cats)
        bar_colors = [color_map[c] for c in df_sorted[color_col]]
    else:
        bar_colors = [fallback[0] if v >= 0 else fallback[3]
                      for v in df_sorted[value_col]]

    y_pos = np.arange(n)
    ax.barh(y_pos, df_sorted[value_col].values, height=0.65,
            color=bar_colors, edgecolor="white", linewidth=0.3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[group_col].values, fontsize=5)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel(value_col)
    if standalone:
        apply_chart_polish(ax, "diverging_bar")
    return ax


def gen_heatmap_symmetric(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Symmetric heatmap with identical upper and lower triangles.

    Expects a square correlation/distance matrix or long-format data that can
    be pivoted into one.  Semantic roles:
      - feature_id: row labels column
      - group: column labels column
      - value: cell value column
    Falls back to correlation matrix of all numeric columns.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    row_col = roles.get("feature_id")
    col_col = roles.get("group")
    val_col = roles.get("value")

    if row_col and col_col and val_col:
        mat = df.pivot_table(index=row_col, columns=col_col,
                             values=val_col, aggfunc="mean").fillna(0)
    else:
        numeric = df.select_dtypes(include="number")
        if len(numeric.columns) < 2:
            raise ValueError("heatmap_symmetric requires at least 2 numeric columns or pivot roles")
        mat = numeric.corr()

    # Make symmetric if not already
    labels = mat.columns.tolist()
    M = mat.values
    symmetric = (M + M.T) / 2.0
    np.fill_diagonal(symmetric, 1.0)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(symmetric, ax=ax, cmap="vlag", center=0,
                xticklabels=labels, yticklabels=labels,
                linewidths=0.3, annot=symmetric.shape[0] <= 12,
                fmt=".2f", annot_kws={"size": 4.5},
                cbar_kws={"shrink": 0.6, "label": "Value"})
    ax.tick_params(labelsize=5)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    if standalone:
        apply_chart_polish(ax, "heatmap_symmetric")
    return ax


def gen_violin_grouped(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Grouped violin plot: multiple violins per group for factorial comparisons.

    Semantic roles:
      - x: primary grouping factor (x-axis categories)
      - group: secondary grouping factor (violins within each x category)
      - value: numeric outcome variable
    Falls back to _resolve_roles if 'x' is absent: uses 'group' as x and
    splits by a second categorical column if available.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    hue_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")

    if not all([x_col, hue_col, value_col]):
        # Fallback: try _resolve_roles and look for a second categorical
        group_col, val_col, alt_x = _resolve_roles(dataProfile)
        if group_col and val_col:
            other_cats = [c for c in df.select_dtypes(include="object").columns
                          if c != group_col]
            if other_cats:
                x_col = other_cats[0]
                hue_col = group_col
                value_col = val_col
            else:
                raise ValueError("violin_grouped requires 'x', 'group', and 'value' "
                                 "in semanticRoles")

    categories = df[hue_col].unique()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    sns.violinplot(data=df, x=x_col, y=value_col, hue=hue_col,
                   palette=color_map, width=0.7, inner="quartile",
                   linewidth=0.5, ax=ax, dodge=True)

    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    ax.legend(title=hue_col, fontsize=5, title_fontsize=5.5,
              frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "violin_grouped")
    return ax
```
**Usage notes for multi-panel composition:**

- All generators accept an `ax` keyword argument pattern. To use inside a
  multi-panel figure, pass `ax=axes["B"]` after minor refactoring to accept
  an optional `ax` parameter.
- The `palette` argument is a dict from `resolve_color_system()` containing
  `categorical`, `categoryMap`, and other keys.
- `dataProfile` must carry `semanticRoles` with at minimum `value` (numeric
  column) and optionally `group` (categorical column).
- For `violin_paired`, `semanticRoles.pair_id` identifies matched
  observations.
- For `violin_split`, `semanticRoles.x` provides an additional grouping axis
  (e.g., timepoint) while `group` provides the two halves.

## Output

- **Variable**: `styledCode`
- **TodoWrite**: Mark Phase 3 completed, Phase 4 in_progress

## Next Phase

Return to orchestrator, then continue to [Phase 4: Export, Source Data, And Reporting](04-export-report.md).
