# Template Distillation Contract

This contract governs how `template/articles` examples become executable `scifig-generate` behavior.

## Promotion Rules

1. Promote code before prose. If an article contains reusable Matplotlib logic, move the behavior into helper or generator source instead of expanding prompt text.
2. Do not register a chart key until `registry.py`, chart catalog, generator implementation, recommendation logic, and tests are all updated.
3. Motifs are overlays or layout intents, not chart keys. They belong in `specs/template-visual-motifs.md`, Phase 2 `visualContentPlan`, and helper counters.
4. Layout recipes must reserve physical space for sidecars, legends, colorbars, risk tables, and annotations. Negative axes text is forbidden unless a real slot exists.
5. Every promoted visual effect must expose a QA signal: a counter, `gid`, render metadata field, or testable artifact.
6. Article code may be normalized to print-scale typography and current legend/layout contracts. Do not copy poster-scale font sizes, outside-right legends, or `loc="best"`.

## Classification

| Class | Destination | Required Validation |
|-------|-------------|---------------------|
| `motif` | `specs/template-visual-motifs.md` + Phase 2 motif inference | motif counter and Phase 4 hard gate when planned |
| `layout` | `templates/panel-layout-recipes.md` or `template-mining/04-grid-recipes.md` | no cross-panel overlap; reserved slots for outside elements |
| `helper` | `phases/code-gen/helpers.py` or `template_mining_helpers.py` | targeted unit/render test plus QA metadata |
| `generator` | split generator file + `registry.py` + chart catalog | registry completeness test and smoke/render test |
| `policy` | `specs/workflow-policies.md` + Phase 4 | failing output blocks completion |

## High-Value Article Patterns

- Joint scatter plus top/right marginal KDE or histogram sidecars using reserved figure space.
- Polygon radar grids with layered "glass" markers and non-zero radial emphasis.
- Triangular correlation heatmaps with mask discipline, significance stars, and compact colorbar slots.
- SHAP beeswarm plus aligned importance bar/pie sidecars.
- Gradient or layered distribution plots that combine raw samples, quantiles, and summary markers.
- Dense prediction diagnostics with metric tables, perfect-fit references, density encoding, and train/test sample styling.

## Non-Negotiables

- Keep legend finalization in `enforce_figure_legend_contract(...)`.
- Keep layout finalization in `audit_figure_layout_contract(...)`.
- Never invent statistics for visual impact.
- Prefer one strong article-derived motif plus one support motif over many weak decorations.
- Keep all generated output source-data friendly and reproducible.
