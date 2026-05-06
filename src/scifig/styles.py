"""Journal style profiles and rcParams application."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

import matplotlib.pyplot as plt

from .types import JournalProfile


_BASE: JournalProfile = {
    "name": "nature",
    "single_width_mm": 89.0,
    "double_width_mm": 183.0,
    "max_height_mm": 247.0,
    "body_pt": 6.5,
    "panel_label_pt": 8.0,
    "axis_lw_pt": 0.65,
    "tick_w_pt": 0.6,
    "panel_gap_rel": 0.18,
    "font_family": "DejaVu Sans",
    "grid": False,
    "legend_frame": True,
}

_PROFILES: Dict[str, JournalProfile] = {
    "nature": _BASE,
    "cell": {**_BASE, "name": "cell", "single_width_mm": 85.0, "double_width_mm": 174.0, "body_pt": 6.0, "panel_gap_rel": 0.15},
    "science": {**_BASE, "name": "science", "single_width_mm": 90.0, "double_width_mm": 190.0, "body_pt": 6.25, "panel_gap_rel": 0.16},
    "lancet": {**_BASE, "name": "lancet", "single_width_mm": 84.0, "double_width_mm": 174.0, "body_pt": 7.0, "panel_gap_rel": 0.2},
    "nejm": {**_BASE, "name": "nejm", "single_width_mm": 88.0, "double_width_mm": 171.0, "body_pt": 7.0, "panel_gap_rel": 0.22},
    "jama": {**_BASE, "name": "jama", "single_width_mm": 89.0, "double_width_mm": 183.0, "body_pt": 6.75, "panel_gap_rel": 0.2},
}


def available_profiles() -> List[str]:
    return sorted(_PROFILES)


def get_profile(name: str = "nature") -> JournalProfile:
    key = (name or "nature").lower()
    if key not in _PROFILES:
        raise ValueError(f"Unknown style '{name}'. Available styles: {', '.join(available_profiles())}")
    return deepcopy(_PROFILES[key])


def apply_style(name: str = "nature") -> JournalProfile:
    profile = get_profile(name)
    body = profile["body_pt"]
    plt.rcParams.update({
        "font.family": profile["font_family"],
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": body,
        "axes.labelsize": body + 0.5,
        "axes.titlesize": body + 1.0,
        "axes.linewidth": profile["axis_lw_pt"],
        "axes.grid": profile["grid"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": max(5.0, body - 0.5),
        "ytick.labelsize": max(5.0, body - 0.5),
        "xtick.major.width": profile["tick_w_pt"],
        "ytick.major.width": profile["tick_w_pt"],
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.fontsize": 7,
        "legend.frameon": profile["legend_frame"],
        "legend.edgecolor": "#cccccc",
        "legend.borderpad": 0.4,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    return profile
