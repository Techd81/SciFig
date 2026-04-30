"""Template-mining helpers — the operational layer for the 7-module knowledge base
under `template-mining/`. Phase 3 imports from this module to apply 顶刊 patterns
distilled from 77 reference cases.

Module status (n/n implemented):
  - apply_journal_kernel        ✓
  - resolve_palette             ✓
  - role_color                  ✓
  - add_metric_box              ✓
  - add_perfect_fit_diagonal    ✓
  - add_zero_reference          ✓
  - add_group_dividers          ✓
  - add_panel_label             ✓
  - density_sort                ✓
  - density_color_scatter       ✓
  - add_polygon_polar_grid      ✓
  - draw_gradient_box           ✓
  - build_grid                  ✓ (R0 / R1 / R2 / R3 / R5 / R6 / R8 / R9; R7 / R10 / R11 stubs)
  - select_narrative_arc        ✓
  - arc_required_motifs         ✓
  - arc_default_grid            ✓
  - apply_zorder_recipe         ✓ (scatter_regression / forest / dual_axis / radar / shap_composite / marginal_joint)

Reference docs:
  - 01-rcparams-kernel.md       kernel definitions
  - 02-zorder-recipes.md        per-family zorder layering
  - 03-palette-bank.md          named palettes + role mapping
  - 04-grid-recipes.md          GridSpec / subplots recipes
  - 05-annotation-idioms.md     in-axes annotation idioms
  - 06-narrative-arcs.md        story shapes
  - 07-techniques/<family>.md   deep-dive per chart family
"""
from __future__ import annotations

from typing import Iterable, Sequence

import matplotlib as mpl
import matplotlib.colors as mc
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec


# ============================================================================
# 1. RCPARAMS KERNEL  (01-rcparams-kernel.md)
# ============================================================================

_KERNEL_BASE = {
    "font.family":       ["Times New Roman", "Arial", "DejaVu Sans"],
    "mathtext.fontset":  "stix",
    "font.size":         6.5,
    "axes.linewidth":    0.65,
    "xtick.direction":   "in",
    "ytick.direction":   "in",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "lines.linewidth":   0.9,
    "lines.markersize":  3.5,
    "savefig.bbox":      "tight",
    "savefig.dpi":       600,
}

_VARIANTS = {
    "default": {},
    "hero":    {"font.size": 7.5, "axes.linewidth": 0.75, "lines.linewidth": 1.2},
    "compact": {"font.family": ["Arial", "Times New Roman", "DejaVu Sans"],
                "font.size": 6.5, "axes.linewidth": 0.65,
                "lines.linewidth": 0.9, "lines.markersize": 3.5},
    "polar":   {"font.size": 7.0, "axes.linewidth": 0.75,
                "grid.linestyle": "--", "grid.alpha": 0.5},
}


def apply_journal_kernel(variant: str = "default",
                          journalProfile: dict | None = None) -> None:
    """Apply the kernel rcParams for one of the four variants and let
    journal-specific overrides win. Variants: 'default' | 'hero' | 'compact' | 'polar'.

    Behavioral rules (from 01-rcparams-kernel.md):
      1. Variant is required; no silent fallback to matplotlib defaults.
      2. journalProfile fields take precedence for font_family, font_size_body_pt,
         axis_linewidth_pt.
      3. Always keep tick.direction='in'.
    """
    if variant not in _VARIANTS:
        raise KeyError(f"unknown kernel variant {variant!r}; "
                       f"choices: {sorted(_VARIANTS)}")
    rc = dict(_KERNEL_BASE)
    rc.update(_VARIANTS[variant])

    if journalProfile:
        if journalProfile.get("font_family"):
            rc["font.family"] = list(journalProfile["font_family"])
        if journalProfile.get("font_size_body_pt"):
            rc["font.size"] = float(journalProfile["font_size_body_pt"])
        if journalProfile.get("axis_linewidth_pt"):
            rc["axes.linewidth"] = float(journalProfile["axis_linewidth_pt"])

    rc["xtick.direction"] = "in"
    rc["ytick.direction"] = "in"
    plt.rcParams.update(rc)


# ============================================================================
# 2. PALETTE BANK  (03-palette-bank.md)
# ============================================================================

