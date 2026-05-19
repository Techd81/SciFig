# Technique: Threshold / Hump Regression

Anchor case:
- `期刊复现：Advanced Science “驼峰”阈值回归图解剖与复刻（附Python源码）_1777450933`

## Hallmark elements

The transferable visual grammar is a single high-density scatter-regression
panel:

- Light gray panel background with white dashed grid.
- Coral sample scatter above a gray bootstrap confidence band.
- Black global cubic trend line forming the hump.
- Red dashed vertical threshold line, shortened to the lower half of the panel.
- Two thick dashed segmented linear fits: cyan on the low-x side and green on
  the high-x side.
- Direct `R^2` text in axes coordinates plus a data-coordinate threshold label.
- Legend outside the right axis using `bbox_to_anchor=(1.02, 0.5)`.

## Executable mapping: hump threshold regression

Route through `gen_scatter_regression` when `visualContentPlan.templateMotifs`
or `specialPatterns` contains `hump_threshold_regression`,
`threshold_hump_regression`, or `segmented_threshold_regression`.

```python
result = draw_hump_threshold_regression(
    df,
    x_col=x_col,
    y_col=y_col,
    threshold=chartPlan["visualContentPlan"].get("humpThresholdValue"),
    degree=3,
)
```

The generator must mark these motifs as applied:

- `hump_threshold_regression`
- `regression_band_fillbtw`
- `threshold_split_line`

## QA signals

- `templateMotifsApplied` contains `hump_threshold_regression`.
- `confidenceBandCount` is at least 1.
- `regressionLineCount` is at least 1 for the black global curve.
- `segmentedRegressionLineCount` is exactly 2 when both sides of the threshold
  have enough data.
- `thresholdLineCount` and `referenceLineCount` are at least 1.
- `externalLegendCount` is at least 1.

Case-089 audit note: the later queue pass over this Markdown was treated as
`duplicate_markdown_covered_by_case_024`; keep using the hump-threshold
regression helper rather than a generic polynomial scatter fit.
