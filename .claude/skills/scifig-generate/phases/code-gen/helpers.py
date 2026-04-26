```python
# Shared Helper Functions for Chart Generators and Crowding Control

import re
import numpy as np


def sanitize_columns(df):
    """Rename columns to safe Python identifiers. Returns (df_renamed, name_map)."""
    name_map = {}
    new_cols = []
    for col in df.columns:
        safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(col)).strip('_')
        if safe and safe[0].isdigit():
            safe = 'col_' + safe
        safe = safe or 'unnamed'
        base = safe
        i = 1
        while safe in new_cols:
            safe = f"{base}_{i}"
            i += 1
        new_cols.append(safe)
        if safe != col:
            name_map[safe] = col
    df.columns = new_cols
    return df, name_map


def apply_chart_polish(ax, chart_type):
    """Apply publication-quality post-processing to any axes."""
    ax.spines["top"].set_visible(False)
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


def add_significance_bracket(ax, x1, x2, y, height, p_value, lw=0.6):
    """Add a Nature-style significance bracket with T-caps and italic p."""
    cap_w = height * 0.25
    ax.plot([x1, x1], [y, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x2, x2], [y, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x1, x2], [y + height, y + height], lw=lw, c="black", clip_on=False)
    ax.plot([x1 - cap_w, x1 + cap_w], [y, y], lw=lw, c="black", clip_on=False)
    ax.plot([x2 - cap_w, x2 + cap_w], [y, y], lw=lw, c="black", clip_on=False)
    if p_value < 0.001:
        p_text = "p < 0.001"
    else:
        p_text = f"p = {p_value:.3g}"
    ax.text((x1 + x2) / 2, y + height * 1.1, p_text, ha="center", va="bottom",
            fontsize=6, fontstyle="italic")


def format_p_value(p_value):
    if p_value < 0.001:
        return "p < 0.001"
    return f"p = {p_value:.2g}"


def _resolve_roles(dataProfile):
    roles = dataProfile.get("semanticRoles", {})
    group_col = roles.get("group")
    value_col = roles.get("value") or roles.get("y")
    x_col = roles.get("x") or roles.get("condition")
    return group_col, value_col, x_col


def _extract_colors(palette, categories):
    cat_colors = palette.get("categoryMap", {})
    fallback = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73",
                                            "#F0E442", "#0072B2", "#D55E00", "#CC79A7"])
    color_map = {}
    for i, cat in enumerate(categories):
        if cat in cat_colors:
            color_map[cat] = cat_colors[cat]
        else:
            color_map[cat] = fallback[i % len(fallback)]
    return color_map


def display_label(sanitized_name, col_map):
    return col_map.get(sanitized_name, sanitized_name)


def default_crowding_plan():
    return {
        "legendScope": "figure",
        "legendMode": "bottom_center",
        "legendPlacementPriority": ["bottom_center", "top_center", "outside_right"],
        "legendLabelMaxChars": 32,
        "maxLegendColumns": 6,
        "forbidInAxesLegend": True,
        "colorbarMode": "none",
        "maxDirectLabelsHero": 5,
        "maxDirectLabelsSupport": 3,
        "maxBracketGroups": 2,
        "pointDensityMode": "alpha_jitter_small_markers",
        "simplifyIfCrowded": True,
        "simplificationsApplied": [],
        "droppedDirectLabelCount": 0,
    }


def dedupe_handles_labels(handles, labels):
    seen = set()
    out_handles = []
    out_labels = []
    for handle, label in zip(handles, labels):
        clean = str(label).strip()
        if not clean or clean == "_nolegend_" or clean in seen:
            continue
        seen.add(clean)
        out_handles.append(handle)
        out_labels.append(clean)
    return out_handles, out_labels


def collect_legend_entries(axes):
    handles = []
    labels = []
    for ax in axes.values():
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
        legend = ax.get_legend()
        if legend is not None:
            legend_handles = getattr(legend, "legend_handles", None)
            if legend_handles is None:
                legend_handles = getattr(legend, "legendHandles", [])
            legend_labels = [text.get_text() for text in legend.get_texts()]
            handles.extend(legend_handles)
            labels.extend(legend_labels)
    return dedupe_handles_labels(handles, labels)


def remove_axis_legends(axes):
    removed = 0
    for ax in axes.values():
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()
            removed += 1
    return removed


def shorten_legend_labels(labels, max_chars=32):
    shortened = False
    output = []
    for label in labels:
        clean = str(label).strip()
        if max_chars and len(clean) > max_chars:
            output.append(clean[:max_chars - 3].rstrip() + "...")
            shortened = True
        else:
            output.append(clean)
    return output, shortened


def trim_excess_text_annotations(ax, max_keep):
    if max_keep is None:
        return 0
    texts = list(ax.texts)
    if len(texts) <= max_keep:
        return 0
    removed = 0
    for text in texts[max_keep:]:
        text.remove()
        removed += 1
    return removed


def trim_pvalue_annotations(ax, max_keep=2):
    p_texts = [text for text in list(ax.texts) if str(text.get_text()).startswith("p")]
    removed = 0
    for text in p_texts[max_keep:]:
        text.remove()
        removed += 1
    return removed


def find_first_mappable(ax):
    for artist in list(ax.images) + list(ax.collections):
        if hasattr(artist, "get_array"):
            data = artist.get_array()
            if data is not None:
                return artist
    return None


def remove_extra_axes(fig, axes):
    panel_axes = set(axes.values())
    for extra_ax in [ax for ax in list(fig.axes) if ax not in panel_axes]:
        extra_ax.remove()


def get_non_panel_axes(fig, axes):
    panel_axes = set(axes.values())
    return [ax for ax in list(fig.axes) if ax not in panel_axes]


def _bbox_in_figure_coords(fig, artist):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    return artist.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())


def legend_overlaps_axes(fig, legend, axes):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend_box = legend.get_window_extent(renderer=renderer)
    return any(legend_box.overlaps(ax.get_window_extent(renderer=renderer)) for ax in axes)


def apply_subplot_margins(fig, legend_mode, has_colorbar=False, legend=None):
    subplotpars = fig.subplotpars
    left = 0.11
    top = min(subplotpars.top, 0.95)
    bottom = max(subplotpars.bottom, 0.12)
    right = min(subplotpars.right, 0.95)

    if has_colorbar:
        right = min(right, 0.78)

    if legend is not None:
        legend_box = _bbox_in_figure_coords(fig, legend)
        if legend_mode == "bottom_center":
            bottom = max(bottom, min(0.74, legend_box.y1 + 0.035))
        elif legend_mode == "top_center":
            top = min(top, max(0.26, legend_box.y0 - 0.035))
        elif legend_mode == "outside_right":
            right = min(right, max(0.30, legend_box.x0 - 0.035))

    if right <= left + 0.12:
        right = left + 0.12
    if top <= bottom + 0.12:
        if legend_mode == "bottom_center":
            bottom = max(0.12, top - 0.12)
        else:
            top = min(0.95, bottom + 0.12)

    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)


def _unique_modes(modes):
    out = []
    for mode in modes:
        if mode and mode not in out:
            out.append(mode)
    return out


def _legend_column_options(label_count, legend_mode, max_columns):
    if legend_mode == "outside_right":
        return [1]
    candidates = [
        min(label_count, max_columns),
        min(label_count, 4),
        min(label_count, 3),
        min(label_count, 2),
        1,
    ]
    return [n for n in dict.fromkeys(candidates) if n >= 1]


def create_figure_legend(fig, handles, labels, legend_mode, fontsize, ncol=1):
    common = {
        "ncol": ncol,
        "frameon": False,
        "fontsize": fontsize,
        "borderaxespad": 0.0,
        "handlelength": 1.2,
        "handletextpad": 0.4,
        "labelspacing": 0.35,
        "columnspacing": 0.8,
    }
    if legend_mode == "outside_right":
        return fig.legend(handles, labels, loc="center left",
                          bbox_to_anchor=(0.80, 0.5), **common)
    if legend_mode == "top_center":
        return fig.legend(handles, labels, loc="upper center",
                          bbox_to_anchor=(0.5, 0.99), **common)
    return fig.legend(handles, labels, loc="lower center",
                      bbox_to_anchor=(0.5, 0.01), **common)


def enforce_non_overlapping_legend(fig, legend, legend_mode, occupied_axes, has_colorbar=False):
    for _ in range(8):
        apply_subplot_margins(fig, legend_mode, has_colorbar=has_colorbar, legend=legend)
        if not legend_overlaps_axes(fig, legend, occupied_axes):
            return True

        subplotpars = fig.subplotpars
        if legend_mode == "bottom_center":
            next_bottom = min(0.76, subplotpars.bottom + 0.04)
            fig.subplots_adjust(bottom=next_bottom)
        elif legend_mode == "top_center":
            next_top = max(subplotpars.bottom + 0.12, subplotpars.top - 0.04)
            fig.subplots_adjust(top=next_top)
        elif legend_mode == "outside_right":
            next_right = max(0.28, subplotpars.right - 0.04)
            fig.subplots_adjust(right=next_right)

    return not legend_overlaps_axes(fig, legend, occupied_axes)


def place_shared_legend(fig, axes, occupied_axes, crowdingPlan, journalProfile, has_colorbar=False, handles=None, labels=None):
    if handles is None or labels is None:
        handles, labels = collect_legend_entries(axes)
    empty_info = {
        "legendScope": "figure",
        "legendLabelsShortened": False,
        "legendNColumns": 0,
        "legendOutsidePlotArea": True,
    }
    if not handles:
        return None, crowdingPlan.get("legendMode", "bottom_center"), empty_info

    requested_mode = crowdingPlan.get("legendMode", "bottom_center")
    if requested_mode == "shared_auto":
        requested_mode = "bottom_center"
    priority = crowdingPlan.get("legendPlacementPriority") or ["bottom_center", "top_center", "outside_right"]
    candidate_modes = _unique_modes(priority + [requested_mode, "bottom_center", "top_center", "outside_right"])
    fontsize = journalProfile.get("font_size_small_pt", 5)
    max_label_chars = crowdingPlan.get("legendLabelMaxChars", 32)
    max_columns = crowdingPlan.get("maxLegendColumns", 6)
    legend_labels, labels_shortened = shorten_legend_labels(labels, max_label_chars)
    info = {
        "legendScope": "figure",
        "legendLabelsShortened": labels_shortened,
        "legendNColumns": 0,
        "legendOutsidePlotArea": False,
    }

    for mode in candidate_modes:
        for ncol in _legend_column_options(len(legend_labels), mode, max_columns):
            for existing in list(fig.legends):
                existing.remove()
            legend = create_figure_legend(fig, handles, legend_labels, mode, fontsize, ncol=ncol)
            ok = enforce_non_overlapping_legend(
                fig,
                legend,
                mode,
                occupied_axes,
                has_colorbar=has_colorbar,
            )
            if ok:
                info["legendNColumns"] = ncol
                info["legendOutsidePlotArea"] = True
                return legend, mode, info

    for existing in list(fig.legends):
        existing.remove()
    fallback_mode = "outside_right"
    legend = create_figure_legend(fig, handles, legend_labels, fallback_mode, fontsize, ncol=1)
    apply_subplot_margins(fig, fallback_mode, has_colorbar=has_colorbar, legend=legend)
    info["legendNColumns"] = 1
    info["legendOutsidePlotArea"] = not legend_overlaps_axes(fig, legend, occupied_axes)
    return legend, fallback_mode, info


def apply_crowding_management(fig, axes, chartPlan, journalProfile):
    crowdingPlan = {**default_crowding_plan(), **chartPlan.get("crowdingPlan", {})}
    panelBlueprint = chartPlan.get("panelBlueprint", {})

    dropped_direct_labels = 0
    for panel_id, ax in axes.items():
        if panel_id == "A":
            dropped_direct_labels += trim_excess_text_annotations(ax, crowdingPlan.get("maxDirectLabelsHero"))
        else:
            dropped_direct_labels += trim_excess_text_annotations(ax, crowdingPlan.get("maxDirectLabelsSupport"))
        trim_pvalue_annotations(ax, crowdingPlan.get("maxBracketGroups", 2))

    handles, labels = collect_legend_entries(axes)
    removed_axis_legends = remove_axis_legends(axes)
    legend = None
    legend_mode_used = "none"
    legend_info = {
        "legendScope": "figure",
        "legendLabelsShortened": False,
        "legendNColumns": 0,
        "legendOutsidePlotArea": True,
    }
    shared_colorbar_applied = False
    if panelBlueprint.get("sharedColorbar", False):
        remove_extra_axes(fig, axes)
        mappable = None
        for ax in axes.values():
            mappable = find_first_mappable(ax)
            if mappable is not None:
                break
        if mappable is not None:
            fig.colorbar(mappable, ax=list(axes.values()), shrink=0.6, pad=0.02)
            shared_colorbar_applied = True

    occupied_axes = list(axes.values()) + get_non_panel_axes(fig, axes)
    if handles:
        legend, legend_mode_used, legend_info = place_shared_legend(
            fig,
            axes,
            occupied_axes,
            crowdingPlan,
            journalProfile,
            has_colorbar=shared_colorbar_applied,
            handles=handles,
            labels=labels,
        )

    apply_subplot_margins(fig, legend_mode_used, has_colorbar=shared_colorbar_applied, legend=legend)

    crowdingPlan["droppedDirectLabelCount"] = dropped_direct_labels
    crowdingPlan["legendScope"] = "figure"
    crowdingPlan["legendModeUsed"] = legend_mode_used
    crowdingPlan["axisLegendRemovedCount"] = removed_axis_legends
    crowdingPlan["legendNColumns"] = legend_info.get("legendNColumns", 0)
    crowdingPlan["legendLabelsShortened"] = legend_info.get("legendLabelsShortened", False)
    crowdingPlan["legendOutsidePlotArea"] = legend_info.get("legendOutsidePlotArea", True)
    simplifications = list(crowdingPlan.get("simplificationsApplied", []))
    if legend is not None:
        simplifications.append("figure_level_shared_legend")
    if removed_axis_legends:
        simplifications.append(f"axis_legends_removed:{removed_axis_legends}")
    if legend_info.get("legendLabelsShortened", False):
        simplifications.append("legend_labels_shortened")
    if dropped_direct_labels:
        simplifications.append(f"direct_labels_trimmed:{dropped_direct_labels}")
    crowdingPlan["simplificationsApplied"] = list(dict.fromkeys(simplifications))
    chartPlan["crowdingPlan"] = crowdingPlan

    return {
        "droppedDirectLabelCount": dropped_direct_labels,
        "legendModeUsed": legend_mode_used,
        "sharedColorbarApplied": shared_colorbar_applied,
        "hasFigureLegend": legend is not None,
        "axisLegendRemovedCount": removed_axis_legends,
        "legendOutsidePlotArea": legend_info.get("legendOutsidePlotArea", True),
        "legendLabelsShortened": legend_info.get("legendLabelsShortened", False),
    }
```
