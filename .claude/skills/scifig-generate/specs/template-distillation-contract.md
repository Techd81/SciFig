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

The binding map is grouped into **six chart-family categories**; every category must contain
at least one bound generator (family-coverage assertion in the binding probe).

### Polar / Radar family
Polygon dashed grid replaces matplotlib's default circular polar grid (Nature Vol 626 Fig 3c discipline).

| Chart family          | Registered generator           | Required template_mining_helpers calls                           | Deep-dive reference        |
|-----------------------|--------------------------------|------------------------------------------------------------------|-----------------------------|
| `radar`               | `gen_radar`                    | `add_polygon_polar_grid`                                          | `07-techniques/radar.md`   |
| `biodiversity_radar`  | `gen_biodiversity_radar`       | `add_polygon_polar_grid`                                          | `07-techniques/radar.md`   |

### Forest / CI family
One-call forest discipline: dashed reference line + asymmetric CI whiskers + per-row HR(CI) annotation column.

| Chart family          | Registered generator           | Required template_mining_helpers calls                           | Deep-dive reference                 |
|-----------------------|--------------------------------|------------------------------------------------------------------|-------------------------------------|
| `forest`              | `gen_forest`                   | `add_forest_panel`                                                | `02-zorder-recipes.md § forest`     |
| `caterpillar_plot`    | `gen_caterpillar_plot`         | `add_forest_panel` (linear scale, reference_line=0)               | `02-zorder-recipes.md § forest`     |
| `risk_ratio_plot`     | `gen_risk_ratio_plot`          | `add_forest_panel` (log scale, reference_line=1)                  | `02-zorder-recipes.md § forest`     |
| `ci_plot`             | `gen_ci_plot`                  | `add_forest_panel` (linear scale, reference_line=0)               | `02-zorder-recipes.md § forest`     |

### Correlation heatmap family
TwoSlopeNorm + RdBu_r enforce the corpus-anchored diverging palette centered at 0.

| Chart family          | Registered generator           | Required template_mining_helpers calls                           | Deep-dive reference                  |
|-----------------------|--------------------------------|------------------------------------------------------------------|--------------------------------------|
| `heatmap_triangular`  | `gen_heatmap_triangular`       | `TwoSlopeNorm` + `RdBu_r` cmap                                    | `07-techniques/heatmap-pairwise.md`  |
| `correlation`         | `gen_correlation`              | `TwoSlopeNorm` + `RdBu_r` cmap                                    | `07-techniques/heatmap-pairwise.md`  |
| `heatmap_symmetric`   | `gen_heatmap_symmetric`        | `TwoSlopeNorm` + `RdBu_r` cmap                                    | `07-techniques/heatmap-pairwise.md`  |

### Perfect-fit diagonal family (y=x reference)
Dashed y=x line for predicted-vs-actual / probability-probability / quantile-quantile / random-classifier panels.

| Chart family          | Registered generator           | Required template_mining_helpers calls                           | Deep-dive reference                  |
|-----------------------|--------------------------------|------------------------------------------------------------------|--------------------------------------|
| `calibration`         | `gen_calibration`              | `add_perfect_fit_diagonal`                                        | `05-annotation-idioms.md § I2`       |
| `pp_plot`             | `gen_pp_plot`                  | `add_perfect_fit_diagonal`                                        | `05-annotation-idioms.md § I2`       |
| `qq`                  | `gen_qq`                       | `add_perfect_fit_diagonal`                                        | `05-annotation-idioms.md § I2`       |
| `roc`                 | `gen_roc`                      | `add_perfect_fit_diagonal` (random classifier chance line)        | `05-annotation-idioms.md § I2`       |

### Zero reference family
Dashed/solid y=0 (or x=0) anchor for residual / fold-change / waterfall / diverging / SHAP-divider panels.

