# Technique: Cell Marker Bar + Scatter

Anchor case: `高级感！Python复刻Cell顶刊散点柱状图_1777451193`.

Case-077 evidence lives in
`.workflow/case_studies/case_077_cell_marker_bar_scatter/comparison_report.json`.

## Hallmark Elements

1. Single-panel marker-composition chart, not a multi-panel board.
2. Non-uniform x coordinates create a semantic gap between dorsal and ventral
   marker blocks.
3. Bars show group means as the background layer.
4. Error bars sit above bars.
5. Jittered sample points sit on top with black edges.
6. Top horizontal rules label marker blocks such as `dorsal` and `ventral`.
7. The y-limit is derived from the maximum upper error bound so top group labels
   do not collide with data.

## Reference Pattern

```python
markers = ["PAX6", "EMX2", "TBR2", "MAP2", "NKX2-1", "OLIG2", "DLX2", "GAD67", "GAD65"]
x_pos = [0, 1, 2, 3, 4.5, 5.5, 6.5, 7.5, 8.5]

for i, marker in enumerate(markers):
    ax.bar(x_pos[i], mean_val, 0.6, color=color, edgecolor="black",
           alpha=0.7, zorder=1)
    ax.errorbar(x_pos[i], mean_val, yerr=std_val, fmt="none",
                ecolor="black", capsize=5, zorder=2)
    jitter = np.random.normal(0, 0.07, size=len(data_series))
    ax.scatter(x_pos[i] + jitter, data_series, s=100, color=color,
               edgecolor="black", zorder=3)

dynamic_ylim = global_max * 1.25
line_y = global_max * 1.2
ax.hlines(line_y, x_pos[0] - 0.4, x_pos[3] + 0.4, colors="black", linewidth=3)
ax.text((x_pos[0] + x_pos[3]) / 2, line_y + dynamic_ylim * 0.02,
        "dorsal", ha="center", va="bottom", fontweight="bold")
```

## Discipline Rules

- Treat the top rules as group-navigation labels, not significance brackets.
- Keep the semantic x gap even when categories are evenly sampled.
- Do not hide jittered sample points behind bars; raw observations are the top
  evidence layer.
- Use black bar and point edges for Cell-like print contrast.
- Rotate x tick labels only enough to protect marker names.

## QA Contract

- `nonUniformXGap == true`
- `barCount == markerCategoryCount`
- `errorbarCount == markerCategoryCount`
- `jitterScatterLayerCount == markerCategoryCount`
- `topGroupRuleCount >= 2`
- `groupLabelCount >= 2`
