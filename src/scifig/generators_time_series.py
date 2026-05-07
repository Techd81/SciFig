"""Differentiated time-series generators for the chart registry.

Each chart key owns a distinct visual grammar and replaces the shared
``charts._draw_line`` fallback for Tier 1 time-series coverage.
"""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .registry import register_chart


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
    return list(palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2"]))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _resolve_time_value_group(
    df: pd.DataFrame,
    profile: Any,
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    roles = _roles(profile)
    time_col = roles.get("time") or roles.get("x")
    value_col = roles.get("value") or roles.get("y")
    group_col = roles.get("group")
    identifier_col = roles.get("identifier")
    columns = set(str(c) for c in df.columns)
    if time_col not in columns:
        numeric = _numeric_columns(df)
        time_col = numeric[0] if numeric else None
    if value_col not in columns:
        numeric = [col for col in _numeric_columns(df) if col != time_col]
        value_col = numeric[-1] if numeric else None
    if group_col not in columns:
        group_col = None
    if identifier_col not in columns:
        identifier_col = None
    return time_col, value_col, group_col, identifier_col


def _ordered_xy(part: pd.DataFrame, time_col: str, value_col: str) -> tuple[pd.Series, pd.Series]:
    ordered = part.sort_values(time_col)
    x = ordered[time_col]
    y = pd.to_numeric(ordered[value_col], errors="coerce")
    valid = y.notna() & ordered[time_col].notna()
    return x[valid], y[valid]


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.6, pad=2)


def _fallback_empty(ax: Any, chart: str) -> Any:
    ax.text(0.5, 0.5, "No plottable time-series columns", ha="center", va="center", transform=ax.transAxes)
    ax.set_title(chart.replace("_", " ").title(), loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("line")
def gen_line(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
             rc_params: dict[str, Any], palette: dict[str, Any],
             col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Basic solid time-series line with point markers."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col:
        return _fallback_empty(ax, "line")

    if group_col:
        for i, (name, part) in enumerate(df.groupby(group_col, sort=False)):
            x, y = _ordered_xy(part, time_col, value_col)
            if len(y):
                ax.plot(x, y, color=colors[i % len(colors)], linestyle="-", marker="o",
                        markersize=2.8, linewidth=0.95, label=str(name))
    else:
        x, y = _ordered_xy(df, time_col, value_col)
        if len(y):
            ax.plot(x, y, color=colors[1 % len(colors)], linestyle="-", marker="o",
                    markersize=2.8, linewidth=0.95)

    ax.set_xlabel(time_col)
    ax.set_ylabel(value_col)
    ax.set_title("Line", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("line_ci")
def gen_line_ci(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Mean line with a 95% confidence interval ribbon."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col:
        return _fallback_empty(ax, "line_ci")

    groups: list[tuple[str, pd.DataFrame]]
    if group_col:
        groups = [(str(name), part) for name, part in df.groupby(group_col, sort=False)]
    else:
        groups = [(value_col, df)]

    for i, (label, part) in enumerate(groups):
        clean = part[[time_col, value_col]].copy()
        clean[value_col] = pd.to_numeric(clean[value_col], errors="coerce")
        clean = clean.dropna(subset=[time_col, value_col])
        if clean.empty:
            continue
        stats = clean.groupby(time_col, sort=True)[value_col].agg(["mean", "sem", "count"]).reset_index()
        ci = 1.96 * stats["sem"].fillna(0.0)
        x = stats[time_col].to_numpy()
        mean = stats["mean"].to_numpy(dtype=float)
        lower = mean - ci.to_numpy(dtype=float)
        upper = mean + ci.to_numpy(dtype=float)
        color = colors[i % len(colors)]
        ax.fill_between(x, lower, upper, color=color, alpha=0.22, linewidth=0)
        ax.plot(x, mean, color=color, linestyle="-", marker="o", markersize=2.4,
                linewidth=1.15, label=label)

    ax.set_xlabel(time_col)
    ax.set_ylabel(f"Mean {value_col}")
    ax.set_title("Line + 95% CI", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("area_stacked")
def gen_area_stacked(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Stacked area chart with one layer per group."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col:
        return _fallback_empty(ax, "area_stacked")

    clean = df.copy()
    clean[value_col] = pd.to_numeric(clean[value_col], errors="coerce")
    clean = clean.dropna(subset=[time_col, value_col])
    if clean.empty:
        return _fallback_empty(ax, "area_stacked")

    if group_col:
        pivot = clean.pivot_table(index=time_col, columns=group_col, values=value_col, aggfunc="mean")
    else:
        pivot = clean.groupby(time_col, sort=True)[value_col].mean().to_frame(value_col)
    pivot = pivot.sort_index().fillna(0.0)
    values = pivot.to_numpy(dtype=float)
    min_value = float(np.nanmin(values)) if values.size else 0.0
    if min_value < 0:
        values = values - min_value
    labels = [str(label) for label in pivot.columns]
    layer_colors = [colors[i % len(colors)] for i in range(len(labels))]
    ax.stackplot(pivot.index.to_numpy(), values.T, colors=layer_colors, alpha=0.76, labels=labels)

    ax.set_xlabel(time_col)
    ax.set_ylabel(value_col)
    ax.set_title("Stacked area", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("spaghetti")
def gen_spaghetti(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Individual trajectories as grey threads plus a bold mean trajectory."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, identifier_col = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col:
        return _fallback_empty(ax, "spaghetti")

    trajectory_col = identifier_col or group_col
    if trajectory_col:
        for _, part in df.groupby(trajectory_col, sort=False):
            x, y = _ordered_xy(part, time_col, value_col)
            if len(y):
                ax.plot(x, y, color="#8A8A8A", linestyle="-", marker=None,
                        linewidth=0.55, alpha=0.35)
    else:
        x, y = _ordered_xy(df, time_col, value_col)
        if len(y):
            ax.plot(x, y, color="#8A8A8A", linestyle="-", marker=None,
                    linewidth=0.55, alpha=0.35)

    clean = df[[time_col, value_col]].copy()
    clean[value_col] = pd.to_numeric(clean[value_col], errors="coerce")
    clean = clean.dropna(subset=[time_col, value_col])
    if not clean.empty:
        mean = clean.groupby(time_col, sort=True)[value_col].mean().reset_index()
        ax.plot(mean[time_col], mean[value_col], color=colors[1 % len(colors)], linestyle="-",
                marker="o", markersize=2.8, linewidth=1.75, label="Mean")

    ax.set_xlabel(time_col)
    ax.set_ylabel(value_col)
    ax.set_title("Spaghetti", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
