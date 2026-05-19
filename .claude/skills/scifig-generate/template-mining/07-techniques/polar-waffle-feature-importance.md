# Technique: Polar Waffle Feature Importance

Anchor case: `期刊配图：基于极坐标条形图与华夫饼图拆解机器学习特征重要性（附完整代码）_1778680326`.

Case-086 evidence lives in
`.workflow/case_studies/case_086_polar_waffle_feature_importance/comparison_report.json`.

## Learned Essence

This case is an asymmetric explainability board, not a generic radar chart.

1. Left panel is a polar bar chart for feature-level mean absolute SHAP values.
2. Right panel is a 10x10 waffle chart for group-level contribution shares.
3. Both panels must derive from the same feature-importance table and feature
   group mapping.
4. The polar axis hides the default polar spine and grid, then redraws custom
   concentric rings and radial guide lines.
5. Feature labels sit outside the polar bars and rotate by angle, with flipped
   alignment on the left half of the circle.
6. Waffle counts are rounded to 100 squares and the rounding difference is
   assigned back to the largest group.

## Layout Contract

Use an asymmetric `GridSpec(2, 2)`:

```python
fig = plt.figure(figsize=(16.5, 7.6), facecolor="white")
gs = GridSpec(
    2, 2,
    width_ratios=[1.18, 1.00],
    height_ratios=[1.00, 0.16],
    wspace=0.18,
    hspace=0.02,
)
ax_polar = fig.add_subplot(gs[:, 0], polar=True)
ax_waffle = fig.add_subplot(gs[0, 1])
ax_legend = fig.add_subplot(gs[1, 1])
```

The polar chart spans both rows on the left; the waffle chart occupies the
upper-right cell; the lower-right cell is reserved for the group legend.

## QA Contract

- `templateMotifCount` includes `polar_waffle_feature_importance`.
- `polarBarCount` equals the number of rendered feature rows.
- `waffleSquareCount == 100`.
- `groupCount` matches the feature-group mapping.
- `waffleRoundingSum == 100` after integer correction.
- `polygonPolarGrid` is true because the default polar grid must be replaced.
- `panelLabelCount >= 2`.