| Chart family          | Registered generator           | Required template_mining_helpers calls                           | Deep-dive reference                  |
|-----------------------|--------------------------------|------------------------------------------------------------------|--------------------------------------|
| `residual_vs_fitted`  | `gen_residual_vs_fitted`       | `add_zero_reference` (axis='y') + `apply_scatter_regression_floor` | `05-annotation-idioms.md § I4`       |
| `ma_plot`             | `gen_ma_plot`                  | `add_zero_reference` (axis='y')                                   | `05-annotation-idioms.md § I4`       |
| `waterfall`           | `gen_waterfall`                | `add_zero_reference` (axis='y')                                   | `05-annotation-idioms.md § I4`       |
| `diverging_bar`       | `gen_diverging_bar`            | `add_zero_reference` (axis='x')                                   | `05-annotation-idioms.md § I4`       |
| `likert_divergent`    | `gen_likert_divergent`         | `add_zero_reference` (axis='x')                                   | `05-annotation-idioms.md § I4`       |
| `decision_curve`      | `gen_decision_curve`           | `add_zero_reference` (axis='y', "Treat none" reference)           | `05-annotation-idioms.md § I4`       |
| `lollipop_horizontal` | `gen_lollipop_horizontal`      | `add_zero_reference` (axis='x', SHAP signed-value divider)        | `07-techniques/shap-composite.md`    |
| `dotplot`             | `gen_dotplot`                  | `add_zero_reference` (axis='x', SHAP composite divider)           | `07-techniques/shap-composite.md`    |

### Scatter regression floor family
L0 floor: light dashed grid + despine, applied BEFORE drawing scatter so the grid sits at zorder=0.
**Polar-safe** (cycle 21 + round-3): the despine step is skipped on polar axes so radar variants can call generically.

| Chart family          | Registered generator           | Required template_mining_helpers calls                           | Deep-dive reference                                |
|-----------------------|--------------------------------|------------------------------------------------------------------|----------------------------------------------------|
| `scatter_regression`  | `gen_scatter_regression`       | `apply_scatter_regression_floor` + `add_perfect_fit_diagonal` (when prediction) | `02-zorder-recipes.md § scatter-regression`         |
| `dose_response`       | `gen_dose_response`            | `apply_scatter_regression_floor`                                  | `02-zorder-recipes.md § scatter-regression`         |
| `scale_location`      | `gen_scale_location`           | `apply_scatter_regression_floor`                                  | `02-zorder-recipes.md § scatter-regression`         |

### Composite / future families (binding TBD)

| Chart family          | Registered generator           | Required template_mining_helpers calls                           | Deep-dive reference                                |
|-----------------------|--------------------------------|------------------------------------------------------------------|----------------------------------------------------|
| `marginal_joint`      | (via `gen_scatter_regression`) | `density_color_scatter` + `add_perfect_fit_diagonal` + marginal axes setup | `07-techniques/marginal-joint.md`                  |
| `dual_axis`           | (axis pair generator)          | `apply_zorder_recipe('dual_axis', ...)` + corpus-anchored color spines      | `07-techniques/dual-axis.md`                       |
| `shap_composite`      | (via composite board)          | `add_zero_reference` + `add_group_dividers` + bipolar palette               | `07-techniques/shap-composite.md`                  |

### Static-scan probe (autonomous cycle requirement)

Every autonomous distillation cycle must run `template-mining/_extraction/binding_probe.py`
and persist its output to the cycle report. The probe enumerates all 19 strict bindings
across the six covered families, reports per-generator pass/fail, and asserts every
family is covered.

