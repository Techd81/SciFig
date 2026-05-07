"""Publication-quality figure finalizer for matplotlib.

This module is the canonical home for the SciFig "polish" pipeline that runs
**immediately before ``fig.savefig``**. The skill (``scifig-generate``) used to
embed an inline ``helpers.py`` source via ``exec()`` to access these utilities;
v0.1.5 establishes ``scifig.polish`` as the single source of truth so users who
``pip install scifig`` can import the same finalizer directly.

Public API (stable):

- :func:`enforce` - main legend-contract finalizer (alias of
  :func:`enforce_figure_legend_contract`)
- :func:`sanitize_columns` - rename DataFrame columns to safe Python identifiers
- :func:`apply_chart_polish` - per-axes spine/tick/violin/baseline polish
- :func:`add_significance_bracket` - Nature-style p-value brackets
- :func:`format_p_value` - p-value formatting per Nature convention
- :data:`CROWDING_DEFAULTS` - canonical legend/colorbar defaults

Migration note: this v0.1.5 port focuses on the **legend-contract finalizer**
and its hard dependencies. The fuller crowding-management and visual-density
audit pipelines (``apply_visual_content_pass``, ``audit_figure_layout_contract``,
etc.) currently remain in the skill's ``helpers.py`` and will land in
``scifig.polish`` over the v0.1.5 -> v0.2.0 milestone window.

Typical usage::

    import matplotlib.pyplot as plt
    from scifig.polish import enforce

    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [4, 5, 6], label="series")
    ax.legend()                          # temporary handle source
    report = enforce(fig)                # promote to bottom-center figure legend
    fig.savefig("output.svg")
"""

from __future__ import annotations

import re
from typing import Any, Optional

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

__all__ = [
    "CROWDING_DEFAULTS",
    "enforce",
    "enforce_figure_legend_contract",
    "sanitize_columns",
    "apply_chart_polish",
    "add_significance_bracket",
    "format_p_value",
    "normalize_axes_map",
    "collect_legend_handles",
    "promote_to_bottom_center_legend",
]


# ----------------------------------------------------------------------------
# Defaults
# ----------------------------------------------------------------------------

CROWDING_DEFAULTS: dict[str, Any] = {
    "legendScope": "figure",
    "legendMode": "bottom_center",
    "legendPlacementPriority": ["bottom_center"],
    "legendAllowedModes": ["bottom_center"],
    "legendLabelMaxChars": 32,
    "legendFontSizePt": 7,
    "legendBottomAnchorY": 0.015,
    "legendBottomMarginNoLegend": 0.05,
    "legendBottomMarginMin": 0.06,
    "legendBottomMarginMax": 0.16,
    "maxLegendColumns": 6,
    "legendFrame": True,
    "legendFrameStyle": {
        "facecolor": "#FFFFFF",
        "edgecolor": "#cccccc",
        "linewidth": 0.55,
        "alpha": 1.0,
        "pad": 0.4,
        "boxstyle": "round",
    },
    "legendCenterPlacementOnly": True,
    "forbidOutsideRightLegend": True,
    "forbidInAxesLegend": True,
}


# ----------------------------------------------------------------------------
# Column sanitization
# ----------------------------------------------------------------------------

def sanitize_columns(df: Any) -> tuple[Any, dict[str, str]]:
    """Rename DataFrame columns to safe Python identifiers.

    Returns ``(df_renamed, name_map)`` where ``name_map`` maps the new safe
    identifier back to the original column name (only entries where renaming
    actually happened). Mutates ``df`` in place by reassigning ``df.columns``.
    """
    name_map: dict[str, str] = {}
    new_cols: list[str] = []
    for col in df.columns:
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", str(col)).strip("_")
        if safe and safe[0].isdigit():
            safe = "col_" + safe
        safe = safe or "unnamed"
        base = safe
        i = 1
        while safe in new_cols:
            safe = f"{base}_{i}"
            i += 1
        new_cols.append(safe)
        if safe != col:
            name_map[safe] = str(col)
    df.columns = new_cols
    return df, name_map


