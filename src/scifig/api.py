"""Fluent public plotting API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

import matplotlib.pyplot as plt

from .charts import generate
from .export import export_figure
from .ingest import profile_data
from .palettes import resolve_palette
from .registry import resolve_chart_key
from .stats import add_group_stat_annotation
from .styles import apply_style
from .types import ChartPlan, DataInput


def plot(data: DataInput, chart: str = "auto", style: str = "nature", palette: Any = "colorblind",
         output: Optional[Union[str, Path]] = None, stats: str = "strict", dpi: int = 300, **kwargs: Any) -> Any:
    df, data_profile = profile_data(data)
    profile = apply_style(style)
    palette_map = resolve_palette(palette)
    chart_key = choose_chart(data_profile, chart)
    chart_plan = ChartPlan(primary_chart=chart_key, stat_method=stats)
    fig, ax = plt.subplots(
        figsize=(profile["single_width_mm"] / 25.4, min(70.0, profile["max_height_mm"]) / 25.4),
        constrained_layout=True,
    )
    generate(chart_key, df, data_profile, chart_plan, dict(plt.rcParams), palette_map, ax=ax)
    warnings = add_group_stat_annotation(
        ax,
        df,
        data_profile.semantic_roles.get("group"),
        data_profile.semantic_roles.get("value") or data_profile.semantic_roles.get("y"),
        stats,
    )
    if warnings:
        ax.text(0.01, 0.01, "; ".join(warnings), transform=ax.transAxes, fontsize=5, color="#555555")
    if output is not None:
        return export_figure(fig, output, chart=chart_key, style=style, dpi=dpi)
    return fig


def choose_chart(data_profile: Any, chart: str) -> str:
    if chart != "auto":
        return resolve_chart_key(chart)
    roles = data_profile.semantic_roles
    if {"fold_change", "p_value"} <= set(roles):
        return "volcano"
    if data_profile.structure == "matrix":
        return "heatmap_pure"
    if "time" in roles and ("value" in roles or "y" in roles):
        return "line"
    if "group" in roles and ("value" in roles or "y" in roles):
        return "box_strip"
    if "x" in roles and "y" in roles:
        return "scatter_regression"
    return "histogram"
