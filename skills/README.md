# SciFig Skills

This directory contains reusable agent skills distributed with SciFig.

## Available Skills

- `scifig-generate`: Turns experimental data into publication-ready scientific figure workflows.

## Install

Copy the desired skill directory into your agent runner's skills directory.

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force "skills\scifig-generate" "$env:USERPROFILE\.claude\skills\"

New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force "skills\scifig-generate" "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux:

```bash
mkdir -p ~/.claude/skills ~/.codex/skills
cp -r skills/scifig-generate ~/.claude/skills/
cp -r skills/scifig-generate ~/.codex/skills/
```

The repository keeps skills in this neutral `skills/` directory so the same
skill can be used by different compatible runners. Do not commit installed
copies under tool-specific dot directories such as `.claude/`, `.codex/`, or
`.agents/`.
