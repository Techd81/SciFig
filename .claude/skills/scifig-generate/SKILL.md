---
name: scifig-generate
description: Upload experimental data (CSV/Excel/matrix), auto-detect structure, infer scientific domain, recommend publication-grade charts, generate Nature/Cell/Science-aligned figure code, optimize multi-panel composition and palette systems, and export vector graphics with statistical reports. Triggers on "generate figure", "plot data", "sci figure", "科研图", "画图", "多 panel".
allowed-tools: Agent, AskUserQuestion, TodoWrite, Read, Write, Edit, Bash, Glob, Grep
---
# SciFig Generate

End-to-end workflow for turning real experimental data into submission-ready scientific figures. The skill is journal-token driven, domain-aware, and narrative-first: it reads the data, infers the scientific context, picks chart families and statistics, builds a multi-panel story when needed, and exports reproducible code plus publication assets.

## Architecture

Pipeline: preference gates -> Phase 1 `dataProfile` -> Phase 2 `chartPlan` -> Phase 3 `styledCode` -> Phase 4 `outputBundle`. Each phase owns one artifact, and blocking findings route back to the owning phase before completion.

## Key Design Principles

1. **Journal-token driven**: Use explicit style profiles instead of ad-hoc plotting choices. Nature dimensions are grounded in the official Nature figure guide; Cell-like and Science-like presets maintain the same production-safe discipline.
2. **Domain-aware charting**: Infer likely domains such as genomics, single-cell, pharmacology, neuroscience, or clinical survival and bias chart recommendations toward the conventions of that field.
3. **Narrative multi-panel design**: Treat multi-panel figures as a story with hero, support, validation, and mechanism panels rather than a loose grid of unrelated plots.
4. **Palette governance**: Prefer restrained, colorblind-safe palettes; keep semantic mappings consistent across panels; avoid rainbow and uncontrolled red-green contrasts.
5. **Statistical honesty**: No inferential claims without replicate or cohort meaning. When data only support descriptive visualization, say so.
6. **Reference visual grammar**: Add data-supported evidence layers that make figures look like dense top-journal panels: metric tables, perfect-fit/reference lines, density halos, marginal distributions, density-colored points, sample-shape overlays, matrix cell labels, p-value stars only when supplied, and dual-axis error bars only when error columns exist.
7. **Policy-driven defaults**: Thresholds for scale, crowding, visual density, render retries, and export QA come from shared workflow policies rather than ad-hoc literals.
8. **Agent-assisted quality gates**: Use read-only Agents for complex schema review, chart/stat planning, layout/palette audit, generated-code review, and rendered QA.
9. **Reproducibility-first**: Every figure should be exportable as code plus metadata, source-data manifests, render-QA evidence, and methods-ready statistical descriptions.
10. **Template-mining grounded**: All "顶刊感" choices (rcParams kernel, sandwich layering, palette, GridSpec recipes, in-axes idioms, narrative arcs) trace back to the 77 reference cases under `template/articles/`, distilled into the 7-module knowledge base under `template-mining/`. Operational helpers live in `phases/code-gen/template_mining_helpers.py`.

## Template-Mining Knowledge Base

`template-mining/` is the project's canonical reference layer for visual grammar. **All Phase 2 narrative-arc / chart-family decisions and Phase 3 styling decisions must consult this knowledge base** instead of inventing patterns.

**Loading protocol** (see `template-mining/INDEX.md`):

1. **Always** load `template-mining/INDEX.md` before Phase 2/3 decisions.
2. **Phase 2** narrative + chart selection:
   - Read `06-narrative-arcs.md` to bind the figure to one of 10 corpus arcs.
   - Read `04-grid-recipes.md` if `panel_count > 1`.
   - Lookup `case-index.json` for ≥3 cases matching `chart_families` or `narrative_arc`.
