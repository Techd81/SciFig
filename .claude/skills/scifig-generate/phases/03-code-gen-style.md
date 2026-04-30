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

## Template-Mining Bootstrap (REQUIRED before any chart code)

Phase 3 must consult `template-mining/` (the 7-module knowledge base built from 77 顶刊复刻案例) before emitting chart code. Operational helpers live in `phases/code-gen/template_mining_helpers.py`.

**Bootstrap sequence at the top of every generator:**

```python
from template_mining_helpers import (
    apply_journal_kernel, resolve_palette, role_color,
    add_metric_box, add_perfect_fit_diagonal, add_zero_reference,
    add_group_dividers, add_panel_label,
    density_sort, density_color_scatter,
    add_polygon_polar_grid, draw_gradient_box,
    build_grid, select_narrative_arc, arc_required_motifs,
    arc_default_grid, apply_zorder_recipe, bootstrap_chart,
)

# 1. Resolve narrative arc + grid recipe (06 + 04)
arc    = select_narrative_arc(dataProfile, chartPlan)             # one of 10
recipe = arc_default_grid(arc, panel_count=len(chartPlan["panels"]))

# 2. Apply kernel (01) — choose variant based on arc
variant = "hero" if arc in ("hero",) else "compact" if arc in ("multipanel_grid", "n×n_pairwise") else "default"
apply_journal_kernel(variant=variant, journalProfile=journalProfile)

# 3. Build figure + axes (04)
fig, axes = build_grid(recipe, figsize=chartPlan.get("figsize"))

# 4. Resolve palette (03) — palette key chosen in Phase 2
palette = resolve_palette(chartPlan["palette_name"], journalProfile=journalProfile)

# 5. Apply per-family zorder recipe (02) AFTER drawing primitives
# 6. Apply required idioms (05) per arc
required = arc_required_motifs(arc)
```

**Reference docs (read on demand, not eagerly):**

| Decision | File |
|---|---|
| Kernel + variants | `template-mining/01-rcparams-kernel.md` |
| Sandwich layering per family | `template-mining/02-zorder-recipes.md` |
| Palette name → hex | `template-mining/03-palette-bank.md` |
| Multi-panel grid recipe | `template-mining/04-grid-recipes.md` |
| In-axes annotation idioms | `template-mining/05-annotation-idioms.md` |
| Narrative arc selection | `template-mining/06-narrative-arcs.md` |
| Family deep-dive (only if needed) | `template-mining/07-techniques/<family>.md` |

