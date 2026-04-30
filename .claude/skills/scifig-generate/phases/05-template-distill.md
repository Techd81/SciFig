# Phase 5: Template Article Distillation

> **COMPACT SENTINEL [Phase 5: template-distill]**
> This optional maintenance phase contains 6 execution steps.
> If only this sentinel remains, recover with `Read("phases/05-template-distill.md")`.

Distill reusable visual code and design grammar from `D:/SciFig/template/articles` into the executable `scifig-generate` skill.

## Objective

- Inventory changed or underused article examples.
- Classify each finding as a motif, layout recipe, helper primitive, generator, or policy.
- Promote reusable code into the canonical runtime files instead of growing prompt prose.
- Keep registry, chart catalog, Phase 2 planning, Phase 3 code generation, and tests aligned.

## Execution

### Step 5.1: Article Inventory

Scan `template/articles/*.md` for Python code fences, Matplotlib APIs, layout APIs, and named visual tricks. Record article filename, code block count, detected chart family, and candidate APIs such as `GridSpec`, `SubGridSpec`, `inset_axes`, `twinx`, `polar`, `contourf`, `gaussian_kde`, `PathPatch`, `FancyBboxPatch`, and custom colormaps.

### Step 5.2: Promotion Classification

Use [specs/template-distillation-contract.md](../specs/template-distillation-contract.md). Classify every candidate as:

- `motif`: reusable overlay or annotation grammar for `specs/template-visual-motifs.md`.
- `layout`: reusable panel structure for `templates/panel-layout-recipes.md` or `template-mining/04-grid-recipes.md`.
- `helper`: reusable runtime primitive for `phases/code-gen/helpers.py` or `template_mining_helpers.py`.
- `generator`: full chart implementation for a split generator file plus `registry.py`.
- `policy`: threshold or hard gate for `specs/workflow-policies.md` and Phase 4 QA.

### Step 5.3: Code Promotion

Promote real code in this order:

1. Shared primitives into `phases/code-gen/helpers.py` when generated scripts must execute the behavior.
2. Template-mining primitives into `phases/code-gen/template_mining_helpers.py` when Phase 3 needs style helpers before generator assembly.
3. Existing chart upgrades into the current split generator file.
4. New chart keys only after a generator, catalog row, recommendation rule, and test exist.

Do not paste article snippets into `SKILL.md` or Phase 3 prose. The promoted code must be import-free or use dependencies already emitted into generated scripts.

### Step 5.4: Planning And QA Sync

If a promoted primitive changes figure planning, update Phase 2:

- `infer_template_layout_intents`
- `infer_template_visual_motifs`
- `build_visual_content_plan`

If completion criteria change, update Phase 4 render QA and `specs/workflow-policies.md`.

### Step 5.5: Validation

Run:

```powershell
python -m pytest tests/test_crowding_controls.py -q
python -m pytest tests/test_scifig_generators.py -q
python -m pytest tests/test_skill_prompt_contracts.py -q
python -m pytest -q
git diff --check
```

Add targeted tests for every promoted helper or generator path. Render QA failures are blockers, not caveats.

### Step 5.6: Distillation Report

Summarize:

- article files mined
- promoted motifs/helpers/generators
- files changed
- tests run
- remaining gaps that still prevent matching the reference cases

## Output

- **Files**: promoted runtime/helper/generator/spec/test changes
- **Variable**: `templateDistillationReport`
- **TodoWrite**: Mark Phase 5 completed

## Next Phase

Return to orchestrator. If generated output quality still trails the article cases, run Phase 5 again on the highest-impact gap rather than adding more generic prompt text.
