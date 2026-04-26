# Chart Catalog

Expanded chart taxonomy for `scifig-generate`. Use this as the lookup table during Phase 2.

## Core Quantitative Charts

| Chart | Typical triggers | Best use | Notes |
|-------|------------------|----------|-------|
| `violin+strip` | grouped numeric values, moderate sample size | Distribution-aware group comparison | Default for 2-6 groups when showing individual points is feasible |
| `box+strip` | grouped numeric values, larger sample size | Robust summary plus points | Use when distributions are dense |
| `raincloud` | grouped numeric values with enough observations | Publication-grade density + points + box summary | Strong choice for Cell-like and review-style figures |
| `beeswarm` | grouped numeric values, low/moderate n | Exact point placement | Good for immunology and cell biology validation panels |
| `paired_lines` | subject ID plus before/after or matched conditions | Paired response visualization | Prefer over bars for matched designs |
| `dumbbell` | two values per subject/group | Before/after or treatment delta | Works well for clinical or pharmacology summary panels |
| `line` | ordered time or dose axis | Mean or median trend | Use with explicit summary choice |
| `line_ci` | ordered axis plus CI columns or repeated estimates | Trajectory with uncertainty band | Strong default for longitudinal or model estimates |
| `spaghetti` | repeated subject-level trajectories | Individual longitudinal traces | Overlay with summary only when not overcrowded |
| `ridgeline` | many related distributions | Cohort or time distribution landscape | Useful in omics or epidemiology density summaries |

## Omics / High-dimensional Charts

| Chart | Typical triggers | Best use | Notes |
|-------|------------------|----------|-------|
| `heatmap+cluster` | matrix-like feature x sample table | Structured abundance/expression map | Default for moderate-size matrices |
| `heatmap_pure` | matrix-like table, clustering not desired | Ordered matrix with explicit annotation | Better when row/column order matters |
| `volcano` | fold-change + p-value | Differential analysis overview | Add threshold lines and optional labels |
| `ma_plot` | mean abundance + fold-change | Differential expression with intensity context | Pair naturally with volcano or heatmap |
| `pca` | PC columns or reducible matrix | Global structure | Label explained variance when available |
| `umap` | UMAP columns or embedding request | Single-cell or manifold embedding | Pair with abundance or marker-expression panels |
| `tsne` | tSNE columns or embedding request | Nonlinear embedding | Use sparingly; document parameters |
| `enrichment_dotplot` | pathway terms + score + adjusted p-value | Pathway/GSEA summary | Dot size can encode gene ratio or set size |
| `oncoprint` | mutation matrix / gene x sample events | Cancer genomics summary | Often hero panel in genomics storyboards |
| `lollipop_mutation` | amino-acid position + mutation frequency | Mutation landscape | Useful with oncoprint or domain map |
| `manhattan` | chromosome + position + p-value | GWAS association scan | Use alternating chromosome colors |
| `qq` | p-value only | Association calibration | Pair with Manhattan in genetics |
| `correlation` | matrix of pairwise associations | Feature association overview | Keep labels sparse and ordering meaningful |

## Clinical / Modeling Charts

| Chart | Typical triggers | Best use | Notes |
|-------|------------------|----------|-------|
| `km` | survival time + event + group | Time-to-event outcome | Consider at-risk table when space allows |
| `forest` | effect estimate + CI bounds | Multivariable or subgroup effects | Common support panel beside KM or ROC |
| `roc` | score/probability + binary label | Classifier discrimination | Include AUC and confidence interval when available |
| `pr_curve` | score + binary label with class imbalance | Precision-recall assessment | Prefer when positives are rare |
| `calibration` | predicted risk + observed outcome | Calibration of risk models | Natural pair with ROC/PR |
| `waterfall` | ordered patient/response values | Heterogeneous response summary | Common in oncology and pharmacology |
| `stacked_bar_comp` | compositional outcome by group | Cohort composition | Use only when composition is the real variable |

## Pharmacology / Mechanistic Charts

| Chart | Typical triggers | Best use | Notes |
|-------|------------------|----------|-------|
| `dose_response` | dose/concentration + response | Potency/efficacy curves | Fit 4PL if appropriate and report EC50/IC50 |
| `paired_lines` | matched pretreatment/post-treatment | Within-subject response | Prefer when samples are paired |
| `scatter_regression` | x/y continuous mechanistic variables | Correlation or regression evidence | Distinguish fit from summary |

## Advanced Domain-specific Charts

| Chart | Typical triggers | Best use | Notes |
|-------|------------------|----------|-------|
| `spatial_feature` | x/y coordinates plus expression or cell-state signal | Spatial omics hero/support panel | Combine with UMAP or abundance panels |
| `composition_dotplot` | category abundances across groups | Cell-type or class composition | Better than stacked bars when many categories exist |
| `alluvial` | state transitions between stages | Flow between categories | Use cautiously; easy to overload |

## Selection Heuristics

1. If the data support a field-standard chart, prefer it over a generic chart.
2. If the same story can be told with fewer marks, prefer the lower-ink chart.
3. Use exploratory charts as support panels and inferential charts as hero/validation panels where appropriate.
4. If a requested chart is visually fashionable but statistically weak for the data structure, recommend a safer alternative and explain the substitution.
