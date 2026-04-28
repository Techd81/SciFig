# Relationship / Psychology / Social Chart Generators

> Extracted from phases/03-code-gen-style.md. Read this file when the coordinator needs relationship, psychology, or social science chart generator implementations.

### Relationship / Psychology / Social chart generators

```python
def gen_chord_diagram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Chord diagram showing flows between categories using matplotlib arcs.

    Expects a square matrix or long-format flow table.  Semantic roles:
      - feature_id: source category column
      - group: target category column
      - value: flow magnitude column
    Falls back to the first NxN numeric block if roles are absent.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    src_col = roles.get("feature_id")
    tgt_col = roles.get("group")
    val_col = roles.get("value")

    # Build adjacency matrix
    if src_col and tgt_col and val_col:
        cats = sorted(set(df[src_col]) | set(df[tgt_col]))
        mat = df.pivot_table(index=src_col, columns=tgt_col,
                             values=val_col, aggfunc="sum").reindex(
                                 index=cats, columns=cats).fillna(0).values
    else:
        numeric = df.select_dtypes(include="number")
        mat = numeric.values[:len(numeric.columns), :len(numeric.columns)]
        cats = list(numeric.columns[:mat.shape[0]])

    n = len(cats)
    totals = mat.sum(axis=1) + mat.sum(axis=0)
    total = totals.sum()
    if total == 0:
        total = 1

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           subplot_kw={"aspect": "equal"},
                           constrained_layout=True)

    fallback = palette.get("categorical",
                            ["#0072B2", "#E69F00", "#56B4E9", "#009E73",
                             "#F0E442", "#D55E00", "#CC79A7", "#999999"])
    colors = [fallback[i % len(fallback)] for i in range(n)]

    angle_gap = 4  # degrees between arcs
    gap_total = n * angle_gap
    sweep = 360 - gap_total

    # Compute angular spans for each node
    spans = []
    start = 0
    for i in range(n):
        extent = (totals[i] / total) * sweep
        spans.append((start, extent))
        start += extent + angle_gap

    # Draw outer arcs
    for i, (s, e) in enumerate(spans):
        wedge = matplotlib.patches.Wedge(
            (0, 0), 1.0, s, s + e, width=0.15,
            facecolor=colors[i], edgecolor="white", linewidth=0.5)
        ax.add_patch(wedge)
        mid_angle = np.radians(s + e / 2)
        ax.text(1.18 * np.cos(mid_angle), 1.18 * np.sin(mid_angle),
                cats[i], ha="center", va="center", fontsize=5,
                rotation=np.degrees(mid_angle) - 90
                if 90 < np.degrees(mid_angle) < 270
                else np.degrees(mid_angle) + 90)

    # Draw chords
    out_pos = [0.0] * n  # track outgoing offset within each arc
    for i in range(n):
        for j in range(n):
            if mat[i, j] == 0:
                continue
            frac = mat[i, j] / total
            si, ei = spans[i]
            sj, ej = spans[j]

            a1 = si + out_pos[i] * sweep / totals[i] if totals[i] else 0
            out_pos[i] += mat[i, j]

            b1 = sj + out_pos[j] * sweep / totals[j] if totals[j] else 0
            out_pos[j] += mat[j, i]

            t = np.linspace(0, 1, 50)
            # Quadratic Bezier through center
            p0 = np.array([np.cos(np.radians(a1)), np.sin(np.radians(a1))])
            p2 = np.array([np.cos(np.radians(b1)), np.sin(np.radians(b1))])
            mid = (p0 + p2) / 2 * 0.3  # pull toward center
            chord_pts = ((1 - t)[:, None] ** 2 * p0
                         + 2 * (1 - t)[:, None] * t[:, None] * mid
                         + t[:, None] ** 2 * p2)
            ax.plot(chord_pts[:, 0], chord_pts[:, 1],
                    color=colors[i], alpha=0.25, lw=0.4)

    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "chord_diagram")
    return ax


def gen_parallel_coordinates(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Parallel coordinates plot for multivariate profiles.

    Each row becomes a polyline across numeric columns.  Semantic roles:
      - group: categorical column used for colouring lines
      - value / feature_id are optional; all numeric columns are used.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, _, _ = _resolve_roles(dataProfile)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("parallel_coordinates requires at least 2 numeric columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    # Normalize each column to [0, 1]
    normed = df[numeric_cols].copy()
    for c in numeric_cols:
        rng = normed[c].max() - normed[c].min()
        normed[c] = (normed[c] - normed[c].min()) / (rng if rng != 0 else 1)

    x = np.arange(len(numeric_cols))

    if group_col and group_col in df.columns:
        categories = df[group_col].unique()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            mask = df[group_col] == cat
            for _, row in normed.loc[mask].iterrows():
                ax.plot(x, row.values, color=color_map[cat], alpha=0.35, lw=0.5)
        # Legend proxy
        for cat in categories:
            ax.plot([], [], color=color_map[cat], label=str(cat), lw=1.5)
        ax.legend(fontsize=5, frameon=False, loc="upper right")
    else:
        for _, row in normed.iterrows():
            ax.plot(x, row.values, color="#999999", alpha=0.35, lw=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(numeric_cols, rotation=30, ha="right", fontsize=5)
    ax.set_ylabel("Normalized value")
    ax.set_xlim(x[0], x[-1])
    if standalone:
        apply_chart_polish(ax, "parallel_coordinates")
    return ax


def gen_mediation_path(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mediation path diagram: X -> M -> Y with path coefficients.

    Semantic roles:
      - x: independent variable (column name or computed summary key)
      - mediator: mediating variable column
      - y: dependent variable column
    Coefficients are computed as standardized betas via OLS.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    m_col = roles.get("mediator") or roles.get("feature_id")
    y_col = roles.get("y") or roles.get("value")

    if not all([x_col, m_col, y_col]):
        raise ValueError("mediation_path requires 'x', 'mediator', and 'y' in semanticRoles")

    # Standardize for comparable coefficients
    z = (df[[x_col, m_col, y_col]] - df[[x_col, m_col, y_col]].mean()) / \
        df[[x_col, m_col, y_col]].std().replace(0, 1)

    # Path coefficients
    a = np.polyfit(z[x_col], z[m_col], 1)[0]  # X -> M
    b = np.polyfit(z[m_col], z[y_col], 1)[0]  # M -> Y
    c_prime = np.polyfit(z[x_col], z[y_col], 1)[0]  # X -> Y (direct)
    ab = a * b  # indirect effect

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    # Node positions
    nodes = {x_col: (0.1, 0.5), m_col: (0.5, 0.5), y_col: (0.9, 0.5)}
    box_w, box_h = 0.12, 0.10

    color_accent = palette.get("categorical", ["#0072B2"])[0]

    for name, (cx, cy) in nodes.items():
        rect = plt.Rectangle((cx - box_w / 2, cy - box_h / 2), box_w, box_h,
                              facecolor="white", edgecolor=color_accent,
                              linewidth=1, transform=ax.transAxes, clip_on=False)
        ax.add_patch(rect)
        ax.text(cx, cy, name, ha="center", va="center", fontsize=6,
                fontweight="bold", transform=ax.transAxes)

    # Arrows with coefficients
    arrow_kw = dict(arrowstyle="-|>", color="#333333", lw=1,
                    connectionstyle="arc3,rad=0", transform=ax.transAxes)

    def _draw_arrow(src, dst, coeff, y_off=0.08):
        sx, sy = nodes[src]
        dx, dy = nodes[dst]
        ax.annotate("", xy=(dx - box_w / 2 - 0.01, dy),
                     xytext=(sx + box_w / 2 + 0.01, sy),
                     xycoords="axes fraction", textcoords="axes fraction",
                     arrowprops=arrow_kw)
        mx = (sx + dx) / 2
        ax.text(mx, sy + y_off, f"{coeff:.3f}", ha="center", va="bottom",
                fontsize=5.5, color="#333333", transform=ax.transAxes)

    _draw_arrow(x_col, m_col, a, y_off=0.06)
    _draw_arrow(m_col, y_col, b, y_off=0.06)
    # Direct path below
    sx, sy = nodes[x_col]
    dx, dy = nodes[y_col]
    ax.annotate("", xy=(dx - box_w / 2 - 0.01, dy - 0.18),
                 xytext=(sx + box_w / 2 + 0.01, sy - 0.18),
                 xycoords="axes fraction", textcoords="axes fraction",
                 arrowprops={**arrow_kw, "linestyle": "--"})
    mx = (sx + dx) / 2
    ax.text(mx, sy - 0.18 - 0.06, f"c'={c_prime:.3f}", ha="center",
            va="top", fontsize=5, color="#666666", transform=ax.transAxes)

    ax.text(0.5, 0.02, f"Indirect effect (a*b) = {ab:.3f}",
            ha="center", fontsize=5, transform=ax.transAxes, color="#333333")

    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "mediation_path")
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
              frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "interaction_plot")
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
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel(value_col)
    if standalone:
        apply_chart_polish(ax, "diverging_bar")
    return ax


def gen_heatmap_symmetric(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Symmetric heatmap with identical upper and lower triangles.

    Expects a square correlation/distance matrix or long-format data that can
    be pivoted into one.  Semantic roles:
      - feature_id: row labels column
      - group: column labels column
      - value: cell value column
    Falls back to correlation matrix of all numeric columns.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    row_col = roles.get("feature_id")
    col_col = roles.get("group")
    val_col = roles.get("value")

    if row_col and col_col and val_col:
        mat = df.pivot_table(index=row_col, columns=col_col,
                             values=val_col, aggfunc="mean").fillna(0)
    else:
        numeric = df.select_dtypes(include="number")
        if len(numeric.columns) < 2:
            raise ValueError("heatmap_symmetric requires at least 2 numeric columns or pivot roles")
        mat = numeric.corr()

    # Make symmetric if not already
    labels = mat.columns.tolist()
    M = mat.values
    symmetric = (M + M.T) / 2.0
    np.fill_diagonal(symmetric, 1.0)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    sns.heatmap(symmetric, ax=ax, cmap="vlag", center=0,
                xticklabels=labels, yticklabels=labels,
                linewidths=0.3, annot=symmetric.shape[0] <= 12,
                fmt=".2f", annot_kws={"size": 4.5},
                cbar_kws={"shrink": 0.6, "label": "Value"})
    ax.tick_params(labelsize=5)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    if standalone:
        apply_chart_polish(ax, "heatmap_symmetric")
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


def gen_line(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simple line chart for ordered time, dose, or index trends."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("time") or roles.get("dose") or roles.get("condition")
    y_col = roles.get("value") or roles.get("y") or roles.get("response")
    group_col = roles.get("group")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if y_col is None:
        y_col = numeric_cols[-1] if numeric_cols else None
    if y_col is None:
        raise ValueError("line requires a numeric 'value' or 'y' column")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    fallback = palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541"])
    if x_col is None:
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
                  frameon=False, fontsize=5)
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


def gen_ma_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """MA plot: average abundance/intensity versus log2 fold change."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    mean_col = roles.get("mean") or roles.get("baseMean") or roles.get("abundance") or roles.get("x")
    fc_col = roles.get("log2fc") or roles.get("fold_change") or roles.get("effect") or roles.get("y")
    p_col = roles.get("padj") or roles.get("p_value") or roles.get("pvalue")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if mean_col is None and numeric_cols:
        mean_col = numeric_cols[0]
    if fc_col is None and len(numeric_cols) > 1:
        fc_col = numeric_cols[1]
    if mean_col is None or fc_col is None:
        raise ValueError("ma_plot requires mean abundance and log2 fold-change columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    mean_vals = df[mean_col].astype(float).clip(lower=1e-12)
    fc_vals = df[fc_col].astype(float)
    sig = np.zeros(len(df), dtype=bool)
    if p_col and p_col in df.columns:
        sig = df[p_col].astype(float) < 0.05
    sig = sig & (np.abs(fc_vals) >= 1)

    ax.scatter(np.log10(mean_vals[~sig]), fc_vals[~sig], s=9, c="#B8B8B8",
               alpha=0.55, linewidth=0, label=f"NS ({int((~sig).sum())})")
    ax.scatter(np.log10(mean_vals[sig]), fc_vals[sig], s=13, c="#C8553D",
               alpha=0.8, edgecolors="white", linewidth=0.25,
               label=f"Changed ({int(sig.sum())})")
    ax.axhline(0, color="black", lw=0.55)
    ax.axhline(1, color="#777777", lw=0.45, ls="--")
    ax.axhline(-1, color="#777777", lw=0.45, ls="--")
    ax.set_xlabel(f"log10({_display_col(mean_col, col_map)})")
    ax.set_ylabel(_display_col(fc_col, col_map))
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
              frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "ma_plot")
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
                  frameon=False, fontsize=5)
    else:
        ax.scatter(x_vals, y_vals, s=12, alpha=0.75,
                   color=palette.get("categorical", ["#1F4E79"])[0],
                   edgecolors="white", linewidth=0.25)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if standalone:
        apply_chart_polish(ax, "tsne")
    return ax


def gen_oncoprint(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Oncoprint-style alteration matrix for gene-by-sample mutation calls."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    gene_col = roles.get("gene") or roles.get("feature_id") or roles.get("row")
    sample_col = roles.get("sample") or roles.get("subject_id") or roles.get("column")
    alteration_col = roles.get("alteration") or roles.get("mutation") or roles.get("value")

    if gene_col and sample_col and alteration_col:
        mat = df.pivot_table(index=gene_col, columns=sample_col, values=alteration_col,
                             aggfunc=lambda x: ";".join(sorted(set(map(str, x)))))
    else:
        mat = df.copy()
        if gene_col and gene_col in mat.columns:
            mat = mat.set_index(gene_col)

    mat = mat.fillna("")
    genes = list(mat.index)[:40]
    samples = list(mat.columns)[:80]
    mat = mat.loc[genes, samples]
    alteration_types = sorted({str(v) for v in mat.to_numpy().ravel() if str(v) not in ("", "0", "nan", "False")})
    if not alteration_types:
        alteration_types = ["altered"]
    code_map = {alt: i + 1 for i, alt in enumerate(alteration_types)}
    codes = np.zeros(mat.shape, dtype=float)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            value = str(mat.iat[i, j])
            if value in code_map:
                codes[i, j] = code_map[value]
            elif value not in ("", "0", "nan", "False"):
                codes[i, j] = 1

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(55, 3 * len(genes)) * (1 / 25.4)),
                           constrained_layout=True)

    cmap_colors = ["#F2F2F2"] + palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541"])
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(cmap_colors[:len(alteration_types) + 1])
    norm = BoundaryNorm(np.arange(-0.5, len(alteration_types) + 1.5), cmap.N)
    ax.imshow(codes, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
    ax.set_yticks(range(len(genes)))
    ax.set_yticklabels(genes, fontsize=5)
    ax.set_xticks([])
    ax.set_xlabel(f"Samples (n={len(samples)})")
    ax.set_ylabel("Genes")
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=cmap_colors[i + 1]) for i in range(len(alteration_types))]
    ax.legend(handles, alteration_types, loc="upper left", bbox_to_anchor=(1.02, 1),
              borderaxespad=0, frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "oncoprint")
    return ax


def gen_lollipop_mutation(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mutation lollipop plot: protein/genomic position versus mutation frequency."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pos_col = roles.get("position") or roles.get("aa_position") or roles.get("x")
    count_col = roles.get("count") or roles.get("frequency") or roles.get("value") or roles.get("y")
    label_col = roles.get("label") or roles.get("mutation") or roles.get("feature_id")

    if pos_col is None or count_col is None:
        raise ValueError("lollipop_mutation requires 'position' and 'count'/'frequency' columns")

    plot_df = df[[c for c in [pos_col, count_col, label_col] if c and c in df.columns]].dropna().sort_values(pos_col)
    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#C8553D"])[0]
    ax.hlines(0, plot_df[pos_col].min(), plot_df[pos_col].max(), color="#333333", lw=1.0)
    ax.vlines(plot_df[pos_col], 0, plot_df[count_col], color=color, lw=0.8, alpha=0.75)
    sizes = 25 + 40 * (plot_df[count_col] / plot_df[count_col].max())
    ax.scatter(plot_df[pos_col], plot_df[count_col], s=sizes, color=color,
               edgecolor="white", linewidth=0.35, zorder=3)
    if label_col:
        for _, row in plot_df.nlargest(min(8, len(plot_df)), count_col).iterrows():
            ax.annotate(str(row[label_col])[:16], (row[pos_col], row[count_col]),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=4.5,
                        arrowprops=dict(arrowstyle="-", lw=0.25, color="#555555"))
    ax.set_xlabel("Position")
    ax.set_ylabel("Mutation frequency")
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "lollipop_mutation")
    return ax


def gen_manhattan(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Manhattan plot for chromosome-position association scans."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    chrom_col = roles.get("chromosome") or roles.get("chr") or roles.get("group")
    pos_col = roles.get("position") or roles.get("x")
    p_col = roles.get("pvalue") or roles.get("p_value") or roles.get("padj") or roles.get("y")

    if chrom_col is None or pos_col is None or p_col is None:
        raise ValueError("manhattan requires chromosome, position, and p-value columns")

    plot_df = df[[chrom_col, pos_col, p_col]].dropna().copy()
    plot_df[p_col] = plot_df[p_col].astype(float).clip(lower=1e-300, upper=1.0)
    chroms = sorted(plot_df[chrom_col].unique(), key=lambda x: str(x))
    offset = 0
    ticks, ticklabels = [], []
    xs = np.zeros(len(plot_df))
    for chrom in chroms:
        idx = plot_df[chrom_col] == chrom
        sub_pos = plot_df.loc[idx, pos_col].astype(float)
        xs[idx.to_numpy()] = sub_pos + offset
        ticks.append(offset + (sub_pos.min() + sub_pos.max()) / 2)
        ticklabels.append(str(chrom))
        offset += sub_pos.max() + max(sub_pos.max() * 0.04, 1)
    plot_df["_x"] = xs
    plot_df["_nlogp"] = -np.log10(plot_df[p_col])

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    colors = palette.get("categorical", ["#1F4E79", "#C8553D"])
    for i, chrom in enumerate(chroms):
        sub = plot_df[plot_df[chrom_col] == chrom]
        ax.scatter(sub["_x"], sub["_nlogp"], s=6, color=colors[i % len(colors)],
                   alpha=0.72, linewidth=0)
    ax.axhline(-np.log10(5e-8), color="#333333", lw=0.5, ls="--")
    ax.axhline(-np.log10(1e-5), color="#999999", lw=0.45, ls=":")
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticklabels, fontsize=5)
    ax.set_xlabel("Chromosome")
    ax.set_ylabel("-log10(p-value)")
    if standalone:
        apply_chart_polish(ax, "manhattan")
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
    ax.plot([0, lim], [0, lim], color="#333333", lw=0.6, ls="--")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Expected -log10(p)")
    ax.set_ylabel("Observed -log10(p)")
    if standalone:
        apply_chart_polish(ax, "qq")
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
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
                  frameon=False, fontsize=5)
    else:
        ax.scatter(df[x_col], df[y_col], color=palette.get("categorical", ["#1F4E79"])[0],
                   s=12, alpha=0.85, linewidth=0)
    ax.set_xlabel(_display_col(x_col, col_map))
    ax.set_ylabel(_display_col(y_col, col_map))
    ax.set_aspect("equal", adjustable="datalim")
    if standalone:
        apply_chart_polish(ax, "spatial_feature")
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


def gen_bubble_matrix(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Bubble matrix with row/column categories and numeric bubble magnitude."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    row_col = roles.get("row") or roles.get("feature_id") or roles.get("y") or roles.get("label")
    col_col = roles.get("column") or roles.get("group") or roles.get("x")
    value_col = roles.get("value") or roles.get("size")
    if row_col is None or col_col is None or value_col is None:
        raise ValueError("bubble_matrix requires row, column, and value columns")

    pivot = df.pivot_table(index=row_col, columns=col_col, values=value_col,
                           aggfunc="mean", fill_value=0)
    rows = pivot.index.tolist()
    cols = pivot.columns.tolist()
    values = pivot.to_numpy(dtype=float)
    vmax = np.nanmax(np.abs(values)) or 1
    if standalone:
        fig, ax = plt.subplots(figsize=(max(80, 7 * len(cols)) * (1 / 25.4),
                                    max(60, 5 * len(rows)) * (1 / 25.4)),
                           constrained_layout=True)

    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            value = pivot.loc[row, col]
            ax.scatter(j, i, s=10 + 150 * abs(value) / vmax, c=value,
                       cmap="coolwarm", vmin=-vmax, vmax=vmax,
                       edgecolor="white", linewidth=0.25)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=5)
    ax.invert_yaxis()
    ax.set_xlabel(_display_col(col_col, col_map))
    ax.set_ylabel(_display_col(row_col, col_map))
    if standalone:
        apply_chart_polish(ax, "bubble_matrix")
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
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
              frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "stacked_bar_comp")
    return ax


def gen_alluvial(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Two-stage alluvial flow diagram between source and target categories."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    source_col = roles.get("source") or roles.get("from") or roles.get("feature_id")
    target_col = roles.get("target") or roles.get("to") or roles.get("group")
    value_col = roles.get("value") or roles.get("count")
    if source_col is None or target_col is None:
        raise ValueError("alluvial requires source and target columns")

    flows = df.copy()
    if value_col is None or value_col not in flows.columns:
        flows["_value"] = 1.0
        value_col = "_value"
    flows = flows.groupby([source_col, target_col], as_index=False)[value_col].sum()
    sources = flows[source_col].dropna().unique().tolist()
    targets = flows[target_col].dropna().unique().tolist()
    total = flows[value_col].sum() or 1.0

    if standalone:
        fig, ax = plt.subplots(figsize=(120 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)

    colors = _extract_colors(palette, sources)
    src_totals = flows.groupby(source_col)[value_col].sum().reindex(sources).fillna(0)
    tgt_totals = flows.groupby(target_col)[value_col].sum().reindex(targets).fillna(0)

    def _spans(labels, totals):
        spans = {}
        cursor = 0.0
        gap = 0.025
        usable = 1.0 - gap * max(len(labels) - 1, 0)
        for label in labels:
            height = usable * totals[label] / total
            spans[label] = [cursor, cursor + height]
            cursor += height + gap
        return spans

    src_spans = _spans(sources, src_totals)
    tgt_spans = _spans(targets, tgt_totals)
    src_cursor = {k: v[0] for k, v in src_spans.items()}
    tgt_cursor = {k: v[0] for k, v in tgt_spans.items()}

    for label, (y0, y1) in src_spans.items():
        ax.add_patch(plt.Rectangle((0.05, y0), 0.08, y1 - y0,
                                   facecolor=colors.get(label, "#999999"),
                                   edgecolor="white", linewidth=0.4))
        ax.text(0.035, (y0 + y1) / 2, str(label), ha="right", va="center", fontsize=5)
    for label, (y0, y1) in tgt_spans.items():
        ax.add_patch(plt.Rectangle((0.87, y0), 0.08, y1 - y0,
                                   facecolor="#D9D9D9", edgecolor="white", linewidth=0.4))
        ax.text(0.965, (y0 + y1) / 2, str(label), ha="left", va="center", fontsize=5)

    for _, row in flows.iterrows():
        source = row[source_col]
        target = row[target_col]
        height = row[value_col] / total * (1.0 - 0.025 * max(len(sources) - 1, 0))
        y0s, y1s = src_cursor[source], src_cursor[source] + height
        y0t, y1t = tgt_cursor[target], tgt_cursor[target] + height
        src_cursor[source] = y1s
        tgt_cursor[target] = y1t
        verts = [(0.13, y0s), (0.45, y0s), (0.55, y0t), (0.87, y0t),
                 (0.87, y1t), (0.55, y1t), (0.45, y1s), (0.13, y1s)]
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        path = Path(verts + [verts[0]],
                    [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                     Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                     Path.CLOSEPOLY])
        ax.add_patch(PathPatch(path, facecolor=colors.get(source, "#999999"),
                               edgecolor="none", alpha=0.35))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "alluvial")
    return ax
```
**Usage notes for multi-panel composition:**

- All generators accept an `ax` keyword argument pattern. To use inside a
  multi-panel figure, pass `ax=axes["B"]` after minor refactoring to accept
  an optional `ax` parameter.
- The `palette` argument is a dict from `resolve_color_system()` containing
  `categorical`, `categoryMap`, and other keys.
- `dataProfile` must carry `semanticRoles` with at minimum `value` (numeric
  column) and optionally `group` (categorical column).
- For `violin_paired`, `semanticRoles.pair_id` identifies matched
  observations.
- For `violin_split`, `semanticRoles.x` provides an additional grouping axis
  (e.g., timepoint) while `group` provides the two halves.
