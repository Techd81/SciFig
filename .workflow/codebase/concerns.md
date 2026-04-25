# Cross-cutting Concerns

## High Priority

### No committed runtime implementation

The repository documents the workflow but does not yet include the Python package, CLI, or scripts needed to execute it from source.

### Provenance gap for outputs

`output/all14/` proves that figure examples exist, but there is no checked-in code path linking those files back to exact commands, seeds, input hashes, or style settings.

### Initialization drift existed before this scan

`.workflow/` existed without `project.md`, `state.json`, or `config.json`, which meant the project was only partially initialized.

## Medium Priority

### Index drift

The previous `.claude/index.json` reflected an earlier state and missed `data/`, `output/`, `.workflow/`, and `.ace-tool/` contents.

### Dependency manifest is in `output/`

The only committed requirements file lives under `output/requirements.txt`, which is useful for examples but not ideal as the root runtime manifest.

### Output tracking strategy is ambiguous

[.gitignore](/D:/SciFig/.gitignore:1) ignores `output/` plus common rendered formats (`*.pdf`, `*.png`, `*.svg`, `*.tiff`, `*.eps`). If the gallery is intended as a reference asset, the repository should make that decision explicit.

## Low Priority

### Hidden support metadata

`.ace-tool/index.json` exists but is not described anywhere else. It is low risk, but future contributors may not know whether it is disposable cache or required metadata.