3. **Phase 3** code generation:
   - Read `01-rcparams-kernel.md` for the kernel; call `apply_journal_kernel(variant, journalProfile)`.
   - Read `02-zorder-recipes.md` for the matching chart family; call `apply_zorder_recipe(family, ax, layers)`.
   - Read `03-palette-bank.md` to bind palette names to hex; call `resolve_palette(name)` and `role_color(role)`.
   - Read `05-annotation-idioms.md` to apply in-axes idioms; call `add_metric_box`, `add_perfect_fit_diagonal`, `add_zero_reference`, `add_group_dividers`, `add_panel_label`, `density_color_scatter`, `add_polygon_polar_grid`, `draw_gradient_box` from `template_mining_helpers`.
   - Read `07-techniques/<family>.md` only if the chart family has a dedicated deep-dive (radar, shap-composite, dual-axis, heatmap-pairwise, marginal-joint, time-series-pi, lollipop-bipolar, gradient-box, inset-distribution).
4. **Phase 4** render QA: every required motif from the chosen arc + family must be present (`arc_required_motifs(arc)`); failures route back to Phase 3.

**Re-extraction**: when `template/articles/` changes, run `python .claude/skills/scifig-generate/template-mining/_extraction/extract.py` then `enrich.py` to refresh `case-index.json`, `stats.md`, `narratives.md`. Then audit the "Distilled Universal Findings" section in `INDEX.md`.

**Code promotion**: when the user asks to absorb article examples into the skill, run optional Phase 5 and follow `specs/template-distillation-contract.md`. Promote reusable Matplotlib logic into helpers/generators first; update prose only after executable behavior and tests exist.

**Operational entry point** — Phase 3 generators should start with:

```python
from template_mining_helpers import (
    apply_journal_kernel, resolve_palette, role_color,
    add_metric_box, add_perfect_fit_diagonal, add_zero_reference,
    add_group_dividers, add_panel_label,
    density_sort, density_color_scatter,
    add_polygon_polar_grid, draw_gradient_box,
    build_grid, select_narrative_arc, arc_required_motifs,
    arc_default_grid, apply_zorder_recipe, bootstrap_chart,
)

apply_journal_kernel(variant="hero", journalProfile=journalProfile)
fig, axes, palette = bootstrap_chart(arc="hero", panel_count=1,
                                     palette="nature_radar_dual",
                                     journalProfile=journalProfile)
```

## Interactive Preference Collection

Collect workflow preferences before dispatching to phases, but treat data availability, file-path validation, and mode selection as separate gates.

- Never use Bash, Glob, Grep, or Read to scan the workspace for candidate CSV, TSV, XLSX, or XLS files.
- Never assume files under `tests/`, `output/`, fixtures, or nearby folders are the user's real data.
- Mirror the user's language in all AskUserQuestion cards. If the request is Chinese, use Chinese cards from the start.
- If the user did not explicitly provide `FILE:` or a concrete file path, first use AskUserQuestion to ask whether a data file already exists.
- If the user says a file exists, use a second AskUserQuestion card to ask where it is. Tell the user to choose Other and paste the exact path there so the answer still appears under `User answered Claude's questions`.
- If the path card comes back with the canned option label instead of a real path, ask one direct follow-up for the exact path and stop there.
- Only accept concrete file paths ending in `.csv`, `.tsv`, `.xlsx`, or `.xls`. If the reply is a directory, a folder-like path, or anything without one of those suffixes, ask again and stop there.
- Never run Bash, Read, Grep, or directory inspection on a provided path before both the file-path gate and the mode gate are complete.
- Mode selection is a separate gate after the data-status decision, and after the file path only when a real file already exists. Never infer `auto` from any answer that is not an exact mode-card selection, and never fall through to auto defaults after an invalid answer.
- If the user answers a card with a localization request such as `请用中文`, treat it as a language-switch request, re-issue the same card in Chinese, and do not consume it as a data or mode decision.
- If the user does not have data yet, branch explicitly: either help define a schema/template first, or generate a synthetic dataset only if the user explicitly asks for simulated data. Custom domains entered through Other must be preserved and must not collapse back to biomedical defaults.
- AskUserQuestion payloads must stay tool-compatible: every question needs `id`, `header`, `question`, and 2-3 options. Do not use `multiSelect`. Use 1-3 questions per card by default; the final visual preference card is the only permitted 4-question exception because journal style, color, resolution, and crowding must be answered together. Before showing that card, perform a domain-journal synthesis step from the selected or custom scientific domain. The journal-style options must be field-leading journals, conferences, or venue families for that exact domain, not a fixed Nature/Science/Cell list.

