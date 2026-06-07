"""Composition / hierarchical chart generators (treemap/sunburst/bar/...).

Stage-2 refactor: function bodies are byte-identical to the pre-refactor
runtime generator_sources map. Consumed via _load_generator_source_map()
source-concatenation (not standalone import); shared role/color helpers
live in generators_distribution, classifier-board helpers in generators_ml.
"""


from math import pi as _pi
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colors import TwoSlopeNorm
from matplotlib.gridspec import GridSpecFromSubplotSpec
from matplotlib.patches import Ellipse
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.optimize import curve_fit
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import gaussian_kde
from scipy.stats import norm
from sklearn.linear_model import LinearRegression
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.metrics import roc_curve, auc
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from statsmodels.nonparametric.smoothers_lowess import lowess
import math as _math
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
import squarify
import textwrap
import warnings


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


def gen_composition_dotplot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Composition dot plot: group-by-feature proportions encoded by size and color."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    feature_col = roles.get("feature_id") or roles.get("feature") or roles.get("label")
    group_col = roles.get("group") or roles.get("sample")
    value_col = roles.get("value") or roles.get("proportion") or roles.get("fraction")
    if feature_col is None or group_col is None or value_col is None:
        raise ValueError("composition_dotplot requires feature, group, and value columns")

    pivot = df.pivot_table(index=feature_col, columns=group_col, values=value_col,
                           aggfunc="sum", fill_value=0)
    features = pivot.index.tolist()
    groups = pivot.columns.tolist()
    if standalone:
        fig, ax = plt.subplots(figsize=(max(89, 8 * len(groups)) * (1 / 25.4),
                                    max(60, 5 * len(features)) * (1 / 25.4)),
                           constrained_layout=True)

    vmax = pivot.to_numpy().max() or 1
    for i, feature in enumerate(features):
        for j, group in enumerate(groups):
            value = pivot.loc[feature, group]
            ax.scatter(j, i, s=12 + 120 * value / vmax, c=value, cmap="viridis",
                       vmin=0, vmax=vmax, edgecolor="white", linewidth=0.25)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups, rotation=45, ha="right", fontsize=5)
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features, fontsize=5)
    ax.set_xlabel(_display_col(group_col, col_map))
    ax.set_ylabel(_display_col(feature_col, col_map))
    if standalone:
        apply_chart_polish(ax, "composition_dotplot")
    return ax


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


