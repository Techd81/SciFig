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
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": 72}
    if recipe == "hero_plus_stacked_support":
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": 130}
    return {"width_mm": journalProfile["double_width_mm"], "height_mm": 140}


def resolve_panel_geometry(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    gap = journalProfile["panel_gap_rel"]

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
    "violin+strip": "gen_violin_strip",
    "box+strip": "gen_box_strip",
    "raincloud": "gen_raincloud",
    "beeswarm": "gen_beeswarm",
    "paired_lines": "gen_paired_lines",
    "dumbbell": "gen_dumbbell",
    "line": "gen_line",
    "line_ci": "gen_line_ci",
    "spaghetti": "gen_spaghetti",
    "heatmap+cluster": "gen_heatmap_cluster",
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
    if chart_type in ("violin+strip", "violin_paired", "violin_split", "violin_grouped"):
        for coll in ax.collections:
            if hasattr(coll, "set_alpha"):
                coll.set_alpha(0.3)

    # Y-axis baseline: anchor at 0 for ratio-scale data
    if chart_type in ("violin+strip", "box+strip", "dot+box", "bar"):
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

When labeling top genes/points, use staggered vertical offsets to prevent overlap:

```python
# Sort by significance, pick top N
top = df[df.category != "NS"].nlargest(6, "nlogp")
for idx, (_, row) in enumerate(top.iterrows()):
    # Stagger: alternate offset groups to spread labels
    y_offset = (idx % 3) * max_y * 0.04  # 3 stagger levels
    ax.annotate(row["gene"], (row["log2fc"], row["nlogp"] + y_offset),
                fontsize=4, ha="center", va="bottom",
                arrowprops=dict(arrowstyle="-", lw=0.3, color="black"))
```

If >8 labels, consider showing only top 5 and adding a legend entry for the rest.

### Step 3.4b: Improved Multi-panel Composition

Use the `panelBlueprint` as the source of truth.

```python
def gen_multipanel(chartPlan, journalProfile, colorSystem):
    panelBlueprint = chartPlan["panelBlueprint"]
    panels = panelBlueprint["panels"]
    geometry = resolve_panel_geometry(panelBlueprint, journalProfile)
    canvas = resolve_canvas(panelBlueprint, journalProfile)

    code = f"""
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt

mm = 1/25.4
fig = plt.figure(figsize=({canvas['width_mm']}*mm, {canvas['height_mm']}*mm))
labels = {[p['id'] for p in panels]}
panel_defs = {panels}
shared_handles = []

"""

    if geometry["engine"] == "GridSpec":
        if geometry["grid"] == "2x2-hero-span":
            code += f"""
gs = GridSpec(2, 2, figure=fig, hspace={geometry['hspace']}, wspace={geometry['wspace']})
axes = {{
    "A": fig.add_subplot(gs[:, 0]),
    "B": fig.add_subplot(gs[0, 1]),
    "C": fig.add_subplot(gs[1, 1]),
}}
"""
        else:
            code += f"""
gs = GridSpec(2, 2, figure=fig, hspace={geometry['hspace']}, wspace={geometry['wspace']})
axes = {{
    "A": fig.add_subplot(gs[0, 0]),
    "B": fig.add_subplot(gs[0, 1]),
    "C": fig.add_subplot(gs[1, 0]),
    "D": fig.add_subplot(gs[1, 1]),
}}
"""
    else:
        code += """
fig, axs = plt.subplots(1, 2, figsize=fig.get_size_inches())
axes = {"A": axs[0], "B": axs[1]}
"""

    code += """
for panel in panel_defs:
    ax = axes[panel["id"]]
    # Dispatch to chart generator using panel["chart"]
    # Generators should accept ax=... so panels share one figure.
    ax.text(-0.12, 1.05, panel["id"], transform=ax.transAxes,
            fontsize=8, fontweight="bold", va="top", ha="left")

if chartPlan["panelBlueprint"].get("sharedLegend", False):
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels),
               frameon=False, fontsize=5, bbox_to_anchor=(0.5, 1.02))

fig.savefig("output/figure1.pdf", bbox_inches="tight")
fig.savefig("output/figure1.svg", bbox_inches="tight")
"""
    return code
```

Composition rules:

- Hero panel may span rows or columns.
- Panels sharing the same semantic categories should reuse one legend.
- Heatmaps and spatial score panels should reuse one colorbar when the same signal is encoded.
- Keep panel labels at the same anchor, font, and offset.
- Respect `axisLinkGroups` only when scales are semantically identical.

### Step 3.4c: Expanded Generator Examples

Provide first-class templates for newly added chart families:

```python
def gen_raincloud(df, roles, colorSystem, ax):
    # half-violin + box + jittered points
    pass


def gen_dose_response(df, roles, colorSystem, ax):
    # fit 4PL curve, show observations and estimated EC50/IC50
    pass


def gen_enrichment_dotplot(df, roles, colorSystem, ax):
    # term on y-axis, NES or ratio on x-axis, dot size for set size, color for adjusted p
    pass


def gen_pr_curve(df, roles, colorSystem, ax):
    # precision-recall curve with AP annotation and optional baseline
    pass


def gen_umap(df, roles, colorSystem, ax):
    # embedding scatter with stable cell-type colors and optional centroid labels
    pass
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

### Step 3.4d: Distribution Chart Generators (Implemented)

The following 8 generators provide production-ready templates for distribution chart types registered in `CHART_GENERATORS`. Each follows the Nature/Cell style contract: open-L spines, no grid, round line caps, publication font sizes, and `apply_chart_polish` post-processing.

```python
# ──────────────────────────────────────────────────────────────
# Distribution Chart Generators
# Signature: gen_xxx(df, dataProfile, chartPlan, rcParams, palette) -> ax
# Each returns the matplotlib Axes for multi-panel composition.
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


def gen_histogram(df, dataProfile, chartPlan, rcParams, palette):
    """Grouped histogram with overlaid KDE density curves.

    Supports 1-6 groups. Uses Freedman-Diaconis bin width with a floor of
    10 bins.  KDE overlay uses Gaussian kernel with Scott bandwidth.
    """
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("histogram requires a numeric value column in semanticRoles")

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
        ax.legend(loc="best", frameon=False, fontsize=5)
    else:
        values = df[value_col].dropna()
        iqr = values.quantile(0.75) - values.quantile(0.25)
        bin_width = 2 * iqr * len(values) ** (-1 / 3) if iqr > 0 else 0.1
        n_bins = max(10, int(np.ceil((values.max() - values.min()) / bin_width))) if bin_width > 0 else 15
        color = palette.get("categorical", ["#000000"])[0]

        ax.hist(values, bins=n_bins, density=True, alpha=0.35,
                color=color, edgecolor="white", linewidth=0.4)
        sns.kdeplot(values, ax=ax, color=color, linewidth=0.8)

    ax.set_xlabel(value_col)
    ax.set_ylabel("Density")
    apply_chart_polish(ax, "histogram")
    return ax


def gen_density(df, dataProfile, chartPlan, rcParams, palette):
    """Kernel density estimation for multiple groups.

    Uses Gaussian kernel with Silverman bandwidth.  Each group gets a filled
    KDE with controlled opacity so overlapping distributions remain legible.
    """
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("density requires a numeric value column in semanticRoles")

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
        ax.legend(loc="best", frameon=False, fontsize=5)
    else:
        values = df[value_col].dropna()
        color = palette.get("categorical", ["#000000"])[0]
        sns.kdeplot(values, ax=ax, fill=True, alpha=0.3,
                    color=color, linewidth=0.8)

    ax.set_xlabel(value_col)
    ax.set_ylabel("Density")
    apply_chart_polish(ax, "density")
    return ax


def gen_ecdf(df, dataProfile, chartPlan, rcParams, palette):
    """Empirical cumulative distribution function for comparing groups.

    Step-function CDF (no smoothing).  Each group drawn in its palette color
    with a thin line to preserve legibility when many groups overlap.
    """
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("ecdf requires a numeric value column in semanticRoles")

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
        ax.legend(loc="best", frameon=False, fontsize=5)
    else:
        values = df[value_col].dropna()
        color = palette.get("categorical", ["#000000"])[0]
        sorted_vals = np.sort(values)
        ecdf_y = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        ax.step(sorted_vals, ecdf_y, where="post", color=color, linewidth=0.8)

    ax.set_xlabel(value_col)
    ax.set_ylabel("Cumulative proportion")
    ax.set_ylim(0, 1.05)
    apply_chart_polish(ax, "ecdf")
    return ax


def gen_ridge(df, dataProfile, chartPlan, rcParams, palette):
    """Ridgeline / joy plot for many groups.

    Overlapping density ridges stacked vertically.  Uses Gaussian KDE with
    shared bandwidth across groups.  Groups ordered by median value.
    """
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
    apply_chart_polish(ax, "ridge")
    return ax


def gen_violin_paired(df, dataProfile, chartPlan, rcParams, palette):
    """Paired violin plots (before/after or time 1/time 2).

    Expects a group column with exactly 2 levels and a subject/pair ID column
    in semanticRoles["pair_id"].  Connects paired observations with thin gray
    lines.
    """
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
    apply_chart_polish(ax, "violin_paired")
    return ax


def gen_violin_split(df, dataProfile, chartPlan, rcParams, palette):
    """Split violin (half/half comparison).

    Two groups shown as left and right halves of a violin at the same
    position.  Requires exactly 2 groups.  Each half is the KDE of one group,
    mirrored for visual comparison.
    """
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
    ax.legend(handles=legend_handles, loc="best", frameon=False, fontsize=5)

    apply_chart_polish(ax, "violin_split")
    return ax


def gen_dot_strip(df, dataProfile, chartPlan, rcParams, palette):
    """Pure dot plot (Cleveland-style, no box or violin).

    Each observation is a single dot.  Dots are stacked along the y-axis using
    a beeswarm-style jitter to prevent overplotting.  Preferred for small-to-
    medium sample sizes (n < 100 per group).
    """
    plt.rcParams.update(rcParams)
    group_col, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("dot_strip requires a numeric value column")

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
    apply_chart_polish(ax, "dot_strip")
    return ax


def gen_joyplot(df, dataProfile, chartPlan, rcParams, palette):
    """Stacked density ridgeline (joyplot).

    Similar to gen_ridge but with more overlap and filled areas, producing the
    classic "joy division" aesthetic.  Groups are ordered by median and each
    ridge is a filled KDE with high overlap.
    """
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
    apply_chart_polish(ax, "joyplot")
    return ax


def gen_residual_vs_fitted(df, dataProfile, chartPlan, rcParams, palette):
    """Residuals vs fitted values scatter for regression diagnostics.

    Expects columns: fitted (predicted values) and residual in semanticRoles.
    Adds a horizontal reference line at y=0 and a LOWESS smoother to reveal
    non-linearity or heteroscedasticity patterns.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    fitted_col = roles.get("fitted") or roles.get("x")
    resid_col = roles.get("residual") or roles.get("value")

    if fitted_col is None or resid_col is None:
        raise ValueError("residual_vs_fitted requires 'fitted' and 'residual' in semanticRoles")

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
    apply_chart_polish(ax, "residual_vs_fitted")
    return ax


def gen_scale_location(df, dataProfile, chartPlan, rcParams, palette):
    """Scale-location plot: sqrt(|standardized residuals|) vs fitted values.

    Used to assess homoscedasticity.  A flat LOWESS line suggests constant
    variance; an upward trend indicates increasing spread with fitted values.
    Expects columns: fitted and residual (or standardized_residual) in
    semanticRoles.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    fitted_col = roles.get("fitted") or roles.get("x")
    resid_col = roles.get("standardized_residual") or roles.get("residual") or roles.get("value")

    if fitted_col is None or resid_col is None:
        raise ValueError("scale_location requires 'fitted' and 'residual' in semanticRoles")

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
    apply_chart_polish(ax, "scale_location")
    return ax


def gen_pp_plot(df, dataProfile, chartPlan, rcParams, palette):
    """P-P plot: observed vs expected cumulative probabilities.

    Plots empirical CDF against a theoretical reference (normal by default)
    to assess distributional fit.  Points lying on the diagonal indicate
    good agreement; systematic deviations reveal skew, heavy tails, or
    other departures from the reference distribution.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    value_col = roles.get("value") or roles.get("y")

    if value_col is None:
        raise ValueError("pp_plot requires a numeric value column in semanticRoles")

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
    apply_chart_polish(ax, "pp_plot")
    return ax


def gen_bland_altman(df, dataProfile, chartPlan, rcParams, palette):
    """Bland-Altman agreement plot: mean vs difference of paired measurements.

    Each point represents one subject measured by two methods (or timepoints).
    The x-axis is the mean of the two measurements; the y-axis is their
    difference.  Horizontal lines mark the mean bias and 95 % limits of
    agreement (mean +/- 1.96 SD of differences).
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    # Expect two measurement columns
    method_a = roles.get("method_a") or roles.get("x")
    method_b = roles.get("method_b") or roles.get("y") or roles.get("value")

    if method_a is None or method_b is None:
        raise ValueError("bland_altman requires 'method_a' and 'method_b' columns in semanticRoles")

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
    apply_chart_polish(ax, "bland_altman")
    return ax


def gen_funnel_plot(df, dataProfile, chartPlan, rcParams, palette):
    """Funnel plot for publication bias assessment.

    Plots effect size (or log odds ratio) against a precision measure
    (typically sample size or inverse standard error).  A pseudo-95%
    confidence funnel is drawn around the pooled estimate, and studies
    outside the funnel are highlighted as potential bias signals.

    Expects in semanticRoles: effect (effect size), precision (1/SE or
    sample size), and optionally label (study identifier).
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    effect_col = roles.get("effect") or roles.get("y") or roles.get("value")
    precision_col = roles.get("precision") or roles.get("x")
    label_col = roles.get("label")

    if effect_col is None or precision_col is None:
        raise ValueError("funnel_plot requires 'effect' and 'precision' in semanticRoles")

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
    apply_chart_polish(ax, "funnel_plot")
    return ax


def gen_pareto_chart(df, dataProfile, chartPlan, rcParams, palette):
    """Pareto chart: bars sorted descending with cumulative percentage line.

    Bars represent category frequencies (descending order) and a secondary
    y-axis shows the cumulative percentage.  The 80% threshold line is
    drawn per the Pareto principle.

    Expects in semanticRoles: category (categorical column) and optionally
    value (pre-aggregated counts).  If value is absent, rows are counted
    per category.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    cat_col = roles.get("category") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")

    if cat_col is None:
        raise ValueError("pareto_chart requires a 'category' column in semanticRoles")

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
    apply_chart_polish(ax, "pareto_chart")
    return ax


def gen_mean_diff_plot(df, dataProfile, chartPlan, rcParams, palette):
    """Mean-difference plot (Tukey-style alternative to Bland-Altman).

    Each point is one subject measured twice.  X-axis = mean of the two
    measurements; Y-axis = difference (method A minus method B).  A solid
    horizontal line marks the mean difference; dashed lines mark the 95 % CI
    of the mean and 95 % limits of agreement (mean +/- 1.96 SD).
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    method_a = roles.get("method_a") or roles.get("x")
    method_b = roles.get("method_b") or roles.get("y") or roles.get("value")

    if method_a is None or method_b is None:
        raise ValueError("mean_diff_plot requires 'method_a' and 'method_b' in semanticRoles")

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
    apply_chart_polish(ax, "mean_diff_plot")
    return ax


def gen_ci_plot(df, dataProfile, chartPlan, rcParams, palette):
    """Confidence interval plot for multiple estimates.

    Displays horizontal CI bars for each estimate row.  Expects columns for
    estimate (point value), lower CI bound, and upper CI bound.  Optionally
    accepts a label column for y-axis tick names.  A vertical reference line
    at x = 0 is drawn when the interval spans zero.
    """
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
    apply_chart_polish(ax, "ci_plot")
    return ax


def gen_cook_distance(df, dataProfile, chartPlan, rcParams, palette):
    """Cook's distance bar chart for influential point detection.

    Fits OLS on observation index vs value column, computes Cook's D for each
    point, and highlights observations exceeding the 4/n threshold.
    """
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

    fig, ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4),
                           constrained_layout=True)
    ax.bar(np.arange(n), cook_d, color=colors, edgecolor="white",
           linewidth=0.4, width=0.8)
    ax.axhline(threshold, color="gray", linestyle="--", linewidth=0.6,
               label=f"4/n = {threshold:.3f}")
    ax.legend(frameon=False, fontsize=5)
    ax.set_xlabel("Observation index")
    ax.set_ylabel("Cook's distance")
    apply_chart_polish(ax, "cook_distance")
    return ax


def gen_leverage_plot(df, dataProfile, chartPlan, rcParams, palette):
    """Leverage vs squared residual for regression diagnostics.

    Fits OLS on observation index vs value, plots leverage (hat values) against
    squared residuals.  A vertical line marks the 2p/n high-leverage threshold.
    """
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
    apply_chart_polish(ax, "leverage_plot")
    return ax


def gen_circos_karyotype(df, dataProfile, chartPlan, rcParams, palette):
    """Simplified circos-like karyotype plot (linear chromosomes with colored tracks).

    Expects columns: chromosome, start, end, and optionally track_value and
    track_color in semanticRoles.  Draws horizontal chromosome bands with
    colored overlay tracks simulating a circos layout in linear form.
    """
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
                seg_alpha = 0.3 + 0.7 * min(row[value_col], 1.0)
            ax.barh(yi, row[end_col] - row[start_col], left=row[start_col],
                    height=0.5, color=seg_color, alpha=seg_alpha, linewidth=0)

    ax.set_yticks(range(n_chr))
    ax.set_yticklabels(chromosomes, fontsize=5)
    ax.set_xlabel("Genomic position")
    ax.set_ylim(-0.5, n_chr - 0.5)
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    apply_chart_polish(ax, "circos_karyotype")
    return ax


def gen_gene_structure(df, dataProfile, chartPlan, rcParams, palette):
    """Gene structure diagram (exons as boxes, introns as lines, UTRs colored).

    Expects columns: feature_type (exon/intron/5utr/3utr/cds), start, end,
    and optionally strand in semanticRoles.  Draws a horizontal gene model
    with exon boxes, intron lines, and colored UTR regions.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    type_col = roles.get("feature_type") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end")
    strand = roles.get("strand", "+")

    if type_col is None or start_col is None or end_col is None:
        raise ValueError("gene_structure requires 'feature_type', 'start', 'end' in semanticRoles")

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

    apply_chart_polish(ax, "gene_structure")
    return ax


def gen_pathway_map(df, dataProfile, chartPlan, rcParams, palette):
    """Pathway enrichment bubble chart.

    x=enrichment score, y=pathway name, size=gene count, color=-log10(p).
    Expects columns: pathway, enrichment_score, gene_count, p_value in semanticRoles.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pathway_col = roles.get("pathway") or roles.get("group") or roles.get("y")
    score_col = roles.get("enrichment_score") or roles.get("x") or roles.get("value")
    count_col = roles.get("gene_count") or roles.get("size")
    pval_col = roles.get("p_value") or roles.get("color")

    if pathway_col is None or score_col is None:
        raise ValueError("pathway_map requires 'pathway' and 'enrichment_score' in semanticRoles")

    fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(60, 12 * len(df) + 20) * (1 / 25.4)),
                           constrained_layout=True)

    nlogp = -np.log10(df[pval_col].clip(lower=1e-300)) if pval_col and pval_col in df.columns else np.ones(len(df))
    sizes = df[count_col] * 8 if count_col and count_col in df.columns else np.full(len(df), 40)
    cmap = plt.cm.YlOrRd

    scatter = ax.scatter(df[score_col], df[pathway_col], s=sizes, c=nlogp,
                         cmap=cmap, alpha=0.7, edgecolor="white", linewidth=0.4)
    cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label(r"$-\log_{10}(p)$", fontsize=5)
    cbar.ax.tick_params(labelsize=4)

    ax.set_xlabel("Enrichment score")
    ax.set_ylabel("")
    ax.invert_yaxis()
    apply_chart_polish(ax, "pathway_map")
    return ax


def gen_kegg_bar(df, dataProfile, chartPlan, rcParams, palette):
    """KEGG pathway horizontal bar chart.

    Enrichment ratio bars with significance markers (* p<0.05, ** p<0.01, *** p<0.001).
    Expects columns: pathway, enrichment_ratio, p_value in semanticRoles.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pathway_col = roles.get("pathway") or roles.get("group") or roles.get("y")
    ratio_col = roles.get("enrichment_ratio") or roles.get("x") or roles.get("value")
    pval_col = roles.get("p_value")

    if pathway_col is None or ratio_col is None:
        raise ValueError("kegg_bar requires 'pathway' and 'enrichment_ratio' in semanticRoles")

    n = len(df)
    fig_height = max(60, 12 * n + 20) * (1 / 25.4)
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
    apply_chart_polish(ax, "kegg_bar")
    return ax


def gen_control_chart(df, dataProfile, chartPlan, rcParams, palette):
    """Shewhart control chart with mean line and +/-3sigma limits.

    Expects a numeric value column in semanticRoles["value"].  Points beyond
    the control limits are highlighted in red.  Center line shows the process
    mean; upper/lower limits are mean +/- 3 * std.
    """
    plt.rcParams.update(rcParams)
    _, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("control_chart requires a numeric value column in semanticRoles")

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
    ax.legend(loc="best", frameon=False, fontsize=5)
    apply_chart_polish(ax, "control_chart")
    return ax


def gen_box_paired(df, dataProfile, chartPlan, rcParams, palette):
    """Paired box plots with per-subject connecting lines.

    Expects a group column with exactly 2 levels and a subject/pair ID column
    in semanticRoles["pair_id"].  Boxes show before/after distributions; thin
    gray lines connect paired observations across conditions.
    """
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
    apply_chart_polish(ax, "box_paired")
    return ax


def gen_stress_strain(df, dataProfile, chartPlan, rcParams, palette):
    """Stress-strain curve for materials science.

    Plots strain (x) vs stress (y) with optional yield point annotation.
    Expects columns: strain (x-axis) and stress (y-axis) in semanticRoles.
    If a yield_strain/yield_stress column exists, annotates the yield point.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    strain_col = roles.get("strain") or roles.get("x")
    stress_col = roles.get("stress") or roles.get("y") or roles.get("value")

    if strain_col is None or stress_col is None:
        raise ValueError("stress_strain requires 'strain' and 'stress' in semanticRoles")

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
    apply_chart_polish(ax, "stress_strain")
    return ax


def gen_xrd_pattern(df, dataProfile, chartPlan, rcParams, palette):
    """X-ray diffraction (XRD) pattern with stick plot peaks.

    Plots 2-theta (x) vs intensity (y) as vertical sticks at peak positions.
    Expects columns: two_theta (x-axis) and intensity (y-axis) in semanticRoles.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    theta_col = roles.get("two_theta") or roles.get("x")
    intensity_col = roles.get("intensity") or roles.get("y") or roles.get("value")

    if theta_col is None or intensity_col is None:
        raise ValueError("xrd_pattern requires 'two_theta' and 'intensity' in semanticRoles")

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
    apply_chart_polish(ax, "xrd_pattern")
    return ax


def gen_treemap(df, dataProfile, chartPlan, rcParams, palette):
    """Treemap with squarified algorithm, hierarchical size encoding, labels inside rectangles.

    Expects in semanticRoles: category (labels) and value (numeric sizes).
    Optionally parent for two-level hierarchy.  Uses squarify library when
    available; falls back to a simple slice-and-dice layout with matplotlib
    patches.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    cat_col = roles.get("category") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")
    parent_col = roles.get("parent")

    if cat_col is None or val_col is None:
        raise ValueError("treemap requires 'category' and 'value' in semanticRoles")

    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])
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
    apply_chart_polish(ax, "treemap")
    return ax


def gen_sunburst(df, dataProfile, chartPlan, rcParams, palette):
    """Sunburst / hierarchical donut chart with rings from center outward.

    Expects in semanticRoles: category (inner ring labels), value (numeric
    sizes), and optionally subcategory (outer ring labels).  When only
    category is provided, renders a single-ring donut.  With subcategory,
    draws two concentric rings where the outer ring segments are proportional
    within each inner-ring wedge.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    cat_col = roles.get("category") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")
    sub_col = roles.get("subcategory") or roles.get("subgroup")

    if cat_col is None or val_col is None:
        raise ValueError("sunburst requires 'category' and 'value' in semanticRoles")

    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])
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
    apply_chart_polish(ax, "sunburst")
    return ax


