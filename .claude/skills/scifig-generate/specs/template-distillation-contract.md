# Template Distillation Contract

This contract governs how `template/articles` examples become executable `scifig-generate` behavior.

## Promotion Rules

1. Promote code before prose. If an article contains reusable Matplotlib logic, move the behavior into helper or generator source instead of expanding prompt text.
2. Do not register a chart key until `registry.py`, chart catalog, generator implementation, recommendation logic, and tests are all updated.
3. Motifs are overlays or layout intents, not chart keys. They belong in `specs/template-visual-motifs.md`, Phase 2 `visualContentPlan`, and helper counters.
4. Layout recipes must reserve physical space for sidecars, legends, colorbars, risk tables, and annotations. Negative axes text is forbidden unless a real slot exists.
5. Every promoted visual effect must expose a QA signal: a counter, `gid`, render metadata field, or testable artifact.
6. Article code may be normalized to print-scale typography and current legend/layout contracts. Do not copy poster-scale font sizes, outside-right legends, or `loc="best"`.
7. Autonomous distillation cycles must leave generated smoke artifacts under the ignored output root, then commit only tracked skill/package changes after validation.
8. Autonomous smoke validation must read runtime evidence, not planned defaults. Every saved figure must produce or be represented in `output/reports/render_contracts.json`, and the cycle report must fail missing runtime contract reports.
9. Template alignment is exact. If Phase 2 plans template or reference motifs, validation must compare planned motifs with applied motifs and report the exact missing motif names.
10. Template routing is metadata-backed. When `case-index.json` contains cases for a selected family, the cycle report must show the case-index matches and anchors used before static fallback anchors are accepted.

## Classification

| Class | Destination | Required Validation |
|-------|-------------|---------------------|
| `motif` | `specs/template-visual-motifs.md` + Phase 2 motif inference | exact planned-vs-applied motif coverage plus Phase 4 hard gate |
| `layout` | `templates/panel-layout-recipes.md` or `template-mining/04-grid-recipes.md` | no cross-panel overlap; reserved slots for outside elements; runtime contract report persisted |
| `helper` | `phases/code-gen/helpers.py` or `template_mining_helpers.py` | targeted unit/render test plus runtime QA metadata |
| `generator` | split generator file + `registry.py` + chart catalog | registry completeness test and smoke/render test |
| `policy` | `specs/workflow-policies.md` + Phase 4 | failing output blocks completion via runtime `render_contracts.json` evidence |

## High-Value Article Patterns

- Joint scatter plus top/right marginal KDE or histogram sidecars using reserved figure space.
- Polygon radar grids with layered "glass" markers and non-zero radial emphasis.
- Triangular correlation heatmaps with mask discipline, significance stars, and compact colorbar slots.
- SHAP beeswarm plus aligned importance bar/pie sidecars.
- Gradient or layered distribution plots that combine raw samples, quantiles, and summary markers.
- Dense prediction diagnostics with metric tables, perfect-fit references, density encoding, and train/test sample styling.

## Non-Negotiables

- Keep legend finalization in `enforce_figure_legend_contract(...)`.
- Persist legend/layout runtime evidence through `render_contracts.json`; do not infer pass/fail from `chartPlan` defaults.
- Keep layout finalization in `audit_figure_layout_contract(...)`.
- Keep density finalization in `audit_visual_density_contract(...)` whenever template or reference motifs are planned.
- Never invent statistics for visual impact.
- Prefer one strong article-derived motif plus one support motif over many weak decorations.
- Keep all generated output source-data friendly and reproducible.
- In each autonomous cycle, compare the new smoke bundle against the previous cycle and promote at least one reusable lesson before the next commit.
