# Project: SciFig

## What This Is

SciFig is a repository for designing an open-source workflow that turns experimental data into publication-ready scientific figures. The current checkout is artifact-first: it contains product research, a local AI skill specification, demo datasets, and rendered figure examples, but no committed Python package yet.

## Core Value

Given real experimental data, the system should reliably produce submission-quality figures with reproducible code, defensible statistical defaults, and journal-style vector exports.

## Requirements

### Validated

- Demo assets already cover 14 figure archetypes through checked-in example outputs.

### Active

- [ ] Turn the research report and skill phases into a runnable Python package.
- [ ] Preserve publication-ready defaults and statistical guardrails as first-class behavior.
- [ ] Make every generated output traceable to versioned data, code, and export metadata.

### Out of Scope

- Generic illustration or slide-design tooling - the repository is focused on scientific figure automation.
- Opaque black-box statistics - reproducibility and auditability are part of the product value.

## Context

The repository currently centers on `doc/deep-research-report.md`, seven CSV sample datasets under `data/`, a rendered gallery of 14 PDF/PNG figures under `output/all14/`, and `.claude/skills/scifig-generate/`, which documents the intended end-to-end workflow. Initialization work therefore needs to document both the actual repository contents and the planned runtime architecture.

## Constraints

- **Artifact-first repository**: There is no committed runtime package yet, so current docs must distinguish planned behavior from implemented code.
- **Scientific reproducibility**: Future automation must emit code, metadata, and statistical choices alongside figures.
- **Journal-style defaults**: Nature-like sizing, typography, line widths, and vector export rules are core requirements, not optional polish.

## Tech Stack

- **Language**: Planned Python runtime; current repository assets are primarily Markdown, CSV, JSON, PDF, and PNG.
- **Framework**: None committed yet; workflow behavior is currently captured in local skill markdown under `.claude/skills/`.
- **Database**: None.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Bootstrap from research and workflow specs before code exists | The repo started as a product-definition and workflow-design effort | Accepted |
| Keep sample datasets and rendered outputs as reference assets | They provide concrete fixtures for future implementation and tests | Accepted |
| Treat `.claude/skills/scifig-generate` as the operational pipeline contract for now | It captures the intended flow until executable modules land | Accepted |

## Stakeholders

- Researchers who need publication-ready figures from real experiment data.
- Maintainers turning the research and skill definitions into a runnable package.
- Future AI/code agents that will rely on repository-grounded initialization metadata.

---
*Last updated: 2026-04-26 after deep scan initialization*
