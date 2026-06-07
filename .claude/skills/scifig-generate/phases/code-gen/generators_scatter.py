"""Scatter / embedding / agreement chart generators.

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
        ax.legend(loc="upper right", frameon=False, fontsize=5, title_fontsize=5)
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
        ax.legend(loc="upper right", frameon=False, fontsize=5)
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
              frameon=False, loc="upper right", borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "interaction_plot")
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
        ax.legend(loc="upper right", frameon=False, fontsize=5)
    else:
        ax.scatter(df[x_col], df[y_col], s=12, alpha=0.7,
                   color=palette.get("categorical", ["#0072B2"])[0],
                   linewidth=0.3, edgecolor="white", zorder=2)

    ax.set_xlabel(f"{method} axis 1")
    ax.set_ylabel(f"{method} axis 2")
    if standalone:
        apply_chart_polish(ax, "ordination_plot")
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


def gen_scatter_regression(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Scatter with regression line, parity diagnostics, or SHAP dependence view."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    columns_lower = {str(c).lower(): c for c in df.columns}

    def _role_or_column(*names):
        for name in names:
            value = roles.get(name)
            if value in df.columns:
                return value
            if isinstance(value, str) and value.lower() in columns_lower:
                return columns_lower[value.lower()]
            if name in columns_lower:
                return columns_lower[name]
        return None

    x_col = _role_or_column("actual", "observed", "measured", "true", "y_true", "x", "dose", "concentration")
    y_col = _role_or_column("predicted", "prediction", "fitted", "y_pred", "y", "value")
    trend_x_col = _role_or_column("x", "sample", "sample_id", "sample_index", "index", "concentration", "dose", "time")
    true_col = _role_or_column("true", "actual", "observed", "measured", "y_true")
    predicted_col = _role_or_column("predicted", "prediction", "fitted", "y_pred")
    split_col = _role_or_column("split", "sample_type", "source", "cohort", "group", "set", "dataset")
    panel_col = _role_or_column("panel", "facet", "task", "target", "property", "condition", "temperature", "temp", "system", "material", "dopant")
    method_col = _role_or_column("method", "model", "algorithm", "series", "source")
    lower_col = _role_or_column("pi_low", "pi_lower", "lower", "lower_bound", "y_lower", "prediction_lower", "prediction_interval_lower")
    upper_col = _role_or_column("pi_high", "pi_upper", "upper", "upper_bound", "y_upper", "prediction_upper", "prediction_interval_upper")
    threshold_col = _role_or_column("threshold", "breakpoint", "changepoint", "split_value")
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    bundle_key = str(template_case.get("bundleKey") or "").lower()
    visual_plan = chartPlan.get("visualContentPlan")
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        chartPlan["visualContentPlan"] = visual_plan
    template_families = {
        str(f).lower()
        for f in (
            template_case.get("families")
            or template_case.get("templateFamilies")
            or visual_plan.get("families")
            or visual_plan.get("templateFamilies")
            or []
        )
    }
    template_motifs = {
        str(m).lower()
        for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs") or [])
    }
    feature_value_col = _role_or_column("feature_value", "feature_val", "feature_numeric", "x")
    shap_value_col = _role_or_column("shap_value", "shap", "shap_impact", "y")
    interaction_col = _role_or_column("interaction_value", "interaction", "feature_color", "color", "hue")
    feature_name_col = _role_or_column("feature_id", "feature", "feature_name", "term")
    is_shap_candidate = (
        bundle_key in {"rf_feature_importance_shap", "shap_explainability_composite", "template_shap_explainability"}
        or "shap_composite" in patterns
        or "ml_explainability" in patterns
        or "shap_dependence" in patterns
        or any("shap" in name for name in columns_lower)
    )
    is_shap_dependence = (
        is_shap_candidate
        and feature_value_col
        and shap_value_col
        and feature_value_col in df.columns
        and shap_value_col in df.columns
        and feature_value_col != shap_value_col
    )
    if is_shap_dependence:
        x_col = feature_value_col
        y_col = shap_value_col
    is_prediction_report = (
        bundle_key == "rf_model_performance_report"
        or "model_performance_benchmark" in patterns
        or "ml_model_family" in patterns
        or "prediction_diagnostic" in patterns
        or ("actual" in roles and ("predicted" in roles or "fitted" in roles))
    )

    if x_col is None or y_col is None:
        raise ValueError("scatter_regression requires 'x' and 'y' in semanticRoles")

    inset_tokens = " ".join(
        str(v).lower()
        for v in [
            bundle_key,
            *patterns,
            *template_motifs,
            trend_x_col or "",
            true_col or "",
            predicted_col or "",
            panel_col or "",
            split_col or "",
            lower_col or "",
            upper_col or "",
            feature_name_col or "",
            feature_value_col or "",
            shap_value_col or "",
            interaction_col or "",
            *template_families,
            dataProfile.get("domain", ""),
        ]
    )
    use_hump_threshold_regression = (
        standalone
        and (
            visual_plan.get("useHumpThresholdRegression")
            or
            "hump_threshold_regression" in template_motifs
            or "threshold_hump_regression" in template_motifs
            or "hump_threshold_regression" in patterns
            or "threshold_hump_regression" in patterns
            or (
                any(token in inset_tokens for token in ("hump", "threshold", "breakpoint", "changepoint", "驼峰", "阈值"))
                and not is_shap_dependence
            )
        )
    )

    if use_hump_threshold_regression:
        drawer = globals().get("draw_hump_threshold_regression")
        if drawer is None:
            raise RuntimeError("draw_hump_threshold_regression helper is required for hump threshold regression")
        threshold_value = visual_plan.get("humpThresholdValue")
        if threshold_value is None and threshold_col and threshold_col in df.columns:
            threshold_series = pd.to_numeric(df[threshold_col], errors="coerce").dropna()
            if len(threshold_series):
                threshold_value = float(threshold_series.iloc[0])
        result = drawer(
            df,
            x_col=x_col,
            y_col=y_col,
            threshold=threshold_value,
            degree=visual_plan.get("humpThresholdPolynomialDegree", 3),
            n_bootstraps=visual_plan.get("humpThresholdBootstraps", 200),
            figsize=tuple(visual_plan.get("humpThresholdFigsize", [7.0, 5.0])),
            ci_color=visual_plan.get("humpThresholdCIColor", "#D9D9D9"),
            ci_alpha=visual_plan.get("humpThresholdCIAlpha", 0.60),
            scatter_color=visual_plan.get("humpThresholdScatterColor", "#E87A6E"),
            global_line_color=visual_plan.get("humpThresholdGlobalLineColor", "#404040"),
            threshold_color=visual_plan.get("humpThresholdColor", "#E63946"),
            low_segment_color=visual_plan.get("humpThresholdLowSegmentColor", "#2AB7CA"),
            high_segment_color=visual_plan.get("humpThresholdHighSegmentColor", "#1E847F"),
            scatter_size=visual_plan.get("humpThresholdScatterSize", 60),
            scatter_alpha=visual_plan.get("humpThresholdScatterAlpha", 0.80),
            col_map=col_map,
        )
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        for motif in ("hump_threshold_regression", "regression_band_fillbtw", "threshold_split_line"):
            if motif not in planned_motifs:
                planned_motifs.append(motif)
            record_fn(visual_plan, motif)
        for _ in range(result.get("confidence_band_count", 0)):
            count_fn(visual_plan, "confidenceBandCount")
        for _ in range(result.get("scatter_count", 0)):
            count_fn(visual_plan, "sampleEncodingCount")
        for _ in range(result.get("global_fit_count", 0)):
            count_fn(visual_plan, "regressionLineCount")
        for _ in range(result.get("segment_fit_count", 0)):
            count_fn(visual_plan, "segmentedRegressionLineCount")
        for _ in range(result.get("threshold_line_count", 0)):
            count_fn(visual_plan, "referenceLineCount")
            count_fn(visual_plan, "thresholdLineCount")
        for _ in range(result.get("external_legend_count", 0)):
            count_fn(visual_plan, "externalLegendCount")
        for _ in range(result.get("annotation_count", 0)):
            count_fn(visual_plan, "annotationTextCount")
        visual_plan["humpThresholdValue"] = result.get("threshold")
        visual_plan["humpThresholdR2"] = result.get("r2")
        visual_plan["humpThresholdSegmentLineCount"] = result.get("segment_fit_count")
        visual_plan["templateMatchMode"] = "case_024_hump_threshold_regression"
        return result["axis"]

    use_shap_interaction_dependence_grid = (
        standalone
        and is_shap_dependence
        and bool(feature_name_col) and feature_name_col in df.columns
        and bool(interaction_col) and interaction_col in df.columns
        and df[feature_name_col].dropna().astype(str).nunique() > 1
        and (
            "shap_interaction_dependence_grid" in template_motifs
            or "interaction_color_mapped_scatter" in template_motifs
            or "shap_interaction_grid" in patterns
            or "interaction_effect" in patterns
            or ("shap_dependence" in patterns and ("interaction" in inset_tokens or "secondary" in inset_tokens))
        )
    )

    if use_shap_interaction_dependence_grid:
        drawer = globals().get("draw_shap_interaction_dependence_grid")
        if drawer is None:
            raise RuntimeError("draw_shap_interaction_dependence_grid helper is required for SHAP interaction grid")
        result = drawer(
            df,
            feature_col=feature_name_col,
            feature_value_col=feature_value_col,
            shap_value_col=shap_value_col,
            interaction_col=interaction_col,
            max_features=visual_plan.get("shapInteractionMaxFeatures", 6),
            ncols=visual_plan.get("shapInteractionNcols", 3),
            figsize=tuple(visual_plan.get("shapInteractionFigsize", [14.0, 8.0])),
            cmap=visual_plan.get("shapInteractionColormap", "coolwarm"),
            scatter_size=visual_plan.get("shapInteractionScatterSize", 15),
            scatter_alpha=visual_plan.get("shapInteractionScatterAlpha", 0.80),
            zero_color=visual_plan.get("shapInteractionZeroLineColor", "gray"),
            colorbar_label=visual_plan.get("shapInteractionColorbarLabel", "Interaction Feature"),
            col_map=col_map,
        )
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn(visual_plan, "shap_interaction_dependence_grid")
        record_fn(visual_plan, "interaction_color_mapped_scatter")
        record_fn(visual_plan, "shap_dependence_grid")
        for _ in range(result.get("panel_count", 0)):
            count_fn(visual_plan, "shapInteractionPanelCount")
        for _ in range(result.get("scatter_count", 0)):
            count_fn(visual_plan, "shapInteractionScatterCount")
            count_fn(visual_plan, "sampleEncodingCount")
        for _ in range(result.get("colorbar_count", 0)):
            count_fn(visual_plan, "colorbarSlotCount")
        for _ in range(result.get("zero_line_count", 0)):
            count_fn(visual_plan, "zeroReferenceLineCount")
            count_fn(visual_plan, "referenceLineCount")
        for _ in range(result.get("panel_label_count", 0)):
            count_fn(visual_plan, "panelLabelCount")
        visual_plan["shapInteractionPanelCount"] = result.get("panel_count", 0)
        visual_plan["shapInteractionScatterCount"] = result.get("scatter_count", 0)
        visual_plan["shapInteractionColorbarCount"] = result.get("colorbar_count", 0)
        visual_plan["shapInteractionZeroLineCount"] = result.get("zero_line_count", 0)
        visual_plan["shapInteractionColormap"] = result.get("cmap")
        return result["axes"][0]

    use_shap_dependence_background_grid = (
        standalone
        and is_shap_dependence
        and bool(feature_name_col) and feature_name_col in df.columns
        and not use_shap_interaction_dependence_grid
        and df[feature_name_col].dropna().astype(str).nunique() > 1
        and (
            "shap_dependence_background_grid" in template_motifs
            or "shap_dependence_grid" in template_motifs
            or "signed_effect_background" in template_motifs
            or "shap_dependence" in patterns
            or "shap_background_grid" in patterns
            or "shap_composite" in template_families
        )
    )

    if use_shap_dependence_background_grid:
        drawer = globals().get("draw_shap_dependence_background_grid")
        if drawer is None:
            raise RuntimeError("draw_shap_dependence_background_grid helper is required for SHAP dependence grid")
        result = drawer(
            df,
            feature_col=feature_name_col,
            feature_value_col=feature_value_col,
            shap_value_col=shap_value_col,
            max_features=visual_plan.get("shapDependenceMaxFeatures", 6),
            ncols=visual_plan.get("shapDependenceNcols", 3),
            figsize=tuple(visual_plan.get("shapDependenceFigsize", [12.0, 7.0])),
            y_limits=tuple(visual_plan.get("shapDependenceYLimits", [-2.5, 2.5])),
            positive_color=visual_plan.get("shapPositiveBackgroundColor", "#ffcccc"),
            negative_color=visual_plan.get("shapNegativeBackgroundColor", "#cce5ff"),
            background_alpha=visual_plan.get("shapBackgroundAlpha", 0.40),
            scatter_color=visual_plan.get("shapDependenceScatterColor", "black"),
            scatter_size=visual_plan.get("shapDependenceScatterSize", 15),
            scatter_alpha=visual_plan.get("shapDependenceScatterAlpha", 0.70),
            zero_color=visual_plan.get("shapZeroLineColor", "gray"),
            col_map=col_map,
        )
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn(visual_plan, "shap_dependence_background_grid")
        record_fn(visual_plan, "signed_effect_background")
        record_fn(visual_plan, "shap_dependence_grid")
        for _ in range(result.get("panel_count", 0)):
            count_fn(visual_plan, "shapDependencePanelCount")
            count_fn(visual_plan, "panelLabelCount")
        for _ in range(result.get("scatter_count", 0)):
            count_fn(visual_plan, "shapDependenceScatterCount")
            count_fn(visual_plan, "sampleEncodingCount")
        for _ in range(result.get("zero_line_count", 0)):
            count_fn(visual_plan, "zeroReferenceLineCount")
            count_fn(visual_plan, "referenceLineCount")
        for _ in range(result.get("background_zone_count", 0)):
            count_fn(visual_plan, "backgroundZoneCount")
        visual_plan["shapDependencePanelCount"] = result.get("panel_count", 0)
        visual_plan["shapDependenceBackgroundZoneCount"] = result.get("background_zone_count", 0)
        visual_plan["shapDependenceZeroLineCount"] = result.get("zero_line_count", 0)
        visual_plan["shapDependenceYLimits"] = result.get("y_limits")
        return result["axes"][0]

    use_time_series_pi = (
        standalone
        and bool(trend_x_col) and trend_x_col in df.columns
        and bool(true_col) and bool(predicted_col)
        and true_col in df.columns and predicted_col in df.columns
        and true_col != predicted_col
        and (
            "time_series_prediction_interval" in template_motifs
            or "time_series_pi" in template_motifs
            or "interval_uncertainty_band" in template_motifs
            or "time_series_pi" in patterns
            or "prediction_interval" in patterns
            or "train_test_prediction_interval" in patterns
            or "time_series_pi" in template_families
            or (
                "prediction" in inset_tokens
                and "interval" in inset_tokens
                and any(token in inset_tokens for token in ("train", "training", "test", "testing", "time", "series"))
            )
        )
    )

    if use_time_series_pi:
        drawer = globals().get("draw_time_series_prediction_interval")
        if drawer is None:
            raise RuntimeError("draw_time_series_prediction_interval helper is required for time-series PI")
        result = drawer(
            df,
            time_col=trend_x_col,
            actual_col=true_col,
            predicted_col=predicted_col,
            lower_col=lower_col,
            upper_col=upper_col,
            split_col=split_col,
            split_index=visual_plan.get("timeSeriesSplitIndex"),
            figsize=tuple(visual_plan.get("timeSeriesPIFigsize", [10.0, 5.0])),
            interval_color=visual_plan.get("timeSeriesPIBandColor", "skyblue"),
            interval_alpha=visual_plan.get("timeSeriesPIAlpha", 0.40),
            observed_color=visual_plan.get("timeSeriesObservedColor", "black"),
            predicted_color=visual_plan.get("timeSeriesPredictedColor", "red"),
            divider_color=visual_plan.get("timeSeriesDividerColor", "gray"),
            observed_size=visual_plan.get("timeSeriesObservedSize", 15),
            observed_alpha=visual_plan.get("timeSeriesObservedAlpha", 0.70),
            predicted_lw=visual_plan.get("timeSeriesPredictedLinewidth", 1.5),
            interval_label=visual_plan.get("timeSeriesPIBandLabel", "90% Prediction Interval"),
            observed_label=visual_plan.get("timeSeriesObservedLabel", "Actual Observations"),
            predicted_label=visual_plan.get("timeSeriesPredictedLabel", "Model Prediction"),
            train_label=visual_plan.get("timeSeriesTrainLabel", "Training data set"),
            test_label=visual_plan.get("timeSeriesTestLabel", "Testing data set"),
            top_legend=visual_plan.get("timeSeriesTopLegend", True),
            region_labels=visual_plan.get("timeSeriesRegionLabels", True),
            col_map=col_map,
        )
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn(visual_plan, "time_series_prediction_interval")
        record_fn(visual_plan, "interval_uncertainty_band")
        record_fn(visual_plan, "train_test_diagnostic")
        if "prediction_diagnostic_matrix" in template_motifs:
            record_fn(visual_plan, "prediction_diagnostic_matrix")
        for _ in range(result.get("interval_band_count", 0)):
            count_fn(visual_plan, "intervalBandCount")
        for _ in range(result.get("observed_scatter_count", 0)):
            count_fn(visual_plan, "observedScatterCount")
            count_fn(visual_plan, "sampleEncodingCount")
        for _ in range(result.get("predicted_line_count", 0)):
            count_fn(visual_plan, "predictedLineCount")
        for _ in range(result.get("train_test_divider_count", 0)):
            count_fn(visual_plan, "trainTestDividerCount")
            count_fn(visual_plan, "referenceLineCount")
        for _ in range(result.get("train_test_region_label_count", 0)):
            count_fn(visual_plan, "trainTestRegionLabelCount")
        for _ in range(result.get("legend_count", 0)):
            count_fn(visual_plan, "externalLegendCount")
        visual_plan["timeSeriesPredictionIntervalCount"] = result.get("interval_band_count", 0)
        visual_plan["timeSeriesObservedScatterCount"] = result.get("observed_scatter_count", 0)
        visual_plan["timeSeriesPredictedLineCount"] = result.get("predicted_line_count", 0)
        visual_plan["timeSeriesTrainTestDividerPresent"] = result.get("train_test_divider_count", 0) > 0
        visual_plan["timeSeriesSplitIndex"] = result.get("split_index")
        visual_plan["timeSeriesUsesSuppliedInterval"] = result.get("uses_supplied_interval")
        return result["axis"]

    use_inset_raincloud_residual = (
        standalone
        and bool(true_col) and bool(predicted_col)
        and true_col in df.columns and predicted_col in df.columns
        and true_col != predicted_col
        and (
            "inset_raincloud_residual" in template_motifs
            or "inset_raincloud" in patterns
            or "inset_residual_raincloud" in patterns
            or ("raincloud" in inset_tokens and ("inset" in inset_tokens or "residual" in inset_tokens))
        )
    )

    if use_inset_raincloud_residual:
        draw_raincloud_fn = globals().get("draw_inset_raincloud")
        if draw_raincloud_fn is None:
            def draw_raincloud_fn(ax, residuals, *, color="#008000",
                                  rect=(0.55, 0.35, 0.40, 0.35),
                                  title="Residual", seed=42):
                vals = np.asarray(residuals, dtype=float)
                vals = vals[np.isfinite(vals)]
                if len(vals) < 3:
                    return None
                inset = ax.inset_axes(list(rect), zorder=10)
                inset.set_gid("scifig_inset_raincloud")
                inset.set_facecolor("white")
                inset.patch.set_alpha(0.96)
                for spine in inset.spines.values():
                    spine.set_linewidth(0.8)
                    spine.set_color("#222222")
                y_min = float(np.nanmin(vals))
                y_max = float(np.nanmax(vals))
                span = max(y_max - y_min, 1e-9)
                pad = span * 0.15
                grid = np.linspace(y_min - pad, y_max + pad, 120)
                if len(vals) >= 5 and float(np.nanstd(vals)) > 1e-12:
                    try:
                        from scipy.stats import gaussian_kde
                        density = gaussian_kde(vals)(grid)
                    except Exception:
                        hist, edges = np.histogram(vals, bins=min(12, max(5, int(np.sqrt(len(vals))))), density=True)
                        grid = (edges[:-1] + edges[1:]) / 2
                        density = hist
                    if np.nanmax(density) > 0:
                        density = density / np.nanmax(density) * 0.38
                        inset.fill_betweenx(grid, 0, density, color=color, alpha=0.40, linewidth=0, zorder=1)
                        inset.plot(density, grid, color=color, linewidth=1.15, zorder=2)
                q1, med, q3 = np.percentile(vals, [25, 50, 75])
                box_x = 0.50
                inset.add_patch(plt.Rectangle((box_x - 0.045, q1), 0.09, max(q3 - q1, span * 0.015),
                                              facecolor="white", edgecolor=color, linewidth=1.0, zorder=3))
                inset.plot([box_x - 0.045, box_x + 0.045], [med, med], color=color, linewidth=1.45, zorder=4)
                rng = np.random.default_rng(seed)
                inset.scatter(box_x + 0.13 + rng.random(len(vals)) * 0.15, vals,
                              s=10, color=color, alpha=0.55, edgecolor="white", linewidth=0.25, zorder=5)
                inset.axhline(0, color="black", linestyle="--", linewidth=0.65, alpha=0.70, zorder=4)
                inset.set_xlim(0, 0.84)
                inset.set_ylim(y_min - pad, y_max + pad)
                inset.set_xticks([])
                inset.tick_params(axis="y", labelsize=5.0, length=2, width=0.45, direction="in")
                inset.set_ylabel("Residual", fontsize=5.2)
                inset.set_title(title, fontsize=5.4, pad=1.5)
                return inset

        metric_cols = [
            col for col in (
                _role_or_column("mse"),
                _role_or_column("mae"),
                _role_or_column("medae", "median_absolute_error"),
                _role_or_column("difference", "diff"),
            )
            if col and col in df.columns
        ]
        plot_cols = [true_col, predicted_col]
        if trend_x_col and trend_x_col in df.columns and trend_x_col not in plot_cols:
            plot_cols.append(trend_x_col)
        if panel_col and panel_col in df.columns and panel_col not in plot_cols:
            plot_cols.append(panel_col)
        for col in metric_cols:
            if col not in plot_cols:
                plot_cols.append(col)
        plot_df = df[plot_cols].copy()
        plot_df[true_col] = pd.to_numeric(plot_df[true_col], errors="coerce")
        plot_df[predicted_col] = pd.to_numeric(plot_df[predicted_col], errors="coerce")
        if trend_x_col and trend_x_col in plot_df.columns:
            plot_df[trend_x_col] = pd.to_numeric(plot_df[trend_x_col], errors="coerce")
        plot_df = plot_df.dropna(subset=[true_col, predicted_col])
        if plot_df.empty:
            raise ValueError("inset_raincloud_residual requires non-empty true/predicted rows")

        if panel_col and panel_col in plot_df.columns:
            panels = plot_df[panel_col].dropna().astype(str).unique().tolist()[:2]
            if not panels:
                panels = ["Panel"]
        else:
            panels = ["Panel"]
        n_panels = max(1, len(panels))
        fig = plt.figure(figsize=(12, 5))
        gs = fig.add_gridspec(1, n_panels, wspace=0.25)
        true_color = visual_plan.get("truePredPalette", {}).get("true", "#FFA500")
        pred_color = visual_plan.get("truePredPalette", {}).get(
            "predicted", visual_plan.get("insetRaincloudColor", "#008000")
        )
        inset_rect = visual_plan.get("insetRaincloudRect", [0.55, 0.35, 0.40, 0.35])
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        floor_fn = globals().get("apply_scatter_regression_floor")
        axes = []
        for idx, panel_value in enumerate(panels):
            sub_ax = fig.add_subplot(gs[0, idx])
            axes.append(sub_ax)
            if floor_fn is not None:
                try:
                    floor_fn(sub_ax, despine=True, grid_axis="both")
                except Exception:
                    sub_ax.grid(True, linestyle="--", color="#E0E0E0", linewidth=0.45, alpha=0.60, zorder=0)
            if panel_col and panel_col in plot_df.columns:
                panel_df = plot_df[plot_df[panel_col].astype(str) == str(panel_value)].copy()
            else:
                panel_df = plot_df.copy()
            if trend_x_col and trend_x_col in panel_df.columns and panel_df[trend_x_col].notna().any():
                panel_df = panel_df.sort_values(trend_x_col)
                x_values = panel_df[trend_x_col].to_numpy(dtype=float)
                x_label = display_label(trend_x_col, col_map) if col_map else str(trend_x_col)
            else:
                panel_df = panel_df.reset_index(drop=True)
                x_values = np.arange(1, len(panel_df) + 1)
                x_label = "Sample index"
            true_values = panel_df[true_col].to_numpy(dtype=float)
            pred_values = panel_df[predicted_col].to_numpy(dtype=float)
            residuals = pred_values - true_values
            sub_ax.plot(
                x_values, true_values, color=true_color, marker="s", markersize=4.8,
                linewidth=1.45, label="True", zorder=3,
            )
            sub_ax.plot(
                x_values, pred_values, color=pred_color, marker="o", markersize=4.8,
                linewidth=1.45, label="Predicted", zorder=4,
            )
            if len(panel_df) >= 2:
                sub_ax.fill_between(x_values, true_values, pred_values,
                                    color="#888888", alpha=0.12, linewidth=0, zorder=2)
            mse = float(np.nanmean(residuals ** 2)) if len(residuals) else np.nan
            mae = float(np.nanmean(np.abs(residuals))) if len(residuals) else np.nan
            medae = float(np.nanmedian(np.abs(residuals))) if len(residuals) else np.nan
            diff = float(np.nanmean(residuals)) if len(residuals) else np.nan
            metric_text = f"MSE: {mse:.3f}\nMAE: {mae:.3f}\nMedAE: {medae:.3f}\nDifference: {diff:.3f}"
            sub_ax.text(0.05, 0.05, metric_text, transform=sub_ax.transAxes,
                        ha="left", va="bottom", fontsize=7.2, color="#222222", zorder=9)
            sub_ax.legend(loc="upper left", frameon=False, fontsize=7.5, handlelength=1.6)
            sub_ax.text(-0.12, 1.04, chr(ord("a") + idx), transform=sub_ax.transAxes,
                        fontsize=10, fontweight="bold", ha="left", va="bottom", zorder=20)
            sub_ax.set_title(str(display_label(panel_value, col_map) if col_map else panel_value),
                             fontsize=8.2, fontweight="bold", pad=3)
            sub_ax.set_xlabel(x_label)
            sub_ax.set_ylabel(display_label(true_col, col_map) if col_map else str(true_col))
            sub_ax.tick_params(labelsize=7, length=3, direction="in")
            for spine_name in ("top", "right"):
                sub_ax.spines[spine_name].set_visible(False)
            inset_ax = draw_raincloud_fn(
                sub_ax, residuals, color=pred_color, rect=inset_rect,
                title="Residual", seed=42 + idx,
            )
            count_fn(visual_plan, "metricTextCount")
            count_fn(visual_plan, "panelLabelCount")
            if inset_ax is not None:
                count_fn(visual_plan, "insetCount")
                count_fn(visual_plan, "insetRaincloudCount")
                count_fn(visual_plan, "referenceLineCount")
                count_fn(visual_plan, "subAxesCount")
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        if "inset_raincloud_residual" not in planned_motifs:
            planned_motifs.append("inset_raincloud_residual")
        record_fn(visual_plan, "inset_raincloud_residual")
        visual_plan["useInsetAxes"] = True
        visual_plan["useInsetRaincloud"] = True
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.14, top=0.90, wspace=0.25)
        return axes[0]

    gam_tokens = " ".join(
        str(v).lower()
        for v in [
            bundle_key,
            *patterns,
            *template_motifs,
            x_col,
            y_col,
            split_col or "",
            dataProfile.get("domain", ""),
        ]
    )
    use_gam_log_residual_diagnostic = (
        standalone
        and (
            "gam_log_residual_diagnostic" in template_motifs
            or "gam_residual_diagnostic" in patterns
            or ("gam" in gam_tokens and "residual" in gam_tokens)
            or ("spline" in gam_tokens and "residual" in gam_tokens)
        )
    )

    if use_gam_log_residual_diagnostic:
        import matplotlib.gridspec as gridspec
        import matplotlib.ticker as ticker

        plot_cols = [x_col, y_col]
        if split_col and split_col in df.columns:
            plot_cols.append(split_col)
        plot_df = df[plot_cols].copy()
        plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
        plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
        plot_df = plot_df.dropna(subset=[x_col, y_col])
        plot_df = plot_df[(plot_df[x_col] > 0) & (plot_df[y_col] > 0)]
        if len(plot_df) < 8:
            raise ValueError("gam_log_residual_diagnostic requires at least 8 positive x/y rows")

        log_x = np.log10(plot_df[x_col].to_numpy(dtype=float))
        log_y = np.log10(plot_df[y_col].to_numpy(dtype=float))
        smooth_log_x = np.linspace(float(np.nanmin(log_x)), float(np.nanmax(log_x)), 220)
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import SplineTransformer
            n_knots = int(min(7, max(4, len(plot_df) // 80)))
            model = make_pipeline(
                SplineTransformer(n_knots=n_knots, degree=3, include_bias=False),
                LinearRegression(),
            )
            model.fit(log_x.reshape(-1, 1), log_y)
            smooth_log_y = model.predict(smooth_log_x.reshape(-1, 1))
            fitted_log_y = model.predict(log_x.reshape(-1, 1))
            r2 = float(model.score(log_x.reshape(-1, 1), log_y))
        except Exception:
            degree = min(3, max(1, len(np.unique(log_x)) - 1))
            coeff = np.polyfit(log_x, log_y, degree)
            poly = np.poly1d(coeff)
            smooth_log_y = poly(smooth_log_x)
            fitted_log_y = poly(log_x)
            ss_res = float(np.sum((log_y - fitted_log_y) ** 2))
            ss_tot = float(np.sum((log_y - np.nanmean(log_y)) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        residuals = log_y - fitted_log_y
        band = 1.64 * float(np.nanstd(residuals)) if len(residuals) else 0.0
        smooth_x = np.power(10.0, smooth_log_x)
        smooth_y = np.power(10.0, smooth_log_y)
        lower = np.power(10.0, smooth_log_y - band)
        upper = np.power(10.0, smooth_log_y + band)

        if split_col and split_col in plot_df.columns:
            groups = plot_df[split_col].fillna("Non").astype(str).to_numpy()
        else:
            groups = np.full(len(plot_df), "Non", dtype=object)
            if len(residuals) >= 20:
                groups[np.abs(residuals) >= np.nanquantile(np.abs(residuals), 0.90)] = "Adj"
                groups[residuals >= np.nanquantile(residuals, 0.95)] = "In"
        style_fn = globals().get("resolve_gam_residual_style_map")
        group_order = ["Non", "Adj", "In"]
        for value in pd.unique(pd.Series(groups)):
            if value not in group_order:
                group_order.append(value)
        group_styles = (
            style_fn(group_order) if style_fn is not None
            else {g: {"color": "#B0B0B0", "alpha": 0.45, "size": 22, "zorder": 2, "linewidth": 0.0} for g in group_order}
        )

        fig = plt.figure(figsize=(12, 5.5))
        gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1, 1], wspace=0.25)
        ax_a = fig.add_subplot(gs[0, 0])
        ax_b = fig.add_subplot(gs[0, 1])
        for sub_ax in (ax_a, ax_b):
            sub_ax.spines["top"].set_visible(False)
            sub_ax.spines["right"].set_visible(False)
            sub_ax.tick_params(labelsize=8, length=3.5, direction="in")

        for group in group_order:
            mask = groups == group
            if not np.any(mask):
                continue
            style = dict(group_styles.get(group, {}))
            ax_a.scatter(
                plot_df.loc[mask, x_col], plot_df.loc[mask, y_col],
                c=style.get("color", "#B0B0B0"), alpha=style.get("alpha", 0.45),
                s=style.get("size", 22), linewidths=style.get("linewidth", 0.0),
                zorder=style.get("zorder", 2), label=(group if group != "Non" else "_nolegend_"),
            )
        ax_a.fill_between(smooth_x, lower, upper, color="black", alpha=0.15, linewidth=0, zorder=2)
        ax_a.plot(smooth_x, smooth_y, color="black", linewidth=2.5, zorder=3)
        ax_a.set_xscale("log")
        ax_a.set_yscale("log")
        tick_values = [1e-2, 1e-1, 1, 10, 100, 1000, 10000]
        ax_a.set_xticks([v for v in tick_values if plot_df[x_col].min() <= v <= plot_df[x_col].max()])
        ax_a.xaxis.set_minor_locator(ticker.NullLocator())
        ax_a.yaxis.set_minor_locator(ticker.NullLocator())
        ax_a.text(
            0.10, 0.90, f"$R^2 = {r2:.2f}$", transform=ax_a.transAxes,
            fontsize=13, fontweight="bold", fontstyle="italic", zorder=20,
        )
        ax_a.text(-0.12, 1.03, "a", transform=ax_a.transAxes, fontsize=12, fontweight="bold")
        ax_a.set_xlabel(display_label(x_col, col_map) if col_map else str(x_col))
        ax_a.set_ylabel(display_label(y_col, col_map) if col_map else str(y_col))

        ax_b.axhline(0, color="black", linestyle="--", linewidth=1.0, alpha=0.55, zorder=2)
        for group in group_order:
            mask = groups == group
            if not np.any(mask):
                continue
            style = dict(group_styles.get(group, {}))
            ax_b.scatter(
                plot_df.loc[mask, x_col], residuals[mask],
                c=style.get("color", "#B0B0B0"), alpha=style.get("alpha", 0.45),
                s=style.get("size", 22), linewidths=style.get("linewidth", 0.0),
                zorder=style.get("zorder", 2), label=(group if group != "Non" else "_nolegend_"),
            )
        ax_b.set_xscale("log")
        ax_b.set_xticks([v for v in tick_values if plot_df[x_col].min() <= v <= plot_df[x_col].max()])
        ax_b.xaxis.set_minor_locator(ticker.NullLocator())
        ax_b.text(
            0.07, 0.90, "positive residuals\nindicate hidden links",
            transform=ax_b.transAxes, fontsize=9, color="#333333", zorder=20,
        )
        ax_b.text(-0.12, 1.03, "b", transform=ax_b.transAxes, fontsize=12, fontweight="bold")
        ax_b.set_xlabel(display_label(x_col, col_map) if col_map else str(x_col))
        ax_b.set_ylabel("log residual")
        handles, legend_labels = ax_a.get_legend_handles_labels()
        if legend_labels:
            fig.legend(handles, legend_labels, loc="lower center", bbox_to_anchor=(0.52, -0.02),
                       ncol=min(2, len(legend_labels)), frameon=False, fontsize=8)
            fig.subplots_adjust(bottom=0.16, top=0.94)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        if "gam_log_residual_diagnostic" not in planned_motifs:
            planned_motifs.append("gam_log_residual_diagnostic")
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn(visual_plan, "gam_log_residual_diagnostic")
        count_fn(visual_plan, "confidenceBandCount")
        count_fn(visual_plan, "smoothFitLineCount")
        count_fn(visual_plan, "referenceLineCount")
        count_fn(visual_plan, "residualDiagnosticPanelCount")
        count_fn(visual_plan, "r2AnnotationCount")
        count_fn(visual_plan, "panelLabelCount")
        count_fn(visual_plan, "panelLabelCount")
        return ax_a

    nested_joint_tokens = " ".join(
        str(v).lower()
        for v in [
            bundle_key,
            *patterns,
            *template_motifs,
            x_col,
            y_col,
            method_col or "",
            split_col or "",
            dataProfile.get("domain", ""),
        ]
    )
    use_nested_marginal_joint_matrix = (
        standalone
        and bool(method_col) and method_col in df.columns
        and bool(split_col) and split_col in df.columns
        and method_col != split_col
        and (
            "nested_marginal_joint_matrix" in template_motifs
            or "marginal_joint_matrix" in template_motifs
            or "nested_marginal_joint" in patterns
            or ("marginal" in nested_joint_tokens and "model" in nested_joint_tokens)
        )
    )

    if use_nested_marginal_joint_matrix:
        from matplotlib.gridspec import GridSpecFromSubplotSpec

        plot_df = df[[method_col, split_col, x_col, y_col]].copy()
        plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
        plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
        plot_df = plot_df.dropna(subset=[method_col, split_col, x_col, y_col])
        if plot_df.empty:
            raise ValueError("nested_marginal_joint_matrix requires non-empty model/split/x/y rows")
        models = plot_df[method_col].dropna().astype(str).unique().tolist()[:6]
        splits = plot_df[split_col].dropna().astype(str).unique().tolist()
        style_fn = globals().get("resolve_parity_split_style_map")
        split_styles = (
            style_fn(splits, variant="nested_marginal_joint")
            if style_fn is not None else {}
        )

        def _draw_side_kde(side_ax, values, color, orientation="x"):
            vals = np.asarray(values, dtype=float)
            vals = vals[np.isfinite(vals)]
            if len(vals) < 5 or np.nanstd(vals) <= 1e-12:
                return
            grid = np.linspace(float(vals.min()), float(vals.max()), 120)
            try:
                from scipy.stats import gaussian_kde
                density = gaussian_kde(vals)(grid)
            except Exception:
                hist, edges = np.histogram(vals, bins=18, density=True)
                grid = (edges[:-1] + edges[1:]) / 2
                density = hist
            if orientation == "x":
                side_ax.fill_between(grid, 0, density, color=color, alpha=0.30, linewidth=0)
                side_ax.plot(grid, density, color=color, linewidth=0.8, alpha=0.9)
            else:
                side_ax.fill_betweenx(grid, 0, density, color=color, alpha=0.30, linewidth=0)
                side_ax.plot(density, grid, color=color, linewidth=0.8, alpha=0.9)

        ncols = 3 if len(models) > 2 else max(1, len(models))
        nrows = int(np.ceil(len(models) / max(ncols, 1)))
        fig = plt.figure(figsize=(14, max(4.2, 4.3 * nrows)))
        outer = fig.add_gridspec(nrows, ncols, wspace=0.32, hspace=0.36)
        main_axes = []
        marginal_axes = []
        handles_by_label = {}
        for model_idx, model_name in enumerate(models):
            inner = GridSpecFromSubplotSpec(
                2, 2, subplot_spec=outer[model_idx // ncols, model_idx % ncols],
                width_ratios=[4, 1], height_ratios=[1, 4],
                wspace=0.05, hspace=0.05,
            )
            ax_top = fig.add_subplot(inner[0, 0])
            ax_main = fig.add_subplot(inner[1, 0], sharex=ax_top)
            ax_right = fig.add_subplot(inner[1, 1], sharey=ax_main)
            main_axes.append(ax_main)
            marginal_axes.extend([ax_top, ax_right])
            model_df = plot_df[plot_df[method_col].astype(str) == str(model_name)]
            lo = float(np.nanmin([model_df[x_col].min(), model_df[y_col].min(), 0.0]))
            hi = float(np.nanmax([model_df[x_col].max(), model_df[y_col].max(), 1.0]))
            pad = max((hi - lo) * 0.04, 1e-9)
            ax_main.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
                         color="gray", linestyle="--", alpha=0.62, linewidth=1.0, zorder=0)
            for split in splits:
                split_df = model_df[model_df[split_col].astype(str) == str(split)].sort_values(x_col)
                if split_df.empty:
                    continue
                style = dict(split_styles.get(str(split), {}))
                color = style.get("color", "#d62728")
                scatter = ax_main.scatter(
                    split_df[x_col], split_df[y_col],
                    c=color, s=18, alpha=0.70, label=str(split),
                    edgecolor="white", linewidth=0.35, zorder=4,
                )
                handles_by_label.setdefault(str(split), scatter)
                _draw_side_kde(ax_top, split_df[x_col], color, orientation="x")
                _draw_side_kde(ax_right, split_df[y_col], color, orientation="y")
            residuals = model_df[y_col] - model_df[x_col]
            ss_res = float(np.sum((model_df[y_col] - model_df[x_col]) ** 2))
            ss_tot = float(np.sum((model_df[x_col] - model_df[x_col].mean()) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
            mae = float(np.mean(np.abs(residuals))) if len(residuals) else np.nan
            rmse = float(np.sqrt(np.mean(residuals ** 2))) if len(residuals) else np.nan
            ax_main.text(
                0.95, 0.05, f"R2: {r2:.5f}\nMAE: {mae:.5f}\nRMSE: {rmse:.5f}",
                transform=ax_main.transAxes, ha="right", va="bottom",
                fontsize=5.6, fontweight="bold",
                bbox=dict(facecolor="white", alpha=0.80, edgecolor="none"),
                zorder=8,
            )
            ax_main.set_xlim(lo - pad, hi + pad)
            ax_main.set_ylim(lo - pad, hi + pad)
            ax_main.set_aspect("equal", adjustable="box")
            ax_main.set_title(str(display_label(model_name, col_map) if col_map else model_name),
                              fontsize=7.5, fontweight="bold", pad=2)
            if model_idx // ncols == nrows - 1:
                ax_main.set_xlabel("Actual", fontsize=6.6)
            if model_idx % ncols == 0:
                ax_main.set_ylabel("Predicted", fontsize=6.6)
            ax_main.tick_params(labelsize=5.8, length=2.5)
            for marginal in (ax_top, ax_right):
                marginal.axis("off")
        if handles_by_label:
            legend_labels = [s for s in splits if str(s) in handles_by_label]
            fig.legend(
                [handles_by_label[str(s)] for s in legend_labels],
                [str(s) for s in legend_labels],
                loc="upper center", bbox_to_anchor=(0.5, 0.995),
                ncol=min(2, len(legend_labels)), frameon=False, fontsize=8,
            )
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        if "nested_marginal_joint_matrix" not in planned_motifs:
            planned_motifs.append("nested_marginal_joint_matrix")
        globals().get("_record_template_motif", lambda *args, **kwargs: None)(
            visual_plan, "nested_marginal_joint_matrix"
        )
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        for _ in main_axes:
            count_fn(visual_plan, "referenceLineCount")
            count_fn(visual_plan, "metricBoxCount")
        for _ in marginal_axes:
            count_fn(visual_plan, "marginalAxesCount")
            count_fn(visual_plan, "subAxesCount")
        return main_axes[0]

    parity_tokens = " ".join(
        str(v).lower()
        for v in [
            bundle_key,
            *patterns,
            *template_motifs,
            x_col,
            y_col,
            panel_col or "",
            split_col or "",
            dataProfile.get("domain", ""),
        ]
    )
    use_density_parity_matrix = (
        standalone
        and bool(panel_col) and panel_col in df.columns
        and (
            "density_parity_matrix" in template_motifs
            or "kde_parity_matrix" in template_motifs
            or "density_parity_matrix" in patterns
            or "kde_parity_matrix" in patterns
            or ("parity" in parity_tokens and ("density" in parity_tokens or "kde" in parity_tokens))
        )
    )

    if use_density_parity_matrix:
        drawer = globals().get("draw_density_parity_matrix")
        if drawer is None:
            raise RuntimeError("draw_density_parity_matrix helper is required for density parity matrix")
        result = drawer(
            df,
            actual_col=x_col,
            predicted_col=y_col,
            panel_col=panel_col,
            max_panels=visual_plan.get("densityParityMaxPanels", 2),
            cmap=visual_plan.get("densityParityColormap", visual_plan.get("densityColormap", "jet")),
            scatter_size=visual_plan.get("densityParityScatterSize", 20),
            scatter_alpha=visual_plan.get("densityParityAlpha", 0.90),
            reference_color=visual_plan.get("densityParityReferenceColor", "#D62728"),
            colorbar_label=visual_plan.get("densityParityColorbarLabel", "Density"),
            metric_box=visual_plan.get("densityParityMetricBox", True),
            figsize=tuple(visual_plan.get("densityParityFigsize", [12.0, 5.0])),
            wspace=visual_plan.get("densityParityWspace", 0.30),
            col_map=col_map,
        )
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn(visual_plan, "density_parity_matrix")
        record_fn(visual_plan, "density_encoded_scatter")
        record_fn(visual_plan, "metric_table_in_panel")
        if "prediction_diagnostic_matrix" in template_motifs:
            record_fn(visual_plan, "prediction_diagnostic_matrix")
        for _ in range(result.get("reference_line_count", 0)):
            count_fn(visual_plan, "referenceLineCount")
        for _ in range(result.get("metric_box_count", 0)):
            count_fn(visual_plan, "metricBoxCount")
            count_fn(visual_plan, "metricTextCount")
        for _ in range(result.get("density_scatter_count", 0)):
            count_fn(visual_plan, "densityColorEncodingCount")
            count_fn(visual_plan, "sampleEncodingCount")
        for _ in range(result.get("colorbar_count", 0)):
            count_fn(visual_plan, "colorbarSlotCount")
        visual_plan["densityParityPanelCount"] = result.get("panel_count", 0)
        visual_plan["densityParityScatterCount"] = result.get("density_scatter_count", 0)
        visual_plan["densityParityColorbarCount"] = result.get("colorbar_count", 0)
        visual_plan["densityParityColormap"] = result.get("cmap")
        visual_plan["densitySortedPoints"] = True
        return result["axes"][0]

    use_parity_ci_matrix = (
        standalone
        and bool(panel_col) and panel_col in df.columns
        and bool(split_col) and split_col in df.columns
        and (
            "parity_ci_matrix" in template_motifs
            or "parity_ci_matrix" in patterns
            or ("parity" in parity_tokens and ("ci" in parity_tokens or "confidence" in parity_tokens))
        )
    )

    if use_parity_ci_matrix:
        plot_df = df[[panel_col, split_col, x_col, y_col]].copy()
        plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
        plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
        plot_df = plot_df.dropna(subset=[panel_col, split_col, x_col, y_col])
        if plot_df.empty:
            raise ValueError("parity_ci_matrix requires non-empty panel/split/x/y rows")

        panels = plot_df[panel_col].dropna().astype(str).unique().tolist()[:4]
        splits = plot_df[split_col].dropna().astype(str).unique().tolist()
        style_fn = globals().get("resolve_parity_split_style_map")
        split_styles = (
            style_fn(splits, variant="spt_train_test")
            if style_fn is not None else {}
        )

        def _fit_line_ci(x_values, y_values, grid):
            x_arr = np.asarray(x_values, dtype=float)
            y_arr = np.asarray(y_values, dtype=float)
            if len(x_arr) < 3 or np.nanstd(x_arr) <= 1e-12:
                mean_y = float(np.nanmean(y_arr)) if len(y_arr) else 0.0
                return np.full_like(grid, mean_y), np.full_like(grid, mean_y), np.full_like(grid, mean_y)
            slope, intercept = np.polyfit(x_arr, y_arr, 1)
            pred = slope * grid + intercept
            resid = y_arr - (slope * x_arr + intercept)
            se = float(np.sqrt(np.sum(resid ** 2) / max(len(x_arr) - 2, 1)))
            x_mean = float(np.nanmean(x_arr))
            denom = float(np.sum((x_arr - x_mean) ** 2))
            spread = se * np.sqrt(1 / max(len(x_arr), 1) + (grid - x_mean) ** 2 / max(denom, 1e-12))
            return pred, pred - 1.96 * spread, pred + 1.96 * spread

        fig = plt.figure(figsize=(12, 10))
        gs = fig.add_gridspec(2, 2, wspace=0.25, hspace=0.25)
        axes = [fig.add_subplot(gs[i // 2, i % 2]) for i in range(len(panels))]
        handles_by_label = {}
        for idx, (sub_ax, panel_value) in enumerate(zip(axes, panels)):
            panel_df = plot_df[plot_df[panel_col].astype(str) == str(panel_value)]
            lo = float(np.nanmin([panel_df[x_col].min(), panel_df[y_col].min(), 0.0]))
            hi = float(np.nanmax([panel_df[x_col].max(), panel_df[y_col].max()]))
            pad = max((hi - lo) * 0.04, 1e-9)
            sub_ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
                        color="maroon", linestyle="--", linewidth=2.0, zorder=2)
            for split in splits:
                split_df = panel_df[panel_df[split_col].astype(str) == str(split)].sort_values(x_col)
                if split_df.empty:
                    continue
                style = dict(split_styles.get(str(split), {}))
                color = style.get("color", "#313695")
                sub_ax.scatter(
                    split_df[x_col], split_df[y_col],
                    c="none", edgecolors=style.get("markeredgecolor", color),
                    s=style.get("scatter_size", 54),
                    alpha=style.get("scatter_alpha", 0.72),
                    linewidths=1.1, marker=style.get("marker", "o"),
                    label=str(split), zorder=style.get("zorder_scatter", 5),
                )
                grid = np.linspace(lo, hi, 120)
                reg, ci_low, ci_high = _fit_line_ci(split_df[x_col], split_df[y_col], grid)
                line = sub_ax.plot(
                    grid, reg, color=color, linewidth=style.get("linewidth", 2.0),
                    alpha=0.85, zorder=style.get("zorder_line", 4),
                )[0]
                sub_ax.fill_between(
                    grid, ci_low, ci_high, color=color,
                    alpha=style.get("ci_alpha", 0.15), linewidth=0,
                    zorder=style.get("zorder_band", 3),
                )
                handles_by_label.setdefault(str(split), line)
            residuals = panel_df[y_col] - panel_df[x_col]
            ss_res = float(np.sum((panel_df[y_col] - panel_df[x_col]) ** 2))
            ss_tot = float(np.sum((panel_df[x_col] - panel_df[x_col].mean()) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
            rmse = float(np.sqrt(np.mean(residuals ** 2))) if len(residuals) else np.nan
            sub_ax.text(
                0.05, 0.95, f"$\\mathbf{{R^2: {r2:.2f}}}$\nRMSE: {rmse:.2f}",
                transform=sub_ax.transAxes, fontsize=8, fontweight="bold",
                color="#A50026", va="top",
                bbox=dict(facecolor="white", alpha=0.62, edgecolor="none"),
                zorder=10,
            )
            sub_ax.text(
                -0.15, 1.05, chr(ord("a") + idx),
                transform=sub_ax.transAxes, fontsize=14, fontweight="bold",
                va="top", ha="right", zorder=12,
            )
            sub_ax.set_title(str(display_label(panel_value, col_map) if col_map else panel_value),
                             fontsize=8.5, fontweight="bold")
            sub_ax.set_xlim(lo - pad, hi + pad)
            sub_ax.set_ylim(lo - pad, hi + pad)
            sub_ax.set_aspect("equal", adjustable="box")
            sub_ax.set_xlabel("Actual")
            sub_ax.set_ylabel("Predicted")
            sub_ax.tick_params(labelsize=6, length=3)
        if handles_by_label:
            legend_labels = [s for s in splits if str(s) in handles_by_label]
            fig.legend(
                [handles_by_label[str(s)] for s in legend_labels],
                [str(s) for s in legend_labels],
                loc="upper center", bbox_to_anchor=(0.5, 0.99),
                ncol=min(2, len(legend_labels)), frameon=False, fontsize=8,
            )
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        if "parity_ci_matrix" not in planned_motifs:
            planned_motifs.append("parity_ci_matrix")
        globals().get("_record_template_motif", lambda *args, **kwargs: None)(
            visual_plan, "parity_ci_matrix"
        )
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        for _ in axes:
            count_fn(visual_plan, "referenceLineCount")
            count_fn(visual_plan, "metricBoxCount")
            count_fn(visual_plan, "panelLabelCount")
        return axes[0]

    adsorption_tokens = " ".join(
        str(v).lower()
        for v in [
            bundle_key,
            *patterns,
            *template_motifs,
            x_col,
            y_col,
            panel_col or "",
            method_col or "",
            dataProfile.get("domain", ""),
        ]
    )
    use_adsorption_isotherm_board = (
        standalone
        and bool(panel_col) and panel_col in df.columns
        and bool(method_col) and method_col in df.columns
        and (
        "adsorption_isotherm_multipanel" in template_motifs
        or "adsorption_isotherm" in patterns
        or "isotherm" in adsorption_tokens
        or "adsorption" in adsorption_tokens
        )
    )

    if use_adsorption_isotherm_board:
        plot_df = df[[panel_col, method_col, x_col, y_col]].copy()
        plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
        plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
        plot_df = plot_df.dropna(subset=[panel_col, method_col, x_col, y_col])
        if plot_df.empty:
            raise ValueError("adsorption_isotherm_multipanel requires non-empty panel/method/x/y rows")
        panels = plot_df[panel_col].dropna().astype(str).unique().tolist()[:6]
        methods = plot_df[method_col].dropna().astype(str).unique().tolist()
        style_fn = globals().get("resolve_method_style_map")
        method_styles = (
            style_fn(methods, variant="cej_adsorption")
            if style_fn is not None else {}
        )
        ncols = 3 if len(panels) > 2 else len(panels)
        nrows = int(np.ceil(len(panels) / max(ncols, 1)))
        fig = plt.figure(figsize=(15 * (1 / 1.35), max(5.2, 3.4 * nrows)))
        gs = fig.add_gridspec(nrows, ncols, wspace=0.30, hspace=0.34)
        axes = []
        handles_by_label = {}
        floor_fn = globals().get("apply_scatter_regression_floor")
        for idx, panel_value in enumerate(panels):
            sub_ax = fig.add_subplot(gs[idx // ncols, idx % ncols])
            axes.append(sub_ax)
            if floor_fn is not None:
                try:
                    floor_fn(sub_ax, despine=True, grid_axis="both")
                except Exception:
                    sub_ax.grid(True, linestyle="--", color="#E0E0E0", linewidth=0.45, alpha=0.65, zorder=0)
            else:
                sub_ax.grid(True, linestyle="--", color="#E0E0E0", linewidth=0.45, alpha=0.65, zorder=0)
            panel_df = plot_df[plot_df[panel_col].astype(str) == str(panel_value)]
            for method in methods:
                method_df = panel_df[panel_df[method_col].astype(str) == str(method)].sort_values(x_col)
                if method_df.empty:
                    continue
                style = dict(method_styles.get(str(method), {}))
                color = style.get("color", "#4A6B8A")
                marker = style.get("marker", "o")
                linestyle = style.get("linestyle", "-")
                zorder = style.get("zorder", 3)
                draw = style.get("draw", "line_marker")
                if draw == "hollow_marker" or linestyle == "None":
                    handle = sub_ax.plot(
                        method_df[x_col], method_df[y_col],
                        linestyle="None", marker=marker, markersize=4.2,
                        markerfacecolor=style.get("markerfacecolor", "white"),
                        markeredgecolor=style.get("markeredgecolor", color),
                        markeredgewidth=0.9, color=color, label=str(method),
                        zorder=zorder,
                    )[0]
                else:
                    handle = sub_ax.plot(
                        method_df[x_col], method_df[y_col],
                        linestyle=linestyle, marker=marker, markersize=3.4,
                        markerfacecolor=style.get("markerfacecolor", color),
                        markeredgecolor=style.get("markeredgecolor", color),
                        color=color, linewidth=1.25, label=str(method),
                        zorder=zorder,
                    )[0]
                handles_by_label.setdefault(str(method), handle)
            sub_ax.text(
                -0.15, 1.06, f"({chr(ord('a') + idx)})",
                transform=sub_ax.transAxes, fontsize=8.5, fontweight="bold",
                va="top", ha="right", zorder=20,
            )
            sub_ax.text(
                0.04, 0.91, str(display_label(panel_value, col_map) if col_map else panel_value),
                transform=sub_ax.transAxes, fontsize=6.2, fontweight="bold",
                ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.16", facecolor="white",
                          edgecolor="#BBBBBB", linewidth=0.35, alpha=0.88),
                zorder=15,
            )
            if idx // ncols == nrows - 1:
                sub_ax.set_xlabel(display_label(x_col, col_map) if col_map else x_col)
            if idx % ncols == 0:
                sub_ax.set_ylabel(display_label(y_col, col_map) if col_map else y_col)
            sub_ax.tick_params(labelsize=6, length=2.5)
        legend_labels = [m for m in methods if str(m) in handles_by_label]
        if legend_labels:
            fig.legend(
                [handles_by_label[str(m)] for m in legend_labels],
                [str(m) for m in legend_labels],
                loc="lower center", bbox_to_anchor=(0.5, 0.01),
                ncol=min(4, len(legend_labels)), frameon=True, fontsize=6.2,
                borderpad=0.3, handlelength=2.0,
            )
        fig.subplots_adjust(bottom=0.10, top=0.94)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        if "adsorption_isotherm_multipanel" not in planned_motifs:
            planned_motifs.append("adsorption_isotherm_multipanel")
        globals().get("_record_template_motif", lambda *args, **kwargs: None)(
            visual_plan, "adsorption_isotherm_multipanel"
        )
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        for _ in axes:
            count_fn(visual_plan, "panelLabelCount")
        return axes[0]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    # ─── L0 floor: light dashed grid + despine (corpus anchor: GAM scatter+
    # residual Nature, R² scatter, distance-decay scatter). Phase A1 made
    # apply_scatter_regression_floor reachable from generated runtime; prefer
    # the canonical template_mining_helpers version over inline ax.grid calls.
    floor_fn = globals().get("apply_scatter_regression_floor")
    if floor_fn is not None:
        try:
            floor_fn(ax, despine=True, grid_axis="both")
        except Exception:
            pass

    plot_cols = [x_col, y_col]
    for optional_col in (split_col, interaction_col if is_shap_dependence else None, feature_name_col if is_shap_dependence else None):
        if optional_col and optional_col in df.columns and optional_col not in plot_cols:
            plot_cols.append(optional_col)
    plot_df = df[plot_cols].copy()
    plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[x_col, y_col])
    use_marginal_joint = (
        standalone
        and not is_shap_dependence
        and len(plot_df) >= 30
        and (
            visual_plan.get("useMarginalAxes")
            or "joint_marginal_grid" in template_motifs
            or "marginal_joint" in template_families
            or (is_prediction_report and (bundle_key == "rf_model_performance_report" or "prediction_diagnostic" in patterns))
        )
    )
    if use_marginal_joint:
        visual_plan["useMarginalAxes"] = True
        visual_plan["useDensityColorEncoding"] = True
        visual_plan.setdefault("reserveMarginalTitleGap", False)
        visual_plan.setdefault("marginalTopGap", 0.008)
        visual_plan.setdefault("marginalSideGap", 0.008)
        visual_plan.setdefault("marginalColor", "#69b3a2")
        visual_plan.setdefault("densityColormap", "GnBu_r")
        visual_plan.setdefault("densityColorMethod", "kde")
        if "joint_marginal_grid" not in visual_plan.get("templateMotifs", []):
            visual_plan.setdefault("templateMotifs", []).append("joint_marginal_grid")
        if "density_encoded_scatter" not in visual_plan.get("templateMotifs", []):
            visual_plan.setdefault("templateMotifs", []).append("density_encoded_scatter")

    if is_shap_dependence:
        if interaction_col and interaction_col in plot_df.columns:
            plot_df[interaction_col] = pd.to_numeric(plot_df[interaction_col], errors="coerce")
            color_values = plot_df[interaction_col]
        else:
            color_values = None

        scatter_kwargs = dict(
            s=18 if standalone else 12,
            alpha=0.76,
            edgecolors="white",
            linewidth=0.28,
            zorder=4,
        )
        if color_values is not None and color_values.notna().any():
            sc = ax.scatter(
                plot_df[x_col], plot_df[y_col],
                c=color_values, cmap="RdYlBu_r", **scatter_kwargs,
            )
        else:
            sc = ax.scatter(
                plot_df[x_col], plot_df[y_col],
                color="#1F4E79", **scatter_kwargs,
            )

        # SHAP value zero divider — delegate to template_mining_helpers when reachable
        canonical_zero_ref = globals().get("add_zero_reference")
        if canonical_zero_ref is not None:
            try:
                canonical_zero_ref(ax, axis="y", color="black", lw=0.8, ls="-", zorder=3)
            except Exception:
                ax.axhline(0, color="black", linewidth=0.8, zorder=3)
        else:
            ax.axhline(0, color="black", linewidth=0.8, zorder=3)
        if plot_df[x_col].nunique() >= 4:
            for q in np.nanquantile(plot_df[x_col], [0.25, 0.5, 0.75]):
                ax.axvline(q, color="#8A8A8A", linewidth=0.35, linestyle=":", alpha=0.55, zorder=1)

        if plot_df[x_col].nunique() >= 3 and len(plot_df) >= 5:
            deg = 2 if plot_df[x_col].nunique() >= 5 else 1
            z = np.polyfit(plot_df[x_col], plot_df[y_col], deg)
            p_line = np.poly1d(z)
            xs = np.linspace(plot_df[x_col].min(), plot_df[x_col].max(), 140)
            ax.plot(xs, p_line(xs), color="#D55E00", lw=1.05, zorder=5)

        feature_label = None
        if feature_name_col and feature_name_col in plot_df.columns:
            values = plot_df[feature_name_col].dropna().astype(str).unique().tolist()
            if len(values) == 1:
                feature_label = values[0]
        mean_abs = float(np.nanmean(np.abs(plot_df[y_col]))) if len(plot_df) else np.nan
        effect_range = float(np.nanmax(plot_df[y_col]) - np.nanmin(plot_df[y_col])) if len(plot_df) else np.nan
        label_lines = []
        if feature_label:
            label_lines.append(feature_label)
        label_lines.extend([f"n={len(plot_df)}", f"mean|SHAP|={mean_abs:.3g}", f"range={effect_range:.3g}"])
        ax.text(
            0.04, 0.96, "\n".join(label_lines),
            transform=ax.transAxes, ha="left", va="top", fontsize=5.2,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.35, alpha=0.92),
            zorder=7,
        )
        if feature_label and not standalone:
            ax.set_title(feature_label, fontsize=6, pad=2)
        if standalone and color_values is not None and color_values.notna().any():
            cbar = ax.figure.colorbar(sc, ax=ax, fraction=0.045, pad=0.025)
            cbar.set_label("Interaction value", fontsize=6)
            cbar.ax.tick_params(labelsize=5, length=2)
        ax.set_xlabel(display_label(x_col, col_map) if (standalone and col_map) else ("Feature value" if standalone else ""))
        ax.set_ylabel("")
        if standalone:
            ax.text(
                0.015, 0.52, "SHAP value",
                transform=ax.transAxes, rotation=90, ha="left", va="center",
                fontsize=6, color="#222222",
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.72),
                zorder=8,
            )
        if standalone:
            apply_chart_polish(ax, "scatter_regression")
        return ax

    density_scatter = None
    if is_prediction_report:
        split_styles = {
            "train": ("s", "#F6CFA3"),
            "training": ("s", "#F6CFA3"),
            "test": ("^", "#9BCBEB"),
            "testing": ("^", "#9BCBEB"),
            "valid": ("D", "#CFE8CF"),
            "validation": ("D", "#CFE8CF"),
            "external": ("v", "#B7C9E2"),
        }
        groups = [(None, plot_df)] if not split_col or split_col not in plot_df.columns else list(plot_df.groupby(split_col))
        fallback = palette.get("categorical", ["#1F4E79", "#D55E00", "#009E73"])
        if use_marginal_joint and "_overlay_density_colored_points" in globals():
            density_scatter = _overlay_density_colored_points(ax, plot_df[x_col], plot_df[y_col], visual_plan)
        if density_scatter is None or (split_col and split_col in plot_df.columns):
            for i, (name, grp) in enumerate(groups):
                label = "samples" if name is None else str(name)
                marker, color = split_styles.get(label.lower(), ("o", fallback[i % len(fallback)]))
                ax.scatter(
                    grp[x_col], grp[y_col], marker=marker, s=18 if density_scatter is not None else 22,
                    facecolors="none", edgecolors=color, linewidth=0.55 if density_scatter is not None else 0.75,
                    alpha=0.62 if density_scatter is not None else 0.9, label=label, zorder=7 if density_scatter is not None else 3,
                )
        lo = float(np.nanmin([plot_df[x_col].min(), plot_df[y_col].min()]))
        hi = float(np.nanmax([plot_df[x_col].max(), plot_df[y_col].max()]))
        pad = max((hi - lo) * 0.04, 1e-9)
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="black", lw=0.8, ls="--", label="1:1", zorder=2)
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(lo - pad, hi + pad)
        if use_marginal_joint:
            ax.set_aspect("equal", adjustable="box")
        residuals = plot_df[y_col] - plot_df[x_col]
        ss_res = float(np.sum((plot_df[y_col] - plot_df[x_col]) ** 2))
        ss_tot = float(np.sum((plot_df[x_col] - plot_df[x_col].mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rmse = float(np.sqrt(np.mean(residuals ** 2))) if len(residuals) else np.nan
        mae = float(np.mean(np.abs(residuals))) if len(residuals) else np.nan
        ax.text(
            0.05, 0.95, f"R2={r2:.3f}\nRMSE={rmse:.3g}\nMAE={mae:.3g}",
            transform=ax.transAxes, ha="left", va="top", fontsize=5.2,
            bbox=dict(
                boxstyle=("square,pad=0.30" if use_marginal_joint else "round,pad=0.22"),
                facecolor="white", edgecolor="#333333",
                linewidth=(0.8 if use_marginal_joint else 0.4), alpha=0.92,
            ),
            zorder=(20 if use_marginal_joint else 6),
        )
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(frameon=False, fontsize=5, ncol=min(4, len(labels)))
    else:
        if use_marginal_joint and "_overlay_density_colored_points" in globals():
            density_scatter = _overlay_density_colored_points(ax, plot_df[x_col], plot_df[y_col], visual_plan)
        if density_scatter is None:
            ax.scatter(plot_df[x_col], plot_df[y_col], c="#000000", s=15, alpha=0.7,
                       linewidth=0.3, edgecolors="white")

    z = np.polyfit(plot_df[x_col], plot_df[y_col], 1)
    p_line = np.poly1d(z)
    xs = np.linspace(plot_df[x_col].min(), plot_df[x_col].max(), 100)
    ax.plot(xs, p_line(xs), color="#D55E00", lw=1, ls="--")

    r = np.corrcoef(plot_df[x_col], plot_df[y_col])[0, 1]
    if not is_prediction_report:
        ax.text(0.05, 0.95, f"r = {r:.3f}", transform=ax.transAxes, fontsize=6, va="top")

    ax.set_xlabel(("Actual" if is_prediction_report else x_col) if standalone else "")
    ax.set_ylabel(("Predicted" if is_prediction_report else y_col) if standalone else "")
    if use_marginal_joint and "_add_marginal_distribution_axes" in globals():
        marginal_axes = _add_marginal_distribution_axes(
            ax, plot_df[x_col], plot_df[y_col], visual_plan,
            color=visual_plan.get("marginalColor", palette.get("categorical", ["#69B3A2"])[0]),
        )
        if density_scatter is not None:
            if marginal_axes:
                right_ax = marginal_axes[1]
                pos = right_ax.get_position()
                cbar_x = min(pos.x1 + 0.01, 0.965)
                cax = ax.figure.add_axes([cbar_x, pos.y0, 0.010, pos.height])
                cbar = ax.figure.colorbar(density_scatter, cax=cax)
            else:
                cbar = ax.figure.colorbar(density_scatter, ax=ax, fraction=0.04, pad=0.025)
            cbar.set_label("Density", fontsize=5.5)
            cbar.ax.tick_params(labelsize=4.8, length=2)
            globals().get("_visual_count", lambda *args, **kwargs: None)(visual_plan, "colorbarSlotCount")
    if standalone:
        apply_chart_polish(ax, "scatter_regression")
    return ax


def gen_spatial_feature(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Spatial feature plot with spot coordinates colored by expression/value."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("spatial_x") or roles.get("x")
    y_col = roles.get("spatial_y") or roles.get("y")
    value_col = roles.get("value") or roles.get("feature") or roles.get("score")
    group_col = roles.get("group")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if x_col is None and len(numeric_cols) >= 1:
        x_col = numeric_cols[0]
    if y_col is None and len(numeric_cols) >= 2:
        y_col = numeric_cols[1]
    if x_col is None or y_col is None:
        raise ValueError("spatial_feature requires spatial x/y coordinates")

    if standalone:
        fig, ax = plt.subplots(figsize=(80 * (1 / 25.4), 80 * (1 / 25.4)),
                           constrained_layout=True)

    if value_col and value_col in df.columns:
        sc = ax.scatter(df[x_col], df[y_col], c=df[value_col], cmap="viridis",
                        s=12, alpha=0.85, linewidth=0)
        cbar = plt.colorbar(sc, ax=ax, shrink=0.65, pad=0.02)
        cbar.set_label(_display_col(value_col, col_map), fontsize=5)
    elif group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            sub = df[df[group_col] == cat]
            ax.scatter(sub[x_col], sub[y_col], color=color_map[cat], s=12,
                       alpha=0.85, linewidth=0, label=str(cat))
        ax.legend(loc="upper right", frameon=False, fontsize=5)
    else:
        ax.scatter(df[x_col], df[y_col], color=palette.get("categorical", ["#1F4E79"])[0],
                   s=12, alpha=0.85, linewidth=0)
    ax.set_xlabel(_display_col(x_col, col_map))
    ax.set_ylabel(_display_col(y_col, col_map))
    ax.set_aspect("equal", adjustable="datalim")
    if standalone:
        apply_chart_polish(ax, "spatial_feature")
    return ax


def gen_tsne(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """t-SNE embedding scatter, using supplied tSNE coordinates when present."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("tsne_1") or roles.get("tsne1") or roles.get("x")
    y_col = roles.get("tsne_2") or roles.get("tsne2") or roles.get("y")
    group_col = roles.get("group") or roles.get("cell_type")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if x_col is None or y_col is None:
        if len(numeric_cols) < 2:
            raise ValueError("tsne requires tSNE coordinates or at least two numeric columns")
        matrix = df[numeric_cols].fillna(0).to_numpy(dtype=float)
        matrix = matrix - matrix.mean(axis=0, keepdims=True)
        _, _, vt = np.linalg.svd(matrix, full_matrices=False)
        coords = matrix @ vt[:2].T
        x_vals, y_vals = coords[:, 0], coords[:, 1]
        x_label, y_label = "tSNE 1 (fallback embedding)", "tSNE 2 (fallback embedding)"
    else:
        x_vals, y_vals = df[x_col].astype(float).values, df[y_col].astype(float).values
        x_label, y_label = "tSNE 1", "tSNE 2"

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            mask = df[group_col] == cat
            ax.scatter(x_vals[mask], y_vals[mask], s=12, alpha=0.75,
                       color=color_map[cat], edgecolors="white", linewidth=0.25,
                       label=str(cat))
        ax.legend(loc="upper right", frameon=False, fontsize=5)
    else:
        ax.scatter(x_vals, y_vals, s=12, alpha=0.75,
                   color=palette.get("categorical", ["#1F4E79"])[0],
                   edgecolors="white", linewidth=0.25)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if standalone:
        apply_chart_polish(ax, "tsne")
    return ax