Preference collection helpers, bilingual card templates, answer maps, and resolution maps are defined in [specs/preference-collection.md](specs/preference-collection.md). Read that file before executing any AskUserQuestion card. The helpers use a single bilingual-lookup pattern instead of duplicated zh/en branches.

Key functions from that file used in the flow below:
- `normalize_card_answer(raw_answer, mapping)` -- resolves card answers, detects language-switch requests
- `is_concrete_data_file_path(path_candidate)` -- validates file suffix
- `resolve_domain_answer(raw_answer, mapping)` -- maps domain card answers to family keys
- `infer_journal_style_options(domain_family, custom_domain_text, language, context=None)` -- AI-generated journal options with domain-aware fallback
- `infer_synthetic_bundle_options(domain_family, custom_domain_text, language)` -- domain-aware bundle options
- `generate_options_with_ai(context, question_type, fallback_options)` -- AI option generation with fallback chain
- `_call_option_generator(prompt, question_type, fallback_options)` -- coordinator-interceptable call with proper fallback

## Preference Collection Flow

Execute the 6-card flow defined in [specs/preference-collection.md](specs/preference-collection.md) § "Card Definitions and Flow". Use the bilingual answer maps, card option templates, and resolution maps from that file. The flow is:

1. **Data-status card**: `normalize_card_answer(answer, DATA_STATUS_MAP)` → `file_exists` / `synthetic_data` / `template`
2. **Data-path card** (only if file exists): `normalize_card_answer(answer, DATA_PATH_MAP)` → validate with `is_concrete_data_file_path()`
3. **Mode card**: `normalize_card_answer(answer, MODE_MAP)` → `auto` / `interactive`
4. **Synthetic-domain card** (only if synthetic): `resolve_domain_answer(answer, SYNTHETIC_DOMAIN_MAP)` → domain family + custom text
5. **Synthetic-bundle card** (only if synthetic): `infer_synthetic_bundle_options()` + optional `generate_options_with_ai()`
6. **Visual-preference card** (4 questions): use `_localize_options(template, lang)` for palette/resolution/crowding; use `infer_journal_style_options(..., context={...})` for AI-generated field-top-journal options based on the selected domain. Pass only `{label, description}` to AskUserQuestion, but keep the full `journalOptions` list in state for `styleKey` resolution. Example: audio/signal/acoustics should produce options such as IEEE/ACM TASLP, JASA, IEEE TSP / Signal Processing, ICASSP, or Interspeech when appropriate, not generic Nature-like / Science-like / Cell-like options.

After all cards, assemble `workflowPreferences` using the resolution maps (`JOURNAL_STYLE_RESOLVE`, `STORY_MODE_RESOLVE`, `MISSING_RESOLVE`, `COLOR_MODE_RESOLVE`, `DPI_RESOLVE`, `CROWDING_RESOLVE`, `EXPORT_FORMATS_RESOLVE`, `STATS_RIGOR_RESOLVE`, `PANEL_LAYOUT_RESOLVE`) as defined in § "Building `workflowPreferences`".

For auto mode: fill visual-preference card with submission-safe defaults unless the user selected interactive mode. Freeze `workflowPreferences` before phase dispatch.

## Auto Mode Defaults

When `workflowPreferences["interactionMode"] == "auto"`:

- Ask the data-status card first, then always ask the explicit mode card before any plotting or synthetic-data generation branch. Ask the data-path card only when the user already has a file.
- If the user chooses synthetic data, ask the synthetic-domain card after mode selection, infer suitable journal-style and bundle options from that answer, then ask the synthetic-bundle card as a separate follow-up.
- Ask journal style, color, raster DPI, and crowding together in the final visual preference card for every synthetic-data run. The journal-style options in that card must come from `infer_journal_style_options(..., context={...})`, which first asks AI to reason from the selected domain, custom domain text, and available data/profile context, then falls back to domain-specific top-journal seeds only if AI generation is unavailable or invalid. Do not show the broad Nature/Science/Cell trio unless the selected field itself is broad high-impact biology or the user explicitly asks for cross-disciplinary top-journal styling. For real-file auto mode, fill these with submission-safe defaults unless the user selected interactive mode.
- Use `crowdingPolicy=auto_simplify` and `overlapPriority=clarity_first`.
- Continue directly into Phase 1 only after either a concrete user-confirmed file path exists or a user-approved synthetic-data plan exists, and only after the user explicitly selected free mode.
- Let the data and detected domain cues drive the recommendation unless the user already supplied explicit `DOMAIN_OVERRIDE` or `MUST_HAVE` constraints.

