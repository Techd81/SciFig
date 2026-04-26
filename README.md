# SciFig Generate Skill

SciFig Generate is a reusable agent skill for turning experimental data
(CSV, Excel, or matrix-like tables) into publication-ready scientific figure
workflows with journal-style defaults, statistical guardrails, and reproducible
export plans.

This repository is the skill package itself. The repository root contains the
files an agent runner should load:

- `SKILL.md`
- `phases/`
- `specs/`
- `templates/`

Do not wrap this skill inside another `skills/` directory when publishing this
repository.

## Install

Clone this repository directly into your local skills directory.

PowerShell:

```powershell
git clone https://github.com/Techd81/SciFig.git "$env:USERPROFILE\.claude\skills\scifig-generate"
git clone https://github.com/Techd81/SciFig.git "$env:USERPROFILE\.codex\skills\scifig-generate"
```

macOS/Linux:

```bash
git clone https://github.com/Techd81/SciFig.git ~/.claude/skills/scifig-generate
git clone https://github.com/Techd81/SciFig.git ~/.codex/skills/scifig-generate
```

## Scope

Keep this repository limited to the skill content and essential repository
metadata. Runtime packages, tests, workflow scratchpads, generated figures,
sample data, and tool-specific dot directories belong outside this public skill
repository unless they are explicitly promoted as part of the skill.

## License

MIT
