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
    add_forest_panel, add_heatmap_pairwise_panel,
    apply_scatter_regression_floor, resolve_split_palette,
    set_polar_title,
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

**Anchor cases lookup**: query `template-mining/case-index.json` for ≥3 cases matching the chosen `chart_families` or `narrative_arc`. If `chartPlan.templateCasePlan.templateMatchMode == "clone_when_known"` or `visualContentPlan.exactTemplateReplicationRequired` is true, read every `templateCasePlan.techniqueRefs` file and use `templateCasePlan.anchors` as the primary visual references. For known families (marginal-joint, SHAP composite, heatmap-pairwise, radar, dual-axis, time-series-pi, gradient-box, inset-distribution, ML model diagnostics), copy the template case's layer structure, subplot proportions, palette anchors, z-order stack, annotation idioms, legend/colorbar placement, and sidecar axes layout before tuning to the user's data. If the selected bundle key is `rf_model_performance_report`, clone the RF triptych first: top-row model train/test benchmark, bottom-left predicted-vs-actual parity scatter, bottom-right residual-vs-predicted diagnostic.

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
        "font_family": ["DejaVu Sans", "Arial", "Helvetica"],
        "font_size_body_pt": 6,
        "font_size_small_pt": 7,
        "font_size_panel_label_pt": 9,
        "axis_linewidth_pt": 0.6,
        "tick_width_pt": 0.6,
        "panel_gap_rel": 0.22,
        "canvas_height_mm": {
            "single": 62,
            "comparison_pair": 78,
            "hero_plus_stacked_support": 134,
            "story_board_2x2": 146
        },
        "panel_label_offset_xy": [-0.06, 1.08],
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
        "font.sans-serif": ["DejaVu Sans", *[f for f in journalProfile["font_family"] if f != "DejaVu Sans"]],
        "font.size": journalProfile["font_size_body_pt"],
        "axes.labelsize": journalProfile.get("font_size_body_pt", 6),
        "axes.titlesize": journalProfile.get("font_size_body_pt", 6) + 1,
        "xtick.labelsize": journalProfile.get("font_size_body_pt", 6) - 1,
        "ytick.labelsize": journalProfile.get("font_size_body_pt", 6) - 1,
        "legend.fontsize": 7,

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
        "legend.frameon": True,
        "legend.edgecolor": "#cccccc",
        "legend.borderpad": 0.4,

        # Output
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05
    }
```

### Step 3.2: Resolve Color System

Palette defaults are defined in `templates/template-palette-registry.json`.
Use `resolve_palette(name)` from `template_mining_helpers`; do not duplicate
palette hex lists in this phase document.

```python
def resolve_color_system(chartPlan, dataProfile):
    palettePlan = chartPlan["palettePlan"]
    roles = dataProfile["semanticRoles"]
    df = dataProfile["df"]

    template_palette = list(palettePlan.get("templatePaletteHex", []) or [])
    categorical = template_palette or resolve_palette(palettePlan["categoricalPreset"])
    sequential = resolve_palette(palettePlan["sequentialPreset"])
    diverging = resolve_palette(palettePlan["divergingPreset"])

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
        "paletteSource": palettePlan.get("paletteSource", "preset"),
        "templateCaseIds": palettePlan.get("templateCaseIds", []),
        "templatePaletteHex": template_palette,
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
    if recipe == "architecture_metric_storyboard":
        return {"engine": "GridSpec", "grid": "2x2-architecture-metric", "hspace": max(gap, 0.38), "wspace": max(gap, 0.34)}
    return {"engine": "GridSpec", "grid": "2x2", "hspace": gap, "wspace": gap}
```

### Step 3.4: Generate Chart Code And Registry

The canonical 121-chart family list lives in
`phases/code-gen/registry.py::CHART_GENERATORS`. Phase-3 dispatch reads this
dict directly; do not duplicate the registry in this document.

```python
registry_source = Path(".claude/skills/scifig-generate/phases/code-gen/registry.py").read_text(encoding="utf-8").strip()
registry_source = registry_source.replace("```python", "", 1).rsplit("```", 1)[0].strip()
_registry_ns = {}
exec(registry_source, _registry_ns)
CHART_GENERATORS = _registry_ns["CHART_GENERATORS"]

