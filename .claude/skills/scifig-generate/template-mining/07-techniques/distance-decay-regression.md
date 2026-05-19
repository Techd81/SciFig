# Technique: Distance-Decay Regression

Use this when the prompt/data compares community similarity, beta diversity,
Bray-Curtis similarity, or other ecological similarity metrics against
geographic distance, especially when periods or treatments such as WDP/NWDP
must be compared by regression slope.

## Visual Contract

- Use `scatter_regression` as the chart key; do not add a separate registry key.
- Draw one single-panel scatter-regression figure unless the prompt asks for
  separate watersheds, taxa, basins, or treatments as facets.
- Encode periods/treatments with a stable two-color palette:
  WDP `#D62728`, NWDP `#1F77B4` when those labels are present.
- Keep dense pairwise-distance points at low alpha, around `0.15`, and no marker
  edge so the slope evidence remains dominant.
- Fit one linear trend per group; the slope contrast is the scientific claim.
- Add a matching translucent `fill_between` band around each group fit, alpha
  around `0.20`.
- Put `R^2` and `p` annotations inside the axes in group colors, away from the
  densest scatter region.
- Prune the legend to trend lines only when scatter points are visually noisy.
- Hide top/right spines and reserve enough right/top space for formula text.

## Runtime Boundary

The current public `scatter_regression` generator validates the base OLS
scatter + CI ribbon + statistics text. A dedicated distance-decay grouped branch
is still a gap: it should preserve separate group slopes, group-matched error
bands, and fit-only legend pruning.

## QA Contract

- `scatterPointCount > 0`
- `groupCount >= 2` when period/treatment groups are present
- `regressionLineCount == groupCount`
- `errorBandCount == groupCount`
- `annotationTextCount >= groupCount`
- `legendFitOnly == true` when scatter alpha is below `0.25`
- `exportDpi >= 600`

Evidence path:
