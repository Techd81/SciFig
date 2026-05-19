"""Dedicated model-diagnostic generators for the chart registry."""

from __future__ import annotations

from statistics import NormalDist
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
    return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))


def _categorical_palette(palette: dict[str, Any]) -> list[str]:
    return list(palette.get("categorical",
                           ["#000000", "#E69F00", "#56B4E9", "#009E73",
                            "#F0E442", "#0072B2"]))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _status(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _clean_numeric(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    return values[np.isfinite(values)]


def _distribution_values(df: pd.DataFrame, roles: dict[str, str]) -> np.ndarray:
    numeric = _numeric_columns(df)
    residual_col = roles.get("residual")
    if residual_col in df.columns:
        return _clean_numeric(df[residual_col])

    actual_col = roles.get("actual") or roles.get("y")
    fitted_col = roles.get("predicted") or roles.get("score") or roles.get("x")
    if actual_col in df.columns and fitted_col in df.columns:
        actual = pd.to_numeric(df[actual_col], errors="coerce")
        fitted = pd.to_numeric(df[fitted_col], errors="coerce")
        return _clean_numeric(actual - fitted)

    value_col = roles.get("value") or (numeric[0] if numeric else None)
    if value_col in df.columns:
        return _clean_numeric(df[value_col])
    return np.array([], dtype=float)


def _prediction_frame(df: pd.DataFrame, roles: dict[str, str]) -> tuple[pd.DataFrame, str | None]:
    numeric = _numeric_columns(df)
    fitted_col = roles.get("predicted") or roles.get("score") or roles.get("x") or (numeric[0] if numeric else None)
    residual_col = roles.get("residual")
    actual_col = roles.get("actual") or roles.get("y") or roles.get("value")
    if fitted_col not in df.columns:
        return pd.DataFrame(), "Need fitted/predicted values"

    fitted = pd.to_numeric(df[fitted_col], errors="coerce")
    if residual_col in df.columns:
        residual = pd.to_numeric(df[residual_col], errors="coerce")
    elif actual_col in df.columns:
        actual = pd.to_numeric(df[actual_col], errors="coerce")
        residual = actual - fitted
    elif len(numeric) >= 2:
        actual = pd.to_numeric(df[numeric[1]], errors="coerce")
        residual = actual - fitted
    else:
        return pd.DataFrame(), "Need residual or actual values"

    frame = pd.DataFrame({"fitted": fitted, "residual": residual}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < 3:
        return pd.DataFrame(), "Need >=3 finite fitted-residual pairs"
    return frame, None


def _standardize(values: np.ndarray) -> np.ndarray:
    values = values[np.isfinite(values)]
    if len(values) < 3:
        return np.array([], dtype=float)
    sd = float(values.std(ddof=1))
    if not np.isfinite(sd) or sd == 0:
        return np.array([], dtype=float)
    return (values - float(values.mean())) / sd


def _add_diagonal(ax: Any, x: np.ndarray, y: np.ndarray, *, color: str = "#777777") -> None:
    lo = float(np.nanmin([np.nanmin(x), np.nanmin(y)]))
    hi = float(np.nanmax([np.nanmax(x), np.nanmax(y)]))
    if np.isfinite(lo) and np.isfinite(hi) and lo != hi:
        ax.plot([lo, hi], [lo, hi], color=color, lw=0.7, ls="--", zorder=1)


@register_chart("qq")
def gen_qq(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
           rc_params: dict[str, Any], palette: dict[str, Any],
           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Normal Q-Q plot with a perfect-fit diagonal."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    values = _standardize(_distribution_values(df, _roles(data_profile)))
    if len(values) < 3:
        return _status(ax, "Q-Q plot", "Need >=3 varying numeric values")

    n = len(values)
    probs = (np.arange(1, n + 1) - 0.5) / n
    normal = NormalDist()
    theoretical = np.array([normal.inv_cdf(float(p)) for p in probs])
    sample = np.sort(values)
    ax.scatter(theoretical, sample, s=14, color=colors[1 % len(colors)], alpha=0.78, linewidths=0, zorder=2)
    _add_diagonal(ax, theoretical, sample)
    ax.set_xlabel("Theoretical quantiles")
    ax.set_ylabel("Sample quantiles")
    ax.set_title("Q-Q plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("pp_plot")
def gen_pp_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Normal P-P plot with a perfect-fit diagonal."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    values = _standardize(_distribution_values(df, _roles(data_profile)))
    if len(values) < 3:
        return _status(ax, "P-P plot", "Need >=3 varying numeric values")

    n = len(values)
    sample = np.sort(values)
    empirical = (np.arange(1, n + 1) - 0.5) / n
    normal = NormalDist()
    expected = np.array([normal.cdf(float(v)) for v in sample])
    ax.scatter(expected, empirical, s=14, color=colors[1 % len(colors)], alpha=0.78, linewidths=0, zorder=2)
    ax.plot([0, 1], [0, 1], color="#777777", lw=0.7, ls="--", zorder=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Expected cumulative probability")
    ax.set_ylabel("Observed cumulative probability")
    ax.set_title("P-P plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("residual_vs_fitted")
def gen_residual_vs_fitted(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                           rc_params: dict[str, Any], palette: dict[str, Any],
                           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Residual-vs-fitted scatter with a zero residual reference."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    frame, message = _prediction_frame(df, _roles(data_profile))
    if message:
        return _status(ax, "Residual vs fitted", message)

    ax.scatter(frame["fitted"], frame["residual"], s=15, color=colors[1 % len(colors)],
               alpha=0.75, linewidths=0)
    ax.axhline(0.0, color="#777777", lw=0.7, ls="--")
    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residuals")
    ax.set_title("Residual vs fitted", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("scale_location")
def gen_scale_location(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Scale-location diagnostic: sqrt(|standardized residuals|) vs fitted."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    frame, message = _prediction_frame(df, _roles(data_profile))
    if message:
        return _status(ax, "Scale-location", message)

    residual = frame["residual"].to_numpy(dtype=float)
    sd = float(residual.std(ddof=1))
    if not np.isfinite(sd) or sd == 0:
        return _status(ax, "Scale-location", "Need varying residuals")
    y = np.sqrt(np.abs((residual - float(residual.mean())) / sd))
    ax.scatter(frame["fitted"], y, s=15, color=colors[1 % len(colors)], alpha=0.75, linewidths=0)
    ax.axhline(float(np.median(y)), color="#777777", lw=0.7, ls="--")
    ax.set_xlabel("Fitted values")
    ax.set_ylabel("sqrt(|standardized residuals|)")
    ax.set_title("Scale-location", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
