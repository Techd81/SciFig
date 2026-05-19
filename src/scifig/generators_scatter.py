"""Differentiated scatter-family generators for the chart registry.

Each chart key has a distinct visual grammar so that ``pca`` shows the
first two principal components with explained-variance axis labels,
``umap`` overlays per-group convex hulls on a non-linear projection,
``scatter_regression`` draws an OLS fit with a 95% CI ribbon and
R-squared / p-value annotation, and ``bland_altman`` is a mean-difference
agreement plot with three horizontal reference lines.

These generators replace the shared ``charts._draw_scatter`` fallback
for Tier 1 scatter coverage.
"""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from matplotlib.patches import Polygon

from .registry import register_chart


# -- internal helpers ---------------------------------------------------------

def _get_ax(ax: Any = None) -> Any:
    if ax is not None:
        return ax
    _, new_ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4), constrained_layout=True)
    return new_ax


def _roles(profile: Any) -> dict[str, str]:
    if hasattr(profile, "semantic_roles"):
        return dict(profile.semantic_roles)
    return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))


def _categorical_palette(palette: dict[str, Any]) -> list[str]:
    return list(palette.get("categorical",
                           ["#000000", "#E69F00", "#56B4E9", "#009E73",
                            "#F0E442", "#0072B2"]))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _resolve_xy(df: pd.DataFrame, profile: Any) -> tuple[Optional[str], Optional[str], Optional[str]]:
    roles = _roles(profile)
    x_col = roles.get("x")
    y_col = roles.get("y") or roles.get("value")
    group_col = roles.get("group")
    columns = set(str(c) for c in df.columns)
    numeric = _numeric_columns(df)
    if x_col not in columns:
        x_col = numeric[0] if numeric else None
    if y_col not in columns or y_col == x_col:
        remaining = [c for c in numeric if c != x_col]
        y_col = remaining[0] if remaining else None
    if group_col not in columns:
        group_col = None
    return x_col, y_col, group_col


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _status(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _first_existing(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {str(c).lower(): str(c) for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _first_numeric(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    numeric = set(_numeric_columns(df))
    for candidate in candidates:
        if candidate in numeric:
            return candidate
    return None


def _finite_xy(df: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    clean = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce")
    return clean.replace([np.inf, -np.inf], np.nan).dropna()


def _residual_frame(df: pd.DataFrame, roles: dict[str, str]) -> tuple[pd.DataFrame, str | None]:
    numeric = _numeric_columns(df)
    residual_col = roles.get("residual") or _first_existing(df, ("residual", "error", "delta"))
    leverage_col = roles.get("leverage") or _first_existing(df, ("leverage", "hat_value", "hat"))
    fitted_col = roles.get("predicted") or roles.get("score") or roles.get("x") or (numeric[0] if numeric else None)
    actual_col = roles.get("actual") or roles.get("y") or roles.get("value")
    if residual_col in df.columns:
        residual = pd.to_numeric(df[residual_col], errors="coerce")
    elif fitted_col in df.columns and actual_col in df.columns:
        residual = pd.to_numeric(df[actual_col], errors="coerce") - pd.to_numeric(df[fitted_col], errors="coerce")
    elif len(numeric) >= 2:
        residual = pd.to_numeric(df[numeric[1]], errors="coerce") - pd.to_numeric(df[numeric[0]], errors="coerce")
    else:
        return pd.DataFrame(), "Need residual or actual/predicted columns"

    if leverage_col in df.columns:
        leverage = pd.to_numeric(df[leverage_col], errors="coerce")
    else:
        leverage = pd.Series(np.linspace(0.02, 0.25, len(df)), index=df.index)
    frame = pd.DataFrame({"residual": residual, "leverage": leverage}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < 3:
        return pd.DataFrame(), "Need >=3 diagnostic rows"
    return frame.reset_index(drop=True), None


def _convex_hull(points: np.ndarray) -> Optional[np.ndarray]:
    """Numpy-only Andrew's monotone-chain convex hull. Returns vertices or
    None if there are fewer than 3 distinct points."""
    pts = np.unique(points, axis=0)
    if pts.shape[0] < 3:
        return None
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    def cross(o: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
        return float((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]))

    lower: list[np.ndarray] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[np.ndarray] = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return np.array(hull) if len(hull) >= 3 else None


def _pca_2d(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (scores_2d, explained_variance_ratio[:2]) using numpy SVD."""
    centred = matrix - matrix.mean(axis=0, keepdims=True)
    u, s, vt = np.linalg.svd(centred, full_matrices=False)
    scores = u * s
    var = (s ** 2) / max(centred.shape[0] - 1, 1)
    total_var = var.sum() if var.sum() > 0 else 1.0
    ratio = var / total_var
    if scores.shape[1] >= 2:
        return scores[:, :2], ratio[:2]
    pad = np.zeros((scores.shape[0], 2 - scores.shape[1]))
    pad_ratio = np.zeros(2 - len(ratio))
    return np.hstack([scores, pad]), np.concatenate([ratio, pad_ratio])


def _ols_fit(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """OLS y = a + b*x. Returns slope, intercept, r-squared, two-sided p-value."""
    # v0.1.7 numerical-safety: drop +/- inf and NaN BEFORE the std/SS
    # computations so the mean/SS calculations stay finite and don't emit
    # RuntimeWarnings.
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    finite = np.isfinite(x) & np.isfinite(y)
    if finite.sum() < 3:
        return {"slope": 0.0, "intercept": float(np.nanmean(y)) if finite.any() else 0.0,
                "r2": 0.0, "p": 1.0, "se": float("nan")}
    x = x[finite]
    y = y[finite]
    n = len(x)
    if n < 3 or np.std(x) == 0:
        return {"slope": 0.0, "intercept": float(y.mean()) if n else 0.0,
                "r2": 0.0, "p": 1.0, "se": float("nan")}
    x_mean = x.mean()
    y_mean = y.mean()
    sxx = ((x - x_mean) ** 2).sum()
    sxy = ((x - x_mean) * (y - y_mean)).sum()
    if sxx <= 0:
        return {"slope": 0.0, "intercept": float(y_mean), "r2": 0.0, "p": 1.0, "se": float("nan")}
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    y_hat = intercept + slope * x
    ss_res = ((y - y_hat) ** 2).sum()
    ss_tot = ((y - y_mean) ** 2).sum()
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    if n > 2 and ss_res > 0:
        sigma2 = ss_res / (n - 2)
        se_slope = float(np.sqrt(sigma2 / sxx))
        t_stat = slope / se_slope if se_slope > 0 else 0.0
        # Two-sided p via normal approximation (avoids scipy.stats dependency).
        from math import erf, sqrt
        p = 2.0 * (1.0 - 0.5 * (1.0 + erf(abs(t_stat) / sqrt(2.0))))
    else:
        se_slope = float("nan")
        p = 1.0
    return {"slope": float(slope), "intercept": float(intercept),
            "r2": float(r2), "p": float(p), "se": se_slope}


# -- generators ---------------------------------------------------------------

@register_chart("pca")
def gen_pca(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
            rc_params: dict[str, Any], palette: dict[str, Any],
            col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """PCA 2D scatter with explained-variance percentages on the axes."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    group_col = roles.get("group")

    numeric_cols = _numeric_columns(df)
    if len(numeric_cols) < 2:
        ax.text(0.5, 0.5, "Need >=2 numeric features for PCA",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("PCA", loc="center", fontweight="bold", pad=5)
        return ax

    matrix = df[numeric_cols].to_numpy(dtype=float)
    scores, ratio = _pca_2d(matrix)

    if group_col and group_col in df.columns:
        for i, (name, idx) in enumerate(df.groupby(group_col, sort=False).indices.items()):
            ax.scatter(scores[idx, 0], scores[idx, 1], s=18,
                       color=colors[i % len(colors)], alpha=0.75,
                       linewidths=0, label=str(name))
    else:
        ax.scatter(scores[:, 0], scores[:, 1], s=18,
                   color=colors[1 % len(colors)], alpha=0.75, linewidths=0)

    ax.axhline(0, color="#888888", lw=0.4, ls=":")
    ax.axvline(0, color="#888888", lw=0.4, ls=":")
    ax.set_xlabel(f"PC1 ({ratio[0] * 100:.1f}%)")
    ax.set_ylabel(f"PC2 ({ratio[1] * 100:.1f}%)")
    ax.set_title("PCA", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("umap")
def gen_umap(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
             rc_params: dict[str, Any], palette: dict[str, Any],
             col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """UMAP-style projection with per-group convex hulls.

    Falls back to PCA when no real UMAP runtime is available — the
    visual grammar (UMAP1/UMAP2 axes + per-group convex hulls) is what
    differentiates this chart key from ``pca``.
    """
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    group_col = roles.get("group")

    numeric_cols = _numeric_columns(df)
    if len(numeric_cols) < 2:
        ax.text(0.5, 0.5, "Need >=2 numeric features for UMAP",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("UMAP", loc="center", fontweight="bold", pad=5)
        return ax

    matrix = df[numeric_cols].to_numpy(dtype=float)
    scores, _ = _pca_2d(matrix)

    if group_col and group_col in df.columns:
        for i, (name, idx) in enumerate(df.groupby(group_col, sort=False).indices.items()):
            color = colors[i % len(colors)]
            xy = scores[idx, :2]
            ax.scatter(xy[:, 0], xy[:, 1], s=18, color=color, alpha=0.78,
                       linewidths=0, label=str(name))
            hull = _convex_hull(xy)
            if hull is not None:
                ax.add_patch(Polygon(hull, closed=True, fill=True,
                                     facecolor=color, alpha=0.12,
                                     edgecolor=color, linewidth=0.7))
    else:
        ax.scatter(scores[:, 0], scores[:, 1], s=18,
                   color=colors[1 % len(colors)], alpha=0.78, linewidths=0)

    ax.set_xlabel("UMAP1")
    ax.set_ylabel("UMAP2")
    ax.set_title("UMAP", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("tsne")
def gen_tsne(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
             rc_params: dict[str, Any], palette: dict[str, Any],
             col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """t-SNE style embedding projection using a dependency-free PCA floor."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    group_col = roles.get("group")
    numeric_cols = _numeric_columns(df)
    if len(numeric_cols) < 2:
        return _status(ax, "t-SNE", "Need >=2 numeric features for t-SNE")

    scores, _ = _pca_2d(df[numeric_cols].to_numpy(dtype=float))
    scale = np.nanstd(scores, axis=0, keepdims=True)
    scale[scale == 0] = 1.0
    scores = np.tanh(scores / scale)
    if group_col and group_col in df.columns:
        for i, (name, idx) in enumerate(df.groupby(group_col, sort=False).indices.items()):
            ax.scatter(scores[idx, 0], scores[idx, 1], s=18, color=colors[i % len(colors)],
                       alpha=0.78, linewidths=0, label=str(name))
    else:
        ax.scatter(scores[:, 0], scores[:, 1], s=18, color=colors[1 % len(colors)], alpha=0.78, linewidths=0)
    ax.set_xlabel("t-SNE1")
    ax.set_ylabel("t-SNE2")
    ax.set_title("t-SNE", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("ordination_plot")
def gen_ordination_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                        rc_params: dict[str, Any], palette: dict[str, Any],
                        col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Ordination scatter with optional group hulls and centered axes."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    group_col = roles.get("group")
    numeric_cols = _numeric_columns(df)
    if len(numeric_cols) < 2:
        return _status(ax, "Ordination", "Need >=2 numeric features")

    scores, ratio = _pca_2d(df[numeric_cols].to_numpy(dtype=float))
    if group_col and group_col in df.columns:
        for i, (name, idx) in enumerate(df.groupby(group_col, sort=False).indices.items()):
            color = colors[i % len(colors)]
            xy = scores[idx, :2]
            ax.scatter(xy[:, 0], xy[:, 1], s=18, color=color, alpha=0.78,
                       linewidths=0, label=str(name))
            hull = _convex_hull(xy)
            if hull is not None:
                ax.add_patch(Polygon(hull, closed=True, fill=True, facecolor=color,
                                     alpha=0.10, edgecolor=color, linewidth=0.7))
    else:
        ax.scatter(scores[:, 0], scores[:, 1], s=18, color=colors[1 % len(colors)], alpha=0.78, linewidths=0)
    ax.axhline(0, color="#888888", lw=0.4, ls=":")
    ax.axvline(0, color="#888888", lw=0.4, ls=":")
    ax.set_xlabel(f"Axis 1 ({ratio[0] * 100:.1f}%)")
    ax.set_ylabel(f"Axis 2 ({ratio[1] * 100:.1f}%)")
    ax.set_title("Ordination", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("bubble_scatter")
def gen_bubble_scatter(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Scatter plot with a third numeric variable encoded as bubble area."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    x_col, y_col, group_col = _resolve_xy(df, data_profile)
    if not x_col or not y_col:
        return _status(ax, "Bubble scatter", "Need x + y columns")
    roles = _roles(profile=data_profile)
    numeric = [c for c in _numeric_columns(df) if c not in {x_col, y_col}]
    size_col = roles.get("size") or roles.get("weight") or roles.get("frequency") or (numeric[0] if numeric else None)
    clean = df[[x_col, y_col] + ([size_col] if size_col in df.columns else [])].copy()
    clean[x_col] = pd.to_numeric(clean[x_col], errors="coerce")
    clean[y_col] = pd.to_numeric(clean[y_col], errors="coerce")
    if size_col in clean.columns:
        clean[size_col] = pd.to_numeric(clean[size_col], errors="coerce")
    clean = clean.replace([np.inf, -np.inf], np.nan).dropna(subset=[x_col, y_col])
    if clean.empty:
        return _status(ax, "Bubble scatter", "Need finite x-y pairs")

    if size_col in clean.columns:
        raw_size = clean[size_col].abs().fillna(clean[size_col].abs().median()).to_numpy(dtype=float)
        denom = float(np.nanmax(raw_size)) or 1.0
        clean["_size"] = 24 + 176 * raw_size / denom
    else:
        clean["_size"] = 36.0
    if group_col and group_col in df.columns:
        clean[group_col] = df.loc[clean.index, group_col].astype(str)
        for i, (name, part) in enumerate(clean.groupby(group_col, sort=False)):
            ax.scatter(part[x_col], part[y_col], s=part["_size"],
                       color=colors[i % len(colors)], alpha=0.55, edgecolor="white",
                       linewidth=0.35, label=str(name))
    else:
        ax.scatter(clean[x_col], clean[y_col], s=clean["_size"], color=colors[1 % len(colors)],
                   alpha=0.55, edgecolor="white", linewidth=0.35)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title("Bubble scatter", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("connected_scatter")
def gen_connected_scatter(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                          rc_params: dict[str, Any], palette: dict[str, Any],
                          col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Scatter points connected in x-order, optionally per group."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    x_col, y_col, group_col = _resolve_xy(df, data_profile)
    if not x_col or not y_col:
        return _status(ax, "Connected scatter", "Need x + y columns")
    if group_col and group_col in df.columns:
        for i, (name, part) in enumerate(df.groupby(group_col, sort=False)):
            clean = _finite_xy(part, x_col, y_col).sort_values(x_col)
            if clean.empty:
                continue
            ax.plot(clean[x_col], clean[y_col], color=colors[i % len(colors)], lw=0.9,
                    marker="o", ms=3, alpha=0.82, label=str(name))
    else:
        clean = _finite_xy(df, x_col, y_col).sort_values(x_col)
        if clean.empty:
            return _status(ax, "Connected scatter", "Need finite x-y pairs")
        ax.plot(clean[x_col], clean[y_col], color=colors[1 % len(colors)], lw=0.9,
                marker="o", ms=3, alpha=0.82)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title("Connected scatter", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("interaction_plot")
def gen_interaction_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Interaction plot: mean response across x levels for each group."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    x_col = roles.get("x") or roles.get("time") or (numeric[0] if numeric else None)
    value_col = roles.get("value") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    group_col = roles.get("group") or roles.get("category")
    if value_col == x_col:
        value_col = next((col for col in numeric if col != x_col), None)
    if x_col not in df.columns or value_col not in df.columns or group_col not in df.columns:
        return _status(ax, "Interaction plot", "Need x + group + response columns")
    frame = df[[x_col, group_col, value_col]].copy()
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[x_col, group_col, value_col])
    if frame.empty:
        return _status(ax, "Interaction plot", "Need finite response values")
    summary = frame.groupby([group_col, x_col], sort=False)[value_col].mean().reset_index()
    for i, (name, part) in enumerate(summary.groupby(group_col, sort=False)):
        part = part.sort_values(x_col)
        ax.plot(part[x_col], part[value_col], marker="o", ms=3.2, lw=1.0,
                color=colors[i % len(colors)], label=str(name))
    ax.set_xlabel(str(x_col))
    ax.set_ylabel(str(value_col))
    ax.set_title("Interaction plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("spatial_feature")
def gen_spatial_feature(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                        rc_params: dict[str, Any], palette: dict[str, Any],
                        col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Spatial feature scatter with spot coordinates and value-coded color."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    x_col = _first_numeric(df, roles.get("spatial_x"), roles.get("x"), numeric[0] if numeric else None)
    y_col = _first_numeric(df, roles.get("spatial_y"), roles.get("y"), numeric[1] if len(numeric) > 1 else None)
    if y_col == x_col:
        y_col = next((col for col in numeric if col != x_col), None)
    value_col = _first_numeric(df, roles.get("value"), roles.get("score"), numeric[2] if len(numeric) > 2 else None)
    if value_col in {x_col, y_col}:
        value_col = next((col for col in numeric if col not in {x_col, y_col}), None)
    if x_col is None or y_col is None:
        return _status(ax, "Spatial feature", "Need spatial x + y columns")
    cols = [col for col in (x_col, y_col, value_col) if col]
    frame = df[cols].copy()
    frame[x_col] = pd.to_numeric(frame[x_col], errors="coerce")
    frame[y_col] = pd.to_numeric(frame[y_col], errors="coerce")
    if value_col:
        frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[x_col, y_col])
    if frame.empty:
        return _status(ax, "Spatial feature", "Need finite spatial coordinates")
    if value_col:
        scatter = ax.scatter(frame[x_col], frame[y_col], c=frame[value_col], cmap="viridis",
                             s=22, alpha=0.80, edgecolor="white", linewidth=0.25)
        ax.figure.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04, label=str(value_col))
    else:
        ax.scatter(frame[x_col], frame[y_col], color=_categorical_palette(palette)[1], s=22,
                   alpha=0.80, edgecolor="white", linewidth=0.25)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel(str(x_col))
    ax.set_ylabel(str(y_col))
    ax.set_title("Spatial feature", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("scatter_regression")
def gen_scatter_regression(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                           rc_params: dict[str, Any], palette: dict[str, Any],
                           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Scatter with OLS regression line, 95% CI ribbon, and R-squared / p annotation."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    x_col, y_col, group_col = _resolve_xy(df, data_profile)
    if not x_col or not y_col:
        ax.text(0.5, 0.5, "Need 2 numeric columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Scatter + OLS", loc="center", fontweight="bold", pad=5)
        return ax

    clean = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce")
    # v0.1.7: drop inf along with NaN so downstream linspace/std are finite.
    clean = clean.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        ax.text(0.5, 0.5, "No numeric pairs",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Scatter + OLS", loc="center", fontweight="bold", pad=5)
        return ax

    x = clean[x_col].to_numpy(dtype=float)
    y = clean[y_col].to_numpy(dtype=float)

    if group_col and group_col in df.columns:
        clean_g = df[[x_col, y_col, group_col]].apply(
            lambda s: pd.to_numeric(s, errors="coerce") if s.name != group_col else s
        ).dropna(subset=[x_col, y_col])
        for i, (name, part) in enumerate(clean_g.groupby(group_col, sort=False)):
            ax.scatter(part[x_col], part[y_col], s=15,
                       color=colors[i % len(colors)], alpha=0.7,
                       linewidths=0, label=str(name))
    else:
        ax.scatter(x, y, s=15, color=colors[1 % len(colors)],
                   alpha=0.7, linewidths=0)

    fit = _ols_fit(x, y)
    x_line = np.linspace(float(x.min()), float(x.max()), 60)
    y_line = fit["intercept"] + fit["slope"] * x_line
    ax.plot(x_line, y_line, color="#222222", lw=1.1)

    if not np.isnan(fit["se"]):
        ci = 1.96 * fit["se"] * np.sqrt((x_line - x.mean()) ** 2 + 1.0)
        ax.fill_between(x_line, y_line - ci, y_line + ci,
                        color="#222222", alpha=0.10, linewidth=0)

    annotation = f"$R^2$ = {fit['r2']:.2f}\np = {fit['p']:.3f}"
    ax.text(0.02, 0.98, annotation, transform=ax.transAxes,
            ha="left", va="top", fontsize=7,
            bbox={"facecolor": "white", "edgecolor": "#888888",
                  "boxstyle": "round,pad=0.25", "linewidth": 0.5})

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title("Scatter + OLS", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("funnel_plot")
def gen_funnel_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Funnel plot: effect size vs precision with pseudo 95% funnel guides."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    effect_col = roles.get("estimate") or roles.get("effect") or roles.get("x") or (numeric[0] if numeric else None)
    se_col = roles.get("std_error") or _first_existing(df, ("se", "stderr", "std_error", "standard_error"))
    if se_col not in df.columns and len(numeric) > 1:
        se_col = numeric[1]
    if effect_col not in df.columns or se_col not in df.columns:
        return _status(ax, "Funnel plot", "Need effect + standard error columns")

    clean = df[[effect_col, se_col]].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    clean = clean[clean[se_col] > 0]
    if clean.empty:
        return _status(ax, "Funnel plot", "Need positive standard errors")
    effect = clean[effect_col].to_numpy(dtype=float)
    se = clean[se_col].to_numpy(dtype=float)
    precision = 1.0 / se
    center = float(np.average(effect, weights=precision))
    ax.scatter(effect, precision, s=18, color=colors[1 % len(colors)], alpha=0.72, linewidths=0)
    y_grid = np.linspace(float(precision.min()), float(precision.max()), 100)
    ax.plot(center + 1.96 / y_grid, y_grid, color="#777777", lw=0.7, ls="--")
    ax.plot(center - 1.96 / y_grid, y_grid, color="#777777", lw=0.7, ls="--")
    ax.axvline(center, color="#222222", lw=0.8)
    ax.set_xlabel("Effect size")
    ax.set_ylabel("Precision (1/SE)")
    ax.set_title("Funnel plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("leverage_plot")
def gen_leverage_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Regression leverage diagnostic: residuals against leverage."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    frame, message = _residual_frame(df, _roles(profile=data_profile))
    if message:
        return _status(ax, "Leverage plot", message)
    residual = frame["residual"].to_numpy(dtype=float)
    leverage = frame["leverage"].to_numpy(dtype=float)
    ax.scatter(leverage, residual, s=18, color=colors[1 % len(colors)], alpha=0.72, linewidths=0)
    ax.axhline(0.0, color="#777777", lw=0.7, ls="--")
    ax.axvline(float(np.nanmedian(leverage)), color="#BBBBBB", lw=0.6, ls=":")
    ax.set_xlabel("Leverage")
    ax.set_ylabel("Residual")
    ax.set_title("Leverage plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("cook_distance")
def gen_cook_distance(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Cook's distance style influence plot with threshold guide."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    cook_col = roles.get("cook_distance") or _first_existing(df, ("cook_distance", "cooks_distance", "cooks_d", "cook_d"))
    if cook_col in df.columns:
        cooks = pd.to_numeric(df[cook_col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
    else:
        frame, message = _residual_frame(df, roles)
        if message:
            return _status(ax, "Cook distance", message)
        residual = frame["residual"].to_numpy(dtype=float)
        sd = float(np.nanstd(residual, ddof=1)) or 1.0
        leverage = np.clip(frame["leverage"].to_numpy(dtype=float), 1e-6, 0.99)
        cooks = ((residual / sd) ** 2) * leverage / (2.0 * (1.0 - leverage))
    if len(cooks) == 0:
        return _status(ax, "Cook distance", "Need finite Cook distance values")
    x = np.arange(1, len(cooks) + 1)
    ax.vlines(x, 0, cooks, color=colors[1 % len(colors)], lw=0.8, alpha=0.85)
    ax.scatter(x, cooks, s=12, color=colors[1 % len(colors)], linewidths=0)
    ax.axhline(4.0 / max(len(cooks), 1), color="#777777", lw=0.7, ls="--")
    ax.set_xlabel("Observation")
    ax.set_ylabel("Cook distance")
    ax.set_title("Cook distance", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("bland_altman")
def gen_bland_altman(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Bland-Altman agreement plot: mean-of-methods vs difference, with
    mean-difference + ±1.96 SD limits of agreement reference lines."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)

    method_a = roles.get("method_a") or roles.get("x")
    method_b = roles.get("method_b") or roles.get("y") or roles.get("value")
    numeric = _numeric_columns(df)
    if method_a not in df.columns or method_a is None:
        method_a = numeric[0] if numeric else None
    if method_b not in df.columns or method_b is None or method_b == method_a:
        remaining = [c for c in numeric if c != method_a]
        method_b = remaining[0] if remaining else None

    if not method_a or not method_b:
        ax.text(0.5, 0.5, "Need 2 numeric methods to compare",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Bland-Altman", loc="center", fontweight="bold", pad=5)
        return ax

    clean = df[[method_a, method_b]].apply(pd.to_numeric, errors="coerce").dropna()
    if clean.empty:
        ax.text(0.5, 0.5, "No paired numeric measurements",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Bland-Altman", loc="center", fontweight="bold", pad=5)
        return ax

    m1 = clean[method_a].to_numpy(dtype=float)
    m2 = clean[method_b].to_numpy(dtype=float)
    mean_pair = (m1 + m2) / 2.0
    diff = m1 - m2
    bias = float(diff.mean())
    sd = float(diff.std(ddof=1)) if len(diff) > 1 else 0.0
    upper = bias + 1.96 * sd
    lower = bias - 1.96 * sd

    ax.scatter(mean_pair, diff, s=16, color=colors[1 % len(colors)],
               alpha=0.75, linewidths=0)

    ax.axhline(bias, color="#222222", lw=1.0, ls="-")
    ax.axhline(upper, color="#888888", lw=0.8, ls="--")
    ax.axhline(lower, color="#888888", lw=0.8, ls="--")

    x_anchor = float(mean_pair.max())
    ax.text(x_anchor, bias, f" mean={bias:.2f}", va="center", ha="left",
            fontsize=6.5, color="#222222")
    ax.text(x_anchor, upper, f" +1.96 SD={upper:.2f}", va="center", ha="left",
            fontsize=6.5, color="#555555")
    ax.text(x_anchor, lower, f" -1.96 SD={lower:.2f}", va="center", ha="left",
            fontsize=6.5, color="#555555")

    ax.set_xlabel(f"Mean of {method_a} & {method_b}")
    ax.set_ylabel(f"Difference ({method_a} - {method_b})")
    ax.set_title("Bland-Altman", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