def gen_grouped_bar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Grouped bar chart with error bars: subgroups within categories.

    Each category on the x-axis contains one bar per subgroup, with SEM
    error bars.  Expects in semanticRoles: group (x-axis categories),
    subgroup (bar series within each group), and value (numeric y).
    Computes mean and SEM per cell for error bar display.  In AI/ML model
    benchmark contexts, switches to the RF-template horizontal benchmark:
    models sorted by test/validation metric, stable train/test colors, and
    Random Forest highlighted when present.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    subgroup_col = roles.get("subgroup") or roles.get("color") or roles.get("hue")
    value_col = roles.get("value") or roles.get("y")
    source_df = df.copy()
    source_subgroup_col = subgroup_col

    if group_col is None:
        raise ValueError("grouped_bar requires 'group' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)
    patterns = set(dataProfile.get("specialPatterns", []))
    visual_plan = chartPlan.setdefault("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
    domain = (dataProfile.get("domainHints", {}) or {}).get("primary", "")
    tokens = " ".join(
        [str(c).lower() for c in df.columns]
        + [str(v).lower() for v in roles.values()]
        + [str(v).lower() for v in df[group_col].dropna().unique().tolist()]
    )
    is_ml_benchmark = (
        domain == "computer_ai_ml"
        or "model_performance_benchmark" in patterns
        or "ml_model_family" in patterns
        or any(t in tokens for t in ("random forest", "randomforest", "rf", "rfr", "xgboost", "lightgbm", "gbdt", "svm", "knn"))
    )
    is_inset_heatmap_rank = (
        "inset_heatmap_bar_rank" in patterns
        or "ranked_bar_inset_heatmap" in patterns
        or "bar_rank_heatmap_inset" in patterns
        or (
            "heatmap" in tokens
            and any(t in tokens for t in ("rank", "ranking", "pearson", "correlation"))
            and not is_ml_benchmark
        )
    )
    metric_priority = ["auc", "roc_auc", "accuracy", "f1", "precision", "recall", "r2", "rmse", "mae", "mse", "error"]

    def _metric_key(value):
        return str(value).lower().replace("-", "_").replace(" ", "_")

    metric_cols = [
        col for col in df.columns
        if col not in {group_col, subgroup_col, value_col}
        and pd.api.types.is_numeric_dtype(df[col])
        and any(metric in _metric_key(col) for metric in metric_priority)
    ]
    wide_metric_cols = sorted(
        metric_cols,
        key=lambda col: next((idx for idx, metric in enumerate(metric_priority) if metric in _metric_key(col)), len(metric_priority)),
    )
    wide_metric_mode = None
    if is_ml_benchmark and value_col is None and wide_metric_cols:
        if subgroup_col and subgroup_col in df.columns:
            value_col = wide_metric_cols[0]
            wide_metric_mode = "selected_metric_column"
        else:
            plot_df = df[[group_col] + wide_metric_cols].melt(
                id_vars=[group_col],
                value_vars=wide_metric_cols,
                var_name="_metric_name",
                value_name="_metric_value",
            )
            df = plot_df
            subgroup_col = "_metric_name"
            value_col = "_metric_value"
            wide_metric_mode = "metrics_as_subgroups"

    if is_inset_heatmap_rank and standalone:
        if value_col is None:
            raise ValueError("grouped_bar inset_heatmap_bar_rank requires a numeric 'value' role")
        draw_inset_heatmap_bar_rank = globals().get("draw_inset_heatmap_bar_rank")
        if callable(draw_inset_heatmap_bar_rank):
            numeric_candidates = [
                col for col in source_df.columns
                if col not in {group_col, subgroup_col, value_col}
                and pd.api.types.is_numeric_dtype(source_df[col])
            ]
            result = draw_inset_heatmap_bar_rank(
                source_df,
                category_col=group_col,
                value_col=value_col,
                error_col=roles.get("error") if roles.get("error") in source_df.columns else None,
                heatmap_cols=numeric_candidates[:6],
                col_map=col_map,
            )
            record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
            count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
            planned = visual_plan.setdefault("templateMotifs", [])
            for motif in ("inset_heatmap_bar_rank", "inset_heatmap_colorbar"):
                if motif not in planned:
                    planned.append(motif)
                record_fn(visual_plan, motif)
            count_fn(visual_plan, "insetCount")
            count_fn(visual_plan, "colorbarSlotCount")
            count_fn(visual_plan, "sampleEncodingCount")
            visual_plan["templateMatchMode"] = "case_027_inset_heatmap_bar_rank"
            visual_plan["rankedBarInsetHeatmapCategories"] = int(result.get("bar_count", 0))
            visual_plan["rankedBarInsetHeatmapSamples"] = int(result.get("sample_point_count", 0))
            return result["axis"]

    if subgroup_col is None or value_col is None:
        raise ValueError("grouped_bar requires 'subgroup' and 'value' in semanticRoles, or AI/ML wide metric columns")

    categories = df[group_col].dropna().unique().tolist()
    subgroups = df[subgroup_col].dropna().unique().tolist()
    n_sub = len(subgroups)
    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])

    if is_ml_benchmark:
        metric_col = roles.get("metric")
        plot_df = df.copy()
        metric_label = value_col
        higher_is_better = True

        def _is_rf_label(value):
            label = str(value).lower().replace("-", " ").replace("_", " ")
            collapsed = label.replace(" ", "")
            return "random forest" in label or collapsed in {"rf", "rfr", "randomforest"} or collapsed.startswith("rf")

        def _wrap_model_label(value, width=24, max_lines=2):
            text = str(value).strip()
            if len(text) <= width:
                return text
            words = text.replace("_", " ").split()
            lines = []
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if len(candidate) <= width or not current:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
                if len(lines) >= max_lines:
                    break
            if current and len(lines) < max_lines:
                lines.append(current)
            if not lines:
                lines = [text[:width]]
            original_joined = " ".join(lines)
            if len(original_joined) < len(text):
                lines[-1] = lines[-1][:max(3, width - 3)].rstrip() + "..."
            return "\n".join(lines[:max_lines])

        def _compact_label(value, width=22):
            text = str(value).strip()
            return text if len(text) <= width else text[:max(3, width - 3)].rstrip() + "..."
        visual_plan = chartPlan.setdefault("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
        priority_terms = ("test", "valid", "validation", "cv", "external")
        metric_table_rows = []

        def _format_metric_value(value):
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return str(value)
            if not np.isfinite(numeric):
                return ""
            return f"{numeric:.3f}" if abs(numeric) < 10 else f"{numeric:.3g}"

        def _metric_display(value):
            key = _metric_key(value)
            aliases = {
                "roc_auc": "ROC AUC",
                "accuracy": "Acc.",
                "precision": "Prec.",
                "recall": "Rec.",
                "rmse": "RMSE",
                "mae": "MAE",
                "mse": "MSE",
                "auc": "AUC",
                "f1": "F1",
                "r2": "R2",
            }
            for token, label in aliases.items():
                if token in key:
                    return label
            label = str(value).replace("_", " ").replace("-", " ").strip()
            return label.upper() if len(label) <= 8 else label[:10].rstrip()
        if metric_col and metric_col in plot_df:
            metric_values = plot_df[metric_col].astype(str).str.lower()
            selected_metric = next((m for m in metric_priority if metric_values.str.contains(m, regex=False).any()), None)
            if selected_metric:
                plot_df = plot_df[metric_values.str.contains(selected_metric, regex=False)]
                metric_label = selected_metric.upper()
                higher_is_better = selected_metric not in {"rmse", "mae", "mse", "error"}
        elif wide_metric_mode == "selected_metric_column":
            metric_label = str(value_col).upper()
            higher_is_better = not any(metric in _metric_key(value_col) for metric in ("rmse", "mae", "mse", "error"))
        elif wide_metric_mode == "metrics_as_subgroups":
            metric_label = "Metric score"
            higher_is_better = True

        summary_metric_cols = []
        for candidate in ([value_col] if value_col in source_df.columns else []) + wide_metric_cols:
            if (
                candidate in source_df.columns
                and pd.api.types.is_numeric_dtype(source_df[candidate])
                and any(metric in _metric_key(candidate) for metric in metric_priority)
                and candidate not in summary_metric_cols
            ):
                summary_metric_cols.append(candidate)

        subgroup_labels = [str(s).lower() for s in subgroups]
        if wide_metric_mode == "metrics_as_subgroups":
            priority_subgroups = subgroups[:1]
        else:
            priority_subgroups = [
                subgroups[i] for i, label in enumerate(subgroup_labels)
                if any(term in label for term in priority_terms)
            ] or subgroups[-1:]

        score_by_category = {}
        for cat in categories:
            cell = plot_df[plot_df[group_col] == cat]
            priority_cell = cell[cell[subgroup_col].isin(priority_subgroups)]
            score_source = priority_cell if len(priority_cell) else cell
            vals = pd.to_numeric(score_source[value_col], errors="coerce").dropna()
            score_by_category[cat] = vals.mean() if len(vals) else np.nan
        categories = sorted(
            categories,
            key=lambda c: np.nan_to_num(score_by_category.get(c), nan=-np.inf if higher_is_better else np.inf),
            reverse=higher_is_better,
        )
        if summary_metric_cols and categories and group_col in source_df.columns:
            table_source = source_df[source_df[group_col] == categories[0]]
            if source_subgroup_col and source_subgroup_col in table_source.columns:
                split_labels = table_source[source_subgroup_col].astype(str).str.lower()
                for term in ("external", "test", "valid", "validation", "cv"):
                    split_match = split_labels.str.contains(term, regex=False)
                    if split_match.any():
                        table_source = table_source[split_match]
                        break
            for metric_name in summary_metric_cols[:4]:
                values = pd.to_numeric(table_source[metric_name], errors="coerce").dropna()
                if len(values):
                    metric_table_rows.append((_metric_display(metric_name), _format_metric_value(values.mean())))

        max_model_label_len = max([len(str(c)) for c in categories] or [0])
        if standalone:
            fig_for_size = ax.figure
            target_width_mm = 112 if max_model_label_len > 26 or n_sub > 4 else 100
            target_height_mm = max(68, 12 * len(categories) + 22 + (10 if n_sub > 4 else 0))
            fig_for_size.set_size_inches(target_width_mm / 25.4, target_height_mm / 25.4, forward=True)

        split_colors = {
            "train": "#F6CFA3",
            "training": "#F6CFA3",
            "test": "#9BCBEB",
            "testing": "#9BCBEB",
            "valid": "#CFE8CF",
            "validation": "#CFE8CF",
            "cv": "#CFE8CF",
            "external": "#B7C9E2",
        }
        bar_height = min(0.78 / max(n_sub, 1), 0.26)
        y = np.arange(len(categories))
        best_index = 0 if categories else None
        best_score = score_by_category.get(categories[0]) if categories else None

        for si, sub in enumerate(subgroups):
            means, sems = [], []
            for cat in categories:
                cell = pd.to_numeric(
                    plot_df[(plot_df[group_col] == cat) & (plot_df[subgroup_col] == sub)][value_col],
                    errors="coerce",
                ).dropna()
                means.append(cell.mean() if len(cell) > 0 else np.nan)
                sems.append(cell.sem() if len(cell) > 1 else 0)
            offset = (si - (n_sub - 1) / 2) * bar_height
            label = str(sub)
            color = split_colors.get(label.lower(), colors[si % len(colors)])
            for yi, cat, mean, sem in zip(y + offset, categories, means, sems):
                if np.isnan(mean):
                    continue
                is_rf = _is_rf_label(cat)
                ax.barh(
                    yi,
                    mean,
                    height=bar_height,
                    xerr=sem,
                    color=color,
                    edgecolor="#111111" if is_rf else "white",
                    linewidth=0.85 if is_rf else 0.35,
                    capsize=2,
                    error_kw=dict(linewidth=0.5),
                    label=label if yi == y[0] + offset else "_nolegend_",
                    zorder=3 if is_rf else 2,
                )

        ax.set_yticks(y)
        wrapped_labels = [_wrap_model_label(c, width=24 if len(categories) <= 7 else 20) for c in categories]
        ax.set_yticklabels(wrapped_labels, fontsize=4.8 if max_model_label_len > 28 else 5)
        for tick, cat in zip(ax.get_yticklabels(), categories):
            if _is_rf_label(cat):
                tick.set_fontweight("bold")
                tick.set_color("#111111")
        ax.invert_yaxis()
        ax.set_xlabel(metric_label)
        ax.set_ylabel("Model" if standalone else "")
        ax.xaxis.grid(True, linestyle="--", linewidth=0.35, alpha=0.45, zorder=0)
        ax.set_axisbelow(True)
        if metric_table_rows:
            finite_values = pd.to_numeric(plot_df[value_col], errors="coerce").dropna()
            if len(finite_values):
                current_left, current_right = ax.get_xlim()
                max_value = float(finite_values.max())
                if np.isfinite(max_value) and max_value > 0:
                    ax.set_xlim(left=current_left, right=max(current_right, max_value / 0.68))
            add_metric_table = globals().get("_add_metric_table")
            record_template_motif = globals().get("_record_template_motif")
            if callable(add_metric_table):
                table = add_metric_table(ax, metric_table_rows, visual_plan, loc="sidecar_right")
                if table is not None:
                    enhancements = visual_plan.setdefault("appliedEnhancements", [])
                    if "model_benchmark_metric_table" not in enhancements:
                        enhancements.append("model_benchmark_metric_table")
                    if callable(record_template_motif):
                        record_template_motif(visual_plan, "ml_model_performance_triptych")
        fig_for_margin = ax.figure
        if fig_for_margin is not None:
            try:
                if hasattr(fig_for_margin, "set_layout_engine"):
                    fig_for_margin.set_layout_engine(None)
                else:
                    fig_for_margin.set_constrained_layout(False)
            except Exception:
                pass
            sp = fig_for_margin.subplotpars
            left_margin = min(0.46, max(0.22, 0.16 + min(max_model_label_len, 54) * 0.0052))
            bottom_margin = 0.26 if n_sub > 4 else 0.22
            fig_for_margin.subplots_adjust(
                left=max(sp.left, left_margin),
                bottom=max(sp.bottom, bottom_margin),
                right=min(sp.right, 0.94),
            )
        if best_index is not None and best_score is not None and not np.isnan(best_score):
            if metric_table_rows and _is_rf_label(categories[best_index]):
                best_label = "RF"
            elif _is_rf_label(categories[best_index]):
                best_label = "Random Forest"
            else:
                best_label = _compact_label(categories[best_index], 14 if metric_table_rows else 18)
            best_note = f"best: {best_label}"
            if standalone:
                ax.set_title(f"Model benchmark | {best_note}", loc="left", fontsize=7, fontweight="bold", pad=6)
            else:
                note_x, note_y = (0.70, 0.34) if metric_table_rows else (0.02, 0.06)
                ax.text(
                    note_x,
                    note_y,
                    best_note,
                    transform=ax.transAxes,
                    fontsize=5,
                    ha="left",
                    va="bottom",
                    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#333333", linewidth=0.35, alpha=0.88),
                    zorder=8,
                )
        if standalone:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                legend = ax.figure.legend(
                    handles,
                    [_compact_label(label, 18) for label in labels],
                    loc="lower center",
                    bbox_to_anchor=(0.5, 0.025),
                    ncol=min(n_sub, 6),
                    fontsize=4.8,
                    frameon=True,
                    fancybox=True,
                    borderpad=0.25,
                    handlelength=1.1,
                    columnspacing=0.7,
                )
                legend.set_gid("scifig_shared_legend")
                legend.get_frame().set_linewidth(0.35)
                legend.get_frame().set_edgecolor("#333333")
                legend.get_frame().set_alpha(0.94)
        else:
            ax.legend(frameon=False, fontsize=4.8, ncol=min(n_sub, 4))
        if standalone:
            apply_chart_polish(ax, "grouped_bar")
        return ax

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

    # Zero divider for diverging Likert — delegate to template_mining_helpers when reachable
    canonical_zero_ref = globals().get("add_zero_reference")
    if canonical_zero_ref is not None:
        try:
            canonical_zero_ref(ax, axis="x", color="black", lw=0.6, ls="-", zorder=3)
        except Exception:
            ax.axvline(0, color="black", linewidth=0.6, linestyle="-", zorder=3)
    else:
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
    ax.legend(handles=handles, loc="upper center", ncol=n_cats,
              frameon=False, fontsize=5, bbox_to_anchor=(0.5, 1.02))
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

    ax.legend(loc="upper center", ncol=n_cats, frameon=False, fontsize=5,
              bbox_to_anchor=(0.5, 1.02))
    if standalone:
        apply_chart_polish(ax, "likert_stacked")
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
    ax.legend(handles, [str(c) for c in categories], loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "marimekko")
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
    ax.legend(handles, [str(l) for l in outer_labels], loc="upper right", frameon=False, fontsize=5)
    ax.set_aspect("equal")
    if standalone:
        apply_chart_polish(ax, "nested_donut")
    return ax


def gen_pareto_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pareto chart or optimization Pareto tradeoff board.

    Default mode is the classical categorical Pareto chart: bars sorted
    descending with a cumulative-percentage line.  When templateCasePlan or
    specialPatterns indicate PSO/NSGA/Pareto/multi-objective optimization and
    two numeric objective columns are available, this renders a tradeoff
    scatter with Pareto / optimal points highlighted from supplied flags or
    ranks.

    Expects in semanticRoles: category (categorical column) and optionally
    value for categorical mode; x/y or objective_1/objective_2 for
    optimization mode.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    cat_col = roles.get("category") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    lower_cols = {str(c).lower(): c for c in df.columns}
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    optimization_tokens = {
        "pareto", "optimization", "optimisation", "multiobjective",
        "multi_objective", "pso", "nsga", "tradeoff", "trade_off",
    }
    is_optimization_pareto = (
        template_case.get("bundleKey") in {"pso_shap_optimization_framework", "materials_model_explain_optimize"}
        or bool(optimization_tokens & patterns)
        or any(token in " ".join(lower_cols.keys()) for token in ("pareto", "objective", "optimal", "optimization", "rank"))
    )

    def _first_existing(candidates):
        for candidate in candidates:
            if candidate and candidate in df.columns:
                return candidate
            if candidate and str(candidate).lower() in lower_cols:
                return lower_cols[str(candidate).lower()]
        return None

    objective_x = _first_existing([
        roles.get("objective_1"), roles.get("objective_x"), roles.get("x"),
        roles.get("score"), roles.get("performance"), "objective_1",
        "objective1", "obj1", "accuracy", "auc", "f1", "r2", "score",
        "performance", "utility", "benefit",
    ])
    objective_y = _first_existing([
        roles.get("objective_2"), roles.get("objective_y"), roles.get("y"),
        roles.get("cost"), roles.get("complexity"), "objective_2",
        "objective2", "obj2", "cost", "latency", "complexity", "rmse",
        "mae", "loss", "error", "time", "size",
    ])
    if objective_x == objective_y:
        objective_y = None
    if (objective_x is None or objective_y is None) and len(numeric_cols) >= 2:
        candidates = [c for c in numeric_cols if str(c).lower() not in {"rank", "iteration", "seed"}]
        if objective_x is None and candidates:
            objective_x = candidates[0]
        if objective_y is None:
            objective_y = next((c for c in candidates if c != objective_x), None)

    if is_optimization_pareto and objective_x and objective_y:
        if standalone:
            fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 72 * (1 / 25.4)),
                               constrained_layout=True)

        plot_df = df[[objective_x, objective_y]].copy()
        for optional in ("rank", "pareto_flag", "optimal_flag", "iteration", "candidate_id", "candidate"):
            col = roles.get(optional) or lower_cols.get(optional)
            if col and col in df.columns and col not in plot_df.columns:
                plot_df[col] = df[col]
        rank_col = roles.get("rank") or lower_cols.get("rank")
        flag_col = (
            roles.get("pareto_flag") or roles.get("optimal_flag")
            or _first_existing(["pareto_flag", "is_pareto", "pareto", "optimal_flag", "optimal", "non_dominated"])
        )
        candidate_col = roles.get("candidate_id") or roles.get("candidate") or lower_cols.get("candidate_id") or lower_cols.get("candidate")
        iter_col = roles.get("iteration") or lower_cols.get("iteration")

        plot_df["_scifig_source_index"] = plot_df.index
        plot_df[objective_x] = pd.to_numeric(plot_df[objective_x], errors="coerce")
        plot_df[objective_y] = pd.to_numeric(plot_df[objective_y], errors="coerce")
        plot_df = plot_df.dropna(subset=[objective_x, objective_y]).reset_index(drop=True)
        if plot_df.empty:
            raise ValueError("pareto_chart optimization mode requires finite objective values")
        source_index = plot_df["_scifig_source_index"]

        if rank_col and rank_col in df.columns:
            rank_values = pd.to_numeric(df.loc[source_index, rank_col], errors="coerce").reset_index(drop=True)
        elif rank_col and rank_col in plot_df.columns:
            rank_values = pd.to_numeric(plot_df[rank_col], errors="coerce")
        else:
            rank_values = pd.Series(np.nan, index=plot_df.index)
        color_values = rank_values.where(
            rank_values.notna(),
            pd.Series(np.arange(len(plot_df)), index=rank_values.index),
        )
        sc = ax.scatter(
            plot_df[objective_x], plot_df[objective_y],
            c=color_values, cmap="viridis_r", s=26,
            alpha=0.72, edgecolor="white", linewidth=0.35,
            zorder=3, label="Candidates",
        )
        if standalone:
            cbar = ax.figure.colorbar(sc, ax=ax, shrink=0.72, pad=0.02)
            cbar.set_label("Rank" if rank_values.notna().any() else "Candidate index")

        highlight_mask = pd.Series(False, index=plot_df.index)
        if flag_col and flag_col in df.columns:
            raw_flag = df.loc[source_index, flag_col].reset_index(drop=True)
            if pd.api.types.is_numeric_dtype(raw_flag):
                highlight_mask = pd.to_numeric(raw_flag, errors="coerce").fillna(0) > 0
            else:
                highlight_mask = raw_flag.astype(str).str.lower().isin({"true", "1", "yes", "pareto", "optimal", "front"})
        elif rank_values.notna().any():
            best_rank = float(rank_values.min())
            highlight_mask = rank_values <= best_rank + max(2.0, abs(best_rank) * 0.05)

        if bool(highlight_mask.any()):
            front = plot_df.loc[highlight_mask].copy().sort_values(objective_x)
            ax.plot(front[objective_x], front[objective_y], color="#B00000", lw=1.0,
                    alpha=0.86, zorder=4, label="Pareto / top rank")
            ax.scatter(front[objective_x], front[objective_y], s=58, marker="D",
                       facecolor="#B00000", edgecolor="white", linewidth=0.55,
                       zorder=5)
            if rank_values.notna().any():
                best_idx = int(rank_values.idxmin())
            else:
                best_idx = int(front.index[0])
            best_x = plot_df.loc[best_idx, objective_x]
            best_y = plot_df.loc[best_idx, objective_y]
            source_best_idx = plot_df.loc[best_idx, "_scifig_source_index"]
            best_label = str(df.loc[source_best_idx, candidate_col]) if candidate_col and candidate_col in df.columns else "best"
            ax.annotate(
                f"{best_label}\n{objective_x}={best_x:.3g}\n{objective_y}={best_y:.3g}",
                xy=(best_x, best_y), xytext=(0.05, 0.95),
                textcoords=ax.transAxes, ha="left", va="top", fontsize=5.1,
                arrowprops=dict(arrowstyle="-", color="#B00000", lw=0.65),
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )
        else:
            ax.text(
                0.05, 0.95, f"tradeoff cloud\nn={len(plot_df)}\nno Pareto flag",
                transform=ax.transAxes, ha="left", va="top", fontsize=5.1,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )

        if iter_col and iter_col in df.columns:
            iter_vals = pd.to_numeric(df.loc[source_index, iter_col], errors="coerce").reset_index(drop=True)
            if iter_vals.notna().any():
                early = iter_vals <= iter_vals.quantile(0.25)
                late = iter_vals >= iter_vals.quantile(0.75)
                ax.scatter(plot_df.loc[early, objective_x], plot_df.loc[early, objective_y],
                           s=18, facecolor="none", edgecolor="#777777", linewidth=0.45,
                           alpha=0.7, zorder=2, label="Early search")
                ax.scatter(plot_df.loc[late, objective_x], plot_df.loc[late, objective_y],
                           s=36, facecolor="none", edgecolor="#111111", linewidth=0.65,
                           alpha=0.85, zorder=4, label="Late search")

        y_name = str(objective_y).lower()
        if any(token in y_name for token in ("cost", "loss", "error", "rmse", "mae", "latency", "complexity", "time")):
            ax.annotate("better", xy=(0.96, 0.08), xytext=(0.80, 0.24),
                        xycoords="axes fraction", textcoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color="#555555", lw=0.65),
                        ha="center", va="center", fontsize=5.0, color="#333333")
        else:
            ax.annotate("better", xy=(0.96, 0.92), xytext=(0.80, 0.76),
                        xycoords="axes fraction", textcoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color="#555555", lw=0.65),
                        ha="center", va="center", fontsize=5.0, color="#333333")

        ax.set_xlabel(display_label(objective_x, col_map) if col_map else str(objective_x))
        ax.set_ylabel(display_label(objective_y, col_map) if (standalone and col_map) else (str(objective_y) if standalone else ""))
        ax.xaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25, zorder=0)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25, zorder=0)
        if standalone:
            apply_chart_polish(ax, "pareto_chart")
        return ax

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


