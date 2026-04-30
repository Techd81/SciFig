```python
# Multi-panel Composition

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

RECIPE_GEOMETRY = {
    "single":                  {"rows": 1, "cols": 1, "axes_map": {"A": (0, 0, 1, 1)}},
    "comparison_pair":         {"rows": 1, "cols": 2, "axes_map": {"A": (0, 0, 1, 1), "B": (0, 1, 1, 1)}},
    "hero_plus_stacked_support": {"rows": 2, "cols": 2, "axes_map": {"A": (0, 0, 2, 1), "B": (0, 1, 1, 1), "C": (1, 1, 1, 1)}},
    "story_board_2x2":         {"rows": 2, "cols": 2, "axes_map": {"A": (0, 0, 1, 1), "B": (0, 1, 1, 1), "C": (1, 0, 1, 1), "D": (1, 1, 1, 1)}},
    "triple_horizontal":       {"rows": 1, "cols": 3, "axes_map": {"A": (0, 0, 1, 1), "B": (0, 1, 1, 1), "C": (0, 2, 1, 1)}},
    "triple_vertical":         {"rows": 3, "cols": 1, "axes_map": {"A": (0, 0, 1, 1), "B": (1, 0, 1, 1), "C": (2, 0, 1, 1)}},
    "stacked_pair":            {"rows": 2, "cols": 1, "axes_map": {"A": (0, 0, 1, 1), "B": (1, 0, 1, 1)}},
    "board_2x3":               {"rows": 2, "cols": 3, "axes_map": {"A": (0, 0, 1, 1), "B": (0, 1, 1, 1), "C": (0, 2, 1, 1), "D": (1, 0, 1, 1), "E": (1, 1, 1, 1), "F": (1, 2, 1, 1)}},
    "board_3x3":               {"rows": 3, "cols": 3, "axes_map": {"A": (0, 0, 1, 1), "B": (0, 1, 1, 1), "C": (0, 2, 1, 1), "D": (1, 0, 1, 1), "E": (1, 1, 1, 1), "F": (1, 2, 1, 1), "G": (2, 0, 1, 1), "H": (2, 1, 1, 1), "I": (2, 2, 1, 1)}},
    "hero_plus_triple_support": {"rows": 3, "cols": 2, "axes_map": {"A": (0, 0, 3, 1), "B": (0, 1, 1, 1), "C": (1, 1, 1, 1), "D": (2, 1, 1, 1)}},
    "asymmetric_L":            {"rows": 2, "cols": 2, "axes_map": {"A": (0, 0, 1, 2), "B": (1, 0, 1, 1), "C": (1, 1, 1, 1)}},
}

RECIPE_CANVAS = {
    "single":                  {"width": "single", "height_key": "single",              "default_h": 62},
    "comparison_pair":         {"width": "double", "height_key": "comparison_pair",     "default_h": 78},
    "hero_plus_stacked_support": {"width": "double", "height_key": "hero_plus_stacked_support", "default_h": 134},
    "story_board_2x2":         {"width": "double", "height_key": "story_board_2x2",    "default_h": 146},
    "triple_horizontal":       {"width": "double", "height_key": "triple_horizontal",  "default_h": 68},
    "triple_vertical":         {"width": "single", "height_key": "triple_vertical",    "default_h": 100},
    "stacked_pair":            {"width": "single", "height_key": "stacked_pair",        "default_h": 95},
    "board_2x3":               {"width": "double", "height_key": "board_2x3",           "default_h": 200},
    "board_3x3":               {"width": "double", "height_key": "board_3x3",           "default_h": 270},
    "hero_plus_triple_support": {"width": "double", "height_key": "hero_plus_triple_support", "default_h": 170},
    "asymmetric_L":            {"width": "double", "height_key": "asymmetric_L",        "default_h": 130},
}


def resolve_canvas(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    cfg = RECIPE_CANVAS.get(recipe, RECIPE_CANVAS["story_board_2x2"])
    heights = journalProfile.get("canvas_height_mm", {})
    width_key = "double_width_mm" if cfg["width"] == "double" else "single_width_mm"
    return {
        "width_mm": journalProfile.get(width_key, 183),
        "height_mm": heights.get(cfg["height_key"], cfg["default_h"]),
    }


def resolve_panel_geometry(panelBlueprint, journalProfile):
    recipe = panelBlueprint["layout"]["recipe"]
    geo = RECIPE_GEOMETRY.get(recipe, RECIPE_GEOMETRY["story_board_2x2"])
    gap = max(journalProfile.get("panel_gap_rel", 0.18), 0.24 if recipe != "single" else 0.0)
    return {
        "engine": "GridSpec" if geo["rows"] > 1 or geo["cols"] > 2 else "subplots",
        "rows": geo["rows"],
        "cols": geo["cols"],
        "axes_map": geo["axes_map"],
        "hspace": gap if geo["rows"] > 1 else 0.0,
        "wspace": gap if geo["cols"] > 1 else 0.0,
    }


def gen_multipanel(chartPlan, journalProfile, colorSystem, dataProfile, rcParams, col_map=None):
    panelBlueprint = chartPlan["panelBlueprint"]
    panels = panelBlueprint["panels"]
    geometry = resolve_panel_geometry(panelBlueprint, journalProfile)
    canvas = resolve_canvas(panelBlueprint, journalProfile)

    mm = 1 / 25.4
    fig = plt.figure(figsize=(canvas["width_mm"] * mm, canvas["height_mm"] * mm), constrained_layout=False)

    gs = GridSpec(
        geometry["rows"], geometry["cols"],
        figure=fig,
        hspace=geometry["hspace"],
        wspace=geometry["wspace"],
    )
    axes = {}
    for panel_id, (r, c, rs, cs) in geometry["axes_map"].items():
        axes[panel_id] = fig.add_subplot(gs[r:r+rs, c:c+cs])

    for panel in panels:
        panel_id = panel["id"]
        if panel_id not in axes:
            continue
        chart_type = panel["chart"]
        ax = axes[panel_id]
        gen_func_name = CHART_GENERATORS.get(chart_type)
        if gen_func_name:
            gen_func = globals().get(gen_func_name)
            if gen_func:
                gen_func(dataProfile["df"], dataProfile, chartPlan, rcParams,
                         colorSystem, col_map=col_map, ax=ax)

    apply_visual_content_pass(fig, axes, chartPlan, dataProfile, journalProfile,
                              colorSystem, col_map=col_map)
    crowding_result = enforce_figure_legend_contract(fig, axes, chartPlan, journalProfile)
    chartPlan["crowdingResult"] = crowding_result

    for panel in panels:
        panel_id = panel["id"]
        if panel_id not in axes:
            continue
        ax = axes[panel_id]
        label_x, label_y = journalProfile.get("panel_label_offset_xy", [-0.12, 1.05])
        ax.text(label_x, label_y, panel_id, transform=ax.transAxes,
                fontsize=journalProfile.get("font_size_panel_label_pt", 8),
                fontweight="bold", va="top", ha="left")

    return fig
```