PALETTES: dict[str, list[str]] = {
    # categorical
    "nature_radar_dual":              ["#1F3A5F", "#C8553D"],
    "morandi_sci_4":                  ["#4A6B8A", "#5FA896", "#D9A75A", "#B85B5B"],
    "cej_vibrant_3":                  ["#00CED1", "#FF0000", "#1E90FF"],
    "cell_high_contrast_6":           ["#1B1B1B", "#D73027", "#4575B4",
                                        "#1A9850", "#FDAE61", "#7570B3"],
    "materials_porosity_terracotta":  ["#CFE2F3", "#9BC2E6", "#F48E66"],
    "npg_4":                          ["#E64B35", "#4DBBD5", "#00A087", "#3C5488"],
    "cool_summer_4":                  ["#8DA0CB", "#FC8D62", "#66C2A5", "#FBC15E"],
    "tableau10_classic":              ["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728",
                                        "#9467BD", "#8C564B", "#E377C2", "#7F7F7F",
                                        "#BCBD22", "#17BECF"],
    # sequential (returned as a list of stops; for actual cmap use mpl.colormaps)
    "seq_cool_5":                     ["#F7FBFF", "#D6EAF8", "#A9CCE3", "#5DADE2", "#21618C"],
    "seq_warm_5":                     ["#FFF6E8", "#FBD38D", "#F6AD55", "#DD6B20", "#9C4221"],
    # diverging anchors
    "bipolar_ALE":                    ["#4F81BD", "#FFFFFF", "#C0504D"],
    "red_blue_correlation":           ["#3B6FB6", "#F7F7F7", "#B5403A"],
}


PALETTE_ROLE_MAP: dict[str, str] = {
    "control":              "#1F4E79",
    "treatment":            "#C8553D",
    "rescue":               "#4C956C",
    "vehicle":              "#6C757D",
    "train":                "#4C78A8",
    "test":                 "#E45756",
    "actual":               "#1F4E79",
    "observed":             "#1F4E79",
    "experimental":         "#1F4E79",
    "predicted":            "#C8553D",
    "fitted":               "#C8553D",
    "estimated":            "#C8553D",
    "negative_correlation": "#4F81BD",
    "positive_correlation": "#C0504D",
    "shap_positive":        "#C0504D",
    "shap_negative":        "#4F81BD",
    "optimal":              "#00A087",
    "pareto":               "#00A087",
    "dominated":            "#7F7F7F",
}


def resolve_palette(name: str, n: int | None = None,
                    journalProfile: dict | None = None) -> list[str]:
    """Return the hex list for a named palette. Truncates or cycles to n if given.
    journalProfile.palette_overrides[name] takes precedence."""
    if journalProfile and "palette_overrides" in journalProfile:
        overrides = journalProfile["palette_overrides"]
        if name in overrides:
            return list(overrides[name])
    if name not in PALETTES:
        raise KeyError(f"palette {name!r} not in PALETTES; "
                       f"choices: {sorted(PALETTES)}")
    palette = list(PALETTES[name])
    if n is None:
        return palette
    if n <= len(palette):
        return palette[:n]
    return [palette[i % len(palette)] for i in range(n)]


def role_color(role: str, palette: list[str] | None = None) -> str:
    """Lookup a semantic role from PALETTE_ROLE_MAP."""
    if role not in PALETTE_ROLE_MAP:
        raise KeyError(f"role {role!r} not in PALETTE_ROLE_MAP")
    return PALETTE_ROLE_MAP[role]


# ============================================================================
# 3. ANNOTATION IDIOMS  (05-annotation-idioms.md)
# ============================================================================

def add_metric_box(ax: Axes, metrics: dict[str, str | float], *,
                   loc: str = "top_left", fontsize: int = 6,
                   pad: float = 0.28, lw: float = 0.45) -> None:
    """Place a metric text box with white fill + thin black border (idiom I1).

    metrics: dict mapping label → value. Values formatted with default precision.
             Keys may use $...$ for math.
    loc: 'top_left' (default), 'top_right', 'bottom_left', 'bottom_right'.
    """
    positions = {
        "top_left":     (0.05, 0.95, "top",    "left"),
        "top_right":    (0.95, 0.95, "top",    "right"),
        "bottom_left":  (0.05, 0.05, "bottom", "left"),
        "bottom_right": (0.95, 0.05, "bottom", "right"),
    }
    if loc not in positions:
        raise KeyError(f"loc {loc!r} invalid; choices: {sorted(positions)}")
    x, y, va, ha = positions[loc]

    lines = []
    for k, v in metrics.items():
        if isinstance(v, float):
            lines.append(f"{k} = {v:.3f}")
        else:
            lines.append(f"{k} = {v}")
    text = "\n".join(lines)

    ax.text(x, y, text, transform=ax.transAxes, va=va, ha=ha,
            fontsize=fontsize, fontweight="bold",
            bbox=dict(boxstyle=f"square,pad={pad}", fc="white",
                      ec="black", lw=lw),
            zorder=20)