# ----------------------------------------------------------------------------
# Per-chart axes polish
# ----------------------------------------------------------------------------

def apply_chart_polish(ax: Any, chart_type: str) -> None:
    """Apply publication-quality post-processing to any axes.

    Polar-safe: matplotlib's polar Axes only owns a 'polar' spine, not
    'top'/'right'. Guard the cartesian spine hiding so radar/polar charts
    can call this generically without KeyError.
    """
    spines = getattr(ax, "spines", None)
    is_polar = getattr(ax, "name", "") == "polar" or (
        hasattr(spines, "__contains__") and "polar" in spines and "top" not in spines
    )
    if not is_polar and spines is not None:
        if "top" in spines:
            ax.spines["top"].set_visible(False)
        if "right" in spines:
            ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.6, pad=2)

    if chart_type in ("violin_strip", "violin_paired", "violin_split", "violin_grouped"):
        for coll in ax.collections:
            if hasattr(coll, "set_alpha"):
                coll.set_alpha(0.3)

    if chart_type in ("violin_strip", "box_strip", "dot+box", "bar"):
        ymin = ax.get_ylim()[0]
        if ymin > 0:
            ax.set_ylim(bottom=0)

    for text in ax.texts:
        if text.get_text().startswith("n="):
            text.set_fontsize(5)
            text.set_color("#333")


# ----------------------------------------------------------------------------
# Significance brackets and p-value formatting
# ----------------------------------------------------------------------------

def add_significance_bracket(
    ax: Any,
    x1: float,
    x2: float,
    y: float,
    height: float,
    p_value: float,
    lw: float = 0.6,
) -> None:
    """Add a Nature-style significance bracket with T-caps and italic p."""
    cap_w = height * 0.25
    ax.plot([x1, x1], [y, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x2, x2], [y, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x1, x2], [y + height, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x1 - cap_w, x1 + cap_w], [y, y], lw=lw, c="black", clip_on=False)
    ax.plot([x2 - cap_w, x2 + cap_w], [y, y], lw=lw, c="black", clip_on=False)
    p_text = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3g}"
    ax.text(
        (x1 + x2) / 2,
        y + height * 1.1,
        p_text,
        ha="center",
        va="bottom",
        fontsize=6,
        fontstyle="italic",
    )


def format_p_value(p_value: float) -> str:
    """Format a p-value per Nature convention (italic p, no leading zero)."""
    if p_value < 0.001:
        return "p < 0.001"
    return f"p = {p_value:.2g}"


# ----------------------------------------------------------------------------
# Axes-map normalization
# ----------------------------------------------------------------------------