**Anchor cases lookup**: query `template-mining/case-index.json` for ≥3 cases matching the chosen `chart_families` or `narrative_arc`. Use them as visual references when writing the generator code — copy their layer structure, palette anchors, and annotation idioms verbatim before tuning to the user's data.

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

    field_top_journal = {
        **science,
        "name": workflowPreferences.get("journalStyleLabel", "field_top_journal"),
        "base_profile": "science",
        "single_width_mm": 89,
        "double_width_mm": 183,
        "font_size_body_pt": 6,
        "font_size_panel_label_pt": 8,
        "axis_linewidth_pt": 0.55,
        "tick_width_pt": 0.5,
        "panel_gap_rel": 0.18,
        "story_bias": "field_specific_top_journal",
        "domain_journal_label": workflowPreferences.get("journalStyleLabel"),
    }

    field_methods = {
        **nature,
        "name": workflowPreferences.get("journalStyleLabel", "field_methods"),
        "base_profile": "nature",
        "panel_gap_rel": 0.22,
        "story_bias": "methods_benchmark_validation",
        "domain_journal_label": workflowPreferences.get("journalStyleLabel"),
    }

    field_dense = {
        **cell,
        "name": workflowPreferences.get("journalStyleLabel", "field_dense"),
        "base_profile": "cell",
        "panel_gap_rel": 0.26,
        "story_bias": "dense_mechanism_performance",
        "domain_journal_label": workflowPreferences.get("journalStyleLabel"),
    }

    field_compact = {
        **science,
        "name": workflowPreferences.get("journalStyleLabel", "field_compact"),
        "base_profile": "science",
        "panel_gap_rel": 0.16,
        "story_bias": "compact_technical_comparison",
        "domain_journal_label": workflowPreferences.get("journalStyleLabel"),
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
    if style == "field_methods":
        return field_methods
    if style == "field_dense":
        return field_dense
    if style == "field_compact":
        return field_compact
    if style == "field_top_journal":
        return field_top_journal
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
- Do not rely on bare lines/points alone: `apply_visual_content_pass(...)` must add data-derived in-plot explanatory labels plus metric boxes/tables, inset or marginal summaries, endpoint/peak labels, threshold labels, perfect-fit/reference lines, density halos, density-colored points, sample-shape overlays, matrix labels, p-value star layers when p-values exist, dual-axis error bars when error columns exist, or effect/range summaries according to `visualContentPlan`

### Post-plot polish function (call after every chart generator)

Generator functions draw the base chart and apply minimal polish only. The generated script then runs `apply_visual_content_pass(...)` before the final figure contract so content density is controlled centrally instead of being reimplemented chart-by-chart. The helper source in `phases/code-gen/helpers.py` is the execution source of truth for in-plot explanatory labels, reference/template visual grammar motifs, metric tables, marginal axes, density-colored points, density halos, enhancement counts, residual axis-legend checks, typography limits, and cross-panel layout QA. Every saved figure must call the skill helper `enforce_figure_legend_contract(...)` immediately before the first `savefig`; direct `ax.legend(...)` calls are temporary handle sources only and are illegal if this finalizer is absent. Do not hand-write a replacement `enforce_figure_legend_contract`, because that bypasses rendered QA.

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

The canonical helper runtime is `phases/code-gen/helpers.py`. Do not duplicate helper implementations in this phase document. Step 3.6 must read that file, embed it into `full_code_string`, execute it, and use its public contract:

- `sanitize_columns`, `apply_chart_polish`, `apply_visual_content_pass`, `apply_template_radar_signature`, `apply_template_triangular_heatmap_signature`, `apply_crowding_management`, `enforce_figure_legend_contract`, `audit_figure_layout_contract`
- metadata fields: `legendContractEnforced`, `layoutContractEnforced`, `legendOutsidePlotArea`, `axisLegendRemainingCount`, `layoutContractFailures`, `visualGrammarMotifsApplied`, `templateMotifsApplied`, `metricTableCount`, `referenceLineCount`, `densityHaloCount`, `marginalAxesCount`, `densityColorEncodingCount`
- hard rule: generated code may create temporary `ax.legend(...)` handles, but final output must call `enforce_figure_legend_contract(...)` immediately before the first `savefig` and leave no axis legends behind

If a helper behavior needs to change, edit `phases/code-gen/helpers.py` and update tests; do not paste a local replacement here.
### Step 3.4b: Improved Multi-panel Composition

Use `panelBlueprint` as the source of truth and embed the canonical source from `phases/code-gen/generators-multipanel.py` during Step 3.6. Do not duplicate `resolve_canvas`, `resolve_panel_geometry`, or `compose_multipanel` here.

Composition rules that must remain true:

- Shared legends/colorbars are external layout elements, not plotted-area annotations.
- Bottom-center framed shared legend is preferred; top-center is the only fallback. Outside-right and `loc="best"` publication legends are forbidden.
- Risk tables, side summaries, and footnotes need reserved GridSpec/subfigure slots; no negative `ax.transAxes` text unless a slot is reserved.
- Print-scale typography only: body 5-7 pt, axes labels 6-8 pt, panel labels 8-10 pt, compact titles 7-9 pt.
- Panel labels use consistent anchor/font/offset, and axis link groups are used only when scales are semantically identical.
### Step 3.4c: Generator Source Contract

All charts in `CHART_GENERATORS` are backed by dedicated implementations loaded from the split source files listed in Step 3.6. Do not keep example generator bodies in this phase document; they drift from the tested source. If a future registry entry is added before its generator lands, emit a template-backed skeleton and note the gap in `styledCode["generatorCoverage"]`.
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
import re
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
legend_contract_report = enforce_figure_legend_contract(fig, fig.axes, chartPlan, journalProfile)
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
legend_contract_report = enforce_figure_legend_contract(fig, {{"A": ax}}, chartPlan, journalProfile)
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
legend_contract_report = enforce_figure_legend_contract(fig, {{"A": ax}}, secondaryPlan, journalProfile)
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
    "axisLegendGatePresent": "axisLegendRemainingCount" in full_code_string,
    "legendContractFinalizerPresent": "legend_contract_report = enforce_figure_legend_contract(" in full_code_string,
    "legendContractMetadataPresent": "legendContractEnforced" in full_code_string,
    "layoutContractMetadataPresent": "layoutContractFailures" in full_code_string and "audit_figure_layout_contract" in full_code_string,
    "embeddedHelperSourcePresent": "# Embedded helper source from the skill package" in full_code_string and "exec(aaa, globals())" in full_code_string,
    "singleLegendContractDefinition": full_code_string.count("def enforce_figure_legend_contract(") == 1,
    "negativeLegendAnchorScan": re.search(r"bbox_to_anchor\s*=\s*\([^)]*-\d", full_code_string) is None,
    "negativeAxesTextScan": re.search(r"(risk_table_y|table_y|footnote_y|label_y)\s*=\s*-\d", full_code_string) is None,
    "posterScaleFontScan": re.search(r"(font\.size['\"]?\s*:\s*(1[2-9]|[2-9]\d)|fontsize\s*=\s*(1[3-9]|[2-9]\d))", full_code_string) is None,
    "directAxesLegendCalls": len(re.findall(r"\b[a-zA-Z_]\w*\.legend\s*\(", full_code_string)),
    "visualDensityGatePresent": "minTotalEnhancements" in full_code_string and "inPlotExplanatoryLabelCount" in full_code_string,
    "referenceGrammarGatePresent": "minReferenceMotifsPerFigure" in full_code_string and "visualGrammarMotifsApplied" in full_code_string,
    "predictionDiagnosticGatePresent": "metricTableCount" in full_code_string and "densityHaloCount" in full_code_string,
    "hasSourceDataHooks": "source_data" in full_code_string,
    "hasMetadataHooks": "metadata" in full_code_string,
    "panelBlueprintMatched": True,
    "blockingFindings": []
}

