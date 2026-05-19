"""Dedicated ranked-effect and explainability generators."""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .registry import register_chart

POSITIVE = "#C0504D"
NEGATIVE = "#4F81BD"
NEUTRAL = "#6B7280"


def _get_ax(ax: Any = None) -> Any:
    if ax is not None:
        return ax
    _, new_ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4), constrained_layout=True)
    return new_ax


def _roles(profile: Any) -> dict[str, str]:
    if hasattr(profile, "semantic_roles"):
        return dict(profile.semantic_roles)
    return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    numeric = set(_numeric_columns(df))
    return [str(c) for c in df.columns if str(c) not in numeric]


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _status(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _first_existing(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {str(c).lower(): str(c) for c in df.columns}
    for candidate in candidates:
        key = candidate.lower()
        if key in lowered:
            return lowered[key]
    return None


def _feature_value_columns(df: pd.DataFrame, roles: dict[str, str]) -> tuple[str | None, str | None]:
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)
    feature_col = (
        roles.get("feature_id")
        or roles.get("identifier")
        or roles.get("label")
        or roles.get("group")
        or _first_existing(df, ("feature", "feature_name", "term", "variable", "name"))
        or (categorical[0] if categorical else None)
    )
    value_col = (
        roles.get("importance")
        or roles.get("value")
        or roles.get("y")
        or _first_existing(
            df,
            (
                "mean_abs_shap", "shap_value", "shap", "importance",
                "gain", "permutation", "permutation_importance", "effect",
                "ale", "coefficient",
            ),
        )
        or (numeric[0] if numeric else None)
    )
    return feature_col, value_col


def _ranked_frame(df: pd.DataFrame, roles: dict[str, str], *, max_rows: int = 15) -> tuple[pd.DataFrame, str | None]:
    feature_col, value_col = _feature_value_columns(df, roles)
    if feature_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame(), "Need feature + value columns"
    frame = pd.DataFrame({
        "feature": df[feature_col].astype(str),
        "value": pd.to_numeric(df[value_col], errors="coerce"),
    }).replace([np.inf, -np.inf], np.nan).dropna()
    if frame.empty:
        return pd.DataFrame(), "Need finite feature values"
    frame = (
        frame.assign(_abs=frame["value"].abs())
        .sort_values("_abs", ascending=False)
        .head(max_rows)
        .sort_values("_abs", ascending=True)
        .reset_index(drop=True)
    )
    return frame, None


@register_chart("lollipop_horizontal")
def gen_lollipop_horizontal(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                            rc_params: dict[str, Any], palette: dict[str, Any],
                            col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Horizontal bipolar lollipop plot for signed feature effects."""
    ax = _get_ax(ax)
    frame, message = _ranked_frame(df, _roles(data_profile))
    if message:
        return _status(ax, "Lollipop", message)

    y_pos = np.arange(len(frame))
    values = frame["value"].to_numpy(dtype=float)
    colors = np.where(values >= 0, POSITIVE, NEGATIVE)
    for y, value, color in zip(y_pos, values, colors):
        ax.plot([0.0, value], [y, y], color=color, lw=1.0, solid_capstyle="round", zorder=1)
    ax.scatter(values, y_pos, s=36, color=colors, edgecolor="white", linewidth=0.4, zorder=3)
    ax.axvline(0.0, color=NEUTRAL, lw=0.7, ls="--", zorder=0)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(frame["feature"].tolist())
    ax.set_xlabel("Signed effect")
    ax.set_title("Lollipop", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


@register_chart("diverging_bar")
def gen_diverging_bar(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                      rc_params: dict[str, Any], palette: dict[str, Any],
                      col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Horizontal diverging bars sorted by absolute effect size."""
    ax = _get_ax(ax)
    frame, message = _ranked_frame(df, _roles(data_profile))
    if message:
        return _status(ax, "Diverging bar", message)

    y_pos = np.arange(len(frame))
    values = frame["value"].to_numpy(dtype=float)
    colors = np.where(values >= 0, POSITIVE, NEGATIVE)
    ax.barh(y_pos, values, color=colors, height=0.68, alpha=0.88)
    ax.axvline(0.0, color=NEUTRAL, lw=0.7, ls="--")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(frame["feature"].tolist())
    ax.set_xlabel("Signed effect")
    ax.set_title("Diverging bar", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


@register_chart("dotplot")
def gen_dotplot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Feature dotplot with SHAP-style ordering and optional feature-value color."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    feature_col, value_col = _feature_value_columns(df, roles)
    color_col = _first_existing(df, ("feature_value", "feature_val", "feature_numeric", "interaction", "hue"))
    if feature_col not in df.columns or value_col not in df.columns:
        return _status(ax, "Dotplot", "Need feature + value columns")

    plot_df = pd.DataFrame({
        "feature": df[feature_col].astype(str),
        "value": pd.to_numeric(df[value_col], errors="coerce"),
    })
    if color_col in df.columns:
        plot_df["color"] = pd.to_numeric(df[color_col], errors="coerce")
    plot_df = plot_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["feature", "value"])
    if plot_df.empty:
        return _status(ax, "Dotplot", "Need finite feature values")

    order = (
        plot_df.assign(_abs=plot_df["value"].abs())
        .groupby("feature", sort=False)["_abs"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
        .index.tolist()
    )
    y_lookup = {feature: i for i, feature in enumerate(reversed(order))}
    plot_df = plot_df[plot_df["feature"].isin(order)].copy()
    y = plot_df["feature"].map(y_lookup).astype(float).to_numpy()
    if len(plot_df) > len(order):
        offsets = ((np.arange(len(plot_df)) % 7) - 3) * 0.035
        y = y + offsets

    if "color" in plot_df and plot_df["color"].notna().any():
        scatter = ax.scatter(plot_df["value"], y, c=plot_df["color"], cmap="coolwarm",
                             s=18, alpha=0.78, linewidths=0)
        ax.figure.colorbar(scatter, ax=ax, fraction=0.046, pad=0.02, label=color_col)
    else:
        colors = np.where(plot_df["value"].to_numpy(dtype=float) >= 0, POSITIVE, NEGATIVE)
        ax.scatter(plot_df["value"], y, color=colors, s=18, alpha=0.78, linewidths=0)

    ax.axvline(0.0, color=NEUTRAL, lw=0.7, ls="--")
    ax.set_yticks(list(y_lookup.values()))
    ax.set_yticklabels(list(y_lookup.keys()))
    ax.set_xlabel("Feature effect")
    ax.set_title("Dotplot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return ax


@register_chart("decision_curve")
def gen_decision_curve(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Decision-curve style threshold vs net-benefit panel."""
    ax = _get_ax(ax)
    colors = list(palette.get("categorical", ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]))
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    threshold_col = _first_existing(df, ("threshold", "probability_threshold", "pt")) or roles.get("x")
    benefit_col = _first_existing(df, ("net_benefit", "benefit", "utility")) or roles.get("value") or roles.get("y")
    group_col = roles.get("model") or roles.get("group")
    if threshold_col not in df.columns and numeric:
        threshold_col = numeric[0]
    if benefit_col not in df.columns and len(numeric) > 1:
        benefit_col = numeric[1]
    if threshold_col not in df.columns or benefit_col not in df.columns:
        return _status(ax, "Decision curve", "Need threshold + net benefit columns")

    plot_df = df.copy()
    plot_df[threshold_col] = pd.to_numeric(plot_df[threshold_col], errors="coerce")
    plot_df[benefit_col] = pd.to_numeric(plot_df[benefit_col], errors="coerce")
    plot_df = plot_df.replace([np.inf, -np.inf], np.nan).dropna(subset=[threshold_col, benefit_col])
    if plot_df.empty:
        return _status(ax, "Decision curve", "Need finite threshold-benefit pairs")

    if group_col in plot_df.columns:
        for i, (name, part) in enumerate(plot_df.groupby(group_col, sort=False)):
            part = part.sort_values(threshold_col)
            ax.plot(part[threshold_col], part[benefit_col], color=colors[i % len(colors)],
                    lw=1.1, label=str(name))
    else:
        plot_df = plot_df.sort_values(threshold_col)
        ax.plot(plot_df[threshold_col], plot_df[benefit_col], color=colors[0], lw=1.1)
    ax.axhline(0.0, color=NEUTRAL, lw=0.7, ls="--")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_title("Decision curve", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