def gen_swimmer_plot(df, dataProfile, chartPlan, rcParams, palette):
    """Swimmer plot: horizontal bars for treatment duration with event markers.

    Each row is a patient.  A horizontal bar spans from start to end (e.g.
    treatment start/stop).  Optional marker columns encode events such as
    response, progression, or adverse events with distinct shapes/colors.

    Expects in semanticRoles: id (patient label), start, end, and optionally
    group (arm/cohort).  Event markers are read from columns whose names are
    listed in chartPlan.get("eventColumns", []).
    """
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
    apply_chart_polish(ax, "swimmer_plot")
    return ax


def gen_risk_ratio_plot(df, dataProfile, chartPlan, rcParams, palette):
    """Risk ratio forest plot (HR / OR with 95 % CI).

    Horizontal forest plot showing hazard ratios or odds ratios with
    confidence intervals for each subgroup.  A vertical reference line at 1
    (no effect) is drawn.  Optionally annotates p-values on the right margin.

    Expects in semanticRoles: label (subgroup name), estimate (HR or OR),
    ci_lower, ci_upper, and optionally p_value.
    """
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
    apply_chart_polish(ax, "risk_ratio_plot")
    return ax


def gen_sankey(df, dataProfile, chartPlan, rcParams, palette):
    """Simplified Sankey diagram showing flow between stages using matplotlib patches.

    Expects columns: source (origin stage), target (destination stage), and
    value (flow magnitude) in semanticRoles.  Draws horizontal node bars at
    left/right with filled bezier-like flow ribbons connecting them.
    Nature style: no grid, open-L spines, publication fonts.
    """
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
    apply_chart_polish(ax, "sankey")
    return ax