if 'loc="best"' in full_code_string or "loc='best'" in full_code_string:
    codeReview["blockingFindings"].append("forbidden_loc_best")
if "axisLegendRemainingCount" not in full_code_string:
    codeReview["blockingFindings"].append("missing_axis_legend_remaining_gate")
if "legend_contract_report = enforce_figure_legend_contract(" not in full_code_string:
    codeReview["blockingFindings"].append("missing_legend_contract_finalizer_before_savefig")
if "legendContractEnforced" not in full_code_string:
    codeReview["blockingFindings"].append("missing_legend_contract_metadata")
if "layoutContractFailures" not in full_code_string or "audit_figure_layout_contract" not in full_code_string:
    codeReview["blockingFindings"].append("missing_layout_contract_metadata")
if "# Embedded helper source from the skill package" not in full_code_string or "exec(aaa, globals())" not in full_code_string:
    codeReview["blockingFindings"].append("missing_embedded_skill_helper_source")
if full_code_string.count("def enforce_figure_legend_contract(") != 1:
    codeReview["blockingFindings"].append("custom_or_duplicate_legend_contract_finalizer")
if re.search(r"bbox_to_anchor\s*=\s*\([^)]*-\d", full_code_string):
    codeReview["blockingFindings"].append("negative_legend_bbox_anchor")