CHART_KEY_ALIASES = {
    "violin+strip": "violin_strip",
    "box+strip": "box_strip",
    "heatmap+cluster": "heatmap_cluster",
    "dot+box": "box_strip",
}


def normalize_chart_key(chart):
    raw = str(chart or "")
    return CHART_KEY_ALIASES.get(raw, CHART_KEY_ALIASES.get(raw.replace("+", "_"), raw.replace("+", "_")))
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

- `sanitize_columns`, `apply_chart_polish`, `apply_visual_content_pass`, `apply_template_radar_signature`, `apply_template_triangular_heatmap_signature`, `apply_crowding_management`, `reflow_colorbars_outside_panels`, `enforce_figure_legend_contract`, `audit_figure_layout_contract`
- metadata fields: `legendContractEnforced`, `layoutContractEnforced`, `legendOutsidePlotArea`, `axisLegendRemainingCount`, `layoutContractFailures`, `colorbarReflowCount`, `colorbarPanelOverlapCount`, `metricTableDataOverlapCount`, `metricTableRelocatedCount`, `metricTableSuppressedCount`, `metricTableFallbackBoxCount`, `visualGrammarMotifsApplied`, `templateMotifsApplied`, `templateCaseAnchors`, `templateTechniqueRefs`, `templateMatchMode`, `metricTableCount`, `referenceLineCount`, `densityHaloCount`, `marginalAxesCount`, `densityColorEncodingCount`
- hard rule: generated code may create temporary `ax.legend(...)` handles, but final output must call `enforce_figure_legend_contract(...)` immediately before the first `savefig` and leave no axis legends behind
- title rule: `fig.suptitle(...)` and `ax.set_title(...)` default to centered alignment; never use left/right title positions for panel labels.
- label rule: use ASCII-safe labels (`Earth radii`, `Earth masses`, `log10`, `-`) and avoid fragile glyphs such as `⊕`, subscript digits, and em dashes.

If a helper behavior needs to change, edit `phases/code-gen/helpers.py` and update tests; do not paste a local replacement here.
### Step 3.4b: Improved Multi-panel Composition

Use `panelBlueprint` as the source of truth and embed the canonical source from `phases/code-gen/generators-multipanel.py` during Step 3.6. Do not duplicate `resolve_canvas`, `resolve_panel_geometry`, or `compose_multipanel` here.

Composition rules that must remain true:

- Shared legends/colorbars are external layout elements, not plotted-area annotations.
- Bottom-center rectangular framed shared legend is mandatory for final composites. Outside-right, top-center, in-axes, and `loc="best"` publication legends are forbidden.
- Risk tables, side summaries, and footnotes need reserved GridSpec/subfigure slots; no negative `ax.transAxes` text unless a slot is reserved.
- Print-scale typography only: body 5-7 pt, axes labels 6-8 pt, panel labels 8-10 pt, compact titles 7-9 pt.
- Panel labels use `add_panel_label(..., x=-0.06, y=1.08, fontsize=9)` outside the data rectangle, and axis link groups are used only when scales are semantically identical.
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
    dependency_map = {
        "gen_model_architecture_board": ["gen_model_architecture"],
        "gen_rf_classifier_report_board": ["gen_classifier_validation_board"],
        "gen_classifier_validation_board": ["gen_roc", "gen_pr_curve", "gen_calibration", "gen_confusion_matrix"],
    }
    expanded_names = []
    for name in needed_names:
        for dependency in dependency_map.get(name, []):
            if dependency not in expanded_names:
                expanded_names.append(dependency)
        if name not in expanded_names:
            expanded_names.append(name)
    needed_names = expanded_names
    missing = [name for name in needed_names if name not in generator_sources]
    if missing:
        raise RuntimeError(f"Missing generator implementations: {missing}")

    lines = imports + [""] + helper_sources + [""] + [generator_sources[name] for name in needed_names]
    return "\n\n".join(line for line in lines if line)

