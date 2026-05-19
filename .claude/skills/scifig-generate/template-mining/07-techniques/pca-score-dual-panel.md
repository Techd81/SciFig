# PCA Score Dual Panel

Use this when a formulation or recipe table contains signed PCA component
scores and a weighted total score.

## Visual Grammar

- Use a 1x2 board: left panel for signed PC1-PC3 stacked component
  decomposition; right panel for total-score ranking.
- Maintain independent `bottom_pos` and `bottom_neg` arrays when stacking PC
  components. A single bottom array corrupts negative contributions by stacking
  them from the positive baseline.
- Draw the same zero baseline in both panels. It is the semantic anchor for
  positive and negative PCA contribution.
- Label bars with polarity-aware offsets: positive labels above the bar and
  negative labels below the bar. Rotated labels must not sit on the zero line.
- Keep the zorder sandwich fixed: grid `0`, bars `3`, zero line `4`, text `5`.
- The right total-score panel is the decision closure; it identifies the best
  and worst formulations after the left panel explains the component basis.

## Interpretation Boundary

PCA component scores are decomposition evidence, while total score is a weighted
ranking metric. The figure supports optimization explanation only when the
weighting rule is supplied or clearly declared.

## Runtime Boundary

Current `stacked_bar_comp` validates one generic stacked-composition channel.
It does not yet compose the signed PCA decomposition plus paired total-score
ranking board, dynamic positive/negative bottoms, shared zero lines, or
polarity-aware rotated labels.
