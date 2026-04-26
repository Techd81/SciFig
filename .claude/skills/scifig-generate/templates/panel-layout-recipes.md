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

## Density & Spacing Rules

- `hspace=0.45` for 2-row layouts, `wspace=0.35` for 2-column layouts
- Panel labels (A/B/C/D) at `(-0.12, 1.05)` in axes coordinates, bold, 8pt
- Shared y-axis: align ticks across panels in same row
- Shared x-axis: align ticks across panels in same column
- Colorbar: `shrink=0.6`, positioned right of heatmap panels
- Legend: shared at figure level when panels encode same semantics

## Shared Legend Pattern

```python
# After all panels drawn, create shared legend
handles, labels = ax_a.get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=len(labels),
           frameon=False, fontsize=5, bbox_to_anchor=(0.5, 1.02))
```

## Shared Colorbar Pattern

```python
# After heatmap, extract mappable for colorbar
cbar = fig.colorbar(im, ax=[ax_a, ax_b], shrink=0.6, pad=0.02)
cbar.set_label("Value", fontsize=5)
```

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
