"""Multi-panel composition recipes loaded from the canonical JSON registry.

The skill (``scifig-generate``) maintains layout recipes in
``templates/layout-recipes-ready.json``. v0.1.6 lifts that JSON into the
package so users can ``from scifig.compose import get_recipe, list_recipes``
without touching skill internals.

Public API:

- :func:`list_recipes` - return all recipe IDs
- :func:`get_recipe` - look up a recipe by ID (e.g. ``"R0"`` or its name
  ``"single_panel"``); raises ``KeyError`` if unknown
- :func:`pick_recipe` - choose a recipe by panel count and use case
- :func:`build_grid` - resolve a recipe ID into a ``(fig, axes_dict)`` pair
  using matplotlib's GridSpec / subplots engines
- :data:`RECIPE_REGISTRY` - read-only snapshot of the parsed JSON
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

__all__ = [
    "RECIPE_REGISTRY",
    "list_recipes",
    "get_recipe",
    "pick_recipe",
    "build_grid",
    "load_recipes_from_path",
]


# ----------------------------------------------------------------------------
# JSON loader (single source of truth)
# ----------------------------------------------------------------------------

# Resolve the canonical JSON path. Search candidate locations so the package
# works both in a checkout (skill JSON sits alongside the repo) and in a
# pip-installed environment (vendored copy bundled into site-packages).
_CANDIDATE_PATHS = [
    # Vendored alongside the package (ship at sdist time)
    Path(__file__).resolve().parent / "data" / "layout-recipes-ready.json",
    # Source checkout layout: skill at .claude/skills/scifig-generate/templates/
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "scifig-generate" / "templates" / "layout-recipes-ready.json",
    # Workspace fallback: user runs from project root
    Path.cwd() / ".claude" / "skills" / "scifig-generate" / "templates" / "layout-recipes-ready.json",
]


def load_recipes_from_path(path: Optional[Path] = None) -> dict[str, Any]:
    """Load and parse a layout-recipes JSON file.

    If ``path`` is ``None``, search the bundled / skill / workspace candidate
    locations and use the first that exists.
    """
    if path is not None:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    for candidate in _CANDIDATE_PATHS:
        if candidate.is_file():
            return json.loads(candidate.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        "layout-recipes-ready.json not found. Searched: "
        + ", ".join(str(p) for p in _CANDIDATE_PATHS)
    )


def _build_initial_registry() -> dict[str, Any]:
    """Try to load the JSON registry, fall back to a built-in skeleton if absent."""
    try:
        return load_recipes_from_path(None)
    except FileNotFoundError:
        # Built-in fallback so ``import scifig.compose`` never raises in an
        # environment that lacks both the bundled JSON and the skill checkout.
        return {
            "version": "fallback",
            "source": "scifig.compose built-in",
            "R0": {
                "id": "R0",
                "name": "single_panel",
                "panel_count": 1,
                "gridspec_args": {"engine": "subplots", "nrows": 1, "ncols": 1, "figsize_mm": [89, 62]},
                "reserved_slots": {"legend": "bottom_center_optional"},
                "use_cases": ["hero_single", "single_focus"],
            },
            "R1": {
                "id": "R1",
                "name": "two_panel_horizontal",
                "panel_count": 2,
                "gridspec_args": {"engine": "subplots", "nrows": 1, "ncols": 2, "wspace": 0.30, "hspace": 0.0},
                "reserved_slots": {"legend": "bottom_center"},
                "use_cases": ["comparison_pair"],
            },
        }


RECIPE_REGISTRY: dict[str, Any] = _build_initial_registry()


def _name_index() -> dict[str, str]:
    """Build a ``name -> id`` lookup from the current registry."""
    return {
        v["name"]: k
        for k, v in RECIPE_REGISTRY.items()
        if isinstance(v, dict) and "name" in v
    }


# ----------------------------------------------------------------------------
# Recipe lookup
# ----------------------------------------------------------------------------

def list_recipes() -> list[str]:
    """Return every recipe ID present in the registry, sorted."""
    return sorted(k for k, v in RECIPE_REGISTRY.items() if isinstance(v, dict) and "id" in v)


def get_recipe(key: str) -> dict[str, Any]:
    """Look up a recipe by ID (``"R0"``) or name (``"single_panel"``).

    Raises ``KeyError`` if no recipe matches.
    """
    if key in RECIPE_REGISTRY and isinstance(RECIPE_REGISTRY[key], dict):
        return dict(RECIPE_REGISTRY[key])
    name_idx = _name_index()
    if key in name_idx:
        return dict(RECIPE_REGISTRY[name_idx[key]])
    raise KeyError(f"Unknown layout recipe: {key!r}. Available: {list_recipes()}")


def pick_recipe(panel_count: int, use_case: Optional[str] = None) -> dict[str, Any]:
    """Pick the most appropriate recipe for a panel count + optional use case.

    Strategy:
    1. If ``use_case`` matches a recipe's ``use_cases`` AND its panel_count
       matches (or is the symbolic ``"n*n"`` for pairwise grids), prefer it.
    2. Otherwise pick the recipe with the smallest abs(panel_count - target).
    3. Tie-break: prefer recipes with ``use_case`` matches; then lower ID.
    """
    candidates = [(k, v) for k, v in RECIPE_REGISTRY.items() if isinstance(v, dict) and "id" in v]
    if not candidates:
        raise RuntimeError("No layout recipes registered.")

    def _score(item: tuple[str, dict[str, Any]]) -> tuple[int, int, str]:
        rid, recipe = item
        rc = recipe.get("panel_count", 0)
        rc_int = panel_count if isinstance(rc, str) else int(rc)
        panel_diff = abs(rc_int - panel_count)
        use_case_match = 0 if (use_case and use_case in recipe.get("use_cases", [])) else 1
        return (use_case_match, panel_diff, rid)

    best = min(candidates, key=_score)
    return dict(best[1])


# ----------------------------------------------------------------------------
# Grid construction
# ----------------------------------------------------------------------------

def _figsize_inches(recipe: dict[str, Any], override: Optional[tuple[float, float]] = None) -> tuple[float, float]:
    if override is not None:
        return override
    args = recipe.get("gridspec_args", {})
    figsize_mm = args.get("figsize_mm")
    if figsize_mm and len(figsize_mm) == 2:
        return (float(figsize_mm[0]) / 25.4, float(figsize_mm[1]) / 25.4)
    # Reasonable defaults: single column ~89mm wide, height scales with rows
    nrows = int(args.get("nrows") or 1) if isinstance(args.get("nrows"), (int, float)) else 1
    ncols = int(args.get("ncols") or 1) if isinstance(args.get("ncols"), (int, float)) else 1
    width_mm = 89 if ncols == 1 else 183
    height_mm = max(62, nrows * 60)
    return (width_mm / 25.4, height_mm / 25.4)


def build_grid(
    key: str,
    *,
    figsize: Optional[tuple[float, float]] = None,
    n: Optional[int] = None,
) -> tuple[Figure, dict[str, Any]]:
    """Materialize a recipe into a ``(fig, axes_dict)`` pair.

    Parameters
    ----------
    key : str
        Recipe ID (``"R0"``) or name (``"single_panel"``).
    figsize : (width_in, height_in) | None
        Override the recipe's intrinsic ``figsize_mm`` value.
    n : int | None
        Required when the recipe uses the symbolic ``n*n`` panel count
        (e.g. pairwise correlation grids).

    Returns
    -------
    (fig, axes) : matplotlib Figure + dict mapping panel labels (A, B, ...) to Axes.
    """
    recipe = get_recipe(key)
    args = dict(recipe.get("gridspec_args", {}))
    engine = args.pop("engine", "subplots")
    figsize_in = _figsize_inches(recipe, figsize)

    nrows_raw = args.pop("nrows", 1)
    ncols_raw = args.pop("ncols", 1)
    if isinstance(nrows_raw, str) or isinstance(ncols_raw, str):
        if n is None:
            raise ValueError(
                f"Recipe {recipe.get('id')} uses symbolic n*n panel count; pass n=<int>."
            )
        nrows = int(n)
        ncols = int(n)
    else:
        nrows = int(nrows_raw)
        ncols = int(ncols_raw)

    # Drop JSON-only fields not understood by matplotlib
    args.pop("figsize_mm", None)

    fig: Figure
    axes_list: list[Any]
    if engine == "subplots":
        fig, raw_axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize_in)
        if hasattr(raw_axes, "flatten"):
            axes_list = list(raw_axes.flatten())
        elif isinstance(raw_axes, (list, tuple)):
            axes_list = list(raw_axes)
        else:
            axes_list = [raw_axes]
        # Apply spacing args after creation
        wspace = args.pop("wspace", None)
        hspace = args.pop("hspace", None)
        if wspace is not None or hspace is not None:
            fig.subplots_adjust(
                wspace=wspace if wspace is not None else 0.2,
                hspace=hspace if hspace is not None else 0.2,
            )
    else:  # GridSpec engine
        fig = plt.figure(figsize=figsize_in)
        height_ratios = args.pop("height_ratios", None)
        width_ratios = args.pop("width_ratios", None)
        wspace = args.pop("wspace", None)
        hspace = args.pop("hspace", None)
        gs_kwargs: dict[str, Any] = {}
        if height_ratios is not None:
            gs_kwargs["height_ratios"] = height_ratios
        if width_ratios is not None:
            gs_kwargs["width_ratios"] = width_ratios
        if wspace is not None:
            gs_kwargs["wspace"] = wspace
        if hspace is not None:
            gs_kwargs["hspace"] = hspace
        gs = fig.add_gridspec(nrows=nrows, ncols=ncols, **gs_kwargs)
        axes_list = []
        for r in range(nrows):
            for c in range(ncols):
                axes_list.append(fig.add_subplot(gs[r, c]))

    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    axes_dict = {labels[i]: ax for i, ax in enumerate(axes_list[: len(labels)])}
    return fig, axes_dict
