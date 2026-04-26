---
name: scifig-generate
description: Upload experimental data (CSV/Excel/matrix), auto-detect structure, infer scientific domain, recommend publication-grade charts, generate Nature/Cell/Science-aligned figure code, optimize multi-panel composition and palette systems, and export vector graphics with statistical reports. Triggers on "generate figure", "plot data", "sci figure", "科研图", "画图", "多 panel".
allowed-tools: Agent, AskUserQuestion, TodoWrite, Read, Write, Edit, Bash, Glob, Grep
---

# SciFig Generate

End-to-end workflow for turning real experimental data into submission-ready scientific figures. The skill is journal-token driven, domain-aware, and narrative-first: it reads the data, infers the scientific context, picks chart families and statistics, builds a multi-panel story when needed, and exports reproducible code plus publication assets.

## Architecture Overview

```text
+-----------------------------------------------------------------------------------+
| scifig-generate (Orchestrator)                                                    |
| -> collect preferences -> load references -> dispatch phases -> iterate on demand |
+----------------------+----------------------+----------------------+---------------+
                       |                      |                      |
                       v                      v                      v
                +-------------+        +-------------+        +-------------+
                | Phase 1     |        | Phase 2     |        | Phase 3     |
                | Data Detect |        | Charts+Stat |        | Code+Style  |
                +------+------+        +------+------+        +------+------+
                       |                      |                      |
                       v                      v                      v
                  dataProfile           chartPlan +             styledCode +
                + domainHints         panelBlueprint           journalProfile
                + panelCandidates      + palettePlan           + colorSystem
                       \                      |                      /
                        \                     v                     /
                         \              +-------------+            /
                          ------------> | Phase 4     | <----------
                                        | Export      |
                                        +------+------+
                                               |
                                               v
                                          outputBundle
```

## Key Design Principles

1. **Journal-token driven**: Use explicit style profiles instead of ad-hoc plotting choices. Nature dimensions are grounded in the official Nature figure guide; Cell-like and Science-like presets maintain the same production-safe discipline.
2. **Domain-aware charting**: Infer likely domains such as genomics, single-cell, pharmacology, neuroscience, or clinical survival and bias chart recommendations toward the conventions of that field.
3. **Narrative multi-panel design**: Treat multi-panel figures as a story with hero, support, validation, and mechanism panels rather than a loose grid of unrelated plots.
4. **Palette governance**: Prefer restrained, colorblind-safe palettes; keep semantic mappings consistent across panels; avoid rainbow and uncontrolled red-green contrasts.
5. **Statistical honesty**: No inferential claims without replicate or cohort meaning. When data only support descriptive visualization, say so.
6. **Reproducibility-first**: Every figure should be exportable as code plus metadata, source-data manifests, and methods-ready statistical descriptions.

## Interactive Preference Collection

Collect workflow preferences via AskUserQuestion before dispatching to phases:

