"""Time-series chart generators (line/area/streamgraph/gantt/...).

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


def gen_line(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simple line chart for ordered time, dose, or index trends."""
    standalone = ax is None
    import numpy as np
    import pandas as pd
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("time") or roles.get("dose") or roles.get("condition")
    y_col = roles.get("value") or roles.get("y") or roles.get("response")
    group_col = roles.get("group")
    columns_lower = {str(c).lower(): c for c in df.columns}
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    visual_plan = chartPlan.get("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        chartPlan["visualContentPlan"] = visual_plan
    template_motifs = {
        str(m).lower()
        for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs") or [])
    } if isinstance(chartPlan, dict) else set()
    is_incremental_ml = (
        template_case.get("bundleKey") == "incremental_feature_selection_curve"
        or "incremental_feature_selection" in patterns
        or "feature_selection" in patterns
        or "incremental_feature_selection_curve" in template_motifs
        or any(token in columns_lower for token in ("n_features", "top_k", "feature_count", "ablation"))
    )

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if is_incremental_ml:
        x_candidates = ["n_features", "top_k", "feature_count", "ablation"]
        metric_candidates = ["auc", "accuracy", "f1", "r2", "score", "mae", "rmse", "mse", "error"]
        x_col = x_col or next((columns_lower[c] for c in x_candidates if c in columns_lower), None)
        y_col = y_col or next((columns_lower[c] for c in metric_candidates if c in columns_lower), None)
        group_col = group_col or roles.get("model") or roles.get("algorithm") or columns_lower.get("model") or columns_lower.get("algorithm")
    if y_col is None:
        y_col = numeric_cols[-1] if numeric_cols else None
    if y_col is None:
        raise ValueError("line requires a numeric 'value' or 'y' column")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    fallback = palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541"])
    if is_incremental_ml and x_col and x_col in df.columns:
        score_name = str(y_col).lower()
        lower_is_better = any(token in score_name for token in ("rmse", "mae", "mse", "error", "loss"))
        motif_palette = visual_plan.get("featureSelectionPalette") or palette.get("ml_model_performance_10")
        if motif_palette:
            fallback = list(motif_palette)
        color_map = _extract_colors({"categorical": fallback}, df[group_col].dropna().unique()) if group_col and group_col in df.columns else {}
        groups = [(None, df)] if not group_col or group_col not in df.columns else list(df.groupby(group_col))
        marker_cycle = list(visual_plan.get("featureSelectionMarkers") or ["o", "v", "^", "s", "D", "p", "*", "h", "X"])

        def _final_score(item):
            _, grp = item
            ordered = grp.sort_values(x_col)
            vals = pd.to_numeric(ordered[y_col], errors="coerce").dropna()
            return vals.iloc[-1] if len(vals) else np.nan

        def _decision_point(grp):
            ordered = grp.sort_values(x_col).copy()
            ordered[x_col] = pd.to_numeric(ordered[x_col], errors="coerce")
            ordered[y_col] = pd.to_numeric(ordered[y_col], errors="coerce")
            ordered = ordered.dropna(subset=[x_col, y_col])
            if len(ordered) < 3:
                return ordered.iloc[-1] if len(ordered) else None
            y_vals = ordered[y_col].to_numpy(dtype=float)
            if lower_is_better:
                gains = y_vals[:-1] - y_vals[1:]
                total_gain = y_vals[0] - np.nanmin(y_vals)
                if total_gain > 0:
                    target = y_vals[0] - total_gain * 0.95
                    matches = np.where(y_vals <= target)[0]
                    if len(matches):
                        return ordered.iloc[int(matches[0])]
            else:
                gains = y_vals[1:] - y_vals[:-1]
                total_gain = np.nanmax(y_vals) - y_vals[0]
                if total_gain > 0:
                    target = y_vals[0] + total_gain * 0.95
                    matches = np.where(y_vals >= target)[0]
                    if len(matches):
                        return ordered.iloc[int(matches[0])]
            if len(gains) == 0:
                return ordered.iloc[-1]
            positive = gains[gains > 0]
            threshold = max(float(np.nanmax(positive)) * 0.18, 1e-12) if len(positive) else 1e-12
            elbow_offset = next((idx + 1 for idx, gain in enumerate(gains) if gain <= threshold), int(np.nanargmax(y_vals) if not lower_is_better else np.nanargmin(y_vals)))
            elbow_offset = min(max(elbow_offset, 0), len(ordered) - 1)
            return ordered.iloc[elbow_offset]

        groups = sorted(groups, key=_final_score, reverse=not lower_is_better)
        if group_col and group_col in df.columns:
            color_map = {name: fallback[i % len(fallback)] for i, (name, _) in enumerate(groups)}
        decision_source = None
        for i, (name, grp) in enumerate(groups):
            ordered = grp.sort_values(x_col)
            label = "feature path" if name is None else str(name)
            is_rf = any(token in label.lower() for token in ("random forest", "rf", "rfr"))
            if decision_source is None or is_rf:
                decision_source = (label, ordered)
            ax.plot(
                ordered[x_col], ordered[y_col],
                marker="o" if is_rf else marker_cycle[i % len(marker_cycle)],
                markersize=4 if is_rf else 3,
                lw=1.9 if is_rf else 0.9,
                alpha=1.0 if is_rf else 0.74,
                color=color_map.get(name, fallback[i % len(fallback)]),
                label=label,
                zorder=4 if is_rf else 2,
                markeredgecolor="#111111" if is_rf else "white",
                markeredgewidth=0.45,
            )
        if decision_source is not None:
            decision_label, decision_grp = decision_source
            supplied_decision_x = visual_plan.get("featureSelectionDecisionX")
            if supplied_decision_x is not None and x_col in decision_grp.columns:
                decision_candidates = decision_grp.copy()
                decision_candidates["_x_numeric"] = pd.to_numeric(decision_candidates[x_col], errors="coerce")
                decision_candidates["_delta"] = (decision_candidates["_x_numeric"] - float(supplied_decision_x)).abs()
                decision_candidates = decision_candidates.dropna(subset=["_delta"])
                decision_row = decision_candidates.sort_values("_delta").iloc[0] if len(decision_candidates) else _decision_point(decision_grp)
            else:
                decision_row = _decision_point(decision_grp)
        else:
            decision_label, decision_row = "feature path", _decision_point(df)
        if decision_row is not None:
            best_x = decision_row[x_col]
            best_y = decision_row[y_col]
            ax.axvline(best_x, color="#444444", lw=0.75, ls="--", alpha=0.72, zorder=1)
            ax.axhline(best_y, color="#444444", lw=0.65, ls="--", alpha=0.48, zorder=1)
            ax.scatter([best_x], [best_y], s=42, color="#B00000", edgecolor="white", linewidth=0.55, zorder=5)
            callout_x = 0.98 if standalone else 0.04
            callout_ha = "right" if standalone else "left"
            ax.text(
                callout_x, 0.06, f"best {x_col}: {best_x:g}\n{decision_label[:14]} {best_y:.3g}",
                transform=ax.transAxes, ha=callout_ha, va="bottom", fontsize=5.2, color="#111111",
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.45, alpha=0.92),
                zorder=6,
            )
            visual_plan["featureSelectionDecisionX"] = float(best_x)
            visual_plan["featureSelectionDecisionY"] = float(best_y)
        ax.xaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25, zorder=0)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25, zorder=0)
        ax.set_xlabel(_display_col(x_col, col_map))
        ax.set_ylabel(_display_col(y_col, col_map) if standalone else "")
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            if visual_plan.get("featureSelectionLegendOutside", standalone):
                ax.figure.legend(handles, labels, loc="lower center",
                                 ncol=min(4, len(labels)), frameon=False,
                                 fontsize=5, handletextpad=0.5)
                visual_plan["externalLegend"] = True
            else:
                ax.legend(loc="upper right", ncol=min(4, len(labels)),
                          frameon=False, fontsize=5)
                visual_plan["externalLegend"] = False
        if callable(globals().get("_record_template_motif")):
            _record_template_motif(visual_plan, "incremental_feature_selection_curve")
        if callable(globals().get("_visual_count")):
            _visual_count(visual_plan, "referenceLineCount")
            _visual_count(visual_plan, "referenceLineCount")
            _visual_count(visual_plan, "sampleEncodingCount")
            _visual_count(visual_plan, "inPlotExplanatoryLabelCount")
        visual_plan["featureSelectionModelCount"] = len(groups)
        visual_plan["featureSelectionSortedByFinalScore"] = True
        visual_plan["featureSelectionPreserveZigZag"] = True
        visual_plan["rfHighlighted"] = any("rf" == str(name).lower() or "random forest" in str(name).lower() for name, _ in groups if name is not None)
        if ax.figure is not None:
            try:
                if hasattr(ax.figure, "set_layout_engine"):
                    ax.figure.set_layout_engine(None)
                else:
                    ax.figure.set_constrained_layout(False)
            except Exception:
                pass
            sp = ax.figure.subplotpars
            right_margin = 0.78 if visual_plan.get("externalLegend") else 0.94
            ax.figure.subplots_adjust(left=max(sp.left, 0.16), bottom=max(sp.bottom, 0.26), right=min(sp.right, right_margin))
    elif x_col is None:
        x_vals = np.arange(len(df))
        if group_col and group_col in df.columns:
            color_map = _extract_colors(palette, df[group_col].dropna().unique())
            for i, (name, grp) in enumerate(df.groupby(group_col)):
                ordered = grp.reset_index(drop=True)
                ax.plot(np.arange(len(ordered)), ordered[y_col], marker="o", markersize=3,
                        lw=0.9, color=color_map.get(name, fallback[i % len(fallback)]),
                        label=str(name))
        else:
            ax.plot(x_vals, df[y_col], marker="o", markersize=3, lw=0.9, color=fallback[0])
        ax.set_xlabel("Index")
    elif group_col and group_col in df.columns:
        color_map = _extract_colors(palette, df[group_col].dropna().unique())
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            ordered = grp.sort_values(x_col)
            ax.plot(ordered[x_col], ordered[y_col], marker="o", markersize=3,
                    lw=0.9, color=color_map.get(name, fallback[i % len(fallback)]),
                    label=str(name))
        ax.legend(loc="upper right", frameon=False, fontsize=5)
        ax.set_xlabel(_display_col(x_col, col_map))
    else:
        ordered = df.sort_values(x_col)
        ax.plot(ordered[x_col], ordered[y_col], marker="o", markersize=3,
                lw=0.9, color=fallback[0])
        ax.set_xlabel(_display_col(x_col, col_map))

    ax.set_ylabel(_display_col(y_col, col_map))
    if standalone:
        apply_chart_polish(ax, "line")
    return ax


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
    ax.legend(loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "stacked_area_comp")
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


# ──────────────────────────────────────────────────────────────
# Missing Generator Specs (5 charts)
# ──────────────────────────────────────────────────────────────