def add_perfect_fit_diagonal(ax: Axes,
                              x: np.ndarray, y: np.ndarray, *,
                              color: str = "black",
                              lw: float = 1.0,
                              alpha: float = 0.6,
                              percentile: float | None = None) -> None:
    """Add y=x dashed diagonal for predicted-vs-actual scatter (idiom I2).
    Sets equal aspect ratio.

    percentile: when given (e.g. 99.5), clip the diagonal range to the [p, 100-p]
                joint percentile of x and y. Use this for noisy density scatter
                where a few outliers would otherwise stretch the diagonal far
                beyond the data bulk. None (default) uses the full min/max range.
    """
    if percentile is not None:
        p_lo = (100.0 - percentile)
        p_hi = percentile
        lo = float(min(np.percentile(x, p_lo), np.percentile(y, p_lo)))
        hi = float(max(np.percentile(x, p_hi), np.percentile(y, p_hi)))
    else:
        lo = float(min(np.min(x), np.min(y)))
        hi = float(max(np.max(x), np.max(y)))
    pad = (hi - lo) * 0.05
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
            color=color, linestyle="--", linewidth=lw, alpha=alpha, zorder=6)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_aspect("equal")


def add_zero_reference(ax: Axes, *, axis: str = "y",
                        color: str = "#222222",
                        lw: float = 1.0, ls: str = "--",
                        zorder: int = 5) -> None:
    """Add a dashed zero reference line (idiom I4). axis='y' → axhline; 'x' → axvline."""
    if axis == "y":
        ax.axhline(0, color=color, linestyle=ls, linewidth=lw, zorder=zorder)
    elif axis == "x":
        ax.axvline(0, color=color, linestyle=ls, linewidth=lw, zorder=zorder)
    else:
        raise ValueError("axis must be 'x' or 'y'")


def add_group_dividers(ax: Axes,
                        split_indices: Sequence[float], *,
                        group_labels: Sequence[str] | None = None,
                        group_centers: Sequence[float] | None = None,
                        color: str = "gray", lw: float = 0.7,
                        alpha: float = 0.6,
                        label_position: str = "above",
                        label_y_frac: float | None = None,
                        label_color: str = "#444",
                        label_fontsize: int = 6) -> None:
    """Draw dashed vertical group dividers and optional group labels (idiom I3).

    label_position: 'above' (default, outside chart at y=1.02 axes coords) |
                    'inside_top' (at y=0.96 axes coords, safer with figure title) |
                    'inside_bottom' (at y=0.04 axes coords).
    label_y_frac:  override fraction (axes coords) explicitly. Wins over label_position.
    """
    for x_split in split_indices:
        ax.axvline(x_split, color=color, linestyle="--",
                   linewidth=lw, alpha=alpha, zorder=1)
    if not (group_labels and group_centers):
        return
    pos_map = {"above": 1.02, "inside_top": 0.96, "inside_bottom": 0.04}
    yfrac = label_y_frac if label_y_frac is not None else pos_map.get(label_position, 0.96)
    va = "bottom" if yfrac >= 1.0 else "top"
    for cx, name in zip(group_centers, group_labels):
        ax.text(cx, yfrac, name,
                ha="center", va=va,
                fontsize=label_fontsize, fontweight="bold",
                color=label_color, transform=ax.get_xaxis_transform())


def add_panel_label(ax: Axes, label: str, *,
                     x: float = -0.12, y: float = 1.05,
                     fontsize: int = 8) -> None:
    """Bold panel label (a/b/c) outside the data rectangle (idiom I13)."""
    ax.text(x, y, label, transform=ax.transAxes,
            fontweight="bold", fontsize=fontsize, va="top", ha="right")


def apply_scatter_regression_floor(ax: Axes, *,
                                    grid_color: str = "#E0E0E0",
                                    grid_lw: float = 0.6,
                                    despine: bool = True,
                                    grid_axis: str = "both") -> None:
    """Apply the L0 floor for scatter-regression panels: light dashed grid + despine.
    Anchor cases: GAM scatter+residual (Nature), R² scatter, distance-decay scatter.
    Always call this BEFORE drawing scatter so the grid sits at zorder=0.

    grid_axis: 'both' (default, scatter), 'x' (horizontal bars / dot-plot), 'y' (vertical bars).
    """
    if grid_axis == "both":
        ax.grid(True, linestyle="--", color=grid_color, linewidth=grid_lw,
                alpha=0.6, zorder=0)
    elif grid_axis == "x":
        ax.xaxis.grid(True, linestyle="--", color=grid_color, linewidth=grid_lw,
                       alpha=0.6, zorder=0)
        ax.yaxis.grid(False)
    elif grid_axis == "y":
        ax.yaxis.grid(True, linestyle="--", color=grid_color, linewidth=grid_lw,
                       alpha=0.6, zorder=0)
        ax.xaxis.grid(False)
    else:
        raise ValueError(f"grid_axis must be 'both'|'x'|'y', got {grid_axis!r}")
    ax.set_axisbelow(True)
    if despine:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)


