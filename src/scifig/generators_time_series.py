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


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    numeric = set(_numeric_columns(df))
    return [str(c) for c in df.columns if str(c) not in numeric]


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


def _first_existing(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {str(c).lower(): str(c) for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _short_label(value: Any, width: int = 18) -> str:
    text = str(value)
    return text if len(text) <= width else text[: width - 1] + "..."


def _unique_columns(*columns: Optional[str]) -> list[str]:
    result: list[str] = []
    for column in columns:
        if column and column not in result:
            result.append(column)
    return result


def _time_pivot(df: pd.DataFrame, data_profile: Any) -> tuple[pd.DataFrame, str | None, str | None]:
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col:
        return pd.DataFrame(), time_col, value_col
    clean = df.copy()
    clean[value_col] = pd.to_numeric(clean[value_col], errors="coerce")
    clean = clean.replace([np.inf, -np.inf], np.nan).dropna(subset=[time_col, value_col])
    if clean.empty:
        return pd.DataFrame(), time_col, value_col
    if group_col:
        pivot = clean.pivot_table(index=time_col, columns=group_col, values=value_col, aggfunc="mean")
    else:
        pivot = clean.groupby(time_col, sort=True)[value_col].mean().to_frame(value_col)
    return pivot.sort_index(), time_col, value_col


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


@register_chart("area")
def gen_area(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
             rc_params: dict[str, Any], palette: dict[str, Any],
             col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Filled area trend with optional group overlays."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col:
        return _fallback_empty(ax, "area")
    if group_col:
        for i, (name, part) in enumerate(df.groupby(group_col, sort=False)):
            x, y = _ordered_xy(part, time_col, value_col)
            if len(y):
                color = colors[i % len(colors)]
                ax.fill_between(x, y, color=color, alpha=0.22, linewidth=0)
                ax.plot(x, y, color=color, lw=1.0, label=str(name))
    else:
        x, y = _ordered_xy(df, time_col, value_col)
        if len(y):
            ax.fill_between(x, y, color=colors[1 % len(colors)], alpha=0.28, linewidth=0)
            ax.plot(x, y, color=colors[1 % len(colors)], lw=1.0)
    ax.set_xlabel(time_col)
    ax.set_ylabel(value_col)
    ax.set_title("Area", loc="center", fontweight="bold", pad=5)
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
    roles = _roles(data_profile)
    columns = set(str(col) for col in df.columns)
    ci_low_col = roles.get("ci_low") or roles.get("low")
    ci_high_col = roles.get("ci_high") or roles.get("high")
    if ci_low_col not in columns or ci_high_col not in columns:
        ci_low_col = None
        ci_high_col = None

    groups: list[tuple[str, pd.DataFrame]]
    if group_col:
        groups = [(str(name), part) for name, part in df.groupby(group_col, sort=False)]
    else:
        groups = [(value_col, df)]

    for i, (label, part) in enumerate(groups):
        keep = [time_col, value_col] + ([ci_low_col, ci_high_col] if ci_low_col and ci_high_col else [])
        clean = part[keep].copy()
        for col in [value_col, ci_low_col, ci_high_col]:
            if col:
                clean[col] = pd.to_numeric(clean[col], errors="coerce")
        clean = clean.replace([np.inf, -np.inf], np.nan).dropna(subset=keep)
        if clean.empty:
            continue
        if ci_low_col and ci_high_col:
            stats = clean.groupby(time_col, sort=True).agg(
                mean=(value_col, "mean"),
                lower=(ci_low_col, "mean"),
                upper=(ci_high_col, "mean"),
            ).reset_index()
        else:
            stats = clean.groupby(time_col, sort=True)[value_col].agg(["mean", "sem", "count"]).reset_index()
            ci = 1.96 * stats["sem"].fillna(0.0)
            stats["lower"] = stats["mean"] - ci
            stats["upper"] = stats["mean"] + ci
        x = stats[time_col].to_numpy()
        mean = stats["mean"].to_numpy(dtype=float)
        lower = stats["lower"].to_numpy(dtype=float)
        upper = stats["upper"].to_numpy(dtype=float)
        color = colors[i % len(colors)]
        ax.fill_between(x, lower, upper, color=color, alpha=0.22, linewidth=0)
        ax.plot(x, mean, color=color, linestyle="-", marker="o", markersize=2.4,
                linewidth=1.15, label="_nolegend_")
        if len(x):
            ax.text(x[-1], mean[-1], f"  {label}", color=color, fontsize=6,
                    va="center", ha="left", clip_on=True)

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


@register_chart("stacked_area_comp")
def gen_stacked_area_comp(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                          rc_params: dict[str, Any], palette: dict[str, Any],
                          col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Composition-style stacked area chart."""
    return gen_area_stacked(df, data_profile, chart_plan, rc_params, palette, col_map=col_map, ax=ax)


@register_chart("streamgraph")
def gen_streamgraph(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Centered stacked area streamgraph."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    pivot, time_col, value_col = _time_pivot(df, data_profile)
    if pivot.empty or time_col is None or value_col is None:
        return _fallback_empty(ax, "streamgraph")
    values = pivot.fillna(0.0).to_numpy(dtype=float)
    min_value = float(np.nanmin(values)) if values.size else 0.0
    if min_value < 0:
        values = values - min_value
    totals = values.sum(axis=1, keepdims=True)
    baseline = -0.5 * totals
    layers = []
    current = baseline[:, 0].copy()
    for j in range(values.shape[1]):
        layers.append((current.copy(), current + values[:, j]))
        current = current + values[:, j]
    x = pivot.index.to_numpy()
    for j, (lo, hi) in enumerate(layers):
        ax.fill_between(x, lo, hi, color=colors[j % len(colors)], alpha=0.78, linewidth=0)
    ax.axhline(0, color="#888888", lw=0.5, ls=":")
    ax.set_xlabel(time_col)
    ax.set_ylabel(value_col)
    ax.set_title("Streamgraph", loc="center", fontweight="bold", pad=5)
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


@register_chart("sparkline")
def gen_sparkline(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Compact trend line with all nonessential axes suppressed."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col:
        return _fallback_empty(ax, "sparkline")
    if group_col:
        for i, (_, part) in enumerate(df.groupby(group_col, sort=False)):
            x, y = _ordered_xy(part, time_col, value_col)
            if len(y):
                ax.plot(x, y, color=colors[i % len(colors)], lw=0.9)
    else:
        x, y = _ordered_xy(df, time_col, value_col)
        if len(y):
            ax.plot(x, y, color=colors[1 % len(colors)], lw=0.9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Sparkline", loc="center", fontweight="bold", pad=3)
    return ax


@register_chart("gantt")
def gen_gantt(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
              rc_params: dict[str, Any], palette: dict[str, Any],
              col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Gantt timeline with horizontal task bars."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    start_col = roles.get("start") or _first_existing(df, ("start", "begin"))
    end_col = roles.get("end") or _first_existing(df, ("end", "stop", "finish"))
    label_col = roles.get("label") or roles.get("group") or roles.get("identifier")
    if start_col not in df.columns or end_col not in df.columns:
        return _fallback_empty(ax, "gantt")
    labels = df[label_col].astype(str).tolist() if label_col in df.columns else [str(i + 1) for i in range(len(df))]
    frame = pd.DataFrame({
        "label": labels,
        "start": pd.to_numeric(df[start_col], errors="coerce"),
        "end": pd.to_numeric(df[end_col], errors="coerce"),
    }).replace([np.inf, -np.inf], np.nan).dropna()
    frame = frame[frame["end"] >= frame["start"]]
    if frame.empty:
        return _fallback_empty(ax, "gantt")
    y_pos = np.arange(len(frame))
    duration = frame["end"] - frame["start"]
    ax.barh(y_pos, duration, left=frame["start"], color=[colors[i % len(colors)] for i in y_pos], height=0.62)
    ax.set_yticks(y_pos, frame["label"].astype(str).tolist())
    ax.set_xlabel("Time")
    ax.set_title("Gantt", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


@register_chart("timeline_annotation")
def gen_timeline_annotation(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                            rc_params: dict[str, Any], palette: dict[str, Any],
                            col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Annotated event timeline with staggered labels and vertical markers."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)
    time_col = roles.get("time") or roles.get("start") or roles.get("x") or (numeric[0] if numeric else None)
    label_col = roles.get("label") or roles.get("identifier") or (categorical[0] if categorical else None)
    group_col = roles.get("group") if roles.get("group") in df.columns else None
    value_col = roles.get("value") if roles.get("value") in df.columns else None
    if time_col not in df.columns or label_col not in df.columns:
        return _fallback_empty(ax, "timeline_annotation")
    if value_col == time_col:
        value_col = None
    if group_col == label_col:
        group_col = None
    keep = _unique_columns(time_col, label_col, group_col, value_col)
    frame = df[keep].copy()
    frame[time_col] = pd.to_numeric(frame[time_col], errors="coerce")
    if value_col:
        frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[time_col, label_col])
    if frame.empty:
        return _fallback_empty(ax, "timeline_annotation")
    frame = frame.sort_values(time_col).head(18)
    if value_col:
        raw_y = frame[value_col].fillna(0).to_numpy(dtype=float)
        span = float(raw_y.max() - raw_y.min()) or 1.0
        y = 0.18 + 0.64 * (raw_y - float(raw_y.min())) / span
    else:
        y = 0.5 + 0.22 * np.where(np.arange(len(frame)) % 2 == 0, 1.0, -1.0)
    if group_col:
        groups = list(dict.fromkeys(frame[group_col].astype(str).tolist()))
        color_map = {name: colors[i % len(colors)] for i, name in enumerate(groups)}
    else:
        color_map = {}
    ax.axhline(0.5, color="#B0B0B0", lw=0.7)
    for i, (_, row) in enumerate(frame.iterrows()):
        color = color_map.get(str(row[group_col]), colors[i % len(colors)]) if group_col else colors[i % len(colors)]
        x = float(row[time_col])
        yi = float(y[i])
        ax.vlines(x, 0.5, yi, color=color, lw=0.75, alpha=0.82)
        ax.scatter([x], [yi], s=24, color=color, edgecolor="white", linewidth=0.35, zorder=3)
        va = "bottom" if yi >= 0.5 else "top"
        offset = 0.035 if yi >= 0.5 else -0.035
        ax.text(x, yi + offset, _short_label(row[label_col], 14),
                ha="center", va=va, fontsize=5.5, rotation=30)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Time")
    ax.set_title("Timeline annotation", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    return ax


@register_chart("bump_chart")
def gen_bump_chart(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                   rc_params: dict[str, Any], palette: dict[str, Any],
                   col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Rank-over-time bump chart."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col or not group_col:
        return _fallback_empty(ax, "bump_chart")
    clean = df[[time_col, value_col, group_col]].copy()
    clean[value_col] = pd.to_numeric(clean[value_col], errors="coerce")
    clean = clean.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return _fallback_empty(ax, "bump_chart")
    clean["_rank"] = clean.groupby(time_col)[value_col].rank(ascending=False, method="dense")
    for i, (name, part) in enumerate(clean.groupby(group_col, sort=False)):
        ordered = part.sort_values(time_col)
        ax.plot(ordered[time_col], ordered["_rank"], color=colors[i % len(colors)],
                marker="o", ms=3, lw=1.0, label=str(name))
    ax.invert_yaxis()
    ax.set_xlabel(time_col)
    ax.set_ylabel("Rank")
    ax.set_title("Bump chart", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("slope_chart")
def gen_slope_chart(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Two-endpoint slope chart, one line per group."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    time_col, value_col, group_col, _ = _resolve_time_value_group(df, data_profile)
    if not time_col or not value_col or not group_col:
        return _fallback_empty(ax, "slope_chart")
    clean = df[[time_col, value_col, group_col]].copy()
    clean[value_col] = pd.to_numeric(clean[value_col], errors="coerce")
    clean = clean.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return _fallback_empty(ax, "slope_chart")
    endpoints = sorted(clean[time_col].drop_duplicates().tolist())
    if len(endpoints) < 2:
        return _fallback_empty(ax, "slope_chart")
    first, last = endpoints[0], endpoints[-1]
    for i, (name, part) in enumerate(clean.groupby(group_col, sort=False)):
        vals = part.groupby(time_col)[value_col].mean()
        if first in vals.index and last in vals.index:
            ax.plot([0, 1], [vals.loc[first], vals.loc[last]], color=colors[i % len(colors)],
                    marker="o", ms=3, lw=1.0)
            ax.text(-0.03, vals.loc[first], str(name), ha="right", va="center", fontsize=6, color="#444444")
            ax.text(1.03, vals.loc[last], str(name), ha="left", va="center", fontsize=6, color="#444444")
    ax.set_xticks([0, 1], [str(first), str(last)])
    ax.set_ylabel(value_col)
    ax.set_title("Slope chart", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
