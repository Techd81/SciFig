# Coordinator Reference

Read when executing gates, agent delegation, or completion checklist.

## Preference Gates

Full card flow and helpers: [specs/preference-collection.md](../specs/preference-collection.md)

Key gates (must complete before phase dispatch):

1. Data-status card → file exists / synthetic / template
2. Data-path card (if file exists) → validate suffix with `is_concrete_data_file_path()`
3. Mode card → `auto` / `interactive`
4. Synthetic-domain + bundle cards (if synthetic)
5. Template chart-bundle card (domain-matched packages from `knowledge/case-index.json`)
6. Visual-preference card (4 questions: journal, color, DPI, crowding)

Never scan workspace for CSV/Excel files. Never run Read/Bash on paths before file-path and mode gates complete.

## Agent Delegation

Do not spawn Agents before preference gates complete. Blocking findings route back to owning phase.

| Agent | Phase | Trigger |
| ----- | ----- | ------- |
| `data-profile-auditor` | 1 | matrix structure, missing roles, n_groups>10 |
| `chart-stats-planner` | 2 | inferential claims, custom domain, survival charts |
| `panel-layout-auditor` | 2 | panel_count>2, shared legend, long labels |
| `palette-journal-auditor` | 2 | n_categories>=8, journal submission |
| `scientific-color-harmony` | 2 | after build_palette_plan |
| `layout-aesthetics` | 2 | after build_panel_blueprint |
| `content-richness` | 2 | after build_visual_content_plan |
| `code-reviewer` | 3 | before Phase 3 completes |
| `rendered-qa` | 4 | after code execution |
| `visual-impact-scorer` | 4 | after rendered-qa |

## Data Flow Artifacts

- `dataProfile`: format, structure, columns, semanticRoles, domainHints, audit
- `chartPlan`: primaryChart, panelBlueprint, palettePlan, templateCasePlan, delegationReports
- `styledCode`: pythonCode, journalProfile, codeReview
- `outputBundle`: figures, sourceData, renderQa, metadata

## Core Rules (summary)

1. Journal styling requires typography, spacing, and panel discipline — not palette alone.
2. One shared bottom-center `fig.legend` per figure; no in-axes or outside-right legends.
3. Every script calls `enforce_figure_legend_contract(...)` before `savefig`.
4. Embed helper source from `runtime/helpers.py` — never hand-write replacements.
5. Multi-panel figures need an explicit panel blueprint before Phase 3.
6. Promote template learnings into `runtime/` before expanding coordinator prose.
7. Use `specs/workflow-policies.md` for thresholds — no ad-hoc magic numbers.

## Completion Checklist

Before declaring done, require:

- `renderQa.hardFail == false`
- `legendContractEnforced == true`, `layoutContractEnforced == true`
- `axisLegendRemainingCount == 0`, `layoutContractFailures == []`
- `legendModeUsed in ["bottom_center", "none"]`
- Visual content satisfies `visualContentPlan.minTotalEnhancements`

## Error Handling

- Ambiguous domain → `General biomedical` + alternatives in rationale
- Unsupported chart → closest supported family + explanation
- Overcrowded plan → fewer panels or hero-plus-support recipe
- Render QA failure → return to Phase 3 (layout/code) or Phase 2 (overpacked plan)
