# Technique: Grouped Box Median Regression

Anchor case: `Python绘制箱型图与回归线，一眼看穿数据趋势！_1778682795`.

Case-093 evidence lives in
`.workflow/case_studies/case_093_grouped_box_median_regression/comparison_report.json`.

## Hallmark Elements

1. One categorical or ordinal interval axis with repeated samples per interval.
2. Two or more boxplot series share each interval center using stable left/right
   offsets.
3. Outliers are hidden when the trend story depends on the distribution body
   and median.
4. Trend lines are fitted to per-interval medians, not to every raw sample.
5. Alternating vertical interval bands replace a grid so bins remain readable
   without competing with the boxes.
6. A combined legend includes both box patches and median-regression lines.
7. Series-colored `k` / `R` text is anchored in axes coordinates, usually at the
   upper-right corner.

## Rendering Contract

- Use the existing `box` family; do not add a separate public chart key.
- Derive box positions from the ordinal interval center plus a deterministic
  offset per series.
- Compute one median per interval per series before fitting `linregress`.
- Draw each regression line across the full interval range with a dashed line
  that matches the series color.
- Keep median lines black so the fitted trend line is not confused with the box
  statistic inside each distribution.
- Keep `showfliers=False` only when the source or prompt asks for the article
  style; otherwise preserve outliers.
- Use thick four-side spines and bold ticks when the prompt asks for the local
  article style.

## QA Contract

Runtime metadata should record:

- `templateMotifsApplied` contains `grouped_box_median_regression`.
- `intervalCount` equals the number of category centers.
- `boxSeriesCount` equals the number of offset series.
- `boxCount == intervalCount * boxSeriesCount`.
- `medianRegressionLineCount == boxSeriesCount`.
- `regressionBasis == "per_interval_medians"`.
- `combinedLegendCount >= 1` and `legendItemCount >= boxSeriesCount * 2`.
- `krAnnotationCount >= boxSeriesCount` when slope/correlation text is planned.
- `alternatingBandCount` is present when gridlines are intentionally disabled.