def gen_umap(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """UMAP/tSNE embedding scatter plot with optional color-by metadata."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 78 * (1 / 25.4)), constrained_layout=True)

    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("umap_1") or roles.get("x")
    y_col = roles.get("umap_2") or roles.get("y")
    group_col = roles.get("group") or roles.get("cell_type")

    if not x_col or not y_col:
        raise ValueError("umap requires 'x'/'umap_1' and 'y'/'umap_2' in semanticRoles")

    if group_col and group_col in df.columns:
        groups = df[group_col].unique().tolist()
        color_map = _extract_colors(palette, groups)
        fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])
        for i, grp in enumerate(groups):
            mask = df[group_col] == grp
            color = color_map.get(grp, fallback_colors[i % len(fallback_colors)])
            ax.scatter(df[mask][x_col], df[mask][y_col], s=3, alpha=0.6, color=color,
                      label=display_label(grp, col_map), edgecolor="none", rasterized=True)
        ax.legend(fontsize=4.5, markerscale=2, frameon=False, loc="upper right")
    else:
        ax.scatter(df[x_col], df[y_col], s=3, alpha=0.6, color="#1F4E79", edgecolor="none", rasterized=True)

    ax.set_xlabel(display_label(x_col, col_map), fontsize=5)
    ax.set_ylabel(display_label(y_col, col_map), fontsize=5)
    ax.set_xticks([])
    ax.set_yticks([])
    if standalone:
        apply_chart_polish(ax, "umap")
    return ax