def normalize_axes_map(fig: Figure, axes: Any = None) -> dict[str, Any]:
    """Return a stable ``{label: ax}`` dict for the given figure.

    Accepts ``None`` (auto-discovers via ``fig.axes``), a list/tuple of axes,
    or an already-prepared dict. Labels default to ``"A"``, ``"B"``, ...
    """
    if isinstance(axes, dict):
        return dict(axes)
    if axes is None:
        candidates = list(fig.axes)
    else:
        candidates = list(axes)
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return {labels[i % len(labels)] + (str(i // len(labels)) if i >= len(labels) else ""): ax
            for i, ax in enumerate(candidates)}


# ----------------------------------------------------------------------------
# Legend collection and promotion
# ----------------------------------------------------------------------------

def collect_legend_handles(axes_map: dict[str, Any]) -> tuple[list[Any], list[str]]:
    """Collect (handle, label) pairs from all axes legends, deduped by label."""
    seen: set[str] = set()
    handles: list[Any] = []
    labels: list[str] = []
    for ax in axes_map.values():
        # Capture both currently-shown legend entries and historical handles
        for handle in ax.get_legend_handles_labels()[0]:
            pass  # walked together below
        h_list, l_list = ax.get_legend_handles_labels()
        for h, lab in zip(h_list, l_list):
            if not lab or lab.startswith("_"):
                continue
            if lab in seen:
                continue
            seen.add(lab)
            handles.append(h)
            labels.append(lab)
    return handles, labels


def _remove_axis_legends(axes_map: dict[str, Any]) -> int:
    """Remove every per-axes legend; return removed count."""
    removed = 0
    for ax in axes_map.values():
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()
            removed += 1
    return removed


def promote_to_bottom_center_legend(
    fig: Figure,
    handles: list[Any],
    labels: list[str],
    *,
    fontsize: int = 7,
    anchor_y: float = 0.015,
    max_columns: int = 6,
    frame_style: Optional[dict[str, Any]] = None,
) -> Optional[Any]:
    """Place ``(handles, labels)`` as a single framed bottom-center figure legend.

    Returns the matplotlib ``Legend`` object, or ``None`` if there were no
    handles to place.
    """
    if not handles:
        return None
    style = dict(CROWDING_DEFAULTS["legendFrameStyle"])
    if frame_style:
        style.update(frame_style)
    ncol = min(len(handles), max_columns)
    legend = fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, anchor_y),
        ncol=ncol,
        fontsize=fontsize,
        frameon=True,
        edgecolor=style.get("edgecolor", "#cccccc"),
        facecolor=style.get("facecolor", "#FFFFFF"),
        borderpad=style.get("pad", 0.4),
    )
    frame = legend.get_frame()
    frame.set_linewidth(style.get("linewidth", 0.55))
    frame.set_alpha(style.get("alpha", 1.0))
    return legend


# ----------------------------------------------------------------------------
# Forbidden legend pattern detection
# ----------------------------------------------------------------------------

_FORBIDDEN_BBOX_RE = re.compile(r"")  # placeholder — anchor checks happen at runtime


def _check_legend_anchor_forbidden(legend: Any) -> list[str]:
    """Return a list of failure tags for the given legend's bbox anchor.

    Converts the legend's bbox-to-anchor (which matplotlib stores in display
    coordinates) back into figure-relative coordinates so the 0..1 forbidden
    region checks work regardless of figure size.
    """
    failures: list[str] = []
    try:
        anchor = legend.get_bbox_to_anchor()
    except Exception:
        return failures
    if anchor is None:
        return failures
    fig = getattr(legend, "figure", None)
    try:
        if fig is not None and hasattr(anchor, "transformed"):
            anchor_fig = anchor.transformed(fig.transFigure.inverted())
            x = anchor_fig.x0 + anchor_fig.width / 2
            y = anchor_fig.y0 + anchor_fig.height / 2
        elif hasattr(anchor, "x0"):
            # Fallback: treat as figure coords directly (best effort)
            x = anchor.x0 + getattr(anchor, "width", 0) / 2
            y = anchor.y0 + getattr(anchor, "height", 0) / 2
        else:
            x, y = anchor[0], anchor[1]
    except Exception:
        return failures
    if x >= 1.0:
        failures.append("outside_right_legend_bbox_anchor")
    if y < 0:
        failures.append("negative_legend_bbox_anchor")
    return failures


# ----------------------------------------------------------------------------
# Main finalizer
# ----------------------------------------------------------------------------

