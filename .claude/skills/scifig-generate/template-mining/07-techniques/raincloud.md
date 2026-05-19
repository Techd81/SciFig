# Technique: Raincloud Distribution

Use when grouped numeric data needs both distribution shape and raw observation
visibility. Raincloud plots are preferable to plain boxplots when multimodality,
skew, or sample clustering matters.

## Visual Grammar

- Use `raincloud` as the chart key for a single grouped distribution panel.
- For article-style two-metric boards, compose `subplots(1, 2)` and draw one
  raincloud panel per metric with independent y-axis scales.
- Layer order is fixed: half-violin density cloud at `zorder=1`, jittered raw
  observations at `zorder=2`, and narrow boxplot summary at `zorder=3`.
- Offset the half violin to one side of the categorical center and place the
  jittered rain points on the opposite side so the layers do not obscure each
  other.
- Use white point edges (`linewidth` about 0.5) and alpha about 0.70 for dense
  environmental or ecological observations.
- Keep the box face transparent and use black median/whisker strokes so the
  summary reads above the cloud and points.

## Two-Panel Flux Board

Anchor: `期刊配图：云雨图结合半小提琴与抖动散点展示不同城市化水平的通量差异`.

```python
fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(12, 5), dpi=300)
plt.subplots_adjust(wspace=0.25, bottom=0.15, left=0.08, right=0.95)

for ax, value_col, ylabel in [
    (ax1, "CH4_Flux", r"CH$_4$ flux (mmol m$^{-2}$ d$^{-1}$)"),
    (ax2, "CO2_Flux", r"CO$_2$ flux (mmol m$^{-2}$ d$^{-1}$)"),
]:
    draw_half_violin_cloud(ax, value_col, zorder=1)
    draw_jittered_rain(ax, value_col, edgecolor="white", alpha=0.70, zorder=2)
    draw_narrow_box(ax, value_col, width=0.12, facecolor="none", zorder=3)
    ax.set_ylabel(ylabel, fontweight="bold")
```

Case-061 evidence lives in
`.workflow/case_studies/case_061_greenhouse_flux_raincloud/comparison_report.json`.

Use the Case-061 `greenhouse_flux_raincloud` motif when the data has two gas or
flux metrics that share the same categorical grouping but need independent
y-axis units or tick formatters. This is a two-panel board, not a faceted
single-axis raincloud.

## Stacked Violin Metric Board

Anchor: `顶刊同款！Python绘制堆叠小提琴图_1777452180`.

Use this when model-comparison data contains repeated resampling values for
several incompatible metrics such as `R2`, `MAE`, and `RMSE`, and the story is
model stability rather than only mean rank.

Required rendering contract:

- Layout is `plt.subplots(3, 1, figsize=(7, 11), sharex=True,
  gridspec_kw={"hspace": 0.0})`.
- Each row is one metric with an independent y-axis scale; the x positions and
  model order are identical in every row.
- Layer order per model is full violin distribution first, narrow white boxplot
  summary second, and red median point third.
- Use one stable model palette across all metric rows, for example
  `#F79698`, `#6CA6F0`, `#98E6B6`, `#FBC285`.
- Hide upper-panel x tick labels and make separator spines dashed; emphasize
  the bottom spine on the final metric row.
- Place color-matched median value labels just beside the corresponding violin.

Case-074 evidence lives in
`.workflow/case_studies/case_074_stacked_violin_metric_board/comparison_report.json`.

## QA Counters

- `raincloudPanelCount` equals the number of composed metric panels.
- `halfViolinCount`, `jitterPointCount`, and `boxplotCount` are all positive.
- `raincloudLayerOrder` records cloud < points < box.
- `legendRemoved` is true when the source grammar has no legend.
- `independentYScales` is true for multi-metric flux boards.
- For stacked violin boards: `panelCount == metricPanelCount`,
  `violinLayerCount`, `boxplotLayerCount`, `medianPointCount`, and
  `medianLabelCount` are all at least `metricPanelCount * modelCount`.
