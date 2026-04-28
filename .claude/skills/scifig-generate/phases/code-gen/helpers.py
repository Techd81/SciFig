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
    "legendExternalHardLimit": True,
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


def elements_overlap_axes(fig, axes):
    renderer = get_cached_renderer(fig)
    axes_boxes = {pid: ax.get_window_extent(renderer=renderer) for pid, ax in axes.items()}
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
        for mode in ["outside_right", "bottom_center", "top_center"]:
            for existing in list(fig.legends):
                existing.remove()
            legend = create_figure_legend(fig, handles, legend_labels, mode, fontsize, ncol=1)
            ok = enforce_non_overlapping_legend(fig, legend, mode, occupied_axes, retry_limit=3)
            if ok:
                return legend, mode
    fig.set_figheight(base_height)
    return None, None


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

    if legend is not None:
        renderer = get_cached_renderer(fig)
        legend_box = legend.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
        if legend_mode == "outside_right" and legend_box.x1 > 0.99:
            needed_right = max(0.20, legend_box.x0 - 0.02)
            right = min(right, needed_right)
        elif legend_mode == "bottom_center":
            bottom = max(bottom, min(0.74, legend_box.y1 + 0.035))
        elif legend_mode == "top_center":
            top = min(top, max(0.26, legend_box.y0 - 0.035))

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

    if not legend_overlaps_axes(fig, legend, occupied_axes):
        return True

    invalidate_layout_cache(fig)
    apply_subplot_margins(fig, legend_mode, has_colorbar=has_colorbar, legend=legend)
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
    if legend_overlaps_axes(fig, legend, occupied_axes):
        legend.remove()
        invalidate_layout_cache(fig)
        info["legendOutsidePlotArea"] = False
        info["layoutReflowNeeded"] = True
        return None, fallback_mode, info
    info["legendNColumns"] = 1
    info["legendOutsidePlotArea"] = True
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

    if legend_info.get("layoutReflowNeeded") and crowdingPlan.get("legendExternalHardLimit", True):
        fontsize = journalProfile.get("font_size_small_pt", 5)
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
        else:
            legend_info["legendOutsidePlotArea"] = False

    apply_subplot_margins(fig, legend_mode_used, has_colorbar=shared_colorbar_applied, legend=legend)
    if chartPlan.get("visualContentPlan", {}).get("outsideLayoutElements"):
        fig.subplots_adjust(right=min(fig.subplotpars.right, 0.78))

    get_cached_renderer(fig, force=True)
    overlap_issues = elements_overlap_axes(fig, axes)
    if overlap_issues:
        for issue in overlap_issues:
            for child in list(axes[issue["host_panel"]].get_children()):
                gid = getattr(child, "get_gid", lambda: None)()
                if gid == issue["element"]:
                    current_x = getattr(child, '_x', None) or 1.015
                    if hasattr(child, 'set_position'):
                        child.set_position((current_x + 0.05, getattr(child, '_y', 1.0)))
                    elif hasattr(child, 'set_x'):
                        child.set_x(current_x + 0.05)
        invalidate_layout_cache(fig)

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
    if overlap_issues:
        crowdingPlan["overlapIssues"] = overlap_issues
    chartPlan["crowdingPlan"] = crowdingPlan

    return {
        "droppedDirectLabelCount": dropped_direct_labels,
        "legendModeUsed": legend_mode_used,
        "sharedColorbarApplied": shared_colorbar_applied,
        "hasFigureLegend": legend is not None,
        "axisLegendRemovedCount": removed_axis_legends,
        "legendOutsidePlotArea": legend_info.get("legendOutsidePlotArea", True),
        "legendLabelsShortened": legend_info.get("legendLabelsShortened", False),
        "layoutReflowApplied": legend_info.get("layoutReflowNeeded", False) is False and legend_info.get("heightIncreased", False),
        "overlapIssues": overlap_issues,
    }
```
