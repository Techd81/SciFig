"""Radar / polar chart generators.

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


def gen_biodiversity_radar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Biodiversity radar: multiple diversity indices on polar axes.

    Anchor: ecological community comparison (Shannon, Simpson, Richness, Evenness, Chao1).
    Aligned with knowledge/techniques/radar.md polygon-grid + sandwich-layer
    discipline. Calls add_polygon_polar_grid (template_mining_helpers, embedded via
    Phase A1) for the corpus-anchored polygon grid replacement, with min-max
    normalisation per index for cross-index comparability.
    """
    from math import pi as _pi
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    attr_col = roles.get("attribute") or roles.get("x")
    group_col = roles.get("group")
    val_col = roles.get("value") or roles.get("y")

    if attr_col is None or val_col is None:
        raise ValueError("biodiversity_radar requires 'attribute' and 'value' in semanticRoles")

    indices = df[attr_col].dropna().unique().tolist()
    n_idx = len(indices)
    if n_idx < 3:
        raise ValueError("biodiversity_radar requires at least 3 diversity indices")

    fallback = palette.get("categorical", ["#4A6B8A", "#5FA896", "#D9A75A",
                                            "#B85B5B", "#7A6C8F", "#2B6F77"])
    cat_map = palette.get("categoryMap", {})

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                               subplot_kw=dict(polar=True),
                               constrained_layout=False)

    angles = [i / n_idx * 2 * _pi for i in range(n_idx)]
    angles_closed = angles + [angles[0]]

    # ─── Polar discipline: north start, clockwise (matches gen_radar) ─────
    if hasattr(ax, "set_theta_offset"):
        ax.set_theta_offset(_pi / 2)
        ax.set_theta_direction(-1)

    # ─── Polygon dashed grid via template_mining_helpers (Phase A1) ──────
    polygon_grid_fn = globals().get("add_polygon_polar_grid")
    if polygon_grid_fn is not None:
        polygon_grid_fn(ax, angles_closed, levels=(0.25, 0.5, 0.75, 1.0))
    else:
        # Defensive fallback
        ax.spines["polar"].set_visible(False)
        ax.grid(False)
        for level in (0.25, 0.5, 0.75, 1.0):
            ax.plot(angles_closed, [level] * len(angles_closed),
                    color="black", linestyle="--", linewidth=0.8,
                    alpha=0.6, zorder=0)

    ax.set_xticks(angles)
    label_strings = [str(display_label(i, col_map) if col_map else i)
                     for i in indices]
    ax.set_xticklabels(label_strings, fontsize=8)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["", "", "", ""])
    ax.set_ylim(0, 1.05)

    # Normalise values per index to [0, 1] across all groups for proper cross-group
    # cmp. Compute global min/max per index across rows.
    per_index_min = {}
    per_index_max = {}
    for idx_name in indices:
        sub = df[df[attr_col] == idx_name][val_col].dropna().astype(float)
        per_index_min[idx_name] = float(sub.min()) if len(sub) else 0.0
        per_index_max[idx_name] = float(sub.max()) if len(sub) else 1.0

    def _norm_vals(vals, idxs):
        out = []
        for v, i_name in zip(vals, idxs):
            lo, hi = per_index_min[i_name], per_index_max[i_name]
            rng = (hi - lo) if hi != lo else 1.0
            out.append((float(v) - lo) / rng)
        return out

    if group_col and group_col in df.columns:
        groups = df[group_col].dropna().unique().tolist()
        for i, grp in enumerate(groups):
            subset = df[df[group_col] == grp]
            vals = []
            for idx_name in indices:
                match = subset[subset[attr_col] == idx_name][val_col]
                vals.append(float(match.values[0]) if len(match) > 0 else 0.0)
            vals_norm = _norm_vals(vals, indices)
            color = cat_map.get(grp, fallback[i % len(fallback)])
            label = display_label(grp, col_map) if col_map else str(grp)
            # Sandwich layers: fill + thick outline + markers (matches gen_radar)
            ax.fill(angles_closed, vals_norm + vals_norm[:1],
                    alpha=0.15, color=color, zorder=1)
            ax.plot(angles_closed, vals_norm + vals_norm[:1],
                    linewidth=2.5, color=color, label=label, zorder=5)
            ax.scatter(angles, vals_norm, s=42, color=color,
                       edgecolor="white", linewidth=0.6, zorder=10)
    else:
        vals = []
        for idx_name in indices:
            match = df[df[attr_col] == idx_name][val_col]
            vals.append(float(match.values[0]) if len(match) > 0 else 0.0)
        vals_norm = _norm_vals(vals, indices)
        color = fallback[0]
        ax.fill(angles_closed, vals_norm + vals_norm[:1],
                alpha=0.15, color=color, zorder=1)
        ax.plot(angles_closed, vals_norm + vals_norm[:1],
                linewidth=2.5, color=color, zorder=5)

    if standalone:
        apply_chart_polish(ax, "biodiversity_radar")
    return ax


