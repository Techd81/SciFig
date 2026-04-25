# Architecture

## Repository Layout

```text
.
|-- doc/
|-- data/
|-- output/all14/
|-- .claude/skills/scifig-generate/
|-- .workflow/
|-- .ace-tool/
|-- CLAUDE.md
|-- .gitignore
`-- LICENSE
```

## What Exists Today

- `doc/` contains the deep research report and doc-specific guidance.
- `data/` contains seven CSV fixtures for dose-response, multi-panel, line-with-CI, Manhattan, QQ, waterfall, and forest-style outputs.
- `output/all14/` contains 14 rendered figure examples in both PDF and PNG form.
- `.claude/skills/scifig-generate/` defines the intended end-to-end workflow in one top-level skill file plus four phase documents.
- `.workflow/` now holds initialization metadata, specs, and this deep-scan output.

## Current Data Flow

The repository implies the following design-time pipeline:

```text
research report
  -> workflow skill phases
  -> sample datasets
  -> generated figure gallery
```

This is evidence of product shape, not executable implementation. There is no committed package that performs the flow directly.

## Planned Runtime Architecture

The research and skill docs consistently point to a layered Python design:

- `style/` for journal-style presets and export-safe rcParams
- `io/` for dataset loading and schema detection
- `stats/` for test selection and corrections
- `plots/` for chart generators
- `compose/` for multi-panel layout
- `export/` for vector and bitmap outputs

## Inventory Summary

- Non-`.git` files scanned: 52
- Sample datasets: 7
- Rendered figure files in `output/all14/`: 28
- Skill phase documents: 4

## Architectural Constraint

Until the Python package exists, implementation work should treat the research report and skill markdown as the contract, while keeping all new code grounded in the checked-in datasets and reference outputs.
