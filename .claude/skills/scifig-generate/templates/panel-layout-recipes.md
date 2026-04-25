# Panel Layout Recipes

Reusable layout blueprints for multi-panel scientific figures.

## Recipe 1: Comparison Pair

**When to use**
- One primary quantitative claim plus one support or validation panel

**Layout**
- `1 x 2`
- Left = hero
- Right = validation or support

**Typical pairings**
- `violin+strip` + `paired_lines`
- `km` + `forest`
- `volcano` + `enrichment_dotplot`

## Recipe 2: 2x2 Story Board

**When to use**
- Discovery + mechanism + validation + cohort/context

**Layout**
- `2 x 2`
- A = hero
- B = orthogonal support
- C = validation
- D = context / cohort / summary

**Typical pairings**
- `volcano`, `heatmap+cluster`, `enrichment_dotplot`, `pca`
- `umap`, `composition_dotplot`, `violin+strip`, `heatmap_pure`

## Recipe 3: Hero + Stacked Support

**When to use**
- One wide main panel needs two or three narrow supporting panels

**Layout**
- Wide left hero spanning two rows
- Right column stacked support panels

**Typical pairings**
- `manhattan` + `qq` + `forest`
- `spatial_feature` + `violin+strip` + `composition_dotplot`

## Recipe 4: Clinical Outcome Board

**When to use**
- Outcome, effect size, discrimination, and calibration in one figure

**Layout**
- `2 x 2`
- A = `km`
- B = `forest`
- C = `roc` or `pr_curve`
- D = `calibration`

## Recipe 5: Omics Discovery Board

**When to use**
- Differential signal plus structure plus pathway context

**Layout**
- `2 x 2`
- A = `volcano` or `ma_plot`
- B = `heatmap+cluster`
- C = `enrichment_dotplot`
- D = `pca` or `umap`

## Composition Rules

1. Share legends whenever the same categorical mapping appears in multiple panels.
2. Share colorbars for the same continuous encoding.
3. Align axes only when the encoded variable is the same.
4. Prefer one hero panel over four equal-priority panels.
5. Use panel labels at the same anchor point and size across the figure.
6. Keep whitespace intentional; do not fill every slot if the story only needs three panels.