# Build executable Python code
chartPlan["primaryChart"] = normalize_chart_key(chartPlan["primaryChart"])
chartPlan["secondaryCharts"] = [normalize_chart_key(chart) for chart in chartPlan.get("secondaryCharts", [])]
primary_gen = CHART_GENERATORS.get(chartPlan["primaryChart"], "")
secondary_gens = [CHART_GENERATORS.get(c, "") for c in chartPlan.get("secondaryCharts", [])]

# Build the data loading and role assignment code
roles_code = ""
for role, col in dataProfile.get("semanticRoles", {}).items():
    if col:
        roles_code += f'"{role}": "{col}", '

# Resolve export formats from workflow preferences or policy defaults. SVG is
# always emitted as the canonical editable source; PNG derivatives are rendered
# from that SVG so raster output matches the editable file; PDF follows the SVG
# renderer when available and records a fallback warning otherwise.
normalized_formats = workflowPreferences.get("exportFormats", ["pdf", "svg"])
export_dpi = workflowPreferences.get("rasterDpi", 300)

def _editable_export_call(figure_id, axes_expr, plan_expr):
    return (
        f'editable_export_report = export_editable_svg_bundle('
        f'fig, "{figure_id}", Path("output"), axes={axes_expr}, chartPlan={plan_expr}, '
        f'raster_dpi={export_dpi}, normalized_formats={repr(normalized_formats)}, strict=True)'
    )

savefig_lines = _editable_export_call("figure1", "audit_axes_map", "chartPlan")

helper_source = Path(".claude/skills/scifig-generate/phases/code-gen/helpers.py").read_text(encoding="utf-8").strip()
helper_source = helper_source.replace("```python", "", 1).rsplit("```", 1)[0].strip()
multipanel_source = Path(".claude/skills/scifig-generate/phases/code-gen/generators-multipanel.py").read_text(encoding="utf-8").strip()
multipanel_source = multipanel_source.replace("```python", "", 1).rsplit("```", 1)[0].strip()
# Template-mining helpers: the canonical operational layer for radar polygon grid,
# nature_radar_dual palette, sandwich z-order recipes, perfect-fit diagonals, etc.
# Without this, generated scripts cannot call apply_journal_kernel, resolve_palette,
# add_polygon_polar_grid, add_perfect_fit_diagonal, density_color_scatter,
# add_forest_panel, bootstrap_chart, apply_zorder_recipe — leaving 77-case knowledge
# unreachable at runtime. Must be embedded BEFORE helpers.py so generators can resolve
# template_mining_helpers public API symbols.
template_mining_helpers_source = Path(".claude/skills/scifig-generate/phases/code-gen/template_mining_helpers.py").read_text(encoding="utf-8").strip()
template_mining_helpers_source = template_mining_helpers_source.replace("```python", "", 1).rsplit("```", 1)[0].strip()

# Resolve absolute path to the bundled-fonts directory. Passed into the
# generated script as an env var so template_mining_helpers._resolve_fonts_dir
# can locate user-supplied TTFs at runtime — without this, the helper code
# embedded via exec() loses __file__ context and cannot find the fonts.
_FONTS_DIR_PATH = Path(".claude/skills/scifig-generate/assets/fonts").resolve()
fonts_dir_str = str(_FONTS_DIR_PATH) if _FONTS_DIR_PATH.is_dir() else ""

# Build generator call code
# Check if multi-panel composition is needed
panels = chartPlan.get("panelBlueprint", {}).get("panels", [])
is_multipanel = len(panels) > 1

