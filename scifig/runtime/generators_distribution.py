"""Distribution-family chart generators (violin/box/strip/ridge/histogram/...).

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


def _resolve_roles(dataProfile):
    """Extract semantic roles from dataProfile."""
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")
    x_col = roles.get("x") or roles.get("condition")
    return group_col, value_col, x_col


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
        ax.legend(loc="upper right", frameon=False, fontsize=5)
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
        ax.legend(loc="upper right", frameon=False, fontsize=5)
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
        ax.legend(loc="upper right", frameon=False, fontsize=5)
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


def gen_raincloud(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Raincloud plot: half-violin + box + individual points. Publication-grade distribution comparison."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 62 * (1 / 25.4)), constrained_layout=True)

    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")
    if not group_col or not value_col:
        raise ValueError("raincloud requires 'group' and 'value' in semanticRoles")

    groups = df[group_col].unique().tolist()
    color_map = _extract_colors(palette, groups)
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    for i, grp in enumerate(groups):
        vals = df[df[group_col] == grp][value_col].dropna().values
        if len(vals) == 0:
            continue
        color = color_map.get(grp, fallback_colors[i % len(fallback_colors)])
        y_pos = i

        # Half violin (right side)
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(vals)
        y_range = np.linspace(vals.min(), vals.max(), 200)
        density = kde(y_range)
        density = density / density.max() * 0.3  # scale to 0.3 width
        ax.fill_betweenx(y_range, y_pos, y_pos + density, alpha=0.3, color=color, linewidth=0)
        ax.plot(y_pos + density, y_range, color=color, linewidth=0.6)

        # Box (left side)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        ax.plot([y_pos - 0.15, y_pos - 0.15], [q1, q3], color=color, linewidth=1.2, solid_capstyle="round")
        ax.scatter(y_pos - 0.15, med, color=color, s=15, zorder=3, edgecolor="white", lw=0.3)

        # Individual points (jittered)
        jitter = np.random.default_rng(42).uniform(-0.08, 0.08, len(vals))
        ax.scatter(y_pos + jitter - 0.15, vals, color=color, s=4, alpha=0.5, zorder=2, edgecolor="none")

    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([display_label(g, col_map) for g in groups])
    ax.set_xlabel(display_label(value_col, col_map))
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "raincloud")
    return ax


def gen_ridge(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Ridgeline / joy plot for many groups.

    Overlapping density ridges stacked vertically.  Uses Gaussian KDE with
    shared bandwidth across groups.  Groups ordered by median value.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col, value_col, _ = _resolve_roles(dataProfile)
    visual_plan = chartPlan.get("visualContentPlan", {})
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        chartPlan["visualContentPlan"] = visual_plan
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    template_motifs = {str(m).lower() for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs") or [])}
    lower_to_col = {str(col).lower(): col for col in df.columns}

    def _first_column(*names):
        for name in names:
            if not name:
                continue
            if name in df.columns:
                return name
            lowered = str(name).lower()
            if lowered in lower_to_col:
                return lower_to_col[lowered]
        return None

    use_bayesian_ridge_heatmap = (
        standalone
        and (
            visual_plan.get("useBayesianRidgeHeatmapBoard")
            or "bayesian_ridge_heatmap_board" in template_motifs
            or "ridge_heatmap_composite" in template_motifs
            or "bayesian_ridge_heatmap_board" in patterns
            or "ridge_heatmap_composite" in patterns
        )
    )
    if use_bayesian_ridge_heatmap:
        draw_fn = globals().get("draw_bayesian_ridge_heatmap_board")
        if draw_fn is None:
            raise RuntimeError("draw_bayesian_ridge_heatmap_board helper is required for gen_ridge")
        condition_col = _first_column(roles.get("condition"), roles.get("panel"), roles.get("soc_group"), "condition", "soc_group", "panel")
        factor_col = _first_column(roles.get("factor"), roles.get("feature"), roles.get("group"), "factor", "feature", "variable")
        draw_col = _first_column(roles.get("posterior"), roles.get("value"), roles.get("effect"), "posterior", "draw", "effect", "value")
        correlation_col = _first_column(roles.get("correlation"), roles.get("corr"), roles.get("r"), "correlation", "corr", "r")
        probability_col = _first_column(roles.get("probability"), roles.get("posterior_prob"), "probability", "posterior_prob", "prob")
        result = draw_fn(
            df,
            condition_col=condition_col,
            factor_col=factor_col,
            draw_col=draw_col,
            correlation_col=correlation_col,
            probability_col=probability_col,
            condition_order=visual_plan.get("bayesianRidgeConditionOrder"),
            figsize=tuple(visual_plan.get("bayesianRidgeHeatmapFigsize", [16.0, 10.0])),
            width_ratios=visual_plan.get("bayesianRidgeHeatmapWidthRatios", [4.2, 0.35, 0.6, 4.2, 0.35]),
            positive_color=visual_plan.get("bayesianRidgePositiveColor", "#D95F5F"),
            negative_color=visual_plan.get("bayesianRidgeNegativeColor", "#4C78A8"),
            heatmap_cmap=visual_plan.get("bayesianHeatmapCmap", "RdBu_r"),
            heatmap_vlim=visual_plan.get("bayesianHeatmapVlim", 0.6),
            col_map=col_map,
        )
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        for motif in ("bayesian_ridge_heatmap_board", "ridge_heatmap_composite", "inset_heatmap_colorbar"):
            if motif not in planned_motifs:
                planned_motifs.append(motif)
            record_fn(visual_plan, motif)
        for _ in range(result.get("ridge_panel_count", 0)):
            count_fn(visual_plan, "ridgePanelCount")
        for _ in range(result.get("heat_strip_count", 0)):
            count_fn(visual_plan, "heatmapStripCount")
        for _ in range(result.get("ridge_fill_count", 0)):
            count_fn(visual_plan, "ridgeFillCount")
        for _ in range(result.get("inset_colorbar_count", 0)):
            count_fn(visual_plan, "colorbarSlotCount")
        count_fn(visual_plan, "sampleEncodingCount")
        visual_plan["bayesianRidgeGridWidthRatios"] = result.get("grid_width_ratios")
        visual_plan["bayesianRidgePanelCount"] = result.get("ridge_panel_count")
        visual_plan["bayesianHeatStripCount"] = result.get("heat_strip_count")
        visual_plan["bayesianRidgeFillCount"] = result.get("ridge_fill_count")
        visual_plan["bayesianRidgeOutlineCount"] = result.get("ridge_outline_count")
        visual_plan["bayesianRidgeProbabilityTextCount"] = result.get("probability_text_count")
        visual_plan["bayesianHeatmapSignificanceTextCount"] = result.get("significance_text_count")
        visual_plan["bayesianInsetColorbarCount"] = result.get("inset_colorbar_count")
        visual_plan["templateMatchMode"] = "case_025_bayesian_ridge_heatmap_board"
        return result["ridge_axes"][0]

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
              frameon=False, loc="upper right", borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "violin_grouped")
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
    ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=5)

    if standalone:
        apply_chart_polish(ax, "violin_split")
    return ax


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