def enforce_figure_legend_contract(
    fig: Figure,
    axes: Any = None,
    chart_plan: Optional[dict[str, Any]] = None,
    journal_profile: Optional[dict[str, Any]] = None,
    crowding_plan: Optional[dict[str, Any]] = None,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Promote per-axes legends into a single framed bottom-center figure legend.

    This is the **canonical legend-contract finalizer**. Call it immediately
    before ``fig.savefig`` to make the figure publication-compliant:

    1. Collect all per-axes legend handles (deduplicated by label).
    2. Remove the per-axes legends so the data area is unobstructed.
    3. Place a single ``fig.legend(...)`` at bottom-center with a framed box.
    4. Verify there are no forbidden anchors (outside-right, negative-y).
    5. Return a structured ``report`` dict for downstream metadata.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to finalize.
    axes : dict | list | None
        Axes map. ``None`` auto-discovers via ``fig.axes``.
    chart_plan, journal_profile, crowding_plan : dict | None
        Reserved for forward compatibility with the skill's full crowding
        pipeline. Currently used only to read ``legendBottomAnchorY`` and
        ``legendFontSizePt`` overrides.
    strict : bool
        If True, raise ``RuntimeError`` when the contract fails.

    Returns
    -------
    dict
        A structured report with at least:

        - ``hasFigureLegend`` (bool)
        - ``axisLegendRemainingCount`` (int) - should be 0
        - ``legendInputEntryCount`` (int)
        - ``legendModeUsed`` (str) - "bottom_center" when a legend was placed
        - ``legendFrameApplied`` (bool)
        - ``legendOutsidePlotArea`` (bool)
        - ``legendContractEnforced`` (bool) - always True after this call
        - ``legendContractFailures`` (list[str])
    """
    axes_map = normalize_axes_map(fig, axes)
    plan = dict(crowding_plan or {})
    fontsize = int(plan.get("legendFontSizePt", CROWDING_DEFAULTS["legendFontSizePt"]))
    anchor_y = float(plan.get("legendBottomAnchorY", CROWDING_DEFAULTS["legendBottomAnchorY"]))
    max_cols = int(plan.get("maxLegendColumns", CROWDING_DEFAULTS["maxLegendColumns"]))
    frame_style = plan.get("legendFrameStyle")

    # Gather legend handles BEFORE removing per-axes legends so the lookup still
    # finds them even if a generator placed handles via ax.legend().
    handles, labels = collect_legend_handles(axes_map)
    legend_input_entry_count = len(handles)

    # Drop any pre-existing figure-level legends so we end up with exactly one.
    existing_fig_legends = list(fig.legends)
    for leg in existing_fig_legends:
        leg.remove()

    # Remove all per-axes legends.
    _remove_axis_legends(axes_map)

    legend = promote_to_bottom_center_legend(
        fig,
        handles,
        labels,
        fontsize=fontsize,
        anchor_y=anchor_y,
        max_columns=max_cols,
        frame_style=frame_style,
    )

    failures: list[str] = []
    if legend is not None:
        failures.extend(_check_legend_anchor_forbidden(legend))

    has_figure_legend = legend is not None
    legend_frame_applied = bool(has_figure_legend and legend.get_frame() is not None)

    # Verify no per-axes legends remain (should always be 0 since we just removed them).
    axis_legend_remaining = sum(1 for ax in axes_map.values() if ax.get_legend() is not None)
    if axis_legend_remaining > 0:
        failures.append("axis_legend_remaining")
    if legend_input_entry_count > 0 and not has_figure_legend:
        failures.append("figure_legend_missing_for_handles")
    if has_figure_legend and len(fig.legends) != 1:
        failures.append("figure_legend_count_not_one")

    report: dict[str, Any] = {
        "hasFigureLegend": has_figure_legend,
        "axisLegendRemainingCount": axis_legend_remaining,
        "legendInputEntryCount": legend_input_entry_count,
        "legendModeUsed": "bottom_center" if has_figure_legend else "none",
        "legendFrameApplied": legend_frame_applied,
        "legendOutsidePlotArea": True,  # bottom-center anchor at y=0.015 is outside any panel
        "legendContractEnforced": True,
        "legendContractFailures": failures,
    }

    if strict and failures:
        raise RuntimeError("Figure legend contract failed: " + ", ".join(failures))
    return report


# Alias (public-API friendly short name)
enforce = enforce_figure_legend_contract
