# Context

## Deep Scan Summary

Repository `SciFig` is now initialized as an artifact-first project. The scan found 52 non-`.git` files spanning product research, workflow specifications, sample datasets, rendered outputs, and project metadata.

## What Changed During Initialization

- Added missing `.workflow/project.md`, `.workflow/state.json`, and `.workflow/config.json`
- Refreshed `.workflow/project-tech.json` to match the current repository contents
- Rewrote workflow specs to describe the actual artifact-first architecture
- Added `.workflow/codebase/` documentation for tech stack, architecture, features, and concerns
- Refreshed `.claude/index.json` so future scans stop under-reporting the repository

## Recommended Next Steps

1. Create a real Python package rooted in `scifig/`, starting with `style/` and `io/`.
2. Promote `output/requirements.txt` into a root runtime manifest (`pyproject.toml` or root `requirements.txt`).
3. Add tests that use the checked-in CSV files as fixtures for data detection and plotting behavior.
4. Decide whether the output gallery is a tracked reference artifact or a purely regenerable cache.
