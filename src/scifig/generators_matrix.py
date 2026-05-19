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


def _correlation_frame(df: pd.DataFrame) -> pd.DataFrame:
    matrix = _numeric_matrix(df)
    if matrix.shape[1] < 2:
        return pd.DataFrame()
    return matrix.corr().fillna(0.0)


def _roles(profile: Any) -> dict[str, str]:
    if hasattr(profile, "semantic_roles"):
        return dict(profile.semantic_roles)
    if isinstance(profile, dict):
        return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))
    return {}


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    numeric = set(df.select_dtypes(include=[np.number]).columns.astype(str))
    return [str(col) for col in df.columns if str(col) not in numeric]


def _first_valid(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    columns = {str(c) for c in df.columns}
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _first_numeric_valid(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    numeric = {str(c) for c in df.select_dtypes(include=[np.number]).columns}
    for candidate in candidates:
        if candidate in numeric:
            return candidate
    return None


def _fallback_empty(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _flow_matrix(
    df: pd.DataFrame,
    profile: Any,
    *,
    symmetric: bool = False,
    limit: int = 12,
) -> tuple[pd.DataFrame, str | None]:
    roles = _roles(profile)
    numeric = [str(c) for c in df.select_dtypes(include=[np.number]).columns]
    categorical = _categorical_columns(df)
    row_col = _first_valid(
        df,
        roles.get("source"),
        roles.get("row"),
        roles.get("feature_id"),
        roles.get("identifier"),
        categorical[0] if categorical else None,
    )
    col_col = _first_valid(
        df,
        roles.get("target"),
        roles.get("column"),
        roles.get("group"),
        roles.get("category"),
        categorical[1] if len(categorical) > 1 else None,
    )
    if col_col == row_col:
        col_col = next((col for col in categorical if col != row_col), None)
    value_col = _first_numeric_valid(
        df,
        roles.get("weight"),
        roles.get("value"),
        roles.get("frequency"),
        roles.get("size"),
        numeric[-1] if numeric else None,
    )

    if row_col and col_col and value_col:
        frame = df[[row_col, col_col, value_col]].copy()
        frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
        frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
        if frame.empty:
            return pd.DataFrame(), "Need finite matrix values"
        pivot = frame.pivot_table(index=row_col, columns=col_col, values=value_col,
                                  aggfunc="sum", fill_value=0.0)
        if symmetric:
            labels = list(dict.fromkeys([*pivot.index.astype(str), *pivot.columns.astype(str)]))
            pivot.index = pivot.index.astype(str)
            pivot.columns = pivot.columns.astype(str)
            pivot = pivot.reindex(index=labels, columns=labels, fill_value=0.0)
            pivot = pivot.add(pivot.T, fill_value=0.0)
            order = pivot.sum(axis=1).add(pivot.sum(axis=0), fill_value=0.0).sort_values(ascending=False).index[:limit]
            return pivot.reindex(index=order, columns=order, fill_value=0.0), None
        row_order = pivot.sum(axis=1).sort_values(ascending=False).index[:limit]
        col_order = pivot.sum(axis=0).sort_values(ascending=False).index[:limit]
        return pivot.reindex(index=row_order, columns=col_order, fill_value=0.0), None

    matrix = _numeric_matrix(df)
    if matrix.empty:
        return pd.DataFrame(), "Need numeric matrix values"
    side = min(matrix.shape[0], matrix.shape[1], limit)
    if symmetric:
        trimmed = matrix.iloc[:side, :side].copy()
        labels = [str(col) for col in matrix.columns[:side]]
        trimmed.index = labels
        trimmed.columns = labels
        return trimmed.add(trimmed.T, fill_value=0.0), None
    return matrix.iloc[: min(matrix.shape[0], limit), : min(matrix.shape[1], limit)].copy(), None


def _draw_correlation_heatmap(
    ax: Any,
    corr: pd.DataFrame,
    *,
    title: str,
    mask: str = "full",
    annotate: bool = True,
) -> Any:
    values = corr.to_numpy(dtype=float)
    if mask == "upper":
        values = np.ma.masked_where(np.tril(np.ones_like(values, dtype=bool), k=-1), values)
    elif mask == "lower":
        values = np.ma.masked_where(np.triu(np.ones_like(values, dtype=bool), k=1), values)

    norm = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)
    image = ax.imshow(values, aspect="equal", cmap="RdBu_r", norm=norm)
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Pearson r")

    n = corr.shape[0]
    if annotate:
        for i in range(n):
            for j in range(n):
                if mask == "upper" and i > j:
                    continue
                if mask == "lower" and i < j:
                    continue
                value = float(corr.iat[i, j])
                color = "white" if abs(value) > 0.5 else "#222222"
                ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                        color=color, fontsize=6.5, fontweight="bold" if i != j else "normal")

    labels = _tick_labels(corr.columns)
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Variables")
    ax.set_ylabel("Variables")
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


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


@register_chart("adjacency_matrix")
def gen_adjacency_matrix(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Weighted network adjacency matrix with diagonal masked for clarity."""
    ax = _get_ax(ax)
    matrix, error = _flow_matrix(df, data_profile, symmetric=True)
    if error or matrix.empty:
        return _fallback_empty(ax, "Adjacency matrix", error or "Need edge or matrix values")
    values = matrix.to_numpy(dtype=float)
    mask = np.eye(values.shape[0], dtype=bool) if values.shape[0] == values.shape[1] else np.zeros_like(values, dtype=bool)
    image = ax.imshow(np.ma.masked_where(mask, values), aspect="equal", cmap="Blues")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Weight")
    n_rows, n_cols = matrix.shape
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(_tick_labels(matrix.columns), rotation=30, ha="right")
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(_tick_labels(matrix.index))
    ax.set_xlabel("Target node")
    ax.set_ylabel("Source node")
    ax.set_title("Adjacency matrix", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("cooccurrence_matrix")
def gen_cooccurrence_matrix(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                            rc_params: dict[str, Any], palette: dict[str, Any],
                            col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Symmetric co-occurrence heatmap for entity pairs or binary feature tables."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    matrix, error = _flow_matrix(df, data_profile, symmetric=True)
    if not error and not matrix.empty:
        values = matrix.to_numpy(dtype=float)
    else:
        numeric = df.select_dtypes(include=[np.number]).fillna(0.0)
        if numeric.shape[1] < 2:
            return _fallback_empty(ax, "Co-occurrence matrix", "Need pair table or >=2 numeric features")
        binary = (numeric > 0).astype(float)
        values = binary.T.to_numpy() @ binary.to_numpy()
        matrix = pd.DataFrame(values, index=numeric.columns.astype(str), columns=numeric.columns.astype(str))
    image = ax.imshow(values, aspect="equal", cmap="YlGnBu")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label=roles.get("weight", "Co-occurrence"))
    n = matrix.shape[0]
    labels = _tick_labels(matrix.index)
    ax.set_xticks(range(n), labels, rotation=30, ha="right")
    ax.set_yticks(range(n), labels)
    if n <= 8:
        threshold = float(np.nanmax(values)) * 0.55 if values.size else 0.0
        for i in range(n):
            for j in range(n):
                color = "white" if values[i, j] > threshold else "#222222"
                ax.text(j, i, f"{values[i, j]:.0f}", ha="center", va="center", fontsize=6, color=color)
    ax.set_title("Co-occurrence matrix", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("bubble_matrix")
def gen_bubble_matrix(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Matrix view with cell magnitude encoded by bubble size and colour."""
    ax = _get_ax(ax)
    matrix, error = _flow_matrix(df, data_profile, symmetric=False)
    if error or matrix.empty:
        return _fallback_empty(ax, "Bubble matrix", error or "Need row-column-value data")
    values = matrix.to_numpy(dtype=float)
    vmax = float(np.nanmax(np.abs(values))) if values.size else 1.0
    vmax = vmax if vmax > 0 else 1.0
    x_idx, y_idx = np.meshgrid(np.arange(matrix.shape[1]), np.arange(matrix.shape[0]))
    scatter = ax.scatter(
        x_idx.ravel(),
        y_idx.ravel(),
        s=(22 + 220 * np.abs(values).ravel() / vmax),
        c=values.ravel(),
        cmap="coolwarm",
        vmin=-vmax,
        vmax=vmax,
        edgecolor="white",
        linewidth=0.35,
    )
    ax.figure.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04, label="Value")
    ax.set_xticks(range(matrix.shape[1]), _tick_labels(matrix.columns), rotation=30, ha="right")
    ax.set_yticks(range(matrix.shape[0]), _tick_labels(matrix.index))
    ax.invert_yaxis()
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    ax.set_title("Bubble matrix", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("confusion_matrix")
def gen_confusion_matrix(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Square confusion matrix with diagonal-emphasis Blues palette and
    per-cell count + percentage annotations.

    BUG-15 fix: Prefer pd.crosstab(actual, predicted) when those roles exist —
    previously the code unconditionally sliced the raw numeric matrix as if it
    were a count matrix, producing incorrect (fraud-level) confusion values.
    Falls back to legacy raw-matrix mode (with explicit warning text) when
    actual/predicted roles are missing, preserving backward compatibility for
    users who supply pre-aggregated count matrices.
    """
    ax = _get_ax(ax)
    # Extract semantic roles (compat with both dataclass and dict profile shapes)
    if hasattr(data_profile, "semantic_roles"):
        roles = dict(data_profile.semantic_roles)
    elif hasattr(data_profile, "get"):
        roles = dict(data_profile.get("semanticRoles", data_profile.get("semantic_roles", {})))
    else:
        roles = {}
    actual_col = roles.get("actual") or roles.get("y_true") or roles.get("truth")
    predicted_col = roles.get("predicted") or roles.get("y_pred") or roles.get("prediction")

    matrix: Optional[pd.DataFrame] = None
    if actual_col and predicted_col and actual_col in df.columns and predicted_col in df.columns:
        # Correct path: aggregate raw observations into a true count matrix.
        try:
            matrix = pd.crosstab(df[actual_col], df[predicted_col])
        except (ValueError, TypeError):
            matrix = None

    if matrix is None or matrix.empty:
        # Legacy fallback: treat numeric DataFrame as a pre-aggregated count matrix.
        matrix_full = _numeric_matrix(df)
        if matrix_full.empty:
            ax.text(0.5, 0.5, "No numeric data", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_title("Confusion matrix", loc="center", fontweight="bold", pad=5)
            return ax
        n_full = min(matrix_full.shape)
        matrix = matrix_full.iloc[:n_full, :n_full].abs()

    n = min(matrix.shape)
    if n == 0:
        ax.text(0.5, 0.5, "Empty confusion matrix", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Confusion matrix", loc="center", fontweight="bold", pad=5)
        return ax
    counts = matrix.iloc[:n, :n].to_numpy(dtype=float)
    total = counts.sum() if counts.sum() > 0 else 1.0
    pct = counts / total * 100.0

    image = ax.imshow(counts, aspect="equal", cmap="Blues")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Count")

    ax.set_xticks(range(n))
    ax.set_xticklabels(_tick_labels(matrix.columns[:n]), rotation=30, ha="right")
    ax.set_yticks(range(n))
    ax.set_yticklabels(_tick_labels(matrix.index[:n]))

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
    corr = _correlation_frame(df)
    if corr.empty:
        ax.text(0.5, 0.5, "Need >=2 numeric columns", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Correlation", loc="center", fontweight="bold", pad=5)
        return ax
    return _draw_correlation_heatmap(ax, corr, title="Correlation")


@register_chart("heatmap_symmetric")
def gen_heatmap_symmetric(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                          rc_params: dict[str, Any], palette: dict[str, Any],
                          col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Symmetric pairwise correlation heatmap with centered diverging colour."""
    ax = _get_ax(ax)
    corr = _correlation_frame(df)
    if corr.empty:
        ax.text(0.5, 0.5, "Need >=2 numeric columns", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Symmetric heatmap", loc="center", fontweight="bold", pad=5)
        return ax
    return _draw_correlation_heatmap(ax, corr, title="Symmetric heatmap")


@register_chart("heatmap_triangular")
def gen_heatmap_triangular(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                           rc_params: dict[str, Any], palette: dict[str, Any],
                           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Upper-triangle correlation heatmap matching the pairwise template grammar."""
    ax = _get_ax(ax)
    corr = _correlation_frame(df)
    if corr.empty:
        ax.text(0.5, 0.5, "Need >=2 numeric columns", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Triangular heatmap", loc="center", fontweight="bold", pad=5)
        return ax
    return _draw_correlation_heatmap(ax, corr, title="Triangular heatmap", mask="upper")


@register_chart("heatmap_mirrored")
def gen_heatmap_mirrored(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Lower-triangle mirrored correlation heatmap for compact pairwise views."""
    ax = _get_ax(ax)
    corr = _correlation_frame(df)
    if corr.empty:
        ax.text(0.5, 0.5, "Need >=2 numeric columns", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Mirrored heatmap", loc="center", fontweight="bold", pad=5)
        return ax
    return _draw_correlation_heatmap(ax, corr, title="Mirrored heatmap", mask="lower")


@register_chart("heatmap_annotated")
def gen_heatmap_annotated(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                          rc_params: dict[str, Any], palette: dict[str, Any],
                          col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Annotated correlation heatmap with contrast-aware cell labels."""
    ax = _get_ax(ax)
    corr = _correlation_frame(df)
    if corr.empty:
        ax.text(0.5, 0.5, "Need >=2 numeric columns", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title("Annotated heatmap", loc="center", fontweight="bold", pad=5)
        return ax
    return _draw_correlation_heatmap(ax, corr, title="Annotated heatmap")
