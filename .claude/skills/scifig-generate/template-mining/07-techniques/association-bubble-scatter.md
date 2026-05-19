# Technique: Association Bubble Scatter

Anchor case: `精准复现顶刊插图：Python实战零售食品环境与肥胖率关联气泡图！_1778682618`.

Case-098 evidence lives in
`.workflow/case_studies/case_098_food_environment_obesity_bubble_scatter/comparison_report.json`.

## Hallmark Elements

1. One x/y association is the primary message.
2. Bubble area encodes a third numeric quantity such as population.
3. Bubble color encodes a categorical group such as income classification.
4. Group legend uses fixed-size proxy circles, not the scaled data bubbles.
5. Statistical summary is a boxed Spearman `r` annotation inside the axes.
6. The plot uses an open L-frame: left and bottom spines only, no grid.
7. `tight_layout(rect=...)` reserves right-side space for the external legend.

## Rendering Contract

- Use the existing `bubble_scatter` family; do not add a separate public chart
  key for this article.
- Require explicit x, y, size, and category/color columns.
- Normalize bubble size with a documented formula such as
  `population / max(population) * 3000`.
- Keep category colors stable in both data marks and proxy legend handles.
- Compute Spearman correlation on the x/y columns and place `r = ...` in a
  lower-right axes-coordinate text box.
- Hide top/right spines and keep the left/bottom spines and major ticks thick
  enough for print.

## QA Contract

- `bubble_scatter_count == 1`
- `category_count >= 2`
- `size_encoding` is documented
- `color_encoding` is documented
- `proxy_legend_count >= 1`
- `spearman_annotation_count == 1`
- `grid_enabled == false`
- `visible_spines` equals `["left", "bottom"]` for the source-like style
