"""Matrix & heatmap chart generators.

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


def gen_confusion_matrix(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Row-normalized classifier confusion matrix with count + row-percent labels.

    Accepts true/predicted class columns directly, or derives predicted classes
    from classifier scores when a threshold is supplied or implied by the plan.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    plan = chartPlan or {}
    columns_lower = {str(c).lower(): c for c in df.columns}

    def _role_or_col(*names):
        for name in names:
            if name in roles and roles[name] in df.columns:
                return roles[name]
        for name in names:
            key = str(name).lower()
            if key in columns_lower:
                return columns_lower[key]
        return None

    def _is_label_like(series):
        clean = series.dropna()
        if clean.empty:
            return False
        if not pd.api.types.is_numeric_dtype(clean):
            return True
        return clean.nunique() <= min(12, max(2, int(np.sqrt(len(clean))) + 1))

    true_col = _role_or_col("true_label", "actual_label", "label", "y_true", "actual", "class")
    pred_col = _role_or_col("predicted_label", "prediction_label", "predicted_class", "y_pred", "pred_label")
    loose_pred = _role_or_col("prediction")
    if pred_col is None and loose_pred is not None and true_col is not None and _is_label_like(df[loose_pred]):
        pred_col = loose_pred
    score_col = _role_or_col("score", "probability", "proba", "prediction_score", "y_score")
    count_col = _role_or_col("count", "n", "support")

    cm = None
    if true_col and pred_col and true_col in df.columns and pred_col in df.columns:
        work = df[[true_col, pred_col] + ([count_col] if count_col and count_col not in (true_col, pred_col) else [])].dropna()
        if work.empty:
            raise ValueError("confusion_matrix requires non-empty true/predicted labels")
        if count_col and count_col in work.columns:
            cm = work.pivot_table(index=true_col, columns=pred_col, values=count_col,
                                  aggfunc="sum", fill_value=0)
        else:
            cm = pd.crosstab(work[true_col], work[pred_col])
    elif true_col and score_col and true_col in df.columns and score_col in df.columns:
        work = df[[true_col, score_col]].dropna()
        if work.empty:
            raise ValueError("confusion_matrix requires non-empty label/score pairs")
        template_plan = plan.get("templateCasePlan", {}) if isinstance(plan.get("templateCasePlan"), dict) else {}
        threshold = plan.get("threshold", template_plan.get("threshold", 0.5))
        labels = sorted(work[true_col].dropna().unique().tolist(), key=lambda value: str(value))
        positive_label = plan.get("positiveLabel") or template_plan.get("positiveLabel") or labels[-1]
        negative_label = [label for label in labels if label != positive_label][0] if len(labels) > 1 else f"not {positive_label}"
        pred = np.where(work[score_col].astype(float) >= float(threshold), positive_label, negative_label)
        cm = pd.crosstab(work[true_col], pred)
    else:
        numeric = df.select_dtypes(include="number")
        if numeric.shape[0] >= 2 and numeric.shape[1] >= 2:
            side = min(numeric.shape[0], numeric.shape[1], 12)
            cm = numeric.iloc[:side, :side].copy()
            if cm.index.equals(pd.RangeIndex(start=0, stop=side, step=1)):
                cm.index = [f"C{i + 1}" for i in range(side)]
            cm.columns = [str(c) for c in cm.columns[:side]]
        else:
            raise ValueError("confusion_matrix requires true/predicted labels, label/score pairs, or a numeric square matrix")

    cm = cm.astype(float).fillna(0)
    support = cm.sum(axis=1).add(cm.sum(axis=0), fill_value=0)
    classes = support.sort_values(ascending=False).index.tolist()
    if len(classes) > 12:
        keep = classes[:11]
        other = [c for c in classes if c not in keep]
        collapsed = cm.reindex(index=keep + other, columns=keep + other, fill_value=0)
        other_row = collapsed.loc[other].sum(axis=0)
        collapsed = collapsed.loc[keep]
        collapsed.loc["Other"] = other_row
        collapsed["Other"] = collapsed[other].sum(axis=1)
        cm = collapsed[keep + ["Other"]]
        classes = keep + ["Other"]
    else:
        cm = cm.reindex(index=classes, columns=classes, fill_value=0)

    row_totals = cm.sum(axis=1).replace(0, np.nan)
    row_pct = cm.div(row_totals, axis=0).fillna(0) * 100
    annot = cm.round(0).astype(int).astype(str) + "\n" + row_pct.round(0).astype(int).astype(str) + "%"
    n_classes = max(1, len(cm))

    if standalone:
        size_mm = max(82, min(130, 14 * n_classes + 36))
        fig, ax = plt.subplots(figsize=(size_mm / 25.4, size_mm / 25.4),
                               constrained_layout=True)

    annot_size = max(4.2, min(6.8, 24 / np.sqrt(n_classes)))
    sns.heatmap(row_pct, annot=annot, fmt="", cmap="Blues", vmin=0, vmax=100,
                linewidths=0.45, linecolor="white", square=True,
                annot_kws={"size": annot_size},
                cbar=standalone,
                cbar_kws={"shrink": 0.66, "label": "Row %"} if standalone else {},
                ax=ax)

    for idx in range(n_classes):
        ax.add_patch(plt.Rectangle((idx, idx), 1, 1, fill=False,
                                   edgecolor="#111111", linewidth=0.8))

    total = float(cm.to_numpy().sum())
    accuracy = float(np.trace(cm.to_numpy()) / total) if total else 0.0
    balanced = float(np.nanmean(np.diag(row_pct.to_numpy()) / 100)) if n_classes else 0.0
    offdiag = cm.copy()
    for idx in range(min(offdiag.shape)):
        offdiag.iat[idx, idx] = 0
    worst_true, worst_pred, worst_count = "", "", 0.0
    if offdiag.to_numpy().size and offdiag.to_numpy().max() > 0:
        worst_pos = np.unravel_index(np.argmax(offdiag.to_numpy()), offdiag.shape)
        worst_true = str(offdiag.index[worst_pos[0]])
        worst_pred = str(offdiag.columns[worst_pos[1]])
        worst_count = float(offdiag.iat[worst_pos])

    metric_lines = [f"accuracy={accuracy:.2f}", f"balanced={balanced:.2f}", f"n={int(total)}"]
    if worst_count > 0:
        metric_lines.append(f"max error: {worst_true}->{worst_pred}")
    ax.text(0.98, 0.03, "\n".join(metric_lines), transform=ax.transAxes,
            ha="right", va="bottom", fontsize=5.2,
            bbox={"boxstyle": "round,pad=0.22", "facecolor": "white",
                  "edgecolor": "#333333", "linewidth": 0.5, "alpha": 0.92})

    xlabels = [str(c) for c in cm.columns]
    ylabels = [str(c) for c in cm.index]
    ax.set_xticklabels(xlabels, rotation=35, ha="right", fontsize=5.4)
    ax.set_yticklabels(ylabels, rotation=0, fontsize=5.4)
    ax.set_xlabel("Predicted class" if standalone else "")
    ax.set_ylabel("True class" if standalone else "")
    ax.tick_params(length=0)
    if standalone:
        apply_chart_polish(ax, "confusion_matrix")
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


def gen_correlation(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Correlation heatmap: lower triangle with annotations.

    Operational layer (post-Phase A1): when template_mining_helpers is embedded,
    this generator uses the canonical RdBu_r diverging colormap with TwoSlopeNorm
    centered at 0 — matching the corpus-anchored discipline for correlation matrices.
    """
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

    # Diverging norm centered at 0 — matches red_blue_correlation palette anchor
    try:
        from matplotlib.colors import TwoSlopeNorm
        corr_min = float(np.nanmin(corr.values))
        corr_max = float(np.nanmax(corr.values))
        vmin = min(-1.0, corr_min) if np.isfinite(corr_min) else -1.0
        vmax = max(1.0, corr_max) if np.isfinite(corr_max) else 1.0
        if vmin >= 0.0:
            vmin = -vmax if vmax > 0 else -1.0
        if vmax <= 0.0:
            vmax = -vmin if vmin < 0 else 1.0
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)
        sns.heatmap(corr, mask=mask, ax=ax, cmap="RdBu_r", norm=norm,
                    annot=True, fmt=".2f", linewidths=0.5,
                    cbar_kws=cbar_kw, annot_kws={"size": 5},
                    square=True)
    except Exception:
        # Fallback when TwoSlopeNorm or RdBu_r unavailable in this matplotlib build
        sns.heatmap(corr, mask=mask, ax=ax, cmap="RdBu_r", center=0,
                    vmin=-1, vmax=1,
                    annot=True, fmt=".2f", linewidths=0.5,
                    cbar_kws=cbar_kw, annot_kws={"size": 5},
                    square=True)
    if standalone:
        apply_chart_polish(ax, "correlation")
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

    # Diverging norm centered at 0 — matches red_blue_correlation palette anchor
    try:
        from matplotlib.colors import TwoSlopeNorm
        m_min = float(np.nanmin(symmetric))
        m_max = float(np.nanmax(symmetric))
        vmin = min(-1.0, m_min) if np.isfinite(m_min) else -1.0
        vmax = max(1.0, m_max) if np.isfinite(m_max) else 1.0
        if vmin >= 0.0:
            vmin = -vmax if vmax > 0 else -1.0
        if vmax <= 0.0:
            vmax = -vmin if vmin < 0 else 1.0
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)
        sns.heatmap(symmetric, ax=ax, cmap="RdBu_r", norm=norm,
                    xticklabels=labels, yticklabels=labels,
                    linewidths=0.3, annot=symmetric.shape[0] <= 12,
                    fmt=".2f", annot_kws={"size": 4.5},
                    cbar_kws={"shrink": 0.6, "label": "Value"})
    except Exception:
        sns.heatmap(symmetric, ax=ax, cmap="RdBu_r", center=0,
                    vmin=-1, vmax=1,
                    xticklabels=labels, yticklabels=labels,
                    linewidths=0.3, annot=symmetric.shape[0] <= 12,
                    fmt=".2f", annot_kws={"size": 4.5},
                    cbar_kws={"shrink": 0.6, "label": "Value"})
    ax.tick_params(labelsize=5)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    if standalone:
        apply_chart_polish(ax, "heatmap_symmetric")
    return ax


