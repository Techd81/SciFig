# Case Learning Protocol

Use this when a template Markdown case should become SciFig behavior. The rule is one Markdown file at a time: read it, replicate it, compare it, then promote the reusable essence.

## Scope

- Source cases live under local ignored `template/**/*.md`.
- Temporary evidence lives under ignored `.workflow/case_studies/<case_id>/`.
- Committable skill changes stay under `.claude/skills/scifig-generate`.
- Do not copy template Markdown, fetched source images, or replica PNGs into the submitted skill.

## Per-Case Loop

1. Select exactly one Markdown file from `case-index.json` or the local `template/` tree.
2. Read the complete Markdown file.
3. Build an evidence ledger:
   - source path and title
   - embedded image links, alt text, line numbers, and fetch status
   - code fences with language, line count, and plotting APIs
   - rcParams, font, palette, GridSpec/subplots, zorder, legend, annotation, and export signals
4. Recreate the visual grammar in `.workflow/case_studies/<case_id>/`.
5. Compare the replica with the best available reference image or the article's code/visual constraints.
6. Distill a short `learned_essence` list that avoids copying article prose.
7. Promote only reusable elements into the skill:
   - motif -> `specs/template-visual-motifs.md` or `template-mining/05-annotation-idioms.md`
   - layout -> `template-mining/04-grid-recipes.md` or `templates/layout-recipes-ready.json`
   - helper -> `phases/code-gen/template_mining_helpers.py` or `phases/code-gen/helpers.py`
   - generator behavior -> the matching split generator file plus binding/tests
   - policy -> `specs/template-distillation-contract.md` or `specs/workflow-policies.md`
8. Run the smallest verification that covers the promoted behavior.

## Acceptance Gate

A case is not learned until all fields exist:

```json
{
  "source_markdown": "template/...",
  "reference_used": "... or limitation",
  "replica": ".workflow/case_studies/<case_id>/...",
  "comparison": ".workflow/case_studies/<case_id>/...",
  "learned_essence": ["..."],
  "promoted_skill_files": [".claude/skills/scifig-generate/..."],
  "known_gap": ["..."]
}
```

## Anti-Patterns

- Do not claim learning from `stats.json` alone.
- Do not batch-render many generic charts and call that template replication.
- Do not promote a chart key without generator, registry, planning, QA, and binding coverage.
- Do not move `template/` into the repository payload.
- Do not require root `examples/`, root `scripts/`, or root `docs/` for the skill to work.