def gen_radar(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Nature-style radar chart — pixel-faithful reproduction of the canonical
    Nature Vol 626 Fig 3c (semiconductor fibre) and the rest of the radar corpus.

    Anchor cases (template corpus):
      - 绝美！Nature 这张雷达图_1777449664 (the canonical reference)
      - 顶刊复刻 _ 中心挖空 + 立体高光的雷达图_1777451060
      - 期刊配图：基于极坐标系的多面板雷达图_1777454388

    Required visual grammar (from knowledge/techniques/radar.md):
      1. Polygon dashed grid (NOT default circular) via add_polygon_polar_grid
      2. theta_offset = pi/2 (north start) + theta_direction = -1 (clockwise)
      3. Sandwich layering: translucent fill (L1, alpha=0.15) + thick outline
         (L2, lw=2.5) + errorbar markers (L4, zorder=10)
      4. Per-axis physical-limit normalization to [0, 1]
      5. Closed-loop angle array (last angle equals first)
      6. Hidden radial number ticks (clutter removal)
      7. Optional max=<limit> annotations on each spoke (Nature-style)
      8. Optional hollow-center / glass-marker variant for the case-001 radar
         replica via add_hollow_polar_center, add_polar_spoke_tick_labels, and
         scatter_glass_markers when the template motifs request it.

    Data layout — supports BOTH long and wide:
      Long: rows = (group × attribute); semanticRoles { 'group', 'attribute', 'value', 'error'? }
      Wide: rows = groups, columns = attributes; semanticRoles { 'group' } and attribute columns

    Per-axis limits priority:
      1. chartPlan['radarAxisLimits'] dict { attr: limit } if user/Phase 2 supplied
      2. dataProfile['axisLimits'] dict
      3. ceil to nearest 'nice' number above max(value + error) per axis
    """
    from math import pi as _pi
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    attr_col = roles.get("attribute") or roles.get("x")
    group_col = roles.get("group")
    val_col = roles.get("value") or roles.get("y")
    err_col = roles.get("error") or roles.get("std") or roles.get("se")
    visual_plan = chartPlan.get("visualContentPlan") if isinstance(chartPlan.get("visualContentPlan"), dict) else {}
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        chartPlan["visualContentPlan"] = visual_plan
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    template_motifs = {
        str(m).lower()
        for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs") or [])
    }
    lower_to_col = {str(col).lower(): col for col in df.columns}

    def _first_column(*names):
        for name in names:
            if not name:
                continue
            if name in df.columns:
                return name
            lowered = str(name).lower()
            if lowered in lower_to_col:
                return lower_to_col[lowered]
        return None

    use_mirror_radial_bar_board = (
        standalone
        and (
            visual_plan.get("useMirrorRadialBarBoard")
            or "mirror_radial_bar_board" in template_motifs
            or "mirror_radial_bar_board" in patterns
            or "mirror_radial" in patterns
        )
    )
    if use_mirror_radial_bar_board:
        draw_fn = globals().get("draw_mirror_radial_bar_board")
        if draw_fn is None:
            raise RuntimeError("draw_mirror_radial_bar_board helper is required for gen_radar")
        model_col = _first_column(
            roles.get("model"), roles.get("group"), roles.get("label"),
            "model", "models", "algorithm"
        )
        condition_col = _first_column(
            roles.get("condition"), roles.get("pressure"), roles.get("panel"),
            "condition", "pressure", "pressure_bar", "bar"
        )
        original_col = _first_column(
            roles.get("original"), roles.get("original_features"), roles.get("baseline"),
            "original", "original_features", "orig", "full_features", "full"
        )
        simplified_col = _first_column(
            roles.get("simplified"), roles.get("simplified_features"), roles.get("reduced"),
            "simplified", "simplified_features", "simp", "reduced_features", "reduced"
        )
        if model_col is None or original_col is None or simplified_col is None:
            raise ValueError("mirror_radial_bar_board requires model, original, and simplified columns")
        result = draw_fn(
            df,
            model_col=model_col,
            condition_col=condition_col,
            original_col=original_col,
            simplified_col=simplified_col,
            condition_order=visual_plan.get("mirrorRadialConditionOrder"),
            condition_labels=visual_plan.get("mirrorRadialConditionLabels"),
            max_val=visual_plan.get("mirrorRadialMaxValue"),
            original_color=visual_plan.get("mirrorRadialOriginalColor", "#33CCFF"),
            simplified_color=visual_plan.get("mirrorRadialSimplifiedColor", "#FFFF99"),
            bar_width=visual_plan.get("mirrorRadialBarWidth", 0.45),
            scale_rect=visual_plan.get("mirrorRadialScaleRect", [0.05, 0.40, 0.02, 0.40]),
            figsize=tuple(visual_plan.get("mirrorRadialFigsize", [7.0, 7.0])),
            col_map=col_map,
        )
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        for motif in ("mirror_radial_bar_board", "mirror_radial_bar", "external_scale_bar"):
            if motif not in planned_motifs:
                planned_motifs.append(motif)
            record_fn(visual_plan, motif)
        count_fn(visual_plan, "externalScaleBarCount")
        count_fn(visual_plan, "sampleEncodingCount")
        visual_plan["mirrorRadialPanelCount"] = 1
        visual_plan["mirrorRadialOriginalBarCount"] = result.get("original_bar_count")
        visual_plan["mirrorRadialSimplifiedBarCount"] = result.get("simplified_bar_count")
        visual_plan["radialBarLayerCount"] = result.get("radial_bar_layer_count")
        visual_plan["mirrorRadialLayerCount"] = result.get("radial_bar_layer_count")
        visual_plan["mirrorRadialPaletteApplied"] = result.get("palette")
        visual_plan["templateMatchMode"] = "case_023_mirror_radial_bar_board"
        return result["ax"]

    long_format = (attr_col is not None and val_col is not None
                   and attr_col in df.columns and val_col in df.columns)
    if long_format:
        attributes = df[attr_col].dropna().unique().tolist()
    else:
        # Wide format: attributes are numeric columns excluding group_col
        attributes = [c for c in df.select_dtypes(include="number").columns
                      if c != group_col]
    n_attrs = len(attributes)
    if n_attrs < 3:
        raise ValueError("radar requires at least 3 attributes")

    # ─── Palette: prefer Nature radar dual when palette resolves to it ─────
    fallback = palette.get("categorical", ["#1F3A5F", "#C8553D", "#4C956C",
                                            "#F2A541", "#7A6C8F", "#2B6F77"])
    cat_map = palette.get("categoryMap", {})
    template_palette_hex = palette.get("templatePaletteHex") or []
    palette_family = palette.get("paletteFamily") or ""
    is_nature_dual = (palette_family == "nature_radar_dual"
                      or template_palette_hex == ["#1F3A5F", "#C8553D"]
                      or list(fallback)[:2] == ["#1F3A5F", "#C8553D"])

    def _collect_tokens(value):
        tokens = []
        if isinstance(value, (list, tuple, set)):
            tokens.extend(str(v).lower() for v in value)
        elif isinstance(value, dict):
            for item in value.values():
                tokens.extend(_collect_tokens(item))
        elif value:
            tokens.append(str(value).lower())
        return tokens

    motif_tokens = set()
    for source in (
        chartPlan.get("templateMotifs"),
        chartPlan.get("visualMotifs"),
        chartPlan.get("radarStyle"),
        visual_plan.get("templateMotifs"),
        visual_plan.get("visualMotifs"),
        chartPlan.get("templateCasePlan"),
    ):
        motif_tokens.update(_collect_tokens(source))

    def _has_template_motif(*needles):
        for token in motif_tokens:
            normalized = token.replace("_", " ")
            for needle in needles:
                n = str(needle).lower()
                if n in token or n.replace("_", " ") in normalized:
                    return True
        return False

    use_hollow_center = _has_template_motif(
        "hollow_polar_center", "hollow-center", "center_hollow",
        "hollow_highlight_radar", "center cutout", "中心挖空", "立体高光"
    )
    use_glass_markers = use_hollow_center or _has_template_motif(
        "glass_marker_stack", "glass_markers",
        "pseudo_3d_marker_highlight", "specular", "立体高光"
    )

    # ─── Build closed-loop angles ─────────────────────────────────────────
    angles = [i / n_attrs * 2 * _pi for i in range(n_attrs)]
    angles_closed = angles + [angles[0]]

    # ─── Resolve per-axis physical limits ─────────────────────────────────
    radar_limits = (chartPlan.get("radarAxisLimits")
                    or chartPlan.get("axisLimits")
                    or dataProfile.get("axisLimits")
                    or {})
    radar_centers = (chartPlan.get("radarAxisCenters")
                     or chartPlan.get("axisCenters")
                     or dataProfile.get("axisCenters")
                     or {})
    limits = []
    for attr in attributes:
        if attr in radar_limits and radar_limits[attr]:
            limits.append(float(radar_limits[attr]))
            continue
        if long_format:
            col_vals = df[df[attr_col] == attr][val_col].astype(float)
        else:
            col_vals = df[attr].astype(float)
        if err_col and long_format and err_col in df.columns:
            err_vals = df[df[attr_col] == attr][err_col].astype(float).fillna(0)
            top_each = (col_vals.values + err_vals.values).tolist() if len(err_vals) == len(col_vals) else col_vals.tolist()
        else:
            top_each = col_vals.tolist()
        cap = float(max(top_each) if top_each else 1.0)
        # Round up to a 'nice' number (next 1/2/5 × 10^n above cap)
        if cap <= 0:
            limits.append(1.0); continue
        import math as _math
        exp = _math.floor(_math.log10(cap))
        scaled = cap / (10 ** exp)
        nice = next(n for n in (1.0, 2.0, 2.5, 5.0, 10.0) if scaled <= n)
        limits.append(nice * (10 ** exp))

    centers = []
    for attr, limit in zip(attributes, limits):
        try:
            center = float(radar_centers.get(attr, 0.0)) if isinstance(radar_centers, dict) else 0.0
        except Exception:
            center = 0.0
        centers.append(center if center < float(limit) else 0.0)

    def _norm(values, limits, centers=None):
        centers = centers or [0.0] * len(limits)
        out = []
        for value, limit, center in zip(values, limits, centers):
            denom = float(limit) - float(center)
            normed = (float(value) - float(center)) / denom if denom else 0.0
            out.append(float(np.clip(normed, 0.0, 1.1)))
        return out

    def _norm_error(errors, limits, centers=None):
        centers = centers or [0.0] * len(limits)
        out = []
        for err, limit, center in zip(errors, limits, centers):
            denom = float(limit) - float(center)
            out.append(float(err) / denom if denom else 0.0)
        return out

    # ─── Figure setup (standalone) ────────────────────────────────────────
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 89 * (1 / 25.4)),
                               subplot_kw=dict(polar=True),
                               constrained_layout=False)

    # ─── Polar discipline: north start, clockwise (Nature convention) ─────
    if hasattr(ax, "set_theta_offset"):
        ax.set_theta_offset(_pi / 2)
        ax.set_theta_direction(-1)

    # ─── Polygon dashed grid (replaces matplotlib's default circular grid) ──
    # Calls template_mining_helpers.add_polygon_polar_grid which is now embedded
    # in runtime via 03-code-gen-style.md Step 3.6. This is the corpus-anchored
    # 'polygon_polar_grid' motif required by hero.polar arc.
    polygon_grid_fn = globals().get("add_polygon_polar_grid")
    if polygon_grid_fn is not None:
        polygon_grid_fn(ax, angles_closed, levels=(0.25, 0.5, 0.75, 1.0))
    else:
        # Defensive fallback if helpers were not embedded (legacy path)
        ax.spines["polar"].set_visible(False)
        ax.grid(False)
        for level in (0.25, 0.5, 0.75, 1.0):
            ax.plot(angles_closed, [level] * len(angles_closed),
                    color="black", linestyle="--", linewidth=0.8,
                    alpha=0.6, zorder=0)
        for ang in angles:
            ax.plot([ang, ang], [0, 1.0], color="black",
                    linewidth=0.6, alpha=0.4, zorder=0)

    # ─── Sandwich layered draw per group ──────────────────────────────────
    def _plot_group(values_norm, errors_norm, color, label):
        # L1 cushion: translucent fill
        ax.fill(angles_closed, values_norm + values_norm[:1],
                color=color, alpha=0.15, zorder=1)
        # L2 wrapper: thick outline (the Nature signature: lw=2.5)
        ax.plot(angles_closed, values_norm + values_norm[:1],
                color=color, linewidth=2.5, label=label, zorder=5)
        # L4 markers: errorbar at each spoke (or just markers if no errors)
        if errors_norm is not None and any(e > 0 for e in errors_norm):
            ax.errorbar(angles, values_norm, yerr=errors_norm,
                        fmt="o", color=color, markersize=6, capsize=3,
                        elinewidth=1.2, zorder=10)
        elif use_glass_markers:
            glass_marker_fn = globals().get("scatter_glass_markers")
            if glass_marker_fn is not None:
                try:
                    glass_marker_fn(ax, angles, values_norm, color=color,
                                    base_s=48, soft_s=18, hard_s=7, zorder=10)
                except Exception:
                    ax.scatter(angles, values_norm, s=42, color=color,
                               edgecolor="white", linewidth=0.6, zorder=10)
            else:
                ax.scatter(angles, values_norm, s=42, color=color,
                           edgecolor="white", linewidth=0.6, zorder=10)
        else:
            ax.scatter(angles, values_norm, s=42, color=color,
                       edgecolor="white", linewidth=0.6, zorder=10)

    template_rows, template_colors = [], []
    if long_format and group_col and group_col in df.columns:
        groups = df[group_col].dropna().unique().tolist()
        for i, grp in enumerate(groups):
            sub = df[df[group_col] == grp]
            values = [float(sub[sub[attr_col] == a][val_col].iloc[0])
                      if not sub[sub[attr_col] == a].empty else 0.0
                      for a in attributes]
            errors = ([float(sub[sub[attr_col] == a][err_col].iloc[0])
                       if (err_col and err_col in df.columns
                           and not sub[sub[attr_col] == a].empty) else 0.0
                       for a in attributes]
                      if err_col else None)
            values_norm = _norm(values, limits, centers)
            errors_norm = _norm_error(errors, limits, centers) if errors else None
            color = cat_map.get(grp, fallback[i % len(fallback)])
            label = display_label(grp, col_map) if col_map else str(grp)
            _plot_group(values_norm, errors_norm, color, label)
            template_rows.append(values_norm)
            template_colors.append(color)
    elif not long_format and group_col and group_col in df.columns:
        # Wide: rows are groups, columns are attribute values
        groups = df[group_col].dropna().unique().tolist()
        for i, grp in enumerate(groups):
            sub = df[df[group_col] == grp].iloc[0]
            values = [float(sub[a]) if a in sub else 0.0 for a in attributes]
            values_norm = _norm(values, limits, centers)
            color = cat_map.get(grp, fallback[i % len(fallback)])
            label = display_label(grp, col_map) if col_map else str(grp)
            _plot_group(values_norm, None, color, label)
            template_rows.append(values_norm)
            template_colors.append(color)
    else:
        # Single series (no group column)
        if long_format:
            values = [float(df[df[attr_col] == a][val_col].iloc[0])
                      if not df[df[attr_col] == a].empty else 0.0
                      for a in attributes]
        else:
            values = [float(df[a].mean()) for a in attributes]
        values_norm = _norm(values, limits, centers)
        color = fallback[0]
        _plot_group(values_norm, None, color, "value")
        template_rows.append(values_norm)
        template_colors.append(color)

    # ─── Tick label discipline: hide radial numbers (corpus anchor) ──────
    ax.set_xticks(angles)
    label_strings = [str(display_label(a, col_map) if col_map else a)
                     for a in attributes]
    ax.set_xticklabels(label_strings, fontsize=8)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["", "", "", ""])
    ax.set_ylim(0, 1.05)

    if use_hollow_center:
        hollow_fn = globals().get("add_hollow_polar_center")
        if hollow_fn is not None:
            try:
                hollow_fn(ax, size=130, zorder=15)
            except Exception:
                ax.scatter([0], [0], s=130, c="white",
                           edgecolors="black", linewidths=0.9, zorder=15)
        else:
            ax.scatter([0], [0], s=130, c="white",
                       edgecolors="black", linewidths=0.9, zorder=15)
        if any(c > 0 for c in centers):
            spoke_label_fn = globals().get("add_polar_spoke_tick_labels")
            first_center, first_limit = centers[0], limits[0]
            tick_values = chartPlan.get("radarTickValues")
            if not tick_values:
                tick_values = [
                    first_center + (first_limit - first_center) * q
                    for q in (0.25, 0.5, 0.75, 1.0)
                ]
            if spoke_label_fn is not None:
                try:
                    spoke_label_fn(ax, tick_values, center=first_center,
                                   angle=angles[0], fmt="{:g}")
                except Exception:
                    pass

    # ─── Per-spoke physical-limit annotation (Nature signature) ──────────
    if visual_plan.get("requireInPlotExplanatoryLabels", True):
        for ang, lim in zip(angles, limits):
            label_txt = (f"max={int(lim)}" if abs(lim - int(lim)) < 1e-6
                         else f"max={lim:g}")
            ax.text(ang, 1.18, label_txt,
                    ha="center", va="center", fontsize=6, color="#555")

    # ─── Apply zorder recipe via template_mining_helpers when reachable ──
    apply_zorder = globals().get("apply_zorder_recipe")
    if apply_zorder is not None:
        try:
            apply_zorder("radar", ax, {})
        except Exception:
            pass

    # ─── Legacy compatibility: also call apply_template_radar_signature so
    # downstream visualPlan motif counters still register `polar_comparison_signature`
    # during the migration window (Phase D will retire the legacy helper).
    # Pass draw_grid=False because we already drew the polygon grid via
    # add_polygon_polar_grid above — without this guard the legacy shim would
    # delegate the grid drawing AGAIN and produce duplicate dashed lines.
    legacy_sig = globals().get("apply_template_radar_signature")
    if legacy_sig is not None:
        try:
            legacy_sig(ax, angles, value_rows=template_rows,
                       colors=template_colors, visualPlan=visual_plan,
                       draw_grid=False)
        except TypeError:
            # Older legacy shim without draw_grid kwarg — best-effort fallback
            try:
                legacy_sig(ax, angles, value_rows=template_rows,
                           colors=template_colors, visualPlan=visual_plan)
            except Exception:
                pass
        except Exception:
            pass

    if standalone:
        # NOTE: apply_chart_polish in helpers.py assumes cartesian spines
        # ('top'/'right'); polar axes only have 'polar' spine. Skip the call
        # for radar — the polar discipline (spine hiding, grid replacement)
        # is already enforced by add_polygon_polar_grid above.
        try:
            ax.tick_params(axis="x", labelsize=8, pad=4)
        except Exception:
            pass
    return ax
