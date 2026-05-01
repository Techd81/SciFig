# Relationship / Psychology / Social Chart Generators

> Extracted from phases/03-code-gen-style.md. Read this file when the coordinator needs relationship, psychology, or social science chart generator implementations.

### Relationship / Psychology / Social chart generators

```python
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


def gen_mediation_path(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mediation path diagram: X -> M -> Y with path coefficients.

    Semantic roles:
      - x: independent variable (column name or computed summary key)
      - mediator: mediating variable column
      - y: dependent variable column
    Coefficients are computed as standardized betas via OLS.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
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


def gen_interaction_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Interaction plot for factorial designs: lines connecting cell means.

    Semantic roles:
      - x: primary factor (x-axis categories)
      - group: secondary factor (separate lines)
      - value: numeric outcome variable
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")

    if not all([x_col, group_col, value_col]):
        raise ValueError("interaction_plot requires 'x', 'group', and 'value' in semanticRoles")

    cell_means = df.groupby([x_col, group_col])[value_col].mean().unstack()
    cell_sems = df.groupby([x_col, group_col])[value_col].sem().unstack()

    categories = cell_means.columns.tolist()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    x_positions = np.arange(len(cell_means.index))
    for cat in categories:
        means = cell_means[cat].values
        sems = cell_sems[cat].values
        ax.errorbar(x_positions, means, yerr=sems,
                     marker="o", markersize=4, linewidth=1,
                     color=color_map[cat], label=str(cat),
                     capsize=2, capthick=0.5, elinewidth=0.5)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(cell_means.index, fontsize=5.5)
    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    ax.legend(title=group_col, fontsize=5, title_fontsize=5.5,
              frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "interaction_plot")
    return ax


def gen_mosaic_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mosaic plot for categorical associations: area-proportional stacked bars.

    Semantic roles:
      - x: primary categorical variable (columns)
      - group: secondary categorical variable (segments within columns)
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    group_col = roles.get("group")

    if not all([x_col, group_col]):
        raise ValueError("mosaic_plot requires 'x' and 'group' in semanticRoles")

    ct = pd.crosstab(df[x_col], df[group_col])
    row_totals = ct.sum(axis=1)
    grand_total = ct.values.sum()

    categories_g = ct.columns.tolist()
    color_map = _extract_colors(palette, categories_g)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    x_pos = 0.0
    bar_gap = 0.02
    bar_width_avail = 1.0 - (len(ct.index) - 1) * bar_gap

    for i, xcat in enumerate(ct.index):
        col_width = (row_totals[xcat] / grand_total) * bar_width_avail
        y_pos = 0.0
        for gcat in categories_g:
            seg_height = ct.loc[xcat, gcat] / row_totals[xcat]
            ax.bar(x_pos + col_width / 2, seg_height, width=col_width,
                   bottom=y_pos, color=color_map[gcat],
                   edgecolor="white", linewidth=0.5)
            if seg_height > 0.05:
                ax.text(x_pos + col_width / 2, y_pos + seg_height / 2,
                        str(ct.loc[xcat, gcat]), ha="center", va="center",
                        fontsize=4.5, color="white", fontweight="bold")
            y_pos += seg_height
        x_pos += col_width + bar_gap

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_ylabel(f"P({group_col})")
    ax.set_xticks([])
    # Legend
    for gcat in categories_g:
        ax.bar(0, 0, color=color_map[gcat], label=str(gcat))
    ax.legend(title=group_col, fontsize=5, title_fontsize=5.5,
              frameon=False, loc="upper right")
    if standalone:
        apply_chart_polish(ax, "mosaic_plot")
    return ax


def gen_diverging_bar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Diverging bar chart: bars extending left/right from a center zero line.

    Semantic roles:
      - group: category labels (y-axis)
      - value: numeric scores (positive = right, negative = left)
      - feature_id: optional second category for colouring
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")
    color_col = roles.get("feature_id")

    if group_col is None or value_col is None:
        raise ValueError("diverging_bar requires 'group' and 'value' in semanticRoles")

    df_sorted = df.sort_values(value_col, ascending=True).reset_index(drop=True)
    n = len(df_sorted)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(50, n * 4) * (1 / 25.4)),
                           constrained_layout=True)

    fallback = palette.get("categorical",
                            ["#0072B2", "#E69F00", "#56B4E9", "#009E73"])

    if color_col and color_col in df.columns:
        color_cats = df_sorted[color_col].unique()
        color_map = _extract_colors(palette, color_cats)
        bar_colors = [color_map[c] for c in df_sorted[color_col]]
    else:
        bar_colors = [fallback[0] if v >= 0 else fallback[3]
                      for v in df_sorted[value_col]]

    y_pos = np.arange(n)
    ax.barh(y_pos, df_sorted[value_col].values, height=0.65,
            color=bar_colors, edgecolor="white", linewidth=0.3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[group_col].values, fontsize=5)
    # Center divider — delegate to template_mining_helpers when reachable
    canonical_zero_ref = globals().get("add_zero_reference")
    if canonical_zero_ref is not None:
        try:
            canonical_zero_ref(ax, axis="x", color="black", lw=0.6, ls="-", zorder=1)
        except Exception:
            ax.axvline(0, color="black", lw=0.6)
    else:
        ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel(value_col)
    if standalone:
        apply_chart_polish(ax, "diverging_bar")
    return ax


def gen_heatmap_symmetric(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Symmetric heatmap with identical upper and lower triangles.

    Expects a square correlation/distance matrix or long-format data that can
    be pivoted into one.  Semantic roles:
      - feature_id: row labels column
      - group: column labels column
      - value: cell value column
    Falls back to correlation matrix of all numeric columns.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    row_col = roles.get("feature_id")
    col_col = roles.get("group")
    val_col = roles.get("value")

    if row_col and col_col and val_col:
        mat = df.pivot_table(index=row_col, columns=col_col,
                             values=val_col, aggfunc="mean").fillna(0)
    else:
        numeric = df.select_dtypes(include="number")
        if len(numeric.columns) < 2:
            raise ValueError("heatmap_symmetric requires at least 2 numeric columns or pivot roles")
        mat = numeric.corr()

    # Make symmetric if not already
    labels = mat.columns.tolist()
    M = mat.values
    symmetric = (M + M.T) / 2.0
    np.fill_diagonal(symmetric, 1.0)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    # Diverging norm centered at 0 — matches red_blue_correlation palette anchor
    try:
        from matplotlib.colors import TwoSlopeNorm
        m_min = float(np.nanmin(symmetric))
        m_max = float(np.nanmax(symmetric))
        vmin = min(-1.0, m_min) if np.isfinite(m_min) else -1.0
        vmax = max(1.0, m_max) if np.isfinite(m_max) else 1.0
        if vmin >= 0.0:
            vmin = -vmax if vmax > 0 else -1.0
        if vmax <= 0.0:
            vmax = -vmin if vmin < 0 else 1.0
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)
        sns.heatmap(symmetric, ax=ax, cmap="RdBu_r", norm=norm,
                    xticklabels=labels, yticklabels=labels,
                    linewidths=0.3, annot=symmetric.shape[0] <= 12,
                    fmt=".2f", annot_kws={"size": 4.5},
                    cbar_kws={"shrink": 0.6, "label": "Value"})
    except Exception:
        sns.heatmap(symmetric, ax=ax, cmap="RdBu_r", center=0,
                    vmin=-1, vmax=1,
                    xticklabels=labels, yticklabels=labels,
                    linewidths=0.3, annot=symmetric.shape[0] <= 12,
                    fmt=".2f", annot_kws={"size": 4.5},
                    cbar_kws={"shrink": 0.6, "label": "Value"})
    ax.tick_params(labelsize=5)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    if standalone:
        apply_chart_polish(ax, "heatmap_symmetric")
    return ax


def gen_violin_grouped(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Grouped violin plot: multiple violins per group for factorial comparisons.

    Semantic roles:
      - x: primary grouping factor (x-axis categories)
      - group: secondary grouping factor (violins within each x category)
      - value: numeric outcome variable
    Falls back to _resolve_roles if 'x' is absent: uses 'group' as x and
    splits by a second categorical column if available.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("condition")
    hue_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")

    if not all([x_col, hue_col, value_col]):
        # Fallback: try _resolve_roles and look for a second categorical
        group_col, val_col, alt_x = _resolve_roles(dataProfile)
        if group_col and val_col:
            other_cats = [c for c in df.select_dtypes(include="object").columns
                          if c != group_col]
            if other_cats:
                x_col = other_cats[0]
                hue_col = group_col
                value_col = val_col
            else:
                raise ValueError("violin_grouped requires 'x', 'group', and 'value' "
                                 "in semanticRoles")

    categories = df[hue_col].unique()
    color_map = _extract_colors(palette, categories)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    sns.violinplot(data=df, x=x_col, y=value_col, hue=hue_col,
                   palette=color_map, width=0.7, inner="quartile",
                   linewidth=0.5, ax=ax, dodge=True)

    ax.set_xlabel(x_col)
    ax.set_ylabel(value_col)
    ax.legend(title=hue_col, fontsize=5, title_fontsize=5.5,
              frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    if standalone:
        apply_chart_polish(ax, "violin_grouped")
    return ax


def gen_line(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simple line chart for ordered time, dose, or index trends."""
    standalone = ax is None
    import numpy as np
    import pandas as pd
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("time") or roles.get("dose") or roles.get("condition")
    y_col = roles.get("value") or roles.get("y") or roles.get("response")
    group_col = roles.get("group")
    columns_lower = {str(c).lower(): c for c in df.columns}
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    is_incremental_ml = (
        template_case.get("bundleKey") == "incremental_feature_selection_curve"
        or "incremental_feature_selection" in patterns
        or "feature_selection" in patterns
        or any(token in columns_lower for token in ("n_features", "top_k", "feature_count", "ablation"))
    )

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if is_incremental_ml:
        x_candidates = ["n_features", "top_k", "feature_count", "ablation"]
        metric_candidates = ["auc", "accuracy", "f1", "r2", "score", "mae", "rmse", "mse", "error"]
        x_col = x_col or next((columns_lower[c] for c in x_candidates if c in columns_lower), None)
        y_col = y_col or next((columns_lower[c] for c in metric_candidates if c in columns_lower), None)
        group_col = group_col or roles.get("model") or roles.get("algorithm") or columns_lower.get("model") or columns_lower.get("algorithm")
    if y_col is None:
        y_col = numeric_cols[-1] if numeric_cols else None
    if y_col is None:
        raise ValueError("line requires a numeric 'value' or 'y' column")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    fallback = palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541"])
    if is_incremental_ml and x_col and x_col in df.columns:
        score_name = str(y_col).lower()
        lower_is_better = any(token in score_name for token in ("rmse", "mae", "mse", "error", "loss"))
        color_map = _extract_colors(palette, df[group_col].dropna().unique()) if group_col and group_col in df.columns else {}
        groups = [(None, df)] if not group_col or group_col not in df.columns else list(df.groupby(group_col))
        marker_cycle = ["o", "s", "^", "D", "v", "P", "X", "*"]

        def _final_score(item):
            _, grp = item
            ordered = grp.sort_values(x_col)
            vals = pd.to_numeric(ordered[y_col], errors="coerce").dropna()
            return vals.iloc[-1] if len(vals) else np.nan

        def _decision_point(grp):
            ordered = grp.sort_values(x_col).copy()
            ordered[x_col] = pd.to_numeric(ordered[x_col], errors="coerce")
            ordered[y_col] = pd.to_numeric(ordered[y_col], errors="coerce")
            ordered = ordered.dropna(subset=[x_col, y_col])
            if len(ordered) < 3:
                return ordered.iloc[-1] if len(ordered) else None
            y_vals = ordered[y_col].to_numpy(dtype=float)
            if lower_is_better:
                gains = y_vals[:-1] - y_vals[1:]
                total_gain = y_vals[0] - np.nanmin(y_vals)
                if total_gain > 0:
                    target = y_vals[0] - total_gain * 0.95
                    matches = np.where(y_vals <= target)[0]
                    if len(matches):
                        return ordered.iloc[int(matches[0])]
            else:
                gains = y_vals[1:] - y_vals[:-1]
                total_gain = np.nanmax(y_vals) - y_vals[0]
                if total_gain > 0:
                    target = y_vals[0] + total_gain * 0.95
                    matches = np.where(y_vals >= target)[0]
                    if len(matches):
                        return ordered.iloc[int(matches[0])]
            if len(gains) == 0:
                return ordered.iloc[-1]
            positive = gains[gains > 0]
            threshold = max(float(np.nanmax(positive)) * 0.18, 1e-12) if len(positive) else 1e-12
            elbow_offset = next((idx + 1 for idx, gain in enumerate(gains) if gain <= threshold), int(np.nanargmax(y_vals) if not lower_is_better else np.nanargmin(y_vals)))
            elbow_offset = min(max(elbow_offset, 0), len(ordered) - 1)
            return ordered.iloc[elbow_offset]

        groups = sorted(groups, key=_final_score, reverse=not lower_is_better)
        decision_source = None
        for i, (name, grp) in enumerate(groups):
            ordered = grp.sort_values(x_col)
            label = "feature path" if name is None else str(name)
            is_rf = any(token in label.lower() for token in ("random forest", "rf", "rfr"))
            if decision_source is None or is_rf:
                decision_source = (label, ordered)
            ax.plot(
                ordered[x_col], ordered[y_col],
                marker="o" if is_rf else marker_cycle[i % len(marker_cycle)],
                markersize=4 if is_rf else 3,
                lw=1.9 if is_rf else 0.9,
                alpha=1.0 if is_rf else 0.74,
                color=color_map.get(name, fallback[i % len(fallback)]),
                label=label,
                zorder=4 if is_rf else 2,
                markeredgecolor="#111111" if is_rf else "white",
                markeredgewidth=0.45,
            )
        if decision_source is not None:
            decision_label, decision_grp = decision_source
            decision_row = _decision_point(decision_grp)
        else:
            decision_label, decision_row = "feature path", _decision_point(df)
        if decision_row is not None:
            best_x = decision_row[x_col]
            best_y = decision_row[y_col]
            ax.axvline(best_x, color="#444444", lw=0.75, ls="--", alpha=0.72, zorder=1)
            ax.axhline(best_y, color="#444444", lw=0.65, ls="--", alpha=0.48, zorder=1)
            ax.scatter([best_x], [best_y], s=42, color="#B00000", edgecolor="white", linewidth=0.55, zorder=5)
            callout_x = 0.98 if standalone else 0.04
            callout_ha = "right" if standalone else "left"
            ax.text(
                callout_x, 0.06, f"best {x_col}={best_x:g}\n{decision_label[:14]} {best_y:.3g}",
                transform=ax.transAxes, ha=callout_ha, va="bottom", fontsize=5.2, color="#111111",
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.45, alpha=0.92),
                zorder=6,
            )
        ax.xaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25, zorder=0)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25, zorder=0)
        ax.set_xlabel(_display_col(x_col, col_map))
        ax.set_ylabel(_display_col(y_col, col_map) if standalone else "")
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=min(4, len(labels)),
                      frameon=False, fontsize=5)
        if ax.figure is not None:
            try:
                if hasattr(ax.figure, "set_layout_engine"):
                    ax.figure.set_layout_engine(None)
                else:
                    ax.figure.set_constrained_layout(False)
            except Exception:
                pass
            sp = ax.figure.subplotpars
            ax.figure.subplots_adjust(left=max(sp.left, 0.16), bottom=max(sp.bottom, 0.26), right=min(sp.right, 0.94))
    elif x_col is None:
        x_vals = np.arange(len(df))
        if group_col and group_col in df.columns:
            color_map = _extract_colors(palette, df[group_col].dropna().unique())
            for i, (name, grp) in enumerate(df.groupby(group_col)):
                ordered = grp.reset_index(drop=True)
                ax.plot(np.arange(len(ordered)), ordered[y_col], marker="o", markersize=3,
                        lw=0.9, color=color_map.get(name, fallback[i % len(fallback)]),
                        label=str(name))
        else:
            ax.plot(x_vals, df[y_col], marker="o", markersize=3, lw=0.9, color=fallback[0])
        ax.set_xlabel("Index")
    elif group_col and group_col in df.columns:
        color_map = _extract_colors(palette, df[group_col].dropna().unique())
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            ordered = grp.sort_values(x_col)
            ax.plot(ordered[x_col], ordered[y_col], marker="o", markersize=3,
                    lw=0.9, color=color_map.get(name, fallback[i % len(fallback)]),
                    label=str(name))
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
                  frameon=False, fontsize=5)
        ax.set_xlabel(_display_col(x_col, col_map))
    else:
        ordered = df.sort_values(x_col)
        ax.plot(ordered[x_col], ordered[y_col], marker="o", markersize=3,
                lw=0.9, color=fallback[0])
        ax.set_xlabel(_display_col(x_col, col_map))

    ax.set_ylabel(_display_col(y_col, col_map))
    if standalone:
        apply_chart_polish(ax, "line")
    return ax


def gen_training_curve(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Neural-network training history with validation gap and best-epoch callout."""
    standalone = ax is None
    import numpy as np
    import pandas as pd
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    columns_lower = {str(c).lower(): c for c in df.columns}
    display = globals().get("_display_col", lambda col, mapping=None: str(col))

    def _col(*names):
        for name in names:
            if name in roles and roles[name] in df.columns:
                return roles[name]
        for name in names:
            key = str(name).lower()
            if key in columns_lower:
                return columns_lower[key]
        return None

    epoch_col = _col("epoch", "epochs", "step", "iteration", "iter", "batch", "x", "time")
    metric_role = _col("metric")
    value_col = _col("value", "score", "y")
    split_col = _col("split", "phase", "subset", "group")
    model_col = _col("model", "run", "fold", "seed", "optimizer")
    if epoch_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        epoch_col = numeric_cols[0] if numeric_cols else None
    if epoch_col is None:
        raise ValueError("training_curve requires an epoch, step, or iteration column")

    work = df.copy()
    metric_cols = []
    if metric_role and value_col and metric_role in work.columns and value_col in work.columns:
        index_cols = [epoch_col]
        if split_col and split_col in work.columns:
            index_cols.append(split_col)
        if model_col and model_col in work.columns:
            index_cols.append(model_col)
        wide = work.pivot_table(index=index_cols, columns=metric_role, values=value_col, aggfunc="mean").reset_index()
        wide.columns = [str(c) for c in wide.columns]
        work = wide
        columns_lower = {str(c).lower(): c for c in work.columns}

    def _match_cols(tokens, exclude=()):
        matches = []
        for col in work.columns:
            key = str(col).lower()
            if col == epoch_col or col in exclude:
                continue
            if not pd.api.types.is_numeric_dtype(work[col]):
                continue
            if any(token in key for token in tokens):
                matches.append(col)
        return matches

    loss_cols = _match_cols(("loss", "cross_entropy", "ce"), exclude=(value_col,))
    score_cols = _match_cols(("accuracy", "acc", "auc", "f1", "precision", "recall"), exclude=(value_col,))
    preferred = [
        "train_loss", "training_loss", "loss", "val_loss", "validation_loss", "test_loss",
        "train_accuracy", "training_accuracy", "accuracy", "val_accuracy", "validation_accuracy",
        "val_auc", "auc", "f1", "val_f1",
    ]
    ordered = []
    for key in preferred:
        col = columns_lower.get(key)
        if col in loss_cols + score_cols and col not in ordered:
            ordered.append(col)
    for col in loss_cols + score_cols:
        if col not in ordered:
            ordered.append(col)
    metric_cols = ordered[:6]
    if not metric_cols:
        numeric_cols = [c for c in work.select_dtypes(include="number").columns if c != epoch_col]
        metric_cols = numeric_cols[:4]
    if not metric_cols:
        raise ValueError("training_curve requires loss, accuracy, auc, f1, or numeric metric columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(105 * (1 / 25.4), 72 * (1 / 25.4)),
                               constrained_layout=True)

    fallback = palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541", "#7A6C8F", "#2B6F77"])
    line_styles = ["-", "--", "-.", ":", "-", "--"]
    ordered_work = work.sort_values(epoch_col)
    x = pd.to_numeric(ordered_work[epoch_col], errors="coerce").to_numpy(dtype=float)
    finite_x = np.isfinite(x)
    x = x[finite_x]
    line_records = []
    for idx, col in enumerate(metric_cols):
        y = pd.to_numeric(ordered_work[col], errors="coerce").to_numpy(dtype=float)[finite_x]
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 2:
            continue
        key = str(col).lower()
        is_validation = any(token in key for token in ("val", "valid", "test"))
        is_score = any(token in key for token in ("acc", "auc", "f1", "precision", "recall"))
        color = fallback[idx % len(fallback)]
        lw = 1.25 if is_validation else 0.95
        marker = "o" if is_validation else None
        markevery = max(1, int(mask.sum() / 7))
        ax.plot(
            x[mask], y[mask],
            color=color,
            lw=lw,
            ls=line_styles[idx % len(line_styles)],
            marker=marker,
            markersize=2.8,
            markevery=markevery,
            label=display(col, col_map),
            alpha=0.96 if is_validation else 0.78,
            zorder=4 if is_validation else 3,
        )
        line_records.append((col, key, x[mask], y[mask], is_score, color))

    train_loss_col = next((col for col in metric_cols if "loss" in str(col).lower() and not any(t in str(col).lower() for t in ("val", "valid", "test"))), None)
    val_loss_col = next((col for col in metric_cols if "loss" in str(col).lower() and any(t in str(col).lower() for t in ("val", "valid", "test"))), None)
    if train_loss_col and val_loss_col:
        train = pd.to_numeric(ordered_work[train_loss_col], errors="coerce").to_numpy(dtype=float)[finite_x]
        val = pd.to_numeric(ordered_work[val_loss_col], errors="coerce").to_numpy(dtype=float)[finite_x]
        gap_mask = np.isfinite(x) & np.isfinite(train) & np.isfinite(val)
        if gap_mask.sum() >= 2:
            ax.fill_between(x[gap_mask], train[gap_mask], val[gap_mask],
                            color="#B00000", alpha=0.08, linewidth=0, label="generalization gap")

    decision = None
    if val_loss_col:
        y = pd.to_numeric(ordered_work[val_loss_col], errors="coerce").to_numpy(dtype=float)[finite_x]
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.any():
            pos = int(np.nanargmin(y[mask]))
            decision = ("best val loss", x[mask][pos], y[mask][pos], "#B00000")
    if decision is None:
        score_records = [rec for rec in line_records if rec[4]]
        if score_records:
            col, key, xs, ys, _, color = score_records[-1]
            pos = int(np.nanargmax(ys))
            decision = (f"best {display(col, col_map)}", xs[pos], ys[pos], color)
    if decision is not None:
        label, best_x, best_y, color = decision
        ax.axvline(best_x, color="#333333", lw=0.65, ls="--", alpha=0.62, zorder=1)
        ax.scatter([best_x], [best_y], s=38, color=color, edgecolor="white", linewidth=0.55, zorder=7)
        ax.text(
            0.98, 0.07, f"{label}\nepoch={best_x:g}\nvalue={best_y:.3g}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.2,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                      edgecolor="#333333", linewidth=0.45, alpha=0.92),
            zorder=8,
        )

    if line_records:
        first = line_records[0]
        last_delta = first[3][-1] - first[3][0]
        ax.text(0.04, 0.94, f"training history\ncurves={len(line_records)}\nΔ={last_delta:+.2g}",
                transform=ax.transAxes, ha="left", va="top", fontsize=5.2,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                          edgecolor="#CCCCCC", linewidth=0.35, alpha=0.88))

    ax.set_xlabel(display(epoch_col, col_map))
    ax.set_ylabel("Metric value")
    ax.xaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.20)
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        if standalone and ax.figure is not None:
            legend = ax.figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02),
                                      ncol=min(4, len(labels)), fontsize=5, frameon=True,
                                      fancybox=True, borderpad=0.25, handlelength=1.6, columnspacing=0.8)
            legend.set_gid("scifig_shared_legend")
            legend.get_frame().set_linewidth(0.35)
            legend.get_frame().set_edgecolor("#333333")
            legend.get_frame().set_alpha(0.94)
            try:
                if hasattr(ax.figure, "set_layout_engine"):
                    ax.figure.set_layout_engine(None)
                else:
                    ax.figure.set_constrained_layout(False)
            except Exception:
                pass
            sp = ax.figure.subplotpars
            ax.figure.subplots_adjust(left=max(sp.left, 0.16), bottom=max(sp.bottom, 0.30), right=min(sp.right, 0.96))
        else:
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=min(4, len(labels)),
                      frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "training_curve")
    return ax


def gen_ma_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """MA plot: average abundance/intensity versus log2 fold change."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    mean_col = roles.get("mean") or roles.get("baseMean") or roles.get("abundance") or roles.get("x")
    fc_col = roles.get("log2fc") or roles.get("fold_change") or roles.get("effect") or roles.get("y")
    p_col = roles.get("padj") or roles.get("p_value") or roles.get("pvalue")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if mean_col is None and numeric_cols:
        mean_col = numeric_cols[0]
    if fc_col is None and len(numeric_cols) > 1:
        fc_col = numeric_cols[1]
    if mean_col is None or fc_col is None:
        raise ValueError("ma_plot requires mean abundance and log2 fold-change columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    mean_vals = df[mean_col].astype(float).clip(lower=1e-12)
    fc_vals = df[fc_col].astype(float)
    sig = np.zeros(len(df), dtype=bool)
    if p_col and p_col in df.columns:
        sig = df[p_col].astype(float) < 0.05
    sig = sig & (np.abs(fc_vals) >= 1)

    ax.scatter(np.log10(mean_vals[~sig]), fc_vals[~sig], s=9, c="#B8B8B8",
               alpha=0.55, linewidth=0, label=f"NS ({int((~sig).sum())})")
    ax.scatter(np.log10(mean_vals[sig]), fc_vals[sig], s=13, c="#C8553D",
               alpha=0.8, edgecolors="white", linewidth=0.25,
               label=f"Changed ({int(sig.sum())})")
    # Zero baseline (logFC=0) — delegate to template_mining_helpers when reachable
    canonical_zero_ref = globals().get("add_zero_reference")
    if canonical_zero_ref is not None:
        try:
            canonical_zero_ref(ax, axis="y", color="black", lw=0.55, ls="-", zorder=1)
        except Exception:
            ax.axhline(0, color="black", lw=0.55)
    else:
        ax.axhline(0, color="black", lw=0.55)
    ax.axhline(1, color="#777777", lw=0.45, ls="--")
    ax.axhline(-1, color="#777777", lw=0.45, ls="--")
    ax.set_xlabel(f"log10({_display_col(mean_col, col_map)})")
    ax.set_ylabel(_display_col(fc_col, col_map))
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
              frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "ma_plot")
    return ax


def gen_tsne(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """t-SNE embedding scatter, using supplied tSNE coordinates when present."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("tsne_1") or roles.get("tsne1") or roles.get("x")
    y_col = roles.get("tsne_2") or roles.get("tsne2") or roles.get("y")
    group_col = roles.get("group") or roles.get("cell_type")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if x_col is None or y_col is None:
        if len(numeric_cols) < 2:
            raise ValueError("tsne requires tSNE coordinates or at least two numeric columns")
        matrix = df[numeric_cols].fillna(0).to_numpy(dtype=float)
        matrix = matrix - matrix.mean(axis=0, keepdims=True)
        _, _, vt = np.linalg.svd(matrix, full_matrices=False)
        coords = matrix @ vt[:2].T
        x_vals, y_vals = coords[:, 0], coords[:, 1]
        x_label, y_label = "tSNE 1 (fallback embedding)", "tSNE 2 (fallback embedding)"
    else:
        x_vals, y_vals = df[x_col].astype(float).values, df[y_col].astype(float).values
        x_label, y_label = "tSNE 1", "tSNE 2"

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    if group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            mask = df[group_col] == cat
            ax.scatter(x_vals[mask], y_vals[mask], s=12, alpha=0.75,
                       color=color_map[cat], edgecolors="white", linewidth=0.25,
                       label=str(cat))
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
                  frameon=False, fontsize=5)
    else:
        ax.scatter(x_vals, y_vals, s=12, alpha=0.75,
                   color=palette.get("categorical", ["#1F4E79"])[0],
                   edgecolors="white", linewidth=0.25)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if standalone:
        apply_chart_polish(ax, "tsne")
    return ax


def gen_oncoprint(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Oncoprint-style alteration matrix for gene-by-sample mutation calls."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    gene_col = roles.get("gene") or roles.get("feature_id") or roles.get("row")
    sample_col = roles.get("sample") or roles.get("subject_id") or roles.get("column")
    alteration_col = roles.get("alteration") or roles.get("mutation") or roles.get("value")

    if gene_col and sample_col and alteration_col:
        mat = df.pivot_table(index=gene_col, columns=sample_col, values=alteration_col,
                             aggfunc=lambda x: ";".join(sorted(set(map(str, x)))))
    else:
        mat = df.copy()
        if gene_col and gene_col in mat.columns:
            mat = mat.set_index(gene_col)

    mat = mat.fillna("")
    genes = list(mat.index)[:40]
    samples = list(mat.columns)[:80]
    mat = mat.loc[genes, samples]
    alteration_types = sorted({str(v) for v in mat.to_numpy().ravel() if str(v) not in ("", "0", "nan", "False")})
    if not alteration_types:
        alteration_types = ["altered"]
    code_map = {alt: i + 1 for i, alt in enumerate(alteration_types)}
    codes = np.zeros(mat.shape, dtype=float)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            value = str(mat.iat[i, j])
            if value in code_map:
                codes[i, j] = code_map[value]
            elif value not in ("", "0", "nan", "False"):
                codes[i, j] = 1

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(55, 3 * len(genes)) * (1 / 25.4)),
                           constrained_layout=True)

    cmap_colors = ["#F2F2F2"] + palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541"])
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(cmap_colors[:len(alteration_types) + 1])
    norm = BoundaryNorm(np.arange(-0.5, len(alteration_types) + 1.5), cmap.N)
    ax.imshow(codes, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
    ax.set_yticks(range(len(genes)))
    ax.set_yticklabels(genes, fontsize=5)
    ax.set_xticks([])
    ax.set_xlabel(f"Samples (n={len(samples)})")
    ax.set_ylabel("Genes")
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=cmap_colors[i + 1]) for i in range(len(alteration_types))]
    ax.legend(handles, alteration_types, loc="upper left", bbox_to_anchor=(1.02, 1),
              borderaxespad=0, frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "oncoprint")
    return ax


def gen_lollipop_mutation(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mutation lollipop plot: protein/genomic position versus mutation frequency."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pos_col = roles.get("position") or roles.get("aa_position") or roles.get("x")
    count_col = roles.get("count") or roles.get("frequency") or roles.get("value") or roles.get("y")
    label_col = roles.get("label") or roles.get("mutation") or roles.get("feature_id")

    if pos_col is None or count_col is None:
        raise ValueError("lollipop_mutation requires 'position' and 'count'/'frequency' columns")

    plot_df = df[[c for c in [pos_col, count_col, label_col] if c and c in df.columns]].dropna().sort_values(pos_col)
    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#C8553D"])[0]
    ax.hlines(0, plot_df[pos_col].min(), plot_df[pos_col].max(), color="#333333", lw=1.0)
    ax.vlines(plot_df[pos_col], 0, plot_df[count_col], color=color, lw=0.8, alpha=0.75)
    sizes = 25 + 40 * (plot_df[count_col] / plot_df[count_col].max())
    ax.scatter(plot_df[pos_col], plot_df[count_col], s=sizes, color=color,
               edgecolor="white", linewidth=0.35, zorder=3)
    if label_col:
        for _, row in plot_df.nlargest(min(8, len(plot_df)), count_col).iterrows():
            ax.annotate(str(row[label_col])[:16], (row[pos_col], row[count_col]),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=4.5,
                        arrowprops=dict(arrowstyle="-", lw=0.25, color="#555555"))
    ax.set_xlabel("Position")
    ax.set_ylabel("Mutation frequency")
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "lollipop_mutation")
    return ax


def gen_manhattan(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Manhattan plot for chromosome-position association scans."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    chrom_col = roles.get("chromosome") or roles.get("chr") or roles.get("group")
    pos_col = roles.get("position") or roles.get("x")
    p_col = roles.get("pvalue") or roles.get("p_value") or roles.get("padj") or roles.get("y")

    if chrom_col is None or pos_col is None or p_col is None:
        raise ValueError("manhattan requires chromosome, position, and p-value columns")

    plot_df = df[[chrom_col, pos_col, p_col]].dropna().copy()
    plot_df[p_col] = plot_df[p_col].astype(float).clip(lower=1e-300, upper=1.0)
    chroms = sorted(plot_df[chrom_col].unique(), key=lambda x: str(x))
    offset = 0
    ticks, ticklabels = [], []
    xs = np.zeros(len(plot_df))
    for chrom in chroms:
        idx = plot_df[chrom_col] == chrom
        sub_pos = plot_df.loc[idx, pos_col].astype(float)
        xs[idx.to_numpy()] = sub_pos + offset
        ticks.append(offset + (sub_pos.min() + sub_pos.max()) / 2)
        ticklabels.append(str(chrom))
        offset += sub_pos.max() + max(sub_pos.max() * 0.04, 1)
    plot_df["_x"] = xs
    plot_df["_nlogp"] = -np.log10(plot_df[p_col])

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    colors = palette.get("categorical", ["#1F4E79", "#C8553D"])
    for i, chrom in enumerate(chroms):
        sub = plot_df[plot_df[chrom_col] == chrom]
        ax.scatter(sub["_x"], sub["_nlogp"], s=6, color=colors[i % len(colors)],
                   alpha=0.72, linewidth=0)
    ax.axhline(-np.log10(5e-8), color="#333333", lw=0.5, ls="--")
    ax.axhline(-np.log10(1e-5), color="#999999", lw=0.45, ls=":")
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticklabels, fontsize=5)
    ax.set_xlabel("Chromosome")
    ax.set_ylabel("-log10(p-value)")
    if standalone:
        apply_chart_polish(ax, "manhattan")
    return ax


def gen_qq(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Q-Q plot for p-value calibration in association tests."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    p_col = roles.get("pvalue") or roles.get("p_value") or roles.get("padj") or roles.get("value")
    if p_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        p_col = numeric_cols[0] if numeric_cols else None
    if p_col is None:
        raise ValueError("qq requires a p-value column")

    pvals = np.sort(df[p_col].dropna().astype(float).clip(lower=1e-300, upper=1.0).values)
    n = len(pvals)
    expected = -np.log10((np.arange(1, n + 1) - 0.5) / n)
    observed = -np.log10(pvals)

    if standalone:
        fig, ax = plt.subplots(figsize=(70 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)

    ax.scatter(expected, observed, s=9, alpha=0.65, color=palette.get("categorical", ["#1F4E79"])[0],
               edgecolors="white", linewidth=0.25)
    lim = max(expected.max(), observed.max()) * 1.05
    # Q-Q reference diagonal — delegate to template_mining_helpers when reachable
    canonical_diagonal = globals().get("add_perfect_fit_diagonal")
    if canonical_diagonal is not None:
        try:
            canonical_diagonal(ax, np.asarray([0.0, lim]), np.asarray([0.0, lim]),
                               color="#333333", lw=0.6, alpha=1.0)
        except Exception:
            ax.plot([0, lim], [0, lim], color="#333333", lw=0.6, ls="--")
    else:
        ax.plot([0, lim], [0, lim], color="#333333", lw=0.6, ls="--")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Expected -log10(p)")
    ax.set_ylabel("Observed -log10(p)")
    if standalone:
        apply_chart_polish(ax, "qq")
    return ax


def gen_spatial_feature(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Spatial feature plot with spot coordinates colored by expression/value."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("spatial_x") or roles.get("x")
    y_col = roles.get("spatial_y") or roles.get("y")
    value_col = roles.get("value") or roles.get("feature") or roles.get("score")
    group_col = roles.get("group")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if x_col is None and len(numeric_cols) >= 1:
        x_col = numeric_cols[0]
    if y_col is None and len(numeric_cols) >= 2:
        y_col = numeric_cols[1]
    if x_col is None or y_col is None:
        raise ValueError("spatial_feature requires spatial x/y coordinates")

    if standalone:
        fig, ax = plt.subplots(figsize=(80 * (1 / 25.4), 80 * (1 / 25.4)),
                           constrained_layout=True)

    if value_col and value_col in df.columns:
        sc = ax.scatter(df[x_col], df[y_col], c=df[value_col], cmap="viridis",
                        s=12, alpha=0.85, linewidth=0)
        cbar = plt.colorbar(sc, ax=ax, shrink=0.65, pad=0.02)
        cbar.set_label(_display_col(value_col, col_map), fontsize=5)
    elif group_col and group_col in df.columns:
        categories = df[group_col].dropna().unique().tolist()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            sub = df[df[group_col] == cat]
            ax.scatter(sub[x_col], sub[y_col], color=color_map[cat], s=12,
                       alpha=0.85, linewidth=0, label=str(cat))
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
                  frameon=False, fontsize=5)
    else:
        ax.scatter(df[x_col], df[y_col], color=palette.get("categorical", ["#1F4E79"])[0],
                   s=12, alpha=0.85, linewidth=0)
    ax.set_xlabel(_display_col(x_col, col_map))
    ax.set_ylabel(_display_col(y_col, col_map))
    ax.set_aspect("equal", adjustable="datalim")
    if standalone:
        apply_chart_polish(ax, "spatial_feature")
    return ax


def gen_composition_dotplot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Composition dot plot: group-by-feature proportions encoded by size and color."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    feature_col = roles.get("feature_id") or roles.get("feature") or roles.get("label")
    group_col = roles.get("group") or roles.get("sample")
    value_col = roles.get("value") or roles.get("proportion") or roles.get("fraction")
    if feature_col is None or group_col is None or value_col is None:
        raise ValueError("composition_dotplot requires feature, group, and value columns")

    pivot = df.pivot_table(index=feature_col, columns=group_col, values=value_col,
                           aggfunc="sum", fill_value=0)
    features = pivot.index.tolist()
    groups = pivot.columns.tolist()
    if standalone:
        fig, ax = plt.subplots(figsize=(max(89, 8 * len(groups)) * (1 / 25.4),
                                    max(60, 5 * len(features)) * (1 / 25.4)),
                           constrained_layout=True)

    vmax = pivot.to_numpy().max() or 1
    for i, feature in enumerate(features):
        for j, group in enumerate(groups):
            value = pivot.loc[feature, group]
            ax.scatter(j, i, s=12 + 120 * value / vmax, c=value, cmap="viridis",
                       vmin=0, vmax=vmax, edgecolor="white", linewidth=0.25)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups, rotation=45, ha="right", fontsize=5)
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features, fontsize=5)
    ax.set_xlabel(_display_col(group_col, col_map))
    ax.set_ylabel(_display_col(feature_col, col_map))
    if standalone:
        apply_chart_polish(ax, "composition_dotplot")
    return ax


def gen_bubble_matrix(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Bubble matrix with row/column categories and numeric bubble magnitude."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    row_col = roles.get("row") or roles.get("feature_id") or roles.get("y") or roles.get("label")
    col_col = roles.get("column") or roles.get("group") or roles.get("x")
    value_col = roles.get("value") or roles.get("size")
    if row_col is None or col_col is None or value_col is None:
        raise ValueError("bubble_matrix requires row, column, and value columns")

    pivot = df.pivot_table(index=row_col, columns=col_col, values=value_col,
                           aggfunc="mean", fill_value=0)
    rows = pivot.index.tolist()
    cols = pivot.columns.tolist()
    values = pivot.to_numpy(dtype=float)
    vmax = np.nanmax(np.abs(values)) or 1
    if standalone:
        fig, ax = plt.subplots(figsize=(max(80, 7 * len(cols)) * (1 / 25.4),
                                    max(60, 5 * len(rows)) * (1 / 25.4)),
                           constrained_layout=True)

    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            value = pivot.loc[row, col]
            ax.scatter(j, i, s=10 + 150 * abs(value) / vmax, c=value,
                       cmap="coolwarm", vmin=-vmax, vmax=vmax,
                       edgecolor="white", linewidth=0.25)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=5)
    ax.invert_yaxis()
    ax.set_xlabel(_display_col(col_col, col_map))
    ax.set_ylabel(_display_col(row_col, col_map))
    if standalone:
        apply_chart_polish(ax, "bubble_matrix")
    return ax


def gen_stacked_bar_comp(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stacked composition bar chart with optional within-bar normalization."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    x_col = roles.get("x") or roles.get("sample") or roles.get("group")
    stack_col = roles.get("stack") or roles.get("category") or roles.get("feature_id")
    value_col = roles.get("value") or roles.get("proportion") or roles.get("count")
    if x_col is None or stack_col is None or value_col is None:
        raise ValueError("stacked_bar_comp requires x/group, stack/category, and value columns")

    pivot = df.pivot_table(index=x_col, columns=stack_col, values=value_col,
                           aggfunc="sum", fill_value=0)
    row_sums = pivot.sum(axis=1).replace(0, 1)
    if row_sums.max() > 1.5:
        pivot = pivot.div(row_sums, axis=0)
    categories = pivot.columns.tolist()
    color_map = _extract_colors(palette, categories)
    if standalone:
        fig, ax = plt.subplots(figsize=(max(89, 7 * len(pivot)) * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    bottom = np.zeros(len(pivot))
    x = np.arange(len(pivot))
    for cat in categories:
        vals = pivot[cat].values
        ax.bar(x, vals, bottom=bottom, color=color_map.get(cat, "#999999"),
               edgecolor="white", linewidth=0.35, width=0.72, label=str(cat))
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index.astype(str), rotation=45, ha="right", fontsize=5)
    ax.set_ylabel("Proportion" if pivot.to_numpy().max() <= 1.0 else _display_col(value_col, col_map))
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
              frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "stacked_bar_comp")
    return ax


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
```
**Usage notes for multi-panel composition:**

- All generators accept an `ax` keyword argument pattern. To use inside a
  multi-panel figure, pass `ax=axes["B"]` after minor refactoring to accept
  an optional `ax` parameter.
- The `palette` argument is a dict from `resolve_color_system()` containing
  `categorical`, `categoryMap`, and other keys.
- `dataProfile` must carry `semanticRoles` with at minimum `value` (numeric
  column) and optionally `group` (categorical column).
- For `violin_paired`, `semanticRoles.pair_id` identifies matched
  observations.
- For `violin_split`, `semanticRoles.x` provides an additional grouping axis
  (e.g., timepoint) while `group` provides the two halves.
