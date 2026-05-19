"""Engineering and materials chart generators."""

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
    if isinstance(profile, dict):
        return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))
    return {}


def _colors(palette: dict[str, Any]) -> list[str]:
    return list(palette.get("categorical", ["#1F4E79", "#D55E00", "#009E73", "#CC79A7", "#F0E442"]))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _first_existing(df: pd.DataFrame, candidates: tuple[str | None, ...]) -> str | None:
    lowered = {str(c).lower().replace(" ", "_").replace("-", "_"): str(c) for c in df.columns}
    for candidate in candidates:
        if candidate is None:
            continue
        key = str(candidate).lower().replace(" ", "_").replace("-", "_")
        if key in lowered:
            return lowered[key]
    return None


def _xy_columns(
    df: pd.DataFrame,
    profile: Any,
    x_candidates: tuple[str | None, ...],
    y_candidates: tuple[str | None, ...],
) -> tuple[str | None, str | None]:
    roles = _roles(profile)
    numeric = _numeric_columns(df)
    x_col = _first_existing(df, x_candidates + (roles.get("x"), roles.get("time"), numeric[0] if numeric else None))
    y_col = _first_existing(
        df,
        y_candidates + (roles.get("value"), roles.get("y"), numeric[1] if len(numeric) > 1 else None),
    )
    if y_col == x_col:
        y_col = next((col for col in numeric if col != x_col), None)
    return x_col, y_col


