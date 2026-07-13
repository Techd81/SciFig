---
name: scifig
description: Agent-only skill that turns experimental data (CSV/Excel/matrix) into publication-grade scientific figures. Auto-detects structure, infers scientific domain, recommends charts, generates Nature/Cell/Science-aligned matplotlib code, and exports vector graphics with statistical reports. Does not require the scifig Python package. Triggers on "generate figure", "plot data", "sci figure", "科研图", "画图", "多 panel".
allowed-tools: Agent, AskUserQuestion, TodoWrite, Read, Write, Edit, Bash, Glob, Grep
---
# SciFig Generate

End-to-end workflow for turning experimental data into submission-ready scientific figures. Journal-token driven, domain-aware, narrative-first.

## Quick Start

```
preference gates → Phase 1 dataProfile → Phase 2 chartPlan → Phase 3 styledCode → Phase 4 outputBundle
```

Each phase owns one artifact. Blocking findings route back to the owning phase.

> **COMPACT DIRECTIVE**: The phase marked `in_progress` in TodoWrite is active — keep it uncompressed. If a sentinel survives without the full protocol, `Read("phases/0N-xxx.md")` before continuing.

## Directory Map

See [reference/structure.md](reference/structure.md) for the full layout.

| Folder | Role |
|--------|------|
| `phases/` | Phase 1–5 execution protocols |
| `specs/` | Chart catalog, journal profiles, policies |
| `runtime/` | Python generators, finalizer, registry |
| `knowledge/` | 94-case visual grammar (modules + techniques) |
| `resources/` | Palette/layout/zorder JSON registries |
| `reference/` | Coordinator details (gates, finalizer, checklist) |

## Runtime Self-Containment

**Agent-only** — do not import the external `pip install scifig` package.

All behavior lives in this folder:

- `runtime/helpers.py` — finalizer, layout audit
- `runtime/template_mining_helpers.py` — journal kernel, palettes, idioms
- `runtime/generators_*.py` — chart generators
- `runtime/registry.py` — 121-chart registry

Generated scripts must embed and execute helper source inline.

## Design Principles

1. **Journal-token driven** — explicit style profiles, not ad-hoc choices
2. **Domain-aware charting** — bias recommendations toward field conventions
3. **Narrative multi-panel** — hero/support/validation story, not unrelated grids
4. **Palette governance** — colorblind-safe, consistent semantic mappings
5. **Statistical honesty** — no inferential claims without replicate meaning
6. **Template-grounded** — rcParams, zorder, palettes trace to `knowledge/` corpus

Details: [reference/coordinator.md](reference/coordinator.md)

## Knowledge Base

Before Phase 2/3, load `knowledge/INDEX.md`. Consult modules and techniques instead of inventing patterns.

Loading protocol, bootstrap code, maintenance: [reference/knowledge-base.md](reference/knowledge-base.md)

Finalizer rules: [reference/finalizer.md](reference/finalizer.md)

## Preference Gates

Complete before any phase dispatch. Full card flow: [specs/preference-collection.md](specs/preference-collection.md)

Gate summary: [reference/coordinator.md](reference/coordinator.md#preference-gates)

Never scan workspace for data files. Never Read/Bash paths before file-path and mode gates.

## Phase Dispatch

| Phase | Document | Purpose |
| ----- | -------- | ------- |
| 1 | [phases/01-data-detect.md](phases/01-data-detect.md) | Ingest, semantic roles, domain inference |
| 2 | [phases/02-recommend-stats.md](phases/02-recommend-stats.md) | Chart taxonomy, stats, panel blueprint |
| 3 | [phases/03-code-gen-style.md](phases/03-code-gen-style.md) | Journal styling, code generation |
| 4 | [phases/04-export-report.md](phases/04-export-report.md) | Export bundle, source data, QA |
| 5* | [phases/05-template-distill.md](phases/05-template-distill.md) | Optional article-code promotion |

## Reference Specs (on demand)

| Kind | Document |
| ---- | -------- |
| Journal | [specs/journal-profiles.md](specs/journal-profiles.md) |
| Charts | [specs/chart-catalog.md](specs/chart-catalog.md) |
| Domains | [specs/domain-playbooks.md](specs/domain-playbooks.md) |
| Policies | [specs/workflow-policies.md](specs/workflow-policies.md) |
| Motifs | [specs/template-visual-motifs.md](specs/template-visual-motifs.md) |
| Distill | [specs/template-distillation-contract.md](specs/template-distillation-contract.md) |
| Layouts | [resources/panel-layout-recipes.md](resources/panel-layout-recipes.md) |
| Palettes | [resources/palette-presets.md](resources/palette-presets.md) |

## Input Format

```text
FILE: /path/to/data.csv
EXTRAS: optional figure request
DOMAIN_OVERRIDE: optional domain hint
MUST_HAVE: optional chart requirements
```

## TodoWrite Pattern

One active phase at a time. Expand into sub-tasks while `in_progress`; collapse to summary when completed.

## Related Commands

- `/spec-add learning ...` — record plotting edge cases
- `/spec-add arch ...` — new runtime helpers or generator APIs
