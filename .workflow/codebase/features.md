# Features

## Current Repository-Delivered Capabilities

### 1. Research-backed product definition

Status: documented

Evidence:

- [doc/deep-research-report.md](/D:/SciFig/doc/deep-research-report.md:1)
- [CLAUDE.md](/D:/SciFig/CLAUDE.md:1)

This defines target users, chart families, styling constraints, statistical rules, and an MVP direction.

### 2. Skill-defined generation workflow

Status: specified

Evidence:

- [.claude/skills/scifig-generate/SKILL.md](/D:/SciFig/.claude/skills/scifig-generate/SKILL.md:1)
- [.claude/skills/scifig-generate/phases/01-data-detect.md](/D:/SciFig/.claude/skills/scifig-generate/phases/01-data-detect.md:1)
- [.claude/skills/scifig-generate/phases/02-recommend-stats.md](/D:/SciFig/.claude/skills/scifig-generate/phases/02-recommend-stats.md:1)
- [.claude/skills/scifig-generate/phases/03-code-gen-style.md](/D:/SciFig/.claude/skills/scifig-generate/phases/03-code-gen-style.md:1)
- [.claude/skills/scifig-generate/phases/04-export-report.md](/D:/SciFig/.claude/skills/scifig-generate/phases/04-export-report.md:1)

The workflow covers structure detection, chart/statistics selection, styled code generation, and export/reporting.

### 3. Sample dataset pack

Status: available

Evidence:

- [data/dose_response_experiment.csv](/D:/SciFig/data/dose_response_experiment.csv:1)
- [data/multi_panel_experiment.csv](/D:/SciFig/data/multi_panel_experiment.csv:1)
- [data/line_ci_data.csv](/D:/SciFig/data/line_ci_data.csv:1)
- [data/manhattan_data.csv](/D:/SciFig/data/manhattan_data.csv:1)
- [data/qq_data.csv](/D:/SciFig/data/qq_data.csv:1)
- [data/waterfall_data.csv](/D:/SciFig/data/waterfall_data.csv:1)
- [data/forest_data.csv](/D:/SciFig/data/forest_data.csv:1)

These fixtures give future implementation and tests concrete coverage across multiple figure families.

### 4. Rendered figure gallery

Status: available

Evidence:

- [output/all14](/D:/SciFig/output/all14)

The gallery covers 14 named outputs:

- violin with strip
- box with strip
- dot with box
- clustered heatmap
- pure heatmap
- volcano
- PCA
- ROC
- Kaplan-Meier
- correlation matrix
- Manhattan
- QQ
- waterfall
- forest

### 5. Reproducibility seed

Status: partial

Evidence:

- [output/requirements.txt](/D:/SciFig/output/requirements.txt:1)

There is a minimal dependency manifest for the example outputs, but no checked-in source code or provenance metadata yet.

## Missing Features

- Runnable Python package or CLI
- Automated tests
- Provenance mapping from outputs back to code and inputs
- Formal API or notebook entry points
