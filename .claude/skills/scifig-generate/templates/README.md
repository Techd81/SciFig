# Ready Import Registries

This folder contains generator-ready resources distilled from `template-mining/`.
The JSON files are the single source of truth for runtime defaults; prose files
remain human-readable rationale.

## `template-palette-registry.json`

Schema:

- `categorical`, `sequential`, `diverging`: maps palette name to `{name, type, anchors, n_max, source_anchors, anti_palette}`.
- `semantic_roles`: maps stable semantic role tokens to hex colors or active-palette references.

Import example:

```python
import json
from pathlib import Path

with (Path(skill_root) / "templates" / "template-palette-registry.json").open(encoding="utf-8") as f:
    PALETTE_REGISTRY = json.load(f)
```

Phase 3 should resolve colors through `resolve_palette(name)` and `role_color(role)`
rather than redefining palette hex lists inline.

## `layout-recipes-ready.json`

Schema:

- Top-level keys `R0` through `R11`.
- Each recipe includes `id`, `name`, `panel_count`, `gridspec_args`,
  `reserved_slots`, `helper_call`, and `use_cases`.

Generators should treat `reserved_slots.legend` and `reserved_slots.colorbar` as
layout constraints before drawing external legends or colorbars.

## `zorder-recipes-ready.json`

Schema:

- `universal_tiers`: shared zorder tiers including `panel_label`.
- `family_overrides`: per-family semantic layer maps.

Generators should call `apply_zorder_recipe(family, ax, layers)` or map semantic
roles through this registry; ad-hoc zorder defaults should not be reintroduced.

## Single Source Of Truth

Palette, layout, and zorder defaults live in these JSON files:

- `templates/template-palette-registry.json`
- `templates/layout-recipes-ready.json`
- `templates/zorder-recipes-ready.json`

`phases/code-gen/template_mining_helpers.py` is responsible for loading these
registries for runtime helper APIs.
