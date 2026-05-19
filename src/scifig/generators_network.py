"""Network, flow, and relationship chart generators.

The implementations here intentionally stay matplotlib-only while giving
flow/network chart keys their own visual grammar instead of the generic chart
fallback: ribbons for Sankey/alluvial, circular arcs for chord diagrams,
parallel axes for multivariate profiles, and node-link topology for pathways.
"""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import FancyBboxPatch, PathPatch, Rectangle, Wedge
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .registry import register_chart


def _get_ax(ax: Any = None) -> Any:
    if ax is not None:
        return ax
    _, new_ax = plt.subplots(figsize=(110 / 25.4, 70 / 25.4), constrained_layout=True)
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


def _unique_columns(*columns: Optional[str]) -> list[str]:
    result: list[str] = []
    for column in columns:
        if column and column not in result:
            result.append(column)
    return result


def _short_label(value: Any, width: int = 16) -> str:
    text = str(value)
    return text if len(text) <= width else text[: width - 1] + "..."


def _fallback_empty(ax: Any, chart: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(chart.replace("_", " ").title(), loc="center", fontweight="bold", pad=5)
    ax.set_axis_off()
    return ax


def _flow_frame(df: pd.DataFrame, profile: Any) -> tuple[pd.DataFrame, str, str, str, str | None]:
    roles = _roles(profile)
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)

    source_col = _first_valid(
        df,
        roles.get("source"),
        roles.get("parent"),
        roles.get("feature_id"),
        categorical[0] if categorical else None,
    )
    target_col = _first_valid(
        df,
        roles.get("target"),
        roles.get("child"),
        roles.get("group"),
        roles.get("category"),
        categorical[1] if len(categorical) > 1 else None,
    )
    if target_col == source_col:
        target_col = next((col for col in categorical if col != source_col), None)

    value_col = _first_numeric_valid(
        df,
        roles.get("weight"),
        roles.get("frequency"),
        roles.get("value"),
        roles.get("size"),
        roles.get("y"),
        numeric[-1] if numeric else None,
    )

    working = df.copy()
    if source_col is None:
        source_col = "__source__"
        working[source_col] = "Source"
    if target_col is None:
        target_col = "__target__"
        working[target_col] = [f"Obs {i + 1}" for i in range(len(working))]
    if value_col is None:
        value_col = "__value__"
        working[value_col] = 1.0

    frame = working[[source_col, target_col, value_col]].copy()
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[source_col, target_col, value_col])
    frame[value_col] = frame[value_col].clip(lower=0)
    frame = frame[frame[value_col] > 0]
    if frame.empty:
        return pd.DataFrame(), source_col, target_col, value_col, "Need positive flow values"
    frame = frame.groupby([source_col, target_col], as_index=False, sort=False)[value_col].sum()
    frame = frame.sort_values(value_col, ascending=False).head(40)
    return frame, source_col, target_col, value_col, None


def _limit_flow_nodes(frame: pd.DataFrame, source: str, target: str, value: str, limit: int = 9) -> pd.DataFrame:
    node_totals = (
        frame.groupby(source)[value].sum()
        .add(frame.groupby(target)[value].sum(), fill_value=0.0)
        .sort_values(ascending=False)
    )
    keep = set(node_totals.index[:limit])
    limited = frame[frame[source].isin(keep) & frame[target].isin(keep)].copy()
    return limited if not limited.empty else frame.head(limit).copy()


def _node_colors(labels: list[Any], palette: dict[str, Any]) -> dict[Any, str]:
    colors = _categorical_palette(palette)
    return {label: colors[i % len(colors)] for i, label in enumerate(labels)}


def _spans(labels: list[Any], totals: pd.Series, total: float, usable: float, gap: float) -> dict[Any, tuple[float, float]]:
    spans: dict[Any, tuple[float, float]] = {}
    cursor = 0.05
    for label in labels:
        height = usable * float(totals.get(label, 0.0)) / total if total > 0 else 0.0
        spans[label] = (cursor, cursor + height)
        cursor += height + gap
    return spans


