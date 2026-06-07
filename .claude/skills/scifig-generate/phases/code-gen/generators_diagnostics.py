"""Statistical-diagnostic chart generators (qq/pp/residual/...).

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

    # Diagonal reference line — delegate to template_mining_helpers when reachable
    canonical_diagonal = globals().get("add_perfect_fit_diagonal")
    if canonical_diagonal is not None:
        try:
            canonical_diagonal(ax, np.asarray([0.0, 1.0]), np.asarray([0.0, 1.0]),
                               color="black", lw=0.6, alpha=1.0)
        except Exception:
            ax.plot([0, 1], [0, 1], color="black", linewidth=0.6, linestyle="--", zorder=1)
    else:
        ax.plot([0, 1], [0, 1], color="black", linewidth=0.6, linestyle="--", zorder=1)

    ax.set_xlabel("Expected cumulative probability")
    ax.set_ylabel("Observed cumulative probability")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    if standalone:
        apply_chart_polish(ax, "pp_plot")
    return ax


def gen_qq(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Q-Q plot for p-value calibration in association tests."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    p_col = roles.get("pvalue") or roles.get("p_value") or roles.get("padj") or roles.get("value")
    if p_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        p_col = numeric_cols[0] if numeric_cols else None
    if p_col is None:
        raise ValueError("qq requires a p-value column")

    pvals = np.sort(df[p_col].dropna().astype(float).clip(lower=1e-300, upper=1.0).values)
    n = len(pvals)
    expected = -np.log10((np.arange(1, n + 1) - 0.5) / n)
    observed = -np.log10(pvals)

    if standalone:
        fig, ax = plt.subplots(figsize=(70 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)

    ax.scatter(expected, observed, s=9, alpha=0.65, color=palette.get("categorical", ["#1F4E79"])[0],
               edgecolors="white", linewidth=0.25)
    lim = max(expected.max(), observed.max()) * 1.05
    # Q-Q reference diagonal — delegate to template_mining_helpers when reachable
    canonical_diagonal = globals().get("add_perfect_fit_diagonal")
    if canonical_diagonal is not None:
        try:
            canonical_diagonal(ax, np.asarray([0.0, lim]), np.asarray([0.0, lim]),
                               color="#333333", lw=0.6, alpha=1.0)
        except Exception:
            ax.plot([0, lim], [0, lim], color="#333333", lw=0.6, ls="--")
    else:
        ax.plot([0, lim], [0, lim], color="#333333", lw=0.6, ls="--")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Expected -log10(p)")
    ax.set_ylabel("Observed -log10(p)")
    if standalone:
        apply_chart_polish(ax, "qq")
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
    fitted_col = roles.get("fitted") or roles.get("predicted") or roles.get("prediction") or roles.get("x")
    resid_col = roles.get("residual") or roles.get("value")
    actual_col = roles.get("actual") or roles.get("observed") or roles.get("measured")
    split_col = roles.get("split") or roles.get("sample_type") or roles.get("source") or roles.get("cohort") or roles.get("group")
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    is_rf_report = (
        template_case.get("bundleKey") == "rf_model_performance_report"
        or "model_performance_benchmark" in patterns
        or "ml_model_family" in patterns
        or "prediction_diagnostic" in patterns
        or (actual_col and fitted_col)
    )

    working_df = df.copy()
    if resid_col is None and actual_col and fitted_col and actual_col in working_df.columns and fitted_col in working_df.columns:
        resid_col = "_scifig_residual"
        working_df[resid_col] = pd.to_numeric(working_df[actual_col], errors="coerce") - pd.to_numeric(working_df[fitted_col], errors="coerce")

    if fitted_col is None or resid_col is None:
        raise ValueError("residual_vs_fitted requires 'fitted' and 'residual' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    # Apply L0 scatter-regression floor — delegate to template_mining_helpers
    # when reachable. Sets up light dashed grid + despine BEFORE scatter so the
    # grid sits at zorder=0 and residual-vs-fitted reads as a regression diagnostic.
    canonical_floor = globals().get("apply_scatter_regression_floor")
    if canonical_floor is not None:
        try:
            canonical_floor(ax, grid_axis="both")
        except Exception:
            pass

    plot_df = working_df[[fitted_col, resid_col] + ([split_col] if split_col and split_col in working_df.columns else [])].copy()
    plot_df[fitted_col] = pd.to_numeric(plot_df[fitted_col], errors="coerce")
    plot_df[resid_col] = pd.to_numeric(plot_df[resid_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[fitted_col, resid_col])

    if is_rf_report:
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
        for i, (name, grp) in enumerate(groups):
            label = "samples" if name is None else str(name)
            marker, color = split_styles.get(label.lower(), ("o", palette.get("categorical", ["#0072B2"])[i % len(palette.get("categorical", ["#0072B2"]))]))
            ax.scatter(
                grp[fitted_col], grp[resid_col], marker=marker, s=20,
                facecolors="none", edgecolors=color, linewidth=0.75,
                alpha=0.88, label=label, zorder=3,
            )
        # Zero-reference line — delegate to template_mining_helpers when reachable
        canonical_zero_ref = globals().get("add_zero_reference")
        if canonical_zero_ref is not None:
            try:
                canonical_zero_ref(ax, axis="y", color="#B00000", lw=0.85, ls="--", zorder=2)
            except Exception:
                ax.axhline(0, color="#B00000", linewidth=0.85, linestyle="--", zorder=2)
        else:
            ax.axhline(0, color="#B00000", linewidth=0.85, linestyle="--", zorder=2)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.28, zorder=0)
        bias = float(plot_df[resid_col].mean()) if len(plot_df) else 0.0
        spread = float(plot_df[resid_col].std()) if len(plot_df) > 1 else 0.0
        ax.text(
            0.98, 0.94, f"bias={bias:.3g}\nSD={spread:.3g}\nn={len(plot_df)}",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.2,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.92),
            zorder=6,
        )
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(frameon=False, fontsize=5, ncol=min(3, len(labels)))
    else:
        color = palette.get("categorical", ["#0072B2"])[0]
        ax.scatter(plot_df[fitted_col], plot_df[resid_col], s=10, alpha=0.5, color=color,
                   linewidth=0.3, edgecolor="white", zorder=2)
        # Zero-reference line — delegate to template_mining_helpers when reachable
        canonical_zero_ref = globals().get("add_zero_reference")
        if canonical_zero_ref is not None:
            try:
                canonical_zero_ref(ax, axis="y", color="black", lw=0.6, ls="--", zorder=1)
            except Exception:
                ax.axhline(0, color="black", linewidth=0.6, linestyle="--", zorder=1)
        else:
            ax.axhline(0, color="black", linewidth=0.6, linestyle="--", zorder=1)

    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess
        smoothed = lowess(plot_df[resid_col], plot_df[fitted_col], frac=0.3)
        ax.plot(smoothed[:, 0], smoothed[:, 1], color="#C8553D", linewidth=0.8,
                solid_capstyle="round", zorder=4)
    except Exception:
        pass

    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residual" if standalone else "")
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

    # Apply L0 scatter-regression floor — delegate to template_mining_helpers
    # when reachable. Light dashed grid + despine BEFORE drawing scatter, so the
    # grid sits at zorder=0 and the homoscedasticity check reads as a regression
    # diagnostic panel rather than a generic scatter.
    canonical_floor = globals().get("apply_scatter_regression_floor")
    if canonical_floor is not None:
        try:
            canonical_floor(ax, grid_axis="both")
        except Exception:
            pass

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