```python
preferences = AskUserQuestion(questions=[
    {
        "question": "Target journal figure language?",
        "header": "Journal",
        "multiSelect": false,
        "options": [
            {"label": "Nature-like (Recommended)", "description": "89/183 mm canvas discipline, editable sans text, minimal decoration"},
            {"label": "Cell-like", "description": "Story-first panels, clean white canvas, restrained accent colors, sparse labels"},
            {"label": "Science-like", "description": "Compact and minimal, fast visual parsing, low-ink plotting"},
            {"label": "Lancet-like", "description": "80/168 mm, clinical evidence focus, compact Helvetica typography"},
            {"label": "NEJM-like", "description": "86/178 mm, clinical outcome focus, clean Arial typography"},
            {"label": "JAMA-like", "description": "84/175 mm, clinical validation focus, precise labeling"},
            {"label": "Custom", "description": "Override journal tokens manually"}
        ]
    },
    {
        "question": "Primary scientific domain?",
        "header": "Domain",
        "multiSelect": false,
        "options": [
            {"label": "General biomedical (Recommended)", "description": "Generic publication-safe chart rules"},
            {"label": "Genomics / Transcriptomics", "description": "Volcano, enrichment, heatmap, embedding, mutation-aware views"},
            {"label": "Single-cell / Spatial", "description": "UMAP, abundance, feature plots, grouped expression panels"},
            {"label": "Proteomics / Metabolomics", "description": "Heatmaps, PCA, volcano, pathway and abundance views"},
            {"label": "Pharmacology / Toxicology", "description": "Dose-response, paired efficacy, waterfall, exposure-response"},
            {"label": "Immunology / Cell Biology", "description": "Distribution plots, trajectories, composition, validation panels"},
            {"label": "Neuroscience / Behavior", "description": "Time-course, paired traces, tuning or condition comparison panels"},
            {"label": "Clinical / Diagnostics / Survival", "description": "KM, forest, ROC/PR, calibration, cohort summaries"},
            {"label": "Epidemiology / Public Health", "description": "Stratified trends, risk models, forest and correlation views"},
            {"label": "Materials / Engineering", "description": "Stress-strain, property comparisons, phase diagrams, process optimization"},
            {"label": "Ecology / Environmental", "description": "Species abundance, diversity indices, spatial distribution, time-series trends"},
            {"label": "Agriculture / Food Science", "description": "Yield comparisons, treatment effects, sensory panels, growth curves"},
            {"label": "Psychology / Social Science", "description": "Survey distributions, Likert scales, before-after comparisons, mediation paths"}
        ]
    },
    {
        "question": "Figure story shape?",
        "header": "Story",
        "multiSelect": false,
        "options": [
            {"label": "Single panel", "description": "One chart only"},
            {"label": "Comparison pair (Recommended)", "description": "Hero chart plus one support or validation panel"},
            {"label": "2x2 story board", "description": "Hero plus three support panels"},
            {"label": "Hero + stacked support", "description": "Wide hero panel with stacked small multiples"},
            {"label": "Custom grid", "description": "Custom rows x columns"}
        ]
    },
    {
        "question": "Color system preference?",
        "header": "Color",
        "multiSelect": false,
        "options": [
            {"label": "Journal-safe muted (Recommended)", "description": "Muted categorical colors with grayscale resilience"},
            {"label": "Domain semantic", "description": "Use domain-specific mappings such as risk, treatment, pathway, cell state"},
            {"label": "Strict grayscale-safe", "description": "Maximize contrast when printed or reviewed in grayscale"},
            {"label": "Custom", "description": "Manual palette override"}
        ]
    },
    {
        "question": "Export formats?",
        "header": "Export",
        "multiSelect": true,
        "options": [
            {"label": "PDF (Recommended)", "description": "Vector, editable text, submission-safe"},
            {"label": "SVG", "description": "Vector, good for review and editing"},
            {"label": "PNG", "description": "Preview only"},
            {"label": "TIFF", "description": "Raster when required by production workflows"}
        ]
    },
    {
        "question": "Statistical rigor level?",
        "header": "Stats",
        "multiSelect": false,
        "options": [
            {"label": "Strict (Recommended)", "description": "Replicate-aware, correction-aware, conservative defaults"},
            {"label": "Standard", "description": "Reasonable defaults with warnings"},
            {"label": "Descriptive only", "description": "No inferential testing"}
        ]
    },
    {
        "question": "Missing value handling?",
        "header": "Missing",
        "multiSelect": false,
        "options": [
            {"label": "Drop rows with missing values (Recommended)", "description": "Remove rows where key columns (group/value) have NaN, report count"},
            {"label": "Warn but keep", "description": "Show warning, let user decide per-column"},
            {"label": "Impute (mean/median)", "description": "Fill missing values with group mean or median"}
        ]
    }
])

workflowPreferences = {
    "journalStyle": {
        "Nature-like (Recommended)": "nature",
        "Cell-like": "cell",
        "Science-like": "science",
        "Lancet-like": "lancet",
        "NEJM-like": "nejm",
        "JAMA-like": "jama"
    }.get(preferences.journal, "custom"),
    "domainFamily": {
        "General biomedical (Recommended)": "general_biomedical",
        "Genomics / Transcriptomics": "genomics_transcriptomics",
        "Single-cell / Spatial": "single_cell_spatial",
        "Proteomics / Metabolomics": "proteomics_metabolomics",
        "Pharmacology / Toxicology": "pharmacology_toxicology",
        "Immunology / Cell Biology": "immunology_cell_biology",
        "Neuroscience / Behavior": "neuroscience_behavior",
        "Clinical / Diagnostics / Survival": "clinical_diagnostics_survival",
        "Epidemiology / Public Health": "epidemiology_public_health",
        "Materials / Engineering": "materials_engineering",
        "Ecology / Environmental": "ecology_environmental",
        "Agriculture / Food Science": "agriculture_food_science",
        "Psychology / Social Science": "psychology_social_science"
    }.get(preferences.domain, "general_biomedical"),
    "storyMode": {
        "Single panel": "single",
        "Comparison pair (Recommended)": "comparison_pair",
        "2x2 story board": "story_board_2x2",
        "Hero + stacked support": "hero_plus_stacked_support"
    }.get(preferences.story, "custom_grid"),
    "missingHandling": {
        "Drop rows with missing values (Recommended)": "drop",
        "Warn but keep": "warn",
        "Impute (mean/median)": "impute"
    }.get(preferences.missing, "drop"),
    "colorMode": {
        "Journal-safe muted (Recommended)": "journal_safe_muted",
        "Domain semantic": "domain_semantic",
        "Strict grayscale-safe": "strict_grayscale_safe"
    }.get(preferences.color, "custom"),
    "exportFormats": [{"PDF (Recommended)": "pdf", "SVG": "svg", "PNG": "png", "TIFF": "tiff"}.get(x, x.lower()) for x in preferences.export],
    "statsRigor": {
        "Strict (Recommended)": "strict",
        "Standard": "standard",
        "Descriptive only": "descriptive"
    }.get(preferences.stats, "strict"),
    "panelLayout": {
        "Single panel": "single",
        "Comparison pair (Recommended)": "1x2",
        "2x2 story board": "2x2",
        "Hero + stacked support": "2x2-hero-span"
    }.get(preferences.story, "custom")
}
```