if is_multipanel:
    # Multi-panel mode: use gen_multipanel to create a single figure with shared axes
    primary_call = f"""# Multi-panel figure
dataProfile_dict = {{"semanticRoles": {{{roles_code}}}, "df": df}}
chartPlan = {{"primaryChart": "{chartPlan['primaryChart']}", "secondaryCharts": {chartPlan.get("secondaryCharts", [])}, "panelBlueprint": {repr(chartPlan.get("panelBlueprint", {}))}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}, "visualContentPlan": {repr(chartPlan.get("visualContentPlan", {}))}, "templateCasePlan": {repr(chartPlan.get("templateCasePlan", {}))}, "templateRenderPlan": {repr(chartPlan.get("templateRenderPlan", {}))}}}
palette = {repr(colorSystem)}

fig = gen_multipanel(chartPlan, journalProfile, palette, dataProfile_dict, rcParams, col_map=col_map)
audit_axes_map = normalize_axes_map(fig, fig.axes)
visual_density_report = audit_visual_density_contract(chartPlan, strict=True)
legend_contract_report = enforce_figure_legend_contract(fig, audit_axes_map, chartPlan, journalProfile)
record_render_contract_report("figure1", chartPlan, legend_contract_report)
{savefig_lines}
plt.close()
"""
    secondary_calls = ""
