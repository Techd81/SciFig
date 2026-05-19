"""Composition and hierarchy chart generators.

These generators replace the generic fallback for chart types whose visual
grammar depends on category proportions, nested hierarchy, or part-whole
structure.
"""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
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
    if isinstance(profile, dict):
        return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))
    return {}


def _categorical_palette(palette: dict[str, Any]) -> list[str]:
    return list(palette.get(
        "categorical",
        ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"],
    ))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    numeric = set(_numeric_columns(df))
    return [str(c) for c in df.columns if str(c) not in numeric]


def _first_valid(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    columns = {str(c) for c in df.columns}
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _first_numeric_valid(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    numeric = set(_numeric_columns(df))
    for candidate in candidates:
        if candidate in numeric:
            return candidate
    return None


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.6, pad=2)


def _fallback_empty(ax: Any, chart: str, message: str = "Need category + value columns") -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(chart.replace("_", " ").title(), loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


def _resolve_composition_columns(
    df: pd.DataFrame,
    profile: Any,
) -> tuple[str | None, str | None, str | None]:
    roles = _roles(profile)
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)

    value_col = _first_numeric_valid(
        df,
        roles.get("weight"),
        roles.get("frequency"),
        roles.get("proportion"),
        roles.get("value"),
        roles.get("y"),
        numeric[-1] if numeric else None,
    )
    group_col = _first_valid(df, roles.get("group"))
    category_col = _first_valid(
        df,
        roles.get("category"),
        roles.get("label"),
        roles.get("feature_id"),
        roles.get("identifier"),
        roles.get("parent"),
    )

    if category_col is None:
        category_col = next((col for col in categorical if col != group_col), None)
    if group_col is None:
        group_col = next((col for col in categorical if col != category_col), None)
    if category_col is None and group_col is not None:
        category_col, group_col = group_col, None
    if group_col == category_col:
        group_col = None
    return category_col, group_col, value_col


def _composition_frame(
    df: pd.DataFrame,
    profile: Any,
) -> tuple[pd.DataFrame, str | None, str | None, str | None, str | None]:
    category_col, group_col, value_col = _resolve_composition_columns(df, profile)
    if value_col is None:
        return pd.DataFrame(), category_col, group_col, value_col, "Need numeric value column"

    working = df.copy()
    if category_col is None:
        category_col = "__item__"
        working[category_col] = [str(i + 1) for i in range(len(working))]
    keep = [category_col, value_col] + ([group_col] if group_col else [])
    frame = working[keep].copy()
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[category_col, value_col])
    if group_col:
        frame = frame.dropna(subset=[group_col])
    if frame.empty:
        return pd.DataFrame(), category_col, group_col, value_col, "Need finite composition values"
    frame[value_col] = frame[value_col].clip(lower=0)
    frame = frame[frame[value_col] > 0]
    if frame.empty:
        return pd.DataFrame(), category_col, group_col, value_col, "Need positive composition values"
    return frame, category_col, group_col, value_col, None


def _top_totals(frame: pd.DataFrame, category: str, value: str, limit: int = 10) -> pd.Series:
    totals = frame.groupby(category, sort=False)[value].sum()
    totals = totals[totals > 0].sort_values(ascending=False)
    if len(totals) <= limit:
        return totals
    head = totals.iloc[: limit - 1].copy()
    head.loc["Other"] = totals.iloc[limit - 1:].sum()
    return head


def _pivot_composition(
    frame: pd.DataFrame,
    category: str,
    group: str | None,
    value: str,
    limit: int = 8,
) -> pd.DataFrame:
    if group:
        pivot = frame.pivot_table(index=category, columns=group, values=value, aggfunc="sum", fill_value=0.0)
    else:
        pivot = frame.groupby(category, sort=False)[value].sum().to_frame(value)
    order = pivot.sum(axis=1).sort_values(ascending=False).index[:limit]
    return pivot.loc[order].fillna(0.0)


def _short_label(value: Any, width: int = 15) -> str:
    text = str(value)
    return text if len(text) <= width else text[: width - 1] + "..."