## Execution Flow

> **COMPACT DIRECTIVE**: The phase currently marked `in_progress` in TodoWrite is the active execution phase and must remain uncompressed. If a sentinel survives but the detailed protocol does not, re-read that phase file before continuing.

```text
Phase 1: Data Input, Structure Detection, Domain Signals
   -> Ref: phases/01-data-detect.md
      Input: file path + workflowPreferences
      Output: dataProfile (schema, semantic roles, domainHints, risks, panelCandidates)

Phase 2: Chart Recommendation, Stats, Panel Blueprint
   -> Ref: phases/02-recommend-stats.md
      Input: dataProfile + workflowPreferences
      Output: chartPlan (primary/secondary charts, stats, panelBlueprint, palettePlan)

Phase 3: Code Generation, Journal Styling, Multi-panel Composition
   -> Ref: phases/03-code-gen-style.md
      Input: chartPlan + dataProfile + workflowPreferences
      Output: styledCode (pythonCode, journalProfile, colorSystem, figureSpec, panelGeometry)

Phase 4: Export, Source Data, Statistical Report
   -> Ref: phases/04-export-report.md
      Input: styledCode + chartPlan + dataProfile + workflowPreferences
      Output: outputBundle (figures, code, source data, reports, metadata)
```

**Phase Reference Documents** (read on-demand):

| Phase | Document | Purpose | Compact |
|-------|----------|---------|---------|
| 1 | [phases/01-data-detect.md](phases/01-data-detect.md) | Data ingestion, semantic role mapping, domain inference | TodoWrite driven |
| 2 | [phases/02-recommend-stats.md](phases/02-recommend-stats.md) | Chart taxonomy selection, stats, panel blueprint | TodoWrite driven + sentinel |
| 3 | [phases/03-code-gen-style.md](phases/03-code-gen-style.md) | Journal profiles, palette system, code generation, composition | TodoWrite driven + sentinel |
| 4 | [phases/04-export-report.md](phases/04-export-report.md) | Export bundle, source data, metadata, reporting | TodoWrite driven |

**Reference Specs** (read on-demand when needed):

| Kind | Document | Purpose |
|------|----------|---------|
| Journal | [specs/journal-profiles.md](specs/journal-profiles.md) | Nature/Cell/Science-aligned style tokens |
| Charts | [specs/chart-catalog.md](specs/chart-catalog.md) | Expanded chart family taxonomy and triggers |
| Domains | [specs/domain-playbooks.md](specs/domain-playbooks.md) | Domain-specific plotting, stats, and panel guidance |
| Layouts | [templates/panel-layout-recipes.md](templates/panel-layout-recipes.md) | Reusable multi-panel story recipes |
| Palettes | [templates/palette-presets.md](templates/palette-presets.md) | Reusable categorical/sequential/diverging palette presets |

