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
- Legend: treat as a figure-level layout element, never as a panel annotation. If panels share group, color, marker, or line semantics, keep one shared legend outside every plotting area. Final composite figures may use bottom-center or top-center only; outside-right and in-axes legends are forbidden.
- Legend collision policy: never use `loc="best"` or any in-axes legend for publication output. If space is tight, adjust legend columns, shorten labels, reduce handle/text spacing, increase figure margins, or reflow panels before allowing the legend to overlap curves, bars, points, error bars, confidence intervals, grids, or heatmap cells.

## Layout Scoring

Before code generation, score candidate layouts:

```python
layout_score = (
    panel_count * 2 +
    legend_burden * 3 +
    long_label_burden * 2 +
    colorbar_burden * 2 +
    aspect_ratio_mismatch * 2 -
    story_fit * 4
)
```

Choose the lowest score that still tells the scientific story. Dropping a weak support panel is preferred over shrinking four panels into unreadable output. Cell-like figures should bias toward `hero_plus_stacked_support` when one panel carries the main claim.

## Visual Impact Recipes

- **Hero contrast**: make panel A visually dominant through canvas share, not oversized title text.
- **Evidence ladder**: pair each eye-catching highlight with a support panel or source-data table.
- **Inset discipline**: use insets for distributions, residuals, or local detail only when they are data-derived and remain outside the main data marks.
- **Metric boxes**: place compact summaries outside axes; Phase 4 must fail if they overlap the plotted region.
- **Semantic restraint**: reserve high-saturation accents for the key condition, event, or feature; keep context marks muted.

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
           frameon=True, fancybox=False, framealpha=0.96,
           edgecolor="#222222", facecolor="#FFFFFF",
           fontsize=5, bbox_to_anchor=(0.5, 0.02))
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

## Recipe 6: Triple Horizontal

**When to use**
- Three wide-aspect panels side-by-side (e.g. time-course, dose-response, multi-condition)

**Layout**
- `1 x 3`
- A = primary, B = secondary, C = validation

**Typical pairings**
- `line+ci` + `bar_grouped` + `scatter`
- `dose_response` + `dose_response` + `dose_response`

## Recipe 7: Triple Vertical

**When to use**
- Three tall/narrow panels stacked vertically (e.g. multi-gene expression, multi-cohort)

**Layout**
- `3 x 1`
- A = primary, B = secondary, C = validation

**Typical pairings**
- `violin+strip` + `violin+strip` + `violin+strip`
- `box_grouped` + `box_grouped` + `box_grouped`

## Recipe 8: Stacked Pair

**When to use**
- Two vertically-stacked panels (e.g. before/after, upstream/downstream)

**Layout**
- `2 x 1`
- A = primary, B = comparison

**Typical pairings**
- `scatter` + `residual`
- `km` + `risk_table`

## Recipe 9: 2x3 Discovery Board

**When to use**
- Six conditions, time-points, or genes in a compact grid

**Layout**
- `2 x 3`
- A-F mapped left-to-right, top-to-bottom

**Typical pairings**
- Six `violin+strip` panels
- Six `heatmap_pure` panels

## Recipe 10: 3x3 Large Board

**When to use**
- Nine conditions, multi-gene, or multi-omics summary

**Layout**
- `3 x 3`
- A-I mapped left-to-right, top-to-bottom

## Recipe 11: Hero + Triple Support

**When to use**
- One dominant panel with three narrow supporting panels

**Layout**
- `3 x 2` — A spans all 3 rows on the left; B, C, D stacked on the right

**Typical pairings**
- `manhattan` + `qq` + `forest` + `enrichment_dotplot`
- `volcano` + `heatmap_pure` + `violin+strip` + `pca`

## Recipe 12: Asymmetric L

**When to use**
- One wide top panel with two narrow bottom panels

**Layout**
- `2 x 2` — A spans both columns in row 0; B and C in row 1

**Typical pairings**
- `line+ci` + `bar_grouped` + `scatter`
- `km` + `forest` + `roc`

## Recipe 13: Prediction Diagnostic Matrix

**When to use**
- Data contain observed/actual and predicted/fitted values, model split, sample/source, residual, or error columns.

**Layout**
- `2 x 2`
- A = prediction scatter with perfect-fit line, density coloring, marginal distributions, and metric table
- B = residual or error distribution
- C = Bland-Altman or residual-vs-fitted support
- D = new-point/error sidecar or sample/source summary

**Required layout metadata**
- `templateLayoutIntents` includes `prediction_diagnostic_matrix` and `joint_marginal_grid`
- `subAxesRequired=true`
- `axisLinkGroups` links panels that share actual/predicted scale
- legends, metric tables, and marginal axes stay outside plotted data marks

## Recipe 14: ML Explainability Board

**When to use**
- Data contain feature importance, SHAP-like values, ALE/PDP outputs, H-statistic, model, or feature-value columns.

**Layout**
- `2 x 2`
- A = ranked importance lollipop/bar using signed zero reference when values can be negative
- B = feature-value or dependence support heatmap/dotplot
- C = model or cohort comparison
- D = compact table/cutoff/cluster summary when supplied

**Rules**
- Do not invent SHAP, PDP, ALE, clustering, or cutoffs.
- If only generic feature importance exists, use `lollipop_horizontal`, `dotplot`, or `heatmap_annotated`; do not request an unimplemented SHAP chart key.

## Recipe 15: Evidence Strip With Marginal Support

**When to use**
- One hero panel needs small distribution, residual, or interval context without overfilling a board.

**Layout**
- A wide hero plus a narrow bottom or right strip
- Support axes use small multiples, marginal histograms, or interval bands
- Colorbars and legends reserve dedicated strip/slot space outside panel data

## Recipe 16: Correlation Evidence Matrix

**When to use**
- Matrix, correlation, p-value, adjacency, co-occurrence, or bubble-matrix data.

**Layout**
- Main matrix axis with a reserved right colorbar slot
- Optional upper/lower triangular mask, stars only from supplied p-values, small cell labels only for compact matrices
- Any dendrogram or clustering sidecar must come from supplied linkage/order data

## Composition Rules

1. Share legends whenever the same categorical mapping appears in multiple panels, and keep them outside the data region.
2. Share colorbars for the same continuous encoding.
3. Align axes only when the encoded variable is the same.
4. Prefer one hero panel over four equal-priority panels.
5. Use panel labels at the same anchor point and size across the figure.
6. Keep whitespace intentional; do not fill every slot if the story only needs three panels.
7. Use `subAxesRequired`, `colorbarSlotRequired`, and `layoutIntents` when a template motif needs marginal axes, shared colorbars, or linked diagnostic axes.
8. A template-derived motif is an overlay/layout intent, not a new generator key; keep chart keys limited to implemented registry entries.
