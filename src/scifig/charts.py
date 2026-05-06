"""Chart generation dispatch."""

from __future__ import annotations

import math
from typing import Any, Optional, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .registry import CHART_GENERATORS, CHART_KEYS, register_chart, resolve_chart_key


def _roles(profile: Any) -> dict[str, str]:
    if hasattr(profile, "as_skill_dict"):
        return cast(dict[str, str], profile.semantic_roles)
    return cast(dict[str, str], dict(profile.get("semanticRoles", profile.get("semantic_roles", {}))))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    nums = set(_numeric_columns(df))
    return [str(c) for c in df.columns if str(c) not in nums]


def _get_ax(ax: Any = None) -> Any:
    if ax is not None:
        return ax
    _, new_ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4), constrained_layout=True)
    return new_ax


def generate(chart: str, df: pd.DataFrame, data_profile: Any, chart_plan: Any,
             rc_params: dict[str, Any], palette: dict[str, Any], col_map: Optional[dict[str, str]] = None,
             ax: Any = None) -> Any:
    key = resolve_chart_key(chart)
    if key in CHART_GENERATORS:
        return CHART_GENERATORS[key](df, data_profile, chart_plan, rc_params, palette, col_map=col_map, ax=ax)
    return generic_chart(key, df, data_profile, chart_plan, rc_params, palette, col_map=col_map, ax=ax)


def generic_chart(chart: str, df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any], col_map: Optional[dict[str, str]] = None,
                  ax: Any = None) -> Any:
    plt.rcParams.update(rc_params)
    axis = _get_ax(ax)
    roles = _roles(data_profile)
    colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])
    nums = _numeric_columns(df)
    cats = _categorical_columns(df)
    group = roles.get("group")
    value = roles.get("value") or roles.get("y")
    x_col = roles.get("x")
    y_col = roles.get("y")

    if chart in ("volcano", "ma_plot") and {"fold_change", "p_value"} <= set(roles):
        _draw_volcano(axis, df, roles, colors)
    elif "heatmap" in chart or "matrix" in chart or chart in ("correlation", "confusion_matrix"):
        _draw_heatmap(axis, df, colors)
    elif chart in ("box_strip", "violin_strip", "violin_grouped", "raincloud", "beeswarm", "dot_strip") and group and value:
        _draw_grouped_distribution(axis, df, group, value, chart, colors)
    elif chart in ("line", "line_ci", "spaghetti", "sparkline", "area", "area_stacked", "streamgraph") and (x_col or roles.get("time")) and value:
        line_x = x_col or roles.get("time")
        assert line_x is not None
        _draw_line(axis, df, line_x, value, group, colors)
    elif chart in ("roc", "pr_curve", "calibration") and {"score", "actual"} <= set(roles):
        _draw_binary_curve(axis, df, roles, chart, colors)
    elif x_col and y_col and x_col in df.columns and y_col in df.columns:
        _draw_scatter(axis, df, x_col, y_col, group, colors)
    elif value and value in df.columns:
        _draw_histogram(axis, df, value, colors)
    elif nums:
        _draw_histogram(axis, df, nums[0], colors)
    elif cats:
        counts = df[cats[0]].astype(str).value_counts().head(20)
        axis.bar(counts.index, counts.values, color=colors[0])
        axis.set_xlabel(cats[0])
        axis.set_ylabel("Count")
    else:
        axis.text(0.5, 0.5, "No plottable columns", ha="center", va="center", transform=axis.transAxes)

    axis.set_title(chart.replace("_", " ").title(), loc="center", fontweight="bold", pad=5)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(direction="out", length=3, width=0.6, pad=2)
    return axis


def _draw_volcano(ax: Any, df: pd.DataFrame, roles: dict[str, str], colors: list[str]) -> None:
    fc = roles["fold_change"]
    p = roles["p_value"]
    x = pd.to_numeric(df[fc], errors="coerce")
    y = -np.log10(pd.to_numeric(df[p], errors="coerce").clip(lower=1e-300))
    sig = (y > -math.log10(0.05)) & (x.abs() >= 1)
    ax.scatter(x[~sig], y[~sig], s=12, color="#999999", alpha=0.55, linewidths=0)
    ax.scatter(x[sig & (x > 0)], y[sig & (x > 0)], s=14, color=colors[6 % len(colors)], alpha=0.8, linewidths=0)
    ax.scatter(x[sig & (x < 0)], y[sig & (x < 0)], s=14, color=colors[5 % len(colors)], alpha=0.8, linewidths=0)
    ax.axvline(1, color="#555555", lw=0.6, ls="--")
    ax.axvline(-1, color="#555555", lw=0.6, ls="--")
    ax.axhline(-math.log10(0.05), color="#555555", lw=0.6, ls=":")
    ax.set_xlabel("log2 fold-change")
    ax.set_ylabel("-log10(p)")