def gen_heatmap_triangular(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Triangular correlation/distance heatmap aligned with corpus discipline.

    Anchor cases (template corpus):
      - 期刊复现：Nature同款皮尔逊热力图_1777451326
      - 进阶绘图：解决多变量拥挤痛点—Python 绘制带显著性星号与斜向色条的三角热图_1777452320
      - 期刊配图：基于机器学习的Spearman相关性热力图_1777456565

    Required visual grammar (from template-mining/07-techniques/heatmap-pairwise.md):
      1. RdBu_r diverging cmap (not coolwarm) — corpus anchor
      2. TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1) when value range is correlation-like
      3. Mask discipline: hide upper triangle (k=1) to show lower triangle only
      4. Significance stars overlay (when p-value column supplied — never invented)
      5. Compact colorbar (shrink=0.6) with label
      6. Square cells (square=True) and tight tick label rotation (45°)
    """
    from matplotlib.colors import TwoSlopeNorm
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
        # When correlation matrix is the natural interpretation
        if pivot.shape[0] != pivot.shape[1] and len(numeric_cols) >= 2:
            pivot = df[numeric_cols].corr()

    # ─── Triangular mask: keep lower triangle only (k=1 hides diagonal too
    # only when caller wants pure off-diagonal; default k=1 keeps diagonal)
    if pivot.shape[0] == pivot.shape[1]:
        mask = np.triu(np.ones_like(pivot, dtype=bool), k=1)
    else:
        mask = np.zeros_like(pivot, dtype=bool)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                               constrained_layout=True)

    # ─── Detect correlation-like range to apply TwoSlopeNorm + RdBu_r
    pivot_arr = pivot.values
    finite = pivot_arr[np.isfinite(pivot_arr)]
    is_correlation = (finite.size > 0
                      and float(np.nanmin(finite)) >= -1.05
                      and float(np.nanmax(finite)) <= 1.05)
    if is_correlation:
        norm = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)
        cmap_name = "RdBu_r"  # Corpus anchor — matches Nature/Cell heatmap-pairwise
        cbar_label = value_col or "Correlation"
    else:
        # Fall back to centered diverging palette anchor from template_mining_helpers
        red_blue = (palette.get("diverging")
                    or globals().get("PALETTES", {}).get("red_blue_correlation")
                    or ["#3B6FB6", "#F7F7F7", "#B5403A"])
        norm = None
        cmap_name = "RdBu_r"
        cbar_label = value_col or "Value"

    sns.heatmap(pivot, mask=mask, cmap=cmap_name, center=0 if norm is None else None,
                norm=norm, linewidths=0.3, linecolor="white", square=True,
                cbar_kws={"shrink": 0.6, "label": cbar_label, "pad": 0.02},
                ax=ax)
    # Tick discipline (corpus anchor): 45° xrotation, smaller fonts
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=6)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=6)

    pvalue_lookup = {}
    if pvalue_col and group_col and feature_col and pvalue_col in df.columns:
        for _, row in df[[feature_col, group_col, pvalue_col]].dropna().iterrows():
            pvalue_lookup[(row[feature_col], row[group_col])] = row[pvalue_col]
    apply_template_triangular_heatmap_signature(
        ax,
        row_labels=list(pivot.index),
        col_labels=list(pivot.columns),
        pvalue_lookup=pvalue_lookup,
        visualPlan=chartPlan.get("visualContentPlan", {}),
    )
    ax.set_xlabel(group_col or "")
    ax.set_ylabel(feature_col or "")
    if standalone:
        apply_chart_polish(ax, "heatmap_triangular")
    return ax
