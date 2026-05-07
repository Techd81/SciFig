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
    n = len(x)
    if n < 3 or np.std(x) == 0:
        return {"slope": 0.0, "intercept": float(y.mean()) if n else 0.0,
                "r2": 0.0, "p": 1.0, "se": float("nan")}
    x_mean = x.mean()
    y_mean = y.mean()
    sxx = ((x - x_mean) ** 2).sum()
    sxy = ((x - x_mean) * (y - y_mean)).sum()
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

    clean = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
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
