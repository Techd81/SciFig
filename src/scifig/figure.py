"""Object-oriented multi-panel figure builder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import matplotlib.pyplot as plt

from .charts import generate
from .export import export_figure
from .ingest import profile_data
from .palettes import resolve_palette
from .styles import apply_style
from .types import ChartPlan, DataInput


@dataclass
class _Panel:
    chart: str
    data: DataInput
    position: Tuple[int, int]


class Figure:
    def __init__(self, style: str = "nature", palette: Any = "colorblind", grid: Optional[Tuple[int, int]] = None):
        self.style = style
        self.palette = palette
        self.grid = grid or (1, 1)
        self.recipe = "single"
        self._panels: List[_Panel] = []

    def add_panel(self, chart: str, data: DataInput, position: Tuple[int, int] = (0, 0)) -> "Figure":
        self._panels.append(_Panel(chart=chart, data=data, position=position))
        rows = max(self.grid[0], position[0] + 1)
        cols = max(self.grid[1], position[1] + 1)
        self.grid = (rows, cols)
        return self

    def compose(self, recipe: str = "storyboard_2x2") -> "Figure":
        self.recipe = recipe
        if recipe in ("storyboard_2x2", "story_board_2x2"):
            self.grid = (max(self.grid[0], 2), max(self.grid[1], 2))
        elif recipe == "comparison_pair":
            self.grid = (1, max(self.grid[1], 2))
        elif recipe == "hero_plus_stacked":
            self.grid = (max(self.grid[0], 2), max(self.grid[1], 2))
        else:
            self.grid = (max(self.grid[0], 1), max(self.grid[1], 1))
        return self

    def render(self, output: Optional[Union[str, Path]] = None, dpi: int = 300) -> Any:
        profile = apply_style(self.style)
        palette_map = resolve_palette(self.palette)
        rows, cols = self.grid
        width_mm = profile["double_width_mm"] if cols > 1 else profile["single_width_mm"]
        height_mm = min(profile["max_height_mm"], 55.0 * rows)
        fig, axes = plt.subplots(rows, cols, figsize=(width_mm / 25.4, height_mm / 25.4), squeeze=False, constrained_layout=True)
        for idx, panel in enumerate(self._panels):
            ax = axes[panel.position[0]][panel.position[1]]
            df, data_profile = profile_data(panel.data)
            plan = ChartPlan(primary_chart=panel.chart)
            generate(panel.chart, df, data_profile, plan, dict(plt.rcParams), palette_map, ax=ax)
            ax.text(-0.06, 1.08, chr(65 + idx), transform=ax.transAxes, fontsize=profile["panel_label_pt"],
                    fontweight="bold", va="bottom", ha="left")
        for r in range(rows):
            for c in range(cols):
                if not axes[r][c].has_data() and not axes[r][c].texts:
                    axes[r][c].set_axis_off()
        handles = []
        labels = []
        for ax in fig.axes:
            h, l = ax.get_legend_handles_labels()
            for handle, label in zip(h, l):
                if label not in labels:
                    handles.append(handle)
                    labels.append(label)
            legend = ax.get_legend()
            if legend is not None:
                legend.remove()
        if handles:
            fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.01), ncol=min(4, len(labels)),
                       frameon=True, edgecolor="#cccccc", borderpad=0.4)
        if output is not None:
            chart_label = self._panels[0].chart if self._panels else "multipanel"
            return export_figure(fig, output, chart=chart_label, style=self.style, dpi=dpi)
        return fig
