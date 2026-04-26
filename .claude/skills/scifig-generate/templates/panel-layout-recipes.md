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
- Legend: treat as a figure-level layout element, never as a panel annotation. If panels share group, color, marker, or line semantics, keep one shared legend outside every plotting area. Prefer bottom-center, then top-center, then outside-right.
- Legend collision policy: never use `loc="best"` or any in-axes legend for publication output. If space is tight, adjust legend columns, shorten labels, reduce handle/text spacing, increase figure margins, or reflow panels before allowing the legend to overlap curves, bars, points, error bars, confidence intervals, grids, or heatmap cells.

## Shared Legend Pattern

```python
# After all panels are drawn, remove panel legends and create one shared
# figure-level legend outside the plotting regions.
handles, labels = ax_a.get_legend_handles_labels()
for ax in [ax_a, ax_b, ax_c, ax_d]:
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()
fig.subplots_adjust(bottom=0.22)
fig.legend(handles, labels, loc="lower center", ncol=min(len(labels), 4),
           frameon=False, fontsize=5, bbox_to_anchor=(0.5, 0.02))
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

1. Share legends whenever the same categorical mapping appears in multiple panels, and keep them outside the data region.
2. Share colorbars for the same continuous encoding.
3. Align axes only when the encoded variable is the same.
4. Prefer one hero panel over four equal-priority panels.
5. Use panel labels at the same anchor point and size across the figure.
6. Keep whitespace intentional; do not fill every slot if the story only needs three panels.