def gen_stacked_bar_comp(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stacked composition bar chart with optional within-bar normalization."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("sample") or roles.get("group")
    stack_col = roles.get("stack") or roles.get("category") or roles.get("feature_id")
    value_col = roles.get("value") or roles.get("proportion") or roles.get("count")
    if x_col is None or stack_col is None or value_col is None:
        raise ValueError("stacked_bar_comp requires x/group, stack/category, and value columns")

    pivot = df.pivot_table(index=x_col, columns=stack_col, values=value_col,
                           aggfunc="sum", fill_value=0)
    row_sums = pivot.sum(axis=1).replace(0, 1)
    if row_sums.max() > 1.5:
        pivot = pivot.div(row_sums, axis=0)
    categories = pivot.columns.tolist()
    color_map = _extract_colors(palette, categories)
    if standalone:
        fig, ax = plt.subplots(figsize=(max(89, 7 * len(pivot)) * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    bottom = np.zeros(len(pivot))
    x = np.arange(len(pivot))
    for cat in categories:
        vals = pivot[cat].values
        ax.bar(x, vals, bottom=bottom, color=color_map.get(cat, "#999999"),
               edgecolor="white", linewidth=0.35, width=0.72, label=str(cat))
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index.astype(str), rotation=45, ha="right", fontsize=5)
    ax.set_ylabel("Proportion" if pivot.to_numpy().max() <= 1.0 else _display_col(value_col, col_map))
    ax.legend(loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "stacked_bar_comp")
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
    ax.legend(handles, [str(c) for c in categories], loc="upper right", frameon=False, fontsize=5)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "waffle_chart")
    return ax