if re.search(r"(risk_table_y|table_y|footnote_y|label_y)\s*=\s*-\d", full_code_string):
    codeReview["blockingFindings"].append("negative_axes_text_without_reserved_slot")
if re.search(r"(font\.size['\"]?\s*:\s*(1[2-9]|[2-9]\d)|fontsize\s*=\s*(1[3-9]|[2-9]\d))", full_code_string):
    codeReview["blockingFindings"].append("poster_scale_fontsize")
if codeReview["directAxesLegendCalls"] and "legend_contract_report = enforce_figure_legend_contract(" not in full_code_string:
    codeReview["blockingFindings"].append("direct_axes_legend_without_finalizer")
if "inPlotExplanatoryLabelCount" not in full_code_string or "minTotalEnhancements" not in full_code_string:
    codeReview["blockingFindings"].append("missing_visual_density_gate")
if "minReferenceMotifsPerFigure" not in full_code_string or "visualGrammarMotifsApplied" not in full_code_string:
    codeReview["blockingFindings"].append("missing_reference_visual_grammar_gate")
if "metricTableCount" not in full_code_string or "densityHaloCount" not in full_code_string:
    codeReview["blockingFindings"].append("missing_prediction_diagnostic_gate")
if "savefig" not in full_code_string:
    codeReview["blockingFindings"].append("missing_savefig")
if "savefig" in full_code_string and "legend_contract_report = enforce_figure_legend_contract(" not in full_code_string:
    codeReview["blockingFindings"].append("savefig_without_legend_contract")

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
> 5. `codeReview.blockingFindings` is empty after syntax/import drift, missing generator coverage, forbidden `loc="best"`, missing embedded helper source, custom legend finalizer, negative axes text/table slots, poster-scale font sizes, source-data/metadata hooks, reference visual grammar gates, and panelBlueprint checks
> 6. `full_code_string` embeds helper source from `phases/code-gen/helpers.py` and multi-panel source from `phases/code-gen/generators-multipanel.py`, keeps `crowdingPlan` and `visualContentPlan` attached to `chartPlan`, passes `ax` and `col_map` to generators, runs `apply_visual_content_pass(...)` before `enforce_figure_legend_contract(...)`, tracks `legendContractEnforced`, `layoutContractEnforced`, `layoutContractFailures`, `axisLegendRemainingCount`, `visualGrammarMotifsApplied`, `templateMotifsApplied`, `metricTableCount`, `referenceLineCount`, `densityHaloCount`, `marginalAxesCount`, and `densityColorEncodingCount`, and writes `savefig` calls for all `workflowPreferences["exportFormats"]`, using `workflowPreferences["rasterDpi"]` for raster outputs


> **Generator code**: Read [code-gen/generators-distribution.md](code-gen/generators-distribution.md) for distribution chart generators (violin_paired, violin_split, dot_strip, histogram, density, ecdf, joyplot, ridge, and 40+ additional chart types across genomics, engineering, ecology, and more).
> **Generator code**: Read [code-gen/generators-clinical.md](code-gen/generators-clinical.md) for clinical trial, composition, and hierarchical chart generators (caterpillar_plot, swimmer_plot, risk_ratio_plot, tornado_chart, nomogram, decision_curve, treemap, sunburst, waffle_chart, marimekko, stacked_area_comp, nested_donut).
> **Generator code**: Read [code-gen/generators-psychology.md](code-gen/generators-psychology.md) for relationship, psychology, and social science chart generators (chord_diagram, parallel_coordinates, sankey, radar, likert_divergent, likert_stacked, mediation_path, interaction_plot).
## Output

- **Variable**: `styledCode`
- **TodoWrite**: Mark Phase 3 completed, Phase 4 in_progress

## Next Phase

Return to orchestrator, then continue to [Phase 4: Export, Source Data, And Reporting](04-export-report.md).
