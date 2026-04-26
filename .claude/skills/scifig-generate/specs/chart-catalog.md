# Chart Catalog

Expanded chart taxonomy for `scifig-generate`. Use this as the lookup table during Phase 2.

**Status**: ✅ = implemented (66), ⬜ = registered but not yet implemented (49)

## Core Quantitative Charts

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `violin+strip` | ✅ | grouped numeric values, moderate n | Distribution-aware group comparison |
| `box+strip` | ✅ | grouped numeric values, larger n | Robust summary plus points |
| `raincloud` | ✅ | grouped numeric values, enough obs | Publication-grade density + points + box |
| `beeswarm` | ✅ | grouped numeric values, low/moderate n | Exact point placement |
| `paired_lines` | ✅ | subject ID + before/after | Paired response visualization |
| `dumbbell` | ✅ | two values per subject/group | Before/after delta |
| `line` | ⬜ | ordered time or dose axis | Mean/median trend |
| `line_ci` | ✅ | ordered axis + CI/SE | Trajectory with uncertainty band |
| `spaghetti` | ✅ | repeated subject trajectories | Individual longitudinal traces |
| `ridge` | ✅ | many related distributions | Cohort density landscape |

## Omics / High-dimensional Charts

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `heatmap+cluster` | ✅ | matrix-like feature x sample | Structured abundance map |
| `heatmap_pure` | ✅ | matrix, no clustering | Ordered matrix with annotation |
| `volcano` | ✅ | fold-change + p-value | Differential analysis overview |
| `ma_plot` | ⬜ | mean abundance + fold-change | Differential expression with intensity |
| `pca` | ✅ | PC columns or reducible matrix | Global structure |
| `umap` | ✅ | UMAP columns or embedding | Single-cell / manifold embedding |
| `tsne` | ⬜ | tSNE columns | Nonlinear embedding |
| `enrichment_dotplot` | ✅ | pathway terms + score + p-value | Pathway/GSEA summary |
| `oncoprint` | ⬜ | mutation matrix | Cancer genomics summary |
| `lollipop_mutation` | ⬜ | AA position + mutation freq | Mutation landscape |
| `manhattan` | ⬜ | chr + position + p-value | GWAS association scan |
| `qq` | ⬜ | p-value only | Association calibration |
| `correlation` | ✅ | pairwise associations matrix | Feature association overview |

## Clinical / Modeling Charts

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `km` | ✅ | survival time + event + group | Time-to-event outcome |
| `forest` | ✅ | effect estimate + CI bounds | Multivariable/subgroup effects |
| `roc` | ✅ | score + binary label | Classifier discrimination |
| `pr_curve` | ✅ | score + binary label (imbalanced) | Precision-recall assessment |
| `calibration` | ✅ | predicted risk + observed outcome | Calibration of risk models |
| `waterfall` | ✅ | ordered patient/response values | Heterogeneous response summary |
| `stacked_bar_comp` | ⬜ | compositional outcome by group | Cohort composition |

## Pharmacology / Mechanistic Charts

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `dose_response` | ✅ | dose/concentration + response | Potency/efficacy curves |
| `scatter_regression` | ✅ | x/y continuous variables | Correlation / regression evidence |

## Distribution Variants

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `violin_paired` | ✅ | paired data, two conditions | Paired violin comparison |
| `violin_split` | ✅ | two grouping factors | Split violin halves |
| `dot_strip` | ✅ | individual observations | Dot strip plot |
| `histogram` | ✅ | single continuous variable | Frequency distribution |
| `density` | ✅ | continuous variable, groups | Smooth density overlay |
| `ecdf` | ✅ | continuous variable | Cumulative distribution |
| `joyplot` | ✅ | many overlapping distributions | Ridge density plot |

## Time Series Variants

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `sparkline` | ⬜ | compact time series | Minimal trend indicator |
| `area` | ⬜ | time series with fill | Filled area trend |
| `area_stacked` | ⬜ | compositional time series | Stacked area |
| `streamgraph` | ⬜ | flowing compositional data | Streamgraph |
| `gantt` | ⬜ | project timeline | Gantt chart |
| `timeline_annotation` | ⬜ | annotated time points | Timeline with events |

## Statistical / Diagnostic Charts

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `residual_vs_fitted` | ✅ | regression diagnostics | Residual pattern check |
| `scale_location` | ✅ | regression diagnostics | Homoscedasticity check |
| `pp_plot` | ✅ | distribution fit | P-P plot |
| `bland_altman` | ✅ | method comparison | Agreement assessment |
| `funnel_plot` | ✅ | meta-analysis | Publication bias check |
| `pareto_chart` | ✅ | categorical frequency | Pareto analysis |
| `control_chart` | ✅ | process monitoring | SPC control chart |
| `box_paired` | ✅ | paired data | Paired box comparison |
| `mean_diff_plot` | ✅ | paired differences | Mean difference CI |
| `ci_plot` | ✅ | effect estimates + CI | Confidence interval plot |
| `cook_distance` | ✅ | regression diagnostics | Influential points |
| `leverage_plot` | ✅ | regression diagnostics | Leverage detection |

## Matrix / Heatmap Variants

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `dotplot` | ⬜ | matrix with dot encoding | Dot matrix |
| `adjacency_matrix` | ⬜ | network adjacency | Graph structure |
| `heatmap_annotated` | ⬜ | matrix with values | Annotated heatmap |
| `heatmap_triangular` | ⬜ | symmetric matrix | Triangular heatmap |
| `heatmap_mirrored` | ⬜ | symmetric matrix | Mirrored heatmap |
| `cooccurrence_matrix` | ⬜ | co-occurrence data | Co-occurrence heatmap |