## Execution Flow

> **COMPACT DIRECTIVE**: The phase currently marked `in_progress` in TodoWrite is the active execution phase and must remain uncompressed. If a sentinel survives but the detailed protocol does not, re-read that phase file before continuing.

**Phase Reference Documents** (read on-demand):

| Phase | Document                                                  | Purpose                                                        | Compact                     |
| ----- | --------------------------------------------------------- | -------------------------------------------------------------- | --------------------------- |
| 1     | [phases/01-data-detect.md](phases/01-data-detect.md)         | Data ingestion, semantic role mapping, domain inference        | TodoWrite driven            |
| 2     | [phases/02-recommend-stats.md](phases/02-recommend-stats.md) | Chart taxonomy selection, stats, panel blueprint               | TodoWrite driven + sentinel |
| 3     | [phases/03-code-gen-style.md](phases/03-code-gen-style.md)   | Journal profiles, palette system, code generation, composition | TodoWrite driven + sentinel |
| 4     | [phases/04-export-report.md](phases/04-export-report.md)     | Export bundle, source data, metadata, reporting                | TodoWrite driven            |
| 5*    | [phases/05-template-distill.md](phases/05-template-distill.md) | Optional article-code distillation and runtime promotion        | TodoWrite driven + sentinel |

**Reference Specs** (read on-demand when needed):

| Kind       | Document                                                                    | Purpose                                                   |
| ---------- | --------------------------------------------------------------------------- | --------------------------------------------------------- |
| Journal    | [specs/journal-profiles.md](specs/journal-profiles.md)                         | Nature/Cell/Science-aligned style tokens                  |
| Charts     | [specs/chart-catalog.md](specs/chart-catalog.md)                               | Expanded chart family taxonomy and triggers               |
| Domains    | [specs/domain-playbooks.md](specs/domain-playbooks.md)                         | Domain-specific plotting, stats, and panel guidance       |
| Policies   | [specs/workflow-policies.md](specs/workflow-policies.md)                       | Shared thresholds, visual impact, performance, QA, agents |
| Prefs      | [specs/preference-collection.md](specs/preference-collection.md)               | Preference collection helpers, bilingual card templates   |
| Motifs     | [specs/template-visual-motifs.md](specs/template-visual-motifs.md)             | Template-derived evidence motifs and QA counters          |
| Distill    | [specs/template-distillation-contract.md](specs/template-distillation-contract.md) | Rules for promoting article code into executable skill behavior |
| Layouts    | [templates/panel-layout-recipes.md](templates/panel-layout-recipes.md)         | Reusable multi-panel story recipes                        |
| Palettes   | [templates/palette-presets.md](templates/palette-presets.md)                   | Reusable categorical/sequential/diverging palette presets |

**Compact Rules**:

1. `TodoWrite in_progress` -> preserve full content
2. `TodoWrite completed` -> safe to compress to summary
3. If a sentinel remains without the full step protocol -> `Read("phases/0N-xxx.md")` before continuing

## Agent Delegation Policy

Do not spawn any Agent before the data-status, file-path, and mode gates are complete. After those gates, delegate only when complexity or risk justifies the overhead, and keep agent work read-only unless the coordinator explicitly asks for a rewritten artifact.

