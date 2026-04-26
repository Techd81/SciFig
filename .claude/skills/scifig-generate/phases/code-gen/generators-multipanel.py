```python
# Multi-panel Composition

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def resolve_canvas(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    if recipe == "single":
        return {"width_mm": journalProfile["single_width_mm"], "height_mm": 62}
    if recipe == "comparison_pair":
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": 78}
    if recipe == "hero_plus_stacked_support":
        return {"width_mm": journalProfile["double_width_mm"], "height_mm": 134}
    return {"width_mm": journalProfile["double_width_mm"], "height_mm": 146}


def resolve_panel_geometry(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    gap = max(journalProfile.get("panel_gap_rel", 0.18), 0.24 if recipe != "single" else 0.0)

    if recipe == "single":
        return {"engine": "subplots", "grid": "1x1", "hspace": 0.0, "wspace": 0.0}
    if recipe == "comparison_pair":
        return {"engine": "subplots", "grid": "1x2", "hspace": 0.0, "wspace": gap}
    if recipe == "hero_plus_stacked_support":
        return {"engine": "GridSpec", "grid": "2x2-hero-span", "hspace": gap, "wspace": gap}
    return {"engine": "GridSpec", "grid": "2x2", "hspace": gap, "wspace": gap}


def gen_multipanel(chartPlan, journalProfile, colorSystem, dataProfile, rcParams, col_map=None):
    panelBlueprint = chartPlan["panelBlueprint"]
    panels = panelBlueprint["panels"]
    geometry = resolve_panel_geometry(panelBlueprint, journalProfile)
    canvas = resolve_canvas(panelBlueprint, journalProfile)

    mm = 1 / 25.4
    fig = plt.figure(figsize=(canvas["width_mm"] * mm, canvas["height_mm"] * mm), constrained_layout=False)

    if geometry["engine"] == "GridSpec":
        gs = GridSpec(2, 2, figure=fig, hspace=geometry["hspace"], wspace=geometry["wspace"])
        if geometry["grid"] == "2x2-hero-span":
            axes = {
                "A": fig.add_subplot(gs[:, 0]),
                "B": fig.add_subplot(gs[0, 1]),
                "C": fig.add_subplot(gs[1, 1]),
            }
        else:
            axes = {
                "A": fig.add_subplot(gs[0, 0]),
                "B": fig.add_subplot(gs[0, 1]),
                "C": fig.add_subplot(gs[1, 0]),
                "D": fig.add_subplot(gs[1, 1]),
            }
    elif geometry["grid"] == "1x1":
        gs = fig.add_gridspec(1, 1)
        axes = {"A": fig.add_subplot(gs[0, 0])}
    else:
        gs = fig.add_gridspec(1, 2, wspace=geometry["wspace"])
        axes = {"A": fig.add_subplot(gs[0, 0]), "B": fig.add_subplot(gs[0, 1])}

    for panel in panels:
        panel_id = panel["id"]
        chart_type = panel["chart"]
        ax = axes[panel_id]
        gen_func_name = CHART_GENERATORS.get(chart_type)
        if gen_func_name:
            gen_func = globals().get(gen_func_name)
            if gen_func:
                gen_func(dataProfile["df"], dataProfile, chartPlan, rcParams,
                         colorSystem, col_map=col_map, ax=ax)

    apply_crowding_management(fig, axes, chartPlan, journalProfile)

    for panel in panels:
        panel_id = panel["id"]
        ax = axes[panel_id]
        ax.text(-0.12, 1.05, panel_id, transform=ax.transAxes,
                fontsize=journalProfile.get("font_size_panel_label_pt", 8),
                fontweight="bold", va="top", ha="left")

    return fig
```