def gen_radar(df, dataProfile, chartPlan, rcParams, palette):
    """Radar / spider chart for multi-attribute comparison across groups.

    Expects columns: attribute (axis label), group (series), and value in
    semanticRoles.  One polygon per group, filled with semi-transparent color.
    Axes are radial with attribute labels at each spoke.  Nature style: thin
    lines, no grid fill, publication fonts.
    """
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

    fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           subplot_kw=dict(polar=True),
                           constrained_layout=True)

    angles = np.linspace(0, 2 * np.pi, n_attrs, endpoint=False).tolist()
    angles += angles[:1]  # close polygon

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(attributes, fontsize=5)
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

    apply_chart_polish(ax, "radar")
    return ax


def gen_likert_divergent(df, dataProfile, chartPlan, rcParams, palette):
    """Diverging stacked bar chart for Likert scale responses.

    Bars extend left (negative) and right (positive) from a center line at
    neutral.  Expects one row per respondent and columns whose names match the
    Likert categories (e.g., 'Strongly Disagree', 'Disagree', 'Neutral',
    'Agree', 'Strongly Agree').  The question/item labels come from
    semanticRoles['group']; the Likert columns are auto-detected from a
    predefined ordered list.
    """
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
    apply_chart_polish(ax, "likert_divergent")
    return ax


