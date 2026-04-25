"""Utility helpers for data preparation and font detection."""

from __future__ import annotations

import re
import unicodedata
from typing import Sequence

import pandas as pd

# ---------------------------------------------------------------------------
# Column sanitisation
# ---------------------------------------------------------------------------

_SAFE_RE = re.compile(r"[^0-9a-zA-Z_]+")
_LEADING_DIGIT = re.compile(r"^(\d)")


def sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename DataFrame columns to safe Python identifiers.

    Rules:
    * Unicode NFKD normalisation
    * Non-alphanumeric/underscore characters replaced with ``_``
    * Leading digits prefixed with ``col_``
    * Empty results become ``col_<index>``
    * Duplicates get ``_1``, ``_2`` suffixes

    Parameters
    ----------
    df : pd.DataFrame
        Input frame (not mutated).

    Returns
    -------
    pd.DataFrame
        Copy with sanitised column names.
    """
    new_names: list[str] = []
    seen: dict[str, int] = {}
    for i, col in enumerate(df.columns):
        name = unicodedata.normalize("NFKD", str(col))
        name = _SAFE_RE.sub("_", name).strip("_").lower()
        if name and _LEADING_DIGIT.match(name):
            name = f"col_{name}"
        if not name:
            name = f"col_{i}"
        # deduplicate: foo, foo_1, foo_2, …
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        new_names.append(name)

    return df.rename(columns=dict(zip(df.columns, new_names)))


# ---------------------------------------------------------------------------
# Font detection
# ---------------------------------------------------------------------------

# Preferred font order — first available wins
_FONT_CANDIDATES: list[str] = [
    "Arial",
    "Helvetica",
    "Liberation Sans",
    "DejaVu Sans",
    "Noto Sans",
    "FreeSans",
    "sans-serif",
]


def detect_available_font(
    candidates: Sequence[str] | None = None,
) -> str:
    """Return the first available font name from *candidates*.

    Falls back to ``"sans-serif"`` if matplotlib's font manager is not
    available or no candidate is found.

    Parameters
    ----------
    candidates : sequence of str, optional
        Font names to probe.  Defaults to a built-in preference list.

    Returns
    -------
    str
        Name of the first font found on the system.
    """
    if candidates is None:
        candidates = _FONT_CANDIDATES

    try:
        from matplotlib.font_manager import fontManager  # type: ignore[import-untyped]

        available = {f.name for f in fontManager.ttflist}
        for name in candidates:
            if name in available:
                return name
    except ImportError:
        pass

    return "sans-serif"