def _draw_heatmap(ax: Any, df: pd.DataFrame, colors: list[str]) -> None:
    matrix = df.select_dtypes(include=[np.number])
    if matrix.empty:
        matrix = pd.DataFrame(pd.factorize(df.astype(str).agg("|".join, axis=1))[0])
    image = ax.imshow(matrix.to_numpy(), aspect="auto", cmap="viridis")
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xlabel("Features")
    ax.set_ylabel("Observations")


def _draw_grouped_distribution(ax: Any, df: pd.DataFrame, group: str, value: str, chart: str, colors: list[str]) -> None:
    values = [pd.to_numeric(part[value], errors="coerce").dropna() for _, part in df.groupby(group, sort=False)]
    labels = [str(name) for name, _ in df.groupby(group, sort=False)]
    if "violin" in chart or chart == "raincloud":
        body = ax.violinplot(values, showmedians=True)
        for i, pc in enumerate(body["bodies"]):
            pc.set_facecolor(colors[i % len(colors)])
            pc.set_alpha(0.35)
    else:
        try:
            ax.boxplot(values, tick_labels=labels, patch_artist=True)
        except TypeError:
            ax.boxplot(values, labels=labels, patch_artist=True)
    for i, series in enumerate(values, start=1):
        jitter = np.linspace(-0.12, 0.12, max(len(series), 1))
        ax.scatter(np.full(len(series), i) + jitter[:len(series)], series, s=9, color=colors[(i - 1) % len(colors)], alpha=0.65, linewidths=0)
    ax.set_xticks(range(1, len(labels) + 1), labels, rotation=30, ha="right")
    ax.set_xlabel(group)
    ax.set_ylabel(value)


def _draw_line(ax: Any, df: pd.DataFrame, x_col: str, value: str, group: Optional[str], colors: list[str]) -> None:
    if group and group in df.columns:
        for i, (name, part) in enumerate(df.groupby(group, sort=False)):
            ordered = part.sort_values(x_col)
            ax.plot(ordered[x_col], ordered[value], marker="o", ms=2.5, lw=0.9, color=colors[i % len(colors)], label=str(name))
        # NOTE: do not call ax.legend(); Figure.render() collects handles into a single bottom-center fig.legend.
        # In single-panel use, callers can attach handles via ax.get_legend_handles_labels().
    else:
        ordered = df.sort_values(x_col)
        ax.plot(ordered[x_col], ordered[value], marker="o", ms=2.5, lw=0.9, color=colors[1 % len(colors)])
    ax.set_xlabel(x_col)
    ax.set_ylabel(value)


def _draw_binary_curve(ax: Any, df: pd.DataFrame, roles: dict[str, str], chart: str, colors: list[str]) -> None:
    score = pd.to_numeric(df[roles["score"]], errors="coerce").fillna(0)
    actual = pd.to_numeric(df[roles["actual"]], errors="coerce").fillna(0)
    thresholds = np.linspace(0, 1, 50)
    xs: list[float] = []
    ys: list[float] = []
    for threshold in thresholds:
        pred = score >= threshold
        tp = float(((pred == 1) & (actual == 1)).sum())
        fp = float(((pred == 1) & (actual == 0)).sum())
        fn = float(((pred == 0) & (actual == 1)).sum())
        tn = float(((pred == 0) & (actual == 0)).sum())
        if chart == "pr_curve":
            xs.append(tp / max(tp + fn, 1.0))
            ys.append(tp / max(tp + fp, 1.0))
        else:
            xs.append(fp / max(fp + tn, 1.0))
            ys.append(tp / max(tp + fn, 1.0))
    ax.plot(xs, ys, color=colors[1 % len(colors)], lw=1.0)
    ax.set_xlabel("Recall" if chart == "pr_curve" else "False positive rate")
    ax.set_ylabel("Precision" if chart == "pr_curve" else "True positive rate")


def _draw_scatter(ax: Any, df: pd.DataFrame, x_col: str, y_col: str, group: Optional[str], colors: list[str]) -> None:
    if group and group in df.columns:
        for i, (name, part) in enumerate(df.groupby(group, sort=False)):
            ax.scatter(part[x_col], part[y_col], s=15, color=colors[i % len(colors)], alpha=0.75, linewidths=0, label=str(name))
        # NOTE: do not call ax.legend(); Figure.render() collects handles into a single bottom-center fig.legend.
    else:
        ax.scatter(df[x_col], df[y_col], s=15, color=colors[1 % len(colors)], alpha=0.75, linewidths=0)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)


def _draw_histogram(ax: Any, df: pd.DataFrame, value: str, colors: list[str]) -> None:
    series = pd.to_numeric(df[value], errors="coerce").dropna()
    ax.hist(series, bins="auto", color=colors[1 % len(colors)], alpha=0.75, edgecolor="white", linewidth=0.4)
    ax.set_xlabel(value)
    ax.set_ylabel("Frequency")


for _chart_key in list(CHART_KEYS):
    if _chart_key not in CHART_GENERATORS:
        register_chart(_chart_key)(
            lambda df, data_profile, chart_plan, rc_params, palette, col_map=None, ax=None, _key=_chart_key:
                generic_chart(_key, df, data_profile, chart_plan, rc_params, palette, col_map=col_map, ax=ax)
        )
