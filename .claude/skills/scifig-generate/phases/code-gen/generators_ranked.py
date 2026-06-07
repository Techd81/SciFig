"""Ranked-bar / lollipop / dotplot generators.

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
    # "Treat none" reference at y=0 — delegate to template_mining_helpers when reachable
    canonical_zero_ref = globals().get("add_zero_reference")
    if canonical_zero_ref is not None:
        try:
            canonical_zero_ref(ax, axis="y", color="#999999", lw=0.5, ls=":", zorder=5)
            # Register legend entry via proxy (canonical helper has no label kwarg)
            ax.plot([], [], color="#999999", lw=0.5, ls=":", label="Treat none")
        except Exception:
            ax.axhline(0, color="#999999", lw=0.5, ls=":", label="Treat none")
    else:
        ax.axhline(0, color="#999999", lw=0.5, ls=":", label="Treat none")

    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_ylim(-0.05, None)
    if standalone:
        apply_chart_polish(ax, "decision_curve")
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
    # Center divider — delegate to template_mining_helpers when reachable
    canonical_zero_ref = globals().get("add_zero_reference")
    if canonical_zero_ref is not None:
        try:
            canonical_zero_ref(ax, axis="x", color="black", lw=0.6, ls="-", zorder=1)
        except Exception:
            ax.axvline(0, color="black", lw=0.6)
    else:
        ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel(value_col)
    if standalone:
        apply_chart_polish(ax, "diverging_bar")
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
    value_col = roles.get("value") or roles.get("shap_value") or roles.get("effect")
    feature_col = roles.get("feature_id") or roles.get("y")
    feature_value_col = roles.get("feature_value") or roles.get("color") or roles.get("hue")
    importance_col = roles.get("importance") or roles.get("feature_importance") or roles.get("gain") or roles.get("weight")
    category_col = roles.get("category") or roles.get("feature_group") or roles.get("class")
    row_col = roles.get("row") or roles.get("variable_x") or roles.get("source") or roles.get("x")
    col_col = roles.get("column") or roles.get("col") or roles.get("variable_y") or roles.get("target") or roles.get("y")
    correlation_value_col = (
        roles.get("correlation")
        or roles.get("corr")
        or roles.get("pearson_r")
        or roles.get("spearman_r")
        or roles.get("r")
        or roles.get("value")
    )
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    visual_plan = chartPlan.get("visualContentPlan", {})
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        chartPlan["visualContentPlan"] = visual_plan
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    template_motifs = {str(m).lower() for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs") or [])}
    is_shap_beeswarm = (
        template_case.get("bundleKey") == "rf_feature_importance_shap"
        or "shap_composite" in patterns
        or "ml_explainability" in patterns
        or "lollipop_shap_beeswarm_board" in patterns
        or "shap_bar_pie_summary_board" in patterns
        or "shap_bar_beeswarm_inset_pie" in patterns
        or "lollipop_shap_beeswarm_board" in template_motifs
        or "shap_bar_pie_summary_board" in template_motifs
        or "shap_bar_beeswarm_inset_pie" in template_motifs
        or "shap_value" in {str(c).lower() for c in df.columns}
    )

    if is_shap_beeswarm and feature_col and value_col and feature_col in df.columns and value_col in df.columns:
        use_lollipop_shap_beeswarm_board = (
            standalone
            and (
                visual_plan.get("useLollipopShapBeeswarmBoard")
                or "lollipop_shap_beeswarm_board" in template_motifs
                or "lollipop_shap_beeswarm_board" in patterns
            )
        )
        if use_lollipop_shap_beeswarm_board:
            draw_fn = globals().get("draw_lollipop_shap_beeswarm_board")
            if draw_fn is not None:
                result = draw_fn(
                    df,
                    feature_col,
                    value_col,
                    importance_col=importance_col if importance_col in df.columns else None,
                    feature_value_col=feature_value_col if feature_value_col in df.columns else None,
                    top_n=visual_plan.get("shapTopN", 15),
                    width_ratios=visual_plan.get("lollipopShapWidthRatios", [1.0, 2.5]),
                    figsize=tuple(visual_plan.get("lollipopShapFigsize", [12.0, 6.0])),
                    wspace=visual_plan.get("lollipopShapWspace", 0.05),
                    adjust=visual_plan.get("lollipopShapSubplotsAdjust", {"left": 0.15, "right": 0.90, "top": 0.90, "bottom": 0.15}),
                    stem_color=visual_plan.get("lollipopStemColor", "grey"),
                    point_color=visual_plan.get("lollipopPointColor", "teal"),
                    cmap=visual_plan.get("lollipopShapColormap", "coolwarm"),
                    col_map=col_map,
                    zero_reference_fn=globals().get("add_zero_reference"),
                )
                count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
                record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
                planned_motifs = visual_plan.setdefault("templateMotifs", [])
                for motif in ("lollipop_shap_beeswarm_board", "shared_feature_axis", "shap_summary_beeswarm"):
                    if motif not in planned_motifs:
                        planned_motifs.append(motif)
                    record_fn(visual_plan, motif)
                count_fn(visual_plan, "lollipopLayerCount")
                count_fn(visual_plan, "shapBeeswarmCount")
                count_fn(visual_plan, "referenceLineCount")
                count_fn(visual_plan, "zeroReferenceLineCount")
                count_fn(visual_plan, "sampleEncodingCount")
                visual_plan["sharedFeatureOrdering"] = True
                visual_plan["featureValueColorEncoded"] = bool(feature_value_col and feature_value_col in df.columns)
                visual_plan["topFeatureLimit"] = result.get("top_n")
                visual_plan["shapCompositeLayout"] = "subplots(1,2)"
                visual_plan["lollipopShapPanelCount"] = 2
                visual_plan["lollipopShapWidthRatios"] = list(result.get("width_ratios", [1.0, 2.5]))
                visual_plan["templateMatchMode"] = "case_021_lollipop_shap_beeswarm_board"
                return result["ax_beeswarm"]
        use_shap_bar_pie_summary_board = (
            standalone
            and (
                visual_plan.get("useShapBarPieSummaryBoard")
                or "shap_bar_pie_summary_board" in template_motifs
                or "shap_bar_pie_summary_board" in patterns
            )
        )
        if use_shap_bar_pie_summary_board:
            draw_fn = globals().get("draw_shap_bar_pie_summary_board")
            if draw_fn is not None:
                result = draw_fn(
                    df,
                    feature_col,
                    value_col,
                    feature_value_col=feature_value_col if feature_value_col in df.columns else None,
                    category_col=category_col if category_col in df.columns else None,
                    top_n=visual_plan.get("shapTopN", 15),
                    width_ratios=visual_plan.get("shapBarPieWidthRatios", [1.2, 0.8, 1.5]),
                    height_ratios=visual_plan.get("shapBarPieHeightRatios", [1.0, 1.0]),
                    col_map=col_map,
                    zero_reference_fn=globals().get("add_zero_reference"),
                )
                count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
                record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
                planned_motifs = visual_plan.setdefault("templateMotifs", [])
                for motif in ("shap_bar_pie_summary_board", "standalone_category_pie", "shap_summary_beeswarm"):
                    if motif not in planned_motifs:
                        planned_motifs.append(motif)
                    record_fn(visual_plan, motif)
                count_fn(visual_plan, "referenceLineCount")
                count_fn(visual_plan, "zeroReferenceLineCount")
                count_fn(visual_plan, "colorbarSlotCount")
                count_fn(visual_plan, "standalonePieCount")
                count_fn(visual_plan, "piePanelCount")
                count_fn(visual_plan, "sampleEncodingCount")
                for _ in range(3):
                    count_fn(visual_plan, "panelLabelCount")
                visual_plan["sharedFeatureOrdering"] = True
                visual_plan["topFeatureLimit"] = result.get("top_n")
                visual_plan["featureValueColorEncoded"] = bool(feature_value_col and feature_value_col in df.columns)
                visual_plan["shapCompositeLayout"] = "GridSpec(2,3)"
                visual_plan["shapBarPiePanelCount"] = 3
                visual_plan["shapStandalonePieCategoryCount"] = len(result.get("categories") or [])
                return result["ax_bee"]
        use_shap_composite_board = (
            standalone
            and (
                visual_plan.get("useShapCompositeBoard")
                or "shap_bar_beeswarm_inset_pie" in template_motifs
                or "shap_bar_beeswarm_inset_pie" in patterns
                or ("shap_composite" in patterns and feature_value_col and feature_value_col in df.columns)
            )
        )
        if use_shap_composite_board:
            draw_fn = globals().get("draw_shap_bar_beeswarm_inset_pie")
            if draw_fn is not None:
                result = draw_fn(
                    df,
                    feature_col,
                    value_col,
                    feature_value_col=feature_value_col if feature_value_col in df.columns else None,
                    category_col=category_col if category_col in df.columns else None,
                    top_n=visual_plan.get("shapTopN", 15),
                    width_ratios=visual_plan.get("shapCompositeWidthRatios", [1.15, 0.05, 1.20, 0.05]),
                    pie_bbox=visual_plan.get("shapInsetPieBbox", [0.50, 0.20, 0.45, 0.45]),
                    col_map=col_map,
                    zero_reference_fn=globals().get("add_zero_reference"),
                )
                count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
                record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
                planned_motifs = visual_plan.setdefault("templateMotifs", [])
                if "shap_bar_beeswarm_inset_pie" not in planned_motifs:
                    planned_motifs.append("shap_bar_beeswarm_inset_pie")
                record_fn(visual_plan, "shap_bar_beeswarm_inset_pie")
                count_fn(visual_plan, "referenceLineCount")
                count_fn(visual_plan, "colorbarSlotCount")
                count_fn(visual_plan, "insetCount")
                count_fn(visual_plan, "insetPieCount")
                count_fn(visual_plan, "subAxesCount")
                count_fn(visual_plan, "sampleEncodingCount")
                visual_plan["sharedFeatureOrdering"] = True
                visual_plan["topFeatureLimit"] = result.get("top_n")
                visual_plan["featureValueColorEncoded"] = bool(feature_value_col and feature_value_col in df.columns)
                return result["ax_bee"]
        if standalone:
            fig, ax = plt.subplots(figsize=(92 * (1 / 25.4), 92 * (1 / 25.4)),
                               constrained_layout=True)
        plot_df = df.copy()
        plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")
        plot_df = plot_df.dropna(subset=[feature_col, value_col])
        order = (
            plot_df.assign(_abs=plot_df[value_col].abs())
                   .groupby(feature_col)["_abs"].mean()
                   .sort_values(ascending=False)
                   .head(15)
                   .index.tolist()
        )
        plot_df = plot_df[plot_df[feature_col].isin(order)].copy()
        y_lookup = {feature: i for i, feature in enumerate(order)}
        rng = np.random.default_rng(42)
        y = plot_df[feature_col].map(y_lookup).to_numpy(dtype=float)
        y = y + (rng.random(len(plot_df)) - 0.5) * 0.44
        if feature_value_col and feature_value_col in plot_df.columns:
            colors = pd.to_numeric(plot_df[feature_value_col], errors="coerce").fillna(0.0).to_numpy()
            sc = ax.scatter(plot_df[value_col], y, c=colors, cmap="RdYlBu_r",
                            s=14, alpha=0.72, edgecolor="white", linewidth=0.22, zorder=3)
            cbar = ax.figure.colorbar(sc, ax=ax, shrink=0.72, pad=0.02)
            cbar.set_label("Feature value")
            try:
                cbar.set_ticks([np.nanmin(colors), np.nanmax(colors)])
                cbar.set_ticklabels(["Low", "High"])
            except Exception:
                pass
        else:
            ax.scatter(plot_df[value_col], y, color="#1F4E79", s=14,
                       alpha=0.72, edgecolor="white", linewidth=0.22, zorder=3)
        # SHAP-composite zero divider — delegate to template_mining_helpers when reachable
        canonical_zero_ref = globals().get("add_zero_reference")
        if canonical_zero_ref is not None:
            try:
                canonical_zero_ref(ax, axis="x", color="black", lw=0.8, ls="-", zorder=2)
            except Exception:
                ax.axvline(0, color="black", linewidth=0.8, zorder=2)
        else:
            ax.axvline(0, color="black", linewidth=0.8, zorder=2)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels(order, fontsize=5)
        ax.set_ylim(len(order) - 0.5, -0.5)
        ax.set_xlabel("SHAP value (impact on prediction)")
        ax.set_ylabel("Feature" if standalone else "")
        ax.text(
            0.98, 0.04, f"top {len(order)} shared features",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.2,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
            zorder=6,
        )
        if standalone:
            apply_chart_polish(ax, "dotplot")
        return ax

    lower_to_col = {str(col).lower(): col for col in df.columns}
    def _first_column(*names):
        for name in names:
            if name and name in df.columns:
                return name
            if name and str(name).lower() in lower_to_col:
                return lower_to_col[str(name).lower()]
        return None

    row_col = _first_column(row_col, "row", "var1", "variable1", "variable_x", "feature_x", "x")
    col_col = _first_column(col_col, "column", "col", "var2", "variable2", "variable_y", "feature_y", "y")
    correlation_value_col = _first_column(
        correlation_value_col, "value", "r", "corr", "correlation", "pearson_r", "spearman_r"
    )
    has_long_correlation = bool(row_col and col_col and correlation_value_col)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    use_bubble_correlation = (
        standalone
        and (
            visual_plan.get("useBubbleCorrelationMatrix")
            or "bubble_correlation_matrix" in template_motifs
            or "correlation_evidence_matrix" in template_motifs
            or "bubble_correlation_matrix" in patterns
            or "red_blue_bubble_correlation" in patterns
            or ("correlation" in patterns and (has_long_correlation or len(numeric_cols) >= 2))
        )
        and (has_long_correlation or len(numeric_cols) >= 2)
    )
    if use_bubble_correlation:
        draw_fn = globals().get("draw_bubble_correlation_matrix")
        if draw_fn is not None:
            if ax is None:
                fig, ax = plt.subplots(figsize=(118 * (1 / 25.4), 104 * (1 / 25.4)),
                                   constrained_layout=True)
            correlation_label = visual_plan.get("bubbleCorrelationColorbarLabel")
            if not correlation_label:
                if str(correlation_value_col).lower() in {"value", "r", "corr", "correlation", "pearson_r", "spearman_r"}:
                    correlation_label = "Pearson r"
                elif isinstance(col_map, dict):
                    correlation_label = col_map.get(correlation_value_col, correlation_value_col)
                else:
                    correlation_label = correlation_value_col or "Pearson r"
            if has_long_correlation:
                result = draw_fn(
                    ax,
                    df,
                    row_col=row_col,
                    col_col=col_col,
                    value_col=correlation_value_col,
                    palette=visual_plan.get("bubbleCorrelationPalette", ["#8ECFC9", "#FFFFFF", "#FA7F6F"]),
                    size_scale=visual_plan.get("bubbleCorrelationSizeScale", 2000),
                    annotate=visual_plan.get("bubbleCorrelationAnnotate", True),
                    colorbar_label=correlation_label,
                    col_map=col_map,
                )
            else:
                corr_matrix = df[numeric_cols].corr(method="pearson")
                result = draw_fn(
                    ax,
                    corr_matrix,
                    palette=visual_plan.get("bubbleCorrelationPalette", ["#8ECFC9", "#FFFFFF", "#FA7F6F"]),
                    size_scale=visual_plan.get("bubbleCorrelationSizeScale", 2000),
                    annotate=visual_plan.get("bubbleCorrelationAnnotate", True),
                    colorbar_label="Pearson r",
                    col_map=col_map,
                )
            count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
            record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
            planned_motifs = visual_plan.setdefault("templateMotifs", [])
            for motif in ("bubble_correlation_matrix", "correlation_evidence_matrix"):
                if motif not in planned_motifs:
                    planned_motifs.append(motif)
                record_fn(visual_plan, motif)
            count_fn(visual_plan, "correlationBubbleCount")
            count_fn(visual_plan, "colorbarSlotCount")
            count_fn(visual_plan, "sampleEncodingCount")
            count_fn(visual_plan, "metricTextCount")
            visual_plan["correlationBubbleCellCount"] = int(result.get("n", 0) ** 2)
            visual_plan["correlationNumericTextCount"] = int(result.get("text_count", 0))
            visual_plan["divergingNormCentered"] = True
            visual_plan["bubbleAreaEncodesAbsCorrelation"] = True
            visual_plan["signedColorEncodesCorrelation"] = True
            if standalone:
                apply_chart_polish(result["ax"], "dotplot")
            return result["ax"]

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


def gen_lollipop_horizontal(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Horizontal lollipop chart for ranked values.

    Expects columns: label (category names) and value (numeric) in semanticRoles.
    Sorted descending with highest values at top.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group") or roles.get("x")
    val_col = roles.get("value") or roles.get("importance") or roles.get("mean_abs_shap") or roles.get("gain") or roles.get("y")
    ale_col = roles.get("ale") or roles.get("ale_effect") or roles.get("effect") or roles.get("main_effect")
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    visual_plan = chartPlan.get("visualContentPlan", {})
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        chartPlan["visualContentPlan"] = visual_plan
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    template_motifs = {str(m).lower() for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs") or [])}
    is_rf_shap = (
        template_case.get("bundleKey") == "rf_feature_importance_shap"
        or "ml_explainability" in patterns
        or "feature_importance" in patterns
        or "shap_composite" in patterns
        or any(str(c).lower() in ("importance", "mean_abs_shap", "shap_value", "gain", "permutation") for c in df.columns)
    )

    use_bipolar_lollipop_ale = (
        standalone
        and (
            visual_plan.get("useBipolarLollipopAleBoard")
            or "bipolar_lollipop_ale_board" in template_motifs
            or "bipolar_lollipop_ale_board" in patterns
            or "ale_bipolar_lollipop" in patterns
        )
    )
    if use_bipolar_lollipop_ale:
        feature_col = label_col or roles.get("feature") or roles.get("feature_id")
        importance_col = val_col or roles.get("pfi") or roles.get("feature_importance")
        if feature_col is None or importance_col is None or ale_col is None:
            raise ValueError("bipolar_lollipop_ale_board requires feature, importance, and ale/effect roles")
        draw_fn = globals().get("draw_bipolar_lollipop_ale_board")
        if draw_fn is None:
            raise RuntimeError("draw_bipolar_lollipop_ale_board helper is required for gen_lollipop_horizontal")
        result = draw_fn(
            df,
            feature_col,
            importance_col,
            ale_col,
            top_n=visual_plan.get("lollipopTopN", 15),
            figsize=tuple(visual_plan.get("bipolarLollipopFigsize", [10.0, 6.0])),
            wspace=visual_plan.get("bipolarLollipopWspace", 0.15),
            importance_color=visual_plan.get("bipolarImportanceColor", "#4A6B8A"),
            positive_color=visual_plan.get("bipolarPositiveColor", "#C0504D"),
            negative_color=visual_plan.get("bipolarNegativeColor", "#4F81BD"),
            stem_width=visual_plan.get("bipolarStemWidth", 2.5),
            marker_size=visual_plan.get("bipolarMarkerSize", 80),
            col_map=col_map,
            zero_reference_fn=globals().get("add_zero_reference"),
        )
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        for motif in ("bipolar_lollipop_ale_board", "shared_feature_axis", "signed_effect_axis"):
            if motif not in planned_motifs:
                planned_motifs.append(motif)
            record_fn(visual_plan, motif)
        count_fn(visual_plan, "lollipopLayerCount")
        count_fn(visual_plan, "lollipopLayerCount")
        count_fn(visual_plan, "referenceLineCount")
        count_fn(visual_plan, "zeroReferenceLineCount")
        count_fn(visual_plan, "sampleEncodingCount")
        visual_plan["sharedFeatureOrdering"] = True
        visual_plan["bipolarPaletteApplied"] = True
        visual_plan["bipolarPositiveCount"] = result.get("positive_count")
        visual_plan["bipolarNegativeCount"] = result.get("negative_count")
        visual_plan["topFeatureLimit"] = result.get("top_n")
        visual_plan["bipolarLollipopPanelCount"] = 2
        visual_plan["lollipopCompositeLayout"] = "subplots(1,2)"
        visual_plan["templateMatchMode"] = "case_022_bipolar_lollipop_ale_board"
        return result["ax_ale"]

    if label_col is None or val_col is None:
        raise ValueError("lollipop_horizontal requires 'label' and 'value' in semanticRoles")

    df_sorted = df.copy()
    if is_rf_shap:
        order_values = pd.to_numeric(df_sorted[val_col], errors="coerce").abs()
        df_sorted = df_sorted.assign(_scifig_order=order_values).nlargest(min(len(df_sorted), 15), "_scifig_order")
        df_sorted = df_sorted.sort_values("_scifig_order", ascending=True).reset_index(drop=True)
    else:
        df_sorted = df_sorted.sort_values(val_col, ascending=True).reset_index(drop=True)
    color = palette.get("categorical", ["#1F4E79"])[0]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4),
                                    max(50, len(df_sorted) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = range(len(df_sorted))
    if is_rf_shap:
        values = pd.to_numeric(df_sorted[val_col], errors="coerce").fillna(0.0).to_numpy()
        max_val = max(float(np.nanmax(np.abs(values))) if len(values) else 1.0, 1e-12)
        cmap = plt.get_cmap("Blues")
        colors = [cmap(0.35 + 0.55 * (abs(v) / max_val)) for v in values]
        # SHAP signed-value zero divider — delegate to template_mining_helpers when reachable
        canonical_zero_ref = globals().get("add_zero_reference")
        if canonical_zero_ref is not None:
            try:
                canonical_zero_ref(ax, axis="x", color="#888888", lw=0.65, ls="--", zorder=0)
            except Exception:
                ax.axvline(0, color="#888888", linestyle="--", linewidth=0.65, zorder=0)
        else:
            ax.axvline(0, color="#888888", linestyle="--", linewidth=0.65, zorder=0)
        ax.hlines(y_pos, 0, values, color="#A7BBD6", linewidth=1.0, zorder=1)
        ax.scatter(values, list(y_pos), color=colors, s=34, zorder=3,
                   linewidth=0.35, edgecolors="white")
        for y, value in zip(y_pos, values):
            ax.text(value + max_val * 0.025, y, f"{value:.3g}", va="center", ha="left",
                    fontsize=4.8, color="#B00000")
        x_min = min(0.0, float(np.nanmin(values)) if len(values) else 0.0)
        x_max = max(0.0, float(np.nanmax(values)) if len(values) else 0.0)
        x_pad = max(max_val * 0.18, 1e-9)
        ax.set_xlim(x_min - x_pad * 0.35, x_max + x_pad)
        ax.text(
            0.98, 0.05, f"top {len(df_sorted)} features\nRF / SHAP route",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.2,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
            zorder=6,
        )
        ax.set_xlabel("Mean |SHAP| / importance")
    else:
        ax.hlines(y_pos, 0, df_sorted[val_col], color=color, linewidth=0.8)
        ax.scatter(df_sorted[val_col], y_pos, color=color, s=25, zorder=3,
                   linewidth=0.3, edgecolors="white")
        ax.set_xlabel(val_col)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df_sorted[label_col].values, fontsize=5)
    ax.set_ylim(-0.5, len(df_sorted) - 0.5)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if standalone:
        apply_chart_polish(ax, "lollipop_horizontal")
    return ax
