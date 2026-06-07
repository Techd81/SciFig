"""Relationship / network chart generators (sankey/chord/architecture/...).

Stage-2 refactor: function bodies are byte-identical to the pre-refactor
runtime generator_sources map. Consumed via _load_generator_source_map()
source-concatenation (not standalone import); shared role/color helpers
live in generators_distribution, classifier-board helpers in generators_ml.
"""


from math import pi as _pi
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colors import TwoSlopeNorm
from matplotlib.gridspec import GridSpecFromSubplotSpec
from matplotlib.patches import Ellipse
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.optimize import curve_fit
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import gaussian_kde
from scipy.stats import norm
from sklearn.linear_model import LinearRegression
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.metrics import roc_curve, auc
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from statsmodels.nonparametric.smoothers_lowess import lowess
import math as _math
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
import squarify
import textwrap
import warnings


def gen_alluvial(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Two-stage alluvial flow diagram between source and target categories."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    source_col = roles.get("source") or roles.get("from") or roles.get("feature_id")
    target_col = roles.get("target") or roles.get("to") or roles.get("group")
    value_col = roles.get("value") or roles.get("count")
    if source_col is None or target_col is None:
        raise ValueError("alluvial requires source and target columns")

    flows = df.copy()
    if value_col is None or value_col not in flows.columns:
        flows["_value"] = 1.0
        value_col = "_value"
    flows = flows.groupby([source_col, target_col], as_index=False)[value_col].sum()
    sources = flows[source_col].dropna().unique().tolist()
    targets = flows[target_col].dropna().unique().tolist()
    total = flows[value_col].sum() or 1.0

    if standalone:
        fig, ax = plt.subplots(figsize=(120 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)

    colors = _extract_colors(palette, sources)
    src_totals = flows.groupby(source_col)[value_col].sum().reindex(sources).fillna(0)
    tgt_totals = flows.groupby(target_col)[value_col].sum().reindex(targets).fillna(0)

    def _spans(labels, totals):
        spans = {}
        cursor = 0.0
        gap = 0.025
        usable = 1.0 - gap * max(len(labels) - 1, 0)
        for label in labels:
            height = usable * totals[label] / total
            spans[label] = [cursor, cursor + height]
            cursor += height + gap
        return spans

    src_spans = _spans(sources, src_totals)
    tgt_spans = _spans(targets, tgt_totals)
    src_cursor = {k: v[0] for k, v in src_spans.items()}
    tgt_cursor = {k: v[0] for k, v in tgt_spans.items()}

    for label, (y0, y1) in src_spans.items():
        ax.add_patch(plt.Rectangle((0.05, y0), 0.08, y1 - y0,
                                   facecolor=colors.get(label, "#999999"),
                                   edgecolor="white", linewidth=0.4))
        ax.text(0.035, (y0 + y1) / 2, str(label), ha="right", va="center", fontsize=5)
    for label, (y0, y1) in tgt_spans.items():
        ax.add_patch(plt.Rectangle((0.87, y0), 0.08, y1 - y0,
                                   facecolor="#D9D9D9", edgecolor="white", linewidth=0.4))
        ax.text(0.965, (y0 + y1) / 2, str(label), ha="left", va="center", fontsize=5)

    for _, row in flows.iterrows():
        source = row[source_col]
        target = row[target_col]
        height = row[value_col] / total * (1.0 - 0.025 * max(len(sources) - 1, 0))
        y0s, y1s = src_cursor[source], src_cursor[source] + height
        y0t, y1t = tgt_cursor[target], tgt_cursor[target] + height
        src_cursor[source] = y1s
        tgt_cursor[target] = y1t
        verts = [(0.13, y0s), (0.45, y0s), (0.55, y0t), (0.87, y0t),
                 (0.87, y1t), (0.55, y1t), (0.45, y1s), (0.13, y1s)]
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        path = Path(verts + [verts[0]],
                    [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                     Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                     Path.CLOSEPOLY])
        ax.add_patch(PathPatch(path, facecolor=colors.get(source, "#999999"),
                               edgecolor="none", alpha=0.35))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "alluvial")
    return ax


def gen_chord_diagram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Chord diagram showing flows between categories using matplotlib arcs.

    Expects a square matrix or long-format flow table.  Semantic roles:
      - feature_id: source category column
      - group: target category column
      - value: flow magnitude column
    Falls back to the first NxN numeric block if roles are absent.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    src_col = roles.get("feature_id")
    tgt_col = roles.get("group")
    val_col = roles.get("value")

    # Build adjacency matrix
    if src_col and tgt_col and val_col:
        cats = sorted(set(df[src_col]) | set(df[tgt_col]))
        mat = df.pivot_table(index=src_col, columns=tgt_col,
                             values=val_col, aggfunc="sum").reindex(
                                 index=cats, columns=cats).fillna(0).values
    else:
        numeric = df.select_dtypes(include="number")
        mat = numeric.values[:len(numeric.columns), :len(numeric.columns)]
        cats = list(numeric.columns[:mat.shape[0]])

    n = len(cats)
    totals = mat.sum(axis=1) + mat.sum(axis=0)
    total = totals.sum()
    if total == 0:
        total = 1

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           subplot_kw={"aspect": "equal"},
                           constrained_layout=True)

    fallback = palette.get("categorical",
                            ["#0072B2", "#E69F00", "#56B4E9", "#009E73",
                             "#F0E442", "#D55E00", "#CC79A7", "#999999"])
    colors = [fallback[i % len(fallback)] for i in range(n)]

    angle_gap = 4  # degrees between arcs
    gap_total = n * angle_gap
    sweep = 360 - gap_total

    # Compute angular spans for each node
    spans = []
    start = 0
    for i in range(n):
        extent = (totals[i] / total) * sweep
        spans.append((start, extent))
        start += extent + angle_gap

    # Draw outer arcs
    for i, (s, e) in enumerate(spans):
        wedge = matplotlib.patches.Wedge(
            (0, 0), 1.0, s, s + e, width=0.15,
            facecolor=colors[i], edgecolor="white", linewidth=0.5)
        ax.add_patch(wedge)
        mid_angle = np.radians(s + e / 2)
        ax.text(1.18 * np.cos(mid_angle), 1.18 * np.sin(mid_angle),
                cats[i], ha="center", va="center", fontsize=5,
                rotation=np.degrees(mid_angle) - 90
                if 90 < np.degrees(mid_angle) < 270
                else np.degrees(mid_angle) + 90)

    # Draw chords
    out_pos = [0.0] * n  # track outgoing offset within each arc
    for i in range(n):
        for j in range(n):
            if mat[i, j] == 0:
                continue
            frac = mat[i, j] / total
            si, ei = spans[i]
            sj, ej = spans[j]

            a1 = si + out_pos[i] * sweep / totals[i] if totals[i] else 0
            out_pos[i] += mat[i, j]

            b1 = sj + out_pos[j] * sweep / totals[j] if totals[j] else 0
            out_pos[j] += mat[j, i]

            t = np.linspace(0, 1, 50)
            # Quadratic Bezier through center
            p0 = np.array([np.cos(np.radians(a1)), np.sin(np.radians(a1))])
            p2 = np.array([np.cos(np.radians(b1)), np.sin(np.radians(b1))])
            mid = (p0 + p2) / 2 * 0.3  # pull toward center
            chord_pts = ((1 - t)[:, None] ** 2 * p0
                         + 2 * (1 - t)[:, None] * t[:, None] * mid
                         + t[:, None] ** 2 * p2)
            ax.plot(chord_pts[:, 0], chord_pts[:, 1],
                    color=colors[i], alpha=0.25, lw=0.4)

    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "chord_diagram")
    return ax


