---
title: "Architecture Constraints"
category: arch
---
# Architecture Constraints

Current repository state is artifact-first. The checkout contains research, datasets, rendered outputs, and workflow specifications, but not the final runtime package yet.

## Module Structure

### Current repository layers

- `doc/` - product research and design reference.
- `data/` - sample CSV datasets that exercise target figure families.
- `output/all14/` - rendered PDF/PNG gallery used as reference output.
- `.claude/skills/scifig-generate/` - workflow contract describing the intended end-to-end generation pipeline.
- `.workflow/` - project metadata, specs, and deep-scan artifacts.

### Planned runtime package

```text
scifig/
  style/      -- Nature-like style engine and presets
  io/         -- Data input, schema detection, variable mapping
  stats/      -- Statistical decision logic and multiple-testing control
  plots/      -- Figure generators (distribution, heatmap, PCA, ROC, KM, etc.)
  compose/    -- Multi-panel assembly and panel labeling
  export/     -- PDF/SVG/TIFF export and font embedding
  templates/  -- Reusable code-generation templates
```

## Layer Boundaries

- Research documents may define expected behavior, but they are not executable source of truth.
- Sample datasets are reference fixtures; future code must not hard-code dataset-specific assumptions.
- Rendered outputs are evidence artifacts, not the behavioral source of truth.
- Skill markdown is the temporary workflow contract until executable modules replace it.

## Dependency Rules

- Future runtime code should maintain one-way flow: `io -> stats -> plots -> compose -> export`.
- `style/` may be imported by plotting and export layers, but must not depend on them.
- Runtime code must not depend on `.claude/` metadata; `.claude/skills/` may reference runtime code once it exists.
- Avoid circular imports across planned runtime layers.

## Technology Constraints

- Runtime target: Python 3.10+.
- Outputs must support vector export, editable fonts, and journal-style defaults.
- Statistical behavior must remain traceable: inputs, mapping, tests, corrections, and export settings should all be serializable.

## Entries

(empty section for spec-add entries)