**Compact Rules**:
1. `TodoWrite in_progress` -> preserve full content
2. `TodoWrite completed` -> safe to compress to summary
3. If a sentinel remains without the full step protocol -> `Read("phases/0N-xxx.md")` before continuing

## Core Rules

1. Do not claim a Nature- or Cell-like figure solely from a palette; typography, spacing, line weight, and panel discipline must also match.
2. Do not use bar charts to hide distributions when individual-level or cohort-level data can be shown.
3. Do not mix unrelated semantic color mappings across panels of the same figure.
4. Do not use rainbow colormaps unless the variable is cyclic and the legend explicitly justifies it.
5. Keep all figure text editable, sans serif, and legible at final print size.
6. Use shared legends or shared colorbars when panels encode the same semantics.
7. Multi-panel figures must have an explicit panel blueprint before code generation.
8. Prefer vector export and generate source-data friendly artifacts for quantitative panels.
9. If domain inference is weak, fall back to general biomedical rules instead of overfitting to a guessed specialty.
10. If statistical assumptions are uncertain, downgrade to a conservative or descriptive choice and explain why.

## Input Processing

User input is normalized into:

```text
FILE: /path/to/data.csv
EXTRAS: optional figure request or hypothesis
DOMAIN_OVERRIDE: optional explicit domain hint
MUST_HAVE: optional chart or panel requirements
```

If `FILE:` is missing, ask for it. If `DOMAIN_OVERRIDE` conflicts with detected cues, keep the user override but warn in Phase 2.

## Data Flow

```text
input
  ->
Phase 1 -> dataProfile = {
  format,
  structure,
  columns,
  semanticRoles,
  domainHints,
  nGroups,
  nObservations,
  replicateInfo,
  riskFlags,
  panelCandidates,
  warnings
}
  ->
Phase 2 -> chartPlan = {
  primaryChart,
  secondaryCharts,
  statMethod,
  multipleComparison,
  annotations,
  panelBlueprint,
  palettePlan,
  journalOverrides,
  rationale
}
  ->
Phase 3 -> styledCode = {
  pythonCode,
  journalProfile,
  figureSpec,
  colorSystem,
  panelGeometry,
  statsReport,
  seed
}
  ->
Phase 4 -> outputBundle = {
  figures,
  code,
  statsReport,
  sourceData,
  panelManifest,
  requirements,
  metadata
}
```

## TodoWrite Pattern

```text
Phase 1 starts:
  -> [in_progress] Phase 1: data detect and domain inference
     -> [pending] Read and parse file
     -> [pending] Detect structure and semantic roles
     -> [pending] Infer domain hints and panel candidates
     -> [pending] Assess risks and build dataProfile

Phase 1 ends:
  -> [completed] Phase 1: dataProfile ready

Phase 2 starts:
  -> [in_progress] Phase 2: chart, stats, panel blueprint
     -> [pending] Resolve domain playbook
     -> [pending] Recommend chart family and stats
     -> [pending] Build panel blueprint and palette plan

Phase 2 ends:
  -> [completed] Phase 2: chartPlan locked
```

Collapse completed sub-tasks back to phase-level summaries before the next phase starts.

## Post-Phase Updates

- After Phase 1: If domain inference is high confidence, note the selected domain playbook and any field-specific warnings.
- After Phase 2: Freeze the chart vocabulary, panel blueprint, and palette plan unless the user requests revision.
- After Phase 3: Validate syntax, imports, and layout consistency before export.
- After Phase 4: Summarize how the user can iterate without re-running Phase 1.

## Error Handling

- Ambiguous domain -> fall back to `General biomedical`, present the top alternatives in rationale.
- Unsupported chart request -> map to the closest supported family and explain the substitution.
- Overcrowded multi-panel plan -> reduce to fewer panels or use a hero-plus-support recipe.
- Palette collision -> fall back to journal-safe muted palette with grayscale-safe accents.
- Weak statistical support -> switch to descriptive mode or a more conservative test.

## Coordinator Checklist

- Confirm a readable input file exists.
- Collect `workflowPreferences` before any phase dispatch.
- Read chart/domain/journal references only when needed.
- Keep the active phase marked `in_progress`.
- Before Phase 3, ensure the panel blueprint and palette plan are explicit.
- Before Phase 4, ensure code generation includes source-data and metadata hooks.

## Related Commands

- `/spec-add learning ...` to record new plotting or domain edge cases.
- `/spec-add arch ...` when the eventual runtime package introduces permanent APIs.
