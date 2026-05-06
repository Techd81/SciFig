"""Small statistical guardrails for the package API."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd  # type: ignore[import-untyped]


def add_group_stat_annotation(ax: Any, df: pd.DataFrame, group_col: Optional[str], value_col: Optional[str], mode: str) -> list[str]:
    if mode == "none" or not group_col or not value_col or group_col not in df.columns or value_col not in df.columns:
        return []
    groups = [pd.to_numeric(part[value_col], errors="coerce").dropna() for _, part in df.groupby(group_col, sort=False)]
    if len(groups) != 2 or min(len(g) for g in groups) < 2:
        if mode == "strict":
            return ["statistical_test_degraded_to_descriptive"]
        return []
    try:
        from scipy import stats  # type: ignore[import-untyped]
        p_value = float(stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided").pvalue)
    except Exception:
        return ["statistical_test_unavailable"]
    y_max = max(float(g.max()) for g in groups if len(g))
    y_min = min(float(g.min()) for g in groups if len(g))
    height = max((y_max - y_min) * 0.06, 0.05)
    ax.plot([1, 1, 2, 2], [y_max + height, y_max + 2 * height, y_max + 2 * height, y_max + height],
            color="black", lw=0.6, clip_on=False)
    label = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3g}"
    ax.text(1.5, y_max + 2.2 * height, label, ha="center", va="bottom", fontsize=6, fontstyle="italic")
    ax.set_ylim(top=y_max + 4 * height)
    return []
