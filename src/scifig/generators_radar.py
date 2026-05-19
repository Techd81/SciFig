"""Template-backed radar-family generators for the chart registry."""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .registry import register_chart


def _roles(profile: Any) -> dict[str, str]:
    if hasattr(profile, "semantic_roles"):
        return dict(profile.semantic_roles)
    return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))


def _categorical_palette(palette: dict[str, Any]) -> list[str]:
    return list(palette.get(
        "categorical",
        ["#1F4E79", "#4C956C", "#F2A541", "#C8553D", "#7A6C8F", "#2B6F77"],
    ))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _get_polar_ax(ax: Any = None) -> Any:
    if ax is None:
        _, new_ax = plt.subplots(
            figsize=(89 / 25.4, 70 / 25.4),
            subplot_kw={"projection": "polar"},
            constrained_layout=True,
        )
        return new_ax
    if getattr(ax, "name", "") == "polar":
        return ax
    fig = ax.figure
    try:
        spec = ax.get_subplotspec()
    except AttributeError:
        bounds = ax.get_position()
        ax.remove()
        return fig.add_axes(bounds, projection="polar")
    ax.remove()
    return fig.add_subplot(spec, projection="polar")


def _status(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _extract_radar_table(df: pd.DataFrame, data_profile: Any) -> tuple[list[str], list[tuple[str, np.ndarray]]]:
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    category_col = roles.get("category")
    group_col = roles.get("group")

    if category_col in df.columns and len(numeric) >= 3 and roles.get("metric") not in df.columns:
        grouping = group_col if group_col in df.columns else category_col
        grouped = df.groupby(grouping, sort=False)[numeric].mean(numeric_only=True)
        return numeric, [(str(idx), grouped.loc[idx].to_numpy(dtype=float)) for idx in grouped.index]

    label_col = roles.get("metric") or roles.get("feature_id") or roles.get("label") or category_col
    value_col = roles.get("value") or roles.get("score") or roles.get("importance") or roles.get("y")
    if group_col == label_col:
        group_col = None

    if label_col in df.columns and value_col in df.columns:
        if group_col in df.columns:
            pivot = df.pivot_table(
                index=group_col,
                columns=label_col,
                values=value_col,
                aggfunc="mean",
            )
            pivot = pivot.dropna(axis=1, how="all").fillna(0.0)
            labels = [str(c) for c in pivot.columns]
            series = [(str(idx), pivot.loc[idx].to_numpy(dtype=float)) for idx in pivot.index]
            return labels, series
        labels_series = df[label_col].astype(str)
        values = pd.to_numeric(df[value_col], errors="coerce")
        valid = values.notna() & np.isfinite(values)
        return labels_series[valid].tolist(), [("Profile", values[valid].to_numpy(dtype=float))]

    if not numeric:
        return [], []
    labels = numeric
    if group_col in df.columns:
        grouped = df.groupby(group_col, sort=False)[numeric].mean(numeric_only=True)
        return labels, [(str(idx), grouped.loc[idx].to_numpy(dtype=float)) for idx in grouped.index]
    values = df[numeric].mean(numeric_only=True).to_numpy(dtype=float)
    return labels, [("Profile", values)]


def _normalize_series(series: list[tuple[str, np.ndarray]]) -> list[tuple[str, np.ndarray]]:
    matrix = np.vstack([values for _, values in series]).astype(float)
    matrix[~np.isfinite(matrix)] = np.nan
    if matrix.size == 0 or np.isnan(matrix).all():
        return []
    if np.nanmin(matrix) >= 0.0 and np.nanmax(matrix) <= 1.0:
        norm = np.nan_to_num(matrix, nan=0.0)
    elif matrix.shape[0] == 1:
        row = matrix[0]
        lo = float(np.nanmin(row))
        hi = float(np.nanmax(row))
        norm = np.full_like(matrix, 0.5) if hi == lo else (matrix - lo) / (hi - lo)
    else:
        lo = np.nanmin(matrix, axis=0)
        hi = np.nanmax(matrix, axis=0)
        span = np.where(hi == lo, 1.0, hi - lo)
        norm = (matrix - lo) / span
        norm[:, hi == lo] = 0.5
    norm = np.nan_to_num(norm, nan=0.0)
    return [(name, norm[i]) for i, (name, _) in enumerate(series)]


def _draw_radar(
    df: pd.DataFrame,
    data_profile: Any,
    palette: dict[str, Any],
    *,
    title: str,
    ax: Any = None,
) -> Any:
    ax = _get_polar_ax(ax)
    colors = _categorical_palette(palette)
    labels, raw_series = _extract_radar_table(df, data_profile)
    if len(labels) < 3 or not raw_series:
        return _status(ax, title, "Need >=3 metrics for radar")
    series = _normalize_series(raw_series)
    if not series:
        return _status(ax, title, "Need finite radar values")

    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    closed_angles = np.r_[angles, angles[0]]

    ax.set_ylim(0, 1.0)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=6)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=5, color="#555555")
    ax.grid(False)
    ax.spines["polar"].set_visible(False)

    for radius in [0.25, 0.5, 0.75, 1.0]:
        ax.plot(closed_angles, np.full_like(closed_angles, radius), color="#D9D9D9", lw=0.5, zorder=0)
    for angle in angles:
        ax.plot([angle, angle], [0.0, 1.0], color="#E6E6E6", lw=0.45, zorder=0)

    for i, (name, values) in enumerate(series[:6]):
        color = colors[i % len(colors)]
        closed_values = np.r_[values, values[0]]
        ax.plot(closed_angles, closed_values, color=color, lw=1.2, label=name, zorder=3)
        ax.fill(closed_angles, closed_values, color=color, alpha=0.12, zorder=2)
        ax.scatter(angles, values, s=14, color=color, edgecolor="white", linewidth=0.4, zorder=4)

    ax.set_title(title, loc="center", fontweight="bold", pad=8)
    return ax


@register_chart("radar")
def gen_radar(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
              rc_params: dict[str, Any], palette: dict[str, Any],
              col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Radar profile with polygon grid, closed metric hull, and muted fills."""
    plt.rcParams.update(rc_params)
    return _draw_radar(df, data_profile, palette, title="Radar", ax=ax)


@register_chart("biodiversity_radar")
def gen_biodiversity_radar(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                           rc_params: dict[str, Any], palette: dict[str, Any],
                           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Biodiversity radar profile for multi-metric ecological comparisons."""
    plt.rcParams.update(rc_params)
    return _draw_radar(df, data_profile, palette, title="Biodiversity radar", ax=ax)
