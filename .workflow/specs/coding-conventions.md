---
title: "Coding Conventions"
category: coding
---
# Coding Conventions

The repository does not yet contain committed runtime source code. These are the target conventions for future Python modules plus the naming rules already visible in current assets.

## Formatting

- Python indentation: 4 spaces.
- Python line length: 88 characters.
- Trailing commas: yes for multi-line literals and calls.
- Markdown style: short sections, concrete headings, evidence-backed statements.
- CSV headers: lowercase `snake_case`.

## Naming

- Variables and functions: `snake_case`
- Classes and dataclasses: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `snake_case`
- Rendered gallery outputs: numeric prefix plus short slug, for example `01_violin_strip.pdf`

## Imports

- Use explicit imports; no wildcard imports.
- Order imports as stdlib, third-party, local.
- Keep public APIs type hinted.

## Patterns

- Represent data profiles, chart plans, and export metadata as typed models or dataclasses.
- Avoid hidden statistical defaults; emit the chosen method and correction strategy as metadata.
- Keep plotting defaults centralized in style presets rather than duplicated across generators.
- Add comments only when they explain non-obvious reasoning or domain constraints.

## Scientific And Artifact Conventions

- Use `mm = 1 / 25.4` when converting journal sizes.
- Set seeds or `random_state` when randomness is involved.
- Export with `bbox_inches='tight'` and `pdf.fonttype=42` when using Matplotlib.
- Keep sample datasets compact, task-oriented, and named after the figure family they exercise.
- Ensure every generated figure can be traced to source data, style preset, and statistical choices.

## Entries

(empty section for spec-add entries)
