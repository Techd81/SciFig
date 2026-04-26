# Domain Playbooks

Domain playbooks bias charting, statistics, panel stories, and color semantics.

## Domains

| Domain | Typical cues | Preferred charts | Common support panels | Typical stats |
|--------|--------------|------------------|-----------------------|---------------|
| `general_biomedical` | grouped values, time-course, simple comparisons | `violin+strip`, `box+strip`, `line_ci`, `paired_lines` | `beeswarm`, `dumbbell`, `correlation` | Welch, Mann-Whitney, ANOVA, Kruskal |
| `genomics_transcriptomics` | `log2fc`, `padj`, `gene`, `chr`, `pos` | `volcano`, `heatmap+cluster`, `ma_plot`, `manhattan`, `qq` | `enrichment_dotplot`, `pca`, `oncoprint` | FDR-aware testing, enrichment summaries |
| `single_cell_spatial` | `umap`, `tsne`, `cell_type`, `x`, `y`, `cluster` | `umap`, `spatial_feature`, `composition_dotplot` | `violin+strip`, `heatmap_pure`, `enrichment_dotplot` | Mixed descriptive + group comparison |
| `proteomics_metabolomics` | abundance matrix, pathways, feature IDs | `heatmap+cluster`, `pca`, `volcano` | `enrichment_dotplot`, `correlation`, `line_ci` | FDR-aware differential analysis |
| `pharmacology_toxicology` | dose, concentration, response, EC50-like patterns | `dose_response`, `waterfall`, `paired_lines` | `violin+strip`, `forest`, `line_ci` | Curve fitting, paired tests, ANOVA |
| `immunology_cell_biology` | group, marker, condition, stimulation, replicate | `raincloud`, `beeswarm`, `line_ci` | `paired_lines`, `heatmap_pure`, `composition_dotplot` | Welch, paired tests, repeated-measures variants |
| `neuroscience_behavior` | time bins, trials, subject IDs, stimulus levels | `line_ci`, `spaghetti`, `paired_lines` | `beeswarm`, `ridgeline`, `scatter_regression` | Mixed or paired comparisons, correlations |
| `clinical_diagnostics_survival` | survival time, event, risk score, cohort | `km`, `forest`, `roc`, `pr_curve`, `calibration` | `waterfall`, `box+strip` | Log-rank, Cox, AUC/CI, calibration |
| `epidemiology_public_health` | cohorts, strata, incidence, risk ratios | `forest`, `line_ci`, `scatter_regression`, `stacked_bar_comp` | `correlation`, `calibration` | Regression, trend analysis, effect estimates |
| `materials_engineering` | stress, strain, phase, composition, process params | `stress_strain`, `phase_diagram`, `scatter_regression`, `line_ci` | `heatmap_pure`, `correlation`, `box+strip` | ANOVA, regression, curve fitting |
| `ecology_environmental` | species, abundance, coordinates, time, diversity indices | `species_abundance`, `shannon_diversity`, `ordination_plot`, `biodiversity_radar` | `heatmap_pure`, `scatter_regression`, `line_ci` | Diversity indices, PERMANOVA, trend analysis |
| `agriculture_food_science` | yield, treatment, plot, sensory score, growth time | `violin+strip`, `line_ci`, `spaghetti`, `dotplot` | `box+strip`, `correlation`, `stacked_bar_comp` | ANOVA, Dunnett's test, growth curves |
| `psychology_social_science` | Likert scores, before/after, condition, subject ID | `likert_divergent`, `likert_stacked`, `paired_lines`, `mediation_path` | `violin+strip`, `bar+dot`, `interaction_plot` | Paired tests, repeated measures, mediation analysis |

## Panel Story Defaults

### Genomics / Transcriptomics

- Hero: `volcano` or `heatmap+cluster`
- Support: `enrichment_dotplot`
- Support: `pca`
- Validation: `violin+strip` for sentinel genes or pathways

### Single-cell / Spatial

- Hero: `umap` or `spatial_feature`
- Support: `composition_dotplot`
- Support: `heatmap_pure`
- Validation: `violin+strip` or `paired_lines`

### Clinical / Survival

- Hero: `km`
- Support: `forest`
- Support: `roc` or `pr_curve`
- Validation: `calibration` or cohort distribution panel

### Pharmacology

- Hero: `dose_response`
- Support: `waterfall`
- Support: `paired_lines`
- Validation: `violin+strip` or `forest`

## Domain Color Semantics

- Control / baseline -> neutral blue or slate
- Treatment / perturbation -> warm accent
- Rescue / combination -> green-teal accent, not red-green opposition
- Risk gradient -> sequential neutral-to-accent scale
- Up / down regulation -> diverging palette centered at zero
- Cell types / many categories -> muted categorical palette with stable mapping

## Domain Guardrails

1. Do not use a genomics heatmap palette for survival curves.
2. Do not reuse treatment colors for control categories in support panels.
3. In clinical panels, prioritize readability and model interpretability over decorative density.
4. In single-cell and spatial figures, ensure category colors stay stable between embedding, abundance, and expression support panels.
