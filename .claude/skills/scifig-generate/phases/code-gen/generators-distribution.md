# Distribution Chart Generators (Step 3.4d)

> Extracted from phases/03-code-gen-style.md. Read this file when the coordinator needs distribution chart generator implementations.

### Step 3.4d: Distribution Chart Generators (Implemented)

The following 8 generators provide production-ready templates for distribution chart types registered in `CHART_GENERATORS`. Each follows the Nature/Cell style contract: open-L spines, no grid, round line caps, publication font sizes, and `apply_chart_polish` post-processing.

```python
# ──────────────────────────────────────────────────────────────
# Distribution Chart Generators
# Signature: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
# Each returns the matplotlib Axes for multi-panel composition.
# col_map: optional dict mapping sanitized column names -> original display labels.
# Use display_label(col, col_map) to get the human-readable label for axis/legend text.
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
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


def gen_ridge(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Ridgeline / joy plot for many groups.

    Overlapping density ridges stacked vertically.  Uses Gaussian KDE with
    shared bandwidth across groups.  Groups ordered by median value.
    """
    standalone = ax is None
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
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)

    if standalone:
        apply_chart_polish(ax, "violin_split")
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

    # Diagonal reference line
    ax.plot([0, 1], [0, 1], color="black", linewidth=0.6, linestyle="--", zorder=1)

    ax.set_xlabel("Expected cumulative probability")
    ax.set_ylabel("Observed cumulative probability")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    if standalone:
        apply_chart_polish(ax, "pp_plot")
    return ax


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
        if bool(highlight_mask.any()) or iter_col:
            ax.legend(frameon=False, fontsize=5, loc="best")
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


def gen_ci_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Confidence interval plot for multiple estimates.

    Displays horizontal CI bars for each estimate row.  Expects columns for
    estimate (point value), lower CI bound, and upper CI bound.  Optionally
    accepts a label column for y-axis tick names.  A vertical reference line
    at x = 0 is drawn when the interval spans zero.
    """
    standalone = ax is None
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
    if standalone:
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
    if standalone:
        apply_chart_polish(ax, "ci_plot")
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


def gen_circos_karyotype(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified circos-like karyotype plot (linear chromosomes with colored tracks).

    Expects columns: chromosome, start, end, and optionally track_value and
    track_color in semanticRoles.  Draws horizontal chromosome bands with
    colored overlay tracks simulating a circos layout in linear form.
    """
    standalone = ax is None
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
    if standalone:
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
                seg_alpha = max(0, min(1, 0.3 + 0.7 * min(row[value_col], 1.0)))
            ax.barh(yi, row[end_col] - row[start_col], left=row[start_col],
                    height=0.5, color=seg_color, alpha=seg_alpha, linewidth=0)

    ax.set_yticks(range(n_chr))
    ax.set_yticklabels(chromosomes, fontsize=5)
    ax.set_xlabel("Genomic position")
    ax.set_ylim(-0.5, n_chr - 0.5)
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    if standalone:
        apply_chart_polish(ax, "circos_karyotype")
    return ax


def gen_gene_structure(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Gene structure diagram (exons as boxes, introns as lines, UTRs colored).

    Expects columns: feature_type (exon/intron/5utr/3utr/cds), start, end,
    and optionally strand in semanticRoles.  Draws a horizontal gene model
    with exon boxes, intron lines, and colored UTR regions.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    type_col = roles.get("feature_type") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end")
    strand = roles.get("strand", "+")

    if type_col is None or start_col is None or end_col is None:
        raise ValueError("gene_structure requires 'feature_type', 'start', 'end' in semanticRoles")

    if standalone:
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

    if standalone:
        apply_chart_polish(ax, "gene_structure")
    return ax


def gen_pathway_map(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pathway enrichment bubble chart.

    x=enrichment score, y=pathway name, size=gene count, color=-log10(p).
    Expects columns: pathway, enrichment_score, gene_count, p_value in semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pathway_col = roles.get("pathway") or roles.get("group") or roles.get("y")
    score_col = roles.get("enrichment_score") or roles.get("x") or roles.get("value")
    count_col = roles.get("gene_count") or roles.get("size")
    pval_col = roles.get("p_value") or roles.get("color")

    if pathway_col is None or score_col is None:
        raise ValueError("pathway_map requires 'pathway' and 'enrichment_score' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(60, 12 * len(df) + 20) * (1 / 25.4)),
                           constrained_layout=True)

    nlogp = -np.log10(df[pval_col].clip(lower=1e-300)) if pval_col and pval_col in df.columns else np.ones(len(df))
    sizes = df[count_col] * 8 if count_col and count_col in df.columns else np.full(len(df), 40)
    cmap = plt.cm.YlOrRd

    scatter = ax.scatter(df[score_col], df[pathway_col], s=sizes, c=nlogp,
                         cmap=cmap, alpha=0.7, edgecolor="white", linewidth=0.4)
    cbar = ax.figure.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label(r"$-\log_{10}(p)$", fontsize=5)
    cbar.ax.tick_params(labelsize=4)

    ax.set_xlabel("Enrichment score")
    ax.set_ylabel("")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "pathway_map")
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


def gen_control_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Shewhart control chart with mean line and +/-3sigma limits.

    Expects a numeric value column in semanticRoles["value"].  Points beyond
    the control limits are highlighted in red.  Center line shows the process
    mean; upper/lower limits are mean +/- 3 * std.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    _, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("control_chart requires a numeric value column in semanticRoles")

    if standalone:
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
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "control_chart")
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


def gen_stress_strain(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stress-strain curve for materials science.

    Plots strain (x) vs stress (y) with optional yield point annotation.
    Expects columns: strain (x-axis) and stress (y-axis) in semanticRoles.
    If a yield_strain/yield_stress column exists, annotates the yield point.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    strain_col = roles.get("strain") or roles.get("x")
    stress_col = roles.get("stress") or roles.get("y") or roles.get("value")

    if strain_col is None or stress_col is None:
        raise ValueError("stress_strain requires 'strain' and 'stress' in semanticRoles")

    if standalone:
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
    if standalone:
        apply_chart_polish(ax, "stress_strain")
    return ax


def gen_xrd_pattern(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """X-ray diffraction (XRD) pattern with stick plot peaks.

    Plots 2-theta (x) vs intensity (y) as vertical sticks at peak positions.
    Expects columns: two_theta (x-axis) and intensity (y-axis) in semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    theta_col = roles.get("two_theta") or roles.get("x")
    intensity_col = roles.get("intensity") or roles.get("y") or roles.get("value")

    if theta_col is None or intensity_col is None:
        raise ValueError("xrd_pattern requires 'two_theta' and 'intensity' in semanticRoles")

    if standalone:
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
    if standalone:
        apply_chart_polish(ax, "xrd_pattern")
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


def gen_swimmer_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Swimmer plot: horizontal bars for treatment duration with event markers.

    Each row is a patient.  A horizontal bar spans from start to end (e.g.
    treatment start/stop).  Optional marker columns encode events such as
    response, progression, or adverse events with distinct shapes/colors.

    Expects in semanticRoles: id (patient label), start, end, and optionally
    group (arm/cohort).  Event markers are read from columns whose names are
    listed in chartPlan.get("eventColumns", []).
    """
    standalone = ax is None
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
    if standalone:
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
    if standalone:
        apply_chart_polish(ax, "swimmer_plot")
    return ax


def gen_risk_ratio_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Risk ratio forest plot (HR / OR with 95 % CI).

    Horizontal forest plot showing hazard ratios or odds ratios with
    confidence intervals for each subgroup.  A vertical reference line at 1
    (no effect) is drawn.  Optionally annotates p-values on the right margin.

    Expects in semanticRoles: label (subgroup name), estimate (HR or OR),
    ci_lower, ci_upper, and optionally p_value.
    """
    standalone = ax is None
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
    if standalone:
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
    if standalone:
        apply_chart_polish(ax, "risk_ratio_plot")
    return ax


def gen_sankey(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified Sankey diagram showing flow between stages using matplotlib patches.

    Expects columns: source (origin stage), target (destination stage), and
    value (flow magnitude) in semanticRoles.  Draws horizontal node bars at
    left/right with filled bezier-like flow ribbons connecting them.
    Nature style: no grid, open-L spines, publication fonts.
    """
    standalone = ax is None
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

    if standalone:
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
    if standalone:
        apply_chart_polish(ax, "sankey")
    return ax


def gen_radar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Radar / spider chart for multi-attribute comparison across groups.

    Expects columns: attribute (axis label), group (series), and value in
    semanticRoles.  One polygon per group, filled with semi-transparent color.
    Axes are radial with attribute labels at each spoke.  Nature style: thin
    lines, no grid fill, publication fonts.
    """
    standalone = ax is None
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

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           subplot_kw=dict(polar=True),
                           constrained_layout=True)

    angles = np.linspace(0, 2 * np.pi, n_attrs, endpoint=False).tolist()
    angles += angles[:1]  # close polygon

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(attributes, fontsize=5)
    if hasattr(ax, 'set_rlabel_position'):
        ax.set_rlabel_position(30)
        ax.yaxis.set_tick_params(labelsize=4)
        ax.grid(linewidth=0.4, color="#CCCCCC")
        ax.spines["polar"].set_linewidth(0.4)

    template_rows = []
    template_colors = []
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
            template_rows.append(values[:-1])
            template_colors.append(color)
    else:
        values = []
        for attr in attributes:
            match = df[df[attr_col] == attr][val_col]
            values.append(match.values[0] if len(match) > 0 else 0)
        values += values[:1]
        color = fallback[0]
        ax.plot(angles, values, linewidth=0.8, color=color)
        ax.fill(angles, values, alpha=0.15, color=color)
        template_rows.append(values[:-1])
        template_colors.append(color)

    apply_template_radar_signature(
        ax,
        angles[:-1],
        value_rows=template_rows,
        colors=template_colors,
        visualPlan=chartPlan.get("visualContentPlan", {}),
    )

    if standalone:
        apply_chart_polish(ax, "radar")
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

    if group_col is None or subgroup_col is None or value_col is None:
        raise ValueError("grouped_bar requires 'group', 'subgroup', and 'value' in semanticRoles")

    categories = df[group_col].dropna().unique().tolist()
    subgroups = df[subgroup_col].dropna().unique().tolist()
    n_sub = len(subgroups)
    colors = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                          "#C8553D", "#7A6C8F", "#2B6F77"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)
    patterns = set(dataProfile.get("specialPatterns", []))
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

    if is_ml_benchmark:
        metric_col = roles.get("metric")
        plot_df = df.copy()
        metric_label = value_col
        higher_is_better = True
        if metric_col and metric_col in plot_df:
            metric_order = ["r2", "auc", "accuracy", "f1", "precision", "recall", "rmse", "mae", "mse", "error"]
            metric_values = plot_df[metric_col].astype(str).str.lower()
            selected_metric = next((m for m in metric_order if metric_values.str.contains(m, regex=False).any()), None)
            if selected_metric:
                plot_df = plot_df[metric_values.str.contains(selected_metric, regex=False)]
                metric_label = selected_metric.upper()
                higher_is_better = selected_metric not in {"rmse", "mae", "mse", "error"}

        subgroup_labels = [str(s).lower() for s in subgroups]
        priority_terms = ("test", "valid", "validation", "cv", "external")
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
                is_rf = any(token in str(cat).lower() for token in ("random forest", "randomforest", "rf", "rfr"))
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
        ax.set_yticklabels([str(c) for c in categories], fontsize=5)
        for tick, cat in zip(ax.get_yticklabels(), categories):
            if any(token in str(cat).lower() for token in ("random forest", "randomforest", "rf", "rfr")):
                tick.set_fontweight("bold")
                tick.set_color("#111111")
        ax.invert_yaxis()
        ax.set_xlabel(metric_label)
        ax.set_ylabel("Model" if standalone else "")
        ax.xaxis.grid(True, linestyle="--", linewidth=0.35, alpha=0.45, zorder=0)
        ax.set_axisbelow(True)
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
            fig_for_margin.subplots_adjust(
                left=max(sp.left, 0.20),
                bottom=max(sp.bottom, 0.20),
                right=min(sp.right, 0.94),
            )
        if best_index is not None and best_score is not None and not np.isnan(best_score):
            ax.text(
                0.98,
                0.06,
                f"best: {str(categories[best_index])[:18]}",
                transform=ax.transAxes,
                fontsize=5,
                ha="right",
                va="bottom",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#333333", linewidth=0.35, alpha=0.88),
                zorder=8,
            )
        ax.legend(frameon=False, fontsize=5, ncol=min(n_sub, 4))
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
    else:
        ax.scatter(df[x_col], df[y_col], s=12, alpha=0.7,
                   color=palette.get("categorical", ["#0072B2"])[0],
                   linewidth=0.3, edgecolor="white", zorder=2)

    ax.set_xlabel(f"{method} axis 1")
    ax.set_ylabel(f"{method} axis 2")
    if standalone:
        apply_chart_polish(ax, "ordination_plot")
    return ax


def gen_biodiversity_radar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Biodiversity radar: multiple diversity indices on polar axes.

    Expects in semanticRoles: attribute (diversity index name) and value
    (index value).  Optionally group for comparing communities.  Indices are
    plotted as radial spokes (e.g. Shannon, Simpson, Richness, Evenness,
    Chao1).  Values are min-max normalised to [0, 1] for visual comparison.
    Nature style: thin lines, no grid fill, publication fonts.
    """
    standalone = ax is None
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

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 80 * (1 / 25.4)),
                           subplot_kw=dict(polar=True),
                           constrained_layout=True)

    angles = np.linspace(0, 2 * np.pi, n_idx, endpoint=False).tolist()
    angles += angles[:1]

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(indices, fontsize=5)
    if hasattr(ax, 'set_rlabel_position'):
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

    if standalone:
        apply_chart_polish(ax, "biodiversity_radar")
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5, title_fontsize=5)
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, fontsize=5)
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


def gen_km(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Kaplan-Meier survival curve with optional at-risk table."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    time_col = roles.get("time") or roles.get("duration")
    event_col = roles.get("event") or roles.get("status")
    group_col = roles.get("group")

    if time_col is None or event_col is None:
        raise ValueError("km requires 'time' and 'event' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    def _km_curve(times, events):
        """Compute KM survival estimate."""
        unique_times = np.sort(times[events == 1].unique())
        n_at_risk = len(times)
        surv = [1.0]
        t_points = [0]
        for t in unique_times:
            d = ((times == t) & (events == 1)).sum()
            n = (times >= t).sum()
            if n > 0:
                surv.append(surv[-1] * (1 - d / n))
                t_points.append(t)
        return np.array(t_points), np.array(surv)

    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            t_km, s_km = _km_curve(grp[time_col], grp[event_col])
            ax.step(t_km, s_km, where="post", color=col, lw=1, label=str(name))
    else:
        t_km, s_km = _km_curve(df[time_col], df[event_col])
        ax.step(t_km, s_km, where="post", color="#000000", lw=1)

    ax.set_xlabel("Time")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(0, 1.05)
    if group_col:
        ax.legend(frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "km")
    return ax


def gen_forest(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Forest plot for effect sizes with confidence intervals."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    estimate_col = roles.get("estimate") or roles.get("value")
    ci_low_col = roles.get("ci_low")
    ci_high_col = roles.get("ci_high")

    if label_col is None or estimate_col is None:
        raise ValueError("forest requires 'label' and 'estimate' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = range(len(df))
    estimates = df[estimate_col].values

    if ci_low_col and ci_high_col:
        ci_low = df[ci_low_col].values
        ci_high = df[ci_high_col].values
    else:
        # Use SE-based approximate CI
        se = df[roles.get("se", estimate_col)].values if roles.get("se") else estimates * 0.1
        ci_low = estimates - 1.96 * se
        ci_high = estimates + 1.96 * se

    ax.errorbar(estimates, y_pos,
                xerr=[estimates - ci_low, ci_high - estimates],
                fmt="o", color="#000000", markersize=4, capsize=3,
                elinewidth=0.6, capthick=0.6, linewidth=0.6)

    ax.axvline(0, color="#999999", lw=0.5, ls="--", alpha=0.7)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df[label_col].values, fontsize=5)
    ax.set_xlabel("Effect size (95% CI)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "forest")
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


def gen_volcano(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Volcano plot: fold-change vs significance with threshold lines."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    fc_col = roles.get("fold_change") or roles.get("x")
    pval_col = roles.get("p_value")
    label_col = roles.get("label_col") or roles.get("feature_id")

    if fc_col is None or pval_col is None:
        raise ValueError("volcano requires 'fold_change' and 'p_value' in semanticRoles")

    df = df.copy()
    df["nlogp"] = -np.log10(df[pval_col].clip(lower=1e-20))
    fc_thresh = 1
    pval_thresh = 0.05

    def _cat(row):
        if row[pval_col] < pval_thresh and row[fc_col] > fc_thresh:
            return "Up"
        elif row[pval_col] < pval_thresh and row[fc_col] < -fc_thresh:
            return "Down"
        return "NS"

    df["cat"] = df.apply(_cat, axis=1)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)

    colors = {"Up": "#D55E00", "Down": "#0072B2", "NS": "#999999"}
    for cat, col in colors.items():
        s = df[df.cat == cat]
        ax.scatter(s[fc_col], s["nlogp"], c=col, s=12, alpha=0.7,
                   linewidth=0.3, edgecolors="white", label=f"{cat} ({len(s)})")

    ax.axhline(-np.log10(pval_thresh), color="black", lw=0.5, ls="--", alpha=0.5)
    ax.axvline(fc_thresh, color="black", lw=0.5, ls="--", alpha=0.5)
    ax.axvline(-fc_thresh, color="black", lw=0.5, ls="--", alpha=0.5)

    if label_col:
        top = df[df.cat != "NS"].nlargest(5, "nlogp")
        for idx, (_, row) in enumerate(top.iterrows()):
            y_off = (idx % 3) * df["nlogp"].max() * 0.04
            ax.annotate(row[label_col], (row[fc_col], row["nlogp"] + y_off),
                        fontsize=4, ha="center", va="bottom",
                        arrowprops=dict(arrowstyle="-", lw=0.3, color="black"))

    ax.set_xlabel("log2(Fold Change)")
    ax.set_ylabel("-log10(adj. p-value)")
    ax.legend(loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "volcano")
    return ax


def gen_heatmap_cluster(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Heatmap with hierarchical clustering: Z-scored expression/abundance matrix."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    # If data is matrix-like, use directly; otherwise pivot
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) >= 3:
        Z = df[numeric_cols]
        # Z-score normalize
        Z = Z.sub(Z.mean(1), axis=0).div(Z.std(1).replace(0, 1), axis=0)
    else:
        roles = dataProfile.get("semanticRoles", {})
        group_col = roles.get("group")
        value_col = roles.get("value")
        feature_col = roles.get("feature_id")
        if group_col and value_col and feature_col:
            pivot = df.pivot_table(index=feature_col, columns=group_col, values=value_col)
            Z = pivot.sub(pivot.mean(1), axis=0).div(pivot.std(1).replace(0, 1), axis=0)
        else:
            Z = df.select_dtypes(include="number")

    sns.heatmap(Z, cmap="vlag", center=0, linewidths=0, ax=ax,
                cbar_kws={"shrink": 0.6, "label": "Z-score"})
    ax.set_xlabel("Samples")
    ax.set_ylabel("Features")
    ax.set_yticks([])
    apply_chart_polish(ax, "heatmap_cluster")
    return ax


def gen_heatmap_pure(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pure heatmap without clustering: ordered matrix with explicit annotation."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    numeric_cols = df.select_dtypes(include="number").columns
    Z = df[numeric_cols] if len(numeric_cols) >= 3 else df.select_dtypes(include="number")

    sns.heatmap(Z, cmap="vlag", center=0, linewidths=0, ax=ax,
                cbar_kws={"shrink": 0.6, "label": "Value"})
    ax.set_xlabel("Columns")
    ax.set_ylabel("Rows")
    if standalone:
        apply_chart_polish(ax, "heatmap_pure")
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


def _is_classifier_validation_board(chartPlan, dataProfile=None):
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in (dataProfile or {}).get("specialPatterns", [])}
    return (
        template_case.get("bundleKey") == "classifier_validation_board"
        or "classifier_validation" in patterns
        or "probability_calibration" in patterns
        or "threshold_tuning" in patterns
    )


def _place_classifier_validation_legend(ax, standalone=False, ncol=2):
    handles, labels = ax.get_legend_handles_labels()
    if not labels:
        return None
    if standalone and ax.figure is not None:
        legend = ax.figure.legend(
            handles, labels,
            loc="lower center", bbox_to_anchor=(0.5, 0.02),
            ncol=min(max(1, ncol), len(labels)), fontsize=5,
            frameon=True, fancybox=True, borderpad=0.25,
            handlelength=1.4, columnspacing=0.8,
        )
        legend.set_gid("scifig_shared_legend")
        legend.get_frame().set_linewidth(0.35)
        legend.get_frame().set_edgecolor("#333333")
        legend.get_frame().set_alpha(0.94)
        try:
            if hasattr(ax.figure, "set_layout_engine"):
                ax.figure.set_layout_engine(None)
            else:
                ax.figure.set_constrained_layout(False)
        except Exception:
            pass
        sp = ax.figure.subplotpars
        ax.figure.subplots_adjust(left=max(sp.left, 0.20), bottom=max(sp.bottom, 0.32), right=min(sp.right, 0.96))
        return legend
    return ax.legend(frameon=False, fontsize=5, loc="best")


def gen_roc(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """ROC curve with AUC annotation and confidence band."""
    standalone = ax is None
    from sklearn.metrics import roc_curve, auc

    roles = dataProfile.get("semanticRoles", {})
    score_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label") or roles.get("event")

    if score_col is None or label_col is None:
        raise ValueError("roc requires 'score' and 'label' in semanticRoles")

    y_true = df[label_col].values
    y_scores = df[score_col].values

    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)
    is_classifier_board = _is_classifier_validation_board(chartPlan, dataProfile)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    color = "#1F4E79" if is_classifier_board else "#0072B2"
    ax.plot(fpr, tpr, color=color, lw=1.15 if is_classifier_board else 1, label=f"ROC AUC = {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], color="#999999", lw=0.5, ls="--", label="Chance")
    ax.fill_between(fpr, 0, tpr, alpha=0.12 if is_classifier_board else 0.1, color=color)
    if is_classifier_board and len(thresholds):
        youden = tpr - fpr
        best_idx = int(np.nanargmax(youden))
        best_threshold = thresholds[best_idx]
        if np.isfinite(best_threshold):
            ax.axvline(fpr[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.axhline(tpr[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.scatter([fpr[best_idx]], [tpr[best_idx]], s=36, color="#B00000",
                       edgecolor="white", linewidth=0.45, zorder=5, label="Best threshold")
            callout_x = 0.62 if standalone else 0.05
            ax.text(
                callout_x, 0.18,
                f"AUC={roc_auc:.3f}\nthr={best_threshold:.2f}\nn={len(y_true)}",
                transform=ax.transAxes, ha="left", va="bottom", fontsize=5.3,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )

    ax.set_xlabel("False Positive Rate" if standalone or not is_classifier_board else "")
    ax.set_ylabel("True Positive Rate" if standalone or not is_classifier_board else "")
    if is_classifier_board:
        _place_classifier_validation_legend(ax, standalone, ncol=3)
    else:
        ax.legend(loc="lower right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "roc")
    return ax


def gen_calibration(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Calibration plot: predicted probability vs observed fraction."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    pred_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label") or roles.get("event")

    if pred_col is None or label_col is None:
        raise ValueError("calibration requires 'score' and 'label' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    is_classifier_board = _is_classifier_validation_board(chartPlan, dataProfile)

    pred = pd.to_numeric(df[pred_col], errors="coerce").clip(0, 1)
    label = pd.to_numeric(df[label_col], errors="coerce")
    valid_rows = pred.notna() & label.notna()
    pred = pred[valid_rows]
    label = label[valid_rows]

    # Bin predictions and compute observed fraction
    bins = np.linspace(0, 1, 11)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    observed = []
    counts = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (pred >= lo) & (pred <= hi if np.isclose(hi, 1.0) else pred < hi)
        counts.append(int(mask.sum()))
        if mask.sum() > 0:
            observed.append(float(label[mask].mean()))
        else:
            observed.append(np.nan)

    observed_arr = np.asarray(observed, dtype=float)
    counts_arr = np.asarray(counts, dtype=float)
    valid = np.isfinite(observed_arr) & (counts_arr > 0)
    ax.plot(bin_centers[valid], observed_arr[valid], "-", color="#1F4E79" if is_classifier_board else "#0072B2", lw=1)
    if is_classifier_board:
        sizes = 18 + (counts_arr / max(float(np.nanmax(counts_arr)), 1.0)) * 56
        ax.scatter(bin_centers, observed_arr, s=sizes, color="#1F4E79",
                   edgecolor="white", linewidth=0.45, zorder=4, label="Calibration bins")
        ece = float(np.nansum((counts_arr[valid] / max(counts_arr.sum(), 1.0)) * np.abs(observed_arr[valid] - bin_centers[valid]))) if valid.any() else np.nan
        band_x = np.linspace(0, 1, 80)
        ax.fill_between(band_x, np.clip(band_x - 0.05, 0, 1), np.clip(band_x + 0.05, 0, 1),
                        color="#F6CFA3", alpha=0.18, linewidth=0, label="±0.05 band")
        if valid.any():
            calib_error = np.where(valid, np.abs(observed_arr - bin_centers), np.nan)
            worst_idx = int(np.nanargmax(calib_error))
            ax.vlines(bin_centers[worst_idx], bin_centers[worst_idx], observed_arr[worst_idx],
                      color="#B00000", lw=0.75, alpha=0.75, zorder=3)
            ax.scatter([bin_centers[worst_idx]], [observed_arr[worst_idx]], s=sizes[worst_idx] + 16,
                       color="#B00000", edgecolor="white", linewidth=0.5, zorder=5, label="Worst bin")
        if np.isfinite(ece):
            ax.text(
                0.05, 0.88, f"ECE={ece:.3f}\nbins={int(valid.sum())}\nn={int(counts_arr.sum())}",
                transform=ax.transAxes, ha="left", va="top", fontsize=5.3,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )
        _place_classifier_validation_legend(ax, standalone, ncol=3)
    else:
        ax.plot(bin_centers, observed, "o-", color="#0072B2", lw=1, markersize=4)
    ax.plot([0, 1], [0, 1], "--", color="#999999", lw=0.5)

    ax.set_xlabel("Predicted probability" if standalone or not is_classifier_board else "")
    ax.set_ylabel("Observed fraction" if standalone or not is_classifier_board else "")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    if standalone:
        apply_chart_polish(ax, "calibration")
    return ax


def gen_waterfall(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Waterfall plot: ordered patient/response values."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    value_col = roles.get("value") or roles.get("response")
    label_col = roles.get("label") or roles.get("subject_id")

    if value_col is None:
        raise ValueError("waterfall requires 'value' in semanticRoles")

    values = np.sort(df[value_col].values)[::-1]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    colors = ["#0072B2" if v <= -30 else "#999999" if v <= 20 else "#D55E00" for v in values]
    ax.bar(range(len(values)), values, color=colors, width=0.7,
           linewidth=0.3, edgecolor="white")
    ax.axhline(0, color="black", lw=0.5)

    ax.set_xlabel("Patient")
    ax.set_ylabel("Response (%)")
    if standalone:
        apply_chart_polish(ax, "waterfall")
    return ax


def gen_correlation(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Correlation heatmap: lower triangle with annotations."""
    standalone = ax is None
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("correlation requires at least 2 numeric columns")

    corr = df[numeric_cols].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    cbar_kw = {"shrink": 0.6} if standalone else {"shrink": 0.4, "aspect": 20}
    sns.heatmap(corr, mask=mask, ax=ax, cmap="vlag", center=0,
                annot=True, fmt=".2f", linewidths=0.5,
                cbar_kws=cbar_kw, annot_kws={"size": 5},
                square=True)
    if standalone:
        apply_chart_polish(ax, "correlation")
    return ax


def gen_scatter_regression(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Scatter with regression line, parity diagnostics, or SHAP dependence view."""
    standalone = ax is None
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

    x_col = _role_or_column("actual", "observed", "measured", "x", "dose")
    y_col = _role_or_column("predicted", "prediction", "fitted", "y", "value")
    split_col = _role_or_column("split", "sample_type", "source", "cohort", "group")
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    bundle_key = str(template_case.get("bundleKey") or "").lower()
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

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    plot_cols = [x_col, y_col]
    for optional_col in (split_col, interaction_col if is_shap_dependence else None, feature_name_col if is_shap_dependence else None):
        if optional_col and optional_col in df.columns and optional_col not in plot_cols:
            plot_cols.append(optional_col)
    plot_df = df[plot_cols].copy()
    plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[x_col, y_col])

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
        for i, (name, grp) in enumerate(groups):
            label = "samples" if name is None else str(name)
            marker, color = split_styles.get(label.lower(), ("o", fallback[i % len(fallback)]))
            ax.scatter(
                grp[x_col], grp[y_col], marker=marker, s=22,
                facecolors="none", edgecolors=color, linewidth=0.75,
                alpha=0.9, label=label, zorder=3,
            )
        lo = float(np.nanmin([plot_df[x_col].min(), plot_df[y_col].min()]))
        hi = float(np.nanmax([plot_df[x_col].max(), plot_df[y_col].max()]))
        pad = max((hi - lo) * 0.04, 1e-9)
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="black", lw=0.8, ls="--", label="1:1", zorder=2)
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(lo - pad, hi + pad)
        residuals = plot_df[y_col] - plot_df[x_col]
        ss_res = float(np.sum((plot_df[y_col] - plot_df[x_col]) ** 2))
        ss_tot = float(np.sum((plot_df[x_col] - plot_df[x_col].mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rmse = float(np.sqrt(np.mean(residuals ** 2))) if len(residuals) else np.nan
        mae = float(np.mean(np.abs(residuals))) if len(residuals) else np.nan
        ax.text(
            0.05, 0.95, f"R2={r2:.3f}\nRMSE={rmse:.3g}\nMAE={mae:.3g}",
            transform=ax.transAxes, ha="left", va="top", fontsize=5.2,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.92),
            zorder=6,
        )
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(frameon=False, fontsize=5, ncol=min(4, len(labels)))
    else:
        ax.scatter(plot_df[x_col], plot_df[y_col], c="#000000", s=15, alpha=0.7,
                   linewidth=0.3, edgecolors="white")

    z = np.polyfit(plot_df[x_col], plot_df[y_col], 1)
    p_line = np.poly1d(z)
    xs = np.linspace(plot_df[x_col].min(), plot_df[x_col].max(), 100)
    ax.plot(xs, p_line(xs), color="#D55E00", lw=1, ls="--")

    r = np.corrcoef(plot_df[x_col], plot_df[y_col])[0, 1]
    if not is_prediction_report:
        ax.text(0.05, 0.95, f"r = {r:.3f}", transform=ax.transAxes, fontsize=6, va="top")

    ax.set_xlabel("Actual" if is_prediction_report else x_col)
    ax.set_ylabel("Predicted" if is_prediction_report else y_col)
    if standalone:
        apply_chart_polish(ax, "scatter_regression")
    return ax


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
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    is_shap_beeswarm = (
        template_case.get("bundleKey") == "rf_feature_importance_shap"
        or "shap_composite" in patterns
        or "ml_explainability" in patterns
        or "shap_value" in {str(c).lower() for c in df.columns}
    )

    if is_shap_beeswarm and feature_col and value_col and feature_col in df.columns and value_col in df.columns:
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


def gen_adjacency_matrix(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Adjacency matrix visualization for network data.

    A symmetric binary or weighted adjacency matrix rendered as a heatmap.
    Rows and columns represent nodes; cell fill indicates edge presence or
    weight.  Diagonal is masked for clarity.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    source_col = roles.get("x") or roles.get("group")
    target_col = roles.get("y") or roles.get("feature_id")
    weight_col = roles.get("value")

    if source_col and target_col and weight_col:
        adj = df.pivot_table(index=source_col, columns=target_col,
                             values=weight_col, aggfunc="mean", fill_value=0)
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        adj = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    # Make symmetric if nearly symmetric
    if adj.shape[0] == adj.shape[1]:
        adj = (adj + adj.T) / 2

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    mask = np.eye(adj.shape[0], dtype=bool)
    sns.heatmap(adj, mask=mask, cmap="Blues", linewidths=0.3, linecolor="white",
                square=True, cbar_kws={"shrink": 0.6, "label": "Weight"}, ax=ax)
    ax.set_xlabel("Node")
    ax.set_ylabel("Node")
    if standalone:
        apply_chart_polish(ax, "adjacency_matrix")
    return ax


def gen_heatmap_annotated(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Heatmap with cell value annotations displayed inside each cell.

    Suitable for small-to-medium matrices where exact numeric values are
    important.  Font size auto-adjusts to cell count.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")
    if group_col and value_col and feature_col:
        pivot = df.pivot_table(index=feature_col, columns=group_col,
                               values=value_col, aggfunc="mean")
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        pivot = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    n_cells = pivot.shape[0] * pivot.shape[1]
    annot_size = max(4, min(8, int(120 / max(n_cells, 1))))

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(pivot, annot=True, fmt=".2f", annot_kws={"size": annot_size},
                cmap="YlOrRd", linewidths=0.3, linecolor="white",
                cbar_kws={"shrink": 0.6, "label": value_col or "Value"}, ax=ax)
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel((feature_col or "Row") if standalone else "")
    if standalone:
        apply_chart_polish(ax, "heatmap_annotated")
    return ax


def gen_heatmap_triangular(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Lower or upper triangular heatmap.

    Masks the upper triangle to display only the lower half (or vice versa).
    Common for correlation or distance matrices to avoid redundancy.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")
    pvalue_col = roles.get("pvalue") or roles.get("p_value") or roles.get("padj") or roles.get("fdr")

    if group_col and value_col and feature_col:
        pivot = df.pivot_table(index=feature_col, columns=group_col,
                               values=value_col, aggfunc="mean")
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        pivot = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    # Ensure square for triangular masking
    if pivot.shape[0] == pivot.shape[1]:
        mask = np.triu(np.ones_like(pivot, dtype=bool), k=0)
    else:
        mask = np.zeros_like(pivot, dtype=bool)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(pivot, mask=mask, cmap="coolwarm", center=0,
                linewidths=0.3, linecolor="white", square=True,
                cbar_kws={"shrink": 0.6, "label": value_col or "Value"}, ax=ax)
    pvalue_lookup = {}
    if pvalue_col and group_col and feature_col and pvalue_col in df:
        for _, row in df[[feature_col, group_col, pvalue_col]].dropna().iterrows():
            pvalue_lookup[(row[feature_col], row[group_col])] = row[pvalue_col]
    apply_template_triangular_heatmap_signature(
        ax,
        row_labels=list(pivot.index),
        col_labels=list(pivot.columns),
        pvalue_lookup=pvalue_lookup,
        visualPlan=chartPlan.get("visualContentPlan", {}),
    )
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel(feature_col or "Row")
    if standalone:
        apply_chart_polish(ax, "heatmap_triangular")
    return ax


def gen_heatmap_mirrored(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mirrored symmetric heatmap.

    Displays the full matrix on one triangle and a transposed or secondary
    metric on the other triangle.  Useful for showing two related measures
    (e.g., correlation coefficient vs p-value) in a single figure.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")

    if group_col and value_col and feature_col:
        pivot = df.pivot_table(index=feature_col, columns=group_col,
                               values=value_col, aggfunc="mean")
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        pivot = df[numeric_cols] if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    if pivot.shape[0] != pivot.shape[1]:
        pivot = pivot.iloc[:min(pivot.shape), :min(pivot.shape)]
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                               constrained_layout=True)
        sns.heatmap(pivot, cmap="RdBu_r", center=0, linewidths=0.3,
                    cbar_kws={"shrink": 0.6, "label": value_col or "Value"}, ax=ax)
    if standalone:
        apply_chart_polish(ax, "heatmap_mirrored")
        return ax

    n = pivot.shape[0]
    mask_lower = np.tril(np.ones((n, n), dtype=bool), k=-1)
    mask_upper = np.triu(np.ones((n, n), dtype=bool), k=1)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(pivot, mask=mask_lower, cmap="RdBu_r", center=0,
                linewidths=0.3, linecolor="white", square=True,
                cbar_kws={"shrink": 0.6, "label": "Lower"}, ax=ax)
    sns.heatmap(pivot.T, mask=mask_upper, cmap="PiYG", center=0,
                linewidths=0.3, linecolor="white", square=True,
                cbar_kws={"shrink": 0.6, "label": "Upper"}, ax=ax)
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel(feature_col or "Row")
    if standalone:
        apply_chart_polish(ax, "heatmap_mirrored")
    return ax


def gen_cooccurrence_matrix(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Co-occurrence matrix with optional hierarchical clustering.

    Computes pairwise co-occurrence counts or similarity between categories,
    then displays as a clustered heatmap.  Rows and columns are reordered by
    dendrogram to reveal group structure.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group") or roles.get("x")
    value_col = roles.get("value")
    feature_col = roles.get("feature_id") or roles.get("y")

    if group_col and feature_col:
        ct = pd.crosstab(df[feature_col], df[group_col])
    elif group_col and value_col:
        pivot = df.pivot_table(index=df.columns[0], columns=group_col,
                               values=value_col, aggfunc="count", fill_value=0)
        ct = pivot
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        ct = df[numeric_cols].corr() if len(numeric_cols) >= 2 else df.select_dtypes(include="number")

    # Attempt hierarchical clustering to reorder
    try:
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import pdist
        if ct.shape[0] > 2 and ct.shape[1] > 2:
            row_link = linkage(pdist(ct.values, metric="euclidean"), method="average")
            col_link = linkage(pdist(ct.values.T, metric="euclidean"), method="average")
            row_order = leaves_list(row_link)
            col_order = leaves_list(col_link)
            ct = ct.iloc[row_order, col_order]
    except Exception:
        pass

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(ct, cmap="YlGnBu", linewidths=0.3, linecolor="white",
                cbar_kws={"shrink": 0.6, "label": "Co-occurrence"}, ax=ax)
    ax.set_xlabel(group_col or "Column")
    ax.set_ylabel(feature_col or "Row")
    if standalone:
        apply_chart_polish(ax, "cooccurrence_matrix")
    return ax



# ──────────────────────────────────────────────────────────────
# Time Series Chart Generators
# ──────────────────────────────────────────────────────────────

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


def gen_dose_response(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Dose-response curve with optional EC50/IC50 annotation."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 62 * (1 / 25.4)), constrained_layout=True)

    roles = dataProfile.get("semanticRoles", {})
    dose_col = roles.get("dose")
    response_col = roles.get("response") or roles.get("value")
    group_col = roles.get("group")

    if not dose_col or not response_col:
        raise ValueError("dose_response requires 'dose' and 'response' in semanticRoles")

    if group_col and group_col in df.columns:
        groups = df[group_col].unique().tolist()
        color_map = _extract_colors(palette, groups)
        fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])
        for i, grp in enumerate(groups):
            sub = df[df[group_col] == grp].sort_values(dose_col)
            color = color_map.get(grp, fallback_colors[i % len(fallback_colors)])
            ax.scatter(sub[dose_col], sub[response_col], s=10, color=color, label=display_label(grp, col_map),
                      edgecolor="white", lw=0.3, zorder=3)
            # Fit 4PL if scipy available
            try:
                from scipy.optimize import curve_fit
                def four_pl(x, bottom, top, ec50, hill):
                    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)
                popt, _ = curve_fit(four_pl, sub[dose_col].values, sub[response_col].values,
                                   p0=[sub[response_col].min(), sub[response_col].max(),
                                       sub[dose_col].median(), 1], maxfev=5000)
                x_fit = np.logspace(np.log10(sub[dose_col].min()), np.log10(sub[dose_col].max()), 100)
                ax.plot(x_fit, four_pl(x_fit, *popt), color=color, lw=0.8, alpha=0.8)
            except Exception:
                pass
        ax.legend(fontsize=4.5, markerscale=2, frameon=False)
    else:
        sub = df.sort_values(dose_col)
        ax.scatter(sub[dose_col], sub[response_col], s=10, color="#1F4E79", edgecolor="white", lw=0.3)

    ax.set_xlabel(display_label(dose_col, col_map))
    ax.set_ylabel(display_label(response_col, col_map))
    ax.set_xscale("log")
    if standalone:
        apply_chart_polish(ax, "dose_response")
    return ax


def gen_enrichment_dotplot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Enrichment dotplot: pathway terms vs enrichment score with dot size = gene count."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 78 * (1 / 25.4)), constrained_layout=True)

    roles = dataProfile.get("semanticRoles", {})
    term_col = roles.get("term") or roles.get("pathway") or roles.get("label")
    score_col = roles.get("score") or roles.get("effect") or roles.get("fold_change")
    pval_col = roles.get("p_value")
    size_col = roles.get("size")

    if not term_col or not score_col:
        raise ValueError("enrichment_dotplot requires 'term' and 'score' in semanticRoles")

    # Sort by score
    plot_df = df.sort_values(score_col, ascending=True).head(20)

    y_pos = range(len(plot_df))
    scores = plot_df[score_col].values

    # Dot sizes
    if size_col and size_col in plot_df.columns:
        sizes = plot_df[size_col].values
        sizes = 10 + (sizes - sizes.min()) / (sizes.max() - sizes.min() + 1e-9) * 80
    else:
        sizes = np.full(len(plot_df), 30)

    # Colors from p-value or score
    if pval_col and pval_col in plot_df.columns:
        colors = -np.log10(plot_df[pval_col].values.clip(1e-300))
        sc = ax.scatter(scores, y_pos, s=sizes, c=colors, cmap="YlOrRd", edgecolor="white", lw=0.3, zorder=3)
        plt.colorbar(sc, ax=ax, label="-log10(p)", shrink=0.6, pad=0.02)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(scores, y_pos, s=sizes, color=color, edgecolor="white", lw=0.3, zorder=3)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([display_label(t, col_map) for t in plot_df[term_col]], fontsize=4.5)
    ax.set_xlabel("Enrichment Score")
    ax.axvline(x=0, color="#999999", lw=0.4, ls="--")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "enrichment_dotplot")
    return ax


def gen_pr_curve(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Precision-Recall curve with AUC annotation."""
    standalone = ax is None

    roles = dataProfile.get("semanticRoles", {})
    score_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label")

    if not score_col or not label_col:
        raise ValueError("pr_curve requires 'score' and 'label' in semanticRoles")

    y_true = df[label_col].values
    y_score = df[score_col].values
    is_classifier_board = _is_classifier_validation_board(chartPlan, dataProfile)
    if standalone:
        fig_size = (89 * (1 / 25.4), 75 * (1 / 25.4)) if is_classifier_board else (62 * (1 / 25.4), 62 * (1 / 25.4))
        fig, ax = plt.subplots(figsize=fig_size, constrained_layout=True)

    try:
        from sklearn.metrics import precision_recall_curve, average_precision_score
        precision, recall, thresholds = precision_recall_curve(y_true, y_score)
        ap = average_precision_score(y_true, y_score)

        ax.plot(recall, precision, color="#1F4E79", lw=1.1 if is_classifier_board else 0.8, label=f"AP = {ap:.3f}")
        ax.fill_between(recall, precision, alpha=0.12 if is_classifier_board else 0.1, color="#1F4E79")

        # Baseline
        baseline = y_true.mean()
        ax.axhline(y=baseline, color="#999999", lw=0.4, ls="--", label=f"Baseline = {baseline:.3f}")
        if is_classifier_board and len(thresholds):
            f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
            best_idx = int(np.nanargmax(f1))
            best_threshold = thresholds[best_idx]
            ax.axvline(recall[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.axhline(precision[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.scatter([recall[best_idx]], [precision[best_idx]], s=36, color="#B00000",
                       edgecolor="white", linewidth=0.45, zorder=5, label="Best F1 threshold")
            ax.text(
                0.08, 0.18,
                f"AP={ap:.3f}\nF1={f1[best_idx]:.3f}\nthr={best_threshold:.2f}\nn={len(y_true)}",
                transform=ax.transAxes, ha="left", va="bottom", fontsize=5.3,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )

        if is_classifier_board:
            _place_classifier_validation_legend(ax, standalone, ncol=3)
        else:
            ax.legend(fontsize=5, frameon=False)
    except ImportError:
        ax.text(0.5, 0.5, "scikit-learn required", ha="center", va="center", transform=ax.transAxes)

    ax.set_xlabel("Recall" if standalone or not is_classifier_board else "")
    ax.set_ylabel("Precision" if standalone or not is_classifier_board else "")
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    if standalone:
        apply_chart_polish(ax, "pr_curve")
    return ax
