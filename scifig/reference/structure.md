# SciFig Skill Directory Map

```
scifig/
├── SKILL.md              # Coordinator entry point (read first)
├── reference/            # Progressive disclosure — read on demand
├── phases/               # Phase 1–5 execution protocols
├── specs/                # Policies, catalogs, playbooks
├── runtime/              # Executable Python (generators, finalizer, registry)
├── knowledge/            # 94-case visual grammar knowledge base
├── resources/            # Machine-readable registries (palette, layout, zorder)
└── assets/fonts/         # Optional user-supplied fonts
```

## Folder Responsibilities

| Folder | Purpose | Load when |
|--------|---------|-----------|
| `phases/` | Step-by-step pipeline protocols | Active phase is `in_progress` |
| `specs/` | Chart catalog, journal profiles, workflow policies | Phase 2/3 needs policy or taxonomy |
| `runtime/` | `helpers.py`, `generators_*.py`, `registry.py` | Phase 3 code generation |
| `knowledge/` | Narrative arcs, zorder, palettes, techniques | Phase 2/3 chart or style decisions |
| `resources/` | JSON registries consumed by `template_mining_helpers` | Phase 3 layout/palette binding |
| `reference/` | Coordinator details extracted from SKILL.md | Gates, finalizer, checklist |

## Runtime (`runtime/`)

- `helpers.py` — finalizer, layout audit, legend contract
- `template_mining_helpers.py` — journal kernel, palettes, grid recipes, idioms
- `registry.py` — 121-chart key → generator map
- `generators_<domain>.py` — domain-split chart implementations
- `source-lint.py` — forbidden-pattern lint for generated code

## Knowledge (`knowledge/`)

- `INDEX.md` — loading protocol and corpus index (always load before Phase 2/3)
- `modules/` — 6 core modules (rcParams, zorder, palette, grid, annotation, narrative)
- `techniques/` — per-family deep-dives (radar, SHAP, heatmap, etc.)
- `scripts/` — extraction/maintenance scripts (do not load during plotting)
- `case-index.json` — slim routing index for 94 template cases

## Resources (`resources/`)

Runtime JSON/MD registries loaded by `template_mining_helpers.py`:

- `template-palette-registry.json`
- `layout-recipes-ready.json`
- `zorder-recipes-ready.json`

## Install Paths

| Environment | Path |
|-------------|------|
| Repo canonical | `SciFig/scifig/` |
| Claude Code | `~/.claude/skills/scifig/` (copy or symlink) |
| Cursor (project) | `.cursor/skills/scifig/` → junction to `scifig/` |