def resolve_split_palette(dataProfile: dict, *,
                           default_palette: str = "morandi_sci_4",
                           journalProfile: dict | None = None) -> dict[str, str]:
    """One-stop palette resolver that auto-detects split semantics.

    Returns a dict mapping role/category → hex.

    Discipline (per 03-palette-bank.md):
      - dataProfile.has_train_test_split → role_color('train'/'test')
      - dataProfile.has_actual_predicted → role_color('actual'/'predicted')
      - dataProfile.has_shap_signed       → role_color('shap_positive'/'shap_negative')
      - dataProfile.has_correlation_signed→ role_color('positive_correlation'/'negative_correlation')
      - Otherwise return categorical palette by `default_palette` name
        (categorical roles cat_0, cat_1, ...).
    """
    out: dict[str, str] = {}
    if dataProfile.get("has_train_test_split"):
        out["train"] = role_color("train")
        out["test"]  = role_color("test")
    if dataProfile.get("has_actual_predicted"):
        out["actual"]    = role_color("actual")
        out["predicted"] = role_color("predicted")
    if dataProfile.get("has_shap_signed"):
        out["shap_positive"] = role_color("shap_positive")
        out["shap_negative"] = role_color("shap_negative")
    if dataProfile.get("has_correlation_signed"):
        out["positive_correlation"] = role_color("positive_correlation")
        out["negative_correlation"] = role_color("negative_correlation")
    if not out:
        palette = resolve_palette(default_palette, journalProfile=journalProfile)
        for i, hex_ in enumerate(palette):
            out[f"cat_{i}"] = hex_
    return out


