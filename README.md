# SciFig Generate Skill

A reusable agent skill that transforms experimental data (CSV, Excel, or matrix tables) into publication-ready scientific figures with journal-style defaults, statistical guardrails, and reproducible export plans.

## Install

```bash
# Claude Code
git clone https://github.com/Techd81/SciFig.git ~/.claude/skills/scifig-generate

# Codex
git clone https://github.com/Techd81/SciFig.git ~/.codex/skills/scifig-generate
```

## What It Does

- Upload CSV/Excel/matrix data
- Auto-detect data structure (tidy vs matrix) and scientific domain
- Recommend publication-grade chart types (104 charts across 13 domains)
- Generate Nature/Cell/Science/Lancet/NEJM/JAMA-aligned figure code
- Apply colorblind-safe palettes and multi-panel composition
- Export vector graphics (PDF/SVG) with statistical reports

## Structure

- `SKILL.md` — Skill entry point and orchestrator
- `phases/` — Execution phases (data detect, chart recommend, code gen, export)
- `specs/` — Chart catalog, domain playbooks, journal profiles
- `templates/` — Palette presets, panel layout recipes

## License

MIT
