"""Journal style profiles for publication-ready figures."""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Journal profiles — dimensions in mm, fonts in pt, line widths in pt
# ---------------------------------------------------------------------------

JOURNAL_PROFILES: dict[str, dict[str, Any]] = {
    "nature": {
        "name": "Nature",
        "single_width_mm": 89,
        "double_width_mm": 183,
        "font_family": "sans-serif",
        "font_sans_serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font_size_label_pt": 7,
        "font_size_tick_pt": 6,
        "font_size_title_pt": 8,
        "line_width_axis_pt": 0.5,
        "line_width_data_pt": 1.0,
        "tick_length_mm": 2.0,
        "tick_width_pt": 0.5,
        "spine_top": False,
        "spine_right": False,
        "grid": False,
        "dpi": 300,
        "pdf_fonttype": 42,
    },
    "cell": {
        "name": "Cell",
        "single_width_mm": 85,
        "double_width_mm": 178,
        "font_family": "sans-serif",
        "font_sans_serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font_size_label_pt": 7,
        "font_size_tick_pt": 6,
        "font_size_title_pt": 8,
        "line_width_axis_pt": 0.5,
        "line_width_data_pt": 1.0,
        "tick_length_mm": 2.0,
        "tick_width_pt": 0.5,
        "spine_top": False,
        "spine_right": False,
        "grid": False,
        "dpi": 300,
        "pdf_fonttype": 42,
    },
    "science": {
        "name": "Science",
        "single_width_mm": 86,
        "double_width_mm": 178,
        "font_family": "sans-serif",
        "font_sans_serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font_size_label_pt": 6,
        "font_size_tick_pt": 5,
        "font_size_title_pt": 7,
        "line_width_axis_pt": 0.5,
        "line_width_data_pt": 0.75,
        "tick_length_mm": 1.5,
        "tick_width_pt": 0.4,
        "spine_top": False,
        "spine_right": False,
        "grid": False,
        "dpi": 300,
        "pdf_fonttype": 42,
    },
    "lancet": {
        "name": "The Lancet",
        "single_width_mm": 80,
        "double_width_mm": 170,
        "font_family": "sans-serif",
        "font_sans_serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font_size_label_pt": 7,
        "font_size_tick_pt": 6,
        "font_size_title_pt": 8,
        "line_width_axis_pt": 0.5,
        "line_width_data_pt": 1.0,
        "tick_length_mm": 2.0,
        "tick_width_pt": 0.5,
        "spine_top": False,
        "spine_right": False,
        "grid": False,
        "dpi": 300,
        "pdf_fonttype": 42,
    },
    "nejm": {
        "name": "NEJM",
        "single_width_mm": 83,
        "double_width_mm": 172,
        "font_family": "sans-serif",
        "font_sans_serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font_size_label_pt": 7,
        "font_size_tick_pt": 6,
        "font_size_title_pt": 9,
        "line_width_axis_pt": 0.5,
        "line_width_data_pt": 1.0,
        "tick_length_mm": 2.0,
        "tick_width_pt": 0.5,
        "spine_top": False,
        "spine_right": False,
        "grid": False,
        "dpi": 300,
        "pdf_fonttype": 42,
    },
    "jama": {
        "name": "JAMA",
        "single_width_mm": 82,
        "double_width_mm": 170,
        "font_family": "sans-serif",
        "font_sans_serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font_size_label_pt": 7,
        "font_size_tick_pt": 6,
        "font_size_title_pt": 8,
        "line_width_axis_pt": 0.5,
        "line_width_data_pt": 1.0,
        "tick_length_mm": 2.0,
        "tick_width_pt": 0.5,
        "spine_top": False,
        "spine_right": False,
        "grid": False,
        "dpi": 300,
        "pdf_fonttype": 42,
    },
}


def get_journal_profile(name: str) -> dict[str, Any]:
    """Return a journal style profile by name (case-insensitive).

    Parameters
    ----------
    name : str
        Journal key, e.g. ``"nature"``, ``"cell"``, ``"science"``.

    Returns
    -------
    dict
        Copy of the profile dictionary.

    Raises
    ------
    KeyError
        If *name* does not match any known profile.
    """
    key = name.lower().strip()
    if key not in JOURNAL_PROFILES:
        available = ", ".join(sorted(JOURNAL_PROFILES))
        raise KeyError(f"Unknown journal '{name}'. Available: {available}")
    return dict(JOURNAL_PROFILES[key])
