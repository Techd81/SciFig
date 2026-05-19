# Parity CI Matrix

Anchor case: `Python科研绘图：一行代码实现 R² + 95% 置信区间的高级散点图_1777452391`.

Case-083 evidence lives in
`.workflow/case_studies/case_083_parity_ci_matrix/comparison_report.json`.

## Learned Essence

1. Use a 2x2 GridSpec board for multiple prediction tasks.
2. Force equal x/y limits and equal aspect in each panel so the 45-degree
   bisect line stays visually honest.
3. Draw the bisect line below the statistical layers.
4. Encode Training and Testing with fixed dark-blue / dark-red hollow markers.
5. Draw split-specific regression lines plus 95% confidence shadow bands.
6. Anchor R2/RMSE metric boxes and panel letters in `transAxes`.

## Helper Binding

```python
styles = resolve_parity_split_style_map(splits, variant="spt_train_test")
```

The returned styles include marker edge color, regression line color, CI band
alpha, marker size, and zorder levels.

## Generator Mapping

`gen_scatter_regression` enters this mode when:

- `panel` / `facet` / `task` / `target` / `property` role exists
- `split` / `sample_type` / `source` / `set` / `dataset` role exists
- x and y numeric roles are actual/predicted values
- the template motif or data pattern contains `parity_ci_matrix`

The generator renders the full board in standalone mode and returns the first
axis for compatibility with the existing generator contract.

## QA Contract

- `templateMotifCount` includes `parity_ci_matrix`.
- `referenceLineCount`, `metricBoxCount`, and `panelLabelCount` equal the number
  of rendered panels.
- `ciBandCount` should equal `panel_count * split_count` when every split has
  enough points for a fitted confidence interval.
- `equalAspectPanels` should equal the number of rendered panels.
- CI bands are estimated from actual data points in each split; do not invent
  confidence bands when a split has too few points.
- Legends remain figure-level, not repeated in every panel.

## Variant: Multi-model parity grid

Anchor: `期刊复现：多面板回归预测散点图对比不同模型真实与预测偏差_1777455863`.

Use this when the same experimental/predicted target is compared across several
algorithms or model families:

- Layout is usually `2x3` with one model per panel.
- All panels must share identical x/y limits and equal aspect, or visual model
  ranking becomes invalid.
- Draw a solid black `y=x` line in every panel as the absolute accuracy
  reference.
- Draw fixed red dashed tolerance bands such as `+/-15%` only when supplied by
  the article, prompt, or domain convention. These are tolerance bounds, not
  fitted confidence intervals.
- Put model name, R2, and RMSE in a compact in-panel metric box.
- Runtime status: current `scatter_regression` validates only one parity panel;
  no public generator yet composes the full shared-scale multi-model grid.

Case-043 evidence lives in
`.workflow/case_studies/case_043_multimodel_parity_grid/comparison_report.json`.
