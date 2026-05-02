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
              frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "violin_grouped")
    return ax
```
