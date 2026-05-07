"""Dedicated clinical-family generators for the chart registry.

km         — Kaplan-Meier step-function survival curves with censoring marks
forest     — Forest plot (horizontal point estimates + CI + null-effect line)
waterfall  — Waterfall chart (sorted descending vertical bars)
dose_response — Scatter + 4PL sigmoidal dose-response fit
"""

from __future__ import annotations

from typing import Any, Optional
from math import log

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


# -- Kaplan-Meier -------------------------------------------------------------

@register_chart("km")
def gen_km(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
           rc_params: dict[str, Any], palette: dict[str, Any],
           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Kaplan-Meier survival curve with step-function and censoring tick marks."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    group_col = roles.get("group")
    numeric = _numeric_columns(df)
    time_col = roles.get("time") or (numeric[0] if numeric else None)
    event_col = roles.get("event") or roles.get("status") or (numeric[1] if len(numeric) > 1 else None)
    if time_col not in df.columns or event_col not in df.columns:
        ax.text(0.5, 0.5, "Need time + event columns", ha="center",
                va="center", transform=ax.transAxes)
        ax.set_title("Kaplan-Meier", loc="center", fontweight="bold", pad=5)
        return ax

    groups: list[tuple[str, pd.DataFrame]]
    if group_col and group_col in df.columns:
        groups = [(str(n), g) for n, g in df.groupby(group_col, sort=False)]
    else:
        groups = [("_all", df)]

    for i, (name, part) in enumerate(groups):
        t = pd.to_numeric(part[time_col], errors="coerce")
        e = pd.to_numeric(part[event_col], errors="coerce")
        clean = pd.DataFrame({"t": t, "e": e}).dropna().sort_values("t")
        if clean.empty:
            continue
        t_vals = clean["t"].to_numpy()
        e_vals = clean["e"].to_numpy(dtype=int)
        n = len(t_vals)
        surv = [1.0]
        times = [0.0]
        cens_x: list[float] = []
        cens_y: list[float] = []
        remaining = n
        for j in range(n):
            if e_vals[j] == 1:
                surv.append(surv[-1] * (remaining - 1) / remaining)
                times.append(t_vals[j])
            else:
                cens_x.append(t_vals[j])
                cens_y.append(surv[-1])
            remaining -= 1
        color = colors[i % len(colors)]
        ax.step(times, surv, where="post", color=color, lw=1.1, label=name)
        if cens_x:
            ax.scatter(cens_x, cens_y, marker="|", s=28, lw=0.9,
                       color=color, zorder=5)

    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Time")
    ax.set_ylabel("Survival probability")
    ax.set_title("Kaplan-Meier", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- Forest plot --------------------------------------------------------------

@register_chart("forest")
def gen_forest(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
               rc_params: dict[str, Any], palette: dict[str, Any],
               col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Forest plot — horizontal point estimates with CI and null-effect line."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    effect_col = roles.get("effect") or roles.get("value") or (numeric[0] if numeric else None)
    ci_lo = roles.get("ci_lo") or (numeric[1] if len(numeric) > 1 else None)
    ci_hi = roles.get("ci_hi") or (numeric[2] if len(numeric) > 2 else None)
    if effect_col not in df.columns or ci_lo not in df.columns or ci_hi not in df.columns:
        ax.text(0.5, 0.5, "Need effect + ci_lo + ci_hi columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Forest", loc="center", fontweight="bold", pad=5)
        return ax

    n = len(df)
    y_pos = np.arange(n, 0, -1)
    eff = pd.to_numeric(df[effect_col], errors="coerce").to_numpy()
    lo = pd.to_numeric(df[ci_lo], errors="coerce").to_numpy()
    hi = pd.to_numeric(df[ci_hi], errors="coerce").to_numpy()
    for j in range(n):
        color = colors[j % len(colors)]
        ax.plot([lo[j], hi[j]], [y_pos[j], y_pos[j]], color=color, lw=1.0)
        ax.scatter(eff[j], y_pos[j], s=20, color=color, zorder=5, marker="D")

    ax.axvline(1.0, color="#888888", lw=0.6, ls="--")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df.index if df.index.name else [str(i+1) for i in range(n)])
    ax.set_xlabel("Effect size (HR)")
    ax.set_title("Forest", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


# -- Waterfall ----------------------------------------------------------------

@register_chart("waterfall")
def gen_waterfall(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Waterfall chart — vertical bars sorted descending, coloured by category."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    value_col = roles.get("value") or roles.get("y") or (numeric[0] if numeric else None)
    if value_col not in df.columns:
        ax.text(0.5, 0.5, "Need a value column", ha="center",
                va="center", transform=ax.transAxes)
        ax.set_title("Waterfall", loc="center", fontweight="bold", pad=5)
        return ax

    values = pd.to_numeric(df[value_col], errors="coerce").dropna().sort_values(ascending=False)
    if values.empty:
        ax.set_title("Waterfall", loc="center", fontweight="bold", pad=5)
        return ax

    median_val = float(values.median())
    clrs = [colors[0] if v >= median_val else colors[1] for v in values]
    ax.bar(range(len(values)), values.to_numpy(), color=clrs, width=0.8)
    ax.axhline(median_val, color="#888888", lw=0.6, ls=":")
    ax.set_xlabel("Rank")
    ax.set_ylabel(value_col)
    ax.set_title("Waterfall", loc="center", fontweight="bold", pad=5)
    ax.set_xticks([])
    _decorate_axes(ax)
    return ax


# -- Dose-response ------------------------------------------------------------

@register_chart("dose_response")
def gen_dose_response(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Scatter + 4PL sigmoidal dose-response fit."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    dose_col = roles.get("dose") or roles.get("x") or (numeric[0] if numeric else None)
    resp_col = roles.get("response") or roles.get("y") or roles.get("value") or (numeric[1] if len(numeric) > 1 else None)
    if dose_col not in df.columns or resp_col not in df.columns:
        ax.text(0.5, 0.5, "Need dose + response columns", ha="center",
                va="center", transform=ax.transAxes)
        ax.set_title("Dose-response", loc="center", fontweight="bold", pad=5)
        return ax

    clean = df[[dose_col, resp_col]].apply(pd.to_numeric, errors="coerce").dropna()
    x_raw = clean[dose_col].to_numpy()
    y_raw = clean[resp_col].to_numpy()
    valid = x_raw > 0
    x = x_raw[valid]
    y = y_raw[valid]
    if len(x) < 4:
        ax.text(0.5, 0.5, "Need >=4 positive dose points", ha="center",
                va="center", transform=ax.transAxes)
        ax.set_title("Dose-response", loc="center", fontweight="bold", pad=5)
        return ax

    log_x = np.log10(x)
    a = float(y.min())
    d = float(y.max())
    c = float(np.median(x))
    b = 1.0

    def four_pl(lx: np.ndarray, a_: float, b_: float, c_: float, d_: float) -> np.ndarray:
        return d_ + (a_ - d_) / (1.0 + (10.0 ** (b_ * (lx - np.log10(c_)))))

    for _ in range(50):
        denom = 1.0 + (x / c) ** b
        jac_d = 1.0 / denom
        jac_a = 1.0 - 1.0 / denom
        jac_c_ = (d - a) * b * (x ** b) * (c ** (-b - 1)) / (denom ** 2)
        jac_b_ = -(d - a) * np.log(x / c) * (x / c) ** b / (denom ** 2)
        J = np.column_stack([jac_d, jac_a, jac_c_, jac_b_])
        r = y - four_pl(log_x, a, b, c, d)
        try:
            delta, _, _, _ = np.linalg.lstsq(J, r, rcond=None)
        except np.linalg.LinAlgError:
            break
        a += float(delta[0])
        d += float(delta[1])
        c = max(c + float(delta[2]), x.min() / 100)
        b += float(delta[3])

    ax.scatter(x, y, s=12, color=colors[1 % len(colors)], alpha=0.75, linewidths=0, label="Observed")
    x_line = np.logspace(np.log10(x.min()), np.log10(x.max()), 80)
    y_line = four_pl(np.log10(x_line), a, b, c, d)
    ax.plot(x_line, y_line, color="#222222", lw=1.1, label="4PL fit")
    ax.set_xscale("log")
    ax.set_xlabel(f"{dose_col} (log)")
    ax.set_ylabel(resp_col)
    ax.set_title("Dose-response", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