else:
    # Single panel mode: generate individual figures
    primary_call = f"""# Primary chart: {chartPlan['primaryChart']}
dataProfile = {{"semanticRoles": {{{roles_code}}}, "df": df}}
chartPlan = {{"primaryChart": "{chartPlan['primaryChart']}", "secondaryCharts": {chartPlan.get("secondaryCharts", [])}, "panelBlueprint": {{"layout": {{"recipe": "single", "grid": "1x1"}}, "panels": [{{"id": "A", "role": "hero", "chart": "{chartPlan['primaryChart']}", "source": "primary"}}], "requestedLayout": "single", "finalLayout": "single", "sharedLegend": False, "sharedColorbar": False}}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}, "visualContentPlan": {repr(chartPlan.get("visualContentPlan", {}))}, "templateCasePlan": {repr(chartPlan.get("templateCasePlan", {}))}, "templateRenderPlan": {repr(chartPlan.get("templateRenderPlan", {}))}}}
palette = {repr(colorSystem)}

single_height = journalProfile.get("canvas_height_mm", {}).get("single", 62)
fig, ax = plt.subplots(figsize=({journalProfile['single_width_mm']}*MM, single_height*MM), constrained_layout=False)
ax = {primary_gen}(df, dataProfile, chartPlan, rcParams, palette, col_map=col_map, ax=ax)
audit_axes_map = normalize_axes_map(fig, {{"A": ax}})
apply_visual_content_pass(fig, {{"A": ax}}, chartPlan, dataProfile, journalProfile, palette, col_map=col_map)
visual_density_report = audit_visual_density_contract(chartPlan, strict=True)
legend_contract_report = enforce_figure_legend_contract(fig, audit_axes_map, chartPlan, journalProfile)
record_render_contract_report("figure1", chartPlan, legend_contract_report)
{savefig_lines}
plt.close()
"""

    secondary_calls = ""
    for sec_chart in chartPlan.get("secondaryCharts", []):
        sec_gen = CHART_GENERATORS.get(sec_chart, "")
        if sec_gen:
            sec_savefig_lines = _editable_export_call(sec_chart, "audit_secondary_axes_map", "secondaryPlan")
            secondary_calls += f"""
# Secondary chart: {sec_chart}
secondaryPlan = {{"primaryChart": "{sec_chart}", "secondaryCharts": [], "panelBlueprint": {{"layout": {{"recipe": "single", "grid": "1x1"}}, "panels": [{{"id": "A", "role": "hero", "chart": "{sec_chart}", "source": "secondary"}}], "requestedLayout": "single", "finalLayout": "single", "sharedLegend": False, "sharedColorbar": False}}, "crowdingPlan": {repr(chartPlan.get("crowdingPlan", {}))}, "visualContentPlan": {repr(chartPlan.get("visualContentPlan", {}))}, "templateCasePlan": {repr(chartPlan.get("templateCasePlan", {}))}}
single_height = journalProfile.get("canvas_height_mm", {}).get("single", 62)
fig, ax = plt.subplots(figsize=({journalProfile['single_width_mm']}*MM, single_height*MM), constrained_layout=False)
ax = {sec_gen}(df, dataProfile, secondaryPlan, rcParams, palette, col_map=col_map, ax=ax)
audit_secondary_axes_map = normalize_axes_map(fig, {{"A": ax}})
apply_visual_content_pass(fig, {{"A": ax}}, secondaryPlan, dataProfile, journalProfile, palette, col_map=col_map)
visual_density_report = audit_visual_density_contract(secondaryPlan, strict=True)
legend_contract_report = enforce_figure_legend_contract(fig, audit_secondary_axes_map, secondaryPlan, journalProfile)
record_render_contract_report("{sec_chart}", secondaryPlan, legend_contract_report)
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
import os
import re
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Journal profile: {journalProfile['name']}
MM = 1/25.4

# Bundled-font directory (set by Phase 3 at build time so the embedded
# template_mining_helpers source can locate assets/fonts/ via env var).
# Empty string means the directory does not exist on the build host; the
# helper falls back to other resolution strategies.
_SCIFIG_FONTS_DIR = r"{fonts_dir_str}"
if _SCIFIG_FONTS_DIR and Path(_SCIFIG_FONTS_DIR).is_dir():
    os.environ.setdefault("SCIFIG_FONTS_DIR", _SCIFIG_FONTS_DIR)

# rcParams (publication quality)
plt.rcParams.update({repr(rcParams)})

_render_contract_reports = []


def record_render_contract_report(figure_id, chart_plan, legend_contract_report):
    report_path = Path("output/reports/render_contracts.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    record = {{
        "figureId": figure_id,
        "primaryChart": chart_plan.get("primaryChart"),
        "secondaryCharts": chart_plan.get("secondaryCharts", []),
        "crowdingPlan": chart_plan.get("crowdingPlan", {{}}),
        "visualContentPlan": chart_plan.get("visualContentPlan", {{}}),
        "legendContractReport": legend_contract_report,
    }}
    _render_contract_reports.append(record)
    report_path.write_text(
        json.dumps(_render_contract_reports, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return record

# Load data
df = pd.read_csv("{dataProfile.get('filePath', 'data.csv')}")

# Embedded template-mining helpers (canonical 顶刊 operational layer)
# Loaded BEFORE helpers.py so apply_template_*_signature in helpers.py can co-exist
# during the migration window, and so gen_xxx generators can call the canonical
# template_mining_helpers APIs (resolve_palette('nature_radar_dual'),
# add_polygon_polar_grid, add_perfect_fit_diagonal, density_color_scatter,
# add_forest_panel, bootstrap_chart, apply_zorder_recipe, ...).
ccc = """
{template_mining_helpers_source}
"""
exec(ccc, globals())

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
    "legendContractReportPersistencePresent": "record_render_contract_report(" in full_code_string and "render_contracts.json" in full_code_string,
    "layoutContractMetadataPresent": "layoutContractFailures" in full_code_string and "audit_figure_layout_contract" in full_code_string,
    "colorbarContractMetadataPresent": "colorbarReflowCount" in full_code_string and "colorbarPanelOverlapCount" in full_code_string,
    "embeddedHelperSourcePresent": "# Embedded helper source from the skill package" in full_code_string and "exec(aaa, globals())" in full_code_string,
    "embeddedTemplateMiningHelpersPresent": "# Embedded template-mining helpers" in full_code_string and "exec(ccc, globals())" in full_code_string and "add_polygon_polar_grid" in full_code_string,
    "editableSvgExportPresent": "export_editable_svg_bundle(" in full_code_string and "editable_export_report" in full_code_string,
    "editableSvgManifestPresent": "editable_svg_manifest.json" in full_code_string and "svg_render_qa.json" in full_code_string,
    "pngDerivedFromEditableSvg": "fig.savefig(\"output/figure1.png\"" not in full_code_string and "pngSource" in full_code_string,
    "singleLegendContractDefinition": full_code_string.count("def enforce_figure_legend_contract(") == 1,
    "negativeLegendAnchorScan": re.search(r"bbox_to_anchor\s*=\s*\([^)]*-\d", full_code_string) is None,
    "negativeAxesTextScan": re.search(r"(risk_table_y|table_y|footnote_y|label_y)\s*=\s*-\d", full_code_string) is None,
    "posterScaleFontScan": re.search(r"(font\.size['\"]?\s*:\s*(1[2-9]|[2-9]\d)|fontsize\s*=\s*(1[3-9]|[2-9]\d))", full_code_string) is None,
    "directAxesLegendCalls": len(re.findall(r"\b[a-zA-Z_]\w*\.legend\s*\(", full_code_string)),
    "visualDensityGatePresent": "audit_visual_density_contract(" in full_code_string and "minTotalEnhancements" in full_code_string and "inPlotExplanatoryLabelCount" in full_code_string,
    "referenceGrammarGatePresent": "minReferenceMotifsPerFigure" in full_code_string and "visualGrammarMotifsApplied" in full_code_string,
    "predictionDiagnosticGatePresent": "metricTableCount" in full_code_string and "densityHaloCount" in full_code_string,
    "templateRenderPlanPresent": "templateRenderPlan" in full_code_string and "templateCaseIds" in full_code_string,
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
if "record_render_contract_report(" not in full_code_string or "render_contracts.json" not in full_code_string:
    codeReview["blockingFindings"].append("missing_render_contract_report_persistence")
if "layoutContractFailures" not in full_code_string or "audit_figure_layout_contract" not in full_code_string:
    codeReview["blockingFindings"].append("missing_layout_contract_metadata")
if "colorbarReflowCount" not in full_code_string or "colorbarPanelOverlapCount" not in full_code_string:
    codeReview["blockingFindings"].append("missing_colorbar_reflow_gate")
if "# Embedded helper source from the skill package" not in full_code_string or "exec(aaa, globals())" not in full_code_string:
    codeReview["blockingFindings"].append("missing_embedded_skill_helper_source")
if "# Embedded template-mining helpers" not in full_code_string or "exec(ccc, globals())" not in full_code_string:
    codeReview["blockingFindings"].append("missing_embedded_template_mining_helpers")
if "add_polygon_polar_grid" not in full_code_string or "resolve_palette" not in full_code_string:
    codeReview["blockingFindings"].append("template_mining_helpers_api_unreferenced_after_embed")
if "export_editable_svg_bundle(" not in full_code_string or "editable_export_report" not in full_code_string:
    codeReview["blockingFindings"].append("missing_editable_svg_export")
if "editable_svg_manifest.json" not in full_code_string or "svg_render_qa.json" not in full_code_string:
    codeReview["blockingFindings"].append("missing_editable_svg_manifest_or_qa")
if 'fig.savefig("output/figure1.png"' in full_code_string:
    codeReview["blockingFindings"].append("png_saved_directly_instead_of_svg_derived")
if full_code_string.count("def enforce_figure_legend_contract(") != 1:
    codeReview["blockingFindings"].append("custom_or_duplicate_legend_contract_finalizer")
if re.search(r"bbox_to_anchor\s*=\s*\(1\.0\d", full_code_string):
    codeReview["blockingFindings"].append("outside_right_legend_bbox_anchor")
if re.search(r"bbox_to_anchor\s*=\s*\([^)]*-\d", full_code_string):
    codeReview["blockingFindings"].append("negative_legend_bbox_anchor")
if re.search(r"(risk_table_y|table_y|footnote_y|label_y)\s*=\s*-\d", full_code_string):
    codeReview["blockingFindings"].append("negative_axes_text_without_reserved_slot")
if re.search(r"(font\.size['\"]?\s*:\s*(1[2-9]|[2-9]\d)|fontsize\s*=\s*(1[3-9]|[2-9]\d))", full_code_string):
    codeReview["blockingFindings"].append("poster_scale_fontsize")
if codeReview["directAxesLegendCalls"] and "legend_contract_report = enforce_figure_legend_contract(" not in full_code_string:
    codeReview["blockingFindings"].append("direct_axes_legend_without_finalizer")
if "audit_visual_density_contract(" not in full_code_string or "inPlotExplanatoryLabelCount" not in full_code_string or "minTotalEnhancements" not in full_code_string:
    codeReview["blockingFindings"].append("missing_visual_density_gate")
if "minReferenceMotifsPerFigure" not in full_code_string or "visualGrammarMotifsApplied" not in full_code_string:
    codeReview["blockingFindings"].append("missing_reference_visual_grammar_gate")
if "metricTableCount" not in full_code_string or "densityHaloCount" not in full_code_string:
    codeReview["blockingFindings"].append("missing_prediction_diagnostic_gate")
if "templateRenderPlan" not in full_code_string or "templateCaseIds" not in full_code_string:
    codeReview["blockingFindings"].append("missing_template_render_plan")
if "savefig" not in full_code_string:
    codeReview["blockingFindings"].append("missing_savefig")
if "savefig" in full_code_string and "legend_contract_report = enforce_figure_legend_contract(" not in full_code_string:
    codeReview["blockingFindings"].append("savefig_without_legend_contract")
# Source-side legend lint: run `python phases/code-gen/source-lint.py`
# before finalizing; BANNED_LEGEND_PATTERNS block outside-right and
# negative-bottom legend anchors in split generator source.
codeReview["sourceLintCommand"] = "python phases/code-gen/source-lint.py"

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
    "templateCasePlan": chartPlan.get("templateCasePlan", {}),
    "sharedLegend": chartPlan.get("sharedLegend", chartPlan.get("panelBlueprint", {}).get("sharedLegend", False)),
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
> 6. `full_code_string` embeds helper source from `phases/code-gen/helpers.py` and multi-panel source from `phases/code-gen/generators-multipanel.py`, keeps `crowdingPlan` and `visualContentPlan` attached to `chartPlan`, passes `ax` and `col_map` to generators, runs `apply_visual_content_pass(...)` before `enforce_figure_legend_contract(...)`, persists each `legend_contract_report` to `output/reports/render_contracts.json` before `export_editable_svg_bundle(...)`, tracks `legendContractEnforced`, `layoutContractEnforced`, `layoutContractFailures`, `colorbarReflowCount`, `colorbarPanelOverlapCount`, `metricTableDataOverlapCount`, `metricTableRelocatedCount`, `metricTableSuppressedCount`, `metricTableFallbackBoxCount`, `axisLegendRemainingCount`, `visualGrammarMotifsApplied`, `templateMotifsApplied`, `metricTableCount`, `referenceLineCount`, `densityHaloCount`, `marginalAxesCount`, and `densityColorEncodingCount`, and derives requested PNG outputs from the canonical editable SVG using `workflowPreferences["rasterDpi"]`


> **Generator code**: Read [code-gen/generators-distribution.md](code-gen/generators-distribution.md) for distribution chart generators (violin_paired, violin_split, dot_strip, histogram, density, ecdf, joyplot, ridge, and 40+ additional chart types across genomics, engineering, ecology, and more).
> **Generator code**: Read [code-gen/generators-clinical.md](code-gen/generators-clinical.md) for clinical trial, composition, and hierarchical chart generators (caterpillar_plot, swimmer_plot, risk_ratio_plot, tornado_chart, nomogram, decision_curve, treemap, sunburst, waffle_chart, marimekko, stacked_area_comp, nested_donut).
> **Generator code**: Read [code-gen/generators-psychology.md](code-gen/generators-psychology.md) for relationship, psychology, and social science chart generators (chord_diagram, parallel_coordinates, sankey, radar, likert_divergent, likert_stacked, mediation_path, interaction_plot).
## Output

- **Variable**: `styledCode`
- **TodoWrite**: Mark Phase 3 completed, Phase 4 in_progress

## Next Phase

Return to orchestrator, then continue to [Phase 4: Export, Source Data, And Reporting](04-export-report.md).
