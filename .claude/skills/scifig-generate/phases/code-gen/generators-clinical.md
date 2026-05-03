# Clinical & Composition Chart Generators (Step 3.4h)

> Extracted from phases/03-code-gen-style.md. Read this file when the coordinator needs clinical, composition, or hierarchical chart generator implementations.

### Step 3.4h: Clinical & Composition Chart Generators

The following 8 generators cover clinical trial, sensitivity analysis, and compositional chart types.

```python
# ──────────────────────────────────────────────────────────────
# Clinical & Composition Chart Generators
# Signature: gen_xxx(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None) -> ax
# ──────────────────────────────────────────────────────────────


def gen_caterpillar_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Caterpillar plot: ranked effects with confidence intervals, sorted by effect size.

    Operational layer (post-Phase A1): when template_mining_helpers is embedded,
    this generator delegates the forest discipline (markers + asymmetric error bars +
    reference line + per-row estimate(CI) annotation) to add_forest_panel using
    linear scale and reference_line=0.0 (no-effect anchor).
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    estimate_col = roles.get("estimate") or roles.get("value")
    ci_low_col = roles.get("ci_low")
    ci_high_col = roles.get("ci_high")

    if label_col is None or estimate_col is None:
        raise ValueError("caterpillar_plot requires 'label' and 'estimate' in semanticRoles")

    sort_col = roles.get("sort") or estimate_col
    df_sorted = df.sort_values(sort_col).reset_index(drop=True)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df_sorted) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    estimates = df_sorted[estimate_col].astype(float).values
    if ci_low_col and ci_high_col:
        ci_low = df_sorted[ci_low_col].astype(float).values
        ci_high = df_sorted[ci_high_col].astype(float).values
    else:
        se_col = roles.get("se")
        se = df_sorted[se_col].astype(float).values if se_col and se_col in df_sorted.columns else estimates * 0.1
        ci_low = estimates - 1.96 * se
        ci_high = estimates + 1.96 * se
    labels = df_sorted[label_col].astype(str).tolist()

    canonical_forest = globals().get("add_forest_panel")
    if canonical_forest is not None:
        try:
            canonical_forest(ax, estimates, ci_low, ci_high, labels,
                             color="#0072B2",
                             reference_line=0.0,
                             log_scale=False,
                             show_yticklabels=True,
                             annotation_format="{hr:.3g} ({lo:.3g}, {hi:.3g})",
                             title=None)
            ax.set_xlabel("Effect size (95% CI)")
            if standalone:
                apply_chart_polish(ax, "caterpillar_plot")
            return ax
        except Exception:
            pass  # Fall through to inline implementation

    # Inline fallback when add_forest_panel is not embedded
    y_pos = np.arange(len(df_sorted))
    ax.errorbar(estimates, y_pos,
                xerr=[estimates - ci_low, ci_high - estimates],
                fmt="o", color="#0072B2", markersize=4, capsize=3,
                elinewidth=0.6, capthick=0.6, linewidth=0.6)

    ax.axvline(0, color="#999999", lw=0.5, ls="--", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=5)
    ax.set_xlabel("Effect size (95% CI)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "caterpillar_plot")
    return ax


def gen_tornado_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Tornado diagram for sensitivity analysis: horizontal bars showing variable impact."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    low_col = roles.get("low") or roles.get("ci_low")
    high_col = roles.get("high") or roles.get("ci_high")
    base_col = roles.get("base") or roles.get("value")

    if label_col is None or low_col is None or high_col is None:
        raise ValueError("tornado_chart requires 'label', 'low', and 'high' in semanticRoles")

    # Sort by bar width (largest impact first)
    df_sorted = df.copy()
    df_sorted["_width"] = (df_sorted[high_col] - df_sorted[low_col]).abs()
    df_sorted = df_sorted.sort_values("_width", ascending=True).reset_index(drop=True)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df_sorted) * 10) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = np.arange(len(df_sorted))
    base = df_sorted[base_col].values if base_col else np.zeros(len(df_sorted))

    for i in range(len(df_sorted)):
        low = df_sorted[low_col].iloc[i]
        high = df_sorted[high_col].iloc[i]
        ax.barh(y_pos[i], high - base[i], left=base[i], height=0.6,
                color="#0072B2", alpha=0.7, edgecolor="none")
        ax.barh(y_pos[i], low - base[i], left=base[i], height=0.6,
                color="#D55E00", alpha=0.7, edgecolor="none")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[label_col].values, fontsize=5)
    ax.set_xlabel("Impact on outcome")
    if standalone:
        apply_chart_polish(ax, "tornado_chart")
    return ax


def gen_nomogram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified nomogram: linear scale with point markers for prediction models."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    score_col = roles.get("score") or roles.get("value")

    if label_col is None or score_col is None:
        raise ValueError("nomogram requires 'label' and 'score' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(40, len(df) * 14) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = np.arange(len(df))
    labels = df[label_col].values
    scores = df[score_col].values

    for i in range(len(df)):
        # Draw horizontal scale line with tick marks
        ax.plot([0, 100], [y_pos[i], y_pos[i]], color="#CCCCCC", lw=1)
        for tick in np.linspace(0, 100, 6):
            ax.plot([tick, tick], [y_pos[i] - 0.2, y_pos[i] + 0.2], color="#999999", lw=0.5)
        # Mark the score value on the scale
        if np.isscalar(scores[i]) and 0 <= scores[i] <= 100:
            ax.plot(scores[i], y_pos[i], "o", color="#D55E00", markersize=6, zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xlim(-5, 105)
    ax.set_xlabel("Points")
    ax.set_ylim(-0.5, len(df) - 0.5)
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "nomogram")
    return ax


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
```

