# Technique: Ridgeline + Heat Strip Composite

Anchor case:
- `期刊复现：Advanced Science 贝叶斯山脊图 + 热图组合策略（附代码）_1777451123`

## Hallmark elements

- A single-row asymmetric `GridSpec(1, 5)` with width ratios
  `[4.2, 0.35, 0.6, 4.2, 0.35]`.
- Left and right condition lanes, each pairing a wide Bayesian posterior
  ridgeline panel with a very narrow correlation heat strip.
- Ridge layer sandwich: black zero reference line at zorder 1, filled
  posterior density at zorder 3, white outline at zorder 4, probability text
  at zorder 5.
- Positive posterior means use red; negative means use blue.
- Heat strips use `imshow(..., cmap='RdBu_r', vmin=-0.6, vmax=0.6,
  aspect='auto', origin='lower')`.
- Heat strip y labels sit on the right and significant cells use centered
  star annotations.
- Each heat strip has an embedded horizontal colorbar below the strip.

## Executable mapping: Bayesian ridge heatmap board

Route through `gen_ridge` when `visualContentPlan.templateMotifs` or
`specialPatterns` contains `bayesian_ridge_heatmap_board`,
`ridge_heatmap_composite`, or `bayesian_ridgeline_heatmap`.

The generator calls:

```python
draw_bayesian_ridge_heatmap_board(
    df,
    condition_col=condition_col,
    factor_col=factor_col,
    draw_col=posterior_col,
    correlation_col=correlation_col,
)
```

Required applied motifs:

- `bayesian_ridge_heatmap_board`
- `ridge_heatmap_composite`
- `inset_heatmap_colorbar`

## QA signals

- `ridgePanelCount` is 2.
- `heatmapStripCount` is 2.
- `ridgeFillCount` equals condition count times factor count.
- `colorbarSlotCount` is 2 for the embedded heatmap colorbars.
- `bayesianRidgeGridWidthRatios` equals `[4.2, 0.35, 0.6, 4.2, 0.35]`.

Case-090 audit note: the later queue pass over this Markdown was treated as
`duplicate_markdown_covered_by_case_025`; keep using this Bayesian ridge plus
heat-strip board rather than a generic ridgeline or heatmap template.