def gen_likert_stacked(df, dataProfile, chartPlan, rcParams, palette):
    """Horizontal stacked bar chart for Likert responses.

    Each bar represents one item/question; segments show the percentage
    breakdown across ordered Likert categories with percentage labels inside
    each segment.  Expects one row per respondent, item labels in
    semanticRoles['group'], and Likert response columns auto-detected from a
    predefined ordered list.
    """
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
    apply_chart_polish(ax, "likert_stacked")
    return ax


def gen_clustered_bar(df, dataProfile, chartPlan, rcParams, palette):
    """Clustered bar chart: multiple metrics per group, side-by-side bars.

    Each group gets one cluster of bars, one bar per metric column.
    Expects in semanticRoles: group (category axis) and a list of value
    columns encoded as semicolon-separated string in 'value' or 'y'.
    Falls back to all numeric columns when no explicit value list is given.
    """
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
    apply_chart_polish(ax, "clustered_bar")
    return ax


def gen_grouped_bar(df, dataProfile, chartPlan, rcParams, palette):
    """Grouped bar chart with error bars: subgroups within categories.

    Each category on the x-axis contains one bar per subgroup, with SEM
    error bars.  Expects in semanticRoles: group (x-axis categories),
    subgroup (bar series within each group), and value (numeric y).
    Computes mean and SEM per cell for error bar display.
    """
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
    apply_chart_polish(ax, "grouped_bar")
    return ax


