"""Dedicated clinical-family generators for the chart registry.

km               — Kaplan-Meier step-function survival curves with censoring marks
forest           — Forest plot (horizontal point estimates + CI + null-effect line)
caterpillar_plot — Ranked linear-effect plot with confidence intervals
risk_ratio_plot  — Log-scale ratio-effect plot with confidence intervals
ci_plot          — Generic confidence-interval estimate plot
waterfall        — Waterfall chart (sorted descending vertical bars)
dose_response — Scatter + 4PL sigmoidal dose-response fit
"""

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
    return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))


def _categorical_palette(palette: dict[str, Any]) -> list[str]:
    return list(palette.get("categorical",
                           ["#000000", "#E69F00", "#56B4E9", "#009E73",
                            "#F0E442", "#0072B2"]))


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


def _short_label(value: Any, width: int = 18) -> str:
    text = str(value)
    return text if len(text) <= width else text[: width - 1] + "..."


def _unique_columns(*columns: Optional[str]) -> list[str]:
    result: list[str] = []
    for column in columns:
        if column and column not in result:
            result.append(column)
    return result


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _status(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _ci_columns(df: pd.DataFrame, roles: dict[str, str]) -> tuple[str | None, str | None, str | None, str | None]:
    numeric = _numeric_columns(df)
    effect_col = roles.get("estimate") or roles.get("effect") or roles.get("value") or (numeric[0] if numeric else None)
    ci_lo = roles.get("ci_low") or roles.get("ci_lo") or roles.get("low") or (numeric[1] if len(numeric) > 1 else None)
    ci_hi = roles.get("ci_high") or roles.get("ci_hi") or roles.get("high") or (numeric[2] if len(numeric) > 2 else None)
    label_col = roles.get("label") or roles.get("feature_id") or roles.get("group") or roles.get("category")
    return effect_col, ci_lo, ci_hi, label_col


def _ci_frame(df: pd.DataFrame, roles: dict[str, str], *, positive: bool = False,
              sort_by_effect: bool = False) -> tuple[pd.DataFrame, str | None]:
    effect_col, ci_lo, ci_hi, label_col = _ci_columns(df, roles)
    if effect_col not in df.columns or ci_lo not in df.columns or ci_hi not in df.columns:
        return pd.DataFrame(), "Need effect + ci_lo + ci_hi columns"

    numeric_frame = df[[effect_col, ci_lo, ci_hi]].apply(pd.to_numeric, errors="coerce")
    valid = np.isfinite(numeric_frame).all(axis=1)
    valid &= numeric_frame[ci_lo] <= numeric_frame[effect_col]
    valid &= numeric_frame[effect_col] <= numeric_frame[ci_hi]
    if positive:
        valid &= (numeric_frame[[effect_col, ci_lo, ci_hi]] > 0).all(axis=1)
    numeric_frame = numeric_frame[valid]
    if numeric_frame.empty:
        return pd.DataFrame(), "Need finite effect + CI values"

    if label_col and label_col in df.columns:
        labels = df.loc[numeric_frame.index, label_col].astype(str).tolist()
    else:
        labels = [str(i + 1) for i in range(len(numeric_frame))]
    frame = pd.DataFrame({
        "effect": numeric_frame[effect_col].to_numpy(dtype=float),
        "ci_low": numeric_frame[ci_lo].to_numpy(dtype=float),
        "ci_high": numeric_frame[ci_hi].to_numpy(dtype=float),
        "label": labels,
    }, index=numeric_frame.index)
    if sort_by_effect:
        frame = frame.sort_values("effect", ascending=True)
    return frame, None


def _draw_ci_panel(ax: Any, frame: pd.DataFrame, *, colors: list[str], title: str,
                   xlabel: str, reference_line: float, marker: str = "D",
                   log_scale: bool = False, annotate: bool = False) -> Any:
    n = len(frame)
    y_pos = np.arange(n, 0, -1)
    effect = frame["effect"].to_numpy(dtype=float)
    lo = frame["ci_low"].to_numpy(dtype=float)
    hi = frame["ci_high"].to_numpy(dtype=float)

    main_color = colors[1 % len(colors)] if colors else "#0072B2"
    muted_color = "#6B7280"
    for j in range(n):
        ax.plot([lo[j], hi[j]], [y_pos[j], y_pos[j]], color=muted_color, lw=0.9, solid_capstyle="round")
        ax.scatter(effect[j], y_pos[j], s=20, color=main_color, zorder=5, marker=marker,
                   edgecolor="white", linewidth=0.35)
        if annotate:
            ax.text(hi[j], y_pos[j], f" {effect[j]:.3g} [{lo[j]:.3g}, {hi[j]:.3g}]",
                    va="center", ha="left", fontsize=6, color="#333333")

    ax.axvline(reference_line, color="#888888", lw=0.6, ls="--")
    if log_scale:
        ax.set_xscale("log")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(frame["label"].astype(str).tolist())
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


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
    time_col = roles.get("survival_time") or roles.get("time") or (numeric[0] if numeric else None)
    event_col = roles.get("survival_event") or roles.get("event") or roles.get("status") or (numeric[1] if len(numeric) > 1 else None)
    if time_col not in df.columns or event_col not in df.columns:
        return _status(ax, "Kaplan-Meier", "Need time + event columns")

    groups: list[tuple[str, pd.DataFrame]]
    if group_col and group_col in df.columns:
        groups = [(str(n), g) for n, g in df.groupby(group_col, sort=False)]
    else:
        groups = [("_all", df)]

    for i, (name, part) in enumerate(groups):
        t = pd.to_numeric(part[time_col], errors="coerce")
        e = pd.to_numeric(part[event_col], errors="coerce")
        clean = pd.DataFrame({"t": t, "e": e}).dropna()
        clean = clean[np.isfinite(clean["t"]) & np.isfinite(clean["e"]) & clean["e"].isin([0, 1])]
        clean = clean.sort_values("t")
        if clean.empty:
            continue
        t_vals = clean["t"].to_numpy()
        e_vals = clean["e"].to_numpy(dtype=int)
        n_total = len(t_vals)

        # BUG-08 fix: aggregate by unique time so tied events/censors give the
        # same survival regardless of row order. Previous per-row decrement
        # produced S=0.0 for time=[1,1], event=[0,1]; correct value is 0.5.
        unique_times, inv = np.unique(t_vals, return_inverse=True)
        d = np.zeros(len(unique_times), dtype=int)  # event count per time
        c = np.zeros(len(unique_times), dtype=int)  # censor count per time
        for idx, ev in zip(inv, e_vals):
            if ev == 1:
                d[idx] += 1
            else:
                c[idx] += 1
        # At each unique time, n_at_risk = total remaining BEFORE this time's events/censors
        cumulative_remove = np.cumsum(d + c)
        n_at_risk = n_total - np.concatenate([[0], cumulative_remove[:-1]])

        surv = [1.0]
        times = [0.0]
        cens_x: list[float] = []
        cens_y: list[float] = []
        s = 1.0
        for k, t_k in enumerate(unique_times):
            if d[k] > 0 and n_at_risk[k] > 0:
                s = s * (n_at_risk[k] - d[k]) / n_at_risk[k]
                times.append(float(t_k))
                surv.append(s)
            if c[k] > 0:
                cens_x.append(float(t_k))
                cens_y.append(s)
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
    frame, message = _ci_frame(df, roles)
    if message:
        return _status(ax, "Forest", message)
    return _draw_ci_panel(ax, frame, colors=colors, title="Forest",
                          xlabel="Effect size (HR)", reference_line=1.0)


@register_chart("caterpillar_plot")
def gen_caterpillar_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Ranked linear-effect plot with confidence intervals and a zero line."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    frame, message = _ci_frame(df, roles, sort_by_effect=True)
    if message:
        return _status(ax, "Caterpillar plot", message)
    return _draw_ci_panel(ax, frame, colors=colors, title="Caterpillar plot",
                          xlabel="Effect size (95% CI)", reference_line=0.0,
                          marker="o")


@register_chart("risk_ratio_plot")
def gen_risk_ratio_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                        rc_params: dict[str, Any], palette: dict[str, Any],
                        col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Ratio-effect plot with log x-axis and no-effect reference at 1."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    frame, message = _ci_frame(df, roles, positive=True)
    if message:
        return _status(ax, "Risk ratio plot", message)
    return _draw_ci_panel(ax, frame, colors=colors, title="Risk ratio plot",
                          xlabel="Risk ratio (95% CI)", reference_line=1.0,
                          log_scale=True)


@register_chart("ci_plot")
def gen_ci_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Generic estimate-and-confidence-interval panel."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    frame, message = _ci_frame(df, roles)
    if message:
        return _status(ax, "CI plot", message)
    return _draw_ci_panel(ax, frame, colors=colors, title="CI plot",
                          xlabel="Estimate (95% CI)", reference_line=0.0,
                          marker="s", annotate=True)


@register_chart("swimmer_plot")
def gen_swimmer_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                     rc_params: dict[str, Any], palette: dict[str, Any],
                     col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Patient-level swimmer plot with horizontal follow-up intervals."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)
    id_col = _first_valid(df, roles.get("identifier"), roles.get("label"), roles.get("sample"), categorical[0] if categorical else None)
    start_col = _first_numeric_valid(df, roles.get("start"), roles.get("time"), roles.get("x"), numeric[0] if numeric else None)
    end_col = _first_numeric_valid(df, roles.get("end"), roles.get("survival_time"), roles.get("value"), roles.get("y"), numeric[1] if len(numeric) > 1 else None)
    if end_col == start_col:
        end_col = next((col for col in numeric if col != start_col), None)
    group_col = _first_valid(df, roles.get("group"), roles.get("category"), roles.get("survival_event"))
    if group_col == id_col:
        group_col = None
    if id_col is None or start_col is None or end_col is None:
        return _status(ax, "Swimmer plot", "Need subject + start + end columns")

    frame = df[_unique_columns(id_col, start_col, end_col, group_col)].copy()
    frame[start_col] = pd.to_numeric(frame[start_col], errors="coerce")
    frame[end_col] = pd.to_numeric(frame[end_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[id_col, start_col, end_col])
    frame = frame[frame[end_col] >= frame[start_col]].sort_values(end_col, ascending=True).tail(18)
    if frame.empty:
        return _status(ax, "Swimmer plot", "Need finite follow-up intervals")
    y = np.arange(len(frame))
    color_lookup: dict[str, str] = {}
    if group_col and group_col in frame.columns:
        groups = list(dict.fromkeys(frame[group_col].astype(str).tolist()))
        color_lookup = {name: colors[i % len(colors)] for i, name in enumerate(groups)}
    bar_colors = [
        color_lookup.get(str(row[group_col]), colors[i % len(colors)]) if group_col and group_col in frame.columns else colors[i % len(colors)]
        for i, (_, row) in enumerate(frame.iterrows())
    ]
    ax.barh(y, frame[end_col] - frame[start_col], left=frame[start_col], height=0.62,
            color=bar_colors, edgecolor="white", linewidth=0.4)
    ax.scatter(frame[end_col], y, marker=">", s=24, color="#333333", zorder=4, linewidth=0)
    ax.set_yticks(y, [_short_label(label, 16) for label in frame[id_col]])
    ax.set_xlabel("Follow-up time")
    ax.set_title("Swimmer plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


@register_chart("tornado_chart")
def gen_tornado_chart(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Sensitivity tornado chart with low/high deviations around a baseline."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    label_col = _first_valid(df, roles.get("label"), roles.get("feature_id"), roles.get("group"), roles.get("category"))
    low_col = _first_numeric_valid(df, roles.get("low"), roles.get("ci_low"), numeric[0] if numeric else None)
    high_col = _first_numeric_valid(df, roles.get("high"), roles.get("ci_high"), numeric[1] if len(numeric) > 1 else None)
    if high_col == low_col:
        high_col = next((col for col in numeric if col != low_col), None)
    base_col = _first_numeric_valid(df, roles.get("base"), roles.get("estimate"), roles.get("value"), numeric[2] if len(numeric) > 2 else None)
    if base_col in {low_col, high_col}:
        base_col = None
    if label_col is None or low_col is None or high_col is None:
        return _status(ax, "Tornado chart", "Need label + low + high columns")
    frame = df[_unique_columns(label_col, low_col, high_col, base_col)].copy()
    frame[low_col] = pd.to_numeric(frame[low_col], errors="coerce")
    frame[high_col] = pd.to_numeric(frame[high_col], errors="coerce")
    base_value = float(pd.to_numeric(frame[base_col], errors="coerce").median()) if base_col else 0.0
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[label_col, low_col, high_col])
    frame["impact"] = (frame[high_col] - frame[low_col]).abs()
    frame = frame.sort_values("impact", ascending=True).tail(12)
    if frame.empty:
        return _status(ax, "Tornado chart", "Need finite sensitivity ranges")
    y = np.arange(len(frame))
    low = frame[low_col].to_numpy(dtype=float)
    high = frame[high_col].to_numpy(dtype=float)
    left = np.minimum(low, base_value)
    right = np.maximum(high, base_value)
    ax.barh(y, base_value - left, left=left, color=colors[5 % len(colors)], alpha=0.78,
            edgecolor="white", linewidth=0.35)
    ax.barh(y, right - base_value, left=base_value, color=colors[1 % len(colors)], alpha=0.78,
            edgecolor="white", linewidth=0.35)
    ax.axvline(base_value, color="#333333", lw=0.8)
    ax.set_yticks(y, [_short_label(label, 18) for label in frame[label_col]])
    ax.set_xlabel("Outcome range")
    ax.set_title("Tornado chart", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


@register_chart("nomogram")
def gen_nomogram(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                 rc_params: dict[str, Any], palette: dict[str, Any],
                 col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Simplified nomogram with one horizontal points scale per predictor."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    label_col = _first_valid(df, roles.get("label"), roles.get("feature_id"), roles.get("group"), roles.get("category"))
    score_col = _first_numeric_valid(df, roles.get("score"), roles.get("value"), roles.get("estimate"), numeric[0] if numeric else None)
    if label_col is None or score_col is None:
        return _status(ax, "Nomogram", "Need predictor label + score columns")
    frame = df[[label_col, score_col]].copy()
    frame[score_col] = pd.to_numeric(frame[score_col], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().sort_values(score_col, ascending=True).tail(10)
    if frame.empty:
        return _status(ax, "Nomogram", "Need finite predictor scores")
    scores = frame[score_col].to_numpy(dtype=float)
    min_score = float(scores.min())
    span = float(scores.max() - min_score) or 1.0
    points = (scores - min_score) / span * 100.0
    y = np.arange(len(frame))
    for i, (_, row) in enumerate(frame.iterrows()):
        ax.plot([0, 100], [i, i], color="#D0D0D0", lw=0.7)
        ax.scatter(points[i], i, s=32, color=colors[i % len(colors)], edgecolor="white", linewidth=0.35, zorder=4)
        ax.text(102, i, f"{scores[i]:.3g}", va="center", ha="left", fontsize=6)
    ax.set_xlim(0, 112)
    ax.set_yticks(y, [_short_label(label, 18) for label in frame[label_col]])
    ax.set_xlabel("Points")
    ax.set_title("Nomogram", loc="center", fontweight="bold", pad=5)
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
    valid = np.isfinite(x_raw) & np.isfinite(y_raw) & (x_raw > 0)
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
        # Bound parameter b to keep ``x**b`` and ``c**(-b-1)`` numerically
        # stable during Levenberg-style iteration; without this the Jacobian
        # overflows for extreme dose ratios (cycle-22 numerical-stability bug).
        b = float(np.clip(b, -10.0, 10.0))
        with np.errstate(over="ignore", invalid="ignore"):
            denom = 1.0 + (x / c) ** b
            jac_d = 1.0 / denom
            jac_a = 1.0 - 1.0 / denom
            jac_c_ = (d - a) * b * (x ** b) * (c ** (-b - 1)) / (denom ** 2)
            jac_b_ = -(d - a) * np.log(x / c) * (x / c) ** b / (denom ** 2)
        # Drop rows where any Jacobian entry is non-finite — they would
        # poison the lstsq solve. If too few rows remain, stop iterating.
        finite_rows = np.isfinite(jac_d) & np.isfinite(jac_a) & np.isfinite(jac_c_) & np.isfinite(jac_b_)
        if finite_rows.sum() < 4:
            break
        J = np.column_stack([
            jac_d[finite_rows], jac_a[finite_rows],
            jac_c_[finite_rows], jac_b_[finite_rows],
        ])
        r = (y - four_pl(log_x, a, b, c, d))[finite_rows]
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
