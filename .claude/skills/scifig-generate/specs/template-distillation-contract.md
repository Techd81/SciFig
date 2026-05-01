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
11. Each autonomous cycle must execute at least one generated-script-shaped probe in a fresh process. Direct smoke-harness helper calls cannot be the only source of runtime contract evidence.
12. Legend validation must compare `legendInputEntryCount` with the final figure legend. If labeled handles existed and no bottom-center shared legend survived, the figure fails.
13. Density validation must use rendered evidence. Low `figureInkFraction` or excessive `figureWhitespaceFraction` fails even if planned motif counters look complete.
14. **Template-mining helpers reachability is mandatory.** The runtime assembly in `phases/03-code-gen-style.md` Step 3.6 must embed `phases/code-gen/template_mining_helpers.py` source into the generated script BEFORE `helpers.py` and BEFORE generator function bodies. The `codeReview.embeddedTemplateMiningHelpersPresent` gate must remain `True` for every generated script. Adding a new chart family without updating that embedding is a contract violation.
15. **Generator → template-mining helper binding is mandatory.** Each chart family with a `template-mining/07-techniques/<family>.md` deep-dive must have its `gen_<family>` generator call the corresponding canonical template_mining_helpers API. The static binding map (Section "Generator Binding Contract" below) must be honored; any new generator added to `registry.py` for a family with a deep-dive doc must wire the canonical helper before the cycle report is accepted.
16. **Palette routing must be chart-family aware.** `build_palette_plan` in `phases/02-recommend-stats.md` must contain explicit branches for chart families anchored to specific palettes (radar→`nature_radar_dual`/`morandi_sci_4`, forest→`npg_4`, heatmap_pairwise→`red_blue_correlation`, shap_composite→`cool_summer_4`, etc.). Adding a new chart family with a palette-bank anchor without adding the matching `build_palette_plan` branch is a contract violation.

## Generator Binding Contract

Each entry maps a chart family to (1) its registered generator function, (2) the canonical
template_mining_helpers API it must call, and (3) the deep-dive reference. Autonomous
distillation cycles must verify these bindings via static scan of generator source.

| Chart family          | Registered generator           | Required template_mining_helpers calls                                              | Deep-dive reference                     |
|-----------------------|--------------------------------|-------------------------------------------------------------------------------------|------------------------------------------|
| `radar`               | `gen_radar`                    | `add_polygon_polar_grid` + `apply_zorder_recipe('radar', ...)`                      | `07-techniques/radar.md`                |
| `biodiversity_radar`  | `gen_biodiversity_radar`       | `add_polygon_polar_grid` + `apply_zorder_recipe('radar', ...)`                      | `07-techniques/radar.md`                |
| `forest`              | `gen_forest`                   | `add_forest_panel`                                                                   | `02-zorder-recipes.md § forest`          |
| `scatter_regression`  | `gen_scatter_regression`       | `apply_scatter_regression_floor` + `add_perfect_fit_diagonal` (when prediction)     | `02-zorder-recipes.md § scatter-regression` + `05-annotation-idioms.md § I1, I2` |
| `marginal_joint`      | (via `gen_scatter_regression`) | `density_color_scatter` + `add_perfect_fit_diagonal` + marginal axes setup          | `07-techniques/marginal-joint.md`        |
| `heatmap_triangular`  | `gen_heatmap_triangular`       | `TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)` + `RdBu_r` cmap (corpus anchor)          | `07-techniques/heatmap-pairwise.md`      |
| `dual_axis`           | (axis pair generator)          | `apply_zorder_recipe('dual_axis', ...)` + corpus-anchored color spines              | `07-techniques/dual-axis.md`             |
| `shap_composite`      | (via composite board)          | `add_zero_reference` + `add_group_dividers` + bipolar palette                       | `07-techniques/shap-composite.md`        |

### Static-scan probe (autonomous cycle requirement)

Every autonomous distillation cycle must run the binding probe and persist its output
to the cycle report. Pseudo-spec:

```python
import re
from pathlib import Path
SOURCE_FILES = [
    "phases/code-gen/generators-distribution.md",
    "phases/code-gen/generators-clinical.md",
    "phases/code-gen/generators-psychology.md",
    "phases/code-gen/generators-distribution.py",
]
BINDINGS = {
    "gen_radar":               ["add_polygon_polar_grid"],
    "gen_biodiversity_radar":  ["add_polygon_polar_grid"],
    "gen_forest":              ["add_forest_panel"],
    "gen_heatmap_triangular":  ["TwoSlopeNorm", "RdBu_r"],
    "gen_scatter_regression":  ["apply_scatter_regression_floor"],
}
text = "\n".join(Path(p).read_text(encoding="utf-8") for p in SOURCE_FILES if Path(p).exists())
violations = []
for fn_name, required_calls in BINDINGS.items():
    fn_pattern = re.compile(rf"^def {re.escape(fn_name)}\([\s\S]*?(?=^def |\Z)", re.M)
    m = fn_pattern.search(text)
    if not m:
        violations.append(f"missing_generator:{fn_name}")
        continue
    body = m.group(0)
    for required in required_calls:
        if required not in body:
            violations.append(f"unbound:{fn_name}:{required}")
# violations must be empty for the cycle to be accepted.
```

The cycle report's `templateMiningHelperBindings` field must include both the per-generator
binding status and the violation list. A non-empty violation list is a hard block — the cycle
must not commit until either (a) the generator is updated to call the required helper, or
(b) the binding contract is amended in this file (with a recorded reason and ticket reference).

## Classification

| Class | Destination | Required Validation |
|-------|-------------|---------------------|
| `motif` | `specs/template-visual-motifs.md` + Phase 2 motif inference | exact planned-vs-applied motif coverage plus Phase 4 hard gate |
| `layout` | `templates/panel-layout-recipes.md` or `template-mining/04-grid-recipes.md` | no cross-panel overlap; reserved slots for outside elements; runtime contract report persisted |
| `helper` | `phases/code-gen/helpers.py` or `template_mining_helpers.py` | targeted unit/render test plus runtime QA metadata from a generated-script-shaped probe |
| `generator` | split generator file + `registry.py` + chart catalog | registry completeness test and smoke/render test, including at least one generated-script-shaped execution when the generator is part of the promoted path |
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
- Persist `legendInputEntryCount`, `figureLegendCount`, `figureInkFraction`, and `figureWhitespaceFraction` for every saved figure.
- Prove at least one `render_contracts.json` record per cycle came from a generated-script-shaped probe, not a synthesized harness report.
- Keep layout finalization in `audit_figure_layout_contract(...)`.
- Keep density finalization in `audit_visual_density_contract(...)` whenever template or reference motifs are planned.
- Never invent statistics for visual impact.
- Prefer one strong article-derived motif plus one support motif over many weak decorations.
- Keep all generated output source-data friendly and reproducible.
- In each autonomous cycle, compare the new smoke bundle against the previous cycle and promote at least one reusable lesson before the next commit.