def _render_grouped_bar(ax: Any, pivot: pd.DataFrame, colors: list[str], title: str) -> Any:
    if pivot.empty:
        return _fallback_empty(ax, title, "Need grouped composition values")
    x = np.arange(len(pivot.index))
    n_groups = max(len(pivot.columns), 1)
    width = min(0.72 / n_groups, 0.28)
    offsets = (np.arange(n_groups) - (n_groups - 1) / 2) * width
    for i, col in enumerate(pivot.columns):
        ax.bar(x + offsets[i], pivot[col].to_numpy(dtype=float), width=width,
               color=colors[i % len(colors)], edgecolor="white", linewidth=0.35, label=str(col))
    ax.set_xticks(x, [_short_label(idx) for idx in pivot.index], rotation=30, ha="right")
    ax.set_xlabel("Category")
    ax.set_ylabel("Value")
    ax.set_title(title.replace("_", " ").title(), loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("grouped_bar")
def gen_grouped_bar(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Side-by-side bars for category-by-group comparisons."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "grouped_bar", error or "Need category + value columns")
    pivot = _pivot_composition(frame, category, group, value)
    return _render_grouped_bar(ax, pivot, _categorical_palette(palette), "Grouped bar")


@register_chart("clustered_bar")
def gen_clustered_bar(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Clustered bar variant using the same grouped category grammar."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "clustered_bar", error or "Need category + value columns")
    pivot = _pivot_composition(frame, category, group, value)
    return _render_grouped_bar(ax, pivot, _categorical_palette(palette), "Clustered bar")


@register_chart("stacked_bar_comp")
def gen_stacked_bar_comp(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Stacked part-whole bars with one layer per group."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "stacked_bar_comp", error or "Need category + value columns")
    pivot = _pivot_composition(frame, category, group, value)
    colors = _categorical_palette(palette)
    x = np.arange(len(pivot.index))
    bottom = np.zeros(len(pivot.index), dtype=float)
    for i, col in enumerate(pivot.columns):
        values = pivot[col].to_numpy(dtype=float)
        ax.bar(x, values, bottom=bottom, color=colors[i % len(colors)],
               edgecolor="white", linewidth=0.35, label=str(col))
        bottom += values
    ax.set_xticks(x, [_short_label(idx) for idx in pivot.index], rotation=30, ha="right")
    ax.set_xlabel("Category")
    ax.set_ylabel("Value")
    ax.set_title("Stacked composition", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("waffle_chart")
def gen_waffle_chart(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """10x10 waffle grid showing normalized category share."""
    ax = _get_ax(ax)
    frame, category, _, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "waffle_chart", error or "Need category + value columns")
    totals = _top_totals(frame, category, value, limit=7)
    if totals.empty:
        return _fallback_empty(ax, "waffle_chart", "Need positive composition values")
    colors = _categorical_palette(palette)
    raw = totals / totals.sum() * 100
    counts = np.floor(raw).astype(int)
    remainder = int(100 - counts.sum())
    if remainder:
        for idx in np.argsort(-(raw - counts).to_numpy())[:remainder]:
            counts.iloc[idx] += 1
    labels_by_square: list[int] = []
    for idx, count in enumerate(counts):
        labels_by_square.extend([idx] * int(count))
    labels_by_square = (labels_by_square + [len(totals) - 1] * 100)[:100]
    for i, label_idx in enumerate(labels_by_square):
        x = i % 10
        y = 9 - i // 10
        ax.add_patch(Rectangle((x, y), 0.88, 0.88, facecolor=colors[label_idx % len(colors)],
                               edgecolor="white", linewidth=0.25))
    for i, (label, total) in enumerate(totals.items()):
        pct = total / totals.sum() * 100
        ax.text(10.4, 9.4 - i * 0.8, f"{_short_label(label, 12)} {pct:.0f}%",
                ha="left", va="center", fontsize=6, color=colors[i % len(colors)])
    ax.set_xlim(0, 14.8)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Waffle chart", loc="center", fontweight="bold", pad=5)
    return ax


def _slice_rectangles(values: pd.Series) -> list[tuple[Any, float, float, float, float, float]]:
    rects: list[tuple[Any, float, float, float, float, float]] = []
    x0 = 0.0
    y0 = 0.0
    width = 1.0
    height = 1.0
    total = float(values.sum())
    if total <= 0:
        return rects
    remaining = total
    horizontal = width >= height
    for label, raw_value in values.items():
        value = float(raw_value)
        if value <= 0 or remaining <= 0:
            continue
        share = value / remaining
        if horizontal:
            rect_width = width * share
            rects.append((label, x0, y0, rect_width, height, value / total))
            x0 += rect_width
            width -= rect_width
        else:
            rect_height = height * share
            rects.append((label, x0, y0, width, rect_height, value / total))
            y0 += rect_height
            height -= rect_height
        remaining -= value
        horizontal = width >= height
    return rects


@register_chart("treemap")
def gen_treemap(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Slice-and-dice treemap with direct in-rectangle labels."""
    ax = _get_ax(ax)
    frame, category, _, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "treemap", error or "Need category + value columns")
    totals = _top_totals(frame, category, value, limit=10)
    colors = _categorical_palette(palette)
    for i, (label, x, y, width, height, share) in enumerate(_slice_rectangles(totals)):
        ax.add_patch(Rectangle((x, y), width, height, facecolor=colors[i % len(colors)],
                               edgecolor="white", linewidth=0.6, alpha=0.86))
        if width * height > 0.035:
            ax.text(x + width * 0.04, y + height * 0.55, _short_label(label, 13),
                    ha="left", va="center", fontsize=6, color="white", weight="bold")
            ax.text(x + width * 0.04, y + height * 0.34, f"{share * 100:.0f}%",
                    ha="left", va="center", fontsize=5, color="white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Treemap", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("mosaic_plot")
def gen_mosaic_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Two-way categorical composition as proportional mosaic rectangles."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "mosaic_plot", error or "Need category + value columns")
    pivot = _pivot_composition(frame, category, group, value, limit=7)
    colors = _categorical_palette(palette)
    totals = pivot.sum(axis=1)
    grand = float(totals.sum())
    x0 = 0.0
    for i, (idx, total) in enumerate(totals.items()):
        width = float(total) / grand if grand else 0.0
        y0 = 0.0
        for j, col in enumerate(pivot.columns):
            cell = float(pivot.loc[idx, col])
            height = cell / float(total) if total else 0.0
            if height > 0:
                ax.add_patch(Rectangle((x0, y0), width, height,
                                       facecolor=colors[j % len(colors)], edgecolor="white", linewidth=0.45))
            y0 += height
        ax.text(x0 + width / 2, -0.035, _short_label(idx, 10), ha="center", va="top",
                fontsize=6, rotation=30, clip_on=False)
        x0 += width
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Mosaic plot", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("marimekko")
def gen_marimekko(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Marimekko chart: variable category width plus stacked internal share."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "marimekko", error or "Need category + value columns")
    pivot = _pivot_composition(frame, category, group, value, limit=7)
    colors = _categorical_palette(palette)
    totals = pivot.sum(axis=1)
    grand = float(totals.sum())
    x0 = 0.0
    for idx, total in totals.items():
        width = float(total) / grand if grand else 0.0
        y0 = 0.0
        for j, col in enumerate(pivot.columns):
            share = float(pivot.loc[idx, col]) / float(total) if total else 0.0
            if share > 0:
                ax.add_patch(Rectangle((x0, y0), width, share,
                                       facecolor=colors[j % len(colors)], edgecolor="white", linewidth=0.45))
            y0 += share
        ax.text(x0 + width / 2, -0.035, _short_label(idx, 10), ha="center", va="top",
                fontsize=6, rotation=30, clip_on=False)
        x0 += width
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_ylabel("Share within category")
    ax.set_title("Marimekko", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("nested_donut")
def gen_nested_donut(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Two-ring donut for primary categories and optional subgroups."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "nested_donut", error or "Need category + value columns")
    colors = _categorical_palette(palette)
    inner = _top_totals(frame, category, value, limit=7)
    ax.pie(inner.to_numpy(dtype=float), radius=0.78, colors=[colors[i % len(colors)] for i in range(len(inner))],
           labels=[_short_label(label, 10) for label in inner.index], labeldistance=0.62,
           textprops={"fontsize": 5.5}, wedgeprops={"width": 0.28, "edgecolor": "white", "linewidth": 0.5})
    if group:
        outer_frame = frame.groupby([category, group], sort=False)[value].sum().reset_index()
        outer_labels: list[str] = []
        outer_values: list[float] = []
        outer_colors: list[str] = []
        for i, cat in enumerate(inner.index):
            subset = outer_frame[outer_frame[category] == cat]
            for _, row in subset.iterrows():
                outer_labels.append(_short_label(row[group], 9))
                outer_values.append(float(row[value]))
                outer_colors.append(colors[i % len(colors)])
        ax.pie(outer_values, radius=1.06, colors=outer_colors, labels=outer_labels, labeldistance=1.03,
               textprops={"fontsize": 5}, wedgeprops={"width": 0.24, "edgecolor": "white", "linewidth": 0.5})
    ax.set_aspect("equal")
    ax.set_title("Nested donut", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("sunburst")
def gen_sunburst(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                 rc_params: dict[str, Any], palette: dict[str, Any],
                 col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Sunburst-style radial hierarchy with aligned inner and outer rings."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "sunburst", error or "Need category + value columns")
    colors = _categorical_palette(palette)
    inner = _top_totals(frame, category, value, limit=7)
    ax.pie(inner.to_numpy(dtype=float), radius=0.68, colors=[colors[i % len(colors)] for i in range(len(inner))],
           labels=[_short_label(label, 10) for label in inner.index], labeldistance=0.42,
           textprops={"fontsize": 5.5}, wedgeprops={"width": 0.32, "edgecolor": "white", "linewidth": 0.5})
    if group:
        outer_values: list[float] = []
        outer_labels: list[str] = []
        outer_colors: list[str] = []
        grouped = frame.groupby([category, group], sort=False)[value].sum().reset_index()
        for i, cat in enumerate(inner.index):
            subset = grouped[grouped[category] == cat]
            for j, row in subset.iterrows():
                outer_values.append(float(row[value]))
                outer_labels.append(_short_label(row[group], 9))
                outer_colors.append(colors[(i + j) % len(colors)])
        ax.pie(outer_values, radius=1.0, colors=outer_colors, labels=outer_labels, labeldistance=1.02,
               textprops={"fontsize": 5}, wedgeprops={"width": 0.28, "edgecolor": "white", "linewidth": 0.5})
    ax.set_aspect("equal")
    ax.set_title("Sunburst", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("go_treemap")
def gen_go_treemap(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                   rc_params: dict[str, Any], palette: dict[str, Any],
                   col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """GO enrichment treemap using the generic category-value treemap grammar."""
    return gen_treemap(df, data_profile, chart_plan, rc_params, palette, col_map=col_map, ax=ax)


@register_chart("composition_dotplot")
def gen_composition_dotplot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                            rc_params: dict[str, Any], palette: dict[str, Any],
                            col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Bubble dotplot for category-by-group composition values."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "composition_dotplot", error or "Need category + value columns")
    pivot = _pivot_composition(frame, category, group, value, limit=10)
    if pivot.empty:
        return _fallback_empty(ax, "composition_dotplot", "Need composition values")
    values = pivot.to_numpy(dtype=float)
    vmax = float(np.nanmax(values)) if values.size else 1.0
    sizes = 28 + 190 * (values / vmax if vmax > 0 else values)
    x_idx, y_idx = np.meshgrid(np.arange(len(pivot.columns)), np.arange(len(pivot.index)))
    scatter = ax.scatter(x_idx.ravel(), y_idx.ravel(), s=sizes.ravel(), c=values.ravel(),
                         cmap="viridis", edgecolor="white", linewidth=0.35)
    ax.set_xticks(np.arange(len(pivot.columns)), [_short_label(col, 10) for col in pivot.columns],
                  rotation=30, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)), [_short_label(idx, 14) for idx in pivot.index])
    ax.invert_yaxis()
    ax.set_title("Composition dotplot", loc="center", fontweight="bold", pad=5)
    ax.figure.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
    _decorate_axes(ax)
    return ax


@register_chart("species_abundance")
def gen_species_abundance(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                          rc_params: dict[str, Any], palette: dict[str, Any],
                          col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Ranked horizontal abundance bars, prioritizing species/group totals."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "species_abundance", error or "Need species + count columns")
    label_col = group or category
    totals = _top_totals(frame, label_col, value, limit=10).sort_values()
    colors = _categorical_palette(palette)
    y = np.arange(len(totals))
    ax.barh(y, totals.to_numpy(dtype=float), color=[colors[i % len(colors)] for i in range(len(totals))],
            edgecolor="white", linewidth=0.35)
    ax.set_yticks(y, [_short_label(label, 14) for label in totals.index])
    ax.set_xlabel("Abundance")
    ax.set_title("Species abundance", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("shannon_diversity")
def gen_shannon_diversity(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                          rc_params: dict[str, Any], palette: dict[str, Any],
                          col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Shannon diversity index computed from category-by-species counts."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "shannon_diversity", error or "Need community count columns")
    colors = _categorical_palette(palette)
    if group:
        pivot = _pivot_composition(frame, category, group, value, limit=10)
        proportions = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        diversity = -(proportions * np.log(proportions.replace(0, np.nan))).sum(axis=1).sort_values(ascending=False)
    else:
        diversity = _top_totals(frame, category, value, limit=10).sort_values(ascending=False)
    x = np.arange(len(diversity))
    ax.bar(x, diversity.to_numpy(dtype=float), color=[colors[i % len(colors)] for i in range(len(diversity))],
           edgecolor="white", linewidth=0.35)
    ax.set_xticks(x, [_short_label(label, 12) for label in diversity.index], rotation=30, ha="right")
    ax.set_ylabel("Shannon H" if group else "Value")
    ax.set_title("Shannon diversity", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("kegg_bar")
def gen_kegg_bar(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                 rc_params: dict[str, Any], palette: dict[str, Any],
                 col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """KEGG-style ranked horizontal enrichment bars."""
    ax = _get_ax(ax)
    frame, category, _, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "kegg_bar", error or "Need pathway + value columns")
    totals = _top_totals(frame, category, value, limit=12).sort_values()
    colors = _categorical_palette(palette)
    y = np.arange(len(totals))
    ax.barh(y, totals.to_numpy(dtype=float), color=colors[1 % len(colors)],
            edgecolor="white", linewidth=0.35)
    ax.set_yticks(y, [_short_label(label, 18) for label in totals.index])
    ax.set_xlabel("Enrichment value")
    ax.set_title("KEGG bar", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("pareto_chart")
def gen_pareto_chart(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Sorted bars plus cumulative-percentage line."""
    ax = _get_ax(ax)
    frame, category, _, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "pareto_chart", error or "Need category + value columns")
    totals = _top_totals(frame, category, value, limit=10)
    colors = _categorical_palette(palette)
    x = np.arange(len(totals))
    ax.bar(x, totals.to_numpy(dtype=float), color=colors[2 % len(colors)],
           edgecolor="white", linewidth=0.35)
    ax.set_xticks(x, [_short_label(label, 10) for label in totals.index], rotation=30, ha="right")
    ax.set_ylabel("Value")
    cumulative = totals.cumsum() / totals.sum() * 100
    ax2 = ax.twinx()
    ax2.plot(x, cumulative.to_numpy(dtype=float), color="#333333", marker="o", markersize=2.8, lw=1.0)
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative %")
    ax2.spines["top"].set_visible(False)
    ax.set_title("Pareto chart", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("likert_stacked")
def gen_likert_stacked(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Horizontal 100% stacked Likert response bars."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "likert_stacked", error or "Need item + response + count columns")
    pivot = _pivot_composition(frame, category, group, value, limit=8)
    proportions = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0) * 100
    colors = _categorical_palette(palette)
    y = np.arange(len(proportions.index))
    left = np.zeros(len(proportions.index), dtype=float)
    for i, col in enumerate(proportions.columns):
        values = proportions[col].to_numpy(dtype=float)
        ax.barh(y, values, left=left, color=colors[i % len(colors)],
                edgecolor="white", linewidth=0.35, label=str(col))
        left += values
    ax.set_yticks(y, [_short_label(idx, 18) for idx in proportions.index])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Response share (%)")
    ax.set_title("Likert stacked", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("likert_divergent")
def gen_likert_divergent(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Diverging Likert bars centered on neutral response mass."""
    ax = _get_ax(ax)
    frame, category, group, value, error = _composition_frame(df, data_profile)
    if error or category is None or value is None:
        return _fallback_empty(ax, "likert_divergent", error or "Need item + response + count columns")
    pivot = _pivot_composition(frame, category, group, value, limit=8)
    proportions = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0) * 100
    colors = _categorical_palette(palette)
    y = np.arange(len(proportions.index))
    columns = list(proportions.columns)
    split = max(len(columns) // 2, 1)
    for row_idx, (_, row) in enumerate(proportions.iterrows()):
        left = 0.0
        for i, col in enumerate(reversed(columns[:split])):
            value_width = float(row[col])
            ax.barh(row_idx, -value_width, left=left, color=colors[i % len(colors)],
                    edgecolor="white", linewidth=0.35)
            left -= value_width
        right = 0.0
        for j, col in enumerate(columns[split:]):
            value_width = float(row[col])
            ax.barh(row_idx, value_width, left=right, color=colors[(split + j) % len(colors)],
                    edgecolor="white", linewidth=0.35)
            right += value_width
    ax.axvline(0, color="#333333", lw=0.8)
    ax.set_yticks(y, [_short_label(idx, 18) for idx in proportions.index])
    ax.set_xlabel("Diverging response share (%)")
    ax.set_title("Likert divergent", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
