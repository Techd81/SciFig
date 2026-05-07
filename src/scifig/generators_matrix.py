"""Differentiated matrix-family generators for the chart registry.

Each chart key has a distinct visual grammar so that ``heatmap_cluster``
shows a correlation-ordered heatmap with dendrogram brackets, ``heatmap_pure``
is a clean unannotated heatmap with continuous palette, ``confusion_matrix``
emphasises the diagonal with TP/FP/FN/TN-style cell annotations, and
``correlation`` uses a diverging palette centred at 0 with off-diagonal
coefficient labels.

Legends are figure-level (Figure.render bottom-center) or expressed as
colorbars; in-axes legends are forbidden by the project lint.
"""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Rectangle

from .registry import register_chart


# -- internal helpers ---------------------------------------------------------

def _get_ax(ax: Any = None) -> Any:
    if ax is not None:
        return ax
    _, new_ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4), constrained_layout=True)
    return new_ax


def _numeric_matrix(df: pd.DataFrame) -> pd.DataFrame:
    matrix = df.select_dtypes(include=[np.number])
    if matrix.empty:
        joined = df.astype(str).agg("|".join, axis=1)
        codes, _ = pd.factorize(joined)
        matrix = pd.DataFrame({"code": codes})
    return matrix


def _correlation_order(matrix: pd.DataFrame) -> list[int]:
    """Greedy nearest-neighbour ordering using column correlation.

    Replaces a full hierarchical clustering library with a numpy-only
    approximation so we don't introduce a scipy.cluster dependency just
    for the visual hint.
    """
    if matrix.shape[1] <= 1:
        return list(range(matrix.shape[1]))
    corr = matrix.corr().fillna(0.0).to_numpy()
    n = corr.shape[0]
    visited = [0]
    remaining = set(range(1, n))
    while remaining:
        last = visited[-1]
        best = max(remaining, key=lambda j: corr[last, j])
        visited.append(best)
        remaining.remove(best)
    return visited


def _tick_labels(values: Any) -> list[str]:
    return [str(v) for v in values]


# -- generators ---------------------------------------------------------------

@register_chart("heatmap_cluster")
def gen_heatmap_cluster(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                        rc_params: dict[str, Any], palette: dict[str, Any],
                        col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Heatmap with rows/columns reordered via correlation clustering and
    side dendrogram-style brackets indicating the ordering."""
    ax = _get_ax(ax)
    matrix = _numeric_matrix(df)
    if matrix.empty:
        ax.text(0.5, 0.5, "No numeric data", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Heatmap (clustered)", loc="center", fontweight="bold", pad=5)
        return ax

    col_order = _correlation_order(matrix)
    row_matrix = matrix.T if matrix.shape[0] > 1 else matrix
    row_order = _correlation_order(row_matrix) if matrix.shape[0] > 1 else [0]
    reordered = matrix.iloc[row_order, col_order]

    image = ax.imshow(reordered.to_numpy(), aspect="auto", cmap="viridis")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Value")

    n_cols = reordered.shape[1]
    if n_cols > 1:
        bracket_top = -0.7
        bracket_bottom = -0.3
        ax.plot([0, n_cols - 1], [bracket_top, bracket_top],
                color="#444444", lw=0.6, clip_on=False)
        for i in range(n_cols):
            ax.plot([i, i], [bracket_top, bracket_bottom],
                    color="#444444", lw=0.5, clip_on=False)

    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(_tick_labels(reordered.columns), rotation=30, ha="right")
    ax.set_yticks(range(reordered.shape[0]))
    ax.set_yticklabels(_tick_labels(reordered.index))
    ax.set_xlabel("Features (clustered)")
    ax.set_ylabel("Observations (clustered)")
    ax.set_title("Heatmap (clustered)", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("heatmap_pure")
def gen_heatmap_pure(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Pure heatmap — no annotations, no dendrogram, continuous palette."""
    ax = _get_ax(ax)
    matrix = _numeric_matrix(df)
    if matrix.empty:
        ax.text(0.5, 0.5, "No numeric data", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Heatmap", loc="center", fontweight="bold", pad=5)
        return ax

    image = ax.imshow(matrix.to_numpy(), aspect="auto", cmap="viridis")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Value")

    ax.set_xticks(range(matrix.shape[1]))
    ax.set_xticklabels(_tick_labels(matrix.columns), rotation=30, ha="right")
    ax.set_yticks([])
    ax.set_xlabel("Features")
    ax.set_ylabel("Observations")
    ax.set_title("Heatmap", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("confusion_matrix")
def gen_confusion_matrix(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Square confusion matrix with diagonal-emphasis Blues palette and
    per-cell count + percentage annotations."""
    ax = _get_ax(ax)
    matrix_full = _numeric_matrix(df)
    if matrix_full.empty:
        ax.text(0.5, 0.5, "No numeric data", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Confusion matrix", loc="center", fontweight="bold", pad=5)
        return ax

    n = min(matrix_full.shape)
    matrix = matrix_full.iloc[:n, :n].abs()
    counts = matrix.to_numpy(dtype=float)
    total = counts.sum() if counts.sum() > 0 else 1.0
    pct = counts / total * 100.0

    image = ax.imshow(counts, aspect="equal", cmap="Blues")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Count")

    for i in range(n):
        ax.add_patch(Rectangle((i - 0.5, i - 0.5), 1, 1, fill=False,
                               edgecolor="#222222", lw=1.2, clip_on=False))

    threshold = counts.max() / 2.0 if counts.max() > 0 else 0.0
    for i in range(n):
        for j in range(n):
            color = "white" if counts[i, j] > threshold else "#222222"
            ax.text(j, i - 0.18, f"{int(round(counts[i, j]))}",
                    ha="center", va="center", color=color,
                    fontsize=7, fontweight="bold")
            ax.text(j, i + 0.22, f"{pct[i, j]:.1f}%",
                    ha="center", va="center", color=color, fontsize=6)

    labels = _tick_labels(matrix.columns)
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion matrix", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("correlation")
def gen_correlation(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Correlation matrix with diverging palette (RdBu_r) centred at 0
    and off-diagonal coefficient annotations."""
    ax = _get_ax(ax)
    matrix = _numeric_matrix(df)
    if matrix.shape[1] < 2:
        ax.text(0.5, 0.5, "Need >=2 numeric columns", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Correlation", loc="center", fontweight="bold", pad=5)
        return ax

    corr = matrix.corr().fillna(0.0)
    norm = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)
    image = ax.imshow(corr.to_numpy(), aspect="equal", cmap="RdBu_r", norm=norm)
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Pearson r")

    n = corr.shape[0]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            value = float(corr.iat[i, j])
            color = "white" if abs(value) > 0.5 else "#222222"
            ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                    color=color, fontsize=6.5)

    labels = _tick_labels(corr.columns)
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Variables")
    ax.set_ylabel("Variables")
    ax.set_title("Correlation", loc="center", fontweight="bold", pad=5)
    return ax