```python
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


def gen_chromosome_coverage(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Chromosome-wide coverage/depth plot: line along chromosome position.

    Expects columns: position (genomic coordinate) and coverage (read depth) in
    semanticRoles. Optionally chromosome label for multi-chrom figure.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pos_col = roles.get("position") or roles.get("x")
    cov_col = roles.get("coverage") or roles.get("depth") or roles.get("value")
    chrom_col = roles.get("chromosome") or roles.get("group")

    if pos_col is None or cov_col is None:
        raise ValueError("chromosome_coverage requires 'position' and 'coverage' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 40 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#1F4E79"])[0]

    if chrom_col and chrom_col in df.columns:
        for i, (name, grp) in enumerate(df.groupby(chrom_col)):
            c = palette.get("categorical", ["#1F4E79", "#C8553D"])[i % 2]
            ax.fill_between(grp[pos_col], grp[cov_col], alpha=0.5, color=c, linewidth=0)
            ax.plot(grp[pos_col], grp[cov_col], color=c, lw=0.4, label=str(name))
        ax.legend(frameon=False, fontsize=5, loc="upper right")
    else:
        ax.fill_between(df[pos_col], df[cov_col], alpha=0.4, color=color, linewidth=0)
        ax.plot(df[pos_col], df[cov_col], color=color, lw=0.5)

    ax.set_xlabel("Genomic position (bp)")
    ax.set_ylabel("Coverage depth")
    ax.set_xlim(df[pos_col].min(), df[pos_col].max())
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "chromosome_coverage")
    return ax


def gen_phase_diagram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Phase diagram: composition vs temperature with phase regions.

    Expects columns: composition (mole fraction, 0-1), temperature, and optionally
    phase (categorical region label) in semanticRoles. Plots a scatter with
    optional convex-hull outlines per phase region.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    comp_col = roles.get("composition") or roles.get("x")
    temp_col = roles.get("temperature") or roles.get("y")
    phase_col = roles.get("phase") or roles.get("group")

    if comp_col is None or temp_col is None:
        raise ValueError("phase_diagram requires 'composition' and 'temperature' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if phase_col and phase_col in df.columns:
        categories = df[phase_col].unique()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            sub = df[df[phase_col] == cat]
            ax.scatter(sub[comp_col], sub[temp_col], c=color_map.get(cat, "#999999"),
                       s=15, alpha=0.7, linewidth=0.3, edgecolors="white", label=str(cat))
            # Convex hull outline
            try:
                from scipy.spatial import ConvexHull
                pts = sub[[comp_col, temp_col]].dropna().values
                if len(pts) >= 3:
                    hull = ConvexHull(pts)
                    for simplex in hull.simplices:
                        ax.plot(pts[simplex, 0], pts[simplex, 1],
                                color=color_map.get(cat, "#999999"), lw=0.8, alpha=0.6)
            except Exception:
                pass
        ax.legend(frameon=False, fontsize=5, title=phase_col, title_fontsize=5)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(df[comp_col], df[temp_col], c=color, s=15, alpha=0.7,
                   linewidth=0.3, edgecolors="white")

    ax.set_xlabel("Composition (mole fraction)")
    ax.set_ylabel("Temperature")
    ax.set_xlim(0, 1)
    if standalone:
        apply_chart_polish(ax, "phase_diagram")
    return ax


def gen_nyquist_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Nyquist plot: real vs imaginary impedance (Z' vs Z'').

    Expects columns: z_real and z_imaginary (or x/y) in semanticRoles.
    Optionally frequency column for color-coded annotation.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    real_col = roles.get("z_real") or roles.get("x")
    imag_col = roles.get("z_imaginary") or roles.get("y")
    freq_col = roles.get("frequency") or roles.get("value")

    if real_col is None or imag_col is None:
        raise ValueError("nyquist_plot requires 'z_real' and 'z_imaginary' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if freq_col and freq_col in df.columns:
        scatter = ax.scatter(df[real_col], df[imag_col], c=df[freq_col],
                             cmap="viridis", s=20, alpha=0.8, linewidth=0.3, edgecolors="white",
                             zorder=3)
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
        cbar.set_label("Frequency (Hz)", fontsize=5)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(df[real_col], df[imag_col], c=color, s=20, alpha=0.8,
                   linewidth=0.3, edgecolors="white", zorder=3)

    ax.plot(df[real_col], df[imag_col], color="#999999", lw=0.4, alpha=0.5, zorder=2)
    ax.set_xlabel(r"$Z'$ (Real, $\Omega$)")
    ax.set_ylabel(r"$Z''$ (Imaginary, $\Omega$)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "nyquist_plot")
    return ax


def gen_ftir_spectrum(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """FTIR spectrum: wavenumber vs absorbance with inverted x-axis.

    Expects columns: wavenumber (cm^-1) and absorbance (or transmittance) in
    semanticRoles. X-axis is inverted (high wavenumber on left) per FTIR convention.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    wn_col = roles.get("wavenumber") or roles.get("x")
    abs_col = roles.get("absorbance") or roles.get("transmittance") or roles.get("value")

    if wn_col is None or abs_col is None:
        raise ValueError("ftir_spectrum requires 'wavenumber' and 'absorbance' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#C8553D"])[0]
    ax.plot(df[wn_col], df[abs_col], color=color, lw=0.8, solid_capstyle="round")
    ax.fill_between(df[wn_col], df[abs_col], alpha=0.1, color=color)

    ax.set_xlabel(r"Wavenumber (cm$^{-1}$)")
    ax.set_ylabel("Absorbance")
    ax.invert_xaxis()
    if standalone:
        apply_chart_polish(ax, "ftir_spectrum")
    return ax


def gen_dsc_thermogram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """DSC thermogram: temperature vs heat flow (exo down convention).

    Expects columns: temperature and heat_flow in semanticRoles.
    Optionally marks onset/peak temperatures for thermal events.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    temp_col = roles.get("temperature") or roles.get("x")
    hf_col = roles.get("heat_flow") or roles.get("y") or roles.get("value")

    if temp_col is None or hf_col is None:
        raise ValueError("dsc_thermogram requires 'temperature' and 'heat_flow' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#D55E00"])[0]
    ax.plot(df[temp_col], df[hf_col], color=color, lw=0.8, solid_capstyle="round")
    ax.fill_between(df[temp_col], df[hf_col], alpha=0.1, color=color)

    # Annotate peak (most negative heat flow = strongest endotherm)
    peak_idx = df[hf_col].idxmin()
    peak_t = df.loc[peak_idx, temp_col]
    peak_hf = df.loc[peak_idx, hf_col]
    ax.annotate(f"Peak: {peak_t:.1f}", xy=(peak_t, peak_hf),
                xytext=(peak_t + 5, peak_hf * 0.85),
                fontsize=5, arrowprops=dict(arrowstyle="->", lw=0.4, color="black"))

    ax.set_xlabel("Temperature")
    ax.set_ylabel("Heat flow (exo down)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "dsc_thermogram")
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
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    is_rf_shap = (
        template_case.get("bundleKey") == "rf_feature_importance_shap"
        or "ml_explainability" in patterns
        or "feature_importance" in patterns
        or "shap_composite" in patterns
        or any(str(c).lower() in ("importance", "mean_abs_shap", "shap_value", "gain", "permutation") for c in df.columns)
    )

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

```
