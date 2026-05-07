"""Differentiated distribution-family generators for the 121-chart registry.

Each chart key has a distinct visual grammar so that ``violin_strip`` does not
look like ``box_strip`` and ``raincloud`` shows the layered violin+box+strip
sandwich instead of a generic violin.

All generators obey the project's legend contract (no ``loc='best'``,
no in-axes ``bbox_to_anchor=(1.0X, ...)``); group labels use
``ax.set_xticks`` for axes labels rather than ax.legend.
"""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

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


def _resolve_group_value(df: pd.DataFrame, profile: Any) -> tuple[Optional[str], Optional[str]]:
    roles = _roles(profile)
    group = roles.get("group")
    value = roles.get("value") or roles.get("y")
    if group not in (df.columns if df is not None else []):
        group = None
    if value not in (df.columns if df is not None else []):
        value = None
    return group, value


def _grouped_series(df: pd.DataFrame, group: str, value: str) -> tuple[list[pd.Series], list[str]]:
    series: list[pd.Series] = []
    labels: list[str] = []
    for name, part in df.groupby(group, sort=False):
        s = pd.to_numeric(part[value], errors="coerce").dropna()
        if len(s):
            series.append(s)
            labels.append(str(name))
    return series, labels


def _categorical_palette(palette: dict[str, Any]) -> list[str]:
    return list(palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2"]))


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.6, pad=2)


def _annotate_n(ax: Any, x_positions: list[int], series: list[pd.Series]) -> None:
    """Show n=… per group below the x-axis without colliding with tick labels."""
    if not series:
        return
    y_min = min((float(s.min()) for s in series if len(s)), default=0.0)
    y_max = max((float(s.max()) for s in series if len(s)), default=1.0)
    span = max(y_max - y_min, 1e-9)
    y_text = y_min - span * 0.15
    for x_pos, s in zip(x_positions, series):
        ax.text(x_pos, y_text, f"n={len(s)}", ha="center", va="top", fontsize=5,
                color="#555555", clip_on=False)


