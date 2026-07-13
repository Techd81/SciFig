# Knowledge Base Loading Protocol

`knowledge/` is the canonical visual-grammar layer. **All Phase 2 narrative-arc / chart-family decisions and Phase 3 styling decisions must consult this knowledge base** instead of inventing patterns.

Full index: [knowledge/INDEX.md](../knowledge/INDEX.md)

## Loading Steps

1. **Always** load `knowledge/INDEX.md` before Phase 2/3 decisions.
2. **Phase 2** narrative + chart selection:
   - Read `knowledge/modules/06-narrative-arcs.md` to bind the figure to one of 10 corpus arcs.
   - Read `knowledge/modules/04-grid-recipes.md` if `panel_count > 1`.
   - Lookup `knowledge/case-index.json` for cases matching `chart_families` or `narrative_arc`.
   - For deeper evidence (`images`, `code_blocks`, `visual_signals`), read `knowledge/case-evidence.json` (regenerable via `knowledge/scripts/enrich.py`).
3. **Phase 3** code generation:
   - `knowledge/modules/01-rcparams-kernel.md` → `apply_journal_kernel(...)`
   - `knowledge/modules/02-zorder-recipes.md` → `apply_zorder_recipe(...)`
   - `knowledge/modules/03-palette-bank.md` → `resolve_palette(...)`, `role_color(...)`
   - `knowledge/modules/05-annotation-idioms.md` → metric boxes, panel labels, reference lines
   - `knowledge/techniques/<family>.md` only when the chart family has a deep-dive
4. **Phase 4** render QA: required motifs from `arc_required_motifs(arc)` must be present; failures route back to Phase 3.

## Maintenance

- **Re-extraction**: when `template/` changes, run:
  ```bash
  python scifig/knowledge/scripts/extract.py
  python scifig/knowledge/scripts/enrich.py
  ```
- **Case learning**: follow `knowledge/CASE_LEARNING_PROTOCOL.md` — one Markdown at a time, replica under `.workflow/case_studies/`, promote reusable code into `runtime/`.
- **Code promotion**: optional Phase 5 per `specs/template-distillation-contract.md`.

## Phase 3 Bootstrap

```python
from template_mining_helpers import (
    apply_journal_kernel, resolve_palette, role_color,
    add_metric_box, add_perfect_fit_diagonal, add_zero_reference,
    add_group_dividers, add_panel_label,
    density_sort, density_color_scatter,
    add_polygon_polar_grid, draw_gradient_box,
    add_forest_panel, resolve_forest_model_style_map,
    resolve_method_style_map, resolve_parity_split_style_map,
    add_heatmap_pairwise_panel,
    apply_scatter_regression_floor, resolve_split_palette,
    set_polar_title,
    build_grid, select_narrative_arc, arc_required_motifs,
    arc_default_grid, apply_zorder_recipe, bootstrap_chart,
)

apply_journal_kernel(variant="hero", journalProfile=journalProfile)
fig, axes, palette = bootstrap_chart(arc="hero", panel_count=1,
                                     palette="nature_radar_dual",
                                     journalProfile=journalProfile)
```

Finalizer-safe rules: `resources/finalizer-safe-template-contract.md`, `resources/annotation-idioms-ready.md`.