| Agent | Phase | Trigger | Output |
| ----- | ----- | ------- | ------ |
| `data-profile-auditor` | 1 | structure=="matrix", missing_rate>10%, no group/value roles, survival/dose-response with missing roles, n_groups>10 | `dataProfile.audit` |
| `chart-stats-planner` | 2 | inferential claims requested, custom domain, n_groups>=6, survival or dose-response charts | `chartPlan.delegationReports.stats` |
| `panel-layout-auditor` | 2 | panel_count>2, shared legend/colorbar, labels>24 chars, n_groups>=8 | `chartPlan.delegationReports.layout` |
| `palette-journal-auditor` | 2 | n_categories>=8, domain semantic colors, grayscale-safe request, journal submission | `chartPlan.delegationReports.palette` |
| `scientific-color-harmony` | 2 | after build_palette_plan | `chartPlan.delegationReports.color_harmony` |
| `layout-aesthetics` | 2 | after build_panel_blueprint | `chartPlan.delegationReports.aesthetics` |
| `content-richness` | 2 | after build_visual_content_plan | `chartPlan.delegationReports.content_richness` |
| `code-reviewer` | 3 | before Phase 3 completes | `styledCode.codeReview` |
| `rendered-qa` | 4 | after code execution and before outputBundle | `outputBundle.renderQa` |
| `visual-impact-scorer` | 4 | after rendered-qa | `outputBundle.renderQa.impactScore` |

Blocking agent findings must route back to the owning phase before advancing. Never bury them in final notes.

## Core Rules

1. Do not claim a Nature- or Cell-like figure solely from a palette; typography, spacing, line weight, and panel discipline must also match.
2. Do not use bar charts to hide distributions when individual-level or cohort-level data can be shown.
3. Do not mix unrelated semantic color mappings across panels of the same figure.
4. Do not use rainbow colormaps unless the variable is cyclic and the legend explicitly justifies it.
5. Keep all figure text editable, sans serif, and legible at final print size.
6. Treat every legend as a figure-level layout element in final output, not as an axes annotation. When panels share group, color, marker, or line semantics, keep one shared framed `fig.legend` outside every plotting area; allowed positions are bottom-center first, then top-center. Never use `loc="best"` or outside-right for publication output.
7. Every generated script must call `enforce_figure_legend_contract(...)` immediately before the first `savefig` for each figure. Direct `ax.legend(...)` calls are temporary handle sources only; if the finalizer is missing, or if any axis legend remains after the finalizer, return to Phase 3.
8. Do not hand-write replacement runtime helpers when the skill already provides them. Generated code must embed and execute the helper source from `phases/code-gen/helpers.py`, so `legendContractEnforced`, `layoutContractEnforced`, overlap checks, and typography gates are real runtime results rather than local approximations.
9. Use shared legends or shared colorbars when panels encode the same semantics.
10. Multi-panel figures must have an explicit panel blueprint before code generation.
11. For implemented single-panel charts, increase Nature/Cell-style information density through data-derived summaries, in-plot explanatory labels, reference lines, callouts, insets, sample-size labels, metric tables, prediction diagnostics, marginal distributions, density-colored points, density halos, matrix labels, and effect-size context before adding new chart types.
12. Treat `specs/template-visual-motifs.md` as the grammar for learning from reference examples. Add motifs to `visualContentPlan.templateMotifs` and render them through existing generators/helpers; do not register a new chart key until a real generator exists and passes QA.
13. When learning from `template/articles`, promote reusable code into `helpers.py`, `template_mining_helpers.py`, or split generator files before expanding coordinator prose.
14. Do not invent statistics for visual impact. Every p-value, AUC, effect size, threshold count, or fitted parameter must come from the supplied data or a documented upstream result.
15. Prefer vector export and generate source-data friendly artifacts for quantitative panels.
16. If domain inference is weak, fall back to general biomedical rules instead of overfitting to a guessed specialty.
17. If statistical assumptions are uncertain, downgrade to a conservative or descriptive choice and explain why.
18. If rendered QA reports overlap, cross-panel title/table/text collision, negative axes text without a reserved slot, poster-scale font sizes, blank/tiny output, missing `legendContractEnforced`, missing `layoutContractEnforced`, any remaining in-axes legend, too few visual enhancements, missing template/reference visual grammar motifs, missing in-plot explanatory labels, non-editable vector text, or missing formats, return to Phase 3 or Phase 2 before declaring completion.
19. Use `specs/workflow-policies.md` for thresholds and budgets; do not add new magic numbers in phase logic without naming the policy.

## Input Processing

User input is normalized into:

```text
FILE: /path/to/data.csv
EXTRAS: optional figure request or hypothesis
DOMAIN_OVERRIDE: optional explicit domain hint
MUST_HAVE: optional chart or panel requirements
```

