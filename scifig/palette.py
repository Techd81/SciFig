"""Color palettes for scientific figures — colorblind-safe and publication-ready."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Wong (2011) colorblind-safe palette — 8 colors
# Reference: Nature Methods 8, 441 (2011)
# ---------------------------------------------------------------------------

WONG_HEX: list[str] = [
    "#000000",  # black
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
]

# ---------------------------------------------------------------------------
# Categorical presets (subset-friendly)
# ---------------------------------------------------------------------------

CATEGORICAL: dict[str, list[str]] = {
    "wong": WONG_HEX,
    "okabe-ito": [
        "#E69F00", "#56B4E9", "#009E73", "#F0E442",
        "#0072B2", "#D55E00", "#CC79A7", "#000000",
    ],
    "tab10": [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf",
    ],
    "bold4": ["#0072B2", "#E69F00", "#009E73", "#D55E00"],
    "muted6": [
        "#332288", "#88CCEE", "#44AA99",
        "#117733", "#DDCC77", "#CC6677",
    ],
}

# ---------------------------------------------------------------------------
# Sequential presets
# ---------------------------------------------------------------------------

SEQUENTIAL: dict[str, list[str]] = {
    "blues": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"],
    "viridis": ["#440154", "#482777", "#3f4a8a", "#31678e", "#26838f", "#1f9d8a", "#6cce5a", "#fee825"],
    "inferno": ["#000004", "#1b0c41", "#4a0c6b", "#781c6d", "#a52c60", "#cf4446", "#ed6925", "#f9d800"],
    "greens": ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#005a32"],
}

# ---------------------------------------------------------------------------
# Diverging presets
# ---------------------------------------------------------------------------

DIVERGING: dict[str, list[str]] = {
    "rdbu": ["#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#d1e5f0", "#92c5de", "#4393c3", "#2166ac"],
    "brbg": ["#543005", "#8c510a", "#bf812d", "#dfc27d", "#c7eae5", "#80cdc1", "#35978f", "#01665e"],
    "coolwarm": ["#3b4cc0", "#6e8cef", "#a4bff0", "#d5d8dc", "#f0b89a", "#d97456", "#b40426"],
}

# ---------------------------------------------------------------------------
# Lookup helper
# ---------------------------------------------------------------------------

_ALL_PALETTES: dict[str, list[str]] = {
    **{f"cat:{k}": v for k, v in CATEGORICAL.items()},
    **{f"seq:{k}": v for k, v in SEQUENTIAL.items()},
    **{f"div:{k}": v for k, v in DIVERGING.items()},
    # Also expose without prefix for convenience
    **CATEGORICAL,
    **SEQUENTIAL,
    **DIVERGING,
}


def get_palette(name: str, n: int | None = None) -> list[str]:
    """Return *n* colors from the named palette.

    Parameters
    ----------
    name : str
        Palette key — e.g. ``"wong"``, ``"cat:bold4"``, ``"seq:blues"``,
        ``"div:rdbu"``.
    n : int, optional
        Number of colors desired.  For categorical palettes the result is
        cycled/repeated if *n* exceeds the palette length.  For sequential
        palettes, linear interpolation is used.  Defaults to the full palette.

    Returns
    -------
    list[str]
        List of hex color strings.

    Raises
    ------
    KeyError
        If *name* is not found.
    """
    key = name.lower().strip()
    if key not in _ALL_PALETTES:
        available = ", ".join(sorted(_ALL_PALETTES))
        raise KeyError(f"Unknown palette '{name}'. Available: {available}")

    base = list(_ALL_PALETTES[key])
    if n is None:
        return base

    if n <= 0:
        return []

    # Categorical — cycle
    if key in CATEGORICAL or key.startswith("cat:"):
        return [base[i % len(base)] for i in range(n)]

    # Sequential / Diverging — interpolate
    if n == 1:
        return [base[0]]
    result: list[str] = []
    for i in range(n):
        frac = i / (n - 1)
        idx_f = frac * (len(base) - 1)
        lo = int(idx_f)
        hi = min(lo + 1, len(base) - 1)
        result.append(base[lo] if lo == hi else base[lo])  # snap to nearest
    return result
