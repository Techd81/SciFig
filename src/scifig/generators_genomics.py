"""Dedicated genomics-family generators for the chart registry.

volcano    — Volcano plot (log2FC vs -log10(p), significance thresholds)
ma_plot    — MA plot (mean expression vs log2FC)
manhattan  — Manhattan plot (cumulative chromosomal position vs -log10(p))
"""

from __future__ import annotations

import math
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


# -- Volcano ------------------------------------------------------------------

@register_chart("volcano")
def gen_volcano(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Volcano plot — log2 fold-change vs -log10(p), with significance
    thresholds (|FC|>1, p<0.05) and red/blue colouring."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    fc_col = roles.get("fc") or roles.get("x") or (numeric[0] if numeric else None)
    p_col = roles.get("p") or roles.get("pvalue") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if fc_col not in df.columns or p_col not in df.columns:
        ax.text(0.5, 0.5, "Need fold-change + p-value columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Volcano", loc="center", fontweight="bold", pad=5)
        return ax

    x = pd.to_numeric(df[fc_col], errors="coerce")
    y = -np.log10(pd.to_numeric(df[p_col], errors="coerce").clip(lower=1e-300))
    sig = (y > -math.log10(0.05)) & (x.abs() >= 1)
    ax.scatter(x[~sig], y[~sig], s=12, color="#999999", alpha=0.55, linewidths=0)
    ax.scatter(x[sig & (x > 0)], y[sig & (x > 0)], s=14, color=colors[4 % len(colors)],
               alpha=0.8, linewidths=0)
    ax.scatter(x[sig & (x < 0)], y[sig & (x < 0)], s=14, color=colors[5 % len(colors)],
               alpha=0.8, linewidths=0)
    ax.axvline(1, color="#555555", lw=0.6, ls="--")
    ax.axvline(-1, color="#555555", lw=0.6, ls="--")
    ax.axhline(-math.log10(0.05), color="#555555", lw=0.6, ls=":")
    ax.set_xlabel("log2 fold-change")
    ax.set_ylabel("-log10(p)")
    ax.set_title("Volcano", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- MA plot ------------------------------------------------------------------

@register_chart("ma_plot")
def gen_ma_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """MA plot — mean expression (A) vs log2 fold-change (M), with zero line."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    a_col = roles.get("mean") or roles.get("x") or (numeric[0] if numeric else None)
    m_col = roles.get("fc") or roles.get("value") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if a_col not in df.columns or m_col not in df.columns:
        ax.text(0.5, 0.5, "Need mean + fold-change columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("MA plot", loc="center", fontweight="bold", pad=5)
        return ax

    a = pd.to_numeric(df[a_col], errors="coerce")
    m = pd.to_numeric(df[m_col], errors="coerce")
    ax.scatter(a, m, s=12, color=colors[1 % len(colors)], alpha=0.65, linewidths=0)
    ax.axhline(0, color="#555555", lw=0.6, ls="--")
    ax.set_xlabel("Mean expression (A)")
    ax.set_ylabel("log2 fold-change (M)")
    ax.set_title("MA plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- Manhattan ----------------------------------------------------------------

@register_chart("manhattan")
def gen_manhattan(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Manhattan plot — cumulative chromosomal position vs -log10(p),
    alternating chrom colours + genome-wide significance line."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    chr_col = roles.get("chr") or roles.get("chromosome") or roles.get("group")
    pos_col = roles.get("position") or roles.get("pos") or roles.get("x") or (numeric[0] if numeric else None)
    p_col = roles.get("p") or roles.get("pvalue") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if chr_col not in df.columns or pos_col not in df.columns or p_col not in df.columns:
        ax.text(0.5, 0.5, "Need chr + position + p-value columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Manhattan", loc="center", fontweight="bold", pad=5)
        return ax

    p_raw = pd.to_numeric(df[p_col], errors="coerce")
    y = -np.log10(p_raw.clip(lower=1e-300))
    pos = pd.to_numeric(df[pos_col], errors="coerce")
    chr_groups = df[chr_col].astype(str)
    chroms = list(dict.fromkeys(chr_groups.tolist()))
    cum_pos = np.zeros(len(df))
    cum_offsets: list[float] = []
    offset = 0.0
    for chrom in chroms:
        mask = chr_groups == chrom
        chr_pos = pos[mask]
        cum_pos[mask.values] = chr_pos.values + offset
        cum_offsets.append(offset + (chr_pos.max() if not chr_pos.empty else 0))
        offset = cum_offsets[-1]

    for i, chrom in enumerate(chroms):
        mask = chr_groups == chrom
        ax.scatter(cum_pos[mask.values], y[mask.values], s=9,
                   color=colors[i % len(colors)], alpha=0.7, linewidths=0)

    sig = -math.log10(5e-8)
    ax.axhline(sig, color="#CC0000", lw=0.6, ls="--")
    ax.set_xlabel("Chromosomal position (cumulative)")
    ax.set_ylabel("-log10(p)")
    ax.set_title("Manhattan", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
