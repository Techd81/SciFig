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
| `computer_ai_ml` | model, algorithm, layer, module, source/target topology, epoch, train/test split, loss, validation loss, accuracy, R2/RMSE/MAE/AUC/F1, SHAP, feature importance, residuals | `model_architecture_board`, `model_architecture`, `training_curve`, `grouped_bar`, `scatter_regression`, `residual_vs_fitted`, `line`, `lollipop_horizontal` | `dotplot`, `heatmap_annotated`, `roc`, `pr_curve`, `calibration`, `confusion_matrix` | Architecture topology, architecture metric storyboards, training dynamics, cross-validation summaries, residual diagnostics, ROC/PR, calibration |
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

### Computer / AI / Machine Learning

- Hero: `grouped_bar` model benchmark when model and train/test metric columns are present
- Hero: `model_architecture_board` when source-target or module architecture fields also include latency, FLOPs, memory, throughput, cost, edge_weight, or parameter metrics
- Hero: `model_architecture` when layer/module/component or source-target architecture fields are present without enough metric columns for a board
- Hero: `classifier_validation_board` when score/probability plus label or threshold fields are present
- Hero: `training_curve` when epoch/step plus loss, validation loss, accuracy, or learning-rate columns are present
- Support: `scatter_regression` predicted-vs-actual parity panel
- Support: `residual_vs_fitted` or `line` for residuals, cross-validation, or feature-count curves
- Explainability: `lollipop_horizontal`, `dotplot`, or `heatmap_annotated` for importance / SHAP fields
- Classifier errors: `classifier_validation_board` first, then `confusion_matrix` when only true/predicted labels are present
- Rule: if RF/Random Forest/RFR appears and schema is compatible, use the RF template anchors before generic prediction charts

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
- ML model comparison -> `ml_model_performance_10`; keep RF cyan, XGBoost coral, LightGBM teal, train pale orange, test pale blue, residual zero deep red

## Domain Guardrails

1. Do not use a genomics heatmap palette for survival curves.
2. Do not reuse treatment colors for control categories in support panels.
3. In clinical panels, prioritize readability and model interpretability over decorative density.
4. In single-cell and spatial figures, ensure category colors stay stable between embedding, abundance, and expression support panels.
5. In AI/ML figures, do not collapse model benchmarks into generic grouped bars when a template-backed RF/model diagnostic package matches the schema.