def gen_ordination_plot(df, dataProfile, chartPlan, rcParams, palette):
    """Ordination plot (PCoA/NMDS) with group confidence ellipses.

    Expects in semanticRoles: x (axis 1 scores), y (axis 2 scores), and group
    (sample grouping).  Draws 95 % confidence ellipses per group using the
    chi-squared distribution.  Nature style: thin lines, no grid, publication
    fonts.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("axis1")
    y_col = roles.get("y") or roles.get("axis2")
    group_col = roles.get("group")

    if x_col is None or y_col is None:
        raise ValueError("ordination_plot requires 'x' and 'y' (axis scores) in semanticRoles")

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
        ax.legend(loc="best", frameon=False, fontsize=5)
    else:
        ax.scatter(df[x_col], df[y_col], s=12, alpha=0.7,
                   color=palette.get("categorical", ["#0072B2"])[0],
                   linewidth=0.3, edgecolor="white", zorder=2)

    ax.set_xlabel(f"{method} axis 1")
    ax.set_ylabel(f"{method} axis 2")
    apply_chart_polish(ax, "ordination_plot")
    return ax


def gen_biodiversity_radar(df, dataProfile, chartPlan, rcParams, palette):
    """Biodiversity radar: multiple diversity indices on polar axes.

    Expects in semanticRoles: attribute (diversity index name) and value
    (index value).  Optionally group for comparing communities.  Indices are
    plotted as radial spokes (e.g. Shannon, Simpson, Richness, Evenness,
    Chao1).  Values are min-max normalised to [0, 1] for visual comparison.
    Nature style: thin lines, no grid fill, publication fonts.
    """
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

    fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           subplot_kw=dict(polar=True),
                           constrained_layout=True)

    angles = np.linspace(0, 2 * np.pi, n_idx, endpoint=False).tolist()
    angles += angles[:1]

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(indices, fontsize=5)
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

    apply_chart_polish(ax, "biodiversity_radar")
    return ax


def gen_bubble_scatter(df, dataProfile, chartPlan, rcParams, palette):
    """Bubble scatter chart with size and color encoding.

    x and y are numeric axes; a third variable controls marker size and an
    optional fourth variable (or group column) controls marker color.  Uses
    Nature-style open-L spines, no grid, and publication font sizes.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x")
    y_col = roles.get("y") or roles.get("value")
    size_col = roles.get("size") or roles.get("z")
    color_col = roles.get("color") or roles.get("group")

    if x_col is None or y_col is None:
        raise ValueError("bubble_scatter requires 'x' and 'y' in semanticRoles")

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
        ax.legend(loc="best", frameon=False, fontsize=5, title_fontsize=5)
    else:
        color = palette.get("categorical", ["#0072B2"])[0]
        ax.scatter(df[x_col], df[y_col], s=sizes, color=color, alpha=0.6,
                   edgecolor="white", linewidth=0.4, zorder=2)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    apply_chart_polish(ax, "bubble_scatter")
    return ax