def gen_mediation_path(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mediation path diagram: X -> M -> Y or PLS-PM/SEM directed topology.

    Semantic roles:
      - x: independent variable (column name or computed summary key)
      - mediator: mediating variable column
      - y: dependent variable column
      - source/target/coefficient: optional PLS-PM/SEM edge table roles
    Coefficients are computed as standardized betas via OLS.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    visual_plan = chartPlan.get("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        if isinstance(chartPlan, dict):
            chartPlan["visualContentPlan"] = visual_plan
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])} if isinstance(dataProfile, dict) else set()
    template_motifs = {
        str(m).lower()
        for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs", []) if isinstance(chartPlan, dict) else [])
    }
    source_col = roles.get("source") or roles.get("from") or roles.get("feature_id")
    target_col = roles.get("target") or roles.get("to") or roles.get("group")
    coef_col = (
        roles.get("coefficient") or roles.get("coef") or roles.get("path_coef")
        or roles.get("effect") or roles.get("value") or roles.get("edge_weight")
    )
    sig_col = roles.get("significance") or roles.get("sig") or roles.get("stars")
    p_col = roles.get("p_value") or roles.get("p") or roles.get("pvalue")
    columns_lower = {str(c).lower(): c for c in getattr(df, "columns", [])}
    explicit_path_signal = bool(
        (roles.get("source") or roles.get("from") or columns_lower.get("source") or columns_lower.get("from"))
        and (roles.get("target") or roles.get("to") or columns_lower.get("target") or columns_lower.get("to"))
        and (
            roles.get("coefficient") or roles.get("coef") or roles.get("path_coef") or roles.get("effect") or roles.get("edge_weight")
            or columns_lower.get("coefficient") or columns_lower.get("coef") or columns_lower.get("path_coef")
            or columns_lower.get("effect") or columns_lower.get("edge_weight")
        )
    )
    source_col = source_col if source_col in getattr(df, "columns", []) else columns_lower.get("source") or columns_lower.get("from")
    target_col = target_col if target_col in getattr(df, "columns", []) else columns_lower.get("target") or columns_lower.get("to")
    coef_col = coef_col if coef_col in getattr(df, "columns", []) else (
        columns_lower.get("coefficient") or columns_lower.get("coef") or columns_lower.get("path_coef")
        or columns_lower.get("effect") or columns_lower.get("value") or columns_lower.get("edge_weight")
    )
    sig_col = sig_col if sig_col in getattr(df, "columns", []) else columns_lower.get("significance") or columns_lower.get("sig") or columns_lower.get("stars")
    p_col = p_col if p_col in getattr(df, "columns", []) else columns_lower.get("p_value") or columns_lower.get("p") or columns_lower.get("pvalue")
    curvature_col = roles.get("curvature") or roles.get("rad")
    curvature_col = curvature_col if curvature_col in getattr(df, "columns", []) else columns_lower.get("curvature") or columns_lower.get("rad")
    total_effect_col = roles.get("total_effect") or roles.get("totalEffect")
    total_effect_col = total_effect_col if total_effect_col in getattr(df, "columns", []) else columns_lower.get("total_effect") or columns_lower.get("totaleffect")
    explicit_pls_motif = (
        "pls_pm_path_model" in template_motifs
        or "sem_path_model" in template_motifs
        or "path_model_total_effects" in template_motifs
        or bool(patterns & {"pls_pm_path_model", "sem_path_model", "path_model_total_effects", "pls_pm", "sem"})
    )
    if explicit_pls_motif and not source_col:
        source_col = roles.get("feature_id") if roles.get("feature_id") in getattr(df, "columns", []) else None
    if explicit_pls_motif and not target_col:
        target_col = roles.get("group") if roles.get("group") in getattr(df, "columns", []) else None
    if explicit_pls_motif and not coef_col:
        coef_col = roles.get("value") if roles.get("value") in getattr(df, "columns", []) else None
    is_pls_pm = explicit_pls_motif or explicit_path_signal
    if is_pls_pm:
        if not all([source_col, target_col, coef_col]):
            raise ValueError("PLS-PM mediation_path requires 'source', 'target', and 'coefficient' edge roles")
        if standalone:
            fig, ax = plt.subplots(figsize=(115 * (1 / 25.4), 82 * (1 / 25.4)),
                               constrained_layout=True)
        drawer = globals().get("draw_pls_pm_path_model")
        if drawer is None:
            raise RuntimeError("draw_pls_pm_path_model helper is required for PLS-PM mediation_path")
        result = drawer(
            ax,
            df,
            source_col=source_col,
            target_col=target_col,
            coef_col=coef_col,
            significance_col=sig_col,
            p_col=p_col,
            curvature_col=curvature_col,
            node_positions=visual_plan.get("plsNodePositions") or visual_plan.get("nodePositions"),
            total_effects=visual_plan.get("plsTotalEffects") or visual_plan.get("totalEffects"),
            total_effect_col=total_effect_col,
            target_node=visual_plan.get("plsTargetNode") or visual_plan.get("targetNode"),
            gof_text=visual_plan.get("plsGofText") or visual_plan.get("gofText"),
            positive_color=visual_plan.get("plsPositiveColor", "#D73027"),
            negative_color=visual_plan.get("plsNegativeColor", "#2B6CB0"),
            inset_rect=visual_plan.get("plsInsetRect", [0.70, 0.65, 0.25, 0.30]),
            linewidth_base=visual_plan.get("pathLinewidthBase", 1.0),
            linewidth_scale=visual_plan.get("pathLinewidthScale", 8.0),
            col_map=col_map,
        )
        if callable(globals().get("_record_template_motif")):
            _record_template_motif(visual_plan, "pls_pm_path_model")
        if callable(globals().get("_visual_count")):
            _visual_count(visual_plan, "sampleEncodingCount")
            _visual_count(visual_plan, "insetCount")
            _visual_count(visual_plan, "referenceLineCount")
            for _ in range(result.get("significance_label_count", 0)):
                _visual_count(visual_plan, "significanceLabelCount")
        visual_plan["pathEdgeCount"] = result.get("edge_count", 0)
        visual_plan["pathNodeCount"] = result.get("node_count", 0)
        visual_plan["pathPositiveEdgeCount"] = result.get("positive_edge_count", 0)
        visual_plan["pathNegativeEdgeCount"] = result.get("negative_edge_count", 0)
        visual_plan["totalEffectBarCount"] = result.get("total_effect_bar_count", 0)
        visual_plan["pathLinewidthEncodesAbsCoefficient"] = True
        visual_plan["signedPathColorEncoding"] = True
        visual_plan["gofAnnotationPresent"] = bool(visual_plan.get("plsGofText") or visual_plan.get("gofText"))
        visual_plan["pathModelTargetNode"] = result.get("target_node")
        if standalone:
            try:
                ax.figure.set_layout_engine(None)
            except Exception:
                pass
            ax.figure.subplots_adjust(left=0.03, right=0.98, bottom=0.04, top=0.98)
        return ax

    x_col = roles.get("x") or roles.get("condition")
    m_col = roles.get("mediator") or roles.get("feature_id")
    y_col = roles.get("y") or roles.get("value")

    if not all([x_col, m_col, y_col]):
        raise ValueError("mediation_path requires 'x', 'mediator', and 'y' in semanticRoles")

    # Standardize for comparable coefficients
    z = (df[[x_col, m_col, y_col]] - df[[x_col, m_col, y_col]].mean()) / \
        df[[x_col, m_col, y_col]].std().replace(0, 1)

    # Path coefficients
    a = np.polyfit(z[x_col], z[m_col], 1)[0]  # X -> M
    b = np.polyfit(z[m_col], z[y_col], 1)[0]  # M -> Y
    c_prime = np.polyfit(z[x_col], z[y_col], 1)[0]  # X -> Y (direct)
    ab = a * b  # indirect effect

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    # Node positions
    nodes = {x_col: (0.1, 0.5), m_col: (0.5, 0.5), y_col: (0.9, 0.5)}
    box_w, box_h = 0.12, 0.10

    color_accent = palette.get("categorical", ["#0072B2"])[0]

    for name, (cx, cy) in nodes.items():
        rect = plt.Rectangle((cx - box_w / 2, cy - box_h / 2), box_w, box_h,
                              facecolor="white", edgecolor=color_accent,
                              linewidth=1, transform=ax.transAxes, clip_on=False)
        ax.add_patch(rect)
        ax.text(cx, cy, name, ha="center", va="center", fontsize=6,
                fontweight="bold", transform=ax.transAxes)

    # Arrows with coefficients
    arrow_kw = dict(arrowstyle="-|>", color="#333333", lw=1,
                    connectionstyle="arc3,rad=0", transform=ax.transAxes)

    def _draw_arrow(src, dst, coeff, y_off=0.08):
        sx, sy = nodes[src]
        dx, dy = nodes[dst]
        ax.annotate("", xy=(dx - box_w / 2 - 0.01, dy),
                     xytext=(sx + box_w / 2 + 0.01, sy),
                     xycoords="axes fraction", textcoords="axes fraction",
                     arrowprops=arrow_kw)
        mx = (sx + dx) / 2
        ax.text(mx, sy + y_off, f"{coeff:.3f}", ha="center", va="bottom",
                fontsize=5.5, color="#333333", transform=ax.transAxes)

    _draw_arrow(x_col, m_col, a, y_off=0.06)
    _draw_arrow(m_col, y_col, b, y_off=0.06)
    # Direct path below
    sx, sy = nodes[x_col]
    dx, dy = nodes[y_col]
    ax.annotate("", xy=(dx - box_w / 2 - 0.01, dy - 0.18),
                 xytext=(sx + box_w / 2 + 0.01, sy - 0.18),
                 xycoords="axes fraction", textcoords="axes fraction",
                 arrowprops={**arrow_kw, "linestyle": "--"})
    mx = (sx + dx) / 2
    ax.text(mx, sy - 0.18 - 0.06, f"c'={c_prime:.3f}", ha="center",
            va="top", fontsize=5, color="#666666", transform=ax.transAxes)

    ax.text(0.5, 0.02, f"Indirect effect (a*b) = {ab:.3f}",
            ha="center", fontsize=5, transform=ax.transAxes, color="#333333")

    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "mediation_path")
    return ax