def _fallback_singleton(ax: Any, df: pd.DataFrame, value: Optional[str], colors: list[str], chart: str) -> Any:
    """When group/value resolution fails, draw a histogram of the first numeric column."""
    numeric = [str(c) for c in df.select_dtypes(include=[np.number]).columns]
    target = value if value in df.columns else (numeric[0] if numeric else None)
    if target is None:
        ax.text(0.5, 0.5, "No plottable columns", ha="center", va="center", transform=ax.transAxes)
    else:
        s = pd.to_numeric(df[target], errors="coerce").dropna()
        ax.hist(s, bins="auto", color=colors[1 % len(colors)], alpha=0.75,
                edgecolor="white", linewidth=0.4)
        ax.set_xlabel(target)
        ax.set_ylabel("Frequency")
    ax.set_title(chart.replace("_", " ").title(), loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- generators ---------------------------------------------------------------

@register_chart("violin_strip")
def gen_violin_strip(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Violin body + median bar + per-point strip overlay (sample-shape evidence)."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    group, value = _resolve_group_value(df, data_profile)
    if not group or not value:
        return _fallback_singleton(ax, df, value, colors, "violin_strip")
    series, labels = _grouped_series(df, group, value)
    if not series:
        return _fallback_singleton(ax, df, value, colors, "violin_strip")
    positions = list(range(1, len(series) + 1))
    body = ax.violinplot(series, positions=positions, showmedians=True, widths=0.7)
    for i, pc in enumerate(body["bodies"]):
        pc.set_facecolor(colors[i % len(colors)])
        pc.set_edgecolor(colors[i % len(colors)])
        pc.set_alpha(0.35)
    for key in ("cmedians", "cmins", "cmaxes", "cbars"):
        if key in body:
            body[key].set_color("#333333")
            body[key].set_linewidth(0.8)
    rng = np.random.default_rng(42)
    for x_pos, s, color in zip(positions, series, colors):
        jitter = rng.uniform(-0.1, 0.1, size=len(s))
        ax.scatter(np.full(len(s), x_pos) + jitter, s, s=8, color=color,
                   alpha=0.7, linewidths=0)
    ax.set_xticks(positions, labels, rotation=30, ha="right")
    ax.set_xlabel(group)
    ax.set_ylabel(value)
    _annotate_n(ax, positions, series)
    ax.set_title("Violin + strip", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("box_strip")
def gen_box_strip(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Filled boxplot (IQR + median + whiskers) with per-point strip overlay."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    group, value = _resolve_group_value(df, data_profile)
    if not group or not value:
        return _fallback_singleton(ax, df, value, colors, "box_strip")
    series, labels = _grouped_series(df, group, value)
    if not series:
        return _fallback_singleton(ax, df, value, colors, "box_strip")
    positions = list(range(1, len(series) + 1))
    try:
        bp = ax.boxplot(series, positions=positions, widths=0.55, patch_artist=True,
                        tick_labels=labels, showfliers=False)
    except TypeError:
        bp = ax.boxplot(series, positions=positions, widths=0.55, patch_artist=True,
                        labels=labels, showfliers=False)
    for i, box in enumerate(bp["boxes"]):
        box.set_facecolor(colors[i % len(colors)])
        box.set_alpha(0.55)
        box.set_edgecolor("#333333")
    for whisker in bp["whiskers"] + bp["caps"]:
        whisker.set_color("#333333")
        whisker.set_linewidth(0.7)
    for med in bp["medians"]:
        med.set_color("#000000")
        med.set_linewidth(1.0)
    rng = np.random.default_rng(43)
    for x_pos, s, color in zip(positions, series, colors):
        jitter = rng.uniform(-0.12, 0.12, size=len(s))
        ax.scatter(np.full(len(s), x_pos) + jitter, s, s=8, color=color,
                   alpha=0.7, linewidths=0)
    ax.set_xlabel(group)
    ax.set_ylabel(value)
    _annotate_n(ax, positions, series)
    ax.set_title("Box + strip", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("raincloud")
def gen_raincloud(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Half-violin (cloud) above + thin box (rain bar) + jittered strip (rain)."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    group, value = _resolve_group_value(df, data_profile)
    if not group or not value:
        return _fallback_singleton(ax, df, value, colors, "raincloud")
    series, labels = _grouped_series(df, group, value)
    if not series:
        return _fallback_singleton(ax, df, value, colors, "raincloud")
    positions = list(range(1, len(series) + 1))
    body = ax.violinplot(series, positions=positions, showmedians=False,
                         showmeans=False, showextrema=False, widths=0.9)
    for i, pc in enumerate(body["bodies"]):
        verts = pc.get_paths()[0].vertices
        # Keep only the right half (cloud)
        verts[:, 0] = np.clip(verts[:, 0], positions[i], positions[i] + 0.5)
        pc.set_facecolor(colors[i % len(colors)])
        pc.set_edgecolor(colors[i % len(colors)])
        pc.set_alpha(0.45)
    # Thin median box positioned just left of the violin
    box_positions = [p - 0.1 for p in positions]
    try:
        bp = ax.boxplot(series, positions=box_positions, widths=0.12,
                        patch_artist=True, tick_labels=[""] * len(series),
                        showfliers=False, showcaps=False)
    except TypeError:
        bp = ax.boxplot(series, positions=box_positions, widths=0.12,
                        patch_artist=True, labels=[""] * len(series),
                        showfliers=False, showcaps=False)
    for i, box in enumerate(bp["boxes"]):
        box.set_facecolor("white")
        box.set_edgecolor(colors[i % len(colors)])
        box.set_linewidth(0.9)
    for med in bp["medians"]:
        med.set_color("#000000")
        med.set_linewidth(1.0)
    for whisker in bp["whiskers"]:
        whisker.set_color(colors[0])
        whisker.set_linewidth(0.6)
    rng = np.random.default_rng(44)
    for x_pos, s, color in zip(positions, series, colors):
        jitter = rng.uniform(-0.4, -0.18, size=len(s))
        ax.scatter(np.full(len(s), x_pos) + jitter, s, s=7, color=color,
                   alpha=0.7, linewidths=0)
    ax.set_xticks(positions, labels, rotation=30, ha="right")
    ax.set_xlabel(group)
    ax.set_ylabel(value)
    _annotate_n(ax, positions, series)
    ax.set_title("Raincloud", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("beeswarm")
def gen_beeswarm(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                 rc_params: dict[str, Any], palette: dict[str, Any],
                 col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Bee-swarm: per-point scatter with horizontal collision avoidance.

    Implements a deterministic single-pass swarm (sort by value, place each
    point at the smallest legal horizontal offset) so violin density is
    preserved without the smoothing of a kernel.
    """
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    group, value = _resolve_group_value(df, data_profile)
    if not group or not value:
        return _fallback_singleton(ax, df, value, colors, "beeswarm")
    series, labels = _grouped_series(df, group, value)
    if not series:
        return _fallback_singleton(ax, df, value, colors, "beeswarm")
    positions = list(range(1, len(series) + 1))
    # Choose marker size relative to data range (not pixel size, which we
    # cannot resolve before draw — keep it simple and proportional).
    marker_size = 14
    point_radius = 0.08  # in data units
    for x_center, s, color in zip(positions, series, colors):
        sorted_vals = np.sort(s.to_numpy())
        placed: list[tuple[float, float]] = []  # (x, y)
        for v in sorted_vals:
            offset = 0.0
            sign = 1
            for step in range(40):
                candidate = x_center + offset
                # Check collisions
                conflict = any(
                    (candidate - px) ** 2 + ((v - py) * 0.5) ** 2 < point_radius ** 2
                    for px, py in placed[-30:]
                )
                if not conflict:
                    break
                offset = sign * (step + 1) * point_radius
                sign = -sign
            placed.append((candidate, float(v)))
        xs = [p[0] for p in placed]
        ys = [p[1] for p in placed]
        ax.scatter(xs, ys, s=marker_size, color=color, alpha=0.85,
                   linewidths=0.3, edgecolor="white")
    ax.set_xticks(positions, labels, rotation=30, ha="right")
    ax.set_xlabel(group)
    ax.set_ylabel(value)
    _annotate_n(ax, positions, series)
    ax.set_title("Beeswarm", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("histogram")
def gen_histogram(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Single-variable histogram with optional per-group overlay (alpha-blended)."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    group, value = _resolve_group_value(df, data_profile)
    if not value:
        # Pick first numeric column as fallback target
        numeric = [str(c) for c in df.select_dtypes(include=[np.number]).columns]
        if not numeric:
            return _fallback_singleton(ax, df, None, colors, "histogram")
        value = numeric[0]
    if group and group in df.columns:
        series, labels = _grouped_series(df, group, value)
        for s, color, label in zip(series, colors, labels):
            ax.hist(s, bins="auto", color=color, alpha=0.55,
                    edgecolor="white", linewidth=0.4, label=label)
        # Group labels go through xtick legend metadata captured by Figure.render().
    else:
        s = pd.to_numeric(df[value], errors="coerce").dropna()
        ax.hist(s, bins="auto", color=colors[1 % len(colors)], alpha=0.8,
                edgecolor="white", linewidth=0.4)
    ax.set_xlabel(value)
    ax.set_ylabel("Frequency")
    ax.set_title("Histogram", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("density")
def gen_density(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Kernel density estimate (Gaussian KDE) for one or more groups."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    group, value = _resolve_group_value(df, data_profile)
    if not value:
        numeric = [str(c) for c in df.select_dtypes(include=[np.number]).columns]
        if not numeric:
            return _fallback_singleton(ax, df, None, colors, "density")
        value = numeric[0]
    try:
        from scipy.stats import gaussian_kde  # type: ignore[import-untyped]
    except ImportError:
        return gen_histogram(df, data_profile, chart_plan, rc_params, palette,
                             col_map=col_map, ax=ax)
    if group and group in df.columns:
        series, labels = _grouped_series(df, group, value)
    else:
        s = pd.to_numeric(df[value], errors="coerce").dropna()
        series, labels = ([s], [value]) if len(s) else ([], [])
    if not series:
        return _fallback_singleton(ax, df, value, colors, "density")
    lo = min(float(s.min()) for s in series)
    hi = max(float(s.max()) for s in series)
    span = hi - lo if hi > lo else 1.0
    grid = np.linspace(lo - 0.05 * span, hi + 0.05 * span, 256)
    for s, color, label in zip(series, colors, labels):
        if len(s) < 2 or s.std() == 0:
            continue
        kde = gaussian_kde(s.to_numpy())
        density = kde(grid)
        ax.fill_between(grid, density, alpha=0.35, color=color)
        ax.plot(grid, density, color=color, linewidth=1.0, label=str(label))
    ax.set_xlabel(value)
    ax.set_ylabel("Density")
    ax.set_title("Density", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("ridge")
def gen_ridge(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
              rc_params: dict[str, Any], palette: dict[str, Any],
              col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Ridge / joyplot: stacked KDEs offset along the y-axis, one per group."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    group, value = _resolve_group_value(df, data_profile)
    if not group or not value:
        return _fallback_singleton(ax, df, value, colors, "ridge")
    series, labels = _grouped_series(df, group, value)
    if not series:
        return _fallback_singleton(ax, df, value, colors, "ridge")
    try:
        from scipy.stats import gaussian_kde  # type: ignore[import-untyped]
        kde_available = True
    except ImportError:
        kde_available = False
    lo = min(float(s.min()) for s in series)
    hi = max(float(s.max()) for s in series)
    span = hi - lo if hi > lo else 1.0
    grid = np.linspace(lo - 0.05 * span, hi + 0.05 * span, 256)
    densities: list[np.ndarray] = []
    for s in series:
        if kde_available and len(s) > 2 and s.std() > 0:
            densities.append(gaussian_kde(s.to_numpy())(grid))
        else:
            hist, edges = np.histogram(s.to_numpy(), bins=24, range=(grid[0], grid[-1]),
                                       density=True)
            densities.append(np.interp(grid, 0.5 * (edges[:-1] + edges[1:]), hist))
    max_density = max((float(d.max()) for d in densities), default=1.0) or 1.0
    overlap = 0.6  # how much each ridge encroaches on the next
    yticks: list[float] = []
    for idx, (d, label, color) in enumerate(zip(densities, labels, colors)):
        baseline = idx * (1 - overlap)
        scaled = d / max_density
        ax.fill_between(grid, baseline, baseline + scaled, color=color, alpha=0.55,
                        edgecolor=color, linewidth=0.7)
        ax.plot(grid, baseline + scaled, color=color, linewidth=0.9)
        yticks.append(baseline)
    ax.set_yticks(yticks, labels)
    ax.set_xlabel(value)
    ax.set_ylabel(group)
    ax.set_title("Ridge", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