def gen_connected_scatter(df, dataProfile, chartPlan, rcParams, palette):
    """Connected scatter plot showing trajectory in x-y space.

    Points are drawn in row order and connected by sequential lines to reveal
    temporal or ordinal trajectories.  Optional group column draws separate
    trajectories per category.  Nature-style open-L spines, no grid.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x")
    y_col = roles.get("y") or roles.get("value")
    group_col = roles.get("group")

    if x_col is None or y_col is None:
        raise ValueError("connected_scatter requires 'x' and 'y' in semanticRoles")

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
        ax.legend(loc="best", frameon=False, fontsize=5)
    else:
        ordered = df.sort_values(x_col)
        color = palette.get("categorical", ["#0072B2"])[0]
        ax.plot(ordered[x_col], ordered[y_col], color=color, linewidth=0.8,
                solid_capstyle="round", zorder=1)
        ax.scatter(ordered[x_col], ordered[y_col], s=14, color=color, alpha=0.7,
                   edgecolor="white", linewidth=0.3, zorder=2)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    apply_chart_polish(ax, "connected_scatter")
    return ax


def gen_species_abundance(df, dataProfile, chartPlan, rcParams, palette):
    """Horizontal bar chart of species abundance, sorted descending.

    Ecology-style plot where each bar represents a species (or OTU/ASV) and
    its count or relative abundance.  Bars are sorted from most to least
    abundant and drawn horizontally for long species labels.  Uses Nature
    style: open-L spines, no grid, round line caps, 6 pt font.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    species_col = roles.get("species") or roles.get("group") or roles.get("label")
    abundance_col = roles.get("abundance") or roles.get("value") or roles.get("y")

    if species_col is None or abundance_col is None:
        raise ValueError("species_abundance requires 'species' and 'abundance' in semanticRoles")

    agg = df.groupby(species_col)[abundance_col].sum().sort_values(ascending=True)
    n = len(agg)

    fig_height = max(60, 5 * n + 20) * (1 / 25.4)
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
    apply_chart_polish(ax, "species_abundance")
    return ax


def gen_shannon_diversity(df, dataProfile, chartPlan, rcParams, palette):
    """Bar chart comparing Shannon diversity index across groups with error bars.

    Expects one row per sample with a group column and a Shannon index value.
    Computes mean and SEM per group, then draws vertical bars with error caps.
    Nature style: open-L spines, no grid, round line caps, 6 pt font.
    """
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value") or roles.get("y") or roles.get("shannon")

    if group_col is None or value_col is None:
        raise ValueError("shannon_diversity requires 'group' and 'value' in semanticRoles")

    stats = df.groupby(group_col)[value_col].agg(["mean", "sem"]).reset_index()
    categories = stats[group_col].tolist()
    color_map = _extract_colors(palette, categories)

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
    apply_chart_polish(ax, "shannon_diversity")
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