def _draw_two_stage_flow(
    ax: Any,
    frame: pd.DataFrame,
    source: str,
    target: str,
    value: str,
    palette: dict[str, Any],
    *,
    title: str,
    alluvial: bool = False,
) -> Any:
    frame = _limit_flow_nodes(frame, source, target, value)
    src_totals = frame.groupby(source, sort=False)[value].sum().sort_values(ascending=False)
    tgt_totals = frame.groupby(target, sort=False)[value].sum().sort_values(ascending=False)
    sources = src_totals.index.tolist()
    targets = tgt_totals.index.tolist()
    total = float(frame[value].sum())
    if total <= 0 or not sources or not targets:
        return _fallback_empty(ax, title, "Need source-target flow values")

    gap = 0.025 if alluvial else 0.035
    usable = min(0.9 - gap * max(len(sources) - 1, 0), 0.9 - gap * max(len(targets) - 1, 0))
    usable = max(usable, 0.35)
    src_spans = _spans(sources, src_totals, total, usable, gap)
    tgt_spans = _spans(targets, tgt_totals, total, usable, gap)
    src_cursor = {label: span[0] for label, span in src_spans.items()}
    tgt_cursor = {label: span[0] for label, span in tgt_spans.items()}
    colors = _node_colors(list(dict.fromkeys(sources + targets)), palette)

    node_width = 0.075 if alluvial else 0.055
    for label, (y0, y1) in src_spans.items():
        ax.add_patch(Rectangle((0.08, y0), node_width, y1 - y0, facecolor=colors[label],
                               edgecolor="white", linewidth=0.45, zorder=3))
        ax.text(0.06, (y0 + y1) / 2, _short_label(label), ha="right", va="center", fontsize=6)
    for label, (y0, y1) in tgt_spans.items():
        ax.add_patch(Rectangle((0.86, y0), node_width, y1 - y0,
                               facecolor=colors.get(label, "#D9D9D9"),
                               edgecolor="white", linewidth=0.45, zorder=3))
        ax.text(0.86 + node_width + 0.02, (y0 + y1) / 2, _short_label(label),
                ha="left", va="center", fontsize=6)

    for _, row in frame.iterrows():
        src_label = row[source]
        tgt_label = row[target]
        band = usable * float(row[value]) / total
        sy0 = src_cursor[src_label]
        ty0 = tgt_cursor[tgt_label]
        sy1 = sy0 + band
        ty1 = ty0 + band
        src_cursor[src_label] = sy1
        tgt_cursor[tgt_label] = ty1
        verts = [
            (0.08 + node_width, sy0), (0.35, sy0), (0.62, ty0), (0.86, ty0),
            (0.86, ty1), (0.62, ty1), (0.35, sy1), (0.08 + node_width, sy1),
            (0.08 + node_width, sy0),
        ]
        codes = [
            Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
            Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
            Path.CLOSEPOLY,
        ]
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=colors.get(src_label, "#999999"),
                               edgecolor="none", alpha=0.28 if alluvial else 0.36, zorder=2))

    ax.text(0.08 + node_width / 2, 1.01, "Source", ha="center", va="bottom", fontsize=6)
    ax.text(0.86 + node_width / 2, 1.01, "Target", ha="center", va="bottom", fontsize=6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.06)
    ax.set_axis_off()
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("sankey")
def gen_sankey(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
               rc_params: dict[str, Any], palette: dict[str, Any],
               col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Two-stage Sankey diagram with value-proportional flow ribbons."""
    ax = _get_ax(ax)
    frame, source, target, value, error = _flow_frame(df, data_profile)
    if error:
        return _fallback_empty(ax, "sankey", error)
    return _draw_two_stage_flow(ax, frame, source, target, value, palette, title="Sankey")


@register_chart("alluvial")
def gen_alluvial(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                 rc_params: dict[str, Any], palette: dict[str, Any],
                 col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Alluvial flow diagram using broad strata and translucent ribbons."""
    ax = _get_ax(ax)
    frame, source, target, value, error = _flow_frame(df, data_profile)
    if error:
        return _fallback_empty(ax, "alluvial", error)
    return _draw_two_stage_flow(ax, frame, source, target, value, palette, title="Alluvial", alluvial=True)


@register_chart("chord_diagram")
def gen_chord_diagram(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Circular chord diagram for weighted category-to-category relationships."""
    ax = _get_ax(ax)
    frame, source, target, value, error = _flow_frame(df, data_profile)
    if error:
        return _fallback_empty(ax, "chord_diagram", error)
    frame = _limit_flow_nodes(frame, source, target, value, limit=10)
    node_totals = (
        frame.groupby(source)[value].sum()
        .add(frame.groupby(target)[value].sum(), fill_value=0.0)
        .sort_values(ascending=False)
    )
    nodes = node_totals.index.tolist()
    total = float(node_totals.sum())
    if total <= 0 or len(nodes) < 2:
        return _fallback_empty(ax, "chord_diagram", "Need at least two connected nodes")

    colors = _node_colors(nodes, palette)
    gap = 4.0
    sweep = 360.0 - gap * len(nodes)
    spans: dict[Any, tuple[float, float]] = {}
    cursor = 0.0
    for node in nodes:
        extent = sweep * float(node_totals[node]) / total
        spans[node] = (cursor, cursor + extent)
        cursor += extent + gap

    anchors = {node: np.deg2rad((start + end) / 2) for node, (start, end) in spans.items()}
    for node, (start, end) in spans.items():
        ax.add_patch(Wedge((0, 0), 1.0, start, end, width=0.16,
                           facecolor=colors[node], edgecolor="white", linewidth=0.5))
        angle = anchors[node]
        rotation = np.rad2deg(angle)
        if 90 < rotation < 270:
            rotation -= 180
        ax.text(1.18 * np.cos(angle), 1.18 * np.sin(angle), _short_label(node, 12),
                ha="center", va="center", fontsize=6, rotation=rotation)

    max_flow = float(frame[value].max()) or 1.0
    for _, row in frame.iterrows():
        src_label = row[source]
        tgt_label = row[target]
        if src_label not in anchors or tgt_label not in anchors or src_label == tgt_label:
            continue
        a0 = anchors[src_label]
        a1 = anchors[tgt_label]
        p0 = np.array([0.86 * np.cos(a0), 0.86 * np.sin(a0)])
        p2 = np.array([0.86 * np.cos(a1), 0.86 * np.sin(a1)])
        mid = (p0 + p2) * 0.18
        t = np.linspace(0.0, 1.0, 60)
        curve = ((1 - t)[:, None] ** 2 * p0
                 + 2 * (1 - t)[:, None] * t[:, None] * mid
                 + t[:, None] ** 2 * p2)
        ax.plot(curve[:, 0], curve[:, 1], color=colors.get(src_label, "#999999"),
                alpha=0.30, lw=0.5 + 2.2 * float(row[value]) / max_flow)

    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("Chord diagram", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("parallel_coordinates")
def gen_parallel_coordinates(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                             rc_params: dict[str, Any], palette: dict[str, Any],
                             col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Parallel coordinates plot for row-level multivariate profiles."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    if len(numeric) < 2:
        return _fallback_empty(ax, "parallel_coordinates", "Need at least two numeric columns")

    group_col = _first_valid(df, roles.get("group"), roles.get("category"))
    work = df[numeric].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna(how="all")
    if work.empty:
        return _fallback_empty(ax, "parallel_coordinates", "Need finite numeric values")
    mins = work.min(axis=0)
    spans = (work.max(axis=0) - mins).replace(0, 1.0)
    normed = (work - mins) / spans
    x = np.arange(len(numeric))
    colors = _categorical_palette(palette)

    if group_col and group_col in df.columns:
        groups = df.loc[normed.index, group_col].astype(str)
        color_map = {label: colors[i % len(colors)] for i, label in enumerate(pd.unique(groups))}
        for idx, row in normed.iterrows():
            ax.plot(x, row.to_numpy(dtype=float), color=color_map[str(groups.loc[idx])], alpha=0.38, lw=0.8)
    else:
        for _, row in normed.iterrows():
            ax.plot(x, row.to_numpy(dtype=float), color="#666666", alpha=0.38, lw=0.8)

    for pos in x:
        ax.axvline(pos, color="#D0D0D0", lw=0.45, zorder=0)
    ax.set_xticks(x, [_short_label(col, 12) for col in numeric], rotation=30, ha="right")
    ax.set_xlim(float(x[0]), float(x[-1]))
    ax.set_ylim(-0.03, 1.03)
    ax.set_ylabel("Normalized value")
    ax.set_title("Parallel coordinates", loc="center", fontweight="bold", pad=5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return ax


@register_chart("pathway_map")
def gen_pathway_map(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Node-link pathway topology map using source-target relationships."""
    ax = _get_ax(ax)
    frame, source, target, value, error = _flow_frame(df, data_profile)
    if error:
        return _fallback_empty(ax, "pathway_map", error)
    frame = _limit_flow_nodes(frame, source, target, value, limit=12)
    src_nodes = set(frame[source])
    tgt_nodes = set(frame[target])
    source_only = [node for node in src_nodes if node not in tgt_nodes]
    sink_only = [node for node in tgt_nodes if node not in src_nodes]
    middle = [node for node in src_nodes & tgt_nodes]
    if not middle and source_only and sink_only:
        layers = [source_only, sink_only]
    else:
        leftovers = [node for node in (src_nodes | tgt_nodes) if node not in set(source_only + middle + sink_only)]
        layers = [source_only or leftovers[:1], middle or leftovers[1:2], sink_only or leftovers[2:]]
        layers = [layer for layer in layers if layer]

    colors = _node_colors(list(dict.fromkeys([*frame[source].tolist(), *frame[target].tolist()])), palette)
    positions: dict[Any, tuple[float, float]] = {}
    for layer_idx, nodes in enumerate(layers):
        x = 0.1 if len(layers) == 1 else 0.1 + 0.8 * layer_idx / (len(layers) - 1)
        y_values = np.linspace(0.82, 0.18, len(nodes)) if len(nodes) > 1 else np.array([0.5])
        for node, y in zip(nodes, y_values):
            positions[node] = (float(x), float(y))

    max_flow = float(frame[value].max()) or 1.0
    for _, row in frame.iterrows():
        src_label = row[source]
        tgt_label = row[target]
        if src_label not in positions or tgt_label not in positions:
            continue
        x0, y0 = positions[src_label]
        x1, y1 = positions[tgt_label]
        ax.annotate(
            "",
            xy=(x1 - 0.07, y1),
            xytext=(x0 + 0.07, y0),
            arrowprops={
                "arrowstyle": "-|>",
                "color": colors.get(src_label, "#666666"),
                "alpha": 0.38,
                "lw": 0.7 + 2.2 * float(row[value]) / max_flow,
                "shrinkA": 0,
                "shrinkB": 0,
                "connectionstyle": "arc3,rad=0.08",
            },
        )

    for node, (x, y) in positions.items():
        ax.add_patch(Rectangle((x - 0.07, y - 0.035), 0.14, 0.07,
                               facecolor=colors.get(node, "#999999"),
                               edgecolor="white", linewidth=0.55, zorder=3))
        ax.text(x, y, _short_label(node, 12), ha="center", va="center",
                fontsize=5.5, color="white", fontweight="bold", zorder=4)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    ax.set_title("Pathway map", loc="center", fontweight="bold", pad=5)
    return ax


def _architecture_frame(df: pd.DataFrame, profile: Any) -> tuple[list[Any], list[tuple[Any, Any]], str | None]:
    roles = _roles(profile)
    categorical = _categorical_columns(df)
    source_col = _first_valid(df, roles.get("source"), categorical[0] if categorical else None)
    target_col = _first_valid(df, roles.get("target"), categorical[1] if len(categorical) > 1 else None)
    if source_col and target_col and source_col != target_col:
        edges = [(row[source_col], row[target_col]) for _, row in df[_unique_columns(source_col, target_col)].dropna().iterrows()]
        nodes: list[Any] = []
        for src, tgt in edges:
            for node in (src, tgt):
                if node not in nodes:
                    nodes.append(node)
        return nodes[:12], edges[:20], None if nodes else "Need architecture nodes"

    node_col = _first_valid(
        df,
        roles.get("layer"),
        roles.get("component"),
        roles.get("label"),
        roles.get("feature_id"),
        categorical[0] if categorical else None,
    )
    order_col = _first_numeric_valid(df, roles.get("order"), roles.get("rank"))
    if node_col is None:
        return [], [], "Need layer/module nodes or source-target edges"
    frame = df[[col for col in (node_col, order_col) if col]].dropna(subset=[node_col]).copy()
    if order_col:
        frame[order_col] = pd.to_numeric(frame[order_col], errors="coerce")
        frame = frame.sort_values(order_col)
    nodes = frame[node_col].astype(str).drop_duplicates().tolist()[:12]
    edges = list(zip(nodes[:-1], nodes[1:]))
    return nodes, edges, None if nodes else "Need architecture nodes"


def _architecture_source_target(df: pd.DataFrame, profile: Any) -> tuple[Optional[str], Optional[str]]:
    roles = _roles(profile)
    categorical = _categorical_columns(df)
    source_col = _first_valid(df, roles.get("source"), categorical[0] if categorical else None)
    target_col = _first_valid(df, roles.get("target"), categorical[1] if len(categorical) > 1 else None)
    if source_col == target_col:
        target_col = None
    return source_col, target_col


def _architecture_metric_columns(
    df: pd.DataFrame,
    source_col: Optional[str],
    target_col: Optional[str],
) -> list[str]:
    metric_tokens = (
        "latency",
        "flops",
        "memory",
        "throughput",
        "cost",
        "score",
        "accuracy",
        "auc",
        "f1",
        "param",
        "weight",
        "edge",
        "value",
    )
    excluded = {source_col, target_col, None}
    metric_cols: list[str] = []
    for column in df.columns:
        col = str(column)
        if col in excluded or col not in set(_numeric_columns(df)):
            continue
        lowered = col.lower()
        if any(token in lowered for token in metric_tokens):
            metric_cols.append(col)
    if not metric_cols:
        metric_cols = [col for col in _numeric_columns(df) if col not in excluded]
    return metric_cols[:5]


def _draw_architecture(ax: Any, nodes: list[Any], edges: list[tuple[Any, Any]], palette: dict[str, Any], title: str) -> Any:
    colors = _categorical_palette(palette)
    n = len(nodes)
    if n == 0:
        return _fallback_empty(ax, title, "Need architecture nodes")
    x_positions = np.linspace(0.10, 0.90, n) if n > 1 else np.array([0.5])
    positions = {node: (float(x_positions[i]), 0.52 + 0.12 * ((i % 2) - 0.5)) for i, node in enumerate(nodes)}
    if n > 1:
        bounds = [max(0.04, positions[nodes[0]][0] - 0.08)]
        for left, right in zip(nodes, nodes[1:]):
            bounds.append((positions[left][0] + positions[right][0]) / 2)
        bounds.append(min(0.96, positions[nodes[-1]][0] + 0.08))
        for i in range(len(bounds) - 1):
            left = bounds[i]
            right = bounds[i + 1]
            if right <= left:
                continue
            ax.add_patch(
                Rectangle(
                    (left, 0.34),
                    right - left,
                    0.30,
                    transform=ax.transAxes,
                    facecolor=("#F8FAFC" if i % 2 == 0 else "#EEF2F7"),
                    edgecolor="none",
                    alpha=0.95,
                    zorder=0,
                )
            )
    in_degree = {node: 0 for node in nodes}
    out_degree = {node: 0 for node in nodes}
    for src, tgt in edges:
        if src in out_degree:
            out_degree[src] += 1
        if tgt in in_degree:
            in_degree[tgt] += 1
    for src, tgt in edges:
        if src not in positions or tgt not in positions:
            continue
        x0, y0 = positions[src]
        x1, y1 = positions[tgt]
        ax.annotate(
            "",
            xy=(x1 - 0.055, y1),
            xytext=(x0 + 0.055, y0),
            xycoords="axes fraction",
            textcoords="axes fraction",
            arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": "#555555", "connectionstyle": "arc3,rad=0.04"},
        )
    for i, node in enumerate(nodes):
        x, y = positions[node]
        meta_lines = [f"in={in_degree.get(node, 0)}", f"out={out_degree.get(node, 0)}"]
        box_h = 0.12
        ax.add_patch(FancyBboxPatch(
            (x - 0.060, y - box_h / 2),
            0.12,
            box_h,
            transform=ax.transAxes,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            facecolor=colors[i % len(colors)],
            edgecolor="white",
            linewidth=0.55,
            zorder=2,
        ))
        ax.text(x, y + 0.017, _short_label(node, 11), transform=ax.transAxes,
                ha="center", va="center", fontsize=5.2, color="white", fontweight="bold", zorder=3)
        if meta_lines:
            ax.text(
                x,
                y - 0.022,
                "\n".join(meta_lines[:2]),
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=4.2,
                color="white",
                zorder=3,
            )
    ax.set_axis_off()
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _draw_metric_profile(ax: Any, df: pd.DataFrame, metric_cols: list[str], palette: dict[str, Any]) -> None:
    colors = _categorical_palette(palette)
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#CBD5E1")
        spine.set_linewidth(0.55)
    if not metric_cols:
        ax.text(0.5, 0.56, "b  metric profile", ha="center", va="center",
                fontsize=6.1, fontweight="bold", transform=ax.transAxes)
        ax.text(0.5, 0.36, "no numeric metrics", ha="center", va="center",
                fontsize=5.0, color="#64748B", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return

    labels = [_short_label(col.replace("_", " "), 16) for col in metric_cols]
    means: list[float] = []
    fractions: list[float] = []
    for col in metric_cols:
        values = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        mean = float(values.mean()) if len(values) else 0.0
        denom = max(float(values.abs().max()) if len(values) else 1.0, abs(mean), 1.0)
        means.append(mean)
        fractions.append(min(1.0, abs(mean) / denom))

    y = np.arange(len(labels))
    ax.barh(y, fractions, color=[colors[i % len(colors)] for i in range(len(labels))], alpha=0.82)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=5.1)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.18)
    ax.set_xticks([])
    ax.set_title("b  metric profile", loc="left", fontsize=6.1, fontweight="bold", pad=2)
    for yi, value in zip(y, means):
        ax.text(0.88, yi, f"{value:.2g}", va="center", ha="right", fontsize=4.8, color="#1E293B",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.74, "pad": 0.35})