def gen_model_architecture(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """AI/ML model architecture or pipeline topology diagram.

    Supports ordered node tables (`layer`, `module`, `component`, `stage`,
    `type`, `units`, `params`, `order`) and source-target edge tables with
    optional node metadata (`source_stage`, `target_type`, `target_params`) and
    edge metrics (`latency`, `flops`, `memory`, `throughput`, `value`). The
    output intentionally avoids legends and keeps every label inside axes
    bounds so render QA can treat it as a hard layout object.
    """
    import numpy as np
    import pandas as pd
    import matplotlib.patches as mpatches
    import textwrap

    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {}) if isinstance(dataProfile, dict) else {}
    if df is None or not len(df):
        raise ValueError("model_architecture requires layer/module rows or source-target edges")

    def _pick_col(*role_names, tokens=()):
        for role_name in role_names:
            candidate = roles.get(role_name)
            if candidate in getattr(df, "columns", []):
                return candidate
        lower_to_col = {str(col).lower(): col for col in getattr(df, "columns", [])}
        for token in tokens:
            if token in lower_to_col:
                return lower_to_col[token]
        for col in getattr(df, "columns", []):
            lowered = str(col).lower()
            if any(token in lowered for token in tokens):
                return col
        return None

    source_col = _pick_col("source", "from", tokens=("source", "from", "input"))
    target_col = _pick_col("target", "to", tokens=("target", "to", "output"))
    node_col = _pick_col(
        "layer", "module", "node", "name", "component", "block", "feature_id", "label",
        tokens=("layer", "module", "node", "name", "component", "block")
    )
    order_col = _pick_col("order", "step", "depth", tokens=("order", "step", "depth", "rank", "idx"))
    stage_col = _pick_col("stage", "group", "phase", tokens=("stage", "phase", "block_group", "group"))
    type_col = _pick_col("type", "kind", "operation", tokens=("type", "kind", "operation", "op"))
    units_col = _pick_col("units", "channels", "features", tokens=("units", "neurons", "channels", "features", "heads", "dim"))
    params_col = _pick_col("params", "parameters", tokens=("params", "parameters", "n_params"))
    value_col = _pick_col("value", "weight", tokens=("value", "weight", "latency", "flops"))
    metric_tokens = (
        "latency", "flops", "memory", "throughput", "cost", "score",
        "accuracy", "auc", "f1", "params", "parameters", "weight",
    )
    metric_cols = []
    for col in getattr(df, "columns", []):
        lowered = str(col).lower()
        if col in {source_col, target_col, node_col, order_col}:
            continue
        if any(token in lowered for token in metric_tokens):
            try:
                numeric = pd.to_numeric(df[col], errors="coerce")
            except Exception:
                continue
            if numeric.notna().any():
                metric_cols.append(col)

    def _clean_label(value, max_len=20):
        text = str(value).strip()
        if text.lower() in ("nan", "none", ""):
            text = "module"
        replacements = {
            "Transformer": "Transf.",
            "Convolutional": "Conv.",
            "Embedding": "Embed.",
            "Classifier": "Classif.",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text if len(text) <= max_len else text[:max_len - 1] + "..."

    def _wrap_label(value, line_len=13, max_lines=2):
        wrapped = textwrap.wrap(_clean_label(value, max_len=line_len * max_lines + 3), width=line_len)
        if not wrapped:
            return "module"
        if len(wrapped) > max_lines:
            wrapped = wrapped[:max_lines]
            wrapped[-1] = _clean_label(wrapped[-1], line_len)
        return "\n".join(wrapped)

    if source_col and target_col:
        edge_frame = df[[source_col, target_col]].dropna().astype(str)
        if edge_frame.empty:
            raise ValueError("model_architecture source-target table has no valid edges")
        nodes = []
        for src, tgt in edge_frame.itertuples(index=False, name=None):
            for node in (src, tgt):
                if node not in nodes:
                    nodes.append(node)
        edges = [(src, tgt) for src, tgt in edge_frame.itertuples(index=False, name=None)]
        if len(nodes) > 14:
            nodes = nodes[:14]
            node_set = set(nodes)
            edges = [(src, tgt) for src, tgt in edges if src in node_set and tgt in node_set]
        meta = {node: {} for node in nodes}
        meta_fields = {
            "stage": ("stage", "phase", "group"),
            "type": ("type", "kind", "operation", "op"),
            "units": ("units", "neurons", "channels", "features", "heads", "dim"),
            "params": ("params", "parameters", "n_params"),
        }
        lower_cols = {str(col).lower(): col for col in df.columns}
        for _, row in df.iterrows():
            src = str(row.get(source_col))
            tgt = str(row.get(target_col))
            for node, prefix in ((src, "source"), (tgt, "target")):
                if node not in meta:
                    continue
                for field, suffixes in meta_fields.items():
                    candidates = [f"{prefix}_{suffix}" for suffix in suffixes] + [f"{prefix}{suffix}" for suffix in suffixes]
                    if field == "stage":
                        candidates.extend(suffixes)
                    for candidate in candidates:
                        col = lower_cols.get(candidate)
                        if col in df.columns and pd.notna(row.get(col)) and str(row.get(col)).strip():
                            meta[node].setdefault(field, row.get(col))
                            break
    else:
        if not node_col:
            candidate_cols = [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])]
            if not candidate_cols:
                raise ValueError("model_architecture requires a layer/module/node column")
            node_col = candidate_cols[0]
        node_df = df.copy()
        if order_col in node_df:
            node_df = node_df.sort_values(order_col, kind="mergesort")
        node_df = node_df.dropna(subset=[node_col]).head(14)
        nodes = [_clean_label(value, 28) for value in node_df[node_col].astype(str).tolist()]
        edges = list(zip(nodes[:-1], nodes[1:]))
        meta = {}
        for node, (_, row) in zip(nodes, node_df.iterrows()):
            meta[node] = {
                "stage": row.get(stage_col) if stage_col in node_df else None,
                "type": row.get(type_col) if type_col in node_df else None,
                "units": row.get(units_col) if units_col in node_df else None,
                "params": row.get(params_col) if params_col in node_df else None,
            }

    if not nodes:
        raise ValueError("model_architecture could not derive any modules")

    depth = {node: idx for idx, node in enumerate(nodes)}
    if source_col and target_col and edges:
        depth = {node: 0 for node in nodes}
        for _ in range(len(nodes)):
            changed = False
            for src, tgt in edges:
                if src in depth and tgt in depth and depth[tgt] <= depth[src]:
                    depth[tgt] = depth[src] + 1
                    changed = True
            if not changed:
                break
        if max(depth.values(), default=0) > len(nodes):
            depth = {node: idx for idx, node in enumerate(nodes)}

    levels = {}
    for node in nodes:
        levels.setdefault(depth.get(node, 0), []).append(node)
    level_keys = sorted(levels)
    x_positions = np.linspace(0.12, 0.88, max(1, len(level_keys)))
    position = {}
    for depth_idx, level in enumerate(level_keys):
        members = levels[level]
        if len(members) == 1:
            y_positions = [0.52]
        else:
            y_positions = np.linspace(0.75, 0.30, len(members))
        for node, y_pos in zip(members, y_positions):
            position[node] = (float(x_positions[depth_idx]), float(y_pos))

    if standalone:
        fig, ax = plt.subplots(
            figsize=(120 * (1 / 25.4), 72 * (1 / 25.4)),
            constrained_layout=True
        )

    def _arch_text(*args, **kwargs):
        text_artist = ax.text(*args, **kwargs)
        text_artist.set_gid("scifig_inplot_label")
        return text_artist

    colors = palette.get("categorical", ["#2B6CB0", "#D97706", "#0F766E", "#7C3AED", "#DC2626", "#475569"])
    stage_values = []
    for node in nodes:
        stage = meta.get(node, {}).get("stage")
        if pd.notna(stage) and str(stage).strip():
            stage_text = str(stage)
            if stage_text not in stage_values:
                stage_values.append(stage_text)
    if not stage_values:
        stage_values = ["Architecture"]
    stage_color = {stage: colors[idx % len(colors)] for idx, stage in enumerate(stage_values)}

    box_w = min(0.14, max(0.085, 0.72 / max(1, len(level_keys))))
    box_h = 0.150 if max(len(v) for v in levels.values()) <= 2 else 0.115
    label_font = 5.0 if len(level_keys) >= 6 else 5.6
    detail_font = 4.0 if len(level_keys) >= 6 else 4.25
    node_line_len = 9 if len(level_keys) >= 6 else 13

    stage_label_centers = []
    for stage in stage_values:
        stage_nodes = [node for node in nodes if str(meta.get(node, {}).get("stage") or "Architecture") == stage]
        if not stage_nodes:
            continue
        xs = [position[node][0] for node in stage_nodes if node in position]
        if not xs:
            continue
        x0 = max(0.02, min(xs) - box_w * 0.65)
        x1 = min(0.98, max(xs) + box_w * 0.65)
        band = mpatches.FancyBboxPatch(
            (x0, 0.15), x1 - x0, 0.70,
            boxstyle="round,pad=0.008,rounding_size=0.02",
            linewidth=0.55,
            edgecolor=stage_color.get(stage, "#94A3B8"),
            facecolor=stage_color.get(stage, "#94A3B8"),
            alpha=0.08,
            transform=ax.transAxes,
            clip_on=True,
            zorder=0,
        )
        ax.add_patch(band)
        label_center = (x0 + x1) / 2
        if all(abs(label_center - used) > 0.105 for used in stage_label_centers):
            stage_label_centers.append(label_center)
            _arch_text(
                label_center, 0.865, _clean_label(stage, 18),
                ha="center", va="bottom", fontsize=4.8 if len(stage_values) >= 5 else 5.2, fontweight="bold",
                color=stage_color.get(stage, "#475569"), transform=ax.transAxes,
                clip_on=True, zorder=3,
            )

    suppress_dashboard = bool(chartPlan.get("suppressArchitectureDashboard", False))
    dashboard_cols = [] if suppress_dashboard else [col for col in metric_cols if col != params_col][:3]
    show_edge_value_labels = bool(chartPlan.get("showEdgeValueLabels", False) or (len(edges) <= 4 and not dashboard_cols))
    arrow_values = {}
    arrow_widths = {}
    if source_col and target_col and value_col in getattr(df, "columns", []):
        numeric_values = pd.to_numeric(df[value_col], errors="coerce")
        finite_values = numeric_values[np.isfinite(numeric_values)]
        v_min = float(finite_values.min()) if len(finite_values) else None
        v_rng = float(finite_values.max() - finite_values.min()) if len(finite_values) else 0.0
        for _, row in df.iterrows():
            src, tgt = str(row[source_col]), str(row[target_col])
            if src in position and tgt in position:
                arrow_values[(src, tgt)] = row.get(value_col)
                edge_value = pd.to_numeric(pd.Series([row.get(value_col)]), errors="coerce").iloc[0]
                if pd.notna(edge_value) and v_min is not None:
                    scaled = 0.0 if v_rng == 0 else (float(edge_value) - v_min) / v_rng
                    arrow_widths[(src, tgt)] = 0.75 + 1.25 * scaled

    for src, tgt in edges:
        if src not in position or tgt not in position:
            continue
        sx, sy = position[src]
        tx, ty = position[tgt]
        rad = 0.18 if abs(sy - ty) > 0.12 else 0.02
        arrow = mpatches.FancyArrowPatch(
            (sx + box_w / 2, sy), (tx - box_w / 2, ty),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=arrow_widths.get((src, tgt), 0.85),
            color="#334155",
            alpha=0.72,
            connectionstyle=f"arc3,rad={rad}",
            transform=ax.transAxes,
            clip_on=True,
            zorder=1,
        )
        ax.add_patch(arrow)
        edge_value = arrow_values.get((src, tgt))
        if show_edge_value_labels and edge_value is not None and pd.notna(edge_value):
            mx, my = (sx + tx) / 2, (sy + ty) / 2
            _arch_text(
                mx, my + 0.035, _clean_label(edge_value, 10),
                ha="center", va="center", fontsize=4.4, color="#475569",
                transform=ax.transAxes, clip_on=True, zorder=4,
            )

    for idx, node in enumerate(nodes):
        cx, cy = position[node]
        node_meta = meta.get(node, {})
        stage = str(node_meta.get("stage") or "Architecture")
        edge_color = stage_color.get(stage, colors[idx % len(colors)])
        rect = mpatches.FancyBboxPatch(
            (cx - box_w / 2, cy - box_h / 2), box_w, box_h,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            linewidth=1.0,
            edgecolor=edge_color,
            facecolor=edge_color,
            alpha=0.18,
            transform=ax.transAxes,
            clip_on=True,
            zorder=2,
        )
        ax.add_patch(rect)
        _arch_text(
            cx, cy + box_h * 0.16, _wrap_label(node, line_len=node_line_len, max_lines=2),
            ha="center", va="center", fontsize=label_font, fontweight="bold",
            color="#0F172A", transform=ax.transAxes, clip_on=True, zorder=5,
            linespacing=0.95,
        )
        details = []
        if pd.notna(node_meta.get("type")) and str(node_meta.get("type")).strip():
            details.append(_clean_label(node_meta.get("type"), 16))
        if pd.notna(node_meta.get("units")) and str(node_meta.get("units")).strip():
            details.append(f"units={_clean_label(node_meta.get('units'), 10)}")
        if pd.notna(node_meta.get("params")) and str(node_meta.get("params")).strip():
            details.append(f"p={_clean_label(node_meta.get('params'), 10)}")
        if details:
            _arch_text(
                cx, cy - box_h * 0.22, "\n".join(details[:2]),
                ha="center", va="center", fontsize=detail_font, color="#475569",
                transform=ax.transAxes, clip_on=True, zorder=5, linespacing=1.0,
            )

    params_total = None
    if params_col in getattr(df, "columns", []):
        numeric_params = pd.to_numeric(df[params_col], errors="coerce")
        if numeric_params.notna().any():
            params_total = float(numeric_params.sum())
    summary_lines = [f"modules={len(nodes)}", f"edges={len(edges)}"]
    if params_total is not None:
        summary_lines.append(f"params={params_total:.3g}")
    _arch_text(
        0.965, 0.055, "\n".join(summary_lines),
        ha="right", va="bottom", fontsize=5.0, color="#1E293B",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#CBD5E1", linewidth=0.55, alpha=0.94),
        transform=ax.transAxes, clip_on=True, zorder=6,
    )
    if dashboard_cols:
        panel_x, panel_y, panel_w, panel_h = 0.035, 0.045, 0.30, 0.15
        dashboard = mpatches.FancyBboxPatch(
            (panel_x, panel_y), panel_w, panel_h,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=0.55,
            edgecolor="#CBD5E1",
            facecolor="white",
            alpha=0.94,
            transform=ax.transAxes,
            clip_on=True,
            zorder=6,
        )
        ax.add_patch(dashboard)
        _arch_text(
            panel_x + 0.012, panel_y + panel_h - 0.024, "metric dashboard",
            ha="left", va="center", fontsize=4.7, fontweight="bold",
            color="#1E293B", transform=ax.transAxes, clip_on=True, zorder=7,
        )
        for idx, col in enumerate(dashboard_cols):
            numeric = pd.to_numeric(df[col], errors="coerce")
            value = float(numeric.mean()) if numeric.notna().any() else 0.0
            denom = max(float(np.nanmax(np.abs(numeric))) if numeric.notna().any() else 1.0, abs(value), 1.0)
            frac = min(1.0, abs(value) / denom)
            y_pos = panel_y + panel_h - 0.050 - idx * 0.035
            label = _clean_label(str(col).replace("_", " "), 13)
            _arch_text(
                panel_x + 0.012, y_pos, label,
                ha="left", va="center", fontsize=4.2, color="#475569",
                transform=ax.transAxes, clip_on=True, zorder=7,
            )
            ax.add_patch(mpatches.Rectangle(
                (panel_x + 0.115, y_pos - 0.006), 0.145, 0.012,
                facecolor="#E2E8F0", edgecolor="none",
                transform=ax.transAxes, clip_on=True, zorder=7,
            ))
            ax.add_patch(mpatches.Rectangle(
                (panel_x + 0.115, y_pos - 0.006), 0.145 * frac, 0.012,
                facecolor=colors[idx % len(colors)], edgecolor="none",
                alpha=0.75,
                transform=ax.transAxes, clip_on=True, zorder=8,
            ))
            _arch_text(
                panel_x + panel_w - 0.012, y_pos, f"{value:.2g}",
                ha="right", va="center", fontsize=4.2, color="#1E293B",
                transform=ax.transAxes, clip_on=True, zorder=8,
            )
        visual_plan = chartPlan.get("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
        if callable(globals().get("_visual_count")):
            _visual_count(visual_plan, "metricTableCount")
        if callable(globals().get("_record_template_motif")):
            _record_template_motif(visual_plan, "architecture_metric_dashboard")
    if chartPlan.get("drawInternalTitle", False):
        title = chartPlan.get("title") or "AI model architecture"
        title_text = str(title).strip()
        if len(title_text) > 42:
            title_text = title_text[:41] + "..."
        _arch_text(
            0.02, 0.955, title_text,
            ha="left", va="top", fontsize=7.2, fontweight="bold", color="#0F172A",
            transform=ax.transAxes, clip_on=True, zorder=6,
        )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    if standalone:
        apply_chart_polish(ax, "model_architecture")
    return ax


def gen_model_architecture_board(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Architecture plus metric storyboard for AI/ML source-target tables.

    Use when topology rows also contain latency, FLOPs, memory, throughput,
    cost, edge_weight, or parameter columns. The board promotes the metric
    evidence into real support axes instead of compressing everything into
    labels inside the topology panel.
    """
    import numpy as np
    import pandas as pd

    standalone = ax is None
    plt.rcParams.update(rcParams)
    if df is None or not len(df):
        raise ValueError("model_architecture_board requires architecture rows")
    if standalone:
        fig, ax = plt.subplots(figsize=(183 / 25.4, 118 / 25.4), constrained_layout=False)
    else:
        fig = ax.figure

    roles = dataProfile.get("semanticRoles", {}) if isinstance(dataProfile, dict) else {}

    def _pick_col(*role_names, tokens=()):
        for role_name in role_names:
            candidate = roles.get(role_name)
            if candidate in getattr(df, "columns", []):
                return candidate
        lower_to_col = {str(col).lower(): col for col in getattr(df, "columns", [])}
        for token in tokens:
            if token in lower_to_col:
                return lower_to_col[token]
        for col in getattr(df, "columns", []):
            lowered = str(col).lower()
            if any(token in lowered for token in tokens):
                return col
        return None

    def _short(value, max_len=18):
        text = str(value).replace("_", " ").strip()
        if not text or text.lower() in ("nan", "none"):
            return "metric"
        return text if len(text) <= max_len else text[:max_len - 1] + "..."

    source_col = _pick_col("source", "from", tokens=("source", "from", "input"))
    target_col = _pick_col("target", "to", tokens=("target", "to", "output"))
    params_col = _pick_col("params", "parameters", tokens=("params", "parameters", "n_params"))
    metric_tokens = (
        "latency", "flops", "memory", "throughput", "cost", "score",
        "accuracy", "auc", "f1", "params", "parameters", "weight",
    )
    metric_cols = []
    for col in getattr(df, "columns", []):
        lowered = str(col).lower()
        if col in {source_col, target_col}:
            continue
        if any(token in lowered for token in metric_tokens):
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().any():
                metric_cols.append(col)

    ax.set_axis_off()
    arch_ax = ax.inset_axes([0.025, 0.345, 0.95, 0.61])
    metric_ax = ax.inset_axes([0.045, 0.070, 0.425, 0.205])
    edge_ax = ax.inset_axes([0.545, 0.070, 0.405, 0.205])
    for sub_ax in (arch_ax, metric_ax, edge_ax):
        sub_ax.set_facecolor("#FFFFFF")
        for spine in sub_ax.spines.values():
            spine.set_edgecolor("#CBD5E1")
            spine.set_linewidth(0.55)

    arch_plan = dict(chartPlan)
    arch_plan["suppressArchitectureDashboard"] = True
    arch_plan.setdefault("drawInternalTitle", False)
    gen_model_architecture(df, dataProfile, arch_plan, rcParams, palette, col_map=col_map, ax=arch_ax)

    colors = palette.get("categorical", ["#2B6CB0", "#D97706", "#0F766E", "#7C3AED"])
    dashboard_cols = metric_cols[:4]
    if dashboard_cols:
        labels = [_short(col, 16) for col in dashboard_cols]
        means = []
        fractions = []
        for col in dashboard_cols:
            numeric = pd.to_numeric(df[col], errors="coerce")
            value = float(numeric.mean()) if numeric.notna().any() else 0.0
            denom = max(float(np.nanmax(np.abs(numeric))) if numeric.notna().any() else 1.0, abs(value), 1.0)
            means.append(value)
            fractions.append(min(1.0, abs(value) / denom))
        y = np.arange(len(labels))
        metric_ax.barh(y, fractions, color=[colors[i % len(colors)] for i in range(len(labels))], alpha=0.78)
        metric_ax.set_yticks(y)
        metric_ax.set_yticklabels(labels, fontsize=5.1)
        metric_ax.invert_yaxis()
        metric_ax.set_xlim(0, 1.18)
        metric_ax.set_xticks([])
        metric_ax.set_title("b  metric profile", loc="left", fontsize=6.1, fontweight="bold", pad=2)
        for yi, value in zip(y, means):
            metric_ax.text(
                0.86, yi, f"{value:.2g}",
                va="center", ha="right", fontsize=4.8, color="#1E293B", clip_on=True,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, pad=0.35),
            )
    else:
        metric_ax.text(0.5, 0.56, "b  metric profile", ha="center", va="center",
                       fontsize=6.1, fontweight="bold", transform=metric_ax.transAxes)
        metric_ax.text(0.5, 0.38, "no numeric metric columns", ha="center", va="center",
                       fontsize=5.0, color="#64748B", transform=metric_ax.transAxes)
        metric_ax.set_xticks([])
        metric_ax.set_yticks([])

    edge_metric = None
    for token in ("edge_weight", "weight", "latency", "flops", "memory", "throughput"):
        for col in metric_cols:
            if token in str(col).lower():
                edge_metric = col
                break
        if edge_metric:
            break
    if not edge_metric and metric_cols:
        edge_metric = metric_cols[0]

    if source_col and target_col and edge_metric:
        edge_df = df[[source_col, target_col, edge_metric]].copy()
        edge_df[edge_metric] = pd.to_numeric(edge_df[edge_metric], errors="coerce")
        edge_df = edge_df.dropna(subset=[source_col, target_col, edge_metric]).head(8)
    else:
        edge_df = pd.DataFrame()

    if not edge_df.empty:
        labels = [
            _short(f"{row[source_col]} -> {row[target_col]}", 20)
            for _, row in edge_df.iterrows()
        ]
        values = edge_df[edge_metric].astype(float).to_numpy()
        y = np.arange(len(labels))
        edge_ax.barh(y, values, color="#334155", alpha=0.72)
        edge_ax.set_yticks(y)
        edge_ax.set_yticklabels(labels, fontsize=4.8)
        edge_ax.invert_yaxis()
        edge_ax.tick_params(axis="x", labelsize=4.6, length=2)
        edge_ax.set_title(f"c  edge signal: {_short(edge_metric, 14)}", loc="left",
                          fontsize=6.1, fontweight="bold", pad=2)
        limit = max([abs(float(v)) for v in values] + [1.0])
        edge_ax.set_xlim(0, limit * 1.18)
    else:
        edge_ax.text(0.5, 0.56, "c  edge signal", ha="center", va="center",
                     fontsize=6.1, fontweight="bold", transform=edge_ax.transAxes)
        edge_ax.text(0.5, 0.38, "source-target metric unavailable", ha="center", va="center",
                     fontsize=5.0, color="#64748B", transform=edge_ax.transAxes)
        edge_ax.set_xticks([])
        edge_ax.set_yticks([])

    ax.text(0.025, 0.975, "a  architecture topology", ha="left", va="top",
            fontsize=7.0, fontweight="bold", color="#0F172A", transform=ax.transAxes)
    visual_plan = chartPlan.get("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
    if callable(globals().get("_record_template_motif")):
        _record_template_motif(visual_plan, "neural_architecture_topology")
        _record_template_motif(visual_plan, "architecture_metric_dashboard")
        _record_template_motif(visual_plan, "architecture_metric_storyboard")
    if callable(globals().get("_visual_count")):
        _visual_count(visual_plan, "metricTableCount")
    return ax


def gen_parallel_coordinates(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Parallel coordinates plot for multivariate profiles.

    Each row becomes a polyline across numeric columns.  Semantic roles:
      - group: categorical column used for colouring lines
      - value / feature_id are optional; all numeric columns are used.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    group_col, _, _ = _resolve_roles(dataProfile)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("parallel_coordinates requires at least 2 numeric columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    # Normalize each column to [0, 1]
    normed = df[numeric_cols].copy()
    for c in numeric_cols:
        rng = normed[c].max() - normed[c].min()
        normed[c] = (normed[c] - normed[c].min()) / (rng if rng != 0 else 1)

    x = np.arange(len(numeric_cols))

    if group_col and group_col in df.columns:
        categories = df[group_col].unique()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            mask = df[group_col] == cat
            for _, row in normed.loc[mask].iterrows():
                ax.plot(x, row.values, color=color_map[cat], alpha=0.35, lw=0.5)
        # Legend proxy
        for cat in categories:
            ax.plot([], [], color=color_map[cat], label=str(cat), lw=1.5)
        ax.legend(fontsize=5, frameon=False, loc="upper right")
    else:
        for _, row in normed.iterrows():
            ax.plot(x, row.values, color="#999999", alpha=0.35, lw=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(numeric_cols, rotation=30, ha="right", fontsize=5)
    ax.set_ylabel("Normalized value")
    ax.set_xlim(x[0], x[-1])
    if standalone:
        apply_chart_polish(ax, "parallel_coordinates")
    return ax


def gen_pathway_map(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Pathway enrichment bubble chart.

    x=enrichment score, y=pathway name, size=gene count, color=-log10(p).
    Expects columns: pathway, enrichment_score, gene_count, p_value in semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pathway_col = roles.get("pathway") or roles.get("group") or roles.get("y")
    score_col = roles.get("enrichment_score") or roles.get("x") or roles.get("value")
    count_col = roles.get("gene_count") or roles.get("size")
    pval_col = roles.get("p_value") or roles.get("color")

    if pathway_col is None or score_col is None:
        raise ValueError("pathway_map requires 'pathway' and 'enrichment_score' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(60, 12 * len(df) + 20) * (1 / 25.4)),
                           constrained_layout=True)

    nlogp = -np.log10(df[pval_col].clip(lower=1e-300)) if pval_col and pval_col in df.columns else np.ones(len(df))
    sizes = df[count_col] * 8 if count_col and count_col in df.columns else np.full(len(df), 40)
    cmap = plt.cm.YlOrRd

    scatter = ax.scatter(df[score_col], df[pathway_col], s=sizes, c=nlogp,
                         cmap=cmap, alpha=0.7, edgecolor="white", linewidth=0.4)
    cbar = ax.figure.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label(r"$-\log_{10}(p)$", fontsize=5)
    cbar.ax.tick_params(labelsize=4)

    ax.set_xlabel("Enrichment score")
    ax.set_ylabel("")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "pathway_map")
    return ax


def gen_sankey(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified Sankey diagram showing flow between stages using matplotlib patches.

    Expects columns: source (origin stage), target (destination stage), and
    value (flow magnitude) in semanticRoles.  Draws horizontal node bars at
    left/right with filled bezier-like flow ribbons connecting them.
    Nature style: no grid, open-L spines, publication fonts.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    src_col = roles.get("source") or roles.get("group")
    tgt_col = roles.get("target") or roles.get("x")
    val_col = roles.get("value") or roles.get("y")

    if src_col is None or tgt_col is None or val_col is None:
        raise ValueError("sankey requires 'source', 'target', and 'value' in semanticRoles")

    flows = df[[src_col, tgt_col, val_col]].dropna()
    sources = flows[src_col].unique().tolist()
    targets = flows[tgt_col].unique().tolist()

    fallback = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                            "#C8553D", "#7A6C8F", "#2B6F77"])
    all_nodes = list(dict.fromkeys(sources + targets))
    color_map = {n: fallback[i % len(fallback)] for i, n in enumerate(all_nodes)}

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 80 * (1 / 25.4)),
                           constrained_layout=True)

    # Node heights proportional to total flow through each node
    node_totals = {}
    for _, row in flows.iterrows():
        node_totals[row[src_col]] = node_totals.get(row[src_col], 0) + row[val_col]
        node_totals[row[tgt_col]] = node_totals.get(row[tgt_col], 0) + row[val_col]
    max_total = max(node_totals.values()) if node_totals else 1

    # Position source nodes on left, target nodes on right
    y_src, y_tgt = {}, {}
    src_gap, tgt_gap = 0.05, 0.05
    src_y = 0.0
    for s in sources:
        h = node_totals.get(s, 1) / max_total * 0.8
        y_src[s] = (src_y, src_y + h)
        src_y += h + src_gap
    tgt_y = 0.0
    for t in targets:
        h = node_totals.get(t, 1) / max_total * 0.8
        y_tgt[t] = (tgt_y, tgt_y + h)
        tgt_y += h + tgt_gap

    # Draw node bars
    for n, (y0, y1) in {**y_src, **y_tgt}.items():
        x = 0.0 if n in y_src else 1.0
        ax.barh((y0 + y1) / 2, 0.03, height=y1 - y0, left=x - 0.015,
                color=color_map[n], edgecolor="none", alpha=0.85, zorder=3)
        ax.text(x + (0.06 if n in y_src else -0.06), (y0 + y1) / 2, n,
                fontsize=5, ha="left" if n in y_src else "right", va="center")

    # Draw flow bands as filled bezier-like polygons
    src_offset = {s: y_src[s][0] for s in sources}
    tgt_offset = {t: y_tgt[t][0] for t in targets}
    for _, row in flows.iterrows():
        s, t, v = row[src_col], row[tgt_col], row[val_col]
        band_h = v / max_total * 0.8
        sy0, ty0 = src_offset[s], tgt_offset[t]
        src_offset[s] += band_h
        tgt_offset[t] += band_h
        xs = [0.0, 0.0, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0]
        ys = [sy0, sy0 + band_h, sy0 + band_h, ty0 + band_h,
              ty0 + band_h, ty0, ty0, sy0, sy0]
        ax.fill(xs, ys, color=color_map[s], alpha=0.3, linewidth=0)

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.05, max(src_y, tgt_y) + 0.05)
    ax.axis("off")
    ax.set_title(chartPlan.get("title", ""), fontsize=7, pad=8)
    if standalone:
        apply_chart_polish(ax, "sankey")
    return ax