def density_sort(x: np.ndarray, y: np.ndarray, bw_method=None
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (x, y, density) sorted ascending by local 2D KDE density."""
    from scipy.stats import gaussian_kde
    xy = np.vstack([x, y])
    z = gaussian_kde(xy, bw_method=bw_method)(xy)
    idx = z.argsort()
    return x[idx], y[idx], z[idx]


def density_color_scatter(ax: Axes, x: np.ndarray, y: np.ndarray, *,
                           cmap: str = "GnBu_r", s: int = 18,
                           with_colorbar: bool = True,
                           colorbar_label: str = "Density",
                           rasterized: bool = True,
                           edgecolor: str = "white",
                           linewidth: float = 0.4,
                           zorder: int = 4) -> Axes:
    """Density-colored scatter with white-edged markers (idiom I6 + I7)."""
    x_s, y_s, z_s = density_sort(x, y)
    sc = ax.scatter(x_s, y_s, c=z_s, cmap=cmap, s=s,
                    edgecolor=edgecolor, linewidth=linewidth,
                    rasterized=rasterized, zorder=zorder)
    if with_colorbar:
        cbar = ax.figure.colorbar(sc, ax=ax, shrink=0.6, pad=0.04)
        cbar.set_label(colorbar_label, fontsize=6)
    return sc


def add_polygon_polar_grid(ax: Axes, angles: Sequence[float],
                            levels: Sequence[float] = (0.25, 0.5, 0.75, 1.0),
                            *,
                            color: str = "black",
                            grid_lw: float = 0.8,
                            spoke_lw: float = 0.6,
                            alpha_grid: float = 0.6,
                            alpha_spoke: float = 0.4) -> None:
    """Replace default circular polar grid with explicit polygon dashed grid (idiom I11).
    angles must already be closed (first angle appended to end)."""
    ax.spines["polar"].set_visible(False)
    ax.grid(False)
    for level in levels:
        ax.plot(angles, [level] * len(angles), color=color,
                linestyle="--", linewidth=grid_lw, alpha=alpha_grid, zorder=0)
    for ang in angles[:-1]:
        ax.plot([ang, ang], [0, max(levels)], color=color,
                linewidth=spoke_lw, alpha=alpha_spoke, zorder=0)


def set_polar_title(ax: Axes, title: str, *,
                     fontsize: int = 8,
                     fontweight: str = "bold",
                     y: float = 1.18) -> None:
    """Place title above polar axis without colliding with the topmost angle label.
    Default y=1.18 keeps clearance for tick labels (max=...) AND axis names.

    Use this instead of `ax.set_title(title)` on polar axes — matplotlib's default
    title position overlaps the angle-0 label on radar/polygon plots.
    """
    ax.text(0.5, y, title, transform=ax.transAxes,
            ha="center", va="bottom",
            fontsize=fontsize, fontweight=fontweight)


def draw_gradient_box(ax: Axes, x: float, q1: float, width: float,
                       height: float, color: str, *,
                       alpha_lo: float = 0.15, alpha_hi: float = 0.95,
                       zorder: int = 2) -> None:
    """Vertical-gradient fill inside a box rectangle via imshow (idiom I12)."""
    rgba = mc.to_rgba(color)
    alphas = np.linspace(alpha_lo, alpha_hi, 256)
    cmap = mc.LinearSegmentedColormap.from_list(
        "grad", [(rgba[0], rgba[1], rgba[2], a) for a in alphas])
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(grad, extent=(x, x + width, q1, q1 + height),
              aspect="auto", origin="lower", cmap=cmap, zorder=zorder)
    rect = plt.Rectangle((x, q1), width, height, fill=False,
                         edgecolor=color, linewidth=1.2, zorder=zorder + 1)
    ax.add_patch(rect)


# ============================================================================
# 4. GRID RECIPES  (04-grid-recipes.md)
# ============================================================================

def build_grid(recipe: str, *, fig: Figure | None = None,
                figsize: tuple[float, float] | None = None,
                n: int = 5,
                width_ratios: Sequence[float] | None = None,
                height_ratios: Sequence[float] | None = None,
                wspace: float | None = None,
                hspace: float | None = None,
                polar: bool = False,
                ) -> tuple[Figure, list[Axes]]:
    """Build a multi-panel figure from a recipe key. Returns (fig, axes-flat).

    Implemented recipes: R0 R1 R2 R3 R4 R5 R6 R8 R9.
    Stubs raising NotImplementedError: R7 R10 R11 (low frequency in corpus).
    """
    if recipe == "R0_single_panel":
        fig = fig or plt.figure(figsize=figsize or (6.5, 6.0))
        ax = fig.add_subplot(111, polar=polar)
        return fig, [ax]

    if recipe == "R1_two_panel_horizontal":
        fig = fig or plt.figure(figsize=figsize or (12, 5))
        wr = list(width_ratios) if width_ratios else [1, 1]
        gs = GridSpec(1, 2, width_ratios=wr,
                      wspace=wspace if wspace is not None else 0.25)
        ax_l = fig.add_subplot(gs[0, 0]); ax_r = fig.add_subplot(gs[0, 1])
        return fig, [ax_l, ax_r]

    if recipe == "R2_two_by_two_storyboard":
        fig = fig or plt.figure(figsize=figsize or (11, 9))
        gs = GridSpec(2, 2,
                      hspace=hspace if hspace is not None else 0.30,
                      wspace=wspace if wspace is not None else 0.30)
        axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(2)]
        return fig, axes

    if recipe == "R3_two_by_three_grid":
        fig = fig or plt.figure(figsize=figsize or (15, 9))
        gs = GridSpec(2, 3,
                      hspace=hspace if hspace is not None else 0.35,
                      wspace=wspace if wspace is not None else 0.25)
        axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
        return fig, axes

    if recipe == "R4_three_panel_horizontal":
        fig = fig or plt.figure(figsize=figsize or (15, 5))
        axs = fig.subplots(1, 3, sharey=True)
        return fig, list(axs)

    if recipe == "R5_n_by_n_pairwise":
        fig = fig or plt.figure(figsize=figsize or (2.4 * n, 2.4 * n))
        gs = GridSpec(n, n,
                      hspace=hspace if hspace is not None else 0.05,
                      wspace=wspace if wspace is not None else 0.05)
        axes = [fig.add_subplot(gs[i, j]) for i in range(n) for j in range(n)]
        return fig, axes

    if recipe == "R6_four_panel_band":
        fig = fig or plt.figure(figsize=figsize or (16, 4))
        axs = fig.subplots(1, 4, sharey=True)
        return fig, list(axs)

    if recipe == "R8_main_with_marginal":
        fig = fig or plt.figure(figsize=figsize or (8, 8))
        gs = GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                      hspace=hspace if hspace is not None else 0.05,
                      wspace=wspace if wspace is not None else 0.05)
        ax_top    = fig.add_subplot(gs[0, 0])
        ax_main   = fig.add_subplot(gs[1, 0])
        ax_right  = fig.add_subplot(gs[1, 1])
        ax_corner = fig.add_subplot(gs[0, 1]); ax_corner.axis("off")
        return fig, [ax_main, ax_top, ax_right, ax_corner]

    if recipe == "R9_inset_overlay":
        fig = fig or plt.figure(figsize=figsize or (8, 5.5))
        ax = fig.add_subplot(111)
        rect = [0.55, 0.35, 0.40, 0.35]
        ax_ins = ax.inset_axes(rect, zorder=10)
        # Fully opaque so main artists never bleed through (corpus discipline)
        ax_ins.set_facecolor("white")
        ax_ins.patch.set_alpha(1.0)
        # Cover anything behind via a backing white rectangle on the parent axis
        # (inset_axes alone doesn't always block lower-zorder artists)
        from matplotlib.patches import Rectangle
        backing = Rectangle((rect[0], rect[1]), rect[2], rect[3],
                            transform=ax.transAxes,
                            facecolor="white", edgecolor="none", zorder=9)
        ax.add_patch(backing)
        for s in ax_ins.spines.values():
            s.set_linewidth(0.8); s.set_color("#222")
        return fig, [ax, ax_ins]

    if recipe == "R7_dense_2x6_lineup":
        fig = fig or plt.figure(figsize=figsize or (20, 7))
        gs = GridSpec(2, 6,
                      hspace=hspace if hspace is not None else 0.40,
                      wspace=wspace if wspace is not None else 0.30)
        axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(6)]
        return fig, axes

    if recipe == "R10_asymmetric_top_wide":
        # 1 wide top + 2 narrow below (SHAP composite, global_local arc default)
        fig = fig or plt.figure(figsize=figsize or (11, 9))
        gs = GridSpec(2, 2,
                      height_ratios=list(height_ratios) if height_ratios else [1, 1],
                      hspace=hspace if hspace is not None else 0.35,
                      wspace=wspace if wspace is not None else 0.25)
        ax_top = fig.add_subplot(gs[0, :])
        ax_bl  = fig.add_subplot(gs[1, 0])
        ax_br  = fig.add_subplot(gs[1, 1])
        return fig, [ax_top, ax_bl, ax_br]

    if recipe == "R11_triple_y_axis":
        fig = fig or plt.figure(figsize=figsize or (10, 5.5))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        ax3 = ax1.twinx()
        ax3.spines["right"].set_position(("outward", 60))
        return fig, [ax1, ax2, ax3]

    raise KeyError(f"unknown recipe {recipe!r}; see 04-grid-recipes.md")


# ============================================================================
# 5. NARRATIVE ARCS  (06-narrative-arcs.md)
# ============================================================================

ARCS = ("hero", "single_focus", "multipanel_grid", "global_local",
        "n×n_pairwise", "marginal_joint", "train_test_diagnostic",
        "composite_two_lane", "mirror_compare", "inset_overlay")


def select_narrative_arc(dataProfile: dict, chartPlan: dict | None = None) -> str:
    """Heuristic arc selector matching `06-narrative-arcs.md` decision matrix."""
    cp = chartPlan or {}
    if dataProfile.get("has_train_test_split"):
        return "train_test_diagnostic"
    if cp.get("requested_inset"):
        return "inset_overlay"
    if cp.get("has_marginal_distribution"):
        return "marginal_joint"
    if cp.get("has_correlation_matrix"):
        return "n×n_pairwise"
    if cp.get("has_shap_global") and cp.get("has_shap_local"):
        return "global_local"
    if cp.get("bipolar_or_mirror"):
        return "mirror_compare"
    panels = cp.get("panels") or []
    if len(panels) >= 4 and len({p.get("family") for p in panels}) == 1:
        return "multipanel_grid"
    if len(panels) == 2 and len({p.get("family") for p in panels}) > 1:
        return "composite_two_lane"
    if cp.get("is_headline"):
        return "hero"
    return "single_focus"


_ARC_REQUIRED_MOTIFS = {
    # 'hero' is single-panel headline. Sub-types differentiate polar vs cartesian.
    "hero":                  ["colored_marker_edge"],                  # universal hero requirement
    "hero.polar":            ["polygon_polar_grid", "colored_marker_edge"],
    "hero.cartesian":        ["colored_marker_edge"],
    "hero.dual_axis":        ["twin_axes_color_spines", "colored_marker_edge"],
    "single_focus":          ["alpha_layered_scatter"],
    "multipanel_grid":       ["panel_label", "colored_marker_edge", "dotted_zero_axhline"],
    "global_local":          ["shared_feature_ordering", "colored_marker_edge", "dotted_zero_axhline"],
    "n×n_pairwise":          ["upper_triangle_split", "outer_only_labels"],
    "marginal_joint":        ["density_color_scatter", "perfect_fit_diagonal", "marginal_axes_off"],
    "train_test_diagnostic":              ["metric_text_box"],
    "train_test_diagnostic.scatter":      ["metric_text_box", "perfect_fit_diagonal", "colored_marker_edge"],
    "train_test_diagnostic.time_series":  ["metric_text_box", "error_band_fill_between", "group_divider_axvline"],
    "composite_two_lane":    ["shared_feature_ordering", "dotted_zero_axhline"],
    "mirror_compare":        ["dotted_zero_axhline", "bipolar_palette"],
    "inset_overlay":         ["axes_inset_overlay", "colored_marker_edge"],
}


def arc_required_motifs(arc: str, *, chart_family: str | None = None) -> list[str]:
    """Return mandatory motif keys for the chosen narrative arc.

    For arcs with sub-types, pass `chart_family` to disambiguate:
      - hero + 'radar' / 'mirror_radial' → polar sub-type
      - hero + 'dual_axis'                → dual_axis sub-type
      - hero + 'scatter_regression' / 'forest' / 'box' / 'violin' → cartesian sub-type
      - train_test_diagnostic + 'scatter_regression' → scatter sub-type
      - train_test_diagnostic + 'time_series_pi'      → time-series sub-type
    Default (no chart_family): return the arc's universal motifs.
    """
    if arc == "hero" and chart_family:
        if chart_family in {"radar", "mirror_radial", "polar"}:
            return list(_ARC_REQUIRED_MOTIFS["hero.polar"])
        if chart_family in {"dual_axis"}:
            return list(_ARC_REQUIRED_MOTIFS["hero.dual_axis"])
        return list(_ARC_REQUIRED_MOTIFS["hero.cartesian"])
    if arc == "train_test_diagnostic" and chart_family:
        if chart_family in {"scatter_regression", "predicted_actual"}:
            return list(_ARC_REQUIRED_MOTIFS["train_test_diagnostic.scatter"])
        if chart_family in {"time_series_pi", "time_series"}:
            return list(_ARC_REQUIRED_MOTIFS["train_test_diagnostic.time_series"])
    if arc not in _ARC_REQUIRED_MOTIFS:
        raise KeyError(f"unknown arc {arc!r}; choices: {sorted(_ARC_REQUIRED_MOTIFS)}")
    return list(_ARC_REQUIRED_MOTIFS[arc])


_ARC_DEFAULT_GRID = {
    "hero":                  "R0_single_panel",
    "single_focus":          "R0_single_panel",
    "multipanel_grid":       "R3_two_by_three_grid",
    "global_local":          "R10_asymmetric_top_wide",
    "n×n_pairwise":          "R5_n_by_n_pairwise",
    "marginal_joint":        "R8_main_with_marginal",
    "train_test_diagnostic": "R0_single_panel",
    "composite_two_lane":    "R1_two_panel_horizontal",
    "mirror_compare":        "R0_single_panel",
    "inset_overlay":         "R9_inset_overlay",
}


def arc_default_grid(arc: str, panel_count: int = 1) -> str:
    """Return the default grid recipe key for the arc.

    Overrides:
      multipanel_grid + panel_count <= 4 → R2 (2x2)
      multipanel_grid + panel_count >= 9 → R5 (3x3 / n×n)
    """
    if arc == "multipanel_grid":
        if panel_count <= 4:
            return "R2_two_by_two_storyboard"
        if panel_count >= 9:
            return "R5_n_by_n_pairwise"
    return _ARC_DEFAULT_GRID[arc]


# ============================================================================
# 6. ZORDER RECIPES  (02-zorder-recipes.md)
# ============================================================================

_ZORDER_TIER = {
    "grid":        0,
    "background":  1,
    "fill":        2,
    "primary":     4,
    "reference":   6,
    "error":       8,
    "highlight":  10,
}


def apply_zorder_recipe(family: str, ax: Axes, layers: dict[str, list]) -> None:
    """Re-tag artist `zorder` attributes by semantic role.

    family: 'scatter_regression' | 'forest' | 'dual_axis' | 'radar'
            | 'shap_composite' | 'marginal_joint' (plus stubs for
            'time_series_pi' | 'lollipop' | 'gradient_box' | 'inset_distribution').
    layers: dict mapping role-key → list of artist objects (or single artist).
            Roles: 'grid', 'background', 'fill', 'primary', 'reference',
                    'error', 'highlight'.
    """
    if family in {"scatter_regression", "forest", "dual_axis", "radar",
                  "shap_composite", "marginal_joint", "time_series_pi",
                  "lollipop", "gradient_box", "inset_distribution"}:
        for role, artists in layers.items():
            if role not in _ZORDER_TIER:
                raise KeyError(f"role {role!r} unknown; "
                               f"choices: {sorted(_ZORDER_TIER)}")
            zord = _ZORDER_TIER[role]
            seq = artists if isinstance(artists, (list, tuple)) else [artists]
            for art in seq:
                try:
                    art.set_zorder(zord)
                except AttributeError:
                    # Some collection-like objects may need set_zorder_(?)
                    pass
    else:
        raise KeyError(f"family {family!r} has no zorder recipe; "
                       f"see 02-zorder-recipes.md")


# ============================================================================
# 7. CONVENIENCE: ONE-CALL CHART BOOTSTRAP
# ============================================================================

def bootstrap_chart(arc: str, *,
                     panel_count: int = 1,
                     variant: str = "default",
                     palette: str = "morandi_sci_4",
                     journalProfile: dict | None = None,
                     figsize: tuple[float, float] | None = None,
                     ) -> tuple[Figure, list[Axes], list[str]]:
    """Bootstrap a figure from a narrative arc — applies kernel + grid + palette.

    Returns (fig, axes_flat, palette_hex_list).

    Equivalent to:
        apply_journal_kernel(variant, journalProfile)
        recipe = arc_default_grid(arc, panel_count)
        fig, axes = build_grid(recipe, figsize=figsize)
        palette = resolve_palette(palette, journalProfile=journalProfile)
    """
    apply_journal_kernel(variant, journalProfile)
    recipe = arc_default_grid(arc, panel_count)
    fig, axes = build_grid(recipe, figsize=figsize)
    pal = resolve_palette(palette, journalProfile=journalProfile)
    return fig, axes, pal


# ============================================================================
# 8. FOREST PLOT (cycle 2 addition)
# ============================================================================

def add_forest_panel(ax, hrs, lower, upper, labels, *,
                      color="#3C5488",
                      reference_line=1.0,
                      log_scale=True,
                      show_yticklabels=True,
                      annotation_format="{hr:.2f} ({lo:.2f}-{hi:.2f})",
                      title=None):
    """One-call forest panel: dashed reference line + HR markers with asymmetric
    CI whiskers + per-row HR(CI) annotation column at right edge.

    Anchor cases: HR multi-cohort forest (Nature Comms), risk-ratio caterpillar.
    Annotation is positioned via axes-fraction (x=0.99) so it never collides
    with the marker positions on log scale.
    """
    n = len(hrs)
    y_pos = np.arange(n)
    hrs = np.asarray(hrs, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)

    ax.xaxis.grid(True, linestyle=':', color='#E0E0E0',
                  linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.axvline(reference_line, color='#888888', linestyle='--',
               linewidth=1.0, zorder=1)

    xerr = [hrs - lower, upper - hrs]
    ax.errorbar(hrs, y_pos, xerr=xerr, fmt='o',
                color=color, ecolor=color, elinewidth=2, capsize=4,
                markersize=9, markeredgecolor='white', markeredgewidth=0.6,
                zorder=10)

    for i, (hr, lo, hi) in enumerate(zip(hrs, lower, upper)):
        ax.text(0.99, y_pos[i],
                annotation_format.format(hr=hr, lo=lo, hi=hi),
                transform=ax.get_yaxis_transform(),
                ha='right', va='center',
                fontsize=6, color='#222',
                family='monospace', zorder=15,
                bbox=dict(boxstyle='round,pad=0.15',
                          fc='white', ec='none', alpha=0.85))

    if log_scale:
        ax.set_xscale('log')
        from matplotlib.ticker import LogLocator, ScalarFormatter
        ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,), numticks=5))
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        ax.xaxis.set_major_formatter(formatter)

    ax.set_yticks(y_pos)
    if show_yticklabels:
        ax.set_yticklabels(labels, fontsize=6)
    else:
        ax.set_yticklabels([])
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if title:
        ax.set_title(title, color=color, fontsize=8, fontweight='bold')