def _draw_edge_signal(
    ax: Any,
    df: pd.DataFrame,
    source_col: Optional[str],
    target_col: Optional[str],
    metric_col: Optional[str],
) -> None:
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#CBD5E1")
        spine.set_linewidth(0.55)
    if not source_col or not target_col or not metric_col:
        ax.text(0.5, 0.56, "c  edge signal", ha="center", va="center",
                fontsize=6.1, fontweight="bold", transform=ax.transAxes)
        ax.text(0.5, 0.36, "edge metric unavailable", ha="center", va="center",
                fontsize=5.0, color="#64748B", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return

    edge_df = df[[source_col, target_col, metric_col]].copy()
    edge_df[metric_col] = pd.to_numeric(edge_df[metric_col], errors="coerce")
    edge_df = edge_df.replace([np.inf, -np.inf], np.nan).dropna(subset=[source_col, target_col, metric_col]).head(8)
    if edge_df.empty:
        ax.text(0.5, 0.56, "c  edge signal", ha="center", va="center",
                fontsize=6.1, fontweight="bold", transform=ax.transAxes)
        ax.text(0.5, 0.36, "no valid edge rows", ha="center", va="center",
                fontsize=5.0, color="#64748B", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return

    labels = [_short_label(f"{row[source_col]} -> {row[target_col]}", 20) for _, row in edge_df.iterrows()]
    values = edge_df[metric_col].astype(float).to_numpy()
    y = np.arange(len(labels))
    ax.barh(y, values, color="#334155", alpha=0.74)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=4.8)
    ax.invert_yaxis()
    ax.tick_params(axis="x", labelsize=4.6, length=2)
    ax.set_title(f"c  edge signal: {_short_label(metric_col, 14)}", loc="left", fontsize=6.1, fontweight="bold", pad=2)
    limit = max([abs(float(v)) for v in values] + [1.0])
    ax.set_xlim(0, limit * 1.18)


@register_chart("model_architecture")
def gen_model_architecture(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                           rc_params: dict[str, Any], palette: dict[str, Any],
                           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Model architecture node-link diagram from layer rows or source-target edges."""
    ax = _get_ax(ax)
    nodes, edges, error = _architecture_frame(df, data_profile)
    if error:
        return _fallback_empty(ax, "model_architecture", error)
    return _draw_architecture(ax, nodes, edges, palette, "Model architecture")


@register_chart("model_architecture_board")
def gen_model_architecture_board(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                                 rc_params: dict[str, Any], palette: dict[str, Any],
                                 col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Architecture storyboard with topology plus real metric support axes."""
    ax = _get_ax(ax)
    nodes, edges, error = _architecture_frame(df, data_profile)
    if error:
        return _fallback_empty(ax, "model_architecture_board", error)
    source_col, target_col = _architecture_source_target(df, data_profile)
    metric_cols = _architecture_metric_columns(df, source_col, target_col)
    edge_metric = next((col for col in metric_cols if any(token in col.lower() for token in ("edge", "weight"))), None)
    if edge_metric is None and metric_cols:
        edge_metric = metric_cols[0]

    ax.clear()
    ax.set_axis_off()
    ax.set_title("Model architecture board", loc="center", fontweight="bold", pad=5)
    arch_ax = ax.inset_axes([0.025, 0.355, 0.95, 0.585])
    metric_ax = ax.inset_axes([0.045, 0.070, 0.425, 0.215])
    edge_ax = ax.inset_axes([0.545, 0.070, 0.405, 0.215])

    _draw_architecture(arch_ax, nodes, edges, palette, "a  architecture topology")
    _draw_metric_profile(metric_ax, df, metric_cols[:4], palette)
    _draw_edge_signal(edge_ax, df, source_col, target_col, edge_metric)
    ax.text(0.975, 0.975, f"nodes={len(nodes)}  edges={len(edges)}", transform=ax.transAxes,
            ha="right", va="top", fontsize=5.2, color="#334155")
    return ax


@register_chart("mediation_path")
def gen_mediation_path(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Mediation path diagram X -> M -> Y with standardized path coefficients."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    x_col = _first_numeric_valid(df, roles.get("x"), numeric[0] if numeric else None)
    m_col = _first_numeric_valid(df, roles.get("mediator"), roles.get("feature_id"), numeric[1] if len(numeric) > 1 else None)
    y_col = _first_numeric_valid(df, roles.get("y"), roles.get("value"), numeric[2] if len(numeric) > 2 else None)
    if len({x_col, m_col, y_col}) < 3 or x_col is None or m_col is None or y_col is None:
        return _fallback_empty(ax, "mediation_path", "Need x + mediator + y numeric columns")
    frame = df[[x_col, m_col, y_col]].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < 3:
        return _fallback_empty(ax, "mediation_path", "Need >=3 mediation rows")
    z = (frame - frame.mean()) / frame.std(ddof=0).replace(0, 1.0)
    a = float(np.polyfit(z[x_col], z[m_col], 1)[0])
    b = float(np.polyfit(z[m_col], z[y_col], 1)[0])
    c_prime = float(np.polyfit(z[x_col], z[y_col], 1)[0])
    indirect = a * b
    colors = _categorical_palette(palette)
    nodes = {x_col: (0.16, 0.66), m_col: (0.50, 0.66), y_col: (0.84, 0.66)}
    ax.add_patch(Rectangle((0.07, 0.50), 0.86, 0.27, transform=ax.transAxes,
                           facecolor="#F8FAFC", edgecolor="none", zorder=0))
    for i, (name, (cx, cy)) in enumerate(nodes.items()):
        ax.add_patch(FancyBboxPatch(
            (cx - 0.075, cy - 0.050),
            0.15,
            0.10,
            transform=ax.transAxes,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            facecolor=colors[i % len(colors)],
            edgecolor="white",
            linewidth=0.55,
            zorder=2,
        ))
        ax.text(cx, cy, _short_label(name, 10), transform=ax.transAxes,
                ha="center", va="center", fontsize=6, color="white", fontweight="bold", zorder=3)
    for src, dst, coeff in [(x_col, m_col, a), (m_col, y_col, b)]:
        sx, sy = nodes[src]
        dx, dy = nodes[dst]
        ax.annotate("", xy=(dx - 0.09, dy), xytext=(sx + 0.09, sy),
                    xycoords="axes fraction", textcoords="axes fraction",
                    arrowprops={"arrowstyle": "-|>", "lw": 1.0, "color": "#333333"})
        ax.text((sx + dx) / 2, sy + 0.075, f"{coeff:.2f}", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=6,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.45})
    ax.annotate("", xy=(0.76, 0.45), xytext=(0.24, 0.45),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "lw": 0.85, "color": "#777777", "linestyle": "--"})
    ax.text(0.50, 0.385, f"direct c'={c_prime:.2f}", transform=ax.transAxes,
            ha="center", va="center", fontsize=5.8, color="#555555")

    ax.add_patch(FancyBboxPatch(
        (0.10, 0.075),
        0.80,
        0.205,
        transform=ax.transAxes,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor="white",
        edgecolor="#CBD5E1",
        linewidth=0.55,
        zorder=1,
    ))
    ax.text(0.135, 0.247, "Effect summary", transform=ax.transAxes,
            ha="left", va="center", fontsize=6.2, fontweight="bold", color="#0F172A", zorder=3)
    summary = [
        ("a  X -> M", a, colors[0 % len(colors)]),
        ("b  M -> Y", b, colors[1 % len(colors)]),
        ("c' direct", c_prime, "#64748B"),
        ("ab indirect", indirect, colors[2 % len(colors)]),
    ]
    scale = max([abs(value) for _, value, _ in summary] + [1.0])
    for idx, (label, value, color) in enumerate(summary):
        y = 0.210 - idx * 0.038
        width = 0.23 * min(1.0, abs(value) / scale)
        baseline = 0.50
        x0 = baseline if value >= 0 else baseline - width
        ax.text(0.135, y, label, transform=ax.transAxes, ha="left", va="center", fontsize=5.1, color="#334155")
        ax.plot([baseline - 0.24, baseline + 0.24], [y, y], transform=ax.transAxes,
                color="#E2E8F0", lw=0.55, zorder=1)
        ax.add_patch(Rectangle((x0, y - 0.010), width, 0.020, transform=ax.transAxes,
                               facecolor=color, edgecolor="none", alpha=0.82, zorder=2))
        ax.text(0.80, y, f"{value:.2f}", transform=ax.transAxes,
                ha="right", va="center", fontsize=5.1, color="#334155")
    ax.text(0.50, 0.035, f"Indirect effect (a*b) = {indirect:.2f}", transform=ax.transAxes,
            ha="center", va="center", fontsize=5.3, color="#333333")
    ax.set_axis_off()
    ax.set_title("Mediation path", loc="center", fontweight="bold", pad=5)
    return ax