```python
import re
from pathlib import Path
SOURCE_FILES = [
    "phases/code-gen/generators-distribution.md",
    "phases/code-gen/generators-distribution.py",
    "phases/code-gen/generators-clinical.md",
    "phases/code-gen/generators-psychology.md",
]
BINDINGS = {
    # Polar / Radar family
    "gen_radar":              ["add_polygon_polar_grid"],
    "gen_biodiversity_radar": ["add_polygon_polar_grid"],
    # Forest / CI family
    "gen_forest":             ["add_forest_panel"],
    "gen_caterpillar_plot":   ["add_forest_panel"],
    "gen_risk_ratio_plot":    ["add_forest_panel"],
    "gen_ci_plot":            ["add_forest_panel"],
    # Correlation heatmap family
    "gen_heatmap_triangular": ["TwoSlopeNorm", "RdBu_r"],
    "gen_correlation":        ["TwoSlopeNorm", "RdBu_r"],
    "gen_heatmap_symmetric":  ["TwoSlopeNorm", "RdBu_r"],
    # Perfect-fit diagonal family
    "gen_calibration":        ["add_perfect_fit_diagonal"],
    "gen_pp_plot":            ["add_perfect_fit_diagonal"],
    "gen_qq":                 ["add_perfect_fit_diagonal"],
    "gen_roc":                ["add_perfect_fit_diagonal"],
    # Zero reference family
    "gen_residual_vs_fitted": ["add_zero_reference", "apply_scatter_regression_floor"],
    "gen_ma_plot":            ["add_zero_reference"],
    "gen_waterfall":          ["add_zero_reference"],
    "gen_diverging_bar":      ["add_zero_reference"],
    "gen_likert_divergent":   ["add_zero_reference"],
    "gen_decision_curve":     ["add_zero_reference"],
    "gen_lollipop_horizontal": ["add_zero_reference"],
    "gen_dotplot":            ["add_zero_reference"],
    # Scatter regression floor family
    "gen_scatter_regression": ["apply_scatter_regression_floor", "add_zero_reference"],
    "gen_dose_response":      ["apply_scatter_regression_floor"],
    "gen_scale_location":     ["apply_scatter_regression_floor"],
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
binding status, the family-coverage map, and the violation list. A non-empty violation list
is a hard block — the cycle must not commit until either (a) the generator is updated to
call the required helper, or (b) the binding contract is amended in this file (with a
recorded reason and ticket reference).

### Guarded-call pattern (canonical + fallback)

When a generator binds to a template_mining_helpers API, it must use the **guarded-call
pattern** so the function still works when `template_mining_helpers.py` source is not
embedded in the runtime (e.g., legacy direct imports, alternate runtimes):

```python
canonical_helper = globals().get("helper_name")
if canonical_helper is not None:
    try:
        canonical_helper(ax, ...)
    except Exception:
        # inline fallback (preserved legacy implementation)
        ax.axhline(0, ...)
else:
    # inline fallback
    ax.axhline(0, ...)
```

Both branches must reference the helper name textually so the binding probe sees the
binding regardless of which path executes at runtime.

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

### Wave-2 Distillation Output (V0.1.1)

The following ready-to-import registries are the authoritative runtime outputs
of the V0.1.1 template distillation wave:

| Registry | Responsibility | Importer |
|----------|----------------|----------|
| `templates/template-palette-registry.json` | Named palettes plus semantic role colors. | `template_mining_helpers.resolve_palette` and `role_color` |
| `templates/layout-recipes-ready.json` | `R0`-`R11` GridSpec/subplots recipes with reserved legend/colorbar/inset slots. | `template_mining_helpers.build_grid` and Phase 3 layout planning |
| `templates/zorder-recipes-ready.json` | Universal zorder tiers plus family overrides. | `template_mining_helpers.apply_zorder_recipe` |

Phase 3 documentation may link to these files, but must not duplicate palette,
layout, or zorder defaults inline.

### Family-Level Smoke Matrix (V0.1.1)

`template-mining/_extraction/binding_probe.py` must verify the strict generator
bindings plus this 10 family x 5 check smoke matrix. Each row is grep-backed
against generator source, Phase 3/4 contracts, helper code, and ready registry
files.

| Family | legend_compliance | zorder_declared | colorbar_slot_reserved | inset_audit_inclusion | text_safe_bbox |
|--------|-------------------|-----------------|------------------------|-----------------------|----------------|
| scatter_regression | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| ale_pdp | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| shap_composite | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| dual_axis | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| heatmap | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| multipanel_grid | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| single_focus | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| global_local | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| n_by_n_pairwise | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
| marginal_joint | finalizer path | zorder recipe | reserved slot contract | normalize_axes_map | text safety audit |