def _clean_xy(df: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    frame = df[[x_col, y_col]].copy()
    frame[x_col] = pd.to_numeric(frame[x_col], errors="coerce")
    frame[y_col] = pd.to_numeric(frame[y_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[x_col, y_col])
    return frame.sort_values(x_col)


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.6, pad=2)


def _status(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


def _line_panel(
    ax: Any,
    frame: pd.DataFrame,
    x_col: str,
    y_col: str,
    *,
    color: str,
    title: str,
    marker: str | None = None,
) -> Any:
    ax.plot(frame[x_col], frame[y_col], color=color, lw=1.05, marker=marker, markersize=2.6 if marker else 0)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("stress_strain")
def gen_stress_strain(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Stress-strain curve with the elastic segment drawn as a clean profile."""
    ax = _get_ax(ax)
    x_col, y_col = _xy_columns(df, data_profile, ("strain", "epsilon", "extension"), ("stress", "sigma", "load"))
    if not x_col or not y_col:
        return _status(ax, "Stress-strain", "Need strain + stress columns")
    frame = _clean_xy(df, x_col, y_col)
    if frame.empty:
        return _status(ax, "Stress-strain", "Need finite stress-strain values")
    _line_panel(ax, frame, x_col, y_col, color=_colors(palette)[0], title="Stress-strain", marker=None)
    peak_idx = frame[y_col].idxmax()
    ax.scatter([frame.loc[peak_idx, x_col]], [frame.loc[peak_idx, y_col]], s=18,
               color=_colors(palette)[1], edgecolor="white", linewidth=0.45, zorder=4)
    return ax


@register_chart("phase_diagram")
def gen_phase_diagram(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Phase diagram scatter/line panel with optional phase categories."""
    ax = _get_ax(ax)
    x_col, y_col = _xy_columns(df, data_profile, ("composition", "temperature", "temp", "x"), ("temperature", "value", "phase_y", "y"))
    if not x_col or not y_col:
        return _status(ax, "Phase diagram", "Need composition/temperature axes")
    frame = _clean_xy(df, x_col, y_col)
    if frame.empty:
        return _status(ax, "Phase diagram", "Need finite phase values")
    colors = _colors(palette)
    group_col = _first_existing(df, (_roles(data_profile).get("group"), "phase", "state", "region"))
    if group_col and group_col in df.columns:
        merged = df[[x_col, y_col, group_col]].copy()
        merged[x_col] = pd.to_numeric(merged[x_col], errors="coerce")
        merged[y_col] = pd.to_numeric(merged[y_col], errors="coerce")
        merged = merged.dropna(subset=[x_col, y_col, group_col])
        for i, (name, part) in enumerate(merged.groupby(group_col, sort=False)):
            ax.scatter(part[x_col], part[y_col], s=16, color=colors[i % len(colors)],
                       edgecolor="white", linewidth=0.35, label=str(name))
    else:
        ax.plot(frame[x_col], frame[y_col], color=colors[0], lw=1.0, marker="o", markersize=2.6)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title("Phase diagram", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("nyquist_plot")
def gen_nyquist_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Electrochemical Nyquist plot with equal scaling and point trace."""
    ax = _get_ax(ax)
    x_col, y_col = _xy_columns(df, data_profile, ("z_real", "zprime", "real", "re_z"), ("z_imag", "zimag", "imag", "im_z"))
    if not x_col or not y_col:
        return _status(ax, "Nyquist plot", "Need real + imaginary impedance columns")
    frame = _clean_xy(df, x_col, y_col)
    if frame.empty:
        return _status(ax, "Nyquist plot", "Need finite impedance values")
    y_values = frame[y_col].to_numpy(dtype=float)
    y_plot = -y_values if float(np.nanmean(y_values)) < 0 else y_values
    ax.plot(frame[x_col], y_plot, color=_colors(palette)[0], lw=1.0, marker="o", markersize=2.8)
    ax.set_xlabel("Z real")
    ax.set_ylabel("-Z imag")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Nyquist plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("xrd_pattern")
def gen_xrd_pattern(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """XRD intensity trace with stick markers at local maxima."""
    ax = _get_ax(ax)
    x_col, y_col = _xy_columns(df, data_profile, ("two_theta", "2theta", "theta", "angle"), ("intensity", "counts", "value"))
    if not x_col or not y_col:
        return _status(ax, "XRD pattern", "Need two-theta + intensity columns")
    frame = _clean_xy(df, x_col, y_col)
    if frame.empty:
        return _status(ax, "XRD pattern", "Need finite diffraction values")
    color = _colors(palette)[0]
    ax.plot(frame[x_col], frame[y_col], color=color, lw=0.9)
    y = frame[y_col].to_numpy(dtype=float)
    if len(y) >= 3:
        threshold = np.nanpercentile(y, 75)
        peak_mask = (y[1:-1] > y[:-2]) & (y[1:-1] > y[2:]) & (y[1:-1] >= threshold)
        peak_indices = np.where(peak_mask)[0] + 1
        for idx in peak_indices[:8]:
            ax.vlines(frame[x_col].iloc[idx], 0, y[idx], color=_colors(palette)[1], lw=0.6, alpha=0.8)
    ax.set_xlabel("2-theta")
    ax.set_ylabel("Intensity")
    ax.set_title("XRD pattern", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("ftir_spectrum")
def gen_ftir_spectrum(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """FTIR spectrum with conventional high-to-low wavenumber axis."""
    ax = _get_ax(ax)
    x_col, y_col = _xy_columns(df, data_profile, ("wavenumber", "wave_number", "cm-1", "cm1"), ("absorbance", "transmittance", "intensity"))
    if not x_col or not y_col:
        return _status(ax, "FTIR spectrum", "Need wavenumber + signal columns")
    frame = _clean_xy(df, x_col, y_col)
    if frame.empty:
        return _status(ax, "FTIR spectrum", "Need finite spectrum values")
    _line_panel(ax, frame, x_col, y_col, color=_colors(palette)[0], title="FTIR spectrum", marker=None)
    ax.invert_xaxis()
    return ax


@register_chart("dsc_thermogram")
def gen_dsc_thermogram(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """DSC thermogram with zero heat-flow reference."""
    ax = _get_ax(ax)
    x_col, y_col = _xy_columns(df, data_profile, ("temperature", "temp", "time"), ("heat_flow", "heatflow", "dsc", "value"))
    if not x_col or not y_col:
        return _status(ax, "DSC thermogram", "Need temperature + heat-flow columns")
    frame = _clean_xy(df, x_col, y_col)
    if frame.empty:
        return _status(ax, "DSC thermogram", "Need finite thermogram values")
    _line_panel(ax, frame, x_col, y_col, color=_colors(palette)[1], title="DSC thermogram", marker=None)
    ax.axhline(0, color="#333333", lw=0.7, linestyle="--")
    return ax


@register_chart("control_chart")
def gen_control_chart(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Process control chart with mean and three-sigma control limits."""
    ax = _get_ax(ax)
    x_col, y_col = _xy_columns(df, data_profile, ("sample", "run", "time", "index"), ("value", "measurement", "response", "y"))
    if not x_col or not y_col:
        return _status(ax, "Control chart", "Need sample + measurement columns")
    frame = _clean_xy(df, x_col, y_col)
    if frame.empty:
        return _status(ax, "Control chart", "Need finite control values")
    color = _colors(palette)[0]
    ax.plot(frame[x_col], frame[y_col], color=color, lw=0.95, marker="o", markersize=2.6)
    mean = float(frame[y_col].mean())
    sigma = float(frame[y_col].std(ddof=1)) if len(frame) > 1 else 0.0
    for y_ref, label, linestyle in [
        (mean, "Mean", "-"),
        (mean + 3 * sigma, "UCL", "--"),
        (mean - 3 * sigma, "LCL", "--"),
    ]:
        ax.axhline(y_ref, color="#333333", lw=0.7, linestyle=linestyle, label=label)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title("Control chart", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