## Genomics Extended

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `circos_karyotype` | ✅ | chromosome data | Circos plot |
| `gene_structure` | ✅ | gene/exon coordinates | Gene model |
| `pathway_map` | ✅ | pathway topology | Pathway diagram |
| `kegg_bar` | ✅ | KEGG enrichment | KEGG bar chart |
| `go_treemap` | ⬜ | GO enrichment | GO treemap |
| `chromosome_coverage` | ⬜ | chromosome-wide signal | Coverage plot |

## Clinical Extended

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `swimmer_plot` | ✅ | patient timeline | Swimmer plot |
| `risk_ratio_plot` | ✅ | risk ratios + CI | Risk forest plot |
| `caterpillar_plot` | ⬜ | ranked effects | Caterpillar plot |
| `tornado_chart` | ⬜ | sensitivity analysis | Tornado diagram |
| `nomogram` | ⬜ | prediction model | Nomogram |
| `decision_curve` | ⬜ | net benefit analysis | DCA plot |

## Composition / Hierarchical

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `treemap` | ✅ | hierarchical proportions | Treemap |
| `sunburst` | ✅ | hierarchical proportions | Sunburst chart |
| `waffle_chart` | ⬜ | proportional counts | Waffle chart |
| `marimekko` | ⬜ | variable-width stacked | Marimekko chart |
| `stacked_area_comp` | ⬜ | compositional time series | Stacked area composition |
| `nested_donut` | ⬜ | nested proportions | Nested donut |

## Relationship / Network

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `chord_diagram` | ⬜ | flow between categories | Chord diagram |
| `parallel_coordinates` | ⬜ | multivariate profiles | Parallel coordinates |
| `sankey` | ✅ | flow between stages | Sankey diagram |
| `radar` | ✅ | multi-attribute comparison | Radar/spider chart |

## Engineering / Materials

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `stress_strain` | ✅ | stress + strain data | Stress-strain curve |
| `phase_diagram` | ⬜ | composition + temperature | Phase diagram |
| `nyquist_plot` | ⬜ | impedance data | Nyquist plot |
| `xrd_pattern` | ✅ | 2theta + intensity | XRD diffractogram |
| `ftir_spectrum` | ⬜ | wavenumber + absorbance | FTIR spectrum |
| `dsc_thermogram` | ⬜ | temperature + heat flow | DSC curve |

## Ecology / Environmental

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `species_abundance` | ✅ | species + abundance | Abundance bar/dot |
| `shannon_diversity` | ✅ | diversity index by group | Diversity comparison |
| `ordination_plot` | ✅ | NMDS/PCoA coordinates | Ordination scatter |
| `biodiversity_radar` | ✅ | multiple diversity indices | Biodiversity radar |

## Psychology / Social Science

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `likert_divergent` | ✅ | Likert scale responses | Divergent stacked bar |
| `likert_stacked` | ✅ | Likert scale responses | Stacked bar |
| `mediation_path` | ⬜ | mediation analysis | Path diagram |
| `interaction_plot` | ⬜ | factorial design | Interaction plot |

## Additional Variants

| Chart | Status | Typical triggers | Best use |
|-------|--------|------------------|----------|
| `bubble_scatter` | ✅ | x/y + size variable | Bubble chart |
| `connected_scatter` | ✅ | x/y trajectory | Connected scatter |
| `stem_plot` | ⬜ | discrete signal | Stem plot |
| `lollipop_horizontal` | ⬜ | ranked values | Horizontal lollipop |
| `slope_chart` | ⬜ | before/after ranking | Slope chart |
| `bump_chart` | ⬜ | ranking over time | Bump chart |
| `mosaic_plot` | ⬜ | categorical association | Mosaic plot |
| `clustered_bar` | ✅ | grouped categories | Clustered bar |
| `diverging_bar` | ⬜ | diverging values | Diverging bar |
| `grouped_bar` | ✅ | grouped categories | Grouped bar |
| `heatmap_symmetric` | ⬜ | symmetric matrix | Symmetric heatmap |
| `violin_grouped` | ⬜ | multiple groups | Grouped violin |

## Selection Heuristics

1. If the data support a field-standard chart, prefer it over a generic chart.
2. Only recommend charts with ✅ status (implemented). Use fallback mapping for ⬜ charts.
3. If the same story can be told with fewer marks, prefer the lower-ink chart.
4. Use exploratory charts as support panels and inferential charts as hero/validation panels.
5. If a requested chart is visually fashionable but statistically weak, recommend a safer alternative.

## Fallback Mapping

When a chart is registered but not implemented, use these fallbacks:

| Unimplemented | Fallback |
|---------------|----------|
| `manhattan` | `volcano` |
| `qq` | `pp_plot` |
| `tsne` | `umap` |
| `ma_plot` | `volcano` |
| `spatial_feature` | `umap` |
| `oncoprint` | `heatmap_pure` |
| `lollipop_mutation` | `scatter_regression` |
| `alluvial` | `sankey` |
| `ridgeline` | `ridge` |
| `stacked_bar_comp` | `clustered_bar` |
| `composition_dotplot` | `bubble_scatter` |