Normalize a confirmed real-file reply into `FILE:` and carry that exact path into Phase 1 as `{{FILE_PATH}}`. If `DOMAIN_OVERRIDE` conflicts with detected cues, keep the user override but warn in Phase 2. All preference collection rules and card flow are defined in the "Interactive Preference Collection" section above and in [specs/preference-collection.md](specs/preference-collection.md).

## Data Flow

Carry these canonical fields forward:

- `dataProfile`: `format`, `structure`, `columns`, `semanticRoles`, `domainHints`, `nGroups`, `nObservations`, `replicateInfo`, `riskFlags`, `panelCandidates`, `warnings`, `audit`
- `chartPlan`: `primaryChart`, `secondaryCharts`, `statMethod`, `multipleComparison`, `annotations`, `panelBlueprint`, `crowdingPlan`, `visualContentPlan`, `templateMotifs`, `palettePlan`, `delegationReports`, `journalOverrides`, `rationale`
- `styledCode`: `pythonCode`, `journalProfile`, `figureSpec`, `colorSystem`, `panelGeometry`, `statsReport`, `codeReview`, `seed`
- `outputBundle`: `figures`, `code`, `statsReport`, `sourceData`, `panelManifest`, `requirements`, `metadata`, `renderQa`

## TodoWrite Pattern

Keep exactly one active phase. Expand the active phase into concrete sub-tasks, then collapse completed work back to a phase-level summary before starting the next phase.

## Post-Phase Updates

- After Phase 1: If domain inference is high confidence, note the selected domain playbook and any field-specific warnings.
- After Phase 2: Freeze the chart vocabulary, panel blueprint, visual-content plan, and palette plan unless the user requests revision.
- After Phase 3: Validate syntax, imports, code-review findings, generator coverage, and layout consistency before export.
- After Phase 4: Summarize render QA and how the user can iterate without re-running Phase 1.

## Error Handling

- Ambiguous domain -> fall back to `General biomedical`, present the top alternatives in rationale.
- Unsupported chart request -> map to the closest supported family and explain the substitution.
- Overcrowded multi-panel plan -> reduce to fewer panels or use a hero-plus-support recipe.
- Palette collision -> fall back to journal-safe muted palette with grayscale-safe accents.
- Weak statistical support -> switch to descriptive mode or a more conservative test.
- Rendered QA failure -> return to Phase 3 for layout/style/code or Phase 2 for an overpacked plan.

## Coordinator Checklist

- Confirm a readable input file exists. If the path is missing, use a data-status card, a data-path card, validate the file suffix, and then use a separate mode card before Phase 1.
- Never scan the workspace for candidate data files unless the user explicitly asked for that behavior.
- If the confirmed path is a directory or lacks a supported file suffix, ask again and stop there.
- Never run Bash, Read, Grep, or directory inspection before the file-path gate and mode gate are both complete.
- If any card answer is a language-switch request or otherwise invalid, re-ask the same card and do not consume it as a decision.
- Collect `workflowPreferences` with tool-compatible AskUserQuestion rounds before any phase dispatch, preserving the final 4-question visual preference card when synthetic data or interactive mode requires it.
- In auto mode, do not stop for extra style questions after defaults are set unless the user explicitly asks to switch to interactive refinement.
- Read chart/domain/journal references only when needed.
- Keep the active phase marked `in_progress`.
- Before Phase 3, ensure the panel blueprint and palette plan are explicit.
- Before Phase 3, resolve blocking chart/stat/layout/palette agent findings.
- Before Phase 4, ensure code generation includes source-data, render-QA, and metadata hooks.
- Before completion, require `renderQa.hardFail == false`, `legendContractEnforced == true`, `layoutContractEnforced == true`, `legendOutsidePlotArea == true`, `axisLegendRemainingCount == 0`, `layoutContractFailures == []`, `legendModeUsed in ["bottom_center", "top_center", "none"]`, exactly one framed shared legend when a legend exists, and enough data-derived visual content to satisfy `visualContentPlan.minTotalEnhancements` and `visualContentPlan.minInPlotLabelsPerFigure`.

## Related Commands

- `/spec-add learning ...` to record new plotting or domain edge cases.
- `/spec-add arch ...` when the eventual runtime package introduces permanent APIs.
