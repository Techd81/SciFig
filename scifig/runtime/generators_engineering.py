"""Engineering / spectra chart generators + dual-axis idiom.

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


def gen_control_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Shewhart control chart with mean line and +/-3sigma limits.

    Expects a numeric value column in semanticRoles["value"].  Points beyond
    the control limits are highlighted in red.  Center line shows the process
    mean; upper/lower limits are mean +/- 3 * std.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    _, value_col, _ = _resolve_roles(dataProfile)

    if value_col is None:
        raise ValueError("control_chart requires a numeric value column in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    values = df[value_col].dropna().values
    mean = np.mean(values)
    sigma = np.std(values, ddof=1)
    ucl, lcl = mean + 3 * sigma, mean - 3 * sigma

    x = np.arange(len(values))
    color_normal = palette.get("categorical", ["#0072B2"])[0]

    # In-control points
    in_ctrl = (values >= lcl) & (values <= ucl)
    ax.scatter(x[in_ctrl], values[in_ctrl], s=12, color=color_normal,
               linewidth=0.3, edgecolor="white", zorder=2)
    # Out-of-control points
    ooc = ~in_ctrl
    if ooc.any():
        ax.scatter(x[ooc], values[ooc], s=16, color="#C8553D",
                   linewidth=0.3, edgecolor="white", zorder=3)

    # Control limit lines
    ax.axhline(mean, color="black", linewidth=0.8, linestyle="-",
               solid_capstyle="round", label=f"Mean = {mean:.2f}")
    ax.axhline(ucl, color="#C8553D", linewidth=0.6, linestyle="--",
               label=f"+3σ = {ucl:.2f}")
    ax.axhline(lcl, color="#C8553D", linewidth=0.6, linestyle="--",
               label=f"−3σ = {lcl:.2f}")

    ax.set_xlabel("Observation")
    ax.set_ylabel(value_col)
    ax.legend(loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "control_chart")
    return ax


def gen_dsc_thermogram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """DSC thermogram: temperature vs heat flow (exo down convention).

    Expects columns: temperature and heat_flow in semanticRoles.
    Optionally marks onset/peak temperatures for thermal events.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    temp_col = roles.get("temperature") or roles.get("x")
    hf_col = roles.get("heat_flow") or roles.get("y") or roles.get("value")

    if temp_col is None or hf_col is None:
        raise ValueError("dsc_thermogram requires 'temperature' and 'heat_flow' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#D55E00"])[0]
    ax.plot(df[temp_col], df[hf_col], color=color, lw=0.8, solid_capstyle="round")
    ax.fill_between(df[temp_col], df[hf_col], alpha=0.1, color=color)

    # Annotate peak (most negative heat flow = strongest endotherm)
    peak_idx = df[hf_col].idxmin()
    peak_t = df.loc[peak_idx, temp_col]
    peak_hf = df.loc[peak_idx, hf_col]
    ax.annotate(f"Peak: {peak_t:.1f}", xy=(peak_t, peak_hf),
                xytext=(peak_t + 5, peak_hf * 0.85),
                fontsize=5, arrowprops=dict(arrowstyle="->", lw=0.4, color="black"))

    ax.set_xlabel("Temperature")
    ax.set_ylabel("Heat flow (exo down)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "dsc_thermogram")
    return ax


def gen_dual_axis(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Textbook dual-Y axis bar+spline line chart.

    Left axis carries pale context bars; right axis carries a saturated smooth
    line plus raw marker error bars.  Anchored to the Materials Today
    porosity-strength template.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    visual_plan = chartPlan.get("visualContentPlan", {})
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
            if name and name in df.columns:
                return name
            if name and str(name).lower() in lower_to_col:
                return lower_to_col[str(name).lower()]
        return None

    def _column_list(raw):
        if raw is None:
            return None
        if isinstance(raw, str):
            parts = [part.strip() for part in raw.replace(";", ",").split(",")]
            cols = []
            for part in parts:
                if part in df.columns:
                    cols.append(part)
                elif part.lower() in lower_to_col:
                    cols.append(lower_to_col[part.lower()])
            return cols or None
        if isinstance(raw, (list, tuple)):
            cols = []
            for item in raw:
                name = str(item)
                if name in df.columns:
                    cols.append(name)
                elif name.lower() in lower_to_col:
                    cols.append(lower_to_col[name.lower()])
            return cols or None
        return None

    use_hist_cumfreq_grid = (
        standalone
        and (
            visual_plan.get("useDualAxisHistCumfreqGrid")
            or "dual_axis_hist_cumfreq_grid" in template_motifs
            or "hist_cumfreq_grid" in template_motifs
            or "cumulative_frequency_grid" in template_motifs
            or "dual_axis_hist_cumfreq_grid" in patterns
            or "hist_cumfreq_grid" in patterns
            or "cumulative_frequency_grid" in patterns
        )
    )
    if use_hist_cumfreq_grid:
        draw_fn = globals().get("draw_dual_axis_hist_cumfreq_grid")
        if draw_fn is None:
            raise RuntimeError("draw_dual_axis_hist_cumfreq_grid helper is required for gen_dual_axis")
        grid_shape = visual_plan.get("dualAxisDistributionGridShape", [3, 3])
        if not isinstance(grid_shape, (list, tuple)) or len(grid_shape) != 2:
            grid_shape = [3, 3]
        value_cols = (
            visual_plan.get("dualAxisDistributionColumns")
            or roles.get("value_columns")
            or roles.get("variables")
            or roles.get("distribution_columns")
        )
        result = draw_fn(
            df,
            value_cols=_column_list(value_cols),
            nrows=int(grid_shape[0]),
            ncols=int(grid_shape[1]),
            bins=visual_plan.get("dualAxisDistributionBins", 15),
            figsize=tuple(visual_plan.get("dualAxisDistributionFigsize", [12.0, 10.0])),
            wspace=visual_plan.get("dualAxisDistributionWspace", 0.40),
            hspace=visual_plan.get("dualAxisDistributionHspace", 0.35),
            hist_color=visual_plan.get("dualAxisHistColor", "gray"),
            hist_edgecolor=visual_plan.get("dualAxisHistEdgeColor", "black"),
            hist_alpha=visual_plan.get("dualAxisHistAlpha", 0.70),
            line_color=visual_plan.get("dualAxisCumulativeColor", "blue"),
            marker=visual_plan.get("dualAxisCumulativeMarker", "o"),
            marker_size=visual_plan.get("dualAxisCumulativeMarkerSize", 4.0),
            line_width=visual_plan.get("dualAxisCumulativeLinewidth", 1.5),
            col_map=col_map,
        )
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        for motif in ("dual_axis_hist_cumfreq_grid", "cumulative_frequency_curve", "multipanel_distribution_matrix"):
            if motif not in planned_motifs:
                planned_motifs.append(motif)
            record_fn(visual_plan, motif)
        panel_count = int(result.get("panel_count", 0))
        for _ in range(panel_count):
            count_fn(visual_plan, "dualAxisEncodingCount")
            count_fn(visual_plan, "multiAxisEncodingCount")
            count_fn(visual_plan, "twinAxisPanelCount")
            count_fn(visual_plan, "histogramPanelCount")
            count_fn(visual_plan, "cumulativeCurveCount")
        count_fn(visual_plan, "sampleEncodingCount")
        visual_plan["dualAxisDistributionLayout"] = f"{int(grid_shape[0])}x{int(grid_shape[1])}"
        visual_plan["dualAxisDistributionGridShape"] = [int(grid_shape[0]), int(grid_shape[1])]
        visual_plan["dualAxisDistributionBins"] = int(result.get("bins", visual_plan.get("dualAxisDistributionBins", 15)))
        visual_plan["dualAxisDistributionVariableCount"] = len(result.get("columns") or [])
        visual_plan["dualAxisDistributionVariables"] = list(result.get("columns") or [])
        visual_plan["cumulativeFrequencyYLim"] = list(result.get("right_ylim", [0, 105]))
        visual_plan["independentPanelScales"] = True
        visual_plan["templateMatchMode"] = "case_020_dual_axis_hist_cumfreq_grid"
        return result["axes_left"][0]

    x_col = _first_column(roles.get("x"), roles.get("condition"), roles.get("group"), "group", "condition", "sample")
    bar_col = _first_column(
        roles.get("bar"),
        roles.get("left_y"),
        roles.get("primary_y"),
        roles.get("porosity"),
        "porosity",
        "left_y",
        "bar_value",
    )
    line_col = _first_column(
        roles.get("line"),
        roles.get("right_y"),
        roles.get("secondary_y"),
        roles.get("strength"),
        "strength",
        "right_y",
        "line_value",
    )
    bar_err_col = _first_column(roles.get("bar_error"), roles.get("left_error"), roles.get("porosity_error"), "por_err", "bar_err", "porosity_err")
    line_err_col = _first_column(roles.get("line_error"), roles.get("right_error"), roles.get("strength_error"), "str_err", "line_err", "strength_err")
    group_col = _first_column(roles.get("group_series"), roles.get("family"), roles.get("series"), roles.get("category"))
    if x_col is None or bar_col is None or line_col is None:
        raise ValueError("dual_axis requires x, bar/left_y, and line/right_y semantic roles")

    if standalone:
        fig, ax = plt.subplots(figsize=(118 * (1 / 25.4), 68 * (1 / 25.4)),
                           constrained_layout=True)

    palette_values = visual_plan.get("dualAxisPalette") or palette.get("materials_porosity_terracotta")
    if not palette_values:
        palette_values = palette.get("categorical", ["#CFE2F3", "#9BC2E6", "#F48E66"])[:3]
    if len(palette_values) < 3:
        palette_values = ["#CFE2F3", "#9BC2E6", "#F48E66"]
    draw_fn = globals().get("draw_textbook_dual_axis_bar_line")
    if draw_fn is None:
        raise RuntimeError("draw_textbook_dual_axis_bar_line helper is required for gen_dual_axis")
    result = draw_fn(
        ax,
        df,
        x_col=x_col,
        bar_col=bar_col,
        line_col=line_col,
        bar_err_col=bar_err_col,
        line_err_col=line_err_col,
        group_col=group_col,
        group_splits=visual_plan.get("dualAxisGroupSplits"),
        left_ylim=visual_plan.get("dualAxisLeftYlim"),
        right_ylim=visual_plan.get("dualAxisRightYlim"),
        palette=palette_values,
        spline_points=visual_plan.get("dualAxisSplinePoints", 300),
        xtick_rotation=visual_plan.get("dualAxisXtickRotation", 90),
        line_smoothing=visual_plan.get("dualAxisLineSmoothing", True),
        show_mean_line=visual_plan.get("dualAxisShowMeanLine", False),
        mean_line_label=visual_plan.get("dualAxisMeanLineLabel", "Mean"),
        bar_width=visual_plan.get("dualAxisBarWidth", 0.6),
        line_width=visual_plan.get("dualAxisLineWidth", 3.0),
        marker_size=visual_plan.get("dualAxisMarkerSize", 8.0),
        bar_edge_color=visual_plan.get("dualAxisBarEdgeColor"),
        col_map=col_map,
    )
    count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
    record_fn = globals().get("_record_template_motif", lambda *args, **kwargs: None)
    planned_motifs = visual_plan.setdefault("templateMotifs", [])
    motif = "textbook_dual_axis_bar_line"
    nature_motif = "nature_comms_dual_axis_bar_line"
    if nature_motif in template_motifs or nature_motif in patterns:
        motif = nature_motif
    if motif not in planned_motifs:
        planned_motifs.append(motif)
    record_fn(visual_plan, motif)
    count_fn(visual_plan, "dualAxisEncodingCount")
    count_fn(visual_plan, "multiAxisEncodingCount")
    count_fn(visual_plan, "sampleEncodingCount")
    if result.get("has_bar_error") or result.get("has_line_error"):
        count_fn(visual_plan, "errorBarLayerCount")
    visual_plan["groupDividerCount"] = len(result.get("divider_lines", []))
    visual_plan["dualAxisSpineTinted"] = True
    visual_plan["combinedLegend"] = True
    visual_plan["topSpineHidden"] = True
    visual_plan["dualAxisSplinePointCount"] = int(len(result.get("x_smooth", [])))
    visual_plan["dualAxisLayerSandwich"] = True
    if result.get("has_mean_line"):
        count_fn(visual_plan, "referenceLineCount")
        visual_plan["dualAxisMeanReferenceLine"] = True
    if motif == nature_motif:
        visual_plan["templateMatchMode"] = "case_026_nature_comms_dual_axis"
        visual_plan["dualAxisColorLinkedRightAxis"] = True
    elif "dual_axis" in patterns or motif in template_motifs:
        visual_plan["templateMatchMode"] = "case_012_dual_axis"
    if standalone:
        apply_chart_polish(result["ax_left"], "dual_axis")
    return result["ax_left"]


def gen_ftir_spectrum(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """FTIR spectrum: wavenumber vs absorbance with inverted x-axis.

    Expects columns: wavenumber (cm^-1) and absorbance (or transmittance) in
    semanticRoles. X-axis is inverted (high wavenumber on left) per FTIR convention.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    wn_col = roles.get("wavenumber") or roles.get("x")
    abs_col = roles.get("absorbance") or roles.get("transmittance") or roles.get("value")

    if wn_col is None or abs_col is None:
        raise ValueError("ftir_spectrum requires 'wavenumber' and 'absorbance' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#C8553D"])[0]
    ax.plot(df[wn_col], df[abs_col], color=color, lw=0.8, solid_capstyle="round")
    ax.fill_between(df[wn_col], df[abs_col], alpha=0.1, color=color)

    ax.set_xlabel(r"Wavenumber (cm$^{-1}$)")
    ax.set_ylabel("Absorbance")
    ax.invert_xaxis()
    if standalone:
        apply_chart_polish(ax, "ftir_spectrum")
    return ax


def gen_nyquist_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Nyquist plot: real vs imaginary impedance (Z' vs Z'').

    Expects columns: z_real and z_imaginary (or x/y) in semanticRoles.
    Optionally frequency column for color-coded annotation.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    real_col = roles.get("z_real") or roles.get("x")
    imag_col = roles.get("z_imaginary") or roles.get("y")
    freq_col = roles.get("frequency") or roles.get("value")

    if real_col is None or imag_col is None:
        raise ValueError("nyquist_plot requires 'z_real' and 'z_imaginary' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if freq_col and freq_col in df.columns:
        scatter = ax.scatter(df[real_col], df[imag_col], c=df[freq_col],
                             cmap="viridis", s=20, alpha=0.8, linewidth=0.3, edgecolors="white",
                             zorder=3)
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
        cbar.set_label("Frequency (Hz)", fontsize=5)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(df[real_col], df[imag_col], c=color, s=20, alpha=0.8,
                   linewidth=0.3, edgecolors="white", zorder=3)

    ax.plot(df[real_col], df[imag_col], color="#999999", lw=0.4, alpha=0.5, zorder=2)
    ax.set_xlabel(r"$Z'$ (Real, $\Omega$)")
    ax.set_ylabel(r"$Z''$ (Imaginary, $\Omega$)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "nyquist_plot")
    return ax


def gen_phase_diagram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Phase diagram: composition vs temperature with phase regions.

    Expects columns: composition (mole fraction, 0-1), temperature, and optionally
    phase (categorical region label) in semanticRoles. Plots a scatter with
    optional convex-hull outlines per phase region.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    comp_col = roles.get("composition") or roles.get("x")
    temp_col = roles.get("temperature") or roles.get("y")
    phase_col = roles.get("phase") or roles.get("group")

    if comp_col is None or temp_col is None:
        raise ValueError("phase_diagram requires 'composition' and 'temperature' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    if phase_col and phase_col in df.columns:
        categories = df[phase_col].unique()
        color_map = _extract_colors(palette, categories)
        for cat in categories:
            sub = df[df[phase_col] == cat]
            ax.scatter(sub[comp_col], sub[temp_col], c=color_map.get(cat, "#999999"),
                       s=15, alpha=0.7, linewidth=0.3, edgecolors="white", label=str(cat))
            # Convex hull outline
            try:
                from scipy.spatial import ConvexHull
                pts = sub[[comp_col, temp_col]].dropna().values
                if len(pts) >= 3:
                    hull = ConvexHull(pts)
                    for simplex in hull.simplices:
                        ax.plot(pts[simplex, 0], pts[simplex, 1],
                                color=color_map.get(cat, "#999999"), lw=0.8, alpha=0.6)
            except Exception:
                pass
        ax.legend(frameon=False, fontsize=5, title=phase_col, title_fontsize=5)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(df[comp_col], df[temp_col], c=color, s=15, alpha=0.7,
                   linewidth=0.3, edgecolors="white")

    ax.set_xlabel("Composition (mole fraction)")
    ax.set_ylabel("Temperature")
    ax.set_xlim(0, 1)
    if standalone:
        apply_chart_polish(ax, "phase_diagram")
    return ax


def gen_stress_strain(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Stress-strain curve for materials science.

    Plots strain (x) vs stress (y) with optional yield point annotation.
    Expects columns: strain (x-axis) and stress (y-axis) in semanticRoles.
    If a yield_strain/yield_stress column exists, annotates the yield point.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    strain_col = roles.get("strain") or roles.get("x")
    stress_col = roles.get("stress") or roles.get("y") or roles.get("value")

    if strain_col is None or stress_col is None:
        raise ValueError("stress_strain requires 'strain' and 'stress' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#0072B2"])[0]
    ax.plot(df[strain_col], df[stress_col], color=color, linewidth=0.8,
            solid_capstyle="round", zorder=2)

    # Yield point annotation if available
    yield_strain_col = roles.get("yield_strain")
    yield_stress_col = roles.get("yield_stress")
    if yield_strain_col and yield_stress_col and yield_strain_col in df.columns:
        ystrain = df[yield_strain_col].dropna().iloc[0]
        ystress = df[yield_stress_col].dropna().iloc[0]
        ax.plot(ystrain, ystress, "o", color="#C8553D", markersize=4, zorder=3)
        ax.annotate(f"Yield\n({ystrain:.2f}, {ystress:.1f})",
                    xy=(ystrain, ystress), xytext=(ystrain + 0.02, ystress * 0.9),
                    fontsize=5, arrowprops=dict(arrowstyle="->", lw=0.4, color="black"))

    ax.set_xlabel("Strain")
    ax.set_ylabel("Stress (MPa)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "stress_strain")
    return ax


def gen_xrd_pattern(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """X-ray diffraction (XRD) pattern with stick plot peaks.

    Plots 2-theta (x) vs intensity (y) as vertical sticks at peak positions.
    Expects columns: two_theta (x-axis) and intensity (y-axis) in semanticRoles.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    theta_col = roles.get("two_theta") or roles.get("x")
    intensity_col = roles.get("intensity") or roles.get("y") or roles.get("value")

    if theta_col is None or intensity_col is None:
        raise ValueError("xrd_pattern requires 'two_theta' and 'intensity' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#1F4E79"])[0]

    # Vertical stick plot
    theta = df[theta_col].dropna()
    intensity = df[intensity_col].dropna()
    common = theta.index.intersection(intensity.index)
    theta, intensity = theta.loc[common], intensity.loc[common]

    # Normalize intensity to [0, 1] for stick heights
    max_int = intensity.max()
    norm_int = intensity / max_int if max_int > 0 else intensity

    # Draw sticks
    for t, h in zip(theta, norm_int):
        ax.plot([t, t], [0, h], color=color, linewidth=0.6, solid_capstyle="round", zorder=2)

    ax.set_xlabel(r"2$\theta$ (degrees)")
    ax.set_ylabel("Relative intensity")
    ax.set_ylim(0, 1.1)
    if standalone:
        apply_chart_polish(ax, "xrd_pattern")
    return ax
